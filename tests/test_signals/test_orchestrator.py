"""
Tests for AI Signal Orchestrator

Tests the consensus mechanism, dynamic reweighting, and multi-provider coordination.
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from proratio_signals.orchestrator import SignalOrchestrator, ConsensusSignal
from proratio_signals.llm_providers.base import MarketAnalysis, OHLCVData


def create_sample_ohlcv() -> pd.DataFrame:
    """Create sample OHLCV data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    data = {
        'timestamp': dates,
        'open': [100 + i for i in range(100)],
        'high': [105 + i for i in range(100)],
        'low': [95 + i for i in range(100)],
        'close': [102 + i for i in range(100)],
        'volume': [1000 + i*10 for i in range(100)]
    }
    return pd.DataFrame(data)


def create_mock_analysis(direction: str, confidence: float, provider: str) -> MarketAnalysis:
    """Create mock MarketAnalysis for testing"""
    return MarketAnalysis(
        direction=direction,
        confidence=confidence,
        technical_summary=f"{provider} analysis",
        risk_assessment=f"{provider} risk assessment",
        sentiment="neutral",
        reasoning=f"{provider} reasoning",
        provider=provider,
        timestamp=datetime.now(),
        pair="BTC/USDT",
        timeframe="1h"
    )


class TestConsensusSignal:
    """Test ConsensusSignal dataclass"""

    def test_should_trade_yes(self):
        """Test should_trade returns True for strong signal"""
        signal = ConsensusSignal(
            direction='long',
            confidence=0.75,
            consensus_score=0.85,
            active_providers=['claude', 'gemini'],
            failed_providers=[],
            provider_models={'claude': 'test', 'gemini': 'test'}
        )

        assert signal.should_trade(threshold=0.6) is True

    def test_should_trade_no_low_confidence(self):
        """Test should_trade returns False for low confidence"""
        signal = ConsensusSignal(
            direction='long',
            confidence=0.45,
            consensus_score=0.80,
            active_providers=['claude'],
            failed_providers=[],
            provider_models={'claude': 'test'}
        )

        assert signal.should_trade(threshold=0.6) is False

    def test_should_trade_no_neutral(self):
        """Test should_trade returns False for neutral direction"""
        signal = ConsensusSignal(
            direction='neutral',
            confidence=0.75,
            consensus_score=0.85,
            active_providers=['claude', 'gemini'],
            failed_providers=[],
            provider_models={'claude': 'test', 'gemini': 'test'}
        )

        assert signal.should_trade(threshold=0.6) is False

    def test_get_provider_status_report(self):
        """Test provider status report generation"""
        signal = ConsensusSignal(
            direction='long',
            confidence=0.75,
            consensus_score=0.85,
            active_providers=['claude', 'gemini'],
            failed_providers=['chatgpt'],
            provider_models={
                'claude': 'claude-sonnet-4',
                'gemini': 'gemini-2.0-flash'
            }
        )

        report = signal.get_provider_status_report()

        assert "Active: 2/3" in report
        assert "claude: claude-sonnet-4" in report
        assert "gemini: gemini-2.0-flash" in report
        assert "Failed: chatgpt" in report


class TestConsensusCalculation:
    """Test consensus calculation logic"""

    def test_unanimous_long_signal(self):
        """Test consensus when all providers agree on LONG"""
        analyses = {
            'chatgpt': create_mock_analysis('long', 0.8, 'chatgpt'),
            'claude': create_mock_analysis('long', 0.7, 'claude'),
            'gemini': create_mock_analysis('long', 0.75, 'gemini')
        }

        orchestrator = SignalOrchestrator.__new__(SignalOrchestrator)
        orchestrator.WEIGHTS = {'chatgpt': 0.40, 'claude': 0.35, 'gemini': 0.25}

        signal = orchestrator._calculate_consensus(
            analyses, "BTC/USDT", "1h", [],
            {'chatgpt': 'gpt-5', 'claude': 'sonnet-4', 'gemini': 'gemini-2'}
        )

        assert signal.direction == 'long'
        assert signal.consensus_score == 1.0  # All agree
        # Weighted confidence: 0.8*0.4 + 0.7*0.35 + 0.75*0.25 = 0.7525
        assert abs(signal.confidence - 0.7525) < 0.01

    def test_split_signal(self):
        """Test consensus when providers disagree"""
        analyses = {
            'chatgpt': create_mock_analysis('long', 0.8, 'chatgpt'),
            'claude': create_mock_analysis('short', 0.7, 'claude'),
            'gemini': create_mock_analysis('neutral', 0.6, 'gemini')
        }

        orchestrator = SignalOrchestrator.__new__(SignalOrchestrator)
        orchestrator.WEIGHTS = {'chatgpt': 0.40, 'claude': 0.35, 'gemini': 0.25}

        signal = orchestrator._calculate_consensus(
            analyses, "BTC/USDT", "1h", [],
            {'chatgpt': 'gpt-5', 'claude': 'sonnet-4', 'gemini': 'gemini-2'}
        )

        # ChatGPT has 40% weight for 'long', Claude 35% for 'short', Gemini 25% for 'neutral'
        assert signal.direction == 'long'  # Highest weight
        assert signal.consensus_score == 0.40  # Only 40% agree

    def test_dynamic_reweighting_one_provider(self):
        """Test dynamic reweighting with only one provider"""
        analyses = {
            'claude': create_mock_analysis('long', 0.7, 'claude')
        }

        orchestrator = SignalOrchestrator.__new__(SignalOrchestrator)
        orchestrator.WEIGHTS = {'chatgpt': 0.40, 'claude': 0.35, 'gemini': 0.25}

        signal = orchestrator._calculate_consensus(
            analyses, "BTC/USDT", "1h", ['chatgpt', 'gemini'],
            {'claude': 'sonnet-4'}
        )

        # Claude's 35% should be reweighted to 100%
        assert signal.direction == 'long'
        assert signal.consensus_score == 1.0  # Only one provider, so 100% consensus
        assert signal.confidence == 0.7  # Claude's confidence
        assert signal.failed_providers == ['chatgpt', 'gemini']

    def test_dynamic_reweighting_two_providers(self):
        """Test dynamic reweighting with two providers"""
        analyses = {
            'claude': create_mock_analysis('long', 0.7, 'claude'),
            'gemini': create_mock_analysis('long', 0.6, 'gemini')
        }

        orchestrator = SignalOrchestrator.__new__(SignalOrchestrator)
        orchestrator.WEIGHTS = {'chatgpt': 0.40, 'claude': 0.35, 'gemini': 0.25}

        signal = orchestrator._calculate_consensus(
            analyses, "BTC/USDT", "1h", ['chatgpt'],
            {'claude': 'sonnet-4', 'gemini': 'gemini-2'}
        )

        # Original: Claude 35%, Gemini 25% = 60% total
        # Reweighted: Claude 35/60 = 58.3%, Gemini 25/60 = 41.7%
        # Confidence: 0.7 * 0.583 + 0.6 * 0.417 = 0.408 + 0.250 = 0.658
        assert signal.direction == 'long'
        assert abs(signal.confidence - 0.658) < 0.01
        assert len(signal.active_providers) == 2

    def test_no_providers_available(self):
        """Test consensus when no providers are available"""
        analyses = {}

        orchestrator = SignalOrchestrator.__new__(SignalOrchestrator)
        orchestrator.WEIGHTS = {'chatgpt': 0.40, 'claude': 0.35, 'gemini': 0.25}

        signal = orchestrator._calculate_consensus(
            analyses, "BTC/USDT", "1h", ['chatgpt', 'claude', 'gemini'], {}
        )

        assert signal.direction == 'neutral'
        assert signal.confidence == 0.0
        assert signal.consensus_score == 0.0
        assert "No AI providers available" in signal.combined_reasoning


class TestOrchestrator:
    """Test SignalOrchestrator end-to-end"""

    @patch('proratio_signals.orchestrator.ChatGPTProvider')
    @patch('proratio_signals.orchestrator.ClaudeProvider')
    @patch('proratio_signals.orchestrator.GeminiProvider')
    @patch('proratio_signals.orchestrator.get_settings')
    def test_initialization_all_providers(self, mock_settings, mock_gemini, mock_claude, mock_chatgpt):
        """Test orchestrator initialization with all providers"""
        # Mock settings
        mock_settings.return_value = MagicMock(
            openai_api_key='sk-test',
            anthropic_api_key='sk-ant-test',
            gemini_api_key='test-key'
        )

        orchestrator = SignalOrchestrator()

        assert len(orchestrator.providers) == 3
        assert 'chatgpt' in orchestrator.providers
        assert 'claude' in orchestrator.providers
        assert 'gemini' in orchestrator.providers

    @patch('proratio_signals.orchestrator.get_settings')
    def test_initialization_no_providers(self, mock_settings):
        """Test orchestrator initialization with no valid API keys"""
        mock_settings.return_value = MagicMock(
            openai_api_key=None,
            anthropic_api_key=None,
            gemini_api_key=None
        )

        with pytest.raises(ValueError, match="No AI providers initialized"):
            SignalOrchestrator()

    def test_weights_sum_to_one(self):
        """Test that provider weights sum to 1.0"""
        total_weight = sum(SignalOrchestrator.WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.001  # Allow for floating point errors


class TestCombiningMethods:
    """Test reasoning/risk/technical summary combination methods"""

    def test_combine_reasoning(self):
        """Test combining reasoning from multiple providers"""
        analyses = {
            'chatgpt': create_mock_analysis('long', 0.8, 'chatgpt'),
            'claude': create_mock_analysis('long', 0.7, 'claude')
        }

        orchestrator = SignalOrchestrator.__new__(SignalOrchestrator)
        orchestrator.WEIGHTS = {'chatgpt': 0.40, 'claude': 0.35, 'gemini': 0.25}

        combined = orchestrator._combine_reasoning(analyses)

        assert 'CHATGPT' in combined
        assert 'CLAUDE' in combined
        assert '40%' in combined
        assert '35%' in combined

    def test_combine_risk_assessments(self):
        """Test combining risk assessments"""
        analyses = {
            'claude': create_mock_analysis('long', 0.7, 'claude'),
            'gemini': create_mock_analysis('long', 0.6, 'gemini')
        }

        orchestrator = SignalOrchestrator.__new__(SignalOrchestrator)

        combined = orchestrator._combine_risk_assessments(analyses)

        assert 'claude' in combined
        assert 'gemini' in combined
        assert 'risk assessment' in combined.lower()

    def test_combine_technical_summaries(self):
        """Test combining technical summaries"""
        analyses = {
            'chatgpt': create_mock_analysis('long', 0.8, 'chatgpt'),
            'claude': create_mock_analysis('long', 0.7, 'claude')
        }

        orchestrator = SignalOrchestrator.__new__(SignalOrchestrator)

        combined = orchestrator._combine_technical_summaries(analyses)

        assert 'chatgpt' in combined
        assert 'claude' in combined
        assert 'analysis' in combined.lower()
