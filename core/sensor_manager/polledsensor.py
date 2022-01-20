import math
import time
from datetime import datetime
from .sensor import Sensor


class PolledSensor(Sensor):
    POLL_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, poll_interval=1):
        self._receive_time = 0
        self._poll_interval = poll_interval

        super().__init__()

    @property
    def value(self):
        if self._is_stale_data():
            data = self.get_value()
            self._value = data
            self._receive_time = math.ceil(time.time())

        return self._value

    def _is_stale_data(self):
        self.log.debug("Checking for stale data")

        if self._value == None or self._receive_time == 0:
            self.log.debug("No previous data received")
            return True

        receive_time_dtfmt = datetime.fromtimestamp(self._receive_time).strftime(
            self.POLL_TIME_FORMAT
        )
        self.log.debug("Last receive time is {}".format(receive_time_dtfmt))
        data_age = math.ceil(time.time() - self._receive_time)
        is_stale = data_age >= self._poll_interval
        self.log.debug("Data age is {} seconds; stale: {}".format(data_age, is_stale))

        return is_stale
