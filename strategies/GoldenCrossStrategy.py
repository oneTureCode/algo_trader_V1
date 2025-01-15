import backtrader as bt

class GoldenCrossStrategy(bt.Strategy):
    # Define the parameters for the SMAs
    short_sma_period = 50
    long_sma_period = 200

    def __init__(self):
        # Define the 50-period and 200-period SMAs
        self.short_sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.short_sma_period)
        self.long_sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.long_sma_period)

    def next(self):
        # Check if we are in a consolidation phase by using Bollinger Bands (optional)
        # For simplicity, assume Bollinger Bands are not used here, but you can add them if needed

        # Entry logic: Golden Cross (50 SMA crosses above 200 SMA)
        if self.short_sma > self.long_sma and self.data.close[0] > self.long_sma[0]:
            if not self.position:  # Only enter if we don't already have a position
                self.buy()

        # Exit logic: Death Cross (50 SMA crosses below 200 SMA)
        elif self.short_sma < self.long_sma:
            if self.position:  # Only exit if we have a position
                self.sell()
