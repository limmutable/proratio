#!/bin/bash
# Start Proratio Streamlit Dashboard
#
# This script starts the monitoring dashboard for the Proratio trading system.
# The dashboard provides real-time monitoring, AI signal visualization, and emergency controls.

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ${GREEN}Proratio Dashboard${BLUE} - AI-Driven Trading Monitor           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo

# Check if Streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo -e "${YELLOW}⚠️  Streamlit not found. Installing dependencies...${NC}"
    uv add streamlit plotly pandas
    echo -e "${GREEN}✅ Dependencies installed${NC}"
    echo
fi

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Check if Freqtrade is running
echo -e "${BLUE}🔍 Checking Freqtrade status...${NC}"
if curl -s http://127.0.0.1:8080/api/v1/ping &> /dev/null; then
    echo -e "${GREEN}✅ Freqtrade API detected at http://127.0.0.1:8080${NC}"
else
    echo -e "${YELLOW}⚠️  Freqtrade API not responding${NC}"
    echo -e "${YELLOW}   The dashboard will still load but won't show live data${NC}"
    echo -e "${YELLOW}   Start Freqtrade first: freqtrade trade --config ...${NC}"
fi
echo

# Display configuration
echo -e "${BLUE}📊 Dashboard Configuration:${NC}"
echo -e "   Freqtrade API: ${GREEN}http://127.0.0.1:8080${NC}"
echo -e "   Dashboard URL: ${GREEN}http://localhost:8501${NC}"
echo -e "   Database: ${GREEN}user_data/db/tradesv3.dryrun.sqlite${NC}"
echo -e "   Config: ${GREEN}proratio_utilities/config/trading_config.json${NC}"
echo

# Start the dashboard
echo -e "${BLUE}🚀 Starting dashboard...${NC}"
echo -e "${YELLOW}   Press Ctrl+C to stop${NC}"
echo

streamlit run proratio_tradehub/dashboard/app.py \
    --server.port 8501 \
    --server.address localhost \
    --browser.gatherUsageStats false
