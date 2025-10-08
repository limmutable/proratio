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
