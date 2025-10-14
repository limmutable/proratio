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
    console,
)

app = typer.Typer()


@app.command()
def quickstart():
    """Quick start guide."""
    print_header("Quick Start Guide", "Get started with Proratio in 5 minutes")

    print_section_header("1. Check System Status")
    print_command_example("./start.sh", "Show startup status")
    print_command_example("./start.sh status all", "Detailed system check")

    print_section_header("2. Download Data")
    print_command_example(
        "./start.sh data download --pairs BTC/USDT --days 180",
        "Download 180 days of BTC data",
    )

    print_section_header("3. List Strategies")
    print_command_example(
        "./start.sh strategy list", "Show all available strategies"
    )

    print_section_header("4. Backtest Strategy")
    print_command_example(
        "./start.sh strategy backtest AIEnhancedStrategy --days 90",
        "Backtest strategy on 90 days",
    )

    print_section_header("5. Start Paper Trading")
    print_command_example(
        "./start.sh trade start --strategy AIEnhancedStrategy",
        "Start dry-run trading",
    )


@app.command()
def commands():
    """Show all available commands."""
    print_header("Available Commands", "Complete command reference")

    menu_items = {
        "Status Commands": [
            "./start.sh status all - Complete system status",
            "./start.sh status providers - LLM provider status",
            "./start.sh status data - Data availability",
            "./start.sh status models - ML models status",
        ],
        "Strategy Commands": [
            "./start.sh strategy list - List all strategies",
            "./start.sh strategy show <name> - Show strategy code",
            "./start.sh strategy backtest <name> - Run backtest",
            "./start.sh strategy validate <name> - Validate strategy",
        ],
        "Configuration": [
            "./start.sh config show - Show configuration",
            "./start.sh config set <key> <value> - Set config value",
            "./start.sh config validate - Validate config",
        ],
        "Data Management": [
            "./start.sh data download - Download historical data",
            "./start.sh data status - Show data files",
        ],
        "Trading Operations": [
            "./start.sh trade start - Start paper trading",
            "./start.sh trade start --live - Start live trading",
            "./start.sh trade stop - Stop trading",
            "./start.sh trade monitor - Monitor trades",
        ],
        "Help & Guides": [
            "./start.sh help quickstart - Quick start guide",
            "./start.sh help commands - All commands",
            "./start.sh help config - Configuration guide",
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
    print_command_example("./start.sh config show", "View current configuration")
    print_command_example(
        "./start.sh config set risk.max_loss_per_trade_pct 0.02",
        "Set max loss to 2%",
    )

    print_section_header("Validation")
    print_command_example(
        "./start.sh config validate", "Validate configuration file"
    )


@app.command()
def ml():
    """Machine learning guide."""
    print_header("Machine Learning Guide", "Train and use ML models")

    print_section_header("1. Train LSTM Model")
    print_command_example(
        "python scripts/train_lstm_model.py --pair BTC/USDT --epochs 100",
        "Train LSTM for price prediction",
    )

    print_section_header("2. Train Ensemble Model")
    print_command_example(
        "python scripts/example_ensemble_usage.py",
        "Train ensemble (LSTM + LightGBM + XGBoost)",
    )

    print_section_header("3. Use in Strategy")
    console.print("Integrate trained models in your FreqAI strategy")
    console.print("See: [cyan]docs/ensemble_implementation.md[/cyan]\n")


@app.command()
def validate():
    """Strategy validation guide."""
    print_header("Strategy Validation Guide", "Using the Strategy Validation Framework")

    print_section_header("Overview")
    console.print("The validation framework tests strategies in 5-10 minutes vs 5-7 days of paper trading.")
    console.print("It runs 6 automated checks:\n")
    console.print("  1. Pre-flight checks (file exists, data available)")
    console.print("  2. Backtest execution (2-3 min)")
    console.print("  3. Results validation (trades, win rate, drawdown, Sharpe, profit factor)")
    console.print("  4. Integration tests (if available)")
    console.print("  5. Code quality checks")
    console.print("  6. Generate validation report\n")

    print_section_header("Basic Usage")
    print_command_example(
        "./start.sh strategy validate <strategy_name>",
        "Validate any strategy (takes 5-10 min)"
    )
    print_command_example(
        "./start.sh strategy validate AIEnhancedStrategy",
        "Example: Validate AIEnhancedStrategy"
    )

    print_section_header("Validation Criteria")
    console.print("  ✓ Minimum trades: 5")
    console.print("  ✓ Win rate: ≥ 45%")
    console.print("  ✓ Max drawdown: < 25%")
    console.print("  ✓ Sharpe ratio: ≥ 0.5")
    console.print("  ✓ Profit factor: ≥ 1.0\n")

    print_section_header("Faster Testing")
    print_command_example(
        "./start.sh strategy validate MyStrategy --skip-backtest",
        "Use shorter timerange (2 weeks vs 6 months)"
    )

    print_section_header("View Results")
    console.print("Validation reports saved to:")
    console.print("  [cyan]tests/validation_results/<strategy_name>/[/cyan]\n")
    console.print("Includes:")
    console.print("  • validation_summary.json - Pass/fail status")
    console.print("  • <strategy>_validation_<timestamp>.txt - Full report")
    console.print("  • backtest_results.json - Backtest metrics\n")

    print_section_header("Next Steps After Validation")
    console.print("  [green]PASSED[/green] → Ready for paper trading")
    console.print("  [yellow]PASSED_WITH_WARNINGS[/yellow] → Review warnings first")
    console.print("  [red]FAILED[/red] → Fix issues and re-validate\n")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Show help menu."""
    if ctx.invoked_subcommand is None:
        print_header("Proratio Help", "Interactive help system")

        console.print("\n[bold cyan]Available Help Topics:[/bold cyan]\n")
        console.print("  [green]quickstart[/green]  - Quick start guide")
        console.print("  [green]commands[/green]     - All available commands")
        console.print("  [green]validate[/green]     - Strategy validation guide")
        console.print("  [green]config[/green]       - Configuration guide")
        console.print("  [green]ml[/green]           - Machine learning guide")

        console.print("\n[dim]Usage: ./start.sh help <topic>[/dim]\n")
