import PIL
import util.utils as utils
from ..view.view import View


class HygrometerView(View):
    WATER_PERCENT_0_DEGREES = 90
    WATER_PERCENT_100_DEGREES = 330

    def __init__(self, hygrometer, x, y, width, height) -> None:
        super().__init__(x, y, width, height)

        self.hygrometer = hygrometer

    def draw_compact_frame(self) -> PIL.Image:
        frame = self.util.new_frame(self.util.MODE_4GRAY)

        cX, _ = self.util.coords(self.width / 2, self.height * 0.3)
        font = self.util.get_font(type="medium", size=self.util.text_size_tiny)

        # draw hygrometer name
        hygrometer_name = utils.wraptext(
            self.hygrometer.name, font, framewidth=self.width
        )
        tW, tH = self.util.textsize(hygrometer_name, font)
        tX, tY = self.width / 2 - tW / 2, tH / 4
        self.util.draw_text(font, hygrometer_name, tX, tY, align="center")

        iconW = iconH = self.width * 0.55
        water_icon = (
            self.util.ICON_WATER if not self.hygrometer.is_dry else self.util.ICON_DRY
        )
        water_iconX, water_iconY = cX - iconW / 2, tY + tH + iconH / 2

        self.util.draw_image(water_icon, water_iconX, water_iconY, (iconW, iconH))

        moisture_text = "{}%".format(self.hygrometer.moisture_percentage)
        moisture_textW, moisture_textH = self.util.textsize(moisture_text, font)
        moisture_textX, moisture_textY = (
            cX - moisture_textW / 2,
            water_iconY + iconH * 1.2,
        )

        self.util.draw_text(
            font, moisture_text, moisture_textX, moisture_textY, align="center"
        )

        # draw separator
        self.util.draw_line(0, 0, 0, self.height)

        return frame

    def draw_frame(self) -> PIL.Image:
        frame = self.util.new_frame(self.util.MODE_4GRAY)

        font = self.util.get_font(type="medium", size=self.util.text_size_tiny)

        water_icon = (
            self.util.ICON_WATER if not self.hygrometer.is_dry else self.util.ICON_DRY
        )
        iconW = iconH = self.width * 0.125

        min_ang = self.WATER_PERCENT_0_DEGREES
        max_ang = self.WATER_PERCENT_100_DEGREES
        warning = None

        # get angles in circle for water levels
        poor_water_level_ang = utils.percentage_angle_in_range(
            min_ang, max_ang, self.hygrometer.moisture_percentage
        )
        water_level_ang = utils.percentage_angle_in_range(
            min_ang, max_ang, self.hygrometer.moisture_percentage
        )
        if self.hygrometer.is_dry:
            poor_water_level_ang = water_level_ang

        cX, cY = self.util.coords(self.width / 2, self.height * 0.35)
        cD = self.width * 0.70
        cR = cD / 2

        plant_iconW = plant_iconH = self.width * 0.25
        plant_iconX, plant_iconY = cX - plant_iconW / 2, cY - plant_iconH / 2

        # draw plant icon
        self.util.draw_image(
            self.util.ICON_PLANT,
            plant_iconX,
            plant_iconY,
            (plant_iconW, plant_iconH),
        )

        if warning:
            self.util.draw_image(
                self.util.ICON_WARNING, plant_iconX, plant_iconY, (iconW, iconH)
            )
            return

        # draw dry level
        self.util.draw_dashed_arc(
            cX,
            cY,
            cR,
            min_ang,
            poor_water_level_ang,
            fill=self.util.GRAY4,
            width=1,
        )
        # draw water remaining
        self.util.draw_arc(
            cX,
            cY,
            cR,
            poor_water_level_ang,
            water_level_ang,
            fill=self.util.GRAY4,
            width=1,
        )
        # get start point on arc to draw water level
        sX, sY = self.util.point_on_circle(cX, cY, cR, min_ang)
        self.util.draw_circle(sX, sY, 3, fill="white")
        # get end point on arc to draw water level
        eX, eY = self.util.point_on_circle(cX, cY, cR, max_ang)
        self.util.draw_circle(eX, eY, 3, fill="white")
        # water icon coords
        wiX, wiY = self.util.point_on_circle(cX, cY, cR, water_level_ang)
        wiX, wiY = wiX - iconW / 2, wiY - iconH / 2
        self.util.draw_image(water_icon, wiX, wiY, (iconW, iconH))

        # draw hygrometer name
        hygrometer_name = utils.wraptext(
            self.hygrometer.name, font, framewidth=self.width
        )
        tW, tH = self.util.textsize(hygrometer_name, font)
        tX, tY = self.width / 2 - tW / 2, tH / 4
        self.util.draw_text(font, hygrometer_name, tX, tY, align="center")

        return frame
