"""
Claude (Anthropic) Provider

Implements Claude for risk assessment and market analysis.
Weight in consensus: 35%
"""

from typing import Dict, Any, Optional
import json
from anthropic import Anthropic
from .base import BaseLLMProvider, MarketAnalysis, OHLCVData
import pandas as pd


class ClaudeProvider(BaseLLMProvider):
    """Claude provider for risk assessment and analysis"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize Claude provider.

        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-3-5-sonnet-20241022)
        """
        self.client = None
        super().__init__(api_key, model)

    @property
    def provider_name(self) -> str:
        return "claude"

    def _validate_api_key(self) -> None:
        """Validate Anthropic API key format"""
        if not self.api_key or not self.api_key.startswith('sk-ant-'):
            raise ValueError("Invalid Anthropic API key format (should start with 'sk-ant-')")

        # Initialize Anthropic client
        self.client = Anthropic(api_key=self.api_key)

    def _call_api(self, prompt: str) -> str:
        """
        Call Anthropic Claude API.

        Args:
            prompt: Formatted prompt

        Returns:
            Raw text response
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.3,
                system="You are an expert cryptocurrency risk analyst. Analyze market conditions and assess risk/reward ratios. Provide responses in JSON format with keys: direction, confidence, technical_summary, risk_assessment, sentiment, reasoning.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract text from response
            return response.content[0].text

        except Exception as e:
            raise RuntimeError(f"Claude API call failed: {e}")

    def analyze_market(
        self,
        ohlcv_data: OHLCVData,
        prompt_template: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> MarketAnalysis:
        """
        Analyze market using Claude.

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
            additional_context=json.dumps(additional_context) if additional_context else ""
        )

        # Call API
        raw_response = self._call_api(full_prompt)

        # Parse JSON response
        return self._parse_json_response(raw_response, ohlcv_data)

    def _parse_json_response(self, raw_response: str, ohlcv_data: OHLCVData) -> MarketAnalysis:
        """
        Parse JSON response from Claude.

        Args:
            raw_response: JSON string from Claude
            ohlcv_data: Original OHLCV data

        Returns:
            MarketAnalysis object
        """
        try:
            # Try to find JSON in response (Claude sometimes wraps in markdown)
            response_text = raw_response.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()

            data = json.loads(response_text)

            # Extract fields with defaults
            direction = data.get('direction', 'neutral').lower()
            confidence = float(data.get('confidence', 0.5))

            # Validate direction
            if direction not in ['long', 'short', 'neutral']:
                direction = 'neutral'

            # Clamp confidence to [0, 1]
            confidence = max(0.0, min(1.0, confidence))

            return MarketAnalysis(
                direction=direction,
                confidence=confidence,
                technical_summary=data.get('technical_summary', ''),
                risk_assessment=data.get('risk_assessment', ''),
                sentiment=data.get('sentiment', 'neutral'),
                reasoning=data.get('reasoning', raw_response),
                provider=self.provider_name,
                timestamp=pd.Timestamp.now(),
                pair=ohlcv_data.pair,
                timeframe=ohlcv_data.timeframe,
                raw_response=raw_response
            )

        except (json.JSONDecodeError, ValueError) as e:
            # Fallback to base class parsing if JSON parsing fails
            print(f"Claude JSON parsing failed: {e}")
            return self._parse_response(raw_response, ohlcv_data)
