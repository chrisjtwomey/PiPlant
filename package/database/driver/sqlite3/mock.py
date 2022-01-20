from .driver import SQLiteDriver


class InMemSQLiteDriver(SQLiteDriver):
    def __init__(self, **kwargs):
        super().__init__(":memory:")
