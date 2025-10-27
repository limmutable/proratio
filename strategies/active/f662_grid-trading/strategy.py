"""
Grid Trading Strategy - Freqtrade Adapter

This is a thin wrapper that adapts the Proratio GridTradingStrategy
to work with Freqtrade's IStrategy interface.

Strategy Logic:
- Define grid levels above and below current price
- Place buy orders at lower grid levels
- Place sell orders at upper grid levels
- Profit from price oscillations between grids

Best for: High volatility, ranging markets, sideways consolidation
Avoid: Strong trending markets (price may escape grid range)
"""

import sys
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

# Add project root to Python path for imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# These imports must come after path modification - ignore linting
import talib.abstract as ta  # noqa: E402
from freqtrade.strategy import IStrategy  # noqa: E402
from pandas import DataFrame  # noqa: E402
from proratio_tradehub.strategies import GridTradingStrategy  # noqa: E402


class GridTradingAdapter(IStrategy):
    """
    Freqtrade adapter for Proratio GridTradingStrategy.

    This is a thin wrapper that delegates core trading logic to the
    framework-agnostic GridTradingStrategy from proratio_tradehub.

    Entry Logic:
    - Long: High volatility + ranging market + price in lower range (RSI 25-45)
    
    Exit Logic:
    - Price reaches upper grid (RSI > 55 in upper range)
    - Strong trend emerges
    - Volatility drops

    Timeframes: Best on 1h
    Markets: High volatility, ranging/sideways markets
    """

    # Strategy metadata
    INTERFACE_VERSION = 3
    can_short = False  # Spot trading only

    # ROI table - Grid profits accumulate gradually
    minimal_roi = {
        "0": 0.03,  # 3% profit per grid level
        "30": 0.02,  # After 30 min, 2% profit
        "60": 0.01,  # After 60 min, 1% profit
    }

    # Stoploss - Below lowest grid level
    stoploss = -0.12  # 12% stop loss (5 grids x 2% + buffer)

    # No trailing stop for grid trading
    trailing_stop = False

    # Timeframe - Grid trading works on multiple timeframes
    timeframe = "1h"

    # Run "populate_indicators()" only for new candle
    process_only_new_candles = True

    # Startup candles
    startup_candle_count = 100

    # Optional order types
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    # Optional order time in force
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    # Grid parameters
    grid_spacing = 0.02  # 2% spacing between grids
    num_grids_above = 5
    num_grids_below = 5
    grid_type = "geometric"  # or "arithmetic"

    # Volatility parameters
    min_volatility_threshold = 0.015  # 1.5% ATR required
    max_trend_strength = 0.03  # 3% EMA diff = too strong trend

    def __init__(self, config: dict) -> None:
        """
        Initialize Grid Trading adapter.

        Args:
            config: Freqtrade configuration dict
        """
        super().__init__(config)

        # Initialize core strategy
        self.strategy = GridTradingStrategy(
            name="GridTrading",
            grid_spacing=self.grid_spacing,
            num_grids_above=self.num_grids_above,
            num_grids_below=self.num_grids_below,
            grid_type=self.grid_type,
            use_ai_volatility_check=False,  # Disable AI for now
            min_volatility_threshold=self.min_volatility_threshold,
        )

        print(f"✓ Initialized {self.strategy}")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Add technical indicators to the dataframe.

        Args:
            dataframe: Raw OHLCV data
            metadata: Strategy metadata (pair, timeframe, etc.)

        Returns:
            DataFrame with indicators added
        """
        # ATR - Average True Range (volatility)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]

        # EMAs for trend detection
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema_diff_pct"] = (
            abs(dataframe["ema_fast"] - dataframe["ema_slow"]) / dataframe["ema_slow"]
        )

        # RSI for additional context
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        # Volume
        dataframe["volume_mean"] = dataframe["volume"].rolling(window=20).mean()

        # Bollinger Bands for volatility context
        bollinger = ta.BBANDS(dataframe, timeperiod=20)
        dataframe["bb_upper"] = bollinger["upperband"]
        dataframe["bb_middle"] = bollinger["middleband"]
        dataframe["bb_lower"] = bollinger["lowerband"]
        dataframe["bb_width"] = (
            dataframe["bb_upper"] - dataframe["bb_lower"]
        ) / dataframe["bb_middle"]

        return dataframe



    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Define entry signals for grid trading.

        Entry conditions:
        1. High volatility (ATR% > threshold)
        2. Ranging market (no strong trend)
        3. Price at or below a buy grid level

        Args:
            dataframe: DataFrame with indicators
            metadata: Strategy metadata

        Returns:
            DataFrame with 'enter_long' column added
        """
        pair = metadata["pair"]
        
        # Initialize columns
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        # Market conditions suitable for grid trading
        market_conditions = (
            # High volatility
            (dataframe["atr_pct"] > self.min_volatility_threshold)
            &
            # Not strong trending
            (dataframe["ema_diff_pct"] < self.max_trend_strength)
            &
            # Sufficient volume
            (dataframe["volume"] > dataframe["volume_mean"] * 0.8)
        )

        # Check if price is at a buy grid level
        # Since we can't check future prices in Freqtrade, we check if RSI is oversold
        # and price is in lower half of BB (proxy for being at lower grid)
        grid_entry_conditions = (
            # Price in lower range
            (dataframe["close"] < dataframe["bb_middle"])
            &
            # RSI not extreme
            (dataframe["rsi"] > 25)
            & (dataframe["rsi"] < 45)
        )

        # Combine conditions
        dataframe.loc[market_conditions & grid_entry_conditions, "enter_long"] = 1
        dataframe.loc[market_conditions & grid_entry_conditions, "enter_tag"] = "grid_trading_long"

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Define exit signals for grid trading.

        Exit conditions:
        1. Price reaches upper grid (take profit)
        2. Market becomes trending (exit grid)
        3. Volatility drops (grid no longer profitable)

        Args:
            dataframe: DataFrame with indicators
            metadata: Strategy metadata

        Returns:
            DataFrame with 'exit_long' column added
        """
        # Initialize columns
        dataframe["exit_long"] = 0
        dataframe["exit_tag"] = ""
        
        # Exit conditions
        exit_conditions = (
            # Price in upper range (reached sell grid)
            ((dataframe["close"] > dataframe["bb_middle"]) & (dataframe["rsi"] > 55))
            |
            # Strong trend emerged (exit grid)
            (dataframe["ema_diff_pct"] > self.max_trend_strength)
            |
            # Volatility dropped (grid not profitable)
            (dataframe["atr_pct"] < self.min_volatility_threshold * 0.7)
        )

        dataframe.loc[exit_conditions, "exit_long"] = 1
        dataframe.loc[exit_conditions, "exit_tag"] = "grid_trading_exit"

        return dataframe

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
        Adjust position size for grid trading.

        Grid trading uses smaller position sizes since multiple orders are active.

        Args:
            pair: Trading pair
            proposed_stake: Base stake amount from config
            ... (other Freqtrade parameters)

        Returns:
            Adjusted stake amount
        """
        # Reduce stake per grid level (divide by number of grid levels)
        stake_per_grid = proposed_stake / self.num_grids_below

        # Ensure minimum stake
        if min_stake and stake_per_grid < min_stake:
            stake_per_grid = min_stake

        # Ensure maximum stake
        if stake_per_grid > max_stake:
            stake_per_grid = max_stake

        return stake_per_grid

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time,
        entry_tag,
        side: str,
        **kwargs,
    ) -> bool:
        """
        Final confirmation before entering trade.

        Returns:
            True to allow entry, False to reject
        """
        # Always allow entry for grid trading
        # Grid management is handled by position sizing
        return True
