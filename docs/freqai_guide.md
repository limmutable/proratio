# FreqAI Guide - Machine Learning Integration

**Last Updated**: 2025-10-11
**Phase**: 3.1 - FreqAI Integration & Setup
**Status**: Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Strategy Development](#strategy-development)
6. [Feature Engineering](#feature-engineering)
7. [Training & Backtesting](#training--backtesting)
8. [Model Selection](#model-selection)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

---

## Overview

FreqAI is Freqtrade's machine learning framework that enables adaptive trading strategies through automated model training and prediction. Our implementation combines FreqAI with custom feature engineering to create ML-enhanced strategies.

### Key Benefits

- **Adaptive Learning**: Models retrain automatically with new data
- **Feature Engineering**: 80+ engineered features from market data
- **Multiple Models**: Support for LightGBM, XGBoost, CatBoost, LSTM
- **Backtesting**: Walk-forward validation ensures realistic performance
- **Risk Management**: Outlier detection and confidence scoring

### Expected Improvements

| Metric | Baseline (Phase 2) | Target (Phase 3) | Improvement |
|--------|-------------------|------------------|-------------|
| Win Rate | 61.6% | 65%+ | +5.5% |
| Sharpe Ratio | 1.0 | 1.3+ | +30% |
| Max Drawdown | 15% | <12% | -20% |
| Profit Factor | 1.2 | 1.4+ | +17% |

---

## Architecture

### Data Flow

```
Historical Data → Feature Engineering → ML Model Training → Predictions → Strategy Execution
                        ↓                       ↓                ↓
                 (80+ features)        (LightGBM/LSTM)    (Entry/Exit Signals)
```

### Components

1. **FeatureEngineer** (`proratio_quantlab/ml/feature_engineering.py`)
   - Technical indicators (RSI, MACD, BB, ATR, EMAs, ADX, etc.)
   - Derived features (price changes, volume ratios, volatility)
   - Market regime detection (trending/ranging/volatile)
   - Time features (cyclical hour/day encoding)

2. **FreqAI Core** (Freqtrade built-in)
   - Model training pipeline
   - Walk-forward validation
   - Outlier detection (SVM/DBSCAN)
   - Feature normalization
   - Model persistence

3. **FreqAIStrategy** (`user_data/strategies/FreqAIStrategy.py`)
   - ML prediction integration
   - Technical confirmation filters
   - Confidence-based position sizing
   - Dynamic entry/exit logic

---

## Installation

### 1. Install Dependencies

All required packages are in `requirements.txt`:

```bash
# FreqAI core dependencies
pip install lightgbm==4.5.0 xgboost==2.1.3 catboost==1.2.7
pip install joblib==1.4.2 optuna==4.1.0 shap==0.47.0

# Or install all requirements
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python -c "import lightgbm; print(f'LightGBM {lightgbm.__version__} installed')"
python -c "import xgboost; print(f'XGBoost {xgboost.__version__} installed')"
```

Expected output:
```
LightGBM 4.5.0 installed
XGBoost 2.1.3 installed
```

---

## Configuration

### FreqAI Configuration File

Location: `proratio_utilities/config/freqtrade/config_freqai.json`

Key settings:

```json
{
  "freqai": {
    "enabled": true,
    "train_period_days": 30,        // 30 days training window
    "backtest_period_days": 7,       // 7 days validation window
    "identifier": "proratio_freqai_v1",

    "feature_parameters": {
      "include_timeframes": ["4h", "1h"],  // Multi-timeframe features
      "label_period_candles": 4,            // Predict 4 candles ahead
      "use_SVM_to_remove_outliers": true    // Outlier detection
    },

    "model_training_parameters": {
      "n_estimators": 1000,
      "learning_rate": 0.02,
      "max_depth": 8
    }
  }
}
```

### Configuration Options

#### Training Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `train_period_days` | 30 | Days of historical data for training |
| `backtest_period_days` | 7 | Days for walk-forward validation |
| `purge_old_models` | 2 | Keep only N recent models |

#### Feature Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `include_timeframes` | ["4h", "1h"] | Additional timeframes for features |
| `label_period_candles` | 4 | Prediction horizon (candles ahead) |
| `include_shifted_candles` | 2 | Include lagged features |
| `use_SVM_to_remove_outliers` | true | Enable SVM outlier detection |

#### Model Parameters (LightGBM)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `n_estimators` | 1000 | Number of boosting rounds |
| `learning_rate` | 0.02 | Learning rate (smaller = more conservative) |
| `max_depth` | 8 | Maximum tree depth |
| `num_leaves` | 64 | Maximum leaves per tree |
| `subsample` | 0.8 | Row sampling ratio |
| `colsample_bytree` | 0.8 | Feature sampling ratio |

---

## Strategy Development

### FreqAIStrategy Structure

Our FreqAI strategy (`FreqAIStrategy.py`) follows this structure:

```python
class FreqAIStrategy(IStrategy):
    def populate_indicators(self, dataframe, metadata):
        """Add technical indicators and engineered features"""
        dataframe = self.feature_engineer.add_all_features(dataframe)
        return dataframe

    def feature_engineering_expand_all(self, dataframe, period):
        """Create period-based features for FreqAI"""
        # Add RSI, MFI, ADX, CCI with variable periods
        return dataframe

    def set_freqai_targets(self, dataframe):
        """Define ML prediction targets"""
        # Regression: Predict price change (%)
        # Classification: Predict direction (up/down)
        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        """Entry signals: ML prediction + technical confirmation"""
        # Conditions:
        # 1. ML predicts positive return > threshold
        # 2. Technical confirmation (EMA crossover, RSI, ADX)
        # 3. Data quality check (DI_values < 1)
        return dataframe

    def populate_exit_trend(self, dataframe, metadata):
        """Exit signals: ML reversal + technical signals"""
        # Exit on:
        # 1. ML predicts negative return
        # 2. Technical reversal (EMA crossover, RSI overbought)
        return dataframe

    def custom_stake_amount(self, pair, proposed_stake, **kwargs):
        """Adjust position size based on ML confidence"""
        # Scale stake: 0.8x (low confidence) to 1.2x (high confidence)
        return adjusted_stake
```

### Key Methods for FreqAI

#### 1. Feature Engineering Methods

FreqAI expects methods with specific names:

- `feature_engineering_expand_all(dataframe, period)`: Create features with variable periods
- `feature_engineering_expand_basic(dataframe)`: Create static features
- `feature_engineering_standard(dataframe)`: Combine all features

These methods should prefix feature columns with `%-` to mark them for FreqAI.

#### 2. Target Definition

`set_freqai_targets(dataframe)` defines what the model predicts:

- **Regression target**: `&-target` = future price change (%)
- **Classification target**: `&-target_direction` = future direction (0/1)

#### 3. Prediction Columns

FreqAI adds these columns to your dataframe:

- `do_predict`: 1 if prediction should be made, 0 otherwise
- `&-target`: Model's prediction (regression value or probability)
- `DI_values`: Dissimilarity Index (data quality check, <1 = good)

---

## Feature Engineering

Our `FeatureEngineer` class creates 80+ features from raw OHLCV data.

### Feature Categories

#### 1. Technical Indicators (20+ features)

```python
# Momentum
- RSI (14, 21, 7 periods)
- Stochastic (14, 3, 3)
- CCI (20)
- Williams %R (14)

# Trend
- EMA (9, 21, 50, 200)
- MACD (12, 26, 9)
- ADX (14)

# Volatility
- Bollinger Bands (20, 2)
- ATR (14)
```

#### 2. Price Features (15+ features)

```python
# Price changes
- close_pct_change (1, 4, 8, 24 candles)
- high_low_range / close
- close position in range

# Price to moving averages
- close / ema9, close / ema21, close / ema50
- ema9 / ema21 (crossover detection)
```

#### 3. Volume Features (10+ features)

```python
# Volume patterns
- volume_pct_change (1, 4, 8 candles)
- volume / volume_sma_20
- price_volume_correlation (rolling 20)
```

#### 4. Volatility Features (8+ features)

```python
# Volatility measures
- atr_pct (ATR / close)
- rolling_volatility (20, 50 periods)
- bb_pct ((close - bb_lower) / bb_width)
- high_low_pct ((high - low) / close)
```

#### 5. Momentum Features (12+ features)

```python
# Rate of change
- roc (4, 8, 12 periods)
- ema_crossover (ema9 > ema21)
- macd_signal_diff
- adx_trend (adx > 25)
```

#### 6. Regime Features (8+ features)

```python
# Market regime detection
- is_trending (adx > 25 & ema9 > ema21)
- is_ranging (adx < 20 & bb_width < threshold)
- is_volatile (rolling_volatility > threshold)
- regime_strength (0-1 scale)
```

#### 7. Time Features (4+ features)

```python
# Cyclical time encoding
- hour_sin, hour_cos (24-hour cycle)
- day_of_week_sin, day_of_week_cos (7-day cycle)
```

### Adding Custom Features

To add custom features, edit `proratio_quantlab/ml/feature_engineering.py`:

```python
class FeatureEngineer:
    def add_custom_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Add your custom features here"""

        # Example: Price distance from VWAP
        dataframe['vwap'] = (dataframe['close'] * dataframe['volume']).cumsum() / \
                            dataframe['volume'].cumsum()
        dataframe['close_to_vwap'] = (dataframe['close'] - dataframe['vwap']) / dataframe['vwap']

        # Example: Order book imbalance (if available)
        # dataframe['bid_ask_imbalance'] = (bids - asks) / (bids + asks)

        return dataframe
```

Then call it in `add_all_features()`:

```python
def add_all_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
    df = dataframe.copy()
    df = self.add_technical_indicators(df)
    df = self.add_price_features(df)
    # ... other features ...
    df = self.add_custom_features(df)  # Add this line
    return df
```

---

## Training & Backtesting

### Training Process

FreqAI trains models automatically during backtesting using walk-forward analysis:

1. **Initial Training**: Train on first `train_period_days` (30 days)
2. **Validation**: Test on next `backtest_period_days` (7 days)
3. **Walk Forward**: Move window forward and retrain
4. **Repeat**: Continue until all data is processed

### Running a Backtest

```bash
# Download historical data (if not already done)
freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT ETH/USDT \
  --timeframe 4h 1h \
  --days 180 \
  --userdir user_data

# Run FreqAI backtest
freqtrade backtesting \
  --strategy FreqAIStrategy \
  --timeframe 4h \
  --config proratio_utilities/config/freqtrade/config_freqai.json \
  --userdir user_data \
  --timerange 20240101-20240401
```

### Expected Output

```
=========================================================== BACKTESTING REPORT
| Pair      | Entries | Avg Profit % | Total Profit USDT | Win Rate % |
|-----------+---------+--------------+-------------------+------------|
| BTC/USDT  | 23      | 2.34         | 538.20            | 69.6       |
| ETH/USDT  | 28      | 1.89         | 529.20            | 64.3       |
| TOTAL     | 51      | 2.09         | 1067.40           | 66.7       |

FreqAI Model Stats:
- Total models trained: 13
- Avg training time: 45.2s
- Feature count: 84
- Best iteration: 7 (Sharpe: 1.45)
```

### Analyzing Results

Check trained models:

```bash
ls -lh user_data/models/proratio_freqai_v1/
```

You should see:

```
btcusdt_model_2024-01-15.pkl
btcusdt_model_2024-02-01.pkl
...
ethusdt_model_2024-01-15.pkl
```

View feature importance:

```python
import joblib
import pandas as pd

# Load a trained model
model = joblib.load('user_data/models/proratio_freqai_v1/btcusdt_model_2024-02-01.pkl')

# Get feature importance
importance = pd.DataFrame({
    'feature': model.feature_name_,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(importance.head(20))
```

---

## Model Selection

FreqAI supports multiple ML models. Our default is LightGBM, but you can experiment with others.

### Available Models

#### 1. LightGBMRegressor (Default)

**Best for**: Fast training, good generalization, interpretable

**Config**:
```json
"freqaimodel": "LightGBMRegressor",
"model_training_parameters": {
  "n_estimators": 1000,
  "learning_rate": 0.02,
  "max_depth": 8,
  "num_leaves": 64
}
```

**Pros**:
- Fast training (30-60s per model)
- Handles missing values
- Feature importance available
- Good default choice

**Cons**:
- May underfit complex patterns
- Less flexible than neural networks

#### 2. XGBoostRegressor

**Best for**: Maximum accuracy, feature engineering emphasis

**Config**:
```json
"freqaimodel": "XGBoostRegressor",
"model_training_parameters": {
  "n_estimators": 1000,
  "learning_rate": 0.02,
  "max_depth": 8,
  "subsample": 0.8,
  "colsample_bytree": 0.8
}
```

**Pros**:
- Often highest accuracy
- Robust to overfitting
- Fast prediction

**Cons**:
- Slower training than LightGBM
- More memory intensive

#### 3. CatBoostRegressor

**Best for**: Categorical features, robust defaults

**Config**:
```json
"freqaimodel": "CatBoostRegressor",
"model_training_parameters": {
  "iterations": 1000,
  "learning_rate": 0.02,
  "depth": 8
}
```

**Pros**:
- Handles categorical features natively
- Good defaults (less tuning needed)
- Built-in regularization

**Cons**:
- Slowest training
- Less popular (fewer resources)

#### 4. PyTorchMLPRegressor (Neural Network)

**Best for**: Complex patterns, large datasets

**Config**:
```json
"freqaimodel": "PyTorchMLPRegressor",
"model_training_parameters": {
  "learning_rate": 0.001,
  "trainer_kwargs": {
    "max_epochs": 100,
    "patience": 10
  }
}
```

**Pros**:
- Can learn complex non-linear patterns
- Flexible architecture
- Good for time-series with LSTM

**Cons**:
- Requires more data (6+ months)
- Longer training (5-10 min per model)
- Harder to interpret

### Choosing a Model

| Criteria | Best Choice |
|----------|-------------|
| **Speed** | LightGBM |
| **Accuracy** | XGBoost or CatBoost |
| **Interpretability** | LightGBM (SHAP values) |
| **Complex patterns** | PyTorch Neural Network |
| **Small dataset** | LightGBM or XGBoost |
| **Large dataset** | Any (XGBoost/PyTorch scale well) |
| **Default choice** | **LightGBM** (best balance) |

---

## Performance Optimization

### 1. Feature Selection

Not all 80+ features may be useful. Reduce features for faster training:

```python
# In FreqAIStrategy, after training first model
def feature_engineering_standard(self, dataframe):
    # Only keep top 30 most important features
    important_features = [
        'rsi_14', 'macd', 'bb_width', 'atr_pct',
        'close_pct_change_4', 'volume_pct_change_4',
        'ema_crossover', 'is_trending', 'adx',
        # ... add more based on feature_importances_
    ]
    return dataframe[important_features]
```

### 2. Training Window Optimization

Adjust training window based on market conditions:

```json
// Volatile markets: Shorter training window (more recent data)
"train_period_days": 15,
"backtest_period_days": 3

// Stable markets: Longer training window (more data)
"train_period_days": 60,
"backtest_period_days": 14
```

### 3. Hyperparameter Tuning

Use Optuna for automated hyperparameter optimization:

```bash
freqtrade hyperopt \
  --strategy FreqAIStrategy \
  --hyperopt-loss SharpeHyperOptLoss \
  --epochs 100 \
  --spaces freqai \
  --config proratio_utilities/config/freqtrade/config_freqai.json
```

This will optimize:
- Model parameters (learning_rate, max_depth, n_estimators)
- Feature parameters (include_shifted_candles, label_period_candles)
- Entry/exit thresholds (ml_prediction_threshold, ml_min_confidence)

### 4. Multi-GPU Training (Advanced)

For neural networks, enable GPU training:

```json
"model_training_parameters": {
  "trainer_kwargs": {
    "accelerator": "gpu",
    "devices": 1
  }
}
```

---

## Troubleshooting

### Issue 1: "No models trained" error

**Symptom**: Backtest fails with "FreqAI: No models found"

**Solution**:
```bash
# Ensure enough training data
freqtrade download-data --days 90  # Need at least train_period_days + 30

# Check config has freqai.enabled = true
grep -A 5 '"freqai"' proratio_utilities/config/freqtrade/config_freqai.json

# Verify strategy has set_freqai_targets() method
grep "def set_freqai_targets" user_data/strategies/FreqAIStrategy.py
```

### Issue 2: Poor ML performance (worse than baseline)

**Symptom**: ML strategy underperforms non-ML strategies

**Possible causes & solutions**:

1. **Overfitting**: Model memorizes training data
   ```json
   // Solution: Increase regularization
   "model_training_parameters": {
     "reg_alpha": 0.5,     // L1 regularization
     "reg_lambda": 0.5,    // L2 regularization
     "subsample": 0.7      // Reduce to 70% row sampling
   }
   ```

2. **Look-ahead bias**: Using future data in features
   ```python
   # BAD: Uses future data
   dataframe['future_return'] = dataframe['close'].pct_change().shift(-4)

   # GOOD: Only uses past data
   dataframe['past_return'] = dataframe['close'].pct_change(4)
   ```

3. **Insufficient training data**:
   ```bash
   # Download more historical data
   freqtrade download-data --days 365
   ```

4. **Wrong prediction horizon**:
   ```json
   // For 4h timeframe, predict 4 candles = 16 hours ahead
   "label_period_candles": 4,

   // For 1h timeframe, predict 16 candles = 16 hours ahead
   "label_period_candles": 16
   ```

### Issue 3: Training is too slow

**Symptom**: Each model takes 5+ minutes to train

**Solutions**:

1. **Reduce features**:
   ```python
   # Keep only top 30 features based on importance
   ```

2. **Reduce estimators**:
   ```json
   "n_estimators": 500  // Instead of 1000
   ```

3. **Use LightGBM instead of XGBoost**:
   ```json
   "freqaimodel": "LightGBMRegressor"  // 2-3x faster
   ```

4. **Enable parallel processing**:
   ```json
   "n_jobs": -1  // Use all CPU cores
   ```

### Issue 4: High memory usage

**Symptom**: System runs out of RAM during training

**Solutions**:

1. **Reduce training window**:
   ```json
   "train_period_days": 20  // Instead of 30
   ```

2. **Reduce feature count**: Keep only essential features

3. **Lower max_depth**:
   ```json
   "max_depth": 6  // Instead of 8
   ```

4. **Process fewer pairs**: Start with BTC/USDT only

### Issue 5: DI_values always > 1 (no predictions)

**Symptom**: `do_predict` column is always 0

**Cause**: Dissimilarity Index too high (data is too different from training)

**Solution**:
```json
// Increase DI threshold or disable
"feature_parameters": {
  "DI_threshold": 1.0  // Allow more dissimilar data (default: 0)
}
```

Or in strategy:
```python
# Remove DI check from entry conditions
ml_conditions = (
    (dataframe['do_predict'] == 1) &
    (dataframe['&-target'] > self.ml_prediction_threshold)
    # (dataframe['DI_values'] < 1)  # <-- Remove this line
)
```

---

## Best Practices

### 1. Start Simple

- Begin with LightGBM regressor (fastest, good baseline)
- Use default hyperparameters first
- Add complexity only if needed

### 2. Validate Rigorously

- Always use walk-forward validation (FreqAI does this automatically)
- Test on out-of-sample data (different time period)
- Compare against non-ML baseline strategy

### 3. Monitor Model Drift

- Check if model performance degrades over time
- Retrain more frequently if market conditions change
- Set up alerts for poor performance

### 4. Combine with Risk Management

- ML predictions are not perfect - use stop-losses
- Size positions based on confidence scores
- Diversify across multiple pairs and strategies

### 5. Document Everything

- Track which features work best
- Record hyperparameter changes
- Note market conditions during testing

---

## Next Steps

1. **Phase 3.2**: Implement LSTM price prediction models
2. **Phase 3.3**: Create ensemble models combining multiple predictors
3. **Phase 3.4**: Experiment with reinforcement learning (optional)

---

## Related Documentation

- [Phase 3 Plan](phase3_plan.md) - Overall ML integration roadmap
- [Strategy Development Guide](strategy_development_guide.md) - Strategy patterns and best practices
- [Backtesting Guide](backtesting_guide.md) - Testing and validation methods
- [Feature Engineering Code](../proratio_quantlab/ml/feature_engineering.py) - Technical reference

---

**Questions or issues?** Check Freqtrade FreqAI docs: https://www.freqtrade.io/en/stable/freqai/
