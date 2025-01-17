# data_handler.py

import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time
import config
import os

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
        # Fetch markets from the exchange
        print("Fetching available symbols from the exchange...")
        markets = exchange.load_markets()
        
        # Extract trading pairs with '/'
        symbols = [market for market in markets if '/' in market]
        if not symbols:
            print("No trading pairs found. Exiting.")
            return
        
        # Create a DataFrame of symbols
        symbols_df = pd.DataFrame(symbols, columns=["symbol"])
        
        # Ensure the data_store directory exists
        if not os.path.exists('data_store'):
            os.makedirs('data_store')
        
        # Save to CSV (overwriting if the file exists)
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


def filter_symbols_from_csv(
    csv_file='data_store/available_symbols.csv', 
    base_currency="USDT", 
    min_volume=100000, 
    active_only=True, 
    min_price=0.1, 
    max_price=1000000
):
    """
    Filter symbols based on flexible criteria such as base currency, minimum volume, and price range,
    reading from a CSV file instead of querying the exchange.
    """
    if not os.path.exists(csv_file):
        print(f"CSV file '{csv_file}' not found.")
        return []

    try:
        # Load the CSV file
        symbols_df = pd.read_csv(csv_file)
        if 'symbol' not in symbols_df.columns:
            print("CSV file does not contain a 'symbol' column.")
            return []

        available_symbols = symbols_df['symbol'].tolist()
        print(f"Loaded {len(available_symbols)} symbols from CSV.")

        # Fetch market details from the exchange
        markets = exchange.load_markets()
        filtered = []

        for symbol in available_symbols:
            if symbol not in markets:
                print(f"Symbol {symbol} not found in exchange markets.")
                continue

            details = markets[symbol]

            # Base currency check
            if not symbol.endswith(f"/{base_currency}"):
                print(f"Skipping {symbol}: Does not match base currency {base_currency}.")
                continue

            # Active market check
            if active_only and not details.get('active', True):  # Default to True if 'active' is missing
                print(f"Skipping {symbol}: Market is not active.")
                continue

            # Volume and price checks
            info = details.get('info', {})
            volume = float(info.get('volume', 0))
            price = float(info.get('last', 0))

            if volume < min_volume:
                print(f"Skipping {symbol}: Volume {volume} is below minimum {min_volume}.")
                continue
            if not (min_price <= price <= max_price):
                print(f"Skipping {symbol}: Price {price} is outside range {min_price}-{max_price}.")
                continue

            # Add to filtered list
            filtered.append(symbol)

        print(f"Filtered symbols: {filtered}")
        return filtered

    except Exception as e:
        print(f"An error occurred while filtering symbols: {e}")
        return []

def fetch_historical_data(symbol, timeframe='15m', days=180):
    """
    Fetch historical OHLCV data from MEXC exchange for the past 'days'.
    :param symbol: The trading pair (e.g., 'BTC/USDT')
    :param timeframe: The time interval for the data (e.g., '1m')
    :param days: Number of days to fetch data for
    :return: Pandas DataFrame with historical data
    """
    all_data = []
    since = exchange.parse8601((datetime.utcnow() - timedelta(days=days)).isoformat())

    while since < exchange.milliseconds():
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
            if not ohlcv:
                break
            all_data.extend(ohlcv)
            since = ohlcv[-1][0] + 1  # Increment to the next batch
            time.sleep(exchange.rateLimit / 1000)  # Respect rate limits
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
    :param df: The DataFrame containing the data
    :param symbol: The trading pair symbol (e.g., 'BTC/USDT')
    :param timeframe: The timeframe for the data (e.g., '1m', '15m')
    """
    if not os.path.exists('data_store'):
        os.makedirs('data_store')
    
    filename = f"data_store/{symbol.replace('/', '_')}_{timeframe}.csv"
    df.to_csv(filename)
    print(f"Data for {symbol} with timeframe {timeframe} saved to {filename}")

def load_data(symbol, timeframe):
    """
    Load historical data from CSV files.
    :param symbol: The trading pair (e.g., 'BTC/USDT')
    :param timeframe: The timeframe for the data (e.g., '15m', '1h')
    :return: Pandas DataFrame with historical data
    """
    filename = f"data_store/{symbol.replace('/', '_')}_{timeframe}.csv"
    
    if os.path.exists(filename):
        print(f"Loading data from {filename}...")
        df = pd.read_csv(filename, index_col='timestamp', parse_dates=True)
        return df
    else:
        print(f"Data file for {symbol} on {timeframe} not found.")
        return None

#testing
if __name__ == "__main__":
    # Step 1: Test connection
    if not test_connection():
        exit()
    
    # Step 2: Get available symbols and save to CSV
    get_available_symbols()
    """
    # Step 3: Filter symbols with advanced criteria
    filtered_symbols = filter_symbols_from_csv(
        base_currency="USDT", 
        min_volume=500000, 
        active_only=True, 
        min_price=1, 
        max_price=5000
    )
"""
    # Step 4: Fetch and save historical data for selected symbols
    timeframe = "1h"  # Example timeframe
   
    selected_symbols = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT","APT/USDT","TON/USDT","MXNA/USDT","TRX/USDT","DVA/USDT"
]
    for symbol in selected_symbols:
        print(f"Fetching data for {symbol} with timeframe {timeframe}...")
        data = fetch_historical_data(symbol, timeframe=timeframe, days=90)
        if data is not None and not data.empty:
            save_data_to_csv(data, symbol, timeframe)

