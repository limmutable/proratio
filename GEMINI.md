# Project Overview

This project, "Proratio," is an AI-driven cryptocurrency trading system. It leverages multiple LLMs (ChatGPT, Claude, Gemini) to generate trading signals and automates execution on the Binance exchange. The system is designed for low-frequency, high-conviction trading and includes features for backtesting, risk management, and a real-time monitoring dashboard.

The architecture is modular, consisting of four main components:
- **Proratio Utilities:** Handles exchange connectivity, data collection, and order execution using Freqtrade.
- **Proratio Signals:** Generates trading signals using AI/LLM analysis.
- **Proratio QuantLab:** Provides tools for backtesting strategies and developing machine learning models.
- **Proratio TradeHub:** Orchestrates trading strategies and includes a Streamlit-based dashboard for monitoring.

The project is built with Python and utilizes a PostgreSQL database for data storage and Redis for caching.

# Building and Running

## 1. Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Binance account (testnet recommended for development)
- API keys for OpenAI, Anthropic, and Google

## 2. Setup

The project includes a setup script that automates the environment configuration.

```bash
# Make the script executable
chmod +x scripts/setup.sh

# Run the setup script
./scripts/setup.sh
```

This script will:
- Create a Python virtual environment.
- Install the required dependencies from `requirements.txt`.
- Create a `.env` file from the `.env.example` template.
- Start the PostgreSQL and Redis services using Docker Compose.

## 3. Configuration

After running the setup script, you need to edit the `.env` file to add your API keys for Binance and the various AI/LLM services.

## 4. Running the System

### Paper Trading

To start the trading bot in paper trading mode, use the following command:

```bash
freqtrade trade \
  --strategy ProRatioAdapter \
  --userdir user_data \
  --config proratio_utilities/config/freqtrade/config_dry.json
```

### Dashboard

To launch the monitoring dashboard:

```bash
streamlit run proratio_tradehub/dashboard/app.py
```

The dashboard will be available at `http://localhost:8501`.

## 5. Testing

The project uses `pytest` for testing. To run the test suite:

```bash
pytest
```

# Development Conventions

- **Configuration:** The project uses a central `settings.py` file with Pydantic for managing configuration, which is loaded from a `.env` file.
- **Dependencies:** Python dependencies are managed in the `requirements.txt` file.
- **Infrastructure:** The project's infrastructure (database, cache) is managed with Docker Compose.
- **Code Style:** The `requirements.txt` file includes `black` for code formatting and `flake8` for linting, suggesting a standardized code style.
- **Testing:** The presence of a `tests` directory and `pytest` in the dependencies indicates a convention of writing unit tests for the codebase.
