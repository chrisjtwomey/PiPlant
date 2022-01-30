import PIL
import logging
from ..pil.pil import PILUtil


class View:
    MIN_WIDTH = 30
    COMPACT_MODE_PX = 60

    def __init__(self, x, y, width, height) -> None:
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self.util = PILUtil(width, height)

        self.log = logging.getLogger(self.__class__.__name__)

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def is_compact_mode(self):
        return 0 <= self.width <= self.COMPACT_MODE_PX

    def draw_frame(self) -> PIL.Image:
        raise NotImplementedError()

    def draw_compact_frame(self) -> PIL.Image:
        raise NotImplementedError()

    def draw(self) -> PIL.Image:
        frame = None

        print(frame.width)
        if self.is_compact_mode():
            try:
                frame = self.draw_compact_frame()
            except NotImplementedError:
                frame = self.draw_frame()
            except Exception as e:
                raise e
        else:
            frame = self.draw_frame()

        return frame
