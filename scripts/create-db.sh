
touch ../weather.s3db

sqlite3 ../weather.s3db 'create table stations (station_id integer primary key autoincrement, station_code varchar(50), zip varchar(20), city varchar(100), latitude real, longitude real);'
sqlite3 ../weather.s3db 'create table normals (normal_id integer primary key autoincrement, station_id int, month int, day int, snow_depth_inches_25pctl real, snow_depth_inches_50pctl real, snow_depth_inches_75pctl real, tempf_tavg_normal real, tempf_tavg_stddev real, tempf_tmax_normal real, tempf_tmax_stddev real, tempf_tmin_normal real, tempf_tmin_stddev real);'
sqlite3 ../weather.s3db 'create unique index normals_station_date on normals(station_id, month, day);'

