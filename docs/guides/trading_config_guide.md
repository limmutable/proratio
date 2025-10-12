# Trading Configuration Guide

**Single source of truth for all trading parameters**

All trading variables are centralized in:
- **Code**: [`proratio_utilities/config/trading_config.py`](../proratio_utilities/config/trading_config.py)
- **JSON**: [`proratio_utilities/config/trading_config.json`](../proratio_utilities/config/trading_config.json)

---

## Quick Start

### View Current Configuration

```python
from proratio_utilities.config.trading_config import get_trading_config

config = get_trading_config()
config.print_summary()
```

### Load from JSON File

```python
from pathlib import Path
from proratio_utilities.config.trading_config import TradingConfig

config = TradingConfig.load_from_file(Path('proratio_utilities/config/trading_config.json'))
config.print_summary()
```

### Modify and Save

```python
config = get_trading_config()

# Adjust risk parameters
config.risk.max_loss_per_trade_pct = 1.5  # More conservative
config.risk.max_concurrent_positions = 5   # More positions

# Adjust AI settings
config.ai.min_confidence = 0.70  # Higher confidence threshold

# Save to file
config.save_to_file(Path('proratio_utilities/config/my_config.json'))
```

---

## Configuration Sections

### 1. Risk Management (`config.risk`)

Controls all risk limits and safety mechanisms.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_loss_per_trade_pct` | 2.0 | Maximum loss per trade (% of portfolio) |
| `max_position_size_pct` | 10.0 | Maximum position size (% of portfolio) |
| `min_position_size_pct` | 1.0 | Minimum position size (% of portfolio) |
| `max_total_drawdown_pct` | 10.0 | **Emergency stop** - halt trading at this drawdown |
| `warning_drawdown_pct` | 7.0 | Warning threshold (approaching danger zone) |
| `max_concurrent_positions` | 3 | Maximum number of open positions |
| `max_positions_per_pair` | 1 | Max positions per trading pair |
| `max_leverage` | 1.0 | Leverage (1.0 = spot only, >1.0 = futures) |

**Example Adjustments**:
```python
# Conservative trader
config.risk.max_loss_per_trade_pct = 1.0
config.risk.max_total_drawdown_pct = 5.0

# Aggressive trader
config.risk.max_loss_per_trade_pct = 3.0
config.risk.max_concurrent_positions = 5
```

---

### 2. Position Sizing (`config.position_sizing`)

Controls how position sizes are calculated.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `method` | 'ai_weighted' | Sizing method: `fixed_fraction`, `risk_based`, `kelly`, `ai_weighted`, `atr_based` |
| `base_risk_pct` | 2.0 | Base risk percentage for calculations |
| `ai_confidence_min` | 0.60 | Minimum AI confidence to trade (60%) |
| `ai_confidence_multiplier_min` | 0.8 | Stake multiplier at 60% confidence (0.8x) |
| `ai_confidence_multiplier_max` | 1.2 | Stake multiplier at 100% confidence (1.2x) |
| `atr_period` | 14 | ATR calculation period |
| `atr_multiplier` | 2.0 | ATR multiplier for stop-loss distance |
| `kelly_fraction` | 0.5 | Kelly fraction (0.5 = half-Kelly for safety) |

**Position Sizing Methods**:

1. **`fixed_fraction`**: Always use same % of portfolio
2. **`risk_based`**: Size based on stop-loss distance (recommended)
3. **`kelly`**: Kelly Criterion (requires win rate history)
4. **`ai_weighted`**: Risk-based + AI confidence multiplier (recommended for AI strategies)
5. **`atr_based`**: ATR-based volatility adjustment

**Example Adjustments**:
```python
# Lower AI confidence threshold for more trades
config.position_sizing.ai_confidence_min = 0.55

# More aggressive position sizing with AI
config.position_sizing.ai_confidence_multiplier_max = 1.5  # Up to 1.5x stake

# Use pure risk-based sizing (no AI adjustment)
config.position_sizing.method = 'risk_based'
```

---

### 3. Strategy Parameters (`config.strategy`)

Controls technical indicators and strategy behavior.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `strategy_name` | 'AIEnhancedStrategy' | Strategy class name |
| `timeframe` | '1h' | Trading timeframe (1h, 4h, 1d) |
| `pairs` | ['BTC/USDT', 'ETH/USDT'] | Trading pairs |
| `ema_fast_period` | 20 | Fast EMA period |
| `ema_slow_period` | 50 | Slow EMA period |
| `rsi_period` | 14 | RSI calculation period |
| `rsi_buy_threshold` | 30 | RSI buy threshold |
| `rsi_sell_threshold` | 70 | RSI sell threshold |
| `atr_period` | 14 | ATR period |
| `adx_period` | 14 | ADX period |
| `adx_trend_threshold` | 20.0 | ADX threshold for trending market |
| `roi_levels` | {0: 0.15, 60: 0.08, 120: 0.04} | Take-profit levels (minutes: %) |
| `stoploss_pct` | -0.04 | Stop-loss percentage (4% loss) |
| `trailing_stop_enabled` | true | Enable trailing stop |
| `trailing_stop_positive` | 0.015 | Activate trailing at 1.5% profit |
| `trailing_stop_positive_offset` | 0.025 | Trail after 2.5% profit |

**Example Adjustments**:
```python
# Trade more pairs
config.strategy.pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT']

# Faster EMA crossover (more signals, more noise)
config.strategy.ema_fast_period = 10
config.strategy.ema_slow_period = 30

# Tighter stop-loss
config.strategy.stoploss_pct = -0.03  # 3%

# More aggressive take-profit
config.strategy.roi_levels = {
    "0": 0.20,   # 20% immediately
    "30": 0.10,  # 10% after 30 min
    "60": 0.05   # 5% after 60 min
}
```

---

### 4. AI Configuration (`config.ai`)

Controls AI signal generation and consensus.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `chatgpt_weight` | 0.40 | ChatGPT weight (technical analysis) |
| `claude_weight` | 0.35 | Claude weight (risk assessment) |
| `gemini_weight` | 0.25 | Gemini weight (sentiment) |
| `min_consensus_score` | 0.60 | Minimum weighted consensus (60%) |
| `min_confidence` | 0.60 | Minimum AI confidence to trade |
| `require_all_providers` | false | Require all 3 providers (or use dynamic reweighting) |
| `signal_cache_minutes` | 60 | Cache AI signals for X minutes |
| `lookback_candles` | 50 | Candles to send to AI for context |
| `chatgpt_model` | null | Override ChatGPT model (auto-detect if null) |
| `claude_model` | null | Override Claude model (auto-detect if null) |
| `gemini_model` | null | Override Gemini model (auto-detect if null) |

**Provider Weights**:
- Must sum to 1.0
- Adjust based on which AI you trust most
- Set to 0 to disable a provider

**Example Adjustments**:
```python
# Equal weights for all providers
config.ai.chatgpt_weight = 0.33
config.ai.claude_weight = 0.34
config.ai.gemini_weight = 0.33

# Higher confidence requirement (fewer but better signals)
config.ai.min_confidence = 0.75

# Require all providers (no dynamic reweighting)
config.ai.require_all_providers = True

# Use specific models
config.ai.chatgpt_model = 'gpt-5-nano-2025-08-07'
config.ai.claude_model = 'claude-sonnet-4-20250514'
```

---

### 5. Execution Settings (`config.execution`)

Controls order execution and trading mode.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `trading_mode` | 'dry_run' | **'dry_run'** (paper) or **'live'** (real money) |
| `exchange` | 'binance' | Exchange name |
| `entry_order_type` | 'limit' | Entry order type (limit or market) |
| `exit_order_type` | 'limit' | Exit order type |
| `stoploss_order_type` | 'market' | Stop-loss order type |
| `stoploss_on_exchange` | false | Place stop-loss on exchange |
| `order_time_in_force` | 'GTC' | Order time-in-force (GTC or IOC) |
| `starting_balance` | 10000.0 | Starting balance (USDT) |
| `stake_currency` | 'USDT' | Stake currency |
| `stake_amount` | 100.0 | Base stake amount per trade |

**⚠️ IMPORTANT**: Always start with `dry_run` mode!

**Example Adjustments**:
```python
# Paper trading with higher balance
config.execution.starting_balance = 50000.0
config.execution.stake_amount = 500.0

# Use market orders for faster execution
config.execution.entry_order_type = 'market'
config.execution.exit_order_type = 'market'

# ⚠️ LIVE TRADING (use with caution!)
config.execution.trading_mode = 'live'
config.execution.starting_balance = 1000.0  # Start small!
```

---

## Common Configuration Scenarios

### Conservative Trader

```python
config.risk.max_loss_per_trade_pct = 1.0        # 1% max loss
config.risk.max_total_drawdown_pct = 5.0        # Stop at 5% drawdown
config.risk.max_concurrent_positions = 2         # Fewer positions
config.position_sizing.base_risk_pct = 1.0      # Lower risk per trade
config.ai.min_confidence = 0.75                 # Higher confidence required
```

### Aggressive Trader

```python
config.risk.max_loss_per_trade_pct = 3.0        # 3% max loss
config.risk.max_concurrent_positions = 5         # More positions
config.position_sizing.base_risk_pct = 3.0      # Higher risk per trade
config.position_sizing.ai_confidence_min = 0.55 # Lower confidence threshold
config.ai.min_confidence = 0.55                 # Accept more signals
```

### High-Frequency Scalper

```python
config.strategy.timeframe = '15m'               # Faster timeframe
config.strategy.ema_fast_period = 5
config.strategy.ema_slow_period = 15
config.strategy.roi_levels = {
    "0": 0.05,   # Quick 5% profit
    "15": 0.02,  # Or 2% after 15 min
}
config.strategy.stoploss_pct = -0.02           # Tight 2% stop
```

### Long-Term Trend Follower

```python
config.strategy.timeframe = '1d'                # Daily timeframe
config.strategy.ema_fast_period = 50
config.strategy.ema_slow_period = 200
config.strategy.roi_levels = {
    "0": 0.50,      # 50% profit
    "1440": 0.30,   # 30% after 1 day
    "2880": 0.20    # 20% after 2 days
}
config.strategy.stoploss_pct = -0.10           # Wider 10% stop
```

---

## Validation

Always validate configuration before using:

```python
config = get_trading_config()

# Validate
errors = config.validate()
if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("✅ Configuration valid")
    config.print_summary()
```

---

## Using in Code

### In Strategies

```python
from proratio_utilities.config.trading_config import get_trading_config

class AIEnhancedStrategy(IStrategy):
    def __init__(self, config: dict):
        super().__init__(config)

        # Load trading config
        trading_config = get_trading_config()

        # Use parameters
        self.ai_min_confidence = trading_config.position_sizing.ai_confidence_min
        self.timeframe = trading_config.strategy.timeframe
        self.stoploss = trading_config.strategy.stoploss_pct
```

### In Risk Manager

```python
from proratio_utilities.config.trading_config import get_trading_config
from proratio_tradehub.risk.risk_manager import RiskManager, RiskLimits

trading_config = get_trading_config()

# Create risk manager from config
risk_limits = RiskLimits(
    max_loss_per_trade_pct=trading_config.risk.max_loss_per_trade_pct,
    max_total_drawdown_pct=trading_config.risk.max_total_drawdown_pct,
    max_concurrent_positions=trading_config.risk.max_concurrent_positions,
)

risk_manager = RiskManager(risk_limits)
```

### In Backtests

```python
from proratio_utilities.config.trading_config import get_trading_config
from proratio_quantlab import BacktestEngine

config = get_trading_config()

engine = BacktestEngine()
results = engine.backtest(
    strategy=config.strategy.strategy_name,
    timeframe=config.strategy.timeframe,
    start_date='2024-01-01',
    end_date='2024-12-31',
    pairs=config.strategy.pairs,
    initial_balance=config.execution.starting_balance,
    stake_amount=config.execution.stake_amount
)
```

---

## Best Practices

1. **Always use version control** for `trading_config.json`
2. **Test changes in dry-run mode** before live trading
3. **Document why you changed parameters** (comments in JSON or git commit message)
4. **Start conservative** and gradually increase risk as you gain confidence
5. **Never change config during active trades** - stop trading first
6. **Backup working configs** before making major changes
7. **Validate after changes**: `config.validate()`

---

## File Locations

- **Python config**: [`proratio_utilities/config/trading_config.py`](../proratio_utilities/config/trading_config.py)
- **JSON config**: [`proratio_utilities/config/trading_config.json`](../proratio_utilities/config/trading_config.json)
- **This guide**: [`docs/trading_config_guide.md`](trading_config_guide.md)

---

**Remember**: Paper trade for at least 1-2 weeks before considering live trading!
