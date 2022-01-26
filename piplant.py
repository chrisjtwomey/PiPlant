import sys
import os
import yaml
import time
import argparse
import schedule
import threading
import logging.config
import util.utils as utils
from package.package import PackageImporter
from core.sensor_manager.sensor_manager import SensorManager
from core.display_manager.display_manager import DisplayManager
from core.database_manager.database_manager import DatabaseManager
from core.schedule_manager.schedule_manager import ScheduleManager
from core.motion_trigger_manager.motion_trigger_manager import (
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
    "-p",
    "--packages",
    type=argparse.FileType("r"),
    required=True,
    help="The path of the packages yaml",
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


class PiPlant:
    def __init__(self, config, packages_config, mock=False, debug=False):
        template_path = os.path.join(cwd, "template")
        logging_cfg_path = os.path.join(template_path, "logging.ini")
        if debug:
            logging_cfg_path = os.path.join(template_path, "logging.dev.ini")
        logging.config.fileConfig(logging_cfg_path)
        self.log = logging.getLogger("PiPlant")

        self.debug = debug
        self.mock = mock

        if self.debug:
            self.log.info("In global debug mode")
        if self.mock:
            self.log.info("In global mock mode")

        self.database_manager = None
        self.display_manager = None
        self.schedule_manager = None
        self.sensor_manager = None
        self.motion_trigger_manager = None

        # dynamically import packages
        self.log.info("Importing packages...")
        self.package_importer = PackageImporter(packages_config)
        try:
            self.package_importer.import_packages(mock=self.mock)
            config = self.package_importer.config_embed_packages(config)
        except ModuleNotFoundError as mnfe:
            self.log.error(mnfe)
            sys.exit(1)
        except Exception as e:
            raise e

        # database manager
        db_driver = utils.get_config_prop_by_keys(config, "database_manager", "driver")
        self.database_manager = DatabaseManager(db_driver)

        # sensor manager
        sensors = utils.get_config_prop_by_keys(config, "sensor_manager", "sensors")
        self.sensor_manager = SensorManager(sensors, self.database_manager)

        # schedule manager
        enabled = utils.get_config_prop_by_keys(
            config, "schedule_manager", "enabled", default="false", dehumanized=True
        )
        if enabled:
            self.log.info("Initializing lights schedule manager")
            schedules = utils.get_config_prop_by_keys(
                config, "schedule_manager", "schedules", required=True
            )
            device_groups = utils.get_config_prop_by_keys(
                config, "schedule_manager", "device_groups", required=True
            )

            self.schedule_manager = ScheduleManager(device_groups, schedules)

        # motion trigger manager
        enabled = utils.get_config_prop_by_keys(
            config,
            "motion_trigger_manager",
            "enabled",
            default="false",
            dehumanized=True,
        )

        if enabled:
            self.log.info("Initializing light motion trigger manager")
            motion_sensors = utils.get_config_prop_by_keys(
                config, "motion_trigger_manager", "sensors", required=True
            )
            device_groups = utils.get_config_prop_by_keys(
                config, "motion_trigger_manager", "device_groups", required=True
            )
            on_motion_trigger_config = utils.get_config_prop_by_keys(
                config, "motion_trigger_manager", "on_motion_trigger", required=True
            )
            on_motion_timeout_config = utils.get_config_prop_by_keys(
                config, "motion_trigger_manager", "on_motion_timeout", required=True
            )
            timeout_seconds = utils.get_config_prop_by_keys(
                config,
                "motion_trigger_manager",
                "timeout",
                required=True,
                dehumanized=True,
            )

            self.motion_trigger_manager = MotionTriggerManager(
                device_groups,
                motion_sensors,
                on_motion_trigger_config,
                on_motion_timeout_config,
                timeout_seconds,
            )

        # display manager
        display_config = utils.get_config_prop(
            config, "display_manager", required=False
        )
        display_enabled = utils.get_config_prop(
            display_config, "enabled", default="false", required=False, dehumanized=True
        )

        if display_enabled:
            display_driver = utils.get_config_prop(display_config, "driver")
            refresh_schedules = utils.get_config_prop(
                display_config, "refresh_schedule", default=["12:00", "18:00"]
            )
            skip_splash_screen = utils.get_config_prop(
                display_config, "skip_splash_screen", default="false", dehumanized=True
            )

            self.display_manager = DisplayManager(
                display_driver,
                refresh_schedules,
                splash_screen=not skip_splash_screen,
                debug=self.debug,
            )

    def schedule(self):
        def threaded(func):
            run_thread = threading.Thread(target=func)
            run_thread.start()

        if self.sensor_manager is not None:
            schedule.every().minute.do(threaded, self.sensor_manager.run)

        if self.schedule_manager is not None:
            schedule.every(10).minutes.do(threaded, self.schedule_manager.run)

        if self.motion_trigger_manager is not None:
            schedule.every().second.do(threaded, self.motion_trigger_manager.run)

        if self.display_manager is not None:
            schedule.every().minute.do(threaded, self.display_manager.run)

    def run_once(self):
        schedule.run_all()

    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
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

    args = parser.parse_args()
    config = yaml.safe_load(args.config)
    packages_config = yaml.safe_load(args.packages)

    piplant = PiPlant(config, packages_config, mock=args.mock, debug=args.debug)
    piplant.schedule()
    piplant.run()
