"""
System Checks for Proratio CLI

Performs startup validation checks for database, APIs, configuration, etc.

Author: Proratio Team
Date: 2025-10-11
"""

import os
from pathlib import Path
from typing import Dict, Tuple
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def check_environment() -> Tuple[bool, str]:
    """Check if .env file exists and has required variables."""
    env_path = Path(".env")
    if not env_path.exists():
        return False, ".env file not found"

    required_vars = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        return False, f"Missing: {', '.join(missing)}"

    return True, "All required variables present"


def check_database() -> Tuple[bool, str]:
    """Check if database is accessible."""
    try:
        # Check if PostgreSQL is running
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                "name=proratio_postgres",
                "--format",
                "{{.Status}}",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0 and "Up" in result.stdout:
            return True, "PostgreSQL running"
        else:
            return False, "PostgreSQL not running"

    except Exception as e:
        return False, str(e)


def check_redis() -> Tuple[bool, str]:
    """Check if Redis is accessible."""
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                "name=proratio_redis",
                "--format",
                "{{.Status}}",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0 and "Up" in result.stdout:
            return True, "Redis running"
        else:
            return False, "Redis not running"

    except Exception as e:
        return False, str(e)


def check_data_availability() -> Tuple[bool, str]:
    """Check if historical data is available."""
    data_path = Path("user_data/data")

    if not data_path.exists():
        return False, "Data directory not found"

    # Check for data files
    feather_files = list(data_path.glob("*.feather"))
    json_files = list(data_path.glob("*.json"))

    if feather_files or json_files:
        return True, f"{len(feather_files)} feather, {len(json_files)} json files"
    else:
        return False, "No data files found"


def check_strategies() -> Tuple[bool, str]:
    """Check if strategies are available."""
    strategy_path = Path("user_data/strategies")

    if not strategy_path.exists():
        return False, "Strategy directory not found"

    strategies = [
        f
        for f in strategy_path.glob("*.py")
        if not f.name.startswith("_") and f.name != "__init__.py"
    ]

    if strategies:
        return True, f"{len(strategies)} strategies found"
    else:
        return False, "No strategies found"


def check_ml_models() -> Tuple[bool, str]:
    """Check if ML models are available."""
    models_path = Path("models")

    if not models_path.exists():
        return False, "Models directory not found"

    model_files = list(models_path.glob("*.pkl")) + list(models_path.glob("*.h5"))

    if model_files:
        return True, f"{len(model_files)} models found"
    else:
        return False, "No trained models found"


def check_llm_providers() -> Dict[str, Tuple[bool, str]]:
    """Check LLM provider status."""
    providers = {}

    # OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "your-openai-api-key-here":
        providers["OpenAI"] = (True, "API key configured")
    else:
        providers["OpenAI"] = (False, "API key not configured")

    # Anthropic (Claude)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key and anthropic_key != "your-anthropic-api-key-here":
        providers["Anthropic"] = (True, "API key configured")
    else:
        providers["Anthropic"] = (False, "API key not configured")

    # Google (Gemini)
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and gemini_key != "your-gemini-api-key-here":
        providers["Gemini"] = (True, "API key configured")
    else:
        providers["Gemini"] = (False, "API key not configured")

    return providers


def check_binance_api() -> Tuple[bool, str]:
    """Check Binance API configuration."""
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or api_key == "your-binance-api-key-here":
        return False, "API key not configured"

    if not api_secret or api_secret == "your-binance-api-secret-here":
        return False, "API secret not configured"

    return True, "API credentials configured"


def check_freqtrade() -> Tuple[bool, str]:
    """Check if Freqtrade is installed."""
    try:
        result = subprocess.run(
            ["freqtrade", "--version"], capture_output=True, text=True, timeout=5
        )

        if result.returncode == 0:
            version = result.stdout.strip()
            return True, f"Installed: {version}"
        else:
            return False, "Not found"

    except FileNotFoundError:
        return False, "Not installed"
    except Exception as e:
        return False, str(e)


def check_config_file() -> Tuple[bool, str]:
    """Check if trading config exists."""
    config_path = Path("proratio_utilities/config/trading_config.json")

    if not config_path.exists():
        return False, "Config file not found"

    try:
        import json

        with open(config_path, "r") as f:
            config = json.load(f)

        if config:
            return True, f"{len(config)} sections configured"
        else:
            return False, "Config file is empty"

    except Exception as e:
        return False, f"Error reading config: {str(e)}"


def check_pytorch() -> Tuple[bool, str]:
    """Check if PyTorch is installed."""
    try:
        import torch

        version = torch.__version__
        cuda = "CUDA" if torch.cuda.is_available() else "CPU"
        return True, f"v{version} ({cuda})"
    except ImportError:
        return False, "Not installed"


def run_all_checks() -> Dict[str, Tuple[bool, str]]:
    """Run all system checks and return results."""
    checks = {
        "Environment": check_environment(),
        "Database": check_database(),
        "Redis": check_redis(),
        "Data": check_data_availability(),
        "Strategies": check_strategies(),
        "ML Models": check_ml_models(),
        "Config File": check_config_file(),
        "Freqtrade": check_freqtrade(),
        "PyTorch": check_pytorch(),
        "Binance API": check_binance_api(),
    }

    return checks


def get_llm_provider_status() -> Dict[str, Tuple[bool, str]]:
    """Get detailed LLM provider status."""
    return check_llm_providers()
