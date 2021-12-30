import random
from ...sensor import Sensor

class HygrometerMock(Sensor):
    def __init__(self, kwargs):
        self.adc_channel = kwargs["adc_channel"]
        pass

    def get_value(self):
        water_threshold_perc = random.randrange(10, 60)
        value = random.randrange(0, 100)
        needs_water = value <= water_threshold_perc

        return {
            "value": value,
            "needs_water": needs_water,
            "needs_water_threshold_percent": water_threshold_perc,
            "error": random.randrange(False, True),
            "icon": random.choice(['fukien_tea.png', 'ficus.png', 'china_doll.png', 'palm.png', 'succulent.png'])
        }