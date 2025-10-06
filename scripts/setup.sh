#!/usr/bin/env bash

# Proratio Setup Script
# This script initializes the development environment

set -e  # Exit on error

echo "🚀 Proratio Setup Script"
echo "================================"
echo ""

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
    echo "❌ Error: Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "✅ Docker installed"
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
pip install --upgrade pip > /dev/null 2>&1
echo "✅ Pip upgraded"
echo ""

# Install dependencies
echo "📥 Installing Python dependencies..."
echo "   (This may take a few minutes...)"
pip install -r requirements.txt > /dev/null 2>&1
echo "✅ Dependencies installed"
echo ""

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

# Check if Freqtrade is installed
echo "📋 Checking Freqtrade installation..."
if ! command -v freqtrade &> /dev/null; then
    echo "⚠️  Freqtrade not found in PATH. Installing..."
    pip install freqtrade > /dev/null 2>&1
    echo "✅ Freqtrade installed"
else
    echo "✅ Freqtrade already installed"
fi
echo ""

# Create Freqtrade user directory structure
echo "📁 Setting up Freqtrade user data..."
if [ ! -f "user_data/config.json" ]; then
    freqtrade create-userdir --userdir user_data
    echo "✅ Freqtrade user directory created"
else
    echo "⚠️  Freqtrade user directory already exists"
fi
echo ""

# Create initial test directories
echo "📁 Creating additional directories..."
mkdir -p user_data/data
mkdir -p user_data/logs
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
echo "   - Binance API (testnet recommended for development)"
echo "   - OpenAI API (ChatGPT)"
echo "   - Anthropic API (Claude)"
echo "   - Google API (Gemini)"
echo ""
echo "2. Configure Freqtrade:"
echo "   cp proratio_core/config/freqtrade/config_dry.json user_data/config.json"
echo ""
echo "3. Download historical data:"
echo "   freqtrade download-data \\"
echo "     --exchange binance \\"
echo "     --pairs BTC/USDT ETH/USDT \\"
echo "     --timeframe 4h 1h \\"
echo "     --days 180 \\"
echo "     --userdir user_data"
echo ""
echo "4. Check infrastructure status:"
echo "   docker-compose ps"
echo ""
echo "5. Start development:"
echo "   source venv/bin/activate  # Activate virtual environment"
echo "   jupyter lab               # For research"
echo "   streamlit run proratio_tradehub/dashboard/app.py  # For dashboard"
echo ""
echo "📚 Documentation:"
echo "   - README.md: Project overview"
echo "   - CLAUDE.md: Developer guide"
echo "   - PLAN.md: Implementation roadmap"
echo ""
echo "⚠️  IMPORTANT SECURITY REMINDERS:"
echo "   - Never commit .env file to git"
echo "   - Use testnet API keys for development"
echo "   - Never enable withdrawal permissions on API keys"
echo "   - Enable 2FA on your exchange account"
echo ""
echo "Happy trading! 🚀"
