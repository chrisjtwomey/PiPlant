import PIL
from .page import Page


class HistoricalDataPage(Page):
    def __init__(self, database_manager, width, height) -> None:
        super().__init__(width, height)

    def draw(self) -> PIL.Image:
        return super().draw()
