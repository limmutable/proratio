# Feature Spec: Configuration Consolidation

## 1. Overview

**Goal:** Refactor the configuration management system to establish a single source of truth, eliminating duplication and potential inconsistencies between the Pydantic `Settings` and the `freqtrade` JSON configuration files.

**Current Problem:** Secrets and environment-specific settings (like API keys, Telegram tokens, and database URLs) are defined in both `.env` (read by Pydantic) and duplicated in various `config_*.json` files. This makes configuration changes error-prone and difficult to manage across different environments (dry-run, live, test).

**Proposed Solution:** Treat the `freqtrade` JSON files as templates. At runtime, a loading mechanism will read a base JSON configuration and dynamically inject the up-to-date values from the Pydantic `Settings` object. This ensures that secrets and environment settings are managed in one place (`.env` file) and the application always uses a consistent, correctly hydrated configuration.

## 2. Functional Requirements

### 2.1. Dynamic Config Loader

- A new function, `load_and_hydrate_config(config_path: str) -> dict`, will be created in `proratio_utilities.config`.
- This function will:
    1. Load the base JSON configuration file specified by `config_path`.
    2. Get the cached Pydantic `Settings` instance.
    3. Recursively traverse the JSON dictionary and override specific keys with values from the `Settings` object.
        - `exchange.key` -> `settings.binance_api_key`
        - `exchange.secret` -> `settings.binance_api_secret`
        - `telegram.token` -> `settings.telegram_bot_token`
        - `telegram.chat_id` -> `settings.telegram_chat_id`
        - `api_server.enabled` -> `True` if `settings.trading_mode` is not `backtest`.
- The function will return the hydrated configuration as a Python dictionary.

### 2.2. Integration with Application Startup

- The main application entry points (e.g., `proratio_cli`, `scripts/run_paper_trading.sh`) will be modified to use this new loading mechanism.
- Instead of passing a path to a static JSON file to `freqtrade`, the application will pass the in-memory, hydrated configuration dictionary.

## 3. Non-Functional Requirements

- **Security:** The hydrated configuration containing secrets must **never** be written to a file on disk. It should only be held in memory.
- **Performance:** The configuration hydration process should be lightweight and not introduce any noticeable delay to the application's startup time.
- **Clarity:** The mapping between Pydantic settings and JSON keys should be clearly defined and easy to maintain within the `load_and_hydrate_config` function.

## 4. Out of Scope

- This refactoring will **not** change the fundamental structure or schema of the `freqtrade` JSON configuration files.
- This work will **not** introduce new configuration variables, only consolidate the management of existing ones.
