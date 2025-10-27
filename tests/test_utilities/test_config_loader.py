import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import json
import pytest
from unittest.mock import patch, MagicMock
from proratio_utilities.config.loader import load_and_hydrate_config

@pytest.fixture
def mock_settings():
    """Fixture for mocking the Pydantic Settings object."""
    mock = MagicMock()
    mock.binance_api_key = "test_api_key"
    mock.binance_api_secret = "test_api_secret"
    mock.telegram_bot_token = "test_telegram_token"
    mock.telegram_chat_id = "test_telegram_chat_id"
    mock.trading_mode = "dry_run"
    return mock

@pytest.fixture
def base_config_file(tmp_path):
    """Fixture for creating a temporary base config file."""
    config = {
        "exchange": {
            "key": "YOUR_API_KEY",
            "secret": "YOUR_SECRET_KEY",
            "other_exchange_setting": "value"
        },
        "telegram": {
            "token": "YOUR_TELEGRAM_TOKEN",
            "chat_id": "YOUR_TELEGRAM_CHAT_ID"
        },
        "api_server": {
            "enabled": False
        },
        "other_setting": "should_remain"
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    return str(config_file)

@patch('proratio_utilities.config.loader.get_settings')
def test_hydration_api_keys(mock_get_settings, mock_settings, base_config_file):
    """T009: Test that API keys are correctly injected."""
    mock_get_settings.return_value = mock_settings
    hydrated_config = load_and_hydrate_config(base_config_file)
    assert hydrated_config['exchange']['key'] == "test_api_key"
    assert hydrated_config['exchange']['secret'] == "test_api_secret"

@patch('proratio_utilities.config.loader.get_settings')
def test_hydration_telegram_settings(mock_get_settings, mock_settings, base_config_file):
    """T010: Test that Telegram settings are correctly injected."""
    mock_get_settings.return_value = mock_settings
    hydrated_config = load_and_hydrate_config(base_config_file)
    assert hydrated_config['telegram']['token'] == "test_telegram_token"
    assert hydrated_config['telegram']['chat_id'] == "test_telegram_chat_id"

@patch('proratio_utilities.config.loader.get_settings')
def test_hydration_api_server_enabled(mock_get_settings, mock_settings, base_config_file):
    """T011: Test that api_server.enabled is correctly set for different trading modes."""
    # Test with dry_run
    mock_settings.trading_mode = "dry_run"
    mock_get_settings.return_value = mock_settings
    hydrated_config = load_and_hydrate_config(base_config_file)
    assert hydrated_config['api_server']['enabled'] is True

    # Test with backtest
    mock_settings.trading_mode = "backtest"
    mock_get_settings.return_value = mock_settings
    hydrated_config = load_and_hydrate_config(base_config_file)
    assert hydrated_config['api_server']['enabled'] is False

@patch('proratio_utilities.config.loader.get_settings')
def test_hydration_preserves_other_values(mock_get_settings, mock_settings, base_config_file):
    """T012: Test that other configuration values are not modified."""
    mock_get_settings.return_value = mock_settings
    hydrated_config = load_and_hydrate_config(base_config_file)
    assert hydrated_config['exchange']['other_exchange_setting'] == "value"
    assert hydrated_config['other_setting'] == "should_remain"

