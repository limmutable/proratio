# Proratio Development Plan

**Project**: AI-Driven Crypto Trading System
**Target**: Binance (Spot, Futures, Options)
**Timeline**: 4 weeks MVP → Iterative improvements
**Last Updated**: 2025-10-06
**Version**: 0.1.0

---

## 📍 Current Status

**Phase**: Week 1 Complete - Week 2 Ready
**Completion**: 90% of Week 1 delivered

### ✅ Week 1 Completed
- Data collection infrastructure (CCXT + PostgreSQL)
- 24 months of historical data downloaded (BTC/USDT, ETH/USDT)
- Database storage layer with 44,640 OHLCV records
- Test suite (9 tests passing)
- Freqtrade integration with backtesting
- SimpleTestStrategy validated (73 trades on 2024 data)

### 🚧 Week 2 In Progress
- Multi-AI signal generation (ChatGPT, Claude, Gemini)
- AI consensus mechanism
- Strategy integration with AI signals

### 📋 Upcoming
- Paper trading deployment (Week 2)
- Backtesting framework enhancements (Week 3)
- Risk management implementation (Week 3)

---

## Vision & Goals

Build an intelligent crypto trading system that:
- Leverages multiple AI services (ChatGPT, Claude, Gemini) for market analysis
- Executes 1-2 manual trades per week with automated execution
- Supports trend-following, mean-reversion, and grid strategies
- Enables futures and options trading
- Provides comprehensive backtesting and performance analytics

---

## Architecture Overview

### Modular Design

**Proratio Core** - Execution & Data Engine
**Proratio Signals** - AI Alpha Signal Generation
**Proratio QuantLab** - Backtesting & Model Development
**Proratio TradeHub** - Strategy Orchestration & Risk Management

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Freqtrade | Trading bot (extensible, battle-tested) |
| Exchange | CCXT | Binance integration |
| Database | PostgreSQL 16 | Time-series data storage |
| Cache | Redis 7 | State management |
| AI/ML | OpenAI, Anthropic, Google | LLM-based signal generation |
| Visualization | Streamlit, Plotly | Dashboard & analytics |
| Testing | pytest | Unit & integration tests |
| Python | 3.13+ | Main language |

### Module Breakdown

| Module | Purpose | Tech Stack | Status |
|--------|---------|------------|--------|
| **Core** | Exchange connectivity, data collection, order execution | Freqtrade, CCXT, PostgreSQL | 75% |
| **Signals** | Multi-LLM analysis, consensus mechanism | OpenAI API, Anthropic API, Gemini API | 0% |
| **QuantLab** | Strategy backtesting, ML model development | PyTorch, scikit-learn, Jupyter | 0% |
| **TradeHub** | Multi-strategy coordination, risk management | Streamlit, Custom framework | 0% |

---

## Development Workflow

1. **Research** in QuantLab Jupyter notebooks
2. **Develop** strategy in TradeHub
3. **Backtest** using QuantLab engine
4. **Integrate** AI signals from Signals module
5. **Paper trade** using Freqtrade dry-run (1-2 weeks minimum)
6. **Validate** performance within 20% of backtest expectations
7. **Deploy live** with small capital (1-5% of intended amount)

---

## Security & Risk Management

### API Key Security
- ✅ All keys stored in `.env` (gitignored)
- ✅ Use read-only or trade-only API permissions
- ❌ **NEVER** enable withdrawal permissions
- ✅ Enable IP whitelisting on Binance
- ✅ Enable 2FA on exchange accounts
- ✅ Start with Binance **testnet** before using mainnet

### Risk Controls (Enforced in Code)
- **Max loss per trade**: 2% of portfolio
- **Max total drawdown**: 10% → halt trading
- **Max concurrent positions**: 2-3
- **Position sizing**: 5% base × AI confidence score
- **Stop-loss**: Always enabled (no exceptions)

### Security Checklist
- [ ] API keys configured with minimal permissions (read + trade only)
- [ ] IP whitelisting enabled on Binance
- [ ] 2FA enabled on exchange account
- [ ] `.env` file in `.gitignore`
- [ ] No secrets in code or documentation
- [ ] Testnet validated before mainnet
- [ ] Paper trading validated before live trading

---

## Initial Strategy (MVP)

### Trend-Following with AI Enhancement

**Core Logic:**
- **Entry Signal**:
  - Fast EMA (20) crosses above Slow EMA (50)
  - RSI > 30 and < 70 (not oversold/overbought)
  - Volume > 20-period average
  - **AI consensus score > 0.6** (60% agreement)

- **Exit Signal**:
  - Reverse EMA crossover
  - OR RSI > 70 (overbought)
  - OR Stop-loss hit (-5%)
  - OR Take-profit hit (+10%, +5%, +2% tiered)

- **Position Sizing**: 5% of portfolio × AI confidence score
- **Risk/Reward**: 2:1 minimum (6% target, 3% stop)

### AI Integration

| AI Provider | Role | Weight | Focus |
|-------------|------|--------|-------|
| ChatGPT-4 | Technical pattern recognition | 40% | Chart patterns, indicators |
| Claude | Risk assessment | 35% | Market conditions, volatility |
| Gemini | Market sentiment | 25% | Trend direction, momentum |

**Consensus Mechanism:**
- Weighted voting based on above percentages
- Final signal only if consensus > 0.6 (60% agreement)
- All three AIs must participate (no partial consensus)

---

## 📊 Weekly Progress Reports

### Week 1 Completion Summary (Oct 5-6, 2025)

**Status:** ✅ **COMPLETE** (90% delivered)

#### Achievements

**1. Data Infrastructure**
- PostgreSQL database with 44,640 OHLCV records (24 months: BTC/USDT, ETH/USDT)
- 3 timeframes per pair: 1h, 4h, 1d
- CCXT-based data collector with automatic pagination
- Database storage layer with conflict handling
- **Single source of truth**: PostgreSQL → Export to Freqtrade on demand

**2. Completed Files (18 created/updated)**
- Core Modules: `collectors.py`, `storage.py`, `loaders.py`, `schema.sql`
- Scripts: `download_historical_data.py`, `export_data_for_freqtrade.py`, `test_data_pipeline.py`
- Strategy: `SimpleTestStrategy.py` (EMA crossover)
- Tests: 9 passing unit tests
- Documentation: Updated README, CLAUDE.md, this plan

**3. Freqtrade Integration**
- Simple EMA crossover strategy validated
- Backtest on full year 2024: **73 trades, 61.6% win rate, +0.14% profit**
- Data export workflow: PostgreSQL → Feather format → Freqtrade
- Configuration: `config_dry.json` for paper trading

**4. Technical Stack Validated**
- Python 3.13.7, Freqtrade 2025.9, CCXT 4.5.7
- PostgreSQL 16 (Docker), psycopg2 2.9.10
- pandas 2.3.3, TA-Lib 0.6.7, pytest 8.4.2

#### Key Learnings

1. **Single Source of Truth**: PostgreSQL as master, export to Freqtrade prevents duplication
2. **No API Keys Needed**: CCXT can fetch public OHLCV data without authentication
3. **Feather Format**: Freqtrade prefers `.feather` over `.json` for performance
4. **Strategy Framework**: Simple strategies validate infrastructure before AI integration

#### Files Created
- `proratio_core/data/`: collectors.py, storage.py, loaders.py, schema.sql
- `scripts/`: download_historical_data.py, export_data_for_freqtrade.py, test_data_pipeline.py
- `user_data/strategies/`: SimpleTestStrategy.py
- `tests/test_core/`: test_config.py, test_storage.py, test_collectors.py
- `docs/`: data_management_workflow.md

#### Metrics
- **Development Time**: 2 days
- **Lines of Code**: ~1,500
- **Data Volume**: 44,640 records
- **Test Coverage**: 9 tests passing
- **Backtest Validation**: 73 trades on 2024 data

#### Remaining Tasks (10%)
- [ ] Deploy dry-run paper trading (requires API keys)
- [ ] Telegram notifications (deferred to Week 2)

**Ready for Week 2:** ✅ YES - All prerequisites complete

---

## MVP Implementation Timeline (4 Weeks)

### Week 1: Foundation (Proratio Core) - ✅ 90% Complete

**Goal**: Working data pipeline + Freqtrade integration

**Completed:**
- [x] Set up development environment (Python 3.13, Docker)
- [x] Install and configure Freqtrade
- [x] Configure Binance public API for data collection
- [x] Create PostgreSQL database schema (`schema.sql`)
- [x] Implement data collectors (CCXT wrapper - `collectors.py`)
- [x] Implement data storage layer (`storage.py`)
- [x] Implement data loader (`loaders.py`)
- [x] Download historical data (BTC/USDT, ETH/USDT, 24 months)
  - 17,280 1h candles per pair (PostgreSQL)
  - 4,320 4h candles per pair (PostgreSQL)
  - 720 daily candles per pair (PostgreSQL)
- [x] Create test suite (9 tests passing)
- [x] Create Freqtrade test strategy (`SimpleTestStrategy`)
- [x] Run successful backtest (73 trades, strategy validated)

**Pending:**
- [ ] Set up Telegram alerts (optional - deferred to Week 2)
- [ ] Deploy dry-run paper trading

**Deliverables:**
- ✅ Freqtrade operational with backtesting
- ✅ Market data collection pipeline working
- ✅ Database storing OHLCV data (44,640 records)
- ✅ Strategy framework proven (SimpleTestStrategy)
- ⏳ Telegram notifications (deferred)

---

### Week 2: AI Integration (Proratio Signals + Basic TradeHub)

**Goal**: Multi-AI analysis + Simple trend strategy

**Tasks:**
- [ ] Build LLM provider interfaces (ChatGPT, Claude, Gemini)
- [ ] Create prompt templates for technical analysis
- [ ] Implement AI consensus mechanism (weighted voting)
- [ ] Develop simple trend-following strategy
- [ ] Integrate AI signals into strategy
- [ ] Backtest AI-enhanced strategy (6-12 months)
- [ ] Optimize parameters using Hyperopt

**Deliverables:**
- ✅ Multi-AI orchestration working
- ✅ Trend-following strategy with positive backtest results
- ✅ AI signals influencing trade decisions

**Success Criteria:**
- All 3 AI providers responding correctly
- Consensus mechanism producing signals
- Backtest Sharpe ratio > 1.0
- Strategy outperforms SimpleTestStrategy

---

### Week 3: Backtesting & Risk Management (Proratio QuantLab + Enhanced TradeHub)

**Goal**: Robust backtesting + Risk controls + Dashboard

**Tasks:**
- [ ] Build backtesting wrapper for Freqtrade
- [ ] Implement walk-forward analysis
- [ ] Create risk management module (position sizing, drawdown control)
- [ ] Build portfolio allocator
- [ ] Develop Streamlit dashboard
- [ ] Add performance analytics and visualizations

**Deliverables:**
- ✅ QuantLab can backtest strategies rigorously
- ✅ Risk limits enforced in code
- ✅ Dashboard showing positions, AI insights, performance

**Success Criteria:**
- Walk-forward analysis validates strategy robustness
- Risk controls prevent excessive drawdown
- Dashboard displays real-time data
- All metrics calculated correctly

---

### Week 4: Integration & Paper Trading

**Goal**: End-to-end validation with live data

**Tasks:**
- [ ] Full system integration testing
- [ ] Deploy in paper trading mode (dry-run)
- [ ] Monitor for 5-7 days minimum
- [ ] Log all trades and AI decisions
- [ ] Generate weekly performance report
- [ ] Compare paper trading vs. backtest results
- [ ] Document all modules and workflows

**Deliverables:**
- ✅ 5-7 days of paper trading completed
- ✅ Performance within 20% of backtest expectations
- ✅ No critical errors
- ✅ System ready for live deployment decision

**Success Criteria:**
- Paper trading profit/loss within 20% of backtest
- No system crashes or errors
- AI consensus functioning correctly
- Risk limits enforced properly

---

## Post-MVP Roadmap (Weeks 5+)

### Phase 2: Advanced Strategies (Weeks 5-6)
- Mean-reversion strategy for range-bound markets
- Grid trading strategy for volatility
- Multi-strategy portfolio allocation
- A/B testing framework for strategies

### Phase 3: Machine Learning Models (Weeks 7-8)
- Integrate FreqAI for adaptive strategies
- LSTM price prediction models
- Ensemble models combining multiple approaches
- Reinforcement learning experiments (optional)

### Phase 4: Options & Futures (Weeks 9-10)
- Binance options trading integration
- Perpetual futures strategies
- Funding rate arbitrage
- Delta hedging for options

### Phase 5: Sentiment Analysis (Weeks 11-12)
- Twitter/Reddit sentiment analysis
- News sentiment APIs (CryptoPanic, NewsAPI)
- On-chain metrics (Glassnode, Nansen)
- Social volume and engagement tracking

### Phase 6: Continuous Improvement (Ongoing)
- Performance monitoring and optimization
- Strategy refinement based on live results
- New AI models and providers
- Community feedback integration

---

## Module Implementation Status

### Proratio Core (75% implemented)

**Completed:**
- [x] Data collectors (CCXT wrapper - `collectors.py`)
- [x] Data loaders (database integration - `loaders.py`)
- [x] Data storage (PostgreSQL - `storage.py`, `schema.sql`)
- [x] Historical data download (24 months BTC/USDT, ETH/USDT)
- [x] Test suite for data pipeline (9 tests passing)
- [x] Freqtrade integration - `SimpleTestStrategy.py`
- [x] Data export utility - `export_data_for_freqtrade.py`
- [x] Backtesting validated (73 trades, strategy working)

**Pending:**
- [ ] Freqtrade execution wrapper (for live trading)
- [ ] Order manager
- [ ] Position manager
- [ ] Logger utility
- [ ] Telegram alerts integration

---

### Proratio Signals (0% implemented)

**Week 2 Tasks:**
- [ ] ChatGPT provider implementation
- [ ] Claude provider implementation
- [ ] Gemini provider implementation
- [ ] Base LLM interface
- [ ] Technical analysis prompts
- [ ] Risk assessment prompts
- [ ] Sentiment prompts
- [ ] Signal orchestrator (consensus mechanism)
- [ ] Signal scoring and weighting

---

### Proratio QuantLab (0% implemented)

**Week 3 Tasks:**
- [ ] Backtest engine wrapper
- [ ] Walk-forward analysis
- [ ] Performance analytics
- [ ] Strategy optimizer (Hyperopt integration)
- [ ] Jupyter notebook templates
- [ ] Visualization tools (Plotly charts)
- [ ] ML model training pipeline (future)

---

### Proratio TradeHub (0% implemented)

**Week 2-3 Tasks:**
- [ ] Strategy base classes
- [ ] Multi-strategy orchestrator
- [ ] Risk management module
- [ ] Position sizing calculator
- [ ] Portfolio allocator
- [ ] Streamlit dashboard
- [ ] Alert system (Telegram)

---

## Development Principles

### Code Quality
- Follow PEP 8 style guidelines
- Write comprehensive docstrings
- Use type hints for all functions
- Keep functions small and focused (<50 lines)
- Prefer composition over inheritance

### Security
- Never commit secrets to git
- Use environment variables for sensitive data
- Implement proper error handling
- Log security-relevant events
- Regular dependency updates

### Risk Management
- Code review all strategy changes
- Backtest with realistic slippage (0.1%)
- Paper trade for minimum 1-2 weeks
- Start live trading with 1-5% capital
- Implement circuit breakers for losses

### Testing Philosophy
- Write tests before production deployment
- Test all critical paths (entry, exit, risk)
- Mock external APIs in tests
- Test edge cases and error conditions
- Maintain >80% code coverage goal

---

## Success Metrics

### Development Phase
- ✅ All tests passing
- ✅ Code coverage > 80%
- ✅ No critical security issues
- ✅ Documentation complete

### Paper Trading Phase
- ✅ 5-7 days minimum runtime
- ✅ Performance within 20% of backtest
- ✅ No system crashes
- ✅ Risk limits enforced correctly
- ✅ AI consensus functioning

### Live Trading Phase
- ✅ Sharpe ratio > 1.5
- ✅ Max drawdown < 15%
- ✅ Win rate > 55%
- ✅ Profit factor > 1.3
- ✅ No manual interventions needed

---

## Key Design Decisions

### Why Freqtrade?
- ✅ Production-ready, battle-tested framework
- ✅ Active community and regular updates
- ✅ Extensive documentation and examples
- ✅ Supports multiple exchanges via CCXT
- ✅ Built-in backtesting and optimization
- ✅ Can be swapped if needed (modular design)

### Why Modular Architecture?
- ✅ Easy to test components independently
- ✅ Can swap Freqtrade for custom engine later
- ✅ AI providers can be added/removed easily
- ✅ Strategies are independent and portable
- ✅ Clean separation of concerns

### Why Multi-AI Consensus?
- ✅ Reduces bias from single AI model
- ✅ More robust signal generation
- ✅ Can weight based on past performance
- ✅ Each AI brings different strengths
- ✅ Consensus reduces false signals

---

## Project Statistics

**Lines of Code**: ~1,500 (Week 1)
**Test Coverage**: 9 passing tests
**Data Volume**: 44,640 OHLCV records
**Supported Pairs**: BTC/USDT, ETH/USDT (expandable)
**Timeframes**: 1h, 4h, 1d
**Historical Data**: 24 months (Oct 2023 - Oct 2025)

---

## Resources

### Documentation
- [README.md](./README.md) - Quick start guide
- [CLAUDE.md](./CLAUDE.md) - Developer guide for Claude Code
- [docs/data_management_workflow.md](./docs/data_management_workflow.md) - Data workflow
- [PLANREVIEW.md](./PLANREVIEW.md) - Initial plan assessment

### External Resources
- Freqtrade Docs: https://www.freqtrade.io/
- CCXT Docs: https://docs.ccxt.com/
- Binance API: https://binance-docs.github.io/apidocs/spot/en/

---

## What Makes Proratio Unique?

1. **Multi-AI Consensus**: Combines 3 leading LLMs for robust signals
2. **Modular Design**: Easy to swap components and add new strategies
3. **Risk-First Approach**: Multiple safety nets and conservative sizing
4. **Full Transparency**: All decisions logged with AI reasoning
5. **Open Architecture**: Not locked into any single provider or exchange

---

**Last Updated**: October 6, 2025
**Next Review**: After Week 2 completion
