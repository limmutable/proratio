"""
Trading Commands

Start, stop, and monitor trading operations.

Author: Proratio Team
Date: 2025-10-11
"""

import typer
import subprocess
import json
from proratio_cli.utils.display import (
    print_header,
    print_success,
    print_error,
    print_warning,
    console,
)
from proratio_utilities.config import load_and_hydrate_config

app = typer.Typer()


@app.command()
def start(
    strategy: str = typer.Option(
        "ProRatioAdapter", "--strategy", "-s", help="Strategy name"
    ),
    live: bool = typer.Option(False, "--live", help="Live trading (default: dry-run)"),
    dashboard: bool = typer.Option(
        True, "--dashboard/--no-dashboard", help="Start dashboard"
    ),
):
    """Start trading bot."""
    # Fix: Handle typer.Option objects when called from shell
    import typer.models
    if isinstance(strategy, typer.models.OptionInfo):
        strategy = "ProRatioAdapter"
    if isinstance(live, typer.models.OptionInfo):
        live = False
    if isinstance(dashboard, typer.models.OptionInfo):
        dashboard = True

    mode = "live" if live else "dry-run"
    config_file = (
        "proratio_utilities/config/freqtrade/config_live.json"
        if live
        else "proratio_utilities/config/freqtrade/config_dry.json"
    )

    print_header(f"Starting Trading Bot - {mode.upper()}", f"Strategy: {strategy}")

    if live:
        print_warning("⚠️  LIVE TRADING MODE - Real money at risk!")
        confirm = typer.confirm("Are you sure you want to proceed?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit()

    # Load and hydrate config with secrets from .env
    try:
        hydrated_config = load_and_hydrate_config(config_file)
        config_json = json.dumps(hydrated_config)
    except Exception as e:
        print_error(f"Failed to load configuration: {e}")
        raise typer.Exit(1)

    cmd = [
        "freqtrade",
        "trade",
        "--strategy",
        strategy,
        "--userdir",
        "user_data",
        "--config",
        "-",  # Read config from stdin
    ]

    console.print(f"\n[dim]Running: {' '.join(cmd)}[/dim]\n")

    try:
        # Pass hydrated config via stdin
        subprocess.run(cmd, input=config_json, text=True)
        print_success("Trading bot stopped")
    except KeyboardInterrupt:
        print_warning("Trading interrupted by user")
    except subprocess.CalledProcessError as e:
        print_error(f"Trading failed: {e}")
        raise typer.Exit(1)


@app.command()
def stop():
    """Stop running trading bot."""
    print_header("Stopping Trading Bot", "Graceful shutdown")

    try:
        subprocess.run(["pkill", "-f", "freqtrade trade"], check=True)
        print_success("Trading bot stopped")
    except subprocess.CalledProcessError:
        print_warning("No running bot found")


@app.command()
def monitor():
    """Monitor trading activity."""
    print_header("Trading Monitor", "Real-time trading activity")

    # cmd = ['freqtrade', 'trade', '--userdir', 'user_data', '--config', 'proratio_utilities/config/freqtrade/config_dry.json', '--db-url', 'sqlite:///user_data/tradesv3.sqlite']

    console.print("[yellow]Feature coming soon![/yellow]")
    console.print(
        "Use Streamlit dashboard: streamlit run proratio_tradehub/dashboard/app.py\n"
    )
