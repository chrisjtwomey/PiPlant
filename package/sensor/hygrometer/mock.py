import random
from .hygrometer import Hygrometer


class MockHygrometer(Hygrometer):
    def __init__(self, **kwargs):
        self.adc_channel = kwargs["adc_channel"]
        dry_value_percentage = random.randrange(25, 50)

        super().__init__(dry_value_percentage)

    @property
    def percentage(self) -> int:
        return random.randrange(0, 100)
