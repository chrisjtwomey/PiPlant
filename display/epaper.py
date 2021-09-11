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

        epd = EPD(partial_refresh_limit=2)
        epd.init()
        self.epd = epd

        self.rotation = 270
        self.width = self.epd.height - 9  # lines won't draw past 255
        self.height = self.epd.width

        self.plant_bmp_margin_ratio = 1.2
        self.large_col_ratio = 0.6
        self.header_height = 20
        self.line_margin_px = 5

        self.max_moisture_display_dots = 5

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
        self.text_tiny = ImageFont.truetype(
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)

        self.flush()
        self.log.debug("Initialized")

    def flush(self):
        self.log.debug("Flushing")
        image = Image.new('1', (self.epd.height, self.epd.width), 255)
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

    def add_header(self, image):
        self.log.debug("Drawing header")

        logo_x, logo_y = self.translate(0, self.height)
        self.draw_logo(image, logo_x, logo_y)

        draw = ImageDraw.Draw(image)
        start_x, start_y = self.translate(
            self.line_margin_px, self.height - self.header_height)
        end_x, end_y = self.translate(
            self.width - self.line_margin_px, self.height - self.header_height)
        draw.line((start_x, start_y, end_x, end_y), fill=0)

        font = self.text_tiny
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M")
        size_x, size_y = font.getsize(dt_string)
        time_x, time_y = self.translate(
            self.width - 10 - size_x, self.height - size_y / 2)
        draw.text((time_x, time_y), dt_string, font=font, fill=0)

    def draw_logo(self, image, x, y, size="small"):
        bmp_file = "logo_112x40.bmp" if size == "large" else "logo_56x20.bmp"

        bmp = Image.open(os.path.join(self.picdir, bmp_file))
        image.paste(bmp, (x, y))

    def draw_data(self, data):
        self.log.debug("Drawing data")
        image = Image.new('1', (self.width, self.height), 255)
        self.add_header(image)

        bmp_x = self.line_margin_px
        bmp_y = self.height - 30
        for adc_channel in range(len(data["soil_moisture"])):
            sms_data = data["soil_moisture"][adc_channel]
            sms_id_str = str(adc_channel + 1)

            bmp = Image.open(os.path.join(self.picdir, 'plant_24x24.bmp'))
            image.paste(bmp, self.translate(bmp_x, bmp_y))

            draw = ImageDraw.Draw(image)
            draw.text(self.translate(self.line_margin_px + bmp.width - 5,
                      bmp_y - bmp.height / 2), sms_id_str, font=self.text_tiny, fill=0)

            bmp_y -= bmp.height * self.plant_bmp_margin_ratio

            dot_x = bmp_x + bmp.width + 10
            dot_y = bmp.height / 2
            num_display_dots = math.ceil(sms_data / (1 / self.max_moisture_display_dots))
            print(num_display_dots)
            for idx in range(num_display_dots):
                draw.ellipse((dot_x, dot_y, dot_x + 6, dot_y - 6), fill = 0)
                dot_x += 10

        draw = ImageDraw.Draw(image)
        start_x, start_y = self.translate(
            self.width * self.large_col_ratio, self.height - self.header_height - self.line_margin_px)
        end_x, end_y = self.translate(
            self.width * self.large_col_ratio, self.line_margin_px)
        draw.line((start_x, start_y, end_x, end_y), fill=0)

        self.draw(image)

    def translate(self, x, y):
        return (int(x), int(self.height - y))

    def draw(self, image):
        self.epd.smart_update(image.rotate(self.rotation, expand=True))
