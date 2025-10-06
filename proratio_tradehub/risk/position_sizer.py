"""
Position Sizing Calculator

Implements various position sizing methods:
- Fixed fractional (% of portfolio)
- Kelly Criterion
- Risk-based (based on stop-loss distance)
- AI confidence-weighted
- ATR-based (volatility-adjusted)
"""

from typing import Optional
from enum import Enum
import math


class SizingMethod(Enum):
    """Position sizing methods"""
    FIXED_FRACTION = "fixed_fraction"      # Fixed % of portfolio
    RISK_BASED = "risk_based"              # Based on stop-loss risk
    KELLY = "kelly"                        # Kelly Criterion
    AI_WEIGHTED = "ai_weighted"            # AI confidence weighted
    ATR_BASED = "atr_based"                # Volatility-adjusted


class PositionSizer:
    """
    Position sizing calculator.

    Calculates optimal position size based on:
    - Portfolio balance
    - Risk tolerance
    - Market conditions
    - AI signals (optional)
    """

    def __init__(
        self,
        method: SizingMethod = SizingMethod.RISK_BASED,
        base_risk_pct: float = 2.0,
        max_position_pct: float = 10.0,
        min_position_pct: float = 1.0
    ):
        """
        Initialize position sizer.

        Args:
            method: Sizing method to use
            base_risk_pct: Base risk per trade (% of portfolio)
            max_position_pct: Maximum position size (% of portfolio)
            min_position_pct: Minimum position size (% of portfolio)
        """
        self.method = method
        self.base_risk_pct = base_risk_pct
        self.max_position_pct = max_position_pct
        self.min_position_pct = min_position_pct

    def calculate_position_size(
        self,
        balance: float,
        entry_price: float,
        stop_loss_price: float,
        ai_confidence: Optional[float] = None,
        atr: Optional[float] = None,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None
    ) -> float:
        """
        Calculate position size (in quote currency).

        Args:
            balance: Portfolio balance (USDT)
            entry_price: Entry price
            stop_loss_price: Stop-loss price
            ai_confidence: AI confidence score (0.0 - 1.0)
            atr: Average True Range (for volatility sizing)
            win_rate: Historical win rate (for Kelly)
            avg_win: Average win amount (for Kelly)
            avg_loss: Average loss amount (for Kelly)

        Returns:
            Position size in quote currency (USDT)
        """
        if self.method == SizingMethod.FIXED_FRACTION:
            return self._fixed_fraction(balance)

        elif self.method == SizingMethod.RISK_BASED:
            return self._risk_based(balance, entry_price, stop_loss_price)

        elif self.method == SizingMethod.KELLY:
            if win_rate is None or avg_win is None or avg_loss is None:
                # Fallback to risk-based if Kelly parameters missing
                return self._risk_based(balance, entry_price, stop_loss_price)
            return self._kelly(balance, win_rate, avg_win, avg_loss)

        elif self.method == SizingMethod.AI_WEIGHTED:
            base_size = self._risk_based(balance, entry_price, stop_loss_price)
            return self._ai_weighted(base_size, balance, ai_confidence)

        elif self.method == SizingMethod.ATR_BASED:
            if atr is None:
                # Fallback to risk-based
                return self._risk_based(balance, entry_price, stop_loss_price)
            return self._atr_based(balance, entry_price, atr)

        else:
            raise ValueError(f"Unknown sizing method: {self.method}")

    def _fixed_fraction(self, balance: float) -> float:
        """
        Fixed fractional sizing: Always use same % of portfolio.

        Args:
            balance: Portfolio balance

        Returns:
            Position size
        """
        return balance * (self.base_risk_pct / 100)

    def _risk_based(
        self,
        balance: float,
        entry_price: float,
        stop_loss_price: float
    ) -> float:
        """
        Risk-based sizing: Size position so stop-loss = fixed % of portfolio.

        Formula:
          position_size = (balance * risk_pct) / (entry_price - stop_loss_price) * entry_price

        Args:
            balance: Portfolio balance
            entry_price: Entry price
            stop_loss_price: Stop-loss price

        Returns:
            Position size
        """
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss_price)

        if risk_per_unit <= 0:
            raise ValueError("Invalid stop-loss: must be different from entry price")

        # Calculate position size
        risk_amount = balance * (self.base_risk_pct / 100)
        units = risk_amount / risk_per_unit
        position_size = units * entry_price

        # Apply min/max limits
        return self._apply_limits(position_size, balance)

    def _kelly(
        self,
        balance: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Kelly Criterion sizing.

        Formula:
          f = (W * B - L) / B
          where:
            W = win rate
            B = avg_win / avg_loss (payoff ratio)
            L = loss rate (1 - W)

        Uses half-Kelly to reduce volatility.

        Args:
            balance: Portfolio balance
            win_rate: Win rate (0.0 - 1.0)
            avg_win: Average win amount
            avg_loss: Average loss amount

        Returns:
            Position size
        """
        if avg_loss <= 0:
            raise ValueError("avg_loss must be positive")

        payoff_ratio = avg_win / abs(avg_loss)
        loss_rate = 1 - win_rate

        # Kelly %
        kelly_pct = (win_rate * payoff_ratio - loss_rate) / payoff_ratio

        # Use half-Kelly to reduce risk
        kelly_pct = kelly_pct * 0.5

        # Ensure positive and within limits
        kelly_pct = max(0, min(kelly_pct, self.max_position_pct / 100))

        position_size = balance * kelly_pct

        return self._apply_limits(position_size, balance)

    def _ai_weighted(
        self,
        base_size: float,
        balance: float,
        ai_confidence: Optional[float]
    ) -> float:
        """
        AI confidence-weighted sizing.

        Adjusts base size by AI confidence:
        - Low confidence (60%) → 0.8x base
        - Medium confidence (80%) → 1.0x base
        - High confidence (100%) → 1.2x base

        Args:
            base_size: Base position size
            balance: Portfolio balance
            ai_confidence: AI confidence (0.6 - 1.0)

        Returns:
            Adjusted position size
        """
        if ai_confidence is None:
            return base_size

        # Confidence must be >= 0.6 (60%) to trade
        min_confidence = 0.6
        if ai_confidence < min_confidence:
            return 0.0  # Don't trade

        # Scale confidence to multiplier range (0.8x - 1.2x)
        confidence_normalized = (ai_confidence - min_confidence) / (1.0 - min_confidence)
        multiplier = 0.8 + (confidence_normalized * 0.4)  # 0.8 to 1.2

        adjusted_size = base_size * multiplier

        return self._apply_limits(adjusted_size, balance)

    def _atr_based(
        self,
        balance: float,
        entry_price: float,
        atr: float,
        atr_multiplier: float = 2.0
    ) -> float:
        """
        ATR-based volatility sizing.

        Higher volatility → smaller position
        Lower volatility → larger position

        Stop-loss = entry - (ATR * multiplier)

        Args:
            balance: Portfolio balance
            entry_price: Entry price
            atr: Average True Range
            atr_multiplier: ATR multiplier for stop-loss distance

        Returns:
            Position size
        """
        # Calculate stop-loss based on ATR
        stop_loss_distance = atr * atr_multiplier
        stop_loss_price = entry_price - stop_loss_distance

        # Use risk-based sizing with ATR stop
        return self._risk_based(balance, entry_price, stop_loss_price)

    def _apply_limits(self, position_size: float, balance: float) -> float:
        """
        Apply min/max position size limits.

        Args:
            position_size: Calculated position size
            balance: Portfolio balance

        Returns:
            Position size within limits
        """
        min_size = balance * (self.min_position_pct / 100)
        max_size = balance * (self.max_position_pct / 100)

        return max(min_size, min(position_size, max_size))

    def calculate_units(
        self,
        position_size_usd: float,
        entry_price: float
    ) -> float:
        """
        Convert position size (USD) to units.

        Args:
            position_size_usd: Position size in quote currency (USDT)
            entry_price: Entry price

        Returns:
            Number of units to buy
        """
        return position_size_usd / entry_price

    def calculate_stop_loss_from_atr(
        self,
        entry_price: float,
        atr: float,
        direction: str = "long",
        atr_multiplier: float = 2.0
    ) -> float:
        """
        Calculate stop-loss price from ATR.

        Args:
            entry_price: Entry price
            atr: Average True Range
            direction: 'long' or 'short'
            atr_multiplier: ATR multiplier

        Returns:
            Stop-loss price
        """
        stop_distance = atr * atr_multiplier

        if direction.lower() == "long":
            return entry_price - stop_distance
        else:  # short
            return entry_price + stop_distance


def get_position_size_for_ai_strategy(
    balance: float,
    entry_price: float,
    stop_loss_price: float,
    ai_confidence: float,
    base_risk_pct: float = 2.0
) -> float:
    """
    Helper function for AI-enhanced strategies.

    Args:
        balance: Portfolio balance (USDT)
        entry_price: Entry price
        stop_loss_price: Stop-loss price
        ai_confidence: AI confidence (0.6 - 1.0)
        base_risk_pct: Base risk per trade (%)

    Returns:
        Position size in USDT
    """
    sizer = PositionSizer(
        method=SizingMethod.AI_WEIGHTED,
        base_risk_pct=base_risk_pct,
        max_position_pct=10.0,
        min_position_pct=1.0
    )

    return sizer.calculate_position_size(
        balance=balance,
        entry_price=entry_price,
        stop_loss_price=stop_loss_price,
        ai_confidence=ai_confidence
    )
