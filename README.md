# TODO
1. ~~Add type hints to all files~~
2. ~~Add train_no as a primary column to all CSVs~~
3. Clean up main.py
## MAJOR:
1. ~~Integrate weather API (evaluate: OpenWeather, Meteostat)~~
2. ~~Map timestamps → weather data~~
3. Have to caonvert from wide to long format time_series.csv cant proceed further without it messing with concat
3. Do analysis on the weather file
4. Add a DAG engine and vizualizer


# DATA
1. The data in time_series.csv signifies delay in minutes 
2. The data in primary.csv signifies no of time delay happened where avg can be found by divding that number by no of non null rows which indicates total running for last year