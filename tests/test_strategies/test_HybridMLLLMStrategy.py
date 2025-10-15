"""
Unit Tests for HybridMLLLMStrategy

Tests the Freqtrade strategy implementation including entry logic,
position sizing, and integration with hybrid predictor.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime

# Import strategy
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from user_data.strategies.HybridMLLLMStrategy import HybridMLLLMStrategy  # noqa: E402
from proratio_signals.hybrid_predictor import HybridSignal, SignalStrength, MLPrediction, LLMPrediction  # noqa: E402


class TestHybridMLLLMStrategyInitialization:
    """Test strategy initialization"""

    @pytest.fixture
    def strategy(self):
        """Create strategy instance"""
        config = {
            "stake_currency": "USDT",
            "stake_amount": 100,
            "dry_run": True,
        }
        return HybridMLLLMStrategy(config)

    def test_strategy_initialization(self, strategy):
        """Test strategy initializes with correct parameters"""
        assert strategy.timeframe == "4h"
        assert strategy.stoploss == -0.05
        assert strategy.min_combined_confidence == 0.65
        assert strategy.min_agreement_score == 0.70
        assert strategy.startup_candle_count == 100

    def test_strategy_metadata(self, strategy):
        """Test strategy metadata"""
        assert strategy.INTERFACE_VERSION == 3
        assert strategy.can_short is False  # Long-only initially

    def test_minimal_roi(self, strategy):
        """Test minimal ROI configuration"""
        assert strategy.minimal_roi["0"] == 0.10
        assert strategy.minimal_roi["720"] == 0.05
        assert strategy.minimal_roi["1440"] == 0.03
        assert strategy.minimal_roi["2880"] == 0.01

    def test_trailing_stop(self, strategy):
        """Test trailing stop configuration"""
        assert strategy.trailing_stop is True
        assert strategy.trailing_stop_positive == 0.01
        assert strategy.trailing_stop_positive_offset == 0.03
        assert strategy.trailing_only_offset_is_reached is True


class TestSimpleFallbackPredictor:
    """Test SimpleFallbackPredictor"""

    @pytest.fixture
    def strategy(self):
        config = {"stake_currency": "USDT", "stake_amount": 100, "dry_run": True}
        return HybridMLLLMStrategy(config)

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample dataframe with indicators"""
        df = pd.DataFrame(
            {
                "open": [40000, 41000, 42000],
                "high": [41000, 42000, 43000],
                "low": [39000, 40000, 41000],
                "close": [40500, 41500, 42500],
                "volume": [1000, 1100, 1200],
                "rsi": [35, 40, 45],  # Bullish (oversold recovery)
                "macd": [50, 100, 150],
                "macdsignal": [60, 90, 120],  # Bullish crossover
                "ema_9": [40000, 41000, 42000],
                "ema_21": [39500, 40500, 41500],
                "ema_50": [39000, 40000, 41000],
            }
        )
        return df

    def test_fallback_predictor_creation(self, strategy):
        """Test fallback predictor is created"""
        predictor = strategy._create_simple_predictor()
        assert predictor is not None
        assert hasattr(predictor, "predict")
        assert hasattr(predictor, "prepare_features")

    def test_fallback_predictor_bullish(self, strategy, sample_dataframe):
        """Test fallback predictor detects bullish signal"""
        predictor = strategy._create_simple_predictor()

        result = predictor.predict(sample_dataframe)

        assert result["direction"] == 1  # Bullish
        assert result["confidence"] > 0.3  # Should show some confidence
        assert "RSI" in result["model_contributions"]
        assert "MACD" in result["model_contributions"]
        assert "EMA" in result["model_contributions"]

    def test_fallback_predictor_bearish(self, strategy):
        """Test fallback predictor detects bearish signal"""
        predictor = strategy._create_simple_predictor()

        # Create bearish dataframe
        df = pd.DataFrame(
            {
                "open": [42000, 41000, 40000],
                "high": [43000, 42000, 41000],
                "low": [41000, 40000, 39000],
                "close": [41500, 40500, 39500],
                "volume": [1000, 1100, 1200],
                "rsi": [75, 70, 65],  # Bearish (overbought)
                "macd": [50, 40, 30],
                "macdsignal": [40, 50, 60],  # Bearish crossover
                "ema_9": [42000, 41000, 40000],
                "ema_21": [42500, 41500, 40500],
                "ema_50": [43000, 42000, 41000],
            }
        )

        result = predictor.predict(df)

        assert result["direction"] == -1  # Bearish
        assert result["confidence"] > 0.5


class TestPopulateIndicators:
    """Test indicator population"""

    @pytest.fixture
    def strategy(self):
        config = {"stake_currency": "USDT", "stake_amount": 100, "dry_run": True}
        return HybridMLLLMStrategy(config)

    @pytest.fixture
    def sample_dataframe(self):
        """Create minimal OHLCV dataframe"""
        # Need 250+ periods for EMA_200 to have valid recent values
        dates = pd.date_range("2024-01-01", periods=300, freq="4h")
        df = pd.DataFrame(
            {
                "date": dates,
                "open": np.random.uniform(40000, 45000, 300),
                "high": np.random.uniform(45000, 50000, 300),
                "low": np.random.uniform(35000, 40000, 300),
                "close": np.random.uniform(40000, 45000, 300),
                "volume": np.random.uniform(1000, 5000, 300),
            }
        )
        return df

    def test_populate_indicators(self, strategy, sample_dataframe):
        """Test all required indicators are added"""
        metadata = {"pair": "BTC/USDT"}
        df = strategy.populate_indicators(sample_dataframe, metadata)

        # Check all required indicators exist
        required_indicators = [
            "rsi",
            "macd",
            "macdsignal",
            "macdhist",
            "bb_upper",
            "bb_middle",
            "bb_lower",
            "ema_9",
            "ema_21",
            "ema_50",
            "ema_200",
            "sma_200",
            "adx",
            "atr",
            "volume_sma",
        ]

        for indicator in required_indicators:
            assert indicator in df.columns, f"Missing indicator: {indicator}"

        # Check no NaN in recent data (after warmup period)
        recent_df = df.iloc[-50:]
        for indicator in required_indicators:
            assert not recent_df[indicator].isna().any(), f"NaN in {indicator}"


class TestPopulateEntryTrend:
    """Test entry signal generation"""

    @pytest.fixture
    def strategy(self):
        config = {"stake_currency": "USDT", "stake_amount": 100, "dry_run": True}
        return HybridMLLLMStrategy(config)

    @pytest.fixture
    def sample_dataframe_with_indicators(self):
        """Create dataframe with indicators"""
        dates = pd.date_range("2024-01-01", periods=100, freq="4h")
        df = pd.DataFrame(
            {
                "date": dates,
                "open": np.random.uniform(40000, 45000, 100),
                "high": np.random.uniform(45000, 50000, 100),
                "low": np.random.uniform(35000, 40000, 100),
                "close": np.random.uniform(40000, 45000, 100),
                "volume": np.random.uniform(1000, 5000, 100),
                "rsi": np.random.uniform(30, 70, 100),
                "macd": np.random.uniform(-100, 100, 100),
                "macdsignal": np.random.uniform(-100, 100, 100),
                "ema_9": np.random.uniform(40000, 45000, 100),
                "ema_21": np.random.uniform(40000, 45000, 100),
                "ema_50": np.random.uniform(40000, 45000, 100),
            }
        )
        return df

    def test_populate_entry_trend_no_signal(
        self, strategy, sample_dataframe_with_indicators
    ):
        """Test no entry when signal is weak"""
        metadata = {"pair": "BTC/USDT"}

        # Mock hybrid predictor to return WEAK signal
        mock_signal = HybridSignal(
            action="WAIT",
            strength=SignalStrength.WEAK,
            combined_confidence=0.50,
            ml_prediction=MLPrediction("up", 0.50, 0.01, 0.60, {}),
            llm_prediction=LLMPrediction("long", 0.50, "Weak", [], 0.55),
            agreement_score=0.55,
            recommended_position_size=0.0,
            reasoning="Weak signal",
        )

        with patch.object(
            strategy.hybrid_predictor, "generate_hybrid_signal", return_value=mock_signal
        ):
            df = strategy.populate_entry_trend(
                sample_dataframe_with_indicators, metadata
            )

            # Should not have enter_long signal
            if "enter_long" in df.columns:
                assert df["enter_long"].sum() == 0

    def test_populate_entry_trend_strong_signal(
        self, strategy, sample_dataframe_with_indicators
    ):
        """Test entry when signal is STRONG"""
        metadata = {"pair": "BTC/USDT"}

        # Mock hybrid predictor to return STRONG signal
        mock_signal = HybridSignal(
            action="ENTER_LONG",
            strength=SignalStrength.STRONG,
            combined_confidence=0.75,
            ml_prediction=MLPrediction("up", 0.75, 0.025, 0.80, {}),
            llm_prediction=LLMPrediction("long", 0.75, "Strong", [], 0.80),
            agreement_score=0.80,
            recommended_position_size=1.0,
            reasoning="Strong agreement",
        )

        with patch.object(
            strategy.hybrid_predictor, "generate_hybrid_signal", return_value=mock_signal
        ):
            df = strategy.populate_entry_trend(
                sample_dataframe_with_indicators, metadata
            )

            # Should have enter_long signal on last row
            assert "enter_long" in df.columns
            assert df["enter_long"].iloc[-1] == 1


class TestCustomStakeAmount:
    """Test custom position sizing"""

    @pytest.fixture
    def strategy(self):
        config = {"stake_currency": "USDT", "stake_amount": 100, "dry_run": True}
        strategy = HybridMLLLMStrategy(config)

        # Mock dataprovider
        strategy.dp = Mock()
        return strategy

    def test_position_sizing_very_strong(self, strategy):
        """Test position sizing for VERY_STRONG signal"""
        # Mock dataframe with position_size_multiplier
        df = pd.DataFrame(
            {
                "close": [42000],
                "position_size_multiplier": [1.4],  # VERY_STRONG = 1.2-1.5x
            }
        )
        strategy.dp.get_analyzed_dataframe = Mock(return_value=(df, None))

        adjusted = strategy.custom_stake_amount(
            pair="BTC/USDT",
            current_time=datetime.now(),
            current_rate=42000,
            proposed_stake=100,
            min_stake=10,
            max_stake=1000,
            leverage=1.0,
            entry_tag=None,
            side="long",
        )

        # Should be ~140 (100 * 1.4)
        assert 130 <= adjusted <= 150

    def test_position_sizing_strong(self, strategy):
        """Test position sizing for STRONG signal"""
        df = pd.DataFrame(
            {"close": [42000], "position_size_multiplier": [1.0]}  # STRONG = 1.0x
        )
        strategy.dp.get_analyzed_dataframe = Mock(return_value=(df, None))

        adjusted = strategy.custom_stake_amount(
            pair="BTC/USDT",
            current_time=datetime.now(),
            current_rate=42000,
            proposed_stake=100,
            min_stake=10,
            max_stake=1000,
            leverage=1.0,
            entry_tag=None,
            side="long",
        )

        # Should be ~100 (100 * 1.0)
        assert 95 <= adjusted <= 105

    def test_position_sizing_moderate(self, strategy):
        """Test position sizing for MODERATE signal"""
        df = pd.DataFrame(
            {
                "close": [42000],
                "position_size_multiplier": [0.6],  # MODERATE = 0.5-0.7x
            }
        )
        strategy.dp.get_analyzed_dataframe = Mock(return_value=(df, None))

        adjusted = strategy.custom_stake_amount(
            pair="BTC/USDT",
            current_time=datetime.now(),
            current_rate=42000,
            proposed_stake=100,
            min_stake=10,
            max_stake=1000,
            leverage=1.0,
            entry_tag=None,
            side="long",
        )

        # Should be ~60 (100 * 0.6)
        assert 50 <= adjusted <= 70

    def test_position_sizing_respects_max_stake(self, strategy):
        """Test position sizing respects max stake limit"""
        df = pd.DataFrame(
            {
                "close": [42000],
                "position_size_multiplier": [1.5],  # Very high multiplier
            }
        )
        strategy.dp.get_analyzed_dataframe = Mock(return_value=(df, None))

        adjusted = strategy.custom_stake_amount(
            pair="BTC/USDT",
            current_time=datetime.now(),
            current_rate=42000,
            proposed_stake=100,
            min_stake=10,
            max_stake=120,  # Lower max stake
            leverage=1.0,
            entry_tag=None,
            side="long",
        )

        # Should cap at 120
        assert adjusted == 120


class TestLazyLoading:
    """Test lazy loading of components"""

    @pytest.fixture
    def strategy(self):
        config = {"stake_currency": "USDT", "stake_amount": 100, "dry_run": True}
        return HybridMLLLMStrategy(config)

    def test_ensemble_model_lazy_loading(self, strategy):
        """Test ensemble model is loaded on first access"""
        assert strategy._ensemble_model is None

        # Access should trigger loading
        ensemble = strategy.ensemble_model

        assert ensemble is not None
        # Should create fallback predictor if model file doesn't exist
        assert hasattr(ensemble, "predict")

    def test_llm_orchestrator_lazy_loading(self, strategy):
        """Test LLM orchestrator is loaded on first access"""
        assert strategy._llm_orchestrator is None

        # Access should trigger loading
        orchestrator = strategy.llm_orchestrator

        assert orchestrator is not None

    def test_hybrid_predictor_lazy_loading(self, strategy):
        """Test hybrid predictor is loaded on first access"""
        assert strategy._hybrid_predictor is None

        # Access should trigger loading
        predictor = strategy.hybrid_predictor

        assert predictor is not None
        assert hasattr(predictor, "generate_hybrid_signal")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
