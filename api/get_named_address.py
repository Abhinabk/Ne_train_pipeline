from geopy.geocoders import Nominatim
import pandas as pd
from pathlib import Path
import time

#verys strict api only 1 request per sec 
def get_address(path_to_station_coords,output_path:Path):
    df = pd.read_csv(path_to_station_coords)
    geolocator = Nominatim(user_agent="geo_state_lookup")
    total = len(df)
    count=0
    output_csv_path = output_path/"address.csv"
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    stations_not_found = set()
    
    if output_csv_path.exists():
        completed_df = pd.read_csv(output_csv_path, usecols=["station_code"])
        completed = set(completed_df["station_code"])
    else:
        completed = set()
    
    for rows in df.itertuples(index=False):
        station_code = rows.station_code
        longitude = rows.longitude
        latitude = rows.latitude
        if station_code in completed:
            count+=1
            print(f"[SKIP] {station_code} present ")
            print(f"[LOG] completed {count}/{total}")
            continue
        try:
            location = geolocator.reverse(f"{latitude}, {longitude}",timeout=10)
            if location:
                address = location.raw.get("address", {}) # type: ignore
                address_row = pd.DataFrame([{ 
                    "station_code": station_code,
                    "state": address.get("state"),
                    "district": address.get("state_district"),
                    "country": address.get("country")
                }])
                
                address_row.to_csv(output_csv_path,mode="a",
                                header= not output_csv_path.exists(),index=False)
                completed.add(station_code)
                print(f"[LOG] SUCCESS {station_code}")
            else:
                stations_not_found.add(station_code)
                print(f"[WARN] {station_code} not found")

        except Exception as e:
            print(f"[ERROR] {station_code}: {e}")
            
        count+=1
        print(f"[LOG] completed {count}/{total}")
        time.sleep(1)
        
    if stations_not_found:
        print(f"[WARN] stations not found: {stations_not_found}")

if __name__ == "__main__":
    path_to_station_coords = Path("data/processed/station_coordinates.csv") 
    output_path = Path("data/processed")
    get_address(path_to_station_coords,output_path)
