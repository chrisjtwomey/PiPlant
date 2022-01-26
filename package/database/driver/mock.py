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

    def select(self, cols, table_name, where=[], order_by=[]):
        return self.data[table_name]

    def insert_row(self, table_name, row):
        self.data[table_name] = row
    
    def insert_rows(self, table_name, rows):
        new_rows = []
        existing_rows = self.data[table_name]

        new_rows = existing_rows
        for row in rows:
            new_rows.append(row)
        self.data[table_name] = new_rows
        

    def __del__(self):
        # no guarantee this closes the connection but it doesn't matter too much
        self.close()
