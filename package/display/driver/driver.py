class DisplayDriver:
    def __init__(self, **kwargs):
        pass

    def init(self):
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.init.__name__
            )
        )

    def clear(self):
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.clear.__name__
            )
        )

    def display(self, frame):
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.display.__name__
            )
        )

    def sleep(self):
        raise NotImplementedError(
            "Sub-classes of {} should implement function {}".format(
                self.__class__.__name__, self.sleep.__name__
            )
        )
