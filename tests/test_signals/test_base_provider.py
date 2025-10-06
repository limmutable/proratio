"""
Tests for Base LLM Provider

Tests the abstract base class and common functionality for all LLM providers.
"""

import pytest
import pandas as pd
from datetime import datetime
from proratio_signals.llm_providers.base import (
    BaseLLMProvider,
    MarketAnalysis,
    OHLCVData
)


class MockLLMProvider(BaseLLMProvider):
    """Mock implementation for testing"""

    @property
    def provider_name(self) -> str:
        return "mock"

    def _validate_api_key(self) -> None:
        if not self.api_key or len(self.api_key) < 5:
            raise ValueError("Invalid API key")

    def _call_api(self, prompt: str) -> str:
        return "Mock response: LONG signal with high confidence"

    def analyze_market(self, ohlcv_data, prompt_template, additional_context=None):
        response = self._call_api(prompt_template)
        return self._parse_response(response, ohlcv_data)


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


class TestOHLCVData:
    """Test OHLCVData container"""

    def test_creation(self):
        """Test OHLCVData creation"""
        df = create_sample_ohlcv()
        ohlcv = OHLCVData(
            pair="BTC/USDT",
            timeframe="1h",
            data=df,
            indicators={'RSI': 50.0, 'EMA_20': 100.5}
        )

        assert ohlcv.pair == "BTC/USDT"
        assert ohlcv.timeframe == "1h"
        assert len(ohlcv.data) == 100
        assert ohlcv.indicators['RSI'] == 50.0

    def test_to_summary_text(self):
        """Test conversion to summary text"""
        df = create_sample_ohlcv()
        ohlcv = OHLCVData(
            pair="BTC/USDT",
            timeframe="1h",
            data=df,
            indicators={'RSI': 50.0, 'MACD': 2.5}
        )

        summary = ohlcv.to_summary_text(lookback=20)

        assert "BTC/USDT" in summary
        assert "1h" in summary
        assert "RSI: 50.00" in summary
        assert "MACD: 2.50" in summary
        assert "Current Price:" in summary


class TestMarketAnalysis:
    """Test MarketAnalysis dataclass"""

    def test_creation(self):
        """Test MarketAnalysis creation"""
        analysis = MarketAnalysis(
            direction='long',
            confidence=0.8,
            technical_summary="Strong uptrend",
            risk_assessment="Low risk",
            sentiment="bullish",
            reasoning="EMA crossover + high volume",
            provider="test",
            timestamp=datetime.now(),
            pair="BTC/USDT",
            timeframe="1h"
        )

        assert analysis.direction == 'long'
        assert analysis.confidence == 0.8
        assert analysis.provider == "test"

    def test_validation(self):
        """Test that all required fields are present"""
        with pytest.raises(TypeError):
            MarketAnalysis(direction='long')  # Missing required fields


class TestBaseLLMProvider:
    """Test BaseLLMProvider functionality"""

    def test_initialization_valid_key(self):
        """Test provider initialization with valid API key"""
        provider = MockLLMProvider(api_key="valid_key_123")
        assert provider.api_key == "valid_key_123"
        assert provider.provider_name == "mock"

    def test_initialization_invalid_key(self):
        """Test provider initialization with invalid API key"""
        with pytest.raises(ValueError, match="Invalid API key"):
            MockLLMProvider(api_key="bad")

    def test_parse_response_long_signal(self):
        """Test response parsing for LONG signal"""
        provider = MockLLMProvider(api_key="test_key_12345")
        df = create_sample_ohlcv()
        ohlcv = OHLCVData(pair="BTC/USDT", timeframe="1h", data=df)

        response = "This is a strong LONG signal with high confidence. Buy recommended."
        analysis = provider._parse_response(response, ohlcv)

        assert analysis.direction == 'long'
        assert analysis.confidence > 0.5
        assert analysis.pair == "BTC/USDT"

    def test_parse_response_short_signal(self):
        """Test response parsing for SHORT signal"""
        provider = MockLLMProvider(api_key="test_key_12345")
        df = create_sample_ohlcv()
        ohlcv = OHLCVData(pair="BTC/USDT", timeframe="1h", data=df)

        response = "Bearish signal detected. Sell recommended with short position."
        analysis = provider._parse_response(response, ohlcv)

        assert analysis.direction == 'short'
        assert analysis.pair == "BTC/USDT"

    def test_parse_response_neutral_signal(self):
        """Test response parsing for NEUTRAL signal"""
        provider = MockLLMProvider(api_key="test_key_12345")
        df = create_sample_ohlcv()
        ohlcv = OHLCVData(pair="BTC/USDT", timeframe="1h", data=df)

        response = "Market conditions are unclear. No clear signal."
        analysis = provider._parse_response(response, ohlcv)

        assert analysis.direction == 'neutral'

    def test_test_connection(self):
        """Test connection testing"""
        provider = MockLLMProvider(api_key="test_key_12345")
        result = provider.test_connection()
        assert result is True


class TestProviderAnalyzeMarket:
    """Test analyze_market method"""

    def test_analyze_market_basic(self):
        """Test basic market analysis"""
        provider = MockLLMProvider(api_key="test_key_12345")
        df = create_sample_ohlcv()
        ohlcv = OHLCVData(pair="BTC/USDT", timeframe="1h", data=df)

        analysis = provider.analyze_market(
            ohlcv_data=ohlcv,
            prompt_template="Analyze this: {market_data}"
        )

        assert isinstance(analysis, MarketAnalysis)
        assert analysis.provider == "mock"
        assert analysis.direction in ['long', 'short', 'neutral']

    def test_analyze_market_with_indicators(self):
        """Test market analysis with technical indicators"""
        provider = MockLLMProvider(api_key="test_key_12345")
        df = create_sample_ohlcv()
        ohlcv = OHLCVData(
            pair="BTC/USDT",
            timeframe="1h",
            data=df,
            indicators={'RSI': 65.0, 'MACD': 1.5}
        )

        analysis = provider.analyze_market(
            ohlcv_data=ohlcv,
            prompt_template="Analyze {pair} on {timeframe}: {market_data}"
        )

        assert analysis.pair == "BTC/USDT"
        assert analysis.timeframe == "1h"
