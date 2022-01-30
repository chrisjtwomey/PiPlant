from .page import Page


class DevicePage(Page):
    def __init__(self, sensor_manager, database_manager, width, height) -> None:
        super().__init__(sensor_manager, database_manager, width, height)

    def draw(self):
        pass
