import os
from rpi_epd2in7.epd import EPD
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import logging

class EPaperDisplay:

    def __init__(self):
        self.log = logging.getLogger("PiPlantMon display")
        self.log.debug("Initializing E-Paper")

        epd = EPD()
        epd.init()
        self.epd = epd

        self.rotation = 270
        self.width = self.epd.height
        self.height = self.epd.width

        self.picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'static', 'bmp')
        self.fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'static', 'font')
        self.logofont = ImageFont.truetype(os.path.join(self.fontdir, "Lobster-Regular.ttf"), 32)
        
        self.flush()
        self.log.debug("E-Paper display initialized")
     
    def flush(self):
        self.log.debug("Flushing E-Paper display")
        image = Image.new('1', (self.epd.height, self.epd.width), 255)
        self.epd.display_frame(image.rotate(self.rotation, expand=True))

    def drawLogo(self, logo_text):
        self.log.debug("Drawing logo")
        font = self.logofont
        image = Image.new('1', (self.epd.height, self.epd.width), 255)

        # center text in display
        size_x, size_y = font.getsize(logo_text)
        logo_coords = self.translate((self.width / 2 - size_x / 2) + 10, self.height / 2 + size_y / 2)
        logo_x, logo_y = logo_coords

        bmp = Image.open(os.path.join(self.picdir, 'plant-4.bmp'))
        bmp_x = int(logo_x - 20)
        bmp_y = int(logo_y - 10)
        image.paste(bmp, (bmp_x, bmp_y))
        draw = ImageDraw.Draw(image)
        draw.text(logo_coords, logo_text, font=font, fill=0)

        self.draw(image)

    def drawData(self, data):
        return None

    def translate(self, x, y):
        return (x, self.height - y)

    def draw(self, image):
        self.epd.smart_update(image.rotate(self.rotation, expand=True))
