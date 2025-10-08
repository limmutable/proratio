# Proratio Project Structure

## Overview

Clean, organized structure separating production code from temporary testing.

**Last Updated**: 2025-10-08

---

## Directory Tree

```
proratio/
│
├── 📄 README.md                    # Project overview
├── 📄 CLAUDE.md                    # AI assistant instructions
├── 📄 PLAN.md                      # Implementation roadmap
├── 📄 CLEANUP_PLAN.md              # Cleanup strategy
├── 📄 CLEANUP_COMPLETE.md          # Cleanup summary
├── 📄 PROJECT_STRUCTURE.md         # This file
├── 📄 .gitignore                   # Git exclusions
├── 📄 requirements.txt             # Python dependencies
├── 📄 docker-compose.yml           # Docker services
│
├── 📁 docs/                        # Documentation
│   ├── backtesting_guide.md
│   ├── 3hour_test_guide.md
│   └── ... (permanent docs)
│
├── 📁 tests/                       # Unit Tests (pytest)
│   ├── test_utilities/
│   ├── test_signals/
│   ├── test_tradehub/
│   └── test_quantlab/
│
├── 🧪 temp_tests/                  # TEMPORARY Testing (gitignored)
│   ├── README.md                   # Testing guide
│   ├── strategies/                 # Test strategies
│   │   ├── MeanReversionTest5m.py
│   │   ├── MeanReversionTest.py
│   │   └── SimpleTestStrategy.py
│   ├── configs/                    # Test configurations
│   │   └── config_live_btc_test.json
│   ├── scripts/                    # Test scripts
│   │   ├── start_live_test_btc.sh
│   │   ├── print_test_summary.py
│   │   ├── analyze_live_test_period.py
│   │   └── sensitivity_analysis.py
│   ├── docs/                       # Test documentation
│   │   ├── LIVE_TEST_README.md
│   │   ├── live_test_analysis_20251008.md
│   │   ├── enhanced_logging_summary.md
│   │   ├── quiet_mode_summary.md
│   │   └── DNS_FIX_README.md
│   └── results/                    # Test results
│       ├── logs/                   # Live test logs (4 files)
│       ├── backtest_results/       # Backtest outputs (16 files)
│       └── analysis/               # Analysis outputs
│
├── 📁 user_data/                   # Freqtrade User Data
│   ├── strategies/                 # Production strategies (empty - ready)
│   ├── data/                       # Market data (gitignored)
│   │   └── binance/
│   │       ├── BTC_USDT-4h.feather
│   │       ├── BTC_USDT-5m.feather
│   │       └── ETH_USDT-*.feather
│   ├── logs/                       # Production logs (gitignored)
│   ├── backtest_results/           # Production results (gitignored)
│   └── db/                         # Databases (gitignored) ✨ NEW
│       ├── tradesv3.dryrun.sqlite
│       ├── tradesv3.dryrun.sqlite-shm
│       ├── tradesv3.dryrun.sqlite-wal
│       └── tradesv3_dryrun.sqlite
│
├── 📁 proratio_utilities/          # Core Utilities Module
│   ├── __init__.py
│   ├── config/
│   │   ├── settings.py             # Centralized config
│   │   └── freqtrade/
│   │       ├── config_dry.json
│   │       └── config_backtest.json
│   ├── data/
│   │   ├── collectors.py           # Data collection
│   │   ├── loaders.py              # Data loading
│   │   └── storage.py              # Database storage
│   └── execution/
│       ├── freqtrade_wrapper.py
│       └── order_manager.py
│
├── 📁 proratio_signals/            # Signal Generation Module
│   ├── __init__.py
│   ├── orchestrator.py             # Multi-AI coordination
│   ├── llm_providers/
│   │   ├── base_provider.py
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   └── gemini_provider.py
│   ├── signal_generators/
│   │   ├── ai_signal_generator.py
│   │   └── base_signal_generator.py
│   └── prompts/
│       └── analysis_prompts.py
│
├── 📁 proratio_tradehub/           # Strategy Orchestration Module
│   ├── __init__.py
│   ├── strategies/                 # Production Strategy Classes
│   │   ├── __init__.py
│   │   ├── base_strategy.py
│   │   ├── mean_reversion.py       # 🎯 Production strategy
│   │   └── trend_following.py
│   ├── orchestration/
│   │   └── strategy_manager.py
│   ├── risk/
│   │   ├── position_sizer.py
│   │   └── risk_limits.py
│   └── dashboard/
│       └── app.py                  # Streamlit dashboard
│
├── 📁 proratio_quantlab/           # Backtesting & ML Module
│   ├── __init__.py
│   ├── backtesting/
│   │   ├── backtest_engine.py
│   │   └── performance_metrics.py
│   ├── ml/
│   │   └── (future ML models)
│   └── research/
│       └── notebooks/              # Jupyter notebooks
│
└── 📁 scripts/                     # Production Scripts
    ├── download_historical_data.py # Data download
    ├── setup.sh                    # Project setup
    ├── diagnose_mean_reversion.py  # Diagnostics
    └── ... (production utilities)
```

---

## Key Directories

### Production Code (Version Controlled)

| Directory | Purpose | Git |
|-----------|---------|-----|
| `proratio_*/` | Core modules | ✅ Yes |
| `user_data/strategies/` | Production strategies | ✅ Yes (currently empty) |
| `scripts/` | Production utilities | ✅ Yes |
| `docs/` | Permanent documentation | ✅ Yes |
| `tests/` | Unit tests (pytest) | ✅ Yes |

### Temporary Testing (Excluded from Git)

| Directory | Purpose | Git |
|-----------|---------|-----|
| `temp_tests/` | **ALL testing files** | ❌ No (gitignored) |
| `user_data/data/` | Market data | ❌ No (gitignored) |
| `user_data/db/` | Databases | ❌ No (gitignored) |
| `user_data/logs/` | Logs | ❌ No (gitignored) |
| `user_data/backtest_results/` | Results | ❌ No (gitignored) |

---

## File Counts

### temp_tests/ (Temporary Testing)
- **Strategies**: 3 files (MeanReversionTest*.py, SimpleTestStrategy.py)
- **Configs**: 1 file (config_live_btc_test.json)
- **Scripts**: 4 files (start script, analysis scripts)
- **Docs**: 5 files (READMEs, analysis reports)
- **Results**: 20+ files (logs, backtest results)

**Total**: 30+ temporary test files

### Production Modules
- **proratio_utilities**: 10+ files
- **proratio_signals**: 8+ files
- **proratio_tradehub**: 8+ files
- **proratio_quantlab**: 5+ files

**Total**: 30+ production files

---

## Workflows

### Testing Workflow
```
1. Create → temp_tests/strategies/
2. Configure → temp_tests/configs/
3. Test → temp_tests/scripts/
4. Analyze → temp_tests/results/
5. Document → temp_tests/docs/
```

### Production Promotion
```
1. Validate in temp_tests/
2. Archive temp_tests/ (optional)
3. Move to proratio_tradehub/strategies/
4. Create Freqtrade adapter in user_data/strategies/
5. Delete temp_tests/ (or keep for reference)
```

---

## Quick Navigation

### To run tests:
```bash
./temp_tests/scripts/start_live_test_btc.sh
```

### To view test docs:
```bash
cat temp_tests/docs/LIVE_TEST_README.md
```

### To check production strategies:
```bash
ls proratio_tradehub/strategies/
```

### To see test results:
```bash
ls temp_tests/results/logs/
ls temp_tests/results/backtest_results/
```

---

## Clean Structure Benefits

✅ **Clear Separation**: Production vs. testing
✅ **Easy Cleanup**: Delete `temp_tests/` when done
✅ **Git Clean**: Only production code in version control
✅ **Scalable**: Same pattern for all future strategies
✅ **Organized**: Everything has a logical home

---

**Structure Version**: 2.0 (after cleanup)
**Last Updated**: 2025-10-08
**Changes**: Reorganized to separate temp testing from production
