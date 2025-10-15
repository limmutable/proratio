"""
Ensemble Model Training Script for Phase 3.3

Trains ensemble of LSTM + LightGBM + XGBoost models and combines
predictions using stacking, blending, or voting methods.

Usage:
    python scripts/train_ensemble_model.py --pair BTC/USDT --ensemble-method stacking
    python scripts/train_ensemble_model.py --pair ETH/USDT --ensemble-method blending

Author: Proratio Team
Date: 2025-10-11
Phase: 3.3 - Ensemble Learning
"""

import sys
from pathlib import Path
import argparse
import pandas as pd
from typing import Optional, Tuple, Dict
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from proratio_utilities.data.loaders import DataLoader
from proratio_quantlab.ml.feature_engineering import (
    FeatureEngineer,
    create_target_labels,
)
from proratio_quantlab.ml.ensemble_predictor import EnsembleBuilder, EnsemblePredictor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_and_prepare_data(
    pair: str = "BTC/USDT", timeframe: str = "4h", limit: int = 10000
) -> pd.DataFrame:
    """
    Load and prepare data for ensemble training.

    Uses Freqtrade's downloaded data from user_data/data/binance/

    Args:
        pair: Trading pair
        timeframe: Timeframe for data
        limit: Number of candles to load

    Returns:
        DataFrame with OHLCV data
    """
    logger.info(f"[1/6] Loading data for {pair} ({timeframe})...")

    # Load from Freqtrade data directory
    # Convert pair format: BTC/USDT -> BTC_USDT
    pair_filename = pair.replace("/", "_")

    # Try feather format first (newer Freqtrade), then JSON
    data_file_feather = project_root / f"user_data/data/binance/{pair_filename}-{timeframe}.feather"
    data_file_json = project_root / f"user_data/data/binance/{pair_filename}-{timeframe}.json"

    if data_file_feather.exists():
        # Load feather format (Freqtrade 2025+)
        df = pd.read_feather(data_file_feather)
        # Rename columns to standard format
        if 'date' in df.columns:
            df.rename(columns={'date': 'timestamp'}, inplace=True)
        df.set_index('timestamp', inplace=True)
        logger.info(f"✓ Loaded {len(df)} candles from {data_file_feather.name} (feather format)")
    elif data_file_json.exists():
        # Load JSON format (older Freqtrade)
        import json
        with open(data_file_json) as f:
            data = json.load(f)
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        logger.info(f"✓ Loaded {len(df)} candles from {data_file_json.name} (JSON format)")
    else:
        raise FileNotFoundError(
            f"Data file not found: {data_file_feather.name} or {data_file_json.name}\n"
            f"Please download data first with:\n"
            f"  freqtrade download-data --pairs {pair} --timeframe {timeframe} "
            f"--days 700 --userdir user_data"
        )

    # Limit to requested number of candles (most recent)
    if len(df) > limit:
        df = df.iloc[-limit:]

    logger.info(f"  Date range: {df.index[0]} to {df.index[-1]}")

    return df


def train_ensemble_model(
    dataframe: pd.DataFrame,
    ensemble_method: str = "stacking",
    meta_model_type: str = "ridge",
    sequence_length: int = 24,
    include_lstm: bool = True,
    include_lgbm: bool = True,
    include_xgb: bool = True,
    target_column: str = "target_return",
    save_path: Optional[str] = None,
) -> Tuple[EnsemblePredictor, Dict]:
    """
    Train ensemble model with multiple base models.

    Args:
        dataframe: OHLCV data
        ensemble_method: 'stacking', 'blending', or 'voting'
        meta_model_type: 'ridge', 'lasso', 'rf' (for stacking)
        sequence_length: LSTM sequence length
        include_lstm: Include LSTM in ensemble
        include_lgbm: Include LightGBM in ensemble
        include_xgb: Include XGBoost in ensemble
        target_column: Target column name
        save_path: Path to save ensemble model

    Returns:
        Trained ensemble predictor and evaluation results
    """
    # [2/6] Feature Engineering
    logger.info("[2/6] Engineering features...")
    fe = FeatureEngineer()
    df_features = fe.add_all_features(dataframe)
    df_features = create_target_labels(df_features, target_type="regression")

    logger.info(f"✓ Created {len(df_features.columns)} features")

    # [3/6] Data Preparation
    logger.info("[3/6] Preparing train/val/test splits...")

    # For tree models: use regular features
    from proratio_quantlab.ml.lstm_data_pipeline import LSTMDataPipeline

    pipeline = LSTMDataPipeline(train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
    df_clean, features = pipeline.prepare_data(df_features, target_column=target_column)

    # Split data (time-ordered, no shuffling)
    df_train, df_val, df_test = pipeline.split_data(df_clean, features, target_column)

    # Extract arrays
    X_train, y_train = pipeline.get_arrays(df_train, features, target_column)
    X_val, y_val = pipeline.get_arrays(df_val, features, target_column)
    X_test, y_test = pipeline.get_arrays(df_test, features, target_column)

    logger.info(f"✓ Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    # [4/6] Build Ensemble
    logger.info(f"[4/6] Building {ensemble_method} ensemble...")

    builder = EnsembleBuilder(ensemble_method=ensemble_method)

    # Add base models
    if include_lgbm:
        logger.info("  Adding LightGBM...")
        builder.add_lightgbm(
            name="lgbm",
            params={
                "num_leaves": 31,
                "learning_rate": 0.05,
                "n_estimators": 500,
                "random_state": 42,
            },
        )

    if include_xgb:
        logger.info("  Adding XGBoost...")
        builder.add_xgboost(
            name="xgb",
            params={
                "max_depth": 6,
                "learning_rate": 0.1,
                "n_estimators": 300,
                "random_state": 42,
            },
        )

    if include_lstm:
        logger.info("  Adding LSTM...")
        builder.add_lstm(
            name="lstm",
            sequence_length=sequence_length,
            hidden_size=128,
            num_layers=2,
            dropout=0.2,
        )

    # Train base models
    logger.info("  Training base models...")
    builder.train_all(X_train, y_train, X_val, y_val)

    # Build ensemble
    logger.info(f"  Building {ensemble_method} ensemble...")
    ensemble = builder.build_ensemble(X_val, y_val, meta_model_type=meta_model_type)

    logger.info("✓ Ensemble built successfully")

    # [5/6] Evaluation
    logger.info("[5/6] Evaluating ensemble...")

    results = ensemble.evaluate(X_test, y_test)

    # Print results
    print("\n" + "=" * 60)
    print("ENSEMBLE EVALUATION RESULTS")
    print("=" * 60)

    for model_name, metrics in results.items():
        print(f"\n{model_name.upper()}")
        print(f"  RMSE: {metrics['rmse']:.6f}")
        print(f"  MAE:  {metrics['mae']:.6f}")
        print(f"  MSE:  {metrics['mse']:.6f}")

    # Compare ensemble vs best base model
    ensemble_rmse = results["ensemble"]["rmse"]
    base_models = {k: v for k, v in results.items() if k != "ensemble"}
    best_base_rmse = min(m["rmse"] for m in base_models.values())
    improvement = ((best_base_rmse - ensemble_rmse) / best_base_rmse) * 100

    print("\n" + "-" * 60)
    print(f"Ensemble improvement: {improvement:.2f}% better than best base model")
    print("-" * 60)

    # Show model contributions
    if ensemble_method == "blending":
        print("\nModel Weights:")
        for name, weight in ensemble.weights.items():
            print(f"  {name}: {weight:.4f}")

    # [6/6] Save Model
    if save_path:
        logger.info(f"[6/6] Saving ensemble to {save_path}...")
        # Store feature names for validation
        ensemble.feature_names = features
        ensemble.save(save_path)
        logger.info("✓ Model saved")
        logger.info(f"   Features saved: {len(features)} feature names")

    return ensemble, results


def main():
    parser = argparse.ArgumentParser(description="Train ensemble model")

    # Data parameters
    parser.add_argument("--pair", type=str, default="BTC/USDT", help="Trading pair")
    parser.add_argument("--timeframe", type=str, default="4h", help="Timeframe")
    parser.add_argument("--limit", type=int, default=10000, help="Number of candles")

    # Ensemble parameters
    parser.add_argument(
        "--ensemble-method",
        type=str,
        default="stacking",
        choices=["stacking", "blending", "voting"],
        help="Ensemble method",
    )
    parser.add_argument(
        "--meta-model",
        type=str,
        default="ridge",
        choices=["ridge", "lasso", "rf"],
        help="Meta-model type for stacking",
    )

    # Base model selection
    parser.add_argument(
        "--no-lstm", action="store_true", help="Exclude LSTM from ensemble"
    )
    parser.add_argument(
        "--no-lgbm", action="store_true", help="Exclude LightGBM from ensemble"
    )
    parser.add_argument(
        "--no-xgb", action="store_true", help="Exclude XGBoost from ensemble"
    )

    # Model parameters
    parser.add_argument(
        "--sequence-length", type=int, default=24, help="LSTM sequence length"
    )
    parser.add_argument(
        "--target", type=str, default="target_return", help="Target column"
    )

    # Output
    parser.add_argument(
        "--save", type=str, default=None, help="Path to save ensemble model"
    )

    args = parser.parse_args()

    # Validate at least one model selected
    if args.no_lstm and args.no_lgbm and args.no_xgb:
        raise ValueError("At least one base model must be selected")

    try:
        # Load data
        df = load_and_prepare_data(args.pair, args.timeframe, args.limit)

        # Train ensemble
        ensemble, results = train_ensemble_model(
            dataframe=df,
            ensemble_method=args.ensemble_method,
            meta_model_type=args.meta_model,
            sequence_length=args.sequence_length,
            include_lstm=not args.no_lstm,
            include_lgbm=not args.no_lgbm,
            include_xgb=not args.no_xgb,
            target_column=args.target,
            save_path=args.save,
        )

        print("\n✓ Training complete!")

        # Show next steps
        print("\nNext Steps:")
        print("  1. Review model performance metrics above")
        print("  2. Test ensemble with new data")
        print("  3. Integrate with Freqtrade strategy")
        if args.save:
            print(f"  4. Load model: ensemble.load('{args.save}')")

    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
