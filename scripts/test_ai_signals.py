#!/usr/bin/env python3
"""
Test AI Signal Generation

Tests the multi-AI orchestrator with real market data.
Verifies that ChatGPT, Claude, and Gemini can generate consensus signals.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from proratio_signals import SignalOrchestrator
from proratio_core.data.storage import DatabaseStorage
from proratio_core.config.settings import get_settings
import pandas as pd


def test_ai_providers():
    """Test connection to all AI providers"""
    print("=" * 70)
    print("  Testing AI Provider Connections")
    print("=" * 70)
    print()

    settings = get_settings()

    # Check API keys
    providers_status = {
        'ChatGPT (OpenAI)': bool(settings.openai_api_key and settings.openai_api_key.startswith('sk-')),
        'Claude (Anthropic)': bool(settings.anthropic_api_key and settings.anthropic_api_key.startswith('sk-ant-')),
        'Gemini (Google)': bool(settings.gemini_api_key and len(settings.gemini_api_key) > 20),
    }

    for provider, has_key in providers_status.items():
        status = "✓ API key configured" if has_key else "✗ API key missing"
        print(f"{provider:25} {status}")

    print()

    if not any(providers_status.values()):
        print("❌ No AI providers configured!")
        print("   Please add API keys to .env file:")
        print("   - OPENAI_API_KEY=sk-...")
        print("   - ANTHROPIC_API_KEY=sk-ant-...")
        print("   - GEMINI_API_KEY=...")
        return False

    # Initialize orchestrator
    try:
        orchestrator = SignalOrchestrator()
        print(f"✓ Orchestrator initialized with {len(orchestrator.providers)} provider(s)")
        print()

        # Test connections
        print("Testing provider connections...")
        results = orchestrator.test_providers()

        for provider, success in results.items():
            status = "✓ Connected" if success else "✗ Connection failed"
            print(f"  {provider:15} {status}")

        print()
        return any(results.values())

    except Exception as e:
        print(f"❌ Orchestrator initialization failed: {e}")
        return False


def test_signal_generation():
    """Test signal generation with real market data"""
    print("=" * 70)
    print("  Testing AI Signal Generation")
    print("=" * 70)
    print()

    # Load market data from database
    storage = DatabaseStorage()

    pair = "BTC/USDT"
    timeframe = "1h"

    print(f"Loading market data for {pair} ({timeframe})...")
    df = storage.get_ohlcv(
        exchange="binance",
        pair=pair,
        timeframe=timeframe,
        limit=100  # Last 100 candles
    )

    if df.empty:
        print(f"❌ No data found for {pair} {timeframe}")
        print("   Run: python scripts/download_historical_data.py")
        return False

    print(f"✓ Loaded {len(df)} candles")
    print(f"  Latest price: ${df['close'].iloc[-1]:,.2f}")
    print(f"  Time range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
    print()

    # Calculate indicators (simple example)
    df['ema_20'] = df['close'].ewm(span=20).mean()
    df['ema_50'] = df['close'].ewm(span=50).mean()
    df['rsi'] = calculate_rsi(df['close'], 14)

    indicators = {
        'EMA_20': df['ema_20'].iloc[-1],
        'EMA_50': df['ema_50'].iloc[-1],
        'RSI': df['rsi'].iloc[-1],
        'Volume_MA': df['volume'].tail(20).mean()
    }

    print("Technical Indicators:")
    for key, value in indicators.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value:.2f}")
    print()

    # Generate AI signal
    print("Generating AI consensus signal...")
    print("(This may take 10-30 seconds...)")
    print()

    try:
        orchestrator = SignalOrchestrator()

        signal = orchestrator.generate_signal(
            pair=pair,
            timeframe=timeframe,
            ohlcv_data=df,
            indicators=indicators
        )

        # Display results
        print("=" * 70)
        print("  AI CONSENSUS SIGNAL")
        print("=" * 70)
        print()
        print(f"Direction:       {signal.direction.upper()}")
        print(f"Confidence:      {signal.confidence:.2%}")
        print(f"Consensus Score: {signal.consensus_score:.2%}")
        print(f"Should Trade:    {'YES' if signal.should_trade() else 'NO'} (threshold: 60%)")
        print()

        # Provider status
        print("=" * 70)
        print("  PROVIDER STATUS")
        print("=" * 70)
        print()
        if signal.active_providers:
            print(f"✓ Active: {', '.join(signal.active_providers)} ({len(signal.active_providers)}/{len(signal.active_providers) + len(signal.failed_providers or [])})")
            for provider in signal.active_providers:
                model = signal.provider_models.get(provider, 'unknown')
                print(f"  → {provider}: {model}")
        if signal.failed_providers:
            print(f"✗ Failed: {', '.join(signal.failed_providers)}")
        print()

        print("=" * 70)
        print("  INDIVIDUAL ANALYSES")
        print("=" * 70)
        print()

        if signal.chatgpt_analysis:
            print(f"ChatGPT (40% weight):")
            print(f"  Direction: {signal.chatgpt_analysis.direction.upper()}")
            print(f"  Confidence: {signal.chatgpt_analysis.confidence:.2%}")
            summary = str(signal.chatgpt_analysis.technical_summary or "N/A")
            print(f"  Summary: {summary[:100]}...")
            print()

        if signal.claude_analysis:
            print(f"Claude (35% weight):")
            print(f"  Direction: {signal.claude_analysis.direction.upper()}")
            print(f"  Confidence: {signal.claude_analysis.confidence:.2%}")
            risk = str(signal.claude_analysis.risk_assessment or "N/A")
            print(f"  Risk: {risk[:100]}...")
            print()

        if signal.gemini_analysis:
            print(f"Gemini (25% weight):")
            print(f"  Direction: {signal.gemini_analysis.direction.upper()}")
            print(f"  Confidence: {signal.gemini_analysis.confidence:.2%}")
            print(f"  Sentiment: {signal.gemini_analysis.sentiment}")
            print()

        print("=" * 70)
        print("  COMBINED ANALYSIS")
        print("=" * 70)
        print()
        print("Technical Summary:")
        print(signal.technical_summary)
        print()
        print("Risk Summary:")
        print(signal.risk_summary)
        print()

        print("=" * 70)
        print("✓ AI signal generation test complete!")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"❌ Signal generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def calculate_rsi(series, period=14):
    """Calculate RSI indicator"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


if __name__ == "__main__":
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "Proratio AI Signal Test" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Test 1: Provider connections
    providers_ok = test_ai_providers()

    if not providers_ok:
        sys.exit(1)

    # Test 2: Signal generation
    signal_ok = test_signal_generation()

    if not signal_ok:
        sys.exit(1)

    print()
    print("🎉 All tests passed!")
    print()
