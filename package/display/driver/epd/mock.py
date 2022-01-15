from ..mock import MockDriver


class MockEPD(MockDriver):
    def __init__(self, **kwargs):
        super().__init__(kwargs)
