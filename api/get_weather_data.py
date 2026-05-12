from script import get_min_max_date
from pathlib import Path
import requests
from typing import Any
import pandas as pd
from datetime import datetime,date
import time 
import random
# open-meteo api call
def fetch_weather_daily(
    station_code: str, latitude: float, longitude: float, start_date: str, end_date: str
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
    response = requests.get(url=url, params=params, timeout=(5, 30))
    response.raise_for_status()
    print(f"[FETCH] {station_code}")
    return {"station_code": station_code,"weather": response.json()}

def flatten_weather_data(weather_data: list[dict]) -> list[dict]:
    rows = []
    for station in weather_data:
        station_code = station["station_code"]
        daily = station.get("weather", {}).get("daily")
        if not daily:
            continue

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
    count = 0

    if path_to_weather_file.is_file():
        fetched_date = datetime.fromtimestamp(path_to_weather_file.stat().st_mtime).date()
        if fetched_date == date.today():
            print(f"[SKIP] {path_to_weather_file.name}")
            return
        
    station_df = pd.read_csv(station_coordinates_path)
    min_max_date = get_min_max_date.get_global_date_range(raw_csv_path)
    start_date,end_date = min_max_date
    total_stations = len(station_df['station_code'])
    if not min_max_date:
        print("[WARN] No min/max dates found")
        return
    
    weather_data = []

    print("[LOG] Fetching weather data from API...")

    for _,row in station_df.iterrows():

        station_code = row["station_code"]
        latitude = row["latitude"]
        longitude = row["longitude"]
        

        try:
            data = fetch_weather_daily(station_code, latitude, longitude, start_date, end_date)
            weather_data.append(data)
            count+=1
            print(f"[LOG] Fetched weather for station: {station_code} {count}/{total_stations}")
            delay = random.uniform(1, 2)
            print(f"[LOG] Sleeping for {delay:.2f}s")
            time.sleep(delay)
        except Exception as e:
            need_to_fetch_again.add(station_code)
            print(f"[WARN] [{station_code}] API failed: {e}")

    rows = flatten_weather_data(weather_data)
    if not rows:
        print("[WARN] No weather data collected")
        return
    df = pd.DataFrame(rows)
    df.to_csv(path_to_weather_file, index=False)
    print(f"[DONE] Saved {path_to_weather_file.name}")



if __name__ == "__main__":
    output_path = Path("data/raw/weather")
    raw_csv_path = Path("data/raw/raw_csv")
    station_coordinates_path = Path("data/processed/station_coordinates.csv")
    build_weather_dataset(raw_csv_path, station_coordinates_path, output_path)
