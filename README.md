# Proratio

**AI-Driven Cryptocurrency Trading System**

Proratio [pro-ra-tee-oh] is an intelligent trading system that combines multi-LLM analysis (ChatGPT, Claude, Gemini) with machine learning to trade cryptocurrencies on Binance. This is a personal development project exploring algorithmic trading and AI integration.

**Version**: 1.0.0 (Phase 1-4.7 Complete)

> **📋 Status**: Phase 4.7 Complete ✅ | Confidence Analysis Done | Ready for Phase 4.8 (Extended Paper Trading)!
>
> **🚀 New Users**: See [docs/getting_started.md](./docs/getting_started.md) for step-by-step setup guide (20 minutes)
>
> **🖥️ Fresh Machine**: See [docs/guides/fresh_machine_setup.md](./docs/guides/fresh_machine_setup.md) for complete installation (30 minutes)
>
> For detailed project status and development plans, see [docs/project/roadmap.md](./docs/project/roadmap.md)

---

## What is Proratio?

**Proratio** is an algorithmic trading system that uses artificial intelligence to make cryptocurrency trading decisions. Instead of manually watching charts and placing trades, Proratio automates the entire process: it collects market data, analyzes it using AI, and executes trades automatically on Binance.

### How It Works (In Plain English)

Think of Proratio as having a team of AI analysts working 24/7:

1. **Data Collection**: Proratio constantly monitors Bitcoin and other cryptocurrency prices, volumes, and market trends from Binance.

2. **Multi-AI Analysis**: When a potential trading opportunity appears, Proratio asks three different AI models (ChatGPT, Claude, and Gemini) to analyze the market data. Each AI provides its recommendation: Buy, Sell, or Hold, along with an explanation.

3. **Machine Learning Predictions**: Simultaneously, machine learning models (trained on years of historical price data) predict likely price movements based on statistical patterns.

4. **Consensus Decision**: Proratio combines the AI opinions and ML predictions. If all systems agree with high confidence, it executes a trade. If there's disagreement or low confidence, it waits.

5. **Automated Execution**: When a strong signal emerges, Proratio automatically places orders on Binance, manages positions, and implements stop-losses to limit risk.

6. **Risk Management**: Multiple layers of safety controls ensure no single trade risks more than 2% of capital, and trading halts automatically if losses exceed 10%.

### Why Multi-AI + Machine Learning?

- **AI Language Models** (ChatGPT, Claude, Gemini) understand context and market narrative: news, sentiment, unusual patterns.
- **Machine Learning Models** (LSTM, LightGBM, XGBoost) identify statistical patterns invisible to humans: price cycles, momentum shifts, support/resistance levels.
- **Combined**: When both quantitative (ML) and qualitative (AI) analysis agree, the signal is stronger and more reliable.

### What Makes It Different?

Most trading bots use only technical indicators (RSI, MACD, moving averages). Proratio adds:
- **Multiple AI perspectives** (not just one model)
- **ML ensemble learning** (3 different model types working together)
- **Consensus mechanism** (only trades when AI + ML agree)
- **Adaptive risk** (position size scales with confidence)

### Who Is This For?

Proratio is a **personal development project** for exploring:
- Algorithmic trading strategies
- AI/LLM integration in finance
- Machine learning for time-series prediction
- Risk management frameworks
- Python system architecture

**This is NOT**:
- A commercial product or service
- Financial advice or guaranteed profits
- Suitable for beginners without programming/finance knowledge
- A complete, battle-tested trading system (it's under active development)

**For detailed explanations** of strategies, technical concepts, and architecture, see:
- **[Proratio Concepts Guide](./docs/proratio_concepts.md)** - Complete technical details for finance/analytical audiences
- **[Project Roadmap](./docs/project/roadmap.md)** - Development phases and status
- **[Getting Started Guide](./docs/getting_started.md)** - Setup instructions

---

## 🎯 Key Features

- **Multi-AI Analysis**: Leverages ChatGPT, Claude, and Gemini for market insights
- **Advanced Machine Learning**:
  - LSTM neural networks for time-series prediction
  - Ensemble learning (stacking/blending/voting) combining LSTM + LightGBM + XGBoost
  - 65+ engineered features (technical indicators, momentum, volatility, temporal)
  - ~10-20% improvement over single models with ensemble methods
- **Automated Execution**: Freqtrade-powered trading on Binance (Spot trading)
- **Comprehensive Backtesting**: Walk-forward analysis, strategy validation framework (5-10 min)
- **Risk Management**: 6-layer risk validation with emergency stops and adaptive position sizing
- **Centralized Configuration**: Single JSON file controls all 60+ trading parameters
- **Modular Architecture**: Four independent modules for flexibility and extensibility
- **Multi-Strategy System**: Multiple strategies (Trend, Mean Reversion, Grid, AI-Enhanced) with portfolio allocation
- **Testing**: 186+ passing tests with comprehensive coverage
- **Security**: Automated dependency scanning (pip-audit), API key auditing, pre-commit hooks

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
| **Signals** | Multi-LLM analysis, hybrid ML+LLM prediction | OpenAI API, Anthropic API, Gemini API, PyTorch, LightGBM, XGBoost | ✅ 95% (ML ✅, LLM ✅) |
| **QuantLab** | Backtesting, ML models (LSTM, Ensemble), feature engineering, confidence analysis | PyTorch, LightGBM, XGBoost, scikit-learn, Jupyter | ✅ 90% |
| **TradeHub** | Multi-strategy coordination, risk management, strategy registry | Python, Custom framework | ✅ 60% |

---

## 🚀 Quick Start

> **⭐ New to Proratio?** Follow the complete step-by-step guide: **[docs/getting_started.md](./docs/getting_started.md)** (20 minutes)

### Fast Setup (3 commands)

```bash
# 1. Run automated setup
./scripts/setup.sh

# 2. Configure API keys
cp .env.example .env  # Edit with your keys

# 3. Launch CLI (default)
./start.sh
```

### Usage Examples

```bash
# Launch CLI (default - no arguments needed)
./start.sh

# Or explicitly use CLI mode
./start.sh
```

**Direct Commands** (no interactive prompt):
```bash
./start.sh status all           # System status
./start.sh strategy list        # List strategies
./start.sh strategy validate AIEnhancedStrategy  # Validate strategy
./start.sh help validate        # Validation guide
```

**Interactive Mode** (launches prompt):
```bash
./start.sh                      # Enter interactive CLI
# Then use commands with / prefix:
proratio> /help                 # Show all commands
proratio> /status quick         # Quick system check
proratio> /strategy list        # List all strategies
proratio> /quit                 # Exit CLI
```

**Features:**
- 🎨 Beautiful Rich terminal output with colors and tables
- 🔍 Real-time system health checks on startup
- 💬 Both direct commands AND interactive prompt mode
- ❓ Built-in help system (`/help <command>` or `./start.sh help <topic>`)
- ✅ Strategy validation framework (5-10 min vs 5-7 days paper trading)
- 🚪 Graceful shutdown (`/quit` or `/exit`)

See [CLI Guide](./docs/cli_guide.md) for complete reference

> **⚙️ Advanced Setup**: For manual installation and configuration options, see [Getting Started Guide - Advanced Setup](./docs/getting_started.md#advanced-manual-setup)

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

### Train Machine Learning Models

```bash
# Train LSTM model for price prediction
python scripts/train_lstm_model.py --pair BTC/USDT --epochs 100

# Train ensemble model (LSTM + LightGBM + XGBoost)
python scripts/example_ensemble_usage.py

# Example output:
# Ensemble RMSE: 1.726914
# → 19.66% improvement over best base model
```

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
│   ├── ml/                 # ML models (LSTM, Ensemble, FreqAI), feature engineering (80+ features)
│   │   ├── lstm_predictor.py          # LSTM/GRU neural networks
│   │   ├── lstm_data_pipeline.py      # Time-series preprocessing
│   │   ├── ensemble_predictor.py      # Ensemble learning (stacking/blending/voting)
│   │   └── feature_engineering.py     # 80+ technical indicators
│   ├── ab_testing/         # A/B testing framework
│   ├── research/           # Jupyter notebooks
│   └── analytics/          # Performance metrics
│
├── proratio_tradehub/      # Strategy orchestration
│   ├── strategies/         # Trading strategies
│   ├── orchestration/      # Multi-strategy manager
│   ├── risk/               # Risk management (risk_manager.py, position_sizer.py)
│   └── dashboard/          # Monitoring UI
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
# Run all tests (186+ tests)
pytest

# Run specific module
pytest tests/test_signals/      # AI signal tests (42 tests)
pytest tests/test_quantlab/     # ML, backtesting & A/B tests (52 tests)
pytest tests/test_tradehub/     # Risk & strategy tests (97 tests)

# With coverage
pytest --cov=proratio_signals --cov=proratio_tradehub --cov=proratio_quantlab --cov-report=html
```

---

## 📚 Documentation

> **📖 Documentation Index**: See [docs/index.md](./docs/index.md) for complete navigation

### Core Documentation
- **[Proratio Concepts](./docs/proratio_concepts.md)** - ⭐ Technical details for finance/analytical audiences
- **[Getting Started](./docs/getting_started.md)** - Quick setup guide (20 minutes)
- **[Fresh Machine Setup](./docs/guides/fresh_machine_setup.md)** - Complete installation for new machines (30 minutes)
- **[Project Roadmap](./docs/project/roadmap.md)** - Complete development roadmap and Phase 4-10 plans
- **[CLAUDE.md](./CLAUDE.md)** - Developer guide for Claude Code

### Project Management (docs/project/)
- **[roadmap.md](./docs/project/roadmap.md)** - Development phases and timeline
- **[project_progress.md](./docs/project/project_progress.md)** - Current status and metrics
- **[advanced_ai_strategies.md](./docs/project/advanced_ai_strategies.md)** - Phase 4-10 AI strategies (2000+ lines)
- **[ml_paper_trading_analysis_20251015.md](./docs/project/ml_paper_trading_analysis_20251015.md)** - Phase 4.5 paper trading analysis
- **[phase4_integration_status_20251015.md](./docs/project/phase4_integration_status_20251015.md)** - Phase 4 status
- **[technical_debt_gemini_review.md](./docs/project/technical_debt_gemini_review.md)** - Code review and tech debt
- **[security_scanning.md](./docs/project/security_scanning.md)** - Security scanning procedures

### User Guides (docs/guides/)
- **[strategy_development_guide.md](./docs/guides/strategy_development_guide.md)** - Strategy development patterns
- **[paper_trading_guide.md](./docs/guides/paper_trading_guide.md)** - Paper trading setup
- **[ml_paper_trading_guide.md](./docs/guides/ml_paper_trading_guide.md)** - ML paper trading guide (400+ lines)
- **[configuration_guide.md](./docs/guides/configuration_guide.md)** - Complete configuration guide
- **[validation_framework_guide.md](./docs/guides/validation_framework_guide.md)** - Strategy validation (5-10 min)

### Technical Reference (docs/reference/)
- **[freqai_guide.md](./docs/reference/freqai_guide.md)** - Machine learning with FreqAI
- **[lstm_implementation.md](./docs/reference/lstm_implementation.md)** - LSTM neural networks
- **[ensemble_implementation.md](./docs/reference/ensemble_implementation.md)** - Ensemble learning
- **[backtesting_guide.md](./docs/reference/backtesting_guide.md)** - Backtesting guide

---

## ⚠️ Disclaimer

**This software is for educational and personal development purposes only. Use at your own risk.**

- Cryptocurrency trading involves substantial risk of loss
- Past performance does not guarantee future results
- Never trade with money you cannot afford to lose
- Always test thoroughly in paper trading before going live
- This is a personal development project, not a commercial product
- The authors are not responsible for any financial losses
- Not financial advice

---

## 📄 License

MIT License - See [LICENSE](./LICENSE) file for details

---

## 📧 Contact

For questions or support, please refer to:
- Project documentation in `docs/`
- Freqtrade community: https://www.freqtrade.io/
- CCXT documentation: https://docs.ccxt.com/

---

**Built with ❤️ for intelligent crypto trading**
