import json
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import re 
# MANUAL_COORDS = {
#     "DDU":  {"lat": 25.278149, "long": 83.11925 },  #prev mgs (mugal sarai)
#     "PRYJ": {"lat": 25.446241, "long": 81.828816}, #still uses allahabad  in geojson dataset
#     "NBJU": {"long": 87.0627, "lat": 25.8656},  
#     "PCOI": {"long": 82.5685, "lat": 25.5014},  
    
# }
def load_geo_data(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Geo data file not found: {path}") 
def get_overlap_percentage(s1, s2):
    return SequenceMatcher(None, s1, s2).ratio()
      
def extract_station_names_from_html(raw_html_path: Path,station_code:str) -> dict[str, str]:
    """Extract {station_code: station_name} from already-scraped HTML files"""
    code_to_name = {}
    for html_file in raw_html_path.rglob("*.html"):
        soup = BeautifulSoup(html_file.read_text(), "html.parser")
        # matches "DIBRUGARH (DBRG)", "LUMDING JN (LMG)" etc
        for text in soup.stripped_strings:
            match = re.search(rf"(.+?)\(({station_code})\)", text)
            if match:
                name = match.group(1).strip().upper()
                code = match.group(2).strip()
                code_to_name[code] = name
    return code_to_name



def get_coords(raw_html_path:Path,station_code: str,geo_data: dict) -> dict | None:
    """return longitude and latitude"""
    code_to_name = extract_station_names_from_html(raw_html_path, station_code)
    station_name = code_to_name.get(station_code, "").upper()

    if not station_name:
        print(f"[WARN] {station_code} not found in any HTML file")
        return None
    
    for feature in geo_data["features"]:
        geo_name = feature["properties"]["name"].upper()
        if station_name in geo_name:
            lon, lat = feature["geometry"]["coordinates"]
            return {"Station_code": station_code, "longitude": lon, "latitude": lat}
        
        elif get_overlap_percentage(station_name, geo_name)>0.5:
            lon, lat = feature["geometry"]["coordinates"]
            return {"Station_code": station_code, "longitude": lon, "latitude": lat}
    
    print(f"[WARN] {station_code} ({station_name}) not found in GeoJSON")
    return None

def get_longitude_latitude(path_to_raw_csv: Path, raw_html_path:Path,path_to_geo_loc_json: Path) -> dict:
    """return the long and latitude of all station of the journey
    GeoJSON coordinate order is: [longitude, latitude]

    #TODO: Insed of looping over geojson every
    #  time build a hastable of only the station names and coordinates
    """
    geo_data = load_geo_data(path_to_geo_loc_json)
    if not geo_data:
        return {}
    
    all_coords = {}
    for csv_file in path_to_raw_csv.rglob("time_series.csv"):
        df = pd.read_csv(csv_file,nrows=0)
        stations = df.drop(columns=['Train','Date']).columns.tolist()
        for station_code in stations:
            if station_code not in all_coords:
                coords = get_coords(raw_html_path,station_code, geo_data)
                if coords:
                    all_coords[station_code] = coords
                else:
                    print(f"[WARN] No coords for {station_code}")

    return all_coords

if __name__ == "__main__":
    raw_csv_path = Path("data/raw/raw_csv")
    path_to_geo_loc_json = Path("train_geo_location/Railway_Station.geojson")
    raw_html_path = Path("data/raw/raw_html")
    print(get_longitude_latitude(raw_csv_path,raw_html_path,path_to_geo_loc_json))
