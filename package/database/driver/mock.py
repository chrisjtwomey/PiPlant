from .driver import DatabaseDriver


class MockDatabaseDriver(DatabaseDriver):
    def __init__(self, **kwargs):
        self.data = {}
        super().__init__()

    def connect(self):
        pass

    def close(self):
        self.data = {}

    def create_table(self, table_name, cols):
        self.data[table_name] = []

    def select(self, cols, table_name, where=None, order_by=None):
        return self.data[table_name]

    def insert(self, table_name, values):
        self.data[table_name] = values

    def __del__(self):
        # no guarantee this closes the connection but it doesn't matter too much
        self.close()
