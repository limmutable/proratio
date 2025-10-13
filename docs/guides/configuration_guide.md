# Complete Configuration Guide

**Comprehensive guide to configuring Proratio trading system**

## Table of Contents

1. [Overview](#overview)
2. [Configuration Architecture](#configuration-architecture)
3. [Environment Configuration (.env)](#environment-configuration-env)
4. [Trading Configuration (trading_config)](#trading-configuration-trading_config)
5. [Configuration Sections](#configuration-sections)
6. [Common Scenarios](#common-scenarios)
7. [Migration Guide](#migration-guide)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Proratio uses a **two-layer configuration system**:

1. **Environment Configuration (`.env`)** - Secrets and environment-specific settings
2. **Trading Configuration (`trading_config.py`/`.json`)** - Trading parameters and strategy settings

### Why Two Layers?

**Clear separation of concerns:**
- **Secrets** (API keys, passwords) → `.env` (never commit to git)
- **Trading logic** (risk limits, strategy params) → `trading_config.py` (version controlled)

This ensures:
- ✅ Secrets stay secure
- ✅ Trading parameters are versioned and tracked
- ✅ Easy to share configurations without exposing keys
- ✅ Clear distinction between "what to hide" vs "what to version"

---

## Configuration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Configuration Layers                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ .env (secrets + environment flags)                   │   │
│  │ Location: /proratio/.env                             │   │
│  │                                                        │   │
│  │ - Exchange API keys (Binance)                        │   │
│  │ - AI API keys (OpenAI, Anthropic, Google)            │   │
│  │ - Database URLs (PostgreSQL, Redis)                  │   │
│  │ - Telegram credentials (optional)                    │   │
│  │ - Environment flags (TRADING_MODE, DEBUG)            │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ▲                                   │
│                          │ Loaded by                         │
│  ┌──────────────────────┴───────────────────────────────┐   │
│  │ settings.py                                          │   │
│  │ → get_settings() returns Settings object            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ trading_config.py (code defaults)                    │   │
│  │ Location: /proratio_utilities/config/               │   │
│  │                                                        │   │
│  │ - Risk management (limits, thresholds)               │   │
│  │ - Position sizing (methods, multipliers)             │   │
│  │ - Strategy parameters (indicators, timeframes)       │   │
│  │ - AI configuration (weights, consensus)              │   │
│  │ - Execution settings (order types, balance)          │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ▲                                   │
│                          │ Optional override                 │
│  ┌──────────────────────┴───────────────────────────────┐   │
│  │ trading_config.json (runtime overrides)              │   │
│  │ Location: /proratio_utilities/config/               │   │
│  │                                                        │   │
│  │ - Custom risk limits per environment                 │   │
│  │ - Different strategies per deployment                │   │
│  │ - A/B testing configurations                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ▲                                   │
│                          │ Loaded by                         │
│  ┌──────────────────────┴───────────────────────────────┐   │
│  │ get_trading_config()                                 │   │
│  │ → Returns TradingConfig object                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘

Priority Order:
1. trading_config.json (if exists) - highest priority
2. trading_config.py code defaults
3. .env TRADING_MODE override (safety - always respected)
```

---

## Environment Configuration (.env)

### Setup

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your values:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **NEVER commit `.env` to git!**
   - Already in `.gitignore`
   - Contains sensitive credentials

### Environment Variables Reference

#### Exchange API Keys

```bash
# Binance API credentials
# Get from: https://www.binance.com/en/my/settings/api-management
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# Start with testnet for safety
BINANCE_TESTNET=true
```

**Important:**
- Create API keys with **read and trade** permissions only
- **NEVER** enable withdrawal permissions
- Use IP whitelist if possible
- Start with testnet: https://testnet.binance.vision/

#### AI/LLM API Keys

```bash
# OpenAI (ChatGPT-4)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-api-key-here

# Anthropic (Claude)
# Get from: https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# Google (Gemini)
# Get from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your-google-api-key-here
```

**Note:** You need at least one AI provider. System will work with any combination.

#### Database & Infrastructure

```bash
# PostgreSQL - For time-series data storage
DATABASE_URL=postgresql://proratio:proratio_password@localhost:5432/proratio

# Redis - For caching and state management
REDIS_URL=redis://localhost:6379/0
```

**Default:** Works with `docker-compose up -d` infrastructure

#### Telegram Alerts (Optional)

```bash
# Get bot token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Leave empty to disable notifications
```

**Setup Telegram Bot:**
1. Message @BotFather on Telegram
2. Use `/newbot` command
3. Get your bot token
4. Get your chat ID from @userinfobot

#### Environment Settings

```bash
# Trading mode: dry_run (paper) or live (real money)
# ⚠️ CRITICAL: Always start with dry_run!
TRADING_MODE=dry_run

# Data refresh interval (seconds)
# How often to fetch new market data
DATA_REFRESH_INTERVAL=300
```

**Important:** `TRADING_MODE` in `.env` overrides all other settings for safety.

#### Development & Debugging

```bash
# Enable debug mode
DEBUG=false

# Logging level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

### Using Environment Settings in Code

```python
from proratio_utilities.config.settings import get_settings

settings = get_settings()

# Access API keys
api_key = settings.binance_api_key
openai_key = settings.openai_api_key

# Check environment flags
is_testnet = settings.binance_testnet
mode = settings.trading_mode  # dry_run or live

# Database URLs
db_url = settings.database_url
```

---

## Trading Configuration (trading_config)

### Three Ways to Configure

**Option 1: Use Code Defaults** (Recommended for beginners)
```python
from proratio_utilities.config.trading_config import get_trading_config

config = get_trading_config()  # Uses defaults from trading_config.py
config.print_summary()
```

**Option 2: Create JSON Config File** (Recommended for production)
```bash
# Edit: proratio_utilities/config/trading_config.json
# System automatically loads this file if it exists
```

**Option 3: Modify Code Defaults** (For developers)
```python
# Edit: proratio_utilities/config/trading_config.py
# Change default values in dataclass definitions
```

### Quick Start

**View Current Configuration:**
```python
from proratio_utilities.config.trading_config import get_trading_config

config = get_trading_config()
config.print_summary()
```

**Load from Specific File:**
```python
from pathlib import Path
from proratio_utilities.config.trading_config import TradingConfig

config = TradingConfig.load_from_file(Path('my_custom_config.json'))
```

**Modify and Save:**
```python
config = get_trading_config()

# Adjust parameters
config.risk.max_loss_per_trade_pct = 1.5
config.ai.min_confidence = 0.70

# Validate
errors = config.validate()
if errors:
    print("Errors:", errors)
else:
    # Save
    config.save_to_file(Path('proratio_utilities/config/my_config.json'))
```

---

## Configuration Sections

### 1. Risk Management (`config.risk`)

Controls all risk limits and safety mechanisms.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_loss_per_trade_pct` | 2.0 | Maximum loss per trade (% of portfolio) |
| `max_position_size_pct` | 10.0 | Maximum position size (% of portfolio) |
| `min_position_size_pct` | 1.0 | Minimum position size (% of portfolio) |
| `max_total_drawdown_pct` | 10.0 | **Emergency stop** - halt trading at this drawdown |
| `warning_drawdown_pct` | 7.0 | Warning threshold (approaching danger zone) |
| `max_concurrent_positions` | 3 | Maximum number of open positions |
| `max_positions_per_pair` | 1 | Max positions per trading pair |
| `max_leverage` | 1.0 | Leverage (1.0 = spot only, >1.0 = futures) |

**Example:**
```python
# Conservative risk profile
config.risk.max_loss_per_trade_pct = 1.0
config.risk.max_total_drawdown_pct = 5.0
config.risk.max_concurrent_positions = 2

# Aggressive risk profile
config.risk.max_loss_per_trade_pct = 3.0
config.risk.max_concurrent_positions = 5
```

---

### 2. Position Sizing (`config.position_sizing`)

Controls how position sizes are calculated.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `method` | 'ai_weighted' | Sizing method (see below) |
| `base_risk_pct` | 2.0 | Base risk percentage |
| `ai_confidence_min` | 0.60 | Minimum AI confidence to trade (60%) |
| `ai_confidence_multiplier_min` | 0.8 | Stake multiplier at 60% confidence |
| `ai_confidence_multiplier_max` | 1.2 | Stake multiplier at 100% confidence |
| `atr_period` | 14 | ATR calculation period |
| `atr_multiplier` | 2.0 | ATR multiplier for stop-loss |
| `kelly_fraction` | 0.5 | Kelly fraction (0.5 = half-Kelly) |

**Position Sizing Methods:**

1. **`fixed_fraction`**: Always use same % of portfolio
2. **`risk_based`**: Size based on stop-loss distance (recommended)
3. **`kelly`**: Kelly Criterion (requires win rate history)
4. **`ai_weighted`**: Risk-based + AI confidence multiplier (recommended for AI strategies)
5. **`atr_based`**: ATR-based volatility adjustment

**Example:**
```python
# Lower AI threshold for more trades
config.position_sizing.ai_confidence_min = 0.55

# More aggressive with high confidence
config.position_sizing.ai_confidence_multiplier_max = 1.5

# Use pure risk-based (no AI adjustment)
config.position_sizing.method = 'risk_based'
```

---

### 3. Strategy Parameters (`config.strategy`)

Controls technical indicators and strategy behavior.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `strategy_name` | 'AIEnhancedStrategy' | Strategy class name |
| `timeframe` | '1h' | Trading timeframe (1h, 4h, 1d) |
| `pairs` | ['BTC/USDT', 'ETH/USDT'] | Trading pairs |
| `ema_fast_period` | 20 | Fast EMA period |
| `ema_slow_period` | 50 | Slow EMA period |
| `rsi_period` | 14 | RSI calculation period |
| `rsi_buy_threshold` | 30 | RSI buy threshold |
| `rsi_sell_threshold` | 70 | RSI sell threshold |
| `atr_period` | 14 | ATR period |
| `adx_period` | 14 | ADX period |
| `adx_trend_threshold` | 20.0 | ADX threshold for trending |
| `roi_levels` | {0: 0.15, 60: 0.08, 120: 0.04} | Take-profit levels |
| `stoploss_pct` | -0.04 | Stop-loss percentage (4% loss) |
| `trailing_stop_enabled` | true | Enable trailing stop |
| `trailing_stop_positive` | 0.015 | Activate at 1.5% profit |
| `trailing_stop_positive_offset` | 0.025 | Trail after 2.5% profit |

**Example:**
```python
# Trade more pairs
config.strategy.pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT']

# Faster timeframe
config.strategy.timeframe = '15m'
config.strategy.ema_fast_period = 10
config.strategy.ema_slow_period = 30

# Tighter stop-loss
config.strategy.stoploss_pct = -0.03  # 3%

# Aggressive take-profit
config.strategy.roi_levels = {
    "0": 0.20,   # 20% immediately
    "30": 0.10,  # 10% after 30 min
    "60": 0.05   # 5% after 60 min
}
```

---

### 4. AI Configuration (`config.ai`)

Controls AI signal generation and consensus.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `chatgpt_weight` | 0.40 | ChatGPT weight (technical analysis) |
| `claude_weight` | 0.35 | Claude weight (risk assessment) |
| `gemini_weight` | 0.25 | Gemini weight (sentiment) |
| `min_consensus_score` | 0.60 | Minimum weighted consensus |
| `min_confidence` | 0.60 | Minimum AI confidence to trade |
| `require_all_providers` | false | Require all 3 providers |
| `signal_cache_minutes` | 60 | Cache signals for X minutes |
| `lookback_candles` | 50 | Candles to send to AI |
| `chatgpt_model` | null | Override model (auto-detect if null) |
| `claude_model` | null | Override model |
| `gemini_model` | null | Override model |

**Provider Weights:**
- Must sum to 1.0
- Set to 0 to disable a provider
- Dynamic reweighting if provider fails (unless `require_all_providers=true`)

**Example:**
```python
# Equal weights
config.ai.chatgpt_weight = 0.33
config.ai.claude_weight = 0.34
config.ai.gemini_weight = 0.33

# Higher confidence requirement
config.ai.min_confidence = 0.75

# Require all providers (no fallback)
config.ai.require_all_providers = True

# Use specific models
config.ai.chatgpt_model = 'gpt-5-nano-2025-08-07'
config.ai.claude_model = 'claude-sonnet-4-20250514'
config.ai.gemini_model = 'gemini-2.0-flash'
```

---

### 5. Execution Settings (`config.execution`)

Controls order execution and trading mode.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `trading_mode` | 'dry_run' | **'dry_run'** (paper) or **'live'** (real) |
| `exchange` | 'binance' | Exchange name |
| `entry_order_type` | 'limit' | Entry order type (limit/market) |
| `exit_order_type` | 'limit' | Exit order type |
| `stoploss_order_type` | 'market' | Stop-loss order type |
| `stoploss_on_exchange` | false | Place stop-loss on exchange |
| `order_time_in_force` | 'GTC' | Order time-in-force (GTC/IOC) |
| `starting_balance` | 10000.0 | Starting balance (USDT) |
| `stake_currency` | 'USDT' | Stake currency |
| `stake_amount` | 100.0 | Base stake per trade |

**⚠️ IMPORTANT:** Always start with `dry_run` mode!

**Example:**
```python
# Paper trading with higher balance
config.execution.starting_balance = 50000.0
config.execution.stake_amount = 500.0

# Use market orders
config.execution.entry_order_type = 'market'
config.execution.exit_order_type = 'market'

# ⚠️ LIVE TRADING (use with extreme caution!)
config.execution.trading_mode = 'live'
config.execution.starting_balance = 1000.0  # Start small!
```

---

## Common Scenarios

### Conservative Trader

```python
config.risk.max_loss_per_trade_pct = 1.0
config.risk.max_total_drawdown_pct = 5.0
config.risk.max_concurrent_positions = 2
config.position_sizing.base_risk_pct = 1.0
config.ai.min_confidence = 0.75
config.strategy.stoploss_pct = -0.03
```

### Aggressive Trader

```python
config.risk.max_loss_per_trade_pct = 3.0
config.risk.max_concurrent_positions = 5
config.position_sizing.base_risk_pct = 3.0
config.position_sizing.ai_confidence_min = 0.55
config.ai.min_confidence = 0.55
config.strategy.stoploss_pct = -0.05
```

### High-Frequency Scalper

```python
config.strategy.timeframe = '15m'
config.strategy.ema_fast_period = 5
config.strategy.ema_slow_period = 15
config.strategy.roi_levels = {"0": 0.05, "15": 0.02}
config.strategy.stoploss_pct = -0.02
config.position_sizing.method = 'fixed_fraction'
```

### Long-Term Trend Follower

```python
config.strategy.timeframe = '1d'
config.strategy.ema_fast_period = 50
config.strategy.ema_slow_period = 200
config.strategy.roi_levels = {"0": 0.50, "1440": 0.30, "2880": 0.20}
config.strategy.stoploss_pct = -0.10
config.risk.max_concurrent_positions = 2
```

---

## Migration Guide

### From Old Configuration (Pre-October 2025)

If you're upgrading from the old configuration system, follow these steps:

#### Step 1: Backup Current `.env`

```bash
cp .env .env.backup
```

#### Step 2: Update `.env` File

The following variables have been **removed** from `.env` (moved to `trading_config`):

| Old .env Variable | New Location |
|------------------|--------------|
| `MAX_OPEN_TRADES` | `trading_config.risk.max_concurrent_positions` |
| `STAKE_AMOUNT` | `trading_config.execution.stake_amount` |
| `MAX_DRAWDOWN_PERCENT` | `trading_config.risk.max_total_drawdown_pct` |
| `AI_CONSENSUS_THRESHOLD` | `trading_config.ai.min_consensus_score` |
| `ENABLE_CHATGPT` | `trading_config.ai.chatgpt_weight` (0 to disable) |
| `ENABLE_CLAUDE` | `trading_config.ai.claude_weight` (0 to disable) |
| `ENABLE_GEMINI` | `trading_config.ai.gemini_weight` (0 to disable) |
| `STRATEGY_MODE` | `trading_config.strategy.strategy_name` |
| `ENABLE_MANUAL_OVERRIDE` | (removed - use CLI/dashboard) |

**Variables that STAY in `.env`:**
- API keys (Binance, OpenAI, Anthropic, Gemini)
- Database URLs
- Telegram credentials
- `TRADING_MODE` (kept for safety)
- `DATA_REFRESH_INTERVAL`
- `DEBUG`, `LOG_LEVEL`

#### Step 3: Copy New Template

```bash
cp .env.example .env
```

Then restore your secrets (API keys, database URLs) from `.env.backup`.

#### Step 4: Configure Trading Parameters

**Option A: Use defaults** (no action needed)

**Option B: Create `trading_config.json`:**

```json
{
  "risk": {
    "max_concurrent_positions": 2,
    "max_total_drawdown_pct": 10.0
  },
  "execution": {
    "stake_amount": 100.0
  },
  "ai": {
    "chatgpt_weight": 0.4,
    "claude_weight": 0.35,
    "gemini_weight": 0.25
  }
}
```

#### Step 5: Update Code References

**Before:**
```python
from proratio_utilities.config.settings import get_settings

settings = get_settings()
max_trades = settings.max_open_trades  # ❌ Removed
```

**After:**
```python
from proratio_utilities.config.settings import get_settings
from proratio_utilities.config.trading_config import get_trading_config

settings = get_settings()  # For secrets
config = get_trading_config()  # For trading params

max_trades = config.risk.max_concurrent_positions  # ✅
```

#### Step 6: Verify Configuration

```bash
./start.sh cli
proratio> /config show
```

### Backward Compatibility

✅ Old `.env` variables are ignored (no errors)
✅ `TRADING_MODE` in `.env` still works (safety override)
✅ All trading parameters have sensible defaults
✅ System works without `trading_config.json`

---

## Best Practices

### Configuration Management

1. **Version Control**
   - ✅ Commit `trading_config.json` to git
   - ❌ Never commit `.env`
   - ✅ Document changes in git commit messages

2. **Testing**
   - Always test changes in `dry_run` mode first
   - Run backtests before live deployment
   - Paper trade for 1-2 weeks minimum

3. **Documentation**
   - Comment why you changed parameters
   - Keep a log of configuration experiments
   - Track performance by configuration version

4. **Safety**
   - Never change config during active trades
   - Backup working configs before major changes
   - Start conservative, increase risk gradually
   - Always validate: `config.validate()`

5. **Environments**
   - Use separate configs for test/prod
   - Never test experimental configs in live mode
   - Keep production configs stable

### Validation Workflow

Always validate before deploying:

```python
config = get_trading_config()

# Validate
errors = config.validate()
if errors:
    print("❌ Configuration errors:")
    for error in errors:
        print(f"  - {error}")
    exit(1)

# Print summary
print("✅ Configuration valid")
config.print_summary()

# Confirm before live trading
if config.execution.trading_mode == 'live':
    confirm = input("⚠️  Live trading enabled! Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        exit(1)
```

---

## Troubleshooting

### Error: "max_open_trades not found"

**Cause:** Old code accessing removed settings

**Solution:** Update to use `get_trading_config()`:
```python
from proratio_utilities.config.trading_config import get_trading_config
config = get_trading_config()
max_trades = config.risk.max_concurrent_positions
```

### Trading Parameters Not Changing

**Cause:** Using old `.env` variables (now ignored)

**Solution:**
1. Create `trading_config.json` with your settings, OR
2. Modify `trading_config.py` defaults

### Can't Find `trading_config.json`

**Cause:** File doesn't exist (optional file)

**Solution:** This is normal! Create it only if you need custom settings.

### Configuration Validation Errors

**Cause:** Invalid parameter values

**Solution:** Run `config.validate()` to see specific errors:
```python
config = get_trading_config()
errors = config.validate()
for error in errors:
    print(f"Error: {error}")
```

### AI Providers Not Working

**Cause:** API keys in `.env` invalid or missing

**Solution:**
1. Check `.env` has correct keys
2. Verify keys are valid (test on provider's website)
3. Check API quotas not exceeded

### "TRADING_MODE override" Warning

**Cause:** `.env` has `TRADING_MODE` set (overrides config)

**Solution:** This is intentional for safety. To use config value, remove `TRADING_MODE` from `.env`.

---

## File Locations

- **Environment config**: `.env` (root directory)
- **Environment template**: [`.env.example`](../../.env.example)
- **Settings loader**: [`proratio_utilities/config/settings.py`](../../proratio_utilities/config/settings.py)
- **Trading config (code)**: [`proratio_utilities/config/trading_config.py`](../../proratio_utilities/config/trading_config.py)
- **Trading config (JSON)**: [`proratio_utilities/config/trading_config.json`](../../proratio_utilities/config/trading_config.json)
- **This guide**: [`docs/guides/configuration_guide.md`](configuration_guide.md)

---

## CLI Commands

```bash
# View all configuration
./start.sh cli
proratio> /config show

# View specific section
proratio> /config show risk
proratio> /config show ai

# Set configuration value
proratio> /config set risk.max_concurrent_positions 5

# Validate configuration
proratio> /config validate
```

---

## Additional Resources

- [Getting Started Guide](../getting_started.md)
- [Paper Trading Guide](paper_trading_guide.md)
- [Strategy Development Guide](strategy_development_guide.md)
- [Dashboard Guide](dashboard_guide.md)
- [Troubleshooting](../troubleshooting.md)

---

**Remember**: Always paper trade for 1-2 weeks before considering live trading!

**Last Updated:** October 13, 2025
