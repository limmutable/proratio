# Proratio

**AI-Driven Cryptocurrency Trading System**

Proratio is an intelligent trading system that combines multi-LLM analysis (ChatGPT, Claude, Gemini) with automated execution on Binance. Designed for low-frequency, high-conviction trading with comprehensive backtesting and risk management.

**Version**: 0.4.0 (Phase 2 Complete: Advanced Strategies & Portfolio Management)

> For detailed project status, weekly progress, and development plans, see [docs/roadmap.md](./docs/roadmap.md)

---

## 🎯 Key Features

- **Multi-AI Analysis**: Leverages ChatGPT, Claude, and Gemini for market insights
- **Automated Execution**: Freqtrade-powered trading on Binance (Spot, Futures, Options)
- **Comprehensive Backtesting**: Walk-forward analysis and multi-strategy comparison
- **Risk Management**: 6-layer risk validation with emergency stops and 5 position sizing methods
- **Centralized Configuration**: Single JSON file controls all 60+ trading parameters
- **Modular Architecture**: Four independent modules for flexibility and extensibility
- **Multi-Strategy System**: 3 strategies (Trend, Mean Reversion, Grid) with intelligent portfolio allocation
- **Production-Ready**: 163 passing tests with comprehensive coverage

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              Proratio System                    │
└─────────────────────────────────────────────────┘

Proratio Utilities          → Execution & data engine
Proratio Signals       → AI alpha signal generation
Proratio QuantLab      → Backtesting & ML models
Proratio TradeHub      → Strategy orchestration
```

### Module Breakdown

| Module | Purpose | Tech Stack | Status |
|--------|---------|------------|--------|
| **Utilities** | Config, data collection, execution utilities | Freqtrade, CCXT, PostgreSQL | ✅ 95% |
| **Signals** | Multi-LLM analysis, consensus mechanism | OpenAI API, Anthropic API, Gemini API | ✅ 95% |
| **QuantLab** | Strategy backtesting, ML model development | PyTorch, scikit-learn, Jupyter | ✅ 60% |
| **TradeHub** | Multi-strategy coordination, risk management | Streamlit, Custom framework | ✅ 50% |

---

## 🚀 Quick Start

### Option 1: One-Command Startup (Recommended)

```bash
# Single command to start everything
./start.sh
```

This unified script will:
- ✅ Check environment and dependencies
- ✅ Start Docker services (PostgreSQL, Redis)
- ✅ Verify API keys and configuration
- ✅ Check data integrity
- ✅ Start Freqtrade trading bot
- ✅ Launch Streamlit dashboard
- ✅ Display system status and helpful information

**Options:**
- `./start.sh --skip-checks` - Skip environment checks (faster)
- `./start.sh --no-dashboard` - Don't start dashboard
- `./start.sh --help` - Show help

### Option 2: Manual Setup

If you need more control or are setting up for the first time:

#### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Binance account (testnet for development)
- API keys for AI services (OpenAI, Anthropic, Google)

#### Installation

```bash
# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start infrastructure
docker-compose up -d postgres redis

# Initialize database schema
docker exec -i proratio_postgres psql -U proratio -d proratio < proratio_utilities/data/schema.sql

# Install dependencies (use UV for proper environment)
uv pip install -r requirements.txt

# Download historical data (to PostgreSQL)
uv run python scripts/download_historical_data.py

# Export data for Freqtrade (when needed)
uv run python scripts/export_data_for_freqtrade.py
```

> **Important:** Always use `uv run python` to ensure you're using the correct Python environment with all dependencies.

> For detailed setup, data management workflow, and troubleshooting, see [docs/](./docs/) or [docs/index.md](./docs/index.md)

### Configure Trading Parameters

```bash
# View current configuration
python scripts/show_trading_config.py

# Edit configuration (all trading parameters in one file)
# Edit: proratio_utilities/config/trading_config.json

# Validate configuration
python scripts/show_trading_config.py --validate
```

> For configuration guide, see [docs/trading_config_guide.md](./docs/trading_config_guide.md)

### Run Paper Trading

```bash
# Start Freqtrade in dry-run mode
freqtrade trade \
  --strategy ProRatioAdapter \
  --userdir user_data \
  --config proratio_utilities/config/freqtrade/config_dry.json
```

> For complete development workflow, see [docs/roadmap.md](./docs/roadmap.md)

---

## 📊 Usage Examples

### Generate AI Signals

```python
from proratio_signals import SignalOrchestrator

# Initialize with API keys from .env
orchestrator = SignalOrchestrator()

# Generate consensus signal from ChatGPT, Claude, and Gemini
signal = orchestrator.generate_signal(
    pair="BTC/USDT",
    timeframe="1h",
    ohlcv_data=dataframe  # pandas DataFrame with OHLCV data
)

print(f"Direction: {signal.direction}")           # 'long', 'short', 'neutral'
print(f"Confidence: {signal.confidence:.1%}")     # AI confidence (0.0 - 1.0)
print(f"Active Providers: {signal.active_providers}")  # ['claude', 'gemini']
print(f"Reasoning: {signal.combined_reasoning}")  # AI explanations

# Check if signal meets trading threshold
if signal.should_trade():
    print("✓ High-confidence signal - ready to trade")
```

### Run AI-Enhanced Trading Strategy

```bash
# Backtest AI-enhanced strategy vs baseline
python scripts/backtest_ai_strategy.py --timeframe 1h --months 6

# Start paper trading with AI signals
freqtrade trade \
  --strategy AIEnhancedStrategy \
  --userdir user_data \
  --config proratio_utilities/config/freqtrade/config_dry.json
```

### Configure Risk & Position Sizing

```python
from proratio_utilities.config.trading_config import TradingConfig

# Load configuration
config = TradingConfig.load_from_file('proratio_utilities/config/trading_config.json')

# Modify risk parameters
config.risk.max_loss_per_trade_pct = 0.015  # 1.5% max loss
config.position_sizing.method = 'ai_weighted'  # Use AI confidence

# Validate and save
errors = config.validate()
if not errors:
    config.save_to_file('proratio_utilities/config/trading_config.json')
```

### Monitor Dashboard

```bash
streamlit run proratio_tradehub/dashboard/app.py
```

Open http://localhost:8501 in your browser.

---

## 📁 Project Structure

```
proratio/
├── proratio_utilities/          # Execution & data engine
│   ├── config/             # Configuration files (trading_config.json)
│   ├── data/               # Data collectors & loaders
│   ├── execution/          # Order & position management
│   └── utils/              # Logging, alerts
│
├── proratio_signals/       # AI signal generation
│   ├── llm_providers/      # ChatGPT, Claude, Gemini
│   ├── prompts/            # Prompt engineering
│   ├── signal_generators/  # Signal logic
│   └── orchestrator.py     # Multi-AI coordination
│
├── proratio_quantlab/      # Backtesting & ML
│   ├── backtesting/        # Backtest engine
│   ├── ml/                 # ML models
│   ├── research/           # Jupyter notebooks
│   └── analytics/          # Performance metrics
│
├── proratio_tradehub/      # Strategy orchestration
│   ├── strategies/         # Trading strategies
│   ├── orchestration/      # Multi-strategy manager
│   ├── risk/               # Risk management (risk_manager.py, position_sizer.py)
│   └── dashboard/          # Streamlit UI
│
├── user_data/              # Freqtrade data (version controlled)
│   ├── strategies/         # Freqtrade strategy adapters
│   ├── data/               # Market data (gitignored)
│   ├── logs/               # Log files (gitignored)
│   └── db/                 # SQLite databases (gitignored)
│
├── temp_tests/             # Temporary testing directory (gitignored)
│   ├── strategies/         # Test strategies (MeanReversionTest5m.py, etc.)
│   ├── configs/            # Test configurations
│   ├── scripts/            # Test scripts (start_live_test_btc.sh)
│   ├── docs/               # Test documentation
│   └── results/            # Test results (logs, backtest_results, analysis)
│
├── scripts/                # Utility scripts
├── tests/                  # Unit tests (163 tests passing)
└── docs/                   # Documentation (14 active + index)
```

> **Note**: The `temp_tests/` directory contains temporary testing materials used during development. These files are gitignored and should be deleted after testing is complete or promoted to production when validated.

---

## 🧪 Testing

```bash
# Run all tests (163 tests)
pytest

# Run specific module
pytest tests/test_signals/      # AI signal tests (42 tests)
pytest tests/test_quantlab/     # Backtesting & A/B tests (24 tests)
pytest tests/test_tradehub/     # Risk & strategy tests (97 tests)

# With coverage
pytest --cov=proratio_signals --cov=proratio_tradehub --cov=proratio_quantlab --cov-report=html
```

---

## 📚 Documentation

- **[docs/roadmap.md](./docs/roadmap.md)** - Complete implementation plan, weekly progress, and development workflow
- **[CLAUDE.md](./CLAUDE.md)** - Developer guide for Claude Code
- **[docs/quickstart.md](./docs/quickstart.md)** - Quick start guide for new users
- **[docs/backtesting_guide.md](./docs/backtesting_guide.md)** - Complete backtesting guide and results
- **[docs/paper_trading_guide.md](./docs/paper_trading_guide.md)** - Paper trading setup and monitoring
- **[docs/quickstart.md](./docs/quickstart.md)** - Quick setup and getting started guide
- **[docs/troubleshooting.md](./docs/troubleshooting.md)** - Troubleshooting common issues
- **[docs/trading_config_guide.md](./docs/trading_config_guide.md)** - Comprehensive configuration guide
- **[docs/](./docs/)** - Module-specific documentation and guides

---

## ⚠️ Disclaimer

**This software is for educational purposes only. Use at your own risk.**

- Cryptocurrency trading involves substantial risk of loss
- Past performance does not guarantee future results
- Never trade with money you cannot afford to lose
- Always test thoroughly in paper trading before going live
- The authors are not responsible for any financial losses

---

## 📄 License

MIT License - See [LICENSE](./LICENSE) file for details

---

## 🤝 Contributing

This is a personal project, but feedback and suggestions are welcome. Please open an issue for discussion.

---

## 📧 Contact

For questions or support, please refer to:
- Project documentation in `docs/`
- Freqtrade community: https://www.freqtrade.io/
- CCXT documentation: https://docs.ccxt.com/

---

**Built with ❤️ for intelligent crypto trading**
