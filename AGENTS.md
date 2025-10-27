# Proratio Agent Guidelines

This document provides guidelines for AI agents working on the Proratio codebase.

## Build, Lint & Test

- **Linting**: `ruff check --fix .`
- **Formatting**: `ruff format .`
- **Run all tests**: `pytest`
- **Run tests for a module**: `pytest tests/test_signals/`
- **Run a single test file**: `pytest tests/test_signals/test_base_provider.py`
- **Run a single test function**: `pytest tests/test_signals/test_base_provider.py::test_my_function`

## Code Style

- **Imports**: Grouped and ordered: 1. standard library, 2. third-party, 3. application-specific.
- **Formatting**: Use `ruff format` (Black-compatible, 88 char line length).
- **Types**: Use type hints for all function signatures. Use `Optional` for nullable types.
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes.
- **Error Handling**: Use specific custom exceptions from `proratio_signals/llm_providers/exceptions.py`.
- **Docstrings**: Google-style docstrings for all public modules, classes, and functions.
- **Logging**: Use the `logging` module for logging errors and info.
- **Modularity**: Keep code in the appropriate module (`signals`, `quantlab`, `tradehub`, `utilities`).
