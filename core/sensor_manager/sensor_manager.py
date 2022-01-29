import logging
from .sensor import Sensor
from package.sensor.environment.environment import *
from package.sensor.device.device import DeviceSensor
from package.sensor.hygrometer.hygrometer import Hygrometer


class SensorManager:
    def __init__(self, sensors, database_manager):
        self.log = logging.getLogger(self.__class__.__name__)
        self._sensors = sensors
        self._db = database_manager

        self.log.info("Initialized")
        self.log.debug(self.sensors)

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

    def get_hygrometers(self) -> list[Sensor]:
        return self._get_sensors_by_class(Hygrometer)

    def get_temperature_sensors(self) -> list[Sensor]:
        return self._get_sensors_by_class(TemperatureSensor)

    def get_humidity_sensors(self) -> list[Sensor]:
        return self._get_sensors_by_class(HumiditySensor)

    def get_pressure_sensors(self) -> list[Sensor]:
        return self._get_sensors_by_class(PressureSensor)

    def get_brightness_sensors(self) -> list[Sensor]:
        return self._get_sensors_by_class(BrightnessSensor)

    def get_motion_sensors(self) -> list[Sensor]:
        return self._get_sensors_by_class(MotionSensor)

    def get_device_sensors(self) -> list[Sensor]:
        return self._get_sensors_by_class(DeviceSensor)

    def _get_sensors_by_class(self, class_) -> list[Sensor]:
        sensors = []

        for sensor in self.sensors:
            if not isinstance(sensor, class_):
                continue

            sensors.append(sensor)

        return sensors
