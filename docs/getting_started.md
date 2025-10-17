# Getting Started with Proratio

**AI-Driven Cryptocurrency Trading System**

Get your system running in **20 minutes** with this step-by-step guide.

> **🖥️ Setting up on a fresh machine?** See [Fresh Machine Setup Guide](guides/fresh_machine_setup.md) for complete installation from scratch (30 minutes).

---

## 📋 What You'll Need

Before starting, make sure you have:

- ✅ **macOS or Linux** (Windows requires WSL2)
- ✅ **Python 3.11+** installed (`python --version`)
- ✅ **Docker Desktop** installed and running
- ✅ **15-20 minutes** of time

**API Keys** (free accounts work!):
- [Binance Testnet](https://testnet.binance.vision/) - Test trading (no real money)
- [OpenAI API](https://platform.openai.com/) - ChatGPT
- [Anthropic API](https://console.anthropic.com/) - Claude
- [Google AI Studio](https://aistudio.google.com/) - Gemini

> **Note**: You need at least **2 out of 3** AI providers to use the system.

---

## 🚀 Installation (Step-by-Step)

### Step 1: Get the Code

```bash
# Clone the repository
git clone https://github.com/yourusername/proratio.git
cd proratio
```

### Step 2: Run Automated Setup

```bash
# Make setup script executable
chmod +x scripts/setup.sh

# Run setup (installs everything automatically)
./scripts/setup.sh
```

**What this does:**
- ✅ Creates Python virtual environment
- ✅ Installs UV package manager
- ✅ Installs all dependencies
- ✅ Starts Docker services (PostgreSQL, Redis)
- ✅ Verifies installation

**Expected output:**
```
✓ Virtual environment created
✓ Dependencies installed
✓ Docker services started
✓ Setup complete!
```

> **Troubleshooting**: If Docker fails to start, make sure **Docker Desktop is running** first.

### Step 3: Configure API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Open .env in your editor
nano .env  # or: vim .env, code .env, etc.
```

**Edit these values in `.env`:**

```bash
# ============================================
# EXCHANGE API (Binance Testnet - FREE!)
# ============================================
BINANCE_API_KEY=your-testnet-api-key-here
BINANCE_API_SECRET=your-testnet-secret-here
BINANCE_TESTNET=true  # ⚠️ KEEP THIS TRUE FOR TESTING!

# ============================================
# AI PROVIDERS (Need at least 2 of 3)
# ============================================
# OpenAI (ChatGPT)
OPENAI_API_KEY=sk-proj-...

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-...

# Google (Gemini)
GEMINI_API_KEY=AI...

# ============================================
# DATABASE (Don't change these!)
# ============================================
DATABASE_URL=postgresql://proratio:proratio_password@localhost:5432/proratio
REDIS_URL=redis://localhost:6379/0

# ============================================
# TRADING MODE (Keep this for testing)
# ============================================
TRADING_MODE=dry_run  # Paper trading (no real money)
```

**Where to get API keys:**

1. **Binance Testnet** (free test exchange):
   - Go to: https://testnet.binance.vision/
   - Register an account
   - Go to API Management → Create API Key
   - Copy both API Key and Secret Key

2. **OpenAI** (ChatGPT):
   - Go to: https://platform.openai.com/api-keys
   - Create new secret key
   - Free tier: $5 credit

3. **Anthropic** (Claude):
   - Go to: https://console.anthropic.com/
   - Get API keys
   - Free tier: $5 credit

4. **Google** (Gemini):
   - Go to: https://aistudio.google.com/app/apikey
   - Create API key
   - **Free tier**: Unlimited!

**Save the file** and exit (Ctrl+X, then Y if using nano).

### Step 4: Initialize Database

```bash
# Initialize database schema
docker exec -i proratio_postgres psql -U proratio -d proratio < proratio_utilities/data/schema.sql
```

**Expected output:**
```
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
```

> This creates the tables needed to store market data and trading history.

### Step 5: Download Market Data

```bash
# Activate virtual environment
source venv/bin/activate

# Download 24 months of BTC/ETH data (takes ~10 seconds, no API key needed!)
freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT ETH/USDT \
  --timeframes 1h 4h 1d \
  --days 730 \
  --userdir user_data \
  --data-format-ohlcv feather
```

**What this does:**
- Downloads BTC/USDT and ETH/USDT historical data (2 years)
- Uses Binance **public API** (no API keys required!)
- Downloads multiple timeframes (1h, 4h, 1d)
- Stores as `.feather` files in `user_data/data/binance/`

**Expected output:**
```
Downloaded data for BTC/USDT with length 17526.
Downloaded data for BTC/USDT with length 4381.
Downloaded data for BTC/USDT with length 730.
Downloaded data for ETH/USDT with length 17526.
Downloaded data for ETH/USDT with length 4381.
Downloaded data for ETH/USDT with length 730.
✓ 6 files downloaded (1.4 MB total)
```

> **Note**: No API keys needed for historical data download!

---

## ✅ Verify Installation

### Test 1: Check Docker Services

```bash
docker-compose ps
```

**Expected output:**
```
NAME                    STATUS
proratio_postgres       Up
proratio_redis          Up
```

If services are not running:
```bash
docker-compose up -d postgres redis
```

### Test 2: Check System Status

```bash
# Check all components
./start.sh status all
```

**Expected output:**
```
System Status - 12/13 components operational

✅ Environment: All required variables present
✅ Database: PostgreSQL running
✅ Redis: Redis running
✅ Data: 6 feather files (if you ran Step 5)
✅ Freqtrade: Installed (version 2025.9.1)
✅ PyTorch: v2.8.0 (CPU)
✅ AI Providers: 3/3 configured
⚠️  ML Models: Not found (normal - train in Phase 4)
```

> **Note**: Freqtrade and PyTorch (~2GB) are installed by setup.sh automatically.

### Test 3: Check Data

```bash
# Verify data was downloaded (must activate venv first)
source venv/bin/activate

python -c "
import pandas as pd
from pathlib import Path

# Read BTC/USDT 1h data
data_file = Path('user_data/data/binance/BTC_USDT-1h.feather')
df = pd.read_feather(data_file)
print(f'✓ Loaded {len(df)} candles for BTC/USDT (1h)')
print(f'Date range: {df[\"date\"].min()} to {df[\"date\"].max()}')
"
```

**Expected output:**
```
✓ Loaded 17526 candles for BTC/USDT (1h)
Date range: 2023-10-15 00:00:00+00:00 to 2025-10-14 05:00:00+00:00
```

---

## 🎮 Launch the System

### Option 1: Interactive CLI (Recommended for Beginners)

```bash
./start.sh
```

**What you'll see:**
```
╔══════════════════════════════════════════╗
║      Proratio Trading System v0.9.0      ║
╚══════════════════════════════════════════╝

🔍 System Health Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Database      Connected (44,640 records)
✓ Redis         Connected
✓ Data Files    12 files available
✓ AI Providers  2/3 active (Claude, Gemini)

Ready! Type /help for commands.

proratio>
```

**Try these commands:**

```bash
proratio> /help              # Show all commands
proratio> /status            # Full system check
proratio> /config show       # View configuration
proratio> /strategy list     # List available strategies
proratio> /data status       # Check data availability
```

**Or use direct commands** (without the interactive prompt):

```bash
./start.sh status all           # Check system status
./start.sh strategy list        # List strategies
./start.sh config show          # Show configuration
./start.sh help                 # Show help
```

> **Tip**: Commands in the interactive CLI start with `/`, but direct commands don't.

### Option 2: Full Trading System (Dashboard + Bot)

```bash
# Start complete system
./start.sh
```

**What this launches:**
1. Freqtrade trading bot (dry-run mode)
2. Streamlit dashboard (http://localhost:8501)
3. FreqUI web interface (http://localhost:8080)

**Access the dashboard:**
- Open browser to http://localhost:8501
- View real-time trading activity
- Monitor AI signals
- Check performance metrics

---

## 🎯 Your First Trading Test

Now that everything is installed, let's validate a strategy:

### Validate a Strategy (5 minutes)

```bash
# Validate the simple test strategy
./scripts/validate_strategy.sh SimpleTestStrategy
```

**What this does:**
1. Runs backtest on 6 months of data
2. Validates results against quality criteria
3. Generates comprehensive report

**Expected output:**
```
[1/6] Running pre-flight checks...
✓ Strategy file found
✓ Data files available

[2/6] Running backtest...
✓ Backtest completed (15 trades, 53% win rate)

[3/6] Validating results...
✓ All checks passed

╔══════════════════════════════════════════╗
║     Validation Complete                  ║
╚══════════════════════════════════════════╝

✓ Strategy is ready for paper trading!
```

**See full guide**: [validation_framework_guide.md](guides/validation_framework_guide.md)

---

## 📚 Next Steps

### For First-Time Users

**1. Explore the CLI** (10 minutes)
```bash
./start.sh
```
Try these commands:
- `/help` - See all commands
- `/status` - Check system health
- `/strategy list` - View strategies
- `/config show risk` - View risk settings

**2. View the Dashboard** (5 minutes)
```bash
streamlit run proratio_tradehub/dashboard/app.py
```
- Open http://localhost:8501
- Explore the interface
- Check AI signal status

**3. Run Your First Backtest** (5 minutes)
```bash
./scripts/validate_strategy.sh TrendFollowingStrategy
```
- See how strategies perform
- Understand validation criteria
- Review performance metrics

### For Developers

**1. Read the Architecture**
- [CLAUDE.md](../CLAUDE.md) - Development guidelines
- [project/roadmap.md](project/roadmap.md) - Development plan
- [project/project_structure.md](project/project_structure.md) - Code organization

**2. Create Your First Strategy**
- [guides/strategy_development_guide.md](guides/strategy_development_guide.md)
- Start with simple indicators
- Use validation framework to test

**3. Explore Machine Learning**
- [reference/lstm_implementation.md](reference/lstm_implementation.md) - LSTM models
- [reference/ensemble_implementation.md](reference/ensemble_implementation.md) - Ensemble learning
- [reference/freqai_guide.md](reference/freqai_guide.md) - FreqAI integration

### For Researchers

**1. Launch Jupyter Lab**
```bash
jupyter lab proratio_quantlab/research/notebooks/
```

**2. Study Advanced AI Strategies**
- [project/advanced_ai_strategies.md](project/advanced_ai_strategies.md) - Phase 4-10 plans
- Multi-timeframe analysis
- Hybrid ML+LLM systems

**3. Experiment with Models**
```bash
# Train LSTM model
uv run python scripts/train_lstm_model.py --pair BTC/USDT

# Train full ensemble model (LSTM + LightGBM + XGBoost) - Phase 4
uv run python scripts/train_ensemble_model.py \
  --pair BTC/USDT \
  --timeframe 4h \
  --ensemble-method stacking \
  --save models/ensemble_model.pkl

# Expected: ~1 minute training time, 2.9MB model file
# Model automatically used by HybridMLLLMStrategy
```

---

## 🛡️ Safety Checklist

**Before going live, verify:**

- [ ] ✅ Using **Binance Testnet** (not mainnet)
- [ ] ✅ `BINANCE_TESTNET=true` in `.env`
- [ ] ✅ `TRADING_MODE=dry_run` in `.env`
- [ ] ✅ API keys have **NO withdrawal permissions**
- [ ] ✅ 2FA enabled on exchange account
- [ ] ✅ IP whitelist enabled (optional but recommended)
- [ ] ✅ Tested strategies with validation framework
- [ ] ✅ Monitored paper trading for 1-2 weeks

**⚠️ NEVER:**
- Start with mainnet before testing
- Give API keys withdrawal permissions
- Trade with money you can't afford to lose
- Skip paper trading validation

---

## 🐛 Troubleshooting

### Problem: Docker services won't start

**Solution:**
```bash
# Stop and remove all containers
docker-compose down -v

# Restart services
docker-compose up -d postgres redis

# Verify they're running
docker-compose ps
```

### Problem: "Module not found" errors

**Solution:** Always use `uv run` prefix:
```bash
# ✅ Correct
uv run python scripts/my_script.py

# ❌ Wrong
python scripts/my_script.py
```

### Problem: API keys not working

**Check the .env file:**
```bash
# View environment variables (safe check - no secrets shown)
uv run python -c "
from proratio_utilities.config.settings import get_settings
settings = get_settings()
print(f'OpenAI key set: {bool(settings.openai_api_key)}')
print(f'Claude key set: {bool(settings.anthropic_api_key)}')
print(f'Gemini key set: {bool(settings.gemini_api_key)}')
"
```

**Test individual providers:**
```bash
./start.sh
# Then run:
proratio> /status providers
```

### Problem: No data in database

**Re-download data:**
```bash
uv run python scripts/download_historical_data.py
```

### Problem: Database connection errors

**Reinitialize database:**
```bash
# Drop and recreate database
docker-compose down -v
docker-compose up -d postgres
sleep 5  # Wait for PostgreSQL to start

# Initialize schema
docker exec -i proratio_postgres psql -U proratio -d proratio < proratio_utilities/data/schema.sql

# Re-download data
uv run python scripts/download_historical_data.py
```

### Problem: Port already in use

**Check what's using the port:**
```bash
# Check port 8501 (Streamlit)
lsof -i :8501

# Check port 8080 (FreqUI)
lsof -i :8080

# Kill process if needed
kill -9 <PID>
```

---

## 📖 Additional Resources

### Quick Reference
- **[CLI Commands](cli_guide.md)** - Complete command reference
- **[Configuration Guide](guides/configuration_guide.md)** - All settings explained
- **[Validation Framework](guides/validation_framework_guide.md)** - Strategy testing

### Guides
- **[Paper Trading Guide](guides/paper_trading_guide.md)** - Safe testing environment
- **[Strategy Development](guides/strategy_development_guide.md)** - Create strategies
- **[Dashboard Guide](guides/dashboard_guide.md)** - Use the UI

### Technical Reference
- **[FreqAI Guide](reference/freqai_guide.md)** - Machine learning
- **[LSTM Implementation](reference/lstm_implementation.md)** - Neural networks
- **[Backtesting Guide](reference/backtesting_guide.md)** - Test strategies

### Project Management
- **[Roadmap](project/roadmap.md)** - Development phases
- **[Project Progress](project/project_progress.md)** - Current status
- **[Advanced AI Strategies](project/advanced_ai_strategies.md)** - Future features

---

## 💬 Getting Help

### 1. Check Documentation
All docs are in the `docs/` directory:
```bash
# View documentation index
cat docs/index.md

# Browse docs
open docs/  # macOS
xdg-open docs/  # Linux
```

### 2. Run Built-in Help
```bash
./start.sh
proratio> /help              # List all commands
proratio> /help status       # Detailed help for command
```

### 3. Check Logs
```bash
# View recent logs
tail -f user_data/logs/freqtrade.log

# Search for errors
grep ERROR user_data/logs/freqtrade.log
```

### 4. Run Diagnostics
```bash
# System health check
./start.sh
proratio> /status

# Test configuration
uv run python scripts/show_trading_config.py --validate
```

---

## 🔧 Advanced: Manual Setup

If you need more control over the installation process or the automated setup fails, you can install manually:

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Binance account (testnet for development)
- API keys for AI services (OpenAI, Anthropic, Google)

### Manual Installation Steps

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# 2. Install UV package manager
pip install uv

# 3. Install dependencies using UV
uv pip install -r requirements.txt

# 4. Start infrastructure
docker-compose up -d postgres redis

# 5. Initialize database schema
docker exec -i proratio_postgres psql -U proratio -d proratio < proratio_utilities/data/schema.sql

# 6. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 7. Download historical data (to PostgreSQL)
uv run python scripts/download_historical_data.py

# 8. Export data for Freqtrade (when needed)
uv run python scripts/export_data_for_freqtrade.py

# 9. Verify installation
uv run python scripts/show_trading_config.py --validate
```

### Important Notes

- **Always use `uv run python`** to ensure you're using the correct Python environment with all dependencies
- **UV manages Python versions** per-project (no global Python managers needed)
- **Each project has isolated environments** via UV's built-in virtual environments
- **System Python (`/usr/bin/python3`)** remains untouched for OS tools

### Manual Configuration

```bash
# View current configuration
python scripts/show_trading_config.py

# Edit configuration (all trading parameters in one file)
# Edit: proratio_utilities/config/trading_config.json

# Validate configuration
python scripts/show_trading_config.py --validate
```

For configuration details, see [Configuration Guide](guides/configuration_guide.md).

### Manual Paper Trading

```bash
# Start Freqtrade in dry-run mode
freqtrade trade \
  --strategy ProRatioAdapter \
  --userdir user_data \
  --config proratio_utilities/config/freqtrade/config_dry.json
```

For complete paper trading workflow, see [Paper Trading Guide](guides/paper_trading_guide.md).

---

## 🎉 You're Ready!

**Congratulations!** Your Proratio system is now installed and ready to use.

**Recommended first actions:**
1. ✅ Explore the CLI: `./start.sh`
2. ✅ Validate a strategy: `./scripts/validate_strategy.sh SimpleTestStrategy`
3. ✅ View the dashboard: `streamlit run proratio_tradehub/dashboard/app.py`
4. ✅ Read the paper trading guide: `docs/guides/paper_trading_guide.md`

**Remember:**
- 🧪 Always test in **dry-run mode** first
- 📊 Use the **validation framework** for all strategies
- 🔒 Never enable withdrawal permissions on API keys
- 📚 Refer to **documentation** when stuck

**Happy trading!** 🚀

---

**Version**: 0.9.0 | **Last Updated**: 2025-10-14
