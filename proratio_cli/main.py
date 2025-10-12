"""
Proratio CLI - Main Entry Point

Command-line interface for the Proratio AI-driven cryptocurrency trading system.

Usage:
    proratio                # Show startup status
    proratio status         # System status
    proratio help          # Show help

Author: Proratio Team
Date: 2025-10-11
"""

import typer
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from proratio_cli.utils.display import (
    print_header,
    print_success,
    print_error,
    print_info,
    create_status_table,
    console,
)
from proratio_cli.utils.checks import run_all_checks, get_llm_provider_status

# Import command groups
from proratio_cli.commands import status, strategy, config, data, trade, help_cmd

# Create main app
app = typer.Typer(
    name="proratio",
    help="🤖 Proratio - AI-Driven Cryptocurrency Trading System",
    add_completion=True,
    no_args_is_help=False,  # Allow running without args to show status
)

# Add command groups
app.add_typer(status.app, name="status", help="📊 System status and health checks")
app.add_typer(strategy.app, name="strategy", help="📈 Strategy management")
app.add_typer(config.app, name="config", help="⚙️  Configuration management")
app.add_typer(data.app, name="data", help="💾 Data management")
app.add_typer(trade.app, name="trade", help="💰 Trading operations")
app.add_typer(help_cmd.app, name="help", help="❓ Help and guides")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
):
    """
    Proratio - AI-Driven Cryptocurrency Trading System

    Run without arguments to launch interactive shell mode.
    Use --help to see available commands.
    """
    if version:
        print_info("Proratio v0.8.0")
        raise typer.Exit()

    # If no subcommand, launch interactive shell
    if ctx.invoked_subcommand is None:
        from proratio_cli.shell import run_shell

        run_shell()


def show_startup_status():
    """Display startup status with system checks."""
    print_header(
        "🤖 Proratio Trading System", "AI-Driven Cryptocurrency Trading | Version 0.8.0"
    )

    console.print("\n[bold cyan]System Status[/bold cyan]\n")

    # Run all checks
    checks = run_all_checks()

    # Prepare data for status table
    status_data = []
    for component, (success, details) in checks.items():
        status_data.append(
            {
                "component": component,
                "status": "✅" if success else "❌",
                "details": details,
            }
        )

    # Display system status
    table = create_status_table("Core Systems", status_data)
    console.print(table)

    # LLM Provider status
    console.print("\n[bold cyan]LLM Providers[/bold cyan]\n")
    provider_status = get_llm_provider_status()

    provider_data = []
    for provider, (success, details) in provider_status.items():
        provider_data.append(
            {
                "component": provider,
                "status": "✅" if success else "❌",
                "details": details,
            }
        )

    provider_table = create_status_table("AI Providers", provider_data)
    console.print(provider_table)

    # Summary
    total_checks = len(checks)
    passed_checks = sum(1 for success, _ in checks.values() if success)
    provider_count = sum(1 for success, _ in provider_status.values() if success)

    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  System Checks: {passed_checks}/{total_checks} passing")
    console.print(f"  LLM Providers: {provider_count}/3 configured")

    if passed_checks == total_checks:
        print_success("All systems operational!")
    elif passed_checks >= total_checks * 0.7:
        console.print("\n⚠️  [yellow]Some systems need attention[/yellow]")
    else:
        print_error("Critical systems offline. Please check configuration.")

    # Quick help
    console.print("\n[dim]Run 'proratio --help' for available commands[/dim]\n")


if __name__ == "__main__":
    app()
