"""
AI-Enhanced Strategy for Week 2 - Multi-LLM Signal Integration

Extends SimpleTestStrategy by adding AI consensus signals from ChatGPT, Claude, and Gemini.
This strategy combines technical indicators with multi-AI analysis for improved decision making.

Strategy Logic:
- Base: EMA crossover + RSI (from SimpleTestStrategy)
- Enhancement: AI consensus filter + confidence-based position sizing
- Entry: Technical signal + AI consensus > 50% + AI direction = LONG
- Exit: Technical signal OR AI consensus changes
- Position sizing: Base stake * AI confidence multiplier

This strategy requires:
- Valid API keys for OpenAI, Anthropic, and Google (at least 1 provider)
- Historical OHLCV data for AI context
"""

import sys
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

# Add project root to Python path for imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# These imports must come after sys.path modification - ignore linting
import talib.abstract as ta  # noqa: E402
from freqtrade.strategy import IStrategy  # noqa: E402
from pandas import DataFrame  # noqa: E402

from proratio_signals import SignalOrchestrator, ConsensusSignal  # noqa: E402
from proratio_signals.llm_providers.base import OHLCVData  # noqa: E402


class AIEnhancedStrategy(IStrategy):
    """
    AI-enhanced trend-following strategy combining technical indicators with multi-LLM consensus.
    """

    # Strategy metadata
    INTERFACE_VERSION = 3
    can_short = False  # Spot trading only (no shorting)

    # ROI table (slightly more conservative than SimpleTestStrategy)
    minimal_roi = {
        "0": 0.15,  # 15% profit → exit (wait for bigger moves with AI confirmation)
        "60": 0.08,  # After 60 min, 8% profit → exit
        "120": 0.04,  # After 120 min, 4% profit → exit
    }

    # Stoploss (slightly tighter with AI confirmation)
    stoploss = -0.04  # 4% stop loss (AI should prevent bad entries)

    # Trailing stop
    trailing_stop = True
    trailing_stop_positive = 0.015  # Activate trailing at 1.5% profit
    trailing_stop_positive_offset = 0.025  # Trail after 2.5% profit
    trailing_only_offset_is_reached = True

    # Timeframe (AI analysis works best on 1h-4h timeframes)
    timeframe = "1h"

    # Run "populate_indicators()" only for new candle
    process_only_new_candles = True

    # Startup candles (need more history for AI context)
    startup_candle_count = 100  # 100 candles for better AI analysis

    # Optional order types
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    # Optional order time in force
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    # AI Configuration
    ai_min_confidence = 0.50  # Minimum AI confidence to enter (50%) - lowered for 2/3 providers
    ai_lookback_candles = 50  # Number of candles to send to AI for context
    ai_cache_minutes = 60  # Cache AI signals for 60 minutes to avoid API spam

    # Position sizing multipliers based on AI confidence
    # Confidence 50% = 0.8x stake, 75% = 1.0x stake, 100% = 1.2x stake
    ai_confidence_multiplier_min = 0.8
    ai_confidence_multiplier_max = 1.2

    def __init__(self, config: dict) -> None:
        """
        Initialize strategy with AI orchestrator.

        Args:
            config: Freqtrade configuration dict
        """
        super().__init__(config)

        # Initialize AI orchestrator
        try:
            self.ai_orchestrator = SignalOrchestrator()
            self.ai_enabled = True
            print("✓ AI Orchestrator initialized successfully")
            print(f"  Active providers: {len(self.ai_orchestrator.providers)}")
        except Exception as e:
            print(f"✗ Failed to initialize AI Orchestrator: {e}")
            print("  Strategy will run in TECHNICAL-ONLY mode (no AI signals)")
            self.ai_orchestrator = None
            self.ai_enabled = False

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
        # EMA indicators (same as SimpleTestStrategy)
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=50)

        # RSI
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        # Volume
        dataframe["volume_mean"] = dataframe["volume"].rolling(window=20).mean()

        # Additional indicators for AI context
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)  # Volatility
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)  # Trend strength

        # Bollinger Bands (for volatility context)
        bollinger = ta.BBANDS(dataframe, timeperiod=20)
        dataframe["bb_upper"] = bollinger["upperband"]
        dataframe["bb_middle"] = bollinger["middleband"]
        dataframe["bb_lower"] = bollinger["lowerband"]

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
                # Cache is still valid
                return cached["signal"]

        # Generate new AI signal
        try:
            # Get recent candles for AI context
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
                    "ema_fast": recent_data["ema_fast"].iloc[-1]
                    if "ema_fast" in recent_data.columns
                    else None,
                    "ema_slow": recent_data["ema_slow"].iloc[-1]
                    if "ema_slow" in recent_data.columns
                    else None,
                    "rsi": recent_data["rsi"].iloc[-1]
                    if "rsi" in recent_data.columns
                    else None,
                    "atr": recent_data["atr"].iloc[-1]
                    if "atr" in recent_data.columns
                    else None,
                    "adx": recent_data["adx"].iloc[-1]
                    if "adx" in recent_data.columns
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
            print(f"✗ AI signal generation failed for {pair}: {e}")
            return None

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Define entry (buy) signals with AI enhancement.

        Entry conditions:
        1. Technical: EMA crossover + RSI not overbought + volume
        2. AI: Consensus signal = LONG + confidence > 50%

        Args:
            dataframe: DataFrame with indicators
            metadata: Strategy metadata

        Returns:
            DataFrame with 'enter_long' column added
        """
        # Get AI signal for current market state
        ai_signal = self.get_ai_signal(dataframe, metadata)

        # Technical conditions (from SimpleTestStrategy)
        technical_conditions = (
            # EMA crossover: fast crosses above slow
            (dataframe["ema_fast"] > dataframe["ema_slow"])
            & (dataframe["ema_fast"].shift(1) <= dataframe["ema_slow"].shift(1))
            &
            # RSI not overbought
            (dataframe["rsi"] > 30)
            & (dataframe["rsi"] < 70)
            &
            # Volume confirmation
            (dataframe["volume"] > dataframe["volume_mean"])
            &
            # Trend strength (ADX > 20 = trending market)
            (dataframe["adx"] > 20)
        )

        # AI conditions
        if ai_signal and ai_signal.should_trade():
            ai_conditions = (ai_signal.direction.lower() == "long") & (
                ai_signal.confidence >= self.ai_min_confidence
            )

            # Combine technical + AI
            dataframe.loc[technical_conditions & ai_conditions, "enter_long"] = 1

            # Debug logging
            if ai_conditions:
                print(
                    f"✓ AI ENTRY signal for {metadata['pair']}: "
                    f"direction={ai_signal.direction}, "
                    f"confidence={ai_signal.confidence:.1%}, "
                    f"providers={len(ai_signal.active_providers or [])}"
                )
        else:
            # Fallback to technical-only if AI unavailable
            dataframe.loc[technical_conditions, "enter_long"] = 1

            if self.ai_enabled:
                print(
                    f"⚠ AI signal unavailable for {metadata['pair']}, using technical-only entry"
                )

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Define exit (sell) signals with AI enhancement.

        Exit conditions:
        1. Technical: EMA crossover down OR RSI overbought
        2. AI: Consensus signal changes to SHORT/NEUTRAL with high confidence

        Args:
            dataframe: DataFrame with indicators
            metadata: Strategy metadata

        Returns:
            DataFrame with 'exit_long' column added
        """
        # Get AI signal for current market state
        ai_signal = self.get_ai_signal(dataframe, metadata)

        # Technical exit conditions (from SimpleTestStrategy)
        technical_exit = (
            # EMA crossover: fast crosses below slow
            (
                (dataframe["ema_fast"] < dataframe["ema_slow"])
                & (dataframe["ema_fast"].shift(1) >= dataframe["ema_slow"].shift(1))
            )
            |
            # RSI overbought
            (dataframe["rsi"] > 70)
        )

        # AI exit conditions (direction changes or low confidence)
        if ai_signal:
            ai_exit = (
                (ai_signal.direction.lower() in ["short", "neutral"])
                & (ai_signal.confidence >= 0.65)  # Slightly higher threshold for exit
            )

            # Exit if technical OR AI says exit
            dataframe.loc[technical_exit | ai_exit, "exit_long"] = 1

            if ai_exit:
                print(
                    f"✓ AI EXIT signal for {metadata['pair']}: "
                    f"direction={ai_signal.direction}, "
                    f"confidence={ai_signal.confidence:.1%}"
                )
        else:
            # Fallback to technical-only
            dataframe.loc[technical_exit, "exit_long"] = 1

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
        Adjust position size based on AI confidence.

        Higher AI confidence = larger position size (within limits)

        Args:
            pair: Trading pair
            proposed_stake: Base stake amount from config
            ... (other Freqtrade parameters)

        Returns:
            Adjusted stake amount
        """
        # Get cached AI signal (should exist from populate_entry_trend)
        if pair in self.ai_signal_cache:
            signal = self.ai_signal_cache[pair]["signal"]

            if signal and signal.confidence >= self.ai_min_confidence:
                # Calculate multiplier based on confidence
                # 50% confidence → 0.8x stake
                # 75% confidence → 1.0x stake
                # 100% confidence → 1.2x stake
                # Formula: normalize confidence (0.5-1.0) to multiplier range (0.8-1.2)
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
                # At 60%: (0.6-0.6)/(1-0.6) = 0.0 → 0.8 + 0.0*(1.2-0.8) = 0.8x
                # At 80%: (0.8-0.6)/(1-0.6) = 0.5 → 0.8 + 0.5*0.4 = 1.0x
                # At 100%: (1.0-0.6)/(1-0.6) = 1.0 → 0.8 + 1.0*0.4 = 1.2x

                adjusted_stake = proposed_stake * multiplier

                # Ensure within min/max bounds
                if min_stake and adjusted_stake < min_stake:
                    adjusted_stake = min_stake
                if adjusted_stake > max_stake:
                    adjusted_stake = max_stake

                print(
                    f"💰 Position sizing for {pair}: "
                    f"base={proposed_stake:.2f} → "
                    f"adjusted={adjusted_stake:.2f} "
                    f"(AI confidence={signal.confidence:.1%}, multiplier={multiplier:.2f}x)"
                )

                return adjusted_stake

        # Fallback to base stake if no AI signal
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
        # Check if AI signal is still cached and valid
        if pair in self.ai_signal_cache:
            cached = self.ai_signal_cache[pair]
            signal = cached["signal"]
            age_minutes = (
                datetime.now(timezone.utc) - cached["timestamp"]
            ).total_seconds() / 60

            # Reject if signal expired or confidence dropped
            if age_minutes >= self.ai_cache_minutes:
                print(
                    f"✗ Rejecting {pair} entry: AI signal expired ({age_minutes:.1f} min old)"
                )
                return False

            if signal.confidence < self.ai_min_confidence:
                print(
                    f"✗ Rejecting {pair} entry: AI confidence too low ({signal.confidence:.1%})"
                )
                return False

            if signal.direction.lower() != "long":
                print(
                    f"✗ Rejecting {pair} entry: AI direction changed to {signal.direction}"
                )
                return False

        # Allow entry if all checks pass
        return True
