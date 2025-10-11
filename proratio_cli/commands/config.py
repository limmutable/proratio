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
from rich.console import Console
from rich.json import JSON
from proratio_cli.utils.display import (
    print_header,
    print_success,
    print_error,
    create_config_table,
    console
)

app = typer.Typer()

CONFIG_PATH = Path('proratio_utilities/config/trading_config.json')


@app.command()
def show(
    section: Optional[str] = typer.Argument(None, help="Config section to show")
):
    """Show trading configuration."""
    if not CONFIG_PATH.exists():
        print_error("Config file not found")
        raise typer.Exit(1)

    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    if section:
        if section in config:
            print_header(f"Configuration: {section}", str(CONFIG_PATH))
            console.print(JSON(json.dumps(config[section], indent=2)))
        else:
            print_error(f"Section '{section}' not found")
            raise typer.Exit(1)
    else:
        print_header("Trading Configuration", str(CONFIG_PATH))
        console.print(JSON(json.dumps(config, indent=2)))


@app.command()
def set(
    key: str = typer.Argument(..., help="Config key (section.key)"),
    value: str = typer.Argument(..., help="New value")
):
    """Set configuration value."""
    if not CONFIG_PATH.exists():
        print_error("Config file not found")
        raise typer.Exit(1)

    parts = key.split('.')
    if len(parts) != 2:
        print_error("Key must be in format 'section.key'")
        raise typer.Exit(1)

    section, key_name = parts

    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    if section not in config:
        print_error(f"Section '{section}' not found")
        raise typer.Exit(1)

    # Try to convert value to appropriate type
    try:
        if value.lower() in ('true', 'false'):
            value = value.lower() == 'true'
        elif '.' in value:
            value = float(value)
        elif value.isdigit():
            value = int(value)
    except:
        pass  # Keep as string

    config[section][key_name] = value

    with open(CONFIG_PATH, 'w') as f:
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
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)

        required_sections = ['risk', 'position_sizing', 'trading']
        checks = {}

        for section in required_sections:
            checks[f"{section} section"] = section in config

        console.print()
        for check, passed in checks.items():
            status = '✅' if passed else '❌'
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
