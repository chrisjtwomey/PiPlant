def get_class_instance(**kwargs):
    mock = kwargs["mock"] if "mock" in kwargs else False

    if mock:
        from .devicestatistics_mock import DeviceStatisticsMock
        return DeviceStatisticsMock(kwargs)

    from .devicestatistics import DeviceStatistics
    return DeviceStatistics()