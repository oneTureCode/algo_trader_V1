import pandas as pd
import os
import backtrader as bt
from data_handler import load_data
from datetime import datetime
import importlib
import numpy as np
import inspect

class Optimizer:
    def __init__(self, results_csv, strategies_folder='strategies', results_dir='results'):
        self.results_csv = results_csv
        self.strategies_folder = strategies_folder
        self.results_dir = results_dir
        self.results = []
        self.backtest_results = self.load_backtest_results()

    def load_backtest_results(self):
        """Load backtest results CSV file"""
        try:
            return pd.read_csv(self.results_csv)
        except Exception as e:
            print(f"Error loading backtest results from {self.results_csv}: {e}")
            return pd.DataFrame()  # Return an empty DataFrame if loading fails

    def get_strategy_info(self, strategy_name):
        """Retrieve strategy info from backtest results"""
        try:
            strategy_info = self.backtest_results[self.backtest_results['strategy'] == strategy_name].iloc[0]
            timeframe = eval(strategy_info['timeframe'])[0]
            symbol = eval(strategy_info['symbol'])[0]
            data_file = f"Data_store/{symbol}_{timeframe}.csv"
            return timeframe, symbol, data_file
        except Exception as e:
            print(f"Error retrieving strategy info for {strategy_name}: {e}")
            return None, None, None

    def load_strategy_class(self, strategy_name):
        """Dynamically load strategy class from the strategies folder"""
        try:
            strategy_module = importlib.import_module(f"{self.strategies_folder}.{strategy_name}")
            strategy_class = getattr(strategy_module, strategy_name)
            return strategy_class
        except Exception as e:
            print(f"Error loading strategy {strategy_name}: {e}")
            return None

    def generate_param_grid(self, strategy_class):
        """Generate parameter grid dynamically based on strategy class"""
        valid_params = self.get_valid_params(strategy_class)
        param_grid = []
        
        # Automatically generate ranges for parameters based on their types
        for param, param_type in valid_params.items():
            if param_type == int:
                param_grid.append(np.arange(10, 25, 1))  # Example: integer range for 'ma_period'
            elif param_type == float:
                param_grid.append(np.arange(0.01, 0.1, 0.01))  # Example: float range for 'range_buffer'
            elif param_type == bool:
                param_grid.append([True, False])  # Example: boolean for 'use_ema'
            else:
                print(f"Unsupported parameter type for {param}. Skipping...")

        # Generate all combinations of parameter values
        param_combinations = np.array(np.meshgrid(*param_grid)).T.reshape(-1, len(param_grid))
        
        # Convert to dictionaries for easy usage
        param_dicts = []
        for combination in param_combinations:
            param_dict = {list(valid_params.keys())[i]: combination[i].item() for i in range(len(combination))}
            param_dicts.append(param_dict)
        
        return param_dicts

    def get_valid_params(self, strategy_class):
        """Get valid parameters from the strategy class"""
        signature = inspect.signature(strategy_class.__init__)
        valid_params = {param: annotation for param, annotation in signature.parameters.items() if param != 'self'}
        return valid_params

    def optimize(self, strategy_name):
        """Optimize a strategy based on parameter grid"""
        timeframe, symbol, data_file = self.get_strategy_info(strategy_name)
        if not timeframe or not symbol or not data_file:
            print(f"Skipping optimization for {strategy_name} due to missing data.")
            return

        data = load_data(symbol, timeframe)

        strategy_class = self.load_strategy_class(strategy_name)
        if not strategy_class:
            print(f"Skipping optimization for {strategy_name} due to missing strategy class.")
            return

        # Generate parameter grid dynamically
        param_grid = self.generate_param_grid(strategy_class)

        # Wrap the full dataset as a Backtrader data feed
        data_feed = bt.feeds.PandasData(dataname=data)

        for param_set in param_grid:
            print(f"Optimizing {strategy_name} with parameters: {param_set}")
            
            cerebro = bt.Cerebro()
            cerebro.adddata(data_feed)  # Add the Backtrader data feed

            # Add analyzers for performance metrics
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradecount')

            cerebro.addstrategy(strategy_class, **param_set)

            try:
                result = cerebro.run()
                self.store_results(result, param_set, strategy_name, symbol, timeframe)
            except Exception as e:
                print(f"Error during optimization for parameters {param_set}: {e}")

        self.save_results_to_csv(strategy_name)

    def store_results(self, result, param_set, strategy_name, symbol, timeframe):
        """Store the results of the optimization"""
        for run in result:
            final_value = run[0].broker.getvalue()
            sharpe_ratio = run[0].analyzers.sharpe.get_analysis().get('sharperatio', 0)
            max_drawdown = run[0].analyzers.drawdown.get_analysis().get('max', 0)
            total_trades = run[0].analyzers.tradecount.get_analysis().get('total', 0)
            winning_trades = run[0].analyzers.tradecount.get_analysis().get('won', 0)
            losing_trades = run[0].analyzers.tradecount.get_analysis().get('lost', 0)
            win_rate = (winning_trades / total_trades) if total_trades > 0 else 0

            self.results.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
                'strategy': strategy_name,
                'timeframe': timeframe,
                'symbol': symbol,
                'final_portfolio_value': final_value,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'params': param_set
            })

    def save_results_to_csv(self, strategy_name):
        """Save the optimization results to CSV"""
        results_df = pd.DataFrame(self.results)
        result_filename = os.path.join(self.results_dir, f"optimization_results_{strategy_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
        results_df.to_csv(result_filename, index=False)
        print(f"Optimization results saved to {result_filename}")

if __name__ == "__main__":
    optimizer = Optimizer(
        results_csv='results/backtest_results_2025-01-15_15-30-47.csv'
    )

    # Automatically optimize all strategies in the backtest results
    for strategy_name in optimizer.backtest_results['strategy'].unique():
        print(f"Optimizing strategy: {strategy_name}")
        optimizer.optimize(strategy_name)
