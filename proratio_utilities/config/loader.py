import json
import logging
from typing import Dict, Any
from pathlib import Path
from proratio_utilities.config.settings import get_settings

logger = logging.getLogger(__name__)


def validate_required_settings(settings) -> None:
    """
    Validates that required environment variables are set.
    
    Raises:
        ValueError: If required settings are missing.
    """
    required_fields = {
        'binance_api_key': 'BINANCE_API_KEY',
        'binance_api_secret': 'BINANCE_API_SECRET',
    }
    
    missing = []
    for field, env_var in required_fields.items():
        value = getattr(settings, field, None)
        if not value or value == "":
            missing.append(env_var)
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Please set them in your .env file."
        )
    
    logger.info("Configuration validation passed")


def load_and_hydrate_config(config_path: str, validate: bool = True) -> Dict[str, Any]:
    """
    Loads a base JSON configuration file and hydrates it with values from the
    Pydantic Settings object.

    Args:
        config_path: Path to the base JSON configuration file.
        validate: Whether to validate required settings (default: True).

    Returns:
        A dictionary containing the hydrated configuration.
        
    Raises:
        ValueError: If required environment variables are missing (when validate=True).
        FileNotFoundError: If config file doesn't exist.
    """
    logger.info(f"Loading configuration from: {config_path}")
    
    # Load the base JSON configuration
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    base_config = json.loads(config_file.read_text())
    logger.debug(f"Base configuration loaded: {len(base_config)} top-level keys")

    # Get the cached Pydantic Settings instance
    settings = get_settings()
    
    # Validate required settings
    if validate:
        validate_required_settings(settings)

    # Hydrate the configuration
    logger.debug("Hydrating configuration with environment variables")
    
    # Exchange settings
    if 'exchange' in base_config:
        base_config['exchange']['key'] = settings.binance_api_key
        base_config['exchange']['secret'] = settings.binance_api_secret
        logger.info("Injected exchange API credentials")

    # Telegram settings
    if 'telegram' in base_config:
        base_config['telegram']['token'] = settings.telegram_bot_token or ""
        base_config['telegram']['chat_id'] = settings.telegram_chat_id or ""
        if settings.telegram_bot_token:
            logger.info("Injected Telegram credentials")

    # API server settings (FreqUI)
    if 'api_server' in base_config:
        base_config['api_server']['enabled'] = settings.trading_mode != 'backtest'
        
        # Inject API server secrets if provided
        if settings.api_server_jwt_secret:
            base_config['api_server']['jwt_secret_key'] = settings.api_server_jwt_secret
        if settings.api_server_ws_token:
            base_config['api_server']['ws_token'] = settings.api_server_ws_token
        if settings.api_server_username:
            base_config['api_server']['username'] = settings.api_server_username
        if settings.api_server_password:
            base_config['api_server']['password'] = settings.api_server_password
            
        logger.info(f"Configured API server (enabled: {base_config['api_server']['enabled']})")

    logger.info("Configuration hydration complete")
    return base_config

