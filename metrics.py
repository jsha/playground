#!/usr/bin/env python
import datetime
import urllib2
import json
import sqlite3
import requests

s = requests.Session()
conn = sqlite3.connect("metrics.sqlite3")

def get_stat(version, date):
    r = requests.get('https://aggregates.telemetry.mozilla.org/aggregates_by/submission_date/channels/release/?version=%d&dates=%s&metric=HTTP_PAGELOAD_IS_SSL' % (
        version, date))
    # API consistently returns 404 for certain dates / versions.
    if r.status_code == 404:
        return None, None
    try:
        data = r.json()
    except ValueError:
        print r.text
        raise
    if data['data'] is not None and len(data['data']) > 0:
        entry = data['data'][0]
        return entry['histogram'][1], entry['histogram'][1] + entry['histogram'][0]
    else:
        return None, None

c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS pageload_is_ssl
            (date TEXT,
             version INTEGER,
             count INTEGER,
             sum INTEGER)''')

current_date = datetime.date.today()
for ago in range(0, 15):
    for version in range(42, 44):
        fetch_date = current_date + datetime.timedelta(-ago)
        formatted_date = fetch_date.strftime('%Y%m%d')
        count, sum = get_stat(version, formatted_date)
        if count == None:
            continue
        c.execute('''INSERT INTO pageload_is_ssl (date, version, count, sum) VALUES(?,?,?,?)''', (formatted_date, version, count, sum))
        print formatted_date, version, "%.2f%%" % (count * 100.0 / sum)
