from lifxlan import Group, WorkflowException
from ..device_group import DeviceGroup, DeviceGroupError


class LifxDeviceGroup(DeviceGroup):
    def __init__(
        self, name, devices, query_interval="2m", retry_interval="2s", max_retries=5
    ):
        self.lifxgroup = Group(devices)
        super().__init__(name, devices, query_interval, retry_interval, max_retries)

    def get_devices(self) -> list:
        return self.lifxgroup.get_device_list()

    def set_power(self, power, transition_seconds=0) -> None:
        if power == self.power:
            return

        def _set_power(power, transition_seconds):
            duration = transition_seconds * 1000
            try:
                self.lifxgroup.set_power(power, duration)
                self.refresh()
            except WorkflowException as e:
                raise DeviceGroupError(e)

        return self.do(_set_power, power, transition_seconds)

    def get_power(self) -> list:
        def _get_power():
            power = []

            try:
                power = [device.get_power() for device in self.devices]
            except WorkflowException as e:
                raise DeviceGroupError(e)

            return power

        return self.do(_get_power)

    def set_hsbk(self, hsbk, transition_seconds=0) -> None:
        if hsbk == self.hsbk:
            return

        def _set_hsbk(hsbk, transition_seconds):
            brightness = hsbk[2]
            duration = transition_seconds * 1000

            try:
                if brightness > 0:
                    self.set_power(True, transition_seconds)
                else:
                    self.set_power(False, transition_seconds)

                self.lifxgroup.set_color(hsbk, duration)
                self.refresh()
            except WorkflowException as e:
                raise DeviceGroupError(e)

        return self.do(_set_hsbk, hsbk, transition_seconds)

    def get_hsbk(self) -> list:
        def _get_hsbk():
            hsbk = []

            try:
                hsbk = [device.get_color() for device in self.devices]
            except WorkflowException as e:
                raise DeviceGroupError(e)

            return hsbk

        return self.do(_get_hsbk)
