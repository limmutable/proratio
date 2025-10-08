"""
Tests for Dashboard Data Fetcher

Tests the data fetching utilities for the Streamlit dashboard.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from proratio_tradehub.dashboard.data_fetcher import (
    FreqtradeAPIClient,
    TradeDatabaseReader,
    DashboardDataFetcher,
)


class TestFreqtradeAPIClient:
    """Tests for Freqtrade API client"""

    def test_init(self):
        """Test client initialization"""
        client = FreqtradeAPIClient(base_url="http://localhost:8080")
        assert client.base_url == "http://localhost:8080"
        assert client.auth is None

    def test_init_with_auth(self):
        """Test client initialization with authentication"""
        client = FreqtradeAPIClient(
            base_url="http://localhost:8080",
            username="admin",
            password="secret"
        )
        assert client.auth == ("admin", "secret")

    @patch('requests.Session.get')
    def test_get_status_success(self, mock_get):
        """Test successful status retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {"state": "running"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = FreqtradeAPIClient()
        status = client.get_status()

        assert status == {"state": "running"}
        mock_get.assert_called_once()

    @patch('requests.Session.get')
    def test_get_status_error(self, mock_get):
        """Test status retrieval with error"""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        client = FreqtradeAPIClient()
        status = client.get_status()

        assert status == {}

    @patch('requests.Session.post')
    def test_force_exit_all(self, mock_post):
        """Test force exit all trades"""
        mock_response = Mock()
        mock_response.json.return_value = {"trades_closed": 3}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = FreqtradeAPIClient()
        result = client.force_exit_all()

        assert result == {"trades_closed": 3}

    @patch('requests.Session.post')
    def test_stop_trading(self, mock_post):
        """Test stop trading command"""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = FreqtradeAPIClient()
        result = client.stop_trading()

        assert result == {"status": "success"}


class TestTradeDatabaseReader:
    """Tests for trade database reader"""

    @pytest.fixture
    def mock_db_path(self, tmp_path):
        """Create a temporary database path"""
        db_path = tmp_path / "test.sqlite"
        return str(db_path)

    def test_init(self, mock_db_path):
        """Test database reader initialization"""
        reader = TradeDatabaseReader(db_path=mock_db_path)
        assert str(reader.db_path) == mock_db_path

    @patch('sqlite3.connect')
    @patch('pathlib.Path.exists')
    def test_get_all_trades(self, mock_exists, mock_connect):
        """Test retrieving all trades"""
        mock_exists.return_value = True

        # Mock cursor and connection
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("pair",), ("is_open",)]
        mock_cursor.fetchall.return_value = [
            (1, "BTC/USDT", 0),
            (2, "ETH/USDT", 0),
        ]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        reader = TradeDatabaseReader(db_path="test.db")
        trades = reader.get_all_trades(limit=100)

        assert len(trades) == 2
        assert trades[0]["pair"] == "BTC/USDT"
        assert trades[1]["pair"] == "ETH/USDT"

    @patch('sqlite3.connect')
    @patch('pathlib.Path.exists')
    def test_get_trade_statistics(self, mock_exists, mock_connect):
        """Test trade statistics calculation"""
        mock_exists.return_value = True

        # Mock cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            (100,),  # total_trades
            (65,),   # winning_trades
            (35,),   # losing_trades
            (1234.56,),  # total_profit
            (0.023,),    # avg_profit
            (-0.015,),   # avg_loss
        ]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        reader = TradeDatabaseReader(db_path="test.db")
        stats = reader.get_trade_statistics()

        assert stats["total_trades"] == 100
        assert stats["winning_trades"] == 65
        assert stats["losing_trades"] == 35
        assert stats["win_rate"] == 65.0
        assert stats["total_profit"] == 1234.56
        assert stats["avg_profit"] == 2.3
        assert stats["avg_loss"] == -1.5


class TestDashboardDataFetcher:
    """Tests for main dashboard data fetcher"""

    @pytest.fixture
    def mock_fetcher(self):
        """Create a data fetcher with mocked dependencies"""
        with patch('proratio_tradehub.dashboard.data_fetcher.FreqtradeAPIClient'), \
             patch('proratio_tradehub.dashboard.data_fetcher.TradeDatabaseReader'):
            fetcher = DashboardDataFetcher()
            return fetcher

    def test_init(self, mock_fetcher):
        """Test data fetcher initialization"""
        assert mock_fetcher.api is not None
        assert mock_fetcher.db is not None
        assert mock_fetcher.signal_orchestrator is None

    @patch('proratio_tradehub.dashboard.data_fetcher.SignalOrchestrator')
    def test_get_orchestrator(self, mock_orchestrator_class, mock_fetcher):
        """Test lazy loading of signal orchestrator"""
        orchestrator = mock_fetcher.get_orchestrator()
        assert orchestrator is not None
        assert mock_fetcher.signal_orchestrator is not None

    @patch('proratio_utilities.config.trading_config.TradingConfig.load_from_file')
    def test_get_trading_status(self, mock_load_config, mock_fetcher):
        """Test getting comprehensive trading status"""
        # Mock config
        mock_config = Mock()
        mock_config.risk.max_concurrent_positions = 3
        mock_config.risk.max_total_drawdown_pct = 0.10
        mock_load_config.return_value = mock_config

        # Mock API responses
        mock_fetcher.api.get_status.return_value = {"state": "running"}
        mock_fetcher.api.get_profit.return_value = {
            "profit_all_coin": 1234.56,
            "profit_all_ratio_mean": 0.1234
        }

        # Mock DB responses
        mock_fetcher.db.get_trade_statistics.return_value = {
            "total_trades": 100,
            "winning_trades": 65,
            "losing_trades": 35,
            "win_rate": 65.0,
            "avg_profit": 2.3,
            "avg_loss": -1.5,
        }
        mock_fetcher.db.get_open_trades.return_value = [{"id": 1}, {"id": 2}]

        status = mock_fetcher.get_trading_status()

        assert status["total_pnl"] == 1234.56
        assert status["total_pnl_pct"] == pytest.approx(12.34)
        assert status["win_rate"] == 65.0
        assert status["total_trades"] == 100
        assert status["open_positions"] == 2
        assert status["max_positions"] == 3
        assert status["trading_enabled"] is True

    def test_get_active_trades_detail(self, mock_fetcher):
        """Test getting detailed active trades"""
        # Mock API response
        mock_fetcher.api.get_open_trades.return_value = [
            {
                "pair": "BTC/USDT",
                "open_rate": 62500.00,
                "current_rate": 63200.00,
                "profit_ratio": 0.0112,
                "profit_abs": 112.00,
                "open_timestamp": 1696800000000,
                "trade_id": 1,
                "amount": 0.01,
            }
        ]

        trades = mock_fetcher.get_active_trades_detail()

        assert len(trades) == 1
        assert trades[0]["pair"] == "BTC/USDT"
        assert trades[0]["entry_price"] == 62500.00
        assert trades[0]["current_price"] == 63200.00
        assert trades[0]["pnl_pct"] == pytest.approx(1.12)
        assert trades[0]["pnl_usd"] == 112.00

    def test_emergency_stop_all(self, mock_fetcher):
        """Test emergency stop all function"""
        # Mock API responses
        mock_fetcher.api.force_exit_all.return_value = {"trades_closed": 3}
        mock_fetcher.api.stop_trading.return_value = {"status": "success"}

        result = mock_fetcher.emergency_stop_all()

        assert result["trades_closed"] == 3
        assert result["bot_stopped"] is True
        assert len(result["errors"]) == 0

    def test_emergency_stop_all_with_error(self, mock_fetcher):
        """Test emergency stop with error"""
        # Mock API to raise exception
        mock_fetcher.api.force_exit_all.side_effect = Exception("API error")

        result = mock_fetcher.emergency_stop_all()

        assert result["trades_closed"] == 0
        assert result["bot_stopped"] is False
        assert len(result["errors"]) > 0
