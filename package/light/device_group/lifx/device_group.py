from lifxlan import Group, WorkflowException
from ..device_group import DeviceGroup


class LifxDeviceGroup(DeviceGroup):
    def __init__(self, name, devices):
        self.lifxgroup = Group(devices)
        super().__init__(name, devices)

    def get_devices(self) -> list:
        return self.lifxgroup.get_device_list()

    def set_power(self, power, transition_seconds=0) -> None:
        try:
            self.lifxgroup.set_power(power, duration=transition_seconds)
            self.refresh()
        except WorkflowException as e:
            self.log.error("Error occurred communicating with LIFX lights")

    def get_power(self) -> list:
        try:
            return [device.get_power() for device in self.devices]
        except WorkflowException as e:
            self.log.error("Error occurred communicating with LIFX lights")

    def set_hsbk(self, hsbk, transition_seconds=0) -> None:
        brightness = hsbk[2]

        try:
            if brightness > 0:
                self.set_power(True)
            else:
                self.set_power(False)

            self.lifxgroup.set_color(hsbk, duration=transition_seconds)
            self.refresh()
        except WorkflowException as e:
            self.log.error("Error occurred communicating with LIFX lights")

    def get_hsbk(self) -> list:
        try:
            return [device.get_color() for device in self.devices]
        except WorkflowException as e:
            self.log.error("Error occurred communicating with LIFX lights")
