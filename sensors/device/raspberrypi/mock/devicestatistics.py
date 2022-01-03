import random
from ...device import DeviceSensor


class DeviceStatistics(DeviceSensor):
    def __init__(self, **kwargs):
        super().__init__()

    @property
    def cpu_temperature(self):
        return random.randrange(0, 100)

    @property
    def cpu_throttle(self):
        return random.choice([False, True])

    @property
    def cpu_usage_perc(self):
        return random.randrange(0, 100)

    @property
    def gpu_temperature(self):
        return random.randrange(0, 100)

    @property
    def memory_usage_perc(self):
        return random.randrange(0, 100)

    @property
    def memory_total_mb(self):
        return 8192

    @property
    def disk_usage_perc(self):
        return random.randrange(0, 100)

    @property
    def disk_total_mb(self):
        return 1024

    @property
    def load_avg(self):
        return random.randrange(0.01, 1.00)
