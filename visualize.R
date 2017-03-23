library(RSQLite)
library(ggplot2)
library(zoo)

con <- dbConnect(RSQLite::SQLite(fetch.default.rec=0), "~/repos/climate-normals/weather.s3db")
res <- dbSendQuery(con, "SELECT * FROM normals")
all.stats <- dbFetch(res, n=-1)
ggplot(subset(all.stats, station_id == 8), aes(x=as.Date(paste0("2016-", month, "-", day)), y=tempf_tavg_normal, 
  ymin=tempf_tavg_normal - 2 * tempf_tavg_stddev, ymax=tempf_tavg_normal + 2 * tempf_tavg_stddev)) + 
  geom_line(size=2) + geom_ribbon(alpha=0.1)
