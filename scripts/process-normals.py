import pandas as pd
import requests
import os
import sys
from io import StringIO
import sqlite3

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

def load_stations(stations):
    conn = sqlite3.connect("../weather.s3db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    station_code_to_id = dict()
    existing_station_codes = set()
    for existing_stations in cur.execute("select * from stations"):
        existing_station_codes.add(existing_stations["station_code"])
        station_code_to_id[existing_stations["station_code"]] = existing_stations["station_id"]

    for i, station_to_insert in stations[~stations["STNID"].isin(existing_station_codes)].iterrows():
        cur.execute("insert into stations (station_code, zip, city) values (?, ?, ?)",
            (station_to_insert["STNID"], station_to_insert["ZIP"], station_to_insert["POSTOFFICE"]))
        station_code_to_id[station_to_insert["STNID"]] = cur.lastrowid

    conn.commit()
    conn.close()

    return station_code_to_id

def load_statistics(stats_df, station_code_map):
    conn = sqlite3.connect("../weather.s3db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    existing_stats = set()
    for r in cur.execute("select * from normals"):
        existing_stats.add((r["station_id"], r["month"], r["day"]))

    for i, r in stats_df.iterrows():
        station_id = station_code_map[r["STNID"]]
        cur_key = (station_id, r["MONTH"], r["DAY"])
        if cur_key in existing_stats:
            continue

        cur.execute("""insert into normals 
                (station_id, month, day, 
                snow_depth_inches_25pctl, snow_depth_inches_50pctl, snow_depth_inches_75pctl, 
                 tempf_tavg_normal, tempf_tavg_stddev, 
                 tempf_tmax_normal, tempf_tmax_stddev, 
                 tempf_tmin_normal, tempf_tmin_stddev) 
                values (?, ?, ?, 
                        ?, ?, ?, 
                        ?, ?,
                        ?, ?,
                        ?, ?)""",
            (station_id, r["MONTH"], r["DAY"], 
            r["snow_depth_inches_25pctl"], r["snow_depth_inches_50pctl"], r["snow_depth_inches_75pctl"],
            r["tempf_tavg_normal"], r["tempf_tavg_stddev"], 
            r["tempf_tmax_normal"], r["tempf_tmax_stddev"], 
            r["tempf_tmin_normal"], r["tempf_tmin_stddev"]))

    conn.commit()
    conn.close()


def main():
    zips = set(["03431", "01002", "01342"])
    stations = retrieve_dataframe("station-inventories/zipcodes-normals-stations.txt", ["STNID", "ZIP", "POSTOFFICE"])
    keep_station_ids = stations["STNID"][stations["ZIP"].isin(zips)].values
    print("Keeping stations: {0}".format(",".join(keep_station_ids)))

    station_code_map = load_stations(stations[stations["STNID"].isin(keep_station_ids)])
    print(station_code_map)

    daily_cols = ["STNID", "MONTH"]
    for i in range(1, 32):
        daily_cols.append("DAY{0}".format(i))

    def process_daily_stats(df, name):
        long_stats = pd.melt(df, id_vars=["STNID", "MONTH"], var_name="DAY", value_name="VALUE")
        long_stats["DAY"] = long_stats["DAY"].str.replace("DAY", "").astype(int)
        long_stats = long_stats[~long_stats["VALUE"].isin(["-8888", "-9999"])]
        long_stats["VALUE"] = long_stats["VALUE"].map(lambda x: x.rstrip("CSQRP")).astype(int)
        long_stats["VALUE"][long_stats["VALUE"] == -6666] = 0
        long_stats["STATISTIC"] = name
        return long_stats

    frames = []
    for agg_type in ["tavg", "tmax", "tmin"]:
        for param_type in ["normal", "stddev"]:
            cur_temps = retrieve_dataframe("products/temperature/dly-{0}-{1}.txt".format(agg_type, param_type), 
                daily_cols, keep_station_ids)
            long_temps = process_daily_stats(cur_temps, "tempf_{0}_{1}".format(agg_type, param_type))
            long_temps["VALUE"] = long_temps["VALUE"] / 10.0 # converting from tenths to fractional degrees
            frames.append(long_temps)

    for stat in [25, 50, 75]:
        cur_snowd = retrieve_dataframe("products/precipitation/dly-snwd-{0}pctl.txt".format(stat),
            daily_cols, keep_station_ids)
        long_snowd = process_daily_stats(cur_snowd, "snow_depth_inches_{0}pctl".format(stat))
        frames.append(long_snowd)

    temp_stats = pd.concat(frames)
    temp_pivot = pd.pivot_table(temp_stats, "VALUE", ["STNID", "MONTH", "DAY"], ["STATISTIC"])
    temp_pivot = temp_pivot.reset_index()
    print(temp_pivot.head())

    load_statistics(temp_pivot, station_code_map)

main()
