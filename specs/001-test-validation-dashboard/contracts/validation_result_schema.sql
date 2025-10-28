-- Database Schema for Backtest Validation Results
-- Feature: 001-test-validation-dashboard
-- Created: 2025-10-27
--
-- Purpose: Store historical backtest validation metrics for all trading strategies
-- to enable performance tracking, regression detection, and code-version traceability.
--
-- Compatible with: PostgreSQL 12+, SQLite 3.35+ (for testing)

-- Drop table if exists (for clean reinstall during development)
-- WARNING: This deletes all historical validation data!
-- Comment out in production environments.
DROP TABLE IF EXISTS validation_results CASCADE;

-- Create validation_results table
CREATE TABLE validation_results (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Strategy identification
    strategy_name VARCHAR(255) NOT NULL,

    -- Timing information
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Trade volume metrics
    total_trades INTEGER NOT NULL CHECK (total_trades >= 0),

    -- Performance metrics (can be NULL if no trades executed)
    win_rate DECIMAL(5,2) CHECK (win_rate IS NULL OR (win_rate >= 0 AND win_rate <= 100)),
    total_profit_pct DECIMAL(10,4),
    max_drawdown DECIMAL(10,4) CHECK (max_drawdown IS NULL OR max_drawdown <= 0),
    sharpe_ratio DECIMAL(10,4),
    profit_factor DECIMAL(10,4) CHECK (profit_factor IS NULL OR profit_factor >= 0),

    -- Code traceability (NULL if git not available)
    git_commit_hash VARCHAR(40)
);

-- Create indexes for common query patterns

-- Index 1: Query all validations for a specific strategy, most recent first
-- Use case: Dashboard showing latest validation runs for GridTrading strategy
CREATE INDEX idx_strategy_timestamp ON validation_results(strategy_name, timestamp DESC);

-- Index 2: Query all validations for a specific git commit
-- Use case: "Show me all strategy validations for commit abc123def456"
CREATE INDEX idx_commit_timestamp ON validation_results(git_commit_hash, timestamp DESC)
    WHERE git_commit_hash IS NOT NULL;  -- Partial index (only non-NULL commits)

-- Index 3: Query most recent validations across all strategies
-- Use case: Dashboard showing latest 50 validation runs system-wide
CREATE INDEX idx_timestamp ON validation_results(timestamp DESC);

-- Add comments to document field purposes
COMMENT ON TABLE validation_results IS 'Historical backtest validation metrics for all trading strategies';
COMMENT ON COLUMN validation_results.id IS 'Unique identifier for this validation run';
COMMENT ON COLUMN validation_results.strategy_name IS 'Name of the strategy being validated (e.g., GridTrading, AIEnhanced)';
COMMENT ON COLUMN validation_results.timestamp IS 'When the backtest validation completed (UTC)';
COMMENT ON COLUMN validation_results.total_trades IS 'Total number of trades executed during backtest';
COMMENT ON COLUMN validation_results.win_rate IS 'Percentage of winning trades (0.00 to 100.00)';
COMMENT ON COLUMN validation_results.total_profit_pct IS 'Total profit/loss as percentage of initial capital (can be negative)';
COMMENT ON COLUMN validation_results.max_drawdown IS 'Maximum peak-to-trough decline as percentage (stored as negative value, e.g., -18.5 = 18.5% drawdown)';
COMMENT ON COLUMN validation_results.sharpe_ratio IS 'Risk-adjusted return measure (returns divided by volatility)';
COMMENT ON COLUMN validation_results.profit_factor IS 'Ratio of gross profit to gross loss (>1 is profitable)';
COMMENT ON COLUMN validation_results.git_commit_hash IS 'Git SHA-1 hash (40 hex chars) of code version used for this validation';
COMMENT ON COLUMN validation_results.created_at IS 'When this record was inserted into database (immutable)';

-- Verification query: Show table structure
-- \d+ validation_results  -- (PostgreSQL psql command)

-- Sample insert query (for testing schema)
-- INSERT INTO validation_results (strategy_name, timestamp, total_trades, win_rate, total_profit_pct, max_drawdown, sharpe_ratio, profit_factor, git_commit_hash)
-- VALUES ('GridTrading', '2025-10-27 12:00:00', 150, 65.33, 12.45, -8.75, 1.82, 1.65, 'a1b2c3d4e5f6789012345678901234567890abcd');

-- Sample query: Get last 10 validations for a specific strategy
-- SELECT * FROM validation_results
-- WHERE strategy_name = 'GridTrading'
-- ORDER BY timestamp DESC
-- LIMIT 10;
