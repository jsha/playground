#!/usr/bin/env python
import plotly

import ConfigParser
import datetime
import json
import requests
import sqlite3
import datetime
import urllib2

s = requests.Session()
conn = sqlite3.connect("metrics.sqlite3")

# Also do:
# HTTP_TRANSACTION_IS_SSL
# CERT_VALIDATION_SUCCESS_BY_CA
def get_stat(version, date, metric):
    # First try to read from DB.
    c.execute("SELECT count, sum FROM metrics WHERE version=? and date=? and metric=?", (version, date, metric))
    for (count, total) in c.fetchall():
        return count, total
    # Otherwise fetch from origin.
    print "fetch", version, date
    r = requests.get('https://aggregates.telemetry.mozilla.org/aggregates_by/submission_date/channels/release/?version=%d&dates=%s&metric=%s' % (
        version, date, metric.upper()))
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
        c.execute("INSERT INTO metrics (date, version, metric, count, sum) VALUES(?,?,?,?,?)",
            (date, version, metric, count, total))
        conn.commit()
        return count, total
    else:
        return None, None

c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS metrics
    (date TEXT NOT NULL,
     version INTEGER NOT NULL,
     metric TEXT NOT NULL,
     count INTEGER,
     sum INTEGER,
     PRIMARY KEY (date, version, metric))
""")
conn.commit()

def fetch(metric):
    current_date = datetime.date.today()
    c.execute("select max(version) from metrics")
    max_version = c.fetchall()[0][0]
    if max_version is None:
        max_version = 44
    for ago in range(2, 250):
        # Check all versions up to the highest one seen, plus one. This way we automatically
        # adapt to new versions.
        for version in range(39, max_version + 1):
            fetch_date = current_date + datetime.timedelta(-ago)
            formatted_date = fetch_date.strftime('%Y%m%d')
            count, total = get_stat(version, formatted_date, metric)
    conn.commit()

def plot(metric):
    c.execute("""
        select date, sum(count) * 100.0 / sum(sum) as percent from metrics
            where count is not null and metric=? group by date;
    """, (metric,))
    percents = []
    dates = []
    percents_graph = plotly.graph_objs.Scatter(
        name='Daily',
        mode='markers',
        marker=dict(
            color="rgb(130, 130, 130)",
            size=3
        ),
        x=[], y=[])
    average_graph = plotly.graph_objs.Scatter(
        name='28-day centered moving average',
        line=dict(
            color="rgb(0, 0, 0)",
        ),
        x=[], y=[])
    results = c.fetchall()
    for i in range(0, len(results)):
        date = datetime.datetime.strptime(results[i][0], "%Y%m%d")
        percents_graph.x.append(date)
        percents_graph.y.append(results[i][1])
        if i <= 14 || i > len(results) - 14:
            continue
        average = sum([x[1] for x in results[i-14:i+13]]) / 28
        average_graph.x.append(date)
        average_graph.y.append(average)

    config = ConfigParser.ConfigParser()
    config.read(".config")
    plotly.session.sign_in(
      config.get("plotly", "user"),
      config.get("plotly", "apikey")
    )

    layout = plotly.graph_objs.Layout(
      title="Percentage of pageloads over HTTPS",
      yaxis=dict(rangemode='tozero')
    )

    try:
      #figure = plotly.graph_objs.Figure(data=percents_graph_obj, layout=layout)
      figure = plotly.graph_objs.Figure(data=[percents_graph, average_graph], layout=layout)
      plot_url = plotly.offline.plot(figure, filename='metrics.html')
      print(plot_url)
    except plotly.exceptions.PlotlyError as pe:
      print(pe)


fetch("http_pageload_is_ssl")
plot("http_pageload_is_ssl")

conn.close()
s.close()
