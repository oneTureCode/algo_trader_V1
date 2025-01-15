import pandas as pd
import os
import backtrader as bt
from datetime import datetime
import importlib
import numpy as np

class Optimizer:
    def __init__(self, results_csv, param_ranges, strategies_folder='strategies', results_dir='results', walk_forward=False, train_ratio=0.7):
        """
        Initialize the Optimizer with parameters and load backtest results.
        """
        self.results_csv = results_csv
        self.param_ranges = param_ranges
        self.strategies_folder = strategies_folder
        self.results_dir = results_dir
        self.walk_forward = walk_forward
        self.train_ratio = train_ratio
        self.results = []

        # Load backtest results
        self.backtest_results = self.load_backtest_results()

    def load_backtest_results(self):
        """
        Load the backtest results from the provided CSV file.
        """
        try:
            return pd.read_csv(self.results_csv)
        except Exception as e:
            print(f"Error loading backtest results from {self.results_csv}: {e}")
            raise

    def get_strategy_info(self, strategy_name):
        """
        Retrieve the symbol, timeframe, and data file for the specified strategy.
        """
        try:
            strategy_info = self.backtest_results[self.backtest_results['strategy'] == strategy_name].iloc[0]
            timeframe = eval(strategy_info['tmieframe'])[0]  # Parse the list string for timeframe
            timestamp = strategy_info['timestamp']

            # Construct the data file path dynamically (adjust based on your folder structure)
            data_file = f"Data_store/{strategy_name}_{timeframe}.csv"
            return timeframe, data_file
        except Exception as e:
            print(f"Error retrieving strategy info for {strategy_name}: {e}")
            raise

    def load_strategy_class(self, strategy_name):
        """
        Dynamically load the strategy class from the strategies folder.
        """
        try:
            strategy_module = importlib.import_module(f"{self.strategies_folder}.{strategy_name}")
            strategy_class = getattr(strategy_module, strategy_name)
            return strategy_class
        except Exception as e:
            print(f"Error loading strategy {strategy_name}: {e}")
            raise

    def generate_param_grid(self):
        """
        Generate parameter grid using the ranges provided.
        """
        param_grid = []
        for param, (min_val, max_val, step) in self.param_ranges.items():
            param_grid.append(np.arange(min_val, max_val, step))
        
        param_combinations = np.array(np.meshgrid(*param_grid)).T.reshape(-1, len(self.param_ranges))
        
        param_dicts = []
        for combination in param_combinations:
            param_dict = {list(self.param_ranges.keys())[i]: combination[i] for i in range(len(combination))}
            param_dicts.append(param_dict)
        
        return param_dicts

    def optimize(self, strategy_name):
        """
        Optimize the specified strategy.
        """
        # Get strategy information from backtest results
        timeframe, data_file = self.get_strategy_info(strategy_name)

        # Load data using your custom data handler
        from data_handler import load_data
        data = load_data(data_file)

        # Dynamically load the strategy class
        strategy_class = self.load_strategy_class(strategy_name)

        # Split the data into training and testing sets if walk-forward is enabled
        if self.walk_forward:
            train_data, test_data = self.split_data(data)
        else:
            train_data = data
            test_data = data

        # Generate parameter grid
        param_grid = self.generate_param_grid()

        # Run optimization for each combination of parameters
        for param_set in param_grid:
            print(f"Optimizing {strategy_name} with parameters: {param_set}")
            
            cerebro = bt.Cerebro()
            cerebro.adddata(train_data)
            cerebro.addstrategy(strategy_class, **param_set)

            result = cerebro.run()
            self.store_results(result, param_set, test_data)

        # After optimization, save results to CSV
        self.save_results_to_csv(strategy_name)

    def split_data(self, data):
        """
        Split data into training and testing sets based on the train_ratio.
        """
        train_len = int(len(data) * self.train_ratio)
        train_data = data[:train_len]
        test_data = data[train_len:]
        return train_data, test_data

    def store_results(self, result, param_set, test_data):
        """
        Store the results of the optimization.
        """
        for run in result:
            final_value = run[0].broker.getvalue()
            sharpe_ratio = run[0].analyzers.sharpe.get_analysis().get('sharperatio', 0)

            # Additional metrics can be added as needed

            self.results.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
                'final_portfolio_value': final_value,
                'sharpe_ratio': sharpe_ratio,
                'params': param_set
            })

    def save_results_to_csv(self, strategy_name):
        """
        Save the optimization results to a CSV file.
        """
        results_df = pd.DataFrame(self.results)
        result_filename = os.path.join(self.results_dir, f"optimization_results_{strategy_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
        results_df.to_csv(result_filename, index=False)
        print(f"Optimization results saved to {result_filename}")


if __name__ == "__main__":
    param_ranges = {
        'risk_appetite': (0.05, 0.3, 0.05),
        'trade_fee': (0.001, 0.01, 0.001),
        'ema_short': (10, 30, 2),
        'ema_long': (30, 100, 5)
    }

    optimizer = Optimizer(
        results_csv='backtest_results_2025-01-15_10-29-46.csv',
        param_ranges=param_ranges,
        walk_forward=True,
        train_ratio=0.7
    )

    # Optimize all strategies found in the CSV
    for strategy_name in optimizer.backtest_results['strategy'].unique():
        print(f"Optimizing strategy: {strategy_name}")
        optimizer.optimize(strategy_name)
