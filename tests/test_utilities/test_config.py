"""
Tests for configuration management
"""

import pytest
from proratio_utilities.config.settings import Settings, get_settings


def test_settings_defaults():
    """Test that settings have sensible defaults"""
    settings = Settings()

    assert settings.binance_testnet is True
    assert settings.trading_mode == "dry_run"
    assert settings.max_open_trades == 2
    assert settings.ai_consensus_threshold == 0.6


def test_get_settings_singleton():
    """Test that get_settings returns the same instance"""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2


def test_settings_validation():
    """Test that settings validation works"""
    settings = Settings(max_open_trades=3, stake_amount=200.0)

    assert settings.max_open_trades == 3
    assert settings.stake_amount == 200.0
