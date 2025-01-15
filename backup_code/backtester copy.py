# backtester.py

import backtrader as bt
import os
import pandas as pd
from data_handler import load_data
from datetime import datetime
import importlib.util
import sys

class Backtester:
    def __init__(self, strategy_name, cash=1000, commission=0.001,symbols=None, timeframes=None):
        """
        Initializes the backtester with a dynamic strategy class.
        :param strategy_name: The name of the strategy class to load (e.g., 'SampleStrategy').
        :param cash: The starting cash for the backtest.
        :param commission: The commission for trades.
        """
        self.strategy_name = strategy_name
        self.cash = cash
        self.commission = commission
        self.cerebro = bt.Cerebro()
        self.strategy = self.load_strategy(strategy_name)
        self.symbols = symbols
        self.timeframes = timeframes

    @staticmethod
    def load_strategy(strategy_name):
        """
        Dynamically load a strategy class from the strategies folder.
        :param strategy_name: The name of the strategy class to load.
        :return: The strategy class.
        """
        strategies_folder = "strategies"
        for file in os.listdir(strategies_folder):
            if file.endswith(".py") and not file.startswith("__"):
                module_name = file[:-3]
                module_path = os.path.join(strategies_folder, file)
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Add the module to sys.modules so Backtrader can find it
                sys.modules[module_name] = module

                if hasattr(module, strategy_name):
                    return getattr(module, strategy_name)

        raise ValueError(f"Strategy '{strategy_name}' not found in {strategies_folder} folder.")

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
    Save backtest results to a CSV file with strategy name, symbols, timeframes, and timestamp
    """    
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Create a name convention for multiple symbols and timeframes
    symbol_str = "_".join(symbols)
    timeframe_str = "_".join(timeframes)
    strategy_name = strategy_name

    # Generate a filename based on strategy name, symbols, timeframes, and timestamp
    filename = f"{results_dir}/backtest_results_{strategy_name}_{symbol_str}_{timeframe_str}_{timestamp}.csv"

    # Assuming the broker's portfolio value is what we want to track
    portfolio_value = self.cerebro.broker.getvalue()

    # Extract the performance metrics
    first_strategy = self.cerebro.run()[0]

    # Access the analyzers
    drawdown_analyzer = first_strategy.analyzers.getbyname('drawdown')
    tradeanalyzer = first_strategy.analyzers.getbyname('tradeanalyzer')
    variance_analyzer = first_strategy.analyzers.getbyname('variance')
    cumulative_analyzer = first_strategy.analyzers.getbyname('cumulative')
    annual_analyzer = first_strategy.analyzers.getbyname('annual')
    sharpe_analyzer = first_strategy.analyzers.getbyname('sharpe')
    sortino_analyzer = first_strategy.analyzers.getbyname('sortino')

    # Performance metrics
    drawdown_data = drawdown_analyzer.get_analysis()
    max_drawdown = drawdown_data.get('max', {}).get('drawdown', None)
    drawdown_duration = drawdown_data.get('max', {}).get('duration', None)

    trade_data = tradeanalyzer.get_analysis()
    total_trades = trade_data.get('total', 0)
    win_rate = (trade_data.get('won', {}).get('total', 0) / total_trades * 100) if total_trades > 0 else 0
    average_gain = trade_data.get('won', {}).get('avg', 0)
    average_loss = trade_data.get('lost', {}).get('avg', 0)
    profit_factor = (trade_data.get('won', {}).get('total', 0) / 
                     abs(trade_data.get('lost', {}).get('total', 1))) if total_trades > 0 else float('inf')
    time_in_market = trade_data.get('time', {}).get('total', 0)
    expected_payoff = trade_data.get('expected', 0)
    avg_trade_duration = trade_data.get('time', {}).get('avg', 0)
    average_trade_size = trade_data.get('size', {}).get('avg', 0)
    max_trade_size = trade_data.get('size', {}).get('max', 0)

    volatility = variance_analyzer.get_analysis().get('variance', 0)

    # Additional performance metrics
    cumulative_return = cumulative_analyzer.get_analysis().get('cumulative', 0)
    annualized_return = annual_analyzer.get_analysis().get('cagr', 0)
    sharpe_ratio = sharpe_analyzer.get_analysis().get('sharpe', 0)
    sortino_ratio = sortino_analyzer.get_analysis().get('sortino', 0)

    # Store results in a dictionary
    results = {
        "timestamp": [timestamp],
        "portfolio_value": [portfolio_value],
        "cumulative_return": [cumulative_return],
        "annualized_return": [annualized_return],
        "sharpe_ratio": [sharpe_ratio],
        "sortino_ratio": [sortino_ratio],
        "max_drawdown": [max_drawdown],
        "win_rate": [win_rate],
        "average_gain": [average_gain],
        "average_loss": [average_loss],
        "profit_factor": [profit_factor],
        "total_trades": [total_trades],
        "time_in_market": [time_in_market],
        "expected_payoff": [expected_payoff],
        "volatility": [volatility],
        "drawdown_duration": [drawdown_duration],
        "avg_trade_duration": [avg_trade_duration],
        "average_trade_size": [average_trade_size],
        "max_trade_size": [max_trade_size],
    }

    # Convert results to a DataFrame and save to CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv(filename, index=False)
    print(f"Results saved to {filename}")


if __name__ == "__main__":
    # Define pairs and timeframes
    symbols = ["XRP_USDT"]
    timeframes = ["15m"]

    # Specify the strategy class name (e.g., 'SampleStrategy')
    strategy_name = "QuickFlipStrategy"

    # Initialize backtester
    backtester = Backtester(strategy_name=strategy_name, cash=100, commission=0.002)

    # Add data and configure
    backtester.add_data(symbols, timeframes)
    backtester.configure()

    # Run backtest
    backtester.run()
