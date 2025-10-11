"""
Data Commands

Manage historical market data.

Author: Proratio Team
Date: 2025-10-11
"""

import typer
import subprocess
from proratio_cli.utils.display import print_header, print_success, print_error, console

app = typer.Typer()


@app.command()
def download(
    pairs: str = typer.Option("BTC/USDT,ETH/USDT", "--pairs", "-p", help="Trading pairs (comma-separated)"),
    timeframes: str = typer.Option("1h,4h", "--timeframes", "-t", help="Timeframes (comma-separated)"),
    days: int = typer.Option(180, "--days", "-d", help="Number of days")
):
    """Download historical data."""
    print_header("Downloading Historical Data", f"{pairs} for {days} days")

    pair_list = pairs.split(',')
    timeframe_list = timeframes.split(',')

    for timeframe in timeframe_list:
        cmd = [
            'freqtrade', 'download-data',
            '--exchange', 'binance',
            '--pairs', *pair_list,
            '--timeframe', timeframe,
            '--days', str(days),
            '--userdir', 'user_data'
        ]

        console.print(f"\n[dim]Downloading {timeframe} data...[/dim]")

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print_error(f"Download failed: {e}")
            raise typer.Exit(1)

    print_success("Data download complete!")


@app.command()
def status():
    """Show data availability status."""
    from pathlib import Path

    print_header("Data Status", "Available market data files")

    data_path = Path('user_data/data')
    if not data_path.exists():
        print_error("Data directory not found")
        raise typer.Exit(1)

    feather_files = list(data_path.glob('*.feather'))
    json_files = list(data_path.glob('*.json'))

    console.print(f"\n[cyan]Feather files:[/cyan] {len(feather_files)}")
    for f in feather_files[:10]:  # Show first 10
        console.print(f"  • {f.name}")

    console.print(f"\n[cyan]JSON files:[/cyan] {len(json_files)}")
    for f in json_files[:10]:
        console.print(f"  • {f.name}")

    console.print()
