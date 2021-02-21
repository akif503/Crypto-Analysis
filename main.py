# Notes: 
# 1. Time will be saved as UTC time (converting while viz)
# 2. The concurrent loop for data collection can be implemented with a better method using asynchronous methods.
# 3. The base_id of all the coins can be fetched from the first url of schema.py
# 4. The definition of interval might be misleading here; An example would clear it up:
#    If we are getting the price of a coin in interval=hour, then we mean the historical prices in the past hour

import requests, json, sys, time
import matplotlib.pyplot as plt
from math import ceil
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation
import matplotlib.dates as mdates
import matplotlib.text as mtext
from matplotlib.patches import Rectangle
import sqlite3
from threading import Thread

from db import update_db
from notify import send_mail

""" Things to do before running the program """
# Create the file individuals.json storing the following dictionary
# {
#   'from': '<receiver>'
#   'to': '<sender>'
# }
# Use the following script:
# import json
# with open("individuals.json", "w") as fp:
#   json.dump(<your_dictionary>, fp)

# When to notify
notifier_settings = {
    'upper_value_threshold': 2500,
    'lower_value_threshold': 1500,
    'hourly_percent_threshold': 0.01,
}
# Minimum wait time between mails is 30 mins
wait_time = 60 * 30


def main():

    if not (ret := fetch_and_update()):
        print("\n\nError occured while fetching the data.")
        return

    data, intervals = ret

    option = m[1] if len(m:=sys.argv) > 1 else ""
    option = option.lower()

    # For the continuous data collection options, call the notifier
    if option in ['--collect', '--live']:
        # We want the notifier to close with the program
        thread = Thread(target=notify, daemon=True)
        thread.start()

    # This option collects price data every minute and stores it into the database in perpetuity until interrupted by the user.
    if option == '--collect':
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(do_quit)

            while not future.done():
                _ = fetch_and_update()
                next_update_time = (datetime.now() + timedelta(minutes=1)).astimezone().strftime('%I:%M:%S %p')
                print(f"Next update in (1 minute): {next_update_time}")
                time.sleep(60)

    elif option == '--live':
        # Note: There is delay between when the graph updates between minutes
        # that is because coinbase takes a few seconds to update their latest value
        # so it will take 10 - 15 seconds more to update to the latest price
        # Update an existing graph every minute:
        fig = plt.figure(figsize=(12,6))
        ax = plt.subplot(111)
        # The text fields correlate to: latest_price, current_time, percent_change over the period respectively
        texts = [ax.text(0, 0, ""), ax.text(0, 0, ""), ax.text(0, 0, "")]

        conn = sqlite3.connect('crypto.db')
        cursor = conn.cursor()

        latest = cursor.execute('SELECT price from eth_data order by timestamp desc limit 1;').fetchone()[0]
        timestamps, prices = extract_last_hour_data(cursor)
        times = set_datetime_axis(ax, timestamps)

        line = plt.plot(times, prices, color='b')[0]

        update_axis(times, prices, ax, texts)

        anim = FuncAnimation(fig, animate, frames=1000, repeat=False, init_func=None, blit=False, interval = 10 * 1000, fargs=(cursor, line, ax, texts))

        Writer = animation.writers['ffmpeg']
        writer = Writer(fps=1, metadata=dict(artist='Akif'), bitrate=1800)

        #anim.save('data.mp4', writer=writer)
        
        #plt.tight_layout()
        plt.show()

    # This function visualizes the historical prices based on interval.
    elif option == '--viz':
        # Graph of the intervals
        plt.figure(figsize=(12, 6))
        # Use the second param to select between intervals: ['hour', 'day', 'week', 'month', 'year']
        plot_interval(intervals, ['hour', 'day'])
        plt.show()


def notify():
    conn = sqlite3.connect('crypto.db')
    cursor = conn.cursor()
    
    last_mail_time = None 

    while True:
        # Get the latest price:
        latest_price, percent_change = map(float, cursor.execute("SELECT price, hour from eth_data where hour not null order by timestamp desc limit 1;").fetchone())
        

        if can_send_a_mail(last_mail_time):
            if abs(percent_change * 100) >= notifier_settings['hourly_percent_threshold']:
                subject = f"ETH is {'rising' if percent_change > 0 else 'dropping'} fast"
                body = f"Current Stats - \n\t Price: {latest_price:.2f} CAD \n\t Percent Change: {'+' if percent_change > 0 else ''}{percent_change * 100:.2f} (last hour)"
                send_mail(subject, body)

                print(subject)
                print(body)

                last_mail_time = time.time()

        # Wait a minute
        time.sleep(60)


def can_send_a_mail(last_mail_time):
    """
    Check if the program can send a mail based on the minimum waiting time

    Parameters:
        - last_mail_time: seconds (float)
    """

    now = time.time()

    # If no mail has been sent so far or time difference is higher than the minimum
    return not last_mail_time or (now - last_mail_time >= wait_time)


def animate(frame, cursor, line, ax, texts):
    """
    The function for updating the figure per frame during animation

    # Parameters:
        - frame: nth frame (int)
        - cursor: cursor to db
        - line: the matplotlib.Line2d to update
        - ax: the matplotlib.Axes to update
        - texts: the matplotlib.Text fields to update
    """

    print(frame)
    # Update the db
    _ = fetch_and_update()

    # Get the price data of the last hour
    latest = cursor.execute('SELECT price from eth_data order by timestamp desc limit 1;').fetchone()[0]
    timestamps, prices = extract_last_hour_data(cursor)

    times = set_datetime_axis(ax, timestamps)
    line.set_data(times, prices)
    update_axis(times, prices, ax, texts)

    return line


def update_axis(times, prices, ax, texts):
    """
    Set the axes limit and ticks, and update the text fields

    Parameter:
        - times: x-ticks [check set_datetime_axis for more details]
        - prices: y-data 
        - ax: a matplotlib.Axes object 
        - texts: a list of matplotlib.Text
    """
    latest_price_text, current_time_text, percent_change_text = texts

    ax.set_ylim(min(prices) - 10, max(prices) + 10)
    ax.set_xticks(times[::5] + [times[-1]])
    ax.set_xlim(times[0], times[-1])

    # Update  latest price text
    latest_price_text.set(
        x = times[0],
        y = max(prices) + 10.5,
        text = f"Latest Price: {prices[-1]:.2f}",
        fontsize = 'xx-large'
    )

    # Update current time text
    current_time_text.set(
        x = times[-1],
        y = max(prices) + 10.5,
        text = f"Current Time: {times[-1]}",
        fontsize = 'xx-large'
    )

    # This gets the width and height of current_time_text in terms of data coordinates
    # FYI: In data coords, the x-axis is a real number line stretching from 0 to 59
    bb = ((m := current_time_text).get_window_extent(m.get_figure().canvas.get_renderer()).inverse_transformed(ax.transData))

    # Adjust the text box's x coord by shifting it to the left by its width 
    current_time_text.set(
        x = bb.x0 - (bb.width),
        transform=ax.transData
    )

    # Percent Change:
    percent_change = (((prices[-1] - prices[0]) / prices[0]) * 100)

    lp_bb = ((m := latest_price_text).get_window_extent(m.get_figure().canvas.get_renderer()).inverse_transformed(ax.transData))
    percent_change_text.set(
        x = lp_bb.x1+0.1,
        y = lp_bb.y1,
        text = f"{'-' if percent_change < 0 else '+'}{abs(percent_change):.2f}%",
        color = 'r' if percent_change < 0 else 'g',
        transform=ax.transData
    )


    # TODO: Draw candle sticks (OHLC charts)
    #select_color = lambda diff: 'r' if diff < 0 else 'g'
    """
    ax.add_patch(Rectangle(
        xy=(0, prices[0]),
        width=1,
        height=abs(m := (prices[1]-prices[0])),
        fc=select_color(m),
        transform=ax.transData
    ))
    """


def set_datetime_axis(ax, timestamps):
    """
    Formats the xaxis, and returns the ticks

    Parameters: 
        - ax: a single matplotlib.Axes object
        - timestamps: ...

    Returns:
        a list of strings of time data in the following format that can be uses as x-ticks
    """

    time_format = "%H:%M"
    times = []
    for timestamp in timestamps:
        time = datetime.fromtimestamp(timestamp)
        times.append(time.strftime(time_format))

    ax.xaxis.set_minor_formatter(mdates.DateFormatter(time_format))
    #_=plt.xticks(rotation=45) 

    return times

def strip_seconds(time):
    """
    Format a datetime object by stripping the seconds and return another datetime object

    Parameters: 
        - time: datetime object
    
    Returns:
        - a datetime object
    """

    return datetime.strptime(time.strftime(r'%y-%m-%d %H:%M'), r'%y-%m-%d %H:%M')


def extract_last_hour_data(cursor):
    """
    Get the price data of the last our

    Parameters:
        - cursor: cursor to the db
    
    Returns: (timestamps, prices) # the prices correspond to the timestamps parallely
    # the timestamps are in ascending order
    """

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

    # Divides the dictionary into parallel lists with timestamps sorted by ascending order
    return zip(*[(time, data[time]) for time in sorted(data.keys(), reverse=False)])


def fetch_and_update():
    """
    The function fetches the json file from the coinbase's endpoint:
        https://www.coinbase.com/api/v2/assets/prices/base_id?base=currency
        Here, 
            - base_id is an internal uuid specifying a certain crypto currency
            - base is the paper currency against which you want to know the price
    
    After fetching the data, it updates the db using the update_db() function, and
    Returns:
        - data<dict>: the data which has been fetched
        - intervals: the historical price of the crypto currency delimited by certain intervals;
                     this also include the latest price. 
        (Check the schema.py to understand how the data is organized)
                     
    """
    # The uuid in the url is the base_id of ETH
    r = requests.get('https://www.coinbase.com/api/v2/assets/prices/d85dce9b-5b73-5c3c-8978-522ce1d1c1b4?base=CAD')

    try:
        if r.status_code == 200:
            data = r.json() 
            data = data['data']

            # Update db
            intervals = update_db(data)
            print(f"Latest: {round(float(data['prices']['latest']), 2)}")

            return data, intervals
        
        else:
            print(r.json()['errors'][0]['message'])
    
    except:
        print("Couldn't fetch the data, check you internet connection.")

    return


def do_quit():
    """
    A function to run a concurrent loop to listen for "quitting" signal.
    """

    print("Enter Q<enter> to quit. You might have to wait a maximum of 1 minute before the program stops.")
    
    while (m := input().strip()) != 'Q':
        if m:
            print("\nIf you want to quit the program press Q<enter>!\n")
        continue

    print("Wait till the sleeping period ends. \nIt will end at the next update time (CHECK ABOVE).")


def plot_interval(intervals: dict, which_intervals: [str]) -> None:
    """
    Plots the historical price data based on given intervals.
    
    Parameters:
        - intervals: the historical price data delimited by all the intervals. 
        - which_intervals: the intervals on which you wanna see the data.
            Note: valid intervals are:
                ['hour', 'day', 'week', 'month', 'year']
    """

    # 1 -> 1 (row, col)
    # 2 -> 2 (rows) col 1
    # 3 -> 2 rows, 1: col 1, col 2

    # Types of intervals -> (rows, cols)
    # Index (starting from 1) is a row wise allocation
    # of indices: 1 <= index <= nrows * ncols
    def generate_subplot_pos(n):
        nrows = ceil(n / 2)
        ncols = 2 

        positions = [(nrows, ncols, idx) for idx in range(1, n + 1 if n % 2 == 0 else n)]

        if n % 2 == 1:
            # This will generate the subplot that spans
            # the entire width for odd number of subplots
            positions.append((nrows, 1, nrows))
        
        return positions
    
    mp = {
        1: [(1,1,1)],
        2: [(2,1,1), (2,1,2)],
        3: [(2,2,1), (2,2,2), (2,1,2)],
        4: [(2,2,1), (2,2,2), (2,2,3), (2,2,4)],
        5: [(3,2,1), (3,2,2), (3,2,3), (3,2,4), (3,1,3)]
    }
    
    #positions = generate_subplot_pos(len(which_intervals))
    positions = mp[len(which_intervals)]

    for idx, interval in enumerate(which_intervals):
        #interval = which_intervals[0]
        time_price_tuples = np.array(intervals[interval]['prices'], dtype=np.float32)

        prices = np.flip(time_price_tuples[:, 0])
        timestamps = np.flip(time_price_tuples[:, 1])

        ax = plt.subplot(*positions[idx])
        ax.plot(prices)
        print(datetime.fromtimestamp(float(timestamps[0])), datetime.fromtimestamp(float(timestamps[1])))
        ax.set_title(interval.capitalize())


main()