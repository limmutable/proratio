"""
Risk Management Module

Enforces risk controls and limits for trading strategies:
- Maximum loss per trade (2% of portfolio)
- Maximum total drawdown (10% → halt trading)
- Maximum concurrent positions (2-3)
- Position sizing based on risk
- Emergency stop mechanisms
"""

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class RiskStatus(Enum):
    """Risk status indicators"""

    NORMAL = "normal"  # Trading allowed
    WARNING = "warning"  # Approaching limits
    CRITICAL = "critical"  # Near emergency stop
    HALT = "halt"  # Trading halted


@dataclass
class RiskLimits:
    """Configurable risk limits"""

    # Per-trade limits
    max_loss_per_trade_pct: float = 2.0  # % of portfolio
    max_position_size_pct: float = 10.0  # % of portfolio

    # Portfolio limits
    max_total_drawdown_pct: float = 10.0  # Emergency stop
    warning_drawdown_pct: float = 7.0  # Warning threshold

    # Position limits
    max_concurrent_positions: int = 3
    max_positions_per_pair: int = 1

    # Leverage limits (for futures)
    max_leverage: float = 1.0  # Spot only = 1.0

    def __post_init__(self):
        """Validate limits"""
        if self.max_loss_per_trade_pct <= 0 or self.max_loss_per_trade_pct > 10:
            raise ValueError("max_loss_per_trade_pct must be between 0 and 10")
        if self.max_total_drawdown_pct <= 0 or self.max_total_drawdown_pct > 50:
            raise ValueError("max_total_drawdown_pct must be between 0 and 50")
        if self.max_concurrent_positions < 1:
            raise ValueError("max_concurrent_positions must be >= 1")


@dataclass
class PortfolioState:
    """Current portfolio state"""

    balance: float
    peak_balance: float
    open_positions: int
    position_pairs: List[str]
    unrealized_pnl: float = 0.0
    realized_pnl_today: float = 0.0

    @property
    def current_drawdown_pct(self) -> float:
        """Calculate current drawdown from peak"""
        if self.peak_balance <= 0:
            return 0.0
        return ((self.peak_balance - self.balance) / self.peak_balance) * 100

    @property
    def total_value(self) -> float:
        """Total portfolio value including unrealized P&L"""
        return self.balance + self.unrealized_pnl


class RiskManager:
    """
    Central risk management system.

    Enforces all risk limits and provides trade approval/rejection logic.
    """

    def __init__(self, limits: Optional[RiskLimits] = None):
        """
        Initialize risk manager.

        Args:
            limits: Custom risk limits (uses defaults if None)
        """
        self.limits = limits or RiskLimits()
        self.trading_halted = False
        self.halt_reason = ""
        self.warning_messages: List[str] = []

    def check_entry_allowed(
        self,
        pair: str,
        proposed_stake: float,
        portfolio: PortfolioState,
        stop_loss_pct: float,
    ) -> tuple[bool, str]:
        """
        Check if new entry is allowed.

        Args:
            pair: Trading pair
            proposed_stake: Proposed stake amount (USDT)
            portfolio: Current portfolio state
            stop_loss_pct: Stop-loss percentage (e.g., 5.0 for 5%)

        Returns:
            (allowed: bool, reason: str)
        """
        # Check if trading is halted
        if self.trading_halted:
            return False, f"Trading halted: {self.halt_reason}"

        # Check drawdown limit
        if portfolio.current_drawdown_pct >= self.limits.max_total_drawdown_pct:
            self.halt_trading(
                f"Max drawdown reached: {portfolio.current_drawdown_pct:.2f}%"
            )
            return (
                False,
                f"Emergency stop: Drawdown {portfolio.current_drawdown_pct:.2f}%",
            )

        # Check concurrent positions
        if portfolio.open_positions >= self.limits.max_concurrent_positions:
            return (
                False,
                f"Max concurrent positions ({self.limits.max_concurrent_positions}) reached",
            )

        # Check positions per pair
        if pair in portfolio.position_pairs:
            if (
                portfolio.position_pairs.count(pair)
                >= self.limits.max_positions_per_pair
            ):
                return (
                    False,
                    f"Max positions for {pair} ({self.limits.max_positions_per_pair}) reached",
                )

        # Check position size limit
        position_size_pct = (proposed_stake / portfolio.balance) * 100
        if position_size_pct > self.limits.max_position_size_pct:
            return (
                False,
                f"Position size {position_size_pct:.1f}% exceeds limit {self.limits.max_position_size_pct}%",
            )

        # Check risk per trade (stake * stop_loss%)
        max_loss = proposed_stake * (stop_loss_pct / 100)
        max_loss_pct = (max_loss / portfolio.balance) * 100

        if max_loss_pct > self.limits.max_loss_per_trade_pct:
            return (
                False,
                f"Risk {max_loss_pct:.2f}% exceeds limit {self.limits.max_loss_per_trade_pct}%",
            )

        # All checks passed
        return True, "Entry allowed"

    def calculate_max_stake(
        self, portfolio: PortfolioState, stop_loss_pct: float
    ) -> float:
        """
        Calculate maximum allowed stake based on risk limits.

        Args:
            portfolio: Current portfolio state
            stop_loss_pct: Stop-loss percentage

        Returns:
            Maximum stake amount (USDT)
        """
        # Calculate based on max loss per trade
        # max_loss = stake * stop_loss_pct
        # stake = max_loss / stop_loss_pct
        max_loss_amount = portfolio.balance * (self.limits.max_loss_per_trade_pct / 100)
        max_stake_from_risk = max_loss_amount / (stop_loss_pct / 100)

        # Calculate based on max position size
        max_stake_from_position = portfolio.balance * (
            self.limits.max_position_size_pct / 100
        )

        # Use the smaller of the two
        return min(max_stake_from_risk, max_stake_from_position)

    def get_risk_status(self, portfolio: PortfolioState) -> RiskStatus:
        """
        Get current risk status.

        Args:
            portfolio: Current portfolio state

        Returns:
            RiskStatus enum
        """
        if self.trading_halted:
            return RiskStatus.HALT

        drawdown = portfolio.current_drawdown_pct

        if drawdown >= self.limits.max_total_drawdown_pct:
            return RiskStatus.CRITICAL
        elif drawdown >= self.limits.warning_drawdown_pct:
            return RiskStatus.WARNING
        else:
            return RiskStatus.NORMAL

    def halt_trading(self, reason: str) -> None:
        """
        Emergency stop - halt all trading.

        Args:
            reason: Reason for halting
        """
        self.trading_halted = True
        self.halt_reason = reason
        print(f"\n{'=' * 80}")
        print("🚨 EMERGENCY STOP - TRADING HALTED")
        print(f"Reason: {reason}")
        print(f"Time: {datetime.now()}")
        print("=" * 80 + "\n")

    def resume_trading(self) -> None:
        """Resume trading after halt (manual override)"""
        self.trading_halted = False
        self.halt_reason = ""
        self.warning_messages.clear()
        print(f"\n✅ Trading resumed at {datetime.now()}\n")

    def add_warning(self, message: str) -> None:
        """Add warning message"""
        self.warning_messages.append(f"{datetime.now()}: {message}")

    def get_warnings(self) -> List[str]:
        """Get all warning messages"""
        return self.warning_messages.copy()

    def generate_report(self, portfolio: PortfolioState) -> str:
        """
        Generate risk management report.

        Args:
            portfolio: Current portfolio state

        Returns:
            Formatted report string
        """
        status = self.get_risk_status(portfolio)

        report = f"""
{"=" * 80}
RISK MANAGEMENT REPORT
{"=" * 80}
Generated: {datetime.now()}

Portfolio Status:
  Balance: ${portfolio.balance:,.2f}
  Peak Balance: ${portfolio.peak_balance:,.2f}
  Current Drawdown: {portfolio.current_drawdown_pct:.2f}%
  Open Positions: {portfolio.open_positions}/{self.limits.max_concurrent_positions}
  Unrealized P&L: ${portfolio.unrealized_pnl:+,.2f}

Risk Status: {status.value.upper()}
  {"✅ Normal operations" if status == RiskStatus.NORMAL else ""}
  {"⚠️  Approaching limits" if status == RiskStatus.WARNING else ""}
  {"🔴 Critical - Near emergency stop" if status == RiskStatus.CRITICAL else ""}
  {"🚨 TRADING HALTED" if status == RiskStatus.HALT else ""}

Risk Limits:
  Max Loss/Trade: {self.limits.max_loss_per_trade_pct}%
  Max Position Size: {self.limits.max_position_size_pct}%
  Max Drawdown: {self.limits.max_total_drawdown_pct}%
  Max Concurrent Positions: {self.limits.max_concurrent_positions}

Warnings ({len(self.warning_messages)}):
"""
        if self.warning_messages:
            for warning in self.warning_messages[-5:]:  # Last 5 warnings
                report += f"  - {warning}\n"
        else:
            report += "  None\n"

        if self.trading_halted:
            report += f"\n🚨 HALT REASON: {self.halt_reason}\n"

        report += "=" * 80 + "\n"

        return report


# Singleton instance
_risk_manager: Optional[RiskManager] = None


def get_risk_manager(limits: Optional[RiskLimits] = None) -> RiskManager:
    """
    Get singleton risk manager instance.

    Args:
        limits: Risk limits (only used on first call)

    Returns:
        RiskManager instance
    """
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = RiskManager(limits)
    return _risk_manager
