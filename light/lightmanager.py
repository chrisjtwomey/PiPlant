import lifxlan
import math
import time
import logging
import datetime
import util.utils as utils
from lifxlan import Light, Group
from astral.geocoder import lookup, database
from astral.sun import sun


class LightManager:
    DEFAULT_CACHE_REFRESH_TIMEOUT = 120
    DEFAULT_DEVICE_OFF_TIMEOUT = 120
    GEO_DEFAULT_CITY = "Dublin"
    GEO_DEFAULT_TZ = "UTC"
    LIFX_MAX_VALUE = 65535

    def __init__(self, config):
        self.log = logging.getLogger(self.__class__.__name__)

        # controlled by PIR motion sensor
        self._motion_device_groups = config["motion_activated_device_groups"] if "motion_activated_device_groups" in config else []
        self._schedules = config["schedules"] if "schedules" in config else []

        city_loc_name = config["geo_city"] if "geo_city" in config else self.GEO_DEFAULT_CITY
        self.geotz = config["geo_tz"].upper() if "geo_tz" in config else self.GEO_DEFAULT_TZ
        self.geocity = lookup(city_loc_name, database())

        self._cache_refresh_timeout = utils.dehumanize(
            config["device_query_interval"]) if "device_query_interval" in config else self.DEFAULT_CACHE_REFRESH_TIMEOUT
        self._device_off_timeout = utils.dehumanize(
            config["motion_device_off_timeout"]) if "motion_device_off_timeout" in config else self.DEFAULT_DEVICE_OFF_TIMEOUT

        nowtime_naive = time.time()
        self._pir_detection_time = nowtime_naive
        self._static_lights_refresh_time = 0

        self._devicegroups = []
        discovery_enabled = utils.dehumanize(config["autodiscovery"])

        if discovery_enabled:
            self._devicegroups = self._find_devicegroups_from_config(config)
        else:
            self._devicegroups = self._set_devicegroups_from_config(config)

        self._state_cache = self._init_state_cache(self._devicegroups)
        self.get_devices_state()

    def _init_state_cache(self, devicegroups):
        hsbk_cache = dict()
        power = False
        hsbk = [0, 0, 0, 0]

        for _, group in devicegroups.items():
            for device in group.get_device_list():
                hsbk_cache[device.mac_addr] = (0, power, hsbk)

        return hsbk_cache

    def _find_devicegroups_from_config(self):
        # TODO
        self.log.warning("Auto-discovery of Lifx devices not implemented yet!")
        return

    def _set_devicegroups_from_config(self, config):
        groups = {}

        for group_entry in config["device_groups"]:
            devices = []
            for groupname, device_entries in group_entry.items():
                for device_entry in device_entries:
                    mac = device_entry["mac"]
                    ip = device_entry["ip"]
                    devices.append(Light(mac, ip))
                groups[groupname] = Group(devices)

        return groups

    def process_sensor_data(self, data):
        self._process_motion_detection(data)
        curr_schedule, next_schedule = self._get_schedules()
        self._process_schedules(curr_schedule, next_schedule)

    def _process_schedules(self, curr_schedule, next_schedule):
        curr_schedule_dt = self._hour_to_datetime(curr_schedule["time"], tzinfo=self.geocity.tzinfo)
        transition_seconds = 0

        if next_schedule is not None:
            next_schedule_dt = self._hour_to_datetime(next_schedule["time"], tzinfo=self.geocity.tzinfo)
            dt_delta = next_schedule_dt - curr_schedule_dt

            transition_seconds = int(dt_delta.total_seconds())

        curr_schedule_hsbk = curr_schedule["hsbk"]
        hsbk_hue = curr_schedule_hsbk["hue"] if "hue" in curr_schedule_hsbk else 0
        hsbk_sat = curr_schedule_hsbk["saturation"] if "saturation" in curr_schedule_hsbk else 0
        
        hsbk_brightness_raw = curr_schedule_hsbk["brightness"] if "brightness" in curr_schedule_hsbk else 0
        hsbk_brightness = 0

        if "%" in hsbk_brightness_raw:
            hsbk_brightness = int(self.LIFX_MAX_VALUE / 100 * int(hsbk_brightness_raw.split("%")[0]))
        else:
            hsbk_brightness = int(hsbk_brightness_raw) 

        hsbk_kelvin = curr_schedule_hsbk["kelvin"] if "kelvin" in curr_schedule_hsbk else 0
        hsbk = [hsbk_hue, hsbk_sat, hsbk_brightness, hsbk_kelvin]

        groups = curr_schedule["device_groups"]

        self.set_devices_state(groups, hsbk)

    def _get_schedules(self):
        if len(self._schedules) == 0:
            return

        # tz localized datetime
        nowdate_tzaware = datetime.datetime.now(tz=self.geocity.tzinfo)

        curr_schedule = None
        next_schedule = None
        next_schedule_idx = 0
        num_schedules = len(self._schedules)

        for idx, schedule in enumerate(self._schedules):
            next_schedule_idx = idx + 1

            if next_schedule_idx < num_schedules:
                next_schedule_tmp = self._schedules[next_schedule_idx]

            curr_schedule_dt = self._hour_to_datetime(schedule["time"], tzinfo=self.geocity.tzinfo)

            if nowdate_tzaware >= curr_schedule_dt:
                curr_schedule = schedule

                if next_schedule_tmp is not None:
                    next_schedule_dt = self._hour_to_datetime(next_schedule_tmp["time"], tzinfo=self.geocity.tzinfo)

                    if nowdate_tzaware > next_schedule_dt:
                        continue

                    if nowdate_tzaware < next_schedule_dt:
                        next_schedule = next_schedule_tmp

        return curr_schedule, next_schedule

    def _hour_to_datetime(self, hour_str, tzinfo = None):  
        nowdate = datetime.datetime.today()
        if tzinfo is not None:
            nowdate = nowdate.replace(tzinfo=tzinfo)

        nowdate_str = nowdate.strftime('%d/%m/%Y')
        nowdatetime_str = nowdate_str + " " + hour_str
        
        dt = datetime.datetime.strptime(nowdatetime_str, '%d/%m/%Y %H:%M')
        if tzinfo is not None:
            dt = dt.replace(tzinfo=tzinfo)

        return dt

    def _process_motion_detection(self, data):
        if "livebody_detection" not in data:
            return

        livebody_detection = data["livebody_detection"]
        # not tz localized time
        nowtime_naive = time.time()

        # PIR motion detected
        if livebody_detection:
            powers, hsbks = self.get_devices_state(self._motion_device_groups)
            # get brightness values

            if not all(powers):
                # set all devices on
                hsbks = [[hsbk[0], hsbk[1], self.LIFX_MAX_VALUE, hsbk[3]] for hsbk in hsbks]
                self.set_devices_state(self._motion_device_groups, hsbks)
            self._pir_detection_time = nowtime_naive

        if not livebody_detection:
            # are we on longer than we should without detecting anybody?
            time_since_detection = math.ceil(
                nowtime_naive - self._pir_detection_time)

            if time_since_detection >= self._device_off_timeout:
                powers, hsbks = self.get_devices_state(
                    self._motion_device_groups)
                # are any on?
                if any(powers):
                    self.log.debug("No PIR motion detected for {} seconds for groups {}".format(
                        self._device_off_timeout, self._motion_device_groups))
                    # set all devices off
                    hsbks = [[hsbk[0], hsbk[1], 0, hsbk[3]] for hsbk in hsbks]
                    self.set_devices_state(
                        self._motion_device_groups, False)

    def update_state_cache(self, device, power, hsbk):
        nowtime_naive = time.time()
        self._state_cache[device.mac_addr] = (nowtime_naive, power, hsbk)

    def get_devices_state(self, groups=[], use_local_state=True):
        if len(groups) == 0:
            groups = self._devicegroups

        devices = []
        for group in groups:
            group = self._devicegroups[group]

            for device in group.get_device_list():
                devices.append(device)

        nowtime_naive = time.time()
        power_states = []
        hsbk_states = []

        for device in devices:
            refresh_time, power, hsbk = self._state_cache[device.mac_addr]
            time_since_update = math.ceil(nowtime_naive - refresh_time)

            if not use_local_state or time_since_update > self._cache_refresh_timeout:
                self.log.info("Querying device for state...\n\tMAC: {}\n\tIP: {}".format(
                    device.mac_addr, device.ip_addr))
                try:
                    power = device.get_power() > 0
                    hsbk = device.get_color()
                    self.update_state_cache(device, power, hsbk)
                except lifxlan.WorkflowException as wfe:
                    # catch exception here as we don't want to stop on
                    # communication errors
                    self.log.error(
                        'Error occurred communicating with LIFX lights')
                    self.log.exception(wfe)
                except Exception as e:
                    self.log.error('A generic exception error has occurred')
                    self.log.exception(e)

            power_states.append(power)
            hsbk_states.append(hsbk)

        self.log.debug("LIFX device state for groups {}:\n\tpower: {}\n\tHSBK: {}".format(
            ", ".join(groups), power_states, hsbk_states))

        return power_states, hsbk_states

    def set_devices_state(self, groups, hsbk, transition_seconds=0):
        duration_ms = int(transition_seconds * 1000)

        for group in groups:
            self.log.debug(
                "Setting state for LIFX device groups:\n\tgroups: {0}\n\tHSBK: {1}".format(group, hsbk))
            if duration_ms > 0:
                self.log.debug("HSBK transition time:\n\t{} seconds".format(transition_seconds))

            g = self._devicegroups[group]
            try:
                power = True
                brightness = hsbk[2]
                if brightness == 0:
                    power = False
                    g.set_power(False)
                
                g.set_color(hsbk, duration=duration_ms)
                
                for device in g.get_device_list():
                    self.update_state_cache(device, power, hsbk)

            except lifxlan.WorkflowException as wfe:
                # catch exception here as we don't want to stop on
                # communication errors
                self.log.error('Error occurred communicating with LIFX lights')
                self.log.exception(wfe)
            except Exception as e:
                self.log.error('A generic exception error has occurred')
                self.log.exception(e)
