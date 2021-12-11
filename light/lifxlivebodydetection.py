import lifxlan
import logging
from lifxlan import Light, Group
from .livebodydetection import LiveBodyDetection

class LIFXLiveBodyDetection(LiveBodyDetection):
    LIFX_MAX_VALUE = 65535

    def __init__(self, config):
        self.log = logging.getLogger(self.__class__.__name__)
        super().__init__(config)

    def init_devicegroup_from_config(self, group_name, devices):
        return group_name, Group(devices)

    def init_device_from_config(self, device_entry):
        mac = device_entry["mac"]
        ip = device_entry["ip"]
        lifx_device = Light(mac, ip)

        return lifx_device

    def on_motion_trigger(self, devicegroup):
        self.set_devicegroup_power(devicegroup, True)

    def on_motion_timeout(self, devicegroup):
        self.set_devicegroup_power(devicegroup, False)

    def get_devicegroup_power(self, devicegroup):
        powers = []

        try:
            devices = devicegroup.get_device_list()
            for device in devices:
                self.log.info("Querying device for power...\n\tMAC: {}\n\tIP: {}".format(device.mac_addr, device.ip_addr))

                power = device.get_power() > 0
                powers.append(power)
        except lifxlan.WorkflowException as e:
            # catch exception here as we don't want to stop on
            # communication errors
            self.log.error(
                'Error occurred communicating with LIFX lights')
            raise e

        return powers
    
    def set_devicegroup_power(self, devicegroup, power):
        try:
            devicegroup.set_power(power)
            return [power] * len(devicegroup.get_device_list())
        except lifxlan.WorkflowException as e:
            # catch exception here as we don't want to stop on
            # communication errors
            self.log.error(
                'Error occurred communicating with LIFX lights')
            raise e

    