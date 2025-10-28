# Data Model: Enhanced Testing and Validation Reporting

**Feature**: 001-test-validation-dashboard
**Date**: 2025-10-27
**Status**: Complete

## Overview

This document defines the data entities for storing backtest validation results in a persistent database. The model supports tracking strategy performance over time with full traceability to code versions.

## Entities

### Validation Result

**Description**: Represents a single backtest validation run for a specific strategy at a specific point in time.

**Purpose**: Store performance metrics from completed backtest validations to enable historical tracking, performance analysis, and regression detection.

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for this validation run |
| strategy_name | VARCHAR(255) | NOT NULL | Name of the strategy being validated (e.g., "GridTrading", "AIEnhanced") |
| timestamp | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When the backtest validation completed |
| total_trades | INTEGER | NOT NULL, >= 0 | Total number of trades executed during backtest |
| win_rate | DECIMAL(5,2) | >= 0 AND <= 100 | Percentage of winning trades (0.00 to 100.00) |
| total_profit_pct | DECIMAL(10,4) | | Total profit/loss as percentage of initial capital (can be negative) |
| max_drawdown | DECIMAL(10,4) | <= 0 | Maximum peak-to-trough decline as percentage (stored as negative value) |
| sharpe_ratio | DECIMAL(10,4) | | Risk-adjusted return measure (returns divided by volatility) |
| profit_factor | DECIMAL(10,4) | >= 0 | Ratio of gross profit to gross loss (>1 is profitable) |
| git_commit_hash | VARCHAR(40) | NULLABLE | Git SHA-1 hash of code version used for this validation |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When this record was inserted into database |

**Relationships**:
- Belongs to Strategy (through strategy_name, foreign key-like relationship but not enforced)
- Has many Performance Metrics (conceptual relationship - metrics are stored as columns)

**Validation Rules**:

1. **Strategy Name**:
   - Required (NOT NULL)
   - Must match pattern: `^[A-Za-z0-9_-]+$` (alphanumeric, underscore, hyphen)
   - Max length: 255 characters

2. **Timestamp**:
   - Required (NOT NULL)
   - Cannot be in the future (validated at application level)
   - Used for time-series ordering

3. **Total Trades**:
   - Required (NOT NULL)
   - Must be >= 0 (CHECK constraint)
   - Zero trades indicates validation ran but strategy generated no signals

4. **Win Rate**:
   - Optional (NULL allowed if no trades executed)
   - Range: 0.00 to 100.00 (CHECK constraint)
   - Stored with 2 decimal precision (e.g., 67.25 = 67.25%)

5. **Total Profit Percentage**:
   - Optional (NULL allowed)
   - Can be negative (losses)
   - 4 decimal precision for accuracy (e.g., -15.3750 = -15.375% loss)

6. **Max Drawdown**:
   - Optional (NULL allowed)
   - Must be <= 0 (CHECK constraint - drawdowns are negative)
   - Stored as percentage (e.g., -18.50 = 18.5% drawdown)

7. **Sharpe Ratio**:
   - Optional (NULL allowed)
   - Can be negative (poor risk-adjusted returns)
   - Typical range: -3.0 to +5.0, but no hard constraint

8. **Profit Factor**:
   - Optional (NULL allowed)
   - Must be >= 0 (CHECK constraint)
   - Values > 1.0 indicate profitability

9. **Git Commit Hash**:
   - Optional (NULL if git not available or not a git repo)
   - Exactly 40 hexadecimal characters when present
   - Validates pattern: `^[0-9a-f]{40}$` at application level

10. **Created At**:
    - Required (NOT NULL, defaults to current timestamp)
    - Immutable (never updated after insert)

**State Transitions**:
- **N/A** - Validation results are immutable once stored (append-only table)
- Records are never updated or deleted (preserve historical data integrity)

---

### Strategy (Conceptual Entity)

**Description**: Represents a trading strategy that can have multiple validation runs over time.

**Purpose**: Group validation results by strategy to enable per-strategy analysis and performance tracking.

**Note**: This is a **conceptual entity only** - no separate strategy table is created. Strategy identity is represented by the `strategy_name` field in Validation Result entity.

**Identifying Attribute**:
- **strategy_name**: Unique identifier for the strategy

**Relationships**:
- Has many Validation Results (1:N relationship via strategy_name)

**Rationale for not creating separate table**:
- Current requirements only need strategy name as identifier
- No additional strategy metadata (description, parameters, author) currently needed
- Avoids premature normalization and JOIN performance overhead
- Can be refactored to separate table later if strategy metadata requirements emerge

---

### Performance Metric (Conceptual Entity)

**Description**: Represents a specific measurable aspect of strategy performance (win rate, profit, drawdown, etc.)

**Purpose**: Provide granular view of strategy performance across multiple dimensions.

**Note**: This is a **conceptual entity only** - metrics are stored as individual columns in Validation Result table, not separate rows.

**Attributes**:
- **metric_name**: Type of metric (win_rate, total_profit_pct, max_drawdown, sharpe_ratio, profit_factor)
- **metric_value**: Numeric value of the metric
- **metric_unit**: Unit of measurement (percentage, ratio, count)

**Relationships**:
- Belongs to Validation Result (N:1 relationship - multiple metrics per validation)

**Rationale for column-based storage (not row-based)**:
- Fixed set of known metrics (not dynamic/extensible)
- Querying is simpler with columns (SELECT win_rate WHERE strategy_name = ...)
- Better type safety (DECIMAL constraints per metric)
- Avoids Entity-Attribute-Value (EAV) anti-pattern complexity
- Can pivot to row-based storage later if metric extensibility becomes a requirement

---

## Indexes

**Purpose**: Optimize common query patterns for validation result retrieval.

1. **idx_strategy_timestamp** (strategy_name, timestamp DESC)
   - **Use case**: Get all validations for a specific strategy, most recent first
   - **Query example**: "Show me the last 100 validation runs for GridTrading"
   - **Cardinality**: High (unique per strategy + time combination)

2. **idx_commit_timestamp** (git_commit_hash, timestamp DESC)
   - **Use case**: Get all validations for a specific code version
   - **Query example**: "Show me all validation runs for commit abc123"
   - **Cardinality**: Medium (multiple strategies may run on same commit)

3. **idx_timestamp** (timestamp DESC)
   - **Use case**: Get most recent validations across all strategies
   - **Query example**: "Show me the last 50 validation runs system-wide"
   - **Cardinality**: High (unique per validation)

**Index Selection Rationale**:
- Composite indexes cover common access patterns (strategy + time, commit + time)
- DESC ordering optimizes "most recent" queries (dashboard default view)
- Single-column timestamp index supports cross-strategy time-range queries
- No index on performance metrics (not used for filtering, only retrieval)

---

## Query Patterns

### Insert Validation Result

```python
# Single insert after backtest completes
insert_validation_result({
    'strategy_name': 'GridTrading',
    'timestamp': datetime.utcnow(),
    'total_trades': 150,
    'win_rate': 65.33,
    'total_profit_pct': 12.45,
    'max_drawdown': -8.75,
    'sharpe_ratio': 1.82,
    'profit_factor': 1.65,
    'git_commit_hash': 'a1b2c3d4e5f6...'
})
```

### Query Validation Results by Strategy

```python
# Get last 100 validation runs for a strategy
results = query_validation_results(
    strategy_name='GridTrading',
    limit=100,
    order_by='timestamp_desc'
)
```

### Query Validation Results by Time Range

```python
# Get all validations in the last 30 days
results = query_validation_results(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    order_by='timestamp_desc'
)
```

### Query Validation Results by Git Commit

```python
# Get all validations for a specific code version
results = query_validation_results(
    git_commit_hash='a1b2c3d4e5f6...',
    order_by='strategy_name_asc'
)
```

---

## Data Integrity

**Immutability**:
- Validation results are **append-only** (no UPDATE or DELETE operations)
- Preserves complete historical record for auditing and trend analysis
- If a validation run needs to be "corrected", insert a new record with updated values

**Uniqueness**:
- No enforced uniqueness constraint on (strategy_name, timestamp, git_commit_hash)
- Multiple validations for same strategy at same time are allowed (different parameter sets)
- Application-level deduplication if needed (check last N minutes before insert)

**Referential Integrity**:
- No foreign key to strategy table (no separate strategy table exists)
- Git commit hash is advisory only (not validated against actual git repo)
- Application is responsible for ensuring strategy_name matches active strategies

**NULL Handling**:
- Performance metrics can be NULL if backtest produces no trades
- Git commit hash can be NULL if git is unavailable
- Application logic must handle NULLs gracefully (display as "N/A" in reports)

---

## Migration Strategy

**Initial Schema Creation**:
1. Run `contracts/validation_result_schema.sql` to create table and indexes
2. Verify table exists: `SELECT * FROM validation_results LIMIT 1;`
3. No seed data required (table starts empty)

**Future Schema Changes**:
- Add columns with ALTER TABLE (e.g., `ALTER TABLE validation_results ADD COLUMN new_metric DECIMAL(10,4);`)
- Backfill existing rows with NULL for new columns (acceptable for metrics)
- Create new indexes if query patterns change (e.g., index on new_metric)
- Never delete columns or change existing column types (maintain backward compatibility)

**Data Retention**:
- No automatic deletion of old records (unlimited retention by default)
- Manual archival script can be added later if database size becomes an issue
- Recommend partitioning by year if >1M records accumulated (future optimization)

---

## Testing Considerations

**Unit Tests** (test_utilities/test_validation_repository.py):
- Test validation result insertion with valid data
- Test validation result insertion with NULL optional fields
- Test validation result insertion with invalid data (negative win_rate, future timestamp)
- Test query by strategy name
- Test query by time range
- Test query by git commit hash
- Test connection failure handling

**Integration Tests** (test_integration/test_data_pipeline.py, test_integration/test_signal_to_trade.py):
- Test end-to-end validation workflow (backtest → metrics → database insert)
- Verify database contains expected record after validation completes
- Test validation script continues if database is unavailable

**Test Data**:
- Use in-memory SQLite for unit tests (fast, isolated)
- Use synthetic validation results (fixed strategy names, known metrics)
- Clean up test database after each test (function-scoped fixtures)

---

## References

- **Feature Spec**: [spec.md](./spec.md) - FR-004, FR-005, FR-008, FR-009
- **Research**: [research.md](./research.md) - Section 2 (Database Schema Design)
- **Contract**: [contracts/validation_result_schema.sql](./contracts/validation_result_schema.sql)
