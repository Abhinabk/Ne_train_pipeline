import duckdb 

with duckdb.connect('data/database/ne_pipeline.db') as con:
  con.execute("""
  CREATE OR REPLACE VIEW merged_view AS
  SELECT
      td.train_no,
      td.date,
      td.station as station_code,
      td.delay_minutes,

      sc.latitude,
      sc.longitude,

      sa.state,
      sa.district,
      sa.country,

      w.temperature_2m_max,
      w.temperature_2m_min,
      w.temperature_2m_mean,
      w.precipitation_sum,
      w.rain_sum,
      w.wind_speed_10m_max,
      w.wind_gusts_10m_max,
      w.relative_humidity_2m_mean,
      w.weather_code

  FROM train_delay td

  LEFT JOIN weather w
      ON td.station = w.station_code
      AND td.date = w.date

  LEFT JOIN stations_coordinates sc
      ON td.station = sc.station_code

  LEFT JOIN station_address sa
      ON td.station = sa.station_code

  """)

  con.sql("""
  SELECT * FROM merged_view
""").show()