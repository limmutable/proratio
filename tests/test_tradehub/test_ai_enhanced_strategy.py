"""
Tests for AIEnhancedStrategy

Tests the AI-enhanced Freqtrade strategy with mocked AI signals.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch
import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from user_data.strategies.AIEnhancedStrategy import AIEnhancedStrategy
from proratio_signals import ConsensusSignal


class TestAIEnhancedStrategy:
    """Test suite for AIEnhancedStrategy"""

    @pytest.fixture
    def strategy(self):
        """Create strategy instance with mocked AI"""
        config = {
            "stake_currency": "USDT",
            "stake_amount": 100,
            "dry_run": True,
        }

        with patch("user_data.strategies.AIEnhancedStrategy.SignalOrchestrator"):
            strategy = AIEnhancedStrategy(config)
            strategy.ai_enabled = True  # Enable AI for tests
            strategy.ai_orchestrator = Mock()
            return strategy

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample OHLCV dataframe"""
        dates = pd.date_range(start="2024-01-01", periods=200, freq="1h")
        df = pd.DataFrame(
            {
                "date": dates,
                "open": [100.0 + i * 0.1 for i in range(200)],
                "high": [101.0 + i * 0.1 for i in range(200)],
                "low": [99.0 + i * 0.1 for i in range(200)],
                "close": [100.5 + i * 0.1 for i in range(200)],
                "volume": [1000000 + i * 1000 for i in range(200)],
            }
        )
        df.set_index("date", inplace=True)
        return df

    @pytest.fixture
    def mock_long_signal(self):
        """Create mock LONG consensus signal"""
        return ConsensusSignal(
            direction="long",
            confidence=0.75,
            consensus_score=0.80,
            combined_reasoning="Strong bullish trend detected",
            risk_summary="Moderate risk",
            technical_summary="Bullish indicators",
            timestamp=datetime.now(timezone.utc),
            pair="BTC/USDT",
            timeframe="1h",
            active_providers=["claude", "gemini"],
            failed_providers=[],
            provider_models={"claude": "sonnet-4", "gemini": "gemini-2.0"},
        )

    @pytest.fixture
    def mock_short_signal(self):
        """Create mock SHORT consensus signal"""
        return ConsensusSignal(
            direction="short",
            confidence=0.70,
            consensus_score=0.75,
            combined_reasoning="Bearish reversal detected",
            risk_summary="High risk",
            technical_summary="Bearish indicators",
            timestamp=datetime.now(timezone.utc),
            pair="BTC/USDT",
            timeframe="1h",
            active_providers=["claude", "gemini"],
            failed_providers=[],
            provider_models={"claude": "sonnet-4", "gemini": "gemini-2.0"},
        )

    def test_strategy_initialization(self, strategy):
        """Test strategy initializes correctly"""
        assert strategy.ai_enabled is True
        assert strategy.ai_orchestrator is not None
        assert strategy.timeframe == "1h"
        assert strategy.ai_min_confidence == 0.60
        assert strategy.ai_lookback_candles == 50

    def test_populate_indicators(self, strategy, sample_dataframe):
        """Test technical indicators are added"""
        metadata = {"pair": "BTC/USDT"}
        df = strategy.populate_indicators(sample_dataframe.copy(), metadata)

        # Check all indicators exist
        assert "ema_fast" in df.columns
        assert "ema_slow" in df.columns
        assert "rsi" in df.columns
        assert "volume_mean" in df.columns
        assert "atr" in df.columns
        assert "adx" in df.columns
        assert "bb_upper" in df.columns
        assert "bb_middle" in df.columns
        assert "bb_lower" in df.columns

        # Check values are calculated (not NaN for most recent candles)
        assert not pd.isna(df["ema_fast"].iloc[-1])
        assert not pd.isna(df["rsi"].iloc[-1])

    def test_get_ai_signal_success(self, strategy, sample_dataframe, mock_long_signal):
        """Test AI signal generation succeeds"""
        strategy.ai_orchestrator.generate_signal.return_value = mock_long_signal
        metadata = {"pair": "BTC/USDT"}

        # Populate indicators first (required for AI context)
        df = strategy.populate_indicators(sample_dataframe.copy(), metadata)

        # Get AI signal
        signal = strategy.get_ai_signal(df, metadata)

        assert signal is not None
        assert signal.direction == "long"
        assert signal.confidence == 0.75
        assert strategy.ai_orchestrator.generate_signal.called

    def test_get_ai_signal_caching(self, strategy, sample_dataframe, mock_long_signal):
        """Test AI signal is cached to avoid API spam"""
        strategy.ai_orchestrator.generate_signal.return_value = mock_long_signal
        metadata = {"pair": "BTC/USDT"}

        df = strategy.populate_indicators(sample_dataframe.copy(), metadata)

        # First call should hit API
        signal1 = strategy.get_ai_signal(df, metadata)
        assert strategy.ai_orchestrator.generate_signal.call_count == 1

        # Second call within cache window should NOT hit API
        signal2 = strategy.get_ai_signal(df, metadata)
        assert strategy.ai_orchestrator.generate_signal.call_count == 1  # Still 1

        # Both signals should be identical
        assert signal1 == signal2

    def test_get_ai_signal_disabled(self, strategy, sample_dataframe):
        """Test AI signal returns None when AI disabled"""
        strategy.ai_enabled = False
        metadata = {"pair": "BTC/USDT"}

        df = strategy.populate_indicators(sample_dataframe.copy(), metadata)
        signal = strategy.get_ai_signal(df, metadata)

        assert signal is None
        assert not strategy.ai_orchestrator.generate_signal.called

    def test_populate_entry_trend_with_ai_long(
        self, strategy, sample_dataframe, mock_long_signal
    ):
        """Test entry signal with AI LONG consensus"""
        strategy.ai_orchestrator.generate_signal.return_value = mock_long_signal
        metadata = {"pair": "BTC/USDT"}

        # Populate indicators
        df = strategy.populate_indicators(sample_dataframe.copy(), metadata)

        # Create favorable technical conditions for entry
        # Simulate EMA crossover (fast crosses above slow)
        df.loc[df.index[-1], "ema_fast"] = 105.0
        df.loc[df.index[-1], "ema_slow"] = 100.0
        df.loc[df.index[-2], "ema_fast"] = 99.0  # Was below
        df.loc[df.index[-2], "ema_slow"] = 100.0

        df.loc[df.index[-1], "rsi"] = 50.0  # Neutral RSI
        df.loc[df.index[-1], "volume"] = (
            df.loc[df.index[-1], "volume_mean"] * 1.5
        )  # High volume
        df.loc[df.index[-1], "adx"] = 25.0  # Trending market

        # Populate entry trend
        df = strategy.populate_entry_trend(df, metadata)

        # Should have entry signals
        assert "enter_long" in df.columns
        # At least the last candle should have an entry signal
        assert df["enter_long"].iloc[-1] == 1

    def test_populate_entry_trend_no_ai_short(
        self, strategy, sample_dataframe, mock_short_signal
    ):
        """Test entry rejected when AI says SHORT"""
        strategy.ai_orchestrator.generate_signal.return_value = mock_short_signal
        metadata = {"pair": "BTC/USDT"}

        df = strategy.populate_indicators(sample_dataframe.copy(), metadata)

        # Create favorable technical conditions
        df["ema_fast"] = 105.0
        df["ema_slow"] = 100.0
        df["rsi"] = 50.0
        df["volume"] = df["volume_mean"] * 1.5
        df["adx"] = 25.0

        # Populate entry trend
        df = strategy.populate_entry_trend(df, metadata)

        # Should NOT have entry signals (AI says SHORT)
        assert df["enter_long"].sum() == 0

    def test_populate_exit_trend_with_ai_short(
        self, strategy, sample_dataframe, mock_short_signal
    ):
        """Test exit signal when AI changes to SHORT"""
        strategy.ai_orchestrator.generate_signal.return_value = mock_short_signal
        metadata = {"pair": "BTC/USDT"}

        df = strategy.populate_indicators(sample_dataframe.copy(), metadata)

        # Populate exit trend
        df = strategy.populate_exit_trend(df, metadata)

        # Should have exit signals (AI says SHORT with confidence > 65%)
        assert "exit_long" in df.columns
        assert df["exit_long"].sum() > 0

    def test_custom_stake_amount_high_confidence(self, strategy, mock_long_signal):
        """Test position sizing increases with high AI confidence"""
        # Create high confidence signal (90%)
        high_confidence_signal = ConsensusSignal(
            direction="long",
            confidence=0.90,  # 90% confidence should give multiplier > 1.0
            consensus_score=0.90,
            combined_reasoning="Very strong signal",
            timestamp=datetime.now(timezone.utc),
            pair="BTC/USDT",
            timeframe="1h",
            active_providers=["claude", "gemini", "chatgpt"],
            failed_providers=[],
            provider_models={
                "claude": "sonnet-4",
                "gemini": "gemini-2.0",
                "chatgpt": "gpt-5",
            },
        )

        # Cache AI signal
        strategy.ai_signal_cache["BTC/USDT"] = {
            "signal": high_confidence_signal,
            "timestamp": datetime.now(timezone.utc),
        }

        proposed_stake = 100.0
        adjusted_stake = strategy.custom_stake_amount(
            pair="BTC/USDT",
            current_time=datetime.now(timezone.utc),
            current_rate=50000.0,
            proposed_stake=proposed_stake,
            min_stake=10.0,
            max_stake=500.0,
            leverage=1.0,
            entry_tag=None,
            side="long",
        )

        # 90% confidence should increase stake (> base stake)
        # Formula: (0.9-0.6)/(1-0.6) = 0.75, multiplier = 0.8 + 0.75*0.4 = 1.1x
        assert adjusted_stake > proposed_stake
        assert adjusted_stake <= 120.0  # Max multiplier is 1.2x

    def test_custom_stake_amount_low_confidence(self, strategy):
        """Test position sizing decreases with low AI confidence"""
        low_confidence_signal = ConsensusSignal(
            direction="long",
            confidence=0.62,  # Just above minimum
            consensus_score=0.65,
            combined_reasoning="Weak signal",
            timestamp=datetime.now(timezone.utc),
            pair="BTC/USDT",
            timeframe="1h",
            active_providers=["claude"],
            failed_providers=["chatgpt", "gemini"],
            provider_models={"claude": "sonnet-4"},
        )

        strategy.ai_signal_cache["BTC/USDT"] = {
            "signal": low_confidence_signal,
            "timestamp": datetime.now(timezone.utc),
        }

        proposed_stake = 100.0
        adjusted_stake = strategy.custom_stake_amount(
            pair="BTC/USDT",
            current_time=datetime.now(timezone.utc),
            current_rate=50000.0,
            proposed_stake=proposed_stake,
            min_stake=10.0,
            max_stake=500.0,
            leverage=1.0,
            entry_tag=None,
            side="long",
        )

        # Low confidence should decrease stake
        assert adjusted_stake < proposed_stake
        assert adjusted_stake >= 80.0  # Min multiplier is 0.8x

    def test_confirm_trade_entry_valid_signal(self, strategy, mock_long_signal):
        """Test trade entry confirmed with valid AI signal"""
        strategy.ai_signal_cache["BTC/USDT"] = {
            "signal": mock_long_signal,
            "timestamp": datetime.now(timezone.utc),
        }

        confirmed = strategy.confirm_trade_entry(
            pair="BTC/USDT",
            order_type="limit",
            amount=1.0,
            rate=50000.0,
            time_in_force="GTC",
            current_time=datetime.now(timezone.utc),
            entry_tag=None,
            side="long",
        )

        assert confirmed is True

    def test_confirm_trade_entry_low_confidence(self, strategy):
        """Test trade entry rejected when confidence drops"""
        low_confidence_signal = ConsensusSignal(
            direction="long",
            confidence=0.55,  # Below minimum threshold
            consensus_score=0.60,
            combined_reasoning="Weak signal",
            timestamp=datetime.now(timezone.utc),
            pair="BTC/USDT",
            timeframe="1h",
            active_providers=["claude"],
            failed_providers=[],
            provider_models={"claude": "sonnet-4"},
        )

        strategy.ai_signal_cache["BTC/USDT"] = {
            "signal": low_confidence_signal,
            "timestamp": datetime.now(timezone.utc),
        }

        confirmed = strategy.confirm_trade_entry(
            pair="BTC/USDT",
            order_type="limit",
            amount=1.0,
            rate=50000.0,
            time_in_force="GTC",
            current_time=datetime.now(timezone.utc),
            entry_tag=None,
            side="long",
        )

        assert confirmed is False

    def test_confirm_trade_entry_wrong_direction(self, strategy, mock_short_signal):
        """Test trade entry rejected when AI direction changes"""
        strategy.ai_signal_cache["BTC/USDT"] = {
            "signal": mock_short_signal,  # Direction = SHORT
            "timestamp": datetime.now(timezone.utc),
        }

        confirmed = strategy.confirm_trade_entry(
            pair="BTC/USDT",
            order_type="limit",
            amount=1.0,
            rate=50000.0,
            time_in_force="GTC",
            current_time=datetime.now(timezone.utc),
            entry_tag=None,
            side="long",
        )

        assert confirmed is False
