"""
Tests for Backtest Engine

Tests the backtest engine wrapper functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from pathlib import Path

from proratio_quantlab.backtesting.backtest_engine import (
    BacktestEngine,
    BacktestResults
)


class TestBacktestResults:
    """Test BacktestResults dataclass"""

    def test_creation(self):
        """Test BacktestResults creation"""
        result = BacktestResults(
            total_trades=50,
            winning_trades=30,
            losing_trades=20,
            win_rate=60.0,
            total_profit_pct=15.5,
            total_profit_abs=1550.0,
            avg_profit_pct=0.31,
            sharpe_ratio=1.8,
            sortino_ratio=2.1,
            max_drawdown_pct=8.5,
            max_drawdown_abs=850.0,
            avg_duration="12:30:00",
            best_trade_pct=5.2,
            worst_trade_pct=-3.1,
            strategy_name="TestStrategy",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 30),
            timeframe="1h",
            pairs=["BTC/USDT", "ETH/USDT"],
            raw_output="test output"
        )

        assert result.total_trades == 50
        assert result.win_rate == 60.0
        assert result.sharpe_ratio == 1.8
        assert result.strategy_name == "TestStrategy"

    def test_str_representation(self):
        """Test string representation"""
        result = BacktestResults(
            total_trades=50,
            winning_trades=30,
            losing_trades=20,
            win_rate=60.0,
            total_profit_pct=15.5,
            total_profit_abs=1550.0,
            avg_profit_pct=0.31,
            sharpe_ratio=1.8,
            sortino_ratio=2.1,
            max_drawdown_pct=8.5,
            max_drawdown_abs=850.0,
            avg_duration="12:30:00",
            best_trade_pct=5.2,
            worst_trade_pct=-3.1,
            strategy_name="TestStrategy",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 30),
            timeframe="1h",
            pairs=["BTC/USDT"],
            raw_output=""
        )

        result_str = str(result)
        assert "TestStrategy" in result_str
        assert "15.50%" in result_str  # Formatted with 2 decimals
        assert "1.80" in result_str  # Sharpe ratio


class TestBacktestEngine:
    """Test BacktestEngine class"""

    @pytest.fixture
    def engine(self):
        """Create engine with mocked paths"""
        with patch.object(Path, 'exists', return_value=True):
            engine = BacktestEngine()
            return engine

    def test_initialization(self, engine):
        """Test engine initialization"""
        assert engine.user_data_dir is not None
        assert engine.config_file is not None

    def test_initialization_missing_paths(self):
        """Test initialization with missing paths"""
        with patch.object(Path, 'exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                BacktestEngine()

    def test_parse_results_basic(self, engine):
        """Test parsing of backtest output"""
        sample_output = """
│    TOTAL │     45 │        -0.41 │         -18.371 │        -0.18 │     12:44:00 │   21     0    24  46.7 │

│ Total/Daily Avg Trades        │ 45 / 0.25                      │
│ Absolute profit               │ -18.371 USDT                   │
│ Total profit %                │ -0.18%                         │
│ Sharpe                        │ -1.03                          │
│ Sortino                       │ -1.85                          │
│ Max % of account underwater   │ 0.25%                          │
│ Best trade                    │ ETH/USDT 2.00%                 │
│ Worst trade                   │ ETH/USDT -4.50%                │
"""

        result = engine._parse_results(
            output=sample_output,
            strategy="TestStrategy",
            timeframe="1h",
            start_date="2024-01-01",
            end_date="2024-06-30",
            pairs=["BTC/USDT", "ETH/USDT"]
        )

        assert result.total_trades == 45
        assert result.winning_trades == 21
        assert result.losing_trades == 24
        assert result.win_rate == 46.7
        assert result.total_profit_pct == -0.18
        assert result.total_profit_abs == -18.371
        assert result.sharpe_ratio == -1.03
        assert result.sortino_ratio == -1.85
        assert result.max_drawdown_pct == 0.25
        assert result.best_trade_pct == 2.00
        assert result.worst_trade_pct == -4.50

    def test_parse_results_no_trades(self, engine):
        """Test parsing output with no trades"""
        sample_output = """
│    TOTAL │      0 │          0.0 │           0.000 │          0.0 │         0:00 │    0     0     0     0 │

│ Total/Daily Avg Trades        │ 0 / 0.00                       │
No trades made.
"""

        result = engine._parse_results(
            output=sample_output,
            strategy="TestStrategy",
            timeframe="1h",
            start_date="2024-01-01",
            end_date="2024-06-30",
            pairs=["BTC/USDT"]
        )

        assert result.total_trades == 0
        assert result.winning_trades == 0
        assert result.losing_trades == 0

    @patch('subprocess.run')
    def test_backtest_success(self, mock_run, engine):
        """Test successful backtest execution"""
        # Mock subprocess result
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """
│    TOTAL │     50 │         0.50 │          50.000 │          0.5 │     10:00:00 │   30     0    20  60.0 │
│ Total/Daily Avg Trades        │ 50 / 0.25                      │
│ Absolute profit               │ 50.000 USDT                    │
│ Total profit %                │ 0.50%                          │
│ Sharpe                        │ 1.50                           │
"""
        mock_run.return_value = mock_result

        result = engine.backtest(
            strategy="TestStrategy",
            timeframe="1h",
            start_date="2024-01-01",
            end_date="2024-06-30",
            pairs=["BTC/USDT"],
            timeout=10
        )

        assert result.total_trades == 50
        assert result.win_rate == 60.0
        assert mock_run.called

    @patch('subprocess.run')
    def test_backtest_failure(self, mock_run, engine):
        """Test backtest failure handling"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Strategy not found"
        mock_run.return_value = mock_result

        with pytest.raises(RuntimeError, match="Backtest failed"):
            engine.backtest(
                strategy="InvalidStrategy",
                timeframe="1h",
                start_date="2024-01-01",
                end_date="2024-06-30"
            )

    @patch('subprocess.run')
    def test_backtest_timeout(self, mock_run, engine):
        """Test backtest timeout"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="freqtrade", timeout=10)

        with pytest.raises(TimeoutError):
            engine.backtest(
                strategy="TestStrategy",
                timeframe="1h",
                start_date="2024-01-01",
                end_date="2024-06-30",
                timeout=10
            )

    def test_walk_forward_analysis_date_calculation(self, engine):
        """Test walk-forward date calculations"""
        # This would require mocking backtest calls
        # For now, test that the method exists and accepts parameters
        with patch.object(engine, 'backtest') as mock_backtest:
            mock_backtest.return_value = BacktestResults(
                total_trades=10,
                winning_trades=6,
                losing_trades=4,
                win_rate=60.0,
                total_profit_pct=5.0,
                total_profit_abs=500.0,
                avg_profit_pct=0.5,
                sharpe_ratio=1.5,
                sortino_ratio=1.8,
                max_drawdown_pct=5.0,
                max_drawdown_abs=500.0,
                avg_duration="10:00:00",
                best_trade_pct=2.0,
                worst_trade_pct=-1.5,
                strategy_name="TestStrategy",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 6, 30),
                timeframe="1h",
                pairs=["BTC/USDT"],
                raw_output=""
            )

            results = engine.walk_forward_analysis(
                strategy="TestStrategy",
                timeframe="1h",
                start_date="2024-01-01",
                end_date="2024-12-31",
                train_window_months=6,
                test_window_months=1
            )

            # Should create multiple windows
            assert len(results) > 0
            assert all(isinstance(r, BacktestResults) for r in results)

    @patch('subprocess.run')
    def test_compare_strategies(self, mock_run, engine):
        """Test strategy comparison"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """
│    TOTAL │     50 │         0.50 │          50.000 │          0.5 │     10:00:00 │   30     0    20  60.0 │
│ Total/Daily Avg Trades        │ 50 / 0.25                      │
│ Absolute profit               │ 50.000 USDT                    │
│ Total profit %                │ 0.50%                          │
│ Sharpe                        │ 1.50                           │
"""
        mock_run.return_value = mock_result

        results = engine.compare_strategies(
            strategies=["Strategy1", "Strategy2"],
            timeframe="1h",
            start_date="2024-01-01",
            end_date="2024-06-30"
        )

        assert len(results) == 2
        assert "Strategy1" in results
        assert "Strategy2" in results
