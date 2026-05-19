import duckdb


def table_has_data(con: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    result = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = ?
    """,
        [table_name],
    ).fetchone()

    if not result or result[0] == 0:
        return False

    row_count = con.execute(f"""
        SELECT COUNT(*)
        FROM {table_name}
    """).fetchone()
    if not row_count or row_count[0] == 0:
        return False
    return True
