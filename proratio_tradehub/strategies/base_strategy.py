"""
Base Strategy Class for Proratio Trading Strategies

Provides abstract interface for all trading strategies in the TradeHub module.
Strategies implement business logic that combines signals, technical indicators,
and risk management to generate trade recommendations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd


@dataclass
class TradeSignal:
    """Represents a trading signal with direction and metadata"""

    direction: str  # 'long', 'short', 'neutral'
    confidence: float  # 0.0 to 1.0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size_multiplier: float = 1.0  # Multiplier for base position size
    reasoning: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def should_trade(self, threshold: float = 0.5) -> bool:
        """Check if signal is strong enough to trade"""
        return self.direction != "neutral" and self.confidence >= threshold


class BaseStrategy(ABC):
    """
    Abstract base class for all Proratio trading strategies.

    Strategies should implement:
    - should_enter_long(): Entry logic for long positions
    - should_enter_short(): Entry logic for short positions
    - should_exit(): Exit logic for positions

    Optional:
    - calculate_position_size(): Custom position sizing
    - calculate_stop_loss(): Custom stop-loss logic
    - calculate_take_profit(): Custom take-profit logic
    """

    def __init__(self, name: str = None):
        """
        Initialize base strategy.

        Args:
            name: Strategy name (defaults to class name)
        """
        self.name = name or self.__class__.__name__
        self.config = {}

    @abstractmethod
    def should_enter_long(
        self, pair: str, dataframe: pd.DataFrame, **kwargs
    ) -> TradeSignal:
        """
        Determine if strategy should enter a long position.

        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            dataframe: OHLCV data with technical indicators
            **kwargs: Additional context (e.g., current position, account balance)

        Returns:
            TradeSignal with direction, confidence, and metadata
        """
        pass

    @abstractmethod
    def should_enter_short(
        self, pair: str, dataframe: pd.DataFrame, **kwargs
    ) -> TradeSignal:
        """
        Determine if strategy should enter a short position.

        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            dataframe: OHLCV data with technical indicators
            **kwargs: Additional context

        Returns:
            TradeSignal with direction, confidence, and metadata
        """
        pass

    @abstractmethod
    def should_exit(
        self, pair: str, dataframe: pd.DataFrame, current_position: Dict, **kwargs
    ) -> TradeSignal:
        """
        Determine if strategy should exit current position.

        Args:
            pair: Trading pair
            dataframe: OHLCV data with technical indicators
            current_position: Current position details (entry_price, side, etc.)
            **kwargs: Additional context

        Returns:
            TradeSignal indicating whether to exit
        """
        pass

    def calculate_position_size(
        self, pair: str, signal: TradeSignal, account_balance: float, **kwargs
    ) -> float:
        """
        Calculate position size for a trade.

        Default: Uses signal's position_size_multiplier on base stake.
        Override for custom position sizing logic.

        Args:
            pair: Trading pair
            signal: Trade signal
            account_balance: Current account balance
            **kwargs: Additional context

        Returns:
            Position size in quote currency (e.g., USDT)
        """
        base_stake = kwargs.get("base_stake", 100.0)
        return base_stake * signal.position_size_multiplier

    def calculate_stop_loss(
        self,
        pair: str,
        entry_price: float,
        side: str,
        dataframe: pd.DataFrame,
        **kwargs,
    ) -> Optional[float]:
        """
        Calculate stop-loss price.

        Default: 2% below entry for long, 2% above for short.
        Override for custom stop-loss logic (e.g., ATR-based, support/resistance).

        Args:
            pair: Trading pair
            entry_price: Entry price
            side: 'long' or 'short'
            dataframe: OHLCV data with indicators
            **kwargs: Additional context

        Returns:
            Stop-loss price or None
        """
        stop_loss_pct = kwargs.get("stop_loss_pct", 0.02)  # 2% default

        if side == "long":
            return entry_price * (1 - stop_loss_pct)
        elif side == "short":
            return entry_price * (1 + stop_loss_pct)
        return None

    def calculate_take_profit(
        self,
        pair: str,
        entry_price: float,
        side: str,
        dataframe: pd.DataFrame,
        **kwargs,
    ) -> Optional[float]:
        """
        Calculate take-profit price.

        Default: 4% above entry for long, 4% below for short (2:1 risk/reward).
        Override for custom take-profit logic.

        Args:
            pair: Trading pair
            entry_price: Entry price
            side: 'long' or 'short'
            dataframe: OHLCV data with indicators
            **kwargs: Additional context

        Returns:
            Take-profit price or None
        """
        take_profit_pct = kwargs.get("take_profit_pct", 0.04)  # 4% default

        if side == "long":
            return entry_price * (1 + take_profit_pct)
        elif side == "short":
            return entry_price * (1 - take_profit_pct)
        return None

    def get_required_indicators(self) -> list:
        """
        Return list of required technical indicators for this strategy.

        Override to specify indicators needed (e.g., ['rsi', 'ema_20', 'bb_lower']).

        Returns:
            List of indicator names
        """
        return []

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
