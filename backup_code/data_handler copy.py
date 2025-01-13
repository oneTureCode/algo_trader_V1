# data_handler.py

import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time
import config
import os

# Initialize exchange connection
exchange = ccxt.mexc({
    'key': config.APIS["MEXC"]["key"],
    'pass': config.APIS["MEXC"]["pass"],
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot'
        # Ensures spot mode is active
    }
})
def test_connection():
    try:
        # Fetching the exchange status to test the connection
        status = exchange.fetch_status()
        print("Connection successful! Exchange status:")
        print(status)
        return True
    except Exception as e:
        print("Connection failed!")
        print(e)
        return False


# Function to get available symbols from the exchange
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

# Function to fetch historical data for a given symbol and timeframe
def fetch_historical_data(symbol, timeframe='1m', limit=1000):
    """
    Fetch historical OHLCV data from MEXC exchange for the past 6 months.
    :param symbol: The trading pair (e.g., 'BTC/USDT')
    :param timeframe: The time interval for the data (e.g., '1m')
    :param limit: Number of data points to fetch (max limit for 1m bars)
    :return: Pandas DataFrame with historical data
    """
    # Calculate the timestamp for 6 months ago
    since = exchange.parse8601((datetime.utcnow() - timedelta(days=180)).isoformat())

    # Fetch data from MEXC
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
    
    # Convert the data into a pandas DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Set timestamp as the index
    df.set_index('timestamp', inplace=True)
    print(df.head())
    return df

# Function to save the historical data to a CSV file
def save_data_to_csv(df, symbol, timeframe):
    """
    Save the historical data to a CSV file in the data_store folder.
    :param df: The DataFrame containing the data
    :param symbol: The trading pair symbol (e.g., 'BTC/USDT')
    :param timeframe: The timeframe for the data (e.g., '1m', '5m')
    """
    # Create a directory for data if it doesn't exist
    if not os.path.exists('data_store'):
        os.makedirs('data_store')
    
    # Define the filename based on the trading pair and timeframe
    filename = f"data_store/{symbol.replace('/', '_')}_{timeframe}.csv"
    
    # Save the data to CSV
    df.to_csv(filename)
    print(f"Data for {symbol} with timeframe {timeframe} saved to {filename}")
# Run the test connection
if __name__ == "__main__":
    test_connection()
    # Step 1: Get available symbols and save to CSV
    get_available_symbols()

    # Example: Fetch and save historical data for selected trading pairs and timeframes
    # Let's assume you've selected some pairs manually or dynamically from the available symbols
    selected_symbols = [
        "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"
    ]

    # Define the timeframe you want to use
    timeframe = '15m'  # You can change this dynamically as needed

    # Fetch and save historical data for each selected symbol
    for symbol in selected_symbols:
        print(f"Fetching data for {symbol} with timeframe {timeframe}...")
        data = fetch_historical_data(symbol, timeframe=timeframe, limit=1000)  # 1000 is the max for 1m bars
        print(data)

        #save_data_to_csv(data, symbol, timeframe)

