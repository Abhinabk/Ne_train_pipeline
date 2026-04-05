from script import get_location
from pathlib import Path

path_to_primary_csv = Path("data/parsed_csv/")
path_to_geo_loc = Path( "train_geo_location/india_railway_stations.geojson")

longitude_latitude = get_location.get_longitude_latitude(path_to_primary_csv,path_to_geo_loc)
print(longitude_latitude)