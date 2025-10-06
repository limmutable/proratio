#!/bin/bash

# Proratio Paper Trading Launcher
# Checks prerequisites and starts paper trading with monitoring

set -e

echo "=============================================="
echo "  Proratio Paper Trading Launcher"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Docker containers
echo "Checking infrastructure..."
if ! docker-compose ps | grep -q "postgres.*Up"; then
    echo -e "${RED}✗ PostgreSQL not running${NC}"
    echo "  Starting Docker containers..."
    docker-compose up -d postgres redis
    sleep 3
else
    echo -e "${GREEN}✓ PostgreSQL running${NC}"
fi

if ! docker-compose ps | grep -q "redis.*Up"; then
    echo -e "${RED}✗ Redis not running${NC}"
    echo "  Starting Docker containers..."
    docker-compose up -d postgres redis
    sleep 3
else
    echo -e "${GREEN}✓ Redis running${NC}"
fi

# Check 2: Freqtrade data files
echo ""
echo "Checking market data..."
if [ ! -f "user_data/data/binance/BTC_USDT-1h.feather" ]; then
    echo -e "${RED}✗ Market data missing${NC}"
    echo "  Exporting from PostgreSQL..."
    python scripts/export_data_for_freqtrade.py
else
    echo -e "${GREEN}✓ Market data available${NC}"
    ls -lh user_data/data/binance/*.feather | wc -l | xargs echo "  Files:"
fi

# Check 3: Strategy exists
echo ""
echo "Checking strategy..."
if [ ! -f "user_data/strategies/SimpleTestStrategy.py" ]; then
    echo -e "${RED}✗ SimpleTestStrategy not found${NC}"
    exit 1
else
    echo -e "${GREEN}✓ SimpleTestStrategy ready${NC}"
fi

# Display configuration
echo ""
echo "=============================================="
echo "  Paper Trading Configuration"
echo "=============================================="
echo "Strategy: SimpleTestStrategy"
echo "Pairs: BTC/USDT, ETH/USDT"
echo "Timeframe: 1h"
echo "Virtual Wallet: \$10,000 USDT"
echo "Stake per trade: \$100 USDT"
echo "Max open trades: 2"
echo ""
echo "FreqUI Dashboard: http://localhost:8080"
echo "  Username: freqtrader"
echo "  Password: change_this_password"
echo ""
echo "=============================================="
echo ""

# Ask for confirmation
read -p "Start paper trading? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Start paper trading
echo ""
echo -e "${GREEN}Starting paper trading...${NC}"
echo "Press Ctrl+C to stop"
echo ""
echo "=============================================="
echo ""

# Run Freqtrade
freqtrade trade \
  --strategy SimpleTestStrategy \
  --config proratio_core/config/freqtrade/config_dry.json \
  --userdir user_data

# On exit
echo ""
echo "=============================================="
echo "Paper trading stopped."
echo ""
echo "View results:"
echo "  freqtrade profit --config proratio_core/config/freqtrade/config_dry.json --userdir user_data"
echo "  freqtrade performance --config proratio_core/config/freqtrade/config_dry.json --userdir user_data"
echo "=============================================="
