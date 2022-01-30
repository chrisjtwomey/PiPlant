import PIL
import util.utils as utils
from core.display_manager.page.page import Page


class EnvironmentPage(Page):
    def __init__(self, sensor_manager, database_manager, width, height) -> None:
        self.temperature_sensors = sensor_manager.get_temperature_sensors()
        self.humidity_sensors = sensor_manager.get_humidity_sensors()
        self.pressure_sensors = sensor_manager.get_pressure_sensors()
        self.brightness_sensors = sensor_manager.get_brightness_sensors()
        self.device_sensors = sensor_manager.get_device_sensors()
        super().__init__(sensor_manager, database_manager, width, height)

    def draw(self) -> PIL.Image:
        frame = self.util.new_frame(self.util.MODE_4GRAY)

        self.draw_header()

        x, y = 0, self.height - self.header_height
        row_height = self.height * 0.45
        outside_txt = "OFFBOARD"
        inside_txt = "ONBOARD"
        font = self.util.get_font(size=self.util.text_size_medium)
        o_tW, _ = font.getsize(outside_txt)
        i_tW, _ = font.getsize(inside_txt)
        x, y = self.margin_px + o_tW / 2, self.height - self.header_height * 1.3

        self.util.draw_text(font, outside_txt, x, y)
        self.util.draw_line(
            x + o_tW / 2 + self.margin_px,
            y - 2,
            self.width - self.margin_px * 2,
            y - 2,
            width=2,
        )

        x, y = self.margin_px + i_tW / 2, y - row_height
        self.util.draw_text(font, inside_txt, x, y)
        self.util.draw_line(
            x + i_tW / 2 + self.margin_px,
            y - 2,
            self.width - self.margin_px * 2,
            y - 2,
            width=2,
        )

        outside_row_y = self.height - self.header_height - row_height / 2
        inside_row_y = self.height - self.header_height - row_height - row_height / 2
        init_x = self.width * 0.01
        sensor_margin = self.width * 0.2

        icon = "ext_temp.png"
        value = utils.avg([s.temperature for s in self.temperature_sensors])
        sensor_unit_txt = "\N{DEGREE SIGN}C"
        x = init_x
        self._draw_sensor_data(icon, value, sensor_unit_txt, x, outside_row_y)

        icon = "ext_temp.png"
        value = utils.avg([s.cpu_temperature for s in self.device_sensors])
        sensor_unit_txt = "\N{DEGREE SIGN}C"
        x = init_x
        self._draw_sensor_data(icon, value, sensor_unit_txt, x, inside_row_y)

        icon = "brightness.png"
        value = utils.avg([s.brightness for s in self.brightness_sensors])
        sensor_unit_txt = "lux"
        x = init_x + sensor_margin * 3
        self._draw_sensor_data(icon, value, sensor_unit_txt, x, outside_row_y)

        icon = "humidity.png"
        value = utils.avg([s.humidity for s in self.humidity_sensors])
        sensor_unit_txt = "%"
        x = init_x + sensor_margin * 1.6
        self._draw_sensor_data(icon, value, sensor_unit_txt, x, inside_row_y)

        icon = "pressure.png"
        value = utils.avg([s.pressure for s in self.pressure_sensors])
        sensor_unit_txt = "hPa"
        x = init_x + sensor_margin * 3
        self._draw_sensor_data(icon, value, sensor_unit_txt, x, inside_row_y)

        return frame

    def _draw_sensor_data(self, icon, data, sensor_unit_txt, x, y):
        iW, iH = self.util.icon_size_medium
        sensor_txt = str(data)
        font = self.util.get_font(type="bold", size=self.util.text_size_large)
        tW, _ = font.getsize(sensor_txt)
        iX, iY = (
            x + iW / 2,
            y - iH / 1.5,
        )
        self.util.draw_image(icon, iX, iY, (iW, iH))
        tX, tY = x + iW + tW / 2, y
        self.util.draw_text(font, sensor_txt, x + iW + tW / 2, y)
        font = self.util.get_font(type="thin", size=self.util.text_size_medium)
        tuW, tuH = font.getsize(sensor_unit_txt)
        tX, tY = tX + tW / 2 + tuW / 2, tY - tuH / 2
        self.util.draw_text(font, sensor_unit_txt, tX, tY)
