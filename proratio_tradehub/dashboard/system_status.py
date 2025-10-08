"""
System Status Checker

Checks status of all critical system components:
- Freqtrade API
- Database connections
- AI providers (OpenAI, Claude, Gemini)
- Trading configuration
"""

import os
import sqlite3
import requests
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env in project root
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # dotenv not installed, will use system environment variables only
    pass


@dataclass
class ServiceStatus:
    """Status of a system service"""
    name: str
    is_available: bool
    message: str
    icon: str = "✅"

    def __post_init__(self):
        """Set icon based on availability"""
        if not self.is_available:
            self.icon = "❌"
        elif "warning" in self.message.lower():
            self.icon = "⚠️"


class SystemStatusChecker:
    """Checks status of all system components"""

    def __init__(
        self,
        freqtrade_url: str = "http://127.0.0.1:8080",
        db_path: str = "user_data/db/tradesv3.dryrun.sqlite",
        config_path: str = "proratio_utilities/config/trading_config.json"
    ):
        self.freqtrade_url = freqtrade_url
        self.db_path = Path(db_path)
        self.config_path = Path(config_path)

    def check_freqtrade(self) -> ServiceStatus:
        """Check if Freqtrade API is responding"""
        try:
            response = requests.get(
                f"{self.freqtrade_url}/api/v1/ping",
                timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                return ServiceStatus(
                    name="Freqtrade API",
                    is_available=True,
                    message=f"Connected ({status})"
                )
            else:
                return ServiceStatus(
                    name="Freqtrade API",
                    is_available=False,
                    message=f"HTTP {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            return ServiceStatus(
                name="Freqtrade API",
                is_available=False,
                message="Not responding"
            )

    def check_database(self) -> ServiceStatus:
        """Check if SQLite database is accessible"""
        try:
            if not self.db_path.exists():
                return ServiceStatus(
                    name="Trade Database",
                    is_available=False,
                    message="Database file not found"
                )

            # Try to connect and query
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades")
            trade_count = cursor.fetchone()[0]
            conn.close()

            return ServiceStatus(
                name="Trade Database",
                is_available=True,
                message=f"Online ({trade_count} trades)"
            )
        except Exception as e:
            return ServiceStatus(
                name="Trade Database",
                is_available=False,
                message=f"Error: {str(e)[:30]}"
            )

    def check_openai(self) -> ServiceStatus:
        """Check if OpenAI API key is configured"""
        api_key = os.getenv("OPENAI_API_KEY", "")

        if not api_key:
            return ServiceStatus(
                name="OpenAI (ChatGPT)",
                is_available=False,
                message="API key not configured"
            )

        # Quick validation - just check if key format looks valid
        if api_key.startswith("sk-") and len(api_key) > 20:
            return ServiceStatus(
                name="OpenAI (ChatGPT)",
                is_available=True,
                message="API key configured"
            )
        else:
            return ServiceStatus(
                name="OpenAI (ChatGPT)",
                is_available=False,
                message="Invalid API key format"
            )

    def check_anthropic(self) -> ServiceStatus:
        """Check if Anthropic (Claude) API key is configured"""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")

        if not api_key:
            return ServiceStatus(
                name="Anthropic (Claude)",
                is_available=False,
                message="API key not configured"
            )

        # Quick validation - check if key format looks valid
        if api_key.startswith("sk-ant-") and len(api_key) > 20:
            return ServiceStatus(
                name="Anthropic (Claude)",
                is_available=True,
                message="API key configured"
            )
        else:
            return ServiceStatus(
                name="Anthropic (Claude)",
                is_available=False,
                message="Invalid API key format"
            )

    def check_gemini(self) -> ServiceStatus:
        """Check if Google Gemini API key is configured"""
        api_key = os.getenv("GEMINI_API_KEY", "")

        if not api_key:
            return ServiceStatus(
                name="Google Gemini",
                is_available=False,
                message="API key not configured"
            )

        # Gemini keys are typically 39 characters
        if len(api_key) > 20:
            return ServiceStatus(
                name="Google Gemini",
                is_available=True,
                message="API key configured"
            )
        else:
            return ServiceStatus(
                name="Google Gemini",
                is_available=False,
                message="Invalid API key format"
            )

    def check_trading_config(self) -> ServiceStatus:
        """Check if trading configuration is valid"""
        try:
            if not self.config_path.exists():
                return ServiceStatus(
                    name="Trading Config",
                    is_available=False,
                    message="Config file not found"
                )

            # Try to load and validate
            from proratio_utilities.config.trading_config import TradingConfig
            config = TradingConfig.load_from_file(str(self.config_path))
            errors = config.validate()

            if errors:
                return ServiceStatus(
                    name="Trading Config",
                    is_available=True,
                    message=f"Warning: {len(errors)} validation issues",
                    icon="⚠️"
                )
            else:
                return ServiceStatus(
                    name="Trading Config",
                    is_available=True,
                    message="Valid configuration"
                )
        except Exception as e:
            return ServiceStatus(
                name="Trading Config",
                is_available=False,
                message=f"Error: {str(e)[:30]}"
            )

    def check_binance_keys(self) -> ServiceStatus:
        """Check if Binance API keys are configured"""
        api_key = os.getenv("BINANCE_API_KEY", "")
        api_secret = os.getenv("BINANCE_API_SECRET", "")

        if not api_key or not api_secret:
            return ServiceStatus(
                name="Binance API",
                is_available=False,
                message="API keys not configured"
            )

        if len(api_key) > 20 and len(api_secret) > 20:
            testnet = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
            mode = "Testnet" if testnet else "Mainnet"
            return ServiceStatus(
                name="Binance API",
                is_available=True,
                message=f"Configured ({mode})"
            )
        else:
            return ServiceStatus(
                name="Binance API",
                is_available=False,
                message="Invalid API key format"
            )

    def get_all_status(self) -> Dict[str, ServiceStatus]:
        """Get status of all system components"""
        return {
            "freqtrade": self.check_freqtrade(),
            "database": self.check_database(),
            "openai": self.check_openai(),
            "anthropic": self.check_anthropic(),
            "gemini": self.check_gemini(),
            "config": self.check_trading_config(),
            "binance": self.check_binance_keys(),
        }

    def get_summary(self) -> Dict[str, int]:
        """Get summary of system health"""
        all_status = self.get_all_status()

        available = sum(1 for s in all_status.values() if s.is_available)
        warnings = sum(1 for s in all_status.values() if "⚠️" in s.icon)
        unavailable = sum(1 for s in all_status.values() if not s.is_available)

        return {
            "total": len(all_status),
            "available": available,
            "warnings": warnings,
            "unavailable": unavailable,
            "health_pct": (available / len(all_status)) * 100 if all_status else 0
        }
