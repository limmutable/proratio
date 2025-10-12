"""
Ensemble Learning Example Script

Demonstrates ensemble learning with synthetic data.
Use this as a reference for implementing ensemble in your trading strategies.

Usage:
    python scripts/example_ensemble_usage.py

Author: Proratio Team
Date: 2025-10-11
Phase: 3.3 - Ensemble Learning
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from proratio_quantlab.ml.ensemble_predictor import EnsembleBuilder


def generate_synthetic_data(n_samples=1000, n_features=20):
    """Generate synthetic time-series data for demonstration."""
    np.random.seed(42)

    # Features
    X = np.random.randn(n_samples, n_features)

    # Target: complex non-linear relationship
    weights = np.random.randn(n_features)
    linear_component = X @ weights
    non_linear_component = np.sin(X[:, 0]) * np.cos(X[:, 1])
    noise = np.random.randn(n_samples) * 0.1

    y = linear_component + non_linear_component + noise

    return X, y


def main():
    print("=" * 60)
    print("ENSEMBLE LEARNING EXAMPLE")
    print("=" * 60)

    # [1] Generate synthetic data
    print("\n[1/5] Generating synthetic data...")
    X, y = generate_synthetic_data(n_samples=1000, n_features=20)

    # Split data (time-ordered, no shuffling)
    train_size = int(0.7 * len(X))
    val_size = int(0.15 * len(X))

    X_train = X[:train_size]
    y_train = y[:train_size]

    X_val = X[train_size : train_size + val_size]
    y_val = y[train_size : train_size + val_size]

    X_test = X[train_size + val_size :]
    y_test = y[train_size + val_size :]

    print(f"✓ Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    # [2] Build Stacking Ensemble
    print("\n[2/5] Building stacking ensemble...")
    builder = EnsembleBuilder(ensemble_method="stacking")

    # Add base models (excluding LSTM for this example)
    builder.add_lightgbm(name="lgbm", params={"num_leaves": 31, "n_estimators": 100})
    builder.add_xgboost(name="xgb", params={"max_depth": 6, "n_estimators": 100})

    print("  Added 2 base models: LightGBM, XGBoost")

    # [3] Train base models
    print("\n[3/5] Training base models...")
    builder.train_all(X_train, y_train, X_val, y_val)
    print("✓ Base models trained")

    # [4] Build ensemble
    print("\n[4/5] Building ensemble with Ridge meta-model...")
    ensemble = builder.build_ensemble(X_val, y_val, meta_model_type="ridge")
    print("✓ Ensemble built")

    # [5] Evaluate
    print("\n[5/5] Evaluating models...")
    results = ensemble.evaluate(X_test, y_test)

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)

    for model_name, metrics in results.items():
        print(f"\n{model_name.upper()}")
        print(f"  RMSE: {metrics['rmse']:.6f}")
        print(f"  MAE:  {metrics['mae']:.6f}")
        print(f"  MSE:  {metrics['mse']:.6f}")

    # Calculate improvement
    ensemble_rmse = results["ensemble"]["rmse"]
    base_models = {k: v for k, v in results.items() if k != "ensemble"}
    best_base_rmse = min(m["rmse"] for m in base_models.values())
    improvement = ((best_base_rmse - ensemble_rmse) / best_base_rmse) * 100

    print("\n" + "-" * 60)
    print(f"✓ Ensemble improvement: {improvement:.2f}% better than best base model")
    print("-" * 60)

    # [6] Compare Ensemble Methods
    print("\n" + "=" * 60)
    print("COMPARING ENSEMBLE METHODS")
    print("=" * 60)

    methods = ["stacking", "blending", "voting"]
    method_results = {}

    for method in methods:
        print(f"\nTraining {method} ensemble...")

        builder = EnsembleBuilder(ensemble_method=method)
        builder.add_lightgbm(
            name="lgbm", params={"num_leaves": 31, "n_estimators": 100}
        )
        builder.add_xgboost(name="xgb", params={"max_depth": 6, "n_estimators": 100})

        # Skip training if models already trained
        builder.trained_models = {
            "lgbm": results  # Reuse previous training
        }

        builder.train_all(X_train, y_train, X_val, y_val)
        ensemble = builder.build_ensemble(X_val, y_val)

        eval_results = ensemble.evaluate(X_test, y_test)
        method_results[method] = eval_results["ensemble"]["rmse"]

        print(f"  {method.capitalize()} RMSE: {eval_results['ensemble']['rmse']:.6f}")

    # Show comparison
    print("\n" + "-" * 60)
    print("ENSEMBLE METHOD COMPARISON")
    print("-" * 60)
    for method, rmse in sorted(method_results.items(), key=lambda x: x[1]):
        print(f"  {method.capitalize()}: {rmse:.6f}")

    print("\n✓ Example complete!")
    print("\nNext Steps:")
    print("  1. Review docs/ensemble_implementation.md for detailed guide")
    print("  2. Adapt this code for your trading data")
    print("  3. Integrate with Freqtrade strategy")


if __name__ == "__main__":
    main()
