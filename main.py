from config import train_info
from script import scraper,parser
import time
import random
from pathlib import Path

if __name__ == "__main__":
    path = Path.cwd()
    raw_html_path = path/"data/raw_html"
    raw_csv_path = path/"data/raw_csv"

    train_info = train_info.get_train_info("config/trains.json")
    duration = "1y"
    fetched_flag = False

    for train_num,train_name in train_info.items():

        p = raw_html_path/f"{train_name}_{train_num}.html"
        if p.exists():
            print(f"{train_name}_{train_num}.html already present skipping ...")
            continue
        print(f"Fetching {train_name}_{train_num}...")
        
        #scraper call
        html = scraper.fetch(train_num,train_name,duration,raw_html_path)
        fetched_flag = True             
        delay = random.uniform(2,4)
        print(f"sleeping for {delay:.2f}s")
        time.sleep(delay)

    if fetched_flag:
        print("\n Fetch completed successfully. Ready for parsing!")
    else:
        print("\n nothing fetched (all files already exist)")
    
    #parser call
    parser.parser(raw_html_path,raw_csv_path)
    