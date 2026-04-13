from config import train_info
from script import scraper, parser, parse_raw_csv
from api import get_weather_data as gwd
from pipeline import Pipeline
import time
import random
from pathlib import Path

def main():
 # paths
    path = Path(__file__).parent
    paths = {
        "raw_html_path": path / "data/raw_html",
        "raw_csv_path": path / "data/raw_csv",
        "train_config_path": path / "config/trains.json",
        "parsed_csv_path": path / "data/parsed_csv",
        "train_geo_location": path
        / "train_geo_location"/"india_railway_stations.geojson",
    }

    # create path if not exist
    paths["raw_html_path"].mkdir(parents=True, exist_ok=True)
    paths["raw_csv_path"].mkdir(parents=True, exist_ok=True)
  
    train_data = train_info.get_train_info(paths["train_config_path"])

     #create pipeline object
    pipeline = Pipeline(paths)
    pipeline.run(train_data)
    return
       # parser call
    parser.parser(raw_html_path, raw_csv_path)
    # fixing column of primary.csv but processing both files to /parsed_csv
    for train_dir in raw_csv_path.iterdir():
        if train_dir.is_dir():
            file_primary = train_dir / "primary.csv"
            file_time_series = train_dir / "time_series.csv"

            df_primary = parse_raw_csv.process_raw_csv(
                file_primary, "Avg Delay (in min)", -1
            )
            df_time_series = parse_raw_csv.process_raw_csv(file_time_series, None, None)

            if df_primary is not None:
                train_parsed_path = parsed_csv_path / train_dir.stem
                train_parsed_path.mkdir(parents=True, exist_ok=True)
                output_file = train_parsed_path / "primary.csv"
                if output_file.exists():
                    print(f"Skipping {output_file} already exist")
                    continue

                print("Parsed raw file")
                print(f"[INFO] Saving: {train_parsed_path}")
                df_primary.to_csv(output_file, index=False)
            else:
                print(f"[WARN] Skipped: {file_primary.name}")

            if df_time_series is not None:
                train_parsed_path = parsed_csv_path / train_dir.stem
                train_parsed_path.mkdir(parents=True, exist_ok=True)
                output_file = train_parsed_path / "time_series.csv"
                if output_file.exists():
                    print(f"Skipping {output_file} already exist")
                    continue

                print("Parsed raw file")
                print(f"[INFO] Saving: {train_parsed_path}")
                df_time_series.to_csv(output_file, index=False)
            else:
                print(f"[WARN] Skipped: {file_primary.name}")

    # build weather dataset
    output_path = Path("data/weather")
    gwd.build_weather_dataset(raw_csv_path, train_geo_location, output_path)

if __name__ == "__main__":
  main() 
