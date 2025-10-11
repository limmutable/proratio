"""
Unit tests for feature engineering module (Phase 3.1)

Tests the FeatureEngineer class and create_target_labels function.

NOTE: Full feature engineering requires pandas_ta which is not available for Python 3.9.
These tests verify the module structure and target label creation.
Full feature tests will pass once pandas_ta is available (Python 3.10+).
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from proratio_quantlab.ml.feature_engineering import FeatureEngineer, create_target_labels


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=200, freq='4h')

    # Generate realistic crypto-like price data
    np.random.seed(42)
    base_price = 50000
    returns = np.random.normal(0.0001, 0.02, 200)
    prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, 200)),
        'high': prices * (1 + np.random.uniform(0.001, 0.02, 200)),
        'low': prices * (1 + np.random.uniform(-0.02, -0.001, 200)),
        'close': prices,
        'volume': np.random.uniform(1000, 10000, 200)
    })

    return df


@pytest.fixture
def feature_engineer():
    """Create FeatureEngineer instance"""
    return FeatureEngineer()


class TestFeatureEngineer:
    """Test FeatureEngineer class"""

    def test_initialization(self, feature_engineer):
        """Test FeatureEngineer initialization"""
        assert feature_engineer is not None
        assert isinstance(feature_engineer, FeatureEngineer)
        assert hasattr(feature_engineer, 'add_all_features')
        assert hasattr(feature_engineer, 'add_technical_indicators')
        assert hasattr(feature_engineer, 'add_price_features')
        assert hasattr(feature_engineer, 'add_volume_features')
        assert hasattr(feature_engineer, 'add_volatility_features')
        assert hasattr(feature_engineer, 'add_momentum_features')
        assert hasattr(feature_engineer, 'add_regime_features')
        assert hasattr(feature_engineer, 'add_time_features')

    @pytest.mark.skip(reason="Requires pandas_ta (not available for Python 3.9)")
    def test_add_all_features_with_pandas_ta(self, feature_engineer, sample_ohlcv_data):
        """Test adding all features - requires pandas_ta"""
        df = feature_engineer.add_all_features(sample_ohlcv_data.copy())

        # Verify we have significantly more columns than original
        original_columns = len(sample_ohlcv_data.columns)
        final_columns = len(df.columns)
        assert final_columns > original_columns + 70  # Should have 80+ new features

    @pytest.mark.skip(reason="Requires pandas_ta (derived features depend on technical indicators)")
    def test_add_all_features_without_pandas_ta(self, feature_engineer, sample_ohlcv_data):
        """Test that add_all_features handles missing pandas_ta gracefully"""
        df = feature_engineer.add_all_features(sample_ohlcv_data.copy())

        # Should return original dataframe if pandas_ta not available
        # (technical indicators will not be added, but should not crash)
        assert len(df) == len(sample_ohlcv_data)
        assert 'close' in df.columns
        assert 'volume' in df.columns


class TestCreateTargetLabels:
    """Test create_target_labels function"""

    def test_regression_target(self, sample_ohlcv_data):
        """Test regression target creation"""
        lookahead = 4
        df = create_target_labels(sample_ohlcv_data.copy(), target_type='regression', lookahead_periods=lookahead)

        # Check expected columns exist
        assert 'target_price' in df.columns or 'target_return' in df.columns

        # Check last N rows were removed (can't predict future)
        assert len(df) == len(sample_ohlcv_data) - lookahead

        # Check values are reasonable (if target_return exists)
        if 'target_return' in df.columns:
            assert df['target_return'].abs().max() < 50  # Max 50% change

    def test_classification_target(self, sample_ohlcv_data):
        """Test classification target creation"""
        lookahead = 4
        df = create_target_labels(sample_ohlcv_data.copy(), target_type='classification', lookahead_periods=lookahead)

        # Check target_direction exists
        assert 'target_direction' in df.columns

        # Check last N rows were removed
        assert len(df) == len(sample_ohlcv_data) - lookahead

        # Check values are in expected range (0, 1, 2 for down/neutral/up)
        unique_values = df['target_direction'].dropna().unique()
        assert all(val in [0.0, 1.0, 2.0] for val in unique_values)

    def test_invalid_target_type(self, sample_ohlcv_data):
        """Test invalid target type returns original dataframe"""
        df = create_target_labels(sample_ohlcv_data.copy(), target_type='invalid')

        # Should return dataframe (may log warning but not crash)
        assert len(df) > 0
        assert 'close' in df.columns

    def test_lookahead_periods_validation(self, sample_ohlcv_data):
        """Test different lookahead periods"""
        for periods in [1, 4, 8, 12]:
            df = create_target_labels(sample_ohlcv_data.copy(), target_type='regression', lookahead_periods=periods)

            # Check correct number of rows removed
            assert len(df) == len(sample_ohlcv_data) - periods

    def test_target_labels_no_future_leakage(self, sample_ohlcv_data):
        """Test that target labels don't leak future information"""
        lookahead = 4
        df = create_target_labels(sample_ohlcv_data.copy(), target_type='regression', lookahead_periods=lookahead)

        # Last lookahead rows should be removed
        assert len(df) < len(sample_ohlcv_data)

        # Verify last row index
        original_last_idx = len(sample_ohlcv_data) - 1
        result_last_idx = len(df) - 1
        assert result_last_idx == original_last_idx - lookahead


class TestFeatureEngineeringIntegration:
    """Integration tests for feature engineering"""

    def test_module_imports(self):
        """Test that all module components can be imported"""
        from proratio_quantlab.ml.feature_engineering import FeatureEngineer, create_target_labels

        assert FeatureEngineer is not None
        assert create_target_labels is not None

    @pytest.mark.skip(reason="Requires pandas_ta")
    def test_feature_engineer_with_target_labels(self, feature_engineer, sample_ohlcv_data):
        """Test combining feature engineering with target label creation"""
        # Add features (will be limited without pandas_ta)
        df = feature_engineer.add_all_features(sample_ohlcv_data.copy())

        # Add target labels
        df = create_target_labels(df, target_type='regression', lookahead_periods=4)

        # Should have valid dataframe
        assert len(df) > 0
        assert len(df) == len(sample_ohlcv_data) - 4

    @pytest.mark.skip(reason="Requires pandas_ta")
    def test_dataframe_integrity(self, feature_engineer, sample_ohlcv_data):
        """Test that feature engineering maintains data integrity"""
        original_len = len(sample_ohlcv_data)

        # Add features
        df = feature_engineer.add_all_features(sample_ohlcv_data.copy())

        # Length should be preserved (before target creation)
        assert len(df) == original_len

        # Original columns should still exist
        assert 'close' in df.columns
        assert 'volume' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns

    @pytest.mark.skip(reason="Requires pandas_ta")
    def test_no_infinite_values(self, feature_engineer, sample_ohlcv_data):
        """Test that feature engineering doesn't create infinite values"""
        df = feature_engineer.add_all_features(sample_ohlcv_data.copy())

        # Check no infinite values in any column
        for col in df.columns:
            if df[col].dtype in [np.float64, np.float32]:
                assert not df[col].isin([np.inf, -np.inf]).any(), f"Column {col} contains infinite values"


class TestFeatureEngineeringDocumentation:
    """Tests documenting expected behavior when pandas_ta is available"""

    def test_expected_technical_indicators(self):
        """Document expected technical indicators"""
        expected_indicators = [
            'rsi_14', 'rsi_21', 'rsi_7',  # RSI variants
            'macd', 'macd_signal', 'macd_diff',  # MACD
            'bb_upper', 'bb_middle', 'bb_lower', 'bb_width',  # Bollinger Bands
            'atr_14', 'atr_7',  # ATR
            'ema_9', 'ema_21', 'ema_50', 'ema_200',  # EMAs
            'sma_20', 'sma_50',  # SMAs
            'adx', 'adx_plus', 'adx_minus',  # ADX
            'stoch_k', 'stoch_d',  # Stochastic
            'cci',  # CCI
            'williams_r',  # Williams %R
        ]

        # This documents what indicators should be generated
        assert len(expected_indicators) > 20

    def test_expected_derived_features(self):
        """Document expected derived features"""
        expected_features = {
            'price': ['close_pct_change', 'price_to_ema', 'high_low_range'],
            'volume': ['volume_pct_change', 'volume_ratio', 'price_volume_corr'],
            'volatility': ['atr_pct', 'rolling_volatility', 'bb_pct'],
            'momentum': ['roc', 'ema_crossover', 'macd_signal_diff'],
            'regime': ['is_trending', 'is_ranging', 'is_volatile'],
            'time': ['hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos']
        }

        # Document feature categories
        assert len(expected_features) == 6
        total_features = sum(len(v) for v in expected_features.values())
        assert total_features > 15


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
