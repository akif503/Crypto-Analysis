# Gets last hours data from the db

import sqlite3
from datetime import datetime
from pprint import pprint

def main():
    conn = sqlite3.connect('crypto.db')
    cursor = conn.cursor()

def strip_seconds(time):
    # time: datetime object
    # Returns: a stripped datetime object

    return datetime.strptime(time.strftime(r'%y-%m-%d %H:%M'), r'%y-%m-%d %H:%M')

def extract_last_hour_data(cursor):
    # cursor: the conn.cursor() to the db

    # Gets all the data from the last hour
    last_hour_data = cursor.execute(r"""select timestamp, datetime(timestamp, 'unixepoch', 'localtime'), price 
                                        from eth_data where timestamp >= (cast(strftime('%s', 'now') as int) - 60*60) 
                                        order by timestamp desc;""").fetchall()

    # Indexed by time
    data = {}

    for timestamp, localtime, price in last_hour_data:
        time = strip_seconds(datetime.fromtimestamp(timestamp)).timestamp()

        if data.get(time, False):
            continue

        data[time] = price 

    return data

def animate(frame, line, ax):
    _, intervals = fetch_and_update()

    price_tuples = np.array(intervals['hour']['prices'], dtype=np.float32)
    prices = np.flip(price_tuples[:, 0])
    timestamps = np.flip(price_tuples[:, 1])

    ax.add_line(line)

    ax.set_xlim(0, len(prices))
    ax.set_ylim(min(prices) - 10, max(prices) + 10)

    #print([datetime.fromtimestamp(t).strftime("%I:%M:%S %p") for t in np.asarray(timestamps, dtype=np.int64)])
    print([datetime.fromtimestamp(t).isoformat() for t in np.asarray(timestamps, dtype=np.int64)])
    print(prices)
    no_of_data_points = len(prices)
    line.set_data(range(no_of_data_points), prices)

    return line,
    #ax.set_title(interval.capitalize())

main()