"""
Integration Test Fixtures

This module provides pytest fixtures for integration tests.
- In-memory SQLite database for testing ValidationRepository
- Temporary storage directories for data pipeline tests
- Mock market data for signal generation tests

Feature: 001-test-validation-dashboard
Created: 2025-10-28
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

from proratio_utilities.data.validation_repository import ValidationRepository


@pytest.fixture(scope="function")
def test_db_engine():
    """
    Provide an in-memory SQLite database engine for testing.

    Scope: function - each test gets a fresh database.

    Yields:
        SQLAlchemy engine connected to in-memory SQLite database.
    """
    # Create in-memory SQLite engine
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create validation_results table
    from proratio_utilities.data.validation_repository import ValidationRepository

    repo = ValidationRepository(database_url="sqlite:///:memory:")
    repo.metadata.create_all(engine)

    yield engine

    # Cleanup
    engine.dispose()


@pytest.fixture(scope="function")
def test_validation_repo():
    """
    Provide a ValidationRepository instance connected to an in-memory SQLite database.

    Scope: function - each test gets a fresh repository with empty database.

    Returns:
        ValidationRepository instance for testing.
    """
    # Create in-memory SQLite repository
    repo = ValidationRepository(database_url="sqlite:///:memory:")

    # Create tables
    repo.metadata.create_all(repo.engine)

    yield repo

    # Cleanup
    repo.engine.dispose()


@pytest.fixture(scope="function")
def test_storage_dir():
    """
    Provide a temporary directory for data storage tests.

    Scope: function - each test gets a fresh temporary directory.

    Yields:
        Path object pointing to temporary directory.

    Note: Automatic cleanup when context exits.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def mock_market_data():
    """
    Provide synthetic market data for signal generation tests.

    Generates 100 hours of synthetic OHLCV data with realistic patterns.

    Scope: function - each test gets fresh synthetic data.

    Returns:
        pandas.DataFrame with columns: timestamp, open, high, low, close, volume.
    """
    # Generate 100 hours of hourly data
    dates = pd.date_range("2024-01-01", periods=100, freq="1h")

    # Generate synthetic price data with trend and noise
    base_price = 50000.0
    trend = np.linspace(0, 2000, 100)  # Upward trend
    noise = np.random.randn(100) * 500  # Random fluctuations

    close_prices = base_price + trend + noise

    # Generate OHLC from close prices
    open_prices = np.roll(close_prices, 1)
    open_prices[0] = base_price

    high_prices = np.maximum(open_prices, close_prices) + np.abs(
        np.random.randn(100) * 200
    )
    low_prices = np.minimum(open_prices, close_prices) - np.abs(
        np.random.randn(100) * 200
    )

    # Generate volume with realistic patterns
    base_volume = 1000000
    volume_noise = np.random.randn(100) * 200000
    volumes = base_volume + volume_noise

    return pd.DataFrame(
        {
            "timestamp": dates,
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "volume": volumes,
        }
    )


@pytest.fixture(scope="function")
def sample_validation_result():
    """
    Provide a sample validation result dictionary for testing.

    Scope: function.

    Returns:
        dict: Sample validation result with all required and optional fields.
    """
    return {
        "strategy_name": "GridTrading",
        "timestamp": datetime.utcnow() - timedelta(hours=1),
        "total_trades": 150,
        "win_rate": 65.33,
        "total_profit_pct": 12.45,
        "max_drawdown": -8.75,
        "sharpe_ratio": 1.82,
        "profit_factor": 1.65,
        "git_commit_hash": "a1b2c3d4e5f6789012345678901234567890abcd",
    }


@pytest.fixture(scope="function")
def sample_validation_results_batch():
    """
    Provide a batch of sample validation results for testing queries.

    Generates 20 validation results across 3 strategies over 10 days.

    Scope: function.

    Returns:
        List[dict]: List of validation result dictionaries.
    """
    strategies = ["GridTrading", "AIEnhanced", "MomentumStrategy"]
    results = []

    for i in range(20):
        strategy = strategies[i % 3]
        timestamp = datetime.utcnow() - timedelta(days=10 - i // 2)

        results.append(
            {
                "strategy_name": strategy,
                "timestamp": timestamp,
                "total_trades": 100 + i * 10,
                "win_rate": 50.0 + i * 1.5,
                "total_profit_pct": -5.0 + i * 1.0,
                "max_drawdown": -15.0 + i * 0.5,
                "sharpe_ratio": 0.5 + i * 0.1,
                "profit_factor": 0.8 + i * 0.1,
                "git_commit_hash": f"{i:040d}",  # Mock commit hashes
            }
        )

    return results
