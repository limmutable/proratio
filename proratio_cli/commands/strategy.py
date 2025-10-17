"""
Strategy Commands

Manage trading strategies, view details, and run backtests.

Author: Proratio Team
Date: 2025-10-11
Updated: 2025-10-16 - Integrated with Strategy Registry System
"""

import typer
from pathlib import Path
from rich.syntax import Syntax
from rich.table import Table
from proratio_cli.utils.display import (
    print_header,
    create_strategy_table,
    print_error,
    print_success,
    print_info,
    console,
)
from proratio_utilities.strategy_registry import get_strategy_registry

app = typer.Typer()


@app.command()
def list(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status (active, archived, experimental)"),
    category: str = typer.Option(None, "--category", "-c", help="Filter by category (ai-enhanced, grid, mean-reversion, etc.)"),
    show_archived: bool = typer.Option(False, "--archived", "-a", help="Show archived strategies"),
):
    """List all available strategies from the Strategy Registry."""
    registry = get_strategy_registry()

    # Fix: Handle typer.Option objects when called from shell (not CLI)
    # This happens when shell.py calls strategy.list() directly
    import typer.models
    if isinstance(status, typer.models.OptionInfo):
        status = None
    if isinstance(category, typer.models.OptionInfo):
        category = None
    if isinstance(show_archived, typer.models.OptionInfo):
        show_archived = False

    # Determine what to show
    if show_archived:
        status = "archived"

    print_header(
        "Strategy Registry",
        f"Status: {status or 'all'} | Category: {category or 'all'}"
    )

    # Get strategies from registry
    strategies = registry.list_strategies(status=status, category=category)

    if not strategies:
        print_error(f"No strategies found with filters: status={status}, category={category}")
        return

    # Create rich table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Category")
    table.add_column("Status")
    table.add_column("Win Rate", justify="right")
    table.add_column("Version")
    table.add_column("Created")

    for strategy in strategies:
        # Get performance metrics
        perf = strategy.performance
        win_rate = "N/A"

        # Try backtest first, then paper trading
        if perf.get("backtest") and perf["backtest"].get("win_rate"):
            win_rate = f"{perf['backtest']['win_rate']:.1%}"
        elif perf.get("paper_trading") and perf["paper_trading"].get("win_rate"):
            win_rate = f"{perf['paper_trading']['win_rate']:.1%}"

        # Status emoji
        status_emoji = {
            "active": "✅",
            "experimental": "🧪",
            "archived": "📦",
            "paused": "⏸️"
        }.get(strategy.status, "❓")

        # Format created date (just date, not time)
        created_date = strategy.created_datetime.split("T")[0]

        table.add_row(
            strategy.id.split("_")[0],  # Just the hash
            strategy.name,
            strategy.category,
            f"{status_emoji} {strategy.status}",
            win_rate,
            strategy.version,
            created_date,
        )

    console.print(table)

    # Summary
    counts = registry.get_strategy_count()
    console.print(f"\n[dim]Total: {len(strategies)} strategies | Active: {counts['active']} | Archived: {counts['archived']} | Experimental: {counts['experimental']}[/dim]\n")

    # Hints
    if not show_archived and counts['archived'] > 0:
        console.print("[dim]Tip: Use --archived to see archived strategies[/dim]")
    console.print("[dim]Tip: Use 'strategy show <id>' to view strategy details[/dim]\n")


@app.command()
def show(
    strategy_id: str = typer.Argument(..., help="Strategy ID or hash (e.g., 'a014' or 'a014_hybrid-ml-llm')"),
    show_code: bool = typer.Option(False, "--code", "-c", help="Show strategy source code"),
):
    """Show strategy details from the registry."""
    # Fix: Handle typer.Option objects when called from shell
    import typer.models
    if isinstance(show_code, typer.models.OptionInfo):
        show_code = False

    registry = get_strategy_registry()

    # Try to find strategy - accept either full ID or just hash
    strategy = None
    if "_" not in strategy_id:
        # Just a hash, find matching strategy
        for s in registry.list_strategies():
            if s.id.startswith(strategy_id):
                strategy = s
                break
    else:
        # Full ID
        strategy = registry.get_strategy(strategy_id)

    if not strategy:
        print_error(f"Strategy '{strategy_id}' not found in registry")
        console.print("\n[dim]Tip: Use 'strategy list' to see all strategies[/dim]\n")
        raise typer.Exit(1)

    print_header(f"Strategy: {strategy.name}", f"ID: {strategy.id}")

    # Display metadata
    console.print(f"[bold cyan]Metadata[/bold cyan]")
    console.print(f"  Class Name: {strategy.class_name}")
    console.print(f"  Status: {strategy.status}")
    console.print(f"  Category: {strategy.category}")
    console.print(f"  Version: {strategy.version}")
    console.print(f"  Author: {strategy.author}")
    console.print(f"  Created: {strategy.created_datetime}")
    console.print(f"  Last Edited: {strategy.last_edited}")
    console.print()

    console.print(f"[bold cyan]Description[/bold cyan]")
    console.print(f"  {strategy.description}")
    console.print()

    console.print(f"[bold cyan]Tags[/bold cyan]")
    console.print(f"  {', '.join(strategy.tags)}")
    console.print()

    # Parameters
    console.print(f"[bold cyan]Parameters[/bold cyan]")
    for key, value in strategy.parameters.items():
        console.print(f"  {key}: {value}")
    console.print()

    # Performance
    console.print(f"[bold cyan]Performance[/bold cyan]")
    for test_type, metrics in strategy.performance.items():
        if metrics:
            console.print(f"  {test_type.title()}:")
            for metric, value in metrics.items():
                if value is not None:
                    console.print(f"    {metric}: {value}")
    console.print()

    # Path info
    console.print(f"[bold cyan]File Locations[/bold cyan]")
    console.print(f"  Directory: {strategy.path['directory']}")
    console.print(f"  Main File: {strategy.path['main_file']}")
    if strategy.path.get('freqtrade_adapter'):
        console.print(f"  Freqtrade Adapter: {strategy.path['freqtrade_adapter']}")
    console.print()

    # Notes
    if strategy.notes:
        console.print(f"[bold cyan]Notes[/bold cyan]")
        console.print(f"  {strategy.notes}")
        console.print()

    # Archived info
    if strategy.status == "archived" and strategy.archived_reason:
        console.print(f"[bold yellow]Archived Information[/bold yellow]")
        console.print(f"  Reason: {strategy.archived_reason}")
        console.print(f"  Date: {strategy.archived_datetime}")
        console.print()

    # Show code if requested
    if show_code:
        strategy_file = Path(strategy.path['directory']) / strategy.path['main_file']
        if strategy_file.exists():
            console.print(f"[bold cyan]Source Code[/bold cyan]")
            with open(strategy_file, "r") as f:
                code = f.read()
            syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            print_error(f"Strategy file not found: {strategy_file}")
    else:
        console.print("[dim]Tip: Use --code to view source code[/dim]\n")


@app.command()
def backtest(
    name: str = typer.Argument(..., help="Strategy name"),
    timeframe: str = typer.Option("4h", "--timeframe", "-t", help="Timeframe"),
    days: int = typer.Option(90, "--days", "-d", help="Number of days"),
    dry_run: bool = typer.Option(True, "--dry-run/--live", help="Dry run mode"),
):
    """Run backtest for a strategy."""
    import subprocess

    # Fix: Handle typer.Option objects when called from shell
    import typer.models
    if isinstance(timeframe, typer.models.OptionInfo):
        timeframe = "4h"
    if isinstance(days, typer.models.OptionInfo):
        days = 90
    if isinstance(dry_run, typer.models.OptionInfo):
        dry_run = True

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

    # Fix: Handle typer.Option objects when called from shell
    import typer.models
    if isinstance(skip_backtest, typer.models.OptionInfo):
        skip_backtest = False
    if isinstance(skip_tests, typer.models.OptionInfo):
        skip_tests = False

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
