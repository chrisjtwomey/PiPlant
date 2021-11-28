import os
import re
import yaml
import math
import time
import logging.config
import util.utils as utils
from light.lightmanager import LightManager
from display.epaper import EPaper
from sensors.polledsensor import PolledSensor
from sensors.devicestatistics import DeviceStatistics
from sensors.sensorhub import SensorHub
from sensors.soilmoisture import SoilMoistureSensor
from sensors.profile import *

cwd = os.path.dirname(os.path.realpath(__file__))
logging.config.fileConfig(os.path.join(cwd, 'logging.dev.ini'))


class PiPlant(PolledSensor):

    def __init__(self, config):
        piplantconf = config["piplant"]
        self._poll_interval_seconds = utils.dehumanize(piplantconf["poll_interval"])
        self._render_interval_seconds = utils.dehumanize(piplantconf["render_interval"])
        self._process_time = 0
        self._render_time = 0

        skip_splash_screen = utils.dehumanize(piplantconf["skip_splash_screen"])

        super().__init__(self._poll_interval_seconds)

        self.log.info(r"""\
            
                            PiPlant
                         @chrisjtwomey
                    _
                  _(_)_                          wWWWw   _
      @@@@       (_)@(_)   vVVVv     _     @@@@  (___) _(_)_
     @@()@@ wWWWw  (_)\    (___)   _(_)_  @@()@@   Y  (_)@(_)
      @@@@  (___)     `|/    Y    (_)@(_)  @@@@   \|/   (_)\
       /      Y       \|    \|/    /(_)    \|      |/      |
    \ |     \ |/       | / \ | /  \|/       |/    \|      \|/
    \\|//   \\|///  \\\|//\\\|/// \|///  \\\|//  \\|//  \\\|// 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        """)

        # sensors
        self.log.info("Initializing sensors...")

        self.soil_moisture_sensors = [
            SoilMoistureSensor(
                adc_channel=0, calibrated_max_value=0.68, profile=PROFILE_CHINA_DOLL_BONSAI),
            SoilMoistureSensor(
                adc_channel=1, calibrated_max_value=0.70, profile=PROFILE_FUKIEN_TEA_BONSAI),
            SoilMoistureSensor(
                adc_channel=2, calibrated_max_value=0.67, profile=PROFILE_PALM),
            SoilMoistureSensor(
                adc_channel=3, calibrated_max_value=0.69, profile=PROFILE_FICUS),
            SoilMoistureSensor(
                adc_channel=4, calibrated_max_value=0.69, profile=PROFILE_SUCCULENT),
        ]
        self.sensorhub = SensorHub()
        self.boardstats = DeviceStatistics()
        self.log.info("Sensors initialized")

        # processors
        self.log.info("Initializing processors...")
        lmconf = config["lightmanager"]
        self.lifxmanager = LightManager(lmconf)
        self.log.info("Processors initialized")

        # renderers
        self.log.info("Initializing display...")
        dconf = config["display"]
        self._display_enabled =  utils.dehumanize(dconf["enabled"])

        if self._display_enabled:
            self.display = EPaper(dconf)
            if not skip_splash_screen:
                self.display.draw_splash_screen()
            self.log.info("Display initialized")

        self._value = dict()

        self.log.info("PiPlant initialized: fetching data every {} seconds".format(
            self._poll_interval_seconds))

    def get_value(self):
        self.log.info("Fetching data...")

        soil_moisture_data = dict()
        for sensor in self.soil_moisture_sensors:
            soil_moisture_data[sensor.adc_channel] = sensor.value

        sensorhub_data = dict(self.sensorhub)
        boardstats_data = dict(self.boardstats)

        data_payload = {
            "soil_moisture": soil_moisture_data,
            "environment": sensorhub_data,
            "device": boardstats_data,
        }
        self.log.info("Fetch finished")

        return data_payload

    def process(self, data):
        self.log.info("Processing data...")

        data = self._value
        env_data = data["environment"]

        self.lifxmanager.process_sensor_data(env_data)
        self._process_time = time.time()

        # save to db
        # print(data)
        self.log.info("Processing finished")
        return None

    def render(self,):
        now = time.time()
        # if time to render
        if math.ceil(now - self._render_time) >= self._render_interval_seconds:
            self.log.info("Rendering data...")
            data = self._value

            if self._display_enabled:
                self.display.draw_data(data)
                self.display.sleep()

            self.log.info("Rendering finished")
            self._render_time = time.time()

    def poll_pause(self):
        seconds = self._poll_interval_seconds
        self.log.debug("Pausing for {} seconds...".format(seconds))
        time.sleep(seconds)


if __name__ == '__main__':
    cfg_path = os.path.join(cwd, 'config.yaml')
    with open(cfg_path, "r") as fs:
        config = yaml.safe_load(fs)
        ppm = PiPlant(config)

        while True:
            data = ppm.value
            ppm.process(data)
            ppm.render()
            ppm.poll_pause()
