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
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")

    # Database
    database_url: str = Field(
        default="postgresql://proratio:proratio_password@localhost:5432/proratio",
        env="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Telegram
    telegram_bot_token: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(default=None, env="TELEGRAM_CHAT_ID")

    # API Server (FreqUI)
    api_server_jwt_secret: str = Field(default="", env="API_SERVER_JWT_SECRET")
    api_server_ws_token: str = Field(default="", env="API_SERVER_WS_TOKEN")
    api_server_username: str = Field(default="freqtrader", env="API_SERVER_USERNAME")
    api_server_password: str = Field(default="", env="API_SERVER_PASSWORD")

    # Environment Settings
    trading_mode: str = Field(default="dry_run", env="TRADING_MODE")  # dry_run or live
    data_refresh_interval: int = Field(
        default=300, env="DATA_REFRESH_INTERVAL"
    )  # seconds

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
