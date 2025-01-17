import backtrader as bt

class SpotDayTradingStrategy(bt.Strategy):
    params = (
        ('ema_short_period', 21),
        ('ema_long_period', 50),
        ('rsi_period', 9),
        ('rsi_lower', 25),
        ('rsi_upper', 75),
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
        ('stop_loss_atr', 1.5),  # ATR multiplier for stop-loss
        ('take_profit_atr', 3.0),  # ATR multiplier for take-profit
        ('cooldown_period', 15),  # Minimum bars between trades
        ('max_hold_time', 23 * 60),  # Maximum hold time in minutes (23 hours)
    )

    def __init__(self):
        # Indicators
        self.ema_short = bt.indicators.EMA(self.data.close, period=self.params.ema_short_period)
        self.ema_long = bt.indicators.EMA(self.data.close, period=self.params.ema_long_period)
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal
        )
        self.atr = bt.indicators.ATR(self.data, period=14)  # ATR for dynamic risk management

        # Track the last trade bar index and trade entry time
        self.last_trade_bar = -self.params.cooldown_period
        self.entry_time = None

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.date(0)
        print(f'{dt}, {txt}')

    def next(self):
        # Ensure cooldown period has passed
        if len(self.data) - self.last_trade_bar < self.params.cooldown_period:
            return

        # Check for maximum hold time
        if self.position and self.entry_time:
            hold_time = (len(self.data) - self.entry_time) * self.data._timeframe
            if hold_time >= self.params.max_hold_time:
                self.close()
                self.log(f'CLOSE DUE TO MAX HOLD TIME: {self.data.close[0]}')
                return

        if not self.position:
            # Long Entry conditions
            if (
                self.data.close[0] > self.ema_short[0] > self.ema_long[0] and
                self.rsi[0] > self.params.rsi_lower and
                self.macd.macd[0] > self.macd.signal[0] and
                self.macd.macd[0] > 0
            ):
                self.buy()
                self.entry_price = self.data.close[0]
                self.entry_time = len(self.data)
                self.last_trade_bar = len(self.data)
                self.stop_loss = self.data.close[0] - (self.atr[0] * self.params.stop_loss_atr)
                self.take_profit = self.data.close[0] + (self.atr[0] * self.params.take_profit_atr)
                self.log(f'BUY CREATE: {self.data.close[0]}')

            # Short Entry conditions
            elif (
                self.data.close[0] < self.ema_short[0] < self.ema_long[0] and
                self.rsi[0] < (100 - self.params.rsi_lower) and
                self.macd.macd[0] < self.macd.signal[0] and
                self.macd.macd[0] < 0
            ):
                self.sell()
                self.entry_price = self.data.close[0]
                self.entry_time = len(self.data)
                self.last_trade_bar = len(self.data)
                self.stop_loss = self.data.close[0] + (self.atr[0] * self.params.stop_loss_atr)
                self.take_profit = self.data.close[0] - (self.atr[0] * self.params.take_profit_atr)
                self.log(f'SELL CREATE: {self.data.close[0]}')
        else:
            # Exit conditions for Long
            if self.position.size > 0 and (
                self.rsi[0] > self.params.rsi_upper or
                self.macd.macd[0] < self.macd.signal[0] or
                self.data.close[0] <= self.stop_loss or
                self.data.close[0] >= self.take_profit
            ):
                self.close()
                self.entry_time = None
                self.log(f'CLOSE LONG: {self.data.close[0]}')

            # Exit conditions for Short
            elif self.position.size < 0 and (
                self.rsi[0] < (100 - self.params.rsi_upper) or
                self.macd.macd[0] > self.macd.signal[0] or
                self.data.close[0] >= self.stop_loss or
                self.data.close[0] <= self.take_profit
            ):
                self.close()
                self.entry_time = None
                self.log(f'CLOSE SHORT: {self.data.close[0]}')