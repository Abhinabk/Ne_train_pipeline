import json
import re

import pandas as pd
from bs4 import BeautifulSoup

def run_extraction_helper(script,phrase):
    temp = ""
    for s in script:
        text = s.get_text()
        if str(phrase) in text:
            temp = text
            break  
    return temp  

def parse_train_history(content):
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


def extract_data_primary(script):
    """Extracts  et.rsStat.primaryData from the script
    originally is in js object converts to json"""
    # NOTE Delay Average is in minutes the site rounds it

    primaryData = ""
    temp = run_extraction_helper(script,"primaryData")
    primaryData = re.search(r"et\.rsStat\.primaryData\s*=\s*(\[.*?\]);", temp)
    primary = primaryData.group(1)
    primary = primary.replace("'", '"')
    return primary


def convert_to_csv_primary(json_data, filename="give_name"):
    data = json.loads(json_data)
    # list evry items are getting treated as rows had to manually give column names a sifrst row
    df = pd.DataFrame(data[1:], columns=data[0])
    df.to_csv(f"data/final/{filename}.csv", index=False)
    return df


def extract_data_time_series(script):
    """Extracts  et.rsStat.tooltipData from the script
    originally is in js object converts to json"""

    temp = run_extraction_helper(script,"tooltipData")
    tooltipData = re.search(r"et\.rsStat\.tooltipData\s*=\s*(\[[^\;]*\])", temp)
    tooltip = tooltipData.group(1)

    def fix_date(match):
        y, m, d = map(int, match.groups())
        return f'"{y}-{m + 1:02d}-{d:02d}"'  # fix month as js month stars at 0

    tooltip = re.sub(r"new Date\((\d+),(\d+),(\d+)\)", fix_date, tooltip)
    tooltip = tooltip.replace("'", '"')
    return tooltip


def convert_to_csv_time_series(json_data, filename="give_name"):
    data = json.loads(json_data)
    header = data[0]
    # have to manually set the columns
    columns = ["Date"] + [col["label"] for col in header[1:]]
    df = pd.DataFrame(data[1:], columns=columns)
    df.to_csv(f"data/final/{filename}.csv", index=False)
    return df


def extract_state_name(script):
    temp = run_extraction_helper(script,"stnname")
    stn_name_Data = re.search(r"stnname\s*=\s*(\{[\s\S]*?\})", temp)
    stn_name = stn_name_Data.group(1)
    stn_name = re.sub(r"(\w+)\s*:",lambda x: f'"{x.group(1)}":',stn_name)
    return stn_name


def convert_to_csv_state_name(json_data, filename="give_name"):
    data = json.loads(json_data)
    df = pd.DataFrame(list(data.items()),columns=["code", "name"])
    df.to_csv(f"data/final/{filename}.csv", index=False)
    return df
    # df = pd.DataFrame(data)
    # df.to_csv(f"data/final/{filename}.csv", index=False)
    # return df


if __name__ == "__main__":
    try:
        with open("data/raw/etrain_raw_12423.html", "r", encoding="utf-8") as f:
            content = f.read()
            data = parse_train_history(content)

    except FileNotFoundError:
        print("The file was not found.")
        exit()

    primary = extract_data_primary(data)
    df_primary = convert_to_csv_primary(primary, "primary")

    time_series = extract_data_time_series(data)
    df_time_series = convert_to_csv_time_series(time_series, "time_series")

    state_name = extract_state_name(data)
    df_sate_name = convert_to_csv_state_name(state_name, "state_names")
