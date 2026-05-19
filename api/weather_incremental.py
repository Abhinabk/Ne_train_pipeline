import duckdb
import pandas as pd 
from pathlib import Path
from api.weather_backfill import fetch_weather_daily,flatten_weather_data
import requests


def stations_needing_update(con)->pd.DataFrame:
    stations_info = con.execute("""
        SELECT
            s.station_code,
            s.latitude,
            s.longitude,
            MIN(td.date) AS first_train_date,
            MAX(td.date) AS latest_train_date,
            MAX(w.date) AS latest_weather_date
                                
        FROM raw.stations_coordinates_raw s
        LEFT JOIN raw.train_delay_raw td
        ON s.station_code = td.station_code
        LEFT JOIN raw.weather_raw w
        ON s.station_code = w.station_code
        GROUP BY
            s.station_code,
            s.latitude,
            s.longitude
        """).fetchdf()

    stations_info["latest_weather_date"] = pd.to_datetime(stations_info["latest_weather_date"])
    stations_info["latest_train_date"] = pd.to_datetime(stations_info["latest_train_date"])
    return stations_info


def update_weather(con):
    df = stations_needing_update(con)
    need_to_fetch_again = set()
    updated_count = 0
    for row in df.itertuples():
        station_code = str(row.station_code)
        latest_weather = row.latest_weather_date
        latest_train = row.latest_train_date
        latitude = float(row.latitude) # type: ignore
        longitude = float(row.longitude) # type: ignore

        if pd.notna(latest_weather) and latest_weather >= latest_train: # type: ignore
            continue
        if pd.isna(latest_weather):
            start_date = str(row.first_train_date.date()) # type: ignore
        else:
            start_date = str((latest_weather - pd.Timedelta(days=2)).date()) # type: ignore

        #adds 1 day to last date
        end_date =str(latest_train.date()) # type: ignore
        print(f"[LOG] Running Incremental " f"{station_code} {start_date} -> {end_date}")
        try:
            data = fetch_weather_daily(station_code,latitude,longitude,start_date,end_date)
            rows = flatten_weather_data(data)
            if rows:
                #as duckdb expects a tuple/list but flatten_weather_data return list[dict]
                rows = [list(r.values()) for r in rows]
                con.executemany("""
                    INSERT OR IGNORE INTO raw.weather_raw
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
                """, rows)
                updated_count += 1
                print(f"[SUCCESS] {station_code}")
            else:
                print(f"[EMPTY] No rows returned for {station_code}")

        except requests.exceptions.HTTPError as e:
            if(e.response is not None and e.response.status_code == 429):
                print(f"[RATE LIMIT] {e}")
                print(f"[STOP] Resume later [{station_code}]")
                need_to_fetch_again.add(station_code)
                break
        except requests.exceptions.RequestException as e:
            print(f"[REQUEST ERROR] {station_code}: {e}")
            need_to_fetch_again.add(station_code)

    if updated_count == 0:
        print("[INFO] Weather already up to date")
    else:
        print(f"[UPDATED STATIONS] {updated_count}")
    if need_to_fetch_again:
        print("\n[FAILED STATIONS]")
        print(need_to_fetch_again)
        

if __name__ == "__main__":
    path_to_db = Path("data/database")
    with duckdb.connect(str(path_to_db / "ne_pipeline.db")) as con:
      
      update_weather(con)
        # print(stations_needing_update(con))

