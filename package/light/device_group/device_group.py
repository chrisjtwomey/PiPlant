import time
import util.utils as utils

import logging

class DeviceGroup:
    def __init__(self, name, devices, query_interval="2m"):
        self._group_name = name
        self._query_interval_seconds = utils.dehumanize(query_interval)
        self._devices = devices

        self._power = self.power
        self._hsbk = self.hsbk
        self._query_time = time.time()

        self.log = logging.getLogger("{}.{}".format(self.__class__.__name__, self.name))

    def get_devices(self) -> list:
        raise NotImplementedError("Sub-classes of {} should implement function {}".format(self.__class__.__name__, self.get_devices.__name__))

    def get_power(self) -> list:
        raise NotImplementedError("Sub-classes of {} should implement function {}".format(self.__class__.__name__, self.get_power.__name__))

    def set_power(self, power, transition_seconds=0) -> None:
        raise NotImplementedError("Sub-classes of {} should implement function {}".format(self.__class__.__name__, self.set_power.__name__))

    def get_hsbk(self) -> list:
        raise NotImplementedError("Sub-classes of {} should implement function {}".format(self.__class__.__name__, self.get_hsbk.__name__))

    def set_hsbk(self, hsbk, transition_seconds=0) -> None:
        raise NotImplementedError("Sub-classes of {} should implement function {}".format(self.__class__.__name__, self.set_hsbk.__name__))
    
    @property
    def name(self) -> str:
        return self._group_name

    @property
    def query_time(self) -> int:
        return self._query_time

    @property
    def power(self) -> list:
        if self.check_refresh:
            self.refresh()

        powers = self._power
        
        return powers

    @property
    def hsbk(self) -> list:
        if self.check_refresh:
            self.refresh()
        
        return self._hsbk

    @property
    def devices(self) -> list:
        return self.get_devices()

    def check_refresh(self) -> bool:
        return time.time() - self.query_time >= self._query_interval_seconds

    def refresh(self) -> None:
        self._power = self.get_power()
        self._hsbk = self.get_hsbk()
        self._query_time = time.time()
