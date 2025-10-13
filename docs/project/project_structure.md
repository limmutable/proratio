# Proratio Project Structure

**Last Updated**: 2025-10-12
**Version**: 0.8.0

> **📋 Roadmap**: [roadmap.md](roadmap.md) | **📖 Documentation**: [../index.md](../index.md)

---

## 📁 Directory Organization

```
proratio/
├── 📄 Root Files
│   ├── README.md                 # Project overview
│   ├── CLAUDE.md                 # AI assistant instructions
│   ├── start.sh                  # Unified startup script (CLI/dashboard)
│   ├── requirements.txt          # Python dependencies
│   └── docker-compose.yml        # Docker services (PostgreSQL, Redis)
│
├── 📚 docs/                      # Documentation (reorganized Oct 2025)
│   ├── getting_started.md        # ⭐ 15-min setup guide
│   ├── index.md                  # Documentation index
│   ├── troubleshooting.md        # Common issues
│   │
│   ├── guides/                   # User guides
│   │   ├── paper_trading_guide.md
│   │   ├── strategy_development_guide.md
│   │   ├── configuration_guide.md
│   │   ├── dashboard_guide.md
│   │   └── data_management_workflow.md
│   │
│   ├── reference/                # Technical reference
│   │   ├── backtesting_guide.md
│   │   ├── freqai_guide.md
│   │   ├── lstm_implementation.md
│   │   └── ensemble_implementation.md
│   │
│   ├── project/                  # Project management
│   │   ├── roadmap.md            # ⭐ Phase 1-12 development plan
│   │   ├── advanced_ai_strategies.md  # ⭐ Phase 4-10 AI strategies
│   │   ├── project_progress.md   # Current status
│   │   ├── project_structure.md  # This file
│   │   └── file_naming_standards.md
│   │
│   └── obsolete/                 # Archived documentation
│
├── 🧪 tests/                     # Unit tests (pytest)
│   ├── test_utilities/
│   ├── test_signals/
│   ├── test_tradehub/
│   └── test_quantlab/
│
├── 🔧 scripts/                   # Utility scripts
│   ├── setup.sh                  # Initial setup
│   ├── download_historical_data.py
│   └── backtest_phase2_strategies.py
│
├── 🗄️ user_data/                # Freqtrade user directory
│   ├── strategies/               # Trading strategies
│   │   ├── AIEnhancedStrategy.py
│   │   ├── MeanReversionStrategy.py
│   │   └── GridTradingStrategy.py
│   ├── db/                       # SQLite databases (gitignored)
│   │   └── tradesv3.dryrun.sqlite
│   └── data/                     # Market data (gitignored)
│
└── 📦 Proratio Modules
    ├── proratio_utilities/       # Execution engine & data
    ├── proratio_signals/         # AI signal generation
    ├── proratio_quantlab/        # Backtesting & ML
    ├── proratio_tradehub/        # Strategy orchestration
    └── proratio_cli/             # Interactive CLI (Phase 4.0)
```

---

## 🏗️ Module Architecture

### 1. proratio_utilities/ (Execution & Data)
**Purpose**: Exchange connectivity, data collection, order execution

```
proratio_utilities/
├── config/
│   ├── settings.py               # Environment config
│   ├── trading_config.json       # Trading parameters
│   └── freqtrade/                # Freqtrade configs
│       ├── config_dry.json       # Paper trading
│       └── config_live.json      # Live trading
│
├── data/
│   ├── collectors.py             # CCXT data collection
│   ├── storage.py                # PostgreSQL interface
│   ├── loaders.py                # Data loading utilities
│   └── schema.sql                # Database schema
│
└── execution/
    ├── freqtrade_wrapper.py      # Freqtrade integration
    └── order_manager.py          # Order lifecycle
```

**Status**: ✅ 100% Complete

---

### 2. proratio_signals/ (AI Alpha Generation)
**Purpose**: Multi-LLM analysis, consensus mechanism, signal scoring

```
proratio_signals/
├── orchestrator.py               # Multi-AI coordination
├── llm_providers/
│   ├── base.py                   # Base provider interface
│   ├── chatgpt.py                # OpenAI GPT-5 Nano
│   ├── claude.py                 # Anthropic Claude Sonnet 4
│   └── gemini.py                 # Google Gemini 2.0 Flash
├── prompts/
│   ├── market_analysis_prompt.py
│   └── ... (prompt templates)
└── signal_generators/
    └── ai_signal_generator.py
```

**Status**: ✅ 100% Complete
**Features**: Weighted voting (40/35/25%), dynamic reweighting, failure handling

---

### 3. proratio_quantlab/ (Backtesting & ML)
**Purpose**: Strategy backtesting, ML model training, performance analytics

```
proratio_quantlab/
├── backtesting/
│   └── backtest_engine.py        # Freqtrade backtest wrapper
│
├── ab_testing/
│   └── strategy_comparison.py    # Statistical A/B testing
│
├── ml/
│   ├── freqai/                   # FreqAI integration (Phase 3.1)
│   ├── lstm_predictor.py         # LSTM models (Phase 3.2)
│   └── ensemble_predictor.py     # Ensemble learning (Phase 3.3)
│
└── research/
    └── notebooks/                # Jupyter research environment
```

**Status**: ✅ 85% Complete
**Models**: LSTM, LightGBM, XGBoost, CatBoost, Ensemble

---

### 4. proratio_tradehub/ (Strategy Orchestration)
**Purpose**: Multi-strategy coordination, portfolio allocation, risk controls

```
proratio_tradehub/
├── strategies/
│   ├── trend_following.py        # AI-enhanced trend
│   ├── mean_reversion.py         # RSI + Bollinger Bands
│   └── grid_trading.py           # Geometric/arithmetic grids
│
├── orchestration/
│   ├── strategy_manager.py       # Strategy lifecycle
│   └── portfolio_manager.py      # Capital allocation
│
├── risk/
│   ├── risk_manager.py           # 6-layer validation
│   └── position_sizer.py         # 5 sizing methods
│
└── dashboard/
    ├── app.py                    # Streamlit dashboard
    ├── data_fetcher.py
    └── system_status.py
```

**Status**: ✅ 90% Complete
**Strategies**: 3 base + AI-enhanced

---

### 5. proratio_cli/ (Interactive CLI - Phase 4.0)
**Purpose**: Beautiful command-line interface for system management

```
proratio_cli/
├── main.py                       # CLI entry point
├── shell.py                      # Interactive shell mode
├── commands/
│   ├── status.py                 # /status commands
│   ├── strategy.py               # /strategy commands
│   ├── config.py                 # /config commands
│   ├── data.py                   # /data commands
│   └── trade.py                  # /trade commands
└── utils/
    ├── checks.py                 # Health checks
    └── display.py                # Rich formatting
```

**Status**: ✅ 100% Complete (Oct 11, 2025)
**Launch**: `./start.sh cli`

---

## 🎯 Development Phases & Module Status

| Phase | Module | Status | Progress |
|-------|--------|--------|----------|
| **1.0** | Utilities | ✅ Complete | 100% |
| **1.1** | Signals | ✅ Complete | 100% |
| **1.2** | QuantLab (Backtesting) | ✅ Complete | 60% |
| **1.2** | TradeHub (Risk) | ✅ Complete | 80% |
| **1.3** | TradeHub (Dashboard) | ✅ Complete | 90% |
| **1.4** | Paper Trading | 🚧 In Progress | 0% |
| **2.0** | TradeHub (Strategies) | ✅ Complete | 100% |
| **3.1** | QuantLab (FreqAI) | ✅ Complete | 100% |
| **3.2** | QuantLab (LSTM) | ✅ Complete | 100% |
| **3.3** | QuantLab (Ensemble) | ✅ Complete | 100% |
| **4.0** | CLI | ✅ Complete | 100% |
| **4-10** | Advanced AI | 📋 Planned | 0% |

---

## 📊 Code Statistics

| Metric | Value |
|--------|-------|
| **Total Lines** | ~12,600 |
| **Python Files** | 80+ |
| **Tests** | 186+ passing |
| **Modules** | 5 (Utilities, Signals, QuantLab, TradeHub, CLI) |
| **Strategies** | 3 base + AI-enhanced |
| **ML Models** | 4 (LSTM, LightGBM, XGBoost, Ensemble) |
| **Documentation** | 16 active docs + 10 archived |

---

## 🗂️ File Naming Conventions

See [file_naming_standards.md](file_naming_standards.md) for complete guidelines.

**Quick Reference**:
- **Root docs**: UPPERCASE (README.md, CLAUDE.md)
- **Python files**: lowercase_with_underscores (data_loader.py)
- **User docs**: lowercase_with_underscores (getting_started.md)
- **Snapshots**: lowercase_YYYYMMDD (status_20251012.md)
- **Output files**: lowercase_YYYYMMDD_HHMMSS (report_20251012_143000.xlsx)

---

## 🚀 Quick Navigation

### For Traders
- Setup: [../getting_started.md](../getting_started.md)
- CLI: `./start.sh cli`
- Dashboard: `streamlit run proratio_tradehub/dashboard/app.py`

### For Developers
- Architecture: See module sections above
- Roadmap: [roadmap.md](roadmap.md)
- Advanced AI: [advanced_ai_strategies.md](advanced_ai_strategies.md)

### For Contributors
- Standards: [file_naming_standards.md](file_naming_standards.md)
- Tests: `pytest tests/`
- Documentation: [../index.md](../index.md)

---

**Last Updated**: 2025-10-12
**Next Review**: After Phase 1.4 completion
