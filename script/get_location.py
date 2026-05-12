import json
from pathlib import Path
import pandas as pd
from difflib import SequenceMatcher

MANUAL_COORDS = {
    "DDU":  {"long": 83.11925 , "lat":25.278149 },  #prev mgs (mugal sarai)
    "PRYJ": {"long": 81.828816 , "lat":25.446241 }, #still uses allahabad  in geojson dataset
    "NBJU": {"long": 85.988056, "lat":  25.462222},  
    "PCOI": {"long":  81.8672, "lat": 25.3767},  
    "DBLG": {"long":93.085623,"lat": 25.595283 },
    "NHLG":{"long":93.032239 ,"lat":25.1483324},
    "JGLP":{"long":92.950867,"lat":25.111219},
    "NHGJ":{"long":92.868056,"lat":25.112778},
}
def load_geo_data(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Geo data file not found: {path}") 
def get_overlap_percentage(s1, s2):
    return SequenceMatcher(None, s1, s2).ratio()
      



def get_coords(station_code: str,geo_data: dict) -> dict | None:
    """return longitude and latitude"""
 
    return_dict = {}
    for feature in geo_data["features"]:
        prop = feature["properties"]
        if prop.get("code") == station_code:
            return_dict["Station_code"] = station_code
            return_dict["long"] = prop["long"]
            return_dict["lat"] = prop["lat"]
            return return_dict
        
    if station_code in MANUAL_COORDS:
        print(f"[FALLBACK] Using manual coords for {station_code}")
        return {"Station_code": station_code, **MANUAL_COORDS[station_code]}
    print(f"{station_code} not found")
    return None

def get_longitude_latitude(path_to_raw_csv: Path,path_to_geo_loc_json: Path,output_path:Path) -> None:
    """return the long and latitude of all station of the journey
    GeoJSON coordinate order is: [longitude, latitude]

    #TODO: Insed of looping over geojson every
    #  time build a hastable of only the station names and coordinates
    """
    geo_data = load_geo_data(path_to_geo_loc_json)
    if not geo_data:
        return None

    all_coords = {}
    for csv_file in path_to_raw_csv.rglob("time_series.csv"):
        df = pd.read_csv(csv_file, nrows=0)
        stations = df.drop(columns=['Train', 'Date']).columns.tolist()
        for station_code in stations:
            if station_code not in all_coords:
                coords = get_coords(station_code, geo_data)
                if coords:
                    all_coords[station_code] = coords
                else:
                    print(f"[WARN] No coords for {station_code}")
    df = pd.DataFrame(all_coords.values()).reset_index(drop=True)
    df.to_csv(output_path/"station_coordinates.csv")

if __name__ == "__main__":
    raw_csv_path = Path("data/raw/raw_csv")
    path_to_geo_loc_json = Path("train_geo_location/india_railway_stations.geojson")
    raw_html_path = Path("data/raw/raw_html")
    output_path = Path("data/processed")
    get_longitude_latitude(raw_csv_path,path_to_geo_loc_json,output_path)
