from script import get_min_max_date
from pathlib import Path
import requests
from typing import Any
import pandas as pd
import time 
import random
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
            
                # print(response.text)
                # print(response.headers)
                #backoff reties not working adding a global cooldown
                # cooldown = 60 + random.uniform(0, 10)
                # print(
                #     f"[RATE LIMIT] cooling down for {cooldown:.1f}s")
                # time.sleep(cooldown)
                # continue

            response.raise_for_status()
            print(f"[FETCH] {station_code}")
            return {"station_code": station_code,"weather": response.json()}
       
        except(requests.exceptions.Timeout,
            requests.exceptions.ConnectionError) as e:
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
                "station-code": station_code,
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
    output_path: Path,
) -> None:

    path_to_weather_file = output_path / "weather.csv"
    need_to_fetch_again = set()
    completed_stations = set()
    count = 0

    station_df = pd.read_csv(station_coordinates_path)
    #nearby station mostly will be same data trying to reduce api calls
    station_df["latitude"] = station_df["latitude"].round(2)
    station_df["longitude"] = station_df["longitude"].round(2)
    
    station_df = station_df.drop_duplicates(subset=['longitude','latitude'])
    min_max_date = get_min_max_date.get_global_date_range(raw_csv_path)
    total_stations = len(station_df['station_code'])

    if not min_max_date:
        print("[WARN] No min/max dates found")
        return
    
    start_date,end_date = min_max_date
    #resume from last Station
    if path_to_weather_file.is_file():
        existing_df = pd.read_csv(path_to_weather_file,usecols=["station-code"])
        expected_days = (pd.to_datetime(end_date)- pd.to_datetime(start_date)).days + 1
        station_counts = (existing_df.groupby("station-code").size())

        completed_stations = set(station_counts[station_counts >= expected_days].index)        
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
                df = pd.DataFrame(rows)
                df.to_csv(path_to_weather_file,mode="a",header=not path_to_weather_file.exists(),index=False)
            
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

    print(f"[DONE] Saved {path_to_weather_file.name}")



if __name__ == "__main__":
    output_path = Path("data/raw/weather")
    raw_csv_path = Path("data/raw/raw_csv")
    station_coordinates_path = Path("data/processed/station_coordinates.csv")
    build_weather_dataset(raw_csv_path, station_coordinates_path, output_path)
