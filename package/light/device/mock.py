from .device import Device


class MockLight(Device):
    def __init__(self, **kwargs):
        self._power = False
        self._hsbk = [0, 0, 0, 0]

        ip_addr = kwargs["ip_addr"]

        super().__init__(ip_addr)

    def get_power(self):
        return self._power

    def set_power(self, power, transition_seconds=0):
        self._power = power

    def get_hsbk(self):
        return self._hsbk

    def set_hsbk(self, hsbk, transition_seconds=0):
        self._hsbk = hsbk
