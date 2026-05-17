import duckdb
import pandas as pd 
from pathlib import Path
from api.weather_backfill import fetch_weather_daily,flatten_weather_data
import requests


def stations_needing_update(con)->pd.DataFrame:
    target_date = con.execute("""
        SELECT MAX(date)
        FROM train_delay
    """).fetchone()[0]
    target_date = pd.to_datetime(target_date)

    stations_info = con.execute("""
    SELECT
        s.station_code,
        s.latitude,
        s.longitude,
        MAX(w.date) AS last_date
    FROM stations_coordinates s
    LEFT JOIN weather w
    ON s.station_code = w.station_code
    GROUP BY
        s.station_code,
        s.latitude,
        s.longitude
    """).fetch_df()
    stations_info["last_date"] = pd.to_datetime(stations_info["last_date"])
    #fillna will make na to be 9999 so will have to fetch this (if corrupted data present)
    stations_info["missing_days"] = (target_date - stations_info["last_date"]).dt.days.fillna(9999).astype(int)
    stations_info["target_date"] = target_date
    return stations_info


def update_weather(con):
    df = stations_needing_update(con)
    need_to_fetch_again = set()
    updated_count = 0
    for row in df.itertuples():
        station_code = str(row.station_code)
        missing_days = int(row.missing_days) # type: ignore
        latitude = float(row.latitude) # type: ignore
        longitude = float(row.longitude) # type: ignore
        if missing_days <= 0:
            continue
        #adds 1 day to last date
        if pd.isna(row.last_date):
            start_date = con.execute("""
                SELECT
                    MIN(date)
                FROM train_delay
                WHERE station = ?
            """, [station_code]).fetchone()[0]
            start_date = str(start_date)

        else:
            start_date = str((row.last_date + pd.Timedelta(days=1)).date()) # type: ignore
        end_date = str(row.target_date.date()) # type: ignore
        print(f"[LOG] Running Incremental " 
              f"{station_code} {start_date} -> {end_date}")
        try:
            data = fetch_weather_daily(station_code,latitude,longitude,start_date,end_date)
            rows = flatten_weather_data(data)
            updated_count += 1
            if rows:
                #as duckdb expects a tuple/list but flatten_weather_data return list[dict]
                rows = [list(r.values()) for r in rows]
                con.executemany("""
                    INSERT OR IGNORE INTO weather
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, rows)
            print(f"[SUCCESS] {station_code}")

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
    if need_to_fetch_again:
        print("\n[FAILED STATIONS]")
        print(need_to_fetch_again)
        

if __name__ == "__main__":
    path_to_db = Path("data/database")
    with duckdb.connect(str(path_to_db / "ne_pipeline.db")) as con:
      
      update_weather(con)
        # print(stations_needing_update(con))

