from config import train_info
from script import scraper
import time
import random

if __name__ == "__main__":
    train_info = train_info.get_train_info("config/trains.json")
    duration = "1y"
    for train_num in train_info:
        print(f"Fetching {train_info[train_num]}...")
        html = scraper.fetch(train_num, train_info[train_num],duration)
        delay = random.uniform(2,4)
        print(f"sleeping for {delay:.2f}s")
        time.sleep(delay)

    if html:
        print("\n✅ Fetch completed successfully. Ready for parsing!")
