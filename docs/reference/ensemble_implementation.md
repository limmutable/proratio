# Ensemble Learning Implementation Guide

**Phase 3.3 - Ensemble Learning System**
**Author:** Proratio Team
**Date:** October 11, 2025
**Status:** ✅ Complete

## Overview

The Ensemble Learning module combines predictions from multiple machine learning models (LSTM, LightGBM, XGBoost) to achieve better prediction accuracy and robustness than individual models. This implementation supports three ensemble strategies: **stacking**, **blending**, and **voting**.

### Why Ensemble Learning?

- **Improved Accuracy**: Combines strengths of different model types (neural networks + gradient boosting)
- **Reduced Overfitting**: Diverse models capture different patterns, reducing overfitting risk
- **Robustness**: Less sensitive to outliers and noise
- **Adaptability**: Dynamic weighting adjusts to changing market conditions

## Architecture

### Ensemble Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     INPUT FEATURES (X)                      │
└────────────┬────────────────────┬─────────────────┬─────────┘
             │                    │                 │
             ▼                    ▼                 ▼
      ┌──────────┐         ┌──────────┐      ┌──────────┐
      │   LSTM   │         │ LightGBM │      │ XGBoost  │
      │ (Neural) │         │  (Tree)  │      │  (Tree)  │
      └─────┬────┘         └────┬─────┘      └────┬─────┘
            │                   │                  │
            ▼                   ▼                  ▼
       [pred_1]            [pred_2]           [pred_3]
            │                   │                  │
            └───────────┬───────┴──────────────────┘
                        ▼
              ┌──────────────────┐
              │ ENSEMBLE METHOD  │
              │  - Stacking      │
              │  - Blending      │
              │  - Voting        │
              └─────────┬────────┘
                        ▼
                [Final Prediction]
```

### Ensemble Methods

| Method | Description | Best For | Training Required |
|--------|-------------|----------|-------------------|
| **Stacking** | Meta-model learns to combine predictions | Maximum accuracy | Yes (meta-model) |
| **Blending** | Weighted average with optimized weights | Balance accuracy/speed | Yes (weight optimization) |
| **Voting** | Simple average (equal weights) | Quick baseline | No |

## Implementation

### Core Components

#### 1. EnsemblePredictor

Main class for ensemble predictions.

```python
from proratio_quantlab.ml.ensemble_predictor import EnsemblePredictor

# Create stacking ensemble
ensemble = EnsemblePredictor(
    ensemble_method='stacking',  # 'stacking', 'blending', or 'voting'
    meta_model_type='ridge'      # 'ridge', 'lasso', 'rf' (for stacking)
)

# Add base models
ensemble.add_base_model('lstm', trained_lstm_model, weight=1.0)
ensemble.add_base_model('lgbm', trained_lgbm_model, weight=1.0)
ensemble.add_base_model('xgb', trained_xgb_model, weight=1.0)

# Train ensemble
ensemble.train_stacking(X_train, y_train, X_val, y_val)

# Make predictions
predictions = ensemble.predict(X_test)
```

#### 2. EnsembleBuilder

Simplified interface for building ensembles from scratch.

```python
from proratio_quantlab.ml.ensemble_predictor import EnsembleBuilder

# Create builder
builder = EnsembleBuilder(ensemble_method='stacking')

# Add base models
builder.add_lightgbm(name='lgbm', params={'num_leaves': 31})
builder.add_xgboost(name='xgb', params={'max_depth': 6})
builder.add_lstm(name='lstm', sequence_length=24, hidden_size=128)

# Train all models
builder.train_all(X_train, y_train, X_val, y_val)

# Build ensemble
ensemble = builder.build_ensemble(X_val, y_val, meta_model_type='ridge')
```

## Usage Examples

### Example 1: Stacking Ensemble

```python
from proratio_quantlab.ml.ensemble_predictor import EnsembleBuilder

# Create stacking ensemble
builder = EnsembleBuilder(ensemble_method='stacking')

# Add models
builder.add_lightgbm(name='lgbm')
builder.add_xgboost(name='xgb')
builder.add_lstm(name='lstm')

# Train base models
builder.train_all(X_train, y_train, X_val, y_val)

# Build ensemble with Ridge meta-model
ensemble = builder.build_ensemble(X_val, y_val, meta_model_type='ridge')

# Evaluate
results = ensemble.evaluate(X_test, y_test)
print(f"Ensemble RMSE: {results['ensemble']['rmse']:.6f}")
print(f"LSTM RMSE: {results['lstm']['rmse']:.6f}")
print(f"LightGBM RMSE: {results['lgbm']['rmse']:.6f}")
```

### Example 2: Blending with Optimized Weights

```python
# Create blending ensemble
builder = EnsembleBuilder(ensemble_method='blending')

# Add models
builder.add_lightgbm(name='lgbm')
builder.add_xgboost(name='xgb')

# Train models
builder.train_all(X_train, y_train, X_val, y_val)

# Build ensemble (optimizes weights automatically)
ensemble = builder.build_ensemble(X_val, y_val)

# Check optimized weights
print("Optimized Weights:")
for name, weight in ensemble.weights.items():
    print(f"  {name}: {weight:.4f}")
```

### Example 3: Dynamic Weight Adjustment

```python
# Create blending ensemble
ensemble = EnsemblePredictor(ensemble_method='blending')

# Add models with initial weights
ensemble.add_base_model('lstm', lstm_model, weight=0.33)
ensemble.add_base_model('lgbm', lgbm_model, weight=0.33)
ensemble.add_base_model('xgb', xgb_model, weight=0.34)

# Update weights based on recent performance
ensemble.update_weights_dynamic(
    X_recent=X_val,
    y_recent=y_val,
    window_size=100  # Use last 100 samples
)

# New weights based on recent performance
print("Updated Weights:", ensemble.weights)
```

### Example 4: Model Contributions Analysis

```python
# Get individual model contributions
contributions = ensemble.get_model_contributions(X_test)

print(contributions.head())
# Output:
#    lstm_pred  lgbm_pred  xgb_pred  ensemble_pred  lstm_weight  lgbm_weight  xgb_weight
# 0   0.0123     0.0145    0.0132      0.0134         0.35         0.40        0.25
# 1  -0.0089    -0.0102   -0.0095     -0.0096         0.35         0.40        0.25
```

## Training Script

### Using the Training Script

```bash
# Train stacking ensemble with all models
python scripts/train_ensemble_model.py \
    --pair BTC/USDT \
    --ensemble-method stacking \
    --meta-model ridge \
    --save models/ensemble_btc_stacking.pkl

# Train blending ensemble without LSTM
python scripts/train_ensemble_model.py \
    --pair ETH/USDT \
    --ensemble-method blending \
    --no-lstm \
    --save models/ensemble_eth_blending.pkl

# Train voting ensemble (quick baseline)
python scripts/train_ensemble_model.py \
    --pair BTC/USDT \
    --ensemble-method voting \
    --save models/ensemble_btc_voting.pkl
```

### Script Parameters

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `--pair` | Trading pair | BTC/USDT | Any pair |
| `--timeframe` | Timeframe | 4h | 1h, 4h, 1d |
| `--limit` | Number of candles | 10000 | Any int |
| `--ensemble-method` | Ensemble strategy | stacking | stacking, blending, voting |
| `--meta-model` | Meta-model type | ridge | ridge, lasso, rf |
| `--no-lstm` | Exclude LSTM | False | Flag |
| `--no-lgbm` | Exclude LightGBM | False | Flag |
| `--no-xgb` | Exclude XGBoost | False | Flag |
| `--sequence-length` | LSTM sequence length | 24 | Any int |
| `--save` | Save path | None | Path to .pkl |

## Performance Considerations

### Computational Complexity

| Method | Training Time | Prediction Time | Memory Usage |
|--------|---------------|-----------------|--------------|
| **Stacking** | High (base + meta) | Low | Medium |
| **Blending** | Medium (base + weight opt) | Low | Medium |
| **Voting** | Low (base only) | Low | Low |

### Training Time Estimates (10,000 samples)

- **Base Models Training**:
  - LightGBM: ~30 seconds
  - XGBoost: ~45 seconds
  - LSTM (CPU): ~10 minutes
  - LSTM (GPU): ~2 minutes

- **Ensemble Training**:
  - Stacking: +30 seconds (meta-model)
  - Blending: +2 minutes (grid search)
  - Voting: 0 seconds (no training)

- **Total (All 3 models)**:
  - Stacking (CPU): ~13 minutes
  - Stacking (GPU): ~5 minutes
  - Blending (CPU): ~14 minutes
  - Voting (CPU): ~11 minutes

### Memory Requirements

- Base Models: ~500 MB (LSTM) + ~50 MB (LightGBM) + ~50 MB (XGBoost) = 600 MB
- Ensemble Metadata: ~10 MB
- Training Data: ~100 MB (10k samples × 100 features)
- **Total**: ~700 MB

## Model Comparison

### LSTM vs LightGBM vs XGBoost vs Ensemble

| Metric | LSTM | LightGBM | XGBoost | Ensemble (Stacking) |
|--------|------|----------|---------|---------------------|
| **Strengths** | Long-term patterns | Fast, interpretable | Robust to outliers | Best of all worlds |
| **Weaknesses** | Slow training | Limited sequences | High memory | Complex training |
| **Training Time** | High | Low | Medium | High |
| **Prediction Speed** | Medium | Fast | Fast | Medium |
| **Accuracy** | High | High | High | **Highest** |
| **Overfitting Risk** | Medium | Low | Low | **Lowest** |

### When to Use Each

- **LSTM Only**: Deep sequential patterns, sufficient training data (>10k samples)
- **LightGBM Only**: Fast iteration, interpretability needed, limited data
- **XGBoost Only**: Robust predictions, handle outliers well
- **Ensemble**: Maximum accuracy, production deployment, sufficient compute

## Evaluation Metrics

### Comprehensive Evaluation

```python
# Evaluate all models
results = ensemble.evaluate(X_test, y_test)

# Print results
for model_name, metrics in results.items():
    print(f"\n{model_name.upper()}")
    print(f"  RMSE: {metrics['rmse']:.6f}")
    print(f"  MAE:  {metrics['mae']:.6f}")
    print(f"  MSE:  {metrics['mse']:.6f}")

# Calculate improvement
ensemble_rmse = results['ensemble']['rmse']
best_base_rmse = min(
    results['lstm']['rmse'],
    results['lgbm']['rmse'],
    results['xgb']['rmse']
)
improvement = ((best_base_rmse - ensemble_rmse) / best_base_rmse) * 100
print(f"\nEnsemble Improvement: {improvement:.2f}%")
```

### Expected Performance Gains

Based on typical cryptocurrency prediction tasks:

- **Stacking Ensemble**: 5-15% improvement over best base model
- **Blending Ensemble**: 3-10% improvement over best base model
- **Voting Ensemble**: 2-5% improvement over best base model

## Persistence

### Save/Load Ensemble

```python
# Save ensemble
ensemble.save('models/my_ensemble.pkl')

# Load ensemble
from proratio_quantlab.ml.ensemble_predictor import EnsemblePredictor

ensemble = EnsemblePredictor(ensemble_method='stacking')
ensemble.load('models/my_ensemble.pkl')

# Note: Base models must be loaded separately
ensemble.base_models['lstm'] = load_lstm_model('models/lstm.pkl')
ensemble.base_models['lgbm'] = load_lgbm_model('models/lgbm.pkl')
```

### Best Practices

1. **Save ensemble config and base models separately**:
   ```python
   ensemble.save('models/ensemble_config.pkl')
   lstm_model.save('models/lstm.pkl')
   joblib.dump(lgbm_model, 'models/lgbm.pkl')
   ```

2. **Version control**:
   ```python
   ensemble.save(f'models/ensemble_v{version}_{date}.pkl')
   ```

3. **Include metadata**:
   ```python
   metadata = {
       'version': '1.0',
       'date': '2025-10-11',
       'pair': 'BTC/USDT',
       'performance': results
   }
   joblib.dump(metadata, 'models/ensemble_metadata.pkl')
   ```

## Integration with Freqtrade

### Strategy Integration

```python
from freqtrade.strategy import IStrategy
from proratio_quantlab.ml.ensemble_predictor import EnsemblePredictor

class EnsembleStrategy(IStrategy):
    def __init__(self, config: dict):
        super().__init__(config)

        # Load ensemble
        self.ensemble = EnsemblePredictor(ensemble_method='stacking')
        self.ensemble.load('models/ensemble_btc.pkl')

        # Load base models
        self.ensemble.base_models['lstm'] = self.load_lstm()
        self.ensemble.base_models['lgbm'] = self.load_lgbm()
        self.ensemble.base_models['xgb'] = self.load_xgb()

    def populate_entry_trend(self, dataframe, metadata):
        # Prepare features
        fe = FeatureEngineer()
        df_features = fe.add_all_features(dataframe)

        # Get ensemble prediction
        X = df_features[self.ensemble.model_names].values
        predictions = self.ensemble.predict(X)

        # Entry signal: positive prediction
        dataframe.loc[predictions > 0.005, 'enter_long'] = 1

        return dataframe
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```python
# Error: No module named 'torch'
# Solution: Install PyTorch for LSTM support
pip install torch

# Error: No module named 'lightgbm'
# Solution: Install LightGBM
pip install lightgbm

# Error: No module named 'xgboost'
# Solution: Install XGBoost
pip install xgboost
```

#### 2. Training Failures

```python
# Error: Insufficient data
# Solution: Reduce min_samples or increase data
pipeline = LSTMDataPipeline(min_samples=500)  # Lower threshold

# Error: CUDA out of memory
# Solution: Use CPU or reduce batch size
predictor = LSTMPredictor(device='cpu')
```

#### 3. Performance Issues

```python
# Slow training
# Solution: Exclude LSTM or use GPU
python scripts/train_ensemble_model.py --no-lstm  # Faster

# Poor accuracy
# Solution: Try different ensemble methods
python scripts/train_ensemble_model.py --ensemble-method stacking --meta-model rf
```

## Advanced Topics

### Custom Meta-Models

```python
from sklearn.neural_network import MLPRegressor

# Create custom meta-model
custom_meta = MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=1000)

# Use in ensemble
ensemble = EnsemblePredictor(ensemble_method='stacking')
ensemble.meta_model = custom_meta
```

### Walk-Forward Validation

```python
from proratio_quantlab.ml.lstm_data_pipeline import LSTMDataPipeline

pipeline = LSTMDataPipeline()
splits = pipeline.create_walk_forward_splits(df, n_splits=5)

results = []
for i, (train_idx, test_idx) in enumerate(splits):
    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    # Train ensemble
    builder = EnsembleBuilder(ensemble_method='stacking')
    builder.add_lightgbm()
    builder.add_xgboost()
    builder.train_all(X_train, y_train, X_val, y_val)
    ensemble = builder.build_ensemble(X_val, y_val)

    # Evaluate
    fold_results = ensemble.evaluate(X_test, y_test)
    results.append(fold_results)

# Average performance across folds
avg_rmse = np.mean([r['ensemble']['rmse'] for r in results])
```

### Confidence-Based Model Selection

```python
def predict_with_confidence(ensemble, X, confidence_threshold=0.8):
    """Use best single model if ensemble confidence is low."""

    # Get individual predictions
    contributions = ensemble.get_model_contributions(X)

    # Calculate prediction variance (low variance = high confidence)
    pred_cols = [c for c in contributions.columns if c.endswith('_pred') and c != 'ensemble_pred']
    variance = contributions[pred_cols].var(axis=1)

    # High variance = low confidence, use best single model
    low_confidence = variance > variance.quantile(1 - confidence_threshold)

    # Get best base model
    best_model = min(ensemble.base_models.items(),
                     key=lambda x: ensemble.evaluate(X, y)[x[0]]['rmse'])

    # Use ensemble for high confidence, best model for low confidence
    predictions = ensemble.predict(X)
    predictions[low_confidence] = best_model[1].predict(X[low_confidence])

    return predictions
```

## Next Steps

### Phase 3.4: Reinforcement Learning (Optional)

- Implement Q-learning for dynamic position sizing
- Create reward functions for risk-adjusted returns
- Train RL agents for market regime detection

### Phase 1.4: Paper Trading Validation

- Deploy ensemble strategies in paper trading
- Real-time performance monitoring
- A/B testing ensemble vs single models

### Phase 4: Production Optimization

- Model compression and quantization
- ONNX export for faster inference
- Distributed training for large datasets

## References

- **Stacking**: Wolpert, D. H. (1992). "Stacked generalization"
- **Blending**: Caruana et al. (2004). "Ensemble selection from libraries of models"
- **Dynamic Weighting**: Breiman, L. (1996). "Bagging predictors"
- **Freqtrade Documentation**: https://www.freqtrade.io/en/stable/strategy-advanced/

---

**Last Updated:** October 11, 2025
**Phase Status:** ✅ Complete
**Next Phase:** 3.4 (Reinforcement Learning) or 1.4 (Paper Trading)
