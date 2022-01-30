import time
import logging
import threading
import util.utils as utils
from datetime import datetime
from .page.device_page import DevicePage
from .page.hygrometer_page import HygrometerPage
from .page.environment_page import EnvironmentPage
from .page.splash_screen_page import SplashScreenPage
from .page.historical_data_page import HistoricalDataPage


class DisplayManager:
    STEP_ENVIRONMENT = 0
    STEP_24HR_HISTORICAL = 1
    STEP_7DAY_HISTORICAL = 2
    STEP_DEVICE = 3
    STEP_HYGROMETER = 4
    STEP_WAIT = 5
    HOURS_IN_DAY = 24
    HOURS_IN_WEEK = 168

    def __init__(
        self,
        driver,
        sensor_manager,
        database_manager,
        refresh_schedule,
        splash_screen=True,
        debug=False,
    ):
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.debug("Initializing...")

        self.debug = debug
        self.driver = driver

        self.splash_screen_page = SplashScreenPage(
            sensor_manager, database_manager, driver.height, driver.width
        )
        self.hygrometer_page = HygrometerPage(
            sensor_manager, database_manager, driver.height, driver.width
        )
        self.environment_page = EnvironmentPage(
            sensor_manager, database_manager, driver.height, driver.width
        )
        self.historical_data_page = HistoricalDataPage(
            sensor_manager, database_manager, driver.height, driver.width
        )
        self.device_page = DevicePage(
            sensor_manager, database_manager, driver.height, driver.width
        )

        self._refresh_schedule = refresh_schedule
        self._current_render_hour = None
        self._render_time = 0

        self._step_wait_seconds = 20

        self.log.info("Initialized")
        self.log.debug("Refresh schedule:   {}".format(self._refresh_schedule))

        if splash_screen:
            self.display_page(self.splash_screen_page)
            self.pause(2)

    def run(self):
        nowdate = datetime.now()
        latest_render_hour = None
        for render_hour in self._refresh_schedule:
            render_hour_dt = utils.hour_to_datetime(render_hour)

            if nowdate >= render_hour_dt:
                latest_render_hour = render_hour_dt

        if self._current_render_hour != latest_render_hour:
            self.display_pages()
            # self.sleep()

            self._render_time = time.time()
            self._current_render_hour = latest_render_hour

    def flush(self):
        self.log.debug("Flushing")
        frame = self.util.new_frame(self.util.MODE_4GRAY)
        self.draw_to_display(frame)

    def display_page(self, page):
        self.log.debug("Rendering page {}".format(page.__class__.__name__))
        # self.flush()
        frame = page.draw()
        self.draw_to_display(frame)

    def display_pages(self):
        steps = [
            self.STEP_HYGROMETER,
            self.STEP_WAIT,
            self.STEP_ENVIRONMENT,
            self.STEP_WAIT,
            # self.STEP_24HR_HISTORICAL,
            # self.STEP_7DAY_HISTORICAL,
            # self.STEP_DEVICE,
            self.STEP_HYGROMETER,
        ]

        for step in steps:
            if step == self.STEP_WAIT:
                self.pause(self._step_wait_seconds)
                continue

            if step == self.STEP_HYGROMETER:
                self.display_page(self.hygrometer_page)

            if step == self.STEP_ENVIRONMENT:
                self.display_page(self.environment_page)

            if step == self.STEP_24HR_HISTORICAL:
                # self.draw_historical_data(self.HOURS_IN_DAY)
                pass

            if step == self.STEP_7DAY_HISTORICAL:
                # self.draw_historical_data(self.HOURS_IN_WEEK)
                pass

    def draw_to_display(self, frame, block_execution=False):
        def draw():
            self.driver.init()
            self.driver.clear()
            self.driver.display(frame)

        t = threading.Thread(target=draw)
        t.start()

        if block_execution:
            t.join()

    def sleep(self):
        if not self.debug:
            self.driver.sleep()

    def pause(self, seconds):
        self.log.debug("Pausing for {} second(s)...".format(seconds))
        self._delay_ms(seconds * 1000)

    def _delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)
