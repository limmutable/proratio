# Backtest Commands Reference

Quick reference for running ML-only backtests with HybridMLLLMStrategy.

## ⚠️ Important Notes

1. **Current Limitation**: HybridMLLLMStrategy still calls LLM (which fails with `OHLCVData.tail()` error)
2. **ML Works**: ML predictions work correctly (31.5% confidence)
3. **Strategy Issue**: Strategy only evaluates first candle (not vectorized for backtesting)
4. **Expected Result**: 0 trades due to strategy architecture (see Phase 4.5 for fix)

## 🚀 Quick Start

### Option 1: Use the automated script
```bash
# Clear cache and run backtest in one command
./scripts/run_ml_backtest.sh
```

### Option 2: Manual steps
```bash
# Step 1: Clear cache
./scripts/clear_backtest_cache.sh

# Step 2: Run backtest
./venv/bin/freqtrade backtesting \
  --strategy HybridMLLLMStrategy \
  --timeframe 4h \
  --pairs BTC/USDT \
  --timerange 20240101-20251014 \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data
```

## 📊 Backtest Variations

### Short test (3 months)
```bash
./venv/bin/freqtrade backtesting \
  --strategy HybridMLLLMStrategy \
  --timeframe 4h \
  --pairs BTC/USDT \
  --timerange 20240701-20251001 \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data
```

### Multiple pairs
```bash
./venv/bin/freqtrade backtesting \
  --strategy HybridMLLLMStrategy \
  --timeframe 4h \
  --pairs BTC/USDT ETH/USDT \
  --timerange 20240101-20251014 \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data
```

### Different timeframe (1h)
```bash
./venv/bin/freqtrade backtesting \
  --strategy HybridMLLLMStrategy \
  --timeframe 1h \
  --pairs BTC/USDT \
  --timerange 20240101-20251014 \
  --config proratio_utilities/config/freqtrade/config_dry.json \
  --userdir user_data
```

## 🗑️ Cache Management

### Clear all cache
```bash
./scripts/clear_backtest_cache.sh
```

### Manual cache clearing
```bash
# Backtest results
rm -f user_data/backtest_results/*.zip
rm -f user_data/backtest_results/*.json
rm -f user_data/backtest_results/*.meta.json

# Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
```

## 🔍 View Results

### List backtest results
```bash
ls -lth user_data/backtest_results/
```

### View latest result
```bash
cat user_data/backtest_results/.last_result.json | jq
```

## 🐛 Troubleshooting

### Issue: "Reusing result of previous backtest"
**Solution**: Clear cache first
```bash
./scripts/clear_backtest_cache.sh
```

### Issue: "Config file not found"
**Solution**: Ensure config path is correct
```bash
ls -l proratio_utilities/config/freqtrade/config_dry.json
```

### Issue: "Ensemble model not found"
**Solution**: Train the model first
```bash
./venv/bin/python scripts/train_ensemble_model.py \
  --pair BTC/USDT \
  --timeframe 4h \
  --ensemble-method stacking \
  --save models/ensemble_model.pkl
```

### Issue: "No trades generated"
**Expected**: This is a known issue with the current strategy architecture
- Strategy only evaluates first candle
- Designed for live trading, not backtesting
- **Fix**: Phase 4.5 - Create ML-only backtest strategy

## 📋 Current Status

**What Works** ✅:
- Cache clearing
- ML model loads successfully
- ML predictions generated (31.5% confidence)
- Feature engineering (65 features, 0 NaN)

**What Doesn't Work** ❌:
- LLM calls fail (OHLCVData.tail() error)
- Strategy not vectorized for backtesting
- Results in 0 trades (expected)

**Next Steps**:
- Phase 4.5: Create dedicated ML-only backtest strategy
- See: `docs/project/phase4_integration_status_20251015.md`

## 📚 Related Documentation

- Strategy code: `user_data/strategies/HybridMLLLMStrategy.py`
- Integration status: `docs/project/phase4_integration_status_20251015.md`
- Ensemble training: `docs/project/ensemble_model_training_summary_20251015.md`
- Roadmap: `docs/project/roadmap.md` (Phase 4.5)

---

*Last Updated: 2025-10-15*
*Phase: 4 (Partial) → 4.5 (ML-Only Backtest)*
