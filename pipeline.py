from pathlib import Path
from script import scraper, parser, merge_to_processed,create_db,get_location,add_station_name,get_weather_info
from api import weather_backfill,weather_incremental,get_named_address
import time
import random
from datetime import datetime,date
import duckdb

class Pipeline:
    def __init__(self, paths: dict[str, Path]):
        self.paths = paths

    # make typehits specific to dict[train_no,train_name]
    def fetch(self, train_data: dict[str, str], duration) -> dict[str, int]:

        fetched_count = 0
        skipped_count = 0
        for train_num, train_name in train_data.items():
            safe_train_name = train_name.strip().replace(" ", "_")
            raw_html_path = (
                self.paths["raw_html_path"] / f"{safe_train_name}_{train_num}.html"
            )
            if raw_html_path.is_file():
                # get a proper logger here
                #raw_html_path.stat().st_mtime (seconds since Jan 1, 1970)
                fetched_date = datetime.fromtimestamp(raw_html_path.stat().st_mtime).date()
                if fetched_date == date.today():
                    print(f"[SKIP] {train_name}-{train_num}.html already present")
                    skipped_count += 1
                    continue

            print(f"Fetching {train_name}-{train_num}...")
            # scraper call
            try:
                scraper.fetch(train_num, train_name, duration, raw_html_path)
                fetched_count += 1
                delay = random.uniform(2, 4)
                print(f"sleeping for {delay:.2f}s")
                time.sleep(delay)
            except Exception:
                continue
        print("[SUMMARY]")
        print(f"Skipped: {skipped_count}")
        print(f"Fetched: {fetched_count}")
     
        return {"fetched": fetched_count, "skipped": skipped_count}

    def parse(self,train_data: dict[str, str]):
        # parser call
        raw_html_path = self.paths["raw_html_path"]
        raw_csv_path = self.paths["raw_csv_path"]

        need_parsing = 0
        skipped_count = 0
        # 1.HTML->Raw csv
        for train_num, _ in train_data.items():
            raw_csv_file = self.paths["raw_csv_path"] / f"{train_num}"/ "time_series.csv"
            if not raw_csv_file.exists():
                need_parsing+=1
                continue

            fetched_date = datetime.fromtimestamp(raw_csv_file.stat().st_mtime).date()

            if fetched_date == date.today():
                skipped_count+=1
            else:
                need_parsing+=1

        if need_parsing == 0:
            print("\n[SUMMARY]")
            print("[SKIP] All trains already parsed today")
            print("Saved: 0")
            print(f"Skipped: {skipped_count}")
            return
        
        print(f"[PARSING] Rebuilding {need_parsing} train(s)")
        parser.parser(raw_html_path, raw_csv_path)

        print("\n[SUMMARY]")
        print(f"Saved: {need_parsing}")
        print(f"Skipped: {skipped_count}")

    def build_station_coords(self):
        path_to_station_coord_csv = self.paths["path_to_station_coord_csv"]

        get_location.get_longitude_latitude(self.paths["raw_csv_path"],
                                            self.paths["train_geo_location_json"],
                                            self.paths["processed_path"])
        if not path_to_station_coord_csv.exists():
            print(f"[WARN] no such file {path_to_station_coord_csv}")
            return
        
        add_station_name.add_to_station_coords(path_to_station_coord_csv,
                                            self.paths["raw_html_path"])
    def build_weather(self):
        raw_csv_path = self.paths["raw_csv_path"]
        station_coordinates_path= self.paths["path_to_station_coord_csv"]
        output_path = self.paths["raw_csv_weather_path"]
        path_to_db = self.paths['database_path']
        with duckdb.connect(str(path_to_db / "ne_pipeline.db")) as con:

            if get_weather_info.table_has_data(con,"weather"):
                print("[WEATHER] Running incremental update")
                weather_incremental.update_weather(con)       
            else:
                print("[WEATHER] Running backfill")
                weather_backfill.build_weather_dataset(
                    raw_csv_path,
                    station_coordinates_path,
                    con
                )
        print("DONE\n")
    
    def build_processed(self):
        merge_to_processed.process(self.paths["raw_csv_path"],self.paths["processed_path"])
        merge_to_processed.process_weather(self.paths["api_data_path"],self.paths["processed_path"])
        print("DONE \n")

    def build_station_address(self):
        path_to_address_csv = self.paths["path_to_address_csv"]

        if path_to_address_csv.exists():
            fetched_date = datetime.fromtimestamp(path_to_address_csv.stat().st_mtime).date()
            if fetched_date == date.today():
                print("[SKIP] address.csv already exists")
                return
        get_named_address.get_address(
            self.paths["path_to_station_coord_csv"],
            self.paths["processed_path"]
        )
        print(f"[LOG] saved to {path_to_address_csv}\n")

    def build_db(self):
        path_to_db = self.paths['database_path']
        with duckdb.connect(str(path_to_db / "ne_pipeline.db")) as con:
            print("Creating the database")
            create_db.create_database(self.paths["database_path"],
                    self.paths['path_to_train_csv'],self.paths['path_to_weather_csv'],
                    self.paths["raw_csv_path"],
                    self.paths["path_to_address_csv"],
                    self.paths["path_to_station_coord_csv"],
                    con
                    )
        
    def run(self, train_data, duration="1y"):
        print("------ FETCH ------")
        self.fetch(train_data, duration)
        print("------ PARSE ------")
        self.parse(train_data)
        print("------ COORDINATES ------")
        self.build_station_coords()
        print("------ COORDINATES TO ADDRESS ------")
        self.build_station_address()
        print("------ WEATHER ------")
        self.build_weather()
        print("------ PROCESSED ------")
        self.build_processed()
        print("------ DATABASE------")
        self.build_db()
        
        
