import backtrader as bt

class DarvasBoxStrategy(bt.Strategy):
    params = (('box_period', 20), ('atr_period', 14))

    def __init__(self):
        self.highest_high = bt.indicators.Highest(self.data.high, period=self.params.box_period)
        self.lowest_low = bt.indicators.Lowest(self.data.low, period=self.params.box_period)
        self.atr = bt.indicators.AverageTrueRange(period=self.params.atr_period)

    def next(self):
        upper_box = self.highest_high[0]
        lower_box = self.lowest_low[0]

        # Long entry: Breakout above the upper box
        if self.data.close[0] > upper_box and self.data.close[-1] <= upper_box:
            if not self.position:
                self.buy()

        # Short entry: Breakout below the lower box
        elif self.data.close[0] < lower_box and self.data.close[-1] >= lower_box:
            if not self.position:
                self.sell()
