# Feature Spec: Strategy Architecture Refactoring

## 1. Overview

**Goal:** Refactor all trading strategies to follow a consistent "Adapter" architectural pattern, separating the core, framework-agnostic trading logic from the `freqtrade`-specific implementation.

**Current Problem:** The project contains a mix of architectural patterns. `MeanReversionAdapter` follows the desired pattern, with its core logic in `proratio_tradehub.strategies`. However, `GridTradingStrategy` is a monolithic implementation where the core logic is tightly coupled with the `freqtrade.strategy.IStrategy` interface. This inconsistency makes the core logic harder to test in isolation, reuse in other contexts (e.g., backtesting engines, simulators), and maintain.

**Proposed Solution:** Refactor `GridTradingStrategy` to align with the adapter pattern. This involves creating a new, pure Python class for the core grid logic and transforming the existing `IStrategy` implementation into a thin adapter that delegates calls to the core logic class.

## 2. Functional Requirements

### 2.1. Create Core `GridTradingStrategy` Class

- A new class, `GridTradingStrategy`, will be created in `proratio_tradehub/strategies/grid_trading.py`.
- This class will be framework-agnostic and will not import anything from `freqtrade`.
- It will contain the essential logic for grid trading:
    - `__init__(self, grid_spacing: float, num_grids_above: int, ...)`: To hold grid parameters.
    - `calculate_grid_levels(self, current_price: float) -> tuple`: To compute buy and sell grid levels.
    - `should_enter(self, dataframe: pd.DataFrame) -> Signal`: To determine entry conditions based on volatility and trend indicators.
    - `should_exit(self, dataframe: pd.DataFrame, position) -> Signal`: To determine exit conditions.
    - It will return a simple `Signal` object (e.g., a dataclass) indicating direction, confidence, and reasoning, rather than manipulating the dataframe directly.

### 2.2. Refactor `GridTradingStrategy` into `GridTradingAdapter`

- The existing file `strategies/active/f662_grid-trading/strategy.py` will be renamed to `adapter.py` (or similar) and the class within it will be renamed to `GridTradingAdapter`.
- This class will continue to inherit from `freqtrade.strategy.IStrategy`.
- In its `__init__` method, it will instantiate the new core `proratio_tradehub.strategies.GridTradingStrategy`.
- The `populate_entry_trend` and `populate_exit_trend` methods will be modified to:
    1. Call the appropriate methods on the core strategy instance (e.g., `self.core_strategy.should_enter(dataframe)`).
    2. Translate the returned `Signal` object into the dataframe modifications that `freqtrade` expects (e.g., setting `dataframe['enter_long'] = 1`).

### 2.3. Unit Testing for Core Logic

- A new test file, `tests/test_tradehub/test_grid_trading_strategy.py`, will be created.
- These tests will target the new core `GridTradingStrategy` class directly, allowing for fast, isolated testing of the trading logic without needing the `freqtrade` framework.

## 3. Non-Functional Requirements

- **Behavioral Equivalence:** The refactored `GridTradingAdapter` must produce the exact same trading signals as the original monolithic `GridTradingStrategy` given the same market data and configuration.
- **Maintainability:** The separation of concerns should make the code easier to read, understand, and modify in the future.
- **Testability:** The core logic must be fully testable with standard Python unit testing tools, independent of the `freqtrade` backtesting environment.

## 4. Out of Scope

- This refactoring will **not** alter the underlying trading logic or parameters of the grid trading strategy.
- This work will **not** involve creating a new backtesting engine; it only decouples the strategy logic from the existing one.
