# Quickstart Guide: Enhanced Testing and Validation Reporting

**Feature**: 001-test-validation-dashboard
**Date**: 2025-10-27

## Overview

This guide walks you through setting up and using the new integration test suite and centralized validation results storage.

## Prerequisites

- Python 3.14+ installed
- PostgreSQL 12+ running (or SQLite for testing)
- Git repository initialized
- Dependencies installed: `pip install -r requirements.txt` (or `uv sync`)

## Setup

### 1. Database Setup

#### For Development (SQLite)

No setup required - integration tests use in-memory SQLite automatically.

#### For Production (PostgreSQL)

1. Create the database:
   ```bash
   psql -U postgres
   CREATE DATABASE proratio_validation;
   \q
   ```

2. Run the schema creation script:
   ```bash
   psql -U postgres -d proratio_validation -f specs/001-test-validation-dashboard/contracts/validation_result_schema.sql
   ```

3. Verify the table was created:
   ```bash
   psql -U postgres -d proratio_validation -c "\d+ validation_results"
   ```

4. Add database connection to `.env`:
   ```bash
   # Add to .env file (NEVER commit this file!)
   VALIDATION_DB_URL=postgresql://postgres:password@localhost:5432/proratio_validation
   ```

### 2. Configuration

Update your Pydantic Settings configuration to include the validation database URL:

```python
# proratio_utilities/config/settings.py (example)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing settings ...

    validation_db_url: str = Field(
        ...,
        env='VALIDATION_DB_URL',
        description='Database connection string for validation results'
    )

    class Config:
        env_file = '.env'
```

## Running Integration Tests

### Run All Integration Tests

```bash
# Run all integration tests
pytest tests/test_integration/ -v

# Expected output:
# tests/test_integration/test_data_pipeline.py::test_data_collection_to_storage PASSED
# tests/test_integration/test_data_pipeline.py::test_storage_to_loading PASSED
# tests/test_integration/test_data_pipeline.py::test_concurrent_reads PASSED
# tests/test_integration/test_signal_to_trade.py::test_signal_to_trade_creation PASSED
# tests/test_integration/test_signal_to_trade.py::test_trade_management_workflow PASSED
# tests/test_integration/test_signal_to_trade.py::test_trade_closure PASSED
# ==================== 6 passed in 45.32s ====================
```

### Run Specific Integration Test

```bash
# Run only data pipeline tests
pytest tests/test_integration/test_data_pipeline.py -v

# Run only signal-to-trade tests
pytest tests/test_integration/test_signal_to_trade.py -v

# Run a specific test function
pytest tests/test_integration/test_data_pipeline.py::test_data_collection_to_storage -v
```

### Run with Coverage

```bash
# Run integration tests with coverage report
pytest tests/test_integration/ --cov=proratio_utilities --cov=proratio_signals --cov=proratio_tradehub --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

## Storing Validation Results

### Manual Storage (Python API)

```python
from proratio_utilities.data.validation_repository import ValidationRepository
from datetime import datetime

# Initialize repository
repo = ValidationRepository()

# Store a validation result
result_id = repo.insert_validation_result(
    strategy_name='GridTrading',
    timestamp=datetime.utcnow(),
    total_trades=150,
    win_rate=65.33,
    total_profit_pct=12.45,
    max_drawdown=-8.75,
    sharpe_ratio=1.82,
    profit_factor=1.65,
    git_commit_hash='a1b2c3d4e5f6789012345678901234567890abcd'
)

print(f"Validation result stored with ID: {result_id}")
```

### Automatic Storage (Validation Script)

The validation script (`scripts/validate_backtest_results.py`) automatically stores results after each backtest:

```bash
# Run validation script (will store results in database)
python scripts/validate_backtest_results.py --strategy GridTrading

# Expected output:
# [2025-10-27 12:00:00] Running backtest validation for GridTrading...
# [2025-10-27 12:05:15] Backtest complete. Metrics:
#   - Total Trades: 150
#   - Win Rate: 65.33%
#   - Total Profit: 12.45%
#   - Max Drawdown: -8.75%
#   - Sharpe Ratio: 1.82
#   - Profit Factor: 1.65
# [2025-10-27 12:05:16] Validation result stored in database (ID: 12345)
# [2025-10-27 12:05:16] Validation report written to: tests/validation_results/GridTrading_2025-10-27.txt
```

## Querying Validation Results

### Query by Strategy

```python
from proratio_utilities.data.validation_repository import ValidationRepository

repo = ValidationRepository()

# Get last 10 validation runs for a specific strategy
results = repo.query_validation_results(
    strategy_name='GridTrading',
    limit=10,
    order_by='timestamp_desc'
)

for result in results:
    print(f"{result.timestamp}: {result.win_rate}% win rate, {result.total_profit_pct}% profit")
```

### Query by Time Range

```python
from datetime import datetime, timedelta

# Get all validations in the last 30 days
start_date = datetime.utcnow() - timedelta(days=30)
results = repo.query_validation_results(
    start_date=start_date,
    order_by='timestamp_desc'
)

print(f"Found {len(results)} validation runs in the last 30 days")
```

### Query by Git Commit

```python
# Get all validations for a specific code version
results = repo.query_validation_results(
    git_commit_hash='a1b2c3d4e5f6789012345678901234567890abcd',
    order_by='strategy_name_asc'
)

for result in results:
    print(f"{result.strategy_name}: {result.win_rate}% win rate")
```

### Get Latest Validation

```python
# Get the most recent validation for a strategy
latest = repo.get_latest_validation('GridTrading')

if latest:
    print(f"Latest GridTrading validation:")
    print(f"  Timestamp: {latest.timestamp}")
    print(f"  Win Rate: {latest.win_rate}%")
    print(f"  Profit: {latest.total_profit_pct}%")
    print(f"  Git Commit: {latest.git_commit_hash}")
else:
    print("No validation results found for GridTrading")
```

### Count Validations

```python
# Count total validations
total_count = repo.count_validations()
print(f"Total validation runs: {total_count}")

# Count validations for a specific strategy
strategy_count = repo.count_validations(strategy_name='GridTrading')
print(f"GridTrading validation runs: {strategy_count}")
```

## Direct Database Queries (SQL)

### Query Recent Validations

```sql
-- Get last 10 validation runs across all strategies
SELECT strategy_name, timestamp, win_rate, total_profit_pct, sharpe_ratio
FROM validation_results
ORDER BY timestamp DESC
LIMIT 10;
```

### Query Strategy Performance Over Time

```sql
-- Get all GridTrading validations in chronological order
SELECT timestamp, win_rate, total_profit_pct, max_drawdown, sharpe_ratio
FROM validation_results
WHERE strategy_name = 'GridTrading'
ORDER BY timestamp ASC;
```

### Query Validations by Git Commit

```sql
-- Get all validations for a specific code version
SELECT strategy_name, timestamp, win_rate, total_profit_pct
FROM validation_results
WHERE git_commit_hash = 'a1b2c3d4e5f6789012345678901234567890abcd'
ORDER BY strategy_name ASC;
```

### Aggregate Statistics

```sql
-- Calculate average win rate by strategy
SELECT
    strategy_name,
    COUNT(*) as validation_count,
    AVG(win_rate) as avg_win_rate,
    AVG(total_profit_pct) as avg_profit,
    AVG(sharpe_ratio) as avg_sharpe
FROM validation_results
GROUP BY strategy_name
ORDER BY avg_profit DESC;
```

## Troubleshooting

### Integration Tests Failing

**Problem**: Integration tests fail with "ModuleNotFoundError"

**Solution**: Ensure you're running tests from the repository root and dependencies are installed:
```bash
cd /path/to/proratio
pip install -r requirements.txt  # or: uv sync
pytest tests/test_integration/ -v
```

**Problem**: Integration tests fail with "Database connection error"

**Solution**: Integration tests use in-memory SQLite by default (no external database required). If you see this error, check the test fixtures in `tests/test_integration/conftest.py`.

### Database Connection Issues

**Problem**: Validation script fails with "Database connection error"

**Solution**: Check your `.env` file has the correct `VALIDATION_DB_URL`:
```bash
# Verify .env file exists and contains database URL
cat .env | grep VALIDATION_DB_URL

# Test database connection manually
psql -U postgres -d proratio_validation -c "SELECT COUNT(*) FROM validation_results;"
```

**Problem**: "relation validation_results does not exist"

**Solution**: Run the schema creation script:
```bash
psql -U postgres -d proratio_validation -f specs/001-test-validation-dashboard/contracts/validation_result_schema.sql
```

### Git Commit Hash Not Captured

**Problem**: Validation results show `git_commit_hash: None`

**Solution**: Ensure you're running validation from within a git repository with at least one commit:
```bash
# Check git status
git status

# If not a git repo, initialize it
git init
git add .
git commit -m "Initial commit"

# Run validation again
python scripts/validate_backtest_results.py --strategy GridTrading
```

### Slow Integration Tests

**Problem**: Integration test suite takes >5 minutes to run

**Solution**: Check if tests are using real databases instead of in-memory SQLite:
1. Review `tests/test_integration/conftest.py` fixtures
2. Ensure `test_db` fixture uses `sqlite:///:memory:`
3. Profile slow tests: `pytest tests/test_integration/ --durations=10`

## Next Steps

- **Run validation for all strategies**: `python scripts/validate_all_strategies.py`
- **View historical trends**: Query validation_results table with SQL or Python API
- **Set up CI/CD integration**: Add integration tests to your CI pipeline
- **Schedule regular validations**: Set up cron job to run validations daily

## References

- **Feature Spec**: [spec.md](./spec.md)
- **Implementation Plan**: [plan.md](./plan.md)
- **Data Model**: [data-model.md](./data-model.md)
- **Database Schema**: [contracts/validation_result_schema.sql](./contracts/validation_result_schema.sql)
- **Repository Interface**: [contracts/validation_repository_interface.py](./contracts/validation_repository_interface.py)
