"""
LLM Provider Interfaces

Provides consistent interface to multiple LLM services:
- ChatGPT (OpenAI)
- Claude (Anthropic)
- Gemini (Google)
"""

from .base import BaseLLMProvider, MarketAnalysis, OHLCVData

__all__ = [
    'BaseLLMProvider',
    'MarketAnalysis',
    'OHLCVData',
]
