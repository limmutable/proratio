"""
Centralized configuration management using Pydantic settings.
Loads configuration from environment variables (.env file).
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # Exchange API Keys
    binance_api_key: str = Field(default="", env="BINANCE_API_KEY")
    binance_api_secret: str = Field(default="", env="BINANCE_API_SECRET")
    binance_testnet: bool = Field(default=True, env="BINANCE_TESTNET")

    # AI/LLM API Keys
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")

    # Database
    database_url: str = Field(
        default="postgresql://proratio:proratio_password@localhost:5432/proratio",
        env="DATABASE_URL"
    )
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Telegram
    telegram_bot_token: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(default=None, env="TELEGRAM_CHAT_ID")

    # Trading Configuration
    trading_mode: str = Field(default="dry_run", env="TRADING_MODE")  # dry_run or live
    max_open_trades: int = Field(default=2, env="MAX_OPEN_TRADES")
    stake_amount: float = Field(default=100.0, env="STAKE_AMOUNT")  # USDT
    max_drawdown_percent: float = Field(default=10.0, env="MAX_DRAWDOWN_PERCENT")

    # Proratio Core
    data_refresh_interval: int = Field(default=300, env="DATA_REFRESH_INTERVAL")  # seconds

    # Proratio Signals
    ai_consensus_threshold: float = Field(default=0.6, env="AI_CONSENSUS_THRESHOLD")
    enable_chatgpt: bool = Field(default=True, env="ENABLE_CHATGPT")
    enable_claude: bool = Field(default=True, env="ENABLE_CLAUDE")
    enable_gemini: bool = Field(default=True, env="ENABLE_GEMINI")

    # Proratio TradeHub
    strategy_mode: str = Field(default="trend_following", env="STRATEGY_MODE")
    enable_manual_override: bool = Field(default=True, env="ENABLE_MANUAL_OVERRIDE")

    # Development
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Settings are loaded from .env file and environment variables.
    """
    return Settings()
