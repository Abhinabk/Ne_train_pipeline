import duckdb
from pathlib import Path


def create_database(
    path_to_db: Path, path_to_train: Path, path_to_weather: Path
) -> None:

    print(f"IN DB {path_to_db}")

    # con = duckdb.connect(str(path_to_db/"ne_pipeline.db"))
    with duckdb.connect(str(path_to_db / "ne_pipeline.db")) as con:
        #TRAIN
        con.execute("""
            CREATE TABLE IF NOT EXISTS train_delay (
                train_no VARCHAR,
                date DATE,
                station VARCHAR,
                delay_minutes INTEGER,
                PRIMARY KEY (train_no, date, station)
            )
        """)

        con.execute(f"""
            INSERT OR IGNORE INTO train_delay
            SELECT
                Train AS train_no,
                Date AS date,
                Station AS station,
                Delay AS delay_minutes
            FROM read_csv('{str(path_to_train)}')
        """)

        #WEATHER
        con.execute("""
            CREATE TABLE IF NOT EXISTS weather (
            train_no VARCHAR,
            date DATE,
            temperature_2m_max DOUBLE,
            temperature_2m_min DOUBLE,
            temperature_2m_mean DOUBLE,
            precipitation_sum DOUBLE,
            rain_sum DOUBLE,
            wind_speed_10m_max DOUBLE,
            wind_gusts_10m_max DOUBLE,
            relative_humidity_2m_mean DOUBLE,
            weather_code INTEGER,
        PRIMARY KEY (train_no, date)
            )
        """)

        con.execute(f"""
            INSERT OR IGNORE INTO weather
            SELECT *
            FROM read_csv('{str(path_to_weather)}')
        """)

        con.sql("""
        SELECT * from train_delay USING SAMPLE 10 ROWS
        """).show()
        con.sql("""
        SELECT * from weather USING SAMPLE 10 ROWS
        """).show()

        con.sql("""
        SELECT COUNT() from train_delay
        """).show()
        con.sql("""
        SELECT COUNT(*) from weather 
        """).show()


if __name__ == "__main__":
    path_to_db = Path("data/database")
    path_to_ts = Path("data/processed/time_series.csv")
    path_to_weather = Path("data/processed/weather.csv")
    path_to_db.mkdir(parents=True, exist_ok=True)
    path_to_ts.parent.mkdir(parents=True, exist_ok=True)
    path_to_weather.parent.mkdir(parents=True, exist_ok=True)

    create_database(path_to_db, path_to_ts, path_to_weather)
