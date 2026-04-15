""""
Merege the raw_processd_csv into a single file
"""

from pathlib import Path
import pandas as pd


def process(path_to_raw: Path, path_to_processed: Path) -> None:
    primary_files = []
    time_series_files = []
    primary_row_count = 0
    ts_row_count = 0

    for i in path_to_raw.rglob("*.csv"):
        if i.stem == "primary":
            df = pd.read_csv(i)
            primary_files.append(i)
            primary_row_count+=len(df)

        elif i.stem == "time_series":
            df = pd.read_csv(i)
            #here
            df = df.melt(
                id_vars=['Train','Date'],
                var_name = "Station",
                value_name="Delay"

            )
            ts_row_count+=len(df)
            time_series_files.append(df)
    print(f"[INFO] primary_row_count: {primary_row_count},ts_row_count: {ts_row_count}")

    if primary_files:
        pd.concat((pd.read_csv(f) for f in primary_files), ignore_index=True).to_csv(
            path_to_processed / "primary.csv", index=False
        )
    if time_series_files:
        pd.concat(
        time_series_files, ignore_index=True
        ).to_csv(path_to_processed / "time_series.csv", index=False)

        
def process_weather(raw_path: Path, processed_path: Path):
    weather_file = []
    for i in raw_path.rglob("*.csv"):
        if i.stem == "weather":
            weather_file.append(i)
    if weather_file:
        pd.concat((pd.read_csv(f) for f in weather_file),ignore_index=True
        ).to_csv(processed_path/"weather.csv",index=False) 

if __name__ == "__main__":
    path_to_raw = Path("data/raw/parsed_csv")
    path_to_raw_weather = Path("data/raw/weather")
    path_to_processed = Path("data/processed")
    
    process(path_to_raw, path_to_processed)
    process_weather(path_to_raw_weather,path_to_processed)