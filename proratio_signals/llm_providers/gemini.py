"""
Gemini (Google) Provider

Implements Google Gemini for market sentiment and trend analysis.
Weight in consensus: 25%
"""

from typing import Dict, Any, Optional
import json
import google.generativeai as genai
from .base import BaseLLMProvider, MarketAnalysis, OHLCVData
import pandas as pd


class GeminiProvider(BaseLLMProvider):
    """Gemini provider for sentiment and trend analysis"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key
            model: Model to use (default: gemini-2.0-flash-exp - fast and efficient)
        """
        self.model_instance = None
        super().__init__(api_key, model)

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _validate_api_key(self) -> None:
        """Validate Google API key format"""
        if not self.api_key or len(self.api_key) < 20:
            raise ValueError("Invalid Google API key format")

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model_instance = genai.GenerativeModel(self.model)

    def _call_api(self, prompt: str) -> str:
        """
        Call Google Gemini API.

        Args:
            prompt: Formatted prompt

        Returns:
            Raw text response
        """
        try:
            # Add JSON format instruction to prompt
            json_prompt = f"""{prompt}

IMPORTANT: Respond ONLY with valid JSON in this exact format:
{{
    "direction": "long" or "short" or "neutral",
    "confidence": 0.0 to 1.0,
    "technical_summary": "brief technical analysis",
    "risk_assessment": "risk evaluation",
    "sentiment": "bullish" or "bearish" or "neutral",
    "reasoning": "detailed reasoning"
}}"""

            response = self.model_instance.generate_content(
                json_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1024,
                ),
            )

            return response.text

        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {e}")

    def analyze_market(
        self,
        ohlcv_data: OHLCVData,
        prompt_template: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> MarketAnalysis:
        """
        Analyze market using Gemini.

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
        Parse JSON response from Gemini.

        Args:
            raw_response: JSON string from Gemini
            ohlcv_data: Original OHLCV data

        Returns:
            MarketAnalysis object
        """
        try:
            # Clean up response
            response_text = raw_response.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = (
                    response_text.replace("```json", "").replace("```", "").strip()
                )
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            # Find JSON object in response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                data = json.loads(json_str)
            else:
                data = json.loads(response_text)

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

        except (json.JSONDecodeError, ValueError) as e:
            # Fallback to base class parsing if JSON parsing fails
            print(f"Gemini JSON parsing failed: {e}")
            return self._parse_response(raw_response, ohlcv_data)
