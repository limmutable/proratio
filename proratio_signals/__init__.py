"""
Proratio Signals - AI Alpha Signal Generation

This module provides multi-LLM analysis and consensus-based
signal generation for trading strategies.
"""

from .orchestrator import SignalOrchestrator, ConsensusSignal
from .llm_providers.base import MarketAnalysis, OHLCVData

__version__ = "0.1.0"

__all__ = [
    "SignalOrchestrator",
    "ConsensusSignal",
    "MarketAnalysis",
    "OHLCVData",
]
