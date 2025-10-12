"""
Freqtrade Adapter for Mean Reversion Strategy

This is a thin wrapper that adapts the Proratio MeanReversionStrategy
to work with Freqtrade's IStrategy interface.

Strategy: Mean reversion using RSI and Bollinger Bands with optional AI confirmation
Author: Proratio
"""

from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from typing import Optional

from proratio_tradehub.strategies import MeanReversionStrategy


class MeanReversionAdapter(IStrategy):
    """
    Freqtrade adapter for Proratio MeanReversionStrategy.

    Entry Logic:
    - Long: RSI < 30 AND price < BB_lower AND AI confirmation (optional)
    - Short: RSI > 70 AND price > BB_upper AND AI confirmation (optional)

    Exit Logic:
    - Price returns to mean (middle Bollinger Band)
    - RSI returns to neutral (40-60)
    - Stop-loss or take-profit hit

    Timeframes: Works best on 1h, 4h, 1d
    Markets: Best in ranging/sideways markets
    """

    # Strategy metadata
    INTERFACE_VERSION = 3

    # Optimal timeframe
    timeframe = "4h"

    # ROI table (take-profit levels)
    minimal_roi = {
        "0": 0.04,  # 4% take profit
        "60": 0.02,  # 2% after 1 hour
        "120": 0.01,  # 1% after 2 hours
    }

    # Stoploss
    stoploss = -0.02  # 2% stop-loss

    # Trailing stop
    trailing_stop = False

    # Run "populate_indicators" only for new candle
    process_only_new_candles = True

    # Strategy parameters (optimizable with hyperopt)
    rsi_oversold = IntParameter(20, 35, default=30, space="buy", optimize=True)
    rsi_overbought = IntParameter(65, 80, default=70, space="sell", optimize=True)
    bb_std = DecimalParameter(1.5, 2.5, default=2.0, space="buy", optimize=True)
    use_ai_confirmation = False  # Set to True to enable AI (requires API keys)
    ai_confidence_threshold = DecimalParameter(
        0.3, 0.7, default=0.5, space="buy", optimize=True
    )

    # Position size adjustment
    position_adjustment_enable = True

    def __init__(self, config: dict) -> None:
        """Initialize Freqtrade adapter"""
        super().__init__(config)

        # Initialize Proratio strategy
        self.strategy = MeanReversionStrategy(
            rsi_oversold=self.rsi_oversold.value,
            rsi_overbought=self.rsi_overbought.value,
            bb_std=self.bb_std.value,
            use_ai_confirmation=self.use_ai_confirmation,
            ai_confidence_threshold=self.ai_confidence_threshold.value,
        )

        print(f"✓ Initialized {self.strategy}")

    def populate_indicators(
        self, dataframe: pd.DataFrame, metadata: dict
    ) -> pd.DataFrame:
        """
        Add technical indicators required by mean reversion strategy.

        Args:
            dataframe: OHLCV data
            metadata: Pair metadata

        Returns:
            Dataframe with indicators added
        """
        # RSI (Relative Strength Index)
        dataframe["rsi"] = ta.rsi(dataframe["close"], length=14)

        # Bollinger Bands
        bb_length = 20
        bb_std = self.bb_std.value

        bollinger = ta.bbands(dataframe["close"], length=bb_length, std=bb_std)

        dataframe["bb_lower"] = bollinger[f"BBL_{bb_length}_{bb_std}"]
        dataframe["bb_middle"] = bollinger[f"BBM_{bb_length}_{bb_std}"]
        dataframe["bb_upper"] = bollinger[f"BBU_{bb_length}_{bb_std}"]

        # Volume moving average (for additional context)
        dataframe["volume_ma"] = ta.sma(dataframe["volume"], length=20)

        return dataframe

    def populate_entry_trend(
        self, dataframe: pd.DataFrame, metadata: dict
    ) -> pd.DataFrame:
        """
        Populate buy signals using mean reversion strategy.

        Args:
            dataframe: OHLCV data with indicators
            metadata: Pair metadata

        Returns:
            Dataframe with entry signals
        """
        # Initialize columns
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        # Check for long entry conditions (RSI < threshold AND price < BB_lower)
        long_conditions = (dataframe["rsi"] < self.rsi_oversold.value) & (
            dataframe["close"] < dataframe["bb_lower"]
        )

        # Mark all rows that meet the criteria
        dataframe.loc[long_conditions, "enter_long"] = 1
        dataframe.loc[long_conditions, "enter_tag"] = "mean_reversion_long"

        return dataframe

    def populate_exit_trend(
        self, dataframe: pd.DataFrame, metadata: dict
    ) -> pd.DataFrame:
        """
        Populate exit signals using mean reversion strategy.

        Args:
            dataframe: OHLCV data with indicators
            metadata: Pair metadata

        Returns:
            Dataframe with exit signals
        """
        # Initialize columns
        dataframe["exit_long"] = 0
        dataframe["exit_tag"] = ""

        # Exit when price returns to mean (middle Bollinger Band) or RSI neutralizes
        exit_conditions = (
            (dataframe["close"] >= dataframe["bb_middle"])  # Price returned to mean
            | (dataframe["rsi"] >= 50)  # RSI neutralized
        )

        # Mark all rows that meet exit criteria
        dataframe.loc[exit_conditions, "exit_long"] = 1
        dataframe.loc[exit_conditions, "exit_tag"] = "mean_reversion_exit"

        return dataframe

    def custom_exit(
        self,
        pair: str,
        trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> Optional[str]:
        """
        Custom exit logic using mean reversion strategy.

        Args:
            pair: Trading pair
            trade: Current trade object
            current_time: Current datetime
            current_rate: Current price
            current_profit: Current profit ratio
            **kwargs: Additional context

        Returns:
            Exit reason string or None
        """
        dataframe = kwargs.get("dataframe")

        if dataframe is None or dataframe.empty:
            return None

        # Build current position dict
        current_position = {
            "entry_price": trade.open_rate,
            "side": "long" if trade.is_short is False else "short",
            "current_price": current_rate,
            "profit": current_profit,
        }

        # Get exit signal from strategy
        exit_signal = self.strategy.should_exit(pair, dataframe, current_position)

        if exit_signal.direction == "exit":
            print(f"\n{'=' * 70}")
            print(f"EXIT SIGNAL: {pair}")
            print(f"{'=' * 70}")
            print(exit_signal.reasoning)
            print(f"Profit: {current_profit:+.2%}")
            print(f"{'=' * 70}\n")

            return "mean_reversion_exit"

        return None

    def custom_stake_amount(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_stake: float,
        min_stake: Optional[float],
        max_stake: float,
        leverage: float,
        entry_tag: Optional[str],
        side: str,
        **kwargs,
    ) -> float:
        """
        Adjust position size based on signal confidence.

        Higher confidence = larger position size.

        Args:
            pair: Trading pair
            proposed_stake: Freqtrade's proposed stake amount
            **kwargs: Additional context

        Returns:
            Adjusted stake amount
        """
        dataframe = kwargs.get("dataframe")

        if dataframe is None or dataframe.empty:
            return proposed_stake

        # Get signal confidence
        signal = self.strategy.should_enter_long(pair, dataframe)

        if signal.direction == "long":
            # Adjust stake by confidence (0.5 - 1.5x)
            multiplier = 0.5 + signal.confidence
            adjusted_stake = proposed_stake * multiplier

            # Ensure within limits
            if min_stake and adjusted_stake < min_stake:
                adjusted_stake = min_stake
            if adjusted_stake > max_stake:
                adjusted_stake = max_stake

            print(
                f"  Position sizing: {signal.confidence:.1%} confidence → {multiplier:.2f}x stake = ${adjusted_stake:.2f}"
            )

            return adjusted_stake

        return proposed_stake

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time: datetime,
        entry_tag: Optional[str],
        side: str,
        **kwargs,
    ) -> bool:
        """
        Confirm trade entry before execution.

        This is a final check before the order is placed.

        Args:
            pair: Trading pair
            rate: Entry price
            **kwargs: Additional context

        Returns:
            True to confirm, False to cancel
        """
        # Could add additional checks here (e.g., check account balance, market conditions)
        # For now, trust the strategy
        return True

    def leverage(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_leverage: float,
        max_leverage: float,
        entry_tag: Optional[str],
        side: str,
        **kwargs,
    ) -> float:
        """
        Set leverage for the trade.

        Mean reversion strategy uses 1x leverage (no leverage) by default.
        Override if you want to use leverage.

        Returns:
            Leverage multiplier
        """
        return 1.0  # No leverage
