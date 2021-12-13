import lifxlan
import math
import time
import logging
import util.utils as utils
from lifxlan import Light, Group
from astral.geocoder import lookup, database
from astral.sun import sun


class LiveBodyDetection:
    DEFAULT_MOTION_TIMEOUT = 30
    DEFAULT_TRANSITION_SECONDS = 0

    def __init__(self, config):
        self.log = logging.getLogger(self.__class__.__name__)

        lbd_conf = config["livebody_detection"]

        self._pir_detection_time = 0
        self._motion_timeout_seconds = utils.dehumanize(lbd_conf["timeout"]) if "timeout" in lbd_conf else self.DEFAULT_MOTION_TIMEOUT
        self._motion_group_names = lbd_conf["device_groups"]

        self._on_motion_trigger_hsbk = [0, 0, 0, 0]
        self._on_motion_trigger_transition = self.DEFAULT_TRANSITION_SECONDS
        if "on_motion_trigger" in lbd_conf:
            if "hsbk" in lbd_conf["on_motion_trigger"]:
                self._on_motion_trigger_hsbk = utils.parse_hsbk_map(lbd_conf["on_motion_trigger"]["hsbk"])

            if "transition" in lbd_conf["on_motion_trigger"]:
                self._on_motion_trigger_transition = utils.dehumanize(lbd_conf["on_motion_trigger"]["transition"])

        self._on_motion_timeout_hsbk = [0, 0, 0, 0]
        self._on_motion_timeout_transition = self.DEFAULT_TRANSITION_SECONDS
        if "on_timeout" in lbd_conf:
            if "hsbk" in lbd_conf["on_motion_timeout"]:
                self._on_motion_timeout_hsbk = utils.parse_hsbk_map(lbd_conf["on_motion_timeout"]["hsbk"])

            if "transition" in lbd_conf["on_motion_timeout"]:
                self._on_motion_timeout_transition = utils.dehumanize(lbd_conf["on_motion_timeout"]["transition"])

        discovery_enabled = utils.dehumanize(config["autodiscovery"])
        if discovery_enabled:
            self._devicegroups = self._autodiscover_devicegroup()
        else:
            self._devicegroups = self._get_device_groups_from_config(config["device_groups"])

        self.log.info("Livebody detection initialized")

    def _autodiscover_devicegroup(self):
        self.log.warning("autodiscover_devicegroups_from_config not implemented!")
        pass
        
    def init_devicegroup_from_config(self, group_name, devices):
        raise NotImplementedError("init_group_from_config not implemented!")

    def init_device_from_config(self, device_entry):
        raise NotImplementedError("init_device_from_config not implemented!")

    def get_devicegroup_power(self, devicegroup):
        raise NotImplementedError("get_device_power not implemented!")

    def set_devicegroup_power(self, devicegroup, power):
        raise NotImplementedError("set_devicegroup_power not implemented!")
    
    def on_motion_trigger(self, devicegroup, hsbk, transition_seconds=0):
        raise NotImplementedError("on_motion_trigger not implemented!")

    def on_motion_timeout(self, devicegroup, hsbk, transition_seconds=0):
        raise NotImplementedError("on_motion_timeout not implemented!")

    def _get_device_groups_from_config(self, config_devicegroups):
        groups = {}

        for group_entry in config_devicegroups:
            for group_entry_name, device_entries in group_entry.items():
                devices = []
                for device_entry in device_entries:
                    devices.append(self.init_device_from_config(device_entry))
                
                group_name, group = self.init_devicegroup_from_config(group_entry_name, devices)
                groups[group_name] = group

        return groups

    def process(self, livebody_detection):
        nowtime_naive = time.time()
        if livebody_detection:
            for group_name, devicegroup in self._devicegroups.items():
                if group_name in self._motion_group_names:
                    self.on_motion_trigger(devicegroup, self._on_motion_trigger_hsbk, transition_seconds=self._on_motion_trigger_transition)
            self._pir_detection_time = nowtime_naive
        else:
            time_since_detection = math.ceil(
                nowtime_naive - self._pir_detection_time)

            if time_since_detection >= self._motion_timeout_seconds:
                for group_name, devicegroup in self._devicegroups.items():
                    if group_name in self._motion_group_names:
                        self.on_motion_timeout(devicegroup, self._on_motion_timeout_hsbk, transition_seconds=self._on_motion_timeout_transition)