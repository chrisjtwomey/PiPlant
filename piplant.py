import os
import time
import logging.config
from display.epaper import EPaper
from sensors.polledsensor import PolledSensor
from sensors.devicestatistics import DeviceStatistics
from sensors.sensorhub import SensorHub
from sensors.soilmoisture import SoilMoistureSensor
from sensors.profile import *

cwd = os.path.dirname(os.path.realpath(__file__))
logging.config.fileConfig(os.path.join(cwd, 'cfg', 'logging.dev.ini'))


class PiPlant(PolledSensor):

    def __init__(self, poll_interval=4):
        super().__init__(poll_interval=poll_interval)

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

        skip_splash_screen = True

        self.log.info("Initializing sensors...")

        self.soil_moisture_sensors = [
            SoilMoistureSensor(adc_channel=0, calibrated_max_value=0.68, profile=PROFILE_CHINA_DOLL_BONSAI),
            SoilMoistureSensor(adc_channel=1, calibrated_max_value=0.70, profile=PROFILE_FUKIEN_TEA_BONSAI),
            SoilMoistureSensor(adc_channel=2, calibrated_max_value=0.67, profile=PROFILE_PALM),
            SoilMoistureSensor(adc_channel=3, calibrated_max_value=0.69, profile=PROFILE_FICUS),
            SoilMoistureSensor(adc_channel=4, calibrated_max_value=0.69, profile=PROFILE_SUCCULENT),
        ]
        self.sensorhub = SensorHub()
        self.boardstats = DeviceStatistics()

        self.log.info("Sensors initialized")
        self.log.info("Initializing display...")

        self.display = EPaper()
        if not skip_splash_screen:
            self.display.draw_splash_screen()

        self.log.info("Display initialized")

        self._value = dict()
        self.log.info("PiPlant initialized: fetching data every {} seconds".format(poll_interval))

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

    def process(self):
        self.log.info("Processing data...")
        data = self._value
        # save to db
        # print(data)
        self.log.info("Processing finished")
        return None

    def render(self,):
        self.log.info("Rendering data...")
        data = self._value
        self.display.draw_data(data)
        self.log.info("Rendering finished")
        self.display.sleep()

    def pause(self, seconds):
        self.log.debug("Pausing for {} seconds...".format(seconds))
        time.sleep(seconds)


if __name__ == '__main__':
    poll_interval = 5
    ppm = PiPlant(poll_interval)
    
    # while True:
    #     ppm.value
    #     ppm.process()
    #     ppm.render()
    #     ppm.pause(poll_interval)
    ppm.value
    ppm.process()
    ppm.render()
