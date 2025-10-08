# Paper Trading Guide

Complete guide to running paper trading (dry-run mode) and viewing trading reports.

---

## Prerequisites

### 1. Check Infrastructure is Running

```bash
# Check Docker containers
docker-compose ps

# Should show:
# - postgres (running)
# - redis (running)

# If not running, start them:
docker-compose up -d postgres redis
```

### 2. Verify Data is Available

```bash
# Check if Freqtrade data exists
ls -la user_data/data/binance/

# Should show .feather files like:
# BTC_USDT-1h.feather
# ETH_USDT-1h.feather

# If missing, export from PostgreSQL:
python scripts/export_data_for_freqtrade.py
```

---

## Running Paper Trading

### Option 1: Basic Dry-Run (No API Keys Needed)

Freqtrade can run in dry-run mode using historical data without connecting to exchange:

```bash
# Start paper trading with SimpleTestStrategy
freqtrade trade \
  --strategy SimpleTestStrategy \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data
```

**What this does:**
- Uses $10,000 virtual wallet (configured in config_dry.json)
- Simulates trades using real-time market data
- No real money involved
- Trades BTC/USDT and ETH/USDT
- Max 2 open trades at a time
- $100 USDT stake per trade

### Option 2: Live Dry-Run (With API Keys - Recommended)

For more realistic paper trading with live data feed:

1. **Get Binance Testnet API Keys**
   - Go to: https://testnet.binance.vision/
   - Register and create API keys
   - Enable "Spot & Margin Trading" permission (safe on testnet)

2. **Configure .env file**

```bash
# Edit .env
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_secret
BINANCE_TESTNET=true
TRADING_MODE=dry_run
```

3. **Run with live data feed**

```bash
freqtrade trade \
  --strategy SimpleTestStrategy \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data
```

---

## Monitoring Paper Trading

### 1. Terminal Output

Freqtrade shows real-time logs:

```
2025-10-06 10:30:15 - freqtrade.worker - INFO - Starting worker
2025-10-06 10:30:45 - freqtrade.strategy.interface - INFO - BUY signal found for BTC/USDT
2025-10-06 10:30:46 - freqtrade.freqtradebot - INFO - Bought BTC/USDT (0.001 BTC) at 67500.00
```

### 2. FreqUI Web Interface (Built-in Dashboard)

Freqtrade has a built-in web UI enabled in config_dry.json:

```bash
# Open in browser
http://localhost:8080

# Default credentials (from config_dry.json):
Username: freqtrader
Password: change_this_password
```

**FreqUI Features:**
- 📊 Real-time open trades table
- 💰 Profit/loss summary
- 📈 Performance charts
- 🔍 Trade history
- ⚙️ Live strategy status
- 📱 Force buy/sell buttons

### 3. Command-Line Status

```bash
# Show current status
freqtrade show_config --config proratio_utilities/config/freqtrade/config_dry.json

# Show open trades (while bot is running in another terminal)
freqtrade show_trades --config proratio_utilities/config/freqtrade/config_dry.json
```

---

## Viewing Trading Reports

### 1. Performance Report (Live)

While paper trading is running, open a new terminal:

```bash
# Generate performance report
freqtrade performance \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data

# Output:
# Pair       | Profit %  | Trades
# -----------+-----------+--------
# BTC/USDT   | 5.23%     | 12
# ETH/USDT   | 3.87%     | 8
```

### 2. Profit Summary

```bash
# Show profit summary
freqtrade profit \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data

# Output:
# Total Profit: 823.45 USDT (8.23%)
# Win Rate: 65.0%
# Best Trade: +245.67 USDT (BTC/USDT)
# Worst Trade: -87.23 USDT (ETH/USDT)
```

### 3. Trade List

```bash
# List all trades
freqtrade list-trades \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data

# Show only profitable trades
freqtrade list-trades --profitable \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data
```

### 4. Detailed Trade Report

```bash
# Show detailed trade information
freqtrade show_trades \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data \
  --print-json > paper_trading_report.json
```

### 5. Generate Plot (Visual Charts)

```bash
# Generate trading chart with entry/exit points
freqtrade plot-dataframe \
  --strategy SimpleTestStrategy \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data \
  --pairs BTC/USDT

# Output: user_data/plot/freqtrade-plot-BTC_USDT-1h.html
# Open in browser to see interactive chart
```

### 6. Generate Profit Plot

```bash
# Generate cumulative profit chart
freqtrade plot-profit \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data

# Output: user_data/plot/freqtrade-profit-plot.html
```

---

## Database Trade History

All trades are stored in SQLite database for long-term analysis:

```bash
# Location of trade database
ls -la user_data/tradesv3.dryrun.sqlite

# Query trades using sqlite3
sqlite3 user_data/tradesv3.dryrun.sqlite

# SQLite queries:
SELECT COUNT(*) FROM trades;
SELECT pair, profit_abs, close_date FROM trades ORDER BY close_date DESC LIMIT 10;
SELECT pair, AVG(profit_ratio) as avg_profit FROM trades GROUP BY pair;
```

---

## Stopping Paper Trading

```bash
# Graceful shutdown (Ctrl+C in terminal)
# Or send stop signal:
freqtrade stop --config proratio_utilities/config/freqtrade/config_dry.json
```

**What happens on stop:**
- All open positions are closed at current price
- Final trades saved to database
- Profit/loss calculated
- Logs written to user_data/logs/

---

## Logs and Debugging

### Log Files

```bash
# View real-time logs
tail -f user_data/logs/freqtrade.log

# View today's trades only
grep "$(date +%Y-%m-%d)" user_data/logs/freqtrade.log | grep "Bought\|Sold"

# View errors
grep "ERROR" user_data/logs/freqtrade.log
```

### Log Levels

Edit `config_dry.json` to change verbosity:

```json
{
  "verbosity": 3,  // 0=ERROR, 1=WARNING, 2=INFO, 3=DEBUG
}
```

---

## Common Issues

### Issue 1: "No data found for pair"

**Solution:** Export data from PostgreSQL first

```bash
python scripts/export_data_for_freqtrade.py
```

### Issue 2: "API key invalid"

**Solution:** Using Binance testnet keys on mainnet or vice versa

- Testnet keys only work with `BINANCE_TESTNET=true`
- For dry-run without keys, leave API keys empty in config

### Issue 3: "No trades executed"

**Solution:** Strategy conditions too strict or market not trending

```bash
# Check if strategy is generating signals
freqtrade backtesting \
  --strategy SimpleTestStrategy \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --timerange 20241001-20241006

# If backtest shows 0 trades, strategy needs adjustment
```

### Issue 4: FreqUI not accessible

**Solution:** Check API server is enabled

```bash
# Verify in config_dry.json:
"api_server": {
  "enabled": true,
  "listen_port": 8080
}

# Check port is not in use:
lsof -i :8080
```

---

## Weekly Performance Report

Create a script to generate weekly reports:

```bash
# Save as scripts/weekly_report.sh
#!/bin/bash

echo "=== Proratio Paper Trading Weekly Report ==="
echo "Week: $(date +%Y-%m-%d)"
echo ""

echo "=== Performance Summary ==="
freqtrade profit --config proratio_utilities/config/freqtrade/config_dry.json --userdir user_data

echo ""
echo "=== Top Performing Pairs ==="
freqtrade performance --config proratio_utilities/config/freqtrade/config_dry.json --userdir user_data

echo ""
echo "=== Recent Trades ==="
freqtrade list-trades --config proratio_utilities/config/freqtrade/config_dry.json --userdir user_data | tail -20

# Run:
chmod +x scripts/weekly_report.sh
./scripts/weekly_report.sh > reports/week_$(date +%Y%m%d).txt
```

---

## Next Steps

After 1-2 weeks of successful paper trading:

1. **Validate Results**
   - Compare paper trading vs. backtest results
   - Should be within 20% performance difference
   - No critical errors or crashes

2. **Prepare for Live Trading** (if validated)
   - Switch to mainnet API keys
   - Start with 1-5% of intended capital
   - Change `"dry_run": true` to `"dry_run": false` in config
   - Use `config_live.json` instead

3. **Monitor Closely**
   - First week: Check every 4-6 hours
   - First month: Daily monitoring
   - Set up Telegram alerts for trade notifications

---

## Resources

- **FreqUI Documentation**: https://www.freqtrade.io/en/stable/rest-api/
- **Freqtrade Commands**: https://www.freqtrade.io/en/stable/bot-usage/
- **Plotting Guide**: https://www.freqtrade.io/en/stable/plotting/
- **Telegram Setup**: https://www.freqtrade.io/en/stable/telegram-usage/

---

---

## Week 4: AI-Enhanced Paper Trading

### New Scripts for Week 4

#### 1. Start Paper Trading (with AI)

```bash
# Interactive start script with checks
./scripts/start_paper_trading.sh
```

This script:
- Verifies infrastructure is running
- Checks database has sufficient data (>1000 records)
- Shows AI provider status
- Starts Freqtrade with AIEnhancedStrategy

#### 2. Real-Time Monitoring

```bash
# Monitor with auto-refresh
uv run python scripts/monitor_paper_trading.py

# Custom refresh interval (seconds)
uv run python scripts/monitor_paper_trading.py --interval 30

# One-time snapshot
uv run python scripts/monitor_paper_trading.py --once
```

Displays:
- Performance summary (win rate, profit, trade count)
- Open trades with current status
- Recent closed trades with P&L
- Auto-refreshes every 10 seconds

#### 3. Weekly Performance Report

```bash
# Generate 7-day report
uv run python scripts/generate_weekly_report.py

# Custom period
uv run python scripts/generate_weekly_report.py --days 14

# Save to file
uv run python scripts/generate_weekly_report.py \
  --output reports/weekly_report_$(date +%Y%m%d).txt
```

Report includes:
- Performance metrics
- Exit reasons breakdown
- Trade-by-trade details
- AI provider status
- Backtest comparison
- Recommendations

### AI Signal Behavior

**Current Status:**
- ✓ Claude (Sonnet 4) - Active
- ✓ Gemini (2.0 Flash) - Active
- ✗ ChatGPT (GPT-5 Nano) - Quota exceeded

**Configuration:**
- Consensus threshold: 60%
- Dynamic reweighting: Enabled (2/3 providers = 100% weight)
- Trade frequency: 1-2 per week (low-frequency strategy)

**Expected Behavior:**
- Fewer trades than backtest (AI filters low-confidence signals)
- Higher win rate (quality over quantity)
- "No trade" decisions are normal and expected

### Week 4 Success Criteria

After 5-7 days of paper trading:

- [ ] No critical errors or crashes
- [ ] Win rate > 50%
- [ ] Total profit ≥ 0% (or small loss < 2%)
- [ ] Max drawdown < 10%
- [ ] AI consensus functioning correctly
- [ ] Risk limits enforced properly
- [ ] Performance within 20% of backtest expectations

---

**Last Updated**: 2025-10-08
