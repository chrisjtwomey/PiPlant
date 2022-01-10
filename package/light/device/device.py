class Device:
    def __init__(self, ip):
        self._ip = ip
    
    def get_power(self) -> bool:
        raise NotImplementedError()

    def set_power(self, power, transition_seconds=0) -> None:
        raise NotImplementedError()

    def get_hsbk(self) -> list:
        raise NotImplementedError()

    def set_hsbk(self, hsbk, transition_seconds=0) -> None:
        raise NotImplementedError()

    @property
    def ip(self) -> str:
        return self._ip
