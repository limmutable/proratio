# ML Paper Trading Guide - 3 Hour Test Run

Complete guide for running live paper trading with the ML ensemble model.

---

## 🎯 Quick Start

```bash
# 1. Start paper trading (runs in background for 3 hours)
./scripts/start_ml_paper_trading.sh

# 2. Monitor in real-time (optional)
./scripts/monitor_ml_paper_trading.sh

# 3. Stop when done (after 3 hours or anytime)
./scripts/stop_ml_paper_trading.sh
```

---

## 📋 Prerequisites

### 1. Ensemble Model
Ensure the trained model exists:
```bash
ls -lh models/ensemble_model.pkl
```

If not, train it first:
```bash
./venv/bin/python scripts/train_ensemble_model.py \
  --pair BTC/USDT \
  --timeframe 4h \
  --ensemble-method stacking \
  --save models/ensemble_model.pkl
```

### 2. Market Data
Fresh data is downloaded automatically, but you can pre-download:
```bash
./venv/bin/freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT \
  --timeframe 4h \
  --days 2 \
  --userdir user_data
```

---

## 🚀 Starting Paper Trading

### Command
```bash
./scripts/start_ml_paper_trading.sh
```

### What It Does
1. ✅ Checks if ensemble model exists
2. ✅ Clears old logs
3. ✅ Downloads latest market data
4. ✅ Starts Freqtrade in background
5. ✅ Validates startup
6. ✅ Provides monitoring commands

### Expected Output
```
╔════════════════════════════════════════════╗
║  ML Ensemble Paper Trading Test (3 hours) ║
╚════════════════════════════════════════════╝

✅ Ensemble model found (2.9M)

📋 Configuration:
  Strategy: HybridMLLLMStrategy
  Pair: BTC/USDT
  Timeframe: 4h
  Initial Balance: 10,000 USDT
  Max Open Trades: 2
  Stake per Trade: 100 USDT

📝 Logging:
  Main Log: user_data/logs/paper_trading_ml_test.log
  API: http://localhost:8080 (admin/admin)

⏰ Test Duration: 3 hours
🚀 Starting paper trading...
✅ Paper trading started successfully!

╔════════════════════════════════════════════╗
║            PAPER TRADING ACTIVE            ║
╚════════════════════════════════════════════╝

PID: 12345
Started: Tue Oct 15 14:30:00 PDT 2025
Expected End: Tue Oct 15 17:30:00 PDT 2025
```

---

## 📊 Monitoring

### Option 1: Live Monitor Script
```bash
./scripts/monitor_ml_paper_trading.sh
```

This shows:
- ML predictions
- LLM predictions (will fail - expected)
- Hybrid signals
- Trade entries/exits
- Warnings/errors

### Option 2: View Full Log
```bash
tail -f user_data/logs/paper_trading_ml_test.log
```

### Option 3: Filter for Specific Events

**ML Predictions Only:**
```bash
tail -f user_data/logs/paper_trading_ml_test.log | grep "ML Prediction"
```

**Trades Only:**
```bash
tail -f user_data/logs/paper_trading_ml_test.log | grep -i "buy\|sell\|entry\|exit"
```

**Errors/Warnings:**
```bash
tail -f user_data/logs/paper_trading_ml_test.log | grep -i "error\|warning"
```

**Signal Strength:**
```bash
tail -f user_data/logs/paper_trading_ml_test.log | grep "HYBRID SIGNAL"
```

---

## 🛑 Stopping Paper Trading

### Graceful Stop
```bash
./scripts/stop_ml_paper_trading.sh
```

This will:
1. Send SIGTERM signal
2. Wait up to 30 seconds for graceful shutdown
3. Force kill if necessary
4. Clean up PID file

### Check if Still Running
```bash
ps aux | grep freqtrade
```

---

## 📝 What to Expect

### ML Predictions
You'll see output like:
```
ML Prediction: up (31.5% confidence)
```

**Expected Confidence Range:** 20-60%
- < 30% = Very conservative
- 30-50% = Moderate confidence
- > 50% = High confidence (rare with current model)

### LLM Failures (Expected)
```
→ ChatGPT (gpt-4o-mini)... ✗
  Error: 'OHLCVData' object has no attribute 'tail'
```

**This is expected** - LLM integration has known issues (Phase 4 status)

### Hybrid Signals
```
HYBRID SIGNAL: WAIT
════════════════════════════════════════════════
ML Prediction: UP (31.5% confidence)
LLM Prediction: NEUTRAL (0.0% confidence)
Agreement Score: 23.7%
```

### Trade Execution
**If thresholds are met:**
```
✅ ENTRY SIGNAL: BTC/USDT - LONG (strong, 67% confidence)
```

**Most likely result:**
- Signal strength: WEAK or MODERATE
- Combined confidence: 15-35% (below 65% threshold)
- Action: WAIT
- **Trades: 0** (expected due to low confidence)

---

## 📁 Log Files

### Main Log
```bash
user_data/logs/paper_trading_ml_test.log
```

Contains:
- Freqtrade startup messages
- Strategy initialization
- ML model loading
- Predictions and signals
- Trade executions (if any)
- All warnings and errors

### View Last 100 Lines
```bash
tail -100 user_data/logs/paper_trading_ml_test.log
```

### Search for Specific Content
```bash
grep -i "confidence" user_data/logs/paper_trading_ml_test.log
```

---

## 🔍 Debugging

### Check Process Status
```bash
# Is it running?
ps aux | grep freqtrade | grep -v grep

# Check PID file
cat /tmp/freqtrade_ml_paper.pid
```

### View Recent Errors
```bash
grep -i "error" user_data/logs/paper_trading_ml_test.log | tail -20
```

### Check ML Model Loading
```bash
grep "Ensemble predictor loaded" user_data/logs/paper_trading_ml_test.log
```

### View All Predictions
```bash
grep "ML Prediction\|LLM Prediction\|Hybrid Signal" user_data/logs/paper_trading_ml_test.log
```

### API Health Check
```bash
curl http://localhost:8080/api/v1/ping
```

---

## ⚙️ Configuration

### Paper Trading Config
Located at: `proratio_utilities/config/freqtrade/config_paper_ml_test.json`

**Key Settings:**
```json
{
  "max_open_trades": 2,
  "stake_amount": 100,
  "dry_run": true,
  "dry_run_wallet": 10000,
  "pair_whitelist": ["BTC/USDT"],
  "api_server": {
    "enabled": true,
    "listen_port": 8080,
    "username": "admin",
    "password": "admin"
  }
}
```

### Strategy Settings
In `user_data/strategies/HybridMLLLMStrategy.py`:

```python
min_combined_confidence = 0.65  # 65% threshold
min_agreement_score = 0.70      # 70% agreement needed
```

**Why 0 trades is expected:**
- ML confidence: ~31%
- LLM fails: 0%
- Combined: ~19% (below 65% threshold)
- Signal strength: WEAK (needs STRONG or VERY_STRONG)

---

## 📈 After 3 Hours

### 1. Stop Trading
```bash
./scripts/stop_ml_paper_trading.sh
```

### 2. Analyze Logs
```bash
# Total predictions made
grep -c "ML Prediction" user_data/logs/paper_trading_ml_test.log

# Confidence distribution
grep "ML Prediction" user_data/logs/paper_trading_ml_test.log | \
  grep -oP '\d+\.\d+% confidence' | sort | uniq -c

# Any trades executed?
grep -i "buy\|sell" user_data/logs/paper_trading_ml_test.log | wc -l

# Errors summary
grep -i "error" user_data/logs/paper_trading_ml_test.log | \
  cut -d':' -f4- | sort | uniq -c | sort -rn
```

### 3. Review Performance
```bash
# View final statistics (if any trades)
cat user_data/logs/paper_trading_ml_test.log | grep -A 20 "BACKTESTING REPORT"
```

### 4. Backup Logs
```bash
# Create timestamped backup
cp user_data/logs/paper_trading_ml_test.log \
   user_data/logs/paper_trading_ml_test_$(date +%Y%m%d_%H%M%S).log
```

---

## 🎯 Success Criteria

### What to Look For

**✅ Positive Signs:**
- [x] Ensemble model loads without errors
- [x] ML predictions generated (~every 4 hours)
- [x] Feature engineering works (65 features, 0 NaN)
- [x] Predictions show varying confidence levels
- [x] No Python crashes or exceptions

**⚠️ Expected Limitations:**
- [ ] LLM calls fail (known issue - Phase 4 status)
- [ ] 0 trades executed (confidence below threshold)
- [ ] Signal strength = WEAK (expected with current model)

**❌ Problems to Report:**
- [ ] Freqtrade crashes
- [ ] Model loading errors
- [ ] Feature engineering failures
- [ ] NaN/infinite value errors
- [ ] Memory leaks

---

## 💡 Tips

1. **First Hour:** Check logs every 15 minutes to ensure stable operation
2. **Mid-Test:** Let it run undisturbed for pure results
3. **Last Hour:** Start preparing analysis scripts
4. **After:** Review all predictions, not just trades

---

## 🔧 Troubleshooting

### Problem: "Ensemble model not found"
**Solution:**
```bash
ls models/ensemble_model.pkl
# If missing, train it:
./venv/bin/python scripts/train_ensemble_model.py \
  --pair BTC/USDT --timeframe 4h --ensemble-method stacking \
  --save models/ensemble_model.pkl
```

### Problem: "Already running"
**Solution:**
```bash
./scripts/stop_ml_paper_trading.sh
# Wait 5 seconds, then:
./scripts/start_ml_paper_trading.sh
```

### Problem: "Failed to start"
**Solution:**
```bash
# Check last 50 lines for errors
tail -50 user_data/logs/paper_trading_ml_test.log

# Common causes:
# - Port 8080 already in use
# - Missing dependencies
# - Corrupted model file
```

### Problem: "No predictions showing"
**Solution:**
```bash
# Check if strategy is evaluating
grep "Generating hybrid signal" user_data/logs/paper_trading_ml_test.log

# If none, check Freqtrade is processing candles
grep "analyze" user_data/logs/paper_trading_ml_test.log
```

---

## 📞 Support

For issues:
1. Check logs: `user_data/logs/paper_trading_ml_test.log`
2. Review status: `docs/project/phase4_integration_status_20251015.md`
3. Check known issues in Phase 4 documentation

---

## 🔗 Related Documentation

- [Phase 4 Integration Status](../project/phase4_integration_status_20251015.md)
- [Ensemble Training Summary](../project/ensemble_model_training_summary_20251015.md)
- [Roadmap - Phase 4.5](../project/roadmap.md)
- [Backtest Commands](../../scripts/BACKTEST_COMMANDS.md)

---

*Created: 2025-10-15*
*Phase: 4 (Paper Trading Validation)*
*Expected Duration: 3 hours*
