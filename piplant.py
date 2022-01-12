import sys
import os
import yaml
import math
import time
import argparse
import logging.config
import util.utils as utils
from package.package import DynamicPackage
from display.epaper import EPaper
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

        packages_config = utils.get_config_prop(config, "packages")

        ppconfig = config["piplant"]
        display_config = utils.get_config_prop(ppconfig, "display", required=False)
        hygrometers_config = utils.get_config_prop(ppconfig, "hygrometers")
        environment_config = utils.get_config_prop(ppconfig, "environment")
        device_config = utils.get_config_prop(ppconfig, "device")
        lights_config = utils.get_config_prop(ppconfig, "lights", required=False)

        self.schedule_manager = None
        self.motion_trigger_manager = None

        self._display_enabled = utils.get_config_prop(
            display_config, "enabled", default="false", required=False, dehumanized=True
        )
        self._render_interval_seconds = utils.get_config_prop(
            display_config, "refresh_interval", default="1hr", dehumanized=True
        )

        self.log.info(
            r"""\
            
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

        self.log.info("Initializing packages...")
        self._package_instances = dict()
        try:
            self._package_instances = self._get_package_instances_from_config(
                packages_config, self.mock
            )
        except ModuleNotFoundError as mnfe:
            self.log.error(mnfe)
            sys.exit(1)
        except Exception as e:
            raise e

        ######################################################################
        # sensor packages
        ######################################################################

        self.log.info("Initializing sensors")
        self.hygrometers = self.get_pkg_instances_from_sensor_config(hygrometers_config)

        self.environment_sensors = {
            "temperature": [],
            "humidity": [],
            "pressure": [],
            "brightness": [],
        }
        env_temp_config = utils.get_config_prop(
            environment_config, "temperature", required=False
        )
        self.environment_sensors[
            "temperature"
        ] = self.get_pkg_instances_from_sensor_config(env_temp_config)

        env_hum_config = utils.get_config_prop(
            environment_config, "humidity", required=False
        )
        self.environment_sensors[
            "humidity"
        ] = self.get_pkg_instances_from_sensor_config(env_hum_config)

        env_press_config = utils.get_config_prop(
            environment_config, "pressure", required=False
        )
        self.environment_sensors[
            "pressure"
        ] = self.get_pkg_instances_from_sensor_config(env_press_config)

        env_bright_config = utils.get_config_prop(
            environment_config, "brightness", required=False
        )
        self.environment_sensors[
            "brightness"
        ] = self.get_pkg_instances_from_sensor_config(env_bright_config)

        self.device_sensors = self.get_pkg_instances_from_sensor_config(device_config)

        ######################################################################
        # light manager packages
        ######################################################################

        sm_config = utils.get_config_prop(lights_config, "schedule_manager")
        enabled = utils.get_config_prop(
            sm_config, "enabled", default="false", dehumanized=True
        )
        if enabled:
            self.log.info("Initializing lights schedule manager")
            schedules = utils.get_config_prop(sm_config, "schedules", required=True)
            device_groups_config = utils.get_config_prop(
                sm_config, "device_groups", required=True
            )
            package_refs = utils.get_config_prop(
                device_groups_config, "package_refs", required=True
            )
            device_groups = self.get_package_instances(package_refs)

            self.schedule_manager = ScheduleManager(schedules, device_groups)

        mtm_config = utils.get_config_prop(lights_config, "motion_trigger_manager")
        enabled = utils.get_config_prop(mtm_config, "enabled", default="false")
        enabled = utils.dehumanize(enabled)

        if enabled:
            self.log.info("Initializing light motion trigger manager")
            motion_sensors_config = utils.get_config_prop(
                mtm_config, "sensors", required=True
            )
            package_refs = utils.get_config_prop(
                motion_sensors_config, "package_refs", required=True
            )
            motion_sensors = self.get_package_instances(package_refs)

            device_groups_config = utils.get_config_prop(
                mtm_config, "device_groups", required=True
            )
            package_refs = utils.get_config_prop(
                device_groups_config, "package_refs", required=True
            )
            device_groups = self.get_package_instances(package_refs)

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

        self.log.info("Packages initialized")

        ######################################################################
        # display package
        ######################################################################

        if self._display_enabled:
            self.log.info("Initializing display")
            driver_config = utils.get_config_prop(display_config, "driver")
            packageref = utils.get_config_prop(driver_config, "package_ref")
            display_driver = self.get_package_instance(packageref)

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
            sensordata = []
            for sensor in sensors:
                sensordata.append(sensor.data)
            device_data.append(sensordata)

        data_payload = {
            "hygrometer": hygrometer_data,
            "environment": environment_data,
            "device": device_data,
        }

        return data_payload

    def process(self, data):
        self.log.debug("Processing...")

        _ = self._value

        if self.schedule_manager is not None:
            self.schedule_manager.process()

        if self.motion_trigger_manager is not None:
            self.motion_trigger_manager.process()

        self._process_time = time.time()

        # save to db
        # print(data)
        return None

    def render(
        self,
    ):
        now = time.time()
        seconds_since_render = math.ceil(now - self._render_time)
        if seconds_since_render >= self._render_interval_seconds:
            self.log.debug("Rendering...")
            data = self._value

            if self._display_enabled:
                self.display.draw_data(data)
                self.display.sleep()

            self._render_time = time.time()

    def poll_pause(self):
        seconds = self._poll_interval_seconds
        self.log.debug("Pausing for {} seconds...".format(seconds))
        time.sleep(seconds)

    def get_package_instance(self, name):
        return self._package_instances[name]

    def get_package_instances(self, names):
        return [self.get_package_instance(name) for name in names]

    def _get_package_instances_from_config(self, packages, mock=False):
        instances = dict()
        for pkg in packages:
            name = utils.get_config_prop(pkg, "name", required=True)
            package = utils.get_config_prop(pkg, "package", required=True)
            kwargs = utils.get_config_prop(package, "kwargs", required=False)

            if kwargs is not None:
                paths = utils.find_paths_to_key(kwargs, "package_refs")
                for keys in paths:
                    package_refs = utils.get_by_path(kwargs, keys)
                    insts = [instances[name] for name in package_refs]
                    utils.del_by_path(kwargs, keys)
                    utils.set_by_path(kwargs, keys[:-1], insts)

                paths = utils.find_paths_to_key(kwargs, "package_ref")
                for keys in paths:
                    package_ref = utils.get_by_path(kwargs, keys)
                    inst = instances[package_ref]
                    utils.del_by_path(kwargs, keys)
                    utils.set_by_path(kwargs, keys[:-1], inst)

            instance = DynamicPackage(package, mock)
            instances[name] = instance

        return instances

    def get_pkg_instances_from_sensor_config(self, config):
        sensor_config = utils.get_config_prop(config, "sensors", required=True)
        package_refs = utils.get_config_prop(
            sensor_config, "package_refs", required=True
        )

        return self.get_package_instances(package_refs)


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
