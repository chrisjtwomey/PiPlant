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
                    ("value", "REAL", "NOT NULL"),
                    ("time", "INTEGER", "NOT NULL"),
                ],
            )
        except Exception as e:
            if "already exists" not in str(e):
                raise e

    def insert_sensors(self, data):
        insert_rows = []
        for data_entry in data:
            row = [
                data_entry["id"],
                data_entry["name"],
                data_entry["type"],
                data_entry["value"],
                data_entry["time"],
            ]
            insert_rows.append(row)

        self.driver.insert_rows(self.TABLE_NAME_SENSORS, insert_rows)

    def get_sensors(self, *ids, types=[], from_seconds=0):
        where = []
        if len(ids) > 0:
            where.append("sensor_id IN ({})".format(ids))
        if len(types) > 0:
            where.append("type IN ({})".format(",".join(types)))
        if from_seconds > 0:
            where.append("time > {}".format(from_seconds))

        return self.driver.select(
            self.TABLE_NAME_SENSORS,
            cols=["sensor_id", "name", "value", "time"],
            where=where,
            order_by=["sensor_id ASC", "time DESC"],
        )
