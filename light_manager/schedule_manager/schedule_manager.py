import logging
import datetime
import util.utils as utils
from package.light.device_group.device_group import DeviceGroupError


class ScheduleManager:
    def __init__(self, schedules, device_groups, debug=False):
        self.log = logging.getLogger(self.__class__.__name__)
        self.debug = debug

        self._schedules = schedules
        self._active_schedule = None

        self._devicegroups = device_groups

    def on_schedule_change(self, current_schedule):
        hsbk = utils.parse_hsbk_map(current_schedule["hsbk"])

        nowdate = datetime.datetime.now()
        curr_schedule_dt = utils.hour_to_datetime(current_schedule["time"])
        transition_seconds = (
            utils.dehumanize(current_schedule["transition"])
            if "transition" in current_schedule
            else 0
        )
        schedule_transition_over_dt = curr_schedule_dt + datetime.timedelta(
            seconds=transition_seconds
        )

        if nowdate >= schedule_transition_over_dt:
            transition_seconds = 0

        return hsbk, transition_seconds

    def process(self):
        current_schedule = self.get_current_schedule()
        if current_schedule is None:
            return

        hsbk, transition_seconds = self.on_schedule_change(current_schedule)

        if transition_seconds is None:
            transition_seconds = 0

        if self._active_schedule != current_schedule:
            transition_msg = (
                "Light schedule changed: {} -> {}".format(
                    self._active_schedule["name"], current_schedule["name"]
                )
                if self._active_schedule is not None
                else "New light schedule: {}".format(current_schedule["name"])
            )
            self.log.info(transition_msg)

            try:
                for group in self._devicegroups:
                    group.set_hsbk(hsbk, transition_seconds)

                self._active_schedule = current_schedule
            except DeviceGroupError as e:
                self.log.error(e)

    def get_current_schedule(self):
        if len(self._schedules) == 0:
            return None

        nowdate = datetime.datetime.now()
        current_schedule = None

        for _, schedule in enumerate(self._schedules):
            schedule_dt = utils.hour_to_datetime(schedule["time"])
            transition_seconds = (
                utils.dehumanize(schedule["transition"])
                if "transition" in schedule
                else 0
            )
            schedule_dt = schedule_dt - datetime.timedelta(seconds=transition_seconds)

            if nowdate >= schedule_dt:
                current_schedule = schedule

        return current_schedule
