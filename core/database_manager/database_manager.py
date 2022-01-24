import logging


class DatabaseManager:
    TABLE_NAME_SENSORS = "sensors"

    def __init__(self, driver):
        self.log = logging.getLogger(self.__class__.__name__)
        self._driver = driver

        self.init_db()

    @property
    def driver(self):
        return self._driver

    def init_db(self):
        self.driver.connect()

        try:
            self.driver.create_table(
                self.TABLE_NAME_SENSORS,
                [
                    ("sensor_id", "TEXT", "PRIMARY_KEY", "NOT NULL"),
                    ("name", "TEXT", "NOT NULL"),
                    ("type", "TEXT", "NOT NULL"),
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

        for row in insert_rows:
            self.driver.insert(self.TABLE_NAME_SENSORS, row)

    def get_sensor(self, table_name, id):
        return self.driver.select(
            table_name, where="sensor_id = " + id, order_by="time DESC"
        )

    def get_sensors(self, table_name):
        return self.driver.select(table_name, order_by="sensor_id ASC, time DESC")
