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

requests_cache.install_cache("weather_cache")

def date_generator(from_date, to_date):
    while from_date <= to_date:
        yield from_date
        from_date = from_date + datetime.timedelta(days=1)

def get_weather(start_date, end_date, station, api_key):
    for cur_date in date_generator(start_date, end_date):
        print("Downloading data for {0}".format(cur_date.isoformat()))
        req_url = ("https://api.darksky.net/forecast/{0}/{1},{2},{3}?exclude=currently,minutely"
            .format(api_key, station["latitude"], station["longitude"], cur_date.isoformat()))
        resp = requests.get(req_url)
        full_response = resp.json()

        daily_data = full_response["daily"]["data"][0]
        print(full_response)

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
        get_weather(dparser.parse(args.start_date), dparser.parse(args.end_date), station, api_key)

main()
