import PIL
import util.utils as utils
from .view import View


class EnvironmentView(View):
    def __init__(
        self,
        temperature_sensor,
        humidity_sensor,
        pressure_sensor,
        brightness_sensor,
        x,
        y,
        width,
        height,
    ) -> None:
        super().__init__(x, y, width, height)

        self.temperature_sensor = temperature_sensor
        self.humidity_sensor = humidity_sensor
        self.pressure_sensor = pressure_sensor
        self.brightness_sensor = brightness_sensor

    def draw_compact_frame(self) -> PIL.Image:
        frame = self.util.new_frame(self.util.MODE_4GRAY)
        font = self.util.get_font(type="medium", size=self.util.text_size_tiny)

        cX, _ = self.util.coords(self.width / 2, 0)

        iconW = iconH = self.width * 0.65
        lux_iconX, lux_iconY = cX - iconW / 2, self.height * 0.2

        lux = self.brightness_sensor.brightness
        lux_icon = self.util.ICON_LUX_LOW

        if lux >= 450:
            lux_icon = self.util.ICON_LUX_MED
        if lux >= 900:
            lux_icon = self.util.ICON_LUX_HIGH

        self.util.draw_image(lux_icon, lux_iconX, lux_iconY, (iconW, iconH))

        lux_text = "{} lx".format(lux)
        lux_textW, _ = self.util.textsize(lux_text, font)
        lux_textX, lux_textY = cX - lux_textW / 2, lux_iconY + iconH * 1.5

        self.util.draw_text(font, lux_text, lux_textX, lux_textY, align="center")

        # draw separator
        self.util.draw_line(0, 0, 0, self.height)
        self.util.draw_line(0, 0, self.width, 0)

        return frame

    def draw_frame(self) -> PIL.Image:
        frame = self.util.new_frame(self.util.MODE_4GRAY)

        return frame
