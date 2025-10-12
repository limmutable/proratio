"""
Feature Engineering Module for ML Trading Strategies

This module provides comprehensive feature engineering for machine learning
models in crypto trading, including technical indicators, derived features,
and market regime detection.

Author: Proratio Team
Date: 2025-10-11
Phase: 3.1 - FreqAI Integration
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Feature engineering for ML trading models.

    Generates technical indicators, derived features, and market regime
    indicators suitable for machine learning models.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize feature engineer.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.feature_list = []

    def add_all_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Add all features to dataframe.

        Args:
            dataframe: OHLCV dataframe

        Returns:
            Dataframe with added features
        """
        df = dataframe.copy()

        # Add base technical indicators
        df = self.add_technical_indicators(df)

        # Add derived features
        df = self.add_price_features(df)
        df = self.add_volume_features(df)
        df = self.add_volatility_features(df)
        df = self.add_momentum_features(df)

        # Add market regime features
        df = self.add_regime_features(df)

        # Add time-based features
        df = self.add_time_features(df)

        return df

    def add_technical_indicators(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Add standard technical indicators.

        Args:
            dataframe: OHLCV dataframe

        Returns:
            Dataframe with technical indicators
        """
        df = dataframe.copy()

        try:
            import pandas_ta as ta
        except ImportError:
            logger.error("pandas_ta not installed. Install with: pip install pandas-ta")
            return df

        # RSI (multiple periods)
        df["rsi_14"] = ta.rsi(df["close"], length=14)
        df["rsi_21"] = ta.rsi(df["close"], length=21)
        df["rsi_7"] = ta.rsi(df["close"], length=7)

        # MACD
        macd = ta.macd(df["close"])
        if macd is not None and not macd.empty:
            df["macd"] = macd["MACD_12_26_9"]
            df["macd_signal"] = macd["MACDs_12_26_9"]
            df["macd_diff"] = macd["MACDh_12_26_9"]

        # Bollinger Bands
        bb = ta.bbands(df["close"], length=20, std=2)
        if bb is not None and not bb.empty:
            df["bb_upper"] = bb["BBU_20_2.0"]
            df["bb_middle"] = bb["BBM_20_2.0"]
            df["bb_lower"] = bb["BBL_20_2.0"]
            df["bb_width"] = (bb["BBU_20_2.0"] - bb["BBL_20_2.0"]) / bb["BBM_20_2.0"]

        # ATR (Average True Range)
        df["atr_14"] = ta.atr(df["high"], df["low"], df["close"], length=14)
        df["atr_7"] = ta.atr(df["high"], df["low"], df["close"], length=7)

        # EMAs (multiple periods)
        df["ema_9"] = ta.ema(df["close"], length=9)
        df["ema_21"] = ta.ema(df["close"], length=21)
        df["ema_50"] = ta.ema(df["close"], length=50)
        df["ema_200"] = ta.ema(df["close"], length=200)

        # SMAs
        df["sma_20"] = ta.sma(df["close"], length=20)
        df["sma_50"] = ta.sma(df["close"], length=50)

        # Volume indicators
        df["volume_sma_20"] = ta.sma(df["volume"], length=20)
        df["obv"] = ta.obv(df["close"], df["volume"])

        # ADX (Trend strength)
        adx = ta.adx(df["high"], df["low"], df["close"], length=14)
        if adx is not None and not adx.empty:
            df["adx"] = adx["ADX_14"]
            df["adx_plus"] = adx["DMP_14"]
            df["adx_minus"] = adx["DMN_14"]

        # Stochastic
        stoch = ta.stoch(df["high"], df["low"], df["close"])
        if stoch is not None and not stoch.empty:
            df["stoch_k"] = stoch["STOCHk_14_3_3"]
            df["stoch_d"] = stoch["STOCHd_14_3_3"]

        # CCI (Commodity Channel Index)
        df["cci"] = ta.cci(df["high"], df["low"], df["close"], length=20)

        # Williams %R
        df["williams_r"] = ta.willr(df["high"], df["low"], df["close"], length=14)

        logger.info(
            f"Added {len([c for c in df.columns if c not in dataframe.columns])} technical indicators"
        )

        return df

    def add_price_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Add price-based derived features.

        Args:
            dataframe: Dataframe with OHLCV data

        Returns:
            Dataframe with price features
        """
        df = dataframe.copy()

        # Price changes (percentage)
        df["price_change_1"] = df["close"].pct_change(1) * 100
        df["price_change_4"] = df["close"].pct_change(4) * 100
        df["price_change_12"] = df["close"].pct_change(12) * 100
        df["price_change_24"] = df["close"].pct_change(24) * 100

        # Price relative to moving averages
        df["price_to_ema_9"] = (df["close"] / df["ema_9"] - 1) * 100
        df["price_to_ema_21"] = (df["close"] / df["ema_21"] - 1) * 100
        df["price_to_ema_50"] = (df["close"] / df["ema_50"] - 1) * 100

        # High/Low ranges
        df["high_low_range"] = (df["high"] - df["low"]) / df["close"] * 100
        df["close_open_range"] = (df["close"] - df["open"]) / df["open"] * 100

        # Price position in range
        df["price_position"] = (df["close"] - df["low"]) / (
            df["high"] - df["low"] + 1e-10
        )

        return df

    def add_volume_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Add volume-based features.

        Args:
            dataframe: Dataframe with OHLCV data

        Returns:
            Dataframe with volume features
        """
        df = dataframe.copy()

        # Volume changes
        df["volume_change_1"] = df["volume"].pct_change(1) * 100
        df["volume_change_4"] = df["volume"].pct_change(4) * 100
        df["volume_change_24"] = df["volume"].pct_change(24) * 100

        # Volume relative to average
        if "volume_sma_20" in df.columns:
            df["volume_to_avg"] = df["volume"] / (df["volume_sma_20"] + 1e-10)

        # Volume-price correlation
        df["volume_price_corr"] = df["volume"].rolling(20).corr(df["close"])

        return df

    def add_volatility_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Add volatility-based features.

        Args:
            dataframe: Dataframe with OHLCV data

        Returns:
            Dataframe with volatility features
        """
        df = dataframe.copy()

        # ATR percentage
        df["atr_pct"] = (df["atr_14"] / df["close"]) * 100

        # Rolling volatility
        df["volatility_7d"] = (
            df["close"].pct_change().rolling(7 * 24).std() * 100
        )  # 7 days for 1h candles
        df["volatility_1d"] = (
            df["close"].pct_change().rolling(24).std() * 100
        )  # 1 day for 1h candles

        # Bollinger Band percentage
        if all(col in df.columns for col in ["bb_upper", "bb_lower", "bb_middle"]):
            df["bb_pct"] = (df["close"] - df["bb_lower"]) / (
                df["bb_upper"] - df["bb_lower"] + 1e-10
            )

        return df

    def add_momentum_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Add momentum-based features.

        Args:
            dataframe: Dataframe with OHLCV data

        Returns:
            Dataframe with momentum features
        """
        df = dataframe.copy()

        # Rate of change
        df["roc_12"] = (
            (df["close"] - df["close"].shift(12)) / df["close"].shift(12)
        ) * 100
        df["roc_24"] = (
            (df["close"] - df["close"].shift(24)) / df["close"].shift(24)
        ) * 100

        # EMA crossover signals
        if "ema_9" in df.columns and "ema_21" in df.columns:
            df["ema_cross_short"] = (df["ema_9"] > df["ema_21"]).astype(int)

        if "ema_21" in df.columns and "ema_50" in df.columns:
            df["ema_cross_medium"] = (df["ema_21"] > df["ema_50"]).astype(int)

        # MACD momentum
        if "macd" in df.columns and "macd_signal" in df.columns:
            df["macd_momentum"] = (df["macd"] > df["macd_signal"]).astype(int)

        return df

    def add_regime_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Add market regime detection features.

        Args:
            dataframe: Dataframe with OHLCV data

        Returns:
            Dataframe with regime features
        """
        df = dataframe.copy()

        # Trending detection (based on ADX)
        if "adx" in df.columns:
            df["is_trending"] = (df["adx"] > 25).astype(int)
            df["trend_strength"] = df["adx"] / 100  # Normalize

        # Direction detection
        if "ema_21" in df.columns and "ema_50" in df.columns:
            df["is_uptrend"] = (df["ema_21"] > df["ema_50"]).astype(int)
            df["is_downtrend"] = (df["ema_21"] < df["ema_50"]).astype(int)

        # Ranging detection (low volatility + low ADX)
        if "adx" in df.columns and "atr_pct" in df.columns:
            df["is_ranging"] = ((df["adx"] < 20) & (df["atr_pct"] < 2.0)).astype(int)

        # Volatile detection
        if "atr_pct" in df.columns and "bb_width" in df.columns:
            df["is_volatile"] = (
                (df["atr_pct"] > 2.5) & (df["bb_width"] > 0.04)
            ).astype(int)

        return df

    def add_time_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Add time-based features (hour, day of week, etc.).

        Args:
            dataframe: Dataframe with datetime index

        Returns:
            Dataframe with time features
        """
        df = dataframe.copy()

        if isinstance(df.index, pd.DatetimeIndex):
            df["hour"] = df.index.hour
            df["day_of_week"] = df.index.dayofweek
            df["day_of_month"] = df.index.day

            # Cyclical encoding (sine/cosine for periodic features)
            df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
            df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
            df["day_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
            df["day_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

        return df

    def get_feature_list(self, dataframe: pd.DataFrame) -> List[str]:
        """
        Get list of feature column names (excluding OHLCV).

        Args:
            dataframe: Dataframe with features

        Returns:
            List of feature column names
        """
        exclude_cols = ["open", "high", "low", "close", "volume", "date"]
        features = [col for col in dataframe.columns if col not in exclude_cols]
        return features

    def clean_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Clean features (handle NaN, inf values).

        Args:
            dataframe: Dataframe with features

        Returns:
            Cleaned dataframe
        """
        df = dataframe.copy()

        # Replace inf with NaN
        df = df.replace([np.inf, -np.inf], np.nan)

        # Forward fill NaN values (for initial periods where indicators aren't calculated)
        df = df.fillna(method="ffill")

        # Backward fill remaining NaN values
        df = df.fillna(method="bfill")

        # If still NaN, fill with 0
        df = df.fillna(0)

        return df


def create_target_labels(
    dataframe: pd.DataFrame, target_type: str = "regression", lookahead_periods: int = 4
) -> pd.DataFrame:
    """
    Create target labels for ML models.

    Args:
        dataframe: OHLCV dataframe
        target_type: 'regression' or 'classification'
        lookahead_periods: Number of periods to look ahead

    Returns:
        Dataframe with target labels
    """
    df = dataframe.copy()

    if target_type == "regression":
        # Future price (absolute)
        df["target_price"] = df["close"].shift(-lookahead_periods)

        # Future return (percentage)
        df["target_return"] = (
            (df["close"].shift(-lookahead_periods) - df["close"]) / df["close"]
        ) * 100

    elif target_type == "classification":
        # Future direction (0=down, 1=neutral, 2=up)
        future_return = (
            (df["close"].shift(-lookahead_periods) - df["close"]) / df["close"]
        ) * 100
        df["target_direction"] = pd.cut(
            future_return,
            bins=[-np.inf, -0.5, 0.5, np.inf],
            labels=[0, 1, 2],  # down, neutral, up
        ).astype(float)

        # Binary profitable entry (1 if future price > current + threshold)
        threshold = 1.0  # 1% profit threshold
        df["target_profitable"] = (future_return > threshold).astype(int)

    # Remove last N rows (no future data available)
    df = df.iloc[:-lookahead_periods]

    return df


# Example usage
if __name__ == "__main__":
    # This would typically be run with real OHLCV data
    print("Feature Engineering Module")
    print("Use FeatureEngineer class to add features to your dataframes")
    print("Example:")
    print("  fe = FeatureEngineer()")
    print("  df = fe.add_all_features(dataframe)")
    print("  features = fe.get_feature_list(df)")
