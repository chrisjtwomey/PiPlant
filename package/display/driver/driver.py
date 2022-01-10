class DisplayDriver:
    def __init__(self, **kwargs):
        pass

    def init(self):
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()

    def display(self, frame):
        raise NotImplementedError()

    def sleep(self):
        raise NotImplementedError()
