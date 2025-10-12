"""
Configuration Commands

View and modify trading configuration.

Author: Proratio Team
Date: 2025-10-11
"""

import typer
import json
from pathlib import Path
from typing import Optional
from rich.json import JSON
from proratio_cli.utils.display import print_header, print_success, print_error, console

app = typer.Typer()

CONFIG_PATH = Path("proratio_utilities/config/trading_config.json")


@app.command()
def show(section: Optional[str] = None):
    """Show trading configuration."""
    if not CONFIG_PATH.exists():
        print_error("Config file not found")
        raise typer.Exit(1)

    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    if section:
        # Show specific section as JSON
        if section in config:
            console.print()
            console.print(f"[bold cyan]Configuration Section:[/bold cyan] {section}")
            console.print(f"[dim]File: {CONFIG_PATH}[/dim]")
            console.print()
            console.print(JSON(json.dumps(config[section], indent=2)))
            console.print()
        else:
            print_error(f"Section '{section}' not found")
            console.print(f"[dim]Available sections: {', '.join(config.keys())}[/dim]")
            raise typer.Exit(1)
    else:
        # Show summary of key configurations
        console.print()
        console.print("[bold cyan]Trading Configuration Summary[/bold cyan]")
        console.print()

        # Risk Management
        console.print("[bold]Risk Management:[/bold]")
        risk = config.get("risk", {})
        console.print(
            f"  Max loss per trade: [yellow]{risk.get('max_loss_per_trade_pct', 'N/A')}%[/yellow]"
        )
        console.print(
            f"  Max drawdown: [yellow]{risk.get('max_total_drawdown_pct', 'N/A')}%[/yellow]"
        )
        console.print(
            f"  Max concurrent positions: [yellow]{risk.get('max_concurrent_positions', 'N/A')}[/yellow]"
        )
        console.print()

        # Trading Strategy
        console.print("[bold]Strategy:[/bold]")
        strategy = config.get("strategy", {})
        console.print(f"  Name: [cyan]{strategy.get('strategy_name', 'N/A')}[/cyan]")
        console.print(f"  Timeframe: [cyan]{strategy.get('timeframe', 'N/A')}[/cyan]")
        pairs = strategy.get("pairs", [])
        console.print(
            f"  Trading pairs: [cyan]{', '.join(pairs) if pairs else 'N/A'}[/cyan]"
        )
        console.print(
            f"  Stop loss: [yellow]{strategy.get('stoploss_pct', 'N/A')}%[/yellow]"
        )
        console.print()

        # AI Configuration
        console.print("[bold]AI Providers:[/bold]")
        ai = config.get("ai", {})
        console.print(
            f"  ChatGPT weight: [green]{ai.get('chatgpt_weight', 'N/A')}[/green]"
        )
        console.print(
            f"  Claude weight: [green]{ai.get('claude_weight', 'N/A')}[/green]"
        )
        console.print(
            f"  Gemini weight: [green]{ai.get('gemini_weight', 'N/A')}[/green]"
        )
        console.print(
            f"  Min consensus: [green]{ai.get('min_consensus_score', 'N/A')}[/green]"
        )
        console.print()

        # Execution
        console.print("[bold]Execution:[/bold]")
        execution = config.get("execution", {})
        mode = execution.get("trading_mode", "N/A")
        mode_color = "green" if mode == "dry_run" else "red"
        console.print(f"  Mode: [{mode_color}]{mode}[/{mode_color}]")
        console.print(f"  Exchange: [cyan]{execution.get('exchange', 'N/A')}[/cyan]")
        console.print(
            f"  Starting balance: [yellow]{execution.get('starting_balance', 'N/A')} {execution.get('stake_currency', 'USDT')}[/yellow]"
        )
        console.print(
            f"  Stake per trade: [yellow]{execution.get('stake_amount', 'N/A')} {execution.get('stake_currency', 'USDT')}[/yellow]"
        )
        console.print()

        # File locations
        console.print("[bold]Configuration Files:[/bold]")
        console.print(f"  [dim]Main config: {CONFIG_PATH}[/dim]")
        console.print(
            "  [dim]Freqtrade config: proratio_utilities/config/freqtrade/config_dry.json[/dim]"
        )
        console.print()

        # Usage hint
        console.print(
            "[dim]Use [cyan]/config show <section>[/cyan] to view full section details[/dim]"
        )
        console.print(
            "[dim]Available sections: {0}[/dim]".format(", ".join(config.keys()))
        )
        console.print()


@app.command()
def set(key: str, value: str):
    """Set configuration value."""
    if not CONFIG_PATH.exists():
        print_error("Config file not found")
        raise typer.Exit(1)

    parts = key.split(".")
    if len(parts) != 2:
        print_error("Key must be in format 'section.key'")
        raise typer.Exit(1)

    section, key_name = parts

    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    if section not in config:
        print_error(f"Section '{section}' not found")
        raise typer.Exit(1)

    # Try to convert value to appropriate type
    try:
        if value.lower() in ("true", "false"):
            value = value.lower() == "true"
        elif "." in value:
            value = float(value)
        elif value.isdigit():
            value = int(value)
    except:
        pass  # Keep as string

    config[section][key_name] = value

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    print_success(f"Set {section}.{key_name} = {value}")


@app.command()
def validate():
    """Validate configuration file."""
    if not CONFIG_PATH.exists():
        print_error("Config file not found")
        raise typer.Exit(1)

    print_header("Validating Configuration", str(CONFIG_PATH))

    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

        required_sections = ["risk", "position_sizing", "trading"]
        checks = {}

        for section in required_sections:
            checks[f"{section} section"] = section in config

        console.print()
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            console.print(f"{status} {check}")

        console.print()

        if all(checks.values()):
            print_success("Configuration is valid!")
        else:
            print_error("Configuration has errors!")
            raise typer.Exit(1)

    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        raise typer.Exit(1)
