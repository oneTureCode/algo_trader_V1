# data_handler.py

import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time
import config
import os
import multiprocessing
import websocket
import json

# Initialize exchange connection
exchange = ccxt.mexc({
    'Key': config.APIS["MEXC"]["key"],
    'pass': config.APIS["MEXC"]["pass"],
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot'  # Ensures spot mode is active
    }
})

def test_connection():
    """
    Test the connection to the exchange by fetching its status.
    """
    try:
        status = exchange.fetch_status()
        print("Connection successful! Exchange status:")
        print(status)
        return True
    except Exception as e:
        print("Connection failed!")
        print(e)
        return False

def get_available_symbols():
    """
    Fetch available symbols from MEXC and save them to a CSV file.
    If the file already exists, it will be overwritten.
    Includes error handling for common issues.
    """
    try:
        print("Fetching available symbols from the exchange...")
        markets = exchange.load_markets()
        symbols = [market for market in markets if '/' in market]
        if not symbols:
            print("No trading pairs found. Exiting.")
            return

        symbols_df = pd.DataFrame(symbols, columns=["symbol"])
        if not os.path.exists('data_store'):
            os.makedirs('data_store')

        file_path = 'data_store/available_symbols.csv'
        symbols_df.to_csv(file_path, index=False)
        print(f"Available symbols successfully saved to '{file_path}'")

    except ccxt.NetworkError as e:
        print(f"Network error occurred while fetching symbols: {e}")
    except ccxt.ExchangeError as e:
        print(f"Exchange error occurred: {e}")
    except PermissionError as e:
        print(f"Permission error while trying to save the file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def fetch_historical_data(symbol, timeframe='15m', days=180):
    """
    Fetch historical OHLCV data from MEXC exchange for the past 'days'.
    """
    all_data = []
    since = exchange.parse8601((datetime.utcnow() - timedelta(days=days)).isoformat())

    while since < exchange.milliseconds():
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
            if not ohlcv:
                break
            all_data.extend(ohlcv)
            since = ohlcv[-1][0] + 1
            time.sleep(exchange.rateLimit / 1000)
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            break

    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def save_data_to_csv(df, symbol, timeframe):
    """
    Save the historical data to a CSV file in the data_store folder.
    """
    if not os.path.exists('data_store'):
        os.makedirs('data_store')

    filename = f"data_store/{symbol.replace('/', '_')}_{timeframe}.csv"
    df.to_csv(filename)
    print(f"Data for {symbol} with timeframe {timeframe} saved to {filename}")

def load_data(symbol, timeframe):
    """
    Load historical data from CSV files.
    """
    filename = f"data_store/{symbol.replace('/', '_')}_{timeframe}.csv"

    if os.path.exists(filename):
        print(f"Loading data from {filename}...")
        df = pd.read_csv(filename, index_col='timestamp', parse_dates=True)
        return df
    else:
        print(f"Data file for {symbol} on {timeframe} not found.")
        return None

def fetch_live_data(symbol):
    """
    Fetch live market data for a specific symbol using WebSockets.
    """
    def on_message(ws, message):
        try:
            data = json.loads(message)
            print(f"Live data for {symbol}: {data}")
        except Exception as e:
            print(f"Error processing live data for {symbol}: {e}")

    def on_error(ws, error):
        print(f"WebSocket error for {symbol}: {error}")

    def on_close(ws, close_status_code, close_msg):
        print(f"WebSocket closed for {symbol}: {close_msg}")

    def on_open(ws):
        print(f"WebSocket connection opened for {symbol}.")
        subscribe_message = {
            "method": "SUBSCRIBE",
            "params": [f"{symbol.lower()}@ticker"],
            "id": 1
        }
        ws.send(json.dumps(subscribe_message))

    ws_url = f"wss://wbs.mexc.com/ws"
    ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()

def start_live_data_stream(symbols):
    """
    Start live data streams for multiple symbols using multiprocessing.
    """
    processes = []
    for symbol in symbols:
        process = multiprocessing.Process(target=fetch_live_data, args=(symbol,))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

# Testing
if __name__ == "__main__":
    # Step 1: Test connection
    if not test_connection():
        exit()

    # Step 2: Get available symbols and save to CSV
    get_available_symbols()

    # Step 3: Fetch and save historical data for selected symbols
    timeframes = ["1d", "4h"]  # Correct variable name for clarity
    selected_symbols = [
        "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT","APT/USDT","TRX/USDT","TON/USDT"
    ]

    for symbol in selected_symbols:
        for timeframe in timeframes:  # Loop through each timeframe
            print(f"Fetching data for {symbol} with timeframe {timeframe}...")
            data = fetch_historical_data(symbol, timeframe=timeframe, days=180)
            if data is not None and not data.empty:
                save_data_to_csv(data, symbol, timeframe)

    # Step 4: Start live data streams
    #start_live_data_stream(selected_symbols)
