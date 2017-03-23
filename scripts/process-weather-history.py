import argparse
import requests_cache
import requests
import csv
import json
import os
from collections import defaultdict
from time import strptime
import datetime
import calendar
import sys
from dateutil import parser as dparser
import sqlite3
import numpy as np

# to do: look into https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02/

requests_cache.install_cache("weather_cache")

def date_generator(from_date, to_date):
    while from_date <= to_date:
        yield from_date
        from_date = from_date + datetime.timedelta(days=1)

def load_weather(start_date, end_date, station, api_key):
    
    conn = sqlite3.connect("../weather.s3db")

    # remove existing history
    cur = conn.cursor()
    cur.execute("delete from history where station_id = ? and date >= ? and date <= ?",
        (station["station_id"], start_date, end_date))
    conn.commit()

    recs_since_commit = 0
    for cur_date in date_generator(start_date, end_date):
        print("Downloading data for {0}".format(cur_date.isoformat()))
        req_url = ("https://api.darksky.net/forecast/{0}/{1},{2},{3}?exclude=currently,minutely"
            .format(api_key, station["latitude"], station["longitude"], cur_date.isoformat()))
        resp = requests.get(req_url)
        full_response = resp.json()

        daily_data = full_response["daily"]["data"][0]
        hourly_data = full_response["hourly"]["data"]

        tempf_mean = np.mean([h["temperature"] for h in hourly_data])
        apparent_tempf_mean = np.mean([h["apparentTemperature"] for h in hourly_data])
        cur.execute("insert into history (station_id, date, tempf_min, tempf_mean, tempf_max, apparent_tempf_min, apparent_tempf_mean, apparent_tempf_max) values (?, ?, ?, ?, ?, ?, ?, ?)",
            (station["station_id"], cur_date,
                daily_data["temperatureMin"], tempf_mean, daily_data["temperatureMax"],
                daily_data["apparentTemperatureMin"], apparent_tempf_mean, daily_data["apparentTemperatureMax"]))

        recs_since_commit += 1
        if recs_since_commit >= 50:
            conn.commit()


    conn.commit()

def get_stations():

    # augment stations with latitude and longitude if not already present
    zip_to_latlon = dict()
    with open("../geocoded-zips.csv", "r") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            zip_to_latlon[row["ZIP"]] = row

    conn = sqlite3.connect("../weather.s3db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    stations = list(cur.execute("select * from stations"))
    stations_missing_geo = [dict(s) for s in stations 
        if s["latitude"] is None or s["longitude"] is None]
    for station in stations_missing_geo:
        geo_info = zip_to_latlon[station["zip"]]
        station["latitude"] = geo_info["LAT"]
        station["longitude"] = geo_info["LNG"]
        cur.execute("update stations set latitude = ?, longitude = ? where station_id = ?", 
            (geo_info["LAT"], geo_info["LNG"], station["station_id"]))
    conn.commit()
    conn.close()

    return stations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("start_date")
    parser.add_argument("end_date")
    args = parser.parse_args()

    api_key = os.environ["DARKSKY_API_KEY"]
    
    for station in get_stations():
        load_weather(dparser.parse(args.start_date), dparser.parse(args.end_date), station, api_key)

main()
