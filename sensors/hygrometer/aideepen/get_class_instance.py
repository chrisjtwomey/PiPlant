def get_class_instance(**kwargs):
    mock = kwargs["mock"] if "mock" in kwargs else False
    
    if mock:
        from .hygrometer_mock import HygrometerMock
        return HygrometerMock(kwargs)

    from .hygrometer import Hygrometer
    return Hygrometer(kwargs)