# Proratio Strategy Development Guide

Complete guide for developing and deploying trading strategies in the Proratio system.

---

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Strategy Layers](#strategy-layers)
- [Creating a New Strategy](#creating-a-new-strategy)
- [Example: Mean Reversion Strategy](#example-mean-reversion-strategy)
- [Testing Strategies](#testing-strategies)
- [Backtesting](#backtesting)
- [Best Practices](#best-practices)

---

## Architecture Overview

### 3-Layer Strategy Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   STRATEGY LAYERS                        │
└──────────────────────────────────────────────────────────┘

Layer 1: SIGNAL GENERATION (proratio_signals/)
├── Purpose: Generate raw trading signals
├── Examples: AI consensus, technical indicators, sentiment
└── Output: Signal objects (direction + confidence)

Layer 2: STRATEGY LOGIC (proratio_tradehub/strategies/)
├── Purpose: Business logic combining signals + indicators
├── Examples: Trend following, mean reversion, grid trading
└── Output: Trade recommendations with sizing

Layer 3: EXECUTION ADAPTERS (user_data/strategies/)
├── Purpose: Freqtrade-specific implementations
├── Examples: Freqtrade wrappers for strategies
└── Output: Freqtrade-compatible strategy classes
```

---

## Strategy Layers

### Layer 1: Signal Generation (`proratio_signals/`)

**Purpose:** Generate raw signals from various sources

**Components:**
- `orchestrator.py` - Multi-AI consensus mechanism
- `llm_providers/` - ChatGPT, Claude, Gemini integrations
- `signal_generators/` - Technical, sentiment, combined signals

**When to use:**
- Adding new AI providers
- Creating new signal sources
- Combining multiple signal types

---

### Layer 2: Strategy Logic (`proratio_tradehub/strategies/`)

**Purpose:** Implement trading strategy business logic

**Base Class:** `BaseStrategy`

**Required Methods:**
- `should_enter_long()` - Long entry logic
- `should_enter_short()` - Short entry logic
- `should_exit()` - Exit logic

**Optional Methods:**
- `calculate_position_size()` - Custom position sizing
- `calculate_stop_loss()` - Custom stop-loss
- `calculate_take_profit()` - Custom take-profit
- `get_required_indicators()` - List required indicators

**When to use:**
- Creating new trading strategies
- Combining multiple signals
- Implementing custom risk logic

---

### Layer 3: Execution Adapters (`user_data/strategies/`)

**Purpose:** Freqtrade-specific wrappers

**Base Class:** `IStrategy` (from Freqtrade)

**Required Methods:**
- `populate_indicators()` - Add technical indicators
- `populate_entry_trend()` - Define entry signals
- `populate_exit_trend()` - Define exit signals

**Optional Methods:**
- `custom_exit()` - Custom exit logic
- `custom_stake_amount()` - Adjust position size
- `confirm_trade_entry()` - Final entry confirmation
- `leverage()` - Set leverage

**When to use:**
- Connecting Proratio strategies to Freqtrade
- Backtesting with Freqtrade
- Paper trading / live trading

---

## Creating a New Strategy

### Step 1: Define Strategy Logic

Create file in `proratio_tradehub/strategies/`:

```python
# proratio_tradehub/strategies/my_strategy.py

from proratio_tradehub.strategies import BaseStrategy, TradeSignal
import pandas as pd

class MyStrategy(BaseStrategy):
    def __init__(self, param1=10, param2=0.5):
        super().__init__(name="MyStrategy")
        self.param1 = param1
        self.param2 = param2

    def should_enter_long(self, pair: str, dataframe: pd.DataFrame, **kwargs) -> TradeSignal:
        # Your long entry logic here
        current_price = dataframe['close'].iloc[-1]

        # Example: Simple condition
        if some_condition:
            return TradeSignal(
                direction='long',
                confidence=0.8,
                entry_price=current_price,
                reasoning="Entry condition met"
            )

        return TradeSignal(direction='neutral', confidence=0.0)

    def should_enter_short(self, pair: str, dataframe: pd.DataFrame, **kwargs) -> TradeSignal:
        # Your short entry logic here
        return TradeSignal(direction='neutral', confidence=0.0)

    def should_exit(self, pair: str, dataframe: pd.DataFrame, current_position: dict, **kwargs) -> TradeSignal:
        # Your exit logic here
        return TradeSignal(direction='neutral', confidence=0.0)

    def get_required_indicators(self) -> list:
        return ['rsi', 'ema_20', 'volume_ma']
```

### Step 2: Create Freqtrade Adapter

Create file in `user_data/strategies/`:

```python
# user_data/strategies/MyStrategyAdapter.py

from freqtrade.strategy import IStrategy
import pandas as pd
import pandas_ta as ta

from proratio_tradehub.strategies.my_strategy import MyStrategy

class MyStrategyAdapter(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = '4h'

    minimal_roi = {"0": 0.04}
    stoploss = -0.02

    def __init__(self, config: dict):
        super().__init__(config)
        self.strategy = MyStrategy(param1=10, param2=0.5)

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        # Add required indicators
        dataframe['rsi'] = ta.rsi(dataframe['close'], length=14)
        dataframe['ema_20'] = ta.ema(dataframe['close'], length=20)
        dataframe['volume_ma'] = ta.sma(dataframe['volume'], length=20)
        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        pair = metadata['pair']
        signal = self.strategy.should_enter_long(pair, dataframe)

        if signal.should_trade():
            dataframe.loc[dataframe.index[-1], 'enter_long'] = 1
            print(f"LONG ENTRY: {pair} - {signal.reasoning}")

        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        return dataframe
```

### Step 3: Register Strategy

Update `proratio_tradehub/strategies/__init__.py`:

```python
from .my_strategy import MyStrategy

__all__ = ['BaseStrategy', 'TradeSignal', 'MeanReversionStrategy', 'MyStrategy']
```

---

## Example: Mean Reversion Strategy

### Overview

**Strategy:** Enter when price deviates from mean, exit when it returns
**Best for:** Range-bound markets
**Avoid:** Strong trending markets

### Entry Logic

**Long Entry:**
- RSI < 30 (oversold)
- Price < Lower Bollinger Band
- AI confirms bullish (optional)

**Short Entry:**
- RSI > 70 (overbought)
- Price > Upper Bollinger Band
- AI confirms bearish (optional)

### Exit Logic

- Price returns to mean (middle BB)
- RSI returns to neutral (40-60)
- Stop-loss or take-profit hit

### Implementation

See complete implementation:
- Strategy: `proratio_tradehub/strategies/mean_reversion.py`
- Adapter: `user_data/strategies/MeanReversionAdapter.py`

---

## Testing Strategies

### Unit Testing

Create tests in `tests/test_tradehub/test_strategies/`:

```python
# tests/test_tradehub/test_strategies/test_mean_reversion.py

import pytest
import pandas as pd
from proratio_tradehub.strategies import MeanReversionStrategy

def test_mean_reversion_long_entry():
    strategy = MeanReversionStrategy()

    # Create test dataframe with oversold conditions
    df = pd.DataFrame({
        'close': [100, 95, 90],
        'rsi': [35, 28, 25],
        'bb_lower': [92, 91, 90],
        'bb_middle': [100, 100, 100],
        'bb_upper': [108, 109, 110]
    })

    signal = strategy.should_enter_long('BTC/USDT', df)

    assert signal.direction == 'long'
    assert signal.confidence > 0.0
```

### Manual Testing

```python
# Test strategy interactively
from proratio_tradehub.strategies import MeanReversionStrategy
import pandas as pd

strategy = MeanReversionStrategy(use_ai_confirmation=False)

# Load sample data
from proratio_utilities.data.loaders import DataLoader
loader = DataLoader()
df = loader.load_ohlcv('binance', 'BTC/USDT', '4h', limit=100)

# Add indicators (RSI, Bollinger Bands)
# ... add indicators here ...

# Test entry signal
signal = strategy.should_enter_long('BTC/USDT', df)
print(signal.reasoning)
```

---

## Backtesting

### Quick Backtest

```bash
# Backtest mean reversion strategy
freqtrade backtesting \
  --strategy MeanReversionAdapter \
  --timeframe 4h \
  --timerange 20250101-20251008 \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data
```

### Compare Against Baseline

```bash
# Compare mean reversion vs simple test strategy
uv run python scripts/backtest_ai_strategy.py \
  --strategy1 SimpleTestStrategy \
  --strategy2 MeanReversionAdapter \
  --timeframe 4h \
  --months 6
```

### Hyperparameter Optimization

```bash
# Optimize strategy parameters
freqtrade hyperopt \
  --strategy MeanReversionAdapter \
  --hyperopt-loss SharpeHyperOptLoss \
  --epochs 100 \
  --timerange 20250101-20251008 \
  --userdir user_data
```

---

## Best Practices

### 1. Separation of Concerns

✅ **Do:**
- Keep signal generation in `proratio_signals/`
- Keep strategy logic in `proratio_tradehub/strategies/`
- Keep Freqtrade adapters in `user_data/strategies/`

❌ **Don't:**
- Mix AI logic into Freqtrade adapters
- Put strategy logic in signal generators
- Couple strategy to specific execution framework

---

### 2. Strategy Design

✅ **Do:**
- Define clear entry/exit conditions
- Include reasoning in TradeSignal
- Make parameters configurable
- Document required indicators
- Handle missing data gracefully

❌ **Don't:**
- Hardcode magic numbers
- Mix multiple strategy types in one class
- Rely on specific data formats
- Ignore edge cases (first candle, missing indicators)

---

### 3. Testing

✅ **Do:**
- Write unit tests for entry/exit logic
- Backtest on multiple timeframes
- Test in different market conditions (trending, ranging, volatile)
- Paper trade before going live
- Compare against baseline

❌ **Don't:**
- Skip backtesting
- Optimize on test data
- Trust backtest results without paper trading
- Deploy without monitoring

---

### 4. Position Sizing

✅ **Do:**
- Scale position size by confidence
- Enforce maximum position size
- Consider account balance
- Adjust for volatility (use ATR)

❌ **Don't:**
- Use fixed position sizes
- Ignore risk limits
- Size positions too large
- Forget stop-losses

---

### 5. Performance Monitoring

✅ **Do:**
- Log all trade decisions
- Track win rate, Sharpe ratio, drawdown
- Monitor vs backtest expectations
- Review failed trades
- Adjust parameters based on performance

❌ **Don't:**
- Set and forget
- Ignore underperformance
- Overtrade in losses
- Change strategy mid-session

---

## Strategy Templates

### Template 1: Technical Indicator Strategy

Use when: Implementing pure technical strategies (no AI)

**Example:** Moving average crossover, Momentum, Breakout

---

### Template 2: AI-Enhanced Strategy

Use when: Combining technical indicators with AI signals

**Example:** Mean reversion (current), trend following with AI

---

### Template 3: Multi-Strategy Portfolio

Use when: Running multiple strategies simultaneously

**Example:** Allocate 50% to trend, 30% to mean reversion, 20% to grid

---

## Common Pitfalls & Troubleshooting

### Issue 1: Backtest Shows 0 Trades (But Opportunities Exist)

**Problem:** Backtest completes but shows 0 trades executed, even when manual analysis shows entry conditions were met.

**Root Cause:** `populate_entry_trend()` only checks the last row instead of all rows.

**Incorrect Implementation:**
```python
def populate_entry_trend(self, dataframe, metadata):
    signal = self.strategy.should_enter_long(pair, dataframe)
    if signal.should_trade():
        dataframe.loc[dataframe.index[-1], 'enter_long'] = 1  # ❌ Only marks last row
    return dataframe
```

**Correct Implementation:**
```python
def populate_entry_trend(self, dataframe, metadata):
    # Initialize columns
    dataframe['enter_long'] = 0

    # Evaluate conditions on ALL rows (vectorized)
    long_conditions = (
        (dataframe['rsi'] < self.rsi_oversold.value) &
        (dataframe['close'] < dataframe['bb_lower'])
    )

    # Mark all rows that meet criteria
    dataframe.loc[long_conditions, 'enter_long'] = 1  # ✅ Marks all qualifying rows
    return dataframe
```

**Why This Happens:**
- Freqtrade backtesting passes the FULL dataframe to `populate_entry_trend()`
- You must evaluate ALL rows to find all entry opportunities
- Using `.iloc[-1]` only checks the most recent candle
- Use vectorized pandas operations for performance

**Diagnosis Command:**
```bash
# Create diagnostic script to check if opportunities exist
PYTHONPATH=/path/to/proratio:$PYTHONPATH uv run python scripts/diagnose_mean_reversion.py
```

---

### Issue 2: Strategy Works in Dry-run But Not Backtest

**Problem:** Live dry-run shows trades, but backtest shows different results.

**Possible Causes:**
1. **Lookahead bias** - Using future data in indicators
2. **Different data sources** - Live uses exchange API, backtest uses downloaded data
3. **Indicator calculation differences** - pandas_ta vs talib

**Solution:**
- Ensure indicators don't use future data
- Use same data source for both (download and backtest from same exchange)
- Verify indicator calculations match between live and backtest

---

## Additional Resources

- [backtesting_guide.md](./backtesting_guide.md) - Complete backtesting guide
- [TRADING_CONFIG_GUIDE.md](./TRADING_CONFIG_GUIDE.md) - Configuration reference
- [Freqtrade Strategy Docs](https://www.freqtrade.io/en/stable/strategy-customization/)

---

**Last Updated:** 2025-10-08
