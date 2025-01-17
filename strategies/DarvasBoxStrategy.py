import backtrader as bt

class DarvasBoxStrategy(bt.Strategy):
    params = (
        ('box_period', 20),  # Box period
        ('atr_period', 14),  # ATR period
        ('stop_loss_atr', 1.5),  # Stop loss as a multiple of ATR
        ('take_profit_atr', 2.0),  # Take profit as a multiple of ATR
        ('sma_period', 50),  # SMA period for trend filter
        ('risk_per_trade', 0.01),  # Risk per trade (1% of portfolio)
    )

    def __init__(self):
        self.highest_high = bt.indicators.Highest(self.data.high, period=self.params.box_period)
        self.lowest_low = bt.indicators.Lowest(self.data.low, period=self.params.box_period)
        self.atr = bt.indicators.AverageTrueRange(period=self.params.atr_period)
        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.sma_period)

    def next(self):
        upper_box = self.highest_high[0]
        lower_box = self.lowest_low[0]

        # Trend filter: Only trade in the direction of the trend (above or below the SMA)
        if self.data.close[0] > self.sma[0]:
            trend = 'up'  # Bullish trend
        else:
            trend = 'down'  # Bearish trend

        # Calculate position size based on risk per trade
        position_size = self.broker.get_value() * self.params.risk_per_trade / self.atr[0]

        # Long entry: Breakout above the upper box and the trend is up
        if self.data.close[0] > upper_box and self.data.close[-1] <= upper_box and trend == 'up':
            if not self.position:
                self.buy(size=position_size)
                # Set stop loss and take profit based on ATR
                stop_loss = self.data.close[0] - self.params.stop_loss_atr * self.atr[0]
                take_profit = self.data.close[0] + self.params.take_profit_atr * self.atr[0]
                self.sell(exectype=bt.Order.Stop, price=stop_loss, parent=self.position)
                self.sell(exectype=bt.Order.Limit, price=take_profit, parent=self.position)

        # Short entry: Breakout below the lower box and the trend is down
        elif self.data.close[0] < lower_box and self.data.close[-1] >= lower_box and trend == 'down':
            if not self.position:
                self.sell(size=position_size)
                # Set stop loss and take profit based on ATR
                stop_loss = self.data.close[0] + self.params.stop_loss_atr * self.atr[0]
                take_profit = self.data.close[0] - self.params.take_profit_atr * self.atr[0]
                self.buy(exectype=bt.Order.Stop, price=stop_loss, parent=self.position)
                self.buy(exectype=bt.Order.Limit, price=take_profit, parent=self.position)
