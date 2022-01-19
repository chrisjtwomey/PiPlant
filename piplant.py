import sys
import os
import yaml
import time
import datetime
import argparse
import logging.config
import util.utils as utils
from display.epaper import EPaper
from db.db import DataPayload, Database
from package.package import PackageImporter
from sensor.polledsensor import PolledSensor
from light_manager.schedule_manager.schedule_manager import ScheduleManager
from light_manager.motion_trigger_manager.motion_trigger_manager import (
    MotionTriggerManager,
)

cwd = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument(
    "-c",
    "--config",
    type=argparse.FileType("r"),
    required=True,
    help="The path of the PiPlant config yaml",
)
parser.add_argument(
    "-m", "--mock", action="store_true", default=False, help="Flag to enable mock mode"
)
parser.add_argument(
    "-d",
    "--debug",
    action="store_true",
    default=False,
    help="Flag to enable verbose logging",
)


class PiPlant(PolledSensor):
    def __init__(self, config, poll_interval="5s", mock=False, debug=False):
        self.debug = debug
        self.mock = mock

        self.config_path = os.path.join(cwd, "template")

        logging_cfg_path = os.path.join(self.config_path, "logging.ini")
        if self.debug:
            logging_cfg_path = os.path.join(self.config_path, "logging.dev.ini")

        logging.config.fileConfig(logging_cfg_path)

        self._poll_interval_seconds = utils.dehumanize(poll_interval)
        self._process_time = 0
        self._render_time = 0

        super().__init__(self._poll_interval_seconds)

        print(
            r"""
                            PiPlant
                         @chrisjtwomey
                    _
                  _(_)_                          wWWWw   _
      @@@@       (_)@(_)   vVVVv     _     @@@@  (___) _(_)_
     @@()@@ wWWWw  (_)\    (___)   _(_)_  @@()@@   Y  (_)@(_)
      @@@@  (___)     `|/    Y    (_)@(_)  @@@@   \|/   (_)\
       /      Y       \|    \|/    /(_)    \|      |/      |
    \ |     \ |/       | / \ | /  \|/       |/    \|      \|/
    \\|//   \\|///  \\\|//\\\|/// \|///  \\\|//  \\|//  \\\|// 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        """
        )

        if self.debug:
            self.log.info("In global debug mode")

        if self.mock:
            self.log.info("In global mock mode")

        ######################################################################
        # dynamically import packages
        ######################################################################

        packages_config = utils.get_config_prop(config, "packages")
        self.log.info("Importing packages...")
        self.importer = PackageImporter(packages_config)
        try:
            self.importer.import_packages(mock=self.mock)
        except ModuleNotFoundError as mnfe:
            self.log.error(mnfe)
            sys.exit(1)
        except Exception as e:
            raise e

        ppconfig = self.importer.config_embed_packages(config["piplant"])
        database_config = utils.get_config_prop(ppconfig, "database", required=True)
        display_config = utils.get_config_prop(ppconfig, "display", required=False)
        hygrometers_config = utils.get_config_prop(ppconfig, "hygrometers")
        environment_config = utils.get_config_prop(ppconfig, "environment")
        device_config = utils.get_config_prop(ppconfig, "device")
        lights_config = utils.get_config_prop(ppconfig, "lights", required=False)

        self.database = None
        self.importer = None
        self.schedule_manager = None
        self.motion_trigger_manager = None

        self._display_enabled = utils.get_config_prop(
            display_config, "enabled", default="false", required=False, dehumanized=True
        )
        self._render_schedules = utils.get_config_prop(
            display_config, "refresh_schedule", default=["12:00", "18:00"]
        )
        self._current_render_hour = None

        ######################################################################
        # database
        ######################################################################

        db_driver = utils.get_config_prop(database_config, "driver")
        self.database = Database(db_driver)

        ######################################################################
        # sensors
        ######################################################################

        self.hygrometers = utils.get_config_prop(
            hygrometers_config, "sensors", required=True
        )

        self.environment_sensors = {
            "temperature": [],
            "humidity": [],
            "pressure": [],
            "brightness": [],
        }
        env_temp_config = utils.get_config_prop(
            environment_config, "temperature", required=False
        )
        self.environment_sensors["temperature"] = utils.get_config_prop(
            env_temp_config, "sensors", required=True
        )

        env_hum_config = utils.get_config_prop(
            environment_config, "humidity", required=False
        )
        self.environment_sensors["humidity"] = utils.get_config_prop(
            env_hum_config, "sensors", required=True
        )

        env_press_config = utils.get_config_prop(
            environment_config, "pressure", required=False
        )
        self.environment_sensors["pressure"] = utils.get_config_prop(
            env_press_config, "sensors", required=True
        )

        env_bright_config = utils.get_config_prop(
            environment_config, "brightness", required=False
        )
        self.environment_sensors["brightness"] = utils.get_config_prop(
            env_bright_config, "sensors", required=True
        )

        self.device_sensors = utils.get_config_prop(
            device_config, "sensors", required=True
        )

        ######################################################################
        # light managers
        ######################################################################

        sm_config = utils.get_config_prop(lights_config, "schedule_manager")
        enabled = utils.get_config_prop(
            sm_config, "enabled", default="false", dehumanized=True
        )
        if enabled:
            self.log.info("Initializing lights schedule manager")
            schedules = utils.get_config_prop(sm_config, "schedules", required=True)
            device_groups = utils.get_config_prop(
                sm_config, "device_groups", required=True
            )

            self.schedule_manager = ScheduleManager(schedules, device_groups)

        mtm_config = utils.get_config_prop(lights_config, "motion_trigger_manager")
        enabled = utils.get_config_prop(mtm_config, "enabled", default="false")
        enabled = utils.dehumanize(enabled)

        if enabled:
            self.log.info("Initializing light motion trigger manager")
            motion_sensors = utils.get_config_prop(mtm_config, "sensors", required=True)
            device_groups = utils.get_config_prop(
                mtm_config, "device_groups", required=True
            )
            on_motion_trigger_config = utils.get_config_prop(
                mtm_config, "on_motion_trigger", required=True
            )
            on_motion_timeout_config = utils.get_config_prop(
                mtm_config, "on_motion_timeout", required=True
            )
            timeout = utils.get_config_prop(mtm_config, "timeout")

            self.motion_trigger_manager = MotionTriggerManager(
                motion_sensors,
                on_motion_trigger_config,
                on_motion_timeout_config,
                device_groups,
                timeout=timeout,
            )

        ######################################################################
        # display package
        ######################################################################

        if self._display_enabled:
            self.log.info("Initializing display")
            display_driver = utils.get_config_prop(display_config, "driver")

            skip_splash_screen = utils.get_config_prop(
                display_config, "skip_splash_screen", default="false", dehumanized=True
            )

            self.display = EPaper(display_driver, display_config, debug=self.debug)
            if not skip_splash_screen:
                self.display.draw_splash_screen()
            self.log.info("Display initialized")

        self._value = dict()

        self.log.info(
            "PiPlant initialized: fetching data every {} seconds".format(
                self._poll_interval_seconds
            )
        )

    def get_value(self):
        self.log.debug("Fetching...")

        hygrometer_data = []
        for sensor in self.hygrometers:
            hygrometer_data.append(sensor.data)

        environment_data = dict()
        for sensortype, sensors in self.environment_sensors.items():
            sensordata = []
            for sensor in sensors:
                sensordata.append(sensor.data)
            environment_data[sensortype] = sensordata

        device_data = []
        for sensor in self.device_sensors:
            device_data.append(sensor.data)

        payload = DataPayload(hygrometer_data, environment_data, device_data)

        return payload

    def process(self, data):
        self.log.debug("Processing...")

        if self.schedule_manager is not None:
            self.schedule_manager.process()

        if self.motion_trigger_manager is not None:
            self.motion_trigger_manager.process()

        self.database.handle_data_payload(data)

        self._process_time = time.time()

    def render(
        self,
    ):
        nowdate = datetime.datetime.now()
        latest_render_hour = None
        for render_hour in self._render_schedules:
            render_hour_dt = utils.hour_to_datetime(render_hour)

            if nowdate >= render_hour_dt:
                latest_render_hour = render_hour_dt

        if self._current_render_hour != latest_render_hour:
            self.log.debug("Rendering...")
            data = self._value

            if self._display_enabled:
                self.display.draw_data(data)
                self.display.sleep()

            self._render_time = time.time()
            self._current_render_hour = latest_render_hour

    def poll_pause(self):
        seconds = self._poll_interval_seconds
        self.log.debug("Pausing for {} seconds...".format(seconds))
        time.sleep(seconds)


if __name__ == "__main__":
    args = parser.parse_args()

    config = yaml.safe_load(args.config)
    if "piplant" not in config:
        raise ValueError("PiPlant config not found - is this the correct config file?")

    ppm = PiPlant(config, mock=args.mock, debug=args.debug)

    while True:
        data = ppm.value
        ppm.process(data)
        ppm.render()
        ppm.poll_pause()
