import time
import util.utils as utils

import logging


class DeviceGroupError(Exception):
    def __init__(self, message):
        super().__init__(message)


class DeviceGroup:
    def __init__(
        self, name, devices, query_interval="2m", retry_interval="2s", max_retries=5
    ):
        self._group_name = name
        self._devices = devices

        self._query_interval_seconds = utils.dehumanize(query_interval)
        self._retry_interval_seconds = utils.dehumanize(retry_interval)
        self._max_retries = max_retries

        self._power = [False] * len(devices)
        self._hsbk = [[0, 0, 0, 0]] * len(devices)
        self._query_time = 0

        self.log = logging.getLogger("{}.{}".format(self.__class__.__name__, self.name))

    def get_devices(self) -> list:
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.get_devices.__name__
            )
        )

    def get_power(self) -> list:
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.get_power.__name__
            )
        )

    def set_power(self, power, transition_seconds=0) -> None:
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.set_power.__name__
            )
        )

    def get_hsbk(self) -> list:
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.get_hsbk.__name__
            )
        )

    def set_hsbk(self, hsbk, transition_seconds=0) -> None:
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.set_hsbk.__name__
            )
        )

    def do(self, doFunc, *args):
        retries = 0
        err = None

        while retries <= self._max_retries:
            try:
                self.log.debug("Do {} on DeviceGroup".format(doFunc.__name__, self.name))
                import random
                if random.choice([False, True]):
                    raise DeviceGroupError("test")
                return doFunc(*args)
            except DeviceGroupError as e:
                err = e
                self.log.warning("an error occurred communicating with DeviceGroup {}".format(self.name))
                time.sleep(self._retry_interval_seconds)
                retries += 1

        raise DeviceGroupError(
            "unable to do {} on DeviceGroup {}: {}".format(doFunc.__name__, self.name, err)
        )

    @property
    def name(self) -> str:
        return self._group_name

    @property
    def query_time(self) -> int:
        return self._query_time

    @property
    def power(self) -> list:
        if self.check_refresh():
            self.refresh()

        powers = self._power

        return powers

    @property
    def hsbk(self) -> list:
        if self.check_refresh():
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

        self.log.debug(
            "refreshed device states:\n\tpower: {}\n\thsbk: {}".format(
                self._power, self._hsbk
            )
        )
