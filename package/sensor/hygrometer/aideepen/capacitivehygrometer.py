from gpiozero import MCP3008
from ..hygrometer import Hygrometer


class CapacitiveHygrometer(Hygrometer):
    ADC_MAX_VOLTAGE = 3.3

    def __init__(
        self,
        name=None,
        adc_channel=0,
        min_value=0.25,
        max_value=0.8,
        dry_value_percentage=0.50,
    ):
        if name is None:
            self.name = "Hygrometer #" + str(adc_channel)
        self.name = name

        self._adc_channel = adc_channel
        self._min_value = min_value
        self._max_value = max_value

        self._adc = MCP3008(channel=self._adc_channel, max_voltage=self.ADC_MAX_VOLTAGE)

        super().__init__(dry_value_percentage)

    @property
    def moisture_percentage(self) -> int:
        def perc_in_range(val, min, max):
            return ((val - min) * 100) / (max - min)

        def clamp(val, smallest, largest):
            return max(smallest, min(val, largest))

        val = clamp(self._adc.value, self._min_value, self._max_value)
        perc_of_max_in_range = 100 - round(
            perc_in_range(val, self._min_value, self._max_value)
        )

        return perc_of_max_in_range

    @property
    def adc_channel(self):
        return self._adc_channel
