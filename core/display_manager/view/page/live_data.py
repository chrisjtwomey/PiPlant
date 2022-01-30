import threading
from .page import Page
from ..hygrometer import HygrometerView
from ..environment import EnvironmentView


class LiveDataPage(Page):
    MAX_HYGROMETER_VIEWS_PER_PAGE = 12

    def __init__(self, sensor_manager, width, height) -> None:
        super().__init__(width, height)

        self.hygrometers = sensor_manager.get_hygrometers()
        self.temperature_sensors = sensor_manager.get_temperature_sensors()
        self.humidity_sensors = sensor_manager.get_humidity_sensors()
        self.pressure_sensors = sensor_manager.get_pressure_sensors()
        self.brightness_sensors = sensor_manager.get_brightness_sensors()

        def init_views(idx):
            hygrometer = self._get_sensor_with_fallback(self.hygrometers, idx)
            temp_sensor = self._get_sensor_with_fallback(self.temperature_sensors, idx)
            hum_sensor = self._get_sensor_with_fallback(self.humidity_sensors, idx)
            pressure_sensor = self._get_sensor_with_fallback(self.pressure_sensors, idx)
            lux_sensor = self._get_sensor_with_fallback(self.brightness_sensors, idx)

            x = self.x + (view_width * idx)
            y = self.header_height

            hview = HygrometerView(
                hygrometer, x, y, view_width, int(self.height * 0.375)
            )
            eview = EnvironmentView(
                temp_sensor,
                hum_sensor,
                pressure_sensor,
                lux_sensor,
                x,
                hview.height,
                view_width,
                int(self.height * 0.35),
            )
            self.add_view(hview)
            self.add_view(eview)

        num_views = len(self.hygrometers)
        num_views = self.MAX_HYGROMETER_VIEWS_PER_PAGE
        view_width = int(self.width / num_views)

        threads = []
        for idx in range(num_views):
            thread = threading.Thread(target=init_views, args=(idx,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def _get_sensor_with_fallback(self, sensors, n):
        if len(sensors) == 0:
            raise ValueError("No items in sensor list")

        sensor = None
        for idx in range(n + 1):
            if idx >= len(sensors):
                break

            sensor = sensors[idx]
        return sensor
