def get_class_instance(**kwargs):
    mock = kwargs["mock"] if "mock" in kwargs else False

    if mock:
        from .sensorhub_mock import SensorHubMock
        return SensorHubMock(kwargs)

    from .sensorhub import SensorHub
    return SensorHub(kwargs)