import PIL
import logging
import datetime
from ..pil.pil import PILUtil


class Page:
    def __init__(self, sensor_manager, database_manager, width, height) -> None:
        self.log = logging.getLogger(self.__class__.__name__)

        self.sensor_manager = sensor_manager
        self.database_manager = database_manager

        self.width = width
        self.height = height
        self.util = PILUtil(width, height)

        self.plant_bmp_margin_ratio = 1.2
        self.header_height = self.height * 0.12
        self.margin_px = 5

    def draw(self) -> PIL.Image:
        raise NotImplementedError()

    def draw_header(self):
        self.log.debug("Drawing header")

        sizeW, sizeH = self.util.logo_size_small
        x, y = (sizeW / 2 + 1, self.height - sizeH / 2 - 1)
        self.util.draw_image("logo.png", x, y, (sizeW, sizeH))

        now = datetime.datetime.now()
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
            fill=self.util.GRAY4,
            outline=self.util.GRAY4,
            radius=1,
        )
        self.util.draw_text(font, dt_txt, x, y, fill=self.util.GRAY1, align="center")
