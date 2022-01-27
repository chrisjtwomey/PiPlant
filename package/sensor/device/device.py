from core.sensor_manager.sensor import Sensor


class DeviceSensor(Sensor):
    def __init__(self, name):
        type = "device"
        super().__init__(name, type)

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
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, "cpu_temperature"
            )
        )

    @property
    def gpu_temperature(self) -> int:
        """Returns the GPU temperature (degrees celsius) as an integer"""
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, "gpu_temperature"
            )
        )

    @property
    def cpu_throttle(self) -> bool:
        """Returns a boolean on whether the CPU is thermal throttling"""
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, "cpu_throttle"
            )
        )

    @property
    def cpu_usage(self) -> int:
        """Returns the CPU usage as an percentage integer"""
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, "cpu_usage"
            )
        )

    @property
    def memory_usage(self) -> int:
        """Returns the memory usage megabytes as an integer"""
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, "memory_usage"
            )
        )

    @property
    def memory_total(self) -> int:
        """Returns the total megabytes of memory as an integer"""
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, "memory_total"
            )
        )

    @property
    def disk_usage(self) -> int:
        """Returns the disk usage megabytes as an integer"""
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, "disk_usage"
            )
        )

    @property
    def disk_total(self) -> int:
        """Returns the total megabytes of disk as an integer"""
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, "disk_total"
            )
        )
