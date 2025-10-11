"""
Help Commands

Interactive help and guides for users.

Author: Proratio Team
Date: 2025-10-11
"""

import typer
from proratio_cli.utils.display import (
    print_header,
    print_section_header,
    print_command_example,
    create_tree_menu,
    console
)

app = typer.Typer()


@app.command()
def quickstart():
    """Quick start guide."""
    print_header("Quick Start Guide", "Get started with Proratio in 5 minutes")

    print_section_header("1. Check System Status")
    print_command_example("./start.sh cli", "Show startup status")
    print_command_example("./start.sh cli status all", "Detailed system check")

    print_section_header("2. Download Data")
    print_command_example(
        "./start.sh cli data download --pairs BTC/USDT --days 180",
        "Download 180 days of BTC data"
    )

    print_section_header("3. List Strategies")
    print_command_example("./start.sh cli strategy list", "Show all available strategies")

    print_section_header("4. Backtest Strategy")
    print_command_example(
        "./start.sh cli strategy backtest AIEnhancedStrategy --days 90",
        "Backtest strategy on 90 days"
    )

    print_section_header("5. Start Paper Trading")
    print_command_example(
        "./start.sh cli trade start --strategy AIEnhancedStrategy",
        "Start dry-run trading"
    )


@app.command()
def commands():
    """Show all available commands."""
    print_header("Available Commands", "Complete command reference")

    menu_items = {
        "Status Commands": [
            "./start.sh cli status all - Complete system status",
            "./start.sh cli status providers - LLM provider status",
            "./start.sh cli status data - Data availability",
            "./start.sh cli status models - ML models status",
        ],
        "Strategy Commands": [
            "./start.sh cli strategy list - List all strategies",
            "./start.sh cli strategy show <name> - Show strategy code",
            "./start.sh cli strategy backtest <name> - Run backtest",
            "./start.sh cli strategy validate <name> - Validate strategy",
        ],
        "Configuration": [
            "./start.sh cli config show - Show configuration",
            "./start.sh cli config set <key> <value> - Set config value",
            "./start.sh cli config validate - Validate config",
        ],
        "Data Management": [
            "./start.sh cli data download - Download historical data",
            "./start.sh cli data status - Show data files",
        ],
        "Trading Operations": [
            "./start.sh cli trade start - Start paper trading",
            "./start.sh cli trade start --live - Start live trading",
            "./start.sh cli trade stop - Stop trading",
            "./start.sh cli trade monitor - Monitor trades",
        ],
        "Help & Guides": [
            "./start.sh cli help quickstart - Quick start guide",
            "./start.sh cli help commands - All commands",
            "./start.sh cli help config - Configuration guide",
        ],
    }

    tree = create_tree_menu("Proratio Commands", menu_items)
    console.print(tree)


@app.command()
def config():
    """Configuration guide."""
    print_header("Configuration Guide", "Setting up Proratio")

    print_section_header("Environment Variables (.env)")
    console.print("Create a .env file with:")
    console.print("  [cyan]DATABASE_URL[/cyan] - PostgreSQL connection")
    console.print("  [cyan]OPENAI_API_KEY[/cyan] - OpenAI API key")
    console.print("  [cyan]ANTHROPIC_API_KEY[/cyan] - Anthropic API key")
    console.print("  [cyan]GEMINI_API_KEY[/cyan] - Google Gemini API key")
    console.print("  [cyan]BINANCE_API_KEY[/cyan] - Binance API key")
    console.print("  [cyan]BINANCE_API_SECRET[/cyan] - Binance API secret\n")

    print_section_header("Trading Configuration")
    print_command_example(
        "./start.sh cli config show",
        "View current configuration"
    )
    print_command_example(
        "./start.sh cli config set risk.max_loss_per_trade_pct 0.02",
        "Set max loss to 2%"
    )

    print_section_header("Validation")
    print_command_example(
        "./start.sh cli config validate",
        "Validate configuration file"
    )


@app.command()
def ml():
    """Machine learning guide."""
    print_header("Machine Learning Guide", "Train and use ML models")

    print_section_header("1. Train LSTM Model")
    print_command_example(
        "python scripts/train_lstm_model.py --pair BTC/USDT --epochs 100",
        "Train LSTM for price prediction"
    )

    print_section_header("2. Train Ensemble Model")
    print_command_example(
        "python scripts/example_ensemble_usage.py",
        "Train ensemble (LSTM + LightGBM + XGBoost)"
    )

    print_section_header("3. Use in Strategy")
    console.print("Integrate trained models in your FreqAI strategy")
    console.print("See: [cyan]docs/ensemble_implementation.md[/cyan]\n")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Show help menu."""
    if ctx.invoked_subcommand is None:
        print_header("Proratio Help", "Interactive help system")

        console.print("\n[bold cyan]Available Help Topics:[/bold cyan]\n")
        console.print("  [green]quickstart[/green]  - Quick start guide")
        console.print("  [green]commands[/green]     - All available commands")
        console.print("  [green]config[/green]       - Configuration guide")
        console.print("  [green]ml[/green]           - Machine learning guide")

        console.print("\n[dim]Usage: ./start.sh cli help <topic>[/dim]\n")
