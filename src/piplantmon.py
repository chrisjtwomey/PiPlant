from display.epaper import EPaperDisplay
from sensors.polledsensor import PolledSensor
from sensors.boardstats import BoardStats
from sensors.sensorhub import SensorHub
from sensors.soilmoisture import SoilMoistureSensor

class PiPlantMon(PolledSensor):

    def __init__(self, poll_interval=1):
        self.sensor_id = "PiPlantMon"
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
            "sensorhub": sensorhub_data,
            "boardstats": boardstats_data,
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