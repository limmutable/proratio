#!/bin/bash
# Clear Freqtrade Backtest Cache
# This removes all cached backtest results to force fresh runs

echo "🗑️  Clearing Freqtrade backtest cache..."

# Remove backtest result files
rm -f user_data/backtest_results/*.zip 2>/dev/null
rm -f user_data/backtest_results/*.json 2>/dev/null
rm -f user_data/backtest_results/*.meta.json 2>/dev/null

# Remove indicator cache (if exists)
rm -f user_data/data/.cache/* 2>/dev/null

# Remove Python bytecode cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null

echo "✅ Cache cleared!"
echo ""
echo "Files removed:"
echo "  - Backtest results (*.zip, *.json)"
echo "  - Indicator cache"
echo "  - Python bytecode (*.pyc, __pycache__)"
echo ""
echo "Ready for fresh backtest run."
