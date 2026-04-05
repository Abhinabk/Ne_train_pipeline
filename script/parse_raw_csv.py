# ingest the raw csv and fix if bad columns

from pathlib import Path
import pandas as pd
from pandas import DataFrame


def process_raw_csv(
    raw_csv_file: Path, new_col_name: str | None, col_pos: int | None
) -> DataFrame | None:

    if not raw_csv_file.exists():
        print(f"No such Path: {raw_csv_file}")
        return None

    try:
        df = pd.read_csv(raw_csv_file)

        if new_col_name is not None:
            col_pos = col_pos if col_pos is not None else -1

            if col_pos < -len(df.columns) or col_pos >= len(df.columns):
                print(f"[WARN] Invalid col pos {col_pos} ")
                return None

            old_name = df.columns[col_pos]
            df.rename(columns={old_name: new_col_name}, inplace=True)

        return df

    except Exception as e:
        print(f"[Error] failed to read {raw_csv_file}:{e}")
        return None
