import backtrader as bt

class SidewaysPriceActionStrategy(bt.Strategy):
    params = (('ma_period', 20), ('range_buffer', 0.01))

    def __init__(self):
        self.ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.ma_period)

    def next(self):
        upper_bound = self.ma[0] * (1 + self.params.range_buffer)
        lower_bound = self.ma[0] * (1 - self.params.range_buffer)

        # Long entry: Price near the lower bound
        if self.data.close[0] < lower_bound:
            if not self.position:
                self.buy()

        # Short entry: Price near the upper bound
        elif self.data.close[0] > upper_bound:
            if not self.position:
                self.sell()
