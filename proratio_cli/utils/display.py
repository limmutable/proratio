"""
Rich Display Utilities for Proratio CLI

Provides beautiful terminal output with colors, tables, and progress indicators.

Author: Proratio Team
Date: 2025-10-11
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich.text import Text
from rich import box
from typing import Dict, List, Any, Optional
import time

# Global console instance
console = Console()


def print_header(title: str, subtitle: Optional[str] = None):
    """Print a styled header."""
    text = Text(title, style="bold cyan")
    if subtitle:
        text.append(f"\n{subtitle}", style="dim")

    console.print(Panel(text, border_style="cyan", box=box.DOUBLE))


def print_success(message: str):
    """Print success message."""
    console.print(f"✅ {message}", style="bold green")


def print_error(message: str):
    """Print error message."""
    console.print(f"❌ {message}", style="bold red")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"⚠️  {message}", style="bold yellow")


def print_info(message: str):
    """Print info message."""
    console.print(f"ℹ️  {message}", style="bold blue")


def create_status_table(title: str, data: List[Dict[str, str]]) -> Table:
    """
    Create a status table.

    Args:
        title: Table title
        data: List of dicts with 'component', 'status', 'details' keys

    Returns:
        Rich Table object
    """
    table = Table(title=title, box=box.ROUNDED, show_header=True)
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="white")

    for row in data:
        status_style = (
            "green"
            if row["status"] == "✅"
            else "red"
            if row["status"] == "❌"
            else "yellow"
        )
        table.add_row(
            row["component"],
            Text(row["status"], style=status_style),
            row.get("details", ""),
        )

    return table


def create_config_table(config_data: Dict[str, Any]) -> Table:
    """Create a configuration display table."""
    table = Table(title="Configuration", box=box.ROUNDED)
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    for key, value in config_data.items():
        table.add_row(key, str(value))

    return table


def create_strategy_table(strategies: List[Dict[str, Any]]) -> Table:
    """Create a strategy list table."""
    table = Table(title="Available Strategies", box=box.ROUNDED)
    table.add_column("Strategy", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Sharpe", justify="right", style="yellow")

    for strategy in strategies:
        table.add_row(
            strategy["name"],
            strategy["type"],
            strategy.get("status", "Unknown"),
            f"{strategy.get('sharpe', 0.0):.2f}",
        )

    return table


def print_loading_status(title: str, checks: List[Dict[str, Any]]):
    """
    Print loading status with spinner.

    Args:
        title: Loading title
        checks: List of checks with 'name', 'func', 'args' keys
    """
    console.print(f"\n[bold cyan]{title}[/bold cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for check in checks:
            task = progress.add_task(f"Checking {check['name']}...", total=1)

            # Run the check
            try:
                result = check["func"](*check.get("args", []))
                if result:
                    progress.update(task, description=f"✅ {check['name']}")
                else:
                    progress.update(task, description=f"❌ {check['name']}")
            except Exception as e:
                progress.update(task, description=f"❌ {check['name']} ({str(e)})")

            progress.update(task, completed=1)
            time.sleep(0.1)  # Brief pause for visual effect


def create_tree_menu(title: str, menu_items: Dict[str, List[str]]) -> Tree:
    """
    Create a tree menu structure.

    Args:
        title: Tree title
        menu_items: Dict of category -> list of items

    Returns:
        Rich Tree object
    """
    tree = Tree(f"[bold cyan]{title}[/bold cyan]")

    for category, items in menu_items.items():
        branch = tree.add(f"[bold yellow]{category}[/bold yellow]")
        for item in items:
            branch.add(f"[green]{item}[/green]")

    return tree


def print_separator(char: str = "─", length: int = 80):
    """Print a separator line."""
    console.print(char * length, style="dim")


def print_key_value(
    key: str, value: str, key_style: str = "cyan", value_style: str = "white"
):
    """Print key-value pair."""
    console.print(
        f"{Text(key + ':', style=key_style)} {Text(str(value), style=value_style)}"
    )


def print_section_header(title: str):
    """Print a section header."""
    console.print(f"\n[bold underline cyan]{title}[/bold underline cyan]\n")


def print_command_example(command: str, description: str):
    """Print command example with description."""
    console.print(f"  [bold green]${command}[/bold green]")
    console.print(f"    {description}\n", style="dim")


def show_progress_bar(total: int, description: str = "Processing"):
    """
    Create and return a progress bar.

    Usage:
        with show_progress_bar(100, "Downloading") as progress:
            task = progress.add_task(description, total=100)
            for i in range(100):
                progress.update(task, advance=1)
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )
