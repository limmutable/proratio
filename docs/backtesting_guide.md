# Proratio Backtesting Guide

Complete guide to running backtests and analyzing results for the AI-enhanced trading strategy.

---

## Overview

Backtesting allows you to test strategies on historical data before risking real money. Proratio includes:
- **Baseline Strategy** (`SimpleTestStrategy`) - Technical indicators only
- **AI-Enhanced Strategy** (`AIEnhancedStrategy`) - Technical + AI consensus signals
- **Automated Comparison** - Side-by-side performance metrics

---

## Quick Start: Run a Backtest

### Basic Backtest (Last 6 Months)

```bash
# Backtest both strategies on BTC/USDT (6 months, 4h timeframe)
uv run python scripts/backtest_ai_strategy.py --timeframe 4h --months 6 --pairs BTC/USDT

# Multiple pairs
uv run python scripts/backtest_ai_strategy.py --timeframe 4h --months 6 --pairs BTC/USDT ETH/USDT

# 1-hour timeframe (more trades, faster execution)
uv run python scripts/backtest_ai_strategy.py --timeframe 1h --months 3 --pairs BTC/USDT

# Full year backtest
uv run python scripts/backtest_ai_strategy.py --timeframe 4h --months 12 --pairs BTC/USDT
```

**Output:**
- Runs `SimpleTestStrategy` first (baseline)
- Then runs `AIEnhancedStrategy` (AI-enhanced)
- Shows side-by-side comparison at the end

---

## Understanding Backtest Results

### Key Metrics Explained

**Performance Metrics:**
```
Total Trades         4                    # Number of trades executed
Total Profit %       -0.01%               # Overall profit/loss percentage
Win Rate             50.0%                # Percentage of winning trades
Sharpe Ratio         -0.06                # Risk-adjusted returns (> 1 is good)
Max Drawdown         0.03%                # Largest peak-to-trough decline
Avg Duration         1 day, 11:00:00      # Average time per trade
```

**What's Good:**
- ✅ **Win Rate > 55%** - More wins than losses
- ✅ **Sharpe Ratio > 1.0** - Good risk-adjusted returns
- ✅ **Max Drawdown < 10%** - Acceptable risk level
- ✅ **Total Profit > 0%** - Positive returns

**What's Bad:**
- ❌ **Win Rate < 45%** - Too many losses
- ❌ **Sharpe Ratio < 0** - Poor risk-adjusted returns
- ❌ **Max Drawdown > 20%** - Excessive risk
- ❌ **Total Profit < -5%** - Significant losses

---

## Backtest Report Breakdown

### 1. Backtesting Report Table

```
BACKTESTING REPORT
┏━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃     Pair ┃ Trades ┃ Avg Profit % ┃ Tot Profit USDT ┃    Win Rate  ┃
┡━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ BTC/USDT │      4 │        -0.31 │          -1.227 │        50.0% │
│    TOTAL │      4 │        -0.31 │          -1.227 │        50.0% │
└──────────┴────────┴──────────────┴─────────────────┴──────────────┘
```

**Interpretation:**
- BTC/USDT had 4 trades
- Average loss of -0.31% per trade
- Total loss of -$1.227 USDT
- 50% win rate (2 wins, 2 losses)

---

### 2. Exit Reason Stats

```
EXIT REASON STATS
┏━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Exit Reason ┃ Exits ┃ Avg Profit % ┃ Tot Profit USDT ┃   Win Rate ┃
┡━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│         roi │     2 │          2.0 │           3.974 │       100% │
│ exit_signal │     2 │        -2.61 │          -5.201 │         0% │
│       TOTAL │     4 │        -0.31 │          -1.227 │        50% │
└─────────────┴───────┴──────────────┴─────────────────┴────────────┘
```

**Exit Reasons:**
- `roi` = Take-profit target hit (good!)
- `exit_signal` = Exit signal triggered (could be stop-loss or strategy exit)
- `stop_loss` = Stop-loss triggered
- `trailing_stop_loss` = Trailing stop hit

**Interpretation:**
- 2 trades hit take-profit (+$3.974 profit)
- 2 trades hit exit signal (-$5.201 loss)
- ROI exits are profitable, exit signal exits are losing

---

### 3. Summary Metrics

```
SUMMARY METRICS
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric                        ┃ Value                          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Total/Daily Avg Trades        │ 4 / 0.02                       │
│ Starting balance              │ 10000 USDT                     │
│ Final balance                 │ 9998.773 USDT                  │
│ Absolute profit               │ -1.227 USDT                    │
│ Total profit %                │ -0.01%                         │
│ Sharpe                        │ -0.06                          │
│ Max Drawdown                  │ 0.03%                          │
│ Win Rate                      │ 50.0%                          │
│ Best trade                    │ BTC/USDT 2.00%                 │
│ Worst trade                   │ BTC/USDT -2.64%                │
└───────────────────────────────┴────────────────────────────────┘
```

**Key Insights:**
- Started with $10,000, ended with $9,998.77
- Lost $1.23 overall (-0.01%)
- Sharpe ratio negative (poor risk-adjusted performance)
- Small drawdown (only 0.03% max decline)

---

## Comparing Strategies

### Comparison Table

After running the backtest script, you'll see:

```
STRATEGY COMPARISON: SimpleTestStrategy vs AIEnhancedStrategy
==============================================================================
Metric               Baseline             AI-Enhanced          Improvement
------------------------------------------------------------------------------
Total Trades         4                    0                    -100.00%
Total Profit %       -0.01%               0.00%                +100.00%
Win Rate             50.00%               0.00%                N/A
Sharpe Ratio         -0.06                0.00                 +100.00%
Max Drawdown         0.03%                0.00%                -100.00%
==============================================================================
```

**Interpretation:**
- AI strategy made **0 trades** (filtered all signals as low-confidence)
- Baseline lost -0.01%, AI stayed flat (0%)
- **AI outperformed** by avoiding losing trades
- Sharpe improved (0 is better than -0.06)
- Drawdown eliminated (better risk management)

**Verdict:**
✅ AI strategy correctly identified unfavorable market conditions
✅ Prevented $1.23 loss by not trading
✅ Better risk-adjusted returns

---

## Interpreting Different Scenarios

### Scenario 1: AI Made Fewer Trades, Higher Profit

```
Baseline: 45 trades, +2.5% profit, 48% win rate
AI:       12 trades, +3.8% profit, 67% win rate
```

**Interpretation:**
- ✅ AI filtered low-quality signals
- ✅ Higher win rate = better trade selection
- ✅ More profit with less trades = excellent

---

### Scenario 2: AI Made No Trades

```
Baseline: 20 trades, -1.2% profit, 45% win rate
AI:       0 trades,  0.0% profit,  N/A
```

**Interpretation:**
- ✅ AI correctly avoided unfavorable market
- ✅ Prevented losses by staying flat
- ⚠️ Threshold may be too high (60%)
- 💡 Consider lowering to 55% for more opportunities

---

### Scenario 3: AI Underperformed Baseline

```
Baseline: 30 trades, +5.0% profit, 53% win rate
AI:       8 trades,  +1.2% profit, 50% win rate
```

**Interpretation:**
- ❌ AI filtered too many good signals
- ❌ Missed profitable opportunities
- 💡 Lower confidence threshold from 60% → 50%
- 💡 Review AI prompt engineering

---

## Advanced Backtesting

### 1. Using Freqtrade Directly

```bash
# Basic backtest
freqtrade backtesting \
  --strategy AIEnhancedStrategy \
  --timeframe 4h \
  --timerange 20250101-20251008 \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data

# With specific pairs
freqtrade backtesting \
  --strategy AIEnhancedStrategy \
  --timeframe 1h \
  --pairs BTC/USDT ETH/USDT \
  --timerange 20250601-20251008 \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data
```

---

### 2. Export Trade Data

```bash
# Export trades to JSON
freqtrade backtesting \
  --strategy AIEnhancedStrategy \
  --timeframe 4h \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data \
  --export trades \
  --export-filename user_data/backtest-results/ai_enhanced_trades.json
```

**Results saved to:**
- `user_data/backtest-results/backtest-result-<timestamp>.json`
- Contains detailed trade-by-trade data

---

### 3. Generate Plots

```bash
# Plot strategy performance
freqtrade plot-dataframe \
  --strategy AIEnhancedStrategy \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data \
  --pairs BTC/USDT \
  --timerange 20250601-20251008

# Output: user_data/plot/freqtrade-plot-BTC_USDT-4h.html
# Open in browser to see interactive chart
```

**Plot shows:**
- Entry and exit points
- Technical indicators (EMA, RSI, Volume)
- Price action with trades overlaid

---

### 4. Profit Plot

```bash
# Generate cumulative profit chart
freqtrade plot-profit \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data \
  --timerange 20250601-20251008

# Output: user_data/plot/freqtrade-profit-plot.html
```

---

## Where to Find Backtest Results

### 1. Terminal Output

Backtest results are printed directly to the terminal when you run:
```bash
uv run python scripts/backtest_ai_strategy.py --timeframe 4h --months 6
```

### 2. Freqtrade Backtest Results

```bash
# Location
ls -la user_data/backtest-results/

# Files
backtest-result-2025-10-08_14-30-45.json  # Detailed trade data
.last_result.json                          # Latest backtest result
```

### 3. JSON Result Files

```bash
# View latest result
cat user_data/backtest-results/.last_result.json | jq .

# View specific backtest
cat user_data/backtest-results/backtest-result-*.json | jq .
```

### 4. HTML Plot Files

```bash
# Location
ls -la user_data/plot/

# Files
freqtrade-plot-BTC_USDT-4h.html       # Strategy chart
freqtrade-profit-plot.html            # Profit chart

# Open in browser
open user_data/plot/freqtrade-plot-BTC_USDT-4h.html
```

---

## A/B Testing Framework

### Overview

The A/B Testing Framework provides statistical strategy comparison with confidence scores to determine which strategy performs better.

### Running Phase 2 Backtests with A/B Testing

```bash
# Backtest all Phase 2 strategies with A/B comparison
python scripts/backtest_phase2_strategies.py \
  --pairs BTC/USDT ETH/USDT \
  --timeframe 1h \
  --days 180

# Backtest specific strategies
python scripts/backtest_phase2_strategies.py \
  --strategies MeanReversionStrategy GridTradingStrategy \
  --days 90

# Use custom config
python scripts/backtest_phase2_strategies.py \
  --config proratio_utilities/config/freqtrade/config_custom.json

# Skip backtest, analyze existing results
python scripts/backtest_phase2_strategies.py --skip-backtest
```

### Statistical Tests

The framework includes four statistical tests:

#### 1. T-Test (Parametric)
- Tests if mean returns differ significantly
- Assumes normal distribution
- Best for: Large sample sizes (> 30 trades)

#### 2. Mann-Whitney U Test (Non-parametric)
- Distribution-free alternative to T-test
- Compares median returns
- Best for: Small samples or non-normal distributions

#### 3. Kolmogorov-Smirnov Test
- Compares entire return distributions
- Detects differences in shape, not just mean
- Best for: Detecting systematic differences

#### 4. Variance Test (F-test)
- Compares risk/volatility between strategies
- Tests if one strategy is more consistent
- Best for: Risk-adjusted performance

### Usage Example

```python
from proratio_quantlab.ab_testing import (
    StrategyComparer,
    StrategyResult,
    create_strategy_result_from_backtest
)

# Initialize comparer
comparer = StrategyComparer(
    significance_level=0.05,  # 5% p-value threshold
    min_trades_for_significance=30
)

# Load backtest results
strategy_a = create_strategy_result_from_backtest(
    "AIEnhancedStrategy",
    backtest_data_a
)

strategy_b = create_strategy_result_from_backtest(
    "MeanReversionStrategy",
    backtest_data_b
)

# Compare strategies
comparison = comparer.compare_strategies(strategy_a, strategy_b)

# Print detailed report
comparer.print_comparison_report(comparison)
```

### Example Output

```
🏆 WINNER: MeanReversionStrategy (confidence: 85%)

Statistical Tests:
  • T-test: p=0.023 ✅ Significant difference in mean returns
  • Mann-Whitney: p=0.031 ✅ Significant difference in medians
  • KS-test: p=0.045 ✅ Distributions differ significantly
  • Variance: p=0.089 ⚠️ No significant risk difference

Key Differences:
  • Returns: +3.50% (✅ Strategy B)
  • Sharpe: +0.45 (✅ Strategy B)
  • Drawdown: +1.20% (✅ Strategy B better)
  • Win Rate: +8.5% (✅ Strategy B)

✅ RECOMMENDATION: Deploy MeanReversionStrategy
   Strong statistical evidence of superior performance.
```

### Confidence Levels

| Confidence | Interpretation | Action |
|------------|----------------|--------|
| **> 70%** | High confidence | ✅ Deploy winner |
| **50-70%** | Medium confidence | ⚠️ More testing needed |
| **< 50%** | Low confidence | ❌ Insufficient evidence |

### Interpreting Results

#### Scenario 1: Clear Winner (Confidence > 80%)

```
Winner: MeanReversionStrategy (confidence: 85%)
All 4 tests show significant differences (p < 0.05)
Mean Reversion outperforms by +5.2% returns
```

**Action:** Deploy MeanReversionStrategy with confidence

#### Scenario 2: Marginal Difference (Confidence 50-70%)

```
Winner: GridTradingStrategy (confidence: 62%)
2 out of 4 tests show significant differences
Grid Trading slightly better (+1.8% returns)
```

**Action:**
- Extend backtest period (180 → 365 days)
- Test on more pairs
- Consider market regime (both may excel in different conditions)

#### Scenario 3: No Clear Winner (Confidence < 50%)

```
Winner: None (confidence: 45%)
No statistical tests show significant differences
Both strategies perform similarly
```

**Action:**
- Use Portfolio Manager to run both simultaneously
- Allocate based on market regime detection
- Continue monitoring performance

### Output Files

The backtest script generates:

1. **Summary Table**: Side-by-side metrics comparison (terminal)
2. **A/B Test Results**: Statistical analysis for each pair (terminal)
3. **JSON Export**: `user_data/backtest_results/phase2_comparison.json`

### Best Practices for A/B Testing

#### 1. Sample Size Requirements
- Minimum 30 trades per strategy for valid statistical tests
- More trades = higher confidence in results
- Consider extending backtest period if < 30 trades

#### 2. Multiple Pairs Testing
```bash
# Test on multiple pairs to validate generalization
python scripts/backtest_phase2_strategies.py \
  --pairs BTC/USDT ETH/USDT BNB/USDT SOL/USDT \
  --days 180
```

#### 3. Different Market Conditions
```bash
# Bull market
python scripts/backtest_phase2_strategies.py --timerange 20241001-20241231

# Bear market
python scripts/backtest_phase2_strategies.py --timerange 20220401-20220930

# Ranging market
python scripts/backtest_phase2_strategies.py --timerange 20230101-20230630
```

#### 4. Walk-Forward Validation
```bash
# Train period
python scripts/backtest_phase2_strategies.py --days 180

# Test period (different time)
python scripts/backtest_phase2_strategies.py --timerange 20251001-20251231
```

**Goal:** Winner should be consistent across both periods

---

## Backtest Best Practices

### 1. Test Multiple Timeframes

```bash
# 1-hour (fast, many trades)
uv run python scripts/backtest_ai_strategy.py --timeframe 1h --months 3

# 4-hour (medium, balanced)
uv run python scripts/backtest_ai_strategy.py --timeframe 4h --months 6

# Daily (slow, fewer trades)
uv run python scripts/backtest_ai_strategy.py --timeframe 1d --months 12
```

### 2. Test Different Market Conditions

```bash
# Bull market (e.g., Q4 2024)
freqtrade backtesting --timerange 20241001-20241231

# Bear market (e.g., mid-2022)
freqtrade backtesting --timerange 20220401-20220930

# Ranging market (sideways)
freqtrade backtesting --timerange 20230101-20230630
```

### 3. Walk-Forward Analysis

Test on different time periods sequentially:

```bash
# Train period (Jan-Jun 2025)
freqtrade backtesting --timerange 20250101-20250630

# Test period (Jul-Oct 2025)
freqtrade backtesting --timerange 20250701-20251008
```

**Goal:** Performance should be consistent across periods.

---

## Tuning Strategy Based on Results

### If Win Rate < 50%

**Problem:** Too many losing trades

**Solutions:**
1. Increase AI confidence threshold (60% → 65%)
2. Add stricter entry filters
3. Review stop-loss settings (too tight?)

### If No Trades / Very Few Trades

**Problem:** AI filtering too aggressively

**Solutions:**
1. Lower AI confidence threshold (60% → 55% or 50%)
2. Test with baseline strategy to verify technical signals work
3. Check AI provider status (all 3 working?)

### If High Drawdown (> 15%)

**Problem:** Excessive risk exposure

**Solutions:**
1. Tighten stop-losses
2. Reduce position sizes
3. Lower max open trades
4. Review exit conditions

---

## Quick Reference Commands

```bash
# Run comprehensive backtest (recommended)
uv run python scripts/backtest_ai_strategy.py --timeframe 4h --months 6 --pairs BTC/USDT

# View latest backtest results
cat user_data/backtest-results/.last_result.json | jq .

# Generate plot
freqtrade plot-dataframe \
  --strategy AIEnhancedStrategy \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data \
  --pairs BTC/USDT

# Open plot in browser
open user_data/plot/freqtrade-plot-BTC_USDT-4h.html
```

---

## Backtest vs Paper Trading vs Live

| Aspect | Backtest | Paper Trading | Live Trading |
|--------|----------|---------------|--------------|
| **Data** | Historical | Real-time | Real-time |
| **Money** | Simulated | Simulated | Real |
| **Speed** | Fast (minutes) | Slow (days/weeks) | Slow (ongoing) |
| **Purpose** | Validate strategy | Test execution | Make profit |
| **Risk** | None | None | High |

**Workflow:**
1. ✅ **Backtest** - Validate strategy works on historical data
2. ✅ **Paper trade** - Confirm execution with real-time data (5-7 days)
3. ✅ **Live trade** - Deploy with real money (small capital first)

---

## Next Steps

After successful backtesting:

1. **Review Results**
   - Win rate > 50%?
   - Sharpe ratio > 1.0?
   - Max drawdown < 10%?

2. **If Good Results:**
   - Proceed to paper trading (Phase 1.3)
   - See [paper_trading_guide.md](./paper_trading_guide.md)

3. **If Poor Results:**
   - Tune parameters in `trading_config.json`
   - Review AI prompt engineering
   - Test different timeframes
   - Re-run backtest

---

## Resources

- **Freqtrade Backtesting Docs**: https://www.freqtrade.io/en/stable/backtesting/
- **Strategy Optimization**: https://www.freqtrade.io/en/stable/hyperopt/
- **Plotting Guide**: https://www.freqtrade.io/en/stable/plotting/

---

**Last Updated**: 2025-10-08
