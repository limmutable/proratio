#!/usr/bin/env python3
"""
Backtest AI-Enhanced Strategy

Runs backtests for both SimpleTestStrategy (baseline) and AIEnhancedStrategy (AI-enhanced)
to compare performance metrics and validate AI improvements.

Usage:
    python scripts/backtest_ai_strategy.py --timeframe 1h --months 6
    python scripts/backtest_ai_strategy.py --timeframe 4h --months 12 --pairs BTC/USDT ETH/USDT
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import json
from typing import List, Dict, Optional
import argparse

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from proratio_utilities.config.settings import get_settings


class BacktestRunner:
    """Runs backtests and compares strategies"""

    def __init__(self):
        self.settings = get_settings()
        self.user_data_dir = project_root / 'user_data'
        self.config_file = project_root / 'proratio_core' / 'config' / 'freqtrade' / 'config_dry.json'

    def run_backtest(
        self,
        strategy: str,
        pairs: List[str],
        timeframe: str,
        start_date: str,
        end_date: str
    ) -> Optional[Dict]:
        """
        Run a single backtest for a strategy.

        Args:
            strategy: Strategy class name
            pairs: List of trading pairs
            timeframe: Timeframe (1h, 4h, 1d)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Backtest results dict or None if failed
        """
        print(f"\n{'=' * 70}")
        print(f"  BACKTESTING: {strategy}")
        print(f"{'=' * 70}")
        print(f"Pairs: {', '.join(pairs)}")
        print(f"Timeframe: {timeframe}")
        print(f"Period: {start_date} to {end_date}")
        print(f"{'=' * 70}\n")

        # Build freqtrade backtest command
        cmd = [
            'freqtrade',
            'backtesting',
            '--strategy', strategy,
            '--timeframe', timeframe,
            '--timerange', f'{start_date.replace("-", "")}-{end_date.replace("-", "")}',
            '--config', str(self.config_file),
            '--userdir', str(self.user_data_dir),
            '--export', 'trades',
            '--export-filename', f'user_data/backtest_results/{strategy}_{timeframe}_{start_date}.json',
        ]

        # Add pairs if specified
        if pairs:
            cmd.extend(['--pairs'] + pairs)

        try:
            # Run backtest
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode == 0:
                print("✓ Backtest completed successfully\n")
                print(result.stdout)
                return self._parse_backtest_results(result.stdout)
            else:
                print(f"✗ Backtest failed with exit code {result.returncode}")
                print(result.stderr)
                return None

        except subprocess.TimeoutExpired:
            print("✗ Backtest timed out after 10 minutes")
            return None
        except Exception as e:
            print(f"✗ Error running backtest: {e}")
            return None

    def _parse_backtest_results(self, output: str) -> Dict:
        """
        Parse backtest results from freqtrade output.

        Args:
            output: Freqtrade stdout

        Returns:
            Dictionary with key metrics
        """
        results = {
            'total_trades': 0,
            'profit_total': 0.0,
            'profit_pct': 0.0,
            'win_rate': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'avg_duration': '0:00:00',
        }

        # Parse key metrics from output
        lines = output.split('\n')
        in_summary = False

        for i, line in enumerate(lines):
            # Detect SUMMARY METRICS section
            if 'SUMMARY METRICS' in line:
                in_summary = True
                continue

            if in_summary:
                # Parse from SUMMARY METRICS table
                if 'Total/Daily Avg Trades' in line:
                    parts = line.split('│')
                    if len(parts) >= 3:
                        try:
                            trades_str = parts[2].strip().split('/')[0].strip()
                            results['total_trades'] = int(trades_str)
                        except (ValueError, IndexError):
                            pass
                elif 'Absolute profit' in line and '│' in line:
                    parts = line.split('│')
                    if len(parts) >= 3:
                        try:
                            profit_str = parts[2].strip().split()[0].strip()
                            results['profit_total'] = float(profit_str)
                        except (ValueError, IndexError):
                            pass
                elif 'Total profit %' in line and '│' in line:
                    parts = line.split('│')
                    if len(parts) >= 3:
                        try:
                            pct_str = parts[2].strip().replace('%', '').strip()
                            results['profit_pct'] = float(pct_str)
                        except (ValueError, IndexError):
                            pass
                elif 'Sharpe' in line and '│' in line:
                    parts = line.split('│')
                    if len(parts) >= 3:
                        try:
                            results['sharpe_ratio'] = float(parts[2].strip())
                        except (ValueError, IndexError):
                            pass
                elif 'Max % of account underwater' in line and '│' in line:
                    parts = line.split('│')
                    if len(parts) >= 3:
                        try:
                            dd_str = parts[2].strip().replace('%', '').strip()
                            results['max_drawdown'] = abs(float(dd_str))
                        except (ValueError, IndexError):
                            pass

            # Parse win rate from BACKTESTING REPORT table (TOTAL row)
            if '│    TOTAL │' in line or '│ TOTAL │' in line:
                parts = line.split('│')
                # Format: │    TOTAL │     45 │        -0.41 │         -18.371 │        -0.18 │     12:44:00 │   21     0    24  46.7 │
                if len(parts) >= 8:
                    try:
                        # Last column contains: "Win  Draw  Loss  Win%"
                        win_stats = parts[-2].strip()  # e.g., "21     0    24  46.7"
                        # Extract win percentage (last number)
                        win_pct = win_stats.split()[-1]  # "46.7"
                        results['win_rate'] = float(win_pct)
                    except (ValueError, IndexError):
                        pass

                    # Extract average duration (second to last column)
                    try:
                        results['avg_duration'] = parts[-3].strip()
                    except IndexError:
                        pass

        return results

    def compare_strategies(
        self,
        baseline_results: Dict,
        enhanced_results: Dict
    ) -> None:
        """
        Print side-by-side comparison of strategy results.

        Args:
            baseline_results: SimpleTestStrategy results
            enhanced_results: AIEnhancedStrategy results
        """
        print("\n" + "=" * 90)
        print("  STRATEGY COMPARISON: SimpleTestStrategy vs AIEnhancedStrategy")
        print("=" * 90)

        metrics = [
            ('Total Trades', 'total_trades', ''),
            ('Total Profit %', 'profit_pct', '%'),
            ('Win Rate', 'win_rate', '%'),
            ('Sharpe Ratio', 'sharpe_ratio', ''),
            ('Max Drawdown', 'max_drawdown', '%'),
            ('Avg Duration', 'avg_duration', ''),
        ]

        print(f"{'Metric':<20} {'Baseline':<20} {'AI-Enhanced':<20} {'Improvement':<20}")
        print("-" * 90)

        for name, key, suffix in metrics:
            baseline = baseline_results.get(key, 0)
            enhanced = enhanced_results.get(key, 0)

            if isinstance(baseline, (int, float)) and isinstance(enhanced, (int, float)):
                if baseline != 0:
                    improvement_pct = ((enhanced - baseline) / abs(baseline)) * 100
                    improvement = f"{improvement_pct:+.2f}%"
                else:
                    improvement = "N/A"

                baseline_str = f"{baseline:.2f}{suffix}" if isinstance(baseline, float) else f"{baseline}{suffix}"
                enhanced_str = f"{enhanced:.2f}{suffix}" if isinstance(enhanced, float) else f"{enhanced}{suffix}"
            else:
                baseline_str = str(baseline)
                enhanced_str = str(enhanced)
                improvement = "N/A"

            print(f"{name:<20} {baseline_str:<20} {enhanced_str:<20} {improvement:<20}")

        print("=" * 90)

        # Print verdict
        print("\n📊 VERDICT:")
        if enhanced_results.get('profit_pct', 0) > baseline_results.get('profit_pct', 0):
            print("✅ AI-Enhanced strategy OUTPERFORMED baseline")
        elif enhanced_results.get('profit_pct', 0) < baseline_results.get('profit_pct', 0):
            print("❌ AI-Enhanced strategy UNDERPERFORMED baseline")
        else:
            print("➖ Strategies performed EQUALLY")

        if enhanced_results.get('sharpe_ratio', 0) > baseline_results.get('sharpe_ratio', 0):
            print("✅ AI-Enhanced strategy has BETTER risk-adjusted returns (Sharpe)")

        if enhanced_results.get('max_drawdown', 100) < baseline_results.get('max_drawdown', 100):
            print("✅ AI-Enhanced strategy has LOWER drawdown (better risk management)")

        print()


def main():
    """Main backtest execution"""
    parser = argparse.ArgumentParser(description='Backtest AI-Enhanced Strategy')
    parser.add_argument(
        '--timeframe',
        type=str,
        default='1h',
        choices=['1h', '4h', '1d'],
        help='Timeframe for backtest (default: 1h)'
    )
    parser.add_argument(
        '--months',
        type=int,
        default=6,
        help='Number of months to backtest (default: 6)'
    )
    parser.add_argument(
        '--pairs',
        type=str,
        nargs='+',
        default=['BTC/USDT', 'ETH/USDT'],
        help='Trading pairs to test (default: BTC/USDT ETH/USDT)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        default=None,
        help='Start date (YYYY-MM-DD) - overrides --months'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        default=None,
        help='End date (YYYY-MM-DD) - overrides --months'
    )
    parser.add_argument(
        '--skip-baseline',
        action='store_true',
        help='Skip baseline strategy backtest (only run AI-enhanced)'
    )

    args = parser.parse_args()

    # Calculate date range
    if args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=args.months * 30)).strftime('%Y-%m-%d')

    runner = BacktestRunner()

    print("\n" + "=" * 90)
    print("  PRORATIO AI STRATEGY BACKTEST")
    print("=" * 90)
    print(f"Timeframe: {args.timeframe}")
    print(f"Date Range: {start_date} to {end_date} ({args.months} months)")
    print(f"Pairs: {', '.join(args.pairs)}")
    print("=" * 90)

    # Run baseline backtest (SimpleTestStrategy)
    baseline_results = None
    if not args.skip_baseline:
        baseline_results = runner.run_backtest(
            strategy='SimpleTestStrategy',
            pairs=args.pairs,
            timeframe=args.timeframe,
            start_date=start_date,
            end_date=end_date
        )

    # Run AI-enhanced backtest
    enhanced_results = runner.run_backtest(
        strategy='AIEnhancedStrategy',
        pairs=args.pairs,
        timeframe=args.timeframe,
        start_date=start_date,
        end_date=end_date
    )

    # Compare results
    if baseline_results and enhanced_results:
        runner.compare_strategies(baseline_results, enhanced_results)
    elif enhanced_results:
        print("\n✓ AI-Enhanced strategy backtest completed")
        print(f"Total Profit: {enhanced_results.get('profit_pct', 0):.2f}%")
        print(f"Sharpe Ratio: {enhanced_results.get('sharpe_ratio', 0):.2f}")
        print(f"Max Drawdown: {enhanced_results.get('max_drawdown', 0):.2f}%")
    else:
        print("\n✗ Backtest failed - check errors above")
        sys.exit(1)


if __name__ == '__main__':
    main()
