import time
import logging
import uuid


class Sensor:
    def __init__(self):
        if not hasattr(self, "name") or self.name == None:
            self.name = self.__class__.__name__

        self.id = uuid.uuid4()
        self.type = "generic"

        self._data = dict()
        self.log = logging.getLogger(str(self.name))

    def get_data(self) -> dict:
        pass

    @property
    def data(self):
        try:
            data = dict()
            value = self.get_data()
            data["id"] = str(self.id)
            data["name"] = self.name
            data["value"] = value
            data["type"] = self.type
            data["time"] = int(time.time())

            self._data = data
        except Exception as e:
            self.log.error("An exception error has occurred")
            self.log.exception(e)

        return self._data
