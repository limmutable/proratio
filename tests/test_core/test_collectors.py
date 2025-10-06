"""
Tests for data collectors module.
"""

import pytest
from datetime import datetime, timedelta
from proratio_core.data.collectors import BinanceCollector


class TestBinanceCollector:
    """Tests for BinanceCollector"""

    def test_init(self):
        """Test collector initialization"""
        collector = BinanceCollector(testnet=False)
        assert collector.exchange is not None
        assert collector.exchange.name == 'Binance'

    def test_parse_timeframe_to_seconds(self):
        """Test timeframe parsing"""
        collector = BinanceCollector()

        assert collector._parse_timeframe_to_seconds('1m') == 60
        assert collector._parse_timeframe_to_seconds('5m') == 300
        assert collector._parse_timeframe_to_seconds('1h') == 3600
        assert collector._parse_timeframe_to_seconds('4h') == 14400
        assert collector._parse_timeframe_to_seconds('1d') == 86400

    @pytest.mark.skipif(
        True,
        reason="Requires API keys and network connection"
    )
    def test_fetch_ohlcv(self):
        """Test fetching OHLCV data (requires API keys)"""
        collector = BinanceCollector()
        data = collector.fetch_ohlcv('BTC/USDT', '1h', limit=10)

        assert isinstance(data, list)
        assert len(data) <= 10

        # Check data structure
        if data:
            first = data[0]
            assert len(first) == 6
            assert isinstance(first[0], datetime)  # timestamp
            assert isinstance(first[1], (int, float))  # open

    @pytest.mark.skipif(
        True,
        reason="Requires API keys and network connection"
    )
    def test_connection(self):
        """Test exchange connection (requires API keys)"""
        collector = BinanceCollector()
        assert collector.test_connection() is True
