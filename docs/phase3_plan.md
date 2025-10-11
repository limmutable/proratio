# Phase 3: Machine Learning Integration - Implementation Plan

**Status**: ✅ Phase 3.1 Complete → 🚧 Phase 3.2 In Progress
**Start Date**: 2025-10-11
**Phase 3.1 Completed**: 2025-10-11
**Target Completion**: Phase 3.2-3.4

---

## 📋 Overview

Phase 3 integrates machine learning capabilities into Proratio to create adaptive, intelligent trading strategies that learn from market data and improve over time.

### Goals
1. Implement FreqAI integration for adaptive ML strategies
2. Create LSTM models for price prediction
3. Build ensemble learning system combining multiple models
4. (Optional) Experiment with reinforcement learning

---

## 🎯 Phase 3 Breakdown

### Phase 3.1: FreqAI Integration & Setup ✅ **COMPLETE**

**Goal**: Set up FreqAI infrastructure and create first ML-enhanced strategy

**Tasks**:
- [x] Research FreqAI architecture and requirements
- [x] Install FreqAI dependencies (LightGBM, XGBoost, CatBoost, Optuna, SHAP)
- [x] Create FreqAI configuration file
- [x] Implement feature engineering module (80+ features)
- [x] Create FreqAI-enabled strategy adapter
- [x] Install and test ML dependencies
- [x] Document setup and usage (600+ line guide)

**Key Deliverables** ✅:
- `proratio_quantlab/ml/feature_engineering.py` - Feature engineering (450+ lines, 80+ features)
- `user_data/strategies/FreqAIStrategy.py` - ML-enabled strategy (400+ lines)
- `proratio_utilities/config/freqtrade/config_freqai.json` - FreqAI configuration
- `docs/freqai_guide.md` - Comprehensive ML guide (600+ lines)
- `docs/phase3_plan.md` - This implementation plan (450+ lines)
- ML dependencies installed: LightGBM 4.5.0, XGBoost 2.1.3, CatBoost 1.2.7, Optuna 4.1.0, SHAP 0.47.0

**Success Criteria** ✅:
- ✅ FreqAI configuration created with LightGBM/XGBoost/CatBoost support
- ✅ Feature engineering module with 80+ features across 7 categories
- ✅ FreqAIStrategy with ML predictions + technical confirmation
- ✅ Comprehensive documentation and setup guide
- 🚧 Pending: Run full backtest (requires complete Freqtrade setup)

---

### Phase 3.2: LSTM Price Prediction

**Goal**: Implement deep learning LSTM models for time-series forecasting

**Tasks**:
- [ ] Design LSTM architecture for crypto price prediction
- [ ] Create data preprocessing pipeline for LSTM
- [ ] Implement LSTM model training module
- [ ] Create price prediction interface
- [ ] Integrate LSTM predictions with strategies
- [ ] Backtest LSTM-enhanced strategies
- [ ] Optimize hyperparameters
- [ ] Document LSTM implementation

**Key Deliverables**:
- `proratio_quantlab/ml/lstm_model.py` - LSTM implementation
- `proratio_quantlab/ml/data_preprocessor.py` - Data preparation
- `user_data/strategies/LSTMStrategy.py` - LSTM-enhanced strategy
- Trained model checkpoints
- Documentation in `docs/lstm_guide.md`

**Success Criteria**:
- LSTM predicts price direction with >55% accuracy
- Model trains without overfitting
- Integration with portfolio manager works seamlessly

---

### Phase 3.3: Ensemble Learning System

**Goal**: Combine multiple ML models for robust predictions

**Tasks**:
- [ ] Design ensemble architecture (voting, stacking, blending)
- [ ] Implement model aggregation logic
- [ ] Create ensemble training pipeline
- [ ] Add model weight optimization
- [ ] Integrate ensemble with portfolio manager
- [ ] Run comprehensive backtests
- [ ] Compare ensemble vs individual models
- [ ] Document ensemble system

**Key Deliverables**:
- `proratio_quantlab/ml/ensemble.py` - Ensemble implementation
- `proratio_quantlab/ml/model_registry.py` - Model management
- `user_data/strategies/EnsembleStrategy.py` - Ensemble strategy
- Performance comparison report
- Documentation in `docs/ensemble_guide.md`

**Success Criteria**:
- Ensemble outperforms individual models by 10%+
- Robust across different market conditions
- Automated model retraining works correctly

---

### Phase 3.4: Reinforcement Learning (Optional)

**Goal**: Explore RL for adaptive strategy optimization

**Tasks**:
- [ ] Set up RL environment (gym-compatible)
- [ ] Implement DQN/PPO agent
- [ ] Define reward function
- [ ] Train RL agent
- [ ] Evaluate vs supervised learning
- [ ] Document findings

**Key Deliverables**:
- `proratio_quantlab/ml/rl_agent.py`
- `proratio_quantlab/ml/trading_env.py`
- Experimental results report

---

## 🛠️ Technical Stack

### ML Libraries
- **FreqAI**: Freqtrade's ML framework
- **PyTorch**: Deep learning (LSTM, NN)
- **scikit-learn**: Traditional ML (Random Forest, XGBoost)
- **LightGBM**: Gradient boosting
- **XGBoost**: Gradient boosting (alternative)

### Feature Engineering
- Technical indicators (RSI, MACD, Bollinger Bands, ATR)
- Price patterns (candlestick patterns, chart patterns)
- Volume profiles
- Market regime indicators
- Volatility measures
- Order book features (if available)

### Model Types
1. **Regression**: Predict price/returns
2. **Classification**: Predict direction (up/down/neutral)
3. **Ranking**: Predict relative performance

---

## 📊 Feature Engineering Strategy

### Base Features (Technical Indicators)
```python
features = [
    'rsi_14', 'rsi_21',
    'macd', 'macd_signal', 'macd_diff',
    'bb_upper', 'bb_middle', 'bb_lower', 'bb_width',
    'atr_14',
    'ema_9', 'ema_21', 'ema_50', 'ema_200',
    'volume_sma_20',
    'obv',  # On-balance volume
]
```

### Derived Features
```python
derived_features = [
    'price_change_1h', 'price_change_4h', 'price_change_24h',
    'volume_change_1h', 'volume_change_4h',
    'volatility_1d', 'volatility_7d',
    'trend_strength',  # ADX-based
    'momentum',        # ROC-based
]
```

### Market Regime Features
```python
regime_features = [
    'is_trending_up', 'is_trending_down',
    'is_ranging', 'is_volatile',
    'regime_confidence',
]
```

### Target Labels
```python
# Regression targets
targets_regression = [
    'price_next_1h',   # Price after 1 hour
    'price_next_4h',   # Price after 4 hours
    'return_next_1h',  # Return % after 1 hour
]

# Classification targets
targets_classification = [
    'direction_1h',  # 0=down, 1=neutral, 2=up
    'profitable_entry',  # Will this entry be profitable?
]
```

---

## 🧪 Testing Strategy

### Model Validation
1. **Train/Test Split**: 70/30 with time-based split (no shuffle)
2. **Walk-Forward Validation**: Train on N months, test on next M months
3. **Cross-Validation**: Time-series cross-validation
4. **Out-of-Sample Testing**: Test on recent unseen data

### Performance Metrics
- **Regression**: MSE, RMSE, MAE, R²
- **Classification**: Accuracy, Precision, Recall, F1, ROC-AUC
- **Trading**: Sharpe ratio, Max drawdown, Win rate, Profit factor

### Backtesting
```bash
# FreqAI backtest
freqtrade backtesting \
  --strategy FreqAIStrategy \
  --freqaimodel LightGBMRegressor \
  --timerange 20240101-20251011 \
  --config config_freqai.json

# Compare ML vs baseline
python scripts/compare_ml_baseline.py
```

---

## 📈 Expected Improvements

### Target Metrics
- **Win Rate**: 61.6% (baseline) → 65%+ (ML)
- **Sharpe Ratio**: 1.0 (baseline) → 1.3+ (ML)
- **Max Drawdown**: <10% (maintain)
- **Profit Factor**: 1.2 → 1.5+

### Model Performance Goals
- **Price Direction Accuracy**: >55%
- **Prediction Confidence Calibration**: Well-calibrated probabilities
- **Model Robustness**: Consistent across different pairs and timeframes

---

## 🚧 Current Progress

### Phase 3.1 Status
- [x] FreqAI research complete
- [ ] FreqAI setup in progress
- [ ] Feature engineering module (next)
- [ ] First ML strategy (next)

---

## 📝 Documentation

### Guides to Create
1. `docs/freqai_guide.md` - FreqAI setup and usage
2. `docs/ml_strategy_guide.md` - Creating ML strategies
3. `docs/feature_engineering_guide.md` - Feature creation patterns
4. `docs/model_training_guide.md` - Training and validation
5. `docs/phase3_summary.md` - Phase 3 completion summary

---

## ⚠️ Risks & Mitigation

### Risk 1: Overfitting
**Mitigation**:
- Use walk-forward validation
- Implement regularization (dropout, L2)
- Monitor train vs test performance

### Risk 2: Look-ahead Bias
**Mitigation**:
- Strict time-series splitting
- Feature engineering review
- Validate with paper trading

### Risk 3: Data Snooping
**Mitigation**:
- Reserve out-of-sample test set
- Document all experiments
- Single final model evaluation

### Risk 4: Model Degradation
**Mitigation**:
- Automated model retraining (FreqAI)
- Performance monitoring
- Model expiration (24-48 hours)

---

## 🔄 Next Steps

1. ✅ Research FreqAI (Complete)
2. 🚧 Set up FreqAI dependencies (Current)
3. Create feature engineering module
4. Implement first FreqAI strategy
5. Run baseline backtests
6. Iterate and optimize

---

**Last Updated**: 2025-10-11
**Phase**: 3.1 - FreqAI Integration (In Progress)
