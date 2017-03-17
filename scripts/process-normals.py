import pandas as pd
import requests
import os
import sys
from io import StringIO

def retrieve_dataframe(path, col_names, filter_stations=None):
    basepath = os.path.basename(path)
    if not os.path.exists(basepath):
        print("downloading {0}".format(path))
        resp = requests.get("https://www1.ncdc.noaa.gov/pub/data/normals/1981-2010/{0}".format(path))
        resp.raise_for_status()
        result = pd.read_csv(StringIO(resp.text), sep=r"\s+", names=col_names, dtype={"ZIP" : str})
        if not filter_stations is None:
            result = result[result["STNID"].isin(filter_stations)]
        result.to_csv(basepath, index=False)
        return result
    else:
        print("reading {0}".format(basepath))
        result = pd.read_csv(basepath, sep=",", dtype={"ZIP" : str})
        return result

zips = set(["03431", "01002", "01342"])
stations = retrieve_dataframe("station-inventories/zipcodes-normals-stations.txt", ["STNID", "ZIP", "POSTOFFICE"])
keep_station_ids = stations["STNID"][stations["ZIP"].isin(zips)].values
print(keep_station_ids)

daily_cols = ["STNID", "MONTH"]
for i in range(1, 32):
    daily_cols.append("DAY{0}".format(i))

frames = []
for agg_type in ["tavg", "tmax", "tmin"]:
    for param_type in ["normal", "stddev"]:
        cur_temps = retrieve_dataframe("products/temperature/dly-{0}-{1}.txt".format(agg_type, param_type), 
            daily_cols, keep_station_ids)
        print(cur_temps)
        long_temps = pd.melt(cur_temps, id_vars=["STNID", "MONTH"], var_name="DAY", value_name="VALUE")
        long_temps["DAY"] = long_temps["DAY"].str.replace("DAY", "").astype(int)
        long_temps = long_temps[long_temps["VALUE"] != "-8888"]
        long_temps["STATISTIC"] = "{0}_{1}".format(agg_type, param_type)
        
        long_temps["VALUE"] = long_temps["VALUE"].map(lambda x: x.rstrip("CSQRP")).astype(int)

        frames.append(long_temps)

temp_stats = pd.concat(frames)
temp_pivot = pd.pivot_table(temp_stats, "VALUE", ["STNID", "MONTH", "DAY"], ["STATISTIC"])
temp_pivot = temp_pivot.reset_index()
print(temp_pivot)



