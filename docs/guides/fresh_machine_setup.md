# Fresh Machine Setup Guide

**Proratio Trading System - Complete Installation for New Machines**

This guide walks you through setting up Proratio on a completely fresh machine, from zero to fully operational trading system.

**Time Required**: ~30 minutes
**Last Updated**: 2025-10-17

---

## 📋 Prerequisites Checklist

Before starting, ensure your machine has:

### Required Software
- [ ] **macOS** (10.15+) or **Linux** (Ubuntu 20.04+)
  - Windows requires WSL2 (Windows Subsystem for Linux)
- [ ] **Homebrew** (macOS) or **apt** (Linux)
- [ ] **Git** installed (`git --version`)
- [ ] **Docker Desktop** installed and running
  - Download: https://www.docker.com/products/docker-desktop
  - Verify: `docker --version` and `docker-compose --version`
- [ ] **Python 3.11+** (managed by UV, see below)
- [ ] **Internet connection** (for downloading data and dependencies)

### API Keys (Get Before Starting)
- [ ] **Binance Testnet** - https://testnet.binance.vision/ (FREE)
  - Create account → API Management → Create API Key
  - Save API Key + Secret somewhere safe
- [ ] **At least 2 of 3 AI Providers** (all have free tiers):
  - [ ] OpenAI (ChatGPT) - https://platform.openai.com/api-keys ($5 free)
  - [ ] Anthropic (Claude) - https://console.anthropic.com/ ($5 free)
  - [ ] Google (Gemini) - https://aistudio.google.com/app/apikey (FREE unlimited!)

---

## 🚀 Step-by-Step Installation

### Step 1: Install UV (Universal Python Manager)

UV manages Python versions and dependencies per-project (replaces pyenv/poetry/pip).

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell to activate UV
source ~/.bashrc  # Linux
# or
source ~/.zshrc   # macOS

# Verify installation
uv --version
```

**Expected output**: `uv 0.x.x`

---

### Step 2: Clone Repository

```bash
# Navigate to your projects directory
cd ~/Projects  # or wherever you keep code

# Clone the repository
git clone https://github.com/yourusername/proratio.git
cd proratio
```

---

### Step 3: Setup Python Environment

UV will automatically manage Python installation and virtual environment.

```bash
# Install Python 3.12 (UV downloads and manages it)
uv python install 3.12

# Pin Python version for this project
uv python pin 3.12

# Verify
uv python list  # Should show 3.12 installed
```

**Expected output**:
```
cpython-3.12.x-macos-aarch64-none    /Users/you/.local/share/uv/python/...
```

---

### Step 4: Run Automated Setup

```bash
# Make setup script executable
chmod +x scripts/setup.sh

# Run automated setup (handles everything!)
./scripts/setup.sh
```

**What this does**:
1. ✅ Creates virtual environment with UV
2. ✅ Installs all Python dependencies
3. ✅ Installs Freqtrade (~500MB)
4. ✅ Installs PyTorch (~2GB, CPU version)
5. ✅ Starts Docker services (PostgreSQL, Redis)
6. ✅ Verifies installation

**Expected output**:
```
[1/5] Creating virtual environment...
✓ Virtual environment created at .venv/

[2/5] Installing dependencies...
✓ Installed 127 packages

[3/5] Starting Docker services...
✓ PostgreSQL running (port 5432)
✓ Redis running (port 6379)

[4/5] Verifying installation...
✓ Freqtrade: 2025.9.1
✓ PyTorch: 2.8.0 (CPU)
✓ All dependencies satisfied

[5/5] Setup complete!
```

**If Docker fails**:
- Ensure Docker Desktop is running
- Check: `docker info`
- Restart: `docker-compose up -d postgres redis`

---

### Step 5: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys
nano .env  # or: vim .env, code .env
```

**Required values to edit**:

```bash
# ============================================
# BINANCE (Use Testnet for Practice!)
# ============================================
BINANCE_API_KEY=your-testnet-api-key-here
BINANCE_API_SECRET=your-testnet-secret-here
BINANCE_TESTNET=true  # ⚠️ ALWAYS TRUE for testing!

# ============================================
# AI PROVIDERS (Need at least 2 of 3)
# ============================================
# OpenAI (ChatGPT)
OPENAI_API_KEY=sk-proj-xxxx...

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-xxxx...

# Google (Gemini) - RECOMMENDED (free unlimited!)
GEMINI_API_KEY=AIza...

# ============================================
# DATABASE (Don't change!)
# ============================================
DATABASE_URL=postgresql://proratio:proratio_password@localhost:5432/proratio
REDIS_URL=redis://localhost:6379/0

# ============================================
# TRADING MODE (Keep dry_run for testing!)
# ============================================
TRADING_MODE=dry_run  # Paper trading (no real money)
```

**Save and exit** (Ctrl+X → Y → Enter in nano)

---

### Step 6: Initialize Database

```bash
# Initialize PostgreSQL schema
docker exec -i proratio_postgres psql -U proratio -d proratio < proratio_utilities/data/schema.sql
```

**Expected output**:
```
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
```

---

### Step 7: Download Historical Market Data

```bash
# Download BTC/USDT historical data (last 2 years)
# This uses Binance PUBLIC API (no API keys needed!)
freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT ETH/USDT \
  --timeframes 1h 4h 1d \
  --days 730 \
  --userdir user_data \
  --data-format-ohlcv feather
```

**Expected output**:
```
Downloading pair BTC/USDT, interval 1h...
Downloaded data for BTC/USDT with length 17526.
Downloading pair BTC/USDT, interval 4h...
Downloaded data for BTC/USDT with length 4381.
Downloading pair BTC/USDT, interval 1d...
Downloaded data for BTC/USDT with length 730.
...
✓ Downloaded 6 files successfully
```

**Note**: This takes ~30 seconds and does NOT require API keys.

---

### Step 8: Train ML Ensemble Model (Phase 4.7)

The system uses a pre-trained ML ensemble (LSTM + LightGBM + XGBoost). Train it on your machine:

```bash
# Train ensemble model on BTC/USDT 4h data
./venv/bin/python scripts/train_ensemble_model.py \
  --pair BTC/USDT \
  --timeframe 4h \
  --ensemble-method stacking \
  --save models/ensemble_model.pkl
```

**What this does**:
- Loads historical BTC/USDT 4h data
- Engineers 65 technical features
- Trains LSTM, LightGBM, XGBoost models
- Creates stacking ensemble meta-model
- Saves to `models/ensemble_model.pkl` (~2.9MB)

**Expected output**:
```
[1/6] Loading data for BTC/USDT (4h)...
✓ Loaded 4386 candles

[2/6] Engineering features...
✓ Created 71 features

[3/6] Preparing train/val/test splits...
✓ Train: 2928, Val: 627, Test: 628

[4/6] Building stacking ensemble...
✓ Ensemble built successfully

[5/6] Evaluating ensemble...
Ensemble RMSE: 1.578622
→ Improvement over best base model

[6/6] Saving ensemble to models/ensemble_model.pkl...
✓ Model saved

✓ Training complete!
```

**Time**: ~1 minute

---

## ✅ Verify Installation

### Test 1: System Health Check

```bash
./start.sh status all
```

**Expected output**:
```
╔══════════════════════════════════════════╗
║    Proratio System Health Check          ║
╚══════════════════════════════════════════╝

✅ Environment Variables: 13/13 configured
✅ Database: PostgreSQL connected (port 5432)
✅ Redis: Connected (port 6379)
✅ Data Files: 6 feather files found
   - BTC_USDT-1h.feather (17,526 candles)
   - BTC_USDT-4h.feather (4,381 candles)
   - BTC_USDT-1d.feather (730 candles)
   - ETH_USDT-1h.feather (17,526 candles)
   - ETH_USDT-4h.feather (4,381 candles)
   - ETH_USDT-1d.feather (730 candles)
✅ Freqtrade: 2025.9.1 installed
✅ PyTorch: 2.8.0 (CPU) installed
✅ AI Providers: 3/3 configured
   - OpenAI: Configured ✓
   - Anthropic: Configured ✓
   - Gemini: Configured ✓
✅ ML Models: Found (models/ensemble_model.pkl, 2.9MB)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
System Status: READY ✅ (13/13 checks passed)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Test 2: Verify Data Loaded

```bash
python -c "
import pandas as pd
from pathlib import Path

data_file = Path('user_data/data/binance/BTC_USDT-4h.feather')
df = pd.read_feather(data_file)
print(f'✓ Loaded {len(df)} candles')
print(f'  Date range: {df[\"date\"].min()} to {df[\"date\"].max()}')
print(f'  Columns: {list(df.columns)}')
"
```

**Expected output**:
```
✓ Loaded 4381 candles
  Date range: 2023-10-15 00:00:00+00:00 to 2025-10-15 20:00:00+00:00
  Columns: ['date', 'open', 'high', 'low', 'close', 'volume']
```

### Test 3: Test ML Model

```bash
python -c "
from proratio_quantlab.ml.ensemble_predictor import EnsemblePredictor
import numpy as np

# Load model
ensemble = EnsemblePredictor()
ensemble.load('models/ensemble_model.pkl')

print(f'✓ Model loaded successfully')
print(f'  Base models: {ensemble.model_names}')
print(f'  Ensemble method: {ensemble.ensemble_method}')
print(f'  Features: {len(ensemble.feature_names)}')
"
```

**Expected output**:
```
✓ Model loaded successfully
  Base models: ['lgbm', 'xgb', 'lstm']
  Ensemble method: stacking
  Features: 65
```

### Test 4: Test LLM Providers (Optional - Uses API Credits)

```bash
# Test a single LLM provider (costs ~$0.001)
python scripts/test_llm_integration.py
```

**Expected output**:
```
Testing LLM Integration...

✓ OpenAI (ChatGPT): Responding
  Direction: neutral
  Confidence: 0.52

✓ Anthropic (Claude): Responding
  Direction: short
  Confidence: 0.61

✓ Google (Gemini): Responding
  Direction: long
  Confidence: 0.58

✓ All 3 providers working!
```

---

## 🎮 Launch the System

### Option 1: Interactive CLI (Recommended)

```bash
./start.sh
```

**What you'll see**:
```
╔══════════════════════════════════════════╗
║      Proratio Trading System v0.9.2      ║
╚══════════════════════════════════════════╝

🔍 Running system health checks...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Database      Connected (0 records)
✓ Redis         Connected
✓ Data Files    6 files available
✓ AI Providers  3/3 active
✓ ML Models     Loaded (models/ensemble_model.pkl)

Ready! Type /help for commands.

proratio>
```

**Try these commands**:
```bash
proratio> /help              # Show all commands
proratio> /status            # Full health check
proratio> /strategy list     # List strategies
proratio> /config show risk  # View risk settings
proratio> /quit              # Exit CLI
```

### Option 2: Run Paper Trading Test

```bash
# Validate Hybrid ML+LLM strategy (6-24 hour test recommended)
./start.sh strategy validate a014_hybrid-ml-llm --duration 24h
```

**What this does**:
- Starts paper trading with Hybrid ML+LLM strategy
- Logs all predictions (ML + LLM)
- Tests conflict detection
- Monitors for errors
- Generates analysis report after completion

---

## 📊 Next Steps

### 1. Understand the System

Read these docs in order:
1. **[proratio_concepts.md](../proratio_concepts.md)** - Technical overview
2. **[roadmap.md](../project/roadmap.md)** - Development phases
3. **[CLAUDE.md](../../CLAUDE.md)** - Implementation guidelines

### 2. Run Your First Backtest

```bash
# Validate Mean Reversion strategy
./scripts/validate_strategy.sh 355c_mean-reversion
```

Expected: Win rate ~56%, validation passes

### 3. Test Phase 4.7 Analysis Scripts

```bash
# Analyze ML confidence distribution
python scripts/analyze_model_confidence.py --pair BTC/USDT --timeframe 4h --days 180

# Optimize thresholds
python scripts/optimize_confidence_thresholds.py --pair BTC/USDT --days 180
```

### 4. Start Extended Paper Trading (Phase 4.8)

```bash
# Run 24-48 hour validation
./start.sh trade start --strategy a014_hybrid-ml-llm --duration 48h
```

**Monitor with**:
```bash
# In separate terminal
tail -f user_data/logs/hybrid_predictor.log
```

---

## 🔒 Security Checklist

Before running paper trading or live trading:

- [ ] ✅ Using **Binance Testnet** (not mainnet!)
- [ ] ✅ `BINANCE_TESTNET=true` in `.env`
- [ ] ✅ `TRADING_MODE=dry_run` in `.env`
- [ ] ✅ API keys have **NO withdrawal permissions**
- [ ] ✅ 2FA enabled on Binance account
- [ ] ✅ IP whitelist enabled (optional)
- [ ] ✅ Never share `.env` file (contains secrets!)
- [ ] ✅ `.env` is gitignored (verify with `git status`)

---

## 🐛 Common Issues

### Issue: "ModuleNotFoundError: No module named 'uv'"

**Solution**: UV not installed or not in PATH
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.zshrc  # or ~/.bashrc
```

### Issue: "docker: command not found"

**Solution**: Docker not installed
```bash
# macOS
brew install --cask docker
# Then start Docker Desktop application

# Linux (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo systemctl start docker
```

### Issue: "Port 5432 already in use"

**Solution**: PostgreSQL already running
```bash
# Check what's using port 5432
lsof -i :5432

# Stop existing PostgreSQL
brew services stop postgresql  # macOS
# or
sudo systemctl stop postgresql  # Linux

# Or use different port in docker-compose.yml
```

### Issue: "libomp.dylib not found" (macOS with LightGBM)

**Solution**: Install OpenMP library
```bash
brew install libomp
```

### Issue: Data download fails

**Solution**: Check internet and try again
```bash
# Download with verbose output
freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT \
  --timeframes 4h \
  --days 180 \
  --userdir user_data \
  --data-format-ohlcv feather \
  -vvv  # Very verbose
```

---

## 📚 Essential Files Reference

### Configuration Files
- `.env` - API keys and secrets (NEVER commit!)
- `proratio_utilities/config/trading_config.json` - Trading parameters
- `docker-compose.yml` - Infrastructure services

### Data Files (gitignored)
- `user_data/data/binance/*.feather` - Market data
- `models/ensemble_model.pkl` - Trained ML model (2.9MB)
- `user_data/logs/*.log` - Application logs

### Key Scripts
- `./start.sh` - Main entry point
- `scripts/setup.sh` - Automated setup
- `scripts/train_ensemble_model.py` - ML model training
- `scripts/analyze_model_confidence.py` - Phase 4.7 analysis

---

## ✅ Installation Complete!

**Your system is now ready for:**
- ✅ Paper trading with Hybrid ML+LLM strategy
- ✅ Strategy backtesting and validation
- ✅ ML model training and evaluation
- ✅ Confidence analysis (Phase 4.7)
- ✅ Extended paper trading tests (Phase 4.8)

**Before live trading:**
1. Run paper trading for 1-2 weeks minimum
2. Validate all strategies meet criteria
3. Test with small capital first (1-5% of intended amount)
4. Review [paper_trading_guide.md](paper_trading_guide.md)

**Remember:**
- 🧪 **ALWAYS test in dry-run mode first**
- 📊 **Use validation framework for all strategies**
- 🔒 **NEVER enable withdrawal permissions on API keys**
- 📚 **Refer to documentation when stuck**

**Happy trading!** 🚀

---

**Version**: 1.0.0
**Last Updated**: 2025-10-17
**Compatible With**: macOS (ARM64/Intel), Linux (Ubuntu 20.04+)
