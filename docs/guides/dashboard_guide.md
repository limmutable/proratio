# Proratio Dashboard Guide

**Real-time monitoring and control interface for AI-driven trading**

Version: 1.0 | Last Updated: 2025-10-09

---

## Overview

The Proratio Dashboard is a Streamlit-based web interface that provides real-time monitoring, AI signal visualization, risk management, and emergency controls for the trading system.

### Key Features

- **Live Trading Status**: Real-time P&L, win rate, open positions
- **AI Consensus Visualization**: See what ChatGPT, Claude, and Gemini recommend
- **Risk Management Dashboard**: Visual risk levels with color-coded alerts
- **Emergency Controls**: Instant stop-all button with confirmation
- **Configuration Viewer**: View all 60+ trading parameters
- **Active Positions Tracking**: Detailed position information with P&L

---

## Quick Start

### Installation

The dashboard requires additional dependencies:

```bash
# Install Streamlit and visualization libraries
uv add streamlit plotly pandas

# Or using pip
pip install streamlit plotly pandas
```

### Running the Dashboard

```bash
# From project root
streamlit run proratio_tradehub/dashboard/app.py

# Or specify port
streamlit run proratio_tradehub/dashboard/app.py --server.port 8501
```

The dashboard will open automatically in your browser at `http://localhost:8501`

### Configuration

The dashboard connects to:
- **Freqtrade API**: `http://127.0.0.1:8080` (default)
- **Trade Database**: `user_data/db/tradesv3.dryrun.sqlite`
- **Trading Config**: `proratio_utilities/config/trading_config.json`

Update `data_fetcher.py` if your Freqtrade API runs on a different port.

---

## Dashboard Sections

### 1. Control Panel (Sidebar)

**Emergency Controls**
- **STOP ALL**: Closes all positions and halts trading immediately
- **RESET**: Clears emergency stop flag and allows resuming

**Trading Controls**
- **Enable Trading**: Toggle to enable/disable automated trading
- **Auto-refresh**: Automatically refresh data every 10 seconds

**Quick Stats**
- Risk level per trade
- Position size percentage
- Maximum concurrent positions

**System Status**
- Freqtrade connection status
- Database connection status
- AI provider status (ChatGPT, Claude, Gemini)

---

### 2. Live Trading Tab

**Performance Overview**
Displays key metrics at a glance:
- **Total P&L**: Total profit/loss in USD and percentage
- **Win Rate**: Percentage of winning trades
- **Open Positions**: Current vs. maximum allowed
- **Drawdown**: Current drawdown vs. maximum limit
- **Sharpe Ratio**: Risk-adjusted return metric

**Additional Metrics**
- Profit Factor
- Average Profit
- Average Loss
- Total Trades

**Active Positions Table**
Shows all currently open positions with:
- Trading pair
- Entry price
- Current price
- P&L percentage
- P&L in USD
- Trade duration

---

### 3. AI Signals Tab

**AI Consensus Visualization**

For each trading pair (BTC/USDT, ETH/USDT):

**Overall Signal**
- Direction (LONG / SHORT / NEUTRAL)
- Confidence score (0-100%)
- Color-coded indicator:
  - 🟢 Green = Bullish (Long)
  - 🔴 Red = Bearish (Short)
  - 🟡 Yellow = Neutral

**Confidence Gauge**
- Visual gauge showing consensus confidence
- Red line at 60% threshold (minimum for trading)
- Color zones:
  - Gray (0-40%): Low confidence
  - Yellow (40-60%): Medium confidence
  - Green (60-100%): High confidence

**AI Reasoning**
- Combined reasoning from all providers
- Explains why the signal was generated

**Provider Breakdown**
Individual signals from each AI provider:
- **ChatGPT**: Technical pattern recognition (40% weight)
- **Claude**: Risk assessment (35% weight)
- **Gemini**: Market sentiment (25% weight)

Each provider shows:
- Status (✅ Active / ❌ Unavailable)
- Individual signal direction
- Individual confidence score

---

### 4. Risk Management Tab

**Risk Level Indicator**
Large color-coded status:
- 🟢 **NORMAL**: Drawdown < 60% of limit
- 🟡 **WARNING**: Drawdown 60-80% of limit
- 🔴 **CRITICAL**: Drawdown 80-100% of limit
- ⚫ **HALT**: Drawdown at/above limit (trading stopped)

**Risk Metrics**
- **Current Drawdown**: Current vs. maximum limit
- **Position Usage**: Number of open positions vs. maximum
- **Max Loss/Trade**: Per-position risk limit
- **Daily Loss Limit**: Maximum daily loss allowed

**Drawdown Progress Bar**
Visual progress bar showing:
- Current drawdown percentage
- Maximum drawdown limit
- Percentage of limit used

**Risk Limits Table**
Complete view of all risk parameters:
- Max Loss Per Trade
- Max Daily Loss
- Max Total Drawdown
- Max Positions
- Position Size (Base)

Each row shows:
- Current limit (from config)
- Current value (actual)
- Status (✅ OK / ⚠️ WARNING / 🚨 CRITICAL)

---

### 5. Configuration Tab

View all trading configuration parameters across 5 sections:

**Risk Settings**
- Max loss per trade
- Max daily loss
- Max total drawdown
- Max concurrent positions
- Emergency stop enabled

**Position Sizing Settings**
- Sizing method (fixed_fraction, risk_based, kelly, ai_weighted, atr_based)
- Fixed fraction percentage
- Min/max position percentages
- AI confidence multipliers

**Strategy Settings**
- Strategy name
- Timeframe
- Trading pairs
- Minimum AI confidence threshold
- Technical fallback enabled

**AI Settings**
- Consensus threshold
- Signal timeout
- Signal caching enabled
- Provider weights (ChatGPT, Claude, Gemini)

**Execution Settings**
- Exchange (Binance)
- Trading mode (dry-run / live)
- Notifications enabled
- Notification channels

---

## Usage Scenarios

### Scenario 1: Paper Trading Monitoring (Phase 1.3)

**Goal**: Monitor paper trading performance and validate against backtest

1. Start Freqtrade in dry-run mode
2. Launch dashboard: `streamlit run proratio_tradehub/dashboard/app.py`
3. Enable auto-refresh (10s intervals)
4. Monitor **Live Trading** tab for performance metrics
5. Check **AI Signals** tab to see what AIs are recommending
6. Watch **Risk Management** tab to ensure limits are respected
7. After 5-7 days, compare performance to backtest expectations

**Success Criteria**:
- Performance within 20% of backtest
- No risk limit violations
- AI signals generating correctly
- No system crashes

---

### Scenario 2: Live Trading Monitoring

**Goal**: Monitor live trading with real money

1. Ensure Freqtrade is in **live mode** (not dry-run)
2. Launch dashboard
3. Keep **Control Panel** visible for emergency controls
4. Monitor **Active Positions** in real-time
5. Watch for risk level changes (NORMAL → WARNING → CRITICAL)
6. Review AI reasoning for each trade in **AI Signals** tab

**Emergency Actions**:
- Click **STOP ALL** to immediately close all positions
- System will:
  1. Force exit all open trades
  2. Stop the trading bot
  3. Display confirmation

---

### Scenario 3: Configuration Review

**Goal**: Review and verify all trading parameters

1. Navigate to **Configuration** tab
2. Review each section:
   - Risk: Ensure limits are conservative for your capital
   - Position Sizing: Verify method matches your strategy
   - Strategy: Check pairs and timeframe
   - AI: Confirm consensus threshold (recommended: 60%+)
   - Execution: Verify correct mode (dry-run vs live)

3. Cross-check with `trading_config.json` file
4. Make changes in config file, then reload Freqtrade

---

### Scenario 4: AI Signal Analysis

**Goal**: Understand why AI made a specific recommendation

1. Go to **AI Signals** tab
2. Select a trading pair (e.g., BTC/USDT)
3. Review:
   - Overall consensus direction and confidence
   - Individual provider signals
   - Combined reasoning
4. Check if confidence meets threshold (60%+)
5. Cross-reference with current price action in **Live Trading** tab

**Example Analysis**:
```
BTC/USDT Signal: LONG | Confidence: 72%

Providers:
- ChatGPT: ❌ Unavailable
- Claude: LONG (78%) ✅
- Gemini: LONG (70%) ✅

Reasoning: Strong uptrend confirmed by multiple indicators.
RSI showing momentum, price above EMA crossover.

Status: ✅ High confidence - ready to trade
```

---

## Troubleshooting

### Dashboard Won't Start

**Error**: `ModuleNotFoundError: No module named 'streamlit'`

**Solution**:
```bash
uv add streamlit plotly pandas
# or
pip install streamlit plotly pandas
```

---

### No Data Showing

**Error**: Dashboard loads but shows "No data available"

**Possible causes**:
1. **Freqtrade not running**
   - Check: `ps aux | grep freqtrade`
   - Start: `freqtrade trade --config ...`

2. **Freqtrade API not accessible**
   - Check: `curl http://127.0.0.1:8080/api/v1/status`
   - Verify API is enabled in Freqtrade config

3. **Database not found**
   - Check: `ls user_data/db/tradesv3.dryrun.sqlite`
   - Ensure database path is correct

**Solution**:
```bash
# Check Freqtrade status
freqtrade --version

# Verify API is running
curl http://127.0.0.1:8080/api/v1/ping

# Check database exists
ls -lh user_data/db/
```

---

### AI Signals Not Updating

**Error**: AI signals show "None" or old data

**Possible causes**:
1. AI providers not configured (missing API keys in `.env`)
2. Signal orchestrator not initialized
3. No OHLCV data available

**Solution**:
```bash
# Check environment variables
cat .env | grep -E "(ANTHROPIC|GOOGLE|OPENAI)"

# Test AI providers
python -m proratio_signals.orchestrator --pair BTC/USDT
```

---

### Connection Refused Error

**Error**: `Connection refused to http://127.0.0.1:8080`

**Cause**: Freqtrade API not running or on different port

**Solution**:
1. Check Freqtrade config: `api_server.enabled = true`
2. Verify port in config: `api_server.listen_port = 8080`
3. Update `data_fetcher.py` if using different port:
   ```python
   FreqtradeAPIClient(base_url="http://127.0.0.1:YOUR_PORT")
   ```

---

## Architecture

### Data Flow

```
Dashboard (Streamlit)
    ↓
DashboardDataFetcher
    ├─→ FreqtradeAPIClient → Freqtrade REST API (port 8080)
    ├─→ TradeDatabaseReader → SQLite DB (user_data/db/)
    ├─→ SignalOrchestrator → AI Providers (ChatGPT, Claude, Gemini)
    └─→ TradingConfig → JSON Config (trading_config.json)
```

### Components

**Frontend (Streamlit)**
- `app.py`: Main dashboard application
- Renders UI components
- Handles user interactions
- Auto-refreshes data

**Backend (Data Fetcher)**
- `data_fetcher.py`: Data aggregation layer
- `FreqtradeAPIClient`: REST API client
- `TradeDatabaseReader`: SQLite query layer
- `DashboardDataFetcher`: Main data aggregator

**Data Sources**
1. Freqtrade API (live status, open trades, profit)
2. SQLite Database (historical trades, statistics)
3. Signal Orchestrator (AI signals)
4. Trading Config (settings, limits)

---

## Customization

### Adding New Metrics

Edit `app.py` to add custom metrics:

```python
def render_custom_metrics():
    """Add your custom metrics here"""
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Custom Metric 1", "Value")

    with col2:
        st.metric("Custom Metric 2", "Value")

# Add to main() function
with tab1:
    render_performance_overview()
    render_custom_metrics()  # Add this line
```

### Changing Refresh Rate

Modify the auto-refresh interval:

```python
# In render_sidebar()
auto_refresh = st.checkbox("Auto-refresh (10s)", value=True)

# Change to 5 seconds
if auto_refresh:
    st_autorefresh(interval=5000)  # 5000ms = 5s
```

### Customizing Colors

Edit the CSS in `app.py`:

```python
st.markdown("""
<style>
    .risk-normal { color: #YOUR_COLOR; }
    .risk-warning { color: #YOUR_COLOR; }
    .risk-critical { color: #YOUR_COLOR; }
</style>
""", unsafe_allow_html=True)
```

---

## Testing

Run dashboard tests:

```bash
# Run all dashboard tests
pytest tests/test_dashboard/

# Run with coverage
pytest tests/test_dashboard/ --cov=proratio_tradehub.dashboard
```

---

## Production Deployment

### Running on Server

```bash
# Install dependencies
uv add streamlit plotly pandas

# Run dashboard in background
nohup streamlit run proratio_tradehub/dashboard/app.py --server.port 8501 &

# Check if running
ps aux | grep streamlit
```

### Security Considerations

1. **Enable authentication**:
   ```bash
   # Create .streamlit/config.toml
   [server]
   enableCORS = false

   [client]
   showErrorDetails = false
   ```

2. **Use HTTPS** (recommended for remote access)
3. **Restrict access** to localhost or VPN only
4. **Set strong passwords** for Freqtrade API

---

## Future Enhancements (Phase 2+)

- [ ] Trade execution directly from dashboard
- [ ] Manual trade entry with AI confirmation
- [ ] Parameter adjustment with live reload
- [ ] Historical performance charts (equity curve, drawdown)
- [ ] Alert system (email, Telegram, Discord)
- [ ] Multi-strategy comparison view
- [ ] Backtesting results visualization
- [ ] Real-time candle charts with indicators

---

## Support

**Documentation**
- [README.md](../README.md) - Project overview
- [roadmap.md](../roadmap.md) - Development plan
- [trading_config_guide.md](./trading_config_guide.md) - Configuration guide

**Troubleshooting**
- Check Freqtrade logs: `user_data/logs/freqtrade.log`
- Check dashboard errors in terminal output
- Verify all dependencies installed

**Resources**
- Streamlit Docs: https://docs.streamlit.io/
- Freqtrade API Docs: https://www.freqtrade.io/en/stable/rest-api/
- Plotly Docs: https://plotly.com/python/

---

**Dashboard Version**: 1.0
**Compatible with**: Proratio v0.3.0
**Last Updated**: 2025-10-09
