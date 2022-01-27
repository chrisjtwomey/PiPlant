import random
from .hygrometer import Hygrometer


class MockHygrometer(Hygrometer):
    def __init__(self, **kwargs):
        name = kwargs["name"] or "MockHygrometer"
        dry_value_percentage = random.randrange(25, 50)

        super().__init__(name, dry_value_percentage)

    @property
    def moisture_percentage(self) -> int:
        return random.randrange(0, 100)
