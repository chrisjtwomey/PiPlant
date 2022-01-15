class DataPayload:
    def __init__(self, hygrometer_data, environment_data, device_data):
        self._hygrometer_data = hygrometer_data
        self._environment_data = environment_data
        self._device_data = device_data

    @property
    def hygrometers(self):
        return self._hygrometer_data

    @property
    def environment(self):
        return self._environment_data

    @property
    def device(self):
        return self._device_data


class Database:
    TABLE_NAME_HYGROMETERS = "hygrometers"
    TABLE_NAME_ENVIRONMENT = "environment"
    TABLE_NAME_DEVICE = "device"

    def __init__(self, driver):
        driver.connect()

        driver.create_table(
            self.TABLE_NAME_HYGROMETERS,
            [
                ("name", "TEXT", "PRIMARY_KEY", "NOT NULL"),
                ("percentage", "INTEGER", "NOT NULL"),
                ("dry_value_percentage", "INTEGER", "NOT NULL"),
                ("is_dry", "INTEGER", "NOT NULL"),
                ("time", "INTEGER", "NOT NULL"),
            ],
        )

        driver.create_table(
            self.TABLE_NAME_ENVIRONMENT,
            [
                ("name", "TEXT", "PRIMARY_KEY", "NOT NULL"),
                ("temperature", "INTEGER"),
                ("humidity", "INTEGER"),
                ("pressure", "INTEGER"),
                ("brightness", "INTEGER"),
                ("motion", "INTEGER"),
                ("time", "INTEGER", "NOT NULL"),
            ],
        )

        driver.create_table(
            self.TABLE_NAME_DEVICE,
            [
                ("name", "TEXT", "PRIMARY_KEY", "NOT NULL"),
                ("cpu_temperature", "INTEGER"),
                ("gpu_temperature", "INTEGER"),
                ("cpu_throttle", "INTEGER"),
                ("cpu_usage", "INTEGER"),
                ("memory_usage", "INTEGER"),
                ("memory_total", "INTEGER"),
                ("disk_usage", "INTEGER"),
                ("disk_total", "INTEGER"),
                ("time", "INTEGER", "NOT NULL"),
            ],
        )

        self._driver = driver

    @property
    def driver(self):
        return self._driver

    def handle_data_payload(self, data_payload):
        if not isinstance(data_payload, DataPayload):
            raise ValueError(
                "Data payload is not of class {}".format(DataPayload.__class__)
            )

        for hygrometer in data_payload.hygrometers:
            self.insert_hygromter(hygrometer)

        for _, sensors in data_payload.environment.items():
            for sensor in sensors:
                self.insert_environment_sensor(sensor)

        for sensor in data_payload.device:
            self.insert_device_sensor(sensor)

    def get_sensor(self, table_name, id):
        return self.driver.select(
            table_name, where="sensor_id = " + id, order_by="time DESC"
        )

    def get_sensors(self, table_name):
        return self.driver.select(table_name, order_by="sensor_id ASC, time DESC")

    def get_hygrometer(self, id):
        return self.get_sensor(self.TABLE_NAME_HYGROMETERS, id)

    def get_hygrometers(self):
        return self.get_sensors(self.TABLE_NAME_HYGROMETERS)

    def get_environment_sensor(self, id):
        return self.get_sensor(self.TABLE_NAME_ENVIRONMENT, id)

    def get_environment_sensors(self):
        return self.get_sensors(self.TABLE_NAME_ENVIRONMENT)

    def get_device_sensor(self, id):
        return self.get_sensor(self.TABLE_NAME_DEVICE, id)

    def get_device_sensors(self):
        return self.get_sensors(self.TABLE_NAME_DEVICE)

    def insert_hygromter(self, sensor):
        self.driver.insert(
            self.TABLE_NAME_HYGROMETERS,
            [
                "\"{}\"".format(sensor["name"]),
                sensor["percentage"],
                sensor["dry_value_percentage"],
                sensor["is_dry"],
                sensor["time"],
            ],
        )

    def insert_environment_sensor(self, sensor):
        self.driver.insert(
            self.TABLE_NAME_ENVIRONMENT,
            [
                "\"{}\"".format(sensor["name"]),
                sensor["temperature"] if "temperature" in sensor else None,
                sensor["humidity"] if "humidity" in sensor else None,
                sensor["pressure"] if "pressure" in sensor else None,
                sensor["brightness"] if "brightness" in sensor else None,
                sensor["motion"] if "motion" in sensor else None,
                sensor["time"],
            ],
        )

    def insert_device_sensor(self, sensor):
        self.driver.insert(
            self.TABLE_NAME_DEVICE,
            [
                "\"{}\"".format(sensor["name"]),
                sensor["cpu_temperature"] if "cpu_temperature" in sensor else None,
                sensor["gpu_temperature"] if "gpu_temperature" in sensor else None,
                sensor["cpu_throttle"] if "cpu_throttle" in sensor else None,
                sensor["cpu_usage"] if "cpu_usage" in sensor else None,
                sensor["memory_usage"] if "memory_usage" in sensor else None,
                sensor["memory_total"] if "memory_total" in sensor else None,
                sensor["disk_usage"] if "disk_usage" in sensor else None,
                sensor["disk_total"] if "disk_total" in sensor else None,
                sensor["time"],
            ],
        )
