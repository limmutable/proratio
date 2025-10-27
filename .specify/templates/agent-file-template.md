# Proratio Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-27

## Active Technologies

### Core Stack
- **Python 3.10+** - Primary language
- **Freqtrade** - Trading bot framework and execution engine
- **CCXT** - Exchange connectivity
- **PostgreSQL** - Time-series data storage
- **Docker** - Containerization and infrastructure

### AI/ML Stack
- **OpenAI API (ChatGPT)** - LLM analysis
- **Anthropic API (Claude)** - LLM analysis
- **Google Gemini API** - LLM analysis
- **PyTorch** - LSTM neural networks
- **LightGBM** - Gradient boosting
- **XGBoost** - Extreme gradient boosting
- **scikit-learn** - ML utilities and ensemble methods

### Development Tools
- **Ruff** - Linting and formatting
- **pytest** - Testing framework
- **pip-audit** - Dependency security scanning
- **pre-commit** - Git hooks for quality checks

## Project Structure

```text
proratio/
├── proratio_utilities/          # Core infrastructure & execution
│   ├── config/                  # Configuration management
│   ├── data/                    # Data collectors & loaders
│   ├── execution/               # Order & position management
│   └── utils/                   # Logging, alerts, helpers
│
├── proratio_signals/            # AI signal generation
│   ├── llm_providers/           # ChatGPT, Claude, Gemini
│   ├── prompts/                 # Prompt engineering
│   ├── signal_generators/       # Signal logic
│   └── orchestrator.py          # Multi-AI coordination
│
├── proratio_quantlab/           # Backtesting & ML research
│   ├── backtesting/             # Backtest engine
│   ├── ml/                      # ML models & feature engineering
│   ├── ab_testing/              # A/B testing framework
│   └── analytics/               # Performance metrics
│
├── proratio_tradehub/           # Strategy orchestration
│   ├── strategies/              # Trading strategies
│   ├── orchestration/           # Multi-strategy manager
│   ├── risk/                    # Risk management
│   └── dashboard/               # Monitoring UI (planned)
│
├── user_data/                   # Freqtrade integration
│   ├── strategies/              # Freqtrade strategy adapters
│   └── data/                    # Market data (gitignored)
│
├── strategies/                  # Strategy registry & implementations
│   ├── active/                  # Active strategies
│   ├── archived/                # Retired strategies
│   └── registry.json            # Strategy metadata
│
├── scripts/                     # Utility scripts
├── tests/                       # Test suite (186+ tests)
├── docs/                        # Documentation
└── specs/                       # Feature specifications (SpecKit)
```

## Commands

### Development
```bash
# Setup
./scripts/setup.sh                           # Initial setup
./start.sh                                   # Launch CLI

# Linting & Formatting
ruff check --fix .                           # Fix linting issues
ruff format .                                # Format code

# Testing
pytest                                       # Run all tests
pytest tests/test_signals/                   # Test specific module
pytest tests/test_signals/test_base_provider.py::test_my_function  # Test specific function
pytest --cov=proratio_signals --cov-report=html  # Coverage report

# Security
pip-audit                                    # Scan dependencies
```

### Trading Operations
```bash
# Strategy Management
./start.sh strategy list                     # List all strategies
./start.sh strategy validate <name>          # Validate strategy (5-10 min)
./start.sh help validate                     # Validation guide

# Data Management
python scripts/download_historical_data.py   # Download market data

# Backtesting
python scripts/backtest_ai_strategy.py --timeframe 1h --months 6

# Paper Trading
./scripts/start_paper_trading.sh             # Start paper trading
./scripts/monitor_paper_trading.py           # Monitor paper trading

# Model Training
python scripts/train_lstm_model.py --pair BTC/USDT --epochs 100
python scripts/train_ensemble_model.py       # Train ensemble
```

### AI/ML Operations
```bash
# Test AI signals
python scripts/test_ai_signals.py

# Analyze model confidence
python scripts/analyze_model_confidence.py
python scripts/analyze_llm_confidence.py

# Generate reports
python scripts/generate_weekly_report.py
python scripts/generate_validation_report.py
```

## Code Style

### Python Standards (Enforced by Ruff)

**Imports**: Grouped and ordered:
1. Standard library
2. Third-party packages
3. Application-specific modules

```python
import logging
from typing import Optional

import pandas as pd
import numpy as np

from proratio_signals import SignalOrchestrator
from proratio_utilities.config import TradingConfig
```

**Formatting**:
- Black-compatible (88 character line length)
- Use double quotes for strings
- Trailing commas in multi-line structures

**Naming**:
- `snake_case` for functions and variables
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Prefix private methods with `_`

**Type Hints**: Required for all function signatures
```python
def calculate_position_size(
    balance: float,
    risk_per_trade: float,
    stop_loss_pct: float,
    confidence: Optional[float] = None
) -> float:
    """Calculate position size using risk-based approach."""
    pass
```

**Error Handling**:
- Use specific custom exceptions (e.g., `proratio_signals.llm_providers.exceptions`)
- Never use bare `except:` clauses
- Always clean up resources with context managers

**Docstrings**: Google-style for all public modules, classes, and functions
```python
def generate_signal(self, pair: str, timeframe: str) -> Signal:
    """Generate trading signal using multi-AI consensus.
    
    Args:
        pair: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candlestick timeframe (e.g., '1h', '4h')
        
    Returns:
        Signal object with direction, confidence, and reasoning
        
    Raises:
        APIError: If all LLM providers fail
        ValidationError: If input data is invalid
    """
    pass
```

**Logging**: Use `logging` module exclusively
```python
import logging

logger = logging.getLogger(__name__)

# Log levels:
logger.debug("Detailed debugging information")
logger.info("General operational information")
logger.warning("Warning about potential issues")
logger.error("Error occurred but system continues")
```

### Module-Specific Guidelines

**proratio_utilities**:
- Configuration: Use `load_and_hydrate_config()` for runtime secret injection
- Data: Return pandas DataFrames with standardized column names
- Execution: Always validate orders before submission

**proratio_signals**:
- LLM providers: Implement `BaseLLMProvider` interface
- Prompts: Store in `prompts/` module, not inline
- Signals: Always include confidence scores and reasoning

**proratio_quantlab**:
- Models: Version all trained models (semantic versioning)
- Features: Document all engineered features in feature_engineering.py
- Backtests: Save results with metadata (date, config, git hash)

**proratio_tradehub**:
- Strategies: Register in `strategies/registry.json`
- Risk: All risk checks MUST be in risk_manager.py, not scattered
- Multi-strategy: Use portfolio_manager.py for allocation

## Constitutional Requirements

All development MUST adhere to the [Proratio Constitution](../.specify/memory/constitution.md):

### NON-NEGOTIABLE Principles:
1. **Modular Architecture** - Four independent modules with clear boundaries
2. **Test-First Development** - TDD for all new features (write tests first)
3. **Strategy Validation** - All strategies MUST pass validation framework before deployment
4. **Configuration as Code** - Secrets in `.env` only, templates in version control
5. **Risk Management First** - Six layers of risk control enforced
6. **AI/ML Consensus** - Multi-LLM voting, ML ensemble, conflict resolution
7. **Observability** - Structured logging, monitoring, debuggability
8. **Code Quality** - Ruff linting, type hints, docstrings, >80% test coverage

### Security Checklist:
- [ ] API keys only in `.env` (never in code)
- [ ] No secrets in logs or error messages
- [ ] `pip-audit` passes (no critical CVEs)
- [ ] Pre-commit hooks enabled

### Quality Gates:
- [ ] Tests pass (186+ tests)
- [ ] Ruff linting passes (zero errors)
- [ ] Test coverage ≥80% for new code
- [ ] Strategy validation passes (if applicable)
- [ ] Documentation updated

## Recent Changes

### 002-name-refactor-strategy (Completed 2025-10-27)
- Refactored GridTradingStrategy to use adapter pattern
- Improved Freqtrade integration
- Added comprehensive tests

### 001-name-refactor-config (Completed 2025-10-27)
- Implemented configuration consolidation
- Dynamic secret injection from `.env`
- Validation framework with CI/CD integration
- Eliminated secrets from version control

### Phase 4.7 - Confidence Calibration (Completed 2025-10-16)
- LLM confidence analysis and calibration
- Improved ML ensemble confidence scoring
- Enhanced hybrid ML+LLM agreement metrics

<!-- MANUAL ADDITIONS START -->

## SpecKit Integration

This project uses SpecKit for structured feature development:

### SpecKit Commands
```bash
# Feature specification workflow
/speckit.specify        # Create spec.md for new feature
/speckit.plan          # Generate plan.md from spec
/speckit.tasks         # Generate tasks.md from plan
/speckit.analyze       # Validate consistency across artifacts
/speckit.implement     # Guide implementation process
/speckit.checklist     # Create feature checklist
/speckit.constitution  # Update project constitution
```

### Feature Development Process
1. Create spec in `specs/<id>-<name>/spec.md` using `/speckit.specify`
2. Generate plan using `/speckit.plan`
3. Generate tasks using `/speckit.tasks`
4. Run analysis using `/speckit.analyze` to check consistency
5. Implement using TDD (tests first)
6. Document completion in `specs/<id>-<name>/completion_report.md`

### Spec Directory Structure
```text
specs/
├── 001-name-refactor-config/
│   ├── spec.md              # Feature specification
│   ├── plan.md              # Implementation plan
│   ├── tasks.md             # Task breakdown
│   └── completion_report.md # Final report
└── 002-name-refactor-strategy/
    └── spec.md
```

<!-- MANUAL ADDITIONS END -->
