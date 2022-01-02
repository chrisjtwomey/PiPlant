import os
import yaml
import math
import time
import logging.config
import util.utils as utils
from util.package import DynamicPackage
from epaper.epaper import EPaper
from sensors.polledsensor import PolledSensor
from light.lifxschedulemanager import LIFXScheduleManager
from light.lifxlivebodydetection import LIFXLiveBodyDetection

cwd = os.path.dirname(os.path.realpath(__file__))


class PiPlant(PolledSensor):
    def __init__(self, config):
        piplantconf = config["piplant"]

        self.debug = (
            utils.dehumanize(piplantconf["debug"]) if "debug" in piplantconf else False
        )

        logging_cfg_path = os.path.join(cwd, "logging.ini")
        if self.debug:
            logging_cfg_path = os.path.join(cwd, "logging.dev.ini")

        logging.config.fileConfig(logging_cfg_path)

        self._poll_interval_seconds = utils.dehumanize(piplantconf["poll_interval"])
        dconf = config["epaper"]
        self._render_interval_seconds = utils.dehumanize(dconf["refresh_interval"])
        self._process_time = 0
        self._render_time = 0

        super().__init__(self._poll_interval_seconds)

        self.log.info(
            r"""\
            
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
        """
        )

        if self.debug:
            self.log.info("DEBUG MODE")

        # sensors
        self.log.info("Initializing sensors...")

        def init_sensors(sensors_config):
            sensors = []

            for config in sensors_config:
                package = config["package"]
                sensor = DynamicPackage(package)
                sensors.append(sensor)

            return sensors

        def init_env_sensors(env_config):
            sensors = dict()

            if "temperature" in env_config:
                package = env_config["temperature"]["package"]
                sensors["temperature"] = DynamicPackage(package)

            if "humidity" in env_config:
                package = env_config["humidity"]["package"]
                sensors["humidity"] = DynamicPackage(package)

            if "pressure" in env_config:
                package = env_config["pressure"]["package"]
                sensors["pressure"] = DynamicPackage(package)

            if "brightness" in env_config:
                package = env_config["brightness"]["package"]
                sensors["brightness"] = DynamicPackage(package)

            return sensors

        sensorsconfig = piplantconf["sensors"]

        hygrometers_config = (
            sensorsconfig["hygrometers"] if "hygrometers" in sensorsconfig else []
        )
        self.hygrometers = init_sensors(hygrometers_config)

        environment_config = (
            sensorsconfig["environment"] if "environment" in sensorsconfig else dict()
        )
        self.environment_sensors = init_env_sensors(environment_config)

        device_config = sensorsconfig["device"] if "device" in sensorsconfig else []
        self.device_sensors = init_sensors(device_config)

        self.log.info("Sensors initialized")

        # processors
        self.log.info("Initializing processors...")
        # TODO: check type of manager
        lmconf = config["lightmanager"]
        self.schedulemanager = LIFXScheduleManager(lmconf, debug=self.debug)
        self.livebodydetection = LIFXLiveBodyDetection(lmconf, debug=self.debug)
        self.log.info("Processors initialized")

        # renderers
        self.log.info("Initializing display...")
        dconf = config["epaper"]
        self._display_enabled = utils.dehumanize(dconf["enabled"])

        if self._display_enabled:
            driver = dconf["driver"]
            package = driver["package"]
            skip_splash_screen = (
                utils.dehumanize(dconf["skip_splash_screen"])
                if "skip_splash_screen" in dconf
                else False
            )
            epd = DynamicPackage(package)
            self.display = EPaper(epd, dconf, debug=self.debug)
            if not skip_splash_screen:
                self.display.draw_splash_screen()
            self.log.info("Display initialized")

        self._value = dict()

        self.log.info(
            "PiPlant initialized: fetching data every {} seconds".format(
                self._poll_interval_seconds
            )
        )

    def get_value(self):
        self.log.info("Fetching...")

        hygrometer_data = []
        for sensor in self.hygrometers:
            hygrometer_data.append(sensor.data)

        environment_data = dict()
        for sensortype, sensor in self.environment_sensors.items():
            environment_data[sensortype] = sensor.data[sensortype]

        device_data = []
        for sensor in self.device_sensors:
            device_data.append(sensor.data)

        data_payload = {
            "hygrometer": hygrometer_data,
            "environment": environment_data,
            "device": device_data,
        }

        return data_payload

    def process(self, data):
        self.log.info("Processing...")

        _ = self._value
        
        self.schedulemanager.process()
        self.livebodydetection.process()
        self._process_time = time.time()

        # save to db
        # print(data)
        return None

    def render(
        self,
    ):
        now = time.time()
        # if time to render
        if math.ceil(now - self._render_time) >= self._render_interval_seconds:
            self.log.info("Rendering...")
            data = self._value

            if self._display_enabled:
                self.display.draw_data(data)
                self.display.sleep()

            self._render_time = time.time()

    def poll_pause(self):
        seconds = self._poll_interval_seconds
        self.log.debug("Pausing for {} seconds...".format(seconds))
        time.sleep(seconds)


if __name__ == "__main__":
    cfg_path = os.path.join(cwd, "config.yaml")
    with open(cfg_path, "r") as fs:
        config = yaml.safe_load(fs)
        ppm = PiPlant(config)

        while True:
            data = ppm.value
            ppm.process(data)
            ppm.render()
            ppm.poll_pause()
