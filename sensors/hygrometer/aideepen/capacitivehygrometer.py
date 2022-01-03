from gpiozero import MCP3008
from ..hygrometer import Hygrometer


class CapacitiveHygrometer(Hygrometer):
    ADC_MAX_VOLTAGE = 3.3

    def __init__(
        self, adc_channel=0, min_value=0.25, max_value=0.8, dry_value_percentage=0.50
    ):
        self.sensor_id = "Hygrometer #{}".format(adc_channel)
        self._adc_channel = adc_channel
        self._min_value = min_value
        self._max_value = max_value

        self._adc = MCP3008(channel=self._adc_channel, max_voltage=self.ADC_MAX_VOLTAGE)

        super().__init__(dry_value_percentage)

    @property
    def percentage(self) -> int:
        def perc_in_range(val, min, max):
            return ((val - min) * 100) / (max - min)

        def clamp(val, smallest, largest):
            return max(smallest, min(val, largest))

        val = self._adc.value
        min = self._calibrated_min_value
        max = self._calibrated_max_value
        val = clamp(val, min, max)
        perc_of_max_in_range = 100 - round(perc_in_range(val, min, max))

        return perc_of_max_in_range

    @property
    def adc_channel(self):
        return self._adc_channel