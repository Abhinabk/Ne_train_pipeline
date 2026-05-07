import duckdb 
from pathlib import Path
def create_database(path_to_db:Path,processed_ts_path:Path)->None:
    
    print(f"IN DB {processed_ts_path}")
    con = duckdb.connect(str(path_to_db/"ne_pipeline.db"))
    con.execute("""
        CREATE TABLE IF NOT EXISTS train_delay (
            train_no    INTEGER,
            date        DATE,
            station     VARCHAR,
            delay_minutes FLOAT,
            PRIMARY KEY (train_no, date, station)
        )
    """)


    con.execute(f"""
        INSERT OR IGNORE INTO train_delay
        SELECT 
            Train, 
            Date::DATE, 
            Station, 
            Delay 
        FROM read_csv('{processed_ts_path}')
    """)

    con.sql("""
        SELECT * from train_delay USING SAMPLE 10 ROWS
    """).show()
    

if __name__ == '__main__':
    path_to_db = Path("data/database")
    path_to_ts= Path("data/processed/time_series.csv")
    path_to_db.mkdir(parents=True, exist_ok=True)
    path_to_ts.parent.mkdir(parents=True, exist_ok=True)

    create_database(path_to_db,path_to_ts)

    