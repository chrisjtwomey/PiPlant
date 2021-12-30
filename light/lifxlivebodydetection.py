import logging
import util.utils as utils
from .devicegroup import lifx
from .livebodydetection import LiveBodyDetection

class LIFXLiveBodyDetection(LiveBodyDetection):
    def __init__(self, config, debug=False):
        self.log = logging.getLogger(self.__class__.__name__)
        super().__init__(config, debug)

    def on_motion(self, devicegroup, hsbk, transition_seconds=0):
        _, _, brightness, _ = hsbk

        if brightness > 0:
            self.set_devicegroup_power(devicegroup, True)
        else:
            self.set_devicegroup_power(devicegroup, False)

        self.set_devicegroup_hsbk(devicegroup, hsbk, transition_seconds)

    def on_motion_trigger(self, devicegroup, hsbk, transition_seconds=0):
        self.on_motion(devicegroup, hsbk, transition_seconds=transition_seconds)

    def on_motion_timeout(self, devicegroup, hsbk, transition_seconds=0):
        self.on_motion(devicegroup, hsbk, transition_seconds=transition_seconds)

    def init_devicegroup_from_config(self, group_name, devices):
        return lifx.init_devicegroup_from_config(group_name, devices)

    def init_device_from_config(self, device_entry):
        return lifx.init_device_from_config(device_entry)

    def get_devicegroup_power(self, devicegroup):
        return lifx.get_devicegroup_power(devicegroup)
    
    def set_devicegroup_power(self, devicegroup, power):
        return lifx.set_devicegroup_power(devicegroup, power)

    def set_devicegroup_hsbk(self, devicegroup, hsbk, transition_seconds=0):
        return lifx.set_devicegroup_hsbk(devicegroup, hsbk, transition_seconds=transition_seconds)
    