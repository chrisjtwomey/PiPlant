from .page import Page


class DevicePage(Page):
    def __init__(self, sensor_manager, width, height) -> None:
        super().__init__(width, height)

    def draw(self):
        pass
