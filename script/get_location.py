import json
from pathlib import Path
import pandas as pd
from pandas import Series


def get_station_codes(path_to_primary_csv: Path) -> Series:
    df = pd.read_csv(path_to_primary_csv)
    return df["Stations"]


def get_coords(station_code: str, path_to_geo_loc: Path) -> dict | None:
    """return longitude and latitude"""
    return_dict = {}
    with open(path_to_geo_loc, "r") as f:
        data = json.load(f)
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
    lon_lat = {}
    for csv_file in path_to_raw_csv.rglob("*.csv"):
        if csv_file.stem == "primary":
            station_name = get_station_codes(csv_file)[0]
            df = pd.read_csv(csv_file)
            train_no = str(df["Train"].iloc[0])
            lon_lat[train_no] = get_coords(station_name, path_to_geo_loc)

    return lon_lat
