"""
Proratio Core - Execution & Data Engine

This module handles exchange connectivity, market data collection,
and trade execution via Freqtrade integration.
"""

__version__ = "0.1.0"

from . import data, execution, utils

__all__ = ["data", "execution", "utils"]
