import backtrader as bt

class FibonacciRetracementStrategy(bt.Strategy):
    params = (('short_ma_period', 20), ('long_ma_period', 50), ('fib_levels', [0.236, 0.382, 0.5, 0.618]))

    def __init__(self):
        self.short_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.short_ma_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.long_ma_period)

    def next(self):
        high = max(self.data.high.get(size=20))
        low = min(self.data.low.get(size=20))
        diff = high - low
        fib_retracements = [high - diff * level for level in self.params.fib_levels]

        # Long entry: Price is near a Fibonacci retracement level, and short MA > long MA
        for fib_level in fib_retracements:
            if abs(self.data.close[0] - fib_level) <= 0.01 * fib_level and self.short_ma[0] > self.long_ma[0]:
                if not self.position:
                    self.buy()

        # Short entry: Price is near a Fibonacci retracement level, and short MA < long MA
        for fib_level in fib_retracements:
            if abs(self.data.close[0] - fib_level) <= 0.01 * fib_level and self.short_ma[0] < self.long_ma[0]:
                if not self.position:
                    self.sell()
