#!/usr/bin/env python
import datetime
import urllib2
import json
import sqlite3
import requests

metric="PAGELOAD_IS_SSL"
s = requests.Session()
conn = sqlite3.connect("metrics.sqlite3")

# Also do:
# HTTP_TRANSACTION_IS_SSL
# CERT_VALIDATION_SUCCESS_BY_CA
def get_stat(version, date):
    # First try to read from DB.
    c.execute("SELECT count, sum FROM pageload_is_ssl WHERE version=? and date=?", (version, date))
    for (count, total) in c.fetchall():
        return count, total
    # Otherwise fetch from origin.
    print "fetch", version, date
    r = requests.get('https://aggregates.telemetry.mozilla.org/aggregates_by/submission_date/channels/release/?version=%d&dates=%s&metric=%s' % (
        version, date, metric))
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
        print entry
        count, total = entry['histogram'][1], sum(entry['histogram'])
        c.execute("INSERT INTO pageload_is_ssl (date, version, count, sum) VALUES(?,?,?,?)",
            (date, version, count, total))
        conn.commit()
        return count, total
    else:
        return None, None

c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS pageload_is_ssl
    (date TEXT NOT NULL,
     version INTEGER NOT NULL,
     count INTEGER,
     sum INTEGER,
     PRIMARY KEY (date, version))
""")
conn.commit()

def fetch():
    current_date = datetime.date.today()
    c.execute("select max(version) from pageload_is_ssl")
    max_version = c.fetchall()[0][0]
    for ago in range(0, 365):
        # Check all versions up to the highest one seen, plus one. This way we automatically
        # adapt to new versions.
        for version in range(39, max_version + 1):
            fetch_date = current_date + datetime.timedelta(-ago)
            formatted_date = fetch_date.strftime('%Y%m%d')
            count, total = get_stat(version, formatted_date)
    conn.commit()

def plot():
    c.execute("""
        select date, sum(count) * 100.0 / sum(sum) as percent from pageload_is_ssl
            where count is not null group by date;
    """)
    percents = []
    dates = []
    for (date, percent) in c.fetchall():
        percents.append(percent)
        if len(percents) < 28:
            continue
        print date, percents[14], sum(percents) / 28
        percents.pop(0)

fetch()
plot()

conn.close()
s.close()
