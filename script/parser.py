import json
import re

import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path


def run_extraction_helper(script: Path, var: str):
    temp = ""
    for s in script:
        text = s.get_text()
        if var in text:
            temp = text
            break
    return temp


def retrive_all_script_tags(content: str) -> list:
    """
    retrive the raw HTML file and extract the relevent script tag
    #IMP var to consider
    et.rsStat.primaryData -> gives the avg over a year
    et.rsStat.tooltipData -> gives day waise distribution over month
    stnname -> get tha sate name from acronyms
    """
    if not content:
        return None

    soup = BeautifulSoup(content, "html.parser")

    # paarse the script tags to find the data in et.rsStat.primaryData  and et.rsStat.tooltipData
    script = soup.find_all("script")  # will return a list of scripts
    return script


def extract_data_primary(script_path: Path) -> json:
    """Extracts  et.rsStat.primaryData from the script
    originally is in js object converts to json"""
    # NOTE Delay Average is in minutes the site rounds it

    primaryData = ""
    temp = run_extraction_helper(script_path, "primaryData")
    primaryData = re.search(r"et\.rsStat\.primaryData\s*=\s*(\[.*?\]);", temp)
    primary = primaryData.group(1)
    if not primary:
        return None
    primary = primary.replace("'", '"')
    return primary


def convert_to_csv_primary(json_data: dict, csv_path: Path) -> None:
    data = json.loads(json_data)
    # in list evry items are getting treated as rows had to manually give column names a sifrst row
    df = pd.DataFrame(data[1:], columns=data[0])
    # assuimng csv_path will always have train no at the end
    train_no = csv_path.stem
    df.insert(0, "Train", train_no)
    df.to_csv(f"{csv_path}/primary.csv", index=False)


def extract_data_time_series(script_path: Path) -> json:
    """Extracts  et.rsStat.tooltipData from the script
    originally is in js object converts to json"""

    temp = run_extraction_helper(script_path, "tooltipData")
    tooltipData = re.search(r"et\.rsStat\.tooltipData\s*=\s*(\[[^\;]*\])", temp)
    tooltip = tooltipData.group(1)
    if not tooltip:
        return None

    def fix_date(match):
        y, m, d = map(int, match.groups())
        return f'"{y}-{m + 1:02d}-{d:02d}"'  # fix month as js month stars at 0

    tooltip = re.sub(r"new Date\((\d+),(\d+),(\d+)\)", fix_date, tooltip)
    tooltip = tooltip.replace("'", '"')
    return tooltip


def convert_to_csv_time_series(json_data: dict, csv_path: Path) -> None:
    data = json.loads(json_data)
    header = data[0]
    # have to manually set the columns
    columns = ["Date"] + [col["label"] for col in header[1:]]
    df = pd.DataFrame(data[1:], columns=columns)
    train_no = csv_path.stem
    df.insert(0, "Train", train_no)
    df.to_csv(f"{csv_path}/time_series.csv", index=False)


def extract_state_name(script_path: Path) -> list[dict | None]:
    temp = run_extraction_helper(script_path, "stnname")
    stn_name_Data = re.search(r"stnname\s*=\s*(\{[\s\S]*?\})", temp)
    if not stn_name_Data:
        return None

    stn_name = stn_name_Data.group(1)
    stn_name = re.sub(r"(\w+)\s*:", lambda x: f'"{x.group(1)}":', stn_name)
    return stn_name


def convert_to_csv_state_name(json_data: dict, csv_path: Path) -> None:
    data = json.loads(json_data)
    df = pd.DataFrame(list(data.items()), columns=["code", "name"])
    train_no = csv_path.stem
    df.insert(0, "Train", train_no)
    df.to_csv(f"{csv_path}/state_name.csv", index=False)


def parser(html_file_path: Path, raw_csv_path: Path) -> None:

    for html_file in html_file_path.glob("*.html"):
        if not html_file.is_file():
            continue

        content = html_file.read_text()
        data = retrive_all_script_tags(content)

        train_no = html_file.stem.split("_")[-1]
        # make a train_no dir if not exist in /data

        train_dir = raw_csv_path / train_no
        if train_dir.exists():
            print(f"{train_dir} already exits")
            continue
        train_dir.mkdir(parents=True, exist_ok=True)

        primary = extract_data_primary(data)
        if primary:
            convert_to_csv_primary(primary, train_dir)
        else:
            print(f"[WARN] No state_name data for train {train_no}")

        time_series = extract_data_time_series(data)
        if time_series:
            convert_to_csv_time_series(time_series, train_dir)
        else:
            print(f"[WARN] No state_name data for train {train_no}")

        state_name = extract_state_name(data)
        if state_name:
            convert_to_csv_state_name(state_name, train_dir)
        else:
            print(f"[WARN] No state_name data for train {train_no}")
            print(f"Can make your own csv its just an expansion of state names")


if __name__ == "__main__":
    parser(Path("data/raw_html"))
