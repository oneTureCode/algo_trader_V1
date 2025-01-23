# strategies/
import backtrader as bt
class SpotDayTradingStrategy(bt.Strategy):
    params = (
        ('ema_short_period', 30),
        ('ema_long_period', 75),
        ('rsi_period', 14),
        ('rsi_lower', 30),
        ('rsi_upper', 70),
        ('macd_fast', 15),
        ('macd_slow', 30),
        ('macd_signal', 10),
        ('stop_loss_atr', 1.2),  # ATR multiplier for stop-loss
        ('take_profit_atr', 2.0),  # ATR multiplier for take-profit
        ('trailing_stop_atr', 1.0),  # ATR multiplier for trailing stop-loss
        ('cooldown_period', 25),  # Minimum bars between trades
        ('max_hold_time', 12 * 60),  # Maximum hold time in minutes (12 hours)
        ('risk_per_trade', 0.02),  # Risk 2% of portfolio per trade
        ('volume_filter_period', 20),  # Period for volume moving average filter
        ('volatility_filter', True),  # Enable/disable volatility filter
        ('max_atr_threshold', 2.0),  # Max ATR threshold for volatility filter
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
        self.volume_sma = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.params.volume_filter_period)

        # Track the last trade bar index and trade entry time
        self.last_trade_bar = -self.params.cooldown_period
        self.entry_time = None
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.trailing_stop = None

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.date(0)
        print(f'{dt}, {txt}')

    def calculate_position_size(self):
        # Risk-based position sizing
        risk_amount = self.broker.getvalue() * self.params.risk_per_trade
        atr_risk = self.atr[0] * self.params.stop_loss_atr
        if atr_risk == 0:  # Avoid division by zero
            return 0
        position_size = risk_amount / atr_risk
        return position_size

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

        # Trade filtering: Avoid low-volume or high-volatility periods
        if self.data.volume[0] < self.volume_sma[0]:
            return
        if self.params.volatility_filter and self.atr[0] > self.params.max_atr_threshold:
            return

        if not self.position:
            # Long Entry conditions
            if (
                self.data.close[0] > self.ema_short[0] > self.ema_long[0] and
                self.rsi[0] > self.params.rsi_lower and
                self.macd.macd[0] > self.macd.signal[0] and
                self.macd.macd[0] > 0
            ):
                position_size = self.calculate_position_size()
                if position_size > 0:
                    self.buy(size=position_size)
                    self.entry_price = self.data.close[0]
                    self.entry_time = len(self.data)
                    self.last_trade_bar = len(self.data)
                    self.stop_loss = self.data.close[0] - (self.atr[0] * self.params.stop_loss_atr)
                    self.take_profit = self.data.close[0] + (self.atr[0] * self.params.take_profit_atr)
                    self.trailing_stop = self.stop_loss
                    self.log(f'BUY CREATE: {self.data.close[0]}')

            # Short Entry conditions
            elif (
                self.data.close[0] < self.ema_short[0] < self.ema_long[0] and
                self.rsi[0] < (100 - self.params.rsi_lower) and
                self.macd.macd[0] < self.macd.signal[0] and
                self.macd.macd[0] < 0
            ):
                position_size = self.calculate_position_size()
                if position_size > 0:
                    self.sell(size=position_size)
                    self.entry_price = self.data.close[0]
                    self.entry_time = len(self.data)
                    self.last_trade_bar = len(self.data)
                    self.stop_loss = self.data.close[0] + (self.atr[0] * self.params.stop_loss_atr)
                    self.take_profit = self.data.close[0] - (self.atr[0] * self.params.take_profit_atr)
                    self.trailing_stop = self.stop_loss
                    self.log(f'SELL CREATE: {self.data.close[0]}')
        else:
            # Update trailing stop-loss for Long positions
            if self.position.size > 0:
                self.trailing_stop = max(self.trailing_stop, self.data.close[0] - (self.atr[0] * self.params.trailing_stop_atr))

            # Update trailing stop-loss for Short positions
            elif self.position.size < 0:
                self.trailing_stop = min(self.trailing_stop, self.data.close[0] + (self.atr[0] * self.params.trailing_stop_atr))

            # Exit conditions
            if (
                (self.position.size > 0 and self.data.close[0] >= self.take_profit) or
                (self.position.size > 0 and self.data.close[0] <= self.trailing_stop) or
                (self.position.size < 0 and self.data.close[0] <= self.take_profit) or
                (self.position.size < 0 and self.data.close[0] >= self.trailing_stop)
            ):
                self.close()
                self.log(f'CLOSE POSITION: {self.data.close[0]}')
