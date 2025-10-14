#!/bin/bash
# Strategy Validation Framework
# Fast, comprehensive validation for any Freqtrade strategy
# Usage: ./scripts/validate_strategy.sh <StrategyName> [timerange]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STRATEGY=$1
TIMERANGE=${2:-"20240401-20241001"}  # Default: 6 months
CONFIG="proratio_utilities/config/freqtrade/config_accelerated_test.json"
USERDIR="user_data"
RESULTS_DIR="tests/validation_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Validation
if [ -z "$STRATEGY" ]; then
    echo -e "${RED}Error: Strategy name required${NC}"
    echo "Usage: $0 <StrategyName> [timerange]"
    echo "Example: $0 SimpleTestStrategy 20240401-20241001"
    exit 1
fi

# Create results directory
mkdir -p "$RESULTS_DIR"
REPORT_FILE="$RESULTS_DIR/${STRATEGY}_validation_${TIMESTAMP}.txt"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Strategy Validation Framework v1.0                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Strategy:${NC} $STRATEGY"
echo -e "${YELLOW}Timerange:${NC} $TIMERANGE"
echo -e "${YELLOW}Report:${NC} $REPORT_FILE"
echo ""

# Start report
{
    echo "========================================="
    echo "Strategy Validation Report"
    echo "========================================="
    echo "Strategy: $STRATEGY"
    echo "Timestamp: $(date)"
    echo "Timerange: $TIMERANGE"
    echo ""
} > "$REPORT_FILE"

# Step 1: Pre-flight checks
echo -e "${BLUE}[1/6]${NC} Running pre-flight checks..."
{
    echo "========================================="
    echo "Step 1: Pre-flight Checks"
    echo "========================================="
} >> "$REPORT_FILE"

# Check if strategy file exists
STRATEGY_FILE=$(find user_data/strategies -name "${STRATEGY}.py" 2>/dev/null | head -1)
if [ -z "$STRATEGY_FILE" ]; then
    echo -e "${RED}✗ Strategy file not found: ${STRATEGY}.py${NC}" | tee -a "$REPORT_FILE"
    exit 1
fi
echo -e "${GREEN}✓ Strategy file found: $STRATEGY_FILE${NC}" | tee -a "$REPORT_FILE"

# Check if data exists
if [ ! -d "$USERDIR/data/binance" ]; then
    echo -e "${RED}✗ Data directory not found${NC}" | tee -a "$REPORT_FILE"
    echo -e "${YELLOW}  Run: python scripts/export_data_for_freqtrade.py${NC}"
    exit 1
fi
DATA_FILES=$(ls $USERDIR/data/binance/*.feather 2>/dev/null | wc -l)
echo -e "${GREEN}✓ Found $DATA_FILES data files${NC}" | tee -a "$REPORT_FILE"

# Check if config exists
if [ ! -f "$CONFIG" ]; then
    echo -e "${YELLOW}⚠ Accelerated test config not found, using default dry-run config${NC}" | tee -a "$REPORT_FILE"
    CONFIG="proratio_utilities/config/freqtrade/config_dry.json"
fi
echo -e "${GREEN}✓ Config file: $CONFIG${NC}" | tee -a "$REPORT_FILE"

echo ""

# Step 2: Quick backtest
echo -e "${BLUE}[2/6]${NC} Running backtest (this may take 2-3 minutes)..."
{
    echo ""
    echo "========================================="
    echo "Step 2: Backtest Results"
    echo "========================================="
} >> "$REPORT_FILE"

BACKTEST_OUTPUT=$(mktemp)
if freqtrade backtesting \
    --strategy "$STRATEGY" \
    --timerange "$TIMERANGE" \
    --config "$CONFIG" \
    --userdir "$USERDIR" \
    --breakdown day \
    2>&1 | tee "$BACKTEST_OUTPUT"; then
    echo -e "${GREEN}✓ Backtest completed${NC}" | tee -a "$REPORT_FILE"

    # Extract key metrics from backtest output
    grep -A 30 "BACKTESTING REPORT" "$BACKTEST_OUTPUT" >> "$REPORT_FILE" || true
else
    echo -e "${RED}✗ Backtest failed${NC}" | tee -a "$REPORT_FILE"
    cat "$BACKTEST_OUTPUT" >> "$REPORT_FILE"
    rm "$BACKTEST_OUTPUT"
    exit 1
fi
rm "$BACKTEST_OUTPUT"

echo ""

# Step 3: Validate backtest results
echo -e "${BLUE}[3/6]${NC} Validating backtest results..."
{
    echo ""
    echo "========================================="
    echo "Step 3: Validation Checks"
    echo "========================================="
} >> "$REPORT_FILE"

if python scripts/validate_backtest_results.py --strategy "$STRATEGY" 2>&1 | tee -a "$REPORT_FILE"; then
    echo -e "${GREEN}✓ Validation checks passed${NC}" | tee -a "$REPORT_FILE"
else
    echo -e "${RED}✗ Validation checks failed${NC}" | tee -a "$REPORT_FILE"
    echo -e "${YELLOW}  See report for details: $REPORT_FILE${NC}"
    # Don't exit - continue with other tests
fi

echo ""

# Step 4: Run integration tests
echo -e "${BLUE}[4/6]${NC} Running integration tests..."
{
    echo ""
    echo "========================================="
    echo "Step 4: Integration Tests"
    echo "========================================="
} >> "$REPORT_FILE"

# Check if test file exists
TEST_FILE="tests/test_strategies/test_${STRATEGY}.py"
if [ -f "$TEST_FILE" ]; then
    if uv run pytest "$TEST_FILE" -v 2>&1 | tee -a "$REPORT_FILE"; then
        echo -e "${GREEN}✓ Integration tests passed${NC}" | tee -a "$REPORT_FILE"
    else
        echo -e "${RED}✗ Integration tests failed${NC}" | tee -a "$REPORT_FILE"
    fi
else
    echo -e "${YELLOW}⚠ No integration tests found: $TEST_FILE${NC}" | tee -a "$REPORT_FILE"
    echo -e "${YELLOW}  Consider creating tests using: tests/test_strategies/test_strategy_template.py${NC}"
fi

echo ""

# Step 5: Check strategy code quality
echo -e "${BLUE}[5/6]${NC} Checking code quality..."
{
    echo ""
    echo "========================================="
    echo "Step 5: Code Quality"
    echo "========================================="
} >> "$REPORT_FILE"

# Run ruff check on strategy file
if uv run ruff check "$STRATEGY_FILE" 2>&1 | tee -a "$REPORT_FILE"; then
    echo -e "${GREEN}✓ No linting issues${NC}" | tee -a "$REPORT_FILE"
else
    echo -e "${YELLOW}⚠ Linting issues found (non-critical)${NC}" | tee -a "$REPORT_FILE"
fi

echo ""

# Step 6: Generate validation report
echo -e "${BLUE}[6/6]${NC} Generating validation report..."
{
    echo ""
    echo "========================================="
    echo "Step 6: Summary Report"
    echo "========================================="
} >> "$REPORT_FILE"

if python scripts/generate_validation_report.py --strategy "$STRATEGY" --report "$REPORT_FILE" 2>&1 | tee -a "$REPORT_FILE"; then
    echo -e "${GREEN}✓ Report generated${NC}"
else
    echo -e "${YELLOW}⚠ Could not generate summary report${NC}"
fi

echo ""

# Final summary
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Validation Complete                                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Validation report saved to: $REPORT_FILE${NC}"
echo ""
echo "Next steps:"
echo "  1. Review the validation report"
echo "  2. Address any failures or warnings"
echo "  3. If passed, strategy is ready for paper trading"
echo ""
echo "To view report:"
echo "  cat $REPORT_FILE"
echo ""
