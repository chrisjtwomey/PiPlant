
import os
import math
from PIL import Image, ImageFont, ImageDraw


class PILUtil:
    MODE_1GRAY = '1'
    MODE_4GRAY = 'L'

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.last_frame = None
        self.frame = None

        self.icondir = os.path.join(os.path.dirname(
            os.path.dirname(os.path.realpath(__file__))), 'static', 'icon')
        self.fontdir = os.path.join(os.path.dirname(
            os.path.dirname(os.path.realpath(__file__))), 'static', 'font')
        self.text_small = ImageFont.truetype(
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
        #self.text_tiny = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
        self.text_tiny = ImageFont.truetype(
            self.fontdir + '/Lobster-Regular.ttf', 16)

    def get_icon_path(self, filename):
        return os.path.join(self.icondir, filename)

    def get_font_path(self, filename):
        return os.path.join(self.fontdir, filename)

    def new_frame(self, mode):
        if self.frame != None:
            self.last_frame = self.frame.copy()

        frame = Image.new(mode, (self.width, self.height), 0xFF)
        self.frame = frame

        return frame

    def get_frame(self):
        frame = None
        if self.frame == None:
           raise ValueError("No frame to get") 

        frame = self.frame

        return frame

    def get_last_frame(self):
        if self.last_frame == None:
            raise ValueError("No last frame to get")

        frame = self.last_frame

        return frame

    def get_draw(self):
        frame = self.get_frame()
        draw = ImageDraw.Draw(frame)

        return draw

    def draw_image(self, filename, x, y, size):
        sizeW, sizeH = size
        coords = self.translate(x - sizeW / 2, y + sizeH / 2)
        path = self.get_icon_path(filename)

        img = Image.open(path).convert("RGBA")
        img.thumbnail(size, Image.ANTIALIAS)

        background = Image.new('RGBA', img.size, (255, 255, 255))
        alpha_composite = Image.alpha_composite(background, img)

        frame = self.get_frame()
        frame.paste(alpha_composite, coords)

    def draw_line(self, x1, y1, x2, y2, fill=0, width=1):
        x1, y1 = self.translate(x1, y1)
        x2, y2 = self.translate(x2, y2)

        draw = self.get_draw()
        draw.line((x1, y1, x2, y2), fill, width)
        del draw

    def draw_text(self, font, text, x, y):
        sizeW, sizeH = font.getsize(text)
        x, y = self.translate(x - sizeW / 2, y + sizeH / 2)

        draw = self.get_draw()
        draw.text((x, y), text, font=font, fill=0)
        del draw

    def draw_circle(self, x, y, r, fill=0, outline=0):
        x, y = self.translate(x, y)

        draw = self.get_draw()
        draw.ellipse([(x-r, y-r), (x+r, y+r)], fill, outline)
        del draw

    def point_on_circle(self, x, y, r, ang):
        rads = math.radians(ang)

        pX = x + (r * math.cos(rads))
        pY = y - (r * math.sin(rads))

        pX, pY = self.round(pX, pY)

        return (pX, pY)

    def draw_arc(self, x, y, r, startAngle, endAngle, width=1):
        x, y = self.translate(x, y)

        # get bounding box based on center point and radius
        bbX1 = int(x - r)
        bbY1 = int(y - r)
        bbX2 = int(x + r)
        bbY2 = int(y + r)
        bb = ((bbX1, bbY1), (bbX2, bbY2))

        if endAngle - startAngle <= 0:
            return

        draw = self.get_draw()
        draw.arc(bb, startAngle, endAngle, 'black', width=width)
        del draw

    def draw_dashed_arc(self, x, y, r, startAngle, endAngle, width=1, dash_length=4):
        x, y = self.translate(x, y)

        # get bounding box based on center point and radius
        bbX1 = int(x - r)
        bbY1 = int(y - r)
        bbX2 = int(x + r)
        bbY2 = int(y + r)
        bb = ((bbX1, bbY1), (bbX2, bbY2))

        arc_angle = endAngle - startAngle
        if arc_angle <= 0:
            return

        arc_length = (math.pi * (r * 2) * (arc_angle / 360))
        iterations = int(arc_length / dash_length)

        if iterations <= 0:
            return

        delta_angle = int(arc_angle / iterations)

        draw = self.get_draw()

        i = 0
        for theta in range(startAngle, endAngle, delta_angle):
            color = 'black' if i % 2 != 0 else 'white'
            draw.arc(bb, theta, theta + delta_angle, color, width=width)
            i += 1

        del draw

    def translate(self, x, y):
        return self.round(x, self.height - y)

    def round(self, x, y):
        return int(x), int(y)
