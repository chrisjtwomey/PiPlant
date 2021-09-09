from gpiozero import MCP3008
from .polledsensor import PolledSensor


class SoilMoistureSensor(PolledSensor):
    ADC_MAX_VOLTAGE = 3.3

    def __init__(self, adc_channel=0, poll_interval=1):
        self.sensor_id = "Soil Moisture Sensor #{}".format(adc_channel)
        self._adc = MCP3008(channel=adc_channel,
                            max_voltage=self.ADC_MAX_VOLTAGE)
        self._adc_channel = adc_channel
        super().__init__(poll_interval=poll_interval)
        self.log.debug(
            "Initialized")

    def getValue(self):
        return self._adc.value

    @property
    def adc_channel(self):
        return self._adc_channel
