import time
import logging
import threading
import util.utils as utils
from .pil.pil import PILUtil
from datetime import datetime
from core.sensor_manager.sensor import Sensor


class DisplayManager:
    WATER_PERCENT_0_DEGREES = 90
    WATER_PERCENT_100_DEGREES = 330

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

        # write display to file and don't sent to e-Paper
        self.debug = debug
        self.driver = driver

        self.sensor_manager = sensor_manager
        self.database_manager = database_manager

        self._refresh_schedule = refresh_schedule
        self._current_render_hour = None
        self._render_time = 0

        self.width = self.driver.height
        self.height = self.driver.width
        self.util = PILUtil(self.width, self.height)

        self.plant_bmp_margin_ratio = 1.2
        self.header_height = self.height * 0.12
        self.margin_px = 5

        self._step_wait_seconds = 20

        self.log.info("Initialized")

        if splash_screen:
            self.draw_splash_screen()

    def run(self):
        nowdate = datetime.now()
        latest_render_hour = None
        for render_hour in self._refresh_schedule:
            render_hour_dt = utils.hour_to_datetime(render_hour)

            if nowdate >= render_hour_dt:
                latest_render_hour = render_hour_dt

        if self._current_render_hour != latest_render_hour:
            self.draw_data()
            self.sleep()

            self._render_time = time.time()
            self._current_render_hour = latest_render_hour

    def flush(self):
        self.log.debug("Flushing")
        frame = self.util.new_frame(self.util.MODE_4GRAY)
        self.draw_to_display(frame)

    def draw_splash_screen(self):
        self.flush()
        self.log.debug("Drawing splash screen")
        frame = self.util.new_frame(self.util.MODE_4GRAY)

        # center text in display
        sizeW, sizeH = self.util.logo_size_large
        x = self.width / 2
        y = self.height / 2 + sizeH / 2
        self.util.draw_image("logo.png", x, y, (sizeW, sizeH))

        self.draw_to_display(frame)
        self.pause(2)

    def draw_header(self):
        self.log.debug("Drawing header")

        sizeW, sizeH = self.util.logo_size_small
        x, y = (sizeW / 2 + 1, self.height - sizeH / 2 - 1)
        self.util.draw_image("logo.png", x, y, (sizeW, sizeH))

        now = datetime.now()
        dt_txt = now.strftime("%H:%M\n%d/%m/%Y")
        font = self.util.get_font(type="medium", size=self.util.text_size_tiny)
        tW, tH = self.util.textsize(dt_txt, font)
        rW, rH = tW + self.margin_px * 2, tH + self.margin_px * 2
        x, y = self.width - tW / 2, self.height - tH / 2
        self.util.draw_rectangle(
            x - rW / 2,
            y + rH / 2,
            rW,
            rH,
            fill=self.driver.GRAY4,
            outline=self.driver.GRAY4,
            radius=1,
        )
        self.util.draw_text(font, dt_txt, x, y, fill=self.driver.GRAY1, align="center")

    def draw_hygrometers(self, hygrometers):
        def draw_hygrometer(hygrometer, coords):
            def percentage_angle_in_range(minAng, maxAng, val_percent):
                return int(minAng + (maxAng - minAng) * (val_percent / 100))

            sensor_val_percent = hygrometer.moisture_percentage
            poor_water = hygrometer.is_dry
            poor_water_percent = hygrometer.dry_value_percentage
            draw_value_text = False
            value_text = str(sensor_val_percent) + "%"
            # warning = data["error"]
            warning = None

            font = self.util.get_font(type="medium", size=self.util.text_size_tiny)
            coords_x, coords_y = coords

            sensor_icon = "plant.png"
            water_icon = "water.png"
            dry_warning_icon = "dry_warning.png"
            warning_icon = "warning.png"

            # plant icon params
            icon_medW, _ = self.util.icon_size_very_large
            iX, iY = self.util.round(coords_x, coords_y)
            # get arc params
            cX, cY = iX, iY
            r = icon_medW / 1.5
            # get angles in circle for water levels
            min_ang = self.WATER_PERCENT_0_DEGREES
            max_ang = self.WATER_PERCENT_100_DEGREES

            poor_water_level_ang = percentage_angle_in_range(
                min_ang, max_ang, poor_water_percent
            )
            water_level_ang = percentage_angle_in_range(
                min_ang, max_ang, sensor_val_percent
            )

            if poor_water:
                poor_water_level_ang = water_level_ang

            # draw plant icon
            self.util.draw_image(sensor_icon, iX, iY, self.util.icon_size_large)

            if warning:
                self.util.draw_image(warning_icon, iX, iY, self.util.icon_size_small)
            else:
                # draw dry level
                self.util.draw_dashed_arc(
                    cX,
                    cY,
                    r,
                    min_ang,
                    poor_water_level_ang,
                    fill=self.driver.GRAY4,
                    width=1,
                )
                # draw water remaining
                self.util.draw_arc(
                    cX,
                    cY,
                    r,
                    poor_water_level_ang,
                    water_level_ang,
                    fill=self.driver.GRAY4,
                    width=1,
                )
                # get start point on arc to draw water level
                sX, sY = self.util.point_on_circle(cX, cY, r, min_ang)
                self.util.draw_circle(sX, sY, 3, fill="white")
                # get end point on arc to draw water level
                eX, eY = self.util.point_on_circle(cX, cY, r, max_ang)
                self.util.draw_circle(eX, eY, 3, fill="white")
                # water icon coords
                wiX, wiY = self.util.point_on_circle(cX, cY, r, water_level_ang)

                icon = water_icon if not poor_water else dry_warning_icon
                self.util.draw_image(icon, wiX, wiY, self.util.icon_size_tiny)

            # draw sensor id
            sensor_id = hygrometer.name
            tW, tH = font.getsize(sensor_id)
            tX, tY = cX, cY + r * 1.5
            self.util.draw_text(font, sensor_id, tX, tY)

            if draw_value_text:
                # draw percentage text
                tW, tH = font.getsize(value_text)
                tX, tY = iX - tW / 1.5, iY + tH / 2
                self.util.draw_text(font, value_text, tX, tY)

        def inverse_pyramid(x, y, colw, rowh, max_items, max_cols_per_row):
            def chunks(lst, n):
                """Yield successive n-sized chunks from lst."""
                for i in range(0, len(lst), n):
                    yield lst[i : i + n]

            coords = []
            items = range(0, max_items)
            x, y = self.util.translate(x, y)

            row_idx = 0
            for i in chunks(items, max_cols_per_row):
                row_y = y + (row_idx * rowh)
                col_start_x = x + (row_idx * (colw / 2))

                col_idx = 0
                for _ in i:
                    col_x = col_start_x + colw * col_idx
                    coords.append((col_x, row_y))

                    col_idx += 1

                row_idx += 1

            return coords

        self.log.debug("Drawing Hygrometer data")

        max_cols_per_row = 3
        col_width = 140
        row_height = 120
        num_sensors = len(hygrometers)

        x = self.width / 2 - col_width
        y = self.height * 0.5

        if num_sensors > max_cols_per_row:
            y = self.height * 0.7

        coords = inverse_pyramid(
            x, y, col_width, row_height, num_sensors, max_cols_per_row
        )

        for idx, hygrometer in enumerate(hygrometers):
            draw_hygrometer(hygrometer, coords[idx])

    def draw_environment_data(
        self,
        temperature_sensors,
        humidity_sensors,
        pressure_sensors,
        brightness_sensors,
        device_sensors,
    ):
        def draw_sensor_data(icon, data, sensor_unit_txt, x, y):
            iW, iH = self.util.icon_size_medium
            sensor_txt = str(data)
            font = self.util.get_font(type="bold", size=self.util.text_size_large)
            tW, _ = font.getsize(sensor_txt)
            iX, iY = (
                x + iW / 2,
                y - iH / 1.5,
            )
            self.util.draw_image(icon, iX, iY, (iW, iH))
            tX, tY = x + iW + tW / 2, y
            self.util.draw_text(font, sensor_txt, x + iW + tW / 2, y)
            font = self.util.get_font(type="thin", size=self.util.text_size_medium)
            tuW, tuH = font.getsize(sensor_unit_txt)
            tX, tY = tX + tW / 2 + tuW / 2, tY - tuH / 2
            self.util.draw_text(font, sensor_unit_txt, tX, tY)

        self.log.debug("Drawing environment data")

        x, y = 0, self.height - self.header_height
        row_height = self.height * 0.45
        outside_txt = "OFFBOARD"
        inside_txt = "ONBOARD"
        font = self.util.get_font(size=self.util.text_size_medium)
        o_tW, _ = font.getsize(outside_txt)
        i_tW, _ = font.getsize(inside_txt)
        x, y = self.margin_px + o_tW / 2, self.height - self.header_height * 1.3

        self.util.draw_text(font, outside_txt, x, y)
        self.util.draw_line(
            x + o_tW / 2 + self.margin_px,
            y - 2,
            self.width - self.margin_px * 2,
            y - 2,
            width=2,
        )

        x, y = self.margin_px + i_tW / 2, y - row_height
        self.util.draw_text(font, inside_txt, x, y)
        self.util.draw_line(
            x + i_tW / 2 + self.margin_px,
            y - 2,
            self.width - self.margin_px * 2,
            y - 2,
            width=2,
        )

        outside_row_y = self.height - self.header_height - row_height / 2
        inside_row_y = self.height - self.header_height - row_height - row_height / 2
        init_x = self.width * 0.01
        sensor_margin = self.width * 0.2

        icon = "ext_temp.png"
        value = utils.avg([s.temperature for s in temperature_sensors])
        sensor_unit_txt = "\N{DEGREE SIGN}C"
        x = init_x
        draw_sensor_data(icon, value, sensor_unit_txt, x, outside_row_y)

        icon = "ext_temp.png"
        value = utils.avg([s.cpu_temperature for s in device_sensors])
        sensor_unit_txt = "\N{DEGREE SIGN}C"
        x = init_x
        draw_sensor_data(icon, value, sensor_unit_txt, x, inside_row_y)

        icon = "brightness.png"
        value = utils.avg([s.brightness for s in brightness_sensors])
        sensor_unit_txt = "lux"
        x = init_x + sensor_margin * 3
        draw_sensor_data(icon, value, sensor_unit_txt, x, outside_row_y)

        icon = "humidity.png"
        value = utils.avg([s.humidity for s in humidity_sensors])
        sensor_unit_txt = "%"
        x = init_x + sensor_margin * 1.6
        draw_sensor_data(icon, value, sensor_unit_txt, x, inside_row_y)

        icon = "pressure.png"
        value = utils.avg([s.pressure for s in pressure_sensors])
        sensor_unit_txt = "hPa"
        x = init_x + sensor_margin * 3
        draw_sensor_data(icon, value, sensor_unit_txt, x, inside_row_y)

    def draw_historical_data(self, hours):
        self.log.debug("Drawing Historical data")
        pass

    def draw_data(self):
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

            # new display frame
            self.util.new_frame(self.util.MODE_4GRAY)

            # draw data
            self.draw_header()

            if step == self.STEP_HYGROMETER:
                hygrometers = self.sensor_manager.get_hygrometers()
                self.draw_hygrometers(hygrometers)

            if step == self.STEP_ENVIRONMENT:
                temperature_sensors = self.sensor_manager.get_temperature_sensors()
                humidity_sensors = self.sensor_manager.get_humidity_sensors()
                pressure_sensors = self.sensor_manager.get_pressure_sensors()
                brightness_sensors = self.sensor_manager.get_brightness_sensors()
                device_sensors = self.sensor_manager.get_device_sensors()
                self.draw_environment_data(
                    temperature_sensors,
                    humidity_sensors,
                    pressure_sensors,
                    brightness_sensors,
                    device_sensors,
                )

            if step == self.STEP_24HR_HISTORICAL:
                self.draw_historical_data(self.HOURS_IN_DAY)

            if step == self.STEP_7DAY_HISTORICAL:
                self.draw_historical_data(self.HOURS_IN_WEEK)

            # draw frame display
            frame = self.util.get_frame()
            self.draw_to_display(frame)

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
