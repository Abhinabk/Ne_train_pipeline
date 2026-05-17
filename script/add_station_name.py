from bs4 import BeautifulSoup
import re 
from pathlib import Path 
import pandas as pd 

def extract_station_names_from_html(raw_html_path: Path,station_code_list:list) -> dict[str, str]:
    """Extract {station_code: station_name} from already-scraped HTML files"""
    code_to_name = {}
    station_code_set = set(station_code_list)
    pattern = re.compile(
        r"(.+?)\(([A-Z0-9]+)\)"
    )
    for html_file in raw_html_path.rglob("*.html"):
        soup = BeautifulSoup(html_file.read_text(), "html.parser")
        # matches "DIBRUGARH (DBRG)", "LUMDING JN (LMG)" etc
        for text in soup.stripped_strings:
            match = pattern.search(text)
            if match:
                name = match.group(1).strip().upper()
                code = match.group(2).strip()
                if code in station_code_set:
                  code_to_name[code] = name
    missing_codes = station_code_set - set(code_to_name.keys())

    for code in sorted(missing_codes):
      print(f"[WARN] Station name not found for {code}")
      
    return code_to_name

def add_to_station_coords(path_to_station_coord_csv:Path,raw_html_path)->None:
    df = pd.read_csv(path_to_station_coord_csv)
    station_code_list = df["station_code"].to_list()
    code_to_name = extract_station_names_from_html(raw_html_path,station_code_list)
    df["station_name"] = df["station_code"].map(code_to_name)
    missing = df[df["station_name"].isna()]

    if not missing.empty:
        print("[WARN] Missing station names:")
        print(missing["station_code"].to_list())

    df.to_csv(
        path_to_station_coord_csv,
        index=False
    )

        
if __name__ == "__main__":
    raw_html_path = Path("data/raw/raw_html")
    station_coordinates_path = Path("data/processed/station_coordinates.csv")
    add_to_station_coords(station_coordinates_path , raw_html_path)