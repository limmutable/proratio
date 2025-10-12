"""
Grid Trading Strategy - Freqtrade Adapter

Places multiple buy/sell orders at predetermined price levels (grids) to profit from
price volatility. Works best in ranging/sideways markets with high volatility.

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

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class GridTradingStrategy(IStrategy):
    """
    Grid trading strategy that profits from price oscillations.

    Creates a grid of price levels and trades between them.
    Buys at lower grids, sells at upper grids.
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
        Initialize Grid Trading strategy.

        Args:
            config: Freqtrade configuration dict
        """
        super().__init__(config)

        # Grid state
        self.grid_levels: Dict[str, list] = {}  # pair -> list of grid prices
        self.grid_center: Dict[str, float] = {}  # pair -> center price

        print("✓ Grid Trading Strategy initialized")
        print(f"  Grid spacing: {self.grid_spacing:.1%}")
        print(f"  Grids: {self.num_grids_below} below + {self.num_grids_above} above")
        print(f"  Type: {self.grid_type}")

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

    def calculate_grid_levels(self, current_price: float, pair: str) -> tuple:
        """
        Calculate grid levels above and below current price.

        Args:
            current_price: Current market price
            pair: Trading pair

        Returns:
            Tuple of (buy_levels, sell_levels)
        """
        buy_levels = []
        sell_levels = []

        if self.grid_type == "geometric":
            # Geometric progression (equal percentage)
            for i in range(1, self.num_grids_below + 1):
                buy_levels.append(current_price * (1 - self.grid_spacing * i))

            for i in range(1, self.num_grids_above + 1):
                sell_levels.append(current_price * (1 + self.grid_spacing * i))
        else:
            # Arithmetic progression (equal dollar)
            dollar_spacing = current_price * self.grid_spacing

            for i in range(1, self.num_grids_below + 1):
                buy_levels.append(current_price - dollar_spacing * i)

            for i in range(1, self.num_grids_above + 1):
                sell_levels.append(current_price + dollar_spacing * i)

        # Store grid levels
        self.grid_levels[pair] = buy_levels + [current_price] + sell_levels
        self.grid_center[pair] = current_price

        return buy_levels, sell_levels

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
        current_price = dataframe["close"].iloc[-1]

        # Initialize grids if not exists
        if pair not in self.grid_levels:
            buy_levels, sell_levels = self.calculate_grid_levels(current_price, pair)
        else:
            buy_levels = [
                level
                for level in self.grid_levels[pair]
                if level < self.grid_center[pair]
            ]

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
