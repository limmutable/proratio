"""
Analyze ML Model Confidence Distribution

Analyzes the ensemble model's confidence scores on historical data
to understand if 23-35% confidence is normal or indicates a problem.

Phase 4.7: Confidence Calibration

Usage:
    python scripts/analyze_model_confidence.py --pair BTC/USDT --timeframe 4h

Author: Proratio Team
Date: 2025-10-16
"""

import argparse
import joblib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from proratio_quantlab.ml.feature_engineering import FeatureEngineer
from proratio_quantlab.ml.ensemble_predictor import EnsemblePredictor


def load_ensemble_model(model_path: str):
    """Load the trained ensemble model"""
    ensemble = EnsemblePredictor()
    ensemble.load(model_path)
    return ensemble


def analyze_confidence_distribution(predictions: np.ndarray, actuals: np.ndarray = None):
    """Analyze the distribution of prediction confidences"""

    # Predictions are already confidence scores (0-1), just convert to percentage
    confidences = predictions * 100

    print("\n" + "="*60)
    print("CONFIDENCE DISTRIBUTION ANALYSIS")
    print("="*60)

    print(f"\nTotal Predictions: {len(confidences)}")
    print(f"\nConfidence Statistics:")
    print(f"  Mean:   {np.mean(confidences):.2f}%")
    print(f"  Median: {np.median(confidences):.2f}%")
    print(f"  Std:    {np.std(confidences):.2f}%")
    print(f"  Min:    {np.min(confidences):.2f}%")
    print(f"  Max:    {np.max(confidences):.2f}%")

    # Percentiles
    print(f"\nPercentiles:")
    for p in [10, 25, 50, 75, 90, 95, 99]:
        print(f"  {p}th: {np.percentile(confidences, p):.2f}%")

    # Confidence buckets
    print(f"\nConfidence Distribution:")
    buckets = [(0, 55), (55, 60), (60, 65), (65, 70), (70, 75), (75, 100)]
    for low, high in buckets:
        count = np.sum((confidences >= low) & (confidences < high))
        pct = count / len(confidences) * 100
        print(f"  {low}-{high}%: {count:4d} ({pct:5.2f}%)")

    # Direction distribution - predictions are confidence scores, not direction probabilities
    # We need to show how many high vs low confidence predictions there are
    print(f"\nConfidence Level Distribution:")
    high_conf = np.sum(confidences >= 60)
    low_conf = np.sum(confidences < 60)
    print(f"  High (≥60%): {high_conf:4d} ({high_conf/len(predictions)*100:.2f}%)")
    print(f"  Low (<60%):  {low_conf:4d} ({low_conf/len(predictions)*100:.2f}%)")

    # If we have actuals, calculate win rate by confidence bucket
    # Note: predictions are confidence scores (0-1), not probabilities
    # We need the raw return predictions to determine direction
    if actuals is not None:
        print(f"\nWin Rate by Confidence Bucket:")
        for low, high in buckets:
            mask = (confidences >= low) & (confidences < high)
            if np.sum(mask) > 0:
                bucket_actuals = actuals[mask]
                # For regression, "win" means actual moved in predicted direction
                # Since we don't have direction here, use simple accuracy
                win_rate = np.mean(bucket_actuals)
                count = np.sum(mask)
                print(f"  {low}-{high}%: {win_rate:.2%} ({count} samples)")

    return confidences


def main():
    parser = argparse.ArgumentParser(description="Analyze ML model confidence distribution")
    parser.add_argument("--pair", default="BTC/USDT", help="Trading pair")
    parser.add_argument("--timeframe", default="4h", help="Timeframe")
    parser.add_argument("--model", default="models/ensemble_model.pkl", help="Model path")
    parser.add_argument("--days", type=int, default=180, help="Days of data to analyze")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"ML MODEL CONFIDENCE ANALYSIS - PHASE 4.7")
    print(f"{'='*60}")
    print(f"\nPair: {args.pair}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Model: {args.model}")
    print(f"Analysis Period: Last {args.days} days")

    # Load model
    print(f"\n📊 Loading model...")
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        print(f"\nTrain the model first:")
        print(f"  python scripts/train_ensemble_model.py --pair {args.pair} --timeframe {args.timeframe}")
        sys.exit(1)

    ensemble_model = load_ensemble_model(args.model)
    feature_columns = ensemble_model.feature_names

    if not feature_columns:
        print(f"⚠️  No feature names found in model, will use all available features")

    print(f"✅ Model loaded successfully")
    print(f"   Base models: {ensemble_model.model_names}")
    print(f"   Ensemble method: {ensemble_model.ensemble_method}")
    if feature_columns:
        print(f"   Features: {len(feature_columns)}")

    # Load historical data from Freqtrade data directory
    print(f"\n📊 Loading historical data...")
    pair_filename = args.pair.replace("/", "_")
    data_file = project_root / f"user_data/data/binance/{pair_filename}-{args.timeframe}.feather"

    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        print(f"\nDownload data first with:")
        print(f"  freqtrade download-data --exchange binance --pairs {args.pair} --timeframe {args.timeframe} --days {args.days} --userdir user_data")
        sys.exit(1)

    # Load feather format
    df = pd.read_feather(data_file)
    if 'date' in df.columns:
        df.rename(columns={'date': 'timestamp'}, inplace=True)
    df.set_index('timestamp', inplace=True)

    # Filter to last N days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    df = df[df.index >= pd.Timestamp(start_date, tz='UTC')]

    if len(df) == 0:
        print(f"❌ No data in date range")
        sys.exit(1)

    print(f"✅ Loaded {len(df)} candles")
    print(f"   Period: {df.index[0]} to {df.index[-1]}")

    # Add features
    print(f"\n📊 Engineering features...")
    fe = FeatureEngineer()
    df = fe.add_all_features(df)

    # Remove NaN rows
    df_clean = df.dropna()
    print(f"✅ Features engineered, {len(df_clean)} clean samples")

    # Prepare features - use exactly the features the model was trained with
    # Check which features are available
    missing_features = [col for col in feature_columns if col not in df_clean.columns]

    if missing_features:
        print(f"⚠️  Missing features: {missing_features}")
        print(f"   Creating them with zeros...")
        for col in missing_features:
            df_clean[col] = 0

    X = df_clean[feature_columns].values

    # Make predictions
    print(f"\n📊 Generating predictions...")
    raw_predictions = ensemble_model.predict(X)  # Predicted returns (percentage)

    print(f"✅ Generated {len(raw_predictions)} predictions")
    print(f"   Prediction range: {raw_predictions.min():.2f}% to {raw_predictions.max():.2f}%")

    # Convert return predictions to confidence using the same formula as hybrid_predictor
    # confidence = min(abs(predicted_return) / 5.0, 1.0)
    # A 5% predicted return = 100% confidence, 2.5% = 50% confidence, etc.
    predictions = np.minimum(np.abs(raw_predictions) / 5.0, 1.0)

    # Create actuals (1 if next candle closed higher)
    df_clean = df_clean.copy()
    df_clean['next_close'] = df_clean['close'].shift(-1)
    df_clean['actual_direction'] = (df_clean['next_close'] > df_clean['close']).astype(int)
    df_clean = df_clean.dropna()

    actuals = df_clean['actual_direction'].values[:len(predictions)]

    # Analyze confidence distribution
    confidences = analyze_confidence_distribution(predictions, actuals)

    # Recent predictions (last 30 days)
    recent_days = 30
    recent_samples = min(len(predictions), int(recent_days * 24 / 4))  # 4h timeframe

    print(f"\n{'='*60}")
    print(f"RECENT PREDICTIONS (Last {recent_days} days)")
    print(f"{'='*60}")

    recent_preds = predictions[-recent_samples:]
    recent_actuals = actuals[-recent_samples:]
    recent_confidences = analyze_confidence_distribution(recent_preds, recent_actuals)

    # Compare with Phase 4.6 observed values
    print(f"\n{'='*60}")
    print(f"COMPARISON WITH PHASE 4.6 OBSERVATIONS")
    print(f"{'='*60}")

    phase46_confidences = [35.3, 23.3]
    phase46_avg = np.mean(phase46_confidences)

    print(f"\nPhase 4.6 Observed:")
    print(f"  Range: 23.3% - 35.3%")
    print(f"  Average: {phase46_avg:.1f}%")

    print(f"\nHistorical Baseline ({args.days} days):")
    print(f"  Mean: {np.mean(confidences):.1f}%")
    print(f"  Median: {np.median(confidences):.1f}%")

    print(f"\nRecent Baseline (Last {recent_days} days):")
    print(f"  Mean: {np.mean(recent_confidences):.1f}%")
    print(f"  Median: {np.median(recent_confidences):.1f}%")

    # Interpretation
    print(f"\n{'='*60}")
    print(f"INTERPRETATION")
    print(f"{'='*60}")

    hist_mean = np.mean(confidences)
    recent_mean = np.mean(recent_confidences)

    if phase46_avg < hist_mean - 10:
        print(f"\n⚠️  Phase 4.6 confidence ({phase46_avg:.1f}%) is SIGNIFICANTLY LOWER than")
        print(f"    historical average ({hist_mean:.1f}%)")
        print(f"\n    Possible causes:")
        print(f"    1. Market conditions changed (more uncertain)")
        print(f"    2. Model needs retraining on recent data")
        print(f"    3. Features degraded over time")
    elif phase46_avg < hist_mean - 5:
        print(f"\n⚠️  Phase 4.6 confidence ({phase46_avg:.1f}%) is LOWER than")
        print(f"    historical average ({hist_mean:.1f}%)")
        print(f"\n    This is normal for uncertain market conditions")
    else:
        print(f"\n✅ Phase 4.6 confidence ({phase46_avg:.1f}%) is within normal range")
        print(f"    (Historical average: {hist_mean:.1f}%)")
        print(f"\n    Model is operating normally - low confidence is expected")
        print(f"    in uncertain markets")

    # Recommendations
    print(f"\n{'='*60}")
    print(f"RECOMMENDATIONS FOR PHASE 4.7")
    print(f"{'='*60}")

    if hist_mean < 60:
        print(f"\n1. 📊 Model Calibration Needed")
        print(f"   - Historical mean confidence: {hist_mean:.1f}%")
        print(f"   - This is below trading threshold (60%)")
        print(f"   - Consider:")
        print(f"     • Probability calibration (Platt scaling, isotonic regression)")
        print(f"     • Adjusting confidence thresholds")
        print(f"     • Feature importance analysis")

    if np.mean(recent_confidences) < hist_mean - 5:
        print(f"\n2. 🔄 Model Retraining Recommended")
        print(f"   - Recent confidence declining: {np.mean(recent_confidences):.1f}%")
        print(f"   - Model may be stale")
        print(f"   - Retrain on recent data")

    print(f"\n3. 🎯 Suggested Confidence Thresholds:")
    p75 = np.percentile(confidences, 75)
    p90 = np.percentile(confidences, 90)
    print(f"   - Minimum: {p75:.1f}% (75th percentile)")
    print(f"   - Strong: {p90:.1f}% (90th percentile)")
    print(f"   - Current: 60% (may need adjustment)")

    print(f"\n4. 📈 Next Steps:")
    print(f"   - Implement probability calibration")
    print(f"   - Run longer paper trading test (24-48 hours)")
    print(f"   - Compare calibrated vs uncalibrated performance")

    print(f"\n{'='*60}")
    print(f"Analysis complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
