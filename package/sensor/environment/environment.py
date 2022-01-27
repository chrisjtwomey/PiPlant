from core.sensor_manager.sensor import Sensor


class TemperatureSensor(Sensor):
    def __init__(self, name):
        type = "temperature"
        super().__init__(name, type)

    def get_data(self) -> dict:
        return self.temperature

    @property
    def temperature(self) -> int:
        """Returns the temperature (degrees celsius) as an integer"""
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.temperature.__name__
            )
        )


class BrightnessSensor(Sensor):
    def __init__(self, name):
        type = "brightness"
        super().__init__(name, type)

    def get_data(self) -> dict:
        return self.brightness

    @property
    def brightness(self) -> int:
        """Returns the brightness (lux) as an integer"""
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.brightness.__name__
            )
        )


class HumiditySensor(Sensor):
    def __init__(self, name):
        type = "humidity"
        super().__init__(name, type)

    def get_data(self) -> dict:
        return self.humidity

    @property
    def humidity(self) -> int:
        """Returns the humidity as a percentage integer"""
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.humidity.__name__
            )
        )


class PressureSensor(Sensor):
    def __init__(self, name):
        type = "pressure"
        super().__init__(name, type)

    def get_data(self) -> dict:
        return self.pressure

    @property
    def pressure(self) -> int:
        """Returns the air pressure (hPa) as an integer"""
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.pressure.__name__
            )
        )


class MotionSensor(Sensor):
    def __init__(self, name):
        type = "motion"
        super().__init__(name, type)

    def get_data(self) -> dict:
        return self.motion

    @property
    def motion(self) -> bool:
        """Returns a boolean on whether motion was detected"""
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.motion.__name__
            )
        )


class SensorHub(
    TemperatureSensor, BrightnessSensor, HumiditySensor, PressureSensor, MotionSensor
):
    def __init__(self, name):
        type = "sensorhub"
        Sensor.__init__(self, name, type)

    def get_data(self) -> dict:
        return {
            "temperature": self.temperature,
            "pressure": self.pressure,
            "humidity": self.humidity,
            "brightness": self.brightness,
            "motion": self.motion,
        }
