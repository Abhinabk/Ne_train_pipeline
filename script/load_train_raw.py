from pathlib import Path
import duckdb
#my method very slow
# def train_csv_to_db(path_to_train:Path,con:duckdb.DuckDBPyConnection):
#     for csv in path_to_train.rglob("*.csv"):
#         if csv.is_file():
#             df = pd.read_csv(csv)
#             #convert wide to long
#             df = (df
#                 .melt(id_vars = ['Train','Date'],var_name = "station_code",
#                     value_name = "delay_minutes")
#                 .rename(columns={
#                 "Train": "train_no",
#                 "Date": "date"})
#             )
#             df["date"] = pd.to_datetime(df["date"])
#             con.execute("""
#                 INSERT OR IGNORE INTO raw.train
#                 SELECT *, CURRENT_TIMESTAMP FROM df
#             """)



            

if __name__ == "__main__":

    path_to_db = Path("data/database/ne_pipeline.db")
    path_to_train=Path("data/raw/raw_csv")
    with duckdb.connect(str(path_to_db)) as con:
        train_csv_to_db(path_to_train,con)