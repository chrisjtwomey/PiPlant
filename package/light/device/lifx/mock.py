from ..mock import MockLight


class MockLifxDevice(MockLight):
    def __init__(self, **kwargs):
        super().__init__(kwargs)
