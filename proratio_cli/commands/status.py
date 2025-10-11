"""
Status Commands

Display system status, health checks, and monitoring information.

Author: Proratio Team
Date: 2025-10-11
"""

import typer
from rich.console import Console
from proratio_cli.utils.display import (
    print_header,
    create_status_table,
    print_section_header,
    console
)
from proratio_cli.utils.checks import (
    run_all_checks,
    get_llm_provider_status,
    check_data_availability,
    check_ml_models
)

app = typer.Typer()


@app.command()
def all():
    """Show complete system status."""
    print_header("System Status", "Complete health check")

    checks = run_all_checks()
    provider_status = get_llm_provider_status()

    # Core systems
    status_data = []
    for component, (success, details) in checks.items():
        status_data.append({
            'component': component,
            'status': '✅' if success else '❌',
            'details': details
        })

    table = create_status_table("Core Systems", status_data)
    console.print(table)

    # LLM Providers
    print_section_header("LLM Providers")
    provider_data = []
    for provider, (success, details) in provider_status.items():
        provider_data.append({
            'component': provider,
            'status': '✅' if success else '❌',
            'details': details
        })

    provider_table = create_status_table("AI Providers", provider_data)
    console.print(provider_table)


@app.command()
def providers():
    """Show LLM provider status."""
    print_header("LLM Provider Status", "OpenAI, Anthropic, Google")

    provider_status = get_llm_provider_status()

    data = []
    for provider, (success, details) in provider_status.items():
        data.append({
            'component': provider,
            'status': '✅' if success else '❌',
            'details': details
        })

    table = create_status_table("AI Providers", data)
    console.print(table)

    configured = sum(1 for success, _ in provider_status.values() if success)
    console.print(f"\n[bold]Configured:[/bold] {configured}/3 providers\n")


@app.command()
def data():
    """Show data availability status."""
    print_header("Data Status", "Historical market data availability")

    success, details = check_data_availability()

    console.print(f"\n[bold]Status:[/bold] {'✅ Available' if success else '❌ Not Available'}")
    console.print(f"[bold]Details:[/bold] {details}\n")


@app.command()
def models():
    """Show ML models status."""
    print_header("ML Models Status", "Trained machine learning models")

    success, details = check_ml_models()

    console.print(f"\n[bold]Status:[/bold] {'✅ Available' if success else '❌ Not Available'}")
    console.print(f"[bold]Details:[/bold] {details}\n")


@app.command()
def quick():
    """Quick status check (critical systems only)."""
    from proratio_cli.utils.checks import check_database, check_environment, check_freqtrade

    checks = {
        'Environment': check_environment(),
        'Database': check_database(),
        'Freqtrade': check_freqtrade(),
    }

    for component, (success, details) in checks.items():
        status = '✅' if success else '❌'
        console.print(f"{status} [cyan]{component}[/cyan]: {details}")
