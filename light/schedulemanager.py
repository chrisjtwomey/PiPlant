import math
import time
import logging
import datetime
import util.utils as utils
from astral.geocoder import lookup, database


class ScheduleManager:
    DEFAULT_CACHE_REFRESH_TIMEOUT = 120
    GEO_DEFAULT_CITY = "Dublin"
    GEO_DEFAULT_TZ = "UTC"

    def __init__(self, config, devmode):
        self.log = logging.getLogger(self.__class__.__name__)
        self.devmode = devmode

        self._schedules = config["schedules"] if "schedules" in config else []

        city_loc_name = config["geo_city"] if "geo_city" in config else self.GEO_DEFAULT_CITY
        self.geotz = config["geo_tz"].upper() if "geo_tz" in config else self.GEO_DEFAULT_TZ
        self.geocity = lookup(city_loc_name, database())

        self._cache_refresh_timeout = utils.dehumanize(
            config["device_query_interval"]) if "device_query_interval" in config else self.DEFAULT_CACHE_REFRESH_TIMEOUT

        self._static_lights_refresh_time = 0

        self._devicegroups = []
        discovery_enabled = utils.dehumanize(config["autodiscovery"])

        if discovery_enabled:
            self._devicegroups = self._autodiscover_devicegroup()
        else:
            self._devicegroups = self._get_device_groups_from_config(config["device_groups"])

        self._init_state_cache(self._devicegroups)
        self._get_devicegroup_state()

        self.log.info("Schedule Manager initialized")

    def get_tzinfo(self):
        return self.geocity.tzinfo

    def _autodiscover_devicegroup(self):
        self.log.warning("autodiscover_devicegroups_from_config not implemented!")
        pass

    def on_schedule_change(self, schedule):
        hsbk_raw = schedule["hsbk"]
        
        hsbk_hue = hsbk_raw["hue"] if "hue" in hsbk_raw else 0
        hsbk_sat = hsbk_raw["saturation"] if "saturation" in hsbk_raw else 0
        hsbk_brightness = hsbk_raw["brightness"] if "brightness" in hsbk_raw else 0
        hsbk_kelvin = hsbk_raw["kelvin"] if "kelvin" in hsbk_raw else 0

        hsbk = [hsbk_hue, hsbk_sat, hsbk_brightness, hsbk_kelvin]

        return hsbk, None

    def init_devicegroup_from_config(self, group_name, devices):
        raise NotImplementedError("init_group_from_config not implemented!")

    def init_device_from_config(self, device_entry):
        raise NotImplementedError("init_device_from_config not implemented!")

    def get_devicegroup_hsbk(self, devicegroup):
        raise NotImplementedError("get_device_hsbk not implemented!")

    def get_devicegroup_power(self, devicegroup):
        raise NotImplementedError("get_device_power not implemented!")

    def set_devicegroup_power(self, devicegroup, power):
        raise NotImplementedError("set_devicegroup_power not implemented!")

    def set_devicegroup_hsbk(self, devicegroup, hsbk):
        raise NotImplementedError("set_devicegroup_hsbk not implemented!")

    def process(self):
        current_schedule = self._get_current_schedule()
        if current_schedule is None:
            return
        
        hsbk, transition_seconds = self.on_schedule_change(current_schedule)

        if transition_seconds is None:
            transition_seconds = 0

        if "device_groups" not in current_schedule:
            raise ValueError("No device groups specified for current schedule: {}".format(current_schedule))
        
        groups = current_schedule["device_groups"]
        group_states = self._get_devicegroup_state(groups)
        
        for group_name, group_state in group_states.items():
            if current_schedule != group_state["current_schedule"]:
                self.log.info("Light schedule changed - {}".format(current_schedule["name"]))
                group_state["current_schedule"] = current_schedule
                self._set_devicegroup_hsbk(hsbk, group_names=[group_name], transition_seconds=transition_seconds)
                self._state_cache[group_name] = group_state

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

    def _get_current_schedule(self):
        if len(self._schedules) == 0:
            return None

        # tz localized datetime
        nowdate_tzaware = datetime.datetime.now(tz=self.geocity.tzinfo)
        current_schedule = None

        for _, schedule in enumerate(self._schedules):
            schedule_dt = utils.hour_to_datetime(schedule["time"], tz=self.geocity.tzinfo)
            transition_seconds = utils.dehumanize(schedule["transition"]) if "transition" in schedule else 0
            schedule_dt = schedule_dt - datetime.timedelta(seconds=transition_seconds)

            if nowdate_tzaware >= schedule_dt:
                current_schedule = schedule

        return current_schedule

    def _init_state_cache(self, devicegroups):
        state_cache = dict()

        for group_name, _ in devicegroups.items():
            state_cache[group_name] = {
                "update_time": 0,
                "current_schedule": None,
                "powers": [],
                "hsbks": [],
            }

        self._state_cache = state_cache

    def _get_devicegroup_state(self, group_names = [], use_local_state=True):
        if self.devmode:
            self.log.debug("get_devicegroup_state:\n\tgroup_names: {}\n\tuse_local_state: {}".format(group_names, use_local_state))
            return dict()

        if len(group_names) == 0:
            group_names = self._devicegroups.keys()

        nowtime_naive = time.time()
        group_states = dict()

        for group_name in group_names:
            group = self._devicegroups[group_name]
            group_state = self._state_cache[group_name]
            update_time = group_state["update_time"]

            time_since_update = math.ceil(nowtime_naive - update_time)

            if not use_local_state or time_since_update > self._cache_refresh_timeout:
                try:
                    group_state["powers"] = self.get_devicegroup_power(group)
                    group_state["hsbks"] = self.get_devicegroup_hsbk(group)
                    group_state["update_time"] = nowtime_naive
                    
                    self._state_cache[group_name] = group_state
                except Exception as e:
                    self.log.error('An error has occurred')
                    self.log.exception(e)

            self.log.debug("State for group {}: {}".format(group_name, group_state))
            group_states[group_name] = group_state

        return group_states

    def _set_devicegroup_hsbk(self, hsbk, group_names = [], transition_seconds=0):
        if self.devmode:
            self.log.debug("_set_devicegroup_hsbk:\n\tgroup_names: {}\n\tHSBK: {}\n\ttransition_seconds: {}".format(group_names, hsbk, transition_seconds))
            return

        if len(group_names) == 0:
            group_names = self._devicegroups.keys()
        
        for group_name in group_names:
            group = self._devicegroups[group_name]
            group_state = self._state_cache[group_name]
            nowtime_naive = time.time()

            try:
                power = True
                brightness = hsbk[2]
                if brightness == 0:
                    power = False
                    
                powers = self.set_devicegroup_power(group, power)
                hsbks = self.set_devicegroup_hsbk(group, hsbk, transition_seconds)

                group_state["powers"] = powers
                group_state["hsbks"] = hsbks
                group_state["update_time"] = nowtime_naive
            except Exception as e:
                self.log.error('An error has occurred')
                self.log.exception(e)
            finally:
                self._state_cache[group_name] = group_state
