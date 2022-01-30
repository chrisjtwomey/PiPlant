import PIL
import datetime
import threading
from ..view import View


class Page(View):
    def __init__(self, width, height) -> None:
        super().__init__(0, 0, width, height)

        self.header_height = int(height * 0.10)

        self._views = []

        header_view = self.HeaderView(0, 0, self.width, self.header_height)
        self.add_view(header_view)

    @property
    def views(self) -> list[View]:
        return self._views

    def add_view(self, view: View) -> None:
        self._views.append(view)

    def draw(self) -> PIL.Image:
        def draw_view(view: View):
            frame = self.util.get_frame()
            view_frame = view.draw()
            frame.paste(view_frame, (view.x, view.y))

        frame = self.util.new_frame(self.util.MODE_4GRAY)

        threads = []
        for view in self.views:
            thread = threading.Thread(target=draw_view, args=(view,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

        return frame

    class HeaderView(View):
        def __init__(self, x, y, width, height) -> None:
            super().__init__(x, y, width, height)

        def draw_frame(self):
            frame = self.util.new_frame(self.util.MODE_4GRAY)

            sizeW, sizeH = self.util.logo_size_small
            self.util.draw_image("logo.png", self.x, self.y, (sizeW, sizeH))

            now = datetime.datetime.now()
            datetime_text = now.strftime("%H:%M    %d/%m/%Y")
            font = self.util.get_font(type="medium", size=self.util.text_size_tiny)

            padding = 6  # in px
            text_width, text_height = self.util.textsize(datetime_text, font, padding)

            datetime_text_text_x = self.width - text_width + padding / 2
            datetime_text_text_y = self.y + padding / 2
            datetime_box_x = self.width - text_width
            datetime_box_y = self.y
            datetime_box_w = text_width
            datetime_box_h = text_height

            self.util.draw_rectangle(
                datetime_box_x,
                datetime_box_y,
                datetime_box_w,
                datetime_box_h,
                fill=self.util.GRAY4,
                outline=self.util.GRAY4,
                radius=1,
            )
            self.util.draw_text(
                font,
                datetime_text,
                datetime_text_text_x,
                datetime_text_text_y,
                fill=self.util.GRAY1,
                align="center",
            )

            return frame
