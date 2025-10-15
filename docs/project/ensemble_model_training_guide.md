# Ensemble Model Training Guide

**Date**: October 15, 2025
**Status**: Pending - Infrastructure Ready, Data Loading API Needs Update
**Priority**: HIGH (Required for HybridMLLLMStrategy Phase 4)

---

## 🎯 Purpose

Train a full ensemble model (LSTM + LightGBM + XGBoost) to replace the SimpleFallbackPredictor currently used in HybridMLLLMStrategy. This will enable the hybrid ML+LLM system to achieve its expected performance:

- Win rate: 65-70% (vs 45-50% baseline)
- Sharpe ratio: 2.0-2.5 (vs 1.0-1.2 baseline)
- False signals: -40-60% reduction
- Max drawdown: -10-12% (vs -18-22% baseline)

---

## 📋 Current Status

### ✅ Infrastructure Ready

1. **EnsemblePredictor Class** (`proratio_quantlab/ml/ensemble_predictor.py`)
   - Supports stacking, blending, voting methods
   - Handles LSTM + LightGBM + XGBoost combinations
   - Save/load functionality
   - Dynamic weight adjustment
   - Status: ✅ COMPLETE (650 lines)

2. **Training Script** (`scripts/train_ensemble_model.py`)
   - Complete end-to-end training pipeline
   - Feature engineering integration
   - Train/val/test splitting
   - Model evaluation
   - Status: ✅ COMPLETE (299 lines)

3. **Integration Point** (`user_data/strategies/HybridMLLLMStrategy.py`)
   - Lazy loading pattern for ensemble model
   - SimpleFallbackPredictor as temporary solution
   - Model path: `models/ensemble_model.pkl`
   - Status: ✅ READY FOR ENSEMBLE

### ⚠️ Pending Issue

**Data Loading API Mismatch**: The training script uses `DataLoader.load_ohlcv()` which doesn't exist in current codebase. The data collection API has evolved.

**Error**:
```
AttributeError: 'DataLoader' object has no attribute 'load_ohlcv'
```

---

## 🔧 Solution: Update Training Script

The training script needs to be updated to use the current data collection API. Here are the options:

### Option 1: Use Freqtrade Downloaded Data (Recommended)

**Pros**: Data already available from backtesting, no API calls needed
**Cons**: Limited to timeranges we've already downloaded

```python
def load_and_prepare_data(pair: str = "BTC/USDT", timeframe: str = "4h") -> pd.DataFrame:
    """Load data from Freqtrade user_data directory."""
    import json
    from pathlib import Path

    # Freqtrade data path
    data_file = Path(f"user_data/data/binance/{pair.replace('/', '_')}-{timeframe}.json")

    if not data_file.exists():
        raise FileNotFoundError(
            f"Data file not found: {data_file}. "
            f"Download with: freqtrade download-data --pairs {pair} --timeframe {timeframe}"
        )

    # Load JSON data
    with open(data_file) as f:
        data = json.load(f)

    # Convert to DataFrame
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    logger.info(f"✓ Loaded {len(df)} candles from {data_file}")
    return df
```

###Option 2: Use CCXT Directly

**Pros**: Flexible, can get any timerange
**Cons**: Requires API calls, rate limits

```python
def load_and_prepare_data(pair: str = "BTC/USDT", timeframe: str = "4h", limit: int = 5000) -> pd.DataFrame:
    """Load data using CCXT directly."""
    import ccxt

    exchange = ccxt.binance({
        'enableRateLimit': True,
    })

    # Fetch OHLCV data
    ohlcv = exchange.fetch_ohlcv(pair, timeframe, limit=limit)

    # Convert to DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    logger.info(f"✓ Loaded {len(df)} candles from CCXT")
    return df
```

### Option 3: Read From CSV Cache

**Pros**: Simple, fast, reproducible
**Cons**: Requires manual data export first

```python
def load_and_prepare_data(csv_path: str) -> pd.DataFrame:
    """Load data from CSV file."""
    df = pd.DataFrame(csv_path, parse_dates=['timestamp'], index_col='timestamp')
    logger.info(f"✓ Loaded {len(df)} candles from {csv_path}")
    return df
```

---

## 📝 Training Steps (Once Data Loading is Fixed)

### Step 1: Download Training Data

```bash
# Option A: Use Freqtrade downloader (5000 candles = ~2.3 years for 4h)
freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT ETH/USDT \
  --timeframe 4h \
  --days 700 \
  --userdir user_data

# Option B: Export from backtest results (if available)
# Use existing user_data/data/binance/*.json files
```

### Step 2: Train Ensemble Model

```bash
# After fixing the data loading function
./venv/bin/python scripts/train_ensemble_model.py \
  --pair BTC/USDT \
  --timeframe 4h \
  --limit 5000 \
  --ensemble-method stacking \
  --meta-model ridge \
  --save models/ensemble_model.pkl
```

**Expected Training Time**:
- Data loading: ~30 seconds
- Feature engineering: ~1 minute
- LightGBM training: ~2-3 minutes
- XGBoost training: ~2-3 minutes
- LSTM training: ~10-15 minutes (100 epochs)
- Ensemble stacking: ~30 seconds
- **Total**: ~15-20 minutes

### Step 3: Validate Trained Model

```bash
# Check model exists
ls -lh models/ensemble_model.pkl

# Test loading in Python
./venv/bin/python -c "
from proratio_quantlab.ml.ensemble_predictor import EnsemblePredictor
import joblib

config = joblib.load('models/ensemble_model.pkl')
print('Model loaded successfully!')
print(f'Ensemble method: {config[\"ensemble_method\"]}')
print(f'Model names: {config[\"model_names\"]}')
print(f'Weights: {config[\"weights\"]}')
"
```

### Step 4: Test HybridMLLLMStrategy with Trained Ensemble

```bash
# Re-run validation (should generate trades now)
./start.sh strategy validate HybridMLLLMStrategy
```

**Expected Outcome**:
- ML predictions will be much stronger (60-80% confidence vs 16-33%)
- Combined with LLM signals (60-80% confidence), will trigger STRONG/VERY_STRONG signals
- Should generate 5-15 trades over 6-month backtest period
- Win rate expected: 60-65% (before reaching target 65-70%)

---

## 🎯 Expected Results

### Base Model Performance (from Phase 3.3 testing)

| Model | RMSE | MAE | Training Time |
|-------|------|-----|---------------|
| LightGBM | 0.0124 | 0.0089 | ~3 min |
| XGBoost | 0.0129 | 0.0092 | ~3 min |
| LSTM | 0.0118 | 0.0085 | ~15 min |

### Ensemble Performance

| Method | RMSE | Improvement | Training Time |
|--------|------|-------------|---------------|
| Stacking (Ridge) | 0.0108 | **19.66%** | +30 sec |
| Blending (Optimized) | 0.0112 | 16.10% | +2 min |
| Voting (Average) | 0.0115 | 13.56% | +0 sec |

**Recommended**: Stacking with Ridge meta-model (best performance, fast training)

---

## 🚀 Quick Start (After Data Loading Fix)

### 1-Command Training

```bash
# Fix data loading in scripts/train_ensemble_model.py first, then:
./venv/bin/python scripts/train_ensemble_model.py \
  --pair BTC/USDT \
  --timeframe 4h \
  --limit 5000 \
  --ensemble-method stacking \
  --save models/ensemble_model.pkl
```

### Verify Integration

```bash
# Test HybridMLLLMStrategy with trained ensemble
./start.sh strategy validate HybridMLLLMStrategy

# Check for log message:
# "Loaded ensemble model from /Users/jlim/Projects/proratio/models/ensemble_model.pkl"

# Verify trades are generated (not 0)
```

---

## 📊 Monitoring Training Progress

The training script provides detailed progress logs:

```
2025-10-15 10:00:00 - INFO - [1/6] Loading data for BTC/USDT (4h)...
2025-10-15 10:00:05 - INFO - ✓ Loaded 5000 candles

2025-10-15 10:00:05 - INFO - [2/6] Engineering features...
2025-10-15 10:00:45 - INFO - ✓ Created 120 features

2025-10-15 10:00:45 - INFO - [3/6] Preparing train/val/test splits...
2025-10-15 10:00:50 - INFO - ✓ Train: 3500, Val: 750, Test: 750

2025-10-15 10:00:50 - INFO - [4/6] Building stacking ensemble...
2025-10-15 10:00:50 - INFO -   Training lgbm...
2025-10-15 10:03:00 - INFO -   ✓ lgbm trained successfully
2025-10-15 10:03:00 - INFO -   Training xgb...
2025-10-15 10:05:30 - INFO -   ✓ xgb trained successfully
2025-10-15 10:05:30 - INFO -   Training lstm...
2025-10-15 10:20:00 - INFO -   ✓ lstm trained successfully
2025-10-15 10:20:00 - INFO - ✓ Ensemble built successfully

2025-10-15 10:20:00 - INFO - [5/6] Evaluating ensemble...

============================================================
ENSEMBLE EVALUATION RESULTS
============================================================

ENSEMBLE
  RMSE: 0.010800
  MAE:  0.007800
  MSE:  0.000117

LGBM
  RMSE: 0.012400
  MAE:  0.008900
  MSE:  0.000154

XGB
  RMSE: 0.012900
  MAE:  0.009200
  MSE:  0.000166

LSTM
  RMSE: 0.011800
  MAE:  0.008500
  MSE:  0.000139

------------------------------------------------------------
Ensemble improvement: 19.66% better than best base model
------------------------------------------------------------

2025-10-15 10:20:05 - INFO - [6/6] Saving ensemble to models/ensemble_model.pkl...
2025-10-15 10:20:05 - INFO - ✓ Model saved

✓ Training complete!
```

---

## 🐛 Troubleshooting

### Issue: ModuleNotFoundError

```bash
# Use venv python directly (not uv run python)
./venv/bin/python scripts/train_ensemble_model.py ...
```

### Issue: CUDA Out of Memory (LSTM)

```bash
# Reduce batch size or hidden size
--sequence-length 12  # Instead of 24
# Or disable LSTM
--no-lstm
```

### Issue: Data Not Found

```bash
# Download data first
freqtrade download-data --pairs BTC/USDT --timeframe 4h --days 700 --userdir user_data
```

### Issue: Training Takes Too Long

```bash
# Use smaller dataset
--limit 2000  # Instead of 5000

# Or exclude LSTM (fastest)
--no-lstm
```

---

## 📚 References

- **Ensemble Predictor**: [proratio_quantlab/ml/ensemble_predictor.py](../../proratio_quantlab/ml/ensemble_predictor.py)
- **Training Script**: [scripts/train_ensemble_model.py](../../scripts/train_ensemble_model.py)
- **HybridMLLLMStrategy**: [user_data/strategies/HybridMLLLMStrategy.py](../../user_data/strategies/HybridMLLLMStrategy.py)
- **Phase 3.3 Results**: [docs/project/roadmap.md](roadmap.md#phase-33-ensemble-learning)

---

**Last Updated**: October 15, 2025
**Next Step**: Fix data loading function in `scripts/train_ensemble_model.py` to use current API
