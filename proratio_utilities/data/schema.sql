-- Proratio Database Schema
-- PostgreSQL schema for market data, signals, and trades

-- ============================================================================
-- OHLCV Market Data Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS ohlcv (
    id SERIAL PRIMARY KEY,
    exchange VARCHAR(20) NOT NULL,
    pair VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(20,8) NOT NULL,
    high DECIMAL(20,8) NOT NULL,
    low DECIMAL(20,8) NOT NULL,
    close DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exchange, pair, timeframe, timestamp)
);

-- Index for fast queries by pair and timeframe
CREATE INDEX IF NOT EXISTS idx_ohlcv_pair_timeframe
ON ohlcv(exchange, pair, timeframe, timestamp DESC);

-- Index for timestamp range queries
CREATE INDEX IF NOT EXISTS idx_ohlcv_timestamp
ON ohlcv(timestamp DESC);

-- ============================================================================
-- AI Signals Table (for Week 2)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ai_signals (
    id SERIAL PRIMARY KEY,
    pair VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    chatgpt_score DECIMAL(3,2),
    chatgpt_reasoning TEXT,
    claude_score DECIMAL(3,2),
    claude_reasoning TEXT,
    gemini_score DECIMAL(3,2),
    gemini_reasoning TEXT,
    consensus_score DECIMAL(3,2) NOT NULL,
    direction VARCHAR(10) NOT NULL,  -- 'long', 'short', 'neutral'
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_signals_pair_timestamp
ON ai_signals(pair, timestamp DESC);

-- ============================================================================
-- Trades Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    pair VARCHAR(20) NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    side VARCHAR(10) NOT NULL,  -- 'buy', 'sell'
    entry_price DECIMAL(20,8) NOT NULL,
    exit_price DECIMAL(20,8),
    quantity DECIMAL(20,8) NOT NULL,
    pnl DECIMAL(20,8),
    pnl_percent DECIMAL(10,4),
    ai_signal_id INTEGER REFERENCES ai_signals(id),
    strategy_name VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trades_pair
ON trades(pair, entry_time DESC);

CREATE INDEX IF NOT EXISTS idx_trades_signal
ON trades(ai_signal_id);

-- ============================================================================
-- System Metadata Table (for tracking data collection status)
-- ============================================================================
CREATE TABLE IF NOT EXISTS system_metadata (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial metadata
INSERT INTO system_metadata (key, value)
VALUES ('last_data_sync', '{"timestamp": null, "status": "initialized"}'::jsonb)
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- Validation Results Table (Feature: 001-test-validation-dashboard)
-- ============================================================================
-- Purpose: Store historical backtest validation metrics for all trading strategies
-- to enable performance tracking, regression detection, and code-version traceability.
--
-- Compatible with: PostgreSQL 12+, SQLite 3.35+ (for testing)

CREATE TABLE IF NOT EXISTS validation_results (
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
-- Use case: Dashboard showing latest validation runs for a specific strategy
CREATE INDEX IF NOT EXISTS idx_strategy_timestamp ON validation_results(strategy_name, timestamp DESC);

-- Index 2: Query all validations for a specific git commit
-- Use case: "Show me all strategy validations for commit abc123def456"
CREATE INDEX IF NOT EXISTS idx_commit_timestamp ON validation_results(git_commit_hash, timestamp DESC)
    WHERE git_commit_hash IS NOT NULL;  -- Partial index (only non-NULL commits)

-- Index 3: Query most recent validations across all strategies
-- Use case: Dashboard showing latest 50 validation runs system-wide
CREATE INDEX IF NOT EXISTS idx_timestamp ON validation_results(timestamp DESC);

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
