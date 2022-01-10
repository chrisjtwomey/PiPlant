from sensor.sensor import Sensor


class TemperatureSensor(Sensor):
    def __init__(self, **kwargs):
        super().__init__()

    def get_data(self) -> dict:
        return {
            "temperature": self.temperature,
        }

    @property
    def temperature(self) -> int:
        """Returns the temperature (degrees celsius) as an integer"""
        pass


class BrightnessSensor(Sensor):
    def __init__(self, **kwargs):
        super().__init__()

    def get_data(self) -> dict:
        return {
            "brightness": self.brightness,
        }

    @property
    def brightness(self) -> int:
        """Returns the brightness (lux) as an integer"""
        pass


class HumiditySensor(Sensor):
    def __init__(self, **kwargs):
        super().__init__()

    def get_data(self) -> dict:
        return {
            "humidity": self.humidity,
        }

    @property
    def humidity(self) -> int:
        """Returns the humidity as a percentage integer"""
        pass


class PressureSensor(Sensor):
    def __init__(self, **kwargs):
        super().__init__()

    def get_data(self) -> dict:
        return {"pressure": self.pressure}

    @property
    def pressure(self) -> int:
        """Returns the air pressure (hPa) as an integer"""
        pass


class MotionSensor(Sensor):
    def __init__(self, **kwargs):
        super().__init__()

    def get_data(self) -> dict:
        return {"motion": self.motion}

    @property
    def motion(self) -> bool:
        """Returns a boolean on whether motion was detected"""
        pass


class EnvironmentAll(
    TemperatureSensor, BrightnessSensor, HumiditySensor, PressureSensor, MotionSensor
):
    def __init__(self, **kwargs):
        super().__init__()

    def get_data(self) -> dict:
        return {
            "temperature": self.temperature,
            "pressure": self.pressure,
            "humidity": self.humidity,
            "brightness": self.brightness,
            "motion": self.motion,
        }
