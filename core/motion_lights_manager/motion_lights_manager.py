import math
import time
import logging
import util.utils as utils
from package.light.device_group.device_group import DeviceGroupError


class MotionLightsManager:
    DEFAULT_TRANSITION_SECONDS = "0s"

    def __init__(
        self,
        device_groups,
        motion_sensors,
        on_motion_trigger,
        on_motion_timeout,
        timeout_seconds=10,
        debug=False,
    ):
        self.log = logging.getLogger(self.__class__.__name__)
        self.debug = debug

        self._device_groups = device_groups

        self._detection_time = 0
        self._motion_sensors = motion_sensors
        self._motion_timeout_seconds = timeout_seconds

        self._current_hsbk = None

        self._on_motion_trigger_hsbk = utils.parse_hsbk_map(on_motion_trigger["hsbk"])
        self._on_motion_trigger_transition = utils.get_config_prop(
            on_motion_trigger,
            "transition",
            default=self.DEFAULT_TRANSITION_SECONDS,
            dehumanized=True,
        )
        self._on_motion_timeout_hsbk = utils.parse_hsbk_map(on_motion_timeout["hsbk"])
        self._on_motion_timeout_transition = utils.get_config_prop(
            on_motion_timeout,
            "transition",
            default=self.DEFAULT_TRANSITION_SECONDS,
            dehumanized=True,
        )

        self.log.info("Initialized")
        self.log.debug(utils.repr_device_groups(device_groups))
        self.log.debug("Motion sensors: {}".format(utils.repr_sensors(motion_sensors)))
        self.log.debug(
            "Motion timeout: {} second(s)".format(self._motion_timeout_seconds)
        )
        self.log.debug(
            "On motion detected:\n\tHSBK: {}\n\ttransition: {} second(s)".format(
                self._on_motion_trigger_hsbk, self._on_motion_trigger_transition
            )
        )
        self.log.debug(
            "On motion timeout:\n\tHSBK: {}\n\ttransition: {} second(s)".format(
                self._on_motion_timeout_hsbk, self._on_motion_timeout_transition
            )
        )

    def is_motion_detected(self):
        return any([sensor.motion for sensor in self._motion_sensors])

    def on_motion(self, hsbk, transition_seconds=0):
        for group in self._device_groups:
            group.set_hsbk(hsbk, transition_seconds)

    def on_motion_trigger(self, hsbk, transition_seconds=0):
        if self._current_hsbk == hsbk:
            return

        self.log.info("motion triggered - activating light groups")
        self.on_motion(hsbk, transition_seconds=transition_seconds)
        self._current_hsbk = hsbk

    def on_motion_timeout(self, hsbk, transition_seconds=0):
        if self._current_hsbk == hsbk:
            return

        self.log.info("motion timeout - deactivating light groups")
        try:
            self.on_motion(hsbk, transition_seconds=transition_seconds)
            self._current_hsbk = hsbk
        except DeviceGroupError as e:
            self.log.error(e)

    def run(self):
        motion_detection = self.is_motion_detected()

        nowtime = time.time()
        if motion_detection:
            self.on_motion_trigger(
                self._on_motion_trigger_hsbk,
                transition_seconds=self._on_motion_trigger_transition,
            )
            self._detection_time = nowtime
        else:
            time_since_detection = math.ceil(nowtime - self._detection_time)

            if time_since_detection >= self._motion_timeout_seconds:
                self.on_motion_timeout(
                    self._on_motion_timeout_hsbk,
                    transition_seconds=self._on_motion_timeout_transition,
                )
