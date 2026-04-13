from pathlib import Path
from script import scraper, parser, parse_raw_csv
from api import get_weather_data as gwd
import time


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
                print(f"{train_name}-{train_num}.html already present skipping ...")
                skipped_count += 1
                continue
            print(f"Fetching {train_name}-{train_num}...")

            # scraper call
            html = scraper.fetch(train_num, train_name, duration, raw_html_path)
            fetched_count += 1
            delay = random.uniform(2, 4)
            print(f"sleeping for {delay:.2f}s")
            time.sleep(delay)

        if fetched_count > 0:
            print(f"\nFetched {fetched_count} files.")
        if skipped_count > 0:
            print(f"Skipped {skipped_count} existing files.")
        if fetched_count == 0:
            print("\nNothing fetched (all files already exist).")

        return {"fetched": fetched_count, "skipped": skipped_count}

    def parse(self): ...

    def process_csv(self): ...

    def build_weather(self): ...

    def run(self, train_data, duration="1y"):
        self.fetch(train_data, duration)
        # self.parse()
        # self.process_csv()
        # self.build_weather()
