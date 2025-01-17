import backtrader as bt

class QuickFlipStrategy(bt.Strategy):
    params = (
        ('risk_appetite', 0.02),  # Risk per trade
        ('trade_fee', 0.001),  # Trading fee
        ('ema_short', 21),  # Short EMA period
        ('ema_long', 100),  # Long EMA period
        ('rsi_period', 10),  # RSI period
        ('rsi_overbought', 75),  # Overbought level
        ('rsi_oversold', 25),  # Oversold level
        ('atr_period', 20),  # ATR period
        ('volume_multiplier', 1.3),  # Multiplier for volume threshold
        ('trailing_atr_multiplier', 1.2),  # ATR multiplier for trailing stop
        ('min_atr_threshold', 0.5),  # Minimum ATR threshold for entry
        ('min_price_move', 0.005),  # Minimum price move (0.5%)
        ('min_time_between_trades', 6),  # Minimum time between trades (bars)
    )

    def __init__(self):
        # Indicators
        self.ema_short = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.params.ema_short)
        self.ema_long = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.params.ema_long)
        self.rsi = bt.indicators.RelativeStrengthIndex(self.data.close, period=self.params.rsi_period)
        self.atr = bt.indicators.AverageTrueRange(self.data, period=self.params.atr_period)
        self.avg_volume = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.params.ema_long)

        self.long_trail_stop = None  # For trailing stop-loss in long positions
        self.short_trail_stop = None  # For trailing stop-loss in short positions
        self.last_trade_time = None  # For time-based trade filtering

    def next(self):
        # Manage existing positions
        if self.position:
            if self.position.size > 0:  # Long position
                self.long_trail_stop = max(
                    self.long_trail_stop,
                    self.data.close[0] - self.params.trailing_atr_multiplier * self.atr[0]
                )
                if self.data.close[0] < self.long_trail_stop or self.data.close[0] < self.ema_short[0]:
                    self.close()
                    print(f"Long position closed at {self.data.close[0]}")
            elif self.position.size < 0:  # Short position
                self.short_trail_stop = min(
                    self.short_trail_stop,
                    self.data.close[0] + self.params.trailing_atr_multiplier * self.atr[0]
                )
                if self.data.close[0] > self.short_trail_stop or self.data.close[0] > self.ema_short[0]:
                    self.close()
                    print(f"Short position closed at {self.data.close[0]}")

        # Entry conditions
        if not self.position:
            # Long entry conditions
            long_trend_condition = self.data.close[0] > self.ema_short[0] and self.data.close[0] > self.ema_long[0]
            long_momentum_condition = self.params.rsi_oversold < self.rsi[0] < self.params.rsi_overbought
            long_volume_condition = self.data.volume[0] > self.params.volume_multiplier * self.avg_volume[0]
            long_atr_condition = self.atr[0] > self.params.min_atr_threshold
            long_price_move_condition = abs(self.data.close[0] - self.data.close[-1]) / self.data.close[-1] > self.params.min_price_move

            if long_trend_condition and long_momentum_condition and long_volume_condition and long_atr_condition and long_price_move_condition:
                self.buy_order()

            # Short entry conditions
            short_trend_condition = self.data.close[0] < self.ema_short[0] and self.data.close[0] < self.ema_long[0]
            short_momentum_condition = self.rsi[0] > self.params.rsi_overbought
            short_volume_condition = self.data.volume[0] > self.params.volume_multiplier * self.avg_volume[0]
            short_atr_condition = self.atr[0] > self.params.min_atr_threshold
            short_price_move_condition = abs(self.data.close[0] - self.data.close[-1]) / self.data.close[-1] > self.params.min_price_move

            if short_trend_condition and short_momentum_condition and short_volume_condition and short_atr_condition and short_price_move_condition:
                self.sell_order()

    def buy_order(self):
        # Calculate position size dynamically based on balance and risk appetite
        cash = self.broker.get_cash()
        position_size = cash * self.params.risk_appetite
        limit_price = self.data.close[0] * (1 + self.params.trade_fee)

        # Place a buy limit order
        self.buy(size=position_size / limit_price, price=limit_price, exectype=bt.Order.Limit)
        self.long_trail_stop = self.data.close[0] - self.params.trailing_atr_multiplier * self.atr[0]
        print(f"Long position opened at {limit_price}, size: {position_size / limit_price}")

    def sell_order(self):
        # Calculate position size dynamically based on balance and risk appetite
        cash = self.broker.get_cash()
        position_size = cash * self.params.risk_appetite
        limit_price = self.data.close[0] * (1 - self.params.trade_fee)

        # Place a sell limit order
        self.sell(size=position_size / limit_price, price=limit_price, exectype=bt.Order.Limit)
        self.short_trail_stop = self.data.close[0] + self.params.trailing_atr_multiplier * self.atr[0]
        print(f"Short position opened at {limit_price}, size: {position_size / limit_price}")
