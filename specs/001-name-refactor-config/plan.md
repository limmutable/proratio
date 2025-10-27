# Implementation Plan: Configuration Consolidation

**Branch**: `001-name-refactor-config` | **Date**: 2025-10-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-name-refactor-config/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature refactors the configuration management system to establish a single source of truth. It introduces a dynamic loading mechanism that hydrates a base `freqtrade` JSON configuration with secrets and environment-specific settings from the Pydantic `Settings` object at runtime. This eliminates configuration duplication and ensures consistency.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Pydantic, Freqtrade
**Storage**: N/A
**Testing**: pytest
**Target Platform**: Linux server (via Docker)
**Project Type**: single
**Performance Goals**: No noticeable startup delay.
**Constraints**: Hydrated configuration must not be written to disk.
**Scale/Scope**: Affects all application entry points that rely on `freqtrade` configuration.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Modularity and Separation of Concerns**: **PASS**. The new loading function will be located in `proratio_utilities.config`, respecting the existing modular structure.
- **II. Centralized Configuration**: **PASS**. This feature directly reinforces this principle by removing duplicated configuration and making the Pydantic `Settings` object the single source of truth.
- **III. Data-Driven Development**: **PASS**. No impact on the core data flow.
- **IV. Rigorous Backtesting**: **PASS**. No direct impact, but existing tests will need to be updated to use the new configuration loading mechanism.
- **V. Strict Risk Management**: **PASS**. No impact on risk management logic.

## Project Structure

### Documentation (this feature)

```text
specs/001-name-refactor-config/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
proratio_utilities/
└── config/
    ├── __init__.py
    ├── loader.py          # New file for the hydration logic
    └── settings.py        # Existing Pydantic settings

proratio_cli/
└── main.py              # Will be updated to use the new loader

scripts/
└── run_paper_trading.sh # Will be updated

tests/
└── test_utilities/
    └── test_config_loader.py # New test file
```

**Structure Decision**: The project is a single, monolithic repository. The new logic will be added to the existing `proratio_utilities/config` module to maintain separation of concerns. New tests will be added to validate the hydration logic.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A       | N/A        | N/A                                 |
