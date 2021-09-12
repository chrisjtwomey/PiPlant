from gpiozero import MCP3008
from .polledsensor import PolledSensor


class SoilMoistureSensor(PolledSensor):
    ADC_MAX_VOLTAGE = 3.3

    def __init__(self, adc_channel=0, poll_interval=1, water_threshold = 25, calibrated_min_value=0.35, calibrated_max_value=0.75):
        self.sensor_id = "Soil Moisture Sensor #{}".format(adc_channel)
        self._adc = MCP3008(channel=adc_channel,
                            max_voltage=self.ADC_MAX_VOLTAGE)
        self._adc_channel = adc_channel
        self._water_threshold = water_threshold
        self._calibrated_min_value = calibrated_min_value
        self._calibrated_max_value = calibrated_max_value
        super().__init__(poll_interval=poll_interval)
        self.log.debug(
            "Initialized")

    def getValue(self):
        val = self._adc.value
        min = self._calibrated_min_value
        max = self._calibrated_max_value
        val = clamp(val, min, max)

        perc_of_max_in_range = 100 - round(perc_in_range(val, min, max))

        return perc_of_max_in_range

    @property
    def needs_water(self):
        return 0 <= self.value <= self._water_threshold

    @property
    def in_range(self):
        return self._calibrated_min_value <= self._adc.value

    @property
    def adc_channel(self):
        return self._adc_channel


def perc_in_range(val, min, max):
    return ((val - min) * 100) / (max - min)


def clamp(val, smallest, largest):
    return max(smallest, min(val, largest))
