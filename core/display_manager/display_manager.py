import time
import logging
import threading
import util.utils as utils
from datetime import datetime
from .view.page.device import DevicePage
from .view.page.live_data import LiveDataPage
from .view.page.splash_screen import SplashScreenPage
from .view.page.historical_data import HistoricalDataPage


class DisplayManager:
    STEP_ENVIRONMENT = 0
    STEP_24HR_HISTORICAL = 1
    STEP_7DAY_HISTORICAL = 2
    STEP_DEVICE = 3
    STEP_LIVEDATA = 4
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

        self.splash_screen_page = SplashScreenPage(driver.height, driver.width)
        self.livedata_page = LiveDataPage(sensor_manager, driver.height, driver.width)
        self.historical_data_page = HistoricalDataPage(
            database_manager, driver.height, driver.width
        )
        self.device_page = DevicePage(sensor_manager, driver.height, driver.width)

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

    def display_page(self, page):
        frame = page.draw()
        self.draw_to_display(frame)

    def display_pages(self):
        # steps = [
        #     self.STEP_LIVEDATA,
        #     self.STEP_WAIT,
        #     self.STEP_ENVIRONMENT,
        #     self.STEP_WAIT,
        #     # self.STEP_24HR_HISTORICAL,
        #     # self.STEP_7DAY_HISTORICAL,
        #     # self.STEP_DEVICE,
        #     self.STEP_LIVEDATA,
        # ]
        steps = [
            self.STEP_LIVEDATA,
        ]

        for step in steps:
            if step == self.STEP_WAIT:
                self.pause(self._step_wait_seconds)
                continue

            if step == self.STEP_LIVEDATA:
                self.display_page(self.livedata_page)

            if step == self.STEP_ENVIRONMENT:
                self.display_page(self.environment_page)

            if step == self.STEP_24HR_HISTORICAL:
                self.display_page(self.historical_data_page)

            if step == self.STEP_7DAY_HISTORICAL:
                self.display_page(self.historical_data_page)

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
