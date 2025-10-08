#!/bin/bash
#
# 3-Hour Paper Trading Test - Mean Reversion Strategy
#
# This script will:
# 1. Start Freqtrade in dry-run mode with MeanReversionTest strategy
# 2. Monitor for 3 hours
# 3. Automatically stop and generate report
#
# Usage: ./scripts/run_3h_test.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/jlim/Projects/proratio"
TEST_DURATION_SECONDS=$((3 * 60 * 60))  # 3 hours
STRATEGY="MeanReversionTest"
CONFIG="proratio_utilities/config/freqtrade/config_test_3h.json"
LOG_FILE="user_data/logs/test_3h_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Mean Reversion Strategy - 3 Hour Paper Trading Test          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Freqtrade is already running
if pgrep -f "freqtrade trade" > /dev/null; then
    echo -e "${RED}❌ Freqtrade is already running!${NC}"
    echo "Stop it first with: pkill -f 'freqtrade trade'"
    exit 1
fi

# Check if Docker containers are running
echo -e "${YELLOW}🔍 Checking Docker containers...${NC}"
if ! docker ps | grep -q proratio_postgres; then
    echo -e "${YELLOW}⚠️  PostgreSQL not running. Starting Docker containers...${NC}"
    cd "$PROJECT_ROOT"
    docker-compose up -d postgres redis
    sleep 3
fi
echo -e "${GREEN}✓ Docker containers running${NC}"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/user_data/logs"

# Display test configuration
echo ""
echo -e "${BLUE}📋 Test Configuration:${NC}"
echo "  Strategy: $STRATEGY"
echo "  Timeframe: 1h"
echo "  Pairs: BTC/USDT, ETH/USDT"
echo "  Duration: 3 hours"
echo "  Start Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  End Time (estimated): $(date -v+3H '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -d '+3 hours' '+%Y-%m-%d %H:%M:%S')"
echo "  Config: $CONFIG"
echo "  Log File: $LOG_FILE"
echo ""

# Countdown
echo -e "${YELLOW}Starting in 5 seconds... (Ctrl+C to cancel)${NC}"
sleep 5

# Start Freqtrade in background
echo -e "${GREEN}🚀 Starting Freqtrade...${NC}"
cd "$PROJECT_ROOT"

PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH" uv run freqtrade trade \
    --strategy "$STRATEGY" \
    --config "$CONFIG" \
    --userdir user_data \
    --logfile "$LOG_FILE" \
    > "$LOG_FILE.stdout" 2>&1 &

FREQTRADE_PID=$!

echo -e "${GREEN}✓ Freqtrade started (PID: $FREQTRADE_PID)${NC}"
echo ""

# Save PID for later reference
echo $FREQTRADE_PID > /tmp/proratio_test_3h.pid

# Display monitoring info
echo -e "${BLUE}📊 Monitoring Commands:${NC}"
echo "  View logs: tail -f $LOG_FILE"
echo "  View stdout: tail -f $LOG_FILE.stdout"
echo "  Check status: curl http://localhost:8081/api/v1/status"
echo "  Stop manually: kill $FREQTRADE_PID"
echo ""

# Create monitoring function
monitor_test() {
    local elapsed=0
    local checkpoint_interval=900  # 15 minutes
    local next_checkpoint=$checkpoint_interval

    while [ $elapsed -lt $TEST_DURATION_SECONDS ]; do
        sleep 60  # Check every minute
        elapsed=$((elapsed + 60))

        # Check if process is still running
        if ! kill -0 $FREQTRADE_PID 2>/dev/null; then
            echo -e "${RED}❌ Freqtrade stopped unexpectedly!${NC}"
            echo "Check logs: $LOG_FILE"
            exit 1
        fi

        # Progress update every 15 minutes
        if [ $elapsed -ge $next_checkpoint ]; then
            local hours=$((elapsed / 3600))
            local minutes=$(((elapsed % 3600) / 60))
            echo -e "${BLUE}[$(date '+%H:%M:%S')] Progress: ${hours}h ${minutes}m elapsed${NC}"
            next_checkpoint=$((next_checkpoint + checkpoint_interval))

            # Quick status check
            if command -v curl &> /dev/null; then
                curl -s http://localhost:8081/api/v1/status 2>/dev/null | grep -q "running" && \
                    echo -e "${GREEN}  ✓ Status: Running${NC}" || \
                    echo -e "${YELLOW}  ⚠️  API not responding${NC}"
            fi
        fi
    done
}

# Monitor test
echo -e "${YELLOW}⏱️  Test running... (will auto-stop in 3 hours)${NC}"
echo ""

monitor_test

# Stop Freqtrade
echo ""
echo -e "${YELLOW}⏹️  3 hours elapsed. Stopping Freqtrade...${NC}"
kill $FREQTRADE_PID 2>/dev/null || true
sleep 5

# Force kill if still running
if kill -0 $FREQTRADE_PID 2>/dev/null; then
    echo -e "${YELLOW}Force stopping...${NC}"
    kill -9 $FREQTRADE_PID 2>/dev/null || true
fi

# Clean up PID file
rm -f /tmp/proratio_test_3h.pid

echo -e "${GREEN}✓ Test completed!${NC}"
echo ""

# Generate summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Test Summary                                                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Start Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "End Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Duration: 3 hours"
echo ""
echo "📊 Check results:"
echo "  1. View full logs: less $LOG_FILE"
echo "  2. Check trades: grep 'TRADE' $LOG_FILE"
echo "  3. Check signals: grep 'ENTRY OPPORTUNITY' $LOG_FILE"
echo "  4. Check exits: grep 'EXIT SIGNAL' $LOG_FILE"
echo ""
echo "📈 Performance Analysis:"
echo "  Run: grep -E 'profit|loss|trade' $LOG_FILE | tail -20"
echo ""
echo -e "${GREEN}✅ Test completed successfully!${NC}"
