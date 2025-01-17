import itertools
import numpy as np
import os
import pandas as pd
import importlib.util
import sys
from datetime import datetime
import backtrader as bt
from data_handler import load_data
from tqdm import tqdm
import multiprocessing


class Optimizer:
    def __init__(self, strategy_name, symbols, timeframes, param_ranges, cash=1000, commission=0.001, batch_size=50):
        """
        Initializes the optimizer with a strategy, parameters, and symbols.
        :param strategy_name: The name of the strategy class to optimize.
        :param symbols: List of symbols to backtest on.
        :param timeframes: List of timeframes to backtest on.
        :param param_ranges: Dictionary of parameters and their ranges to optimize.
        :param cash: Starting cash for the backtest.
        :param commission: Commission for trades.
        :param batch_size: Number of combinations to process per batch.
        """
        self.strategy_name = strategy_name
        self.symbols = symbols
        self.timeframes = timeframes
        self.param_ranges = param_ranges
        self.cash = cash
        self.commission = commission
        self.results = []
        self.batch_size = batch_size

    def load_strategy(self):
        """
        Dynamically load the strategy class from the strategies folder.
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

                if hasattr(module, self.strategy_name):
                    return getattr(module, self.strategy_name)

        raise ValueError(f"Strategy '{self.strategy_name}' not found in {strategies_folder} folder.")

    def _generate_param_combinations_in_batches(self):
        """
        Generates and processes parameter combinations in batches to avoid memory overload.
        :return: Generator yielding batches of parameter combinations.
        """
        param_combinations = []
        for param, value in self.param_ranges.items():
            # Check if the value is a list or a range
            if isinstance(value, list):  # If the value is a list, treat it as discrete values
                param_combinations.append(value)
            elif isinstance(value, range):  # If the value is a range object
                param_combinations.append(list(value))  # Convert range to list
            elif isinstance(value, tuple) and len(value) == 3:  # If the value is a tuple (start, stop, step)
                param_combinations.append(np.arange(value[0], value[1], value[2]))
            else:
                raise ValueError(f"Invalid range or list for parameter '{param}'.")

        # Calculate the number of combinations
        total_combinations = np.prod([len(comb) for comb in param_combinations])
        
        # Yield combinations in batches
        for i in range(0, total_combinations, self.batch_size):
            batch_combinations = list(itertools.islice(itertools.product(*param_combinations), i, i + self.batch_size))
            yield [dict(zip(self.param_ranges.keys(), combination)) for combination in batch_combinations]

    def _run_backtest(self, params):
        """
        Runs the backtest for a given set of parameters.
        """
        print(f"Running backtest with parameters: {params}")
        
        # Load strategy dynamically
        strategy = self.load_strategy()

        # Initialize Backtrader engine
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(self.cash)
        cerebro.broker.setcommission(commission=self.commission)

        # Add data for each symbol and timeframe
        for symbol in self.symbols:
            for timeframe in self.timeframes:
                print(f"Loading data for {symbol} on {timeframe} timeframe...")
                data = load_data(symbol, timeframe)
                if data is not None:
                    data_feed = bt.feeds.PandasData(dataname=data)
                    cerebro.adddata(data_feed, name=f"{symbol}_{timeframe}")

        # Add strategy with current params
        cerebro.addstrategy(strategy, **params)

        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')

        # Run backtest
        result = cerebro.run()

        # Store results for analysis
        self.results.append({
            "params": params,
            "final_portfolio_value": cerebro.broker.getvalue(),
            "sharpe_ratio": result[0].analyzers.sharpe.get_analysis().get('sharperatio', None),
            "max_drawdown": result[0].analyzers.drawdown.get_analysis().get('max', {}).get('drawdown', None),
            "total_trades": result[0].analyzers.tradeanalyzer.get_analysis().get('total', {}).get('total', 0),
            "winning_trades": result[0].analyzers.tradeanalyzer.get_analysis().get('won', {}).get('total', 0),
            "losing_trades": result[0].analyzers.tradeanalyzer.get_analysis().get('lost', {}).get('total', 0),
        })

    def optimize(self):
        """
        Runs optimization by iterating over the parameter ranges and running backtests.
        """
        # Initialize TQDM progress bar with better appearance
        with tqdm(total=0, desc="Optimization Progress", 
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [Time: {elapsed} < {remaining}, Speed: {rate_fmt}]", 
                  dynamic_ncols=True) as pbar:

            total_combinations = np.prod([len(v) for v in self.param_ranges.values()])
            pbar.total = total_combinations  # Set total number of combinations

            # Use multiprocessing Pool for parallel execution
            with multiprocessing.Pool() as pool:
                param_batches = self._generate_param_combinations_in_batches()
                # Use pool.map for distributing work
                pool.starmap(self._run_backtest, [(params,) for param_batch in param_batches for params in param_batch])

            # Save all optimization results to CSV
            self.save_optimization_results()

    def save_optimization_results(self):
        """
        Save all optimization results to a CSV file.
        """
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{results_dir}/optimization_results_{timestamp}.csv"

        # Convert results to DataFrame and save to CSV
        df = pd.DataFrame(self.results)
        df.to_csv(filename, index=False)
        print(f"Optimization results saved to {filename}")


if __name__ == "__main__":
    # Define the parameter ranges for optimization
    param_ranges = {
        'ema_short_period': range(10, 30, 2),
        'ema_long_period': range(40, 80, 2),
        'rsi_lower': range(10, 40, 5),
        'rsi_upper': range(30, 80, 5),
        'macd_fast': range(5, 50, 5),
        'macd_slow': range(5, 80, 5),
        'macd_signal': range(9, 30, 5)
    }

    # Initialize optimizer
    optimizer = Optimizer(
        strategy_name="SpotDayTradingStrategy",
        symbols=["XRP/USDT"],
        timeframes=["30m"],
        param_ranges=param_ranges,
        cash=15,
        commission=0.001,
        batch_size=50  # Adjust batch size as needed
    )

    # Run optimization
    optimizer.optimize()
