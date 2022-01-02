class EPD:
    MODE_4GRAY = "L"
    MODE_1GRAY = "1"
    GRAY1 = 0xFF
    GRAY2 = 0xC0
    GRAY3 = 0x80
    GRAY4 = 0x00

    def __init__(self, **kwargs):
        self.width = 280
        self.height = 480

    def init(self):
        pass

    def clear(self):
        pass

    def display(self, frame):
        frame.save("static/testframe.png")

    def sleep(self):
        pass
