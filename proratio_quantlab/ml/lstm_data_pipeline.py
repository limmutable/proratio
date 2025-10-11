"""
LSTM Data Pipeline for Phase 3.2

Provides data preprocessing, train/val/test splitting, and data loading
utilities specifically designed for LSTM price prediction models.

Author: Proratio Team
Date: 2025-10-11
Phase: 3.2 - LSTM Price Prediction
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict
from sklearn.model_selection import TimeSeriesSplit
import logging

logger = logging.getLogger(__name__)


class LSTMDataPipeline:
    """
    Data pipeline for preparing cryptocurrency data for LSTM models.

    Handles feature engineering integration, train/val/test splits,
    and data quality checks specific to time-series forecasting.
    """

    def __init__(
        self,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        min_samples: int = 1000
    ):
        """
        Initialize data pipeline.

        Args:
            train_ratio: Proportion of data for training
            val_ratio: Proportion of data for validation
            test_ratio: Proportion of data for testing
            min_samples: Minimum number of samples required
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.01, \
            "train_ratio + val_ratio + test_ratio must equal 1.0"

        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.min_samples = min_samples

    def prepare_data(
        self,
        dataframe: pd.DataFrame,
        target_column: str = 'target_return',
        feature_columns: Optional[list] = None,
        remove_nan: bool = True
    ) -> Tuple[pd.DataFrame, list]:
        """
        Prepare dataframe for LSTM training.

        Args:
            dataframe: Input dataframe with features and target
            target_column: Name of target column
            feature_columns: List of feature columns (None = auto-detect)
            remove_nan: Whether to remove rows with NaN values

        Returns:
            Cleaned dataframe, list of feature column names
        """
        df = dataframe.copy()

        # Auto-detect feature columns if not provided
        if feature_columns is None:
            # Exclude OHLCV, date, and target columns
            exclude_cols = ['date', 'open', 'high', 'low', 'close', 'volume', target_column]
            feature_columns = [col for col in df.columns if col not in exclude_cols]

        # Check if target exists
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in dataframe")

        # Remove NaN values
        if remove_nan:
            initial_len = len(df)
            df = df.dropna()
            removed = initial_len - len(df)
            if removed > 0:
                logger.info(f"Removed {removed} rows with NaN values ({removed/initial_len*100:.1f}%)")

        # Check minimum samples
        if len(df) < self.min_samples:
            raise ValueError(f"Insufficient data: {len(df)} < {self.min_samples} samples")

        # Verify all feature columns exist
        missing_cols = set(feature_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing feature columns: {missing_cols}")

        logger.info(f"Prepared {len(df)} samples with {len(feature_columns)} features")

        return df, feature_columns

    def split_data(
        self,
        dataframe: pd.DataFrame,
        feature_columns: list,
        target_column: str = 'target_return'
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data into train, validation, and test sets (time-ordered).

        Args:
            dataframe: Prepared dataframe
            feature_columns: List of feature columns
            target_column: Name of target column

        Returns:
            Train dataframe, validation dataframe, test dataframe
        """
        n = len(dataframe)
        train_size = int(n * self.train_ratio)
        val_size = int(n * self.val_ratio)

        # Time-ordered split (no shuffling for time-series)
        df_train = dataframe.iloc[:train_size].copy()
        df_val = dataframe.iloc[train_size:train_size + val_size].copy()
        df_test = dataframe.iloc[train_size + val_size:].copy()

        logger.info(f"Split sizes - Train: {len(df_train)}, Val: {len(df_val)}, Test: {len(df_test)}")

        return df_train, df_val, df_test

    def get_arrays(
        self,
        dataframe: pd.DataFrame,
        feature_columns: list,
        target_column: str = 'target_return'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract feature and target arrays from dataframe.

        Args:
            dataframe: Input dataframe
            feature_columns: List of feature columns
            target_column: Name of target column

        Returns:
            X: Feature array (n_samples, n_features)
            y: Target array (n_samples,)
        """
        X = dataframe[feature_columns].values
        y = dataframe[target_column].values

        return X, y

    def create_walk_forward_splits(
        self,
        dataframe: pd.DataFrame,
        n_splits: int = 5
    ) -> list:
        """
        Create walk-forward validation splits for time-series cross-validation.

        Args:
            dataframe: Input dataframe
            n_splits: Number of splits

        Returns:
            List of (train_indices, test_indices) tuples
        """
        tscv = TimeSeriesSplit(n_splits=n_splits)
        splits = []

        for train_idx, test_idx in tscv.split(dataframe):
            splits.append((train_idx, test_idx))

        logger.info(f"Created {n_splits} walk-forward splits")

        return splits

    def get_data_summary(self, dataframe: pd.DataFrame, feature_columns: list) -> Dict:
        """
        Get summary statistics of the data.

        Args:
            dataframe: Input dataframe
            feature_columns: List of feature columns

        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'n_samples': len(dataframe),
            'n_features': len(feature_columns),
            'date_range': (dataframe['date'].min(), dataframe['date'].max()) if 'date' in dataframe.columns else None,
            'missing_values': dataframe[feature_columns].isnull().sum().sum(),
            'feature_stats': dataframe[feature_columns].describe().to_dict()
        }

        return summary


def prepare_lstm_data(
    dataframe: pd.DataFrame,
    target_column: str = 'target_return',
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    min_samples: int = 100
) -> Tuple[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray], list]:
    """
    Convenience function to prepare data for LSTM training.

    Args:
        dataframe: Input dataframe with features and target
        target_column: Name of target column
        train_ratio: Training data proportion
        val_ratio: Validation data proportion
        test_ratio: Test data proportion
        min_samples: Minimum required samples

    Returns:
        (X_train, y_train), (X_val, y_val), (X_test, y_test), feature_columns
    """
    pipeline = LSTMDataPipeline(train_ratio, val_ratio, test_ratio, min_samples)

    # Prepare data
    df_clean, feature_cols = pipeline.prepare_data(dataframe, target_column)

    # Split data
    df_train, df_val, df_test = pipeline.split_data(df_clean, feature_cols, target_column)

    # Get arrays
    X_train, y_train = pipeline.get_arrays(df_train, feature_cols, target_column)
    X_val, y_val = pipeline.get_arrays(df_val, feature_cols, target_column)
    X_test, y_test = pipeline.get_arrays(df_test, feature_cols, target_column)

    return (X_train, y_train), (X_val, y_val), (X_test, y_test), feature_cols


# Example usage
if __name__ == "__main__":
    print("LSTM Data Pipeline for Time-Series Preprocessing")
    print("Use LSTMDataPipeline class or prepare_lstm_data() function")
    print("\nExample:")
    print("  pipeline = LSTMDataPipeline()")
    print("  df_clean, features = pipeline.prepare_data(df)")
    print("  df_train, df_val, df_test = pipeline.split_data(df_clean, features)")
