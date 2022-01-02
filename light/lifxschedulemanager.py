import logging
import datetime
import util.utils as utils
from .devicegroup import lifx
from .schedulemanager import ScheduleManager


class LIFXScheduleManager(ScheduleManager):
    def __init__(self, config, debug=False):
        self.log = logging.getLogger(self.__class__.__name__)
        super().__init__(config, debug)

    def on_schedule_change(self, current_schedule):
        hsbk = utils.parse_hsbk_map(current_schedule["hsbk"])

        # tz localized datetime
        nowdate_tzaware = datetime.datetime.now(tz=self.geocity.tzinfo)
        curr_schedule_dt = utils.hour_to_datetime(
            current_schedule["time"], tz=self.get_tzinfo()
        )
        transition_seconds = (
            utils.dehumanize(current_schedule["transition"])
            if "transition" in current_schedule
            else 0
        )
        schedule_transition_over_dt = curr_schedule_dt + datetime.timedelta(
            seconds=transition_seconds
        )

        if nowdate_tzaware >= schedule_transition_over_dt:
            transition_seconds = 0

        return hsbk, transition_seconds

    def init_devicegroup_from_config(self, group_name, devices):
        return lifx.init_devicegroup_from_config(group_name, devices)

    def init_device_from_config(self, device_entry):
        return lifx.init_device_from_config(device_entry)

    def get_devicegroup_power(self, devicegroup):
        return lifx.get_devicegroup_power(devicegroup)

    def set_devicegroup_power(self, devicegroup, power):
        return lifx.set_devicegroup_power(devicegroup, power)

    def get_devicegroup_hsbk(self, devicegroup):
        return lifx.get_devicegroup_hsbk(devicegroup)

    def set_devicegroup_hsbk(self, devicegroup, hsbk, transition_seconds=0):
        return lifx.set_devicegroup_hsbk(
            devicegroup, hsbk, transition_seconds=transition_seconds
        )
