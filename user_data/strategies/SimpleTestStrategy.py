"""
Simple Test Strategy for Week 1 - Freqtrade Integration Test

A basic trend-following strategy using EMA crossover for testing the
Freqtrade integration without AI signals (AI integration comes in Week 2).

Strategy Logic:
- Entry: Fast EMA crosses above Slow EMA (bullish trend)
- Exit: Fast EMA crosses below Slow EMA (bearish trend)
- Indicators: EMA-20 (fast), EMA-50 (slow), RSI-14

This is a proof-of-concept strategy for testing paper trading.
DO NOT use in live trading without proper backtesting!
"""

import talib.abstract as ta
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
from pandas import DataFrame


class SimpleTestStrategy(IStrategy):
    """
    Simple EMA crossover strategy for testing Freqtrade integration.
    """

    # Strategy metadata
    INTERFACE_VERSION = 3
    can_short = False  # Spot trading only (no shorting)

    # ROI table (take profit levels)
    minimal_roi = {
        "0": 0.10,   # 10% profit → exit
        "30": 0.05,  # After 30 min, 5% profit → exit
        "60": 0.02,  # After 60 min, 2% profit → exit
    }

    # Stoploss
    stoploss = -0.05  # 5% stop loss

    # Trailing stop
    trailing_stop = True
    trailing_stop_positive = 0.01  # Activate trailing at 1% profit
    trailing_stop_positive_offset = 0.02  # Trail after 2% profit
    trailing_only_offset_is_reached = True

    # Timeframe
    timeframe = '1h'

    # Run "populate_indicators()" only for new candle
    process_only_new_candles = True

    # Startup candles (for indicator calculation)
    startup_candle_count = 50

    # Optional order types
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force
    order_time_in_force = {
        'entry': 'GTC',
        'exit': 'GTC'
    }

    # Hyperopt parameters (for optimization later)
    fast_ema = IntParameter(10, 30, default=20, space='buy')
    slow_ema = IntParameter(40, 70, default=50, space='buy')
    rsi_buy_threshold = IntParameter(20, 50, default=30, space='buy')
    rsi_sell_threshold = IntParameter(50, 80, default=70, space='sell')

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Add indicators to the dataframe.

        Args:
            dataframe: Raw OHLCV data
            metadata: Strategy metadata (pair, timeframe, etc.)

        Returns:
            DataFrame with indicators added
        """
        # EMA indicators
        dataframe['ema_fast'] = ta.EMA(dataframe, timeperiod=self.fast_ema.value)
        dataframe['ema_slow'] = ta.EMA(dataframe, timeperiod=self.slow_ema.value)

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        # Volume
        dataframe['volume_mean'] = dataframe['volume'].rolling(window=20).mean()

        # For debugging (optional)
        print(f"[{metadata['pair']}] Indicators populated for {len(dataframe)} candles")

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Define entry (buy) signals.

        Args:
            dataframe: DataFrame with indicators
            metadata: Strategy metadata

        Returns:
            DataFrame with 'enter_long' column added
        """
        dataframe.loc[
            (
                # EMA crossover: fast crosses above slow
                (dataframe['ema_fast'] > dataframe['ema_slow']) &
                (dataframe['ema_fast'].shift(1) <= dataframe['ema_slow'].shift(1)) &

                # RSI not overbought
                (dataframe['rsi'] > self.rsi_buy_threshold.value) &
                (dataframe['rsi'] < 70) &

                # Volume confirmation
                (dataframe['volume'] > dataframe['volume_mean'])
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Define exit (sell) signals.

        Args:
            dataframe: DataFrame with indicators
            metadata: Strategy metadata

        Returns:
            DataFrame with 'exit_long' column added
        """
        dataframe.loc[
            (
                # EMA crossover: fast crosses below slow
                (dataframe['ema_fast'] < dataframe['ema_slow']) &
                (dataframe['ema_fast'].shift(1) >= dataframe['ema_slow'].shift(1))
            ) |
            (
                # RSI overbought
                (dataframe['rsi'] > self.rsi_sell_threshold.value)
            ),
            'exit_long'] = 1

        return dataframe

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float,
                           rate: float, time_in_force: str, current_time,
                           entry_tag, side: str, **kwargs) -> bool:
        """
        Optional: Confirm trade entry before execution.
        Can be used to add additional checks.

        Returns:
            True to allow entry, False to reject
        """
        # For Week 1, allow all entries (no additional filtering)
        return True

    def confirm_trade_exit(self, pair: str, trade, order_type: str, amount: float,
                          rate: float, time_in_force: str, exit_reason: str,
                          current_time, **kwargs) -> bool:
        """
        Optional: Confirm trade exit before execution.

        Returns:
            True to allow exit, False to reject
        """
        # For Week 1, allow all exits
        return True
