"""
Status Commands

Display system status, health checks, and monitoring information.

Author: Proratio Team
Date: 2025-10-11
"""

import typer
from proratio_cli.utils.display import print_header, create_status_table, console
from proratio_cli.utils.checks import (
    run_all_checks,
    get_llm_provider_status,
    check_data_availability,
    check_ml_models,
)

app = typer.Typer()


@app.command()
def all():
    """Show complete system status."""
    from rich.table import Table
    from rich import box
    import shutil

    # Get terminal width
    terminal_width = shutil.get_terminal_size().columns
    table_width = min(terminal_width - 4, 100)  # Max 100 chars, leave 4 for margins

    checks = run_all_checks()
    provider_status = get_llm_provider_status()

    # Calculate summary
    total_checks = len(checks) + len(provider_status)
    passed_checks = sum(1 for success, _ in checks.values() if success)
    passed_providers = sum(1 for success, _ in provider_status.values() if success)
    total_passed = passed_checks + passed_providers

    # Show header with summary
    console.print()
    console.print(
        f"[bold cyan]System Status[/bold cyan] - {total_passed}/{total_checks} components operational"
    )
    console.print()

    # Core systems table
    core_table = Table(
        title="Core Systems",
        box=box.ROUNDED,
        show_header=True,
        width=table_width,
        title_style="bold white",
    )
    core_table.add_column("Component", style="cyan", width=15)
    core_table.add_column("Status", style="white", width=8)
    core_table.add_column("Details", style="white", width=table_width - 28)

    for component, (success, details) in checks.items():
        status_icon = "✅" if success else "❌"
        core_table.add_row(component, status_icon, details)

    console.print(core_table)
    console.print()

    # AI Providers table (same width and style as core systems)
    provider_table = Table(
        title="AI Providers",
        box=box.ROUNDED,
        show_header=True,
        width=table_width,
        title_style="bold white",
    )
    provider_table.add_column("Provider", style="cyan", width=15)
    provider_table.add_column("Status", style="white", width=8)
    provider_table.add_column("Details", style="white", width=table_width - 28)

    for provider, (success, details) in provider_status.items():
        status_icon = "✅" if success else "❌"
        provider_table.add_row(provider, status_icon, details)

    console.print(provider_table)
    console.print()


@app.command()
def providers():
    """Show LLM provider status."""
    print_header("LLM Provider Status", "OpenAI, Anthropic, Google")

    provider_status = get_llm_provider_status()

    data = []
    for provider, (success, details) in provider_status.items():
        data.append(
            {
                "component": provider,
                "status": "✅" if success else "❌",
                "details": details,
            }
        )

    table = create_status_table("AI Providers", data)
    console.print(table)

    configured = sum(1 for success, _ in provider_status.values() if success)
    console.print(f"\n[bold]Configured:[/bold] {configured}/3 providers\n")


@app.command()
def data():
    """Show data availability status."""
    print_header("Data Status", "Historical market data availability")

    success, details = check_data_availability()

    console.print(
        f"\n[bold]Status:[/bold] {'✅ Available' if success else '❌ Not Available'}"
    )
    console.print(f"[bold]Details:[/bold] {details}\n")


@app.command()
def models():
    """Show ML models status."""
    print_header("ML Models Status", "Trained machine learning models")

    success, details = check_ml_models()

    console.print(
        f"\n[bold]Status:[/bold] {'✅ Available' if success else '❌ Not Available'}"
    )
    console.print(f"[bold]Details:[/bold] {details}\n")


@app.command()
def quick():
    """Quick status check (critical systems only)."""
    from proratio_cli.utils.checks import (
        check_database,
        check_environment,
        check_freqtrade,
    )

    checks = {
        "Environment": check_environment(),
        "Database": check_database(),
        "Freqtrade": check_freqtrade(),
    }

    for component, (success, details) in checks.items():
        status = "✅" if success else "❌"
        console.print(f"{status} [cyan]{component}[/cyan]: {details}")
