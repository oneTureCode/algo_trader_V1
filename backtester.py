# backtester.py

import backtrader as bt
import os
import pandas as pd
from data_handler import load_data
from datetime import datetime
import strategies
#from strategies import *
#import strategies.SampleStrategy

class Backtester:
    def __init__(self, strategy, cash=1000, commission=0.001):
        self.strategy = strategy
        self.cash = cash
        self.commission = commission
        self.cerebro = bt.Cerebro()

    def add_data(self, symbols, timeframes):
        """
        Dynamically add single or multiple pairs and timeframes.
        """
        for symbol in symbols:
            for timeframe in timeframes:
                print(f"Loading data for {symbol} on {timeframe} timeframe...")
                data = load_data(symbol, timeframe)
                if data is not None:
                    data_feed = bt.feeds.PandasData(dataname=data)
                    self.cerebro.adddata(data_feed, name=f"{symbol}_{timeframe}")

    def configure(self):
        """
        Configure cash, commission, and strategy.
        """
        self.cerebro.broker.setcash(self.cash)
        self.cerebro.broker.setcommission(commission=self.commission)
        self.cerebro.addstrategy(self.strategy)

    def run(self):
        """
        Run the backtest and save results.
        """
        print("Starting portfolio value:", self.cerebro.broker.getvalue())
        self.cerebro.run()
        print("Ending portfolio value:", self.cerebro.broker.getvalue())

        # Save results with a timestamp
        self.save_results()

        # Plot the results
        self.cerebro.plot()

    def save_results(self):
        """
        Save backtest results to a CSV file with a timestamp.
        """
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{results_dir}/backtest_results_{timestamp}.csv"

        # Assuming the broker's portfolio value is what we want to track
        portfolio_value = self.cerebro.broker.getvalue()
        results = {
            "timestamp": [timestamp],
            "portfolio_value": [portfolio_value],
        }

        results_df = pd.DataFrame(results)
        results_df.to_csv(filename, index=False)
        print(f"Results saved to {filename}")

if __name__ == "__main__":
    # Example usage with a sample strategy
    #from strategies.sample_strategy import SampleStrategy

    # Define pairs and timeframes
    symbols = ["BTC/USDT", "ETH/USDT"]
    timeframes = ["15m", "1h"]

    # Initialize backtester
    backtester = Backtester(strategy=strategies.SampleStrategy, cash=1000, commission=0.001)

    # Add data and configure
    backtester.add_data(symbols, timeframes)
    backtester.configure()

    # Run backtest
    backtester.run()
