"""
Tests for Portfolio Manager

Tests multi-strategy portfolio allocation, market regime detection, and rebalancing.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from proratio_tradehub.orchestration.portfolio_manager import (
    PortfolioManager,
    MarketRegime,
)
from proratio_tradehub.strategies.base_strategy import BaseStrategy, TradeSignal


# Mock strategies for testing
class MockTrendStrategy(BaseStrategy):
    """Mock trend-following strategy"""

    def should_enter_long(self, pair, dataframe, **kwargs):
        return TradeSignal(direction="long", confidence=0.8)

    def should_enter_short(self, pair, dataframe, **kwargs):
        return TradeSignal(direction="neutral", confidence=0.0)

    def should_exit(self, pair, dataframe, current_position, **kwargs):
        return TradeSignal(direction="neutral", confidence=0.0)


class MockMeanReversionStrategy(BaseStrategy):
    """Mock mean reversion strategy"""

    def should_enter_long(self, pair, dataframe, **kwargs):
        return TradeSignal(direction="long", confidence=0.7)

    def should_enter_short(self, pair, dataframe, **kwargs):
        return TradeSignal(direction="neutral", confidence=0.0)

    def should_exit(self, pair, dataframe, current_position, **kwargs):
        return TradeSignal(direction="neutral", confidence=0.0)


@pytest.fixture
def sample_dataframe():
    """Create sample OHLCV data for testing"""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="1H")

    df = pd.DataFrame(
        {
            "timestamp": dates,
            "open": np.random.uniform(40000, 42000, 100),
            "high": np.random.uniform(41000, 43000, 100),
            "low": np.random.uniform(39000, 41000, 100),
            "close": np.random.uniform(40000, 42000, 100),
            "volume": np.random.uniform(100, 1000, 100),
            "atr": np.random.uniform(400, 800, 100),
            "adx": np.random.uniform(15, 30, 100),
            "rsi": np.random.uniform(40, 60, 100),
            "ema_fast": np.random.uniform(40000, 41000, 100),
            "ema_slow": np.random.uniform(40000, 41000, 100),
            "bb_upper": np.random.uniform(41000, 42000, 100),
            "bb_middle": np.random.uniform(40000, 41000, 100),
            "bb_lower": np.random.uniform(39000, 40000, 100),
        }
    )

    # Calculate derived indicators
    df["close"] = df["close"].rolling(window=5).mean().fillna(df["close"])
    df["ema_fast"] = df["close"].ewm(span=20).mean()
    df["ema_slow"] = df["close"].ewm(span=50).mean()
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]

    return df


def test_portfolio_manager_initialization():
    """Test portfolio manager initialization"""
    pm = PortfolioManager(
        total_capital=10000,
        allocation_method="equal",
        rebalance_frequency_hours=24,
        use_ai_regime_detection=False,
    )

    assert pm.total_capital == 10000
    assert pm.allocation_method == "equal"
    assert pm.rebalance_frequency_hours == 24
    assert len(pm.strategies) == 0


def test_register_strategy():
    """Test strategy registration"""
    pm = PortfolioManager(total_capital=10000, use_ai_regime_detection=False)

    strategy = MockTrendStrategy(name="TestTrend")
    pm.register_strategy(strategy, initial_weight=0.6)

    assert "TestTrend" in pm.strategies
    assert "TestTrend" in pm.allocations
    assert pm.allocations["TestTrend"].weight == 0.6
    assert pm.allocations["TestTrend"].enabled is True


def test_equal_allocation():
    """Test equal weight allocation"""
    pm = PortfolioManager(
        total_capital=10000, allocation_method="equal", use_ai_regime_detection=False
    )

    # Register 3 strategies
    pm.register_strategy(MockTrendStrategy(name="Strategy1"))
    pm.register_strategy(MockMeanReversionStrategy(name="Strategy2"))
    pm.register_strategy(MockTrendStrategy(name="Strategy3"))

    allocations = pm._allocate_equal()

    # Each should get 1/3
    assert len(allocations) == 3
    for alloc in allocations.values():
        assert abs(alloc.weight - 1 / 3) < 0.01


def test_detect_trending_up_regime(sample_dataframe):
    """Test detection of trending up market"""
    pm = PortfolioManager(total_capital=10000, use_ai_regime_detection=False)

    # Set strong uptrend indicators
    sample_dataframe["adx"] = 35  # Strong trend
    sample_dataframe["ema_fast"] = sample_dataframe["close"] * 1.05  # 5% above
    sample_dataframe["ema_slow"] = sample_dataframe["close"]

    regime = pm.detect_market_regime(sample_dataframe)

    assert regime.regime_type == "trending_up"
    assert regime.confidence > 0.5


def test_detect_ranging_regime(sample_dataframe):
    """Test detection of ranging market"""
    pm = PortfolioManager(total_capital=10000, use_ai_regime_detection=False)

    # Set ranging indicators
    sample_dataframe["adx"] = 15  # Low trend strength
    sample_dataframe["ema_fast"] = sample_dataframe["close"] * 1.01  # Close to slow EMA
    sample_dataframe["ema_slow"] = sample_dataframe["close"]

    regime = pm.detect_market_regime(sample_dataframe)

    assert regime.regime_type == "ranging"


def test_detect_volatile_regime(sample_dataframe):
    """Test detection of volatile market"""
    pm = PortfolioManager(total_capital=10000, use_ai_regime_detection=False)

    # Set high volatility indicators
    sample_dataframe["atr"] = sample_dataframe["close"] * 0.03  # 3% ATR
    sample_dataframe["bb_width"] = 0.05  # 5% BB width
    sample_dataframe["adx"] = 20  # Moderate trend

    regime = pm.detect_market_regime(sample_dataframe)

    assert regime.regime_type == "volatile"
    assert regime.confidence > 0.5


def test_calculate_strategy_suitability():
    """Test strategy suitability calculation"""
    pm = PortfolioManager(total_capital=10000, use_ai_regime_detection=False)

    # Trending up regime
    trending_up_regime = MarketRegime(
        regime_type="trending_up",
        confidence=0.8,
        indicators={},
        timestamp=datetime.now(),
    )

    # AIEnhancedStrategy should be highly suitable for trending up
    suitability = pm.calculate_strategy_suitability(
        "AIEnhancedStrategy", trending_up_regime
    )
    assert suitability > 0.6  # 0.9 * 0.8 = 0.72

    # MeanReversion should be less suitable for trending up
    suitability = pm.calculate_strategy_suitability("MeanReversion", trending_up_regime)
    assert suitability < 0.4  # 0.3 * 0.8 = 0.24

    # Ranging regime
    ranging_regime = MarketRegime(
        regime_type="ranging", confidence=0.7, indicators={}, timestamp=datetime.now()
    )

    # MeanReversion should be highly suitable for ranging
    suitability = pm.calculate_strategy_suitability("MeanReversion", ranging_regime)
    assert suitability > 0.5  # 0.9 * 0.7 = 0.63


def test_market_adaptive_allocation(sample_dataframe):
    """Test market-adaptive allocation"""
    pm = PortfolioManager(
        total_capital=10000,
        allocation_method="market_adaptive",
        use_ai_regime_detection=False,
    )

    # Register strategies
    pm.register_strategy(MockTrendStrategy(name="AIEnhancedStrategy"))
    pm.register_strategy(MockMeanReversionStrategy(name="MeanReversion"))
    pm.register_strategy(MockTrendStrategy(name="GridTrading"))

    # Set trending up market
    sample_dataframe["adx"] = 35
    sample_dataframe["ema_fast"] = sample_dataframe["close"] * 1.05
    sample_dataframe["ema_slow"] = sample_dataframe["close"]

    regime = pm.detect_market_regime(sample_dataframe)
    allocations = pm._allocate_market_adaptive(regime)

    # AIEnhancedStrategy should get most allocation in trending market
    assert (
        allocations["AIEnhancedStrategy"].weight > allocations["MeanReversion"].weight
    )


def test_performance_based_allocation():
    """Test performance-based allocation"""
    pm = PortfolioManager(
        total_capital=10000,
        allocation_method="performance",
        use_ai_regime_detection=False,
    )

    # Register strategies
    pm.register_strategy(MockTrendStrategy(name="Strategy1"))
    pm.register_strategy(MockMeanReversionStrategy(name="Strategy2"))

    # Add performance history
    pm.performance_history["Strategy1"] = [0.05, 0.03, 0.04, 0.06]  # Good performance
    pm.performance_history["Strategy2"] = [-0.02, 0.01, -0.01, 0.00]  # Poor performance

    allocations = pm._allocate_by_performance()

    # Strategy1 should get more allocation
    assert allocations["Strategy1"].weight > allocations["Strategy2"].weight


def test_rebalance_portfolio(sample_dataframe):
    """Test portfolio rebalancing"""
    pm = PortfolioManager(
        total_capital=10000,
        allocation_method="market_adaptive",
        rebalance_frequency_hours=24,
        use_ai_regime_detection=False,
    )

    # Register strategies
    pm.register_strategy(MockTrendStrategy(name="AIEnhancedStrategy"))
    pm.register_strategy(MockMeanReversionStrategy(name="MeanReversion"))

    # Rebalance
    allocations = pm.rebalance_portfolio(sample_dataframe)

    # Check allocations sum to 1.0
    total_weight = sum(alloc.weight for alloc in allocations.values())
    assert abs(total_weight - 1.0) < 0.01

    # Check last_rebalance timestamp is set
    assert pm.last_rebalance is not None


def test_get_strategy_capital():
    """Test getting allocated capital for a strategy"""
    pm = PortfolioManager(total_capital=10000, use_ai_regime_detection=False)

    strategy = MockTrendStrategy(name="TestStrategy")
    pm.register_strategy(strategy, initial_weight=0.4)

    capital = pm.get_strategy_capital("TestStrategy")

    assert capital == 4000  # 10000 * 0.4


def test_update_strategy_performance():
    """Test updating strategy performance"""
    pm = PortfolioManager(total_capital=10000, use_ai_regime_detection=False)

    pm.update_strategy_performance("Strategy1", 0.05)
    pm.update_strategy_performance("Strategy1", 0.03)
    pm.update_strategy_performance("Strategy1", -0.02)

    assert len(pm.performance_history["Strategy1"]) == 3
    assert pm.performance_history["Strategy1"][0] == 0.05


def test_get_portfolio_summary():
    """Test portfolio summary generation"""
    pm = PortfolioManager(total_capital=10000, use_ai_regime_detection=False)

    pm.register_strategy(MockTrendStrategy(name="Strategy1"), initial_weight=0.6)
    pm.register_strategy(
        MockMeanReversionStrategy(name="Strategy2"), initial_weight=0.4
    )

    summary = pm.get_portfolio_summary()

    assert summary["total_capital"] == 10000
    assert summary["allocation_method"] == "market_adaptive"
    assert "Strategy1" in summary["strategies"]
    assert "Strategy2" in summary["strategies"]
    assert summary["strategies"]["Strategy1"]["weight"] == 0.6
    assert summary["strategies"]["Strategy1"]["capital"] == 6000


def test_should_rebalance():
    """Test rebalance trigger logic"""
    pm = PortfolioManager(
        total_capital=10000, rebalance_frequency_hours=24, use_ai_regime_detection=False
    )

    # First check - should rebalance (never rebalanced before)
    assert pm.should_rebalance() is True

    # Set last rebalance to now
    pm.last_rebalance = datetime.now()

    # Should not rebalance immediately
    assert pm.should_rebalance() is False


def test_allocation_constraints():
    """Test min/max allocation constraints"""
    pm = PortfolioManager(
        total_capital=10000,
        allocation_method="market_adaptive",
        min_strategy_allocation=0.15,  # 15% min
        max_strategy_allocation=0.50,  # 50% max
        use_ai_regime_detection=False,
    )

    # Register 3 strategies
    pm.register_strategy(MockTrendStrategy(name="Strategy1"))
    pm.register_strategy(MockMeanReversionStrategy(name="Strategy2"))
    pm.register_strategy(MockTrendStrategy(name="Strategy3"))

    # Mock market regime
    regime = MarketRegime(
        regime_type="trending_up",
        confidence=0.9,
        indicators={},
        timestamp=datetime.now(),
    )

    allocations = pm._allocate_market_adaptive(regime)

    # Check constraints
    for alloc in allocations.values():
        if alloc.enabled:
            assert alloc.weight >= pm.min_strategy_allocation
            assert alloc.weight <= pm.max_strategy_allocation


def test_portfolio_manager_repr():
    """Test string representation"""
    pm = PortfolioManager(total_capital=10000, use_ai_regime_detection=False)

    pm.register_strategy(MockTrendStrategy(name="Strategy1"))
    pm.register_strategy(MockMeanReversionStrategy(name="Strategy2"))

    repr_str = repr(pm)

    assert "PortfolioManager" in repr_str
    assert "10000" in repr_str
    assert "2/2" in repr_str  # 2 enabled out of 2 total
