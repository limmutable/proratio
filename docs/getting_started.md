# Getting Started with Proratio

**Version**: 0.8.0
**Last Updated**: 2025-10-12

Get your AI-driven crypto trading system running in 15 minutes.

---

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- API keys: Binance (testnet), OpenAI, Anthropic, Google Gemini

---

## Quick Setup

### 1. Clone and Setup

```bash
cd proratio
./scripts/setup.sh
```

This creates venv, installs dependencies, starts Docker services (PostgreSQL, Redis).

### 2. Configure API Keys

Edit `.env` file:

```bash
# Exchange
BINANCE_API_KEY=your-key-here
BINANCE_API_SECRET=your-secret-here
BINANCE_TESTNET=true  # Keep true for testing!

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# Database (default, don't change)
DATABASE_URL=postgresql://proratio:proratio_password@localhost:5432/proratio
```

### 3. Initialize Database & Download Data

```bash
# Initialize database schema
docker exec -i proratio_postgres psql -U proratio -d proratio < proratio_utilities/data/schema.sql

# Download 24 months of market data
uv run python scripts/download_historical_data.py
```

### 4. Launch CLI

```bash
./start.sh cli
```

**What happens:**
1. System initialization and health checks
2. Displays component status (Database, Redis, APIs, Data, Models)
3. Launches interactive prompt: `proratio>`

---

## Using the CLI

### Interactive Shell

All commands start with `/`:

```
proratio> /help           # Show all commands
proratio> /status         # System health check
proratio> /config         # View configuration
proratio> /strategy list  # List strategies
proratio> /quit           # Exit
```

### Essential Commands

#### Status & Monitoring
```
/status                   # Full system check
/status quick             # Critical systems only
/status providers         # AI provider status
```

#### Configuration
```
/config                   # Show all config
/config show risk         # Show risk settings
/config set key value     # Modify setting
```

#### Strategy Management
```
/strategy list                      # List all strategies
/strategy show AIEnhancedStrategy   # View strategy code
/strategy backtest <name>           # Run backtest
```

#### Data & Trading
```
/data download            # Download historical data
/data status              # Check data availability

/trade start              # Start paper trading
/trade stop               # Stop trading
/trade monitor            # Monitor activity
```

---

## Verify Installation

```bash
# Check services
docker-compose ps  # Should show postgres & redis "Up"

# Run tests
pytest tests/test_core/test_config.py

# Test AI providers
./start.sh cli
# Then run: /status providers
```

---

## Common Issues

### Docker services won't start
```bash
docker-compose down -v
docker-compose up -d postgres redis
docker ps  # Verify running
```

### Environment variables not loaded
```bash
# CLI auto-loads .env
# For manual scripts:
export $(cat .env | grep -v '^#' | xargs)
```

### Module import errors
```bash
# Always use uv:
uv run python script.py

# NOT: python script.py
```

### Database connection errors
```bash
# Reinitialize schema
docker exec -i proratio_postgres psql -U proratio -d proratio < proratio_utilities/data/schema.sql
```

---

## Next Steps

### For Beginners
1. Explore CLI: `./start.sh cli` → Try commands
2. Read [guides/paper_trading_guide.md](guides/paper_trading_guide.md)
3. View dashboard: `streamlit run proratio_tradehub/dashboard/app.py`

### For Developers
1. Review architecture: [../CLAUDE.md](../CLAUDE.md)
2. Follow roadmap: [project/roadmap.md](project/roadmap.md)
3. Implement strategies: [guides/strategy_development_guide.md](guides/strategy_development_guide.md)

### For Researchers
1. Open Jupyter: `jupyter lab proratio_quantlab/research/notebooks/`
2. Study ML models: [reference/lstm_implementation.md](reference/lstm_implementation.md)
3. Advanced AI: [project/advanced_ai_strategies.md](project/advanced_ai_strategies.md)

---

## Security Checklist

Before trading:
- [ ] Using Binance **testnet** (not mainnet)
- [ ] API keys have NO withdrawal permissions
- [ ] 2FA enabled on exchange
- [ ] `.env` not committed to git
- [ ] `TRADING_MODE=dry_run` for testing

---

## Help & Support

- **Troubleshooting**: [troubleshooting.md](troubleshooting.md)
- **CLI Reference**: Full command list with `/help`
- **Documentation Index**: [index.md](index.md)

**Ready to trade!** 🚀
