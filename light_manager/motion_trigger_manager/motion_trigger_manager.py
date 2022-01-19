import math
import time
import logging
import util.utils as utils
from package.light.device_group.device_group import DeviceGroupError


class MotionTriggerManager:
    DEFAULT_TRANSITION_SECONDS = 0

    def __init__(
        self,
        sensors,
        on_motion_trigger,
        on_motion_timeout,
        device_groups,
        timeout="10s",
        debug=False,
    ):
        self.log = logging.getLogger(self.__class__.__name__)
        self.debug = debug

        self.motion_sensors = sensors

        self._pir_detection_time = 0
        self._motion_timeout_seconds = utils.dehumanize(timeout)

        self._on_motion_trigger_hsbk = [0, 0, 0, 0]
        self._on_motion_trigger_transition = self.DEFAULT_TRANSITION_SECONDS
        self._on_motion_trigger_hsbk = utils.parse_hsbk_map(on_motion_trigger["hsbk"])
        self._on_motion_trigger_transition = utils.dehumanize(
            on_motion_trigger["transition"]
        )

        self._on_motion_timeout_hsbk = [0, 0, 0, 0]
        self._on_motion_timeout_transition = self.DEFAULT_TRANSITION_SECONDS
        self._on_motion_timeout_hsbk = utils.parse_hsbk_map(on_motion_timeout["hsbk"])
        self._on_motion_timeout_transition = utils.dehumanize(
            on_motion_timeout["transition"]
        )

        self._current_hsbk = None

        self._devicegroups = device_groups

    def on_motion(self, hsbk, transition_seconds=0):
        for group in self._devicegroups:
            group.set_hsbk(hsbk, transition_seconds)

    def on_motion_trigger(self, hsbk, transition_seconds=0):
        if self._current_hsbk == hsbk:
            return 
            
        self.log.info("motion triggered - activating light groups")
        self.log.debug(
            "HSBK: {}, transition_seconds: {}".format(
                self._on_motion_trigger_hsbk,
                self._on_motion_timeout_transition,
            )
        )
        self.on_motion(hsbk, transition_seconds=transition_seconds)
        self._current_hsbk = hsbk

    def on_motion_timeout(self, hsbk, transition_seconds=0):
        if self._current_hsbk == hsbk:
            return

        self.log.info("motion timeout - deactivating light groups")
        self.log.debug(
            "HSBK: {}, transition_seconds: {}".format(
                self._on_motion_trigger_hsbk,
                self._on_motion_timeout_transition,
            )
        )
        try:
            self.on_motion(hsbk, transition_seconds=transition_seconds)
            self._current_hsbk = hsbk
        except DeviceGroupError as e:
            self.log.error(e)

    def process(self):
        motion_detection = any([sensor.motion for sensor in self.motion_sensors])

        nowtime = time.time()
        if motion_detection:
            self.on_motion_trigger(
                self._on_motion_trigger_hsbk,
                transition_seconds=self._on_motion_trigger_transition,
            )
            self._pir_detection_time = nowtime
        else:
            time_since_detection = math.ceil(nowtime - self._pir_detection_time)

            if time_since_detection >= self._motion_timeout_seconds:
                self.on_motion_timeout(
                    self._on_motion_timeout_hsbk,
                    transition_seconds=self._on_motion_timeout_transition,
                )
