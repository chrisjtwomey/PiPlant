import time
import os
import logging.config
from display.epaper import EPaper
from sensors.polledsensor import PolledSensor
from sensors.devicestatistics import DeviceStatistics
from sensors.sensorhub import SensorHub
from sensors.soilmoisture import SoilMoistureSensor

cwd = os.path.dirname(os.path.realpath(__file__))
logging.config.fileConfig(os.path.join(cwd, 'cfg', 'logging.dev.ini'))


class PiPlant(PolledSensor):

    def __init__(self, poll_interval=1):
        super().__init__(poll_interval=poll_interval)

        self.log.info(r"""\
            
                            PiPlant
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

        self.log.info("Initializing sensors...")

        self.soil_moisture_sensors = [
            SoilMoistureSensor(adc_channel=0, poll_interval=poll_interval),
            SoilMoistureSensor(adc_channel=1, poll_interval=poll_interval),
            SoilMoistureSensor(adc_channel=2, poll_interval=poll_interval),
            SoilMoistureSensor(adc_channel=3, poll_interval=poll_interval),
            SoilMoistureSensor(adc_channel=4, poll_interval=poll_interval),
        ]
        self.sensorhub = SensorHub(poll_interval=poll_interval)
        self.boardstats = DeviceStatistics(poll_interval=poll_interval)

        self.display = EPaper()
        self.display.draw_splash_screen(self.sensor_id)
        self.sleep(2)
        self.display.flush()

        self._value = dict()
        self.log.info(
            "Initialized: polling for new data every {} seconds".format(poll_interval))

    def run(self):
        self.log.info("Polling for new data")
        self.getValue()

    def getValue(self):
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

        self.process(data_payload)
        self.render(data_payload)

        return data_payload

    def process(self, data):
        # save to db
        # print(data)
        return None

    def render(self, data):
        self.display.draw_data(data)

    def sleep(self, seconds):
        time.sleep(seconds)


if __name__ == '__main__':
    ppm = PiPlant(poll_interval=5)
    while True:
        ppm.run()
        ppm.sleep(5)
