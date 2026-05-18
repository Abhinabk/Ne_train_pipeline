from pathlib import Path
import requests
from typing import Any
import pandas as pd
import time 
import random
import duckdb
from script import get_min_max_date
# open-meteo api call
session  = requests.Session()

def fetch_weather_daily(
    station_code: str, latitude: float, longitude: float, start_date: str, end_date: str,
    max_retries:int = 5
) -> dict[str, Any]:
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": [
            "weather_code",
            "temperature_2m_mean",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "rain_sum",
            "daylight_duration",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "relative_humidity_2m_mean",
        ],
    }
    for attempt in range(max_retries):
        try:
            response = session.get(url=url, params=params, timeout=(5, 30))
            #rate limted
            if response.status_code == 429:
                reason = response.json().get("reason","Rate limit exceeded")
                raise requests.exceptions.HTTPError(reason,response=response)
                 
            response.raise_for_status()
            print(f"[FETCH] {station_code}")
            return {"station_code": station_code,"weather": response.json()}
       
        except(requests.exceptions.Timeout,requests.exceptions.ConnectionError) as e:
            if attempt == max_retries-1:
                raise e 
            #exp backoff
            wait = (2 ** attempt) + random.uniform(1, 3) #jitter for thurering herd
            print(f"[RETRY]attempt {attempt+1}/{max_retries} in {wait:.1f}s")
            time.sleep(wait)

    raise AssertionError("Unreachable")

def flatten_weather_data(weather_data: dict) -> list[dict]:
    #run agianst single station at a time
    rows = []
    station_code = weather_data["station_code"]
    daily = weather_data.get("weather", {}).get("daily")
    if not daily:
        return rows
    
    for i in range(len(daily["time"])):
        rows.append(
            {   
                "station_code": station_code,
                "date": daily["time"][i],
                "temperature_2m_max": daily["temperature_2m_max"][i],
                "temperature_2m_min": daily["temperature_2m_min"][i],
                "temperature_2m_mean": daily["temperature_2m_mean"][i],
                "precipitation_sum": daily["precipitation_sum"][i],
                "rain_sum": daily["rain_sum"][i],
                "wind_speed_10m_max": daily["wind_speed_10m_max"][i],
                "wind_gusts_10m_max": daily["wind_gusts_10m_max"][i],
                "relative_humidity_2m_mean": daily["relative_humidity_2m_mean"][i],
                "weather_code": daily["weather_code"][i]
            }
        )

    return rows


def build_weather_dataset(
    raw_csv_path: Path,
    station_coordinates_path: Path,
    con:duckdb.DuckDBPyConnection) -> None:

    #create the staging tabel
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


    need_to_fetch_again = set()
    count = 0

    station_df = pd.read_csv(station_coordinates_path)
    min_max_date = get_min_max_date.get_global_date_range(raw_csv_path)
    total_stations = len(station_df['station_code'])

    if not min_max_date:
        print("[WARN] No min/max dates found")
        return
    
    start_date,end_date = min_max_date
    #resume from last Station
    expected_days = (pd.to_datetime(end_date)- pd.to_datetime(start_date)).days + 1
    completed_stations = set(
        i[0] for i in con.execute("""
            SELECT
                station_code
            FROM  raw.weather_raw
            GROUP BY station_code
            HAVING COUNT(DISTINCT date)>=?
        """,[expected_days]).fetchall() 
        )
    #returns a list of tuple [('STATION_A',), ('STATION_B',)] comma makes it a tuple if not its type will be just string
    # completed_stations = set(i[0] for i in completed_stations_tuple)        
    count = len(completed_stations)
    print(f"[RESUME] Found {count} completed stations")
    
    print("[LOG] Fetching weather data from API...")

    for row in station_df.itertuples(index=False):

        station_code = str(row.station_code)
        latitude = float(str(row.latitude))
        longitude = float(str(row.longitude))
        if station_code in completed_stations:
            print(f"[SKIP] {station_code} already fetched")
            continue

        try:
            data = fetch_weather_daily(station_code,latitude,longitude,start_date,end_date)
            rows = flatten_weather_data(data)
            if rows:
                row_list = [list(r.values()) for r in rows]
                con.execute("""
                    INSERT OR IGNORE INTO raw.weather_raw
                    SELECT *,now() FROM ?
                """,[row_list])
            
            count+=1
            print(f"[LOG] Fetched weather for {station_code} Completed: {count}/{total_stations}")
            delay = random.uniform(4, 8)
            print(f"[LOG] Sleeping for {delay:.2f}s")
            time.sleep(delay)
        except requests.exceptions.HTTPError as e:
            if(e.response is not None and e.response.status_code == 429):
                print(f"[RATE LIMIT] {e}")
                print(f"[STOP] Resume later [{station_code}]")
                break
            need_to_fetch_again.add(station_code)

        except requests.exceptions.RequestException as e:
            need_to_fetch_again.add(station_code)
            print(f"[WARN] [{station_code}] API failed: {e}")

    if need_to_fetch_again:
        print("\n[FAILED STATIONS]")
        print(need_to_fetch_again)

    print("[DONE] Weather data stored in DuckDB")



if __name__ == "__main__":
    raw_csv_path = Path("data/raw/raw_csv")
    station_coordinates_path = Path("data/processed/station_coordinates.csv")
    path_to_db = Path("data/database/ne_pipeline.db")
    with duckdb.connect(str(path_to_db)) as con:
        build_weather_dataset(raw_csv_path, station_coordinates_path,con)
