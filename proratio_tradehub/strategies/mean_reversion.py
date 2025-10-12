"""
Mean Reversion Strategy

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

from typing import Dict
import pandas as pd

from proratio_tradehub.strategies.base_strategy import BaseStrategy, TradeSignal
from proratio_signals import SignalOrchestrator


class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion strategy using RSI and Bollinger Bands.

    Parameters:
    - rsi_oversold: RSI threshold for oversold (default: 30)
    - rsi_overbought: RSI threshold for overbought (default: 70)
    - bb_std: Bollinger Bands standard deviation (default: 2.0)
    - use_ai_confirmation: Whether to require AI signal confirmation (default: True)
    - ai_confidence_threshold: Minimum AI confidence required (default: 0.5)
    """

    def __init__(
        self,
        name: str = "MeanReversion",
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
        bb_std: float = 2.0,
        use_ai_confirmation: bool = True,
        ai_confidence_threshold: float = 0.5,
    ):
        """
        Initialize Mean Reversion Strategy.

        Args:
            name: Strategy name
            rsi_oversold: RSI level below which market is oversold
            rsi_overbought: RSI level above which market is overbought
            bb_std: Bollinger Bands standard deviation multiplier
            use_ai_confirmation: Whether to use AI signals for confirmation
            ai_confidence_threshold: Minimum AI confidence to confirm trade
        """
        super().__init__(name)

        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.bb_std = bb_std
        self.use_ai_confirmation = use_ai_confirmation
        self.ai_confidence_threshold = ai_confidence_threshold

        # Initialize AI orchestrator if needed
        self.orchestrator = None
        if self.use_ai_confirmation:
            try:
                self.orchestrator = SignalOrchestrator()
            except Exception as e:
                print(f"Warning: Could not initialize AI orchestrator: {e}")
                self.use_ai_confirmation = False

        self.config = {
            "rsi_oversold": rsi_oversold,
            "rsi_overbought": rsi_overbought,
            "bb_std": bb_std,
            "use_ai_confirmation": use_ai_confirmation,
            "ai_confidence_threshold": ai_confidence_threshold,
        }

    def should_enter_long(
        self, pair: str, dataframe: pd.DataFrame, **kwargs
    ) -> TradeSignal:
        """
        Check if conditions are met for long entry (buy).

        Long Entry Conditions:
        1. RSI is oversold (< 30)
        2. Price is below lower Bollinger Band
        3. (Optional) AI confirms bullish signal

        Args:
            pair: Trading pair
            dataframe: OHLCV data with indicators
            **kwargs: Additional context

        Returns:
            TradeSignal indicating whether to enter long
        """
        # Get latest values
        current_price = dataframe["close"].iloc[-1]
        rsi = dataframe["rsi"].iloc[-1]
        bb_lower = dataframe["bb_lower"].iloc[-1]
        bb_middle = dataframe["bb_middle"].iloc[-1]

        # Check technical conditions
        is_oversold = rsi < self.rsi_oversold
        below_bb = current_price < bb_lower

        if not (is_oversold and below_bb):
            return TradeSignal(
                direction="neutral",
                confidence=0.0,
                reasoning=f"Not oversold (RSI={rsi:.1f}) or not below BB_lower",
            )

        # Calculate base confidence from technical indicators
        # More oversold = higher confidence, more deviation from BB = higher confidence
        rsi_confidence = max(0, (self.rsi_oversold - rsi) / self.rsi_oversold)  # 0-1
        bb_deviation = abs(current_price - bb_lower) / bb_middle
        bb_confidence = min(1.0, bb_deviation * 10)  # Scale to 0-1

        technical_confidence = (rsi_confidence + bb_confidence) / 2

        # AI confirmation (optional)
        ai_confidence = 0.0
        ai_reasoning = ""

        if self.use_ai_confirmation and self.orchestrator:
            try:
                ai_signal = self.orchestrator.generate_signal(pair, dataframe)

                if ai_signal.direction == "long":
                    ai_confidence = ai_signal.confidence
                    ai_reasoning = f"AI confirms LONG ({ai_confidence:.1%})"

                    # Blend technical and AI confidence
                    final_confidence = (technical_confidence * 0.4) + (
                        ai_confidence * 0.6
                    )
                else:
                    # AI disagrees or is neutral
                    final_confidence = technical_confidence * 0.5  # Reduce confidence
                    ai_reasoning = f"AI disagrees: {ai_signal.direction} ({ai_signal.confidence:.1%})"

            except Exception as e:
                # AI unavailable, use technical only
                final_confidence = technical_confidence
                ai_reasoning = f"AI unavailable: {str(e)}"

        else:
            final_confidence = technical_confidence
            ai_reasoning = "AI confirmation disabled"

        # Check if confidence meets threshold
        meets_threshold = final_confidence >= self.ai_confidence_threshold

        reasoning = (
            f"Mean Reversion LONG signal:\n"
            f"  RSI: {rsi:.1f} (oversold < {self.rsi_oversold})\n"
            f"  Price: ${current_price:.2f} (< BB_lower ${bb_lower:.2f})\n"
            f"  Technical confidence: {technical_confidence:.1%}\n"
            f"  {ai_reasoning}\n"
            f"  Final confidence: {final_confidence:.1%} ({'✓' if meets_threshold else '✗'} threshold {self.ai_confidence_threshold:.1%})"
        )

        return TradeSignal(
            direction="long" if meets_threshold else "neutral",
            confidence=final_confidence,
            entry_price=current_price,
            stop_loss=self.calculate_stop_loss(pair, current_price, "long", dataframe),
            take_profit=self.calculate_take_profit(
                pair, current_price, "long", dataframe
            ),
            position_size_multiplier=final_confidence,  # Higher confidence = larger position
            reasoning=reasoning,
        )

    def should_enter_short(
        self, pair: str, dataframe: pd.DataFrame, **kwargs
    ) -> TradeSignal:
        """
        Check if conditions are met for short entry (sell).

        Short Entry Conditions:
        1. RSI is overbought (> 70)
        2. Price is above upper Bollinger Band
        3. (Optional) AI confirms bearish signal

        Args:
            pair: Trading pair
            dataframe: OHLCV data with indicators
            **kwargs: Additional context

        Returns:
            TradeSignal indicating whether to enter short
        """
        # Get latest values
        current_price = dataframe["close"].iloc[-1]
        rsi = dataframe["rsi"].iloc[-1]
        bb_upper = dataframe["bb_upper"].iloc[-1]
        bb_middle = dataframe["bb_middle"].iloc[-1]

        # Check technical conditions
        is_overbought = rsi > self.rsi_overbought
        above_bb = current_price > bb_upper

        if not (is_overbought and above_bb):
            return TradeSignal(
                direction="neutral",
                confidence=0.0,
                reasoning=f"Not overbought (RSI={rsi:.1f}) or not above BB_upper",
            )

        # Calculate base confidence from technical indicators
        rsi_confidence = max(
            0, (rsi - self.rsi_overbought) / (100 - self.rsi_overbought)
        )
        bb_deviation = abs(current_price - bb_upper) / bb_middle
        bb_confidence = min(1.0, bb_deviation * 10)

        technical_confidence = (rsi_confidence + bb_confidence) / 2

        # AI confirmation (optional)
        ai_confidence = 0.0
        ai_reasoning = ""

        if self.use_ai_confirmation and self.orchestrator:
            try:
                ai_signal = self.orchestrator.generate_signal(pair, dataframe)

                if ai_signal.direction == "short":
                    ai_confidence = ai_signal.confidence
                    ai_reasoning = f"AI confirms SHORT ({ai_confidence:.1%})"
                    final_confidence = (technical_confidence * 0.4) + (
                        ai_confidence * 0.6
                    )
                else:
                    final_confidence = technical_confidence * 0.5
                    ai_reasoning = f"AI disagrees: {ai_signal.direction} ({ai_signal.confidence:.1%})"

            except Exception as e:
                final_confidence = technical_confidence
                ai_reasoning = f"AI unavailable: {str(e)}"
        else:
            final_confidence = technical_confidence
            ai_reasoning = "AI confirmation disabled"

        meets_threshold = final_confidence >= self.ai_confidence_threshold

        reasoning = (
            f"Mean Reversion SHORT signal:\n"
            f"  RSI: {rsi:.1f} (overbought > {self.rsi_overbought})\n"
            f"  Price: ${current_price:.2f} (> BB_upper ${bb_upper:.2f})\n"
            f"  Technical confidence: {technical_confidence:.1%}\n"
            f"  {ai_reasoning}\n"
            f"  Final confidence: {final_confidence:.1%} ({'✓' if meets_threshold else '✗'} threshold {self.ai_confidence_threshold:.1%})"
        )

        return TradeSignal(
            direction="short" if meets_threshold else "neutral",
            confidence=final_confidence,
            entry_price=current_price,
            stop_loss=self.calculate_stop_loss(pair, current_price, "short", dataframe),
            take_profit=self.calculate_take_profit(
                pair, current_price, "short", dataframe
            ),
            position_size_multiplier=final_confidence,
            reasoning=reasoning,
        )

    def should_exit(
        self, pair: str, dataframe: pd.DataFrame, current_position: Dict, **kwargs
    ) -> TradeSignal:
        """
        Determine if strategy should exit current position.

        Exit Conditions:
        - Price returns to mean (middle Bollinger Band)
        - RSI returns to neutral zone (40-60)
        - Stop-loss or take-profit hit (handled by risk manager)

        Args:
            pair: Trading pair
            dataframe: OHLCV data with indicators
            current_position: Current position details
            **kwargs: Additional context

        Returns:
            TradeSignal indicating whether to exit
        """
        current_price = dataframe["close"].iloc[-1]
        rsi = dataframe["rsi"].iloc[-1]
        bb_middle = dataframe["bb_middle"].iloc[-1]

        entry_price = current_position.get("entry_price")
        side = current_position.get("side", "long")

        # Check if price returned to mean
        price_near_mean = abs(current_price - bb_middle) / bb_middle < 0.01  # Within 1%

        # Check if RSI returned to neutral
        rsi_neutral = 40 < rsi < 60

        should_exit = price_near_mean or rsi_neutral

        if should_exit:
            profit_pct = (
                ((current_price - entry_price) / entry_price * 100)
                if side == "long"
                else ((entry_price - current_price) / entry_price * 100)
            )

            reasoning = (
                f"Mean Reversion EXIT signal:\n"
                f"  Price returned to mean: {price_near_mean}\n"
                f"  RSI neutral: {rsi_neutral} (RSI={rsi:.1f})\n"
                f"  Current P&L: {profit_pct:+.2f}%"
            )

            return TradeSignal(direction="exit", confidence=0.8, reasoning=reasoning)

        return TradeSignal(
            direction="neutral",
            confidence=0.0,
            reasoning=f"Hold position (RSI={rsi:.1f}, price=${current_price:.2f} vs mean=${bb_middle:.2f})",
        )

    def get_required_indicators(self) -> list:
        """
        Return list of required technical indicators.

        Returns:
            List of indicator names needed for this strategy
        """
        return [
            "rsi",  # Relative Strength Index
            "bb_upper",  # Bollinger Bands upper
            "bb_middle",  # Bollinger Bands middle (SMA)
            "bb_lower",  # Bollinger Bands lower
        ]

    def __repr__(self) -> str:
        return (
            f"MeanReversionStrategy("
            f"rsi_oversold={self.rsi_oversold}, "
            f"rsi_overbought={self.rsi_overbought}, "
            f"bb_std={self.bb_std}, "
            f"ai_confirmation={self.use_ai_confirmation})"
        )
