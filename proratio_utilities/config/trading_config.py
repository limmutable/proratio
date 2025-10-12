"""
Centralized Trading Configuration

Single source of truth for all trading variables:
- Risk management parameters
- Position sizing settings
- Strategy parameters
- AI confidence thresholds
- Execution settings

Modify this file to adjust trading behavior across the entire system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import json


@dataclass
class RiskConfig:
    """Risk management configuration"""

    # Per-trade risk limits
    max_loss_per_trade_pct: float = 2.0  # Maximum loss per trade (% of portfolio)
    max_position_size_pct: float = 10.0  # Maximum position size (% of portfolio)
    min_position_size_pct: float = 1.0  # Minimum position size (% of portfolio)

    # Portfolio-level limits
    max_total_drawdown_pct: float = 10.0  # Emergency stop threshold
    warning_drawdown_pct: float = 7.0  # Warning threshold

    # Position limits
    max_concurrent_positions: int = 3  # Maximum open positions
    max_positions_per_pair: int = 1  # Max positions per trading pair

    # Leverage (1.0 = spot only, >1.0 = futures/margin)
    max_leverage: float = 1.0


@dataclass
class PositionSizingConfig:
    """Position sizing configuration"""

    # Sizing method: 'fixed_fraction', 'risk_based', 'kelly', 'ai_weighted', 'atr_based'
    method: str = "ai_weighted"

    # Base risk percentage (used by most methods)
    base_risk_pct: float = 2.0

    # AI confidence multipliers
    ai_confidence_min: float = 0.60  # Minimum AI confidence to trade
    ai_confidence_multiplier_min: float = (
        0.8  # Stake multiplier at min confidence (60%)
    )
    ai_confidence_multiplier_max: float = (
        1.2  # Stake multiplier at max confidence (100%)
    )

    # ATR settings (for volatility-based sizing)
    atr_period: int = 14  # ATR calculation period
    atr_multiplier: float = 2.0  # ATR multiplier for stop-loss

    # Kelly Criterion settings
    kelly_fraction: float = 0.5  # Use half-Kelly for safety


@dataclass
class StrategyConfig:
    """Strategy-specific configuration"""

    # Strategy selection
    strategy_name: str = (
        "AIEnhancedStrategy"  # SimpleTestStrategy or AIEnhancedStrategy
    )

    # Timeframe
    timeframe: str = "1h"  # 1h, 4h, 1d

    # Trading pairs
    pairs: List[str] = field(default_factory=lambda: ["BTC/USDT", "ETH/USDT"])

    # Technical indicators
    ema_fast_period: int = 20
    ema_slow_period: int = 50
    rsi_period: int = 14
    rsi_buy_threshold: int = 30
    rsi_sell_threshold: int = 70
    atr_period: int = 14
    adx_period: int = 14
    adx_trend_threshold: float = 20.0  # ADX > 20 = trending market

    # ROI (take profit) levels
    roi_levels: Dict[str, float] = field(
        default_factory=lambda: {
            "0": 0.15,  # 15% profit → exit immediately
            "60": 0.08,  # After 60 min, 8% profit → exit
            "120": 0.04,  # After 120 min, 4% profit → exit
        }
    )

    # Stop-loss
    stoploss_pct: float = -0.04  # 4% stop-loss

    # Trailing stop
    trailing_stop_enabled: bool = True
    trailing_stop_positive: float = 0.015  # Activate at 1.5% profit
    trailing_stop_positive_offset: float = 0.025  # Trail after 2.5% profit

    # Volume confirmation
    volume_min_multiplier: float = 1.0  # Entry requires volume > X * average


@dataclass
class AIConfig:
    """AI signal generation configuration"""

    # Provider weights (must sum to 1.0)
    chatgpt_weight: float = 0.40  # Technical analysis
    claude_weight: float = 0.35  # Risk assessment
    gemini_weight: float = 0.25  # Sentiment

    # Consensus requirements
    min_consensus_score: float = 0.60  # Minimum weighted consensus
    min_confidence: float = 0.60  # Minimum AI confidence to trade
    require_all_providers: bool = False  # If True, all 3 must respond

    # Signal caching
    signal_cache_minutes: int = 60  # Cache signals for X minutes

    # AI context
    lookback_candles: int = 50  # Candles to send to AI

    # Model selection (auto-detected if None)
    chatgpt_model: Optional[str] = None  # e.g., 'gpt-5-nano-2025-08-07'
    claude_model: Optional[str] = None  # e.g., 'claude-sonnet-4-20250514'
    gemini_model: Optional[str] = None  # e.g., 'gemini-2.0-flash'


@dataclass
class ExecutionConfig:
    """Order execution configuration"""

    # Trading mode: 'dry_run' or 'live'
    trading_mode: str = "dry_run"

    # Exchange
    exchange: str = "binance"

    # Order types
    entry_order_type: str = "limit"  # limit or market
    exit_order_type: str = "limit"
    stoploss_order_type: str = "market"
    stoploss_on_exchange: bool = False

    # Order timing
    order_time_in_force: str = "GTC"  # GTC (good-til-cancel) or IOC

    # Starting balance
    starting_balance: float = 10000.0  # USDT
    stake_currency: str = "USDT"
    stake_amount: float = 100.0  # Base stake per trade


@dataclass
class TradingConfig:
    """
    Master trading configuration.

    Single source of truth for all trading parameters.
    """

    risk: RiskConfig = field(default_factory=RiskConfig)
    position_sizing: PositionSizingConfig = field(default_factory=PositionSizingConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)

    @classmethod
    def load_from_file(cls, filepath: Path) -> "TradingConfig":
        """
        Load configuration from JSON file.

        Args:
            filepath: Path to config JSON file

        Returns:
            TradingConfig instance
        """
        with open(filepath, "r") as f:
            data = json.load(f)

        return cls(
            risk=RiskConfig(**data.get("risk", {})),
            position_sizing=PositionSizingConfig(**data.get("position_sizing", {})),
            strategy=StrategyConfig(**data.get("strategy", {})),
            ai=AIConfig(**data.get("ai", {})),
            execution=ExecutionConfig(**data.get("execution", {})),
        )

    def save_to_file(self, filepath: Path) -> None:
        """
        Save configuration to JSON file.

        Args:
            filepath: Path to save config JSON
        """
        data = {
            "risk": {
                "max_loss_per_trade_pct": self.risk.max_loss_per_trade_pct,
                "max_position_size_pct": self.risk.max_position_size_pct,
                "min_position_size_pct": self.risk.min_position_size_pct,
                "max_total_drawdown_pct": self.risk.max_total_drawdown_pct,
                "warning_drawdown_pct": self.risk.warning_drawdown_pct,
                "max_concurrent_positions": self.risk.max_concurrent_positions,
                "max_positions_per_pair": self.risk.max_positions_per_pair,
                "max_leverage": self.risk.max_leverage,
            },
            "position_sizing": {
                "method": self.position_sizing.method,
                "base_risk_pct": self.position_sizing.base_risk_pct,
                "ai_confidence_min": self.position_sizing.ai_confidence_min,
                "ai_confidence_multiplier_min": self.position_sizing.ai_confidence_multiplier_min,
                "ai_confidence_multiplier_max": self.position_sizing.ai_confidence_multiplier_max,
                "atr_period": self.position_sizing.atr_period,
                "atr_multiplier": self.position_sizing.atr_multiplier,
                "kelly_fraction": self.position_sizing.kelly_fraction,
            },
            "strategy": {
                "strategy_name": self.strategy.strategy_name,
                "timeframe": self.strategy.timeframe,
                "pairs": self.strategy.pairs,
                "ema_fast_period": self.strategy.ema_fast_period,
                "ema_slow_period": self.strategy.ema_slow_period,
                "rsi_period": self.strategy.rsi_period,
                "rsi_buy_threshold": self.strategy.rsi_buy_threshold,
                "rsi_sell_threshold": self.strategy.rsi_sell_threshold,
                "atr_period": self.strategy.atr_period,
                "adx_period": self.strategy.adx_period,
                "adx_trend_threshold": self.strategy.adx_trend_threshold,
                "roi_levels": self.strategy.roi_levels,
                "stoploss_pct": self.strategy.stoploss_pct,
                "trailing_stop_enabled": self.strategy.trailing_stop_enabled,
                "trailing_stop_positive": self.strategy.trailing_stop_positive,
                "trailing_stop_positive_offset": self.strategy.trailing_stop_positive_offset,
                "volume_min_multiplier": self.strategy.volume_min_multiplier,
            },
            "ai": {
                "chatgpt_weight": self.ai.chatgpt_weight,
                "claude_weight": self.ai.claude_weight,
                "gemini_weight": self.ai.gemini_weight,
                "min_consensus_score": self.ai.min_consensus_score,
                "min_confidence": self.ai.min_confidence,
                "require_all_providers": self.ai.require_all_providers,
                "signal_cache_minutes": self.ai.signal_cache_minutes,
                "lookback_candles": self.ai.lookback_candles,
                "chatgpt_model": self.ai.chatgpt_model,
                "claude_model": self.ai.claude_model,
                "gemini_model": self.ai.gemini_model,
            },
            "execution": {
                "trading_mode": self.execution.trading_mode,
                "exchange": self.execution.exchange,
                "entry_order_type": self.execution.entry_order_type,
                "exit_order_type": self.execution.exit_order_type,
                "stoploss_order_type": self.execution.stoploss_order_type,
                "stoploss_on_exchange": self.execution.stoploss_on_exchange,
                "order_time_in_force": self.execution.order_time_in_force,
                "starting_balance": self.execution.starting_balance,
                "stake_currency": self.execution.stake_currency,
                "stake_amount": self.execution.stake_amount,
            },
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def validate(self) -> List[str]:
        """
        Validate configuration for common errors.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Risk validation
        if (
            self.risk.max_loss_per_trade_pct <= 0
            or self.risk.max_loss_per_trade_pct > 10
        ):
            errors.append("max_loss_per_trade_pct must be between 0 and 10")

        if (
            self.risk.max_total_drawdown_pct <= 0
            or self.risk.max_total_drawdown_pct > 50
        ):
            errors.append("max_total_drawdown_pct must be between 0 and 50")

        # AI weights validation
        total_weight = (
            self.ai.chatgpt_weight + self.ai.claude_weight + self.ai.gemini_weight
        )
        if abs(total_weight - 1.0) > 0.01:
            errors.append(
                f"AI provider weights must sum to 1.0 (current: {total_weight:.2f})"
            )

        # Position sizing validation
        if (
            self.position_sizing.ai_confidence_min < 0
            or self.position_sizing.ai_confidence_min > 1
        ):
            errors.append("ai_confidence_min must be between 0 and 1")

        # Strategy validation
        if self.strategy.stoploss_pct >= 0:
            errors.append("stoploss_pct must be negative (e.g., -0.04 for 4% loss)")

        return errors

    def print_summary(self) -> None:
        """Print configuration summary"""
        print("\n" + "=" * 80)
        print("TRADING CONFIGURATION SUMMARY")
        print("=" * 80)

        print("\n📊 STRATEGY")
        print(f"  Name: {self.strategy.strategy_name}")
        print(f"  Timeframe: {self.strategy.timeframe}")
        print(f"  Pairs: {', '.join(self.strategy.pairs)}")
        print(f"  Stop-loss: {self.strategy.stoploss_pct:.1%}")

        print("\n⚠️  RISK MANAGEMENT")
        print(f"  Max Loss/Trade: {self.risk.max_loss_per_trade_pct}%")
        print(f"  Max Drawdown: {self.risk.max_total_drawdown_pct}%")
        print(f"  Max Positions: {self.risk.max_concurrent_positions}")
        print(
            f"  Position Size: {self.risk.min_position_size_pct}-{self.risk.max_position_size_pct}%"
        )

        print("\n💰 POSITION SIZING")
        print(f"  Method: {self.position_sizing.method}")
        print(f"  Base Risk: {self.position_sizing.base_risk_pct}%")
        print(
            f"  AI Confidence Range: {self.position_sizing.ai_confidence_min:.0%} - 100%"
        )
        print(
            f"  Stake Multiplier: {self.position_sizing.ai_confidence_multiplier_min}x - {self.position_sizing.ai_confidence_multiplier_max}x"
        )

        print("\n🤖 AI CONFIGURATION")
        print(
            f"  Weights: ChatGPT {self.ai.chatgpt_weight:.0%}, Claude {self.ai.claude_weight:.0%}, Gemini {self.ai.gemini_weight:.0%}"
        )
        print(f"  Min Consensus: {self.ai.min_consensus_score:.0%}")
        print(f"  Min Confidence: {self.ai.min_confidence:.0%}")
        print(f"  Cache Duration: {self.ai.signal_cache_minutes} min")

        print("\n⚙️  EXECUTION")
        print(f"  Mode: {self.execution.trading_mode.upper()}")
        print(f"  Exchange: {self.execution.exchange}")
        print(f"  Starting Balance: ${self.execution.starting_balance:,.2f}")
        print(f"  Base Stake: ${self.execution.stake_amount:.2f}")

        # Validation
        errors = self.validate()
        if errors:
            print("\n❌ VALIDATION ERRORS:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\n✅ Configuration valid")

        print("=" * 80 + "\n")


# Global configuration instance
_config: Optional[TradingConfig] = None


def get_trading_config(config_file: Optional[Path] = None) -> TradingConfig:
    """
    Get global trading configuration.

    Args:
        config_file: Optional path to config JSON file

    Returns:
        TradingConfig instance
    """
    global _config

    if _config is None:
        if config_file and config_file.exists():
            _config = TradingConfig.load_from_file(config_file)
        else:
            _config = TradingConfig()  # Use defaults

    return _config


def reset_trading_config() -> None:
    """Reset global config (useful for testing)"""
    global _config
    _config = None
