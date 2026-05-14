# TODO
1. ~~Add type hints to all files~~
2. ~~Add train_no as a primary column to all CSVs~~
3. ~~Clean up main.py~~
4.  I am check if diff betenn dates say 365 so 365 rows exits for a station code 
    and if less then trigger an api call but have if we do after 5 days now only 5 extra
    days but it will trigger an api call for enire 365 days for each staion wich is lost of wasted api calls sice we only nedd 5 days worth of new data so better approch will be to check for last date recorded in weather table for ech distinct station and only get the diff of data from last recorded date and date when api needs to be called  (son incremental lload insted of full refresh)
## MAJOR:
1. ~~Integrate weather API (evaluate: OpenWeather, Meteostat)~~
2. ~~Map timestamps → weather data~~
3. ~~Have to caonvert from wide to long format time_series.csv cant proceed further without it messing with concat~~
3. Do analysis on the weather file
4. Add a DAG engine and vizualizer


# DATA
1. The data in time_series.csv signifies delay in minutes 

# IMP
Now with station-level weather you have:
  stations×days
instead of:
  trains×days
So row growth becomes much larger.
Example:
9 trains * 365days ~ 3krows
216 stations×365 days ~ 78k rows
That’s why:
row count exploded
API load increased
rate limiting appeared
even though request count may still seem small