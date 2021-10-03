import time
import logging

from datetime import datetime
from rpi_epd3in7.epd import EPD
from .util import PILUtil


class EPaper:
    WATER_PERCENT_0_DEGREES = 90
    WATER_PERCENT_100_DEGREES = 330

    def __init__(self):
        self.log = logging.getLogger("e-Paper")
        self.log.debug("Initializing...")

        # write display to file and don't sent to e-Paper
        self.devmode = True

        self.epd = EPD()
        self.width = self.epd.height
        self.height = self.epd.width
        self.util = PILUtil(self.width, self.height)

        self.plant_bmp_margin_ratio = 1.2
        self.header_height = self.height * 0.1
        self.margin_px = 5

        self.icon_size_tiny = (18, 18)
        self.icon_size_small = (32, 32)
        self.icon_size_medium = (48, 48)
        self.icon_size_large = (80, 80)
        self.logo_size_small = (100, 28)
        self.logo_size_large = (168, 60)

        self.log.debug("Initialized")

    def flush(self):
        self.log.debug("Flushing")
        frame = self.util.new_frame(self.util.MODE_4GRAY)
        self.draw_to_display(frame)

    def draw_splash_screen(self):
        self.flush()
        self.log.debug("Drawing splash screen")
        frame = self.util.new_frame(self.util.MODE_4GRAY)

        # center text in display
        sizeW, sizeH = self.logo_size_large
        x = self.width / 2 - sizeW / 2
        y = self.height / 2 + sizeH / 2
        self.util.draw_image("logo.png", x, y, (sizeW, sizeH))

        self.draw_to_display(frame)
        self.delay_ms(2000)

    def draw_header(self):
        self.log.debug("Drawing header")

        sizeW, sizeH = self.logo_size_small
        x, y = (sizeW / 2, self.height - sizeH / 2)
        self.util.draw_image("logo.png", x, y, (sizeW, sizeH))

        x, y = self.margin_px, self.height - self.header_height
        x1, y1 = self.width - self.margin_px, self.height - self.header_height
        self.util.draw_line(x, y, x1, y1)

        now = datetime.now()
        dt_txt = now.strftime("%d/%m/%Y %H:%M")
        sizeW, sizeH = self.util.text_tiny.getsize(dt_txt)
        x, y = self.width - sizeW / 2, self.height - sizeH
        self.util.draw_text(self.util.text_tiny, dt_txt, x, y)

    def draw_soil_moisture_data(self, data):
        def draw_sensor_data(id, data, coords):
            def percentage_angle_in_range(minAng, maxAng, val_percent):
                return int(minAng + (maxAng - minAng) * (val_percent / 100))

            sensor_val_percent = data["value"]
            poor_water = data["needs_water"]
            poor_water_percent = data["needs_water_threshold_percent"]
            draw_value_text = False
            value_text = str(sensor_val_percent) + "%"
            warning = data["error"]

            font = self.util.text_tiny
            coords_x, coords_y = coords

            sensor_icon = data["icon"]
            water_icon = 'water.png'
            dry_warning_icon = 'dry_warning.png'
            warning_icon = 'warning.png'

            # plant icon params
            icon_medW, _ = self.icon_size_large
            iX, iY = self.util.round(coords_x, coords_y)
            # get arc params
            cX, cY = iX, iY
            r = icon_medW / 1.5
            # get angles in circle for water levels
            min_ang = self.WATER_PERCENT_0_DEGREES
            max_ang = self.WATER_PERCENT_100_DEGREES

            poor_water_level_ang = percentage_angle_in_range(
                min_ang, max_ang, poor_water_percent)
            water_level_ang = percentage_angle_in_range(
                min_ang, max_ang, sensor_val_percent)

            if poor_water:
                poor_water_level_ang = water_level_ang

            # draw plant icon
            self.util.draw_image(sensor_icon, iX, iY, self.icon_size_large)

            if warning:
                self.util.draw_image(warning_icon, iX, iY,
                                     self.icon_size_small)
            else:
                # draw dry level
                self.util.draw_dashed_arc(
                    cX, cY, r, min_ang, poor_water_level_ang)
                # draw water remaining
                self.util.draw_arc(
                    cX, cY, r, poor_water_level_ang, water_level_ang)
                # get start point on arc to draw water level
                sX, sY = self.util.point_on_circle(cX, cY, r, min_ang)
                self.util.draw_circle(sX, sY, 3, fill='white')
                # get end point on arc to draw water level
                eX, eY = self.util.point_on_circle(cX, cY, r, max_ang)
                self.util.draw_circle(eX, eY, 3, fill='white')
                # water icon coords
                wiX, wiY = self.util.point_on_circle(
                    cX, cY, r, water_level_ang)

                icon = water_icon if not poor_water else dry_warning_icon
                self.util.draw_image(icon, wiX, wiY, self.icon_size_tiny)

            # draw sensor id
            sensor_id = '#' + str(id)
            tW, tH = font.getsize(sensor_id)
            tX, tY = cX - r, cY + r
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
                    yield lst[i:i + n]

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

        self.log.debug("Drawing soil moisture data")

        max_cols_per_row = 3
        col_width = 140
        row_height = 120
        num_sensors = len(data)
        sensor_ids = range(0, num_sensors)

        x = self.width / 2 - col_width
        y = self.height * 0.77
        coords = inverse_pyramid(
            x, y, col_width, row_height, num_sensors, max_cols_per_row)

        for id in sensor_ids:
            sensor_data = data[id]
            draw_sensor_data(id, sensor_data, coords[id])

    def draw_environment_data(self, data):
        self.log.debug("Drawing environment data")
        origin_x, origin_y = self.util.translate(
            self.width * self.large_col_ratio, self.height - self.header_height - self.margin_px)

        display_vals = {
            "ext_temp": u"\N{DEGREE SIGN}C",
            "onboard_brightness": "Lux",
            "onboard_humidity": "%",
            "baro_pressure": "hPa"
        }

        idx = 0
        for key, unit in display_vals.items():
            sensor_icon = key + ".png"
            sensor_value_txt = str(data[key]) + unit

            sizeW, sizeH = self.icon_size_small

            x = origin_x + self.margin_px
            y = origin_y - self.header_height + 30 + (35 * idx)

            self.util.draw_image(sensor_icon, x, y, (sizeW, sizeH))

            x, y = x + sizeW + self.margin_px, y + 2

            self.util.draw_text(self.util.text_small, sensor_value_txt, x, y)

            idx += 1

    def draw_data(self, data):
        soil_moisture_data = data["soil_moisture"]
        enviroment_data = data["environment"]
        device_data = data["device"]

        self.flush()
        # new display frame
        self.util.new_frame(self.util.MODE_1GRAY)

        # draw data
        self.draw_header()
        self.draw_soil_moisture_data(soil_moisture_data)
        # self.draw_environment_data(enviroment_data)

        # draw frame display
        frame = self.util.get_frame()
        self.draw_to_display(frame)

    def draw_to_display(self, frame):
        if self.devmode:
            frame.save("static/testframe.png")
        else:
            self.epd.init()
            self.epd.clear()
            self.epd.display(frame)

    def sleep(self):
        if not self.devmode:
            self.epd.sleep()

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)
