#!/usr/bin/env python3
"""
LLM Confidence Distribution Analysis for Phase 4.7

This script analyzes historical LLM prediction confidence to understand:
1. What is the typical LLM confidence range?
2. Is the Phase 4.6 observation (59.2%) normal or anomalous?
3. How does LLM confidence compare to ML confidence?

Author: Proratio Team
Date: 2025-10-17
Phase: 4.7 - Confidence Calibration
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from proratio_signals.orchestrator import SignalOrchestrator


def analyze_confidence_distribution(confidences: List[float], label: str = "LLM"):
    """Analyze and display confidence distribution statistics"""

    if not confidences:
        print(f"\n❌ No {label} predictions to analyze")
        return None

    confidences_arr = np.array(confidences) * 100  # Convert to percentage

    print("\n" + "="*60)
    print(f"{label.upper()} CONFIDENCE DISTRIBUTION ANALYSIS")
    print("="*60)
    print(f"\nTotal Predictions: {len(confidences)}")

    print(f"\nConfidence Statistics:")
    print(f"  Mean:   {np.mean(confidences_arr):.2f}%")
    print(f"  Median: {np.median(confidences_arr):.2f}%")
    print(f"  Std:    {np.std(confidences_arr):.2f}%")
    print(f"  Min:    {np.min(confidences_arr):.2f}%")
    print(f"  Max:    {np.max(confidences_arr):.2f}%")

    print(f"\nPercentiles:")
    for p in [10, 25, 50, 75, 90, 95, 99]:
        print(f"  {p:2d}th: {np.percentile(confidences_arr, p):.2f}%")

    # Confidence distribution buckets
    print(f"\nConfidence Distribution:")
    buckets = [(0, 40), (40, 50), (50, 60), (60, 70), (70, 80), (80, 90), (90, 100)]
    for low, high in buckets:
        count = np.sum((confidences_arr >= low) & (confidences_arr < high))
        pct = count / len(confidences_arr) * 100
        print(f"  {low}-{high}%: {count:4d} ({pct:5.2f}%)")

    # High vs low confidence
    print(f"\nConfidence Levels:")
    high = np.sum(confidences_arr >= 60)
    med = np.sum((confidences_arr >= 50) & (confidences_arr < 60))
    low = np.sum(confidences_arr < 50)
    print(f"  High (≥60%): {high:4d} ({high/len(confidences_arr)*100:.2f}%)")
    print(f"  Med (50-60%): {med:4d} ({med/len(confidences_arr)*100:.2f}%)")
    print(f"  Low (<50%):  {low:4d} ({low/len(confidences_arr)*100:.2f}%)")

    return confidences_arr


def simulate_llm_predictions(
    pair: str = "BTC/USDT",
    timeframe: str = "4h",
    num_samples: int = 20,
    days_back: int = 180
) -> List[Dict]:
    """
    Generate LLM predictions on historical data points

    Note: Due to API costs, we sample historical data points rather than
    analyzing every candle. For production, you'd analyze logged predictions.

    Args:
        pair: Trading pair
        timeframe: Timeframe
        num_samples: Number of historical points to sample
        days_back: How far back to sample from

    Returns:
        List of prediction results
    """
    print(f"\n📊 Generating {num_samples} LLM predictions on historical data...")
    print(f"   Pair: {pair}")
    print(f"   Timeframe: {timeframe}")
    print(f"   Period: Last {days_back} days")
    print(f"\n⚠️  Note: This will make {num_samples} LLM API calls (costs may apply)")

    # Load historical data
    pair_filename = pair.replace("/", "_")
    data_file = project_root / f"user_data/data/binance/{pair_filename}-{timeframe}.feather"

    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return []

    df = pd.read_feather(data_file)
    if 'date' in df.columns:
        df.rename(columns={'date': 'timestamp'}, inplace=True)
    df.set_index('timestamp', inplace=True)

    # Filter to date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    df = df[df.index >= pd.Timestamp(start_date, tz='UTC')]

    if len(df) < num_samples:
        print(f"⚠️  Only {len(df)} candles available, reducing sample size")
        num_samples = len(df)

    # Sample evenly across the time period
    sample_indices = np.linspace(0, len(df)-1, num_samples, dtype=int)

    # Initialize orchestrator
    orchestrator = SignalOrchestrator()

    results = []
    for i, idx in enumerate(sample_indices, 1):
        timestamp = df.index[idx]
        print(f"\n[{i}/{num_samples}] Analyzing {timestamp}...")

        try:
            # Get OHLCV data up to this point
            ohlcv_data = df.iloc[:idx+1].tail(200)  # Last 200 candles

            # Generate LLM signal
            signal = orchestrator.generate_signal(
                pair=pair,
                ohlcv_data=ohlcv_data
            )

            results.append({
                'timestamp': str(timestamp),
                'direction': signal.direction,
                'confidence': signal.confidence,
                'reasoning': signal.combined_reasoning[:100] + "..." if len(signal.combined_reasoning) > 100 else signal.combined_reasoning,
                'provider_count': len(signal.provider_signals),
            })

            print(f"   Direction: {signal.direction}")
            print(f"   Confidence: {signal.confidence:.2%}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            continue

    return results


def analyze_from_phase46_test():
    """Analyze LLM predictions from Phase 4.6 test log if available"""

    phase46_doc = project_root / "docs/project/phase46_llm_integration_test_20251016.md"

    if not phase46_doc.exists():
        return None

    print("\n📊 Analyzing Phase 4.6 test results...")

    # Read the document
    with open(phase46_doc) as f:
        content = f.read()

    # Extract LLM confidence (manually from the doc)
    # From Phase 4.6: LLM confidence was 59.2%

    print("\nPhase 4.6 LLM Observations:")
    print("  Single observation: 59.2% confidence")
    print("  Direction: SHORT")
    print("  All 3 providers (ChatGPT, Claude, Gemini) working")

    return [0.592]  # Single data point


def main():
    parser = argparse.ArgumentParser(description="Analyze LLM confidence distribution")
    parser.add_argument("--pair", default="BTC/USDT", help="Trading pair")
    parser.add_argument("--timeframe", default="4h", help="Timeframe")
    parser.add_argument("--samples", type=int, default=10, help="Number of historical samples to analyze")
    parser.add_argument("--days", type=int, default=180, help="Days of history to sample from")
    parser.add_argument("--skip-api", action="store_true", help="Skip API calls, only analyze Phase 4.6 data")

    args = parser.parse_args()

    print("="*60)
    print("LLM CONFIDENCE ANALYSIS - PHASE 4.7")
    print("="*60)

    # Analyze Phase 4.6 observation
    phase46_confidences = analyze_from_phase46_test()

    # Generate new predictions (if not skipping)
    llm_results = []
    if not args.skip_api:
        response = input(f"\n⚠️  Generate {args.samples} new LLM predictions? This will cost API credits. (y/n): ")
        if response.lower() == 'y':
            llm_results = simulate_llm_predictions(
                pair=args.pair,
                timeframe=args.timeframe,
                num_samples=args.samples,
                days_back=args.days
            )

            # Save results
            output_file = project_root / "data/output/llm_confidence_analysis.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(llm_results, f, indent=2)
            print(f"\n✅ Results saved to {output_file}")

    # Analyze distribution
    if llm_results:
        confidences = [r['confidence'] for r in llm_results]
        analyze_confidence_distribution(confidences, label="LLM (Historical)")

        # Compare with Phase 4.6
        print("\n" + "="*60)
        print("COMPARISON WITH PHASE 4.6")
        print("="*60)
        print(f"\nPhase 4.6 Observation: 59.2%")
        print(f"Historical Mean: {np.mean(confidences)*100:.2f}%")
        print(f"Historical Median: {np.median(np.array(confidences)*100):.2f}%")

        phase46_conf = 0.592
        historical_mean = np.mean(confidences)
        diff = abs(phase46_conf - historical_mean)

        if diff < 0.10:  # Within 10%
            print(f"\n✅ Phase 4.6 confidence ({phase46_conf:.1%}) is NORMAL")
            print(f"   Within expected range (±10% of mean)")
        else:
            print(f"\n⚠️  Phase 4.6 confidence ({phase46_conf:.1%}) is {diff:.1%} from mean")
            print(f"   May indicate unusual market conditions")

    elif phase46_confidences:
        print("\n📊 Only Phase 4.6 data available (1 observation)")
        print("   Generate more samples with --samples N to build distribution")

    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    print("\n1. 📊 To build robust LLM confidence distribution:")
    print(f"   python {Path(__file__).name} --samples 50 --days 180")
    print("\n2. 💰 To avoid API costs:")
    print("   - Analyze logged predictions from paper trading")
    print("   - Use Phase 4.6 as baseline (59.2% single observation)")
    print("\n3. 🎯 Current LLM threshold: 60%")
    print("   - Phase 4.6 observation (59.2%) just below threshold")
    print("   - This triggered WAIT, which may be correct behavior")

    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)


if __name__ == "__main__":
    main()
