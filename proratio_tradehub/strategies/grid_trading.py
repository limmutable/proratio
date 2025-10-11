"""
Grid Trading Strategy

Places multiple buy/sell orders at predetermined price levels (grids) to profit from
price volatility. Works best in ranging/sideways markets with high volatility.

Strategy Logic:
- Define grid levels above and below current price
- Place buy orders at lower grid levels
- Place sell orders at upper grid levels
- Profit from price oscillations between grids

Parameters:
- grid_spacing: Distance between grid levels (% of price)
- num_grids: Number of grid levels above and below center
- grid_type: 'arithmetic' (equal spacing) or 'geometric' (% spacing)

Best for: High volatility, ranging markets, sideways consolidation
Avoid: Strong trending markets (price may escape grid range)
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from proratio_tradehub.strategies.base_strategy import BaseStrategy, TradeSignal
from proratio_signals import SignalOrchestrator
from proratio_utilities.config.settings import get_settings


class GridTradingStrategy(BaseStrategy):
    """
    Grid trading strategy that profits from price oscillations.

    Creates a grid of buy and sell orders around current price.
    Buys at lower grids, sells at upper grids.

    Parameters:
    - grid_spacing: Percentage distance between grid levels (default: 2%)
    - num_grids_above: Number of sell grids above current price (default: 5)
    - num_grids_below: Number of buy grids below current price (default: 5)
    - grid_type: 'arithmetic' or 'geometric' spacing (default: 'geometric')
    - use_ai_volatility_check: Whether to use AI to confirm market is suitable (default: True)
    - min_volatility_threshold: Minimum ATR% to activate grid (default: 1.5%)
    """

    def __init__(
        self,
        name: str = "GridTrading",
        grid_spacing: float = 0.02,  # 2% spacing
        num_grids_above: int = 5,
        num_grids_below: int = 5,
        grid_type: str = "geometric",  # or "arithmetic"
        use_ai_volatility_check: bool = True,
        min_volatility_threshold: float = 0.015  # 1.5% ATR
    ):
        """
        Initialize Grid Trading Strategy.

        Args:
            name: Strategy name
            grid_spacing: Distance between grid levels (as decimal, e.g., 0.02 = 2%)
            num_grids_above: Number of sell grids above current price
            num_grids_below: Number of buy grids below current price
            grid_type: 'arithmetic' (equal $) or 'geometric' (equal %)
            use_ai_volatility_check: Use AI to confirm suitable market conditions
            min_volatility_threshold: Minimum volatility (ATR%) to activate
        """
        super().__init__(name)

        self.grid_spacing = grid_spacing
        self.num_grids_above = num_grids_above
        self.num_grids_below = num_grids_below
        self.grid_type = grid_type
        self.use_ai_volatility_check = use_ai_volatility_check
        self.min_volatility_threshold = min_volatility_threshold

        # Initialize AI orchestrator if needed
        self.orchestrator = None
        if self.use_ai_volatility_check:
            try:
                self.orchestrator = SignalOrchestrator()
            except Exception as e:
                print(f"Warning: Could not initialize AI orchestrator: {e}")
                self.use_ai_volatility_check = False

        # Grid state tracking
        self.grid_levels: Dict[str, List[float]] = {}  # pair -> list of grid prices
        self.grid_positions: Dict[str, Dict[float, bool]] = {}  # pair -> {price: is_filled}

        self.config = {
            'grid_spacing': grid_spacing,
            'num_grids_above': num_grids_above,
            'num_grids_below': num_grids_below,
            'grid_type': grid_type,
            'use_ai_volatility_check': use_ai_volatility_check,
            'min_volatility_threshold': min_volatility_threshold
        }

    def calculate_grid_levels(
        self,
        current_price: float,
        pair: str
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate grid levels above and below current price.

        Args:
            current_price: Current market price
            pair: Trading pair

        Returns:
            Tuple of (buy_levels, sell_levels) as lists of prices
        """
        buy_levels = []
        sell_levels = []

        if self.grid_type == "geometric":
            # Geometric progression (equal percentage spacing)
            for i in range(1, self.num_grids_below + 1):
                buy_price = current_price * (1 - self.grid_spacing * i)
                buy_levels.append(buy_price)

            for i in range(1, self.num_grids_above + 1):
                sell_price = current_price * (1 + self.grid_spacing * i)
                sell_levels.append(sell_price)

        elif self.grid_type == "arithmetic":
            # Arithmetic progression (equal dollar spacing)
            dollar_spacing = current_price * self.grid_spacing

            for i in range(1, self.num_grids_below + 1):
                buy_price = current_price - (dollar_spacing * i)
                buy_levels.append(buy_price)

            for i in range(1, self.num_grids_above + 1):
                sell_price = current_price + (dollar_spacing * i)
                sell_levels.append(sell_price)

        else:
            raise ValueError(f"Invalid grid_type: {self.grid_type}. Must be 'geometric' or 'arithmetic'.")

        # Store grid levels for this pair
        self.grid_levels[pair] = buy_levels + [current_price] + sell_levels

        # Initialize position tracking
        if pair not in self.grid_positions:
            self.grid_positions[pair] = {}

        for level in self.grid_levels[pair]:
            if level not in self.grid_positions[pair]:
                self.grid_positions[pair][level] = False

        return buy_levels, sell_levels

    def is_market_suitable_for_grid(
        self,
        pair: str,
        dataframe: pd.DataFrame
    ) -> Tuple[bool, str]:
        """
        Check if market conditions are suitable for grid trading.

        Suitable conditions:
        - High volatility (ATR% > threshold)
        - Ranging market (no strong trend)
        - AI confirms sideways movement (optional)

        Args:
            pair: Trading pair
            dataframe: OHLCV data with indicators

        Returns:
            Tuple of (is_suitable, reasoning)
        """
        current_price = dataframe['close'].iloc[-1]
        atr = dataframe['atr'].iloc[-1] if 'atr' in dataframe.columns else 0
        atr_pct = (atr / current_price) if current_price > 0 else 0

        # Check volatility
        if atr_pct < self.min_volatility_threshold:
            return False, f"Low volatility: ATR {atr_pct:.2%} < {self.min_volatility_threshold:.2%}"

        # Check if market is ranging (not trending)
        if 'ema_fast' in dataframe.columns and 'ema_slow' in dataframe.columns:
            ema_fast = dataframe['ema_fast'].iloc[-1]
            ema_slow = dataframe['ema_slow'].iloc[-1]
            ema_diff_pct = abs(ema_fast - ema_slow) / ema_slow

            # Strong trend if EMA difference > 3%
            if ema_diff_pct > 0.03:
                return False, f"Strong trend detected: EMA diff {ema_diff_pct:.2%} > 3%"

        # AI volatility check (optional)
        if self.use_ai_volatility_check and self.orchestrator:
            try:
                ai_signal = self.orchestrator.generate_signal(pair, dataframe)

                # Prefer neutral/sideways signals for grid trading
                if ai_signal.direction.lower() in ['long', 'short'] and ai_signal.confidence > 0.7:
                    return False, f"AI detects strong {ai_signal.direction} trend ({ai_signal.confidence:.1%})"

            except Exception as e:
                print(f"Warning: AI volatility check failed: {e}")

        return True, f"Market suitable: High volatility ({atr_pct:.2%}), ranging conditions"

    def should_enter_long(self, pair: str, dataframe: pd.DataFrame, **kwargs) -> TradeSignal:
        """
        Check if conditions are met for long entry (buy at grid level).

        Entry Conditions:
        1. Market is suitable for grid trading (volatility, ranging)
        2. Price has reached a buy grid level
        3. Grid level not already filled

        Args:
            pair: Trading pair
            dataframe: OHLCV data with indicators
            **kwargs: Additional context

        Returns:
            TradeSignal indicating whether to enter long
        """
        current_price = dataframe['close'].iloc[-1]

        # Check if market is suitable
        is_suitable, reasoning = self.is_market_suitable_for_grid(pair, dataframe)

        if not is_suitable:
            return TradeSignal(
                direction='neutral',
                confidence=0.0,
                reasoning=f"Grid Trading: {reasoning}"
            )

        # Calculate or retrieve grid levels
        if pair not in self.grid_levels:
            buy_levels, sell_levels = self.calculate_grid_levels(current_price, pair)
        else:
            buy_levels = [level for level in self.grid_levels[pair] if level < current_price]
            sell_levels = [level for level in self.grid_levels[pair] if level > current_price]

        # Check if price is at or below a buy grid level
        for buy_level in sorted(buy_levels, reverse=True):  # Check from highest to lowest
            price_diff_pct = abs(current_price - buy_level) / buy_level

            # Within 0.5% of grid level = trigger
            if price_diff_pct < 0.005:
                # Check if this grid level is already filled
                if not self.grid_positions[pair].get(buy_level, False):
                    # Calculate confidence based on grid position
                    # Lower grid levels (further from center) = higher confidence
                    grid_index = buy_levels.index(buy_level)
                    confidence = 0.5 + (grid_index / len(buy_levels)) * 0.4  # 0.5 to 0.9

                    reasoning_text = (
                        f"Grid Trading LONG entry:\n"
                        f"  Price ${current_price:.2f} at buy grid level ${buy_level:.2f}\n"
                        f"  Grid {grid_index + 1}/{len(buy_levels)} below center\n"
                        f"  {reasoning}"
                    )

                    return TradeSignal(
                        direction='long',
                        confidence=confidence,
                        entry_price=buy_level,
                        stop_loss=buy_levels[-1] * 0.98 if buy_levels else buy_level * 0.98,  # 2% below lowest grid
                        take_profit=sell_levels[0] if sell_levels else buy_level * (1 + self.grid_spacing),
                        position_size_multiplier=confidence,
                        reasoning=reasoning_text
                    )

        return TradeSignal(
            direction='neutral',
            confidence=0.0,
            reasoning=f"Grid Trading: Price ${current_price:.2f} not at any buy grid level"
        )

    def should_enter_short(self, pair: str, dataframe: pd.DataFrame, **kwargs) -> TradeSignal:
        """
        Check if conditions are met for short entry (sell at grid level).

        Note: For spot trading, this represents closing long positions.
        For futures, this represents opening short positions.

        Args:
            pair: Trading pair
            dataframe: OHLCV data with indicators
            **kwargs: Additional context

        Returns:
            TradeSignal indicating whether to enter short
        """
        # Grid trading on spot is primarily long-only (buy low, sell high)
        # Short entries would only be relevant for futures/margin trading
        return TradeSignal(
            direction='neutral',
            confidence=0.0,
            reasoning="Grid Trading: Short entries not implemented for spot trading"
        )

    def should_exit(
        self,
        pair: str,
        dataframe: pd.DataFrame,
        current_position: Dict,
        **kwargs
    ) -> TradeSignal:
        """
        Determine if strategy should exit current position.

        Exit Conditions:
        - Price reaches upper grid level (sell grid)
        - Market becomes unsuitable for grid trading (strong trend emerges)
        - Stop-loss or take-profit hit

        Args:
            pair: Trading pair
            dataframe: OHLCV data with indicators
            current_position: Current position details
            **kwargs: Additional context

        Returns:
            TradeSignal indicating whether to exit
        """
        current_price = dataframe['close'].iloc[-1]
        entry_price = current_position.get('entry_price')

        # Check if market is still suitable
        is_suitable, reasoning = self.is_market_suitable_for_grid(pair, dataframe)

        if not is_suitable:
            profit_pct = ((current_price - entry_price) / entry_price * 100) if entry_price else 0
            return TradeSignal(
                direction='exit',
                confidence=0.9,
                reasoning=f"Grid Trading EXIT: Market no longer suitable\n  {reasoning}\n  Current P&L: {profit_pct:+.2f}%"
            )

        # Get grid levels
        if pair in self.grid_levels:
            sell_levels = [level for level in self.grid_levels[pair] if level > entry_price]

            # Check if price reached a sell grid level
            for sell_level in sorted(sell_levels):
                price_diff_pct = abs(current_price - sell_level) / sell_level

                # Within 0.5% of sell grid = exit
                if price_diff_pct < 0.005:
                    profit_pct = ((current_price - entry_price) / entry_price * 100)

                    return TradeSignal(
                        direction='exit',
                        confidence=0.8,
                        reasoning=f"Grid Trading EXIT: Price ${current_price:.2f} at sell grid ${sell_level:.2f}\n  Profit: {profit_pct:+.2f}%"
                    )

        return TradeSignal(
            direction='neutral',
            confidence=0.0,
            reasoning=f"Grid Trading: Hold position (price ${current_price:.2f} between grids)"
        )

    def get_required_indicators(self) -> list:
        """
        Return list of required technical indicators.

        Returns:
            List of indicator names needed for this strategy
        """
        return [
            'atr',           # Average True Range (volatility)
            'ema_fast',      # Fast EMA (trend detection)
            'ema_slow',      # Slow EMA (trend detection)
        ]

    def __repr__(self) -> str:
        return (
            f"GridTradingStrategy("
            f"spacing={self.grid_spacing:.1%}, "
            f"grids={self.num_grids_below}+{self.num_grids_above}, "
            f"type={self.grid_type}, "
            f"volatility_check={self.use_ai_volatility_check})"
        )
