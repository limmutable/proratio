# Task Plan: Configuration Consolidation

This document outlines the tasks required to implement the configuration consolidation feature.

## Phase 1: Setup

- [X] T001 Create new file `proratio_utilities/config/loader.py` for the configuration hydration logic.
- [X] T002 Create new test file `tests/test_utilities/test_config_loader.py` for the new functionality.

## Phase 2: User Story 1 - Dynamic Config Loader

**Goal**: Implement the `load_and_hydrate_config` function that dynamically injects secrets from Pydantic settings into a Freqtrade config template.

**Independent Test Criteria**: The function should correctly load a JSON file, override the specified keys with values from the settings object, and return a complete, accurate dictionary.

### Implementation Tasks

- [X] T003 [US1] Implement the `load_and_hydrate_config` function in `proratio_utilities/config/loader.py`.
- [X] T004 [US1] Add logic to load the base JSON configuration file in `proratio_utilities/config/loader.py`.
- [X] T005 [US1] Add logic to fetch the Pydantic `Settings` instance in `proratio_utilities/config/loader.py`.
- [X] T006 [US1] Implement recursive traversal to override `exchange.key` and `exchange.secret` in `proratio_utilities/config/loader.py`.
- [X] T007 [US1] Implement logic to override `telegram.token` and `telegram.chat_id` in `proratio_utilities/config/loader.py`.
- [X] T008 [US1] Implement logic to set `api_server.enabled` based on `settings.trading_mode` in `proratio_utilities/config/loader.py`.

### Test Tasks

- [X] T009 [P] [US1] Write a unit test in `tests/test_utilities/test_config_loader.py` to verify that API keys are correctly injected. ✅ **PASSING**
- [X] T010 [P] [US1] Write a unit test in `tests/test_utilities/test_config_loader.py` to verify that Telegram settings are correctly injected. ✅ **PASSING**
- [X] T011 [P] [US1] Write a unit test in `tests/test_utilities/test_config_loader.py` to verify `api_server.enabled` is correctly set for different trading modes. ✅ **PASSING**
- [X] T012 [P] [US1] Write a unit test in `tests/test_utilities/test_config_loader.py` to ensure other configuration values are not modified. ✅ **PASSING**

## Phase 3: User Story 2 - Integration with Application

**Goal**: Modify application entry points to use the new dynamic configuration loader instead of static JSON files.

**Independent Test Criteria**: The application (CLI, trading scripts) should start and run correctly using the in-memory, hydrated configuration.

### Implementation Tasks

- [X] T013 [US2] Modify `proratio_cli/commands/trade.py` to use `load_and_hydrate_config` when launching Freqtrade processes. ✅ **COMPLETE**
- [X] T014 [US2] Modify any relevant scripts in the `scripts/` directory (e.g., `run_paper_trading.sh`, `run_ml_backtest.sh`) to use the new loader. ✅ **COMPLETE**

## Phase 4: Polish & Finalization

- [X] T015 Review all changes to ensure the hydrated config is never written to disk.
- [X] T016 Update `quickstart.md` and any other relevant documentation to reflect the new configuration process.

## Dependencies

- **US2** depends on **US1**. The integration cannot be done until the loader function is complete.

## Parallel Execution

Within each user story, tasks can be parallelized:
- **US1**: Test tasks (T009-T012) can be written in parallel with the implementation tasks (T003-T008), assuming a clear function signature is defined first.
- **US2**: Modifications to different entry points (T013, T014) can be done in parallel if they are independent.

## Implementation Strategy

The implementation will follow an MVP-first approach.
1.  **MVP**: Complete all tasks for User Story 1 to create a functional and tested config loader.
2.  **Incremental Delivery**: Complete User Story 2 to integrate the loader into the application.
3.  **Finalization**: Complete the Polish phase to ensure security and documentation are up-to-date.
