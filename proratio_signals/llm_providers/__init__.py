"""
LLM Provider Interfaces

Provides consistent interface to multiple LLM services:
- ChatGPT (OpenAI)
- Claude (Anthropic)
- Gemini (Google)
"""

from .base import BaseLLMProvider, MarketAnalysis, OHLCVData
from .exceptions import (
    ProviderError,
    APIKeyError,
    QuotaError,
    RateLimitError,
    TimeoutError,
    ModelNotFoundError,
    InvalidResponseError,
    InvalidPromptError,
)

__all__ = [
    # Base classes and data models
    "BaseLLMProvider",
    "MarketAnalysis",
    "OHLCVData",
    # Exceptions
    "ProviderError",
    "APIKeyError",
    "QuotaError",
    "RateLimitError",
    "TimeoutError",
    "ModelNotFoundError",
    "InvalidResponseError",
    "InvalidPromptError",
]
