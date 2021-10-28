import time
import logging

from datetime import datetime
from rpi_epd3in7.epd import EPD
from .util import PILUtil


class EPaper:
    WATER_PERCENT_0_DEGREES = 90
    WATER_PERCENT_100_DEGREES = 330

    STEP_ENVIRONMENT = 0
    STEP_24HR_HISTORICAL = 1
    STEP_7DAY_HISTORICAL = 2
    STEP_DEVICE = 3
    STEP_SOIL_MOISTURE = 4
    HOURS_IN_DAY = 24
    HOURS_IN_WEEK = 168

    def __init__(self, config):
        self.log = logging.getLogger("e-Paper")
        self.log.debug("Initializing...")

        # write display to file and don't sent to e-Paper
        self.devmode = config.getboolean('dev_mode')

        self.epd = EPD()
        self.width = self.epd.height
        self.height = self.epd.width
        self.util = PILUtil(self.width, self.height)

        self.step = self.STEP_ENVIRONMENT

        self.plant_bmp_margin_ratio = 1.2
        self.header_height = self.height * 0.12
        self.margin_px = 5

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
        sizeW, sizeH = self.util.logo_size_large
        x = self.width / 2 - sizeW / 2
        y = self.height / 2 + sizeH / 2
        self.util.draw_image("logo.png", x, y, (sizeW, sizeH))

        self.draw_to_display(frame)
        self.delay_ms(2000)

    def draw_header(self):
        self.log.debug("Drawing header")

        sizeW, sizeH = self.util.logo_size_small
        x, y = (sizeW / 2 + 1, self.height - sizeH / 2 - 1)
        self.util.draw_image("logo.png", x, y, (sizeW, sizeH))

        now = datetime.now()
        dt_txt = now.strftime("%H:%M\n%d/%m/%Y")
        font = self.util.get_font(type='medium', size=self.util.text_size_tiny)
        tW, tH = self.util.textsize(dt_txt, font)
        rW, rH = tW + self.margin_px * 2, tH + self.margin_px * 2
        x, y = self.width - tW / 2, self.height - tH / 2
        self.util.draw_rectangle(x - rW / 2, y + rH / 2, rW, rH, fill=self.epd.GRAY4, outline=self.epd.GRAY4, radius=1)
        self.util.draw_text(font, dt_txt, x, y, fill=self.epd.GRAY1, align='center')

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

            font = self.util.get_font(type='medium', size=self.util.text_size_tiny)
            coords_x, coords_y = coords

            sensor_icon = data["icon"]
            water_icon = 'water.png'
            dry_warning_icon = 'dry_warning.png'
            warning_icon = 'warning.png'

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
                min_ang, max_ang, poor_water_percent)
            water_level_ang = percentage_angle_in_range(
                min_ang, max_ang, sensor_val_percent)

            if poor_water:
                poor_water_level_ang = water_level_ang

            # draw plant icon
            self.util.draw_image(sensor_icon, iX, iY, self.util.icon_size_very_large)

            if warning:
                self.util.draw_image(warning_icon, iX, iY,
                                     self.util.icon_size_small)
            else:
                # draw dry level
                self.util.draw_dashed_arc(
                    cX, cY, r, min_ang, poor_water_level_ang, fill=self.epd.GRAY4, width=1)
                # draw water remaining
                self.util.draw_arc(
                    cX, cY, r, poor_water_level_ang, water_level_ang, fill=self.epd.GRAY4, width=1)
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
                self.util.draw_image(icon, wiX, wiY, self.util.icon_size_tiny)

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
        y = self.height * 0.7
        coords = inverse_pyramid(
            x, y, col_width, row_height, num_sensors, max_cols_per_row)

        for id in sensor_ids:
            sensor_data = data[id]
            draw_sensor_data(id, sensor_data, coords[id])

    def draw_environment_data(self, data):
        def draw_sensor_data(icon, data_key, sensor_unit_txt, x, y):
            iW, iH = self.util.icon_size_medium
            sensor_txt = str(data[data_key])
            font = self.util.get_font(type='bold', size=self.util.text_size_large)
            tW, _ = font.getsize(sensor_txt)
            iX, iY = x + iW / 2, y - iH / 1.5,
            self.util.draw_image(icon, iX, iY, (iW, iH))
            tX, tY = x + iW + tW / 2, y
            self.util.draw_text(font, sensor_txt, x + iW + tW / 2, y)
            font = self.util.get_font(type='thin', size=self.util.text_size_medium)
            tuW, tuH = font.getsize(sensor_unit_txt)
            tX, tY = tX + tW / 2 + tuW / 2, tY - tuH / 2
            self.util.draw_text(font, sensor_unit_txt, tX, tY)

        self.log.debug("Drawing environment data")

        display_vals = {
            "ext_temp": u"\N{DEGREE SIGN}C",
            "onboard_brightness": "Lux",
            "onboard_humidity": "%",
            "baro_pressure": "hPa"
        }

        x, y = 0, self.height - self.header_height
        row_height = self.height * 0.45
        outside_txt = "OFFBOARD"
        inside_txt = "ONBOARD"
        font = self.util.get_font(size=self.util.text_size_medium)
        o_tW, o_tH = font.getsize(outside_txt)
        i_tW, i_tH = font.getsize(inside_txt)
        x, y = self.margin_px + o_tW / 2, self.height - self.header_height * 1.3

        self.util.draw_text(font, outside_txt, x, y)
        self.util.draw_line(x + o_tW / 2 + self.margin_px, y - 2, self.width - self.margin_px * 2, y - 2, width = 2)

        x, y = self.margin_px + i_tW / 2, y - row_height
        self.util.draw_text(font, inside_txt, x, y)
        self.util.draw_line(x + i_tW / 2 + self.margin_px, y - 2, self.width - self.margin_px * 2, y - 2, width = 2)

        outside_row_y = self.height - self.header_height - row_height / 2
        inside_row_y = self.height - self.header_height - row_height - row_height / 2
        init_x = self.width * 0.01
        sensor_margin = self.width * 0.2

        icon = 'ext_temp.png'
        data_key = 'ext_temp'
        sensor_unit_txt = u"\N{DEGREE SIGN}C"
        x = init_x
        draw_sensor_data(icon, data_key, sensor_unit_txt, x, outside_row_y)

        data_key = 'onboard_temp'
        draw_sensor_data(icon, data_key, sensor_unit_txt, x, inside_row_y)

        icon = 'onboard_brightness.png'
        data_key = 'onboard_brightness'
        sensor_unit_txt = "lux"
        x = init_x + sensor_margin * 3
        draw_sensor_data(icon, data_key, sensor_unit_txt, x, outside_row_y)

        icon = 'onboard_humidity.png'
        data_key = 'onboard_humidity'
        sensor_unit_txt = "%"
        x = init_x + sensor_margin * 1.6
        draw_sensor_data(icon, data_key, sensor_unit_txt, x, inside_row_y)

        icon = 'baro_pressure.png'
        data_key = 'baro_pressure'
        sensor_unit_txt = "hPa"
        x = init_x + sensor_margin * 3
        draw_sensor_data(icon, data_key, sensor_unit_txt, x, inside_row_y)

    def draw_historical_data(self, hours):
        testdata = {
            "series": [
                {
                    "id": "1",
                    "axis": {
                        "x": [
                            "1634387352",
                            "1634300952",
                            "1634214552",
                            "1634128152",
                            "1634041752",
                            "1633955352",  
                        ],
                        "y": [
                            97,
                            40,
                            85,
                            59,
                            75,
                            25, 
                        ]
                    }
                },
                {
                    "id": "2",
                    "axis": {
                        "x": [
                            "1634387352",
                            "1634300952",
                            "1634214552",
                            "1634128152",
                            "1634041752",
                            "1633955352",  
                        ],
                        "y": [
                            90,
                            32,
                            25,
                            80,
                            95,
                            10, 
                        ]
                    }
                }
            ]
        }
        graphdata = {
            "series": []
        }

        hours_ago_epoch_time = datetime.date.today() - datetime.timedelta()

        w = 400
        h = 200

        x = 240
        y = 150

        self.util.draw_linechart(testdata, x, y, w, h)

    def draw_data(self, data):
        soil_moisture_data = data["soil_moisture"]
        enviroment_data = data["environment"]
        device_data = data["device"]

        #step = self.STEP_SOIL_MOISTURE
        #step = self.STEP_ENVIRONMENT
        step = self.STEP_7DAY_HISTORICAL

        self.flush()
        # new display frame
        self.util.new_frame(self.util.MODE_4GRAY)

        # draw data
        self.draw_header()

        if step == self.STEP_ENVIRONMENT:
            self.draw_environment_data(enviroment_data)

        if step == self.STEP_SOIL_MOISTURE:
            self.draw_soil_moisture_data(soil_moisture_data)
    
        if step == self.STEP_24HR_HISTORICAL:
            self.draw_historical_data(self.HOURS_IN_DAY)

        if step == self.STEP_7DAY_HISTORICAL:
            self.draw_historical_data(self.HOURS_IN_WEEK)

        # draw frame display
        frame = self.util.get_frame()
        self.draw_to_display(frame)

        # steps = [
        #     self.STEP_SOIL_MOISTURE
        #     self.STEP_ENVIRONMENT,
        #     self.STEP_24HR_HISTORICAL,
        #     self.STEP_7DAY_HISTORICAL,
        #     self.STEP_DEVICE,
        #     self.STEP_SOIL_MOISTURE
        # ]

        # for step in steps:
        #     self.delay_ms(20000)

        #     self.flush()
        #     # new display frame
        #     self.util.new_frame(self.util.MODE_1GRAY)

        #     # draw data
        #     self.draw_header()

        #     if step == self.STEP_ENVIRONMENT:


        #     if step == self.STEP_SOIL_MOISTURE:
        #         self.draw_soil_moisture_data(soil_moisture_data)
        
        #     if step == self.STEP_24HR_HISTORICAL:
        #         self.draw_historical_data(self.HOURS_IN_DAY)

        #     if step == self.STEP_7DAY_HISTORICAL:
        #         self.draw_historical_data(self.HOURS_IN_WEEK)

        #     # draw frame display
        #     frame = self.util.get_frame()
        #     self.draw_to_display(frame)

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
