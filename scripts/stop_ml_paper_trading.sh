#!/bin/bash
# Stop ML Paper Trading

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PID_FILE="/tmp/freqtrade_ml_paper.pid"

if [ ! -f "${PID_FILE}" ]; then
    echo -e "${YELLOW}⚠️  No paper trading process found${NC}"
    exit 0
fi

PID=$(cat "${PID_FILE}")

if ! ps -p "${PID}" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Process ${PID} not running${NC}"
    rm -f "${PID_FILE}"
    exit 0
fi

echo -e "${YELLOW}🛑 Stopping ML paper trading (PID: ${PID})...${NC}"

# Graceful shutdown
kill "${PID}"

# Wait up to 30 seconds for graceful shutdown
for i in {1..30}; do
    if ! ps -p "${PID}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Paper trading stopped gracefully${NC}"
        rm -f "${PID_FILE}"
        exit 0
    fi
    sleep 1
done

# Force kill if still running
echo -e "${RED}⚠️  Forcing shutdown...${NC}"
kill -9 "${PID}" 2>/dev/null

sleep 2

if ! ps -p "${PID}" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Paper trading stopped (forced)${NC}"
    rm -f "${PID_FILE}"
else
    echo -e "${RED}❌ Failed to stop process ${PID}${NC}"
    exit 1
fi
