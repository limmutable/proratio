"""
Mean Reversion Strategy - Freqtrade Adapter

Enters trades when price deviates significantly from its mean (oversold/overbought),
expecting price to revert back to the mean. Uses RSI and Bollinger Bands with
optional AI confirmation for higher-confidence entries.

Strategy Logic:
- Long Entry: RSI < 30 AND price < BB_lower AND (optional) AI confirmation
- Short Entry: RSI > 70 AND price > BB_upper AND (optional) AI confirmation
- Exit: Price returns to mean (middle BB) OR stop-loss/take-profit hit

Best for: Range-bound markets, sideways consolidation
Avoid: Strong trending markets (use trend-following instead)
"""

import sys
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

# Add project root to Python path for imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame

from proratio_signals import SignalOrchestrator, ConsensusSignal
from proratio_signals.llm_providers.base import OHLCVData


class MeanReversionStrategy(IStrategy):
    """
    Mean reversion strategy combining RSI, Bollinger Bands, and AI consensus.

    Entry conditions:
    - Long: RSI < 30, price < BB_lower, AI confirms (optional)
    - Short: RSI > 70, price > BB_upper, AI confirms (optional)

    Exit conditions:
    - Price returns to BB_middle
    - RSI returns to neutral (40-60)
    - Stop-loss or take-profit hit
    """

    # Strategy metadata
    INTERFACE_VERSION = 3
    can_short = False  # Spot trading only (set to True for futures)

    # ROI table - Take profit at mean reversion
    minimal_roi = {
        "0": 0.05,  # 5% profit → exit (mean reversion complete)
        "30": 0.03,  # After 30 min, 3% profit → exit
        "60": 0.02,  # After 60 min, 2% profit → exit
    }

    # Stoploss - Tight stop for mean reversion
    stoploss = -0.03  # 3% stop loss (price may continue deviation)

    # Trailing stop
    trailing_stop = True
    trailing_stop_positive = 0.01  # Activate trailing at 1% profit
    trailing_stop_positive_offset = 0.015  # Trail after 1.5% profit
    trailing_only_offset_is_reached = True

    # Timeframe - Mean reversion works on shorter timeframes
    timeframe = "1h"

    # Run "populate_indicators()" only for new candle
    process_only_new_candles = True

    # Startup candles
    startup_candle_count = 100

    # Optional order types
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    # Optional order time in force
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    # Strategy parameters
    rsi_oversold = 30
    rsi_overbought = 70
    bb_period = 20
    bb_std = 2.0

    # AI Configuration
    use_ai_confirmation = True
    ai_min_confidence = 0.50  # Lower threshold for mean reversion (50%)
    ai_lookback_candles = 50
    ai_cache_minutes = 60

    # Position sizing multipliers based on AI confidence
    ai_confidence_multiplier_min = 0.7
    ai_confidence_multiplier_max = 1.3

    def __init__(self, config: dict) -> None:
        """
        Initialize strategy with AI orchestrator.

        Args:
            config: Freqtrade configuration dict
        """
        super().__init__(config)

        # Initialize AI orchestrator
        if self.use_ai_confirmation:
            try:
                self.ai_orchestrator = SignalOrchestrator()
                self.ai_enabled = True
                print("✓ Mean Reversion: AI Orchestrator initialized")
                print(f"  Active providers: {len(self.ai_orchestrator.providers)}")
            except Exception as e:
                print(f"✗ Mean Reversion: Failed to initialize AI: {e}")
                print("  Strategy will run in TECHNICAL-ONLY mode")
                self.ai_orchestrator = None
                self.ai_enabled = False
        else:
            self.ai_orchestrator = None
            self.ai_enabled = False
            print("ℹ Mean Reversion: Running in TECHNICAL-ONLY mode (AI disabled)")

        # Cache for AI signals (pair -> {signal, timestamp})
        self.ai_signal_cache = {}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Add technical indicators to the dataframe.

        Args:
            dataframe: Raw OHLCV data
            metadata: Strategy metadata (pair, timeframe, etc.)

        Returns:
            DataFrame with indicators added
        """
        # RSI - Relative Strength Index
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        # Bollinger Bands
        bollinger = ta.BBANDS(
            dataframe,
            timeperiod=self.bb_period,
            nbdevup=self.bb_std,
            nbdevdn=self.bb_std,
        )
        dataframe["bb_upper"] = bollinger["upperband"]
        dataframe["bb_middle"] = bollinger["middleband"]
        dataframe["bb_lower"] = bollinger["lowerband"]

        # BB bandwidth (volatility measure)
        dataframe["bb_width"] = (
            dataframe["bb_upper"] - dataframe["bb_lower"]
        ) / dataframe["bb_middle"]

        # Additional indicators for context
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)  # Volatility
        dataframe["volume_mean"] = dataframe["volume"].rolling(window=20).mean()

        # EMA for trend context (avoid mean reversion in strong trends)
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=50)

        return dataframe

    def get_ai_signal(
        self, dataframe: DataFrame, metadata: dict
    ) -> Optional[ConsensusSignal]:
        """
        Get AI consensus signal for the current market state.
        Uses caching to avoid API spam.

        Args:
            dataframe: DataFrame with OHLCV data and indicators
            metadata: Strategy metadata (pair, timeframe)

        Returns:
            ConsensusSignal or None if AI disabled/failed
        """
        if not self.ai_enabled:
            return None

        pair = metadata["pair"]
        current_time = datetime.now(timezone.utc)

        # Check cache first
        if pair in self.ai_signal_cache:
            cached = self.ai_signal_cache[pair]
            age_minutes = (current_time - cached["timestamp"]).total_seconds() / 60

            if age_minutes < self.ai_cache_minutes:
                return cached["signal"]

        # Generate new AI signal
        try:
            recent_data = dataframe.tail(self.ai_lookback_candles).copy()

            # Ensure timestamp column exists
            if "timestamp" not in recent_data.columns:
                recent_data.reset_index(inplace=True)
                if "date" in recent_data.columns:
                    recent_data.rename(columns={"date": "timestamp"}, inplace=True)

            # Convert to OHLCVData format
            ohlcv = OHLCVData(
                pair=pair,
                timeframe=self.timeframe,
                data=recent_data[["open", "high", "low", "close", "volume"]].copy(),
                indicators={
                    "rsi": recent_data["rsi"].iloc[-1]
                    if "rsi" in recent_data.columns
                    else None,
                    "bb_upper": recent_data["bb_upper"].iloc[-1]
                    if "bb_upper" in recent_data.columns
                    else None,
                    "bb_middle": recent_data["bb_middle"].iloc[-1]
                    if "bb_middle" in recent_data.columns
                    else None,
                    "bb_lower": recent_data["bb_lower"].iloc[-1]
                    if "bb_lower" in recent_data.columns
                    else None,
                    "atr": recent_data["atr"].iloc[-1]
                    if "atr" in recent_data.columns
                    else None,
                },
            )

            # Generate AI consensus
            signal = self.ai_orchestrator.generate_signal(
                pair=pair,
                timeframe=self.timeframe,
                ohlcv_data=ohlcv.data,
                indicators=ohlcv.indicators,
            )

            # Cache the signal
            self.ai_signal_cache[pair] = {"signal": signal, "timestamp": current_time}

            return signal

        except Exception as e:
            print(f"✗ Mean Reversion AI signal failed for {pair}: {e}")
            return None

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Define entry (buy) signals for mean reversion.

        Entry conditions:
        1. RSI < 30 (oversold)
        2. Price < BB_lower (below mean)
        3. Not in strong downtrend (EMA_fast > EMA_slow preferred)
        4. AI confirms (optional)

        Args:
            dataframe: DataFrame with indicators
            metadata: Strategy metadata

        Returns:
            DataFrame with 'enter_long' column added
        """
        # Get AI signal if enabled
        ai_signal = self.get_ai_signal(dataframe, metadata)

        # Technical conditions for long entry
        technical_conditions = (
            # RSI oversold
            (dataframe["rsi"] < self.rsi_oversold)
            &
            # Price below lower Bollinger Band
            (dataframe["close"] < dataframe["bb_lower"])
            &
            # Sufficient volatility for mean reversion
            (dataframe["bb_width"] > 0.02)  # At least 2% bandwidth
            &
            # Volume confirmation
            (dataframe["volume"] > dataframe["volume_mean"])
        )

        # AI conditions
        if ai_signal and ai_signal.should_trade():
            # AI agrees with mean reversion
            ai_conditions = (ai_signal.direction.lower() == "long") & (
                ai_signal.confidence >= self.ai_min_confidence
            )

            # Combine technical + AI
            dataframe.loc[technical_conditions & ai_conditions, "enter_long"] = 1

            if ai_conditions:
                print(
                    f"✓ Mean Reversion ENTRY for {metadata['pair']}: "
                    f"RSI={dataframe['rsi'].iloc[-1]:.1f}, "
                    f"Price below BB_lower, "
                    f"AI confidence={ai_signal.confidence:.1%}"
                )
        else:
            # Fallback to technical-only if AI unavailable or disabled
            dataframe.loc[technical_conditions, "enter_long"] = 1

            if self.ai_enabled and not ai_signal:
                print(
                    f"⚠ Mean Reversion: AI unavailable for {metadata['pair']}, using technical-only"
                )

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Define exit (sell) signals for mean reversion.

        Exit conditions:
        1. Price returns to BB_middle (mean reversion complete)
        2. RSI returns to neutral zone (40-60)
        3. RSI becomes overbought (> 70)

        Args:
            dataframe: DataFrame with indicators
            metadata: Strategy metadata

        Returns:
            DataFrame with 'exit_long' column added
        """
        # Technical exit conditions
        exit_conditions = (
            # Price returned to mean
            (
                (dataframe["close"] >= dataframe["bb_middle"])
                & (dataframe["close"].shift(1) < dataframe["bb_middle"].shift(1))
            )
            |
            # RSI returned to neutral or overbought
            (dataframe["rsi"] > 60)
            |
            # Price above upper BB (overextended)
            (dataframe["close"] > dataframe["bb_upper"])
        )

        dataframe.loc[exit_conditions, "exit_long"] = 1

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
        Adjust position size based on AI confidence and mean reversion strength.

        Args:
            pair: Trading pair
            proposed_stake: Base stake amount from config
            ... (other Freqtrade parameters)

        Returns:
            Adjusted stake amount
        """
        # Get cached AI signal
        if pair in self.ai_signal_cache:
            signal = self.ai_signal_cache[pair]["signal"]

            if signal and signal.confidence >= self.ai_min_confidence:
                # Calculate multiplier based on confidence
                confidence_normalized = (signal.confidence - self.ai_min_confidence) / (
                    1.0 - self.ai_min_confidence
                )
                multiplier = self.ai_confidence_multiplier_min + (
                    confidence_normalized
                    * (
                        self.ai_confidence_multiplier_max
                        - self.ai_confidence_multiplier_min
                    )
                )

                adjusted_stake = proposed_stake * multiplier

                # Ensure within min/max bounds
                if min_stake and adjusted_stake < min_stake:
                    adjusted_stake = min_stake
                if adjusted_stake > max_stake:
                    adjusted_stake = max_stake

                print(
                    f"💰 Mean Reversion position sizing for {pair}: "
                    f"base={proposed_stake:.2f} → adjusted={adjusted_stake:.2f} "
                    f"(confidence={signal.confidence:.1%}, multiplier={multiplier:.2f}x)"
                )

                return adjusted_stake

        return proposed_stake

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time,
        entry_tag,
        side: str,
        **kwargs,
    ) -> bool:
        """
        Final confirmation before entering trade.
        Double-check AI signal is still valid.

        Returns:
            True to allow entry, False to reject
        """
        if pair in self.ai_signal_cache:
            cached = self.ai_signal_cache[pair]
            signal = cached["signal"]
            age_minutes = (
                datetime.now(timezone.utc) - cached["timestamp"]
            ).total_seconds() / 60

            # Reject if signal expired or confidence dropped
            if age_minutes >= self.ai_cache_minutes:
                print(f"✗ Mean Reversion: Rejecting {pair} - AI signal expired")
                return False

            if signal.confidence < self.ai_min_confidence:
                print(f"✗ Mean Reversion: Rejecting {pair} - Low confidence")
                return False

            if signal.direction.lower() != "long":
                print(f"✗ Mean Reversion: Rejecting {pair} - Direction changed")
                return False

        return True
