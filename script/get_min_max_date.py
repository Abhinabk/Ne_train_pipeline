from pathlib import Path
import pandas as pd


def get_min_max_time(path_to_raw_csv: Path) -> dict:
    return_dict = {}
    for csv_file in path_to_raw_csv.rglob("*.csv"):
        if csv_file.stem == "time_series":
            df = pd.read_csv(csv_file)
            min_date = str(df["Date"].iloc[0])
            max_date = str(df["Date"].iloc[-1])
            train_no = str(df["Train"].iloc[0])
            return_dict[train_no] = [min_date, max_date]
    return return_dict
