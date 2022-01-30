import os
import math
import scipy.signal
import matplotlib.pyplot as plt
import matplotlib.dates as md
from matplotlib import font_manager
from PIL import Image, ImageFont, ImageDraw


class XOutOfBoundsError(Exception):
    def __init__(self, x, max_x):
        message = (
            "x-coordinate {} is out-of-bounds. Value must be in range 0-{}".format(
                x, max_x
            )
        )
        super().__init__(message)


class YOutOfBoundsError(Exception):
    def __init__(self, y, max_y):
        message = (
            "y-coordinate {} is out-of-bounds. Value must be in range 0-{}".format(
                y, max_y
            )
        )
        super().__init__(message)


class PILUtil:
    MODE_1GRAY = "1"
    MODE_4GRAY = "L"
    GRAY1 = 0xFF  # white
    GRAY2 = 0xC0  # Close to white
    GRAY3 = 0x80  # Close to black
    GRAY4 = 0x00  # black

    ICON_PLANT = "plant.png"
    ICON_WATER = "water.png"
    ICON_DRY = "dry_warning.png"
    ICON_WARNING = "warning.png"
    ICON_TEMP = "ext_temp.png"
    ICON_LUX_HIGH = "sun.png"
    ICON_LUX_MED = "cloudy.png"
    ICON_LUX_LOW = "moon.png"

    def __init__(self, width=1, height=1, ignore_errors=False):
        self.width = width
        self.height = height

        self.last_frame = None
        self.frame = None

        self.text_size_tiny = 12
        self.text_size_small = 16
        self.text_size_medium = 20
        self.text_size_large = 48
        self.text_size_very_large = 64

        self.icon_size_tiny = (18, 18)
        self.icon_size_small = (24, 24)
        self.icon_size_medium = (32, 32)
        self.icon_size_large = (48, 48)
        self.icon_size_very_large = (80, 80)
        self.logo_size_small = (90, 18)
        self.logo_size_large = (168, 60)

        self.icondir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "pil",
            "icon",
        )
        self.fontdir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "pil",
            "font",
        )

        font_files = font_manager.findSystemFonts(fontpaths=self.fontdir, fontext="ttf")

        for font_file in font_files:
            font_manager.fontManager.addfont(font_file)

        # set font
        plt.rcParams["font.family"] = "Roboto"
        plt.rcParams["font.size"] = 5

        self.ignore_errors = ignore_errors

    def get_icon_path(self, filename):
        return os.path.join(self.icondir, filename)

    def get_font(self, name="Roboto", type="regular", size=24):
        return ImageFont.truetype(
            self.fontdir + "/{}-{}.ttf".format(name, type.capitalize()), size
        )

    def new_frame(self, mode):
        if self.frame != None:
            self.last_frame = self.frame.copy()

        frame = Image.new(mode, (self.width, self.height), 0xFF)
        self.frame = frame

        return frame

    def check_resize(self, width, height):
        if width != self.width or height != self.height:
            self.resize(width, height)

    def resize(self, width, height):
        oldframe = self.get_frame()
        newframe = Image.new(oldframe.mode, (int(width), int(height)))
        newframe.paste(oldframe, (0, 0))

        self.set_frame(newframe)
        self.width = int(width)
        self.height = int(height)

        return newframe

    def get_frame(self):
        frame = None
        if self.frame == None:
            raise ValueError("No frame to get")

        frame = self.frame

        return frame

    def set_frame(self, frame):
        self.frame = frame

    def get_last_frame(self):
        if self.last_frame == None:
            raise ValueError("No last frame to get")

        frame = self.last_frame

        return frame

    def get_draw(self):
        frame = self.get_frame()
        draw = ImageDraw.Draw(frame)

        return draw

    def draw_image(self, filename, x, y, size, bgcolor="#FFF"):
        imW, imH = size
        self.check_resize(imW, imH)

        coords = self.round(x, y)

        path = self.get_icon_path(filename)

        img = Image.open(path).convert("RGBA")
        img.thumbnail(size, Image.ANTIALIAS)

        background = Image.new("RGBA", img.size, bgcolor)
        alpha_composite = Image.alpha_composite(background, img)

        frame = self.get_frame()
        frame.paste(alpha_composite, coords)

    def draw_image_obj(self, img, x, y, size):
        imW, imH = size
        self.check_resize(imW, imH)

        coords = self.coords(x, y)

        img.thumbnail(size, Image.ANTIALIAS)

        frame = self.get_frame()
        frame.paste(img, coords)

    def draw_line(self, x1, y1, x2, y2, fill=0, width=1):
        self.check_resize(x2, y2)

        x1, y1 = self.coords(x1, y1)
        x2, y2 = self.coords(x2, y2)

        draw = self.get_draw()
        draw.line((x1, y1, x2, y2), fill, width)
        del draw

    def draw_text(self, font, text, x, y, fill=0, align="left"):
        draw = self.get_draw()
        x, y = self.coords(x, y)

        # draw.text((x, y), text, font=font, fill=fill)
        draw.multiline_text((x, y), text, font=font, fill=fill, align=align)
        del draw

    def draw_circle(self, x, y, r, fill=0, outline=0):
        self.check_resize(x + r, y + r)
        x, y = self.coords(x, y)

        draw = self.get_draw()
        draw.ellipse([(x - r, y - r), (x + r, y + r)], fill, outline)
        del draw

    def draw_rectangle(self, x, y, w, h, fill=0, outline=0, width=1, radius=0):
        self.check_resize(w, h)

        x, y = self.coords(x, y)
        x1, y1 = self.coords(x + w, y + h)

        draw = self.get_draw()
        if radius > 0:
            draw.rounded_rectangle(
                [(x, y), (x1, y1)],
                radius=radius,
                fill=fill,
                outline=outline,
                width=width,
            )
        else:
            draw.rectangle([(x, y), (x1, y1)], fill, outline, width)

        del draw

    def point_on_circle(self, cX, cY, cR, ang):
        rads = math.radians(ang)

        pX = cX + (cR * math.cos(rads))
        pY = cY + (cR * math.sin(rads))

        pX, pY = self.round(pX, pY)

        return (pX, pY)

    def draw_arc(self, x, y, r, startAngle, endAngle, fill=0, width=1):
        self.check_resize(x + r, y + r)

        x, y = self.coords(x, y)

        # get bounding box based on center point and radius
        bbX1 = int(x - r)
        bbY1 = int(y - r)
        bbX2 = int(x + r)
        bbY2 = int(y + r)
        bb = ((bbX1, bbY1), (bbX2, bbY2))

        if endAngle - startAngle <= 0:
            return

        draw = self.get_draw()
        draw.arc(bb, startAngle, endAngle, fill, width=width)
        del draw

    def draw_dashed_arc(
        self, x, y, r, startAngle, endAngle, fill=0, width=1, dash_length=4
    ):
        self.check_resize(x + r, y + r)

        x, y = self.coords(x, y)

        # get bounding box based on center point and radius
        bbX1 = int(x - r)
        bbY1 = int(y - r)
        bbX2 = int(x + r)
        bbY2 = int(y + r)
        bb = ((bbX1, bbY1), (bbX2, bbY2))

        arc_angle = endAngle - startAngle
        if arc_angle <= 0:
            return

        arc_length = math.pi * (r * 2) * (arc_angle / 360)
        iterations = int(arc_length / dash_length)

        if iterations <= 0:
            return

        delta_angle = int(arc_angle / iterations)

        draw = self.get_draw()

        i = 0
        for theta in range(startAngle, endAngle, delta_angle):
            color = fill if i % 2 != 0 else "#FFF"
            draw.arc(bb, theta, theta + delta_angle, color, width=width)
            i += 1

        del draw

    def draw_linechart(self, data, x, y, w, h, dpi=150):
        self.check_resize(w, h)

        canvas_size = self._calc_fig_size(w, h, 150)
        fig = plt.figure(constrained_layout=True, figsize=canvas_size, dpi=dpi)

        series = data["series"]

        for line in series:
            px = line["axis"]["x"]
            py = line["axis"]["y"]

            py = scipy.signal.savgol_filter(py, len(px) - 1, 4)

            plt.plot(px, py, linewidth=0.5)

        ax = plt.gca()
        xfmt = md.DateFormatter("%a")
        ax.xaxis.set_major_formatter(xfmt)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_ylim([0, 100])

        fig.canvas.draw()
        plotimg = Image.frombytes(
            "RGB", fig.canvas.get_width_height(), fig.canvas.tostring_rgb()
        )
        self.draw_image_obj(plotimg, x, y, (w, h))

    def textsize(self, text, font, padding=0):
        draw = self.get_draw()
        size_w, size_h = draw.textsize(text, font)
        del draw
        return (size_w + padding, size_h + padding)

    def coords(self, x, y):
        return self.round(x, y)

    def round(self, x, y):
        return int(x), int(y)

    def _calc_fig_size(self, w, h, dpi):
        return w / dpi, h / dpi
