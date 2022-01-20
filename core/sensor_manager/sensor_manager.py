from .sensor import Sensor


class SensorManager:
    SENSOR_TYPE_HYGROMETER = "hygrometer"
    SENSOR_TYPE_ENVIRONMENT = "environment"
    SENSOR_TYPE_DEVICE = "device"

    def __init__(self, sensors):
        self._sensors = sensors

    @property
    def sensors(self) -> list[Sensor]:
        return self._sensors

    def run(self):
        pass

    def get_sensors_by_type(self, type) -> list[Sensor]:
        sensors = []

        for sensor in self.sensors:
            if sensor.type != type:
                continue

            sensors.append(sensor)
