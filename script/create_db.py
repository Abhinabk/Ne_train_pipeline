import duckdb
from pathlib import Path
import pandas as pd


def get_route(raw_csv_path: Path) -> list[tuple]:
    routes = []
    for csv_file in raw_csv_path.rglob("time_series.csv"):
        df = pd.read_csv(csv_file, nrows=1)
        train_no = str(df.iloc[0]["Train"])
        stations = df.drop(["Train", "Date"], axis=1).columns.to_list()
        for order, station_code in enumerate(stations, start=1):
            routes.append((train_no, order, station_code))
    return routes

def create_schema(con:duckdb.DuckDBPyConnection):
    #schema
    con.execute("""
        CREATE SCHEMA IF NOT EXISTS raw;
        CREATE SCHEMA IF NOT EXISTS analytics;
    """)


def create_database(
    path_to_db: Path,
    raw_csv_path: Path,
    path_to_address_csv,
    path_to_station_coords: Path,
    con: duckdb.DuckDBPyConnection,
) -> None:
    """old schema expected train_no new data became station_code as column types were same
    so schema drift have to be careful."""
    route_data = get_route(raw_csv_path)
    print(f"IN DB {path_to_db}")
   
    #staging table weather
    con.execute("""
    CREATE TABLE IF NOT EXISTS raw.weather_raw(
        station_code VARCHAR,
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
        fetched_at TIMESTAMP DEFAULT now(),
        PRIMARY KEY (station_code, date)
        )
    """)
    #staging table train
    con.execute("""
    CREATE TABLE IF NOT EXISTS raw.train_delay_raw(
        train_no VARCHAR,
        station_code VARCHAR,
        date DATE,
        delay_minutes INTEGER,
        fetched_at TIMESTAMP DEFAULT now(),
        PRIMARY KEY (train_no, station_code, date)
        )
    """)
    # coordinate
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.stations_coordinates_raw(
            station_code VARCHAR,
            station_name VARCHAR,
            longitude DOUBLE, 
            latitude DOUBLE,
            PRIMARY KEY (station_code)
        )
    """)
    con.execute(f"""
        INSERT OR IGNORE INTO raw.stations_coordinates_raw
        SELECT
            station_code,
            station_name,
            longitude,
            latitude
        FROM read_csv('{str(path_to_station_coords)}') 
        
    """)

    # address
    con.execute("""
    CREATE TABLE IF NOT EXISTS raw.station_address_raw (
        station_code VARCHAR ,
        state VARCHAR,
        district VARCHAR,
        country VARCHAR,
        PRIMARY KEY (station_code)
        )
    """)

    con.execute(f"""
    INSERT OR IGNORE INTO raw.station_address_raw
    SELECT
        station_code,
        state,
        district,
        country
    FROM read_csv('{str(path_to_address_csv)}')
    """)
    # routes
    con.execute("""
    CREATE TABLE IF NOT EXISTS raw.train_route_raw (
        train_no VARCHAR,
        station_order INTEGER,
        station_code VARCHAR,
        PRIMARY KEY (train_no, station_order)
        )
    """)
    con.executemany(
        """
    INSERT OR IGNORE INTO raw.train_route_raw
        VALUES (?, ?, ?)
    """,
        route_data,
    )
    
   
   
    con.sql("""
    SELECT * from raw.train_delay_raw USING SAMPLE 10 ROWS
    """).show()
    con.sql("""
    SELECT * from raw.weather_raw USING SAMPLE 10 ROWS
    """).show()
    con.sql("""
    SELECT * from raw.station_address_raw USING SAMPLE 10 ROWS
    """).show()
    con.sql("""
    SELECT * from raw.stations_coordinates_raw USING SAMPLE 10 ROWS
    """).show()

    con.sql("""
    SELECT COUNT() as total_rows_train from raw.train_delay_raw
    """).show()
    con.sql("""
    SELECT COUNT(*) as total_rows_weather from raw.weather_raw 
    """).show()
    con.sql("""
    SELECT COUNT(*) total_rows_station_coord from raw.stations_coordinates_raw
    """).show()
    con.sql("""
    SELECT COUNT(*) station_address_count from raw.station_address_raw
    """).show()
    con.sql("""
    SELECT COUNT(*) total_rows_routes from raw.train_route_raw
    """).show()

def create_view(con:duckdb.DuckDBPyConnection):
     # DENORMALISED VIEW
    con.execute("""
    CREATE OR REPLACE VIEW analytics.merged_view AS
    SELECT
        td.train_no,
        td.date,
        td.station_code ,
        td.delay_minutes,

        sc.latitude,
        sc.longitude,

        sa.state,
        sa.district,
        sa.country,

        w.temperature_2m_max,
        w.temperature_2m_min,
        w.temperature_2m_mean,
        w.precipitation_sum,
        w.rain_sum,
        w.wind_speed_10m_max,
        w.wind_gusts_10m_max,
        w.relative_humidity_2m_mean,
        w.weather_code

    FROM raw.train_delay_raw td

    LEFT JOIN raw.weather_raw w
        ON td.station_code = w.station_code
        AND td.date = w.date

    LEFT JOIN raw.stations_coordinates_raw sc
        ON td.station_code = sc.station_code

    LEFT JOIN raw.station_address_raw sa
        ON td.station_code = sa.station_code

    """)

    con.execute("""
    COPY (SELECT * FROM analytics.merged_view) 
    TO 'analysis/merged_view.parquet' 
    """)

if __name__ == "__main__":
    path_to_db = Path("data/database")
    raw_csv_path = Path("data/raw/raw_csv")
    path_to_address_csv = Path("data/processed/address.csv")
    path_to_station_coords = Path("data/processed/station_coordinates.csv")
    path_to_db.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(path_to_db / "ne_pipeline.db")) as con:
        create_schema(con)
        create_database(
            path_to_db,
            raw_csv_path,
            path_to_address_csv,
            path_to_station_coords,
            con,
        )
