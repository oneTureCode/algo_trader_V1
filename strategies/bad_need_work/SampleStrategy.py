# strategies/sample_strategy.py

import backtrader as bt

class SampleStrategy(bt.Strategy):
    # Define the moving averages
    short_period = 10
    long_period = 30

    def __init__(self):
        # Add moving averages
        self.short_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.long_period)

    def next(self):
        # Buy signal: Short MA crosses above Long MA
        if self.short_ma > self.long_ma and not self.position:
            self.buy()
        
        # Sell signal: Short MA crosses below Long MA
        elif self.short_ma < self.long_ma and self.position:
            self.sell()
