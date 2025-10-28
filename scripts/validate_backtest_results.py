#!/usr/bin/env python3
"""
Backtest Results Validator

Validates backtest results against defined criteria to ensure strategy quality.
Stores validation results in database for historical tracking.

Feature: 001-test-validation-dashboard (User Story 3)
"""

import argparse
import json
import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from proratio_utilities.data.validation_repository import (
    ValidationRepository,
    DatabaseConnectionError,
    DatabaseWriteError,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Validation criteria
VALIDATION_CRITERIA = {
    "min_trades": 5,  # At least 5 trades to be statistically meaningful
    "min_win_rate": 45.0,  # Minimum 45% win rate
    "max_drawdown": 25.0,  # Maximum 25% drawdown
    "min_sharpe": 0.5,  # Minimum Sharpe ratio (positive risk-adjusted return)
    "min_profit_factor": 1.0,  # Profit factor > 1 means profitable
    "max_avg_loss_pct": 5.0,  # Average loss per trade < 5%
}


def get_git_commit_hash() -> Optional[str]:
    """
    Get current git commit hash.

    Returns:
        40-character commit hash, or None if git is not available or not a git repo.

    User Story 3 (T030): Git commit hash capture with graceful handling
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        commit_hash = result.stdout.strip()

        # Verify format (40 hex characters)
        if len(commit_hash) == 40 and all(c in "0123456789abcdef" for c in commit_hash):
            logger.info(f"Git commit hash: {commit_hash[:8]}...")
            return commit_hash
        else:
            logger.warning(f"Invalid git commit hash format: {commit_hash}")
            return None

    except subprocess.TimeoutExpired:
        logger.warning("Git command timed out - skipping commit hash")
        return None
    except subprocess.CalledProcessError as e:
        logger.warning(f"Not a git repository or git not available: {e}")
        return None
    except FileNotFoundError:
        logger.warning("Git command not found - skipping commit hash")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error getting git commit hash: {e}")
        return None


def store_validation_results(
    strategy: str, metrics: Dict, passed: bool
) -> Optional[int]:
    """
    Store validation results in database.

    Args:
        strategy: Strategy name
        metrics: Validation metrics dictionary
        passed: Whether validation passed

    Returns:
        Database ID of inserted record, or None if storage failed

    User Story 3 (T031-T034): Database storage with error handling
    """
    try:
        # Initialize repository
        repo = ValidationRepository()

        # Get git commit hash (gracefully handle if not available)
        git_commit_hash = get_git_commit_hash()

        # Prepare metrics for storage
        # Convert win_rate from percentage to decimal if needed
        win_rate = metrics.get("win_rate", 0.0)
        total_profit_pct = metrics.get("profit_total", 0.0)
        max_drawdown = abs(metrics.get("max_drawdown", 0.0)) * -1  # Store as negative
        sharpe_ratio = metrics.get("sharpe_ratio", 0.0)
        profit_factor = metrics.get("profit_factor", 0.0)

        # Insert into database
        result_id = repo.insert_validation_result(
            strategy_name=strategy,
            timestamp=datetime.utcnow(),
            total_trades=metrics.get("total_trades", 0),
            win_rate=win_rate if win_rate > 0 else None,
            total_profit_pct=total_profit_pct,
            max_drawdown=max_drawdown if max_drawdown != 0 else None,
            sharpe_ratio=sharpe_ratio if sharpe_ratio != 0 else None,
            profit_factor=profit_factor if profit_factor > 0 else None,
            git_commit_hash=git_commit_hash,
        )

        logger.info(f"✓ Validation result stored in database (ID: {result_id})")
        return result_id

    except DatabaseConnectionError as e:
        logger.warning(f"Could not connect to database: {e}")
        logger.warning("Validation will continue with file-based results only")
        return None
    except DatabaseWriteError as e:
        logger.error(f"Failed to write validation result to database: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error storing validation result: {e}")
        import traceback

        traceback.print_exc()
        return None


def find_latest_backtest_results(strategy: str) -> Path:
    """Find the most recent backtest results file for the strategy."""
    backtest_dir = Path("user_data/backtest_results")

    if not backtest_dir.exists():
        raise FileNotFoundError(f"Backtest results directory not found: {backtest_dir}")

    # Find all backtest result files
    result_files = list(backtest_dir.glob("*.json"))

    if not result_files:
        raise FileNotFoundError(f"No backtest results found in {backtest_dir}")

    # Get the most recent file
    latest_file = max(result_files, key=lambda p: p.stat().st_mtime)

    return latest_file


def parse_backtest_results(results_file: Path) -> Dict:
    """Parse backtest results JSON file."""
    with open(results_file, "r") as f:
        data = json.load(f)

    # Handle case where file only contains metadata (0 trades)
    if "strategy" not in data:
        # Check if this is a metadata-only file or pointer file
        if "latest_backtest" in data or "backtest_start_time" in str(data):
            # Return default metrics for 0 trades case
            return {
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "profit_total": 0.0,
                "profit_total_abs": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "profit_factor": 0.0,
                "avg_profit": 0.0,
                "avg_duration": "0",
            }
        raise ValueError("Invalid backtest results file format")

    strategy_data = data["strategy"]

    # Extract metrics
    metrics = {
        "total_trades": strategy_data.get("total_trades", 0),
        "wins": strategy_data.get("wins", 0),
        "losses": strategy_data.get("losses", 0),
        "win_rate": strategy_data.get("winrate", 0.0),
        "profit_total": strategy_data.get("profit_total", 0.0),
        "profit_total_abs": strategy_data.get("profit_total_abs", 0.0),
        "max_drawdown": strategy_data.get("max_drawdown_account", 0.0),
        "sharpe_ratio": strategy_data.get("sharpe", 0.0),
        "profit_factor": strategy_data.get("profit_factor", 0.0),
        "avg_profit": strategy_data.get("avg_profit", 0.0),
        "avg_duration": strategy_data.get("avg_duration", "0"),
    }

    # Calculate additional metrics
    if metrics["total_trades"] > 0:
        metrics["loss_rate"] = 100.0 - metrics["win_rate"]
        if metrics["losses"] > 0:
            # Approximate average loss (this is simplified)
            total_loss = abs(
                metrics["profit_total_abs"] - (metrics["wins"] * metrics["avg_profit"])
            )
            metrics["avg_loss"] = total_loss / metrics["losses"] if metrics["losses"] > 0 else 0.0
        else:
            metrics["avg_loss"] = 0.0
    else:
        metrics["loss_rate"] = 0.0
        metrics["avg_loss"] = 0.0

    return metrics


def validate_metrics(metrics: Dict) -> Tuple[bool, List[Dict]]:
    """
    Validate metrics against criteria.

    Returns:
        (passed, checks): Boolean indicating if all checks passed, and list of check results
    """
    checks = []

    # Check 0: Zero trades (immediate fail)
    if metrics["total_trades"] == 0:
        check = {
            "name": "Trade Generation",
            "criterion": "> 0 trades (strategy must generate at least 1 trade)",
            "actual": "0 trades - Strategy did not trigger any buy signals",
            "passed": False,
            "severity": "critical",
            "message": "CRITICAL: Strategy generated 0 trades. Cannot validate performance metrics. "
                      "This usually means: (1) Timerange too short, (2) Entry conditions too strict, "
                      "or (3) Strategy logic error. Try longer timerange or review strategy code."
        }
        checks.append(check)
        return False, checks  # Immediate fail

    # Check 1: Minimum trades
    check = {
        "name": "Minimum Trades",
        "criterion": f">= {VALIDATION_CRITERIA['min_trades']} trades",
        "actual": metrics["total_trades"],
        "passed": metrics["total_trades"] >= VALIDATION_CRITERIA["min_trades"],
        "severity": "critical",
    }
    checks.append(check)

    # Check 2: Win rate
    check = {
        "name": "Win Rate",
        "criterion": f">= {VALIDATION_CRITERIA['min_win_rate']}%",
        "actual": f"{metrics['win_rate']:.2f}%",
        "passed": metrics["win_rate"] >= VALIDATION_CRITERIA["min_win_rate"],
        "severity": "high",
    }
    checks.append(check)

    # Check 3: Max drawdown
    check = {
        "name": "Max Drawdown",
        "criterion": f"< {VALIDATION_CRITERIA['max_drawdown']}%",
        "actual": f"{abs(metrics['max_drawdown']):.2f}%",
        "passed": abs(metrics["max_drawdown"]) < VALIDATION_CRITERIA["max_drawdown"],
        "severity": "high",
    }
    checks.append(check)

    # Check 4: Sharpe ratio
    check = {
        "name": "Sharpe Ratio",
        "criterion": f">= {VALIDATION_CRITERIA['min_sharpe']}",
        "actual": f"{metrics['sharpe_ratio']:.2f}",
        "passed": metrics["sharpe_ratio"] >= VALIDATION_CRITERIA["min_sharpe"],
        "severity": "medium",
    }
    checks.append(check)

    # Check 5: Profit factor
    check = {
        "name": "Profit Factor",
        "criterion": f">= {VALIDATION_CRITERIA['min_profit_factor']}",
        "actual": f"{metrics['profit_factor']:.2f}",
        "passed": metrics["profit_factor"] >= VALIDATION_CRITERIA["min_profit_factor"],
        "severity": "high",
    }
    checks.append(check)

    # Check 6: Not losing money overall
    check = {
        "name": "Total Profit",
        "criterion": ">= 0%",
        "actual": f"{metrics['profit_total']:.2f}%",
        "passed": metrics["profit_total"] >= 0.0,
        "severity": "high",
    }
    checks.append(check)

    # Determine if all critical/high checks passed
    critical_checks = [c for c in checks if c["severity"] in ["critical", "high"]]
    all_passed = all(c["passed"] for c in critical_checks)

    return all_passed, checks


def print_validation_report(strategy: str, metrics: Dict, checks: List[Dict], passed: bool):
    """Print formatted validation report."""
    print("\n" + "=" * 60)
    print(f"Validation Results: {strategy}")
    print("=" * 60)
    print()

    # Print metrics
    print("Key Metrics:")
    print(f"  Total Trades:     {metrics['total_trades']}")
    print(f"  Win Rate:         {metrics['win_rate']:.2f}%")
    print(f"  Total Profit:     {metrics['profit_total']:.2f}% ({metrics['profit_total_abs']:.2f} USDT)")
    print(f"  Max Drawdown:     {abs(metrics['max_drawdown']):.2f}%")
    print(f"  Sharpe Ratio:     {metrics['sharpe_ratio']:.2f}")
    print(f"  Profit Factor:    {metrics['profit_factor']:.2f}")
    print(f"  Avg Duration:     {metrics['avg_duration']}")
    print()

    # Print validation checks
    print("Validation Checks:")
    for check in checks:
        status = "✓ PASS" if check["passed"] else "✗ FAIL"
        severity = f"[{check['severity'].upper()}]"
        print(f"  {status:8} {severity:12} {check['name']:20} {check['criterion']:20} (Actual: {check['actual']})")

        # Print additional message if present (for critical failures)
        if not check["passed"] and "message" in check:
            print(f"\n  ⚠️  {check['message']}\n")

    print()
    print("=" * 60)

    if passed:
        print("✓ VALIDATION PASSED - Strategy meets minimum criteria")
        print()
        print("Next steps:")
        print("  1. Review the metrics and ensure they align with expectations")
        print("  2. Run integration tests if available")
        print("  3. Strategy is ready for paper trading validation")
    else:
        print("✗ VALIDATION FAILED - Strategy does not meet minimum criteria")
        print()
        print("Issues to address:")
        failed_checks = [c for c in checks if not c["passed"] and c["severity"] in ["critical", "high"]]
        for i, check in enumerate(failed_checks, 1):
            print(f"  {i}. {check['name']}: {check['criterion']} (Actual: {check['actual']})")
        print()
        print("Recommendations:")
        print("  - Adjust strategy parameters and re-run backtest")
        print("  - Consider different timeframes or pairs")
        print("  - Review strategy logic for improvements")

    print("=" * 60)
    print()


def main():
    parser = argparse.ArgumentParser(description="Validate backtest results against quality criteria")
    parser.add_argument("--strategy", required=True, help="Strategy name")
    parser.add_argument("--results-file", help="Path to backtest results JSON (optional, will find latest)")

    args = parser.parse_args()

    try:
        # Find or use provided results file
        if args.results_file:
            results_file = Path(args.results_file)
        else:
            results_file = find_latest_backtest_results(args.strategy)

        print(f"Using backtest results: {results_file}")

        # Parse results
        metrics = parse_backtest_results(results_file)

        # Validate
        passed, checks = validate_metrics(metrics)

        # Print report
        print_validation_report(args.strategy, metrics, checks, passed)

        # Store results in database (non-blocking)
        # User Story 3 (T033): Database write with error handling
        logger.info("Storing validation results in database...")
        result_id = store_validation_results(args.strategy, metrics, passed)

        if result_id:
            logger.info(f"Database storage successful (Record ID: {result_id})")
        else:
            logger.warning("Database storage failed - results saved to file only")

        # Exit with appropriate code
        sys.exit(0 if passed else 1)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nMake sure you have run a backtest first:", file=sys.stderr)
        print(f"  freqtrade backtesting --strategy {args.strategy} --userdir user_data", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
