import duckdb
from pathlib import Path
import pandas as pd 

def get_route(raw_csv_path:Path)->list[tuple]:
    routes = []
    for csv_file in raw_csv_path.rglob("time_series.csv"):
        df = pd.read_csv(csv_file,nrows=1)
        train_no = str(df.iloc[0]['Train'])
        stations = df.drop(['Train','Date'],axis=1).columns.to_list()
        for order,station_code in enumerate(stations,start=1):
            routes.append((train_no,order,station_code))
    return routes


def create_database(
    path_to_db: Path, path_to_train: Path, path_to_weather: Path,raw_csv_path:Path,
    path_to_station_coords:Path,con:duckdb.DuckDBPyConnection
) -> None:
    
    '''old schema expected train_no new data became station_code as column types were same
    so schema drift have to be careful.'''
    route_data = get_route(raw_csv_path)
    print(f"IN DB {path_to_db}")

    #coordinate
    
    con.execute("""
        CREATE TABLE IF NOT EXISTS stations_coordinates(
            station_code VARCHAR,
            station_name VARCHAR,
            longitude DOUBLE, 
            latitude DOUBLE,
            PRIMARY KEY (station_code)
        )
    """)
    con.execute(f"""
        INSERT OR IGNORE INTO stations_coordinates
        SELECT
            station_code,
            station_name,
            longitude,
            latitude
        FROM read_csv('{str(path_to_station_coords)}') 
        
    """)
    #routes 
    con.execute("""
    CREATE TABLE IF NOT EXISTS train_route (
        train_no VARCHAR,
        station_order INTEGER,
        station_code VARCHAR,
        PRIMARY KEY (train_no, station_order)
        )
    """
    )
    con.executemany("""
    INSERT OR IGNORE INTO train_route
        VALUES (?, ?, ?)
    """, route_data)
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
        PRIMARY KEY (station_code, date)
        )
    """)

    con.execute(f"""
        INSERT OR IGNORE INTO weather
        SELECT 
        station_code,
        date,
        temperature_2m_max,
        temperature_2m_min,
        temperature_2m_mean,
        precipitation_sum,
        rain_sum,
        wind_speed_10m_max,
        wind_gusts_10m_max,
        relative_humidity_2m_mean,
        weather_code
        FROM read_csv('{str(path_to_weather)}')
    """)

    con.sql("""
    SELECT * from train_delay USING SAMPLE 10 ROWS
    """).show()
    con.sql("""
    SELECT * from weather USING SAMPLE 10 ROWS
    """).show()
    con.sql("""
    SELECT * from stations_coordinates USING SAMPLE 10 ROWS
    """).show()


    con.sql("""
    SELECT COUNT() as total_rows_train from train_delay
    """).show()
    con.sql("""
    SELECT COUNT(*) as total_rows_weather from weather 
    """).show()
    con.sql("""
    SELECT COUNT(*) total_rows_station_coord from stations_coordinates
    """).show()
    con.sql("""
    SELECT COUNT(*) total_rows_routes from train_route
    """).show()


if __name__ == "__main__":
    path_to_db = Path("data/database")
    path_to_ts = Path("data/processed/time_series.csv")
    path_to_weather = Path("data/processed/weather.csv")
    raw_csv_path = Path("data/raw/raw_csv")
    path_to_station_coords =  Path("data/processed/station_coordinates.csv")
    path_to_db.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(path_to_db / "ne_pipeline.db")) as con:
        create_database(path_to_db, path_to_ts, 
                        path_to_weather,raw_csv_path,path_to_station_coords,con)
