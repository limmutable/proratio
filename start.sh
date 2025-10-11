#!/bin/bash
#
# Proratio System Startup Script
# Single entry point for initializing and starting the entire trading system
#
# Usage: ./start.sh [mode] [options]
# Modes:
#   cli              Launch CLI interface (recommended)
#   trade            Start trading system (default)
#
# Options:
#   --skip-checks    Skip system checks (faster startup)
#   --no-dashboard   Don't start the dashboard
#   --help           Show this help message
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKIP_CHECKS=false
NO_DASHBOARD=false
MODE="trade"  # Default mode

# Check if first argument is 'cli' mode - if so, skip to CLI immediately
if [ "$1" = "cli" ]; then
    MODE="cli"
else
    # Parse arguments for trade mode
    for arg in "$@"; do
        case $arg in
            trade)
                MODE="trade"
                ;;
            --skip-checks)
                SKIP_CHECKS=true
                ;;
            --no-dashboard)
                NO_DASHBOARD=true
                ;;
            --help)
                head -n 15 "$0" | tail -n 12
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $arg${NC}"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
fi

cd "$PROJECT_ROOT"

# ============================================================================
# CLI Mode: Launch CLI Interface
# ============================================================================

if [ "$MODE" = "cli" ]; then
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                  🤖 Proratio CLI Interface                     ║"
    echo "║              AI-Driven Cryptocurrency Trading                  ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    # Ensure virtual environment exists and is activated
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}⚠${NC} Creating virtual environment..."
        if command -v uv &> /dev/null; then
            uv venv
        else
            python3 -m venv .venv
        fi
    fi

    source .venv/bin/activate

    # Check if CLI dependencies are installed
    if ! python -c "import typer, rich" 2>/dev/null; then
        echo -e "${YELLOW}⚠${NC} Installing CLI dependencies..."
        if command -v uv &> /dev/null; then
            uv pip install typer rich shellingham
        else
            pip install typer rich shellingham
        fi
    fi

    # Launch CLI (filter out 'cli' argument)
    # Build args array excluding 'cli' mode argument
    CLI_ARGS=()
    for arg in "$@"; do
        if [ "$arg" != "cli" ]; then
            CLI_ARGS+=("$arg")
        fi
    done

    exec python -m proratio_cli.main "${CLI_ARGS[@]}"
fi

# ============================================================================
# Trade Mode: Start Full Trading System
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  🚀 Proratio Trading System                    ║"
echo "║              AI-Driven Cryptocurrency Trading                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# STEP 1: Environment Check
# ============================================================================

if [ "$SKIP_CHECKS" = false ]; then
    echo -e "${BLUE}[1/7] Checking environment...${NC}"

    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        echo -e "  ${GREEN}✓${NC} Python: $PYTHON_VERSION"
    else
        echo -e "  ${RED}✗${NC} Python 3 not found"
        exit 1
    fi

    # Check UV
    if command -v uv &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} UV package manager"
    else
        echo -e "  ${YELLOW}⚠${NC} UV not found (optional, will use pip)"
    fi

    # Check Docker
    if command -v docker &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Docker installed"
    else
        echo -e "  ${YELLOW}⚠${NC} Docker not found (required for PostgreSQL/Redis)"
    fi

    # Check .env file
    if [ -f ".env" ]; then
        echo -e "  ${GREEN}✓${NC} .env configuration file"
    else
        echo -e "  ${YELLOW}⚠${NC} .env file missing - creating from template"
        cp .env.example .env
        echo -e "  ${YELLOW}⚠${NC} Please edit .env with your API keys before continuing"
        exit 1
    fi

    echo ""
else
    echo -e "${BLUE}[1/7] Environment check skipped${NC}"
    echo ""
fi

# ============================================================================
# STEP 2: Dependencies Check
# ============================================================================

echo -e "${BLUE}[2/7] Checking dependencies...${NC}"

if [ ! -d ".venv" ]; then
    echo -e "  ${YELLOW}⚠${NC} Virtual environment not found - creating..."
    if command -v uv &> /dev/null; then
        uv venv
    else
        python3 -m venv .venv
    fi
fi

# Activate virtual environment
source .venv/bin/activate

# Check if requirements are installed
if ! python -c "import freqtrade" 2>/dev/null; then
    echo -e "  ${YELLOW}⚠${NC} Installing dependencies..."
    if command -v uv &> /dev/null; then
        uv pip install -r requirements.txt
    else
        pip install -r requirements.txt
    fi
    echo -e "  ${GREEN}✓${NC} Dependencies installed"
else
    echo -e "  ${GREEN}✓${NC} Dependencies already installed"
fi

echo ""

# ============================================================================
# STEP 3: Docker Services
# ============================================================================

echo -e "${BLUE}[3/7] Starting Docker services...${NC}"

if command -v docker &> /dev/null; then
    # Check if containers are running
    if docker ps | grep -q postgres && docker ps | grep -q redis; then
        echo -e "  ${GREEN}✓${NC} PostgreSQL and Redis already running"
    else
        echo -e "  ${YELLOW}⚠${NC} Starting PostgreSQL and Redis..."
        docker-compose up -d postgres redis
        sleep 3  # Wait for services to be ready
        echo -e "  ${GREEN}✓${NC} Services started"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Docker not available - skipping database services"
fi

echo ""

# ============================================================================
# STEP 4: System Status Check
# ============================================================================

echo -e "${BLUE}[4/7] Checking system status...${NC}"

# Load environment variables
set -a
source .env
set +a

# Check API keys
check_api_key() {
    local key_name=$1
    local key_value=$2
    local min_length=$3

    if [ -n "$key_value" ] && [ ${#key_value} -ge $min_length ]; then
        echo -e "  ${GREEN}✓${NC} $key_name configured"
        return 0
    else
        echo -e "  ${YELLOW}⚠${NC} $key_name not configured"
        return 1
    fi
}

check_api_key "Binance API" "$BINANCE_API_KEY" 20 || true
check_api_key "OpenAI API" "$OPENAI_API_KEY" 20 || true
check_api_key "Anthropic API" "$ANTHROPIC_API_KEY" 20 || true
check_api_key "Google Gemini API" "$GEMINI_API_KEY" 20 || true

echo ""

# ============================================================================
# STEP 5: Data Integrity Check
# ============================================================================

echo -e "${BLUE}[5/7] Checking data integrity...${NC}"

# Check user_data directory structure
mkdir -p user_data/{logs,data,db}

if [ -d "user_data/data" ]; then
    DATA_FILES=$(find user_data/data -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${GREEN}✓${NC} user_data directory structure"
    echo -e "  ${GREEN}✓${NC} Market data files: $DATA_FILES"
else
    echo -e "  ${YELLOW}⚠${NC} user_data directory created"
fi

# Check for trade database
if [ -f "user_data/db/tradesv3.dryrun.sqlite" ]; then
    DB_SIZE=$(du -h user_data/db/tradesv3.dryrun.sqlite | cut -f1)
    echo -e "  ${GREEN}✓${NC} Trade database exists ($DB_SIZE)"
else
    echo -e "  ${YELLOW}⚠${NC} Trade database will be created on first run"
fi

echo ""

# ============================================================================
# STEP 6: Start Freqtrade
# ============================================================================

echo -e "${BLUE}[6/7] Starting Freqtrade trading bot...${NC}"

# Check if Freqtrade is already running
if pgrep -f "freqtrade trade" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} Freqtrade already running"
    FT_PID=$(pgrep -f "freqtrade trade")
    echo -e "  ${BLUE}ℹ${NC} Process ID: $FT_PID"
else
    echo -e "  ${YELLOW}⚠${NC} Starting Freqtrade in dry-run mode..."

    # Start Freqtrade in background
    nohup uv run freqtrade trade \
        --strategy AIEnhancedStrategy \
        --config proratio_utilities/config/freqtrade/config_dry.json \
        --userdir user_data \
        --logfile user_data/logs/freqtrade.log \
        > user_data/logs/freqtrade_startup.log 2>&1 &

    FT_PID=$!
    sleep 5  # Wait for Freqtrade to initialize

    # Check if it started successfully
    if pgrep -f "freqtrade trade" > /dev/null; then
        echo -e "  ${GREEN}✓${NC} Freqtrade started (PID: $FT_PID)"
    else
        echo -e "  ${RED}✗${NC} Freqtrade failed to start"
        echo -e "  ${BLUE}ℹ${NC} Check logs: tail -f user_data/logs/freqtrade.log"
        exit 1
    fi
fi

echo ""

# ============================================================================
# STEP 7: Start Dashboard
# ============================================================================

if [ "$NO_DASHBOARD" = false ]; then
    echo -e "${BLUE}[7/7] Starting Streamlit dashboard...${NC}"

    # Check if dashboard is already running
    if pgrep -f "streamlit run" > /dev/null; then
        echo -e "  ${GREEN}✓${NC} Dashboard already running"
        DASHBOARD_PID=$(pgrep -f "streamlit run")
        echo -e "  ${BLUE}ℹ${NC} Process ID: $DASHBOARD_PID"
    else
        echo -e "  ${YELLOW}⚠${NC} Starting dashboard..."

        # Start Streamlit in background
        nohup streamlit run proratio_tradehub/dashboard/app.py \
            --server.headless true \
            --server.port 8501 \
            > user_data/logs/dashboard.log 2>&1 &

        DASHBOARD_PID=$!
        sleep 3  # Wait for Streamlit to start

        echo -e "  ${GREEN}✓${NC} Dashboard started (PID: $DASHBOARD_PID)"
    fi
else
    echo -e "${BLUE}[7/7] Dashboard startup skipped${NC}"
fi

echo ""

# ============================================================================
# System Ready
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  ✅ System Ready                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${GREEN}System Status:${NC}"
echo "  • Trading Mode: Dry-run (Paper Trading)"
echo "  • Strategy: AIEnhancedStrategy"
echo "  • Pairs: BTC/USDT, ETH/USDT"
echo ""

echo -e "${GREEN}Access Points:${NC}"
if [ "$NO_DASHBOARD" = false ]; then
    echo "  • Dashboard:      http://localhost:8501"
fi
echo "  • Freqtrade API:  http://localhost:8080"
echo "  • FreqUI:         http://localhost:8080 (if enabled)"
echo ""

echo -e "${GREEN}Logs & Monitoring:${NC}"
echo "  • Freqtrade logs: tail -f user_data/logs/freqtrade.log"
if [ "$NO_DASHBOARD" = false ]; then
    echo "  • Dashboard logs: tail -f user_data/logs/dashboard.log"
fi
echo "  • System status:  curl http://localhost:8080/api/v1/ping"
echo ""

echo -e "${GREEN}Useful Commands:${NC}"
echo "  • Stop Freqtrade: pkill -f 'freqtrade trade'"
if [ "$NO_DASHBOARD" = false ]; then
    echo "  • Stop Dashboard: pkill -f 'streamlit run'"
fi
echo "  • View trades:    freqtrade trade --userdir user_data"
echo "  • Check status:   freqtrade status --userdir user_data"
echo ""

echo -e "${YELLOW}Important Notes:${NC}"
echo "  ⚠ This is DRY-RUN mode - no real money will be used"
echo "  ⚠ Monitor the dashboard for system health and trading activity"
echo "  ⚠ Check logs regularly for errors or warnings"
echo ""

if [ "$NO_DASHBOARD" = false ]; then
    echo -e "${BLUE}Opening dashboard in 3 seconds...${NC}"
    sleep 3

    # Try to open browser
    if command -v open &> /dev/null; then
        open http://localhost:8501
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8501
    else
        echo -e "${YELLOW}Please open http://localhost:8501 in your browser${NC}"
    fi
fi

echo ""
echo -e "${GREEN}Happy Trading! 🚀${NC}"
echo ""
