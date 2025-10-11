# Phase 2: Advanced Strategies Guide

**Status**: ✅ Complete
**Date**: October 11, 2025
**Version**: 1.0

---

## Overview

Phase 2 extends Proratio with advanced trading strategies and intelligent portfolio management. This phase introduces mean reversion trading, grid trading for volatile markets, multi-strategy portfolio allocation, and statistical A/B testing framework.

### What's New in Phase 2

- **3 Trading Strategies**: Trend-following (existing), Mean Reversion, Grid Trading
- **Portfolio Manager**: Intelligent capital allocation across strategies
- **Market Regime Detection**: Automatically identifies trending, ranging, and volatile markets
- **A/B Testing Framework**: Statistical comparison of strategy performance
- **40 New Tests**: Comprehensive test coverage for all components

---

## Architecture

### Component Overview

```
Phase 2 Components
├── Strategies (proratio_tradehub/strategies/)
│   ├── Mean Reversion (range-bound markets)
│   ├── Grid Trading (high volatility)
│   └── AI Enhanced (trending markets)
│
├── Orchestration (proratio_tradehub/orchestration/)
│   └── Portfolio Manager
│       ├── Market regime detection
│       ├── Dynamic allocation
│       └── Performance tracking
│
└── Testing (proratio_quantlab/ab_testing/)
    └── Strategy Comparer
        ├── Statistical tests
        ├── Metrics comparison
        └── Automated recommendations
```

---

## Strategies

### 1. Mean Reversion Strategy

**Best for**: Range-bound, sideways markets
**Timeframe**: 1h
**Risk Level**: Medium

#### Logic

Enters trades when price deviates significantly from its mean, expecting reversion.

**Long Entry**:
- RSI < 30 (oversold)
- Price < Bollinger Band lower
- Sufficient volatility (BB width > 2%)
- Volume confirmation
- Optional AI confirmation

**Exit**:
- Price returns to BB middle (mean reversion complete)
- RSI returns to neutral (40-60)
- RSI becomes overbought (> 70)

#### Key Parameters

```python
rsi_oversold = 30          # Entry threshold
rsi_overbought = 70        # Exit threshold
bb_period = 20             # Bollinger Bands period
bb_std = 2.0               # Standard deviations
use_ai_confirmation = True # Require AI consensus
ai_min_confidence = 0.50   # Lower threshold (50%)
```

#### Files

- Core: `proratio_tradehub/strategies/mean_reversion.py`
- Freqtrade: `user_data/strategies/MeanReversionStrategy.py`
- Tests: `tests/test_tradehub/test_grid_trading.py` (13 tests)

---

### 2. Grid Trading Strategy

**Best for**: High volatility, ranging markets
**Timeframe**: 1h
**Risk Level**: Medium-High

#### Logic

Creates a grid of buy/sell orders at predetermined price levels. Profits from price oscillations between grid levels.

**Setup**:
1. Detect high volatility (ATR% > 1.5%)
2. Confirm ranging market (EMA diff < 3%)
3. Calculate grid levels above/below current price
4. Place buy orders at lower grids
5. Place sell orders at upper grids

**Entry**:
- Price reaches a buy grid level
- Grid level not already filled
- Market conditions still suitable

**Exit**:
- Price reaches corresponding sell grid
- Market becomes trending (exit grid)
- Volatility drops below threshold

#### Key Parameters

```python
grid_spacing = 0.02        # 2% between grids
num_grids_above = 5        # Sell grids above
num_grids_below = 5        # Buy grids below
grid_type = "geometric"    # or "arithmetic"
min_volatility_threshold = 0.015  # 1.5% ATR
```

#### Grid Types

**Geometric** (equal percentage):
- Grid 1: $40,000
- Grid 2: $40,000 × 1.02 = $40,800
- Grid 3: $40,000 × 1.04 = $41,600

**Arithmetic** (equal dollar amount):
- Grid 1: $40,000
- Grid 2: $40,000 + $800 = $40,800
- Grid 3: $40,000 + $1,600 = $41,600

#### Files

- Core: `proratio_tradehub/strategies/grid_trading.py`
- Freqtrade: `user_data/strategies/GridTradingStrategy.py`
- Tests: `tests/test_tradehub/test_grid_trading.py` (12 tests)

---

## Portfolio Manager

### Overview

The Portfolio Manager intelligently allocates capital across multiple strategies based on market conditions and performance.

### Features

1. **Market Regime Detection**: Identifies market state
   - Trending Up: Strong uptrend (favor trend-following)
   - Trending Down: Strong downtrend (avoid or short)
   - Ranging: Sideways movement (favor mean reversion)
   - Volatile: High volatility, no trend (favor grid trading)
   - Uncertain: Mixed signals

2. **Allocation Methods**:
   - **Equal**: Simple 1/N allocation
   - **Performance**: Allocate to best performers
   - **Market-Adaptive**: Allocate based on regime suitability
   - **AI-Driven**: Hybrid approach using AI + performance

3. **Dynamic Rebalancing**: Adjusts allocation periodically

4. **Performance Tracking**: Monitors strategy returns

### Usage Example

```python
from proratio_tradehub.orchestration import PortfolioManager
from proratio_tradehub.strategies import (
    MeanReversionStrategy,
    GridTradingStrategy
)

# Initialize portfolio manager
pm = PortfolioManager(
    total_capital=10000,
    allocation_method="market_adaptive",
    rebalance_frequency_hours=24,
    min_strategy_allocation=0.10,  # 10% minimum
    max_strategy_allocation=0.60   # 60% maximum
)

# Register strategies
pm.register_strategy(MeanReversionStrategy(name="MeanReversion"))
pm.register_strategy(GridTradingStrategy(name="GridTrading"))

# Detect market regime
regime = pm.detect_market_regime(dataframe, pair="BTC/USDT")
print(f"Market Regime: {regime.regime_type} ({regime.confidence:.1%})")

# Rebalance portfolio
allocations = pm.rebalance_portfolio(dataframe)

# Get allocation for specific strategy
capital = pm.get_strategy_capital("MeanReversion")
print(f"Mean Reversion Capital: ${capital:.2f}")

# Update performance after trade
pm.update_strategy_performance("MeanReversion", return_pct=0.025)  # 2.5% return

# Get summary
summary = pm.get_portfolio_summary()
print(summary)
```

### Market Regime Detection Logic

```python
# Trending Up
if ADX > 25 and EMA_fast > EMA_slow * 1.03:
    regime = "trending_up"

# Ranging
elif ADX < 20 and abs(EMA_fast - EMA_slow) < 0.02:
    regime = "ranging"

# Volatile
elif ATR% > 2.5% and BB_width > 4%:
    regime = "volatile"
```

### Strategy Suitability Matrix

| Strategy | Trending Up | Trending Down | Ranging | Volatile | Uncertain |
|----------|-------------|---------------|---------|----------|-----------|
| **Trend** | 0.9 ⭐ | 0.3 | 0.4 | 0.5 | 0.6 |
| **Mean Rev** | 0.3 | 0.3 | 0.9 ⭐ | 0.6 | 0.5 |
| **Grid** | 0.4 | 0.4 | 0.7 | 0.9 ⭐ | 0.5 |

⭐ = Best suited

---

## A/B Testing Framework

### Overview

Statistical framework for comparing strategy performance with confidence scores.

### Features

1. **Statistical Tests**:
   - **T-test**: Parametric test for mean returns
   - **Mann-Whitney U**: Non-parametric alternative
   - **Kolmogorov-Smirnov**: Distribution comparison
   - **Variance test**: Risk comparison

2. **Metrics Comparison**:
   - Total return
   - Sharpe ratio
   - Max drawdown
   - Win rate
   - Profit factor
   - Average returns

3. **Automated Recommendations**:
   - High confidence (> 70%): Deploy winner
   - Medium confidence (50-70%): More testing needed
   - Low confidence (< 50%): Insufficient evidence

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

# Example output:
# 🏆 WINNER: MeanReversionStrategy (confidence: 85%)
#
# Key Differences:
#   • Returns: +3.50% (✅ Strategy B)
#   • Sharpe: +0.45 (✅ Strategy B)
#   • Drawdown: +1.20% (✅ Strategy B)
#
# ✅ RECOMMENDATION: Deploy MeanReversionStrategy
#    Strong evidence of superior performance.
```

---

## Backtesting

### Running Phase 2 Backtests

```bash
# Backtest all Phase 2 strategies
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

### Backtest Output

The script generates:

1. **Summary Table**: Side-by-side metrics comparison
2. **A/B Test Results**: Statistical analysis for each pair
3. **JSON Export**: `user_data/backtest_results/phase2_comparison.json`

---

## Testing

### Running Tests

```bash
# Run all Phase 2 tests
pytest tests/test_tradehub/test_grid_trading.py tests/test_tradehub/test_portfolio_manager.py -v

# Run specific test
pytest tests/test_tradehub/test_grid_trading.py::test_geometric_grid_calculation -v

# Run with coverage
pytest tests/test_tradehub/test_grid_trading.py --cov=proratio_tradehub.strategies.grid_trading
```

### Test Coverage

**Grid Trading** (12 tests):
- Initialization
- Grid calculation (geometric/arithmetic)
- Market suitability detection
- Entry/exit signals
- Indicator requirements

**Portfolio Manager** (15 tests):
- Initialization and registration
- Allocation methods (equal/performance/market-adaptive)
- Market regime detection
- Rebalancing logic
- Performance tracking

**Total**: 40 new tests (123 → 163 total)

---

## Best Practices

### Strategy Selection

1. **Trending Markets** (ADX > 25, clear direction)
   → Use **AI-Enhanced Strategy**

2. **Ranging Markets** (ADX < 20, sideways)
   → Use **Mean Reversion Strategy**

3. **Volatile Markets** (ATR% > 2%, wide BB)
   → Use **Grid Trading Strategy**

4. **Uncertain Markets**
   → Use **Portfolio Manager** with market-adaptive allocation

### Portfolio Management

1. **Start Conservative**:
   - Begin with equal allocation
   - Gather 30+ trades per strategy
   - Switch to performance-based after validation

2. **Rebalance Regularly**:
   - Daily (24h) for active trading
   - Weekly for longer timeframes

3. **Monitor Regime Changes**:
   - Strong trend → Reduce mean reversion allocation
   - Volatility spike → Increase grid trading allocation

4. **Performance Tracking**:
   - Log all trades and returns
   - Update performance history after each trade
   - Review allocation monthly

### Risk Management

1. **Grid Trading**:
   - Reduce stake per grid (divide by num_grids)
   - Set stop-loss below lowest grid
   - Monitor for trend breakouts

2. **Mean Reversion**:
   - Tight stop-loss (3%)
   - Confirm volatility before entry
   - Exit quickly if trend emerges

3. **Portfolio-Level**:
   - Max 60% allocation to any single strategy
   - Min 10% allocation to maintain diversification
   - Emergency stop if total drawdown > 10%

---

## Troubleshooting

### Grid Trading Not Entering

**Symptoms**: Strategy detects no signals

**Possible Causes**:
1. Low volatility (ATR% < threshold)
2. Strong trending market
3. Price not at grid level

**Solutions**:
- Lower `min_volatility_threshold` (e.g., 0.01 = 1%)
- Increase `grid_spacing` for wider grids
- Check market conditions with portfolio manager

### Mean Reversion Underperforming

**Symptoms**: Low win rate, frequent losses

**Possible Causes**:
1. Trending market (not ranging)
2. RSI thresholds too tight
3. Insufficient volatility

**Solutions**:
- Only use in ranging markets (ADX < 20)
- Relax RSI thresholds (25/75 instead of 30/70)
- Enable AI confirmation for better entries

### Portfolio Manager Allocation Issues

**Symptoms**: All capital to one strategy

**Possible Causes**:
1. Min/max allocation not set
2. Performance history insufficient
3. Strong market regime favoring one strategy

**Solutions**:
```python
pm = PortfolioManager(
    total_capital=10000,
    min_strategy_allocation=0.15,  # Force 15% minimum
    max_strategy_allocation=0.50   # Cap at 50% maximum
)
```

---

## Performance Expectations

### Mean Reversion Strategy

**Ideal Conditions**:
- Ranging markets (BTC $40k-$42k for weeks)
- RSI oscillating 30-70
- Regular reversions to mean

**Expected Metrics**:
- Win Rate: 55-65%
- Sharpe Ratio: 1.0-1.5
- Max Drawdown: < 8%
- Avg Trade Duration: 12-48 hours

### Grid Trading Strategy

**Ideal Conditions**:
- High volatility (ATR% > 2%)
- Price oscillating in range
- No strong trend

**Expected Metrics**:
- Win Rate: 60-70% (small wins, few losses)
- Sharpe Ratio: 0.8-1.2
- Max Drawdown: < 10%
- Avg Trade Duration: 6-24 hours

### Portfolio Manager

**Expected Behavior**:
- Automatically favors suitable strategies
- Reduces allocation to underperformers
- Maintains diversification (10-60% per strategy)

---

## Next Steps

1. **Run Initial Backtests**:
   ```bash
   python scripts/backtest_phase2_strategies.py --days 180
   ```

2. **Compare with Baseline**:
   - Check if Mean Reversion > AI-Enhanced in ranging markets
   - Check if Grid Trading > AI-Enhanced in volatile markets

3. **Paper Trading**:
   - Deploy best strategy in dry-run mode
   - Monitor for 1-2 weeks
   - Validate performance vs backtest

4. **Production Deployment**:
   - Start with Portfolio Manager (market-adaptive)
   - Small capital (1-5% of total)
   - Monitor daily

---

## References

- [Base Strategy Documentation](BASE_STRATEGY_GUIDE.md)
- [Backtesting Guide](BACKTESTING_GUIDE.md)
- [Risk Management](RISK_MANAGEMENT.md)
- [roadmap.md - Phase 2 Section](roadmap.md#phase-2-advanced-strategies-weeks-5-6---complete)

---

**Status**: ✅ Phase 2 Complete
**Next Phase**: Phase 3 - Machine Learning (FreqAI integration)
**Questions**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
