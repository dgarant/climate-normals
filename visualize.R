library(RSQLite)
library(ggplot2)
library(zoo)
library(reshape2)

con <- dbConnect(RSQLite::SQLite(fetch.default.rec=0), "~/repos/climate-normals/weather.s3db")
res <- dbSendQuery(con, "select * from stations")
stations <- subset(dbFetch(res, n=-1),
                  #station_code %in% c("USC00190120"))
                  station_code %in% c("USC00190120", "USC00274399"))
dbClearResult(res)

res <- dbSendQuery(con, "SELECT * FROM normals")
normals <- dbFetch(res, n=-1)
dbClearResult(res)

res <- dbSendQuery(con, "select * from history")
history <- dbFetch(res, n=-1)
dbClearResult(res)
history$date <- as.Date(history$date)


dbDisconnect(con)

all.normals <- NULL
for(year in unique(format(history$date, "%Y"))) {
  normals$date <- as.Date(paste0(year, "-", normals$month, "-", normals$day))
  all.normals <- rbind(all.normals, normals)
}
merged <- merge(all.normals, history, by=c("station_id", "date"))
merged <- merge(merged, stations)

g <- ggplot(merged, aes(x=date, y=tempf_tavg_normal, 
  ymin=tempf_tavg_normal - 2 * tempf_tavg_stddev, ymax=tempf_tavg_normal + 2 * tempf_tavg_stddev)) + 
  geom_line(size=2) + geom_ribbon(alpha=0.1) + 
  geom_line(aes(y=tempf_mean), color="red") + facet_grid(city~.)
print(g)

g <- ggplot(subset(merged, date >= '2015-01-01'), aes(x=date, y=apparent_tempf_mean - tempf_mean)) + geom_smooth() + geom_point()
print(g)

# compare Keene and Amherst
station.compare <- dcast(merged, date ~ city, value.var="tempf_mean")
ggplot(station.compare, aes(x=date, y=Keene-Amherst)) + geom_line()
#plot(hist(merged$tempf_mean-merged$tempf_tavg_normal))
