import backtrader as bt

class MultiLayerStrategy_V1(bt.Strategy):
    params = (
        ('vwap_period', 50),  # VWAP period
        ('volume_sma_period', 20),  # Volume SMA period
        ('rsi_period', 14),  # RSI period
        ('sma_period', 20),  # Simple Moving Average (SMA) period
        ('pattern_3_rule_period', 3),  # Pattern of 3 rule (support/resistance)
    )

    def __init__(self):
        # VWAP Indicator
        self.vwap = bt.indicators.VWAP(self.data, period=self.params.vwap_period)

        # Volume SMA for confirmation
        self.volume_sma = bt.indicators.SimpleMovingAverage(self.data.volume, period=self.params.volume_sma_period)

        # RSI for market conditions (oversold/overbought)
        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.params.rsi_period)

        # Simple Moving Average for trend confirmation
        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.sma_period)

        # Tracking the touches of support or resistance levels (Pattern of 3)
        self.support_resistance_touches = []
    
    def next(self):
        price = self.data.close[0]
        volume = self.data.volume[0]
        
        # Pattern of 3: Track Support/Resistance touches
        support_resistance_level = self.data.close[-1]  # Use the previous close as a reference level
        if price == support_resistance_level:
            self.support_resistance_touches.append(price)

        if len(self.support_resistance_touches) >= self.params.pattern_3_rule_period:
            breakout_confirmed = True
        else:
            breakout_confirmed = False

        # 1. VWAP as the Primary Trend Filter
        if price > self.vwap[0]:
            trend = 'bullish'
        else:
            trend = 'bearish'

        # 2. Price Patterns for Entries (e.g., triangle, double bottom, double top)
        if trend == 'bullish' and self.is_bullish_pattern():
            pattern_confirmed = True
        elif trend == 'bearish' and self.is_bearish_pattern():
            pattern_confirmed = True
        else:
            pattern_confirmed = False
        
        # 3. Volume Confirmation
        if volume > self.volume_sma[0]:
            volume_confirmed = True
        else:
            volume_confirmed = False

        # 4. Pattern of 3 Rule (Breakout Confirmation)
        if breakout_confirmed:
            pattern_of_3_confirmed = True
        else:
            pattern_of_3_confirmed = False

        # Entry Logic: All conditions met
        if trend == 'bullish' and pattern_confirmed and volume_confirmed and pattern_of_3_confirmed and self.rsi[0] < 30:
            if not self.position:
                self.buy()  # Execute Buy (Long) trade

        elif trend == 'bearish' and pattern_confirmed and volume_confirmed and pattern_of_3_confirmed and self.rsi[0] > 70:
            if not self.position:
                self.sell()  # Execute Sell (Short) trade

        # Exit Logic: If conditions reverse or price crosses VWAP
        if self.position:
            if trend == 'bearish' and price > self.vwap[0]:
                self.sell()  # Exit sell position if price moves above VWAP
            elif trend == 'bullish' and price < self.vwap[0]:
                self.sell()  # Exit buy position if price falls below VWAP

    def is_bullish_pattern(self):
        """ Check for bullish patterns like a breakout (e.g., double bottom, triangle breakout) """
        # Simplified pattern check: bullish engulfing as an example
        if len(self) >= 2:
            return self.data.close[0] > self.data.open[0] and self.data.close[-1] < self.data.open[-1]  # Bullish Engulfing Pattern
        return False
    
    def is_bearish_pattern(self):
        """ Check for bearish patterns like a breakdown (e.g., double top, triangle breakdown) """
        # Simplified pattern check: bearish engulfing as an example
        if len(self) >= 2:
            return self.data.close[0] < self.data.open[0] and self.data.close[-1] > self.data.open[-1]  # Bearish Engulfing Pattern
        return False
