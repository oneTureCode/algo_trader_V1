import backtrader as bt
import pandas_ta as ta
import pandas as pd

class MultiLayerStrategyWithPandasTA(bt.Strategy):
    params = (
        ('vwap_period', 50),  # VWAP period
        ('volume_sma_period', 20),  # Volume SMA period
        ('pattern_3_rule_period', 3),  # Pattern of 3 rule (support/resistance)
    )

    def __init__(self):
        # VWAP Indicator
        self.vwap = bt.indicators.VWAP(self.data, period=self.params.vwap_period)

        # Volume SMA for confirmation
        self.volume_sma = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.params.volume_sma_period)

        # Tracking support/resistance touches
        self.support_resistance_touches = []

    def next(self):
        price = self.data.close[0]
        volume = self.data.volume[0]

        # Convert Backtrader data to a Pandas DataFrame for pandas-ta
        df = self.data_to_pandas()
        
        # 1. Use pandas-ta for pattern recognition
        patterns = {
            'bullish_engulfing': ta.cdl_pattern(df, name="engulfing"),
            'bearish_engulfing': ta.cdl_pattern(df, name="engulfing", bear=True),
            'doji': ta.cdl_pattern(df, name="doji"),
        }

        bullish_signal = patterns['bullish_engulfing'].iloc[-1] > 0
        bearish_signal = patterns['bearish_engulfing'].iloc[-1] < 0
        doji_signal = patterns['doji'].iloc[-1] > 0

        # Pattern of 3: Track Support/Resistance touches
        support_resistance_level = self.data.close[-1]  # Previous close as reference
        if price == support_resistance_level:
            self.support_resistance_touches.append(price)

        if len(self.support_resistance_touches) >= self.params.pattern_3_rule_period:
            breakout_confirmed = True
        else:
            breakout_confirmed = False

        # 2. VWAP as the Primary Trend Filter
        if price > self.vwap[0]:
            trend = 'bullish'
        else:
            trend = 'bearish'

        # 3. Volume Confirmation
        volume_confirmed = volume > self.volume_sma[0]

        # Entry Logic: Combine signals
        if trend == 'bullish' and bullish_signal and breakout_confirmed and volume_confirmed:
            if not self.position:
                self.buy()
        elif trend == 'bearish' and bearish_signal and breakout_confirmed and volume_confirmed:
            if not self.position:
                self.sell()

        # Exit Logic: If VWAP direction changes
        if self.position:
            if trend == 'bearish' and price > self.vwap[0]:
                self.sell()
            elif trend == 'bullish' and price < self.vwap[0]:
                self.sell()

    def data_to_pandas(self):
        """
        Convert Backtrader data to a Pandas DataFrame for pandas-ta compatibility.
        """
        df = {
            'open': [self.data.open[i] for i in range(-len(self.data), 0)],
            'high': [self.data.high[i] for i in range(-len(self.data), 0)],
            'low': [self.data.low[i] for i in range(-len(self.data), 0)],
            'close': [self.data.close[i] for i in range(-len(self.data), 0)],
            'volume': [self.data.volume[i] for i in range(-len(self.data), 0)],
        }
        return pd.DataFrame(df)
