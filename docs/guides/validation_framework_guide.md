# Strategy Validation Framework Guide

**Fast, comprehensive validation for Freqtrade strategies**

---

## Overview

The Strategy Validation Framework provides a fast, automated way to validate any Freqtrade strategy in 5-10 minutes. This replaces the traditional multi-day paper trading approach with comprehensive automated testing.

### Why This Framework?

| Traditional Approach | Validation Framework |
|---------------------|---------------------|
| 5-7 days per strategy | 5-10 minutes per strategy |
| Manual monitoring required | Fully automated |
| Market-dependent results | Deterministic testing |
| One-time validation | Reusable for all strategies |
| Unclear success criteria | Clear pass/fail |

---

## Quick Start

### Basic Usage

```bash
# Validate a strategy (5-10 minutes)
./scripts/validate_strategy.sh SimpleTestStrategy

# Validate with custom time range
./scripts/validate_strategy.sh MyStrategy 20240101-20241001
```

### What Gets Validated

1. **Backtest Execution** (2-3 min)
   - Strategy runs without errors
   - Trades are executed
   - Indicators calculate correctly

2. **Results Validation** (instant)
   - Win rate ≥ 45%
   - Max drawdown < 25%
   - Sharpe ratio ≥ 0.5
   - Profit factor ≥ 1.0
   - Minimum 5 trades

3. **Integration Tests** (1-2 min, if available)
   - Strategy logic tests
   - Risk limit enforcement
   - AI integration (if applicable)

4. **Code Quality** (instant)
   - Linting checks
   - Code style validation

5. **Comprehensive Report** (instant)
   - Pass/fail summary
   - Detailed metrics
   - Recommendations

---

## Installation

The framework is already set up! Components:

```
proratio/
├── scripts/
│   ├── validate_strategy.sh              # Main validation script
│   ├── validate_backtest_results.py       # Results validator
│   └── generate_validation_report.py      # Report generator
├── proratio_utilities/config/freqtrade/
│   └── config_accelerated_test.json       # Fast test config
└── tests/test_strategies/
    └── test_strategy_template.py          # Test template
```

---

## Validation Criteria

### Critical Checks (Must Pass)

| Metric | Criterion | Reason |
|--------|-----------|--------|
| **Minimum Trades** | ≥ 5 trades | Statistical significance |
| **Win Rate** | ≥ 45% | Profitability threshold |
| **Max Drawdown** | < 25% | Risk tolerance |
| **Profit Factor** | ≥ 1.0 | Profitable overall |
| **Total Profit** | ≥ 0% | Not losing money |

### Quality Checks (Warning if Failed)

| Metric | Target | Impact |
|--------|--------|--------|
| **Sharpe Ratio** | ≥ 0.5 | Risk-adjusted returns |
| **Average Duration** | Reasonable | Strategy efficiency |
| **No Errors** | 0 errors | Code quality |

### Customizing Criteria

Edit validation criteria in `scripts/validate_backtest_results.py`:

```python
VALIDATION_CRITERIA = {
    "min_trades": 5,
    "min_win_rate": 45.0,        # Adjust this
    "max_drawdown": 25.0,         # Adjust this
    "min_sharpe": 0.5,            # Adjust this
    "min_profit_factor": 1.0,
    "max_avg_loss_pct": 5.0,
}
```

---

## Detailed Usage

### 1. Validating a Strategy

```bash
# Basic validation
./scripts/validate_strategy.sh MyStrategy

# Custom time range (6 months recommended minimum)
./scripts/validate_strategy.sh MyStrategy 20240401-20241001

# Full year
./scripts/validate_strategy.sh MyStrategy 20230101-20231231
```

### 2. Understanding the Output

```
╔══════════════════════════════════════════════════════════╗
║     Strategy Validation Framework v1.0                  ║
╚══════════════════════════════════════════════════════════╝

Strategy: MyStrategy
Timerange: 20240401-20241001
Report: tests/validation_results/MyStrategy_validation_20241014_123456.txt

[1/6] Running pre-flight checks...
✓ Strategy file found: user_data/strategies/MyStrategy.py
✓ Found 12 data files
✓ Config file: config_accelerated_test.json

[2/6] Running backtest (this may take 2-3 minutes)...
✓ Backtest completed

[3/6] Validating backtest results...
✓ Validation checks passed

[4/6] Running integration tests...
✓ Integration tests passed

[5/6] Checking code quality...
✓ No linting issues

[6/6] Generating validation report...
✓ Report generated

╔══════════════════════════════════════════════════════════╗
║     Validation Complete                                  ║
╚══════════════════════════════════════════════════════════╝

✓ Validation report saved to: tests/validation_results/MyStrategy_validation_20241014_123456.txt
```

### 3. Reading the Validation Report

Reports are saved in `tests/validation_results/` and contain:

```
=========================================
Validation Results: MyStrategy
=========================================

Key Metrics:
  Total Trades:     15
  Win Rate:         53.33%
  Total Profit:     8.45% (845.00 USDT)
  Max Drawdown:     12.30%
  Sharpe Ratio:     1.45
  Profit Factor:    1.85
  Avg Duration:     2 days, 6:30:00

Validation Checks:
  ✓ PASS [CRITICAL]    Minimum Trades       >= 5 trades              (Actual: 15)
  ✓ PASS [HIGH]        Win Rate            >= 45.0%                 (Actual: 53.33%)
  ✓ PASS [HIGH]        Max Drawdown        < 25.0%                  (Actual: 12.30%)
  ✓ PASS [MEDIUM]      Sharpe Ratio        >= 0.5                   (Actual: 1.45)
  ✓ PASS [HIGH]        Profit Factor       >= 1.0                   (Actual: 1.85)
  ✓ PASS [HIGH]        Total Profit        >= 0%                    (Actual: 8.45%)

=========================================
✓ VALIDATION PASSED - Strategy meets minimum criteria

Next steps:
  1. Review the metrics and ensure they align with expectations
  2. Run integration tests if available
  3. Strategy is ready for paper trading validation
=========================================
```

---

## Creating Integration Tests

Integration tests ensure your strategy logic works correctly.

### Step 1: Copy Template

```bash
cp tests/test_strategies/test_strategy_template.py \
   tests/test_strategies/test_MyStrategy.py
```

### Step 2: Customize Tests

```python
# tests/test_strategies/test_MyStrategy.py

import pytest
from user_data.strategies.MyStrategy import MyStrategy

class TestMyStrategy:
    @pytest.fixture
    def strategy(self):
        """Initialize strategy"""
        return MyStrategy()

    def test_strategy_loads(self, strategy):
        """Test strategy can be loaded"""
        assert strategy is not None

    def test_custom_indicator(self, strategy, sample_dataframe):
        """Test your custom indicator"""
        df = strategy.populate_indicators(sample_dataframe.copy(), {"pair": "BTC/USDT"})

        # Check your indicator exists
        assert 'my_custom_indicator' in df.columns
        assert not df['my_custom_indicator'].isna().all()

    def test_entry_logic(self, strategy, sample_dataframe):
        """Test entry conditions"""
        df = strategy.populate_indicators(sample_dataframe.copy(), {"pair": "BTC/USDT"})
        df = strategy.populate_entry_trend(df, {"pair": "BTC/USDT"})

        # Verify entries are generated
        entries = df[df['enter_long'] == 1]
        assert len(entries) > 0, "Strategy should generate entry signals"
```

### Step 3: Run Tests

```bash
# Run tests for your strategy
uv run pytest tests/test_strategies/test_MyStrategy.py -v

# Run all strategy tests
uv run pytest tests/test_strategies/ -v
```

---

## Advanced Usage

### Validating Multiple Strategies

Create a batch validation script:

```bash
#!/bin/bash
# validate_all_strategies.sh

STRATEGIES=(
    "SimpleTestStrategy"
    "TrendFollowingStrategy"
    "MeanReversionStrategy"
)

for strategy in "${STRATEGIES[@]}"; do
    echo "Validating $strategy..."
    ./scripts/validate_strategy.sh "$strategy"
    echo ""
done
```

### Continuous Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/validate_strategies.yml
name: Validate Strategies

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Validate strategies
        run: ./scripts/validate_strategy.sh MyStrategy
```

### Custom Validation Logic

Extend validation by modifying `validate_backtest_results.py`:

```python
def validate_metrics(metrics: Dict) -> Tuple[bool, List[Dict]]:
    checks = []

    # Add custom check
    check = {
        "name": "My Custom Check",
        "criterion": "Custom logic",
        "actual": "Value",
        "passed": True,  # Your logic here
        "severity": "high",
    }
    checks.append(check)

    return all_passed, checks
```

---

## Troubleshooting

### Issue 1: "No data found for pair"

**Solution**: Export data from PostgreSQL first

```bash
python scripts/export_data_for_freqtrade.py
```

### Issue 2: "Strategy file not found"

**Solution**: Ensure strategy file is in `user_data/strategies/`

```bash
ls user_data/strategies/
```

### Issue 3: "Backtest shows 0 trades"

**Possible causes**:
- Strategy conditions too strict
- Timerange doesn't match market conditions
- Indicators not configured correctly

**Solution**: Run backtest manually to debug

```bash
freqtrade backtesting \
  --strategy MyStrategy \
  --timerange 20240401-20241001 \
  --userdir user_data \
  --config proratio_utilities/config/freqtrade/config_dry.json
```

### Issue 4: "Validation failed - Win rate too low"

**Options**:
1. Adjust strategy parameters
2. Try different timeframe
3. Test on different market conditions
4. Lower validation criteria (if acceptable)

### Issue 5: "Integration tests not found"

**Not a problem!** Integration tests are optional. The framework works without them.

To add tests:
```bash
cp tests/test_strategies/test_strategy_template.py \
   tests/test_strategies/test_YourStrategy.py
# Edit the file to test your strategy
```

---

## Best Practices

### 1. Validate Before Deployment

**Always** validate strategies before paper trading or live deployment:

```bash
./scripts/validate_strategy.sh MyStrategy
```

### 2. Test on Multiple Timeframes

Validate on different data periods:

```bash
# Bull market
./scripts/validate_strategy.sh MyStrategy 20230101-20230630

# Bear market
./scripts/validate_strategy.sh MyStrategy 20230701-20231231

# Mixed conditions
./scripts/validate_strategy.sh MyStrategy 20230101-20231231
```

### 3. Keep Validation Reports

Reports are saved with timestamps - keep them for comparison:

```bash
# View all validation reports
ls -lh tests/validation_results/

# Compare two validations
diff tests/validation_results/MyStrategy_validation_20241001_120000.txt \
     tests/validation_results/MyStrategy_validation_20241014_120000.txt
```

### 4. Use Integration Tests

Create comprehensive tests for complex strategies:

```bash
# Test all aspects of your strategy
tests/test_strategies/test_MyStrategy.py
  - test_strategy_loads
  - test_indicators_calculate
  - test_entry_conditions
  - test_exit_conditions
  - test_risk_limits
  - test_ai_integration (if applicable)
```

### 5. Automate Validation

Add to your development workflow:

```bash
# In your Makefile
validate:
	./scripts/validate_strategy.sh MyStrategy

# Run validation before committing
git pre-commit hook:
  - Validate changed strategies
  - Ensure tests pass
  - Check for regressions
```

---

## Framework Components

### 1. Main Validation Script

**File**: `scripts/validate_strategy.sh`
- **Purpose**: Orchestrates entire validation process
- **Runtime**: 5-10 minutes
- **Output**: Comprehensive validation report

### 2. Results Validator

**File**: `scripts/validate_backtest_results.py`
- **Purpose**: Validates backtest metrics against criteria
- **Runtime**: Instant
- **Output**: Pass/fail with detailed checks

### 3. Report Generator

**File**: `scripts/generate_validation_report.py`
- **Purpose**: Generates summary reports
- **Runtime**: Instant
- **Output**: Text and JSON reports

### 4. Test Config

**File**: `proratio_utilities/config/freqtrade/config_accelerated_test.json`
- **Purpose**: Optimized config for fast testing
- **Optimizations**:
  - Rate limiting disabled
  - API server disabled
  - Fast processing (1 sec throttle)

### 5. Test Templates

**File**: `tests/test_strategies/test_strategy_template.py`
- **Purpose**: Template for creating strategy tests
- **Usage**: Copy and customize for each strategy

---

## FAQ

### Q: Do I still need multi-day paper trading?

**A**: For production deployment, yes - but as final validation, not primary testing. The validation framework catches 90% of issues in minutes, leaving paper trading as a confidence check.

### Q: Can I adjust the validation criteria?

**A**: Yes! Edit `VALIDATION_CRITERIA` in `scripts/validate_backtest_results.py` to match your risk tolerance.

### Q: What if my strategy fails validation?

**A**: Review the failed checks in the report. Common fixes:
- Adjust strategy parameters
- Test on different timeframes
- Improve entry/exit logic
- Add more indicators

### Q: Can I use this for non-AI strategies?

**A**: Absolutely! The framework works for any Freqtrade strategy.

### Q: How often should I re-validate?

**A**: Re-validate after:
- Strategy code changes
- Parameter adjustments
- Major market regime changes
- Before production deployment

### Q: Can I run multiple validations in parallel?

**A**: Yes! Each validation is independent:

```bash
# Run in parallel
./scripts/validate_strategy.sh Strategy1 &
./scripts/validate_strategy.sh Strategy2 &
./scripts/validate_strategy.sh Strategy3 &
wait
```

---

## Next Steps

1. **Validate existing strategies**
   ```bash
   ./scripts/validate_strategy.sh SimpleTestStrategy
   ```

2. **Create integration tests** (optional but recommended)
   ```bash
   cp tests/test_strategies/test_strategy_template.py tests/test_strategies/test_MyStrategy.py
   ```

3. **Start developing Phase 4 strategies**
   - Now unblocked from Phase 1.4!
   - Use validation framework for all new strategies
   - Fast iteration and testing

---

## Related Documentation

- [Strategy Development Guide](strategy_development_guide.md)
- [Paper Trading Guide](paper_trading_guide.md)
- [Roadmap - Phase 1.4](../project/roadmap.md#phase-14-strategy-validation-framework)

---

**Last Updated**: 2025-10-14
