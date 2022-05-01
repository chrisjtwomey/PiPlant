import gpiozero
from ..environment import MotionSensor


class PIR(MotionSensor):
    def __init__(self, pin=4):
        name = "PIR"

        self.pir = gpiozero.MotionSensor(pin)
        super().__init__(name)

    @property
    def motion(self) -> bool:
        return self.pir.motion_detected
