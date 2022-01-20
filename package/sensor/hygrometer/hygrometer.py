from core.sensor_manager.sensor import Sensor


class Hygrometer(Sensor):
    def __init__(self, dry_value_percentage=50, **kwargs):
        self.type = "hygrometer"
        self._dry_value_percentage = dry_value_percentage
        super().__init__()

    def get_data(self) -> dict:
        return self.moisture_percentage

    @property
    def moisture_percentage(self) -> int:
        """Returns the soil moisture as a percentage of 100"""
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.moisture_percentage.__name__
            )
        )

    @property
    def is_dry(self) -> bool:
        """Returns a boolean on whether the plant is dry based on the target plant water threshold percentage"""
        return self.moisture_percentage <= self.dry_value_percentage

    @property
    def dry_value_percentage(self) -> int:
        """Returns the point at which soil is considered dry as a percentage of the highest moisture value"""
        return self._dry_value_percentage
