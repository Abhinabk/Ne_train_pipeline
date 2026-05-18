import duckdb
from pathlib import Path

def process_train(path_to_train_raw: Path, con: duckdb.DuckDBPyConnection) -> None:
    for csv_file in path_to_train_raw.rglob("time_series.csv"):
        con.execute(f"""
            INSERT OR IGNORE INTO raw.train_delay_raw
            SELECT
                Train AS train_no,
                strptime(Date, '%Y-%m-%d')::DATE AS date,
                Station AS station_code,
                Delay::INTEGER AS delay_minutes,
                CURRENT_TIMESTAMP AS fetched_at
            FROM (
                    UNPIVOT read_csv_auto(
                    '{str(csv_file)}',
                    union_by_name=True)
                ON COLUMNS(* EXCLUDE (Train, Date))
                INTO
                    NAME Station
                    VALUE Delay
            )
        """)


if __name__ == "__main__":
    path_to_raw = Path("data/raw/parsed_csv")

    path_to_db = Path("data/database")
    with duckdb.connect(str(path_to_db / "ne_pipeline.db")) as con:
    # process(path_to_raw, path_to_processed)
    
        process_train(path_to_raw,con)


