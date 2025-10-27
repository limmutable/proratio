#!/bin/bash
# Run ML-Only Backtest for HybridMLLLMStrategy
# This script clears cache and runs a backtest focusing on ML predictions

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 ML-Only Backtest Runner${NC}"
echo "================================"
echo ""

# Step 1: Clear cache
echo -e "${YELLOW}Step 1/3: Clearing cache...${NC}"
./scripts/clear_backtest_cache.sh
echo ""

# Step 2: Verify model exists
echo -e "${YELLOW}Step 2/3: Checking ensemble model...${NC}"
if [ -f "models/ensemble_model.pkl" ]; then
    echo -e "${GREEN}✅ Ensemble model found${NC}"
    ls -lh models/ensemble_model.pkl
else
    echo -e "${RED}❌ Ensemble model not found!${NC}"
    echo "Please train the model first:"
    echo "  ./venv/bin/python scripts/train_ensemble_model.py --pair BTC/USDT --timeframe 4h --ensemble-method stacking --save models/ensemble_model.pkl"
    exit 1
fi
echo ""

# Step 3: Run backtest
echo -e "${YELLOW}Step 3/3: Running backtest...${NC}"
echo ""
echo "Strategy: HybridMLLLMStrategy"
echo "Pair: BTC/USDT"
echo "Timeframe: 4h"
echo "Date Range: 2024-01-01 to 2025-10-14"
echo ""
echo -e "${YELLOW}Note: LLM calls will fail (expected), ML predictions will work${NC}"
echo ""
echo "Starting in 3 seconds..."
sleep 3

# Run backtest
python -c "
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from proratio_utilities.config.loader import load_and_hydrate_config
config = load_and_hydrate_config('proratio_utilities/config/freqtrade/config_dry.json')
print(json.dumps(config))
" | ./venv/bin/freqtrade backtesting \
  --strategy HybridMLLLMStrategy \
  --timeframe 4h \
  --pairs BTC/USDT \
  --timerange 20240101-20251014 \
  --config - \
  --userdir user_data

echo ""
echo -e "${GREEN}✅ Backtest complete!${NC}"
echo ""
echo "Results location: user_data/backtest_results/"
