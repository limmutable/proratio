# Action 4: Configuration Unification Implementation Guide

**Priority**: HIGH
**Estimated Time**: 1-2 days
**Status**: Pending (Phase 3.5 - Technical Debt Resolution)
**Based on**: [technical_debt_gemini_review.md](technical_debt_gemini_review.md) Section 3.1

---

## Problem Statement

Currently, Proratio has **two separate configuration systems**:

1. **`proratio_utilities/config/settings.py`** (Pydantic BaseSettings)
   - Loads from `.env` environment variables
   - Used for: API keys, database URLs, basic trading settings

2. **`proratio_utilities/config/trading_config.py`** (Dataclass-based)
   - Loads from JSON files
   - Used for: Risk management, position sizing, strategy parameters, AI settings

### Issues:
- **Confusion**: Developers don't know which file to check for a setting
- **Duplication**: Some settings exist in both places (e.g., `trading_mode`, `stake_amount`)
- **Inconsistency**: Different loading mechanisms (.env vs JSON)
- **Maintenance burden**: Two systems to update and document

---

## Solution: Unified Pydantic Settings

Merge everything into `proratio_utilities/config/settings.py` as a single source of truth.

### Benefits:
- ✅ Single configuration file
- ✅ Type-safe with Pydantic validation
- ✅ Can still load from both .env AND JSON
- ✅ Easier to maintain and document
- ✅ Consistent API across codebase

---

## Implementation Plan

### Step 1: Create Nested Pydantic Models (4 hours)

**File**: `proratio_utilities/config/settings.py`

Add nested configuration models:

```python
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional
from pathlib import Path
import json

# =============================================================================
# NESTED CONFIGURATION MODELS
# =============================================================================

class RiskSettings(BaseModel):
    """Risk management configuration"""
    max_loss_per_trade_pct: float = Field(default=2.0, ge=0, le=10)
    max_position_size_pct: float = Field(default=10.0, ge=0, le=100)
    min_position_size_pct: float = Field(default=1.0, ge=0, le=100)
    max_total_drawdown_pct: float = Field(default=10.0, ge=0, le=50)
    warning_drawdown_pct: float = Field(default=7.0, ge=0, le=50)
    max_concurrent_positions: int = Field(default=3, ge=1, le=10)
    max_positions_per_pair: int = Field(default=1, ge=1, le=5)
    max_leverage: float = Field(default=1.0, ge=1.0, le=10.0)

class PositionSizingSettings(BaseModel):
    """Position sizing configuration"""
    method: str = Field(default='ai_weighted')
    base_risk_pct: float = Field(default=2.0, ge=0.1, le=10)
    ai_confidence_min: float = Field(default=0.60, ge=0, le=1)
    ai_confidence_multiplier_min: float = Field(default=0.8, ge=0.1, le=2)
    ai_confidence_multiplier_max: float = Field(default=1.2, ge=0.1, le=2)
    atr_period: int = Field(default=14, ge=1, le=100)
    atr_multiplier: float = Field(default=2.0, ge=0.5, le=5)
    kelly_fraction: float = Field(default=0.5, ge=0.1, le=1)

class StrategySettings(BaseModel):
    """Strategy-specific configuration"""
    strategy_name: str = Field(default='AIEnhancedStrategy')
    timeframe: str = Field(default='1h')
    pairs: List[str] = Field(default_factory=lambda: ['BTC/USDT', 'ETH/USDT'])

    # Technical indicators
    ema_fast_period: int = Field(default=20, ge=1, le=200)
    ema_slow_period: int = Field(default=50, ge=1, le=200)
    rsi_period: int = Field(default=14, ge=1, le=100)
    rsi_buy_threshold: int = Field(default=30, ge=0, le=100)
    rsi_sell_threshold: int = Field(default=70, ge=0, le=100)
    atr_period: int = Field(default=14, ge=1, le=100)
    adx_period: int = Field(default=14, ge=1, le=100)
    adx_trend_threshold: float = Field(default=20.0, ge=0, le=100)

    # ROI and stops
    roi_levels: Dict[str, float] = Field(default_factory=lambda: {
        "0": 0.15, "60": 0.08, "120": 0.04
    })
    stoploss_pct: float = Field(default=-0.04, le=0)
    trailing_stop_enabled: bool = Field(default=True)
    trailing_stop_positive: float = Field(default=0.015, ge=0, le=1)
    trailing_stop_positive_offset: float = Field(default=0.025, ge=0, le=1)
    volume_min_multiplier: float = Field(default=1.0, ge=0.1, le=10)

class AISettings(BaseModel):
    """AI signal generation configuration"""
    chatgpt_weight: float = Field(default=0.40, ge=0, le=1)
    claude_weight: float = Field(default=0.35, ge=0, le=1)
    gemini_weight: float = Field(default=0.25, ge=0, le=1)
    min_consensus_score: float = Field(default=0.60, ge=0, le=1)
    min_confidence: float = Field(default=0.60, ge=0, le=1)
    require_all_providers: bool = Field(default=False)
    signal_cache_minutes: int = Field(default=60, ge=1, le=1440)
    lookback_candles: int = Field(default=50, ge=10, le=500)
    chatgpt_model: Optional[str] = None
    claude_model: Optional[str] = None
    gemini_model: Optional[str] = None

    @field_validator('chatgpt_weight', 'claude_weight', 'gemini_weight')
    @classmethod
    def validate_weights_sum(cls, v, info):
        # Note: Full validation done in model_validator
        return v

class ExecutionSettings(BaseModel):
    """Order execution configuration"""
    trading_mode: str = Field(default='dry_run')
    exchange: str = Field(default='binance')
    entry_order_type: str = Field(default='limit')
    exit_order_type: str = Field(default='limit')
    stoploss_order_type: str = Field(default='market')
    stoploss_on_exchange: bool = Field(default=False)
    order_time_in_force: str = Field(default='GTC')
    starting_balance: float = Field(default=10000.0, ge=100)
    stake_currency: str = Field(default='USDT')
    stake_amount: float = Field(default=100.0, ge=1)

# =============================================================================
# MAIN SETTINGS CLASS (UPDATED)
# =============================================================================

class Settings(BaseSettings):
    """
    Unified application settings.

    Single source of truth for all configuration.
    Loads from:
    1. Environment variables (.env file)
    2. Optional JSON config file (for complex nested settings)
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
        env="DATABASE_URL"
    )
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Telegram
    telegram_bot_token: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(default=None, env="TELEGRAM_CHAT_ID")

    # Development
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    data_refresh_interval: int = Field(default=300, env="DATA_REFRESH_INTERVAL")

    # =========================================================================
    # TRADING CONFIGURATION (NESTED)
    # =========================================================================
    risk: RiskSettings = Field(default_factory=RiskSettings)
    position_sizing: PositionSizingSettings = Field(default_factory=PositionSizingSettings)
    strategy: StrategySettings = Field(default_factory=StrategySettings)
    ai: AISettings = Field(default_factory=AISettings)
    execution: ExecutionSettings = Field(default_factory=ExecutionSettings)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @classmethod
    def load_with_json(cls, json_path: Optional[Path] = None) -> 'Settings':
        """
        Load settings from .env PLUS optional JSON config file.

        Args:
            json_path: Optional path to JSON config file

        Returns:
            Settings instance with merged configuration
        """
        # Load base settings from .env
        settings = cls()

        # Overlay JSON config if provided
        if json_path and json_path.exists():
            with open(json_path, 'r') as f:
                json_data = json.load(f)

            # Update nested settings
            if 'risk' in json_data:
                settings.risk = RiskSettings(**json_data['risk'])
            if 'position_sizing' in json_data:
                settings.position_sizing = PositionSizingSettings(**json_data['position_sizing'])
            if 'strategy' in json_data:
                settings.strategy = StrategySettings(**json_data['strategy'])
            if 'ai' in json_data:
                settings.ai = AISettings(**json_data['ai'])
            if 'execution' in json_data:
                settings.execution = ExecutionSettings(**json_data['execution'])

        return settings

    def validate_config(self) -> List[str]:
        """
        Validate configuration for common errors.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # AI weights validation
        total_weight = self.ai.chatgpt_weight + self.ai.claude_weight + self.ai.gemini_weight
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"AI provider weights must sum to 1.0 (current: {total_weight:.2f})")

        return errors


@lru_cache()
def get_settings(json_path: Optional[Path] = None) -> Settings:
    """
    Get cached settings instance.

    Args:
        json_path: Optional path to JSON config file for trading params

    Returns:
        Settings instance
    """
    if json_path:
        return Settings.load_with_json(json_path)
    return Settings()
```

---

### Step 2: Update All Imports (2 hours)

**Files to update** (12 total):

1. `proratio_tradehub/dashboard/app.py`
2. `proratio_tradehub/dashboard/system_status.py`
3. `proratio_tradehub/dashboard/data_fetcher.py`
4. `tests/test_dashboard/test_data_fetcher.py`
5. `scripts/show_trading_config.py`

**Before**:
```python
from proratio_utilities.config.trading_config import TradingConfig, get_trading_config

config = get_trading_config()
max_loss = config.risk.max_loss_per_trade_pct
```

**After**:
```python
from proratio_utilities.config.settings import get_settings

settings = get_settings()
max_loss = settings.risk.max_loss_per_trade_pct
```

---

### Step 3: Create Migration Guide (1 hour)

Document the changes in `docs/guides/config_migration_guide.md`:

```markdown
# Configuration Migration Guide

## What Changed

Proratio now uses a **single unified configuration system** instead of two separate systems.

### Before (Old System)
- `settings.py` for env vars (API keys, DB URLs)
- `trading_config.py` for trading params (risk, strategy)

### After (New System)
- `settings.py` for EVERYTHING (single source of truth)

## Migration Steps

### For Developers

1. **Update imports**:
   ```python
   # OLD
   from proratio_utilities.config.trading_config import TradingConfig
   config = TradingConfig.load_from_file('config.json')

   # NEW
   from proratio_utilities.config.settings import get_settings
   settings = get_settings(json_path=Path('config.json'))
   ```

2. **Update attribute access**:
   ```python
   # OLD
   config = get_trading_config()
   max_loss = config.risk.max_loss_per_trade_pct

   # NEW
   settings = get_settings()
   max_loss = settings.risk.max_loss_per_trade_pct
   ```

### For JSON Config Files

No changes needed! JSON structure remains identical.

```json
{
  "risk": {
    "max_loss_per_trade_pct": 2.0,
    ...
  },
  "ai": {
    "chatgpt_weight": 0.40,
    ...
  }
}
```

## Checklist

- [ ] Update imports in all Python files
- [ ] Update tests
- [ ] Update documentation
- [ ] Delete `proratio_utilities/config/trading_config.py`
- [ ] Run full test suite
```

---

### Step 4: Update Tests (2 hours)

Update test files to use new import:

```python
# tests/test_dashboard/test_data_fetcher.py

from proratio_utilities.config.settings import get_settings

def test_data_fetcher():
    settings = get_settings()
    assert settings.risk.max_loss_per_trade_pct > 0
```

---

### Step 5: Delete Old File (5 minutes)

After all migrations complete and tests pass:

```bash
# Backup first
cp proratio_utilities/config/trading_config.py /tmp/trading_config.py.backup

# Delete old file
rm proratio_utilities/config/trading_config.py

# Run tests
pytest

# If all pass, commit
git add -A
git commit -m "Refactor: Unify configuration into single Pydantic Settings model"
```

---

## Testing Checklist

- [ ] All imports updated
- [ ] All tests passing (186+ tests)
- [ ] Dashboard loads correctly
- [ ] CLI `/config` command works
- [ ] JSON config files still load
- [ ] Environment variables still load
- [ ] No references to `trading_config.py` remain

---

## Validation

Run these commands to verify:

```bash
# Check for old imports
grep -r "trading_config import" proratio_*/
grep -r "TradingConfig" proratio_*/

# Should return no results

# Run tests
pytest -v

# All should pass
```

---

## Rollback Plan

If issues arise:

```bash
# Restore backup
cp /tmp/trading_config.py.backup proratio_utilities/config/trading_config.py

# Revert changes
git revert HEAD
```

---

## Completion Criteria

- ✅ Single `Settings` class in `settings.py`
- ✅ All nested models added (Risk, AI, Strategy, etc.)
- ✅ All 12 files updated with new imports
- ✅ All tests passing
- ✅ Old `trading_config.py` deleted
- ✅ Migration guide created
- ✅ No breaking changes for users

---

**Estimated Total Time**: 1-2 days
**Priority**: HIGH (prerequisite for Phase 4-10)
**Status**: Ready to implement
