from script import get_location, get_min_max_date
from pathlib import Path
import requests
from typing import Any
import pandas as pd

# open-meteo api call
def fetch_weather_daily(train_no:str,lat:float,long:float,start_date:str,end_date:str)->dict[str,Any]:
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": long,
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
    response = requests.get(url=url, params=params)
    response.raise_for_status()
    weather_data = response.json()
    print(f"Fetching train {train_no}")
    return{"train_no":train_no,"weather":weather_data}

def flatten_weather_data(weather_data: list[dict]) -> list[dict]:
    rows = []

    for train in weather_data:
        train_no = train["train_no"]
        daily = train["weather"]["daily"]

        for i in range(len(daily["time"])):
            rows.append({
                "train_no": train_no,
                "date": daily["time"][i],
                "temp_max": daily["temperature_2m_max"][i],
                "temp_min": daily["temperature_2m_min"][i],
                "temp_mean": daily["temperature_2m_mean"][i],
                "precipitation_sum": daily["precipitation_sum"][i],
                "rain_sum": daily["rain_sum"][i],
                "wind_speed": daily["wind_speed_10m_max"][i],
                "wind_gust": daily["wind_gusts_10m_max"][i],
                "humidity": daily["relative_humidity_2m_mean"][i],
                "weathercode": daily["weather_code"][i],
            })

    return rows

def build_weather_dataset(path_to_raw_csv_folder:Path,path_to_geo_loc_csv:Path,output_path)->None:
    # path_to_raw_csv = Path("data/parsed_csv/")
    # path_to_geo_loc = Path("train_geo_location/india_railway_stations.geojson")

    long_lat = get_location.get_longitude_latitude(
        path_to_raw_csv_folder, path_to_geo_loc_csv
    )
    min_max_date = get_min_max_date.get_min_max_time(path_to_raw_csv_folder)
    path_to_weather_file = output_path/"weather_clean.csv"

    if path_to_weather_file.exists():
        print(f"[INFO] file {path_to_weather_file} already exist skipping")
    else:
        weather_data = []
        print("Fetching weather data from API...")
        for train in long_lat.items():
            long = train[1]['long']
            lat = train[1]['lat']
            start_date = min_max_date[train[0]][0]
            end_date = min_max_date[train[0]][1]
            train_no = train[0]
            
            try:
                data = fetch_weather_daily(train_no,lat,long,start_date,end_date)
                weather_data.append(data)
            except Exception as e:
                print(f"[WARN] Train {train_no} failed \nStatus error {e}")
        
        rows = flatten_weather_data(weather_data)
        df = pd.DataFrame(rows)
        df.to_csv(path_to_weather_file, index=False)

        



if __name__ == "__main__":
    output_path = "data/weather_clean.csv" 
    path_to_raw_csv_folder = Path("data/parsed_csv/")
    path_to_geo_loc_csv = Path("train_geo_location/india_railway_stations.geojson")

    build_weather_dataset(path_to_raw_csv_folder,path_to_geo_loc_csv,output_path)