.headers on
.mode column
SELECT COUNT(*) as station_count FROM stations;
SELECT COUNT(*) as schedule_count FROM train_schedule;
SELECT * FROM stations WHERE station_code = 'FM';
SELECT train_name, station_name, arrival_time, departure_time, stop_number 
  FROM train_schedule WHERE train_number = '47154' ORDER BY stop_number LIMIT 5;
SELECT * FROM stations_fts WHERE stations_fts MATCH 'mumbai' LIMIT 5;
