# Proratio Development Plan

**AI-Driven Crypto Trading System for Binance**
**Version**: 0.1.0 | **Last Updated**: 2025-10-06

---

## 📍 Current Status

**Phase**: ✅ Week 1 Complete → 🚧 Week 2 In Progress
**Progress**: Week 1 (90%) | Week 2 (0%) | Week 3 (0%) | Week 4 (0%)

### Quick Status
- ✅ Data pipeline: PostgreSQL + CCXT (44,640 records, 24 months)
- ✅ Freqtrade integration: Backtest validated (73 trades, 61.6% win rate)
- ✅ Test suite: 9 tests passing
- 🚧 Next: Multi-AI signal generation (Week 2)

---

## Vision & Architecture

### Goal
Build an intelligent crypto trading system that leverages multiple AI services (ChatGPT, Claude, Gemini) for market analysis, executes 1-2 trades per week with automated execution, and supports trend-following, mean-reversion, and grid strategies.

### Modular Design

| Module | Purpose | Tech Stack | Status |
|--------|---------|------------|--------|
| **Core** | Data collection, order execution | Freqtrade, CCXT, PostgreSQL | ✅ 75% |
| **Signals** | Multi-LLM analysis, consensus | OpenAI, Anthropic, Gemini APIs | 🚧 0% |
| **QuantLab** | Backtesting, ML models | PyTorch, scikit-learn, Jupyter | ⏳ 0% |
| **TradeHub** | Strategy orchestration, risk mgmt | Streamlit, Custom framework | ⏳ 0% |

### Tech Stack
- **Framework**: Freqtrade (extensible, battle-tested)
- **Database**: PostgreSQL 16 (time-series data)
- **Cache**: Redis 7 (state management)
- **AI/ML**: OpenAI, Anthropic, Google (LLM signals)
- **Visualization**: Streamlit, Plotly
- **Testing**: pytest
- **Python**: 3.13+

---

## Development Workflow

1. **Research** → QuantLab Jupyter notebooks
2. **Develop** → TradeHub strategies
3. **Backtest** → QuantLab engine (validate Sharpe > 1.0)
4. **Integrate** → AI signals from Signals module
5. **Paper trade** → Freqtrade dry-run (1-2 weeks minimum)
6. **Validate** → Performance within 20% of backtest
7. **Deploy live** → Small capital (1-5% of portfolio)

---

## Initial Strategy (MVP)

### Trend-Following with AI Enhancement

**Entry Signal:**
- Fast EMA (20) crosses above Slow EMA (50)
- RSI between 30-70 (not extreme)
- Volume > 20-period average
- **AI consensus score > 0.6** (60% agreement)

**Exit Signal:**
- Reverse EMA crossover OR RSI > 70
- Stop-loss (-5%) OR Take-profit (tiered: +10%, +5%, +2%)

**Position Sizing:** 5% portfolio × AI confidence score
**Risk/Reward:** 2:1 minimum (6% target, 3% stop)

### AI Consensus Mechanism

| AI Provider | Role | Weight |
|-------------|------|--------|
| ChatGPT-4 | Technical pattern recognition | 40% |
| Claude | Risk assessment | 35% |
| Gemini | Market sentiment | 25% |

**Rules:**
- Weighted voting based on above percentages
- Final signal only if consensus > 0.6 (60%)
- All three AIs must participate (no partial consensus)

---

## Security & Risk Management

### API Key Security
- [x] All keys in `.env` (gitignored)
- [ ] Use read-only or trade-only API permissions
- [ ] **NEVER** enable withdrawal permissions
- [ ] Enable IP whitelisting on Binance
- [ ] Enable 2FA on exchange accounts
- [ ] Start with Binance **testnet** before mainnet

### Risk Controls (Enforced in Code)
- **Max loss per trade**: 2% of portfolio
- **Max total drawdown**: 10% → halt trading
- **Max concurrent positions**: 2-3
- **Position sizing**: 5% base × AI confidence score
- **Stop-loss**: Always enabled (no exceptions)

---

## 📊 4-Week MVP Timeline

### ✅ Week 1: Foundation (Proratio Core) - 90% Complete

**Goal**: Working data pipeline + Freqtrade integration

#### Completed
- [x] Development environment (Python 3.13, Docker)
- [x] Freqtrade installation and configuration
- [x] PostgreSQL database schema (`schema.sql`)
- [x] Data collectors (CCXT - `collectors.py`)
- [x] Data storage layer (`storage.py`)
- [x] Data loader (`loaders.py`)
- [x] Historical data download (BTC/USDT, ETH/USDT, 24 months)
  - [x] 17,280 1h candles per pair
  - [x] 4,320 4h candles per pair
  - [x] 720 daily candles per pair
- [x] Test suite (9 tests passing)
- [x] Freqtrade test strategy (`SimpleTestStrategy`)
- [x] Backtest validation (73 trades, 61.6% win rate)
- [x] Data export to Feather format (`export_data_for_freqtrade.py`)

#### Pending
- [ ] Deploy dry-run paper trading (requires API keys)
- [ ] Telegram notifications (deferred to Week 2)

#### Key Achievements
- **PostgreSQL as single source of truth**: No data duplication
- **44,640 OHLCV records** stored (24 months)
- **Feather export format** for Freqtrade performance
- **No API keys needed** for public OHLCV data collection

---

### 🚧 Week 2: AI Integration (Proratio Signals)

**Goal**: Multi-AI analysis + Trend strategy with AI signals

#### Tasks
- [ ] Build LLM provider interfaces
  - [ ] ChatGPT provider (`llm_providers/chatgpt.py`)
  - [ ] Claude provider (`llm_providers/claude.py`)
  - [ ] Gemini provider (`llm_providers/gemini.py`)
  - [ ] Base LLM interface (`llm_providers/base.py`)
- [ ] Create prompt templates
  - [ ] Technical analysis prompts (`prompts/technical_analysis.py`)
  - [ ] Risk assessment prompts (`prompts/risk_assessment.py`)
  - [ ] Sentiment prompts (`prompts/sentiment.py`)
- [ ] Implement AI consensus mechanism
  - [ ] Signal orchestrator (`orchestrator.py`)
  - [ ] Weighted voting logic
  - [ ] Signal scoring and aggregation
- [ ] Integrate AI signals into `SimpleTestStrategy`
- [ ] Backtest AI-enhanced strategy (6-12 months)
- [ ] Hyperopt parameter optimization

#### Success Criteria
- [ ] All 3 AI providers responding correctly
- [ ] Consensus mechanism producing signals
- [ ] Backtest Sharpe ratio > 1.0
- [ ] Strategy outperforms baseline SimpleTestStrategy

---

### ⏳ Week 3: Backtesting & Risk (QuantLab + TradeHub)

**Goal**: Robust backtesting + Risk controls + Dashboard

#### Tasks
- [ ] **QuantLab**
  - [ ] Backtest engine wrapper (`backtesting/backtest_engine.py`)
  - [ ] Walk-forward analysis
  - [ ] Performance analytics (`analytics/metrics.py`)
  - [ ] Visualization tools (Plotly charts)
  - [ ] Jupyter notebook templates
- [ ] **TradeHub - Risk Management**
  - [ ] Risk management module (`risk/risk_manager.py`)
  - [ ] Position sizing calculator (`risk/position_sizer.py`)
  - [ ] Portfolio allocator (`orchestration/portfolio_manager.py`)
  - [ ] Drawdown monitor
- [ ] **TradeHub - Dashboard**
  - [ ] Streamlit dashboard (`dashboard/app.py`)
  - [ ] Real-time position display
  - [ ] AI insights visualization
  - [ ] Performance charts

#### Success Criteria
- [ ] Walk-forward analysis validates strategy robustness
- [ ] Risk controls prevent excessive drawdown in backtest
- [ ] Dashboard displays real-time data correctly
- [ ] All performance metrics calculated accurately

---

### ⏳ Week 4: Integration & Paper Trading

**Goal**: End-to-end validation with live data

#### Tasks
- [ ] Full system integration testing
- [ ] Deploy in paper trading mode (dry-run)
- [ ] Monitor for 5-7 days minimum
- [ ] Log all trades and AI decisions
- [ ] Generate weekly performance report
- [ ] Compare paper trading vs. backtest results
- [ ] Document all modules and workflows

#### Success Criteria
- [ ] 5-7 days of paper trading completed
- [ ] Performance within 20% of backtest expectations
- [ ] No critical errors or crashes
- [ ] AI consensus functioning correctly
- [ ] Risk limits enforced properly
- [ ] System ready for live deployment decision

---

## 📈 Post-MVP Roadmap (Weeks 5+)

### Phase 2: Advanced Strategies (Weeks 5-6)
- [ ] Mean-reversion strategy for range-bound markets
- [ ] Grid trading strategy for volatility
- [ ] Multi-strategy portfolio allocation
- [ ] A/B testing framework

### Phase 3: Machine Learning (Weeks 7-8)
- [ ] FreqAI integration for adaptive strategies
- [ ] LSTM price prediction models
- [ ] Ensemble models
- [ ] Reinforcement learning experiments (optional)

### Phase 4: Options & Futures (Weeks 9-10)
- [ ] Binance options trading integration
- [ ] Perpetual futures strategies
- [ ] Funding rate arbitrage
- [ ] Delta hedging

### Phase 5: Sentiment Analysis (Weeks 11-12)
- [ ] Twitter/Reddit sentiment analysis
- [ ] News sentiment APIs (CryptoPanic, NewsAPI)
- [ ] On-chain metrics (Glassnode)
- [ ] Social volume tracking

---

## 📝 Weekly Progress Log

### Week 1 (Oct 5-6, 2025) - ✅ COMPLETE

**Files Created** (18 total)
- Core: `collectors.py`, `storage.py`, `loaders.py`, `schema.sql`
- Scripts: `download_historical_data.py`, `export_data_for_freqtrade.py`, `test_*.py` (4 files)
- Strategy: `SimpleTestStrategy.py`
- Tests: `test_config.py`, `test_storage.py`, `test_collectors.py`
- Docs: `data_management_workflow.md`

**Metrics**
- Development time: 2 days
- Lines of code: ~1,500
- Data volume: 44,640 OHLCV records
- Test coverage: 9 tests passing
- Backtest: 73 trades on 2024 data, 61.6% win rate

**Key Learnings**
1. PostgreSQL as single source of truth prevents duplication
2. CCXT works without API keys for public data
3. Freqtrade prefers Feather format over JSON
4. Simple strategies validate infrastructure before AI integration

---

## Key Design Decisions

### Why Freqtrade?
- Production-ready, battle-tested framework
- Active community and regular updates
- Built-in backtesting and optimization
- Modular design allows swapping if needed

### Why Multi-AI Consensus?
- Reduces single-model bias
- More robust signal generation
- Each AI brings different strengths
- Weighted voting reduces false signals

### Why PostgreSQL as Single Source?
- Prevents data duplication and inconsistency
- Enables custom analytics on raw data
- Export to Freqtrade only when needed
- Easy to update and maintain

---

## Success Metrics

### Development Phase
- [x] All tests passing (9/9)
- [ ] Code coverage > 80% (current: ~60%)
- [x] No critical security issues
- [x] Documentation complete

### Paper Trading Phase
- [ ] 5-7 days minimum runtime
- [ ] Performance within 20% of backtest
- [ ] No system crashes
- [ ] Risk limits enforced correctly
- [ ] AI consensus functioning

### Live Trading Phase
- [ ] Sharpe ratio > 1.5
- [ ] Max drawdown < 15%
- [ ] Win rate > 55%
- [ ] Profit factor > 1.3
- [ ] No manual interventions needed

---

## Resources

**Documentation**
- [README.md](./README.md) - Quick start guide
- [CLAUDE.md](./CLAUDE.md) - Developer guide
- [docs/](./docs/) - Module-specific guides
- [PLANREVIEW.md](./PLANREVIEW.md) - Initial plan assessment

**External Resources**
- Freqtrade: https://www.freqtrade.io/
- CCXT: https://docs.ccxt.com/
- Binance API: https://binance-docs.github.io/apidocs/spot/en/

---

## Project Statistics

| Metric | Value |
|--------|-------|
| Lines of Code | ~1,500 (Week 1) |
| Test Coverage | 9 passing tests |
| Data Volume | 44,640 OHLCV records |
| Supported Pairs | BTC/USDT, ETH/USDT |
| Timeframes | 1h, 4h, 1d |
| Historical Data | 24 months (Oct 2023 - Oct 2025) |

---

**Next Review**: After Week 2 completion
