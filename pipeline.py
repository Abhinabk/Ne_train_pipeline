from pathlib import Path
from script import scraper, parser, merge_to_processed,create_db
from api import get_weather_data as gwd
import time
import random
from datetime import datetime,date

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


    def build_weather(self):
        raw_csv_path = self.paths["raw_csv_path"]
        train_geo_location = self.paths["train_geo_location"]
        output_path = self.paths["api_data_path"]
        gwd.build_weather_dataset(
                raw_csv_path, 
                train_geo_location, 
                output_path
        )
        print("DONE \n")

    def build_processed(self):
        merge_to_processed.process(self.paths["raw_csv_path"],self.paths["processed_csv_path"])
        merge_to_processed.process_weather(self.paths["api_data_path"],self.paths["processed_csv_path"])
        print("DONE \n")

    def build_db(self):
        processed_ts_path = self.paths["processed_csv_path"]/"time_series.csv"
        if processed_ts_path.exists():
            print("Creating the databse ")
            create_db.create_database(self.paths["database_path"],processed_ts_path)
        else:
            print(f"[WARN] WRONG PATH {processed_ts_path}")
        

    def run(self, train_data, duration="1y"):
        print("------ FETCH ------")
        self.fetch(train_data, duration)
        print("------ PARSE ------")
        self.parse(train_data)
        print("------ WEATHER ------")
        self.build_weather()
        print("------ PROCESSED ------")
        self.build_processed()
        print("------ DATABASE------")
        self.build_db()