"""
Strategy Commands

Manage trading strategies, view details, and run backtests.

Author: Proratio Team
Date: 2025-10-11
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.syntax import Syntax
from proratio_cli.utils.display import (
    print_header,
    create_strategy_table,
    print_error,
    print_success,
    print_section_header,
    console
)

app = typer.Typer()


@app.command()
def list():
    """List all available strategies."""
    print_header("Available Strategies", "Freqtrade strategy files")

    strategy_path = Path('user_data/strategies')

    if not strategy_path.exists():
        print_error("Strategy directory not found")
        raise typer.Exit(1)

    strategies = []
    for strategy_file in strategy_path.glob('*.py'):
        if not strategy_file.name.startswith('_') and strategy_file.name != '__init__.py':
            # Parse strategy info
            strategy_name = strategy_file.stem
            strategy_type = "Unknown"

            # Try to determine strategy type from name
            if 'AI' in strategy_name or 'Enhanced' in strategy_name:
                strategy_type = "AI-Enhanced"
            elif 'Mean' in strategy_name or 'Reversion' in strategy_name:
                strategy_type = "Mean Reversion"
            elif 'Grid' in strategy_name:
                strategy_type = "Grid Trading"
            elif 'Trend' in strategy_name:
                strategy_type = "Trend Following"
            elif 'FreqAI' in strategy_name:
                strategy_type = "FreqAI ML"

            strategies.append({
                'name': strategy_name,
                'type': strategy_type,
                'status': 'Active',
                'sharpe': 0.0  # Would need to read from backtest results
            })

    if strategies:
        table = create_strategy_table(strategies)
        console.print(table)
        console.print(f"\n[dim]Total: {len(strategies)} strategies[/dim]\n")
    else:
        print_error("No strategies found")


@app.command()
def show(
    name: str = typer.Argument(..., help="Strategy name"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show")
):
    """Show strategy source code."""
    strategy_path = Path(f'user_data/strategies/{name}.py')

    if not strategy_path.exists():
        print_error(f"Strategy '{name}' not found")
        raise typer.Exit(1)

    print_header(f"Strategy: {name}", str(strategy_path))

    with open(strategy_path, 'r') as f:
        code = f.read()

    # Syntax highlighting
    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    console.print(syntax)


@app.command()
def backtest(
    name: str = typer.Argument(..., help="Strategy name"),
    timeframe: str = typer.Option("4h", "--timeframe", "-t", help="Timeframe"),
    days: int = typer.Option(90, "--days", "-d", help="Number of days"),
    dry_run: bool = typer.Option(True, "--dry-run/--live", help="Dry run mode")
):
    """Run backtest for a strategy."""
    import subprocess

    print_header(f"Backtesting: {name}", f"{timeframe} timeframe, {days} days")

    strategy_path = Path(f'user_data/strategies/{name}.py')
    if not strategy_path.exists():
        print_error(f"Strategy '{name}' not found")
        raise typer.Exit(1)

    # Build freqtrade command
    config_file = 'proratio_utilities/config/freqtrade/config_dry.json' if dry_run else 'proratio_utilities/config/freqtrade/config_live.json'

    cmd = [
        'freqtrade', 'backtesting',
        '--strategy', name,
        '--timeframe', timeframe,
        '--userdir', 'user_data',
        '--config', config_file
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
def validate(name: str = typer.Argument(..., help="Strategy name")):
    """Validate strategy configuration."""
    strategy_path = Path(f'user_data/strategies/{name}.py')

    if not strategy_path.exists():
        print_error(f"Strategy '{name}' not found")
        raise typer.Exit(1)

    print_header(f"Validating: {name}", "Checking strategy configuration")

    # Simple validation checks
    with open(strategy_path, 'r') as f:
        code = f.read()

    checks = {
        'IStrategy import': 'from freqtrade.strategy import IStrategy' in code,
        'populate_indicators': 'def populate_indicators' in code,
        'populate_entry_trend': 'def populate_entry_trend' in code,
        'populate_exit_trend': 'def populate_exit_trend' in code,
    }

    console.print()
    for check, passed in checks.items():
        status = '✅' if passed else '❌'
        console.print(f"{status} {check}")

    all_passed = all(checks.values())
    console.print()

    if all_passed:
        print_success("Strategy validation passed!")
    else:
        print_error("Strategy validation failed!")
        raise typer.Exit(1)
