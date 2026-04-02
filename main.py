from config import train_info
from script import scraper, parser, parse_raw_csv
import time
import random
from pathlib import Path

if __name__ == "__main__":
    path = Path.cwd()
    raw_html_path = path / "data/raw_html"
    raw_csv_path = path / "data/raw_csv"
    train_config_path = path / "config/trains.json"
    parsed_csv_path = path / "data/parsed_csv"

    # create path if not exist
    raw_html_path.mkdir(parents=True, exist_ok=True)
    raw_csv_path.mkdir(parents=True, exist_ok=True)

    train_info = train_info.get_train_info(train_config_path)
    duration = "1y"
    fetched_flag = False

    for train_num, train_name in train_info.items():
        p = raw_html_path / f"{train_name}_{train_num}.html"
        if p.exists():
            print(f"{train_name}-{train_num}.html already present skipping ...")
            continue
        print(f"Fetching {train_name}-{train_num}...")

        # scraper call
        html = scraper.fetch(train_num, train_name, duration, raw_html_path)
        fetched_flag = True
        delay = random.uniform(2, 4)
        print(f"sleeping for {delay:.2f}s")
        time.sleep(delay)

    if fetched_flag:
        print("\n Fetch completed successfully. Ready for parsing!")
    else:
        print("\n nothing fetched (all files already exist)")

    # parser call
    parser.parser(raw_html_path, raw_csv_path)
    # fix column of primary.csv
    for train_dir in raw_csv_path.iterdir():
        if train_dir.is_dir():
            file = train_dir / "primary.csv"
            df = parse_raw_csv.process_primary(file, -1, "Avg Delay (in min)")
            if df is not None:
                train_parsed_path = parsed_csv_path / train_dir.stem
                train_parsed_path.mkdir(parents=True, exist_ok=True)
                output_file = train_parsed_path / "primary.csv"
                print(f"[INFO] Saving: {train_parsed_path}")
                df.to_csv(output_file, index=False)
            else:
                print(f"[WARN] Skipped: {file.name}")
