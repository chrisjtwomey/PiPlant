from sensor.sensor import Sensor


class DeviceSensor(Sensor):
    def __init__(self, **kwargs):
        super().__init__()

    def get_data(self) -> dict:
        return {
            "cpu_temperature": self.cpu_temperature,
            "gpu_temperature": self.gpu_temperature,
            "cpu_throttle": self.cpu_throttle,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "memory_total": self.memory_total,
            "disk_usage": self.disk_usage,
            "disk_total": self.disk_total,
        }

    @property
    def cpu_temperature(self) -> int:
        """Returns the CPU temperature (degrees celsius) as an integer"""
        pass

    @property
    def gpu_temperature(self) -> int:
        """Returns the GPU temperature (degrees celsius) as an integer"""
        pass

    @property
    def cpu_throttle(self) -> bool:
        """Returns a boolean on whether the CPU is thermal throttling"""
        pass

    @property
    def cpu_usage(self) -> int:
        """Returns the CPU usage as an percentage integer"""
        pass

    @property
    def memory_usage(self) -> int:
        """Returns the memory usage megabytes as an integer"""
        pass

    @property
    def memory_total(self) -> int:
        """Returns the total megabytes of memory as an integer"""
        pass

    @property
    def disk_usage(self) -> int:
        """Returns the disk usage megabytes as an integer"""
        pass

    @property
    def disk_total(self) -> int:
        """Returns the total megabytes of disk as an integer"""
        pass
