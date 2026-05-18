from config import train_info
from pipeline import Pipeline
from pathlib import Path

def main():
    path = Path(__file__).parent
    paths = {
        "raw_html_path": path / "data"/"raw"/"raw_html",
        "raw_csv_path": path / "data"/"raw"/"raw_csv",
        "raw_csv_weather_path": path / "data"/"raw"/"weather",
        "train_config_path": path / "config/trains.json",
        "train_geo_location_json": path / "train_geo_location"/"india_railway_stations.geojson",
        "api_data_path":  path/"data"/"raw"/"weather",
        "processed_path": path/"data"/"processed",
        "database_path": path/"data"/"database",
        "path_to_address_csv": path/"data"/"processed"/"address.csv",
        "path_to_station_coord_csv": path/"data"/"processed"/"station_coordinates.csv"
    }
    #TODO Move to pipeline
    # create path if not exist for saving 
    paths["raw_html_path"].mkdir(parents=True, exist_ok=True)
    paths["raw_csv_path"].mkdir(parents=True, exist_ok=True)
    paths["raw_csv_weather_path"].mkdir(parents=True, exist_ok=True)
    paths["api_data_path"].mkdir(parents=True, exist_ok=True)
    paths["processed_path"].mkdir(parents=True, exist_ok=True)
    paths["database_path"].mkdir(parents=True, exist_ok=True)
    
  
    train_data = train_info.get_train_info(paths["train_config_path"])

     #create pipeline object
    pipeline = Pipeline(paths)
    print("----- PIPELINE START -----")
    pipeline.run(train_data)
    print("----- PIPELINE END -----")

if __name__ == "__main__":
  main() 
