import PIL
from .page import Page


class SplashScreenPage(Page):
    def __init__(self, width, height) -> None:
        super().__init__(width, height)

    def draw_frame(self) -> PIL.Image:
        frame = self.util.new_frame(self.util.MODE_4GRAY)

        sizeW, sizeH = self.util.logo_size_large
        x = self.width / 2
        y = self.height / 2 + sizeH / 2
        self.util.draw_image("logo.png", x, y, (sizeW, sizeH))

        return frame
