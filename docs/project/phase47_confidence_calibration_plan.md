# Phase 4.7: Confidence Calibration - Implementation Plan

**Date**: October 16, 2025
**Status**: PLANNED
**Goal**: Analyze and calibrate ML/LLM confidence scores for optimal trading decisions

---

## 📋 Problem Statement

### Observed Confidence Ranges (Phase 4.6)

**ML Ensemble**:
- Range: 23.3% - 35.3%
- Average: 29.3%
- Direction: Consistent UP (bullish)
- Issue: Below 60% trading threshold

**LLM Consensus**:
- Confidence: 59.2%
- Direction: SHORT (bearish)
- Issue: Just below 60% threshold

**Result**: CONFLICT → No trades (correct behavior)

### Key Questions

1. **Is 23-35% ML confidence normal?**
   - Need baseline from training data
   - Compare with validation set performance
   - Check if model needs recalibration

2. **Why is LLM at 59.2%?**
   - Just under threshold (60%)
   - Is this genuinely uncertain market?
   - Or is threshold too high?

3. **Are current thresholds optimal?**
   - ML: 60% minimum
   - LLM: 60% minimum
   - Agreement: 70% minimum
   - Should these be adjusted?

---

## 🎯 Phase 4.7 Goals

### 1. Baseline Analysis
- Analyze ML confidence distribution on historical data
- Understand typical confidence ranges
- Identify if 23-35% is normal or anomalous

### 2. Probability Calibration
- Implement calibration methods (Platt scaling, isotonic regression)
- Transform raw model outputs to calibrated probabilities
- Ensure confidence scores reflect true probabilities

### 3. Threshold Optimization
- Find optimal thresholds for ML, LLM, and agreement
- Balance trade frequency vs quality
- Maximize risk-adjusted returns

### 4. Validation
- Test calibrated system with paper trading
- Compare calibrated vs uncalibrated performance
- Verify improved decision quality

---

## 📊 Implementation Steps

### Step 1: ML Confidence Baseline Analysis

**Script**: `scripts/analyze_model_confidence.py`

**Analysis**:
```python
# Load ensemble model
# Generate predictions on last 180 days of data
# Analyze confidence distribution:
#   - Mean, median, std dev
#   - Percentiles (25th, 50th, 75th, 90th, 95th)
#   - Confidence buckets (0-55%, 55-60%, 60-65%, etc.)
#   - Accuracy by confidence bucket

# Compare Phase 4.6 observations (23-35%) with baseline
# Determine if low confidence is:
#   a) Normal for uncertain markets
#   b) Indication of model degradation
#   c) Calibration issue
```

**Expected Findings**:
- If historical mean < 60%: Model needs calibration
- If historical mean ≈ 23-35%: This is normal, thresholds too high
- If historical mean > 60%: Model degraded, needs retraining

---

### Step 2: Probability Calibration

**Methods to Implement**:

#### A. Platt Scaling (Logistic Calibration)
```python
from sklearn.calibration import CalibratedClassifierCV

# Calibrate ensemble on validation set
calibrated_model = CalibratedClassifierCV(
    ensemble_model,
    method='sigmoid',  # Platt scaling
    cv='prefit'
)
calibrated_model.fit(X_val, y_val)

# New predictions will be calibrated probabilities
calibrated_probs = calibrated_model.predict_proba(X_test)
```

**Pros**: Fast, works well for neural networks and tree ensembles
**Cons**: Assumes sigmoid-shaped miscalibration

#### B. Isotonic Regression (Non-parametric)
```python
calibrated_model = CalibratedClassifierCV(
    ensemble_model,
    method='isotonic',  # Isotonic regression
    cv='prefit'
)
calibrated_model.fit(X_val, y_val)
```

**Pros**: No assumptions about calibration shape, more flexible
**Cons**: Can overfit on small datasets

#### C. Beta Calibration (For Imbalanced Data)
```python
from betacal import BetaCalibration

# Fit beta calibration
bc = BetaCalibration(parameters="abm")
bc.fit(raw_predictions, y_val)

# Apply calibration
calibrated_probs = bc.predict(raw_predictions)
```

**Pros**: Best for imbalanced classes (crypto often has directional bias)
**Cons**: Requires additional library

**Recommendation**: Start with Platt scaling, compare with isotonic

---

### Step 3: LLM Confidence Analysis

**Current Behavior**:
- LLMs return structured responses with confidence %
- Aggregated via weighted voting (40% ChatGPT, 35% Claude, 25% Gemini)
- Phase 4.6: 59.2% consensus SHORT

**Analysis Needed**:
1. **Historical LLM confidence distribution**
   - Collect LLM predictions over time
   - Analyze typical confidence ranges
   - Check if 59% is high, medium, or low

2. **LLM calibration**
   - LLMs are NOT inherently calibrated
   - They express confidence linguistically, not probabilistically
   - May need to map linguistic confidence to probabilities

3. **Correlation with outcomes**
   - Do high LLM confidence predictions perform better?
   - What's the optimal confidence threshold?

**Potential Calibration**:
```python
# Map LLM confidence ranges to calibrated probabilities
def calibrate_llm_confidence(raw_confidence):
    """
    Calibrate LLM confidence based on historical performance

    Example mapping:
    - 50-60%: Actually ~45% accurate → Low confidence
    - 60-70%: Actually ~55% accurate → Medium confidence
    - 70-80%: Actually ~65% accurate → High confidence
    - 80-90%: Actually ~75% accurate → Very high
    - 90-100%: Actually ~85% accurate → Extreme confidence
    """
    calibration_map = {
        60: 0.45,
        70: 0.55,
        80: 0.65,
        90: 0.75,
        100: 0.85
    }
    # Interpolate between map points
    return interpolate(raw_confidence, calibration_map)
```

---

### Step 4: Threshold Optimization

**Current Thresholds**:
- ML minimum: 60%
- LLM minimum: 60%
- Agreement minimum: 70%
- Signal strength: STRONG or VERY_STRONG required

**Optimization Approach**:

#### A. Grid Search
```python
ml_thresholds = [50, 55, 60, 65, 70]
llm_thresholds = [50, 55, 60, 65, 70]
agreement_thresholds = [60, 65, 70, 75, 80]

best_sharpe = -np.inf
best_params = None

for ml_t in ml_thresholds:
    for llm_t in llm_thresholds:
        for agree_t in agreement_thresholds:
            # Backtest with these thresholds
            results = backtest_with_thresholds(ml_t, llm_t, agree_t)

            if results.sharpe_ratio > best_sharpe:
                best_sharpe = results.sharpe_ratio
                best_params = (ml_t, llm_t, agree_t)

print(f"Optimal thresholds: ML={best_params[0]}%, LLM={best_params[1]}%, Agreement={best_params[2]}%")
```

#### B. ROC Curve Analysis
```python
from sklearn.metrics import roc_curve, roc_auc_score

# For ML predictions
fpr, tpr, thresholds = roc_curve(y_true, ml_predictions)

# Find optimal threshold (maximize Youden's J statistic)
optimal_idx = np.argmax(tpr - fpr)
optimal_ml_threshold = thresholds[optimal_idx]

print(f"Optimal ML threshold: {optimal_ml_threshold:.2%}")
```

#### C. Precision-Recall Trade-off
```python
from sklearn.metrics import precision_recall_curve

precision, recall, thresholds = precision_recall_curve(y_true, ml_predictions)

# Find threshold for desired precision (e.g., 60% minimum)
target_precision = 0.60
idx = np.where(precision >= target_precision)[0]
if len(idx) > 0:
    optimal_threshold = thresholds[idx[0]]
    corresponding_recall = recall[idx[0]]

    print(f"For {target_precision:.0%} precision:")
    print(f"  Threshold: {optimal_threshold:.2%}")
    print(f"  Recall: {corresponding_recall:.2%}")
```

---

### Step 5: Implementation in HybridMLLLMPredictor

**File**: `proratio_signals/hybrid_predictor.py`

**Changes Needed**:

```python
class HybridMLLLMPredictor:
    def __init__(self, ...):
        # ...existing code...

        # NEW: Calibration settings
        self.ml_calibrator = None  # Will be loaded from calibrated model
        self.llm_calibrator = None  # LLM confidence calibration function

        # NEW: Optimized thresholds (from Phase 4.7 analysis)
        self.ml_min_confidence = 0.55  # Adjusted from 0.60
        self.llm_min_confidence = 0.55  # Adjusted from 0.60
        self.min_agreement_score = 0.65  # Adjusted from 0.70

    def _get_ml_prediction(self, ...):
        # Get raw prediction
        raw_prediction = self.ensemble_predictor.predict(ohlcv_data, pair, timeframe)

        # NEW: Apply calibration if available
        if self.ml_calibrator:
            calibrated_confidence = self.ml_calibrator.predict_proba(
                raw_prediction.confidence
            )[0][1]
            raw_prediction.confidence = calibrated_confidence

        return raw_prediction

    def _get_llm_consensus(self, ...):
        # Get raw LLM consensus
        llm_signal = self.llm_orchestrator.generate_signal(...)

        # NEW: Apply LLM calibration
        if self.llm_calibrator:
            calibrated_confidence = self.llm_calibrator(llm_signal.confidence)
            llm_signal.confidence = calibrated_confidence

        return llm_signal
```

---

## 📈 Success Criteria

### Calibration Quality

**ML Model**:
- [ ] Calibration curve close to diagonal (perfect calibration)
- [ ] Brier score < 0.20 (well-calibrated)
- [ ] Expected Calibration Error (ECE) < 0.10

**LLM Consensus**:
- [ ] Confidence correlated with actual accuracy
- [ ] High confidence (>75%) → >65% win rate
- [ ] Low confidence (<60%) → <55% win rate

### Trading Performance

**Backtest Metrics** (After calibration):
- [ ] Sharpe ratio > 1.5
- [ ] Win rate > 55%
- [ ] Max drawdown < 15%
- [ ] Profit factor > 1.3
- [ ] Trade frequency: 2-5 trades per week

### Comparison

| Metric | Uncalibrated | Calibrated | Improvement |
|--------|--------------|------------|-------------|
| Sharpe Ratio | TBD | Target: >1.5 | +20-30% |
| Win Rate | TBD | Target: >55% | +5-10% |
| Trade Frequency | 0-1/week | 2-5/week | More opportunities |
| False Signals | High | Low | -30-50% |

---

## 🚧 Implementation Timeline

### Phase 4.7.1: Analysis (Day 1)
- [x] Create confidence analysis script
- [ ] Run ML baseline analysis
- [ ] Analyze LLM historical confidence
- [ ] Document findings

### Phase 4.7.2: Calibration (Day 2)
- [ ] Implement Platt scaling for ML
- [ ] Implement isotonic regression for ML
- [ ] Compare calibration methods
- [ ] Create LLM confidence calibration function
- [ ] Test calibrated predictions

### Phase 4.7.3: Threshold Optimization (Day 3)
- [ ] Grid search for optimal thresholds
- [ ] ROC curve analysis
- [ ] Precision-recall analysis
- [ ] Backtest with optimized thresholds
- [ ] Compare with baseline

### Phase 4.7.4: Integration & Testing (Day 4)
- [ ] Update HybridMLLLMPredictor with calibration
- [ ] Update configuration with new thresholds
- [ ] Run 24-48 hour paper trading test
- [ ] Compare calibrated vs uncalibrated performance
- [ ] Document results

### Phase 4.7.5: Documentation (Day 5)
- [ ] Create Phase 4.7 completion report
- [ ] Update roadmap
- [ ] Update strategy documentation
- [ ] Prepare for Phase 5

---

## 📊 Expected Outcomes

### Understanding

✅ **ML Confidence**:
- Know if 23-35% is normal or anomalous
- Understand model's confidence distribution
- Identify if retraining is needed

✅ **LLM Confidence**:
- Baseline for typical LLM confidence ranges
- Calibration mapping for LLM predictions
- Optimal LLM confidence threshold

✅ **System Behavior**:
- Optimal thresholds for all confidence scores
- Expected trade frequency
- Risk/reward profile

### Improvements

✅ **Better Calibration**:
- Confidence scores reflect true probabilities
- More reliable trading decisions
- Reduced false signals

✅ **Optimized Thresholds**:
- Balanced trade frequency vs quality
- Improved risk-adjusted returns
- Clear entry criteria

✅ **Production Readiness**:
- Calibrated system ready for live trading
- Confidence in model predictions
- Well-documented performance expectations

---

## 🔍 Reference Materials

### Calibration Resources
- [Scikit-learn Calibration](https://scikit-learn.org/stable/modules/calibration.html)
- [Platt Scaling Paper](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.41.1639)
- [Beta Calibration for Imbalanced Data](https://github.com/betacal/python)

### Threshold Optimization
- [ROC Curve Analysis](https://scikit-learn.org/stable/auto_examples/model_selection/plot_roc.html)
- [Precision-Recall Curves](https://scikit-learn.org/stable/auto_examples/model_selection/plot_precision_recall.html)

### Trading-Specific Metrics
- [Sharpe Ratio](https://en.wikipedia.org/wiki/Sharpe_ratio)
- [Profit Factor](https://www.investopedia.com/terms/p/profit_factor.asp)

---

**Next Phase**: Phase 5 - Weekly Trading Plans (AI-generated market analysis and scenarios)

**Status**: Ready to begin Phase 4.7.1 (Analysis)
