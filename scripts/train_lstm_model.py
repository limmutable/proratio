"""
LSTM Model Training Script

Script to train LSTM price prediction models on historical cryptocurrency data.
Integrates with feature engineering and saves trained models for use in trading strategies.

Usage:
    python scripts/train_lstm_model.py --pair BTC/USDT --timeframe 4h --epochs 100

Author: Proratio Team
Date: 2025-10-11
Phase: 3.2 - LSTM Price Prediction
"""

import sys
from pathlib import Path
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from proratio_quantlab.ml.feature_engineering import (
    FeatureEngineer,
    create_target_labels,
)
from proratio_quantlab.ml.lstm_predictor import LSTMPredictor
from proratio_quantlab.ml.lstm_data_pipeline import prepare_lstm_data


def load_historical_data(pair: str, timeframe: str, days: int = 180) -> pd.DataFrame:
    """
    Load historical OHLCV data.

    For now, this is a placeholder. In production, this would load from:
    - PostgreSQL database
    - Freqtrade user_data
    - CCXT exchange data

    Args:
        pair: Trading pair (e.g., 'BTC/USDT')
        timeframe: Timeframe (e.g., '4h')
        days: Number of days of history

    Returns:
        DataFrame with OHLCV data
    """
    print(f"Loading {days} days of {pair} data at {timeframe} timeframe...")

    # TODO: Implement actual data loading from database/freqtrade
    # For now, return None to indicate data should be loaded externally
    print("Note: Data loading not yet implemented. Please provide dataframe directly.")
    return None


def train_lstm_model(
    dataframe: pd.DataFrame,
    model_type: str = "lstm",
    sequence_length: int = 24,
    hidden_size: int = 128,
    num_layers: int = 2,
    dropout: float = 0.2,
    epochs: int = 100,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    target_column: str = "target_return",
    save_path: Optional[str] = None,
) -> Tuple[LSTMPredictor, dict]:
    """
    Train LSTM model on prepared data.

    Args:
        dataframe: Input dataframe with OHLCV and features
        model_type: 'lstm' or 'gru'
        sequence_length: Lookback window size
        hidden_size: Number of hidden units
        num_layers: Number of recurrent layers
        dropout: Dropout rate
        epochs: Training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        target_column: Target column name
        save_path: Path to save trained model (optional)

    Returns:
        Trained predictor, training history
    """
    print("\n" + "=" * 60)
    print("LSTM Model Training Pipeline")
    print("=" * 60)

    # Step 1: Feature Engineering
    print("\n[1/5] Feature Engineering...")
    fe = FeatureEngineer()
    df_features = fe.add_all_features(dataframe.copy())

    # Add target labels
    df_features = create_target_labels(
        df_features, target_type="regression", lookahead_periods=4
    )

    print(f"  - Generated {len(df_features.columns)} total columns")
    print(f"  - {len(df_features)} samples after feature engineering")

    # Step 2: Data Preparation
    print("\n[2/5] Data Preparation...")
    (X_train, y_train), (X_val, y_val), (X_test, y_test), feature_cols = (
        prepare_lstm_data(
            df_features,
            target_column=target_column,
            train_ratio=0.7,
            val_ratio=0.15,
            test_ratio=0.15,
        )
    )

    print(f"  - Train: {len(X_train)} samples")
    print(f"  - Val: {len(X_val)} samples")
    print(f"  - Test: {len(X_test)} samples")
    print(f"  - Features: {len(feature_cols)}")

    # Step 3: Initialize Predictor
    print(f"\n[3/5] Initializing {model_type.upper()} Model...")
    predictor = LSTMPredictor(
        model_type=model_type,
        sequence_length=sequence_length,
        hidden_size=hidden_size,
        num_layers=num_layers,
        dropout=dropout,
        learning_rate=learning_rate,
        batch_size=batch_size,
    )

    # Preprocess data (fit scaler)
    X_train_scaled, _ = predictor.preprocess_data(
        pd.DataFrame(X_train, columns=feature_cols).assign(**{target_column: y_train}),
        target_column=target_column,
        fit_scaler=True,
    )

    X_val_scaled, _ = predictor.preprocess_data(
        pd.DataFrame(X_val, columns=feature_cols).assign(**{target_column: y_val}),
        target_column=target_column,
        fit_scaler=False,
    )

    X_test_scaled, _ = predictor.preprocess_data(
        pd.DataFrame(X_test, columns=feature_cols).assign(**{target_column: y_test}),
        target_column=target_column,
        fit_scaler=False,
    )

    # Step 4: Training
    print(f"\n[4/5] Training Model ({epochs} epochs)...")
    history = predictor.train(
        X_train_scaled,
        y_train,
        X_val_scaled,
        y_val,
        epochs=epochs,
        early_stopping_patience=15,
        verbose=True,
    )

    # Step 5: Evaluation
    print("\n[5/5] Evaluating Model...")
    predictions = predictor.predict(X_test_scaled)

    # Calculate metrics (account for sequence_length reduction)
    actual_test = y_test[sequence_length:]
    mse = np.mean((predictions - actual_test) ** 2)
    rmse = np.sqrt(mse)
    mae = np.mean(np.abs(predictions - actual_test))

    # Direction accuracy
    pred_direction = (predictions > 0).astype(int)
    actual_direction = (actual_test > 0).astype(int)
    direction_accuracy = (pred_direction == actual_direction).mean()

    print("\nTest Set Metrics:")
    print(f"  - RMSE: {rmse:.6f}")
    print(f"  - MAE: {mae:.6f}")
    print(f"  - Direction Accuracy: {direction_accuracy:.2%}")

    # Save model
    if save_path:
        predictor.save(save_path)
        print(f"\nModel saved to: {save_path}")

    return predictor, history


def plot_training_history(history: dict, save_path: Optional[str] = None):
    """Plot training and validation loss."""
    plt.figure(figsize=(10, 6))
    plt.plot(history["train_loss"], label="Train Loss")
    if "val_loss" in history:
        plt.plot(history["val_loss"], label="Validation Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss (MSE)")
    plt.title("LSTM Training History")
    plt.legend()
    plt.grid(True)

    if save_path:
        plt.savefig(save_path)
        print(f"Training plot saved to: {save_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Train LSTM price prediction model")
    parser.add_argument("--pair", type=str, default="BTC/USDT", help="Trading pair")
    parser.add_argument("--timeframe", type=str, default="4h", help="Timeframe")
    parser.add_argument("--days", type=int, default=180, help="Days of history")
    parser.add_argument(
        "--model-type",
        type=str,
        default="lstm",
        choices=["lstm", "gru"],
        help="Model type",
    )
    parser.add_argument(
        "--sequence-length", type=int, default=24, help="Sequence length"
    )
    parser.add_argument("--hidden-size", type=int, default=128, help="Hidden size")
    parser.add_argument("--num-layers", type=int, default=2, help="Number of layers")
    parser.add_argument("--dropout", type=float, default=0.2, help="Dropout rate")
    parser.add_argument("--epochs", type=int, default=100, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument(
        "--learning-rate", type=float, default=0.001, help="Learning rate"
    )
    parser.add_argument(
        "--save-path", type=str, default=None, help="Path to save model"
    )

    args = parser.parse_args()

    # Load data
    print("Note: This script requires historical data to be provided.")
    print("Please load data externally and pass to train_lstm_model() function.")
    print("\nExample:")
    print("  from scripts.train_lstm_model import train_lstm_model")
    print("  predictor, history = train_lstm_model(your_dataframe)")


if __name__ == "__main__":
    main()
