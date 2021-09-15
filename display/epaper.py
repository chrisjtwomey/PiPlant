import os
import math
from datetime import datetime
from rpi_epd2in7.epd import EPD
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import logging


class EPaper:

    def __init__(self):
        self.log = logging.getLogger("e-Paper")
        self.log.debug("Initializing...")

        epd = EPD(orientation="h", partial_refresh_limit = 2, fast_refresh=False)
        epd.init()
        self.epd = epd

        self.rotation = 270
        self.width = self.epd.width
        self.height = self.epd.height

        self.plant_bmp_margin_ratio = 1.2
        self.large_col_ratio = 0.6
        self.header_height = 20
        self.margin_px = 5

        self.max_moisture_display_dots = 8

        self.logo_sizes = {
            "small": {
                "width": 56,
                "height": 20
            },
            "large": {
                "width": 112,
                "height": 40
            }
        }

        self.picdir = os.path.join(os.path.dirname(
            os.path.dirname(os.path.realpath(__file__))), 'static', 'bmp')
        self.fontdir = os.path.join(os.path.dirname(
            os.path.dirname(os.path.realpath(__file__))), 'static', 'font')
        self.text_small = ImageFont.truetype(
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
        self.text_tiny = ImageFont.truetype(
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)

        self.flush()
        self.log.debug("Initialized")

    def flush(self):
        self.log.debug("Flushing")
        image = Image.new('1', (self.width, self.height), 255)
        self.epd.display_frame(image.rotate(self.rotation, expand=True))

    def draw_splash_screen(self):
        self.log.debug("Drawing splash screen")
        image = Image.new('1', (self.width, self.height), 255)

        # center text in display
        logo_size = self.logo_sizes["large"]
        logo_coords = self.translate(
            self.width / 2 - logo_size["width"] / 2, self.height / 2 + logo_size["height"])
        logo_x, logo_y = logo_coords

        self.draw_logo(image, int(logo_x), int(logo_y), size="large")
        self.draw(image)

    def draw_header(self, image):
        self.log.debug("Drawing header")

        logo_x, logo_y = self.translate(0, self.height)
        self.draw_logo(image, logo_x, logo_y)

        draw = ImageDraw.Draw(image)
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

    def draw_soil_moisture_data(self, image, data):
        self.log.debug("Drawing soil moisture data")
        bmp_plant = 'plant_24x24.bmp'
        bmp_warning = 'warning_24x24.bmp'
        bmp_start_y = self.height - self.header_height - 10

        for idx in range(len(data)):
            sms_data = data[idx]
            sms_value = sms_data["value"]
            sms_water = sms_data["needs_water"]
            sms_error = sms_data["error"]

            bmp_file = bmp_warning if sms_error else bmp_plant
            bmp = Image.open(os.path.join(self.picdir, bmp_file))

            bmp_x, bmp_y = self.translate(self.margin_px + bmp.width / 2, bmp_start_y - (
                idx * bmp.height * self.plant_bmp_margin_ratio))
            image.paste(bmp, (bmp_x, bmp_y))

            if sms_water:
                # draw water warning
                bmp_water = Image.open(os.path.join(self.picdir, 'water_10x13.bmp'))
                image.paste(bmp_water, (int(bmp_x + bmp.width / 2), int(bmp_y + bmp.height / 2)))
    
            # draw sensor id
            sms_id_str = str(idx + 1)
            draw = ImageDraw.Draw(image)
            draw.text((bmp_x - 8, bmp_y + bmp.height / 2),
                      sms_id_str, font=self.text_tiny, fill=0)

            if not sms_error:
                # draw moisture levels
                num_display_dots = math.ceil(
                    self.max_moisture_display_dots * (sms_value / 100))

                dot_x = bmp_x + bmp.width + 10
                dot_y = bmp_y + bmp.height / 2

                for idx in range(num_display_dots):
                    dot_x = bmp_x + bmp.width + 10 + idx * 12
                    self.draw_circle(image, dot_x, dot_y, 2)

    def draw_environment_data(self, image, data):
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
            # draw external temp
            bmp = Image.open(os.path.join(
                self.picdir, '{}_24x24.bmp').format(key))
            bmp_x = origin_x + self.margin_px
            bmp_y = origin_y - self.header_height + 30 + (35 * idx)
            image.paste(bmp, (bmp_x, bmp_y))

            data_msg = str(data[key]) + unit
            draw = ImageDraw.Draw(image)
            draw.text((bmp_x + bmp.width + self.margin_px, bmp_y + 2),
                      data_msg, font=self.text_small, fill=0)

            idx += 1

    def draw_logo(self, image, x, y, size="small"):
        bmp_file = "logo_112x40.bmp" if size == "large" else "logo_56x20.bmp"
        bmp = Image.open(os.path.join(self.picdir, bmp_file))
        image.paste(bmp, (x, y))

    def draw_data(self, data):
        soil_moisture_data = data["soil_moisture"]
        enviroment_data = data["environment"]
        device_data = data["device"]

        image = Image.new('1', (self.width, self.height), 255)
        self.draw_header(image)
        self.draw_soil_moisture_data(image, soil_moisture_data)

        # draw column
        draw = ImageDraw.Draw(image)
        start_x, start_y = self.translate(
            self.width * self.large_col_ratio, self.height - self.header_height - self.margin_px)
        end_x, end_y = self.translate(
            self.width * self.large_col_ratio, self.margin_px)
        draw.line((start_x, start_y, end_x, end_y), fill=0)

        self.draw_environment_data(image, enviroment_data)

        self.draw(image)

    def translate(self, x, y):
        return (int(x), int(self.height - y))

    def draw_circle(self, image, x, y, r):
        draw = ImageDraw.Draw(image)
        draw.ellipse([(x-r, y-r), (x+r, y+r)], fill='black', outline='black')

    def draw(self, image):
        self.epd.smart_update(image.rotate(self.rotation, expand=True))
