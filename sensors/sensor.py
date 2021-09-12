import logging
from gpiozero import GPIOZeroError, GPIOZeroWarning


class Sensor:
    def __init__(self):
        self._value = None

        if not hasattr(self, 'sensor_id') or self.sensor_id == None:
            self.sensor_id = self.__class__.__name__

        self.log = logging.getLogger(self.sensor_id)

    def get_value(self):
        pass

    @property
    def value(self):
        try:
            data = self.get_value()
            self._value = data
        except GPIOZeroWarning as w:
            self.log.error('A GPIO Zero warning occurred')
            self.log.warning(w)
        except GPIOZeroError as e:
            self.log.error('A GPIO Zero error occurred')
            self.log.error(e)
        except Exception as e:
            self.log.error('An generic exception error has occurred')
            self.log.error(e)

        return self._value
