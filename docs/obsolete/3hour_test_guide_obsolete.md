# 3-Hour Paper Trading Test - Mean Reversion Strategy

Complete guide for running a 3-hour paper trading test of the Mean Reversion strategy.

---

## 📋 Overview

**Purpose:** Validate mean reversion strategy logic in live market conditions with real-time data

**Test Configuration:**
- **Strategy:** MeanReversionTest (aggressive test version)
- **Duration:** 3 hours
- **Mode:** Dry-run (paper trading, no real money)
- **Timeframe:** 1h (faster than production 4h)
- **Pairs:** BTC/USDT, ETH/USDT
- **Wallet:** $10,000 USDT (simulated)
- **Stake per trade:** $100 USDT
- **Max open trades:** 2

**Key Differences from Production:**
- More aggressive RSI thresholds (35/65 vs 30/70) for more opportunities
- Shorter timeframe (1h vs 4h) for faster results
- Tighter ROI targets (2%/1%/0.5% vs 4%/2%/1%)
- Enhanced logging for monitoring
- AI confirmation disabled for simplicity

---

## 🚀 Quick Start

### Option 1: Automated Test (Recommended)

Run the automated 3-hour test script:

```bash
cd /Users/jlim/Projects/proratio
./scripts/run_3h_test.sh
```

This will:
1. Check Docker containers (start if needed)
2. Start Freqtrade with test configuration
3. Monitor for 3 hours
4. Auto-stop and generate summary

### Option 2: Manual Test

If you prefer manual control:

```bash
# Start Freqtrade
PYTHONPATH=/Users/jlim/Projects/proratio:$PYTHONPATH uv run freqtrade trade \
  --strategy MeanReversionTest \
  --config proratio_utilities/config/freqtrade/config_test_3h.json \
  --userdir user_data \
  --logfile user_data/logs/test_3h.log

# Stop after 3 hours (Ctrl+C)
```

---

## 📊 Monitoring During Test

### Real-time Log Monitoring

```bash
# Watch main log
tail -f user_data/logs/test_3h_*.log

# Watch for entry signals
tail -f user_data/logs/test_3h_*.log | grep "ENTRY OPPORTUNITY"

# Watch for trade executions
tail -f user_data/logs/test_3h_*.log | grep "TRADE"

# Watch for exits
tail -f user_data/logs/test_3h_*.log | grep "EXIT SIGNAL"
```

### REST API Monitoring

The test runs an API server on port 8081:

```bash
# Check bot status
curl http://localhost:8081/api/v1/status

# Check current trades
curl http://localhost:8081/api/v1/status | jq '.open_trades'

# Check performance
curl http://localhost:8081/api/v1/profit

# View balance
curl http://localhost:8081/api/v1/balance
```

### Web UI (Optional)

If you want a web interface:

```bash
# In another terminal, start FreqUI
cd user_data
npm install -g @freqtrade/frequi
frequi --port 8082
```

Then open: http://localhost:8082

---

## 📈 What to Expect

### Normal Behavior

**Entry Signals:**
- You should see log entries like:
  ```
  [TEST] ENTRY OPPORTUNITY: BTC/USDT
    RSI: 33.21 (threshold: 35)
    Price: 62405.23
    BB Lower: 62450.00
    Timestamp: 2025-10-08 14:30:00
  ```

**Trade Execution:**
- When a trade is entered:
  ```
  [TEST] TRADE ENTRY CONFIRMATION
  Pair: BTC/USDT
  Side: long
  Entry Price: 62405.23 USDT
  Amount: 0.00160256
  Total Value: 100.00 USDT
  ```

**Exits:**
- When price returns to mean or hits ROI/stop-loss:
  ```
  [TEST] EXIT SIGNAL: BTC/USDT
  Entry Price: 62405.23 USDT
  Current Price: 62850.00 USDT
  Profit: +0.71%
  Trade Duration: 1:35:00
  ```

### Expected Opportunities

**Conservative Estimate (1h timeframe):**
- 0-3 entry signals per pair over 3 hours
- Depends on market volatility
- Mean reversion opportunities are less frequent than trend trades

**If Market is Ranging:**
- More opportunities (4-6 signals)
- Higher win rate expected

**If Market is Trending:**
- Fewer opportunities (0-2 signals)
- Lower win rate (mean reversion works best in ranging markets)

---

## 🔍 Post-Test Analysis

### 1. Quick Summary

```bash
# Count total signals
grep "ENTRY OPPORTUNITY" user_data/logs/test_3h_*.log | wc -l

# Count executed trades
grep "TRADE ENTRY CONFIRMATION" user_data/logs/test_3h_*.log | wc -l

# Count exits
grep "EXIT SIGNAL" user_data/logs/test_3h_*.log | wc -l

# View all trades
grep -E "ENTRY CONFIRMATION|EXIT SIGNAL" user_data/logs/test_3h_*.log
```

### 2. Performance Metrics

```bash
# Extract profit/loss data
grep -E "Profit:|profit" user_data/logs/test_3h_*.log

# Count wins vs losses
grep "Profit: +" user_data/logs/test_3h_*.log | wc -l  # Wins
grep "Profit: -" user_data/logs/test_3h_*.log | wc -l  # Losses
```

### 3. Strategy Validation

**Questions to Answer:**

1. **Did signals trigger correctly?**
   - Check if RSI < 35 AND price < BB_lower when entry signal occurred
   - Verify indicators were calculated correctly

2. **Did exits execute as expected?**
   - Check if price reached BB_middle or RSI hit 50
   - Verify ROI/stop-loss levels

3. **Was risk management working?**
   - Max 2 trades open at once
   - Each trade $100 stake
   - Stop-loss limited losses to 2% max

4. **Performance vs backtest?**
   - Compare win rate to backtest (52% from historical test)
   - Similar profit patterns?

---

## 🐛 Troubleshooting

### Issue 1: No Trades After 3 Hours

**Possible Causes:**
1. Market not ranging (trending strongly)
2. RSI not reaching oversold/overbought levels
3. Price not breaching Bollinger Bands

**Solution:**
- This is normal if market is trending
- Check if signals were generated: `grep "ENTRY OPPORTUNITY" log`
- If signals exist but no trades, check entry confirmation logic

### Issue 2: Freqtrade Crashes

**Check:**
```bash
# View error logs
tail -50 user_data/logs/test_3h_*.log

# Common issues:
# - Docker not running (start with docker-compose up -d)
# - PYTHONPATH not set (use automated script)
# - Missing dependencies (run: uv sync)
```

### Issue 3: API Not Responding

**Check:**
```bash
# Is Freqtrade running?
ps aux | grep freqtrade

# Check if port 8081 is in use
lsof -i :8081

# Restart if needed
pkill -f freqtrade
./scripts/run_3h_test.sh
```

### Issue 4: Too Many/Too Few Signals

**Too Many Signals (>10):**
- Market is very volatile
- RSI thresholds might be too loose (35/65)
- Normal for high-volatility periods

**Too Few Signals (0-1):**
- Market is trending (not ranging)
- This is normal for mean reversion
- Try running test during different market conditions

---

## 📝 Test Checklist

Before starting test:
- [ ] Docker containers running (`docker ps`)
- [ ] Historical data downloaded (for indicators)
- [ ] PYTHONPATH set correctly
- [ ] No other Freqtrade instances running (`pgrep freqtrade`)

During test:
- [ ] Monitor logs for errors
- [ ] Check API responds (curl status endpoint)
- [ ] Verify signals are logged
- [ ] Watch for trade executions

After test:
- [ ] Review all entry opportunities
- [ ] Analyze executed trades
- [ ] Compare to backtest results
- [ ] Document any anomalies
- [ ] Save logs for reference

---

## 🎯 Success Criteria

**Test is successful if:**
1. ✅ Freqtrade runs for full 3 hours without crashes
2. ✅ Entry signals are logged when conditions met
3. ✅ Trades execute correctly when signals trigger
4. ✅ Exits happen at expected levels (mean/ROI/stop-loss)
5. ✅ Risk limits respected (max 2 trades, $100 stake)
6. ✅ No errors in logs

**Performance expectations:**
- Win rate: 40-60% (mean reversion baseline)
- If 0 trades: Normal if market trending
- If negative P&L: Acceptable for small sample size
- Match backtest patterns: Good sign

---

## 🔄 Next Steps After Test

### If Test Successful:
1. Run longer paper trading (24h-1week)
2. Test different market conditions
3. Compare 1h vs 4h timeframe performance
4. Enable AI confirmation and retest
5. Optimize parameters with hyperopt

### If Test Failed:
1. Review logs for errors
2. Fix any bugs found
3. Adjust parameters if needed
4. Rerun test
5. Consider different strategy

### Preparing for Live Trading:
1. Paper trade for minimum 2 weeks
2. Achieve positive results
3. Validate risk management
4. Start with small capital (1-5% of intended)
5. Use production config (config_live.json)

---

## 📚 Related Documentation

- [strategy_development_guide.md](./strategy_development_guide.md) - Strategy development
- [backtesting_guide.md](./backtesting_guide.md) - Backtesting guide
- [paper_trading_guide.md](./paper_trading_guide.md) - Full paper trading guide
- [Freqtrade Docs](https://www.freqtrade.io/en/stable/) - Official documentation

---

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `user_data/logs/test_3h_*.log`
2. Review this guide's troubleshooting section
3. Check Freqtrade docs: https://www.freqtrade.io
4. Verify strategy code in `user_data/strategies/MeanReversionTest.py`

---

**Test Version:** 1.0
**Last Updated:** 2025-10-08
**Strategy:** MeanReversionTest
**Timeframe:** 1h
**Duration:** 3 hours
