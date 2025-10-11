# Proratio CLI Guide

**Version**: 0.8.0
**Last Updated**: October 11, 2025

The Proratio CLI provides a beautiful, interactive command-line interface for managing your AI-driven cryptocurrency trading system.

---

## Quick Start

### Interactive Shell Mode (Default)

```bash
# Launch interactive CLI shell
./start.sh cli
```

This will:
1. **Initialize system** - Check dependencies and environment
2. **Run health checks** - Verify database, Redis, APIs, data
3. **Display status** - Show system health with colored tables
4. **Launch prompt** - Interactive `proratio>` prompt awaits your commands

**Example Session:**
```
$ ./start.sh cli

╔════════════════════════════════════════════════════════════════╗
║                  🤖 Proratio CLI Interface                     ║
║              AI-Driven Cryptocurrency Trading                  ║
╚════════════════════════════════════════════════════════════════╝

🔄 Initializing system...
🔍 Running health checks...
✅ Initialization complete

[System Status Table showing all components]
[LLM Providers Table showing API status]

✅ System is ready to use!

Type /help for available commands or /quit to exit

proratio> /help
[Shows command list]

proratio> /strategy list
[Shows all strategies]

proratio> /quit
👋 Thank you for using Proratio!
```

---

## Command Reference

All commands in the interactive shell must start with `/` (forward slash).

### Core Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/help <command>` | Show detailed help for specific command |
| `/clear` | Clear the terminal screen |
| `/quit` or `/exit` | Exit the CLI (with graceful shutdown) |

### Status Commands

Check system health and component status.

```
proratio> /status              # Same as /status all
proratio> /status all          # Complete system health check
proratio> /status quick        # Quick check (critical systems only)
proratio> /status providers    # LLM provider status
proratio> /status data         # Data availability
proratio> /status models       # ML models status
```

### Strategy Commands

Manage and test trading strategies.

```
proratio> /strategy list                      # List all strategies
proratio> /strategy show AIEnhancedStrategy   # Show strategy code
proratio> /strategy validate <name>           # Validate strategy
proratio> /strategy backtest <name>           # Run backtest
```

### Configuration Commands

View and modify trading configuration.

```
proratio> /config                     # Show all configuration
proratio> /config show                # Same as above
proratio> /config show risk           # Show specific section
proratio> /config set <key> <value>   # Set configuration value
proratio> /config validate            # Validate configuration
```

### Data Commands

Manage historical market data.

```
proratio> /data download      # Download historical data
proratio> /data status        # Check data availability
```

### Trading Commands

Start and monitor trading operations.

```
proratio> /trade start       # Start paper trading (dry-run)
proratio> /trade stop        # Stop trading bot
proratio> /trade monitor     # Monitor trading activity
```

---

## Features

### 1. Beautiful Terminal Output

- **Color-coded status**: ✅ (success), ❌ (failure), ⚠️ (warning)
- **Formatted tables**: Clean, bordered tables with aligned columns
- **Syntax highlighting**: Python code with line numbers
- **Progress indicators**: Spinners and progress bars

### 2. Startup Health Checks

On launch, the CLI automatically checks:
- Environment variables
- Docker services (PostgreSQL, Redis)
- LLM provider API keys
- Data availability
- Strategies
- ML models
- Freqtrade installation

### 3. Interactive Prompt

- Command history (use ↑/↓ arrows)
- Graceful error handling
- Ctrl+C doesn't crash

---

## Usage Examples

### Example 1: First-Time Setup

```
$ ./start.sh cli

proratio> /data download
proratio> /strategy list
proratio> /strategy backtest AIEnhancedStrategy
proratio> /quit
```

### Example 2: Daily Check

```
$ ./start.sh cli

proratio> /status quick
proratio> /config show risk
proratio> /trade start
proratio> /quit
```

---

## Troubleshooting

### CLI Won't Start
```bash
# Recreate virtual environment
rm -rf .venv
./start.sh cli
```

### System Status Shows Errors
```
proratio> /help status
proratio> /status all  # See what's failing
proratio> /data download  # If data missing
```

---

**Happy Trading! 🚀**
