#!/usr/bin/env python
import datetime
import urllib2
import json
import sqlite3
import requests

s = requests.Session()
conn = sqlite3.connect("metrics.sqlite3")

# HTTP_TRANSACTION_IS_SSL
# CERT_VALIDATION_SUCCESS_BY_CA
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
        return entry['histogram'][1], sum(entry['histogram'])
    else:
        return None, None

c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS pageload_is_ssl
            (date TEXT,
             version INTEGER,
             count INTEGER,
             sum INTEGER)''')
conn.commit()

def fetch():
    current_date = datetime.date.today()
    for ago in range(0, 365):
        for version in range(30, 44):
            fetch_date = current_date + datetime.timedelta(-ago)
            formatted_date = fetch_date.strftime('%Y%m%d')
            count, total = get_stat(version, formatted_date)
            if count == None:
                continue
            c.execute('''INSERT INTO pageload_is_ssl (date, version, count, sum) VALUES(?,?,?,?)''', (formatted_date, version, count, total))
    conn.commit()

def plot():
    c.execute('''
        select date, sum(count) * 100.0 / sum(sum) as percent from pageload_is_ssl group by date;
    ''')
    percents = []
    dates = []
    for (date, percent) in c.fetchall():
        percents.append(percent)
        if len(percents) < 28:
            continue
        print date, percents[14], sum(percents) / 28
        percents.pop(0)

#fetch()
plot()

conn.close()
