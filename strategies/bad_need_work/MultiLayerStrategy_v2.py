import backtrader as bt
import pandas as pd
import pandas_ta as ta

class MultiLayerStrategy_v2(bt.Strategy):
    params = (
        ('vwap_period', 50),  # VWAP period
        ('volume_sma_period', 20),  # Volume SMA period
        ('rsi_period', 14),  # RSI period
        ('sma_period', 20),  # Simple Moving Average (SMA) period
        ('pattern_3_rule_period', 3),  # Pattern of 3 rule (support/resistance)
        ('atr_stop_multiplier', 2),  # ATR multiplier for stop-loss
        ('atr_tp_multiplier', 3),  # ATR multiplier for take-profit
    )

    def __init__(self):
        # Initialize indicators and dataframes for Pandas TA
        self.dataframe = pd.DataFrame()
        self.support_resistance_touches = []

    def next(self):
        # Add current data to the dataframe
        row = {
            'open': self.data.open[0],
            'high': self.data.high[0],
            'low': self.data.low[0],
            'close': self.data.close[0],
            'volume': self.data.volume[0],
        }
        self.dataframe = pd.concat([self.dataframe, pd.DataFrame([row])], ignore_index=True)

        # Calculate indicators using Pandas TA
        if len(self.dataframe) > self.params.vwap_period:
            self.dataframe['VWAP'] = ta.vwap(
                high=self.dataframe['high'],
                low=self.dataframe['low'],
                close=self.dataframe['close'],
                volume=self.dataframe['volume'],
                length=self.params.vwap_period
            )
            self.dataframe['RSI'] = ta.rsi(self.dataframe['close'], length=self.params.rsi_period)
            self.dataframe['VolumeSMA'] = ta.sma(self.dataframe['volume'], length=self.params.volume_sma_period)
            self.dataframe['ATR'] = ta.atr(
                high=self.dataframe['high'],
                low=self.dataframe['low'],
                close=self.dataframe['close']
            )

            # Add candlestick patterns
            self.dataframe['BullishEngulfing'] = ta.cdl_pattern(
                self.dataframe['open'], self.dataframe['high'], self.dataframe['low'], self.dataframe['close'], pattern="bullish_engulfing"
            )
            self.dataframe['BearishEngulfing'] = ta.cdl_pattern(
                self.dataframe['open'], self.dataframe['high'], self.dataframe['low'], self.dataframe['close'], pattern="bearish_engulfing"
            )

            # Get the latest calculated values
            latest = self.dataframe.iloc[-1]
            vwap = latest['VWAP']
            rsi = latest['RSI']
            volume_sma = latest['VolumeSMA']
            atr = latest['ATR']
            bullish_engulfing = latest['BullishEngulfing']
            bearish_engulfing = latest['BearishEngulfing']

            # Pattern of 3: Support/Resistance touches
            price = self.data.close[0]
            support_resistance_level = self.data.close[-1]
            if price == support_resistance_level:
                self.support_resistance_touches.append(price)

            breakout_confirmed = len(self.support_resistance_touches) >= self.params.pattern_3_rule_period

            # Determine trend using VWAP
            trend = 'bullish' if price > vwap else 'bearish'

            # Confirm price patterns
            pattern_confirmed = False
            if trend == 'bullish' and bullish_engulfing:
                pattern_confirmed = True
            elif trend == 'bearish' and bearish_engulfing:
                pattern_confirmed = True

            # Confirm volume
            volume_confirmed = self.data.volume[0] > volume_sma

            # Entry conditions
            if trend == 'bullish' and pattern_confirmed and volume_confirmed and breakout_confirmed and rsi < 30:
                if not self.position:
                    self.buy()
                    self.set_stop_loss_and_tp(price, trend, atr)

            elif trend == 'bearish' and pattern_confirmed and volume_confirmed and breakout_confirmed and rsi > 70:
                if not self.position:
                    self.sell()
                    self.set_stop_loss_and_tp(price, trend, atr)

            # Exit conditions
            if self.position:
                if trend == 'bearish' and price > vwap:
                    self.close()  # Exit sell position if price moves above VWAP
                elif trend == 'bullish' and price < vwap:
                    self.close()  # Exit buy position if price falls below VWAP

    def set_stop_loss_and_tp(self, entry_price, trend, atr):
        """ Set dynamic stop-loss and take-profit levels based on ATR """
        if trend == 'bullish':
            stop_loss = entry_price - self.params.atr_stop_multiplier * atr
            take_profit = entry_price + self.params.atr_tp_multiplier * atr
        else:
            stop_loss = entry_price + self.params.atr_stop_multiplier * atr
            take_profit = entry_price - self.params.atr_tp_multiplier * atr

        # Place stop-loss and take-profit orders
        if trend == 'bullish':
            self.sell(exectype=bt.Order.Stop, price=stop_loss)
            self.sell(exectype=bt.Order.Limit, price=take_profit)
        else:
            self.buy(exectype=bt.Order.Stop, price=stop_loss)
            self.buy(exectype=bt.Order.Limit, price=take_profit)
