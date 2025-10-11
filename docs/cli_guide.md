# Proratio CLI Guide

**Version**: 0.7.0
**Last Updated**: October 11, 2025

The Proratio CLI provides a beautiful, user-friendly command-line interface for managing your AI-driven cryptocurrency trading system.

## =€ Quick Start

```bash
# Show system status on startup
./proratio

# Or use with uv
uv run python proratio

# Get help
./proratio --help
```

## =Ë Command Overview

### Status Commands (`proratio status`)

Check system health and component status.

```bash
# Complete system status
proratio status all

# Quick check (critical systems only)
proratio status quick

# LLM provider status
proratio status providers

# Data availability
proratio status data

# ML models status
proratio status models
```

### Strategy Commands (`proratio strategy`)

Manage and test trading strategies.

```bash
# List all available strategies
proratio strategy list

# Show strategy source code
proratio strategy show AIEnhancedStrategy

# Validate strategy configuration
proratio strategy validate AIEnhancedStrategy

# Run backtest
proratio strategy backtest AIEnhancedStrategy --timeframe 4h --days 90
```

### Configuration Commands (`proratio config`)

View and modify trading configuration.

```bash
# Show complete configuration
proratio config show

# Show specific section
proratio config show risk

# Set configuration value
proratio config set risk.max_loss_per_trade_pct 0.02

# Validate configuration
proratio config validate
```

### Data Commands (`proratio data`)

Manage historical market data.

```bash
# Download historical data
proratio data download --pairs BTC/USDT,ETH/USDT --timeframes 1h,4h --days 180

# Show data status
proratio data status
```

### Trading Commands (`proratio trade`)

Control trading operations.

```bash
# Start paper trading (dry-run)
proratio trade start --strategy AIEnhancedStrategy

# Start live trading (  real money!)
proratio trade start --strategy AIEnhancedStrategy --live

# Stop trading
proratio trade stop

# Monitor trades (launches dashboard)
proratio trade monitor
```

### Help Commands (`proratio help`)

Interactive help and guides.

```bash
# Show help menu
proratio help

# Quick start guide
proratio help quickstart

# All commands
proratio help commands

# Configuration guide
proratio help config

# Machine learning guide
proratio help ml
```

## <¨ Features

### Beautiful Output

The CLI uses Rich for beautiful terminal output:
-  Color-coded status indicators
- =Ê Formatted tables
- <3 Tree menus for navigation
- ó Progress bars for long operations
- =» Syntax highlighting for code

### Auto-completion

Install shell completion for faster command entry:

```bash
# Bash
proratio --install-completion bash

# Zsh
proratio --install-completion zsh

# Fish
proratio --install-completion fish
```

### Startup Status

Running `proratio` without arguments shows:
-  Core systems status (Database, Redis, Freqtrade)
- > LLM provider configuration
- =¾ Data availability
- =È ML models status
- ™ Configuration validation

## =Ö Usage Examples

### Example 1: First-Time Setup

```bash
# 1. Check system status
proratio

# 2. Download historical data
proratio data download --pairs BTC/USDT --days 180

# 3. List strategies
proratio strategy list

# 4. Validate strategy
proratio strategy validate AIEnhancedStrategy

# 5. Run backtest
proratio strategy backtest AIEnhancedStrategy --days 90

# 6. Start paper trading
proratio trade start
```

### Example 2: Daily Workflow

```bash
# Morning: Check system status
proratio status quick

# Check LLM providers
proratio status providers

# Review strategy performance
proratio strategy list

# Adjust configuration if needed
proratio config set risk.max_loss_per_trade_pct 0.015

# Start trading
proratio trade start --strategy AIEnhancedStrategy
```

### Example 3: Machine Learning Workflow

```bash
# Check ML models
proratio status models

# Train new LSTM model (using script)
python scripts/train_lstm_model.py --pair BTC/USDT

# Train ensemble model
python scripts/example_ensemble_usage.py

# Backtest ML-enhanced strategy
proratio strategy backtest FreqAIStrategy --days 90
```

## ™ Configuration

### Environment Variables

The CLI checks for these environment variables:

```bash
# .env file
DATABASE_URL=postgresql://user:pass@localhost/proratio
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
```

### Trading Configuration

Modify trading parameters via CLI:

```bash
# Risk settings
proratio config set risk.max_loss_per_trade_pct 0.02
proratio config set risk.max_drawdown_pct 0.10

# Position sizing
proratio config set position_sizing.method ai_weighted
proratio config set position_sizing.base_position_pct 0.05

# Validate changes
proratio config validate
```

## = Troubleshooting

### Common Issues

**CLI not found:**
```bash
# Make sure it's executable
chmod +x proratio

# Or use with Python
uv run python proratio
```

**Import errors:**
```bash
# Install dependencies
uv pip install -r requirements.txt

# Specifically install CLI dependencies
uv pip install typer rich shellingham
```

**Database connection issues:**
```bash
# Check PostgreSQL is running
proratio status quick

# Start PostgreSQL
docker-compose up -d postgres
```

**LLM providers not configured:**
```bash
# Check provider status
proratio status providers

# Add API keys to .env file
# Then check again
proratio status providers
```

## <¯ Command Reference

| Command | Description |
|---------|-------------|
| `proratio` | Show startup status |
| `proratio --version` | Show version |
| `proratio --help` | Show help |
| `proratio status all` | Complete system status |
| `proratio status quick` | Quick health check |
| `proratio status providers` | LLM provider status |
| `proratio status data` | Data availability |
| `proratio status models` | ML models status |
| `proratio strategy list` | List strategies |
| `proratio strategy show <name>` | Show strategy code |
| `proratio strategy backtest <name>` | Run backtest |
| `proratio strategy validate <name>` | Validate strategy |
| `proratio config show [section]` | Show configuration |
| `proratio config set <key> <value>` | Set config value |
| `proratio config validate` | Validate config |
| `proratio data download` | Download historical data |
| `proratio data status` | Show data files |
| `proratio trade start` | Start paper trading |
| `proratio trade start --live` | Start live trading |
| `proratio trade stop` | Stop trading |
| `proratio trade monitor` | Monitor trades |
| `proratio help` | Help menu |
| `proratio help quickstart` | Quick start guide |
| `proratio help commands` | All commands |
| `proratio help config` | Config guide |
| `proratio help ml` | ML guide |

## =€ Advanced Usage

### Chaining Commands

```bash
# Download data, validate strategy, and backtest
proratio data download --pairs BTC/USDT --days 180 && \
proratio strategy validate AIEnhancedStrategy && \
proratio strategy backtest AIEnhancedStrategy
```

### Using with Scripts

```bash
# Check if system is ready before running script
if proratio status quick | grep -q ""; then
    python scripts/my_trading_script.py
else
    echo "System not ready"
fi
```

### JSON Output (Future)

```bash
# Export status as JSON (coming soon)
proratio status all --json > status.json
```

## =Ú Related Documentation

- [Main README](../README.md) - Project overview
- [Roadmap](./roadmap.md) - Development plan
- [Trading Config Guide](./trading_config_guide.md) - Configuration details
- [LSTM Implementation](./lstm_implementation.md) - Neural networks
- [Ensemble Implementation](./ensemble_implementation.md) - Ensemble learning
- [FreqAI Guide](./freqai_guide.md) - Machine learning integration

---

**Built with d using Typer and Rich**
