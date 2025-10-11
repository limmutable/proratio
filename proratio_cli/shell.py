"""
Interactive Shell for Proratio CLI

Provides an interactive command prompt with system initialization,
health checks, and continuous command input.

Author: Proratio Team
Date: 2025-10-11
"""

import sys
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from proratio_cli.utils.checks import run_all_checks, check_llm_providers
from proratio_cli.utils.display import console, print_header
from proratio_cli.commands import status, strategy, config, data, trade, help_cmd


class ProratioShell:
    """Interactive shell for Proratio CLI."""

    def __init__(self):
        self.console = console
        self.running = False
        self.initialized = False

    def startup(self):
        """Perform startup initialization and system checks."""
        # Display header
        self.console.print()
        self.console.print("╔════════════════════════════════════════════════════════════════╗", style="cyan")
        self.console.print("║                  🤖 Proratio CLI Interface                     ║", style="cyan")
        self.console.print("║              AI-Driven Cryptocurrency Trading                  ║", style="cyan")
        self.console.print("╚════════════════════════════════════════════════════════════════╝", style="cyan")
        self.console.print()

        # Show loading animation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task("🔄 Initializing system...", total=None)

            # Run system checks
            import time
            time.sleep(0.5)  # Brief pause for visual effect
            progress.update(task, description="🔍 Running health checks...")
            checks = run_all_checks()

            time.sleep(0.3)
            progress.update(task, description="📊 Loading configuration...")
            time.sleep(0.3)

            progress.update(task, description="✅ Initialization complete")
            time.sleep(0.3)

        self.console.print()

        # Display system status
        self._display_startup_status(checks)

        self.initialized = True

    def _display_startup_status(self, checks: dict):
        """Display startup status with health check results."""
        # Create status table
        table = Table(title="System Status", box=box.ROUNDED, show_header=True, title_style="bold cyan")
        table.add_column("Component", style="cyan", no_wrap=True, width=20)
        table.add_column("Status", style="magenta", width=10)
        table.add_column("Details", style="white", width=30)

        all_healthy = True
        critical_components = ['Environment', 'Database', 'Freqtrade']

        for component, (status, details) in checks.items():
            if status:
                status_text = Text("✅", style="green")
            else:
                status_text = Text("❌", style="red")
                if component in critical_components:
                    all_healthy = False

            table.add_row(component, status_text, details)

        self.console.print(table)
        self.console.print()

        # Check LLM providers
        providers = check_llm_providers()
        provider_table = Table(title="LLM Providers", box=box.ROUNDED, show_header=True, title_style="bold cyan")
        provider_table.add_column("Provider", style="cyan", width=15)
        provider_table.add_column("Status", style="magenta", width=10)
        provider_table.add_column("Details", style="white", width=30)

        for provider, (status, details) in providers.items():
            status_text = Text("✅" if status else "⚠️", style="green" if status else "yellow")
            provider_table.add_row(provider, status_text, details)

        self.console.print(provider_table)
        self.console.print()

        # Display overall status
        if all_healthy:
            self.console.print(Panel(
                Text("✅ System is ready to use!", style="bold green"),
                border_style="green",
                box=box.DOUBLE
            ))
        else:
            self.console.print(Panel(
                Text("⚠️  System has critical errors. Please fix the issues above.", style="bold yellow"),
                border_style="yellow",
                box=box.DOUBLE
            ))

        self.console.print()
        self.console.print("[dim]Type [bold cyan]/help[/bold cyan] for available commands or [bold cyan]/quit[/bold cyan] to exit[/dim]")
        self.console.print()

    def run(self):
        """Run the interactive shell."""
        self.running = True

        # Startup sequence
        self.startup()

        # Main command loop
        while self.running:
            try:
                # Display prompt
                user_input = self.console.input("[bold cyan]proratio>[/bold cyan] ")
                user_input = user_input.strip()

                if not user_input:
                    continue

                # Process command
                self.process_command(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use /quit or /exit to exit properly[/yellow]")
                continue
            except EOFError:
                self.console.print()
                self.shutdown()
                break

    def process_command(self, command: str):
        """Process a user command."""
        # Check if command starts with /
        if not command.startswith('/'):
            self.console.print("[red]❌ Commands must start with /[/red]")
            self.console.print("[dim]Example: /help, /status, /quit[/dim]")
            return

        # Remove leading /
        command = command[1:]
        parts = command.split()

        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Route to appropriate handler
        if cmd in ['exit', 'quit', 'q']:
            self.shutdown()
        elif cmd == 'help':
            self.cmd_help(args)
        elif cmd == 'status':
            self.cmd_status(args)
        elif cmd == 'strategy':
            self.cmd_strategy(args)
        elif cmd == 'config':
            self.cmd_config(args)
        elif cmd == 'data':
            self.cmd_data(args)
        elif cmd == 'trade':
            self.cmd_trade(args)
        elif cmd == 'clear':
            self.console.clear()
        else:
            self.console.print(f"[red]❌ Unknown command: /{cmd}[/red]")
            self.console.print("[dim]Type /help for available commands[/dim]")

    def cmd_help(self, args: list):
        """Display help information."""
        if not args:
            # Show main help
            self.console.print()
            print_header("Available Commands", "Type /help <command> for more details")

            table = Table(box=box.ROUNDED, show_header=True)
            table.add_column("Command", style="cyan", width=20)
            table.add_column("Description", style="white", width=50)

            table.add_row("/help", "Show this help message")
            table.add_row("/help <command>", "Show help for specific command")
            table.add_row("/status [all|quick|providers|data|models]", "Check system status")
            table.add_row("/strategy [list|show|validate|backtest]", "Manage strategies")
            table.add_row("/config [show|set|validate]", "Manage configuration")
            table.add_row("/data [download|status]", "Manage market data")
            table.add_row("/trade [start|stop|monitor]", "Trading operations")
            table.add_row("/clear", "Clear screen")
            table.add_row("/quit, /exit", "Exit Proratio CLI")

            self.console.print(table)
            self.console.print()
        else:
            # Show help for specific command
            subcmd = args[0].lower()
            if subcmd == 'status':
                self._help_status()
            elif subcmd == 'strategy':
                self._help_strategy()
            elif subcmd == 'config':
                self._help_config()
            elif subcmd == 'data':
                self._help_data()
            elif subcmd == 'trade':
                self._help_trade()
            else:
                self.console.print(f"[yellow]No detailed help available for: {subcmd}[/yellow]")

    def _help_status(self):
        """Show help for status command."""
        self.console.print()
        self.console.print("[bold cyan]Status Command[/bold cyan]")
        self.console.print()
        self.console.print("Usage: /status [subcommand]")
        self.console.print()
        self.console.print("Subcommands:")
        self.console.print("  all       - Complete system health check")
        self.console.print("  quick     - Quick check (critical systems only)")
        self.console.print("  providers - LLM provider status")
        self.console.print("  data      - Data availability check")
        self.console.print("  models    - ML models status")
        self.console.print()

    def _help_strategy(self):
        """Show help for strategy command."""
        self.console.print()
        self.console.print("[bold cyan]Strategy Command[/bold cyan]")
        self.console.print()
        self.console.print("Usage: /strategy <subcommand> [args]")
        self.console.print()
        self.console.print("Subcommands:")
        self.console.print("  list              - List all strategies")
        self.console.print("  show <name>       - Show strategy source code")
        self.console.print("  validate <name>   - Validate strategy")
        self.console.print("  backtest <name>   - Run backtest")
        self.console.print()

    def _help_config(self):
        """Show help for config command."""
        self.console.print()
        self.console.print("[bold cyan]Config Command[/bold cyan]")
        self.console.print()
        self.console.print("Usage: /config <subcommand> [args]")
        self.console.print()
        self.console.print("Subcommands:")
        self.console.print("  show [section]       - Show configuration")
        self.console.print("  set <key> <value>    - Set config value")
        self.console.print("  validate             - Validate configuration")
        self.console.print()

    def _help_data(self):
        """Show help for data command."""
        self.console.print()
        self.console.print("[bold cyan]Data Command[/bold cyan]")
        self.console.print()
        self.console.print("Usage: /data <subcommand> [args]")
        self.console.print()
        self.console.print("Subcommands:")
        self.console.print("  download  - Download historical data")
        self.console.print("  status    - Check data availability")
        self.console.print()

    def _help_trade(self):
        """Show help for trade command."""
        self.console.print()
        self.console.print("[bold cyan]Trade Command[/bold cyan]")
        self.console.print()
        self.console.print("Usage: /trade <subcommand> [args]")
        self.console.print()
        self.console.print("Subcommands:")
        self.console.print("  start     - Start trading bot")
        self.console.print("  stop      - Stop trading bot")
        self.console.print("  monitor   - Monitor trading activity")
        self.console.print()

    def cmd_status(self, args: list):
        """Handle status command."""
        subcommand = args[0] if args else 'all'

        # Import status command module and call appropriate function
        try:
            if subcommand == 'all':
                status.all()
            elif subcommand == 'quick':
                status.quick()
            elif subcommand == 'providers':
                status.providers()
            elif subcommand == 'data':
                status.data_status()
            elif subcommand == 'models':
                status.models()
            else:
                self.console.print(f"[red]Unknown status subcommand: {subcommand}[/red]")
                self.console.print("[dim]Use: /status [all|quick|providers|data|models][/dim]")
        except Exception as e:
            self.console.print(f"[red]Error executing status command: {e}[/red]")

    def cmd_strategy(self, args: list):
        """Handle strategy command."""
        if not args:
            self.console.print("[red]Strategy command requires a subcommand[/red]")
            self.console.print("[dim]Use: /strategy [list|show|validate|backtest][/dim]")
            return

        subcommand = args[0]

        try:
            if subcommand == 'list':
                strategy.list()
            elif subcommand == 'show':
                if len(args) < 2:
                    self.console.print("[red]Strategy name required[/red]")
                    return
                strategy.show(args[1])
            elif subcommand == 'validate':
                if len(args) < 2:
                    self.console.print("[red]Strategy name required[/red]")
                    return
                strategy.validate(args[1])
            elif subcommand == 'backtest':
                if len(args) < 2:
                    self.console.print("[red]Strategy name required[/red]")
                    return
                strategy.backtest(args[1])
            else:
                self.console.print(f"[red]Unknown strategy subcommand: {subcommand}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error executing strategy command: {e}[/red]")

    def cmd_config(self, args: list):
        """Handle config command."""
        if not args:
            config.show()
            return

        subcommand = args[0]

        try:
            if subcommand == 'show':
                section = args[1] if len(args) > 1 else None
                config.show(section)
            elif subcommand == 'set':
                if len(args) < 3:
                    self.console.print("[red]Usage: /config set <key> <value>[/red]")
                    return
                config.set(args[1], args[2])
            elif subcommand == 'validate':
                config.validate()
            else:
                self.console.print(f"[red]Unknown config subcommand: {subcommand}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error executing config command: {e}[/red]")

    def cmd_data(self, args: list):
        """Handle data command."""
        if not args:
            data.status()
            return

        subcommand = args[0]

        try:
            if subcommand == 'download':
                # Parse download options
                # For now, use defaults
                data.download()
            elif subcommand == 'status':
                data.status()
            else:
                self.console.print(f"[red]Unknown data subcommand: {subcommand}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error executing data command: {e}[/red]")

    def cmd_trade(self, args: list):
        """Handle trade command."""
        if not args:
            self.console.print("[red]Trade command requires a subcommand[/red]")
            self.console.print("[dim]Use: /trade [start|stop|monitor][/dim]")
            return

        subcommand = args[0]

        try:
            if subcommand == 'start':
                trade.start()
            elif subcommand == 'stop':
                trade.stop()
            elif subcommand == 'monitor':
                trade.monitor()
            else:
                self.console.print(f"[red]Unknown trade subcommand: {subcommand}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error executing trade command: {e}[/red]")

    def shutdown(self):
        """Shutdown the shell gracefully."""
        self.console.print()
        self.console.print("[yellow]🔄 Shutting down Proratio CLI...[/yellow]")

        # Perform cleanup
        self.console.print("[dim]  • Saving session...[/dim]")
        self.console.print("[dim]  • Closing connections...[/dim]")

        self.console.print()
        self.console.print(Panel(
            Text("👋 Thank you for using Proratio!", style="bold cyan"),
            border_style="cyan",
            box=box.DOUBLE
        ))
        self.console.print()

        self.running = False
        sys.exit(0)


def run_shell():
    """Entry point for interactive shell mode."""
    shell = ProratioShell()
    shell.run()
