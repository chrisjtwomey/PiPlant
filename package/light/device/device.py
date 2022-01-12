class Device:
    def __init__(self, ip_addr):
        self._ip = ip_addr

    def get_power(self) -> bool:
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

    @property
    def ip(self) -> str:
        return self._ip
