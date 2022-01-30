import PIL
from .page import Page


class HistoricalDataPage(Page):
    def __init__(self, sensor_manager, database_manager, width, height) -> None:
        super().__init__(sensor_manager, database_manager, width, height)

    def draw(self) -> PIL.Image:
        return super().draw()
