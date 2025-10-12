"""
Tests for Ensemble Predictor Module (Phase 3.3)

Tests ensemble learning functionality including:
- Stacking ensemble
- Blending ensemble
- Voting ensemble
- Dynamic weight adjustment
- Model evaluation

Author: Proratio Team
Date: 2025-10-11
Phase: 3.3 - Ensemble Learning
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor

# Try to import ensemble modules
try:
    from proratio_quantlab.ml.ensemble_predictor import (
        EnsemblePredictor,
        EnsembleBuilder,
    )

    ENSEMBLE_AVAILABLE = True
except ImportError:
    ENSEMBLE_AVAILABLE = False

# Try to import base model libraries
try:
    import lightgbm as lgb

    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    import xgboost as xgb

    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_regression_data():
    """Create sample regression data for testing."""
    np.random.seed(42)
    n_samples = 500
    n_features = 10

    X = np.random.randn(n_samples, n_features)
    # True relationship: y = X @ weights + noise
    weights = np.random.randn(n_features)
    y = X @ weights + np.random.randn(n_samples) * 0.1

    # Split into train/val/test
    train_size = int(0.7 * n_samples)
    val_size = int(0.15 * n_samples)

    X_train = X[:train_size]
    y_train = y[:train_size]

    X_val = X[train_size : train_size + val_size]
    y_val = y[train_size : train_size + val_size]

    X_test = X[train_size + val_size :]
    y_test = y[train_size + val_size :]

    return (X_train, y_train), (X_val, y_val), (X_test, y_test)


@pytest.fixture
def simple_base_models():
    """Create simple sklearn models for testing."""
    from sklearn.linear_model import LinearRegression, Ridge

    models = {
        "linear": LinearRegression(),
        "ridge": Ridge(alpha=1.0),
        "rf": RandomForestRegressor(n_estimators=10, max_depth=3, random_state=42),
    }

    return models


# ============================================================================
# Test EnsemblePredictor - Initialization
# ============================================================================


@pytest.mark.skipif(not ENSEMBLE_AVAILABLE, reason="Requires ensemble modules")
class TestEnsemblePredictorInit:
    """Test ensemble predictor initialization."""

    def test_initialization_stacking(self):
        """Test stacking ensemble initialization."""
        ensemble = EnsemblePredictor(
            ensemble_method="stacking", meta_model_type="ridge"
        )

        assert ensemble.ensemble_method == "stacking"
        assert ensemble.meta_model_type == "ridge"
        assert isinstance(ensemble.meta_model, Ridge)
        assert len(ensemble.base_models) == 0

    def test_initialization_blending(self):
        """Test blending ensemble initialization."""
        ensemble = EnsemblePredictor(ensemble_method="blending")

        assert ensemble.ensemble_method == "blending"
        assert ensemble.meta_model is None
        assert len(ensemble.weights) == 0

    def test_initialization_voting(self):
        """Test voting ensemble initialization."""
        ensemble = EnsemblePredictor(ensemble_method="voting")

        assert ensemble.ensemble_method == "voting"
        assert ensemble.meta_model is None

    def test_invalid_ensemble_method(self):
        """Test invalid ensemble method raises error."""
        with pytest.raises(ValueError, match="ensemble_method must be one of"):
            EnsemblePredictor(ensemble_method="invalid")

    def test_invalid_meta_model_type(self):
        """Test invalid meta-model type raises error."""
        with pytest.raises(ValueError, match="Unknown meta_model_type"):
            EnsemblePredictor(ensemble_method="stacking", meta_model_type="invalid")


# ============================================================================
# Test EnsemblePredictor - Base Model Management
# ============================================================================


@pytest.mark.skipif(not ENSEMBLE_AVAILABLE, reason="Requires ensemble modules")
class TestEnsembleBaseModels:
    """Test base model management."""

    def test_add_base_model(self, simple_base_models):
        """Test adding base models."""
        ensemble = EnsemblePredictor(ensemble_method="stacking")

        for name, model in simple_base_models.items():
            ensemble.add_base_model(name, model, weight=1.0)

        assert len(ensemble.base_models) == 3
        assert "linear" in ensemble.base_models
        assert "ridge" in ensemble.base_models
        assert "rf" in ensemble.base_models

    def test_model_names_tracking(self, simple_base_models):
        """Test model names are tracked correctly."""
        ensemble = EnsemblePredictor(ensemble_method="stacking")

        ensemble.add_base_model("model1", simple_base_models["linear"])
        ensemble.add_base_model("model2", simple_base_models["ridge"])

        assert ensemble.model_names == ["model1", "model2"]

    def test_weights_tracking(self, simple_base_models):
        """Test weights are tracked for blending."""
        ensemble = EnsemblePredictor(ensemble_method="blending")

        ensemble.add_base_model("model1", simple_base_models["linear"], weight=0.6)
        ensemble.add_base_model("model2", simple_base_models["ridge"], weight=0.4)

        assert ensemble.weights["model1"] == 0.6
        assert ensemble.weights["model2"] == 0.4


# ============================================================================
# Test EnsemblePredictor - Stacking
# ============================================================================


@pytest.mark.skipif(not ENSEMBLE_AVAILABLE, reason="Requires ensemble modules")
class TestStackingEnsemble:
    """Test stacking ensemble functionality."""

    def test_train_stacking(self, sample_regression_data, simple_base_models):
        """Test stacking ensemble training."""
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = sample_regression_data

        # Train base models
        for model in simple_base_models.values():
            model.fit(X_train, y_train)

        # Create ensemble
        ensemble = EnsemblePredictor(
            ensemble_method="stacking", meta_model_type="ridge"
        )
        for name, model in simple_base_models.items():
            ensemble.add_base_model(name, model)

        # Train stacking
        metrics = ensemble.train_stacking(X_train, y_train, X_val, y_val)

        assert "mse" in metrics
        assert "mae" in metrics
        assert metrics["mse"] > 0
        assert metrics["mae"] > 0

    def test_predict_stacking(self, sample_regression_data, simple_base_models):
        """Test stacking predictions."""
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = sample_regression_data

        # Train base models
        for model in simple_base_models.values():
            model.fit(X_train, y_train)

        # Create and train ensemble
        ensemble = EnsemblePredictor(
            ensemble_method="stacking", meta_model_type="ridge"
        )
        for name, model in simple_base_models.items():
            ensemble.add_base_model(name, model)

        ensemble.train_stacking(X_train, y_train, X_val, y_val)

        # Make predictions
        predictions = ensemble.predict(X_test)

        assert len(predictions) == len(X_test)
        assert predictions.dtype == np.float64

    def test_stacking_different_meta_models(
        self, sample_regression_data, simple_base_models
    ):
        """Test stacking with different meta-models."""
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = sample_regression_data

        # Train base models
        for model in simple_base_models.values():
            model.fit(X_train, y_train)

        meta_models = ["ridge", "lasso", "rf"]
        results = {}

        for meta_type in meta_models:
            ensemble = EnsemblePredictor(
                ensemble_method="stacking", meta_model_type=meta_type
            )
            for name, model in simple_base_models.items():
                ensemble.add_base_model(name, model)

            metrics = ensemble.train_stacking(X_train, y_train, X_val, y_val)
            results[meta_type] = metrics["mse"]

        # All meta-models should produce valid results
        assert all(mse > 0 for mse in results.values())


# ============================================================================
# Test EnsemblePredictor - Blending
# ============================================================================


@pytest.mark.skipif(not ENSEMBLE_AVAILABLE, reason="Requires ensemble modules")
class TestBlendingEnsemble:
    """Test blending ensemble functionality."""

    def test_train_blending(self, sample_regression_data, simple_base_models):
        """Test blending ensemble training."""
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = sample_regression_data

        # Train base models
        for model in simple_base_models.values():
            model.fit(X_train, y_train)

        # Create ensemble
        ensemble = EnsemblePredictor(ensemble_method="blending")
        for name, model in simple_base_models.items():
            ensemble.add_base_model(name, model)

        # Train blending
        metrics = ensemble.train_blending(X_val, y_val, optimization_metric="mse")

        assert "mse" in metrics
        assert "mae" in metrics
        assert "weights" in metrics
        assert sum(metrics["weights"].values()) == pytest.approx(1.0, abs=1e-6)

    def test_predict_blending(self, sample_regression_data, simple_base_models):
        """Test blending predictions."""
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = sample_regression_data

        # Train base models
        for model in simple_base_models.values():
            model.fit(X_train, y_train)

        # Create and train ensemble
        ensemble = EnsemblePredictor(ensemble_method="blending")
        for name, model in simple_base_models.items():
            ensemble.add_base_model(name, model)

        ensemble.train_blending(X_val, y_val)

        # Make predictions
        predictions = ensemble.predict(X_test)

        assert len(predictions) == len(X_test)
        assert predictions.dtype == np.float64

    def test_manual_weights(self, sample_regression_data, simple_base_models):
        """Test blending with manually set weights."""
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = sample_regression_data

        # Train base models
        for model in simple_base_models.values():
            model.fit(X_train, y_train)

        # Create ensemble with manual weights
        ensemble = EnsemblePredictor(ensemble_method="blending")
        ensemble.add_base_model("model1", simple_base_models["linear"], weight=0.5)
        ensemble.add_base_model("model2", simple_base_models["ridge"], weight=0.3)
        ensemble.add_base_model("model3", simple_base_models["rf"], weight=0.2)

        # Predict without training (uses manual weights)
        predictions = ensemble.predict(X_test)

        assert len(predictions) == len(X_test)


# ============================================================================
# Test EnsemblePredictor - Voting
# ============================================================================


@pytest.mark.skipif(not ENSEMBLE_AVAILABLE, reason="Requires ensemble modules")
class TestVotingEnsemble:
    """Test voting ensemble functionality."""

    def test_predict_voting(self, sample_regression_data, simple_base_models):
        """Test voting predictions (equal weights)."""
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = sample_regression_data

        # Train base models
        for model in simple_base_models.values():
            model.fit(X_train, y_train)

        # Create ensemble
        ensemble = EnsemblePredictor(ensemble_method="voting")
        for name, model in simple_base_models.items():
            ensemble.add_base_model(name, model)

        # Make predictions
        predictions = ensemble.predict(X_test)

        # Voting should be mean of all predictions
        base_preds = np.column_stack(
            [model.predict(X_test) for model in simple_base_models.values()]
        )
        expected = base_preds.mean(axis=1)

        np.testing.assert_array_almost_equal(predictions, expected)


# ============================================================================
# Test EnsemblePredictor - Dynamic Weighting
# ============================================================================


@pytest.mark.skipif(not ENSEMBLE_AVAILABLE, reason="Requires ensemble modules")
class TestDynamicWeighting:
    """Test dynamic weight adjustment."""

    def test_update_weights_dynamic(self, sample_regression_data, simple_base_models):
        """Test dynamic weight updates based on recent performance."""
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = sample_regression_data

        # Train base models
        for model in simple_base_models.values():
            model.fit(X_train, y_train)

        # Create ensemble
        ensemble = EnsemblePredictor(ensemble_method="blending")
        for name, model in simple_base_models.items():
            ensemble.add_base_model(name, model)

        # Initial weights
        initial_weights = ensemble.weights.copy()

        # Update weights based on validation data
        ensemble.update_weights_dynamic(X_val, y_val, window_size=50)

        # Weights should change
        assert ensemble.weights != initial_weights
        # Weights should sum to 1
        assert sum(ensemble.weights.values()) == pytest.approx(1.0, abs=1e-6)

    def test_performance_history_tracking(
        self, sample_regression_data, simple_base_models
    ):
        """Test performance history is tracked."""
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = sample_regression_data

        # Train base models
        for model in simple_base_models.values():
            model.fit(X_train, y_train)

        # Create ensemble
        ensemble = EnsemblePredictor(ensemble_method="blending")
        for name, model in simple_base_models.items():
            ensemble.add_base_model(name, model)

        # Update weights twice
        ensemble.update_weights_dynamic(X_val, y_val, window_size=50)
        ensemble.update_weights_dynamic(X_test, y_test, window_size=50)

        assert len(ensemble.performance_history) == 2
        assert "performances" in ensemble.performance_history[0]
        assert "weights" in ensemble.performance_history[0]


# ============================================================================
# Test EnsemblePredictor - Evaluation
# ============================================================================


@pytest.mark.skipif(not ENSEMBLE_AVAILABLE, reason="Requires ensemble modules")
class TestEnsembleEvaluation:
    """Test ensemble evaluation functionality."""

    def test_evaluate_all_models(self, sample_regression_data, simple_base_models):
        """Test evaluation of ensemble and base models."""
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = sample_regression_data

        # Train base models
        for model in simple_base_models.values():
            model.fit(X_train, y_train)

        # Create and train ensemble
        ensemble = EnsemblePredictor(ensemble_method="voting")
        for name, model in simple_base_models.items():
            ensemble.add_base_model(name, model)

        # Evaluate
        results = ensemble.evaluate(X_test, y_test)

        # Check ensemble results
        assert "ensemble" in results
        assert "mse" in results["ensemble"]
        assert "mae" in results["ensemble"]
        assert "rmse" in results["ensemble"]

        # Check individual model results
        for name in simple_base_models.keys():
            assert name in results
            assert "mse" in results[name]
            assert "mae" in results[name]
            assert "rmse" in results[name]

    def test_get_model_contributions(self, sample_regression_data, simple_base_models):
        """Test getting individual model contributions."""
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = sample_regression_data

        # Train base models
        for model in simple_base_models.values():
            model.fit(X_train, y_train)

        # Create ensemble
        ensemble = EnsemblePredictor(ensemble_method="blending")
        for name, model in simple_base_models.items():
            ensemble.add_base_model(name, model, weight=1.0 / 3)

        # Get contributions
        contributions = ensemble.get_model_contributions(X_test)

        assert isinstance(contributions, pd.DataFrame)
        assert "ensemble_pred" in contributions.columns
        assert "linear_pred" in contributions.columns
        assert "ridge_pred" in contributions.columns
        assert "rf_pred" in contributions.columns
        assert len(contributions) == len(X_test)


# ============================================================================
# Test EnsemblePredictor - Save/Load
# ============================================================================


@pytest.mark.skipif(not ENSEMBLE_AVAILABLE, reason="Requires ensemble modules")
class TestEnsemblePersistence:
    """Test ensemble save/load functionality."""

    def test_save_and_load(self, sample_regression_data, simple_base_models):
        """Test saving and loading ensemble."""
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = sample_regression_data

        # Train base models
        for model in simple_base_models.values():
            model.fit(X_train, y_train)

        # Create ensemble
        ensemble = EnsemblePredictor(ensemble_method="blending")
        for name, model in simple_base_models.items():
            ensemble.add_base_model(name, model)
        ensemble.train_blending(X_val, y_val)

        # Save
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp:
            ensemble.save(tmp.name)

            # Create new ensemble and load
            ensemble2 = EnsemblePredictor(ensemble_method="blending")
            ensemble2.load(tmp.name)

            # Check loaded attributes
            assert ensemble2.ensemble_method == ensemble.ensemble_method
            assert ensemble2.weights == ensemble.weights
            assert ensemble2.model_names == ensemble.model_names

            # Clean up
            Path(tmp.name).unlink()


# ============================================================================
# Test EnsembleBuilder
# ============================================================================


@pytest.mark.skipif(not ENSEMBLE_AVAILABLE, reason="Requires ensemble modules")
class TestEnsembleBuilder:
    """Test ensemble builder functionality."""

    def test_builder_initialization(self):
        """Test builder initialization."""
        builder = EnsembleBuilder(ensemble_method="stacking")

        assert builder.ensemble_method == "stacking"
        assert len(builder.base_models) == 0
        assert len(builder.trained_models) == 0

    @pytest.mark.skipif(not LIGHTGBM_AVAILABLE, reason="Requires LightGBM")
    def test_add_lightgbm(self):
        """Test adding LightGBM to builder."""
        builder = EnsembleBuilder()
        builder.add_lightgbm(name="lgbm_custom", params={"num_leaves": 50})

        assert "lgbm_custom" in builder.base_models
        assert builder.base_models["lgbm_custom"][0] == "lightgbm"
        assert builder.base_models["lgbm_custom"][1]["num_leaves"] == 50

    @pytest.mark.skipif(not XGBOOST_AVAILABLE, reason="Requires XGBoost")
    def test_add_xgboost(self):
        """Test adding XGBoost to builder."""
        builder = EnsembleBuilder()
        builder.add_xgboost(name="xgb_custom", params={"max_depth": 8})

        assert "xgb_custom" in builder.base_models
        assert builder.base_models["xgb_custom"][0] == "xgboost"
        assert builder.base_models["xgb_custom"][1]["max_depth"] == 8


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
