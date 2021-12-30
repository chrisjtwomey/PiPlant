import os
import yaml
import math
import time
import logging.config
import util.utils as utils
import util.package as pkgutils
from display.epaper import EPaper
from sensors.polledsensor import PolledSensor
from light.lifxschedulemanager import LIFXScheduleManager
from light.lifxlivebodydetection import LIFXLiveBodyDetection

cwd = os.path.dirname(os.path.realpath(__file__))


class PiPlant(PolledSensor):

    def __init__(self, config):
        piplantconf = config["piplant"]

        self.debug = utils.dehumanize(
            piplantconf["debug"]) if "debug" in piplantconf else False

        logging_cfg_path = os.path.join(cwd, 'logging.ini')
        if self.debug:
            logging_cfg_path = os.path.join(cwd, 'logging.dev.ini')

        logging.config.fileConfig(logging_cfg_path)

        self._poll_interval_seconds = utils.dehumanize(
            piplantconf["poll_interval"])
        self._render_interval_seconds = utils.dehumanize(
            piplantconf["render_interval"])
        self._process_time = 0
        self._render_time = 0

        super().__init__(self._poll_interval_seconds)

        self.log.info(r"""\
            
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
        """)

        if self.debug:
            self.log.info("DEBUG MODE")

        # sensors
        self.log.info("Initializing sensors...")

        def import_sensors(sensors):
            imported_sensors = []

            for sensor_config in sensors:
                kwargs = sensor_config["kwargs"] if "kwargs" in sensor_config else dict()
                package = sensor_config["package"]
                sensor = pkgutils.get_package_instance(package, **kwargs)
                imported_sensors.append(sensor)

            return imported_sensors

        sensorsconfig = piplantconf["sensors"]

        hygrometers_config = sensorsconfig["hygrometers"] if "hygrometers" in sensorsconfig else []
        self.hygrometers = import_sensors(hygrometers_config)

        environment_config = sensorsconfig["environment"] if "environment" in sensorsconfig else []
        self.environment_sensors = import_sensors(environment_config)

        device_config = sensorsconfig["device"] if "device" in sensorsconfig else []
        self.device_sensors = import_sensors(device_config)

        self.log.info("Sensors initialized")

        # processors
        self.log.info("Initializing processors...")
        # TODO: check type of manager
        lmconf = config["lightmanager"]
        self.schedulemanager = LIFXScheduleManager(lmconf, debug=self.debug)
        self.livebodydetection = LIFXLiveBodyDetection(
            lmconf, debug=self.debug)
        self.log.info("Processors initialized")

        # renderers
        self.log.info("Initializing display...")
        dconf = config["display"]
        self._display_enabled = utils.dehumanize(dconf["enabled"])

        if self._display_enabled:
            package = dconf["package"]
            kwargs = dconf["kwargs"]
            skip_splash_screen = utils.dehumanize(
                dconf["skip_splash_screen"]) if "skip_splash_screen" in dconf else False
            epd = pkgutils.get_package_instance(package, **kwargs)

            self.display = EPaper(epd, dconf, debug=self.debug)
            if not skip_splash_screen:
                self.display.draw_splash_screen()
            self.log.info("Display initialized")

        self._value = dict()

        self.log.info("PiPlant initialized: fetching data every {} seconds".format(
            self._poll_interval_seconds))

    def get_value(self):
        self.log.info("Fetching...")

        hygrometer_data = []
        for sensor in self.hygrometers:
            hygrometer_data.append(sensor.value)

        environment_data = []
        for sensor in self.environment_sensors:
            environment_data.append(sensor.value)

        device_data = []
        for sensor in self.device_sensors:
            device_data.append(sensor.value)

        data_payload = {
            "hygrometer": hygrometer_data,
            "environment": environment_data,
            "device": device_data,
        }

        return data_payload

    def process(self, data):
        self.log.info("Processing...")

        data = self._value
        env_data = data["environment"][0]
        livebody_detection = env_data["livebody_detection"]

        self.schedulemanager.process()
        self.livebodydetection.process(livebody_detection)
        self._process_time = time.time()

        # save to db
        # print(data)
        return None

    def render(self,):
        now = time.time()
        # if time to render
        if math.ceil(now - self._render_time) >= self._render_interval_seconds:
            self.log.info("Rendering...")
            data = self._value

            if self._display_enabled:
                self.display.draw_data(data)
                self.display.sleep()

            self._render_time = time.time()

    def poll_pause(self):
        seconds = self._poll_interval_seconds
        self.log.debug("Pausing for {} seconds...".format(seconds))
        time.sleep(seconds)


if __name__ == '__main__':
    cfg_path = os.path.join(cwd, 'config.yaml')
    with open(cfg_path, "r") as fs:
        config = yaml.safe_load(fs)
        ppm = PiPlant(config)

        while True:
            data = ppm.value
            ppm.process(data)
            ppm.render()
            ppm.poll_pause()
