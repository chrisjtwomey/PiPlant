import random
from sensors.environment.environment import (
    TemperatureSensor,
    BrightnessSensor,
    HumiditySensor,
    PressureSensor,
    MotionSensor,
)


class SensorHub(
    TemperatureSensor, BrightnessSensor, HumiditySensor, PressureSensor, MotionSensor
):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_data(self) -> dict:
        return {
            "temperature": self.temperature,
            "pressure": self.pressure,
            "humidity": self.humidity,
            "brightness": self.brightness,
            "motion": self.motion,
        }

    @property
    def temperature(self) -> int:
        return random.randrange(-30, 127)

    @property
    def brightness(self) -> int:
        return random.randrange(0, 100)

    @property
    def humidity(self) -> int:
        return random.randrange(0, 100)

    @property
    def pressure(self) -> int:
        return random.randrange(300, 1100)

    @property
    def motion(self) -> bool:
        return random.choice([False, True])