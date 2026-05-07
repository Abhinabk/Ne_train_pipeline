import json
from pathlib import Path
import pandas as pd

def load_geo_data(path):
    with open(path, "r") as f:
        return json.load(f)
    
def get_coords(station_code: str, geo_data: dict) -> dict | None:
    """return longitude and latitude"""
    return_dict = {}
    data = geo_data
    for feature in data["features"]:
        prop = feature["properties"]
        if prop.get("code") == station_code:
            return_dict["Station_code"] = station_code
            return_dict["long"] = prop["long"]
            return_dict["lat"] = prop["lat"]
            return return_dict

    print(f"{station_code} not found")
    return None


def get_longitude_latitude(path_to_raw_csv: Path, path_to_geo_loc: Path) -> dict:
    """return the long and latitude of first station of the journey"""
    geo_data = load_geo_data(path_to_geo_loc)
    lon_lat = {}
    for csv_file in path_to_raw_csv.rglob("time_series.csv"):

        df = pd.read_csv(csv_file)
        stations = df.drop(columns=['Train','Date']).columns.tolist()
        if not stations:
            continue
        station_name = stations[0]
        train_no = str(df["Train"].iloc[0])
        if train_no not in lon_lat:
            coords = get_coords(station_name, geo_data)
            if coords:
                lon_lat[train_no] = coords
            else:
                print(f"[WARN] Missing coords for {train_no} ({station_name})")

    return lon_lat
