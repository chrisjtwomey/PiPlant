import sqlite3
from ..driver import DatabaseDriver


class SQLiteDriver(DatabaseDriver):
    def __init__(self, dbdata_path):
        self._conn = None
        self._dbdata_path = dbdata_path

        super().__init__()

    def connect(self):
        self._conn = sqlite3.connect(self._dbdata_path, check_same_thread=False)

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

        query = "CREATE TABLE {} {}".format(table_name, formatted_cols)
        self.log.debug(query)

        with self._conn as db:
            db.execute(query)

    def select(self, table_name, cols=[], where=[], order_by=[], limit=None):
        formatted_cols = "*"
        if len(cols) > 0:
            formatted_cols = ",".join(cols)

        formatted_where = ""
        if len(where) > 0:
            formatted_where = "WHERE " + " AND ".join(where)

        formatted_order_by = ""
        if len(order_by) > 0:
            formatted_order_by = "ORDER BY " + ",".join(order_by)

        formatted_limit = ""
        if limit is not None or limit != 0:
            formatted_limit = "LIMIT {}".format(limit)

        query = "SELECT {} FROM {} {} {} {}".format(
            formatted_cols,
            table_name,
            formatted_where,
            formatted_order_by,
            formatted_limit,
        )
        self.log.debug(query)

        results = []
        with self._conn as db:
            cur = db.execute(query)
            col_names = [tup[0] for tup in cur.description]
            for row in cur:
                result = dict()
                idx = 0
                for val in row:
                    result[col_names[idx]] = val
                    idx += 1

                results.append(result)

        return results

    def insert_row(self, table_name, row):
        formatted_row = self._format_values(row)
        query = "INSERT INTO {} VALUES {}".format(table_name, formatted_row)
        self.log.debug(query)

        with self._conn as db:
            db.execute(query)

    def insert_rows(self, table_name, rows):
        formatted_rows = ",".join([self._format_values(row) for row in rows])
        query = "INSERT INTO {} VALUES {}".format(table_name, formatted_rows)
        self.log.debug(query)

        with self._conn as db:
            db.execute(query)

    def _check_connection(self):
        return self._conn is not None

    def _format_values(self, values):
        parsed_values = []
        for value in values:
            if isinstance(value, str):
                value = "'{}'".format(value)

            parsed_values.append(value)

        formatted_values = "(" + ",".join(map(str, parsed_values)) + ")"

        return formatted_values
