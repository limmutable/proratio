# Proratio Quick Start Guide

This guide will get you up and running with Proratio in minutes.

---

## Prerequisites

Before you begin, ensure you have:

- ✅ Python 3.11 or higher
- ✅ Docker and Docker Compose installed
- ✅ Git (for version control)
- ✅ Binance account (testnet recommended for development)
- ✅ API keys for AI services (OpenAI, Anthropic, Google)

---

## Step 1: Initial Setup

Run the automated setup script:

```bash
cd proratio
./scripts/setup.sh
```

This script will:
- Create Python virtual environment
- Install all dependencies
- Start PostgreSQL and Redis containers
- Create `.env` file from template
- Initialize Freqtrade user directory

---

## Step 2: Configure API Keys

Edit the `.env` file and add your API keys:

```bash
nano .env  # or use your preferred editor
```

**Required keys:**
- `BINANCE_API_KEY` - Your Binance API key (testnet recommended)
- `BINANCE_API_SECRET` - Your Binance API secret
- `OPENAI_API_KEY` - OpenAI API key for ChatGPT
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude
- `GEMINI_API_KEY` - Google API key for Gemini

**Optional (for notifications):**
- `TELEGRAM_BOT_TOKEN` - Telegram bot token (from @BotFather)
- `TELEGRAM_CHAT_ID` - Your Telegram chat ID

**Important:** Keep `BINANCE_TESTNET=true` for development!

---

## Step 3: Initialize Database & Download Historical Data

Initialize the PostgreSQL database schema:

```bash
# Initialize database tables
docker exec -i proratio_postgres psql -U proratio -d proratio < proratio_utilities/data/schema.sql
```

Download market data to PostgreSQL (custom Proratio data collector):

```bash
# Download 24 months of OHLCV data
uv run python scripts/download_historical_data.py
```

This downloads 24 months of data for BTC/USDT and ETH/USDT in multiple timeframes (1h, 4h, 1d) and stores it in PostgreSQL.

**Alternative:** Download data using Freqtrade (for Freqtrade-only workflows):

```bash
freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT ETH/USDT \
  --timeframe 4h 1h \
  --days 180 \
  --userdir user_data
```

---

## Step 4: Verify Installation

Check that everything is working:

```bash
# Check infrastructure services
docker-compose ps

# Should show postgres and redis as "Up"

# Test Python environment
python -c "from proratio_utilities.config import get_settings; print('✅ Config loaded')"

# Run tests
pytest tests/test_core/test_config.py
```

---

## Step 5: Explore the System

### Option A: Start Jupyter Lab (Recommended for learning)

```bash
jupyter lab proratio_quantlab/research/notebooks/
```

Create a new notebook and try:

```python
# Test configuration
from proratio_utilities.config import get_settings

settings = get_settings()
print(f"Trading mode: {settings.trading_mode}")
print(f"Max open trades: {settings.max_open_trades}")
```

### Option B: Run Paper Trading

```bash
# Start Freqtrade in dry-run mode
freqtrade trade \
  --strategy ProRatioAdapter \
  --userdir user_data \
  --config proratio_utilities/config/freqtrade/config_dry.json
```

**Note:** The `ProRatioAdapter` strategy will be created in Phase 1.1 of the development plan.

---

## Step 6: Next Steps

Now that your environment is set up, you can:

1. **Review the architecture** in [CLAUDE.md](../CLAUDE.md)
2. **Follow the development plan** in [roadmap.md](../roadmap.md)
3. **Start with Phase 1.0 tasks** (implement Proratio Utilities)
4. **Experiment in Jupyter notebooks**

---

## Common Issues & Solutions

### Issue: `docker-compose: command not found`

**Solution:**
```bash
# Install Docker Desktop (includes Docker Compose)
brew install --cask docker

# Open Docker Desktop from Applications to start the Docker daemon
# Then verify installation:
docker --version
docker-compose --version
```

### Issue: Database error "relation 'ohlcv' does not exist"

**Solution:**
```bash
# Initialize database schema
docker exec -i proratio_postgres psql -U proratio -d proratio < proratio_utilities/data/schema.sql

# Verify tables created
docker exec -it proratio_postgres psql -U proratio -d proratio -c "\dt"
```

### Issue: `ModuleNotFoundError: No module named 'ccxt'`

**Solution:**
```bash
# Always use UV to run Python scripts in this project
uv run python scripts/download_historical_data.py

# NOT: python scripts/download_historical_data.py
# (This uses system Python without the correct dependencies)
```

### Issue: Docker services won't start

**Solution:**
```bash
# Stop all containers
docker-compose down

# Remove volumes and restart
docker-compose down -v
docker-compose up -d postgres redis

# Verify containers are running
docker ps
```

### Issue: Python version mismatch

**Solution:**
```bash
# Install Python 3.11+ via pyenv (macOS)
brew install pyenv
pyenv install 3.11.7
pyenv local 3.11.7

# Recreate virtual environment
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Freqtrade download fails

**Solution:**
```bash
# Ensure you're using testnet for development
export BINANCE_TESTNET=true

# Try with fewer days first
freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT \
  --timeframe 4h \
  --days 30 \
  --userdir user_data
```

### Issue: Can't import proratio modules

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Ensure you're in the project root
pwd  # Should show /Users/jlim/Projects/proratio

# Add project to PYTHONPATH (temporary)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## Useful Commands Reference

```bash
# Activate virtual environment
source venv/bin/activate

# Check infrastructure status
docker-compose ps

# View logs
docker-compose logs -f postgres
docker-compose logs -f redis

# Stop infrastructure
docker-compose down

# Restart infrastructure
docker-compose restart postgres redis

# Run tests
pytest                          # All tests
pytest tests/test_core/         # Specific module
pytest -v                       # Verbose output
pytest --cov=proratio_signals   # With coverage

# Start Jupyter Lab
jupyter lab

# Start Streamlit dashboard (when built)
streamlit run proratio_tradehub/dashboard/app.py

# Freqtrade commands
freqtrade --help
freqtrade backtesting --help
freqtrade hyperopt --help
```

---

## Security Checklist

Before proceeding with development:

- [ ] `.env` file is in `.gitignore` (already done)
- [ ] Using Binance **testnet** API keys (not mainnet)
- [ ] API keys have **read-only** or **trade-only** permissions (NO withdrawal)
- [ ] 2FA enabled on exchange account
- [ ] IP whitelisting configured on API keys (optional but recommended)
- [ ] Never commit API keys to git
- [ ] Keep `TRADING_MODE=dry_run` until thoroughly tested

---

## What's Next?

Follow the **4-Week MVP Plan** in [roadmap.md](../roadmap.md):

- **Phase 1.0**: Build Proratio Utilities (data collection + execution)
- **Phase 1.1**: Build Proratio Signals (AI integration)
- **Phase 1.2**: Build QuantLab & TradeHub (backtesting + risk management)
- **Phase 1.3**: Integration testing and paper trading validation

---

## Need Help?

For more detailed troubleshooting, see:
- **[troubleshooting.md](./troubleshooting.md)** - Comprehensive troubleshooting guide
- **[CLAUDE.md](../CLAUDE.md)** - Developer guide with common workflows

Happy building! 🚀
