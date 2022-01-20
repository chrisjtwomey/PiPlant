import logging


class DatabaseManager:
    TABLE_NAME_SENSORS = "sensors"
    TABLE_NAME_HYGROMETER = "hygrometers"
    TABLE_NAME_TEMPERATURE = "temperature"
    TABLE_NAME_HUMIDITY = "humidity"
    TABLE_NAME_PRESSURE = "pressure"
    TABLE_NAME_BRIGHTNESS = "brightness"
    TABLE_NAME_MOTION = "motion"
    TABLE_NAME_CPU_TEMPERATURE = "cpu_temperature"
    TABLE_NAME_GPU_TEMPERATURE = "gpu_temperature"
    TABLE_NAME_CPU_USAGE = "cpu_usage"
    TABLE_NAME_MEM_USAGE = "memory_usage"
    TABLE_NAME_DISK_USAGE = "disk_usage"

    def __init__(self, driver):
        self.log = logging.getLogger(self.__class__.__name__)
        self._driver = driver

        self.init_db()

    @property
    def driver(self):
        return self._driver

    @property
    def sensor_table_names(self):
        return [
            self.TABLE_NAME_HYGROMETER,
            self.TABLE_NAME_TEMPERATURE,
            self.TABLE_NAME_BRIGHTNESS,
            self.TABLE_NAME_HUMIDITY,
            self.TABLE_NAME_PRESSURE,
            self.TABLE_NAME_MOTION,
            self.TABLE_NAME_CPU_TEMPERATURE,
            self.TABLE_NAME_GPU_TEMPERATURE,
            self.TABLE_NAME_CPU_USAGE,
            self.TABLE_NAME_MEM_USAGE,
            self.TABLE_NAME_DISK_USAGE,
        ]

    def init_db(self):
        self.driver.connect()

        try:
            self.driver.create_table(
                self.TABLE_NAME_SENSORS,
                [
                    ("id", "TEXT", "PRIMARY_KEY", "NOT NULL"),
                    ("name", "TEXT", "NOT NULL"),
                    ("type", "TEXT", "NOT NULL"),
                ],
            )
        except Exception as e:
            self.log.error(e)

        for table_name in self.sensor_table_names:
            try:
                self.driver.create_table(
                    table_name,
                    [
                        ("sensor_id", "TEXT", "PRIMARY_KEY", "NOT NULL"),
                        ("value", "TEXT", "NOT NULL"),
                        ("time", "INTEGER", "NOT NULL"),
                    ],
                )
            except Exception as e:
                self.log.error(e)

    def insert_sensor_data(self, sensor_data):
        insert_rows = []
        for data_entry in sensor_data:
            row = [
                data_entry["id"],
                data_entry["name"],
                data_entry["type"],
                data_entry["value"],
                data_entry["time"],
            ]
            insert_rows.append(row)

    def get_sensor(self, table_name, id):
        return self.driver.select(
            table_name, where="sensor_id = " + id, order_by="time DESC"
        )

    def get_sensors(self, table_name):
        return self.driver.select(table_name, order_by="sensor_id ASC, time DESC")
