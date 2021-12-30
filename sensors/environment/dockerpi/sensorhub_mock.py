import random
from ...sensor import Sensor

class SensorHubMock(Sensor):
    def __init__(self, kwargs):
        pass

    def get_value(self):
        return dict(self)

    def __iter__(self):
        yield 'ext_temp',           random.randrange(-30, 127),
        yield 'onboard_temp',       random.randrange(0, 100),
        yield 'onboard_brightness', random.randrange(0, 100),
        yield 'onboard_humidity',   random.randrange(0, 100),
        yield 'baro_temp',          random.randrange(0, 25),
        yield 'baro_pressure',      random.randrange(300, 1100),
        yield 'livebody_detection', random.randrange(False, True),