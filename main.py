from config import train_info
from pipeline import Pipeline
from pathlib import Path

def main():
    path = Path(__file__).parent
    paths = {
        "raw_html_path": path / "data"/"raw"/"raw_html",
        "raw_csv_path": path / "data"/"raw"/"raw_csv",
        "train_config_path": path / "config/trains.json",
        "parsed_csv_path": path / "data"/"raw"/"parsed_csv",
        "train_geo_location": path / "train_geo_location"/"india_railway_stations.geojson",
        "api_data_path":  path/"data"/"raw"/"weather",
        "processed_csv_path": path/"data"/"processed"
    }

    # create path if not exist for saving 
    paths["raw_html_path"].mkdir(parents=True, exist_ok=True)
    paths["raw_csv_path"].mkdir(parents=True, exist_ok=True)
    paths["parsed_csv_path"].mkdir(parents=True, exist_ok=True)
    paths["api_data_path"].mkdir(parents=True, exist_ok=True)
  
    train_data = train_info.get_train_info(paths["train_config_path"])

     #create pipeline object
    pipeline = Pipeline(paths)
    print("----- PIPELINE START -----")
    pipeline.run(train_data)
    print("----- PIPELINE END -----")

if __name__ == "__main__":
  main() 
