from pathlib import Path
import pandas as pd


def get_global_date_range(path_to_raw_csv: Path) -> tuple[str, str]:

    min_dates = []
    max_dates = []

    for csv_file in path_to_raw_csv.rglob("time_series.csv"):
        df = pd.read_csv(csv_file, usecols=["Date"])

        df["Date"] = pd.to_datetime(df["Date"])

        min_dates.append(df["Date"].min())
        max_dates.append(df["Date"].max())

    return (
        min(min_dates).date().isoformat(),
        max(max_dates).date().isoformat(),
    )
