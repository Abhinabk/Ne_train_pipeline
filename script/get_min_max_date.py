from pathlib import Path
import pandas as pd


def get_min_max_time(path_to_raw_csv: Path) -> dict:
    return_dict = {}
    for csv_file in path_to_raw_csv.rglob("time_series.csv"):
        if not csv_file.is_file():
            continue
        df = pd.read_csv(csv_file)
        df["Date"] = pd.to_datetime(df["Date"])#raw_csv date not processed yet so will compare string if not present
        
        min_date = str(df["Date"].min().date().isoformat())
        max_date = str(df["Date"].max().date().isoformat())
        train_no = str(df["Train"].iloc[0])
        return_dict[train_no] = [min_date, max_date]

    return return_dict

