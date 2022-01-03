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
        self.sensor_id = "Device Statistics"
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

        data["cpu_temp"] = self._cpu.temperature
        data["cpu_throttle"] = self._cpu.temperature >= self.CPU_THROTTLE_DEGC
        data["cpu_usage_perc"] = psutil.cpu_percent()
        data["gpu_temp"] = self._get_gpu_temp()
        data["mem_usage_perc"] = self._mem.usage
        data["mem_total_mb"] = self._mem.capacity
        data["disk_usage_perc"] = round(self._disk.usage, 1)
        data["disk_total_mb"] = kb_to_mb(psutil.disk_usage("/").total)
        # data["load_avg"] = self._load.load_average

        return data

    @property
    def cpu_temperature(self):
        return self.value["cpu_temp"]

    @property
    def cpu_throttle(self):
        return self.value["cpu_throttle"]

    @property
    def cpu_usage_perc(self):
        return self.value["cpu_usage_perc"]

    @property
    def gpu_temperature(self):
        return self.value["gpu_temp"]

    @property
    def memory_usage_perc(self):
        return self.value["mem_usage_perc"]

    @property
    def memory_total_mb(self):
        return self.value["mem_total_mb"]

    @property
    def disk_usage_perc(self):
        return self.value["disk_usage_perc"]

    @property
    def disk_total_mb(self):
        return self.value["disk_total_mb"]

    @property
    def load_avg(self):
        return self.value["load_avg"]

    def _get_gpu_temp(self):
        res = os.popen("/opt/vc/bin/vcgencmd measure_temp").readline()
        res = res.replace("temp=", "")
        res = res.replace("'C\n", "")

        return float(res)

    def __iter__(self):
        yield "cpu_temp", self.cpu_temperature
        yield "cpu_throttle", self.cpu_throttle
        yield "cpu_usage_perc", self.cpu_usage_perc
        yield "gpu_temp", self.gpu_temperature
        yield "mem_usage_perc", self.memory_usage_perc
        yield "mem_total_mb", self.memory_total_mb
        yield "disk_usage_perc", self.disk_usage_perc
        yield "disk_total_mb", self.disk_total_mb
        # yield 'load_avg',         self.load_avg


class MemoryUsage:
    @property
    def usage(self):
        mem = psutil.virtual_memory()
        return mem.percent

    @property
    def capacity(self):
        mem = psutil.virtual_memory()
        return kb_to_mb(mem.total)


def kb_to_mb(kb):
    return round(kb / 1024.0 / 1024.0, 1)
