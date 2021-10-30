import lifxlan
from lifxlan.device import Device
import pytz
import math
import time
import logging
import datetime
from lifxlan import Light, Group
from astral.geocoder import lookup, database
from astral.sun import sun


class LightManager:
    CORNER_LAMP_GROUP_NAME = "LIGHTMANAGER_DEVICE_GROUP_CORNER_LAMP"
    DESK_LAMP_GROUP_NAME = "LIGHTMANAGER_DEVICE_GROUP_DESK_LAMP"
    CACHE_REFRESH_TIMEOUT_SECONDS = 120
    DEVICES_OFF_TIMEOUT_SECONDS = 120

    GEO_DEFAULT_CITY = "Dublin"
    GEO_DEFAULT_TZ = "UTC"

    GROUPS_AMBIENT = [CORNER_LAMP_GROUP_NAME]
    GROUPS_PLANT = [DESK_LAMP_GROUP_NAME]

    def __init__(self, discoveryconf, managerconf, groupsconf):
        self.log = logging.getLogger(self.__class__.__name__)

        self.discoveryconf = discoveryconf
        self.managerconf = managerconf
        self.groupsconf = groupsconf

        city_loc_name = managerconf["geo_city"] if "geo_city" in managerconf else self.GEO_DEFAULT_CITY
        self.geotz = managerconf["geo_tz"].upper(
        ) if "geo_tz" in managerconf else self.GEO_DEFAULT_TZ
        self.geocity = lookup(city_loc_name, database())

        self._light_hours = managerconf.getint("static_light_hours")

        nowtime_naive = time.time()
        self._power_transition_time = nowtime_naive
        self._static_lights_refresh_time = 0
        self._prev_livebody_detection = True  # init PIR lights as on

        self._devicegroups = self.get_devicegroups()
        self._state_cache = self._init_state_cache(self._devicegroups)
        self.get_devices_power_state()

    def _init_state_cache(self, devicegroups):
        cache = dict()

        for _, group in devicegroups.items():
            for device in group.get_device_list():
                cache[device.mac_addr] = (0, False)

        return cache

    def get_devicegroups(self):
        discovery_enabled = self.discoveryconf.getboolean("enabled")
        groups = dict()

        if discovery_enabled:
            return []  # TODO
        else:
            for (group, conf) in self.groupsconf:
                devices = []

                for mac, ip in conf.items():
                    if "-" in mac:
                        mac = mac.replace("-", ":")
                    devices.append(Light(mac, ip))

                groups[group] = Group(devices)

        return groups

    def process_sensor_data(self, data):
        livebody_detection = data['livebody_detection']

        observer = self.geocity.observer
        tz = self.geocity.timezone
        tzinfo = self.geocity.tzinfo

        # not tz localized time
        nowtime_naive = time.time()
        # tz localized datetime
        nowdate_tzaware = datetime.datetime.now(tz=tzinfo)

        today = datetime.datetime.now(tz=tzinfo).date()
        midnight_today = datetime.datetime.combine(
            today, datetime.datetime.min.time())
        midnight_tmrw = midnight_today + datetime.timedelta(days=1)

        sunphases = sun(observer, date=today, tzinfo=tz)

        static_lights_on_dt = sunphases["dawn"]
        static_lights_off_dt = static_lights_on_dt + \
            datetime.timedelta(hours=self._light_hours)

        # static group isn't controlled by motion sensor
        static_light_groups = []
        # controlled by PIR motion sensor
        pir_controlled_light_groups = []

        if nowdate_tzaware < static_lights_on_dt:
            # between midnight and dawn
            # static lights stay off
            # ambient lights activated by PIR
            static_light_groups = self.GROUPS_PLANT
            pir_controlled_light_groups = self.GROUPS_AMBIENT

            states = self.get_devices_power_state(static_light_groups)
            if any(states):
                # keep static lights off
                self.set_devices_power_state(static_light_groups, False)

        elif static_lights_off_dt < nowdate_tzaware < midnight_tmrw:
            # between static lights off and midnight
            # ambient and plant lights activated by PIR
            static_light_groups = []
            pir_controlled_light_groups = self.GROUPS_AMBIENT + self.GROUPS_PLANT

        elif static_lights_on_dt < nowdate_tzaware < static_lights_off_dt:
            # between static lights on and static lights off
            # static lights stay on
            # ambient lights activated by PIR
            static_light_groups = self.GROUPS_PLANT
            pir_controlled_light_groups = self.GROUPS_AMBIENT

            states = self.get_devices_power_state(static_light_groups)
            if not all(states):
                # keep static lights on
                self.set_devices_power_state(static_light_groups, True)

        # PIR motion detected
        if livebody_detection:
            states = self.get_devices_power_state(
                pir_controlled_light_groups)
            if not all(states):
                # set all devices on
                self.set_devices_power_state(
                    pir_controlled_light_groups, True)
                self._power_transition_time = nowtime_naive

        if not livebody_detection:
            # are we on longer than we should without detecting anybody?
            time_since_transition = math.ceil(
                nowtime_naive - self._power_transition_time)

            if time_since_transition >= self.DEVICES_OFF_TIMEOUT_SECONDS:
                states = self.get_devices_power_state(
                    pir_controlled_light_groups)
                # are any on?
                if any(states):
                    self.log.debug("No PIR motion detected for {} seconds for groups {}".format(
                        self.DEVICES_OFF_TIMEOUT_SECONDS, pir_controlled_light_groups))
                    # set all devices off
                    self.set_devices_power_state(
                        pir_controlled_light_groups, False)
                    self._power_transition_time = nowtime_naive

    def update_state_cache(self, device, power_state):
        nowtime_naive = time.time()
        self._state_cache[device.mac_addr] = (nowtime_naive, power_state)

    def get_devices_power_state(self, groups=[], use_local_state=True):
        if len(groups) == 0:
            groups = self.GROUPS_AMBIENT + self.GROUPS_PLANT

        devices = []
        for group in groups:
            group = self._devicegroups[group]

            for device in group.get_device_list():
                devices.append(device)

        nowtime_naive = time.time()
        device_power_states = []

        for device in devices:
            refresh_time, power_state = self._state_cache[device.mac_addr]
            time_since_update = math.ceil(nowtime_naive - refresh_time)

            if not use_local_state or time_since_update > self.CACHE_REFRESH_TIMEOUT_SECONDS:
                self.log.info("Querying device {}:{} for power state...".format(
                    device.mac_addr, device.ip_addr))
                try:
                    power_state = device.get_power() > 0
                    self.update_state_cache(device, power_state)
                except lifxlan.WorkflowException as wfe:
                    # catch exception here as we don't want to stop on
                    # communication errors
                    self.log.error(
                        'Error occurred communicating with LIFX lights')
                    self.log.exception(wfe)
                except Exception as e:
                    self.log.error('A generic exception error has occurred')
                    self.log.exception(e)

            device_power_states.append(power_state)

        self.log.debug("LIFX device power states for groups {}: {}".format(
            ", ".join(groups), device_power_states))

        return device_power_states

    def set_devices_power_state(self, groups, state):
        for group in groups:
            self.log.debug(
                "Setting power state {} for LIFX device groups: {}".format(state, group))
            g = self._devicegroups[group]
            g.set_power(state)
            try:
                g.set_power(state)
                for device in g.get_device_list():
                    self.update_state_cache(device, state)
            except lifxlan.WorkflowException as wfe:
                # catch exception here as we don't want to stop on
                # communication errors
                self.log.error('Error occurred communicating with LIFX lights')
                self.log.exception(wfe)
            except Exception as e:
                self.log.error('A generic exception error has occurred')
                self.log.exception(e)
