import backtrader as bt

class QuickFlipStrategy(bt.Strategy):
    params = (
        ('risk_appetite', 0.1),  # Risk per trade
        ('trade_fee', 0.001),  # Trading fee
        ('ema_short', 21),  # Short EMA period
        ('ema_long', 50),  # Long EMA period
        ('rsi_period', 14),  # RSI period
        ('atr_period', 14),  # ATR period
        ('volume_multiplier', 1.5),  # Multiplier for volume threshold
    )

    def __init__(self):
        # Indicators
        self.ema_short = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.params.ema_short)
        self.ema_long = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.params.ema_long)
        self.rsi = bt.indicators.RelativeStrengthIndex(self.data.close, period=self.params.rsi_period)
        self.atr = bt.indicators.AverageTrueRange(self.data, period=self.params.atr_period)
        self.avg_volume = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.params.ema_long)

        self.order = None  # Track active orders

    def next(self):
        # Exit condition: Close long position if price drops below short EMA
        if self.position:
            if self.data.close[0] < self.ema_short[0]:
                self.close()
                print(f"Position closed at {self.data.close[0]}")

        # Entry condition: Check for buy signal
        if not self.position:
            # Trend: Price above both EMAs
            trend_condition = self.data.close[0] > self.ema_short[0] and self.data.close[0] > self.ema_long[0]
            # Momentum: RSI within range
            momentum_condition = 30 < self.rsi[0] < 70
            # Volume: Current volume exceeds threshold
            volume_condition = self.data.volume[0] > self.params.volume_multiplier * self.avg_volume[0]

            if trend_condition and momentum_condition and volume_condition:
                self.buy_order()

    def buy_order(self):
        # Calculate position size dynamically based on balance and risk appetite
        cash = self.broker.get_cash()
        position_size = cash * self.params.risk_appetite
        limit_price = self.data.close[0] * (1 + self.params.trade_fee)

        # Place a limit order
        self.order = self.buy(
            size=position_size / limit_price,
            price=limit_price,
            exectype=bt.Order.Limit
        )
        print(f"Buy order placed at {limit_price}, size: {position_size / limit_price}")

    def stop(self):
        # Print final portfolio value
        print(f"Final Portfolio Value: {self.broker.getvalue()}")
