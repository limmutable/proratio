"""
Backtest Engine Wrapper

Provides a clean Python API for running Freqtrade backtests with support for:
- Strategy backtesting
- Walk-forward analysis
- Hyperparameter optimization
- Performance comparison
- Result parsing and analysis
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd


@dataclass
class BacktestResults:
    """Container for backtest results"""

    # Summary metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # Profitability
    total_profit_pct: float
    total_profit_abs: float
    avg_profit_pct: float

    # Risk metrics
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    max_drawdown_abs: float

    # Trade metrics
    avg_duration: str
    best_trade_pct: float
    worst_trade_pct: float

    # Strategy info
    strategy_name: str
    start_date: datetime
    end_date: datetime
    timeframe: str
    pairs: List[str]

    # Raw data
    raw_output: str
    trades_df: Optional[pd.DataFrame] = None

    def __str__(self) -> str:
        """Human-readable summary"""
        return f"""
Backtest Results: {self.strategy_name}
{'=' * 60}
Period: {self.start_date.date()} to {self.end_date.date()}
Timeframe: {self.timeframe}
Pairs: {', '.join(self.pairs)}

Performance:
  Total Profit: {self.total_profit_pct:+.2f}% (${self.total_profit_abs:,.2f})
  Total Trades: {self.total_trades}
  Win Rate: {self.win_rate:.1f}% ({self.winning_trades}W / {self.losing_trades}L)

Risk Metrics:
  Sharpe Ratio: {self.sharpe_ratio:.2f}
  Sortino Ratio: {self.sortino_ratio:.2f}
  Max Drawdown: {self.max_drawdown_pct:.2f}%

Trade Stats:
  Avg Profit: {self.avg_profit_pct:+.2f}%
  Best Trade: {self.best_trade_pct:+.2f}%
  Worst Trade: {self.worst_trade_pct:+.2f}%
  Avg Duration: {self.avg_duration}
{'=' * 60}
"""


class BacktestEngine:
    """
    Wrapper for Freqtrade backtesting engine.

    Provides high-level Python API for:
    - Running backtests
    - Walk-forward analysis
    - Hyperparameter optimization
    - Performance comparison
    """

    def __init__(
        self,
        user_data_dir: Optional[Path] = None,
        config_file: Optional[Path] = None
    ):
        """
        Initialize backtest engine.

        Args:
            user_data_dir: Path to Freqtrade user_data directory
            config_file: Path to Freqtrade config file
        """
        # Default paths
        project_root = Path(__file__).resolve().parents[2]
        self.user_data_dir = user_data_dir or project_root / 'user_data'
        self.config_file = config_file or project_root / 'proratio_core' / 'config' / 'freqtrade' / 'config_dry.json'

        # Ensure paths exist
        if not self.user_data_dir.exists():
            raise FileNotFoundError(f"User data directory not found: {self.user_data_dir}")
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_file}")

    def backtest(
        self,
        strategy: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        pairs: Optional[List[str]] = None,
        initial_balance: float = 10000.0,
        stake_amount: float = 100.0,
        export_trades: bool = True,
        timeout: int = 600
    ) -> BacktestResults:
        """
        Run backtest for a strategy.

        Args:
            strategy: Strategy class name
            timeframe: Timeframe (1h, 4h, 1d, etc.)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            pairs: List of trading pairs (default: BTC/USDT, ETH/USDT)
            initial_balance: Starting balance (USDT)
            stake_amount: Amount per trade (USDT)
            export_trades: Export trades to JSON
            timeout: Command timeout in seconds

        Returns:
            BacktestResults with parsed metrics
        """
        if pairs is None:
            pairs = ['BTC/USDT', 'ETH/USDT']

        # Convert dates to Freqtrade format (YYYYMMDD)
        timerange = f"{start_date.replace('-', '')}-{end_date.replace('-', '')}"

        # Build command
        cmd = [
            'freqtrade',
            'backtesting',
            '--strategy', strategy,
            '--timeframe', timeframe,
            '--timerange', timerange,
            '--starting-balance', str(initial_balance),
            '--stake-amount', str(stake_amount),
            '--config', str(self.config_file),
            '--userdir', str(self.user_data_dir),
        ]

        # Add pairs
        if pairs:
            cmd.extend(['--pairs'] + pairs)

        # Export trades
        if export_trades:
            export_file = f"{strategy}_{timeframe}_{start_date}.json"
            cmd.extend(['--export', 'trades'])
            cmd.extend(['--export-filename', f'user_data/backtest_results/{export_file}'])

        # Run backtest
        print(f"Running backtest: {strategy} | {timeframe} | {start_date} to {end_date}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.user_data_dir.parent)
            )

            if result.returncode != 0:
                raise RuntimeError(f"Backtest failed: {result.stderr}")

            # Parse results
            return self._parse_results(
                output=result.stdout,
                strategy=strategy,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                pairs=pairs
            )

        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Backtest timed out after {timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Backtest error: {e}")

    def walk_forward_analysis(
        self,
        strategy: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        train_window_months: int = 6,
        test_window_months: int = 1,
        pairs: Optional[List[str]] = None
    ) -> List[BacktestResults]:
        """
        Run walk-forward analysis.

        Splits time period into training and testing windows, backtests each period,
        and returns results for performance validation.

        Args:
            strategy: Strategy class name
            timeframe: Timeframe
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            train_window_months: Training window size (months)
            test_window_months: Testing window size (months)
            pairs: Trading pairs

        Returns:
            List of BacktestResults for each test window
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        train_delta = timedelta(days=train_window_months * 30)
        test_delta = timedelta(days=test_window_months * 30)

        results = []
        current_start = start

        while current_start + train_delta + test_delta <= end:
            # Training period (not used yet, but calculated for future hyperopt)
            train_start = current_start
            train_end = current_start + train_delta

            # Testing period
            test_start = train_end
            test_end = test_start + test_delta

            print(f"\nWalk-forward window {len(results) + 1}:")
            print(f"  Train: {train_start.date()} to {train_end.date()}")
            print(f"  Test:  {test_start.date()} to {test_end.date()}")

            # Backtest on test window
            result = self.backtest(
                strategy=strategy,
                timeframe=timeframe,
                start_date=test_start.strftime('%Y-%m-%d'),
                end_date=test_end.strftime('%Y-%m-%d'),
                pairs=pairs,
                export_trades=False  # Don't export for each window
            )

            results.append(result)

            # Move to next window
            current_start += test_delta

        # Print summary
        print("\n" + "=" * 80)
        print("WALK-FORWARD ANALYSIS SUMMARY")
        print("=" * 80)

        total_profit = sum(r.total_profit_pct for r in results)
        avg_sharpe = sum(r.sharpe_ratio for r in results) / len(results) if results else 0
        max_dd = max(r.max_drawdown_pct for r in results) if results else 0

        print(f"Windows: {len(results)}")
        print(f"Total Profit: {total_profit:+.2f}%")
        print(f"Avg Sharpe: {avg_sharpe:.2f}")
        print(f"Max Drawdown: {max_dd:.2f}%")
        print("=" * 80)

        return results

    def compare_strategies(
        self,
        strategies: List[str],
        timeframe: str,
        start_date: str,
        end_date: str,
        pairs: Optional[List[str]] = None
    ) -> Dict[str, BacktestResults]:
        """
        Compare multiple strategies on the same data.

        Args:
            strategies: List of strategy names
            timeframe: Timeframe
            start_date: Start date
            end_date: End date
            pairs: Trading pairs

        Returns:
            Dictionary mapping strategy name to BacktestResults
        """
        results = {}

        for strategy in strategies:
            print(f"\nBacktesting strategy: {strategy}")
            result = self.backtest(
                strategy=strategy,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                pairs=pairs
            )
            results[strategy] = result

        # Print comparison
        self._print_comparison(results)

        return results

    def _parse_results(
        self,
        output: str,
        strategy: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        pairs: List[str]
    ) -> BacktestResults:
        """Parse Freqtrade backtest output"""

        # Initialize default values
        metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_profit_pct': 0.0,
            'total_profit_abs': 0.0,
            'avg_profit_pct': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'max_drawdown_pct': 0.0,
            'max_drawdown_abs': 0.0,
            'avg_duration': '0:00',
            'best_trade_pct': 0.0,
            'worst_trade_pct': 0.0,
        }

        lines = output.split('\n')

        for line in lines:
            # Parse from SUMMARY METRICS table
            if 'Total/Daily Avg Trades' in line:
                parts = line.split('│')
                if len(parts) >= 3:
                    try:
                        trades_str = parts[2].strip().split('/')[0].strip()
                        metrics['total_trades'] = int(trades_str)
                    except (ValueError, IndexError):
                        pass

            elif 'Total profit %' in line and '│' in line:
                parts = line.split('│')
                if len(parts) >= 3:
                    try:
                        pct_str = parts[2].strip().replace('%', '').strip()
                        metrics['total_profit_pct'] = float(pct_str)
                    except (ValueError, IndexError):
                        pass

            elif 'Absolute profit' in line and '│' in line:
                parts = line.split('│')
                if len(parts) >= 3:
                    try:
                        profit_str = parts[2].strip().split()[0].strip()
                        metrics['total_profit_abs'] = float(profit_str)
                    except (ValueError, IndexError):
                        pass

            elif 'Sharpe' in line and '│' in line:
                parts = line.split('│')
                if len(parts) >= 3:
                    try:
                        metrics['sharpe_ratio'] = float(parts[2].strip())
                    except (ValueError, IndexError):
                        pass

            elif 'Sortino' in line and '│' in line:
                parts = line.split('│')
                if len(parts) >= 3:
                    try:
                        metrics['sortino_ratio'] = float(parts[2].strip())
                    except (ValueError, IndexError):
                        pass

            elif 'Max % of account underwater' in line and '│' in line:
                parts = line.split('│')
                if len(parts) >= 3:
                    try:
                        dd_str = parts[2].strip().replace('%', '').strip()
                        metrics['max_drawdown_pct'] = abs(float(dd_str))
                    except (ValueError, IndexError):
                        pass

            elif 'Best trade' in line and '│' in line:
                parts = line.split('│')
                if len(parts) >= 3:
                    try:
                        best_str = parts[2].strip().split()[1].replace('%', '')
                        metrics['best_trade_pct'] = float(best_str)
                    except (ValueError, IndexError):
                        pass

            elif 'Worst trade' in line and '│' in line:
                parts = line.split('│')
                if len(parts) >= 3:
                    try:
                        worst_str = parts[2].strip().split()[1].replace('%', '')
                        metrics['worst_trade_pct'] = float(worst_str)
                    except (ValueError, IndexError):
                        pass

            # Parse from BACKTESTING REPORT table (TOTAL row)
            elif '│    TOTAL │' in line or '│ TOTAL │' in line:
                parts = line.split('│')
                if len(parts) >= 8:
                    try:
                        # Win stats: "21     0    24  46.7"
                        win_stats = parts[-2].strip().split()
                        metrics['winning_trades'] = int(win_stats[0])
                        metrics['losing_trades'] = int(win_stats[2])
                        metrics['win_rate'] = float(win_stats[-1])

                        # Average duration
                        metrics['avg_duration'] = parts[-3].strip()

                        # Average profit (column 3)
                        avg_profit_str = parts[3].strip()
                        metrics['avg_profit_pct'] = float(avg_profit_str)
                    except (ValueError, IndexError):
                        pass

        return BacktestResults(
            total_trades=metrics['total_trades'],
            winning_trades=metrics['winning_trades'],
            losing_trades=metrics['losing_trades'],
            win_rate=metrics['win_rate'],
            total_profit_pct=metrics['total_profit_pct'],
            total_profit_abs=metrics['total_profit_abs'],
            avg_profit_pct=metrics['avg_profit_pct'],
            sharpe_ratio=metrics['sharpe_ratio'],
            sortino_ratio=metrics['sortino_ratio'],
            max_drawdown_pct=metrics['max_drawdown_pct'],
            max_drawdown_abs=metrics['max_drawdown_abs'],
            avg_duration=metrics['avg_duration'],
            best_trade_pct=metrics['best_trade_pct'],
            worst_trade_pct=metrics['worst_trade_pct'],
            strategy_name=strategy,
            start_date=datetime.strptime(start_date, '%Y-%m-%d'),
            end_date=datetime.strptime(end_date, '%Y-%m-%d'),
            timeframe=timeframe,
            pairs=pairs,
            raw_output=output
        )

    def _print_comparison(self, results: Dict[str, BacktestResults]) -> None:
        """Print side-by-side strategy comparison"""

        print("\n" + "=" * 100)
        print("STRATEGY COMPARISON")
        print("=" * 100)

        # Headers
        print(f"{'Strategy':<25} {'Profit %':<12} {'Sharpe':<10} {'Win Rate':<12} {'Trades':<10} {'Max DD':<10}")
        print("-" * 100)

        # Results
        for strategy, result in results.items():
            print(
                f"{strategy:<25} "
                f"{result.total_profit_pct:>10.2f}%  "
                f"{result.sharpe_ratio:>8.2f}  "
                f"{result.win_rate:>10.1f}%  "
                f"{result.total_trades:>8}  "
                f"{result.max_drawdown_pct:>8.2f}%"
            )

        print("=" * 100)
