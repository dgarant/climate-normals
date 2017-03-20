# Web app to serve climate normals, historical weather, and weather forecasts
import sqlite3
import requests
import os
import sys
import json
import datetime, time
from contextlib import closing

import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler

import flask
from flask import render_template
from flask import Flask, g, abort, request
from flask_cache import Cache

app = Flask(__name__)
cache = Cache(app, config={"CACHE_TYPE" : "simple"})

def make_cache_key(*args, **kwargs): 
    return request.url

def connect_db():
    conn = sqlite3.connect("weather.s3db")
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'db'):
        g.db = connect_db()
    return g.db

def query_db(query, args=(), one=False):
    with closing(get_db().cursor()) as cur:
		cur.execute(query, args)
		r = [dict((cur.description[i][0], value) \
				   for i, value in enumerate(row)) for row in cur.fetchall()]
		return (r[0] if r else None) if one else r

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db'):
        g.db.close()

@app.route("/stations", methods=["GET"])
@cache.cached(timeout=3600, key_prefix=make_cache_key)
def stations():
	stations = query_db("select * from stations")
	return flask.jsonify(stations)

@app.route("/normals/<station_id>", methods=["GET"])
@cache.cached(timeout=3600, key_prefix=make_cache_key)
def climate_normals(station_id):
	normals = query_db("select * from normals where station_id = ?", (station_id, ))
	return flask.jsonify(normals)

@app.route('/', strict_slashes=False)
def root():
    return flask.send_from_directory(os.path.join('static', 'partials'), 'index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return flask.send_from_directory('static', path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
