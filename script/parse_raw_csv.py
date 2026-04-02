#ingest the raw csv and fix if bad columns 

from pathlib import Path
import pandas as pd
from pandas import DataFrame

def process_primary(raw_csv_file:Path,pos:int,name:str)->DataFrame|None:
   #check if file exist
   if raw_csv_file.exists():
      print(f"Parsing raw file {raw_csv_file}")
      df = pd.read_csv(raw_csv_file)
      df.rename(columns={df.columns[pos]: name},inplace=True)
      return df

   else:
      print(f"No such Path: {raw_csv_file}")
      return None
   
       
       