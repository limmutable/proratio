"""
Base LLM Provider Interface

Abstract base class for all LLM providers (ChatGPT, Claude, Gemini).
Ensures consistent interface across different AI services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd


@dataclass
class MarketAnalysis:
    """Standardized market analysis response from LLM"""

    # Signal information
    direction: str  # 'long', 'short', 'neutral'
    confidence: float  # 0.0 - 1.0

    # Analysis details
    technical_summary: str
    risk_assessment: str
    sentiment: str
    reasoning: str

    # Metadata
    provider: str  # 'chatgpt', 'claude', 'gemini'
    timestamp: datetime
    pair: str
    timeframe: str

    # Raw response (for debugging)
    raw_response: Optional[str] = None


@dataclass
class OHLCVData:
    """OHLCV data container for LLM analysis"""

    pair: str
    timeframe: str
    data: pd.DataFrame  # columns: timestamp, open, high, low, close, volume
    indicators: Optional[Dict[str, Any]] = None  # Pre-calculated indicators

    def to_summary_text(self, lookback: int = 20) -> str:
        """Convert recent OHLCV data to text summary for LLM"""
        recent = self.data.tail(lookback)

        current_price = recent["close"].iloc[-1]
        price_change_pct = (
            (current_price - recent["close"].iloc[0]) / recent["close"].iloc[0]
        ) * 100
        high_24h = recent["high"].max()
        low_24h = recent["low"].min()
        avg_volume = recent["volume"].mean()

        summary = f"""
Pair: {self.pair}
Timeframe: {self.timeframe}
Current Price: ${current_price:,.2f}
Price Change ({lookback} periods): {price_change_pct:+.2f}%
24h High: ${high_24h:,.2f}
24h Low: ${low_24h:,.2f}
Average Volume: {avg_volume:,.0f}
"""

        if self.indicators:
            summary += "\nTechnical Indicators:\n"
            for key, value in self.indicators.items():
                if isinstance(value, (int, float)):
                    summary += f"  {key}: {value:.2f}\n"
                else:
                    summary += f"  {key}: {value}\n"

        return summary.strip()


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, api_key: str, model: Optional[str] = None):
        """
        Initialize LLM provider.

        Args:
            api_key: API key for the LLM service
            model: Model name/version (provider-specific)
        """
        self.api_key = api_key
        self.model = model
        self._validate_api_key()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'chatgpt', 'claude', 'gemini')"""
        pass

    @abstractmethod
    def _validate_api_key(self) -> None:
        """Validate API key format (basic check)"""
        pass

    @abstractmethod
    def analyze_market(
        self,
        ohlcv_data: OHLCVData,
        prompt_template: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> MarketAnalysis:
        """
        Analyze market data and return structured analysis.

        Args:
            ohlcv_data: OHLCV data with indicators
            prompt_template: Formatted prompt for the LLM
            additional_context: Extra context (news, sentiment, etc.)

        Returns:
            MarketAnalysis object with standardized response
        """
        pass

    @abstractmethod
    def _call_api(self, prompt: str) -> str:
        """
        Make API call to LLM service.

        Args:
            prompt: Complete prompt text

        Returns:
            Raw text response from LLM
        """
        pass

    def _parse_response(
        self, raw_response: str, ohlcv_data: OHLCVData
    ) -> MarketAnalysis:
        """
        Parse LLM response into structured MarketAnalysis.

        Default implementation - can be overridden by subclasses.

        Args:
            raw_response: Raw text from LLM
            ohlcv_data: Original OHLCV data for context

        Returns:
            MarketAnalysis object
        """
        # Simple parsing logic - expect JSON-like response
        # Subclasses should override for provider-specific parsing

        # Default values
        direction = "neutral"
        confidence = 0.5
        technical_summary = ""
        risk_assessment = ""
        sentiment = ""
        reasoning = raw_response

        # Try to extract structured data from response
        response_lower = raw_response.lower()

        # Extract direction
        if (
            "long" in response_lower
            or "buy" in response_lower
            or "bullish" in response_lower
        ):
            direction = "long"
        elif (
            "short" in response_lower
            or "sell" in response_lower
            or "bearish" in response_lower
        ):
            direction = "short"

        # Extract confidence (look for percentages or confidence indicators)
        if "high confidence" in response_lower or "strong signal" in response_lower:
            confidence = 0.8
        elif "medium confidence" in response_lower or "moderate" in response_lower:
            confidence = 0.6
        elif "low confidence" in response_lower or "weak signal" in response_lower:
            confidence = 0.4

        return MarketAnalysis(
            direction=direction,
            confidence=confidence,
            technical_summary=technical_summary or raw_response[:200],
            risk_assessment=risk_assessment or "Not specified",
            sentiment=sentiment or "Neutral",
            reasoning=reasoning,
            provider=self.provider_name,
            timestamp=datetime.now(),
            pair=ohlcv_data.pair,
            timeframe=ohlcv_data.timeframe,
            raw_response=raw_response,
        )

    def test_connection(self) -> bool:
        """
        Test API connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Simple test prompt
            response = self._call_api(
                "Hello, please respond with 'OK' if you can read this."
            )
            return len(response) > 0
        except Exception as e:
            print(f"Connection test failed for {self.provider_name}: {e}")
            return False
