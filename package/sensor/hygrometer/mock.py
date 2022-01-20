import random
from .hygrometer import Hygrometer


class MockHygrometer(Hygrometer):
    def __init__(self, **kwargs):
        self.adc_channel = kwargs["adc_channel"]
        self.name = kwargs["name"]
        dry_value_percentage = random.randrange(25, 50)

        super().__init__(dry_value_percentage)

    @property
    def moisture_percentage(self) -> int:
        return random.randrange(0, 100)
