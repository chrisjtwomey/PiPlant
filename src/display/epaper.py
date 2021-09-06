from rpi_epd2in7.epd import EPD
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import logging

class EPaperDisplay:

    def __init__(self):
        self.log = logging.getLogger("PiPlantMon display")

        self.log.info("Initializing E-Paper")
        epd = EPD()
        epd.init()

        self.epd = epd
        self._image = None
        
        self.flush()
        self.log.info("E-Paper display initialized")
     
    def flush(self):
        image = Image.new('1', (self.epd.height, self.epd.width), 255)
        image = image.rotate(180, expand=True)
        self.epd
        self.epd.display_frame(image)
        self.image = image

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, image):
        self._image = image

    def drawLogo(self, logo_text):
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 32)
        draw = ImageDraw.Draw(self.image)
        draw.text((self.epd.width / 2, self.epd.height / 2), logo_text, font=font, fill=0)

        self.draw()

    def drawData(self, data):
        return None

    def draw(self):
        if self.image == None:
            self.flush()

        self.epd.smart_update(self.image)
        self.image = None