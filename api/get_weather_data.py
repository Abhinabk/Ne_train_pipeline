from script import get_location,get_min_max_date
from pathlib import Path

path_to_raw_csv = Path("data/parsed_csv/")
path_to_geo_loc = Path( "train_geo_location/india_railway_stations.geojson")

longitude_latitude = get_location.get_longitude_latitude(path_to_raw_csv,path_to_geo_loc)
min_max_date = get_min_max_date.get_min_max_time(path_to_raw_csv)
print(longitude_latitude)
print()
print(min_max_date)