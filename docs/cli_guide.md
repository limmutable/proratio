# Proratio CLI Guide

**Version**: 0.7.0
**Last Updated**: October 11, 2025

The Proratio CLI provides a beautiful, user-friendly command-line interface for managing your AI-driven cryptocurrency trading system.

---

## Quick Start

```bash
# Launch CLI interface
./start.sh cli

# Show help
./start.sh cli --help

# Quick start guide
./start.sh cli help quickstart

# Check system health
./start.sh cli status all
```

---

## Command Overview

### Status Commands (`./start.sh cli status`)

Check system health and component status.

```bash
# Complete system status
./start.sh cli status all

# Quick check (critical systems only)
./start.sh cli status quick

# LLM provider status
./start.sh cli status providers

# Data availability
./start.sh cli status data

# ML models status
./start.sh cli status models
```

### Strategy Commands (`./start.sh cli strategy`)

Manage and test trading strategies.

```bash
# List all available strategies
./start.sh cli strategy list

# Show strategy source code
./start.sh cli strategy show AIEnhancedStrategy

# Validate strategy configuration
./start.sh cli strategy validate AIEnhancedStrategy

# Run backtest
./start.sh cli strategy backtest AIEnhancedStrategy --timeframe 4h --days 90
```

### Configuration Commands (`./start.sh cli config`)

View and modify trading configuration.

```bash
# Show complete configuration
./start.sh cli config show

# Show specific section
./start.sh cli config show risk

# Set configuration value
./start.sh cli config set risk.max_loss_per_trade_pct 0.02

# Validate configuration
./start.sh cli config validate
```

### Data Commands (`./start.sh cli data`)

Manage historical market data.

```bash
# Download historical data
./start.sh cli data download --pairs BTC/USDT,ETH/USDT --timeframes 1h,4h --days 180

# Check data availability
./start.sh cli data status
```

### Trading Commands (`./start.sh cli trade`)

Start and monitor trading operations.

```bash
# Start paper trading (dry-run)
./start.sh cli trade start --strategy AIEnhancedStrategy

# Start live trading (CAUTION: real money!)
./start.sh cli trade start --strategy AIEnhancedStrategy --live

# Stop trading bot
./start.sh cli trade stop

# Monitor trading activity
./start.sh cli trade monitor
```

### Help Commands (`./start.sh cli help`)

Interactive help and guides.

```bash
# Show main help menu
./start.sh cli help

# Quick start guide (5 steps)
./start.sh cli help quickstart

# Show all commands in tree view
./start.sh cli help commands

# Configuration guide
./start.sh cli help config

# Machine learning guide
./start.sh cli help ml
```

---

## Features

### Beautiful Terminal Output

The CLI uses the **Rich** library for stunning terminal output:

- **Color-coded status indicators**: ✅ (success), ❌ (failure), ⚠️ (warning)
- **Formatted tables**: Clean, bordered tables with aligned columns
- **Tree menus**: Hierarchical command navigation
- **Syntax highlighting**: Python code display with line numbers
- **Progress bars**: Visual feedback for long operations
- **Styled panels**: Headers and sections with borders

### System Health Checks

Comprehensive validation of all system components:

| Component | What's Checked |
|-----------|----------------|
| **Environment** | `.env` file, Python version, dependencies |
| **Database** | PostgreSQL container status |
| **Redis** | Redis container status |
| **LLM Providers** | API keys for OpenAI, Anthropic, Google |
| **Data** | Historical data availability |
| **Strategies** | Strategy files and validation |
| **ML Models** | LSTM and ensemble models |
| **Freqtrade** | Installation and configuration |
| **PyTorch** | Deep learning framework |
| **Binance API** | Exchange connectivity |

### Auto-completion

Shell completion for faster command entry:

```bash
# Install completion for your shell
./start.sh cli --install-completion

# Or manually for specific shells
./start.sh cli --install-completion bash   # Bash
./start.sh cli --install-completion zsh    # Zsh
./start.sh cli --install-completion fish   # Fish
```

### Startup Status Display

Running `./start.sh cli` without any command shows system status:

```
╔══════════════════════════════════════════════════════╗
║         🤖 Proratio System Status                    ║
╚══════════════════════════════════════════════════════╝

Environment Status
┌────────────────┬────────┬──────────────────────┐
│ Component      │ Status │ Details              │
├────────────────┼────────┼──────────────────────┤
│ Environment    │ ✅     │ .env configured      │
│ Database       │ ✅     │ PostgreSQL running   │
│ Redis          │ ✅     │ Redis running        │
│ Freqtrade      │ ✅     │ Installed            │
└────────────────┴────────┴──────────────────────┘

LLM Providers
┌───────────┬────────┬──────────────────────┐
│ Provider  │ Status │ Details              │
├───────────┼────────┼──────────────────────┤
│ OpenAI    │ ✅     │ API key configured   │
│ Anthropic │ ✅     │ API key configured   │
│ Google    │ ✅     │ API key configured   │
└───────────┴────────┴──────────────────────┘

Use './start.sh cli help' for command list
```

---

## Usage Examples

### Example 1: First-Time Setup

```bash
# 1. Launch CLI and check system status
./start.sh cli

# 2. View quick start guide
./start.sh cli help quickstart

# 3. Check what's missing
./start.sh cli status all

# 4. Download historical data
./start.sh cli data download

# 5. List available strategies
./start.sh cli strategy list

# 6. Start paper trading
./start.sh cli trade start
```

### Example 2: Strategy Development Workflow

```bash
# 1. List existing strategies
./start.sh cli strategy list

# 2. View a strategy's code
./start.sh cli strategy show TrendFollowingStrategy

# 3. Validate the strategy
./start.sh cli strategy validate TrendFollowingStrategy

# 4. Run a backtest
./start.sh cli strategy backtest TrendFollowingStrategy --timeframe 4h --days 90

# 5. If successful, start paper trading
./start.sh cli trade start --strategy TrendFollowingStrategy
```

### Example 3: Daily Trading Routine

```bash
# 1. Check system health
./start.sh cli status quick

# 2. Verify LLM providers are working
./start.sh cli status providers

# 3. Check data is up-to-date
./start.sh cli data status

# 4. Review current configuration
./start.sh cli config show risk

# 5. Start trading (if not already running)
./start.sh cli trade start

# 6. Monitor trading activity
./start.sh cli trade monitor
```

---

## Configuration

The CLI reads configuration from:

1. **Environment Variables** (`.env` file)
   - API keys (Binance, OpenAI, Anthropic, Google)
   - Database URLs
   - System settings

2. **Trading Configuration** (`proratio_utilities/config/trading_config.json`)
   - Risk parameters
   - Position sizing
   - Strategy settings
   - 60+ trading parameters

3. **Freqtrade Configuration** (`proratio_utilities/config/freqtrade/`)
   - `config_dry.json` - Paper trading
   - `config_live.json` - Live trading

### Environment Variables Reference

```bash
# Exchange API Keys
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key

# AI Provider API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GEMINI_API_KEY=your_gemini_api_key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/proratio

# Trading Mode
TRADING_MODE=dry_run  # or 'live'
```

---

## Troubleshooting

### CLI Won't Start

**Problem**: `./start.sh cli` shows "command not found" or permission denied

**Solutions**:
```bash
# Make start.sh executable
chmod +x start.sh

# Check if file exists
ls -la start.sh

# Try with bash explicitly
bash start.sh cli
```

### Missing Dependencies

**Problem**: "ModuleNotFoundError: No module named 'typer'" or similar

**Solution**:
```bash
# Install CLI dependencies
pip install typer rich shellingham

# Or with uv
uv pip install typer rich shellingham
```

### System Status Shows Failures

**Problem**: `./start.sh cli status all` shows ❌ for components

**Solutions**:

1. **Database not running**:
   ```bash
   docker-compose up -d postgres
   ```

2. **Redis not running**:
   ```bash
   docker-compose up -d redis
   ```

3. **API keys not configured**:
   ```bash
   # Copy template and edit
   cp .env.example .env
   nano .env  # Add your API keys
   ```

4. **Data not downloaded**:
   ```bash
   ./start.sh cli data download
   ```

### Commands Not Working

**Problem**: Command returns an error or doesn't do anything

**Debug Steps**:
```bash
# Check if virtual environment is activated
which python

# Verify imports work
python -c "import typer, rich; print('OK')"

# Run with verbose error output
./start.sh cli --help
```

---

## Command Reference

| Category | Command | Description |
|----------|---------|-------------|
| **Status** | `status all` | Complete system health check |
| | `status quick` | Quick check (critical systems) |
| | `status providers` | LLM provider status |
| | `status data` | Data availability |
| | `status models` | ML models status |
| **Strategy** | `strategy list` | List all strategies |
| | `strategy show NAME` | Show strategy code |
| | `strategy validate NAME` | Validate strategy |
| | `strategy backtest NAME` | Run backtest |
| **Config** | `config show` | Show all configuration |
| | `config show SECTION` | Show config section |
| | `config set KEY VALUE` | Set config value |
| | `config validate` | Validate configuration |
| **Data** | `data download` | Download historical data |
| | `data status` | Check data availability |
| **Trade** | `trade start` | Start trading bot |
| | `trade start --live` | Start live trading |
| | `trade stop` | Stop trading bot |
| | `trade monitor` | Monitor trading activity |
| **Help** | `help` | Main help menu |
| | `help quickstart` | Quick start guide |
| | `help commands` | All commands tree view |
| | `help config` | Configuration guide |
| | `help ml` | ML training guide |

---

## Advanced Usage

### Running Commands Without Interactive Mode

```bash
# Run a single command and exit
./start.sh cli status all

# Chain multiple commands
./start.sh cli status all && ./start.sh cli data status

# Save output to file
./start.sh cli strategy list > strategies.txt
```

### Integration with Scripts

```python
# Python script using CLI commands
import subprocess

# Check system status
result = subprocess.run(['./start.sh', 'cli', 'status', 'quick'],
                       capture_output=True, text=True)
print(result.stdout)

# Start trading if system is healthy
if result.returncode == 0:
    subprocess.run(['./start.sh', 'cli', 'trade', 'start'])
```

### Custom Configuration Paths

The CLI respects these environment variables:

```bash
# Use different config file
export TRADING_CONFIG=/path/to/custom/config.json
./start.sh cli config show

# Use different Freqtrade userdir
export FREQTRADE_USERDIR=/path/to/userdir
./start.sh cli strategy list
```

---

## What's Next?

After mastering the CLI:

1. **Read Strategy Guides**: Learn about the 4 built-in strategies
   - See `docs/strategies/` for detailed guides

2. **Explore ML Models**: Train LSTM and ensemble models
   - `./start.sh cli help ml` for ML guide

3. **Start Paper Trading**: Test strategies with dry-run mode
   - `./start.sh cli trade start`

4. **Monitor Dashboard**: View real-time trading activity
   - `./start.sh trade` (starts full system with dashboard)

5. **Join Community**: Share strategies and insights
   - Check GitHub repository for discussions

---

## Support

For issues or questions:
- **Documentation**: See `docs/` directory
- **GitHub Issues**: Report bugs or request features
- **Logs**: Check `user_data/logs/` for debugging

---

**Happy Trading! 🚀**
