import os
import time
import math
from datetime import datetime
from rpi_epd3in7.epd import EPD
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import logging

class EPaper:

    def __init__(self):
        self.log = logging.getLogger("e-Paper")
        self.log.debug("Initializing...")

        self.epd = EPD()

        self.width = self.epd.height
        self.height = self.epd.width

        self.plant_bmp_margin_ratio = 1.2
        self.large_col_ratio = 0.6
        self.header_height = 40
        self.margin_px = 5

        self.max_moisture_display_dots = 8

        self.icon_size_small = (32, 32)
        self.icon_size_large = (48, 48)
        self.logo_size_small = (112, 40)
        self.logo_size_large = (168, 60)

        self.icondir = os.path.join(os.path.dirname(
            os.path.dirname(os.path.realpath(__file__))), 'static', 'icon')
        self.fontdir = os.path.join(os.path.dirname(
            os.path.dirname(os.path.realpath(__file__))), 'static', 'font')
        self.text_small = ImageFont.truetype(
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
        self.text_tiny = ImageFont.truetype(
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)

        self.log.debug("Initialized")

    def flush(self):
        self.log.debug("Flushing")
        image = Image.new('L', (self.width, self.height), 0xFF)
        self.draw(image, fast=False)

    def draw_splash_screen(self):
        self.flush()
        self.log.debug("Drawing splash screen")
        frame = Image.new('1', (self.width, self.height), 0xFF)

        # center text in display
        size_x, size_y = self.logo_size_large
        logo_coords = self.translate(
            self.width / 2 - size_x / 2, self.height / 2 + size_y / 2)
        self._draw_image(frame, "logo.png", logo_coords, (size_x, size_y))

        self.draw(frame, fast=True)
        self.delay_ms(2000)

    def draw_header(self, frame):
        self.log.debug("Drawing header")

        size = self.logo_size_small
        logo_coords = self.translate(0, self.height)
        self._draw_image(frame, "logo.png", logo_coords, size)

        draw = ImageDraw.Draw(frame)
        start_x, start_y = self.translate(
            self.margin_px, self.height - self.header_height)
        end_x, end_y = self.translate(
            self.width - self.margin_px, self.height - self.header_height)
        draw.line((start_x, start_y, end_x, end_y), fill=0)

        font = self.text_tiny
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M")
        size_x, size_y = font.getsize(dt_string)
        time_x, time_y = self.translate(
            self.width - 10 - size_x, self.height - size_y / 2)
        draw.text((time_x, time_y), dt_string, font=font, fill=0)

    def draw_soil_moisture_data(self, frame, data):
        self.log.debug("Drawing soil moisture data")
        bmp_plant = 'plant.png'
        bmp_plant_water = 'plant-water.png'
        bmp_warning = 'warning.png'
        bmp_start_y = self.height - self.header_height - 10

        for idx in range(len(data)):
            sms_data = data[idx]
            sms_value = sms_data["value"]
            sms_water = sms_data["needs_water"]
            sms_error = sms_data["error"]

            bmp_file = bmp_plant_water if sms_water else bmp_plant
            if sms_error:
                bmp_file = bmp_warning

            bmp_width, bmp_height = self.icon_size_small
            bmp_x, bmp_y = self.translate(self.margin_px + bmp_width / 2, bmp_start_y - (
                    idx * bmp_height * self.plant_bmp_margin_ratio))

            self._draw_image(frame, bmp_file, (bmp_x, bmp_y), self.icon_size_small)


            # draw sensor id
            sms_id_str = str(idx + 1)
            draw = ImageDraw.Draw(frame)
            draw.text((bmp_x - 8, bmp_y + bmp_height / 2),
                      sms_id_str, font=self.text_tiny, fill=0)

            if not sms_error:
                # draw moisture levels
                num_display_dots = math.ceil(
                    self.max_moisture_display_dots * (sms_value / 100))

                dot_x = bmp_x + bmp_width + 10
                dot_y = bmp_y + bmp_height / 2

                for idx in range(num_display_dots):
                    dot_x = bmp_x + bmp_width + 10 + idx * 12
                    self.draw_circle(frame, dot_x, dot_y, 2)

    def draw_environment_data(self, frame, data):
        self.log.debug("Drawing environment data")
        origin_x, origin_y = self.translate(
            self.width * self.large_col_ratio, self.height - self.header_height - self.margin_px)

        display_vals = {
            "ext_temp": u"\N{DEGREE SIGN}C",
            "onboard_brightness": "Lux",
            "onboard_humidity": "%",
            "baro_pressure": "hPa"
        }

        idx = 0
        for key, unit in display_vals.items():
            bmp_file = key + ".png"
            bmp_width, _ = self.icon_size_small
            bmp_x = origin_x + self.margin_px
            bmp_y = origin_y - self.header_height + 30 + (35 * idx)
            self._draw_image(frame, bmp_file, (bmp_x, bmp_y), self.icon_size_small)

            data_msg = str(data[key]) + unit
            draw = ImageDraw.Draw(frame)
            draw.text((bmp_x + bmp_width + self.margin_px, bmp_y + 2),
                      data_msg, font=self.text_small, fill=0)

            idx += 1

    def draw_data(self, data):
        soil_moisture_data = data["soil_moisture"]
        enviroment_data = data["environment"]
        device_data = data["device"]

        frame = Image.new('1', (self.width, self.height), 0xFF)
       
        self.draw_header(frame)
        self.draw_soil_moisture_data(frame, soil_moisture_data)
        # draw column
        draw = ImageDraw.Draw(frame)
        start_x, start_y = self.translate(
            self.width * self.large_col_ratio, self.height - self.header_height - self.margin_px)
        end_x, end_y = self.translate(
            self.width * self.large_col_ratio, self.margin_px)
        draw.line((start_x, start_y, end_x, end_y), fill=0)

        self.draw_environment_data(frame, enviroment_data)

        self.draw(frame, fast=True)

    def _draw_image(self, frame, filename, coords, size):
        path = os.path.join(self.icondir, filename)
        img = Image.open(path)
        img.thumbnail(size, Image.ANTIALIAS)
        frame.paste(img, coords)

    def translate(self, x, y):
        return (int(x), int(self.height - y))

    def draw_circle(self, frame, x, y, r):
        draw = ImageDraw.Draw(frame)
        draw.ellipse([(x-r, y-r), (x+r, y+r)], fill=0, outline=0)

    def draw(self, frame, fast=False):
        gray_flag = 1 if fast else 0
        self.epd.init(mode=gray_flag)
        self.epd.clear(mode=gray_flag)
        self.epd.display_frame(frame, mode=gray_flag)

    def sleep(self):
        self.epd.sleep()

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)
