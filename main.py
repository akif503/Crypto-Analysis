# Notes: 
# 1. Time will be saved as UTC time (converting while viz)
# 2. The concurrent loop for data collection can be implemented with a better method using asynchronous methods.
# 3. The base_id of all the coins can be fetched from the first url of schema.py
# 4. The definition of interval might be misleading here; An example would clear it up:
#    If we are getting the price of a coin in interval=hour, then we mean the historical prices in the past hour

import requests, json, sys, time
import matplotlib.pyplot as plt
from math import ceil
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from db import update_db


def main():

    if not (ret := fetch_and_update()):
        print("\n\nError occured while fetching the data.")
        return

    data, intervals = ret

    option = m[1] if len(m:=sys.argv) > 1 else ""
    option = option.lower()

    # This option collects price data every minute and stores it into the database in perpetuity until interrupted by the user.
    if option == '--loop':
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(do_quit)

            while not future.done():
                _ = fetch_and_update()
                next_update_time = (datetime.now() + timedelta(minutes=1)).astimezone().strftime('%I:%M:%S %p')
                print(f"Next update in (1 minute): {next_update_time}")
                time.sleep(60)

    # This function visualizes the historical prices based on interval.
    elif option == '--viz':
        """
        Graph of the intervals
        """
        plt.figure(figsize=(16, 8))
        plot_interval(intervals, ['hour', 'day'])
        plt.show()
        

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
        price_vol_tuples = np.array(intervals[interval]['prices'], dtype=np.float32)

        #volume = price_vol_tuples[:, 1]
        prices = np.flip(price_vol_tuples[:, 0])

        ax = plt.subplot(*positions[idx])
        ax.plot(prices)
        ax.set_title(interval.capitalize())


main()