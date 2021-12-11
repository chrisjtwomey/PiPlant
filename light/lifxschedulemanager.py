import lifxlan
import logging
import datetime
import util.utils as utils
from lifxlan import Light, Group
from .schedulemanager import ScheduleManager


class LIFXScheduleManager(ScheduleManager):
    LIFX_MAX_VALUE = 65535

    def __init__(self, config):
        self.log = logging.getLogger(self.__class__.__name__)
        super().__init__(config)

    def on_schedule_change(self, current_schedule):
        hsbk_raw = current_schedule["hsbk"]
        
        hsbk_hue = hsbk_raw["hue"] if "hue" in hsbk_raw else 0
        hsbk_sat = hsbk_raw["saturation"] if "saturation" in hsbk_raw else 0
        
        hsbk_brightness_raw = hsbk_raw["brightness"] if "brightness" in hsbk_raw else 0
        hsbk_brightness = 0

        if "%" in hsbk_brightness_raw:
            hsbk_brightness = int(self.LIFX_MAX_VALUE / 100 * int(hsbk_brightness_raw.split("%")[0]))
        else:
            hsbk_brightness = int(hsbk_brightness_raw) 
        
        hsbk_kelvin = hsbk_raw["kelvin"] if "kelvin" in hsbk_raw else 0

        hsbk = [hsbk_hue, hsbk_sat, hsbk_brightness, hsbk_kelvin]

        # tz localized datetime
        nowdate_tzaware = datetime.datetime.now(tz=self.geocity.tzinfo)
        curr_schedule_dt = utils.hour_to_datetime(current_schedule["time"], tz=self.get_tzinfo())
        transition_seconds = utils.dehumanize(current_schedule["transition"]) if "transition" in current_schedule else 0
        schedule_transition_over_dt = curr_schedule_dt + datetime.timedelta(seconds=transition_seconds)

        if nowdate_tzaware >= schedule_transition_over_dt:
            transition_seconds = 0

        return hsbk, transition_seconds

    def init_devicegroup_from_config(self, group_name, devices):
        return group_name, Group(devices)

    def init_device_from_config(self, device_entry):
        mac = device_entry["mac"]
        ip = device_entry["ip"]
        lifx_device = Light(mac, ip)

        return lifx_device

    def get_devicegroup_hsbk(self, devicegroup):
        hsbks = []

        try:
            devices = devicegroup.get_device_list()
            for device in devices:
                self.log.info("Querying device for HSBK...\n\tMAC: {}\n\tIP: {}".format(device.mac_addr, device.ip_addr))

                hsbk = device.get_color()
                hsbks.append(hsbk)
        except lifxlan.WorkflowException as e:
            # catch exception here as we don't want to stop on
            # communication errors
            self.log.error(
                'Error occurred communicating with LIFX lights')
            raise e

        return hsbks

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

    def set_devicegroup_hsbk(self, devicegroup, hsbk, transition_seconds=0):
        transition_ms = int(transition_seconds * 1000)
        self.log.debug("Setting HSBK for LIFX device group:\n\tHSBK: {0}".format(hsbk))
        if transition_seconds > 0:
            self.log.debug("HSBK transition time:\n\t{} seconds".format(transition_seconds))

        try:
            devicegroup.set_color(hsbk, duration=transition_ms)
            return [hsbk] * len(devicegroup.get_device_list())
        except lifxlan.WorkflowException as e:
            # catch exception here as we don't want to stop on
            # communication errors
            self.log.error(
                'Error occurred communicating with LIFX lights')
            raise e