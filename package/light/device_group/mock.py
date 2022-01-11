from .device_group import DeviceGroup


class MockDeviceGroup(DeviceGroup):
    def __init__(self, **kwargs):
        name = kwargs["name"]
        devices = kwargs["devices"]

        super().__init__(name, devices)

    def get_devices(self) -> list:
        return self._devices

    def get_power(self) -> list:
        return [device.get_power() for device in self.devices]

    def set_power(self, power, transition_seconds=0) -> None:
        for device in self.devices:
            device.set_power(power)

    def get_hsbk(self) -> list:
        return [device.get_hsbk() for device in self.devices]

    def set_hsbk(self, hsbk, transition_seconds=0) -> None:
        for device in self.devices:
            device.set_hsbk(hsbk)
