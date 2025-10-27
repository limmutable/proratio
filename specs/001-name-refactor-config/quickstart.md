# Quickstart: Using the Dynamic Config Loader

This guide explains how to use the `load_and_hydrate_config` function to get a fully-hydrated, in-memory configuration dictionary for Freqtrade.

## 1. Overview

The dynamic loader solves the problem of duplicated configuration by treating the `config_*.json` files as templates and injecting secrets from the Pydantic `Settings` object at runtime.

**Security Note**: The hydrated configuration dictionary contains secrets. **NEVER** write this dictionary to a file.

## 2. Usage

To load and hydrate a configuration, import and call the `load_and_hydrate_config` function from the `proratio_utilities.config.loader` module.

```python
from proratio_utilities.config.loader import load_and_hydrate_config
from proratio_utilities.config.settings import get_settings

# Ensure settings are loaded (this happens on first call to get_settings)
settings = get_settings()

# Specify the path to your base config template
config_path = "proratio_utilities/config/freqtrade/config_dry.json"

# Get the hydrated, in-memory config
hydrated_config = load_and_hydrate_config(config_path)

# Now you can use this dictionary with Freqtrade
# For example, when starting a Freqtrade instance programmatically.
# freqtrade_bot = FreqtradeBot(hydrated_config)
# ...
```

## 3. Example

### Before Hydration (`config_dry.json` template)

```json
{
  "exchange": {
    "name": "binance",
    "key": "YOUR_API_KEY",
    "secret": "YOUR_SECRET_KEY",
    "pair_whitelist": ["BTC/USDT"]
  },
  "telegram": {
    "enabled": true,
    "token": "YOUR_TELEGRAM_TOKEN",
    "chat_id": "YOUR_TELEGRAM_CHAT_ID"
  },
  "api_server": {
    "enabled": false
  }
}
```

### After Hydration (In-memory `hydrated_config` dict)

Assuming your `.env` file has the necessary values and `TRADING_MODE` is `dry_run`:

```python
# The Python dictionary in memory would look like this:
{
  "exchange": {
    "name": "binance",
    "key": "actual_api_key_from_env",
    "secret": "actual_secret_from_env",
    "pair_whitelist": ["BTC/USDT"]
  },
  "telegram": {
    "enabled": true,
    "token": "actual_telegram_token_from_env",
    "chat_id": "actual_chat_id_from_env"
  },
  "api_server": {
    "enabled": true  // Dynamically set to True
  }
}
```
