#!/usr/bin/env bash

# Proratio Setup Script
# Comprehensive setup with multiple options and clear progress feedback

set -e  # Exit on error

echo "🚀 Proratio Setup Script"
echo "================================"
echo ""

# Parse command line arguments
USE_UV=false
SKIP_DEPS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --uv)
            USE_UV=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --help)
            echo "Usage: ./scripts/setup.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --uv          Use UV package manager (faster, recommended)"
            echo "  --skip-deps   Skip dependency installation (use if already installed)"
            echo "  --help        Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version detected"
echo ""

# Check Docker
echo "📋 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker CLI is not installed."
    echo ""
    echo "Please install Docker:"
    echo "  Option 1: Docker Desktop (recommended)"
    echo "    brew install --cask docker"
    echo ""
    echo "  Option 2: Colima (lightweight)"
    echo "    brew install colima && colima start"
    echo ""
    exit 1
fi

# Check if Docker daemon is running
echo "   Checking Docker daemon..."
if ! docker info &> /dev/null; then
    echo "❌ Error: Docker daemon is not running."
    echo ""
    echo "Docker CLI is installed, but the daemon is not running."
    echo ""
    echo "If you have Docker Desktop:"
    echo "  → Open Docker Desktop application"
    echo ""
    echo "If you have Colima:"
    echo "  → Run: colima start"
    echo ""
    exit 1
fi

echo "✅ Docker installed and running"
echo ""

# Setup based on package manager choice
if [ "$USE_UV" = true ]; then
    echo "🔧 Using UV package manager"
    echo ""

    # Install UV if not already installed
    echo "📦 Checking UV package manager..."
    if ! command -v uv &> /dev/null; then
        echo "Installing UV..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
        echo "✅ UV installed"
    else
        echo "✅ UV already installed ($(uv --version))"
    fi
    echo ""

    # Install Python 3.12 with UV (if not already installed)
    echo "📦 Setting up Python 3.12 with UV..."
    if ! uv python list 2>/dev/null | grep -q "3.12"; then
        echo "Installing Python 3.12..."
        uv python install 3.12
        echo "✅ Python 3.12 installed"
    else
        echo "✅ Python 3.12 already available"
    fi

    # Pin Python version for this project
    uv python pin 3.12
    echo "✅ Python version pinned to 3.12"
    echo ""

    # Install dependencies using UV
    if [ "$SKIP_DEPS" = false ]; then
        echo "📥 Installing dependencies with UV..."
        echo "   (First run may take 5-10 minutes...)"
        uv sync
        echo "✅ Dependencies installed"
    else
        echo "⏭️  Skipping dependency installation (--skip-deps)"
    fi
    echo ""

else
    echo "🔧 Using pip/venv package manager"
    echo ""

    # Create virtual environment
    echo "📦 Creating Python virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Virtual environment created"
    else
        echo "⚠️  Virtual environment already exists"
    fi
    echo ""

    # Activate virtual environment
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
    echo ""

    # Upgrade pip
    echo "⬆️  Upgrading pip..."
    pip install --upgrade pip --quiet
    echo "✅ Pip upgraded"
    echo ""

    # Install dependencies
    if [ "$SKIP_DEPS" = false ]; then
        echo "📥 Installing Python dependencies..."
        echo "   (First run may take 5-10 minutes...)"
        echo ""

        echo "Stage 1/4: Core packages (pandas, numpy, scikit-learn)..."
        pip install --quiet pandas numpy scipy scikit-learn
        echo "✅ Core packages installed"

        echo ""
        echo "Stage 2/4: Exchange & AI (ccxt, openai, anthropic, gemini)..."
        pip install --quiet ccxt freqtrade openai anthropic google-generativeai
        echo "✅ Exchange & AI packages installed"

        echo ""
        echo "Stage 3/4: ML & Deep Learning (torch, lightgbm, xgboost)..."
        pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu
        pip install --quiet lightgbm xgboost catboost tensorboard optuna
        echo "✅ ML packages installed"

        echo ""
        echo "Stage 4/4: Visualization & Tools (streamlit, jupyter, pytest)..."
        pip install --quiet plotly matplotlib seaborn streamlit jupyter jupyterlab
        pip install --quiet sqlalchemy psycopg2-binary redis
        pip install --quiet pytest pytest-cov pytest-asyncio ruff mypy
        pip install --quiet python-dotenv pydantic pydantic-settings rich
        echo "✅ Visualization & tools installed"

        echo ""
        echo "✅ All dependencies installed"
    else
        echo "⏭️  Skipping dependency installation (--skip-deps)"
    fi
    echo ""
fi

# Create .env file if it doesn't exist
echo "🔧 Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ .env file created from template"
    echo "⚠️  IMPORTANT: Edit .env and add your API keys!"
else
    echo "⚠️  .env file already exists (not overwriting)"
fi
echo ""

# Start infrastructure services
echo "🐳 Starting infrastructure services (PostgreSQL, Redis)..."
docker-compose up -d postgres redis
echo "⏳ Waiting for services to be ready..."
sleep 5
echo "✅ Infrastructure services started"
echo ""

# Create directories
echo "📁 Creating project directories..."
mkdir -p user_data/data
mkdir -p user_data/logs
mkdir -p tests/validation_results
mkdir -p proratio_quantlab/research/notebooks
mkdir -p proratio_quantlab/research/experiments
echo "✅ Directories created"
echo ""

# Summary
echo "================================"
echo "✅ Setup Complete!"
echo "================================"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Edit .env file with your API keys:"
echo "   nano .env  # or use your favorite editor"
echo ""
echo "   Required API keys:"
echo "   - BINANCE_API_KEY / BINANCE_API_SECRET (get from https://testnet.binance.vision/)"
echo "   - OPENAI_API_KEY (get from https://platform.openai.com/)"
echo "   - ANTHROPIC_API_KEY (get from https://console.anthropic.com/)"
echo "   - GEMINI_API_KEY (get from https://aistudio.google.com/)"
echo ""
echo "2. Initialize database:"
echo "   docker exec -i proratio_postgres psql -U proratio -d proratio < proratio_utilities/data/schema.sql"
echo ""
echo "3. Download historical data:"
if [ "$USE_UV" = true ]; then
    echo "   uv run python scripts/download_historical_data.py"
else
    echo "   source venv/bin/activate"
    echo "   python scripts/download_historical_data.py"
fi
echo ""
echo "4. Launch the system:"
echo "   ./start.sh cli"
echo ""
echo "📚 Documentation:"
echo "   - docs/getting_started.md: Complete setup guide"
echo "   - README.md: Project overview"
echo "   - docs/guides/validation_framework_guide.md: Strategy testing"
echo ""
echo "⚠️  IMPORTANT SECURITY REMINDERS:"
echo "   - Never commit .env file to git"
echo "   - Use testnet API keys (BINANCE_TESTNET=true)"
echo "   - Never enable withdrawal permissions on API keys"
echo "   - Keep TRADING_MODE=dry_run for testing"
echo ""
if [ "$USE_UV" = true ]; then
    echo "💡 UV Tips:"
    echo "   - Always use 'uv run python script.py' to run scripts"
    echo "   - Use 'uv add package' to add new dependencies"
    echo "   - Use 'uv sync' to sync dependencies"
else
    echo "💡 Virtual Environment Tips:"
    echo "   - Activate: source venv/bin/activate"
    echo "   - Deactivate: deactivate"
    echo "   - Run tests: pytest"
fi
echo ""
echo "Happy trading! 🚀"
