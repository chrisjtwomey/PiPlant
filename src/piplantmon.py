import sys
import time
import logging.config
from display.epaper import EPaperDisplay
from sensors.polledsensor import PolledSensor
from sensors.boardstats import BoardStats
from sensors.sensorhub import SensorHub
from sensors.soilmoisture import SoilMoistureSensor

logging.config.fileConfig('./logging.ini')

class PiPlantMon(PolledSensor):

    def __init__(self, poll_interval=1):
        self.sensor_id = "PiPlant"
        self.soil_moisture_sensors = [
            SoilMoistureSensor(adc_channel=0, poll_interval=poll_interval),
            SoilMoistureSensor(adc_channel=1, poll_interval=poll_interval),
            SoilMoistureSensor(adc_channel=2, poll_interval=poll_interval),
            SoilMoistureSensor(adc_channel=3, poll_interval=poll_interval),
            SoilMoistureSensor(adc_channel=4, poll_interval=poll_interval),
        ]
        self.sensorhub = SensorHub(poll_interval=poll_interval)
        self.boardstats = BoardStats(poll_interval=poll_interval)

        self.display = EPaperDisplay()
        self.display.drawLogo(self.sensor_id)
        self.sleep(5)
        self.display.flush()
        sys.exit(0)

        super().__init__(poll_interval=poll_interval)
        self._value = dict()
        self.log.info("###########################")
        self.log.info("# PiPlantMon")
        self.log.info("###########################")
        self.log.info("Initialized PiPlantMon - polling for new data every {} seconds".format(poll_interval))

    def run(self):
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
        self.display.drawData(data)

    def sleep(self, seconds):
        time.sleep(seconds)

if __name__ == '__main__':
    ppm = PiPlantMon(poll_interval=5)
    while True:
        ppm.run()

        ppm.sleep(1)