# Proratio: Core Concepts and Technical Details

**Last Updated**: October 16, 2025

This document provides detailed explanations of Proratio's strategies, technologies, and trading concepts for readers with finance and analytical backgrounds.

---

## Table of Contents

1. [What is Algorithmic Trading?](#what-is-algorithmic-trading)
2. [Multi-AI Consensus System](#multi-ai-consensus-system)
3. [Machine Learning Strategies](#machine-learning-strategies)
4. [Trading Strategies Explained](#trading-strategies-explained)
5. [Risk Management Framework](#risk-management-framework)
6. [Technical Architecture](#technical-architecture)
7. [Key Technologies](#key-technologies)
8. [Backtesting and Validation](#backtesting-and-validation)

---

## What is Algorithmic Trading?

**Algorithmic trading** (or "algo trading") uses computer programs to execute trades automatically based on predefined rules. Instead of manually watching charts and placing orders, traders write code that:

1. **Monitors market data** in real-time (prices, volumes, trends)
2. **Analyzes conditions** using technical indicators and patterns
3. **Makes decisions** about when to buy or sell
4. **Executes trades** automatically through exchange APIs

**Benefits:**
- **Speed**: Computers react in milliseconds vs. human seconds
- **Consistency**: No emotional decisions or fatigue
- **Backtesting**: Test strategies on years of historical data before risking real money
- **24/7 Operation**: Crypto markets never sleep; algorithms don't either

**Proratio's Approach:**
Proratio combines traditional quantitative analysis (math-based indicators) with modern AI language models (ChatGPT, Claude, Gemini) to make trading decisions. Think of it as having three expert analysts working together, plus machine learning models trained on historical patterns.

---

## Multi-AI Consensus System

### How It Works

Instead of relying on a single AI, Proratio asks **three different AI models** (ChatGPT, Claude, Gemini) to analyze the same market data and provide trading recommendations. Each AI:

1. **Receives market data**: Recent price history, technical indicators, volume patterns
2. **Analyzes context**: Market trends, momentum, support/resistance levels
3. **Provides a signal**: Buy, Sell, or Neutral with confidence percentage
4. **Explains reasoning**: Why this signal makes sense

### Consensus Mechanism

Proratio then combines these three opinions using a **weighted voting system**:

- **High Agreement** (all 3 AIs agree): Strong signal → larger position size
- **Moderate Agreement** (2 out of 3 agree): Medium signal → normal position size
- **Disagreement** (no consensus): Weak signal → skip trade or small position
- **Conflict** (opposite directions): No trade → wait for clarity

**Example:**
```
ChatGPT: BUY (75% confidence) - "Strong uptrend, RSI oversold"
Claude:  BUY (68% confidence) - "Bullish momentum, volume increasing"
Gemini:  NEUTRAL (40% confidence) - "Mixed signals, sideways movement"

→ Result: MODERATE BUY signal (2/3 agree, combined 61% confidence)
→ Action: Enter position at 0.7x normal size (reduced due to Gemini's uncertainty)
```

### Why Multiple AIs?

- **Reduces false signals**: One AI might be wrong, but three rarely are
- **Different perspectives**: Each AI model has different training data and biases
- **Robustness**: If one AI service fails, trading continues with remaining two
- **Quality over quantity**: Fewer trades, but higher confidence

---

## Machine Learning Strategies

### What is Machine Learning in Trading?

**Machine learning (ML)** trains computer models to recognize patterns in historical data and predict future price movements. Unlike traditional indicators (which use fixed formulas), ML models **learn** what patterns historically led to profitable trades.

### Proratio's ML Approach: Ensemble Learning

Proratio uses **three different types** of ML models working together:

#### 1. LSTM Neural Networks
**What it is**: Deep learning model specialized for time-series data (sequences of prices over time).

**How it works**:
- Analyzes the last 24-50 candles (price bars) as a sequence
- Learns temporal patterns: "When price moves like THIS, it usually moves like THAT next"
- Captures complex non-linear relationships

**Strengths**: Best at capturing long-term trends and momentum patterns

#### 2. LightGBM (Gradient Boosting)
**What it is**: Tree-based model that makes decisions using "if-then" rules.

**How it works**:
- Looks at current indicators (RSI, MACD, Bollinger Bands, etc.)
- Creates decision rules: "If RSI < 30 AND price < lower_band AND volume > average, then BUY"
- Learns which combinations of conditions work best

**Strengths**: Fast predictions, handles many features, good at finding thresholds

#### 3. XGBoost (Extreme Gradient Boosting)
**What it is**: Another tree-based model, more robust to outliers.

**How it works**:
- Similar to LightGBM but with different mathematical optimization
- Better at handling unusual market conditions
- More conservative predictions

**Strengths**: Reduces overfitting, generalizes well to new data

### Ensemble Method: Stacking

Instead of choosing one "best" model, Proratio uses **stacking**:

1. **Train all three models** on historical data
2. **Collect their predictions** on validation data
3. **Train a meta-model** (Ridge regression) that learns:
   - When to trust LSTM more (trending markets)
   - When to trust LightGBM more (range-bound markets)
   - How to combine their predictions optimally

**Result**: ~10-20% better predictions than any single model alone.

### Feature Engineering

Proratio calculates **65 technical features** from raw price data:

**Price-based**:
- Returns (% change), log returns, volatility
- Support/resistance levels, pivot points

**Momentum indicators**:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Stochastic oscillator

**Trend indicators**:
- Moving averages (EMA, SMA)
- ADX (Average Directional Index)
- Ichimoku Cloud

**Volume indicators**:
- OBV (On-Balance Volume)
- Volume moving averages
- Volume rate of change

**Volatility indicators**:
- Bollinger Bands
- ATR (Average True Range)
- Standard deviation

**Temporal features**:
- Hour of day, day of week
- Time since last high/low

These features help ML models understand market context beyond just price.

---

## Trading Strategies Explained

**Note**: All strategies are tracked in the central Strategy Registry ([strategies/registry.json](../strategies/registry.json)). Use `./start.sh strategy list` to see current active strategies.

### 1. Hybrid ML+LLM Strategy (a014_hybrid-ml-llm)

**Status**: ✅ Active | **ID**: a014 | **Category**: AI-Enhanced

**Concept**: Combine quantitative ML predictions with qualitative AI analysis.

**How it works**:
1. **ML Ensemble** analyzes historical patterns → predicts price direction (UP/DOWN) with confidence
2. **LLM Consensus** analyzes current market context → provides trading signal (BUY/SELL/NEUTRAL) with reasoning
3. **Agreement Scoring** checks if ML and LLM agree on direction
4. **Signal Strength** classification:
   - **VERY_STRONG**: Perfect agreement (ML 75%+, LLM 75%+, 85%+ agreement) → 1.5x position
   - **STRONG**: Good agreement (ML 65%+, LLM 65%+, 70%+ agreement) → 1.0x position
   - **MODERATE**: ML confident, LLM uncertain → 0.5x position
   - **WEAK**: Low confidence → skip trade
   - **CONFLICT**: Opposite predictions → skip trade

**When to use**: Markets with both clear technical patterns AND narrative context (news, sentiment).

**Performance**: Phase 4.6 validated - all 3 LLM providers (ChatGPT, Claude, Gemini) working correctly.

**Expected**: 65-70% win rate, Sharpe ratio 2.0-2.5

**Implementation**: [strategies/active/a014_hybrid-ml-llm/strategy.py](../strategies/active/a014_hybrid-ml-llm/strategy.py)

### 2. Mean Reversion Strategy v2 (355c_mean-reversion)

**Status**: ✅ Active | **ID**: 355c | **Category**: Mean Reversion

**Concept**: "What goes up must come down" - prices revert to average.

**How it works**:
- Uses RSI and Bollinger Bands to identify overbought/oversold conditions
- **Buy signal**: RSI < 30 (oversold) AND price touches lower Bollinger Band
- **Sell signal**: RSI > 70 (overbought) AND price touches upper Bollinger Band
- Assumes price will bounce back to the middle (mean)
- **Stop loss**: 3.5% (improved from v1's 2%)

**When to use**: Range-bound, sideways markets.

**Performance**: 56% win rate (improved from v1's 38%)

**Pros**: Catches reversals, good in stable markets
**Cons**: Fails in strong trends (keeps buying a falling knife)

**Implementation**: [strategies/active/355c_mean-reversion/strategy.py](../strategies/active/355c_mean-reversion/strategy.py)

### 3. Grid Trading Strategy (f662_grid-trading)

**Status**: ✅ Active | **ID**: f662 | **Category**: Grid Trading

**Concept**: Place buy/sell orders at regular price intervals.

**How it works**:
- Sets up a "grid" of price levels (e.g., every 0.5% for cryptocurrency)
- Places buy orders below current price, sell orders above
- As price oscillates, trades execute automatically
- Profits from price volatility regardless of direction

**Example**:
```
Current price: $45,000
Grid spacing: 0.5% (10 grids)
Grid: $44,775, $44,550, $44,325 (buys) | $45,225, $45,450, $45,675 (sells)

Price drops to $44,550 → buy order executes
Price rises to $45,450 → sell order executes (+$900 profit)
```

**When to use**: Choppy, range-bound markets with high volatility.

**Performance**: 73.7% win rate, Sharpe 0.8 (19 trades backtested)

**Pros**: Profits from volatility, no trend prediction needed
**Cons**: Risk of large loss in strong trends, capital intensive

**Implementation**: [strategies/active/f662_grid-trading/strategy.py](../strategies/active/f662_grid-trading/strategy.py)

---

### Archived Strategies

The following strategies have been superseded and are no longer active. They are kept for reference and historical analysis.

#### Mean Reversion v1 (8f5e_mean-reversion-v1)
**Status**: 📦 Archived (2025-09-20)
**Reason**: Stop loss too tight (2%), replaced by v2 with 3.5% stop loss
**Performance**: 38% win rate → Replaced by v2 with 56% win rate

#### FreqAI Strategy (c7f9_freqai)
**Status**: 📦 Archived (2025-10-16)
**Reason**: Legacy ML approach replaced by custom ensemble (a014)
**Note**: Used Freqtrade's FreqAI module, superseded by Hybrid ML+LLM strategy

#### AI Enhanced Strategy (6347_ai-enhanced)
**Status**: 📦 Archived (2025-10-16)
**Reason**: Early prototype replaced by full Hybrid ML+LLM strategy (a014)
**Note**: Initial AI integration experiment, evolved into current production system

---

### Strategy Development

**Want to create a new strategy?**
1. See [Strategy Development Guide](guides/strategy_development_guide.md)
2. Use Strategy Registry: `./start.sh strategy list`
3. Validate before deployment: `./start.sh strategy validate <name>`

---

## Risk Management Framework

Proratio implements **6 layers** of risk controls:

### Layer 1: Position Sizing
- **Max risk per trade**: 2% of portfolio
- **Position size calculation**: Kelly Criterion or AI-weighted
- **Dynamic adjustment**: Larger positions for high-confidence signals

### Layer 2: Stop Loss
- **Fixed stop**: 2-3.5% below entry (depends on strategy)
- **Trailing stop**: Follows price up, locks in profits
- **ATR-based stop**: Adapts to volatility (wider stops in volatile markets)

### Layer 3: Take Profit
- **Target profit**: 5-10% above entry
- **Partial exits**: Take 50% profit at first target, let rest run
- **Risk/reward ratio**: Minimum 2:1 (risk $100 to make $200)

### Layer 4: Portfolio Limits
- **Max open trades**: 2-3 concurrent positions
- **Max drawdown**: 10% → halt trading if portfolio drops 10%
- **Daily loss limit**: 5% → stop trading for the day

### Layer 5: Market Conditions
- **Volatility filter**: Skip trades when volatility > threshold (too risky)
- **Volume filter**: Skip trades when volume < average (low liquidity)
- **Spread filter**: Skip trades when bid-ask spread too wide (poor execution)

### Layer 6: AI Confidence Threshold
- **Minimum confidence**: 65% combined confidence required
- **Agreement score**: 70% agreement required between ML and LLM
- **Conflict resolution**: Always skip trades when ML and LLM disagree

**Emergency Stop**: Manual override to close all positions immediately.

---

## Technical Architecture

### Four-Module Design

Proratio is built as **four independent modules** that work together:

#### 1. Proratio Utilities
**Purpose**: Core infrastructure and execution engine.

**Responsibilities**:
- Data collection from Binance (price, volume, order book)
- Database storage (PostgreSQL)
- Order execution via Freqtrade
- Configuration management
- Logging and alerting

**Technologies**: Freqtrade, CCXT, PostgreSQL, Docker

#### 2. Proratio Signals
**Purpose**: AI signal generation and consensus.

**Responsibilities**:
- LLM integration (ChatGPT, Claude, Gemini)
- Prompt engineering for market analysis
- Consensus mechanism (weighted voting)
- ML ensemble integration (LSTM, LightGBM, XGBoost)
- Hybrid ML+LLM prediction

**Technologies**: OpenAI API, Anthropic API, Google Gemini API, PyTorch, scikit-learn

#### 3. Proratio QuantLab
**Purpose**: Research, backtesting, and model training.

**Responsibilities**:
- Strategy backtesting (historical simulation)
- ML model training and evaluation
- Feature engineering (65+ indicators)
- Performance analytics (Sharpe ratio, drawdown, win rate)
- Jupyter notebooks for research

**Technologies**: Freqtrade backtesting, PyTorch, LightGBM, XGBoost, Jupyter, Pandas

#### 4. Proratio TradeHub
**Purpose**: Strategy orchestration and portfolio management.

**Responsibilities**:
- Multi-strategy coordination (run multiple strategies simultaneously)
- Portfolio allocation (divide capital across strategies)
- Risk management enforcement
- Performance monitoring

**Technologies**: Python, Custom framework

### Data Flow

```
Market Data (Binance)
    ↓
Utilities (collect & store)
    ↓
Signals (ML + LLM analysis)
    ↓
TradeHub (strategy logic)
    ↓
Utilities (execute trades)
    ↓
QuantLab (analyze performance)
```

### Why This Architecture?

- **Modularity**: Each module can be developed/tested independently
- **Reusability**: Signals module can be used with different execution engines
- **Scalability**: Add new strategies without touching core infrastructure
- **Maintainability**: Clear separation of concerns

---

## Key Technologies

### Freqtrade
**What it is**: Open-source cryptocurrency trading bot framework.

**Why Proratio uses it**:
- Battle-tested order execution
- Built-in backtesting engine
- Exchange connectivity (100+ exchanges)
- Dry-run mode (paper trading)
- Strategy framework

**Role in Proratio**: Execution engine (handles order placement, position tracking, database).

### CCXT
**What it is**: Cryptocurrency exchange connectivity library.

**Why Proratio uses it**:
- Unified API for 100+ exchanges
- Handles authentication, rate limiting, WebSocket connections
- Real-time market data

**Role in Proratio**: Data collection (fetch OHLCV data, order book, trades).

### PyTorch
**What it is**: Deep learning framework by Meta/Facebook.

**Why Proratio uses it**:
- LSTM neural network implementation
- GPU acceleration (training 100x faster)
- Flexible model architecture

**Role in Proratio**: LSTM model training and inference.

### LightGBM / XGBoost
**What they are**: Gradient boosting frameworks by Microsoft and DMLC.

**Why Proratio uses them**:
- Fast training on tabular data
- Handle 100+ features efficiently
- Built-in feature importance

**Role in Proratio**: Tree-based models in ensemble, feature selection.

### PostgreSQL
**What it is**: Relational database.

**Why Proratio uses it**:
- Time-series data storage (OHLCV candles)
- Complex queries for backtesting
- ACID compliance (data integrity)

**Role in Proratio**: Historical data storage, trade logs.

### Docker
**What it is**: Containerization platform.

**Why Proratio uses it**:
- Consistent environment (same setup on any machine)
- Easy deployment (PostgreSQL, Redis in containers)
- Isolation (dependencies don't conflict)

**Role in Proratio**: Infrastructure management (database, cache, services).

---

## Backtesting and Validation

### What is Backtesting?

**Backtesting** simulates a trading strategy on historical data to see how it would have performed. It answers: "If I had used this strategy last year, would I have made money?"

### Proratio's Backtesting Approach

#### 1. Walk-Forward Analysis
**Problem**: Strategies trained on all historical data may "overfit" (memorize patterns that don't repeat).

**Solution**: Walk-forward testing
- Train on Jan-Jun data
- Test on Jul-Sep data (unseen)
- Retrain on Jan-Sep data
- Test on Oct-Dec data (unseen)
- Repeat...

**Result**: More realistic performance estimates.

#### 2. Validation Framework
Proratio has a **5-10 minute validation** that replaces 5-7 days of paper trading:

**Steps**:
1. **Pre-flight checks**: Strategy file exists, data available, config valid
2. **Accelerated backtest**: Run on 6 months of 5-minute data (thousands of trades simulated)
3. **Performance validation**: Check win rate ≥45%, max drawdown <25%, Sharpe ≥0.5
4. **Integration tests**: Verify strategy interfaces work correctly
5. **Code quality**: Run linting (Ruff) to catch errors
6. **Report generation**: Create detailed performance report

**Success criteria** (all must pass):
- ✅ Minimum 5 trades executed
- ✅ Win rate ≥ 45%
- ✅ Max drawdown < 25%
- ✅ Sharpe ratio ≥ 0.5
- ✅ Profit factor ≥ 1.0
- ✅ No critical errors

**Why faster than paper trading**:
- Paper trading: Wait 5-7 days for enough trades → slow feedback
- Validation: Simulate 6 months in 2-3 minutes → instant feedback
- Can iterate on strategy 60-120x faster

#### 3. Paper Trading
After validation passes, strategies run in **dry-run mode**:
- Real-time market data
- Simulated trades (no real money)
- Virtual balance ($10,000 USDT)
- Test bot stability, API connections, edge cases

**Duration**: 24-48 hours before live trading.

### Performance Metrics

Proratio tracks these key metrics:

**Profitability**:
- **Total return**: % gain/loss on capital
- **Sharpe ratio**: Risk-adjusted return (>1.5 is good, >2.0 is excellent)
- **Sortino ratio**: Like Sharpe but only penalizes downside volatility
- **Profit factor**: Gross profit ÷ Gross loss (>1.3 is profitable)

**Risk**:
- **Max drawdown**: Largest peak-to-trough decline (want <15%)
- **Win rate**: % of trades that are profitable (want >55%)
- **Risk/reward ratio**: Average win ÷ Average loss (want >2:1)
- **Expectancy**: Average profit per trade

**Consistency**:
- **Consecutive losses**: Max losing streak (want <5)
- **Monthly returns**: Standard deviation of returns
- **Recovery time**: How long to recover from drawdown

---

## Glossary

**Candlestick (OHLCV)**: Bar showing Open, High, Low, Close prices and Volume for a time period.

**Timeframe**: Duration of each candle (e.g., 1h = 1-hour candles, 4h = 4-hour candles).

**Long position**: Buying an asset expecting price to rise.

**Short position**: Selling borrowed assets expecting price to fall (betting on decline).

**Leverage**: Borrowing to amplify position size (2x leverage = control $2,000 with $1,000).

**Slippage**: Difference between expected price and actual execution price.

**Liquidity**: How easily an asset can be bought/sold without affecting price.

**Volatility**: Degree of price fluctuation (high volatility = large price swings).

**Alpha**: Returns above market benchmark (generating alpha = outperforming market).

**Backtesting**: Simulating strategy on historical data.

**Paper trading**: Simulated trading with fake money on real market data.

**Live trading**: Executing real trades with real money.

---

**For implementation details and setup instructions, see**:
- [Getting Started Guide](getting_started.md)
- [Strategy Development Guide](guides/strategy_development_guide.md)
- [Configuration Guide](guides/configuration_guide.md)
- [Project Roadmap](project/roadmap.md)
