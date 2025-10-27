# Data Model: Configuration Hydration

This document outlines the data structures involved in the configuration consolidation feature. The core concept is the hydration of a base `freqtrade` JSON configuration from a Pydantic `Settings` object.

## 1. Entities

### 1.1. `Settings` (Pydantic Model)

- **Source**: `proratio_utilities/config/settings.py`
- **Description**: A Pydantic `BaseSettings` model that loads configuration from environment variables (defined in a `.env` file). It serves as the single source of truth for secrets and environment-specific parameters.

**Key Fields**:
- `binance_api_key: str`
- `binance_api_secret: str`
- `telegram_bot_token: Optional[str]`
- `telegram_chat_id: Optional[str]`
- `trading_mode: str`

### 1.2. `FreqtradeConfig` (JSON Structure)

- **Source**: `proratio_utilities/config/freqtrade/config_*.json`
- **Description**: A JSON file that defines the configuration for the Freqtrade bot. These files act as templates.

**Key Fields to be Hydrated**:
- `exchange.key: str`
- `exchange.secret: str`
- `telegram.token: str`
- `telegram.chat_id: str`
- `api_server.enabled: bool`

## 2. Relationships and Data Flow

The `load_and_hydrate_config` function establishes a one-way data flow from the `Settings` object to the `FreqtradeConfig` structure.

```mermaid
graph TD
    A[.env file] --> B[Settings Pydantic Model];
    C[config_*.json template] --> D{load_and_hydrate_config};
    B --> D;
    D --> E[In-Memory Hydrated Config (dict)];
```

## 3. Field Mapping

The hydration process maps fields from the `Settings` model to the `FreqtradeConfig` dictionary as follows:

| `FreqtradeConfig` Key Path | `Settings` Attribute | Logic |
|----------------------------|------------------------|-------|
| `exchange.key`             | `binance_api_key`      | Direct override |
| `exchange.secret`          | `binance_api_secret`   | Direct override |
| `telegram.token`           | `telegram_bot_token`   | Direct override |
| `telegram.chat_id`         | `telegram_chat_id`     | Direct override |
| `api_server.enabled`       | `trading_mode`         | `True` if mode is not `backtest` |
