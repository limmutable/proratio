#!/usr/bin/env python3
"""
Comprehensive Backtesting Script for Phase 2 Strategies

Tests all Phase 2 strategies and compares their performance:
- Mean Reversion Strategy
- Grid Trading Strategy
- AI-Enhanced Strategy (baseline)
- Multi-strategy Portfolio

Usage:
    python scripts/backtest_phase2_strategies.py --pairs BTC/USDT ETH/USDT --timeframe 1h --days 180

Features:
- Parallel backtesting of all strategies
- A/B testing framework for comparisons
- Performance metrics and reports
- Visual comparison charts (optional)
"""

import sys
from pathlib import Path
from typing import List, Dict
import argparse
import json

# Add project root to Python path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import subprocess
from tabulate import tabulate

from proratio_quantlab.ab_testing import (
    StrategyComparer,
    create_strategy_result_from_backtest,
)


def run_freqtrade_backtest(
    strategy_name: str,
    pairs: List[str],
    timeframe: str,
    days: int,
    config_path: str = "proratio_utilities/config/freqtrade/config_dry.json",
) -> Dict:
    """
    Run Freqtrade backtest for a strategy.

    Args:
        strategy_name: Name of the strategy (must exist in user_data/strategies/)
        pairs: List of trading pairs (e.g., ['BTC/USDT', 'ETH/USDT'])
        timeframe: Timeframe for backtest (e.g., '1h', '4h')
        days: Number of days to backtest
        config_path: Path to Freqtrade config file

    Returns:
        Dictionary with backtest results
    """
    print(f"\n{'=' * 80}")
    print(f"Running backtest for {strategy_name}")
    print(f"{'=' * 80}")

    # Build Freqtrade command
    cmd = [
        "freqtrade",
        "backtesting",
        "--strategy",
        strategy_name,
        "--timeframe",
        timeframe,
        "--timerange",
        f"-{days}",  # Last N days
        "--config",
        config_path,
        "--userdir",
        "user_data",
        "--export",
        "trades",
        "--export-filename",
        f"user_data/backtest_results/{strategy_name}_backtest.json",
    ]

    # Add pairs if specified
    if pairs:
        cmd.extend(["--pairs"] + pairs)

    print(f"Command: {' '.join(cmd)}")
    print()

    # Run backtest
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)

        # Parse results from JSON export
        results_file = (
            project_root / f"user_data/backtest_results/{strategy_name}_backtest.json"
        )

        if results_file.exists():
            with open(results_file, "r") as f:
                backtest_data = json.load(f)
            return parse_freqtrade_results(backtest_data, strategy_name)
        else:
            print(f"⚠ Warning: Results file not found at {results_file}")
            return {}

    except subprocess.CalledProcessError as e:
        print(f"✗ Backtest failed for {strategy_name}")
        print(f"Error: {e.stderr}")
        return {}


def parse_freqtrade_results(backtest_data: Dict, strategy_name: str) -> Dict:
    """
    Parse Freqtrade backtest results into standardized format.

    Args:
        backtest_data: Raw backtest data from Freqtrade
        strategy_name: Name of the strategy

    Returns:
        Parsed results dictionary
    """
    # Freqtrade results structure varies, adapt as needed
    # This is a simplified parser

    try:
        strategy_data = backtest_data.get("strategy", {}).get(strategy_name, {})

        trades = strategy_data.get("trades", [])
        total_trades = len(trades)

        winning_trades = sum(1 for trade in trades if trade.get("profit_ratio", 0) > 0)
        losing_trades = total_trades - winning_trades

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Calculate returns
        returns = [trade.get("profit_ratio", 0) * 100 for trade in trades]
        total_return = sum(returns)
        avg_return = total_return / total_trades if total_trades > 0 else 0

        # Calculate Sharpe ratio (simplified)
        if returns:
            sharpe_ratio = (
                (pd.Series(returns).mean() / pd.Series(returns).std()) * (252**0.5)
                if pd.Series(returns).std() > 0
                else 0
            )
        else:
            sharpe_ratio = 0

        # Max drawdown
        max_drawdown = strategy_data.get("max_drawdown", 0)

        # Profit factor
        gross_profit = sum(r for r in returns if r > 0)
        gross_loss = abs(sum(r for r in returns if r < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        return {
            "strategy_name": strategy_name,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "total_return_pct": total_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown_pct": max_drawdown,
            "profit_factor": profit_factor,
            "avg_trade_return_pct": avg_return,
            "avg_win_pct": sum(r for r in returns if r > 0) / winning_trades
            if winning_trades > 0
            else 0,
            "avg_loss_pct": sum(r for r in returns if r < 0) / losing_trades
            if losing_trades > 0
            else 0,
            "best_trade_pct": max(returns) if returns else 0,
            "worst_trade_pct": min(returns) if returns else 0,
            "avg_trade_duration_hours": sum(
                trade.get("trade_duration", 0) for trade in trades
            )
            / total_trades
            / 60
            if total_trades > 0
            else 0,
            "total_fees": sum(
                trade.get("fee_close", 0) + trade.get("fee_open", 0) for trade in trades
            ),
            "returns_distribution": returns,
            "equity_curve": pd.Series(),  # Would need to reconstruct from trades
            "metadata": {
                "backtest_start": strategy_data.get("backtest_start"),
                "backtest_end": strategy_data.get("backtest_end"),
                "config": strategy_data.get("config", {}),
            },
        }

    except Exception as e:
        print(f"✗ Error parsing results for {strategy_name}: {e}")
        return {}


def print_summary_table(results: Dict[str, Dict]) -> None:
    """
    Print a summary table of all strategy results.

    Args:
        results: Dictionary of strategy_name -> results_dict
    """
    print("\n" + "=" * 120)
    print(" " * 40 + "STRATEGY COMPARISON SUMMARY")
    print("=" * 120)
    print()

    # Prepare table data
    headers = [
        "Strategy",
        "Trades",
        "Win Rate",
        "Total Return",
        "Sharpe",
        "Max DD",
        "Profit Factor",
        "Avg Return",
    ]

    rows = []
    for strategy_name, result in results.items():
        if not result:
            continue

        rows.append(
            [
                strategy_name,
                result.get("total_trades", 0),
                f"{result.get('win_rate', 0):.1f}%",
                f"{result.get('total_return_pct', 0):+.2f}%",
                f"{result.get('sharpe_ratio', 0):.2f}",
                f"{result.get('max_drawdown_pct', 0):.2f}%",
                f"{result.get('profit_factor', 0):.2f}",
                f"{result.get('avg_trade_return_pct', 0):+.2f}%",
            ]
        )

    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print()


def run_ab_tests(results: Dict[str, Dict]) -> None:
    """
    Run A/B tests comparing all strategies pairwise.

    Args:
        results: Dictionary of strategy_name -> results_dict
    """
    print("\n" + "=" * 120)
    print(" " * 45 + "A/B TESTING RESULTS")
    print("=" * 120)
    print()

    comparer = StrategyComparer()

    strategy_names = list(results.keys())

    # Compare each strategy with the baseline (AIEnhancedStrategy)
    baseline_name = "AIEnhancedStrategy"

    if baseline_name in results:
        baseline_result = create_strategy_result_from_backtest(
            baseline_name, results[baseline_name]
        )

        for strategy_name in strategy_names:
            if strategy_name == baseline_name:
                continue

            if not results.get(strategy_name):
                continue

            print(f"\n{'─' * 120}")
            print(f"Comparing: {baseline_name} vs. {strategy_name}")
            print(f"{'─' * 120}\n")

            strategy_result = create_strategy_result_from_backtest(
                strategy_name, results[strategy_name]
            )

            comparison = comparer.compare_strategies(baseline_result, strategy_result)

            comparer.print_comparison_report(comparison)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Backtest Phase 2 trading strategies and compare performance"
    )

    parser.add_argument(
        "--pairs",
        nargs="+",
        default=["BTC/USDT", "ETH/USDT"],
        help="Trading pairs to backtest (default: BTC/USDT ETH/USDT)",
    )

    parser.add_argument(
        "--timeframe", default="1h", help="Timeframe for backtest (default: 1h)"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=180,
        help="Number of days to backtest (default: 180)",
    )

    parser.add_argument(
        "--strategies",
        nargs="+",
        default=["AIEnhancedStrategy", "MeanReversionStrategy", "GridTradingStrategy"],
        help="Strategies to test (default: all Phase 2 strategies)",
    )

    parser.add_argument(
        "--config",
        default="proratio_utilities/config/freqtrade/config_dry.json",
        help="Path to Freqtrade config file",
    )

    parser.add_argument(
        "--skip-backtest",
        action="store_true",
        help="Skip backtest execution, only analyze existing results",
    )

    args = parser.parse_args()

    print("\n" + "=" * 120)
    print(" " * 35 + "PHASE 2 STRATEGIES BACKTEST SUITE")
    print("=" * 120)
    print()
    print(f"Pairs: {', '.join(args.pairs)}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Period: Last {args.days} days")
    print(f"Strategies: {', '.join(args.strategies)}")
    print()

    # Run backtests
    results = {}

    if not args.skip_backtest:
        for strategy_name in args.strategies:
            result = run_freqtrade_backtest(
                strategy_name=strategy_name,
                pairs=args.pairs,
                timeframe=args.timeframe,
                days=args.days,
                config_path=args.config,
            )

            if result:
                results[strategy_name] = result
            else:
                print(f"⚠ Warning: No results for {strategy_name}")

        # Save combined results
        output_file = project_root / "user_data/backtest_results/phase2_comparison.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n✓ Results saved to {output_file}")

    else:
        # Load existing results
        output_file = project_root / "user_data/backtest_results/phase2_comparison.json"

        if output_file.exists():
            with open(output_file, "r") as f:
                results = json.load(f)
            print(f"✓ Loaded results from {output_file}")
        else:
            print(f"✗ No existing results found at {output_file}")
            return

    # Print summary
    if results:
        print_summary_table(results)

        # Run A/B tests
        run_ab_tests(results)

    print("\n" + "=" * 120)
    print(" " * 45 + "BACKTEST COMPLETE")
    print("=" * 120 + "\n")


if __name__ == "__main__":
    main()
