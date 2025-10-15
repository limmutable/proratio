#!/bin/bash
# Monitor ML Paper Trading in Real-Time

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

LOG_FILE="user_data/logs/paper_trading_ml_test.log"

if [ ! -f "${LOG_FILE}" ]; then
    echo "❌ Log file not found: ${LOG_FILE}"
    echo "Start paper trading first: ./scripts/start_ml_paper_trading.sh"
    exit 1
fi

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ML Paper Trading Monitor (Live)      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Monitoring: ${LOG_FILE}${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Follow log with highlighting
tail -f "${LOG_FILE}" | grep --line-buffered --color=always -E "ML Prediction|LLM Prediction|HYBRID SIGNAL|BUY|SELL|ENTRY|EXIT|ERROR|WARNING|✅|❌|⚠️|"
