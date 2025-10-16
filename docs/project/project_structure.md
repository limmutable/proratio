# Proratio Project Structure

**Last Updated**: 2025-10-16
**Version**: 0.9.2

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
│   ├── train_ensemble_model.py   # ML model training
│   ├── start_ml_paper_trading.sh # Paper trading scripts
│   ├── stop_ml_paper_trading.sh
│   ├── monitor_ml_paper_trading.sh
│   └── test_llm_integration.py   # LLM regression test
│
├── 📊 strategies/                # ⭐ NEW: Strategy Registry System (Phase 4.6)
│   ├── registry.json             # Central strategy database
│   ├── active/                   # Production-ready strategies
│   │   ├── a014_hybrid-ml-llm/   # Hybrid ML+LLM (Phase 4.6 validated)
│   │   ├── f662_grid-trading/    # Grid trading (73.7% win rate)
│   │   └── 355c_mean-reversion/  # Mean reversion v2 (56% win rate)
│   ├── experimental/             # Under development
│   ├── archived/                 # Deprecated strategies
│   │   ├── 8f5e_mean-reversion-v1/
│   │   ├── c7f9_freqai/
│   │   └── 6347_ai-enhanced/
│   └── templates/                # Strategy templates
│
├── 🗄️ user_data/                # Freqtrade user directory
│   ├── strategies/               # Freqtrade strategy adapters
│   │   ├── HybridMLLLMStrategy.py
│   │   ├── GridTradingStrategy.py
│   │   └── MeanReversionAdapter.py
│   ├── db/                       # SQLite databases (gitignored)
│   └── data/                     # Market data (gitignored)
│
├── 🤖 models/                    # ⭐ NEW: Trained ML models
│   └── ensemble_model.pkl        # LSTM + LightGBM + XGBoost (2.9MB)
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
│       ├── config_live.json      # Live trading
│       └── config_paper_ml_test.json  # ML paper trading
│
├── data/
│   ├── collectors.py             # CCXT data collection
│   ├── storage.py                # PostgreSQL interface
│   ├── loaders.py                # Data loading utilities
│   └── schema.sql                # Database schema
│
├── execution/
│   ├── freqtrade_wrapper.py      # Freqtrade integration
│   └── order_manager.py          # Order lifecycle
│
└── strategy_registry.py          # ⭐ NEW: Strategy Registry API (Phase 4.6)
```

**Status**: ✅ 100% Complete

---

### 2. proratio_signals/ (AI Alpha Generation)
**Purpose**: Multi-LLM analysis, consensus mechanism, signal scoring

```
proratio_signals/
├── orchestrator.py               # Multi-AI coordination
├── hybrid_predictor.py           # ⭐ NEW: ML+LLM integration (Phase 4.0-4.6)
├── llm_providers/
│   ├── base.py                   # Base provider interface
│   ├── chatgpt.py                # OpenAI GPT-4
│   ├── claude.py                 # Anthropic Claude Sonnet 4
│   └── gemini.py                 # Google Gemini 2.0 Flash
├── prompts/
│   ├── market_analysis_prompt.py
│   └── ... (prompt templates)
└── signal_generators/
    └── ai_signal_generator.py
```

**Status**: ✅ 100% Complete (Phase 4.6 validated)
**Features**: Weighted voting (40/35/25%), dynamic reweighting, failure handling, Hybrid ML+LLM consensus

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
│   ├── ensemble_predictor.py     # Ensemble learning (Phase 3.3)
│   └── feature_engineering.py    # 65+ technical features
│
├── validation/                   # ⭐ NEW: Strategy Validation Framework (Phase 1.4)
│   ├── validate_backtest_results.py
│   └── generate_validation_report.py
│
└── research/
    └── notebooks/                # Jupyter research environment
```

**Status**: ✅ 90% Complete
**Models**: LSTM, LightGBM, XGBoost, Ensemble (stacking), Feature Engineering (65+ indicators)

---

### 4. proratio_tradehub/ (Strategy Orchestration)
**Purpose**: Multi-strategy coordination, portfolio allocation, risk controls

```
proratio_tradehub/
├── strategies/
│   ├── base_strategy.py          # Abstract base class
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
**Strategies**: See [strategies/registry.json](../../strategies/registry.json) for full list (3 active, 3 archived)

---

### 5. proratio_cli/ (Interactive CLI - Phase 4.0)
**Purpose**: Beautiful command-line interface for system management

```
proratio_cli/
├── main.py                       # CLI entry point
├── shell.py                      # Interactive shell mode
├── commands/
│   ├── status.py                 # /status commands
│   ├── strategy.py               # /strategy commands (⭐ Phase 4.6: Registry integration)
│   ├── config.py                 # /config commands
│   ├── data.py                   # /data commands
│   ├── trade.py                  # /trade commands
│   └── help_cmd.py               # /help commands
└── utils/
    ├── checks.py                 # Health checks
    └── display.py                # Rich formatting
```

**Status**: ✅ 100% Complete (Phase 4.6: Strategy Registry integrated)
**Launch**: `./start.sh cli`
**Enhanced Commands**: `/strategy list --archived`, `/strategy show <id>`

---

## 🎯 Development Phases & Module Status

| Phase | Module | Status | Progress |
|-------|--------|--------|----------|
| **1.0** | Utilities | ✅ Complete | 100% |
| **1.1** | Signals | ✅ Complete | 100% |
| **1.2** | QuantLab (Backtesting) | ✅ Complete | 90% |
| **1.2** | TradeHub (Risk) | ✅ Complete | 90% |
| **1.3** | TradeHub (Dashboard) | ✅ Complete | 90% |
| **1.4** | Strategy Validation | ✅ Complete | 100% |
| **2.0** | TradeHub (Strategies) | ✅ Complete | 100% |
| **3.1** | QuantLab (FreqAI) | ✅ Complete | 100% |
| **3.2** | QuantLab (LSTM) | ✅ Complete | 100% |
| **3.3** | QuantLab (Ensemble) | ✅ Complete | 100% |
| **3.5** | Technical Debt | ✅ Complete | 100% |
| **4.0** | Hybrid ML+LLM | ✅ Complete | 100% |
| **4.5** | ML Paper Trading | ✅ Complete | 100% |
| **4.6** | LLM Integration Fix | ✅ Complete | 100% |
| **Registry** | Strategy Registry | ✅ Complete | 100% |
| **4.7** | Confidence Calibration | 🚧 Next | 0% |
| **5-10** | Advanced AI | 📋 Planned | 0% |

---

## 📊 Code Statistics

| Metric | Value |
|--------|-------|
| **Total Lines** | ~14,500+ |
| **Python Files** | 90+ |
| **Tests** | 200+ passing |
| **Modules** | 5 (Utilities, Signals, QuantLab, TradeHub, CLI) |
| **Strategies** | 3 active + 3 archived (tracked in registry) |
| **ML Models** | 4 (LSTM, LightGBM, XGBoost, Ensemble Stacking) |
| **Trained Models** | 1 (ensemble_model.pkl - 2.9MB, trained on 4,386 candles) |
| **Documentation** | 20+ active docs + 10 archived |
| **Phase Progress** | Phase 1-4.6 Complete (92%), Registry Complete |

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

**Last Updated**: 2025-10-16
**Next Review**: After Phase 4.7 completion (Confidence Calibration)

---

## ⭐ Recent Additions (Oct 16, 2025)

### Strategy Registry System
- Central `strategies/registry.json` database tracking all strategies
- Random hash naming convention (`a014`, `f662`, `355c`, etc.)
- Enhanced datetime tracking (created_datetime, last_edited)
- Organized directory structure (active/experimental/archived/templates)
- Python API: `proratio_utilities/strategy_registry.py`
- CLI integration: `/strategy list --archived`, `/strategy show <id>`

### Phase 4.6: LLM Integration Fix
- Fixed `'OHLCVData' object has no attribute 'tail'` error
- Modified `proratio_signals/hybrid_predictor.py`
- Validated with 6-hour paper trading test (0 errors, all LLM providers working)
- Full Hybrid ML+LLM mode now operational

### Active Strategies (from Registry)
1. **a014_hybrid-ml-llm** - Hybrid ML+LLM (Phase 4.6 validated)
2. **f662_grid-trading** - Grid Trading (73.7% win rate)
3. **355c_mean-reversion** - Mean Reversion v2 (56% win rate)

See [roadmap.md](roadmap.md) for complete Phase 4.6 and Registry System details.
