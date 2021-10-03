from gpiozero import MCP3008
from .sensor import Sensor
from .profile import PROFILE_DEFAULT, PlantCareProfile

class SoilMoistureSensor(Sensor):
    ADC_MAX_VOLTAGE = 3.3

    # TODO: profiles for different plants
    def __init__(self, adc_channel, calibrated_min_value=0.35, calibrated_max_value=0.75, profile=PROFILE_DEFAULT):
        self.sensor_id = "Soil Moisture Sensor #{}".format(adc_channel)
        self._adc = MCP3008(channel=adc_channel,
                            max_voltage=self.ADC_MAX_VOLTAGE)
        self._adc_channel = adc_channel
        self._calibrated_min_value = calibrated_min_value
        self._calibrated_max_value = calibrated_max_value

        self._plant_profile = PlantCareProfile(profile)

        super().__init__()
        self.log.debug("Initialized")

    def get_value(self):
        val = self._adc.value
        min = self._calibrated_min_value
        max = self._calibrated_max_value
        val = clamp(val, min, max)
        perc_of_max_in_range = 100 - round(perc_in_range(val, min, max))

        data = {
            "value": perc_of_max_in_range,
            "needs_water": self._plant_profile.needs_water(perc_of_max_in_range),
            "needs_water_threshold_percent": self._plant_profile.needs_water_threshold_percent,
            "error": not self.in_range,
            "icon": self._plant_profile.icon
        }
        return data
            
    @property
    def disconnected(self):
        return self._adc.value <= 0.01

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