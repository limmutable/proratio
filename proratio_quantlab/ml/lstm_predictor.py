"""
LSTM Price Prediction Module for Phase 3.2

Implements LSTM/GRU neural networks for time-series price prediction
in cryptocurrency trading. Provides data preprocessing, model training,
and prediction interfaces compatible with FreqAI strategies.

Author: Proratio Team
Date: 2025-10-11
Phase: 3.2 - LSTM Price Prediction
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from typing import Tuple, Optional, Dict, List
import logging
from pathlib import Path
import joblib
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class TimeSeriesDataset(Dataset):
    """
    PyTorch Dataset for time-series data with sliding window approach.

    Creates sequences of historical data (X) and future targets (y) for training
    LSTM models on price prediction tasks.
    """

    def __init__(
        self,
        data: np.ndarray,
        targets: np.ndarray,
        sequence_length: int = 24,
        device: str = "cpu",
    ):
        """
        Initialize time-series dataset.

        Args:
            data: Feature data (n_samples, n_features)
            targets: Target values (n_samples,)
            sequence_length: Number of timesteps to look back
            device: 'cpu' or 'cuda'
        """
        self.data = torch.FloatTensor(data).to(device)
        self.targets = torch.FloatTensor(targets).to(device)
        self.sequence_length = sequence_length
        self.device = device

        # Calculate valid sample indices
        self.n_samples = len(data) - sequence_length

    def __len__(self) -> int:
        return self.n_samples

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Get a single sequence and its target.

        Returns:
            X: (sequence_length, n_features) tensor
            y: (1,) tensor
        """
        X = self.data[idx : idx + self.sequence_length]
        y = self.targets[idx + self.sequence_length]
        return X, y


class LSTMModel(nn.Module):
    """
    LSTM neural network for price prediction.

    Architecture:
    - LSTM layers with dropout for regularization
    - Fully connected layers for prediction
    - Supports both single-step and multi-step prediction
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        output_size: int = 1,
    ):
        """
        Initialize LSTM model.

        Args:
            input_size: Number of input features
            hidden_size: Number of LSTM hidden units
            num_layers: Number of LSTM layers
            dropout: Dropout rate for regularization
            output_size: Number of output predictions (1 for single-step)
        """
        super(LSTMModel, self).__init__()

        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
        )

        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_size // 2, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through LSTM model.

        Args:
            x: Input tensor (batch_size, sequence_length, input_size)

        Returns:
            Output tensor (batch_size, output_size)
        """
        # LSTM forward pass
        lstm_out, (h_n, c_n) = self.lstm(x)

        # Use last hidden state
        last_hidden = lstm_out[:, -1, :]

        # Fully connected layers
        out = self.fc1(last_hidden)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)

        return out


class GRUModel(nn.Module):
    """
    GRU neural network for price prediction.

    Alternative to LSTM with simpler architecture and faster training.
    Often performs similarly to LSTM with fewer parameters.
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        output_size: int = 1,
    ):
        """
        Initialize GRU model.

        Args:
            input_size: Number of input features
            hidden_size: Number of GRU hidden units
            num_layers: Number of GRU layers
            dropout: Dropout rate for regularization
            output_size: Number of output predictions
        """
        super(GRUModel, self).__init__()

        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size

        # GRU layers
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
        )

        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_size // 2, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through GRU model.

        Args:
            x: Input tensor (batch_size, sequence_length, input_size)

        Returns:
            Output tensor (batch_size, output_size)
        """
        # GRU forward pass
        gru_out, h_n = self.gru(x)

        # Use last hidden state
        last_hidden = gru_out[:, -1, :]

        # Fully connected layers
        out = self.fc1(last_hidden)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)

        return out


class LSTMPredictor:
    """
    LSTM-based price predictor with training and inference capabilities.

    Handles data preprocessing, model training, evaluation, and prediction
    for cryptocurrency price forecasting.
    """

    def __init__(
        self,
        model_type: str = "lstm",
        sequence_length: int = 24,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        learning_rate: float = 0.001,
        batch_size: int = 32,
        device: Optional[str] = None,
    ):
        """
        Initialize LSTM predictor.

        Args:
            model_type: 'lstm' or 'gru'
            sequence_length: Number of timesteps to look back
            hidden_size: Number of hidden units
            num_layers: Number of recurrent layers
            dropout: Dropout rate
            learning_rate: Learning rate for optimizer
            batch_size: Training batch size
            device: 'cpu', 'cuda', or None (auto-detect)
        """
        self.model_type = model_type
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.batch_size = batch_size

        # Auto-detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        logger.info(f"Using device: {self.device}")

        # Model and scaler (initialized during fit)
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.input_size = None

    def _create_model(self, input_size: int) -> nn.Module:
        """Create LSTM or GRU model based on configuration."""
        if self.model_type == "lstm":
            model = LSTMModel(
                input_size=input_size,
                hidden_size=self.hidden_size,
                num_layers=self.num_layers,
                dropout=self.dropout,
                output_size=1,
            )
        elif self.model_type == "gru":
            model = GRUModel(
                input_size=input_size,
                hidden_size=self.hidden_size,
                num_layers=self.num_layers,
                dropout=self.dropout,
                output_size=1,
            )
        else:
            raise ValueError(f"Unknown model_type: {self.model_type}")

        return model.to(self.device)

    def preprocess_data(
        self,
        dataframe: pd.DataFrame,
        target_column: str = "target_return",
        fit_scaler: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess dataframe for LSTM training/prediction.

        Args:
            dataframe: Input dataframe with features and target
            target_column: Name of target column
            fit_scaler: Whether to fit scaler (True for training, False for inference)

        Returns:
            X: Scaled feature array (n_samples, n_features)
            y: Target array (n_samples,)
        """
        # Store feature names
        if self.feature_names is None:
            feature_cols = [
                col
                for col in dataframe.columns
                if col
                not in [target_column, "date", "open", "high", "low", "close", "volume"]
            ]
            self.feature_names = feature_cols

        # Extract features and target
        X = dataframe[self.feature_names].values
        y = (
            dataframe[target_column].values
            if target_column in dataframe.columns
            else None
        )

        # Scale features
        if fit_scaler:
            X = self.scaler.fit_transform(X)
        else:
            X = self.scaler.transform(X)

        return X, y

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 100,
        early_stopping_patience: int = 10,
        verbose: bool = True,
    ) -> Dict[str, List[float]]:
        """
        Train LSTM model.

        Args:
            X_train: Training features (n_samples, n_features)
            y_train: Training targets (n_samples,)
            X_val: Validation features (optional)
            y_val: Validation targets (optional)
            epochs: Number of training epochs
            early_stopping_patience: Epochs to wait before early stopping
            verbose: Print training progress

        Returns:
            History dict with 'train_loss' and 'val_loss' lists
        """
        # Initialize model
        if self.model is None:
            self.input_size = X_train.shape[1]
            self.model = self._create_model(self.input_size)

        # Create datasets
        train_dataset = TimeSeriesDataset(
            X_train, y_train, self.sequence_length, self.device
        )
        train_loader = DataLoader(
            train_dataset, batch_size=self.batch_size, shuffle=True
        )

        val_loader = None
        if X_val is not None and y_val is not None:
            val_dataset = TimeSeriesDataset(
                X_val, y_val, self.sequence_length, self.device
            )
            val_loader = DataLoader(
                val_dataset, batch_size=self.batch_size, shuffle=False
            )

        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)

        # Training loop
        history = {"train_loss": [], "val_loss": []}
        best_val_loss = float("inf")
        patience_counter = 0

        for epoch in range(epochs):
            # Training
            self.model.train()
            train_losses = []

            for X_batch, y_batch in train_loader:
                optimizer.zero_grad()
                outputs = self.model(X_batch).squeeze()
                loss = criterion(outputs, y_batch)
                loss.backward()
                optimizer.step()
                train_losses.append(loss.item())

            avg_train_loss = np.mean(train_losses)
            history["train_loss"].append(avg_train_loss)

            # Validation
            if val_loader is not None:
                self.model.eval()
                val_losses = []

                with torch.no_grad():
                    for X_batch, y_batch in val_loader:
                        outputs = self.model(X_batch).squeeze()
                        loss = criterion(outputs, y_batch)
                        val_losses.append(loss.item())

                avg_val_loss = np.mean(val_losses)
                history["val_loss"].append(avg_val_loss)

                # Early stopping
                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1

                if patience_counter >= early_stopping_patience:
                    if verbose:
                        logger.info(f"Early stopping at epoch {epoch + 1}")
                    break

                if verbose and (epoch + 1) % 10 == 0:
                    logger.info(
                        f"Epoch {epoch + 1}/{epochs} - Train Loss: {avg_train_loss:.6f}, Val Loss: {avg_val_loss:.6f}"
                    )
            else:
                if verbose and (epoch + 1) % 10 == 0:
                    logger.info(
                        f"Epoch {epoch + 1}/{epochs} - Train Loss: {avg_train_loss:.6f}"
                    )

        return history

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions on new data.

        Args:
            X: Input features (n_samples, n_features)

        Returns:
            Predictions (n_samples - sequence_length,)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        self.model.eval()

        # Create dataset
        # Use dummy targets (zeros) since we only need predictions
        dummy_targets = np.zeros(len(X))
        dataset = TimeSeriesDataset(X, dummy_targets, self.sequence_length, self.device)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)

        predictions = []
        with torch.no_grad():
            for X_batch, _ in loader:
                outputs = self.model(X_batch).squeeze()
                # Handle both single sample and batch predictions
                output_np = outputs.cpu().numpy()
                if output_np.ndim == 0:
                    predictions.append(output_np.item())
                else:
                    predictions.extend(output_np)

        return np.array(predictions)

    def save(self, path: str):
        """Save model and scaler to disk."""
        save_dict = {
            "model_state_dict": self.model.state_dict(),
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "input_size": self.input_size,
            "config": {
                "model_type": self.model_type,
                "sequence_length": self.sequence_length,
                "hidden_size": self.hidden_size,
                "num_layers": self.num_layers,
                "dropout": self.dropout,
            },
        }

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(save_dict, path)
        logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load model and scaler from disk."""
        save_dict = joblib.load(path)

        # Restore configuration
        config = save_dict["config"]
        self.model_type = config["model_type"]
        self.sequence_length = config["sequence_length"]
        self.hidden_size = config["hidden_size"]
        self.num_layers = config["num_layers"]
        self.dropout = config["dropout"]

        # Restore scaler and features
        self.scaler = save_dict["scaler"]
        self.feature_names = save_dict["feature_names"]
        self.input_size = save_dict["input_size"]

        # Recreate and load model
        self.model = self._create_model(self.input_size)
        self.model.load_state_dict(save_dict["model_state_dict"])
        self.model.eval()

        logger.info(f"Model loaded from {path}")


# Example usage
if __name__ == "__main__":
    print("LSTM Predictor Module for Cryptocurrency Price Prediction")
    print("Use LSTMPredictor class for training and prediction")
    print("\nExample:")
    print("  predictor = LSTMPredictor(model_type='lstm', sequence_length=24)")
    print("  history = predictor.train(X_train, y_train, X_val, y_val)")
    print("  predictions = predictor.predict(X_test)")
