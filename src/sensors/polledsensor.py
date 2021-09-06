import math
import time
import logging
from datetime import datetime
from gpiozero import GPIOZeroError, GPIOZeroWarning


class PolledSensor:
    POLL_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, poll_interval=1):
        self._receive_time = 0
        self._poll_interval = poll_interval

        self._value = None

        if self.sensor_id == None:
            self.sensor_id = "Generic Sensor #0"

        self.log = logging.getLogger(self.sensor_id)

    @property
    def value(self):
        if not self._is_stale_data():
            return self._value

        try:
            data = self.getValue()
            self._value = data
            self._receive_time = math.ceil(time.time())
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

    def _is_stale_data(self):
        self.log.debug("Checking for stale data")

        if self._value == None:
            self.log.debug("No previous data received")
            return True

        epoch_time = math.ceil(time.time())
        receive_time_dtfmt = datetime.fromtimestamp(
            self._receive_time).strftime(self.POLL_TIME_FORMAT)
        self.log.debug("Last receive time is {}".format(receive_time_dtfmt))
        data_age = time.time() - self._receive_time
        is_stale = epoch_time - self._receive_time > self._poll_interval
        self.log.debug(
            "Data age is {} seconds; stale: {}".format(data_age, is_stale))

        return is_stale
