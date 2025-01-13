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
    """
    markets = exchange.load_markets()
    symbols = [market for market in markets if '/' in market]  # Only trading pairs with '/'
    
    # Save the list of symbols to a CSV file
    symbols_df = pd.DataFrame(symbols, columns=["symbol"])
    if not os.path.exists('data_store'):
        os.makedirs('data_store')
    
    symbols_df.to_csv('data_store/available_symbols.csv', index=False)
    print(f"Available symbols saved to 'data_store/available_symbols.csv'")

def filter_symbols(base_currency="USDT", min_volume=100000, active_only=True, min_price=0.01, max_price=100000):
    """
    Filter symbols based on flexible criteria such as base currency, minimum volume, and price range.
    :param base_currency: The base currency to filter by (e.g., 'USDT').
    :param min_volume: The minimum 24-hour trading volume to include.
    :param active_only: Whether to include only active markets.
    :param min_price: Minimum price of the trading pair.
    :param max_price: Maximum price of the trading pair.
    :return: A list of filtered symbols.
    """
    markets = exchange.load_markets()
    filtered = []
    
    for symbol, details in markets.items():
        if not symbol.endswith(f"/{base_currency}"):
            continue
        if active_only and not details['active']:
            continue
        volume = float(details['info'].get('volume', 0))
        if volume < min_volume:
            continue
        price = float(details['info'].get('last', 0))
        if not (min_price <= price <= max_price):
            continue
        filtered.append(symbol)
    
    print(f"Filtered symbols: {filtered}")
    return filtered

def fetch_historical_data(symbol, timeframe='1m', days=180):
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

    # Step 3: Filter symbols with advanced criteria
    filtered_symbols = filter_symbols(
        base_currency="USDT", 
        min_volume=500000, 
        active_only=True, 
        min_price=0.01, 
        max_price=5000
    )

    # Step 4: Fetch and save historical data for selected symbols
    timeframe = '15m'  # Example timeframe
    for symbol in filtered_symbols[:5]:  # Limit to 5 for testing
        print(f"Fetching data for {symbol} with timeframe {timeframe}...")
        data = fetch_historical_data(symbol, timeframe=timeframe, days=180)
        if data is not None and not data.empty:
            save_data_to_csv(data, symbol, timeframe)
