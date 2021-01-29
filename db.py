import requests, json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import sqlite3

def update_db(data):
    conn = sqlite3.connect('crypto.db')
    cursor = conn.cursor()

    # Constant DATA: (if we were to generalize, we would have a file for global variables defining these variables)
    # coin: ETH
    # coin_id: d85dce9b-5b73-5c3c-8978-522ce1d1c1b4
    # currency: CAD

    if not 'eth_data' in [x[0] for x in cursor.execute("SELECT name FROM sqlite_master where type='table'").fetchall()]:
        cursor.execute("""CREATE TABLE eth_data (
            timestamp INTEGER NOT NULL UNIQUE PRIMARY KEY,
            price REAL NOT NULL,
            hour REAL,
            day REAL,
            week REAL,
            month REAL,
            year REAL
        );""")

    prices = data['prices']
    latest_info = prices['latest_price']
    
    intervals = {
        #"all": prices['all'],
        "year": prices['year'],
        "month": prices['month'],
        "week": prices['week'],
        "hour": prices['hour'],
        "day": prices['day'],
    }

    # Insert Latest price
    timestamp = int(datetime.fromisoformat(prices['latest_price']['timestamp']).timestamp())
    latest_price = round(float(prices['latest']), 2)
    percent_change = [round(float(latest_info['percent_change'][x]), 4) for x in ['hour', 'day', 'week', 'month', 'year']]

    # To interpet date: use ... date(timestamp, 'unixepoch') ...
    # For local time: use ... date(timestamp, 'unixepoch', 'localtime') ...
    latest = (timestamp, latest_price, *percent_change)
    cursor.execute("INSERT INTO eth_data VALUES (?,?,?,?,?,?,?) ON CONFLICT(timestamp) DO NOTHING", latest)
    
    # Insert batch data
    for key, container in intervals.items():
        percent_change = container['percent_change']
        prices = container['prices']

        values = [(tp[1], round(float(tp[0]), 2), round(float(percent_change), 4)) for tp in prices]
        cursor.executemany(f"INSERT INTO eth_data (timestamp, price, {key})\
                                    VALUES (?, ?, ?)\
                               ON CONFLICT(timestamp) DO NOTHING", values)

    # Select the full data rows
    # select datetime(timestamp, 'unixepoch', 'localtime'), price, hour, day from eth_data where month is not null and year is not null;

    conn.commit()
    cursor.close()
    conn.close()

    return intervals
