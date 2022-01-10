import logging


class Sensor:
    def __init__(self):
        if not hasattr(self, "sensor_id") or self.sensor_id == None:
            self.sensor_id = self.__class__.__name__

        self._data = dict()
        self.log = logging.getLogger(self.sensor_id)

    def get_data(self) -> dict:
        pass

    @property
    def data(self):
        try:
            data = self.get_data()
            # data["time"] = time.time()

            self._data = data
        except Exception as e:
            self.log.error("An exception error has occurred")
            self.log.exception(e)

        return self._data
