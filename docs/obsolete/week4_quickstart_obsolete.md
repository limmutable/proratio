# Week 4 Quick Start: Paper Trading with AI

**Goal**: Run paper trading for 5-7 days to validate the complete system.

---

## ✅ Prerequisites (Completed)

- [x] Database initialized with 44,640 OHLCV records
- [x] AI API keys configured (Claude + Gemini working)
- [x] Infrastructure running (PostgreSQL + Redis)
- [x] AI signal generation tested and working

---

## 🚀 Step 1: Start Paper Trading

```bash
# Start paper trading (interactive script with checks)
./scripts/start_paper_trading.sh
```

**What happens:**
- Script verifies infrastructure is running
- Checks database has sufficient data
- Shows configuration summary
- Starts Freqtrade with AIEnhancedStrategy
- Runs in foreground (see live logs)

**Expected output:**
```
======================================================================
  PRORATIO PAPER TRADING - DRY RUN MODE
======================================================================

✓ Infrastructure running
✓ .env file found
✓ Database has 44640 OHLCV records

Paper Trading Configuration:
  Strategy: AIEnhancedStrategy
  Pairs: BTC/USDT, ETH/USDT
  Starting Capital: 10,000 USDT (virtual)
  Max Open Trades: 2
  AI Providers: Claude + Gemini (ChatGPT disabled - quota exceeded)
  Mode: DRY RUN (no real money)

Start paper trading? (y/n)
```

**Important:**
- Keep this terminal open (Freqtrade runs in foreground)
- To stop: Press `Ctrl+C`
- Logs saved to: `user_data/logs/freqtrade.log`

---

## 📊 Step 2: Monitor in Real-Time

Open a **second terminal** and run:

```bash
# Start real-time monitor (auto-refresh every 10 seconds)
uv run python scripts/monitor_paper_trading.py
```

**Dashboard shows:**
```
================================================================================
                    PRORATIO PAPER TRADING MONITOR
================================================================================
Last Updated: 2025-10-08 14:30:00

📊 PERFORMANCE SUMMARY
--------------------------------------------------------------------------------
Total Trades:    3
Winning Trades:  2
Win Rate:        66.7%
Total Profit:    $45.23 USDT
Avg Profit:      2.15%
Max Win:         3.45%
Max Loss:        -1.23%

🔓 OPEN TRADES (1)
--------------------------------------------------------------------------------
#123 BTC/USDT
  Opened:     2025-10-08 12:00:00
  Entry:      $62,450.00
  Amount:     0.0016
  Stake:      $100.00 USDT
  Stop Loss:  $59,327.50

🔒 RECENT CLOSED TRADES (Last 5)
--------------------------------------------------------------------------------
✅ #122 ETH/USDT
  Opened:     2025-10-08 10:00:00
  Closed:     2025-10-08 13:00:00
  Entry:      $2,450.00
  Exit:       $2,534.50
  Profit:     +$3.45 USDT (+3.45%)
```

**Controls:**
- Press `Ctrl+C` to stop monitoring (paper trading continues)
- Monitor refreshes automatically every 10 seconds

---

## 📝 Step 3: Daily Check-In

Run once per day to check status:

```bash
# Quick snapshot (no auto-refresh)
uv run python scripts/monitor_paper_trading.py --once

# Check logs for errors
grep -i "error\|exception" user_data/logs/freqtrade.log | tail -20

# Check AI decisions
grep "AI Signal" user_data/logs/freqtrade.log | tail -10
```

---

## 📈 Step 4: Weekly Report (After 7 Days)

```bash
# Generate comprehensive weekly report
uv run python scripts/generate_weekly_report.py \
  --days 7 \
  --output reports/week4_report_$(date +%Y%m%d).txt

# View report
cat reports/week4_report_*.txt
```

**Report includes:**
- Performance summary (win rate, profit, trade count)
- Exit reasons breakdown
- Trade-by-trade details
- AI provider status
- Backtest comparison
- Recommendations

---

## 🎯 What to Expect

### Trade Frequency

**Expected**: 1-2 trades per week (low-frequency strategy)

**Why so few trades?**
- AI filters low-confidence signals (< 60% consensus)
- Goal: Quality over quantity
- Baseline backtest had 45 trades (without AI filter)
- AI-enhanced strategy is more selective

### AI Signal Behavior

**Current setup:**
- ✓ Claude (Sonnet 4) - Active
- ✓ Gemini (2.0 Flash) - Active
- ✗ ChatGPT (GPT-5 Nano) - Quota exceeded

**Dynamic reweighting:**
- With 2/3 providers: Claude 60% → 100%, Gemini 40% → 100%
- Consensus threshold: 60%

**Example AI log:**
```
AI Signal: NEUTRAL (confidence: 50.83%, consensus: 58.33%)
Providers: claude=NEUTRAL(30%), gemini=LONG(80%)
Action: No trade (below 60% threshold)
Reasoning: Claude flagged overbought RSI, Gemini saw bullish trend
```

---

## ⚠️ Troubleshooting

### No trades for several days

**Normal behavior** - AI may be correctly avoiding unfavorable conditions.

**Check:**
```bash
# View AI rejection reasons
grep "Should Trade: NO" user_data/logs/freqtrade.log

# See confidence scores
grep "Confidence:" user_data/logs/freqtrade.log
```

**If too conservative:**
- Lower threshold from 60% → 55% in `trading_config.json`
- Requires editing config and restarting Freqtrade

### Freqtrade crashed

**Restart:**
```bash
# Stop (if still running)
pkill -9 freqtrade

# Check logs
tail -50 user_data/logs/freqtrade.log

# Restart
./scripts/start_paper_trading.sh
```

### Monitor shows "Database not found"

**Solution:**
- Freqtrade not started yet
- Or database path incorrect
- Check: `ls -la user_data/tradesv3_dryrun.sqlite`

---

## 📋 Success Criteria (After 5-7 Days)

Check these before moving to live trading:

- [ ] Paper trading ran for **minimum 5-7 days**
- [ ] **Win rate > 50%**
- [ ] **Total profit ≥ 0%** (or small loss < 2%)
- [ ] **Max drawdown < 10%**
- [ ] **No critical errors or crashes**
- [ ] **AI consensus working correctly**
- [ ] **Risk limits enforced properly**
- [ ] **Performance within 20% of backtest**

---

## 📅 Daily Routine

**Day 1-7:**

**Morning** (5 min):
```bash
# Check status
uv run python scripts/monitor_paper_trading.py --once

# Check for errors
tail -20 user_data/logs/freqtrade.log | grep -i error
```

**Evening** (5 min):
```bash
# Check trades
uv run python scripts/monitor_paper_trading.py --once

# Review AI decisions
grep "AI Signal" user_data/logs/freqtrade.log | tail -10
```

**Day 7:**
```bash
# Generate final report
uv run python scripts/generate_weekly_report.py \
  --output reports/final_week4_report.txt

# Review report
cat reports/final_week4_report.txt

# Make decision: Deploy live, tune, or redesign
```

---

## 🎉 Next Steps

**If success criteria met:**
1. Review final report carefully
2. Document any observations
3. Prepare for live deployment (start with small capital)
4. See [plan.md](../plan.md) for post-MVP roadmap

**If criteria not met:**
1. Analyze failure modes
2. Tune parameters in `trading_config.json`
3. Run another 5-7 day session
4. Consider strategy adjustments

---

## 📚 Additional Resources

- [paper_trading_guide.md](./paper_trading_guide.md) - Comprehensive paper trading guide
- [troubleshooting.md](./troubleshooting.md) - Common issues and solutions
- [trading_config_guide.md](./trading_config_guide.md) - Configuration reference

---

**Good luck with Week 4 paper trading!** 🚀

Remember: Patience is key. Low trade frequency is expected and healthy for a conservative AI-driven strategy.

---

**Last Updated**: 2025-10-08
