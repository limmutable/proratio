# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Proratio** is an AI-driven cryptocurrency trading system for Binance that combines multi-LLM analysis (ChatGPT, Claude, Gemini) with automated strategy execution. The system is designed for low-frequency trading (1-2 manual trades per week) with automated execution based on AI consensus signals.

## Architecture

Proratio follows a modular architecture with four main components:

### 1. **Proratio Utilities** (`proratio_utilities/`)
Execution engine and data infrastructure
- **Purpose**: Exchange connectivity, data collection, order execution
- **Tech**: Freqtrade (execution), CCXT (data), PostgreSQL (storage)
- **Key files**:
  - `data/collectors.py` - Market data collection
  - `execution/freqtrade_wrapper.py` - Freqtrade integration
  - `execution/order_manager.py` - Order lifecycle management

### 2. **Proratio Signals** (`proratio_signals/`)
AI alpha signal generation
- **Purpose**: Multi-LLM analysis, consensus mechanism, signal scoring
- **Tech**: OpenAI API (ChatGPT-4), Anthropic API (Claude), Google Gemini API
- **Key files**:
  - `orchestrator.py` - Multi-AI coordination
  - `llm_providers/` - Individual LLM integrations
  - `prompts/` - Prompt engineering templates
  - `signal_generators/ai_signal_generator.py` - Signal generation

### 3. **Proratio QuantLab** (`proratio_quantlab/`)
Backtesting and model development
- **Purpose**: Strategy backtesting, ML model training, performance analytics
- **Tech**: Freqtrade backtesting, PyTorch, scikit-learn, Jupyter
- **Key files**:
  - `backtesting/backtest_engine.py` - Backtesting wrapper
  - `ml/` - Machine learning models
  - `research/notebooks/` - Jupyter research environment

### 4. **Proratio TradeHub** (`proratio_tradehub/`)
Strategy orchestration and risk management
- **Purpose**: Multi-strategy coordination, portfolio allocation, risk controls
- **Tech**: Custom strategy framework, Streamlit dashboard
- **Key files**:
  - `strategies/` - Trading strategy implementations
  - `orchestration/strategy_manager.py` - Strategy lifecycle
  - `risk/position_sizer.py` - Position sizing logic
  - `dashboard/app.py` - Monitoring dashboard

## Data Flow

```
Utilities (data) � Signals (AI analysis) � TradeHub (strategy) � Utilities (execution)
                                            �
                                    QuantLab (analytics)
```

## Common Commands

### Quick Start

```bash
# Launch interactive CLI shell (recommended for most tasks)
./start.sh cli

# This will:
# 1. Initialize system and run health checks
# 2. Display system status
# 3. Launch interactive prompt: proratio>
# 4. Wait for commands with / prefix

# Start full trading system (bot + dashboard)
./start.sh
```

### Interactive CLI Commands

All commands in the shell must start with `/` prefix:

```bash
# In the interactive shell (proratio>):

# Core commands
/help                        # Show all commands
/help <command>              # Detailed help
/clear                       # Clear screen
/quit or /exit               # Exit CLI

# System status
/status                      # Complete health check
/status quick                # Quick check
/status providers            # LLM provider status

# Strategy management
/strategy list               # List all strategies
/strategy show <name>        # Show strategy code
/strategy backtest <name>    # Run backtest

# Data management
/data download               # Download historical data
/data status                 # Check data availability

# Trading operations
/trade start                 # Start paper trading
/trade stop                  # Stop trading bot
/trade monitor               # Monitor trading activity

# Configuration
/config show                 # Show all config
/config show risk            # Show specific section
/config set <key> <value>    # Set config value
```

### Setup & Installation
```bash
# Initial setup (usually handled by ./start.sh automatically)
./scripts/setup.sh

# Install dependencies
pip install -r requirements.txt

# Start infrastructure (PostgreSQL, Redis)
docker-compose up -d postgres redis

# Copy environment template
cp .env.example .env
# Then edit .env with your API keys
```

### Freqtrade Operations
```bash
# Download historical data
freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT ETH/USDT \
  --timeframe 4h 1h \
  --days 180 \
  --userdir user_data

# Run backtest
freqtrade backtesting \
  --strategy ProRatioAdapter \
  --timeframe 4h \
  --userdir user_data \
  --config proratio_utilities/config/freqtrade/config_dry.json

# Start dry-run (paper trading)
freqtrade trade \
  --strategy ProRatioAdapter \
  --userdir user_data \
  --config proratio_utilities/config/freqtrade/config_dry.json

# Hyperparameter optimization
freqtrade hyperopt \
  --strategy ProRatioAdapter \
  --hyperopt-loss SharpeHyperOptLoss \
  --epochs 100 \
  --userdir user_data
```

### Testing
```bash
# Run all tests
pytest

# Run specific module tests
pytest tests/test_signals/

# Run with coverage
pytest --cov=proratio_signals --cov-report=html
```

### Development Workflows
```bash
# Start Jupyter Lab for research
jupyter lab proratio_quantlab/research/notebooks/

# Run AI signal analysis (manual)
python -m proratio_signals.orchestrator --pair BTC/USDT

# Generate weekly performance report
python scripts/weekly_analysis.py

# Start dashboard
streamlit run proratio_tradehub/dashboard/app.py
```

## Development Guidelines

### Module Interaction Patterns

**1. Cross-module imports should use absolute imports:**
```python
# Good
from proratio_signals.signal_generators import AISignalGenerator
from proratio_utilities.data.loaders import DataLoader

# Bad
from ..signals.signal_generators import AISignalGenerator
```

**2. Each module exposes a clean API via `__init__.py`:**
```python
# proratio_signals/__init__.py
from .orchestrator import SignalOrchestrator
from .signal_generators.ai_signal_generator import AISignalGenerator

__all__ = ['SignalOrchestrator', 'AISignalGenerator']
```

**3. Configuration is centralized in `proratio_utilities/config/settings.py`:**
```python
from proratio_utilities.config.settings import get_settings

settings = get_settings()  # Loads from .env
api_key = settings.openai_api_key
```

### AI Signal Integration

Signals flow from **Proratio Signals** to **Freqtrade strategies** via the `ProRatioAdapter` strategy in `user_data/strategies/`.

**Example signal generation:**
```python
from proratio_signals import SignalOrchestrator

orchestrator = SignalOrchestrator()
signal = orchestrator.generate_signal(pair="BTC/USDT")
# Signal = {direction: 'long', confidence: 0.78, reasoning: {...}}
```

**Example strategy consumption:**
```python
# In user_data/strategies/ProRatioAdapter.py
from proratio_signals import SignalOrchestrator

class ProRatioAdapter(IStrategy):
    def populate_entry_trend(self, dataframe, metadata):
        signal = self.orchestrator.generate_signal(metadata['pair'])
        if signal.confidence > 0.6 and signal.direction == 'long':
            dataframe.loc[:, 'enter_long'] = 1
        return dataframe
```

### Freqtrade Strategy Development

Strategies live in `user_data/strategies/` and follow Freqtrade's strategy interface:

**Key methods:**
- `populate_indicators()` - Add technical indicators
- `populate_entry_trend()` - Define entry conditions
- `populate_exit_trend()` - Define exit conditions
- `custom_stoploss()` - Dynamic stop-loss logic (optional)

**Freqtrade documentation:** https://www.freqtrade.io/en/stable/strategy-customization/

### Risk Management Rules

**Hard limits enforced in code:**
- Max loss per trade: 2% of portfolio
- Max drawdown: 10% � halt trading
- Max concurrent positions: 2-3
- Position sizing: 5% base � AI confidence score

**Located in:** `proratio_tradehub/risk/risk_limits.py`

### Backtesting Best Practices

**Always backtest before deploying:**
```python
from proratio_quantlab.backtesting import BacktestEngine

engine = BacktestEngine()
results = engine.backtest_strategy(
    strategy_class=TrendFollowingStrategy,
    start_date='2023-01-01',
    end_date='2024-01-01',
    pairs=['BTC/USDT', 'ETH/USDT']
)

# Validate: Sharpe > 1.5, Max Drawdown < 15%
assert results.sharpe_ratio > 1.5
assert results.max_drawdown < 0.15
```

## Security & API Keys

**CRITICAL: Never commit secrets!**

- All API keys go in `.env` (gitignored)
- Use read-only or trade-only API keys (no withdrawal permissions)
- Enable IP whitelisting on Binance API settings
- Enable 2FA on exchange account
- Start with Binance **testnet** before using mainnet

**API key permissions (Binance):**
-  Enable Reading
-  Enable Spot & Margin Trading (for live trading only)
- L Enable Withdrawals (NEVER enable this)
-  Enable Futures Trading (if using futures)

## Trading Modes

### Dry-run (Paper Trading)
- Uses real-time market data
- Simulates trades without real money
- Config: `proratio_utilities/config/freqtrade/config_dry.json`
- Set `TRADING_MODE=dry_run` in `.env`

### Live Trading
- Executes real trades with real money
- Start with small capital (1-5% of intended amount)
- Config: `proratio_utilities/config/freqtrade/config_live.json`
- Set `TRADING_MODE=live` in `.env`
- **Only use after successful paper trading!**

## Troubleshooting

### Freqtrade won't start
- Check `user_data/logs/freqtrade.log`
- Verify API keys in `.env`
- Ensure PostgreSQL and Redis are running: `docker-compose ps`

### AI signals not generating
- Check AI API keys are valid in `.env`
- Verify API quotas/limits not exceeded
- Check `proratio_signals/orchestrator.py` logs

### Backtest fails
- Ensure historical data downloaded: `ls user_data/data/`
- Check timeframe matches strategy: `4h` vs `1h`
- Verify strategy has no syntax errors

### Database connection errors
- Start PostgreSQL: `docker-compose up -d postgres`
- Check `DATABASE_URL` in `.env`
- Test connection: `psql $DATABASE_URL`

## Project Structure Summary

```
proratio/
├── proratio_utilities/     # Execution & data engine
├── proratio_signals/       # AI signal generation
├── proratio_quantlab/      # Backtesting & ML
├── proratio_tradehub/      # Strategy orchestration
├── user_data/              # Freqtrade user data
│   ├── strategies/         # Freqtrade strategies
│   └── db/                 # SQLite databases (gitignored)
├── temp_tests/             # Temporary testing (gitignored)
│   ├── strategies/         # Test strategies
│   ├── configs/            # Test configurations
│   ├── scripts/            # Test scripts
│   ├── docs/               # Test documentation
│   └── results/            # Test results
├── scripts/                # Utility scripts
├── tests/                  # Unit tests (106 passing)
└── docs/                   # Documentation
```

> **Updated Oct 9, 2025**: Created `temp_tests/` directory for all temporary testing materials. This keeps production code clean and makes it easy to identify files that are only needed during development/testing phases.

## Key Technologies

- **Python 3.11+**: Main language
- **Freqtrade**: Trading bot framework
- **CCXT**: Exchange connectivity library
- **PostgreSQL**: Database for time-series data
- **Redis**: Caching and state management
- **Streamlit**: Dashboard UI
- **OpenAI/Anthropic/Google APIs**: AI signal generation
- **Docker**: Containerization

## Additional Resources

- **Freqtrade Docs**: https://www.freqtrade.io/
- **CCXT Docs**: https://docs.ccxt.com/
- **Binance API**: https://binance-docs.github.io/apidocs/spot/en/
- **Project Documentation**: `docs/`
- **Project Reorganization**: `CLEANUP_COMPLETE.md`, `docs/project_structure.md`

## Development Workflow

### Production Strategy Development
1. **Research** in `proratio_quantlab/research/notebooks/`
2. **Develop strategy** in `proratio_tradehub/strategies/`
3. **Backtest** using `proratio_quantlab/backtesting/`
4. **Integrate AI signals** via `proratio_signals/`
5. **Paper trade** using `config_dry.json`
6. **Validate** for 1-2 weeks
7. **Deploy live** with small capital

### Temporary Testing Workflow (New - Oct 2025)
1. **Create test files** in `temp_tests/` directory
   - Strategies → `temp_tests/strategies/`
   - Configs → `temp_tests/configs/`
   - Scripts → `temp_tests/scripts/`
   - Results → `temp_tests/results/`
2. **Run tests** using scripts in `temp_tests/scripts/`
3. **Validate** performance and functionality
4. **Decision point**:
   - If successful → **Promote** to production (move to appropriate proratio_* module)
   - If complete → **Delete** temp_tests/ directory
   - If ongoing → **Keep** in temp_tests/ (gitignored)

> **Note**: `temp_tests/` is gitignored and should be deleted when testing is complete. See `temp_tests/README.md` for detailed workflow.

## 🚫 Git Operations Policy

**CRITICAL: Do NOT perform git operations except `git status`**

- ❌ **NEVER** run: `git add`, `git commit`, `git push`, `git pull`, `git merge`
- ✅ **ONLY ALLOWED:** `git status`, `git diff`, `git log`
- 📝 **Reason:** Git operations are handled in separate manual sessions

### When User Says "Prepare for Git Commit"

Perform these steps in order:

1. **Clean up temporary files**
   - Remove `*.tmp`, `*.bak`, temporary timestamped files
   - Check for any debug files or test outputs

2. **Update documentation**
   - Update `README.md` if features/setup changed
   - Update `roadmap.md` to reflect current progress
   - Update `CLAUDE.md` if workflow changed
   - Ensure all docs are consistent

3. **Security check for GitHub push**
   - Check `.gitignore` excludes: `data/output/*`, `data/cache/*`, `.env`
   - Verify no hardcoded secrets: `grep -r "secret\|password\|api_key\|token" src/`
   - Verify no dangerous code: `eval()`, `exec()`, `__import__`, `subprocess`
   - Confirm output files won't be pushed

4. **Output commit message in terminal**
   - Write commit message directly to terminal output
   - **DO NOT** create files like `COMMIT_MSG.txt` or similar
   - Format: Title + body with bullet points of changes
   - User will copy/paste this message when ready to commit

**Example response to "prepare for git commit":**
```
✅ Cleaned up temporary files
✅ Updated README.md, roadmap.md
✅ Security check passed (no secrets, output files excluded)

Suggested commit message:
---
Fix inactive users calculation and add deleted user tracking

- Track current creators vs deleted creators separately
- Fix inactive users metric (was showing -9, now correctly shows 6)
- Add "About this data" section explaining all metrics
- Update tests for new metrics (28 tests passing)
---
```

## 📁 File Naming Conventions

**All files in this project follow consistent naming standards:**

**Last Updated:** 20251003

### 1. Root Documentation Files → UPPERCASE
Standard documentation files use UPPERCASE for visibility and recognition.

**Examples:**
- `README.md` - Project overview and setup
- `CLAUDE.md` - Claude Code implementation guidelines
- `.gitignore` - Git ignore configuration
- `.env.example` - Environment variable template

**Why:** Industry standard for important project documentation files.

---

### 2. User-Created Documentation → lowercase_with_underscores
All other documentation uses lowercase with underscores for word separation.

**Living Documents (no datetime):**
- `roadmap.md` - Implementation plan (continuously updated)
- `sample_report.md` - Example template
- `file_naming_standards.md` - Project conventions

**Point-in-Time Snapshots (with datetime suffix):**
- `code_review_20241004.md` - Code review from Oct 4, 2024
- `code_review_actions_20241004.md` - Action plan from review
- `project_status_20241003.md` - Status snapshot from Oct 3, 2024

**Datetime Format:** `YYYYMMDD` (Compact date format)
- Allows chronological sorting
- No separators needed
- Example: `meeting_notes_20241215.md`

**Why:** Consistent with Python source code naming, allows version history, easier to type.

---

### 3. Source Code → lowercase_with_underscores
All Python source code follows PEP 8 style guide.

**Examples:**
- `config.py` - Configuration module
- `main.py` - Main entry point
- `src/api_client.py` - API client module
- `src/extractors.py` - Export extraction module
- `src/analytics.py` - Analytics engine
- `src/report_builder.py` - Report generation module
- `tests/test_config.py` - Config tests
- `tests/test_api_client.py` - API client tests

**Why:** Python PEP 8 style guide, standard practice.

---

### 4. Configuration Files → standard names
Configuration files use lowercase and standard naming conventions.

**Examples:**
- `requirements.txt` - Python dependencies
- `pytest.ini` - Pytest configuration
- `.env` - Environment variables (gitignored)
- `pyproject.toml` - Python project configuration (if needed)

**Why:** Standard convention recognized by tools.

---

### 5. Output Files → lowercase_with_datetime
Generated reports and outputs should include datetime stamps for tracking.

**Format:** `{type}_{description}_YYYYMMDD_HHMMSS.{ext}`

**Examples:**
- `workspace_analytics_20241015_143052.xlsx` - Excel report
- `cache_checkpoint_20241015_120000.pkl` - Cache checkpoint
- `export_summary_20241015.json` - Export summary

**Why:**
- Easy to identify when report was generated
- Allows keeping multiple versions
- Prevents overwriting previous runs
- Chronological sorting

---

### ❌ What NOT to Use

### Never Use:
- ❌ **camelCase** (e.g., `apiClient.py`, `codeReview.md`)
- ❌ **PascalCase** (e.g., `ApiClient.py`, `CodeReview.md`)
- ❌ **Mixed conventions** (e.g., `Code_Review.md`, `API_client.py`)
- ❌ **Spaces** (e.g., `code review.md`, `api client.py`)
- ❌ **Hyphens in Python files** (e.g., `api-client.py` - cannot import)

### Why These Are Bad:
- Inconsistent with team standards
- Harder to remember which format
- PascalCase suggests class names (confusing)
- Spaces break command-line tools
- Hyphens cannot be imported in Python

---

### ✅ Quick Reference

**When creating new files:**

| File Type | Convention | Example |
|-----------|------------|---------|
| Standard doc | UPPERCASE | `README.md`, `LICENSE` |
| Living doc | lowercase_underscore | `roadmap.md`, `sample_report.md` |
| Snapshot doc | lowercase_YYYYMMDD | `code_review_20241004.md` |
| Python source | lowercase_underscore | `my_module.py` |
| Python test | test_lowercase_underscore | `test_my_module.py` |
| Config file | lowercase | `requirements.txt` |
| Output file | lowercase_YYYYMMDD_HHMMSS | `report_20241015143052.xlsx` |

**Datetime Decision Tree:**
1. Is it continuously updated? → **NO datetime** (e.g., `roadmap.md`)
2. Is it a point-in-time snapshot? → **Add datetime** (e.g., `status_20241003.md`)
3. Is it generated output? → **Add datetime + time** (e.g., `report_20241015_143052.xlsx`)

---

### 📝 Enforcement

**Before creating any new file:**
1. Check this document for the correct convention
2. Follow the pattern for similar existing files
3. Never mix conventions within a file type

**During code review:**
- Flag any files that don't follow conventions
- Request renaming before merge

---

**Reference:** This standard is documented in [CLAUDE.md](CLAUDE.md) under "File Naming Conventions"


## 🎯 Implementation Workflow

**IMPORTANT:** Always follow [roadmap.md](roadmap.md) as the primary implementation guide.

[roadmap.md](roadmap.md) contains:
- ✅ Phase-by-phase checklist with detailed tasks
- ✅ Progress tracking (completed vs. pending tasks)
- ✅ Code examples and test commands for each phase
- ✅ Time estimates and success criteria
- ✅ Current implementation status

**Before implementing any feature:**
1. Check [roadmap.md](roadmap.md) for the current phase and tasks
2. Review the checklist for that phase
3. Implement according to the detailed requirements
4. Update checkboxes in [roadmap.md](roadmap.md) as tasks are completed
5. Run the test commands provided in the phase
6. Move to the next phase only when all tasks are checked

## Support

For issues or questions:
- Check `docs/` for module-specific guides
- Review Freqtrade documentation
- Check error logs in `user_data/logs/`
- Ensure all API keys are valid and have correct permissions
