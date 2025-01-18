# backtester.py

import backtrader as bt
import os
import pandas as pd
from data_handler import load_data
from datetime import datetime
import importlib.util
import sys

class Backtester:
    def __init__(self, strategy_name, cash=1000, commission=0.001):
        """
        Initializes the backtester with a dynamic strategy class.
        :param strategy_name: The name of the strategy class to load (e.g., 'SampleStrategy').
        :param cash: The starting cash for the backtest.
        :param commission: The commission for trades.
        """
        self.strategy_name = strategy_name
        self.timeframe = timeframes
        self.symbols = symbols
        self.cash = cash
        self.commission = commission
        self.cerebro = bt.Cerebro()
        self.strategy = self.load_strategy(strategy_name)
        self.results = None  # To store the results after the backtest

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

        # Add analyzers
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')

    def run(self):
        """
        Run the backtest and save results.
        """
        print("Starting portfolio value:", self.cerebro.broker.getvalue())
        self.results = self.cerebro.run()
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

        # Extract metrics from analyzers
        metrics = []
        for strat in self.results:
            sharpe = strat.analyzers.sharpe.get_analysis().get('sharperatio', None)
            drawdown = strat.analyzers.drawdown.get_analysis()
            trades = strat.analyzers.tradeanalyzer.get_analysis()

            # Safely access the trade data
            total_trades = trades.get('total', {}).get('total', 0)
            winning_trades = trades.get('won', {}).get('total', 0)
            losing_trades = trades.get('lost', {}).get('total', 0)
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

            # Handle profit factor calculation (check if losses exist)
            profit_factor = None
            won_pnl = trades.get('won', {}).get('pnl', {}).get('gross', 0)
            lost_pnl = trades.get('lost', {}).get('pnl', {}).get('gross', 0)

            if lost_pnl != 0:
                profit_factor = won_pnl / abs(lost_pnl)
            elif won_pnl > 0:  # If no losses but there are winning trades
                profit_factor = float('inf')  # Infinite profit factor (perfect scenario)

            avg_trade_duration = trades.get('len', {}).get('average', None)
            drawdown_duration = drawdown.get('max', {}).get('len', 0)
            volatility = strat.analyzers.sharpe.get_analysis().get('stddev', None)

            metrics.append({
                "timestamp": timestamp,
                "strategy": self.strategy_name,
                "timeframe": self.timeframe,
                "symbol": self.symbols,
                "final_portfolio_value": self.cerebro.broker.getvalue(),
                "sharpe_ratio": sharpe,
                "max_drawdown": drawdown.get('max', {}).get('drawdown', None),
                "drawdown_duration": drawdown_duration,
                "volatility": volatility,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "avg_trade_duration": avg_trade_duration,
                "profit_factor": profit_factor,
            })
        # Save metrics to CSV
        results_df = pd.DataFrame(metrics)
        results_df.to_csv(filename, index=False)
        print(f"Results saved to {filename}")
        

if __name__ == "__main__":
    # Define pairs and timeframes
    symbols = ["XRP/USDT"]
    timeframes = ["30m"]

    # Specify the strategy class name (e.g., 'SampleStrategy')
    strategy_name = "MultiLayerStrategy_V2"

    # Initialize backtester
    backtester = Backtester(strategy_name=strategy_name, cash=15, commission=0.001)

    # Add data and configure
    backtester.add_data(symbols, timeframes)
    backtester.configure()

    # Run backtest
    backtester.run()
