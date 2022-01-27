import random
from .device import DeviceSensor


class MockDeviceStatistics(DeviceSensor):
    def __init__(self):
        name = self.__class__.__name__
        super().__init__(name)

    @property
    def cpu_temperature(self):
        return random.randrange(0, 100)

    @property
    def cpu_throttle(self):
        return random.choice([False, True])

    @property
    def cpu_usage(self):
        return random.randrange(0, 100)

    @property
    def gpu_temperature(self):
        return random.randrange(0, 100)

    @property
    def memory_usage(self):
        return random.randrange(0, self.memory_total)

    @property
    def memory_total(self):
        return 8192

    @property
    def disk_usage(self):
        return random.randrange(0, self.disk_total)

    @property
    def disk_total(self):
        return 1024

    @property
    def load_avg(self):
        return random.randrange(0.01, 1.00)
