import backtrader as bt

class LiquidityHuntingStrategy(bt.Strategy):
    params = (('liquidity_period', 10), ('buffer', 0.05))

    def __init__(self):
        self.highest_high = bt.indicators.Highest(self.data.high, period=self.params.liquidity_period)
        self.lowest_low = bt.indicators.Lowest(self.data.low, period=self.params.liquidity_period)

    def next(self):
        upper_liquidity_zone = self.highest_high[0] * (1 + self.params.buffer)
        lower_liquidity_zone = self.lowest_low[0] * (1 - self.params.buffer)

        # Long entry: Price dips below the lower liquidity zone
        if self.data.low[0] < lower_liquidity_zone:
            if not self.position:
                self.buy()

        # Short entry: Price spikes above the upper liquidity zone
        elif self.data.high[0] > upper_liquidity_zone:
            if not self.position:
                self.sell()
