import os
import psutil
from ..device import DeviceSensor
from gpiozero import CPUTemperature, LoadAverage, DiskUsage


class DeviceStatistics(DeviceSensor):
    MIN_CPU_DEGC = 0
    CPU_THROTTLE_DEGC = 82
    CPU_TEMP_LIMIT = 85
    MAX_CPU_DEGC = 100
    MIN_LOAD_AVG = 0
    MAX_LOAD_AVG = 2

    def __init__(self):
        self._cpu = CPUTemperature(
            min_temp=self.MIN_CPU_DEGC, max_temp=self.MAX_CPU_DEGC
        )
        self._mem = MemoryUsage()
        self._disk = DiskUsage()
        self._load = LoadAverage(
            min_load_average=self.MIN_LOAD_AVG, max_load_average=self.MAX_LOAD_AVG
        )

        super().__init__()
        self._value = dict()
        self.log.debug("Initialized")

    def get_data(self) -> dict:
        data = dict()

        data["cpu_temperature"] = self._cpu.temperature
        data["cpu_throttle"] = self._cpu.temperature >= self.CPU_THROTTLE_DEGC
        data["cpu_usage"] = psutil.cpu_percent()
        data["gpu_temperature"] = self._get_gpu_temp()
        data["memory_usage"] = self._mem.usage
        data["memory_total"] = self._mem.capacity
        data["disk_usage"] = round(self._disk.usage, 1)
        data["disk_total"] = kb_to_mb(psutil.disk_usage("/").total)
        # data["load_avg"] = self._load.load_average

        return data

    @property
    def cpu_temperature(self):
        return self.value["cpu_temperature"]

    @property
    def cpu_throttle(self):
        return self.value["cpu_throttle"]

    @property
    def cpu_usage(self):
        return self.value["cpu_usage"]

    @property
    def gpu_temperature(self):
        return self.value["gpu_temperature"]

    @property
    def memory_usage(self):
        return self.value["memory_usage"]

    @property
    def memory_total(self):
        return self.value["memory_total"]

    @property
    def disk_usage(self):
        return self.value["disk_usage"]

    @property
    def disk_total(self):
        return self.value["disk_total"]

    @property
    def load_avg(self):
        return self.value["load_avg"]

    def _get_gpu_temp(self):
        res = os.popen("/opt/vc/bin/vcgencmd measure_temp").readline()
        res = res.replace("temp=", "")
        res = res.replace("'C\n", "")

        return float(res)

    def __iter__(self):
        yield "cpu_temperature", self.cpu_temperature
        yield "cpu_throttle", self.cpu_throttle
        yield "cpu_usage", self.cpu_usage
        yield "gpu_temperature", self.gpu_temperature
        yield "memory_usage", self.memory_usage
        yield "memory_total", self.memory_total
        yield "disk_usage", self.disk_usage
        yield "disk_total", self.disk_total
        # yield 'load_avg',         self.load_avg


class MemoryUsage:
    @property
    def usage(self):
        mem = psutil.virtual_memory()
        return kb_to_mb(mem.used)

    @property
    def capacity(self):
        mem = psutil.virtual_memory()
        return kb_to_mb(mem.total)


def kb_to_mb(kb):
    return round(kb / 1024.0 / 1024.0, 1)
