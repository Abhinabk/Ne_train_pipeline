import duckdb 

def table_has_data(con:duckdb.DuckDBPyConnection,table_name:str) -> bool:
    table = con.execute("""
        SELECT COUNT(*)
        FROM raw.weather_raw
    """).fetchone()

    if table is None:
        return False
    if table[0]==0:
        return False
    
    row_count = con.execute(f"""
        SELECT COUNT(*)
        FROM {table_name}
    """).fetchone()
    if row_count is None:
        return False
    if row_count[0] ==0:
        return False
    
    return True 
