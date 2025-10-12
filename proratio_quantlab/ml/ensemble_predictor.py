"""
Ensemble Learning Module for Phase 3.3

Implements ensemble methods to combine predictions from multiple models
(LSTM, LightGBM, XGBoost) for improved prediction accuracy and robustness.

Supports:
- Stacking: Meta-model learns to combine base model predictions
- Blending: Simple weighted averaging of predictions
- Dynamic weighting: Adjusts weights based on recent performance

Author: Proratio Team
Date: 2025-10-11
Phase: 3.3 - Ensemble Learning
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union
import logging
from pathlib import Path
import joblib
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

logger = logging.getLogger(__name__)

# Optional imports with graceful fallback
try:
    from .lstm_predictor import LSTMPredictor

    LSTM_AVAILABLE = True
except ImportError:
    LSTM_AVAILABLE = False
    logger.warning(
        "LSTM predictor not available. Install PyTorch to enable LSTM models."
    )

try:
    import lightgbm as lgb

    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning(
        "LightGBM not available. Install lightgbm to enable gradient boosting."
    )

try:
    import xgboost as xgb

    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning(
        "XGBoost not available. Install xgboost to enable gradient boosting."
    )


class EnsemblePredictor:
    """
    Ensemble predictor that combines multiple base models.

    Supports three ensemble strategies:
    1. **Stacking**: Meta-model learns optimal combination
    2. **Blending**: Weighted average with fixed/dynamic weights
    3. **Voting**: Simple average (equal weights)

    Architecture:
        Base Models → Predictions → Meta-Model/Weighting → Final Prediction
    """

    def __init__(
        self,
        ensemble_method: str = "stacking",
        meta_model_type: str = "ridge",
        base_models: Optional[Dict[str, object]] = None,
        weights: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize ensemble predictor.

        Args:
            ensemble_method: 'stacking', 'blending', or 'voting'
            meta_model_type: 'ridge', 'lasso', 'rf' (for stacking)
            base_models: Dictionary of model_name -> model_object
            weights: Dictionary of model_name -> weight (for blending)
        """
        self.ensemble_method = ensemble_method
        self.meta_model_type = meta_model_type
        self.base_models = base_models or {}
        self.weights = weights or {}
        self.meta_model = None
        self.scaler = StandardScaler()
        self.model_names = []
        self.performance_history = []

        # Validate ensemble method
        valid_methods = ["stacking", "blending", "voting"]
        if ensemble_method not in valid_methods:
            raise ValueError(f"ensemble_method must be one of {valid_methods}")

        # Initialize meta-model for stacking
        if ensemble_method == "stacking":
            self.meta_model = self._create_meta_model(meta_model_type)

    def _create_meta_model(self, model_type: str):
        """Create meta-model for stacking."""
        if model_type == "ridge":
            return Ridge(alpha=1.0)
        elif model_type == "lasso":
            return Lasso(alpha=0.1)
        elif model_type == "rf":
            return RandomForestRegressor(
                n_estimators=100, max_depth=5, random_state=42, n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown meta_model_type: {model_type}")

    def add_base_model(self, name: str, model: object, weight: float = 1.0):
        """
        Add a base model to the ensemble.

        Args:
            name: Unique identifier for the model
            model: Model object with predict() method
            weight: Weight for blending (ignored for stacking/voting)
        """
        self.base_models[name] = model
        self.weights[name] = weight
        self.model_names.append(name)
        logger.info(f"Added base model: {name} (weight={weight:.2f})")

    def train_stacking(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
    ):
        """
        Train stacking ensemble.

        Steps:
        1. Get predictions from all base models on validation set
        2. Use these predictions as features for meta-model
        3. Train meta-model to learn optimal combination

        Args:
            X_train: Training features (not used, base models already trained)
            y_train: Training targets (not used, base models already trained)
            X_val: Validation features for meta-training
            y_val: Validation targets for meta-training
        """
        if not self.base_models:
            raise ValueError("No base models added. Use add_base_model() first.")

        logger.info(
            f"Training stacking ensemble with {len(self.base_models)} base models"
        )

        # Step 1: Get base model predictions on validation set
        base_predictions = self._get_base_predictions(X_val)

        # Step 2: Train meta-model on base predictions
        self.meta_model.fit(base_predictions, y_val)

        # Step 3: Evaluate meta-model
        meta_pred = self.meta_model.predict(base_predictions)
        mse = mean_squared_error(y_val, meta_pred)
        mae = mean_absolute_error(y_val, meta_pred)

        logger.info(f"Meta-model trained - MSE: {mse:.6f}, MAE: {mae:.6f}")

        return {"mse": mse, "mae": mae}

    def train_blending(
        self, X_val: np.ndarray, y_val: np.ndarray, optimization_metric: str = "mse"
    ):
        """
        Train blending ensemble by optimizing weights.

        Uses grid search to find optimal weights that minimize
        the specified metric on validation set.

        Args:
            X_val: Validation features
            y_val: Validation targets
            optimization_metric: 'mse' or 'mae'
        """
        if not self.base_models:
            raise ValueError("No base models added. Use add_base_model() first.")

        logger.info(
            f"Training blending ensemble with {len(self.base_models)} base models"
        )

        # Get base model predictions
        base_predictions = self._get_base_predictions(X_val)

        # Grid search for optimal weights
        best_weights = self._optimize_weights(
            base_predictions, y_val, optimization_metric
        )

        self.weights = dict(zip(self.model_names, best_weights))

        # Evaluate final ensemble
        ensemble_pred = self.predict_blending(X_val)
        mse = mean_squared_error(y_val, ensemble_pred)
        mae = mean_absolute_error(y_val, ensemble_pred)

        logger.info(f"Optimal weights found: {self.weights}")
        logger.info(f"Blending ensemble - MSE: {mse:.6f}, MAE: {mae:.6f}")

        return {"mse": mse, "mae": mae, "weights": self.weights}

    def _optimize_weights(
        self, base_predictions: np.ndarray, y_true: np.ndarray, metric: str = "mse"
    ) -> List[float]:
        """
        Find optimal weights using grid search.

        Searches over weight combinations that sum to 1.0.
        """
        n_models = len(self.model_names)
        best_score = float("inf")
        best_weights = [1.0 / n_models] * n_models

        # Grid search resolution
        steps = 11  # 0.0, 0.1, 0.2, ..., 1.0

        # Generate weight combinations
        from itertools import product

        weight_grid = np.linspace(0, 1, steps)

        for weights in product(weight_grid, repeat=n_models):
            # Ensure weights sum to 1.0
            weights = np.array(weights)
            weight_sum = weights.sum()
            if weight_sum == 0:
                continue
            weights = weights / weight_sum

            # Calculate ensemble prediction
            ensemble_pred = (base_predictions * weights).sum(axis=1)

            # Calculate metric
            if metric == "mse":
                score = mean_squared_error(y_true, ensemble_pred)
            else:  # mae
                score = mean_absolute_error(y_true, ensemble_pred)

            # Update best
            if score < best_score:
                best_score = score
                best_weights = weights.tolist()

        return best_weights

    def _get_base_predictions(self, X: np.ndarray) -> np.ndarray:
        """
        Get predictions from all base models.

        Returns:
            Array of shape (n_samples, n_models)
        """
        predictions = []

        for name in self.model_names:
            model = self.base_models[name]

            # Handle different model types
            try:
                pred = model.predict(X)
                # Ensure 1D array
                if len(pred.shape) > 1:
                    pred = pred.flatten()
                predictions.append(pred)
            except Exception as e:
                logger.error(f"Error getting predictions from {name}: {e}")
                raise

        return np.column_stack(predictions)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make ensemble prediction based on ensemble method.

        Args:
            X: Input features

        Returns:
            Ensemble predictions
        """
        if self.ensemble_method == "stacking":
            return self.predict_stacking(X)
        elif self.ensemble_method == "blending":
            return self.predict_blending(X)
        else:  # voting
            return self.predict_voting(X)

    def predict_stacking(self, X: np.ndarray) -> np.ndarray:
        """Predict using stacking (meta-model)."""
        if self.meta_model is None:
            raise ValueError("Meta-model not trained. Call train_stacking() first.")

        base_predictions = self._get_base_predictions(X)
        return self.meta_model.predict(base_predictions)

    def predict_blending(self, X: np.ndarray) -> np.ndarray:
        """Predict using weighted blending."""
        if not self.weights:
            raise ValueError("Weights not set. Call train_blending() or set manually.")

        base_predictions = self._get_base_predictions(X)
        weights = np.array([self.weights[name] for name in self.model_names])

        return (base_predictions * weights).sum(axis=1)

    def predict_voting(self, X: np.ndarray) -> np.ndarray:
        """Predict using simple voting (equal weights)."""
        base_predictions = self._get_base_predictions(X)
        return base_predictions.mean(axis=1)

    def update_weights_dynamic(
        self, X_recent: np.ndarray, y_recent: np.ndarray, window_size: int = 100
    ):
        """
        Update weights based on recent performance.

        Adjusts model weights based on their performance on
        recent data, giving more weight to better-performing models.

        Args:
            X_recent: Recent features
            y_recent: Recent targets
            window_size: Number of recent samples to consider
        """
        if len(X_recent) < window_size:
            window_size = len(X_recent)

        # Use most recent data
        X_window = X_recent[-window_size:]
        y_window = y_recent[-window_size:]

        # Calculate performance for each model
        performances = {}
        for name in self.model_names:
            model = self.base_models[name]
            pred = model.predict(X_window)
            if len(pred.shape) > 1:
                pred = pred.flatten()

            # Use inverse MSE as performance score (higher is better)
            mse = mean_squared_error(y_window, pred)
            performances[name] = 1.0 / (mse + 1e-8)

        # Normalize to weights (sum to 1.0)
        total_performance = sum(performances.values())
        new_weights = {
            name: perf / total_performance for name, perf in performances.items()
        }

        self.weights = new_weights
        self.performance_history.append(
            {"performances": performances, "weights": new_weights}
        )

        logger.info(f"Updated dynamic weights: {self.weights}")

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate ensemble and individual models.

        Returns:
            Dictionary with metrics for ensemble and base models
        """
        results = {}

        # Ensemble prediction
        ensemble_pred = self.predict(X_test)
        results["ensemble"] = {
            "mse": mean_squared_error(y_test, ensemble_pred),
            "mae": mean_absolute_error(y_test, ensemble_pred),
            "rmse": np.sqrt(mean_squared_error(y_test, ensemble_pred)),
        }

        # Individual model predictions
        for name in self.model_names:
            model = self.base_models[name]
            pred = model.predict(X_test)
            if len(pred.shape) > 1:
                pred = pred.flatten()

            results[name] = {
                "mse": mean_squared_error(y_test, pred),
                "mae": mean_absolute_error(y_test, pred),
                "rmse": np.sqrt(mean_squared_error(y_test, pred)),
            }

        return results

    def get_model_contributions(self, X: np.ndarray) -> pd.DataFrame:
        """
        Get individual model contributions to ensemble prediction.

        Returns:
            DataFrame with columns for each model's prediction and final ensemble
        """
        base_predictions = self._get_base_predictions(X)
        ensemble_pred = self.predict(X)

        df = pd.DataFrame(
            base_predictions, columns=[f"{name}_pred" for name in self.model_names]
        )
        df["ensemble_pred"] = ensemble_pred

        # Add weights if using blending
        if self.ensemble_method == "blending":
            for name in self.model_names:
                df[f"{name}_weight"] = self.weights[name]

        return df

    def save(self, path: Union[str, Path]):
        """Save ensemble predictor to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save ensemble configuration
        ensemble_config = {
            "ensemble_method": self.ensemble_method,
            "meta_model_type": self.meta_model_type,
            "weights": self.weights,
            "model_names": self.model_names,
            "meta_model": self.meta_model,
            "performance_history": self.performance_history,
        }

        joblib.dump(ensemble_config, path)
        logger.info(f"Ensemble predictor saved to {path}")

    def load(self, path: Union[str, Path]):
        """Load ensemble predictor from disk."""
        path = Path(path)

        ensemble_config = joblib.load(path)
        self.ensemble_method = ensemble_config["ensemble_method"]
        self.meta_model_type = ensemble_config["meta_model_type"]
        self.weights = ensemble_config["weights"]
        self.model_names = ensemble_config["model_names"]
        self.meta_model = ensemble_config["meta_model"]
        self.performance_history = ensemble_config.get("performance_history", [])

        logger.info(f"Ensemble predictor loaded from {path}")


class EnsembleBuilder:
    """
    Helper class to build ensemble from scratch.

    Simplifies the process of:
    1. Training base models
    2. Collecting predictions
    3. Training ensemble
    """

    def __init__(self, ensemble_method: str = "stacking"):
        """
        Initialize ensemble builder.

        Args:
            ensemble_method: 'stacking', 'blending', or 'voting'
        """
        self.ensemble_method = ensemble_method
        self.base_models = {}
        self.trained_models = {}

    def add_lightgbm(self, name: str = "lgbm", params: Optional[Dict] = None):
        """Add LightGBM to ensemble."""
        if not LIGHTGBM_AVAILABLE:
            raise ImportError(
                "LightGBM not available. Install with: pip install lightgbm"
            )

        default_params = {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "feature_fraction": 0.9,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "verbose": -1,
        }

        if params:
            default_params.update(params)

        self.base_models[name] = ("lightgbm", default_params)

    def add_xgboost(self, name: str = "xgb", params: Optional[Dict] = None):
        """Add XGBoost to ensemble."""
        if not XGBOOST_AVAILABLE:
            raise ImportError(
                "XGBoost not available. Install with: pip install xgboost"
            )

        default_params = {
            "objective": "reg:squarederror",
            "max_depth": 6,
            "learning_rate": 0.1,
            "n_estimators": 100,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
        }

        if params:
            default_params.update(params)

        self.base_models[name] = ("xgboost", default_params)

    def add_lstm(
        self,
        name: str = "lstm",
        sequence_length: int = 24,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
    ):
        """Add LSTM to ensemble."""
        if not LSTM_AVAILABLE:
            raise ImportError("LSTM not available. Install PyTorch first.")

        params = {
            "sequence_length": sequence_length,
            "hidden_size": hidden_size,
            "num_layers": num_layers,
            "dropout": dropout,
        }

        self.base_models[name] = ("lstm", params)

    def train_all(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
    ):
        """
        Train all base models.

        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
        """
        logger.info(f"Training {len(self.base_models)} base models...")

        for name, (model_type, params) in self.base_models.items():
            logger.info(f"Training {name} ({model_type})...")

            if model_type == "lightgbm":
                model = lgb.LGBMRegressor(**params)
                model.fit(
                    X_train,
                    y_train,
                    eval_set=[(X_val, y_val)],
                    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(50)],
                )

            elif model_type == "xgboost":
                model = xgb.XGBRegressor(**params)
                # Handle different XGBoost versions
                try:
                    # XGBoost >= 2.0
                    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=50)
                except TypeError:
                    # XGBoost < 2.0
                    model.fit(
                        X_train,
                        y_train,
                        eval_set=[(X_val, y_val)],
                        early_stopping_rounds=50,
                        verbose=50,
                    )

            elif model_type == "lstm":
                from .lstm_predictor import LSTMPredictor

                model = LSTMPredictor(
                    model_type="lstm",
                    sequence_length=params["sequence_length"],
                    hidden_size=params["hidden_size"],
                    num_layers=params["num_layers"],
                    dropout=params["dropout"],
                )
                model.train(X_train, y_train, X_val, y_val, epochs=100)

            else:
                raise ValueError(f"Unknown model type: {model_type}")

            self.trained_models[name] = model
            logger.info(f"✓ {name} trained successfully")

        logger.info(f"All {len(self.trained_models)} base models trained")

    def build_ensemble(
        self, X_val: np.ndarray, y_val: np.ndarray, meta_model_type: str = "ridge"
    ) -> EnsemblePredictor:
        """
        Build ensemble from trained models.

        Args:
            X_val: Validation features for meta-training
            y_val: Validation targets for meta-training
            meta_model_type: Meta-model type for stacking

        Returns:
            Trained EnsemblePredictor
        """
        if not self.trained_models:
            raise ValueError("No trained models. Call train_all() first.")

        # Create ensemble
        ensemble = EnsemblePredictor(
            ensemble_method=self.ensemble_method, meta_model_type=meta_model_type
        )

        # Add base models
        for name, model in self.trained_models.items():
            ensemble.add_base_model(name, model)

        # Train ensemble
        if self.ensemble_method == "stacking":
            ensemble.train_stacking(None, None, X_val, y_val)
        elif self.ensemble_method == "blending":
            ensemble.train_blending(X_val, y_val)
        # voting needs no training

        return ensemble
