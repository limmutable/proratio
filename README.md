# Proratio

**AI-Driven Cryptocurrency Trading System**

Proratio is an intelligent trading system that combines multi-LLM analysis (ChatGPT, Claude, Gemini) with automated execution on Binance. Designed for low-frequency, high-conviction trading with comprehensive backtesting and risk management.

**Version**: 0.1.0 (MVP Development - Week 1 Complete)

> For detailed project status, weekly progress, and development plans, see [PLAN.md](./PLAN.md)

---

## 🎯 Key Features

- **Multi-AI Analysis**: Leverages ChatGPT, Claude, and Gemini for market insights
- **Automated Execution**: Freqtrade-powered trading on Binance (Spot, Futures, Options)
- **Comprehensive Backtesting**: Rigorous strategy validation before deployment
- **Risk Management**: Built-in position sizing, drawdown control, and stop-losses
- **Modular Architecture**: Four independent modules for flexibility and extensibility
- **Real-time Dashboard**: Streamlit-based monitoring and control interface

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              Proratio System                    │
└─────────────────────────────────────────────────┘

Proratio Core          → Execution & data engine
Proratio Signals       → AI alpha signal generation
Proratio QuantLab      → Backtesting & ML models
Proratio TradeHub      → Strategy orchestration
```

### Module Breakdown

| Module | Purpose | Tech Stack |
|--------|---------|------------|
| **Core** | Exchange connectivity, data collection, order execution | Freqtrade, CCXT, PostgreSQL |
| **Signals** | Multi-LLM analysis, consensus mechanism | OpenAI API, Anthropic API, Gemini API |
| **QuantLab** | Strategy backtesting, ML model development | PyTorch, scikit-learn, Jupyter |
| **TradeHub** | Multi-strategy coordination, risk management | Streamlit, Custom framework |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Binance account (testnet for development)
- API keys for AI services (OpenAI, Anthropic, Google)

### Installation

```bash
# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start infrastructure
docker-compose up -d postgres redis

# Install dependencies
pip install -r requirements.txt

# Download historical data (to PostgreSQL)
python scripts/download_historical_data.py

# Export data for Freqtrade (when needed)
python scripts/export_data_for_freqtrade.py
```

> For detailed setup, data management workflow, and troubleshooting, see [docs/](./docs/)

### Run Paper Trading

```bash
# Start Freqtrade in dry-run mode
freqtrade trade \
  --strategy ProRatioAdapter \
  --userdir user_data \
  --config proratio_core/config/freqtrade/config_dry.json
```

> For complete development workflow, see [PLAN.md](./PLAN.md)

---

## 📊 Usage Examples

### Generate AI Signals

```python
from proratio_signals import SignalOrchestrator

orchestrator = SignalOrchestrator()
signal = orchestrator.generate_signal(pair="BTC/USDT")

print(f"Direction: {signal.direction}")     # 'long', 'short', 'neutral'
print(f"Confidence: {signal.confidence}")   # 0.0 - 1.0
print(f"Reasoning: {signal.reasoning}")     # AI explanations
```

### Backtest a Strategy

```python
from proratio_quantlab.backtesting import BacktestEngine

engine = BacktestEngine()
results = engine.backtest_strategy(
    strategy_class=TrendFollowingStrategy,
    start_date='2023-01-01',
    end_date='2024-01-01',
    pairs=['BTC/USDT', 'ETH/USDT']
)

print(f"Sharpe Ratio: {results.sharpe_ratio}")
print(f"Max Drawdown: {results.max_drawdown}")
print(f"Total Return: {results.total_return}")
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
├── proratio_core/          # Execution & data engine
│   ├── config/             # Configuration files
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
│   ├── risk/               # Risk management
│   └── dashboard/          # Streamlit UI
│
├── user_data/              # Freqtrade data (volume mount)
│   ├── strategies/         # Freqtrade strategy adapters
│   ├── data/               # Market data
│   └── logs/               # Log files
│
├── scripts/                # Utility scripts
├── tests/                  # Unit tests
└── docs/                   # Documentation
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific module
pytest tests/test_signals/

# With coverage
pytest --cov=proratio_signals --cov-report=html
```

---

## 📚 Documentation

- **[PLAN.md](./PLAN.md)** - Complete implementation plan, weekly progress, and development workflow
- **[CLAUDE.md](./CLAUDE.md)** - Developer guide for Claude Code
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
