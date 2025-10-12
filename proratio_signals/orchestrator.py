"""
AI Signal Orchestrator

Coordinates multiple LLM providers and implements weighted consensus mechanism.

Weight Distribution:
- ChatGPT: 40% (Technical pattern recognition)
- Claude: 35% (Risk assessment)
- Gemini: 25% (Market sentiment)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import pandas as pd
from datetime import datetime

from .llm_providers.base import BaseLLMProvider, MarketAnalysis, OHLCVData
from .llm_providers.chatgpt import ChatGPTProvider
from .llm_providers.claude import ClaudeProvider
from .llm_providers.gemini import GeminiProvider
from .prompts import (
    TECHNICAL_ANALYSIS_PROMPT,
    RISK_ASSESSMENT_PROMPT,
    SENTIMENT_ANALYSIS_PROMPT,
)
from proratio_utilities.config.settings import get_settings


@dataclass
class ConsensusSignal:
    """Consensus signal from multiple AI providers"""

    # Final consensus
    direction: str  # 'long', 'short', 'neutral'
    confidence: float  # 0.0 - 1.0 (weighted average)
    consensus_score: float  # 0.0 - 1.0 (agreement level)

    # Individual analyses
    chatgpt_analysis: Optional[MarketAnalysis] = None
    claude_analysis: Optional[MarketAnalysis] = None
    gemini_analysis: Optional[MarketAnalysis] = None

    # Aggregated insights
    combined_reasoning: str = ""
    risk_summary: str = ""
    technical_summary: str = ""

    # Metadata
    timestamp: datetime = None
    pair: str = ""
    timeframe: str = ""

    # Provider status
    active_providers: List[str] = None  # Which providers responded
    failed_providers: List[str] = None  # Which providers failed
    provider_models: Dict[str, str] = None  # Model used by each provider

    def should_trade(self, threshold: float = 0.6) -> bool:
        """
        Determine if consensus is strong enough to trade.

        Args:
            threshold: Minimum consensus score (default: 0.6)

        Returns:
            True if consensus score >= threshold and direction is not neutral
        """
        return (
            self.consensus_score >= threshold
            and self.direction != "neutral"
            and self.confidence >= threshold
        )

    def get_provider_status_report(self) -> str:
        """
        Get formatted provider status report.

        Returns:
            Formatted string with provider status, models, and failure info
        """
        from proratio_signals.orchestrator import SignalOrchestrator

        report = []
        report.append("\n" + "=" * 70)
        report.append("  AI PROVIDER STATUS")
        report.append("=" * 70)

        # Active providers
        if self.active_providers:
            report.append(
                f"\n✓ Active: {len(self.active_providers)}/{len(self.active_providers) + len(self.failed_providers or [])}"
            )
            for provider in self.active_providers:
                model = self.provider_models.get(provider, "unknown")
                weight = SignalOrchestrator.WEIGHTS.get(provider, 0)
                report.append(f"  → {provider}: {model} ({weight:.0%} weight)")

        # Failed providers
        if self.failed_providers:
            report.append(f"\n✗ Failed: {', '.join(self.failed_providers)}")

        # Overall status
        if not self.active_providers:
            report.append("\n❌ No providers active - check API keys and quotas")

        report.append("=" * 70)
        return "\n".join(report)


class SignalOrchestrator:
    """Orchestrates multiple AI providers for consensus signal generation"""

    # Provider weights (must sum to 1.0)
    WEIGHTS = {
        "chatgpt": 0.40,  # Technical analysis
        "claude": 0.35,  # Risk assessment
        "gemini": 0.25,  # Sentiment
    }

    def __init__(
        self,
        chatgpt_key: Optional[str] = None,
        claude_key: Optional[str] = None,
        gemini_key: Optional[str] = None,
        consensus_threshold: float = 0.6,
    ):
        """
        Initialize signal orchestrator.

        Args:
            chatgpt_key: OpenAI API key (or load from settings)
            claude_key: Anthropic API key (or load from settings)
            gemini_key: Google API key (or load from settings)
            consensus_threshold: Minimum consensus score to generate signal
        """
        settings = get_settings()

        # Initialize providers
        self.providers: Dict[str, BaseLLMProvider] = {}

        # ChatGPT - Technical Analysis (40%)
        if chatgpt_key or settings.openai_api_key:
            try:
                self.providers["chatgpt"] = ChatGPTProvider(
                    api_key=chatgpt_key or settings.openai_api_key
                )
            except ValueError as e:
                print(f"ChatGPT initialization failed: {e}")

        # Claude - Risk Assessment (35%)
        if claude_key or settings.anthropic_api_key:
            try:
                self.providers["claude"] = ClaudeProvider(
                    api_key=claude_key or settings.anthropic_api_key
                )
            except ValueError as e:
                print(f"Claude initialization failed: {e}")

        # Gemini - Sentiment (25%)
        if gemini_key or settings.gemini_api_key:
            try:
                self.providers["gemini"] = GeminiProvider(
                    api_key=gemini_key or settings.gemini_api_key
                )
            except ValueError as e:
                print(f"Gemini initialization failed: {e}")

        self.consensus_threshold = consensus_threshold

        # Validate at least one provider is available
        if not self.providers:
            raise ValueError(
                "No AI providers initialized. Check API keys in .env file."
            )

    def generate_signal(
        self,
        pair: str,
        timeframe: str,
        ohlcv_data: pd.DataFrame,
        indicators: Optional[Dict] = None,
    ) -> ConsensusSignal:
        """
        Generate consensus signal from multiple AI providers.

        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '1h', '4h')
            ohlcv_data: DataFrame with OHLCV data
            indicators: Pre-calculated indicators

        Returns:
            ConsensusSignal with weighted consensus
        """
        # Prepare OHLCV data
        ohlcv = OHLCVData(
            pair=pair, timeframe=timeframe, data=ohlcv_data, indicators=indicators
        )

        # Collect analyses from each provider
        analyses = {}
        failed_providers = []
        provider_models = {}
        failure_reasons = {}

        print("\n" + "=" * 70)
        print("  AI PROVIDER ANALYSIS")
        print("=" * 70)

        # ChatGPT: Technical Analysis
        if "chatgpt" in self.providers:
            try:
                print(
                    f"\n→ ChatGPT ({self.providers['chatgpt'].model})... ",
                    end="",
                    flush=True,
                )
                analyses["chatgpt"] = self.providers["chatgpt"].analyze_market(
                    ohlcv_data=ohlcv, prompt_template=TECHNICAL_ANALYSIS_PROMPT
                )
                provider_models["chatgpt"] = self.providers["chatgpt"].model
                print("✓")
            except Exception as e:
                error_msg = str(e)
                # Extract key error info
                if "quota" in error_msg.lower():
                    reason = (
                        "Quota exceeded - add credits at platform.openai.com/billing"
                    )
                elif "429" in error_msg:
                    reason = "Rate limit or quota exceeded"
                elif "404" in error_msg:
                    reason = "Model not found or not accessible"
                elif "401" in error_msg:
                    reason = "Invalid API key"
                else:
                    reason = error_msg[:100]

                failure_reasons["chatgpt"] = reason
                failed_providers.append("chatgpt")
                print(f"✗\n  Error: {reason}")

        # Claude: Risk Assessment
        if "claude" in self.providers:
            try:
                print(
                    f"\n→ Claude ({self.providers['claude'].model})... ",
                    end="",
                    flush=True,
                )
                analyses["claude"] = self.providers["claude"].analyze_market(
                    ohlcv_data=ohlcv, prompt_template=RISK_ASSESSMENT_PROMPT
                )
                provider_models["claude"] = self.providers["claude"].model
                print("✓")
            except Exception as e:
                error_msg = str(e)
                if "overloaded" in error_msg.lower():
                    reason = "Service overloaded - try again in a moment"
                elif "401" in error_msg:
                    reason = "Invalid API key"
                elif "429" in error_msg:
                    reason = "Rate limit exceeded"
                else:
                    reason = error_msg[:100]

                failure_reasons["claude"] = reason
                failed_providers.append("claude")
                print(f"✗\n  Error: {reason}")

        # Gemini: Sentiment
        if "gemini" in self.providers:
            try:
                print(
                    f"\n→ Gemini ({self.providers['gemini'].model})... ",
                    end="",
                    flush=True,
                )
                analyses["gemini"] = self.providers["gemini"].analyze_market(
                    ohlcv_data=ohlcv, prompt_template=SENTIMENT_ANALYSIS_PROMPT
                )
                provider_models["gemini"] = self.providers["gemini"].model
                print("✓")
            except Exception as e:
                error_msg = str(e)
                if "finish_reason" in error_msg.lower() and "2" in error_msg:
                    reason = (
                        "Safety filter blocked - content flagged as financial advice"
                    )
                elif "404" in error_msg:
                    reason = "Model not found - check model name"
                elif "401" in error_msg:
                    reason = "Invalid API key"
                else:
                    reason = error_msg[:100]

                failure_reasons["gemini"] = reason
                failed_providers.append("gemini")
                print(f"✗\n  Error: {reason}")

        # Show final status
        print("\n" + "=" * 70)
        if analyses:
            print(
                f"✓ Active: {', '.join(analyses.keys())} ({len(analyses)}/{len(self.providers)})"
            )
        if failed_providers:
            print(f"✗ Failed: {', '.join(failed_providers)}")
            for provider in failed_providers:
                print(
                    f"  → {provider}: {failure_reasons.get(provider, 'Unknown error')}"
                )
        print("=" * 70)

        # Calculate consensus
        return self._calculate_consensus(
            analyses, pair, timeframe, failed_providers, provider_models
        )

    def _calculate_consensus(
        self,
        analyses: Dict[str, MarketAnalysis],
        pair: str,
        timeframe: str,
        failed_providers: List[str] = None,
        provider_models: Dict[str, str] = None,
    ) -> ConsensusSignal:
        """
        Calculate weighted consensus from individual analyses with dynamic reweighting.

        Args:
            analyses: Dict of provider name -> MarketAnalysis
            pair: Trading pair
            timeframe: Timeframe
            failed_providers: List of providers that failed
            provider_models: Dict of provider -> model name

        Returns:
            ConsensusSignal with weighted results
        """
        failed_providers = failed_providers or []
        provider_models = provider_models or {}

        if not analyses:
            # No analyses available - return neutral
            return ConsensusSignal(
                direction="neutral",
                confidence=0.0,
                consensus_score=0.0,
                combined_reasoning="❌ No AI providers available",
                timestamp=datetime.now(),
                pair=pair,
                timeframe=timeframe,
                active_providers=[],
                failed_providers=failed_providers,
                provider_models=provider_models,
            )

        # Calculate weighted direction scores with dynamic reweighting
        direction_scores = {"long": 0.0, "short": 0.0, "neutral": 0.0}
        weighted_confidence = 0.0
        total_weight = 0.0
        active_providers = list(analyses.keys())

        for provider_name, analysis in analyses.items():
            weight = self.WEIGHTS.get(provider_name, 0.0)
            total_weight += weight

            # Add to direction score
            direction_scores[analysis.direction] += weight

            # Add to weighted confidence
            weighted_confidence += analysis.confidence * weight

        # Normalize weights to sum to 1.0 (redistribute weight from failed providers)
        if total_weight > 0 and total_weight < 1.0:
            reweight_factor = 1.0 / total_weight
            for direction in direction_scores:
                direction_scores[direction] *= reweight_factor
            weighted_confidence *= reweight_factor

            # Log reweighting
            print(
                f"⚙️  Dynamic reweighting: {total_weight:.0%} → 100% (missing: {', '.join(failed_providers)})"
            )

        # Determine consensus direction (highest score)
        consensus_direction = max(direction_scores, key=direction_scores.get)
        consensus_score = direction_scores[consensus_direction]

        # Combine reasoning from all providers
        combined_reasoning = self._combine_reasoning(analyses)
        risk_summary = self._combine_risk_assessments(analyses)
        technical_summary = self._combine_technical_summaries(analyses)

        return ConsensusSignal(
            direction=consensus_direction,
            confidence=weighted_confidence,
            consensus_score=consensus_score,
            chatgpt_analysis=analyses.get("chatgpt"),
            claude_analysis=analyses.get("claude"),
            gemini_analysis=analyses.get("gemini"),
            combined_reasoning=combined_reasoning,
            risk_summary=risk_summary,
            technical_summary=technical_summary,
            timestamp=datetime.now(),
            pair=pair,
            timeframe=timeframe,
            active_providers=active_providers,
            failed_providers=failed_providers,
            provider_models=provider_models,
        )

    def _combine_reasoning(self, analyses: Dict[str, MarketAnalysis]) -> str:
        """Combine reasoning from all providers"""
        reasoning_parts = []

        for provider_name, analysis in analyses.items():
            # Safely truncate reasoning (handle None or non-string values)
            reasoning_text = (
                str(analysis.reasoning)
                if analysis.reasoning
                else "No reasoning provided"
            )
            truncated = (
                reasoning_text[:200] + "..."
                if len(reasoning_text) > 200
                else reasoning_text
            )

            reasoning_parts.append(
                f"**{provider_name.upper()} ({int(self.WEIGHTS[provider_name] * 100)}%)**: "
                f"{analysis.direction.upper()} @ {analysis.confidence:.2f} - "
                f"{truncated}"
            )

        return "\n\n".join(reasoning_parts)

    def _combine_risk_assessments(self, analyses: Dict[str, MarketAnalysis]) -> str:
        """Combine risk assessments from all providers"""
        risk_parts = []

        for provider_name, analysis in analyses.items():
            if analysis.risk_assessment:
                risk_parts.append(f"• {provider_name}: {analysis.risk_assessment}")

        return "\n".join(risk_parts) if risk_parts else "No specific risks identified"

    def _combine_technical_summaries(self, analyses: Dict[str, MarketAnalysis]) -> str:
        """Combine technical summaries from all providers"""
        tech_parts = []

        for provider_name, analysis in analyses.items():
            if analysis.technical_summary:
                tech_parts.append(f"• {provider_name}: {analysis.technical_summary}")

        return "\n".join(tech_parts) if tech_parts else "No technical summary available"

    def test_providers(self) -> Dict[str, bool]:
        """
        Test connection to all providers.

        Returns:
            Dict of provider name -> connection status
        """
        results = {}

        for name, provider in self.providers.items():
            results[name] = provider.test_connection()

        return results
