import PIL
import util.utils as utils
from core.display_manager.page.page import Page


class HygrometerPage(Page):
    WATER_PERCENT_0_DEGREES = 90
    WATER_PERCENT_100_DEGREES = 330

    def __init__(self, sensor_manager, database_manager, width, height) -> None:
        self.hygrometers = sensor_manager.get_hygrometers()
        super().__init__(sensor_manager, database_manager, width, height)

    def draw(self) -> PIL.Image:
        frame = self.util.new_frame(self.util.MODE_4GRAY)

        self.draw_header()

        max_cols_per_row = 3
        col_width = 140
        row_height = 120
        num_sensors = len(self.hygrometers)

        x = self.width / 2 - col_width
        y = self.height * 0.5

        if num_sensors > max_cols_per_row:
            y = self.height * 0.7

        coords = self._inverse_pyramid(
            x, y, col_width, row_height, num_sensors, max_cols_per_row
        )

        for idx, hygrometer in enumerate(self.hygrometers):
            self._draw_hygrometer(hygrometer, coords[idx])

        return frame

    def _draw_hygrometer(self, hygrometer, coords):
        sensor_val_percent = hygrometer.moisture_percentage
        poor_water = hygrometer.is_dry
        poor_water_percent = hygrometer.dry_value_percentage
        draw_value_text = False
        value_text = str(sensor_val_percent) + "%"
        # warning = data["error"]
        warning = None

        font = self.util.get_font(type="medium", size=self.util.text_size_tiny)
        coords_x, coords_y = coords

        sensor_icon = "plant.png"
        water_icon = "water.png"
        dry_warning_icon = "dry_warning.png"
        warning_icon = "warning.png"

        # plant icon params
        icon_medW, _ = self.util.icon_size_very_large
        iX, iY = self.util.round(coords_x, coords_y)
        # get arc params
        cX, cY = iX, iY
        r = icon_medW / 1.5
        # get angles in circle for water levels
        min_ang = self.WATER_PERCENT_0_DEGREES
        max_ang = self.WATER_PERCENT_100_DEGREES

        poor_water_level_ang = utils.percentage_angle_in_range(
            min_ang, max_ang, poor_water_percent
        )
        water_level_ang = utils.percentage_angle_in_range(
            min_ang, max_ang, sensor_val_percent
        )

        if poor_water:
            poor_water_level_ang = water_level_ang

        # draw plant icon
        self.util.draw_image(sensor_icon, iX, iY, self.util.icon_size_large)

        if warning:
            self.util.draw_image(warning_icon, iX, iY, self.util.icon_size_small)
        else:
            # draw dry level
            self.util.draw_dashed_arc(
                cX,
                cY,
                r,
                min_ang,
                poor_water_level_ang,
                fill=self.util.GRAY4,
                width=1,
            )
            # draw water remaining
            self.util.draw_arc(
                cX,
                cY,
                r,
                poor_water_level_ang,
                water_level_ang,
                fill=self.util.GRAY4,
                width=1,
            )
            # get start point on arc to draw water level
            sX, sY = self.util.point_on_circle(cX, cY, r, min_ang)
            self.util.draw_circle(sX, sY, 3, fill="white")
            # get end point on arc to draw water level
            eX, eY = self.util.point_on_circle(cX, cY, r, max_ang)
            self.util.draw_circle(eX, eY, 3, fill="white")
            # water icon coords
            wiX, wiY = self.util.point_on_circle(cX, cY, r, water_level_ang)

            icon = water_icon if not poor_water else dry_warning_icon
            self.util.draw_image(icon, wiX, wiY, self.util.icon_size_tiny)

        # draw sensor id
        sensor_id = hygrometer.name
        tW, tH = font.getsize(sensor_id)
        tX, tY = cX, cY + r * 1.5
        self.util.draw_text(font, sensor_id, tX, tY)

        if draw_value_text:
            # draw percentage text
            tW, tH = font.getsize(value_text)
            tX, tY = iX - tW / 1.5, iY + tH / 2
            self.util.draw_text(font, value_text, tX, tY)

    def _inverse_pyramid(self, x, y, colw, rowh, max_items, max_cols_per_row):
        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i : i + n]

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
