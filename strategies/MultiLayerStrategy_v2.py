import backtrader as bt
import pandas_ta as ta
import pandas as pd
import datetime


class AdaptiveVWAP(bt.Indicator):
    lines = ('vwap',)
    params = (('base_period', 50), ('atr_multiplier', 2))

    def __init__(self):
        self.atr = bt.indicators.AverageTrueRange(self.data, period=14)
        self.adaptive_period = self.params.base_period
        self.cumsum_tp_vol = 0
        self.cumsum_vol = 0

    def next(self):
        self.adaptive_period = int(self.params.base_period + self.params.atr_multiplier * self.atr[0])
        typical_price = (self.data.high[0] + self.data.low[0] + self.data.close[0]) / 3
        self.cumsum_tp_vol += typical_price * self.data.volume[0]
        self.cumsum_vol += self.data.volume[0]

        if len(self.data) > self.adaptive_period:
            self.cumsum_tp_vol -= (self.data.high[-self.adaptive_period] +
                                   self.data.low[-self.adaptive_period] +
                                   self.data.close[-self.adaptive_period]) / 3 * self.data.volume[-self.adaptive_period]
            self.cumsum_vol -= self.data.volume[-self.adaptive_period]

        self.lines.vwap[0] = self.cumsum_tp_vol / self.cumsum_vol if self.cumsum_vol != 0 else 0


class MultiLayerStrategy_V2(bt.Strategy):
    params = (
        ('base_vwap_period', 100),
        ('atr_multiplier', 2),
        ('volume_sma_period', 10),
        ('pattern_3_rule_period', 3),
        ('atr_stop_multiplier', 1.5),
        ('atr_tp_multiplier', 2),
    )

    def __init__(self):
        self.vwap = AdaptiveVWAP(self.data, base_period=self.params.base_vwap_period, atr_multiplier=self.params.atr_multiplier)
        self.atr = bt.indicators.AverageTrueRange(self.data, period=14)
        self.volume_sma = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.params.volume_sma_period)
        self.rsi = bt.indicators.RSI(self.data.close, period=14)
        self.macd = bt.indicators.MACD(self.data.close)
        self.support_resistance_touches = []

    def next(self):
        price = self.data.close[0]
        volume = self.data.volume[0]

        # Convert Backtrader data to Pandas DataFrame
        df = self.data_to_pandas()

        # Generate candlestick pattern signals
        patterns = {
            'bullish_engulfing': ta.cdl_pattern(open_=df['open'], high=df['high'], low=df['low'], close=df['close'], name="engulfing"),
            'bearish_engulfing': ta.cdl_pattern(open_=df['open'], high=df['high'], low=df['low'], close=df['close'], name="engulfing", bear=True),
            'doji': ta.cdl_pattern(open_=df['open'], high=df['high'], low=df['low'], close=df['close'], name="doji"),
        }

        bullish_signal = patterns['bullish_engulfing'].iloc[-1] > 0
        bearish_signal = patterns['bearish_engulfing'].iloc[-1] < 0
        doji_signal = patterns['doji'].iloc[-1] > 0

        # Support and resistance logic
        support_resistance_level = self.data.close[-1]
        if price == support_resistance_level:
            self.support_resistance_touches.append(price)

        breakout_confirmed = len(self.support_resistance_touches) >= self.params.pattern_3_rule_period
        trend = 'bullish' if price > self.vwap[0] else 'bearish'

        # Volume and indicator confirmations
        volume_confirmed = volume > self.volume_sma[0]
        rsi_bullish = self.rsi[0] > 50
        macd_bullish = self.macd.macd[0] > self.macd.signal[0]

        # Stop loss and take profit
        stop_loss = price - self.params.atr_stop_multiplier * self.atr[0] if trend == 'bullish' else price + self.params.atr_stop_multiplier * self.atr[0]
        take_profit = price + self.params.atr_tp_multiplier * self.atr[0] if trend == 'bullish' else price - self.params.atr_tp_multiplier * self.atr[0]

        # Trading window (9 AM to 4 PM UTC)
        current_time = self.datas[0].datetime.datetime(0)
        start_time = datetime.time(9, 0)
        end_time = datetime.time(16, 0)

        if start_time <= current_time.time() <= end_time:
            if trend == 'bullish' and bullish_signal and rsi_bullish and macd_bullish and breakout_confirmed and volume_confirmed:
                if not self.position:
                    self.buy()
                    self.sell(exectype=bt.Order.Stop, price=stop_loss)
                    self.sell(exectype=bt.Order.Limit, price=take_profit)
            elif trend == 'bearish' and bearish_signal and breakout_confirmed and volume_confirmed:
                if not self.position:
                    self.sell()
                    self.buy(exectype=bt.Order.Stop, price=stop_loss)
                    self.buy(exectype=bt.Order.Limit, price=take_profit)

    def data_to_pandas(self):
        # Convert Backtrader data feed to Pandas DataFrame
        df = {
            'open': [self.data.open[i] for i in range(-len(self.data), 0)],
            'high': [self.data.high[i] for i in range(-len(self.data), 0)],
            'low': [self.data.low[i] for i in range(-len(self.data), 0)],
            'close': [self.data.close[i] for i in range(-len(self.data), 0)],
            'volume': [self.data.volume[i] for i in range(-len(self.data), 0)],
        }
        return pd.DataFrame(df)
