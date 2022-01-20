import sqlite3
from ..driver import DatabaseDriver


class SQLiteDriver(DatabaseDriver):
    def __init__(self, dbdata_path):
        self._conn = None
        self._dbdata_path = dbdata_path

        super().__init__()

    def connect(self):
        self._conn = sqlite3.connect(self._dbdata_path)

    def close(self):
        if self._conn is not None:
            self._conn.close()

    def create_table(self, table_name, cols):
        # function that converts tuple to string
        def join_tuple_string(strings_tuple) -> str:
            return " ".join(strings_tuple)

        # joining all the tuples
        joined_tuples = map(join_tuple_string, cols)
        joined_list = ", ".join(list(joined_tuples))
        formatted_cols = "(" + str(joined_list) + ")"

        with self._conn as db:
            db.execute(
                "CREATE TABLE {} {}".format(table_name, formatted_cols),
            )

    def select(self, table_name, cols=[], where=None, order_by=None):
        if len(cols) == 0:
            cols = "*"

        formatted_where = "" if where is None else "WHERE " + where
        formatted_order_by = "" if order_by is None else "ORDER BY " + order_by

        results = []
        with self._conn as db:
            cur = db.execute(
                "SELECT {} FROM {} {} {}".format(
                    cols, table_name, formatted_where, formatted_order_by
                )
            )
            col_names = [tup[0] for tup in cur.description]
            for row in cur:
                result = dict()
                idx = 0
                for val in row:
                    result[col_names[idx]] = val
                    idx += 1

                results.append(result)

        return results

    def insert(self, table_name, values):
        formatted_values = "(" + ",".join(map(str, values)) + ")"

        with self._conn as db:
            db.execute(
                "INSERT INTO {} VALUES {}".format(table_name, formatted_values),
            )

    def _check_connection(self):
        return self._conn is not None
