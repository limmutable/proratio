#!/bin/bash
# Start Paper Trading with ML Ensemble Strategy
# Duration: 3 hours test run with detailed logging

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ML Ensemble Paper Trading Test (3 hours) ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
STRATEGY="HybridMLLLMStrategy"
CONFIG="proratio_utilities/config/freqtrade/config_paper_ml_test.json"
LOG_DIR="user_data/logs"
LOG_FILE="${LOG_DIR}/paper_trading_ml_test.log"
PID_FILE="/tmp/freqtrade_ml_paper.pid"

# Create logs directory
mkdir -p "${LOG_DIR}"

# Check if already running
if [ -f "${PID_FILE}" ]; then
    OLD_PID=$(cat "${PID_FILE}")
    if ps -p "${OLD_PID}" > /dev/null 2>&1; then
        echo -e "${RED}❌ ML paper trading already running (PID: ${OLD_PID})${NC}"
        echo "Stop it first: ./scripts/stop_ml_paper_trading.sh"
        exit 1
    else
        rm -f "${PID_FILE}"
    fi
fi

# Check ensemble model
if [ ! -f "models/ensemble_model.pkl" ]; then
    echo -e "${RED}❌ Ensemble model not found!${NC}"
    echo "Model file: models/ensemble_model.pkl"
    exit 1
fi

echo -e "${GREEN}✅ Ensemble model found ($(ls -lh models/ensemble_model.pkl | awk '{print $5}'))${NC}"
echo ""
echo -e "${BLUE}📋 Configuration:${NC}"
echo "  Strategy: ${STRATEGY}"
echo "  Pair: BTC/USDT"
echo "  Timeframe: 4h"
echo "  Initial Balance: 10,000 USDT"
echo "  Max Open Trades: 2"
echo "  Stake per Trade: 100 USDT"
echo ""
echo -e "${BLUE}📝 Logging:${NC}"
echo "  Main Log: ${LOG_FILE}"
echo "  API: http://localhost:8080 (admin/admin)"
echo ""
echo -e "${YELLOW}⏰ Test Duration: 3 hours${NC}"
echo -e "${YELLOW}📊 Monitor: tail -f ${LOG_FILE}${NC}"
echo -e "${YELLOW}🛑 Stop: ./scripts/stop_ml_paper_trading.sh${NC}"
echo ""

# Clear old logs
echo -e "${BLUE}🗑️  Clearing old logs...${NC}"
> "${LOG_FILE}"

# Download latest data
echo -e "${BLUE}📥 Downloading latest market data...${NC}"
./venv/bin/freqtrade download-data \
    --exchange binance \
    --pairs BTC/USDT \
    --timeframe 4h \
    --days 2 \
    --userdir user_data \
    >> "${LOG_FILE}" 2>&1

echo -e "${GREEN}✅ Data downloaded${NC}"
echo ""

# Start paper trading in background
echo -e "${GREEN}🚀 Starting paper trading...${NC}"
echo ""

nohup ./venv/bin/freqtrade trade \
    --strategy "${STRATEGY}" \
    --config "${CONFIG}" \
    --userdir user_data \
    >> "${LOG_FILE}" 2>&1 &

# Save PID
FREQTRADE_PID=$!
echo "${FREQTRADE_PID}" > "${PID_FILE}"

# Wait for startup
echo -e "${YELLOW}⏳ Waiting for startup (10 seconds)...${NC}"
sleep 10

# Check if still running
if ! ps -p "${FREQTRADE_PID}" > /dev/null 2>&1; then
    echo -e "${RED}❌ Failed to start! Check logs:${NC}"
    echo "  tail -50 ${LOG_FILE}"
    rm -f "${PID_FILE}"
    exit 1
fi

echo -e "${GREEN}✅ Paper trading started successfully!${NC}"
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            PAPER TRADING ACTIVE            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo "PID: ${FREQTRADE_PID}"
echo "Started: $(date)"
echo "Expected End: $(date -v+3H 2>/dev/null || date -d '+3 hours' 2>/dev/null || echo 'in 3 hours')"
echo ""
echo -e "${YELLOW}📊 Monitor Commands:${NC}"
echo ""
echo "  # Watch main log"
echo "  tail -f ${LOG_FILE}"
echo ""
echo "  # Watch for ML predictions"
echo "  tail -f ${LOG_FILE} | grep 'ML Prediction'"
echo ""
echo "  # Watch for trades"
echo "  tail -f ${LOG_FILE} | grep -i 'buy\|sell\|entry\|exit'"
echo ""
echo "  # Check status"
echo "  ps -p ${FREQTRADE_PID}"
echo ""
echo "  # Stop trading"
echo "  ./scripts/stop_ml_paper_trading.sh"
echo ""
echo -e "${BLUE}💡 Tip: Let it run for 3 hours, then analyze ${LOG_FILE}${NC}"
echo ""
