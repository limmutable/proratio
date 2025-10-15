"""
Unit Tests for HybridMLLLMPredictor

Tests the hybrid ML+LLM prediction engine including signal strength
classification, conflict resolution, and agreement scoring.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock

from proratio_signals.hybrid_predictor import (
    HybridMLLLMPredictor,
    MLPrediction,
    LLMPrediction,
    HybridSignal,
    SignalStrength,
)


class TestMLPrediction:
    """Test MLPrediction dataclass"""

    def test_ml_prediction_creation(self):
        """Test creating ML prediction"""
        pred = MLPrediction(
            direction="up",
            confidence=0.75,
            predicted_return=0.025,
            model_agreement=0.85,
            contributing_models={"LSTM": 0.02, "LightGBM": 0.03, "XGBoost": 0.025},
        )

        assert pred.direction == "up"
        assert pred.confidence == 0.75
        assert pred.predicted_return == 0.025
        assert pred.model_agreement == 0.85
        assert len(pred.contributing_models) == 3


class TestLLMPrediction:
    """Test LLMPrediction dataclass"""

    def test_llm_prediction_creation(self):
        """Test creating LLM prediction"""
        pred = LLMPrediction(
            direction="long",
            confidence=0.80,
            reasoning="Strong bullish momentum",
            key_factors=["RSI oversold", "MACD crossover"],
            provider_agreement=0.90,
        )

        assert pred.direction == "long"
        assert pred.confidence == 0.80
        assert "bullish" in pred.reasoning.lower()
        assert len(pred.key_factors) == 2
        assert pred.provider_agreement == 0.90


class TestHybridSignal:
    """Test HybridSignal dataclass"""

    def test_hybrid_signal_creation(self):
        """Test creating hybrid signal"""
        ml_pred = MLPrediction("up", 0.7, 0.02, 0.8, {})
        llm_pred = LLMPrediction("long", 0.75, "Bullish", [], 0.85)

        signal = HybridSignal(
            action="ENTER_LONG",
            strength=SignalStrength.STRONG,
            combined_confidence=0.73,
            ml_prediction=ml_pred,
            llm_prediction=llm_pred,
            agreement_score=0.82,
            recommended_position_size=1.0,
            reasoning="Strong agreement between ML and LLM",
        )

        assert signal.action == "ENTER_LONG"
        assert signal.strength == SignalStrength.STRONG
        assert signal.combined_confidence == 0.73
        assert signal.agreement_score == 0.82
        assert signal.recommended_position_size == 1.0


class TestHybridMLLLMPredictor:
    """Test HybridMLLLMPredictor core functionality"""

    @pytest.fixture
    def mock_ensemble(self):
        """Create mock ensemble model"""
        ensemble = Mock()
        ensemble.prepare_features = Mock(return_value=pd.DataFrame())
        ensemble.predict = Mock(
            return_value={
                "direction": 1,
                "confidence": 0.75,
                "predicted_return": 0.025,
                "model_contributions": {
                    "LSTM": 0.02,
                    "LightGBM": 0.03,
                    "XGBoost": 0.025,
                },
            }
        )
        return ensemble

    @pytest.fixture
    def mock_llm_orchestrator(self):
        """Create mock LLM orchestrator"""
        orchestrator = Mock()

        # Mock consensus signal
        mock_signal = Mock()
        mock_signal.direction = "long"
        mock_signal.confidence = 0.80
        mock_signal.combined_reasoning = "Strong bullish momentum with RSI oversold"

        orchestrator.generate_signal = Mock(return_value=mock_signal)
        return orchestrator

    @pytest.fixture
    def predictor(self, mock_ensemble, mock_llm_orchestrator):
        """Create hybrid predictor with mocks"""
        return HybridMLLLMPredictor(
            ensemble_model=mock_ensemble,
            llm_orchestrator=mock_llm_orchestrator,
            min_ml_confidence=0.60,
            min_llm_confidence=0.60,
            min_agreement_for_trade=0.70,
        )

    @pytest.fixture
    def sample_ohlcv(self):
        """Create sample OHLCV data"""
        dates = pd.date_range("2024-01-01", periods=100, freq="4h")
        df = pd.DataFrame(
            {
                "open": np.random.uniform(40000, 45000, 100),
                "high": np.random.uniform(45000, 50000, 100),
                "low": np.random.uniform(35000, 40000, 100),
                "close": np.random.uniform(40000, 45000, 100),
                "volume": np.random.uniform(1000, 5000, 100),
            },
            index=dates,
        )
        return df

    def test_predictor_initialization(self, predictor):
        """Test predictor initializes correctly"""
        assert predictor.min_ml_confidence == 0.60
        assert predictor.min_llm_confidence == 0.60
        assert predictor.min_agreement_for_trade == 0.70
        assert predictor.ensemble is not None
        assert predictor.llm_orchestrator is not None

    def test_normalize_llm_direction(self, predictor):
        """Test LLM direction normalization"""
        assert predictor._normalize_llm_direction("long") == "up"
        assert predictor._normalize_llm_direction("short") == "down"
        assert predictor._normalize_llm_direction("neutral") == "neutral"

    def test_calculate_agreement(self, predictor):
        """Test agreement calculation from predictions"""
        # Perfect agreement
        predictions = [0.75, 0.75, 0.75]
        agreement = predictor._calculate_agreement(predictions)
        assert agreement > 0.95  # Very high agreement

        # Some disagreement
        predictions = [0.5, 0.7, 0.9]
        agreement = predictor._calculate_agreement(predictions)
        assert 0.5 < agreement < 0.95

        # High disagreement
        predictions = [0.1, 0.5, 0.9]
        agreement = predictor._calculate_agreement(predictions)
        assert agreement < 0.55  # Slightly higher threshold for edge case

    def test_signal_strength_very_strong(self, predictor):
        """Test VERY_STRONG signal classification"""
        ml_pred = MLPrediction("up", 0.80, 0.03, 0.90, {})
        llm_pred = LLMPrediction("long", 0.80, "Strong", [], 0.90)

        strength = predictor._classify_signal_strength(
            ml_pred, llm_pred, directional_match=True, agreement_score=0.90
        )

        assert strength == SignalStrength.VERY_STRONG

    def test_signal_strength_strong(self, predictor):
        """Test STRONG signal classification"""
        ml_pred = MLPrediction("up", 0.70, 0.02, 0.75, {})
        llm_pred = LLMPrediction("long", 0.70, "Bullish", [], 0.75)

        strength = predictor._classify_signal_strength(
            ml_pred, llm_pred, directional_match=True, agreement_score=0.75
        )

        assert strength == SignalStrength.STRONG

    def test_signal_strength_moderate(self, predictor):
        """Test MODERATE signal classification"""
        ml_pred = MLPrediction("up", 0.75, 0.02, 0.70, {})
        llm_pred = LLMPrediction("long", 0.55, "Uncertain", [], 0.60)

        strength = predictor._classify_signal_strength(
            ml_pred, llm_pred, directional_match=True, agreement_score=0.65
        )

        assert strength == SignalStrength.MODERATE

    def test_signal_strength_weak(self, predictor):
        """Test WEAK signal classification"""
        ml_pred = MLPrediction("up", 0.50, 0.01, 0.60, {})
        llm_pred = LLMPrediction("long", 0.50, "Weak", [], 0.55)

        strength = predictor._classify_signal_strength(
            ml_pred, llm_pred, directional_match=True, agreement_score=0.55
        )

        assert strength == SignalStrength.WEAK

    def test_signal_strength_conflict(self, predictor):
        """Test CONFLICT signal classification"""
        ml_pred = MLPrediction("up", 0.75, 0.02, 0.80, {})
        llm_pred = LLMPrediction("short", 0.75, "Bearish", [], 0.80)

        strength = predictor._classify_signal_strength(
            ml_pred, llm_pred, directional_match=False, agreement_score=0.30
        )

        assert strength == SignalStrength.CONFLICT

    def test_determine_action_very_strong(self, predictor):
        """Test action for VERY_STRONG signal"""
        ml_pred = MLPrediction("up", 0.80, 0.03, 0.90, {})
        llm_pred = LLMPrediction("long", 0.80, "Strong", [], 0.90)

        action = predictor._determine_action(
            ml_pred, llm_pred, SignalStrength.VERY_STRONG, directional_match=True
        )

        assert action == "ENTER_LONG"

    def test_determine_action_conflict(self, predictor):
        """Test action for CONFLICT signal"""
        ml_pred = MLPrediction("up", 0.75, 0.02, 0.80, {})
        llm_pred = LLMPrediction("short", 0.75, "Bearish", [], 0.80)

        action = predictor._determine_action(
            ml_pred, llm_pred, SignalStrength.CONFLICT, directional_match=False
        )

        assert action == "WAIT_CONFLICT"

    def test_determine_action_weak(self, predictor):
        """Test action for WEAK signal"""
        ml_pred = MLPrediction("up", 0.50, 0.01, 0.60, {})
        llm_pred = LLMPrediction("long", 0.50, "Weak", [], 0.55)

        action = predictor._determine_action(
            ml_pred, llm_pred, SignalStrength.WEAK, directional_match=True
        )

        assert action == "WAIT"

    def test_calculate_combined_confidence(self, predictor):
        """Test combined confidence calculation"""
        ml_pred = MLPrediction("up", 0.70, 0.02, 0.75, {})
        llm_pred = LLMPrediction("long", 0.80, "Bullish", [], 0.85)

        # High agreement (should add bonus)
        combined = predictor._calculate_combined_confidence(
            ml_pred, llm_pred, agreement_score=0.85
        )

        # Base: 0.70 * 0.6 + 0.80 * 0.4 = 0.42 + 0.32 = 0.74
        # Agreement bonus: (0.85 - 0.5) * 0.4 = 0.14
        # Total: 0.74 + 0.14 = 0.88
        assert 0.85 <= combined <= 0.90

    def test_calculate_position_size(self, predictor):
        """Test position size calculation"""
        # VERY_STRONG: 1.2-1.5x
        size = predictor._calculate_position_size(
            SignalStrength.VERY_STRONG, combined_confidence=0.90
        )
        assert 1.2 <= size <= 1.5

        # STRONG: 1.0x
        size = predictor._calculate_position_size(
            SignalStrength.STRONG, combined_confidence=0.70
        )
        assert size == 1.0

        # MODERATE: 0.5-0.7x
        size = predictor._calculate_position_size(
            SignalStrength.MODERATE, combined_confidence=0.60
        )
        assert 0.5 <= size <= 0.7

        # WEAK: 0.0x
        size = predictor._calculate_position_size(
            SignalStrength.WEAK, combined_confidence=0.50
        )
        assert size == 0.0

    def test_generate_hybrid_signal(self, predictor, sample_ohlcv):
        """Test full hybrid signal generation"""
        signal = predictor.generate_hybrid_signal(
            pair="BTC/USDT", ohlcv_data=sample_ohlcv, market_context=None
        )

        # Verify signal structure
        assert isinstance(signal, HybridSignal)
        assert signal.action in [
            "ENTER_LONG",
            "ENTER_SHORT",
            "WAIT",
            "WAIT_CONFLICT",
        ]
        assert isinstance(signal.strength, SignalStrength)
        assert 0.0 <= signal.combined_confidence <= 1.0
        assert 0.0 <= signal.agreement_score <= 1.0
        assert signal.recommended_position_size >= 0.0
        assert len(signal.reasoning) > 0

    def test_ml_prediction_error_handling(self, predictor, sample_ohlcv):
        """Test ML prediction returns neutral on error"""
        # Make ensemble raise error
        predictor.ensemble.predict = Mock(side_effect=Exception("ML Error"))

        ml_pred = predictor._get_ml_prediction("BTC/USDT", sample_ohlcv)

        assert ml_pred.direction == "neutral"
        assert ml_pred.confidence == 0.0

    def test_llm_prediction_error_handling(self, predictor, sample_ohlcv):
        """Test LLM prediction returns neutral on error"""
        # Make orchestrator raise error
        predictor.llm_orchestrator.generate_signal = Mock(
            side_effect=Exception("LLM Error")
        )

        llm_pred = predictor._get_llm_prediction("BTC/USDT", sample_ohlcv, None)

        assert llm_pred.direction == "neutral"
        assert llm_pred.confidence == 0.0
        assert "Error" in llm_pred.reasoning

    def test_extract_key_factors(self, predictor):
        """Test extracting key factors from reasoning"""
        reasoning = """
        Analysis shows:
        • Strong bullish momentum
        • RSI oversold at 28
        • MACD bullish crossover
        • Volume increasing
        • Support level holding
        """

        factors = predictor._extract_key_factors(reasoning)

        assert len(factors) == 5
        assert "Strong bullish momentum" in factors
        assert "RSI oversold at 28" in factors

    def test_hybrid_agreement_directional_mismatch(self, predictor):
        """Test agreement score when directions don't match"""
        ml_pred = MLPrediction("up", 0.75, 0.02, 0.80, {})
        llm_pred = LLMPrediction("short", 0.75, "Bearish", [], 0.80)

        agreement = predictor._calculate_hybrid_agreement(
            ml_pred, llm_pred, directional_match=False
        )

        # Should be low due to directional mismatch
        assert agreement < 0.5

    def test_hybrid_agreement_directional_match(self, predictor):
        """Test agreement score when directions match"""
        ml_pred = MLPrediction("up", 0.75, 0.02, 0.80, {})
        llm_pred = LLMPrediction("long", 0.75, "Bullish", [], 0.80)

        agreement = predictor._calculate_hybrid_agreement(
            ml_pred, llm_pred, directional_match=True
        )

        # Should be high due to directional match + similar confidence
        assert agreement > 0.70


class TestSignalStrengthEnum:
    """Test SignalStrength enum"""

    def test_signal_strength_values(self):
        """Test all signal strength values exist"""
        assert SignalStrength.VERY_STRONG.value == "very_strong"
        assert SignalStrength.STRONG.value == "strong"
        assert SignalStrength.MODERATE.value == "moderate"
        assert SignalStrength.WEAK.value == "weak"
        assert SignalStrength.CONFLICT.value == "conflict"
        assert SignalStrength.NO_SIGNAL.value == "no_signal"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
