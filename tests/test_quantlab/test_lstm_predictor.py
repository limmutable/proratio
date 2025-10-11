"""
Unit tests for LSTM Predictor Module (Phase 3.2)

Tests the LSTM/GRU models, data pipeline, and training functionality
for cryptocurrency price prediction.

NOTE: These tests require PyTorch which is a large dependency (~2GB).
Install separately: pip install torch==2.8.0
Most tests will be skipped if PyTorch is not available.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Try importing PyTorch
try:
    import torch
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    torch = None

# Try importing LSTM modules (will fail if PyTorch not available)
try:
    from proratio_quantlab.ml.lstm_predictor import (
        LSTMModel, GRUModel, LSTMPredictor, TimeSeriesDataset
    )
    LSTM_MODULES_AVAILABLE = True
except ImportError:
    LSTM_MODULES_AVAILABLE = False

from proratio_quantlab.ml.lstm_data_pipeline import LSTMDataPipeline, prepare_lstm_data


@pytest.fixture
def sample_time_series_data():
    """Create sample time-series data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=500, freq='4h')

    # Generate realistic crypto-like price data
    np.random.seed(42)
    base_price = 50000
    returns = np.random.normal(0.0001, 0.02, 500)
    prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, 500)),
        'high': prices * (1 + np.random.uniform(0.001, 0.02, 500)),
        'low': prices * (1 + np.random.uniform(-0.02, -0.001, 500)),
        'close': prices,
        'volume': np.random.uniform(1000, 10000, 500)
    })

    # Add some simple features
    df['rsi_14'] = np.random.uniform(30, 70, 500)
    df['ema_9'] = prices * 0.98
    df['ema_21'] = prices * 0.95
    df['volume_sma'] = df['volume'].rolling(20).mean().fillna(df['volume'])

    # Add target
    df['target_return'] = ((df['close'].shift(-4) - df['close']) / df['close']) * 100

    return df.dropna()


@pytest.mark.skipif(not LSTM_MODULES_AVAILABLE, reason="Requires PyTorch")
class TestTimeSeriesDataset:
    """Test TimeSeriesDataset class"""

    def test_initialization(self):
        """Test dataset initialization"""
        data = np.random.randn(100, 5)
        targets = np.random.randn(100)

        dataset = TimeSeriesDataset(data, targets, sequence_length=10)

        assert len(dataset) == 90  # 100 - 10
        assert dataset.sequence_length == 10

    def test_getitem(self):
        """Test getting a single item"""
        data = np.random.randn(100, 5)
        targets = np.random.randn(100)

        dataset = TimeSeriesDataset(data, targets, sequence_length=10)

        X, y = dataset[0]

        assert X.shape == (10, 5)  # sequence_length, n_features
        assert y.shape == ()  # scalar

    def test_all_items_accessible(self):
        """Test that all items in dataset can be accessed"""
        data = np.random.randn(100, 5)
        targets = np.random.randn(100)

        dataset = TimeSeriesDataset(data, targets, sequence_length=10)

        for i in range(len(dataset)):
            X, y = dataset[i]
            assert X.shape == (10, 5)


@pytest.mark.skipif(not LSTM_MODULES_AVAILABLE, reason="Requires PyTorch")
class TestLSTMModel:
    """Test LSTM model architecture"""

    def test_initialization(self):
        """Test LSTM model initialization"""
        model = LSTMModel(input_size=10, hidden_size=64, num_layers=2)

        assert model.input_size == 10
        assert model.hidden_size == 64
        assert model.num_layers == 2

    def test_forward_pass(self):
        """Test forward pass through LSTM"""
        model = LSTMModel(input_size=10, hidden_size=64, num_layers=2)
        model.eval()

        # Batch of sequences
        x = torch.randn(32, 20, 10)  # batch_size, sequence_length, input_size
        output = model(x)

        assert output.shape == (32, 1)  # batch_size, output_size

    def test_output_no_nan(self):
        """Test that forward pass doesn't produce NaN"""
        model = LSTMModel(input_size=10, hidden_size=64, num_layers=2)
        model.eval()

        x = torch.randn(8, 20, 10)
        output = model(x)

        assert not torch.isnan(output).any()


@pytest.mark.skipif(not LSTM_MODULES_AVAILABLE, reason="Requires PyTorch")
class TestGRUModel:
    """Test GRU model architecture"""

    def test_initialization(self):
        """Test GRU model initialization"""
        model = GRUModel(input_size=10, hidden_size=64, num_layers=2)

        assert model.input_size == 10
        assert model.hidden_size == 64
        assert model.num_layers == 2

    def test_forward_pass(self):
        """Test forward pass through GRU"""
        model = GRUModel(input_size=10, hidden_size=64, num_layers=2)
        model.eval()

        x = torch.randn(32, 20, 10)
        output = model(x)

        assert output.shape == (32, 1)

    def test_gru_faster_than_lstm(self):
        """GRU should have fewer parameters than LSTM"""
        lstm = LSTMModel(input_size=10, hidden_size=64, num_layers=2)
        gru = GRUModel(input_size=10, hidden_size=64, num_layers=2)

        lstm_params = sum(p.numel() for p in lstm.parameters())
        gru_params = sum(p.numel() for p in gru.parameters())

        # GRU typically has ~75% of LSTM parameters
        assert gru_params < lstm_params


@pytest.mark.skipif(not LSTM_MODULES_AVAILABLE, reason="Requires PyTorch")
class TestLSTMPredictor:
    """Test LSTMPredictor class"""

    def test_initialization(self):
        """Test predictor initialization"""
        predictor = LSTMPredictor(model_type='lstm', sequence_length=24)

        assert predictor.model_type == 'lstm'
        assert predictor.sequence_length == 24
        assert predictor.device in ['cpu', 'cuda']

    def test_preprocess_data(self, sample_time_series_data):
        """Test data preprocessing"""
        predictor = LSTMPredictor()

        X, y = predictor.preprocess_data(
            sample_time_series_data,
            target_column='target_return',
            fit_scaler=True
        )

        assert X.shape[0] == len(sample_time_series_data)
        assert X.shape[1] > 0  # Has features
        assert len(y) == len(sample_time_series_data)

    def test_train_basic(self, sample_time_series_data):
        """Test basic training functionality"""
        predictor = LSTMPredictor(
            model_type='lstm',
            sequence_length=10,
            hidden_size=32,
            num_layers=1
        )

        X, y = predictor.preprocess_data(
            sample_time_series_data,
            target_column='target_return',
            fit_scaler=True
        )

        # Train for just 2 epochs (quick test)
        history = predictor.train(
            X[:300], y[:300],
            X[300:], y[300:],
            epochs=2,
            verbose=False
        )

        assert 'train_loss' in history
        assert 'val_loss' in history
        assert len(history['train_loss']) > 0

    def test_predict(self, sample_time_series_data):
        """Test prediction functionality"""
        predictor = LSTMPredictor(
            model_type='lstm',
            sequence_length=10,
            hidden_size=32,
            num_layers=1
        )

        X, y = predictor.preprocess_data(
            sample_time_series_data,
            target_column='target_return',
            fit_scaler=True
        )

        # Train briefly
        predictor.train(X[:300], y[:300], epochs=2, verbose=False)

        # Predict
        predictions = predictor.predict(X[300:400])

        # Account for sequence_length reduction
        expected_length = 400 - 300 - predictor.sequence_length
        assert len(predictions) == expected_length
        assert not np.isnan(predictions).any()

    def test_save_and_load(self, sample_time_series_data, tmp_path):
        """Test model saving and loading"""
        predictor = LSTMPredictor(
            model_type='lstm',
            sequence_length=10,
            hidden_size=32,
            num_layers=1
        )

        X, y = predictor.preprocess_data(
            sample_time_series_data,
            target_column='target_return',
            fit_scaler=True
        )

        # Train briefly
        predictor.train(X[:300], y[:300], epochs=2, verbose=False)

        # Save
        save_path = tmp_path / "test_model.pkl"
        predictor.save(str(save_path))

        assert save_path.exists()

        # Load into new predictor
        predictor2 = LSTMPredictor()
        predictor2.load(str(save_path))

        assert predictor2.model_type == predictor.model_type
        assert predictor2.sequence_length == predictor.sequence_length
        assert predictor2.hidden_size == predictor.hidden_size


class TestLSTMDataPipeline:
    """Test LSTM data pipeline"""

    def test_initialization(self):
        """Test pipeline initialization"""
        pipeline = LSTMDataPipeline(
            train_ratio=0.7,
            val_ratio=0.15,
            test_ratio=0.15
        )

        assert pipeline.train_ratio == 0.7
        assert pipeline.val_ratio == 0.15
        assert pipeline.test_ratio == 0.15

    def test_prepare_data(self, sample_time_series_data):
        """Test data preparation"""
        pipeline = LSTMDataPipeline(min_samples=100)  # Lower threshold for testing

        df_clean, feature_cols = pipeline.prepare_data(
            sample_time_series_data,
            target_column='target_return'
        )

        assert len(df_clean) > 0
        assert len(feature_cols) > 0
        assert 'target_return' not in feature_cols  # Target excluded from features

    def test_split_data(self, sample_time_series_data):
        """Test train/val/test splitting"""
        pipeline = LSTMDataPipeline(train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, min_samples=100)

        df_clean, feature_cols = pipeline.prepare_data(sample_time_series_data)
        df_train, df_val, df_test = pipeline.split_data(df_clean, feature_cols)

        total_samples = len(df_train) + len(df_val) + len(df_test)
        assert total_samples == len(df_clean)

        # Check approximate ratios
        assert abs(len(df_train) / total_samples - 0.7) < 0.05
        assert abs(len(df_val) / total_samples - 0.15) < 0.05
        assert abs(len(df_test) / total_samples - 0.15) < 0.05

    def test_get_arrays(self, sample_time_series_data):
        """Test array extraction"""
        pipeline = LSTMDataPipeline(min_samples=100)

        df_clean, feature_cols = pipeline.prepare_data(sample_time_series_data)
        X, y = pipeline.get_arrays(df_clean, feature_cols, target_column='target_return')

        assert X.shape[0] == len(df_clean)
        assert X.shape[1] == len(feature_cols)
        assert len(y) == len(df_clean)

    def test_prepare_lstm_data_convenience(self, sample_time_series_data):
        """Test convenience function"""
        (X_train, y_train), (X_val, y_val), (X_test, y_test), feature_cols = prepare_lstm_data(
            sample_time_series_data,
            target_column='target_return'
        )

        assert X_train.shape[0] > 0
        assert X_val.shape[0] > 0
        assert X_test.shape[0] > 0
        assert len(feature_cols) > 0


@pytest.mark.skipif(not LSTM_MODULES_AVAILABLE, reason="Requires PyTorch")
class TestLSTMIntegration:
    """Integration tests for LSTM workflow"""

    def test_full_pipeline(self, sample_time_series_data):
        """Test complete training and prediction pipeline"""
        # Prepare data
        (X_train, y_train), (X_val, y_val), (X_test, y_test), feature_cols = prepare_lstm_data(
            sample_time_series_data
        )

        # Create predictor
        predictor = LSTMPredictor(
            model_type='lstm',
            sequence_length=10,
            hidden_size=32,
            num_layers=1
        )

        # Preprocess
        X_train_scaled, _ = predictor.preprocess_data(
            pd.DataFrame(X_train, columns=feature_cols).assign(target_return=y_train),
            fit_scaler=True
        )

        X_test_scaled, _ = predictor.preprocess_data(
            pd.DataFrame(X_test, columns=feature_cols).assign(target_return=y_test),
            fit_scaler=False
        )

        # Train
        history = predictor.train(X_train_scaled, y_train, epochs=2, verbose=False)

        # Predict
        predictions = predictor.predict(X_test_scaled)

        # Verify
        assert len(predictions) > 0
        assert not np.isnan(predictions).any()
        assert 'train_loss' in history

    def test_gru_vs_lstm(self, sample_time_series_data):
        """Test that GRU and LSTM both work"""
        (X_train, y_train), _, _, feature_cols = prepare_lstm_data(
            sample_time_series_data
        )

        # LSTM
        lstm_predictor = LSTMPredictor(model_type='lstm', sequence_length=10, hidden_size=32)
        X_scaled, _ = lstm_predictor.preprocess_data(
            pd.DataFrame(X_train[:200], columns=feature_cols).assign(target_return=y_train[:200]),
            fit_scaler=True
        )
        lstm_history = lstm_predictor.train(X_scaled, y_train[:200], epochs=2, verbose=False)

        # GRU
        gru_predictor = LSTMPredictor(model_type='gru', sequence_length=10, hidden_size=32)
        X_scaled, _ = gru_predictor.preprocess_data(
            pd.DataFrame(X_train[:200], columns=feature_cols).assign(target_return=y_train[:200]),
            fit_scaler=True
        )
        gru_history = gru_predictor.train(X_scaled, y_train[:200], epochs=2, verbose=False)

        # Both should train successfully
        assert len(lstm_history['train_loss']) > 0
        assert len(gru_history['train_loss']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
