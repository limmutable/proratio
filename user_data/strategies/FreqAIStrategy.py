"""
FreqAI Strategy for Phase 3 - Machine Learning Enhanced Trading

This strategy uses FreqAI for ML-powered predictions combined with technical analysis.
FreqAI trains models on historical data to predict future price movements and confidence scores.

Strategy Logic:
- Base: Technical indicators (EMA, RSI, MACD, Bollinger Bands)
- Enhancement: ML predictions from LightGBM regressor
- Entry: Technical signal + ML prediction > threshold + high confidence
- Exit: Technical signal OR ML prediction reversal
- Position sizing: Base stake * ML confidence multiplier

ML Features:
- 80+ engineered features from FeatureEngineer class
- Technical indicators, price patterns, volume, volatility
- Market regime detection (trending/ranging/volatile)
- Time-based features (hour, day of week)

Model:
- LightGBMRegressor for price prediction
- 30 days training period, 7 days validation
- Retrain every 24 hours with latest data
"""

import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging

# Add project root to Python path for imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import talib.abstract as ta
from freqtrade.strategy import IStrategy, merge_informative_pair
from pandas import DataFrame

# Import our custom feature engineering
from proratio_quantlab.ml.feature_engineering import (
    FeatureEngineer,
    create_target_labels,
)

logger = logging.getLogger(__name__)


class FreqAIStrategy(IStrategy):
    """
    ML-enhanced strategy using FreqAI for adaptive predictions.
    """

    # Strategy metadata
    INTERFACE_VERSION = 3
    can_short = False  # Spot trading only

    # ROI table (conservative with ML confidence)
    minimal_roi = {
        "0": 0.20,  # 20% profit → exit (ML should catch bigger moves)
        "60": 0.10,  # After 60 min, 10% profit → exit
        "120": 0.05,  # After 120 min, 5% profit → exit
    }

    # Stoploss (tighter with ML prediction)
    stoploss = -0.03  # 3% stop loss (ML should prevent bad entries)

    # Trailing stop
    trailing_stop = True
    trailing_stop_positive = 0.02  # Activate trailing at 2% profit
    trailing_stop_positive_offset = 0.03  # Trail after 3% profit
    trailing_only_offset_is_reached = True

    # Timeframe
    timeframe = "4h"

    # Run "populate_indicators()" only for new candle
    process_only_new_candles = True

    # Startup candles (need enough history for features)
    startup_candle_count = 200  # 200 candles for feature engineering

    # Optional order types
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    # Optional order time in force
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    # ML Configuration
    ml_prediction_threshold = 0.01  # Minimum predicted return (1%)
    ml_min_confidence = 0.65  # Minimum ML confidence to enter (65%)

    # Position sizing multipliers based on ML confidence
    # Confidence 65% = 0.8x stake, 80% = 1.0x stake, 95% = 1.2x stake
    ml_confidence_multiplier_min = 0.8
    ml_confidence_multiplier_max = 1.2

    def __init__(self, config: dict) -> None:
        """
        Initialize strategy with feature engineering.

        Args:
            config: Freqtrade configuration dict
        """
        super().__init__(config)

        # Initialize feature engineer
        self.feature_engineer = FeatureEngineer()

        logger.info("FreqAIStrategy initialized with ML predictions")

    def informative_pairs(self):
        """
        Define additional informative pairs/timeframes.
        Called once by Freqtrade to fetch additional data.
        """
        # We want 1h data as additional features for 4h strategy
        return [(pair, "1h") for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Add technical indicators and prepare features for FreqAI.

        Args:
            dataframe: Raw OHLCV data
            metadata: Additional pair metadata

        Returns:
            Dataframe with indicators
        """
        # Add all engineered features (technical, price, volume, volatility, etc.)
        dataframe = self.feature_engineer.add_all_features(dataframe)

        # Add informative 1h data
        if self.dp:
            informative = self.dp.get_pair_dataframe(
                pair=metadata["pair"], timeframe="1h"
            )
            if not informative.empty:
                # Add key indicators from 1h timeframe
                informative["rsi_1h"] = ta.RSI(informative, timeperiod=14)
                informative["ema9_1h"] = ta.EMA(informative, timeperiod=9)
                informative["ema21_1h"] = ta.EMA(informative, timeperiod=21)

                # Merge with main dataframe
                dataframe = merge_informative_pair(
                    dataframe, informative, self.timeframe, "1h", ffill=True
                )

        return dataframe

    def feature_engineering_expand_all(
        self, dataframe: DataFrame, period: int, **kwargs
    ) -> DataFrame:
        """
        FreqAI method: Create features for all periods.
        This is called by FreqAI during training and prediction.

        Args:
            dataframe: Dataframe with indicators
            period: Indicator period

        Returns:
            Dataframe with features
        """
        # Add custom features that FreqAI will use
        dataframe["%-rsi-period"] = ta.RSI(dataframe, timeperiod=period)
        dataframe["%-mfi-period"] = ta.MFI(dataframe, timeperiod=period)
        dataframe["%-adx-period"] = ta.ADX(dataframe, timeperiod=period)
        dataframe["%-cci-period"] = ta.CCI(dataframe, timeperiod=period)

        # Price momentum
        dataframe[f"%-close_pct_change_{period}"] = dataframe["close"].pct_change(
            period
        )
        dataframe[f"%-volume_pct_change_{period}"] = dataframe["volume"].pct_change(
            period
        )

        return dataframe

    def feature_engineering_expand_basic(
        self, dataframe: DataFrame, **kwargs
    ) -> DataFrame:
        """
        FreqAI method: Basic feature engineering without period variations.

        Args:
            dataframe: Dataframe with indicators

        Returns:
            Dataframe with basic features
        """
        # All our engineered features are already added in populate_indicators
        # Just ensure we have key features marked with %-prefix for FreqAI

        if "rsi_14" in dataframe.columns:
            dataframe["%-rsi"] = dataframe["rsi_14"]
        if "macd" in dataframe.columns:
            dataframe["%-macd"] = dataframe["macd"]
        if "macd_signal" in dataframe.columns:
            dataframe["%-macd_signal"] = dataframe["macd_signal"]
        if "bb_upperband" in dataframe.columns and "bb_lowerband" in dataframe.columns:
            dataframe["%-bb_width"] = (
                dataframe["bb_upperband"] - dataframe["bb_lowerband"]
            ) / dataframe["close"]
        if "atr" in dataframe.columns:
            dataframe["%-atr"] = dataframe["atr"] / dataframe["close"]
        if "adx" in dataframe.columns:
            dataframe["%-adx"] = dataframe["adx"]

        # Price patterns
        dataframe["%-close_to_high"] = (
            dataframe["high"] - dataframe["close"]
        ) / dataframe["close"]
        dataframe["%-close_to_low"] = (
            dataframe["close"] - dataframe["low"]
        ) / dataframe["close"]

        return dataframe

    def feature_engineering_standard(self, dataframe: DataFrame, **kwargs) -> DataFrame:
        """
        FreqAI method: Standard feature engineering combining all methods.

        Args:
            dataframe: Dataframe with indicators

        Returns:
            Dataframe with all features
        """
        # This method combines expand_all and expand_basic
        # FreqAI will call this with different periods from config
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, **kwargs) -> DataFrame:
        """
        FreqAI method: Define prediction targets for ML model.
        This tells FreqAI what to predict.

        Args:
            dataframe: Dataframe with features

        Returns:
            Dataframe with target labels
        """
        # Predict future price change (regression target)
        # lookahead_periods=4 means predict 4 candles ahead (16 hours for 4h timeframe)
        dataframe = create_target_labels(
            dataframe, target_type="regression", lookahead_periods=4
        )

        # FreqAI expects target in column named with '&-' prefix
        if "target_price_change" in dataframe.columns:
            dataframe["&-target"] = dataframe["target_price_change"]

        # Also create classification target (optional, for confidence scoring)
        dataframe = create_target_labels(
            dataframe, target_type="classification", lookahead_periods=4
        )

        if "target_direction" in dataframe.columns:
            dataframe["&-target_direction"] = dataframe["target_direction"]

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Define entry (buy) signals based on ML predictions + technical confirmation.

        Args:
            dataframe: Dataframe with indicators and ML predictions
            metadata: Additional pair metadata

        Returns:
            Dataframe with entry signals
        """
        conditions = []

        # ML Prediction conditions (if FreqAI is enabled)
        if "do_predict" in dataframe.columns:
            # FreqAI predictions are in columns with '&-' prefix
            ml_conditions = (
                (dataframe["do_predict"] == 1)  # FreqAI says we should predict
                & (
                    dataframe["&-target"] > self.ml_prediction_threshold
                )  # Positive prediction
                & (
                    dataframe["DI_values"] < 1
                )  # Dissimilarity Index check (data quality)
            )
            conditions.append(ml_conditions)

        # Technical confirmation conditions
        technical_conditions = (
            (dataframe["volume"] > 0)  # Volume check
            & (dataframe["close"] > dataframe["ema21"])  # Price above EMA21
            & (dataframe["ema9"] > dataframe["ema21"])  # EMA9 > EMA21 (uptrend)
            & (dataframe["rsi_14"] > 30)  # RSI not oversold (avoid falling knives)
            & (dataframe["rsi_14"] < 70)  # RSI not overbought (room to grow)
            & (
                dataframe["close"] > dataframe["bb_lowerband"]
            )  # Above lower Bollinger Band
            & (dataframe["adx"] > 20)  # ADX shows trend strength
        )
        conditions.append(technical_conditions)

        # Combine all conditions
        if conditions:
            dataframe.loc[reduce(lambda x, y: x & y, conditions), "enter_long"] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Define exit (sell) signals based on ML prediction reversal + technical signals.

        Args:
            dataframe: Dataframe with indicators and ML predictions
            metadata: Additional pair metadata

        Returns:
            Dataframe with exit signals
        """
        conditions = []

        # ML Prediction reversal (if FreqAI is enabled)
        if "do_predict" in dataframe.columns and "&-target" in dataframe.columns:
            ml_exit_conditions = (
                (dataframe["do_predict"] == 1)  # FreqAI is active
                & (
                    dataframe["&-target"] < -self.ml_prediction_threshold
                )  # Negative prediction
            )
            conditions.append(ml_exit_conditions)

        # Technical exit conditions
        technical_exit = (
            (dataframe["close"] < dataframe["ema9"])  # Price below EMA9
            | (dataframe["ema9"] < dataframe["ema21"])  # EMA9 < EMA21 (downtrend)
            | (dataframe["rsi_14"] > 75)  # RSI overbought
            | (
                dataframe["close"] > dataframe["bb_upperband"]
            )  # Above upper Bollinger Band
        )
        conditions.append(technical_exit)

        # Exit if any condition is true (OR logic for exits)
        if conditions:
            dataframe.loc[reduce(lambda x, y: x | y, conditions), "exit_long"] = 1

        return dataframe

    def custom_stake_amount(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_stake: float,
        min_stake: Optional[float],
        max_stake: float,
        leverage: float,
        entry_tag: Optional[str],
        side: str,
        **kwargs,
    ) -> float:
        """
        Adjust stake amount based on ML confidence.

        Args:
            pair: Trading pair
            current_time: Current datetime
            current_rate: Current price
            proposed_stake: Base stake from config
            min_stake: Minimum allowed stake
            max_stake: Maximum allowed stake
            leverage: Leverage (1 for spot)
            entry_tag: Entry signal tag
            side: 'long' or 'short'

        Returns:
            Adjusted stake amount
        """
        # Get latest dataframe
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)

        if dataframe.empty:
            return proposed_stake

        # Get ML confidence from FreqAI (if available)
        last_candle = dataframe.iloc[-1]

        if "&-target" in last_candle:
            # ML prediction confidence based on absolute predicted return
            ml_prediction = abs(last_candle["&-target"])

            # Map prediction to confidence multiplier (0.01 = 65%, 0.05 = 95%)
            confidence = min(0.95, 0.65 + (ml_prediction - 0.01) * 10)
            confidence = max(0.65, confidence)

            # Calculate multiplier (65% → 0.8x, 80% → 1.0x, 95% → 1.2x)
            multiplier = self.ml_confidence_multiplier_min + (confidence - 0.65) / (
                0.95 - 0.65
            ) * (self.ml_confidence_multiplier_max - self.ml_confidence_multiplier_min)

            # Apply multiplier to proposed stake
            adjusted_stake = proposed_stake * multiplier

            # Ensure within limits
            if min_stake:
                adjusted_stake = max(adjusted_stake, min_stake)
            adjusted_stake = min(adjusted_stake, max_stake)

            logger.info(
                f"ML confidence: {confidence:.2%}, multiplier: {multiplier:.2f}, "
                f"stake: {proposed_stake:.2f} → {adjusted_stake:.2f}"
            )

            return adjusted_stake

        return proposed_stake


# Helper function for reduce (combining conditions)
from functools import reduce
