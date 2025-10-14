"""
Strategy Commands

Manage trading strategies, view details, and run backtests.

Author: Proratio Team
Date: 2025-10-11
"""

import typer
from pathlib import Path
from rich.syntax import Syntax
from proratio_cli.utils.display import (
    print_header,
    create_strategy_table,
    print_error,
    print_success,
    console,
)

app = typer.Typer()


@app.command()
def list():
    """List all available strategies."""
    print_header("Available Strategies", "Freqtrade strategy files")

    strategy_path = Path("user_data/strategies")

    if not strategy_path.exists():
        print_error("Strategy directory not found")
        raise typer.Exit(1)

    strategies = []
    for strategy_file in strategy_path.glob("*.py"):
        if (
            not strategy_file.name.startswith("_")
            and strategy_file.name != "__init__.py"
        ):
            # Parse strategy info
            strategy_name = strategy_file.stem
            strategy_type = "Unknown"

            # Try to determine strategy type from name
            if "AI" in strategy_name or "Enhanced" in strategy_name:
                strategy_type = "AI-Enhanced"
            elif "Mean" in strategy_name or "Reversion" in strategy_name:
                strategy_type = "Mean Reversion"
            elif "Grid" in strategy_name:
                strategy_type = "Grid Trading"
            elif "Trend" in strategy_name:
                strategy_type = "Trend Following"
            elif "FreqAI" in strategy_name:
                strategy_type = "FreqAI ML"

            strategies.append(
                {
                    "name": strategy_name,
                    "type": strategy_type,
                    "status": "Active",
                    "sharpe": 0.0,  # Would need to read from backtest results
                }
            )

    if strategies:
        table = create_strategy_table(strategies)
        console.print(table)
        console.print(f"\n[dim]Total: {len(strategies)} strategies[/dim]\n")
    else:
        print_error("No strategies found")


@app.command()
def show(
    name: str = typer.Argument(..., help="Strategy name"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
):
    """Show strategy source code."""
    strategy_path = Path(f"user_data/strategies/{name}.py")

    if not strategy_path.exists():
        print_error(f"Strategy '{name}' not found")
        raise typer.Exit(1)

    print_header(f"Strategy: {name}", str(strategy_path))

    with open(strategy_path, "r") as f:
        code = f.read()

    # Syntax highlighting
    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    console.print(syntax)


@app.command()
def backtest(
    name: str = typer.Argument(..., help="Strategy name"),
    timeframe: str = typer.Option("4h", "--timeframe", "-t", help="Timeframe"),
    days: int = typer.Option(90, "--days", "-d", help="Number of days"),
    dry_run: bool = typer.Option(True, "--dry-run/--live", help="Dry run mode"),
):
    """Run backtest for a strategy."""
    import subprocess

    print_header(f"Backtesting: {name}", f"{timeframe} timeframe, {days} days")

    strategy_path = Path(f"user_data/strategies/{name}.py")
    if not strategy_path.exists():
        print_error(f"Strategy '{name}' not found")
        raise typer.Exit(1)

    # Build freqtrade command
    config_file = (
        "proratio_utilities/config/freqtrade/config_dry.json"
        if dry_run
        else "proratio_utilities/config/freqtrade/config_live.json"
    )

    cmd = [
        "freqtrade",
        "backtesting",
        "--strategy",
        name,
        "--timeframe",
        timeframe,
        "--userdir",
        "user_data",
        "--config",
        config_file,
    ]

    console.print(f"\n[dim]Running: {' '.join(cmd)}[/dim]\n")

    try:
        result = subprocess.run(cmd, check=True)
        if result.returncode == 0:
            print_success("Backtest completed successfully!")
    except subprocess.CalledProcessError as e:
        print_error(f"Backtest failed: {e}")
        raise typer.Exit(1)


@app.command()
def validate(
    name: str = typer.Argument(..., help="Strategy name"),
    skip_backtest: bool = typer.Option(False, "--skip-backtest", help="Skip backtest validation"),
    skip_tests: bool = typer.Option(False, "--skip-tests", help="Skip integration tests"),
):
    """
    Validate strategy using the Strategy Validation Framework.

    Runs complete validation including:
    - Pre-flight checks (file exists, data available)
    - Backtest execution (2-3 min)
    - Results validation (min trades, win rate, drawdown, Sharpe, profit factor)
    - Integration tests (if available)
    - Code quality checks
    - Generate validation report
    """
    import subprocess
    import json
    from datetime import datetime

    strategy_path = Path(f"user_data/strategies/{name}.py")

    if not strategy_path.exists():
        print_error(f"Strategy '{name}' not found")
        raise typer.Exit(1)

    print_header(f"Validating Strategy: {name}", "Using Strategy Validation Framework")
    console.print("[dim]This will take 5-10 minutes...[/dim]\n")

    # Check if validation script exists
    validation_script = Path("scripts/validate_strategy.sh")
    if not validation_script.exists():
        print_error("Validation script not found: scripts/validate_strategy.sh")
        console.print("\n[yellow]Falling back to basic validation...[/yellow]\n")

        # Basic validation fallback
        with open(strategy_path, "r") as f:
            code = f.read()

        checks = {
            "IStrategy import": "from freqtrade.strategy import IStrategy" in code,
            "populate_indicators": "def populate_indicators" in code,
            "populate_entry_trend": "def populate_entry_trend" in code,
            "populate_exit_trend": "def populate_exit_trend" in code,
        }

        console.print()
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            console.print(f"{status} {check}")

        all_passed = all(checks.values())
        console.print()

        if all_passed:
            print_success("Basic validation passed!")
        else:
            print_error("Basic validation failed!")
            raise typer.Exit(1)
        return

    # Run full validation framework
    # Note: validation script expects: validate_strategy.sh <strategy> [timerange]
    # Use a shorter timerange if skip_backtest is requested
    if skip_backtest:
        console.print("[yellow]Note: --skip-backtest not supported by validation framework[/yellow]")
        console.print("[yellow]Use 'strategy backtest' command for simple backtests[/yellow]\n")
        # Still run validation but use short timerange
        timerange = "20241001-20241014"  # 2 weeks only
    else:
        timerange = "20240401-20241001"  # Default 6 months

    cmd = ["bash", str(validation_script), name, timerange]

    if skip_tests:
        console.print("[yellow]Note: Integration tests are optional - skipping has no effect[/yellow]\n")

    try:
        console.print(f"[dim]Running: {' '.join(cmd)}[/dim]\n")
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=False,
            text=True
        )

        console.print()

        # Check for validation report
        report_dir = Path("tests/validation_results") / name
        summary_file = report_dir / "validation_summary.json"

        if summary_file.exists():
            with open(summary_file, "r") as f:
                summary = json.load(f)

            status = summary.get("status", "UNKNOWN")
            checks_passed = summary.get("checks_passed", 0)
            checks_failed = summary.get("checks_failed", 0)

            console.print(f"\n📊 Validation Summary:")
            console.print(f"   Status: {status}")
            console.print(f"   Checks Passed: {checks_passed}")
            console.print(f"   Checks Failed: {checks_failed}")
            console.print(f"\n   Report: {summary_file}")
            console.print()

            if status == "PASSED":
                print_success(f"✅ Strategy '{name}' validation PASSED!")
                console.print("[green]Strategy meets all quality criteria and is ready for paper trading.[/green]\n")
            elif status == "PASSED_WITH_WARNINGS":
                console.print(f"[yellow]⚠️  Strategy '{name}' validation PASSED WITH WARNINGS[/yellow]")
                console.print("[yellow]Review warnings before deploying to paper trading.[/yellow]\n")
            else:
                print_error(f"❌ Strategy '{name}' validation FAILED")
                console.print("[red]Strategy does not meet quality criteria. Review report and fix issues.[/red]\n")
                raise typer.Exit(1)
        else:
            if result.returncode == 0:
                print_success("Validation completed!")
            else:
                print_error("Validation failed - check output above")
                raise typer.Exit(1)

    except Exception as e:
        print_error(f"Validation error: {e}")
        raise typer.Exit(1)
