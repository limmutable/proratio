#!/bin/bash
#
# Start Proratio Paper Trading (Dry-Run Mode)
# Uses AIEnhancedStrategy with real-time AI signals
#

set -e

echo "======================================================================="
echo "  PRORATIO PAPER TRADING - DRY RUN MODE"
echo "======================================================================="
echo ""

# Check if Docker containers are running
echo "Checking infrastructure..."
if ! docker ps | grep -q proratio_postgres; then
    echo "✗ PostgreSQL not running. Starting..."
    docker-compose up -d postgres redis
    sleep 3
fi

if ! docker ps | grep -q proratio_redis; then
    echo "✗ Redis not running. Starting..."
    docker-compose up -d postgres redis
    sleep 3
fi

echo "✓ Infrastructure running"
echo ""

# Check .env file
if [ ! -f .env ]; then
    echo "✗ Error: .env file not found!"
    echo "  Copy .env.example to .env and add your API keys"
    exit 1
fi

echo "✓ .env file found"
echo ""

# Verify data exists
echo "Checking market data..."
RECORD_COUNT=$(docker exec proratio_postgres psql -U proratio -d proratio -t -c "SELECT COUNT(*) FROM ohlcv;" | tr -d ' ')

if [ "$RECORD_COUNT" -lt 1000 ]; then
    echo "✗ Insufficient data in database ($RECORD_COUNT records)"
    echo "  Run: uv run python scripts/download_historical_data.py"
    exit 1
fi

echo "✓ Database has $RECORD_COUNT OHLCV records"
echo ""

# Show configuration
echo "Paper Trading Configuration:"
echo "  Strategy: AIEnhancedStrategy"
echo "  Pairs: BTC/USDT, ETH/USDT"
echo "  Starting Capital: 10,000 USDT (virtual)"
echo "  Max Open Trades: 2"
echo "  AI Providers: Claude + Gemini (ChatGPT disabled - quota exceeded)"
echo "  Mode: DRY RUN (no real money)"
echo ""

# Warning
echo "⚠️  IMPORTANT:"
echo "  • This is PAPER TRADING mode (no real money)"
echo "  • AI signals will be generated in real-time"
echo "  • Monitor logs in user_data/logs/freqtrade.log"
echo "  • Press Ctrl+C to stop"
echo ""

read -p "Start paper trading? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "======================================================================="
echo "  STARTING PAPER TRADING..."
echo "======================================================================="
echo ""

# Start Freqtrade
uv run freqtrade trade \
  --strategy AIEnhancedStrategy \
  --config proratio_core/config/freqtrade/config_dry.json \
  --userdir user_data \
  --logfile user_data/logs/freqtrade.log \
  --db-url sqlite:///user_data/tradesv3_dryrun.sqlite
