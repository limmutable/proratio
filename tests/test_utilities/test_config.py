"""
Tests for configuration management
"""

from proratio_utilities.config.settings import Settings, get_settings
from proratio_utilities.config.trading_config import (
    TradingConfig,
    get_trading_config,
    reset_trading_config,
)


def test_settings_defaults():
    """Test that settings have sensible defaults (secrets/env only)"""
    settings = Settings()

    assert settings.binance_testnet is True
    assert settings.trading_mode == "dry_run"
    assert settings.data_refresh_interval == 300


def test_get_settings_singleton():
    """Test that get_settings returns the same instance"""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2


def test_trading_config_defaults():
    """Test that trading config has sensible defaults"""
    reset_trading_config()  # Clear any cached config
    config = get_trading_config()

    # Risk settings
    assert config.risk.max_concurrent_positions == 3
    assert config.risk.max_total_drawdown_pct == 10.0
    assert config.risk.max_loss_per_trade_pct == 2.0

    # Execution settings
    assert config.execution.stake_amount == 100.0
    assert config.execution.trading_mode == "dry_run"

    # AI settings
    assert config.ai.min_consensus_score == 0.6
    assert config.ai.chatgpt_weight == 0.4
    assert config.ai.claude_weight == 0.35
    assert config.ai.gemini_weight == 0.25


def test_trading_config_validation():
    """Test that trading config validation works"""
    config = TradingConfig()

    # Valid config should have no errors
    errors = config.validate()
    assert len(errors) == 0

    # Invalid config should have errors
    config.risk.max_loss_per_trade_pct = 15.0  # Too high
    config.strategy.stoploss_pct = 0.04  # Should be negative
    errors = config.validate()
    assert len(errors) > 0
