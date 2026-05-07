import json
import re

import pandas as pd
from bs4 import BeautifulSoup, Tag
from pathlib import Path
from typing import List


def run_extraction_helper(script: List[Tag], var: str) -> str:
    temp = ""
    for s in script:
        text = s.get_text()
        if var in text:
            temp = text
            break
    return temp


def retrive_all_script_tags(content: str) -> List[Tag] | None:
    """
    retrive the raw HTML file and extract the relevent script tag
    #IMP var to consider
    et.rsStat.tooltipData -> gives day waise distribution over month
    stnname -> get tha sate name from acronyms
    """
    if not content:
        return None

    soup = BeautifulSoup(content, "html.parser")

    # paarse the script tags to find the data in  et.rsStat.tooltipData
    script = soup.find_all("script")  # will return a list of scripts
    return script




def extract_data_time_series(script_path: List[Tag]) -> str | None:
    """Extracts  et.rsStat.tooltipData from the script
    originally is in js object converts to json"""

    temp = run_extraction_helper(script_path, "tooltipData")
    tooltipData = re.search(r"et\.rsStat\.tooltipData\s*=\s*(\[[\s\S]*?\]);", temp)
    if not tooltipData:
        return None

    tooltip = tooltipData.group(1)

    def fix_date(match):
        y, m, d = map(int, match.groups())
        return f'"{y}-{m + 1:02d}-{d:02d}"'  # fix month as js month stars at 0

    tooltip = re.sub(r"new Date\((\d+),(\d+),(\d+)\)", fix_date, tooltip)
    tooltip = tooltip.replace("'", '"')
    return tooltip


def convert_to_csv_time_series(json_data: str, csv_path: Path) -> None:
    data = json.loads(json_data)
    header = data[0]
    # have to manually set the columns
    columns = ["Date"] + [col["label"] for col in header[1:]]
    df = pd.DataFrame(data[1:], columns=columns)
    train_no = csv_path.stem
    df.insert(0, "Train", train_no)
    df.to_csv(f"{csv_path}/time_series.csv", index=False)


def parser(html_file_path: Path, raw_csv_path: Path) -> None:

    for html_file in html_file_path.glob("*.html"):
        if not html_file.is_file():
            continue

        content = html_file.read_text()
        scripts = retrive_all_script_tags(content)
        if scripts is None:
            continue
        train_no = html_file.stem.split("_")[-1]
        # make a train_no dir if not exist in /data

        train_dir = raw_csv_path / train_no
       
        train_dir.mkdir(parents=True, exist_ok=True)

        time_series = extract_data_time_series(scripts)
        if time_series:
            convert_to_csv_time_series(time_series, train_dir)
        else:
            print(f"[WARN] No state_name data for train {train_no}")
