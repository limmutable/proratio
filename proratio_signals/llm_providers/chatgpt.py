"""
ChatGPT (OpenAI) Provider

Implements ChatGPT-4 for technical pattern recognition and market analysis.
Weight in consensus: 40%
"""

from typing import Dict, Any, Optional
import json
from openai import OpenAI
from .base import BaseLLMProvider, MarketAnalysis, OHLCVData


class ChatGPTProvider(BaseLLMProvider):
    """ChatGPT-4 provider for technical analysis"""

    def __init__(self, api_key: str, model: str = "gpt-5-nano-2025-08-07"):
        """
        Initialize ChatGPT provider.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-mini - fast and cost-effective)
        """
        self.client = None
        super().__init__(api_key, model)

    @property
    def provider_name(self) -> str:
        return "chatgpt"

    def _validate_api_key(self) -> None:
        """Validate OpenAI API key format"""
        if not self.api_key or not self.api_key.startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format (should start with 'sk-')")

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)

    def _call_api(self, prompt: str) -> str:
        """
        Call OpenAI ChatGPT API.

        Args:
            prompt: Formatted prompt

        Returns:
            Raw text response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert cryptocurrency technical analyst. Analyze market data and provide clear, actionable trading signals.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=1000,
                response_format={"type": "json_object"},  # Request JSON response
            )

            return response.choices[0].message.content

        except Exception as e:
            raise RuntimeError(f"ChatGPT API call failed: {e}")

    def analyze_market(
        self,
        ohlcv_data: OHLCVData,
        prompt_template: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> MarketAnalysis:
        """
        Analyze market using ChatGPT.

        Args:
            ohlcv_data: OHLCV data with indicators
            prompt_template: Prompt template
            additional_context: Extra context

        Returns:
            MarketAnalysis with structured response
        """
        # Build complete prompt
        market_summary = ohlcv_data.to_summary_text(lookback=20)

        full_prompt = prompt_template.format(
            market_data=market_summary,
            pair=ohlcv_data.pair,
            timeframe=ohlcv_data.timeframe,
            additional_context=json.dumps(additional_context)
            if additional_context
            else "",
        )

        # Call API
        raw_response = self._call_api(full_prompt)

        # Parse JSON response
        return self._parse_json_response(raw_response, ohlcv_data)

    def _parse_json_response(
        self, raw_response: str, ohlcv_data: OHLCVData
    ) -> MarketAnalysis:
        """
        Parse JSON response from ChatGPT.

        Args:
            raw_response: JSON string from ChatGPT
            ohlcv_data: Original OHLCV data

        Returns:
            MarketAnalysis object
        """
        try:
            data = json.loads(raw_response)

            # Extract fields with defaults
            direction = data.get("direction", "neutral").lower()
            confidence = float(data.get("confidence", 0.5))

            # Validate direction
            if direction not in ["long", "short", "neutral"]:
                direction = "neutral"

            # Clamp confidence to [0, 1]
            confidence = max(0.0, min(1.0, confidence))

            return MarketAnalysis(
                direction=direction,
                confidence=confidence,
                technical_summary=data.get("technical_summary", ""),
                risk_assessment=data.get("risk_assessment", ""),
                sentiment=data.get("sentiment", "neutral"),
                reasoning=data.get("reasoning", raw_response),
                provider=self.provider_name,
                timestamp=pd.Timestamp.now(),
                pair=ohlcv_data.pair,
                timeframe=ohlcv_data.timeframe,
                raw_response=raw_response,
            )

        except json.JSONDecodeError as e:
            # Fallback to base class parsing if JSON parsing fails
            print(f"ChatGPT JSON parsing failed: {e}")
            return self._parse_response(raw_response, ohlcv_data)


# Import pandas for timestamp
import pandas as pd
