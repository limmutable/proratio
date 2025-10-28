# Research: Enhanced Testing and Validation Reporting

**Feature**: 001-test-validation-dashboard
**Date**: 2025-10-27
**Status**: Complete

## Overview

This document consolidates research findings for implementing integration tests and centralized validation result storage. All NEEDS CLARIFICATION items from the plan have been resolved through analysis of project context, industry best practices, and constitutional requirements.

## Research Questions

### 1. Integration Testing Best Practices for Python Multi-Module Projects

**Question**: How to structure integration tests that span multiple modules (proratio_signals → proratio_tradehub) while maintaining module independence?

**Decision**: Use pytest with a dedicated `tests/test_integration/` directory and module-scoped fixtures that instantiate real components while maintaining test isolation.

**Rationale**:
- **Module independence preserved**: Integration tests import from modules but don't create new cross-module dependencies. Tests depend on modules, not modules on tests.
- **Fixture strategy**: Use `conftest.py` at `tests/test_integration/` level to provide shared fixtures (database connections, test data) while keeping individual test files focused on specific workflows.
- **Test isolation**: Each integration test runs in its own transaction/session that rolls back after completion, ensuring tests don't interfere with each other.
- **Existing pattern alignment**: Project already uses pytest with `tests/test_<module>/` structure; integration tests follow the same pattern at a higher level.

**Alternatives Considered**:
- **Separate integration test repository**: Rejected - adds complexity and separates tests from code
- **Docker Compose for full stack testing**: Rejected for Phase 1 - too heavy for these specific integration tests, may revisit for full system tests later
- **Mocking module boundaries**: Rejected - defeats purpose of integration testing, which verifies actual component interactions

**References**:
- pytest fixtures documentation: https://docs.pytest.org/en/stable/reference/fixtures.html
- Testing strategies for modular Python projects: Integration tests sit between unit tests (single module) and E2E tests (full system)

---

### 2. Database Schema Design for Time-Series Performance Metrics

**Question**: What is the optimal database schema for storing validation results with efficient querying by strategy name, time range, and git commit?

**Decision**: Single table `validation_results` with composite indexes on `(strategy_name, timestamp)` and `(git_commit_hash, timestamp)`.

**Schema**:
```sql
CREATE TABLE validation_results (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_trades INTEGER NOT NULL CHECK (total_trades >= 0),
    win_rate DECIMAL(5,2) CHECK (win_rate >= 0 AND win_rate <= 100),
    total_profit_pct DECIMAL(10,4),
    max_drawdown DECIMAL(10,4) CHECK (max_drawdown <= 0),
    sharpe_ratio DECIMAL(10,4),
    profit_factor DECIMAL(10,4) CHECK (profit_factor >= 0),
    git_commit_hash VARCHAR(40),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_strategy_timestamp ON validation_results(strategy_name, timestamp DESC);
CREATE INDEX idx_commit_timestamp ON validation_results(git_commit_hash, timestamp DESC);
CREATE INDEX idx_timestamp ON validation_results(timestamp DESC);
```

**Rationale**:
- **Single table simplicity**: No joins needed for common queries, aligns with "start simple" philosophy
- **Composite indexes**: Support common query patterns (all results for a strategy, results by time range, results for a specific commit)
- **Timestamp descending**: Most recent results are queried most frequently (dashboard shows latest runs)
- **CHECK constraints**: Enforce data quality at database level (win_rate 0-100, drawdown ≤ 0, etc.)
- **VARCHAR(40) for git hash**: Git SHA-1 hashes are 40 hex characters
- **DECIMAL for financial metrics**: Avoid floating-point rounding errors in financial calculations

**Alternatives Considered**:
- **Separate strategy table**: Rejected - premature normalization. Strategy name is sufficient identifier, no additional strategy metadata currently needed.
- **Time-series database (TimescaleDB)**: Rejected - over-engineering for current scale. Single PostgreSQL table handles expected volume (<1000 records/day).
- **JSON column for flexible metrics**: Rejected - loses type safety and query performance. Fixed schema better matches known metric structure.

**References**:
- PostgreSQL indexing strategies: https://www.postgresql.org/docs/current/indexes-types.html
- Time-series data patterns: Composite indexes on (dimension, time) optimize range queries

---

### 3. SQLAlchemy ORM vs Raw SQL for Simple Insert/Query Operations

**Question**: Should we use SQLAlchemy ORM (already a dependency) or raw SQL for validation result storage given the simple schema and performance constraints (<1 second writes)?

**Decision**: Use SQLAlchemy Core (not ORM) with declarative table definitions and connection pooling.

**Rationale**:
- **SQLAlchemy already a dependency**: No new dependencies, leverages existing infrastructure
- **Core vs ORM**: Core provides SQL expression language with type safety without ORM overhead. Simpler model for insert-heavy, read-light operations.
- **Type safety**: Python type hints + SQLAlchemy types catch schema mismatches at development time
- **Connection pooling**: SQLAlchemy handles connection management, important for <1 second write constraint
- **Prepared statements**: Automatically parameterized queries prevent SQL injection
- **Portability**: Easier to switch databases (PostgreSQL → SQLite for tests) with minimal code changes

**Implementation Pattern**:
```python
from sqlalchemy import create_engine, Table, Column, Integer, String, DECIMAL, TIMESTAMP, MetaData
from sqlalchemy.sql import insert, select

metadata = MetaData()

validation_results = Table(
    'validation_results', metadata,
    Column('id', Integer, primary_key=True),
    Column('strategy_name', String(255), nullable=False),
    Column('timestamp', TIMESTAMP, nullable=False),
    # ... other columns
)

# Insert
with engine.begin() as conn:
    conn.execute(insert(validation_results).values(**metrics))

# Query
with engine.connect() as conn:
    results = conn.execute(
        select(validation_results)
        .where(validation_results.c.strategy_name == 'GridTrading')
        .order_by(validation_results.c.timestamp.desc())
    ).fetchall()
```

**Alternatives Considered**:
- **Full SQLAlchemy ORM**: Rejected - unnecessary overhead for simple insert/select operations. No need for object-relational mapping when working with flat metric dictionaries.
- **Raw SQL with psycopg2**: Rejected - loses type safety, manual connection management, harder to test with different databases.
- **pandas.to_sql()**: Rejected - too high-level, hides connection management and error handling.

**References**:
- SQLAlchemy Core tutorial: https://docs.sqlalchemy.org/en/20/core/
- Performance comparison: Core is 20-30% faster than ORM for simple operations

---

### 4. Test Data Management for Integration Tests

**Question**: How should integration tests manage test data (fixtures, factories, cleanup) for data pipeline and signal workflows without polluting production data?

**Decision**: Use pytest fixtures with function scope, in-memory SQLite for database tests, temporary directories for file storage, and automatic cleanup via fixture teardown.

**Pattern**:
```python
# tests/test_integration/conftest.py
import pytest
import tempfile
from pathlib import Path
from sqlalchemy import create_engine

@pytest.fixture(scope="function")
def test_db():
    """Provide an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    # Create tables
    metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def test_storage_dir():
    """Provide a temporary directory for data storage tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
    # Automatic cleanup when context exits

@pytest.fixture(scope="function")
def mock_market_data():
    """Provide synthetic market data for signal generation tests."""
    import pandas as pd
    # Generate 100 days of synthetic OHLCV data
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    return pd.DataFrame({
        'timestamp': dates,
        'open': 50000 + pd.np.random.randn(100) * 1000,
        'high': 51000 + pd.np.random.randn(100) * 1000,
        'low': 49000 + pd.np.random.randn(100) * 1000,
        'close': 50000 + pd.np.random.randn(100) * 1000,
        'volume': 1000000 + pd.np.random.randn(100) * 100000,
    })
```

**Rationale**:
- **Function scope**: Each test gets fresh fixtures, no state leakage between tests
- **In-memory SQLite**: Fast (no disk I/O), isolated (separate DB per test), automatic cleanup (memory freed when test ends)
- **tempfile.TemporaryDirectory**: OS-managed cleanup, works across platforms, handles edge cases (permissions, disk full)
- **Synthetic data generation**: No external dependencies (APIs, files), reproducible, fast
- **Fixture composition**: Tests combine fixtures as needed (test_db + mock_market_data for full workflow)

**Alternatives Considered**:
- **Shared test database with transactions**: Rejected - rollback complexity, potential for test interference, harder to parallelize
- **Fixture files (JSON/CSV)**: Rejected for generated data - adds maintenance burden, less flexible than programmatic generation
- **Docker containers for PostgreSQL**: Rejected for Phase 1 - too slow for test suite (<5 minute requirement), may add for CI/CD later
- **Database factories (factory_boy)**: Rejected - overkill for simple metric dictionaries, adds dependency

**References**:
- pytest fixtures best practices: https://docs.pytest.org/en/stable/how-to/fixtures.html
- Testing with SQLite: https://www.sqlite.org/inmemorydb.html

---

### 5. Security Considerations for Storing Strategy Validation Results

**Question**: Are there sensitive data concerns when storing strategy names, parameters, or performance metrics in the database?

**Decision**: Validation results (strategy name, performance metrics, git commit) are **not sensitive**. No additional encryption or access control needed beyond database credentials in `.env`.

**Rationale**:
- **Strategy names**: Descriptive identifiers (e.g., "GridTrading", "AIEnhancedMomentum"), not proprietary algorithms
- **Performance metrics**: Aggregate statistics (win rate, Sharpe ratio), not individual trade details
- **Git commit hash**: Public repository identifier, useful for debugging
- **No trade-level data**: Individual trades (entry/exit prices, position sizes) NOT stored in validation results
- **No API keys or credentials**: Validation results contain only derived metrics
- **Database access**: Protected by standard database authentication (username/password in `.env`)

**Security measures already in place**:
- ✅ Database credentials in `.env` (not committed per constitution)
- ✅ Pre-commit hooks scan for exposed secrets
- ✅ No logging of connection strings with credentials
- ✅ Database backups encrypted (if implemented, outside scope of this feature)

**Data classification**:
- **Strategy name**: Internal use only, not public but not secret
- **Performance metrics**: Business confidential, protected by database authentication
- **Git commit hash**: Public (assuming public repo) or internal (private repo)

**Alternatives Considered**:
- **Encrypt validation_results table**: Rejected - over-engineering, adds complexity and performance overhead without meaningful security benefit
- **Separate database with stricter access control**: Rejected - validation results are internal metrics, same access model as application database is appropriate
- **Anonymize strategy names**: Rejected - defeats purpose of tracking performance by strategy, no benefit given existing database access control

**Recommendation for future**:
If individual trade details are ever stored (outside current scope), implement:
1. Separate `trades` table with row-level encryption
2. Access audit logging
3. Data retention policies (auto-delete after N days)

**References**:
- OWASP Data Classification: Aggregate metrics typically "Confidential" not "Secret"
- Constitution Security Requirements: Validates that secrets in `.env` requirement is sufficient

---

## Implementation Checklist

All research questions resolved. Ready to proceed to Phase 1 (Design & Contracts):

- [x] Integration testing structure defined
- [x] Database schema designed with indexes
- [x] SQLAlchemy Core approach selected
- [x] Test data management pattern established
- [x] Security requirements validated

## Next Steps

1. Create `data-model.md` with entity definitions based on schema research
2. Create `contracts/validation_result_schema.sql` from schema decision
3. Create `contracts/validation_repository_interface.py` defining Python interface
4. Create `quickstart.md` with setup and usage instructions
5. Run `.specify/scripts/bash/update-agent-context.sh claude` to update agent memory

## Notes

- All decisions align with project constitution (modularity, testing, configuration, code quality)
- No new dependencies required - leverages existing pytest, SQLAlchemy, PostgreSQL stack
- Complexity minimized - single table, simple fixtures, no ORM overhead
- Performance targets met - in-memory tests (<5 min suite), single-transaction writes (<1 sec)
