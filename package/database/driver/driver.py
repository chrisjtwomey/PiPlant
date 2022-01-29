import logging


class DatabaseDriver:
    def __init__(self):
        self._conn = None
        self.log = logging.getLogger(self.__class__.__name__)

    def connect(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def create_table(self, table_name, cols):
        raise NotImplementedError()

    def select(self, table_name, cols, where=[], order_by=[], limit=None):
        raise NotImplementedError()

    def insert_row(self, table_name, row):
        raise NotImplementedError()

    def insert_rows(self, table_name, rows):
        raise NotImplementedError()

    def __del__(self):
        # no guarantee this closes the connection but it doesn't matter too much
        self.close()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "DatabaseDriver::{}".format(self.__class__.__name__)
