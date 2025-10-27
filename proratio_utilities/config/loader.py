import json
from typing import Dict, Any
from pathlib import Path
from proratio_utilities.config.settings import get_settings

def load_and_hydrate_config(config_path: str) -> Dict[str, Any]:
    """
    Loads a base JSON configuration file and hydrates it with values from the
    Pydantic Settings object.

    Args:
        config_path: Path to the base JSON configuration file.

    Returns:
        A dictionary containing the hydrated configuration.
    """
    # Load the base JSON configuration
    base_config = json.loads(Path(config_path).read_text())

    # Get the cached Pydantic Settings instance
    settings = get_settings()

    # Hydrate the configuration
    # Exchange settings
    if 'exchange' in base_config:
        base_config['exchange']['key'] = settings.binance_api_key
        base_config['exchange']['secret'] = settings.binance_api_secret

    # Telegram settings
    if 'telegram' in base_config:
        base_config['telegram']['token'] = settings.telegram_bot_token
        base_config['telegram']['chat_id'] = settings.telegram_chat_id

    # API server settings
    if 'api_server' in base_config:
        base_config['api_server']['enabled'] = settings.trading_mode != 'backtest'

    return base_config

