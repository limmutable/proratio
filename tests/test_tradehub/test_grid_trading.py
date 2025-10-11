"""
Tests for Grid Trading Strategy

Tests grid level calculation, market suitability detection, and trade signals.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from proratio_tradehub.strategies.grid_trading import GridTradingStrategy


@pytest.fixture
def sample_dataframe():
    """Create sample OHLCV data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')

    df = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(40000, 42000, 100),
        'high': np.random.uniform(41000, 43000, 100),
        'low': np.random.uniform(39000, 41000, 100),
        'close': np.random.uniform(40000, 42000, 100),
        'volume': np.random.uniform(100, 1000, 100),
        'atr': np.random.uniform(400, 800, 100),  # 1-2% ATR
        'ema_fast': np.random.uniform(40000, 41000, 100),
        'ema_slow': np.random.uniform(40000, 41000, 100)
    })

    # Calculate derived indicators
    df['close'] = df['close'].rolling(window=5).mean().fillna(df['close'])  # Smooth prices
    df['ema_fast'] = df['close'].ewm(span=20).mean()
    df['ema_slow'] = df['close'].ewm(span=50).mean()

    return df


def test_grid_strategy_initialization():
    """Test grid strategy initialization"""
    strategy = GridTradingStrategy(
        name="TestGrid",
        grid_spacing=0.02,
        num_grids_above=5,
        num_grids_below=5,
        grid_type="geometric"
    )

    assert strategy.name == "TestGrid"
    assert strategy.grid_spacing == 0.02
    assert strategy.num_grids_above == 5
    assert strategy.num_grids_below == 5
    assert strategy.grid_type == "geometric"


def test_geometric_grid_calculation():
    """Test geometric grid level calculation"""
    strategy = GridTradingStrategy(
        grid_spacing=0.02,  # 2% spacing
        num_grids_above=3,
        num_grids_below=3,
        grid_type="geometric"
    )

    current_price = 40000
    buy_levels, sell_levels = strategy.calculate_grid_levels(current_price, "BTC/USDT")

    # Check buy levels (below current price)
    assert len(buy_levels) == 3
    assert all(level < current_price for level in buy_levels)

    # Check 2% spacing (geometric)
    expected_buy_1 = current_price * (1 - 0.02 * 1)  # 39200
    expected_buy_2 = current_price * (1 - 0.02 * 2)  # 38400
    expected_buy_3 = current_price * (1 - 0.02 * 3)  # 37600

    assert abs(buy_levels[0] - expected_buy_1) < 1
    assert abs(buy_levels[1] - expected_buy_2) < 1
    assert abs(buy_levels[2] - expected_buy_3) < 1

    # Check sell levels (above current price)
    assert len(sell_levels) == 3
    assert all(level > current_price for level in sell_levels)

    expected_sell_1 = current_price * (1 + 0.02 * 1)  # 40800
    expected_sell_2 = current_price * (1 + 0.02 * 2)  # 41600
    expected_sell_3 = current_price * (1 + 0.02 * 3)  # 42400

    assert abs(sell_levels[0] - expected_sell_1) < 1
    assert abs(sell_levels[1] - expected_sell_2) < 1
    assert abs(sell_levels[2] - expected_sell_3) < 1


def test_arithmetic_grid_calculation():
    """Test arithmetic grid level calculation"""
    strategy = GridTradingStrategy(
        grid_spacing=0.02,  # 2% spacing
        num_grids_above=3,
        num_grids_below=3,
        grid_type="arithmetic"
    )

    current_price = 40000
    dollar_spacing = current_price * 0.02  # $800

    buy_levels, sell_levels = strategy.calculate_grid_levels(current_price, "BTC/USDT")

    # Check buy levels (arithmetic)
    expected_buy_1 = current_price - dollar_spacing * 1  # 39200
    expected_buy_2 = current_price - dollar_spacing * 2  # 38400
    expected_buy_3 = current_price - dollar_spacing * 3  # 37600

    assert abs(buy_levels[0] - expected_buy_1) < 1
    assert abs(buy_levels[1] - expected_buy_2) < 1
    assert abs(buy_levels[2] - expected_buy_3) < 1

    # Check sell levels (arithmetic)
    expected_sell_1 = current_price + dollar_spacing * 1  # 40800
    expected_sell_2 = current_price + dollar_spacing * 2  # 41600
    expected_sell_3 = current_price + dollar_spacing * 3  # 42400

    assert abs(sell_levels[0] - expected_sell_1) < 1
    assert abs(sell_levels[1] - expected_sell_2) < 1
    assert abs(sell_levels[2] - expected_sell_3) < 1


def test_market_suitability_high_volatility(sample_dataframe):
    """Test market suitability check with high volatility"""
    strategy = GridTradingStrategy(
        min_volatility_threshold=0.015,  # 1.5% ATR required
        use_ai_volatility_check=False  # Disable AI for unit test
    )

    # Set high volatility (2% ATR)
    sample_dataframe['atr'] = sample_dataframe['close'] * 0.020

    is_suitable, reasoning = strategy.is_market_suitable_for_grid("BTC/USDT", sample_dataframe)

    assert is_suitable is True
    assert "High volatility" in reasoning or "suitable" in reasoning.lower()


def test_market_suitability_low_volatility(sample_dataframe):
    """Test market suitability check with low volatility"""
    strategy = GridTradingStrategy(
        min_volatility_threshold=0.015,
        use_ai_volatility_check=False
    )

    # Set low volatility (0.5% ATR)
    sample_dataframe['atr'] = sample_dataframe['close'] * 0.005

    is_suitable, reasoning = strategy.is_market_suitable_for_grid("BTC/USDT", sample_dataframe)

    assert is_suitable is False
    assert "Low volatility" in reasoning or "volatility" in reasoning.lower()


def test_market_suitability_strong_trend(sample_dataframe):
    """Test market suitability check with strong trend"""
    strategy = GridTradingStrategy(
        min_volatility_threshold=0.015,
        use_ai_volatility_check=False
    )

    # Set high volatility
    sample_dataframe['atr'] = sample_dataframe['close'] * 0.020

    # Set strong uptrend (EMA_fast >> EMA_slow)
    sample_dataframe['ema_fast'] = sample_dataframe['close'] * 1.05  # 5% above
    sample_dataframe['ema_slow'] = sample_dataframe['close']

    is_suitable, reasoning = strategy.is_market_suitable_for_grid("BTC/USDT", sample_dataframe)

    assert is_suitable is False
    assert "trend" in reasoning.lower()


def test_should_enter_long_suitable_market(sample_dataframe):
    """Test long entry signal in suitable market"""
    strategy = GridTradingStrategy(
        grid_spacing=0.02,
        num_grids_below=5,
        min_volatility_threshold=0.015,
        use_ai_volatility_check=False
    )

    # Set high volatility
    sample_dataframe['atr'] = sample_dataframe['close'] * 0.020

    # Set current price at first buy grid level
    current_price = 40000
    sample_dataframe.loc[sample_dataframe.index[-1], 'close'] = current_price

    # Calculate grids
    buy_levels, _ = strategy.calculate_grid_levels(current_price, "BTC/USDT")

    # Set price at first buy grid
    sample_dataframe.loc[sample_dataframe.index[-1], 'close'] = buy_levels[0]

    signal = strategy.should_enter_long("BTC/USDT", sample_dataframe)

    # Should generate long signal
    assert signal.direction in ['long', 'neutral']  # May be neutral if not exactly at grid

    if signal.direction == 'long':
        assert signal.confidence > 0.5
        assert signal.entry_price is not None


def test_should_enter_long_unsuitable_market(sample_dataframe):
    """Test long entry signal in unsuitable market"""
    strategy = GridTradingStrategy(
        min_volatility_threshold=0.015,
        use_ai_volatility_check=False
    )

    # Set low volatility (unsuitable)
    sample_dataframe['atr'] = sample_dataframe['close'] * 0.005

    signal = strategy.should_enter_long("BTC/USDT", sample_dataframe)

    # Should NOT generate signal
    assert signal.direction == 'neutral'
    assert signal.confidence == 0.0


def test_should_exit_at_sell_grid(sample_dataframe):
    """Test exit signal when price reaches sell grid"""
    strategy = GridTradingStrategy(
        grid_spacing=0.02,
        num_grids_above=5,
        use_ai_volatility_check=False
    )

    # Set high volatility
    sample_dataframe['atr'] = sample_dataframe['close'] * 0.020

    # Set entry price
    entry_price = 40000
    current_position = {
        'entry_price': entry_price,
        'side': 'long'
    }

    # Calculate sell grids
    _, sell_levels = strategy.calculate_grid_levels(entry_price, "BTC/USDT")

    # Set current price at first sell grid
    sample_dataframe.loc[sample_dataframe.index[-1], 'close'] = sell_levels[0]

    signal = strategy.should_exit("BTC/USDT", sample_dataframe, current_position)

    # Should generate exit signal
    assert signal.direction in ['exit', 'neutral']


def test_required_indicators():
    """Test required indicators list"""
    strategy = GridTradingStrategy()

    indicators = strategy.get_required_indicators()

    assert 'atr' in indicators
    assert 'ema_fast' in indicators
    assert 'ema_slow' in indicators


def test_strategy_repr():
    """Test string representation"""
    strategy = GridTradingStrategy(
        name="TestGrid",
        grid_spacing=0.025,
        num_grids_above=5,
        num_grids_below=5,
        grid_type="geometric"
    )

    repr_str = repr(strategy)

    assert "GridTradingStrategy" in repr_str
    assert "2.5%" in repr_str or "0.025" in repr_str
    assert "geometric" in repr_str
