from pathlib import Path
from script import scraper, parser, parse_raw_csv
from api import get_weather_data as gwd
import time
import random


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

    def parse(self):
        # parser call
        raw_html_path = self.paths["raw_html_path"]
        raw_csv_path = self.paths["raw_csv_path"]
        parsed_csv_path = self.paths["parsed_csv_path"]
        
        saved = 0
        skipped_exist_count = 0
        skipped_invalid_count = 0

        # 1.HTML->Raw csv
        parser.parser(raw_html_path, raw_csv_path)
        # fixing column of primary.csv but processing both files to /parsed_csv
        # 2 Raw csv -> Processed csv
        for train_dir in raw_csv_path.iterdir():
            if not train_dir.is_dir():
                continue

            file_primary = train_dir / "primary.csv"
            file_time_series = train_dir / "time_series.csv"

            df_primary = parse_raw_csv.process_raw_csv(
                file_primary, "Avg Delay (in min)", -1
            )
            df_time_series = parse_raw_csv.process_raw_csv(file_time_series, None, None)

            # making a path to store csv in each train no individually
            train_parsed_path = parsed_csv_path / train_dir.stem
            train_parsed_path.mkdir(parents=True, exist_ok=True)
            train_id = train_dir.stem
            # primary_csv
            output_primary = train_parsed_path / "primary.csv"
            if df_primary is not None:
                if output_primary.is_file():
                    #skips the csv
                    skipped_exist_count+=1
                    print(f"[SKIP] {train_id}/primary.csv already exists")
                else:
                    saved+=1
                    print(f"[INFO] Saving: {train_id}/primary.csv")
                    df_primary.to_csv(output_primary, index=False)
            else:
                #skips the invalid html
                skipped_invalid_count+=1
                print(f"[WARN] [{train_id}] Skipped: {file_primary.name}")

            # time_series_csv
            output_ts = train_parsed_path / "time_series.csv"
            if df_time_series is not None:
                if output_ts.is_file():
                    skipped_exist_count+=1
                    print(f"[SKIP] {train_id}/time_series.csv already exists")
                else:
                    saved+=1
                    print(f"[INFO] Saving: {train_id}/time_series.csv")
                    df_time_series.to_csv(output_ts, index=False)
            else:
                skipped_invalid_count+=1
                print(f"[WARN] [{train_id}] Skipped: {file_time_series.name}")

        print("\n[SUMMARY]")
        print(f"Saved: {saved}")
        print(f"Skipped (existing): {skipped_exist_count}")
        print(f"Skipped (invalid): {skipped_invalid_count}")

    # def process_csv(self): ...

    def build_weather(self):
        raw_csv_path = self.paths["parsed_csv_path"]
        train_geo_location = self.paths["train_geo_location"]
        output_path = self.paths["api_data_path"]
        gwd.build_weather_dataset(
                raw_csv_path, 
                train_geo_location, 
                output_path
        )

    def run(self, train_data, duration="1y"):
        print("------ FETCH ------")
        self.fetch(train_data, duration)
        print("------ PARSE ------")
        self.parse()
        # self.process_csv()
        print("------ WEATHER ------")
        self.build_weather()
