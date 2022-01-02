import random
import random
from ....sensor import Sensor


class DeviceStatistics(Sensor):
    def __init__(self, **kwargs):
        super().__init__()

    def get_value(self):
        pass

    def __iter__(self):
        yield "cpu_temp", random.randrange(0, 100)
        yield "cpu_throttle", random.randrange(False, True)
        yield "cpu_usage_perc", random.randrange(0, 100)
        yield "gpu_temp", random.randrange(0, 100)
        yield "mem_usage_perc", random.randrange(0, 100)
        yield "mem_total_mb", 1024
        yield "disk_usage_perc", random.randrange(0, 100)
        yield "disk_total_mb", 1024
        # yield 'load_avg',         self.load_avg
