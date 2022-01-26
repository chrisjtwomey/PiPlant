from .sensor import Sensor


class SensorManager:
    SENSOR_TYPE_HYGROMETER = "hygrometer"
    SENSOR_TYPE_ENVIRONMENT = "environment"
    SENSOR_TYPE_DEVICE = "device"

    def __init__(self, sensors, database_manager):
        self._sensors = sensors
        self._db = database_manager

    @property
    def sensors(self) -> list[Sensor]:
        return self._sensors

    def run(self):
        sensors_data = []

        for sensor in self.sensors:
            data = sensor.data
            dataval = data["value"]
            if isinstance(dataval, dict):
                for valuetype, value in dataval.items():
                    extradata = data.copy()
                    extradata["type"] = valuetype
                    extradata["value"] = value

                    sensors_data.append(extradata)
            else:
                sensors_data.append(data)

        self._db.insert_sensors(sensors_data)

    def get_sensors_by_type(self, type) -> list[Sensor]:
        sensors = []

        for sensor in self.sensors:
            if sensor.type != type:
                continue

            sensors.append(sensor)
