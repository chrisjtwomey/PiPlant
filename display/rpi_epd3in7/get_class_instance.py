def get_class_instance(**kwargs):
    mock = kwargs["mock"] if "mock" in kwargs else False

    if mock:
        from .epd_mock import EPDMock
        return EPDMock(kwargs)

    from rpi_epd3in7.epd import EPD
    return EPD(kwargs)