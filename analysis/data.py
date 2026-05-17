from pathlib import Path
import streamlit as st
import duckdb 

db_path = Path(__file__).parent.parent / "data" / "database" / "ne_pipeline.db"

@st.cache_resource
def get_connection():
	return duckdb.connect(str(db_path))

@st.cache_data
def get_overview_data():
	con = get_connection()
	data = con.execute("""
	SELECT
		COUNT(*) AS total_records,
		COUNT(DISTINCT train_no) AS total_trains,
		COUNT(DISTINCT station_code) AS total_stations,
		ROUND(AVG(delay_minutes),1) AS avg_delay,
		MIN(date) AS min_date,
		MAX(date) AS max_date
	FROM merged_view        
	""").fetchone()
	return data

@st.cache_data
def get_delay_data():
	con = get_connection()
	delay_df = con.execute("""
	SELECT 
		delay_minutes
	FROM merged_view
	WHERE delay_minutes IS NOT NULL AND delay_minutes BETWEEN 10 AND 500
	""").fetchdf()
	return delay_df

@st.cache_data
def get_train_delay_data():
	con = get_connection()
	train_data = con.execute("""
		SELECT 
			train_no,
			ROUND(AVG(delay_minutes),1) AS avg_delay,
			ROUND(MEDIAN(delay_minutes), 2) AS median_delay,
			MAX(delay_minutes) as worst_delay
		FROM merged_view
		group by train_no 
	""").fetchdf()
	return train_data
@st.cache_data
def get_station_delay_data():
	con = get_connection()
	station_data = con.execute("""
		SELECT 
			station_code,
			longitude,
			latitude,						
			ROUND(AVG(delay_minutes),1) AS avg_delay,
			ROUND(MEDIAN(delay_minutes), 2) AS median_delay,
			MAX(delay_minutes) as worst_delay
		FROM merged_view
		group by station_code,longitude,latitude
	""").fetchdf()
	return station_data

@st.cache_data
def get_season_delay_data():
	con = get_connection()
	season_data = con.execute("""
	SELECT 
		CASE 
			WHEN MONTH(date) IN (12,1,2) THEN 'Winter'
			WHEN MONTH(date) IN (3,4,5)  THEN 'Pre-Monsoon'
			WHEN MONTH(date) IN (6,7,8,9) THEN 'Monsoon'
			WHEN MONTH(date) IN (10,11)  THEN 'Post-Monsoon'
		END as season,
		ROUND(AVG(delay_minutes),2) as avg_delay,
		COUNT(*) as total_runs
	FROM merged_view
	GROUP BY season
	ORDER BY avg_delay DESC""").fetchdf()
	return season_data
@st.cache_data
def get_temporal_delay_data():
	con = get_connection()
	temporal_data = con.sql("""
	SELECT
		MONTHNAME(date) AS month,
		DAYNAME(date) AS weekday,
		ROUND(AVG(delay_minutes), 2) AS avg_delay
	FROM merged_view
	GROUP BY month, weekday
	""").fetchdf()
	return temporal_data

@st.cache_data
def get_weather_data():
	con = get_connection()
	weather_data = con.execute('''
	SELECT
		delay_minutes,
		station_code,
		train_no,
		temperature_2m_mean,
		precipitation_sum,
		rain_sum,
		wind_speed_10m_max,
		relative_humidity_2m_mean,
	FROM merged_view
	''').fetchdf()

	return weather_data


