#!/usr/bin/env python3
"""
Confidence Threshold Optimization for Phase 4.7

This script optimizes the confidence thresholds for ML and LLM predictions
to maximize trading performance (Sharpe ratio, win rate, profitability).

Uses grid search to find optimal thresholds for:
- min_ml_confidence: Minimum ML confidence to consider signal
- min_llm_confidence: Minimum LLM confidence to consider signal
- min_agreement_for_trade: Minimum agreement between ML and LLM to trade

Author: Proratio Team
Date: 2025-10-17
Phase: 4.7 - Confidence Calibration
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_historical_data(pair: str, timeframe: str, days: int = 180) -> pd.DataFrame:
    """Load historical OHLCV data"""
    pair_filename = pair.replace("/", "_")
    data_file = project_root / f"user_data/data/binance/{pair_filename}-{timeframe}.feather"

    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")

    df = pd.read_feather(data_file)
    if 'date' in df.columns:
        df.rename(columns={'date': 'timestamp'}, inplace=True)
    df.set_index('timestamp', inplace=True)

    # Filter to date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    df = df[df.index >= pd.Timestamp(start_date, tz='UTC')]

    return df


def simulate_trading_with_thresholds(
    df: pd.DataFrame,
    ml_confidences: np.ndarray,
    ml_directions: np.ndarray,
    ml_threshold: float,
    llm_threshold: float,
    agreement_threshold: float,
    llm_confidence_mean: float = 0.60,  # Assumed LLM baseline from Phase 4.6
) -> Dict:
    """
    Simulate trading performance with given thresholds

    Args:
        df: OHLCV dataframe
        ml_confidences: ML confidence scores (0-1)
        ml_directions: ML directions (1 = UP, -1 = DOWN)
        ml_threshold: Minimum ML confidence
        llm_threshold: Minimum LLM confidence
        agreement_threshold: Minimum agreement for trade
        llm_confidence_mean: Assumed LLM confidence (since we don't have historical LLM data)

    Returns:
        Performance metrics dictionary
    """

    # Simulate LLM always at baseline confidence for this analysis
    # In production, you'd use actual LLM predictions
    llm_confidences = np.full(len(ml_confidences), llm_confidence_mean)

    # Calculate returns
    returns = df['close'].pct_change().values[1:]  # Shift by 1 to align with predictions

    # Align arrays
    min_len = min(len(ml_confidences), len(returns))
    ml_confidences = ml_confidences[:min_len]
    ml_directions = ml_directions[:min_len]
    llm_confidences = llm_confidences[:min_len]
    returns = returns[:min_len]

    # Apply thresholds
    ml_pass = ml_confidences >= ml_threshold
    llm_pass = llm_confidences >= llm_threshold

    # Simplified agreement: both pass their thresholds
    # In production, calculate actual directional agreement
    agreement = (ml_pass & llm_pass).astype(float)
    agreement_pass = agreement >= agreement_threshold

    # Generate signals (only trade when all thresholds pass)
    signals = agreement_pass.astype(int) * ml_directions

    # Calculate trading returns
    trade_returns = signals * returns
    winning_trades = np.sum(trade_returns > 0)
    losing_trades = np.sum(trade_returns < 0)
    total_trades = winning_trades + losing_trades

    if total_trades == 0:
        return {
            'total_trades': 0,
            'win_rate': 0.0,
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
        }

    # Calculate metrics
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    total_return = np.sum(trade_returns) * 100  # Percentage
    sharpe_ratio = np.mean(trade_returns) / (np.std(trade_returns) + 1e-10) * np.sqrt(252)  # Annualized

    # Drawdown
    cumulative = np.cumsum(trade_returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = running_max - cumulative
    max_drawdown = np.max(drawdown) * 100 if len(drawdown) > 0 else 0

    # Win/Loss stats
    wins = trade_returns[trade_returns > 0]
    losses = trade_returns[trade_returns < 0]
    avg_win = np.mean(wins) * 100 if len(wins) > 0 else 0
    avg_loss = np.mean(losses) * 100 if len(losses) > 0 else 0

    return {
        'total_trades': int(total_trades),
        'win_rate': float(win_rate),
        'total_return': float(total_return),
        'sharpe_ratio': float(sharpe_ratio),
        'max_drawdown': float(max_drawdown),
        'avg_win': float(avg_win),
        'avg_loss': float(avg_loss),
    }


def grid_search_thresholds(
    df: pd.DataFrame,
    ml_confidences: np.ndarray,
    ml_directions: np.ndarray,
) -> List[Dict]:
    """
    Grid search for optimal threshold combinations

    Args:
        df: OHLCV dataframe
        ml_confidences: ML confidence scores
        ml_directions: ML direction predictions

    Returns:
        List of results sorted by Sharpe ratio
    """

    print("\n📊 Running grid search for optimal thresholds...")

    # Define grid
    ml_thresholds = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
    llm_thresholds = [0.50, 0.55, 0.60, 0.65, 0.70]
    agreement_thresholds = [0.50, 0.60, 0.70, 0.80, 0.90]

    results = []
    total_combinations = len(ml_thresholds) * len(llm_thresholds) * len(agreement_thresholds)
    count = 0

    for ml_thresh in ml_thresholds:
        for llm_thresh in llm_thresholds:
            for agree_thresh in agreement_thresholds:
                count += 1
                print(f"  [{count}/{total_combinations}] Testing ML={ml_thresh:.0%}, LLM={llm_thresh:.0%}, Agreement={agree_thresh:.0%}", end='\r')

                metrics = simulate_trading_with_thresholds(
                    df, ml_confidences, ml_directions,
                    ml_thresh, llm_thresh, agree_thresh
                )

                results.append({
                    'ml_threshold': ml_thresh,
                    'llm_threshold': llm_thresh,
                    'agreement_threshold': agree_thresh,
                    **metrics
                })

    print("\n✅ Grid search complete")

    # Sort by Sharpe ratio (descending)
    results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)

    return results


def main():
    parser = argparse.ArgumentParser(description="Optimize confidence thresholds")
    parser.add_argument("--pair", default="BTC/USDT", help="Trading pair")
    parser.add_argument("--timeframe", default="4h", help="Timeframe")
    parser.add_argument("--days", type=int, default=180, help="Days of history")
    parser.add_argument("--output", default="data/output/threshold_optimization.json", help="Output file")

    args = parser.parse_args()

    print("="*60)
    print("CONFIDENCE THRESHOLD OPTIMIZATION - PHASE 4.7")
    print("="*60)
    print(f"\nPair: {args.pair}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Period: Last {args.days} days")

    # Load historical data
    print(f"\n📊 Loading historical data...")
    df = load_historical_data(args.pair, args.timeframe, args.days)
    print(f"✅ Loaded {len(df)} candles from {df.index[0]} to {df.index[-1]}")

    # Load ML model and generate predictions
    print(f"\n📊 Loading ML ensemble model...")
    from proratio_quantlab.ml.ensemble_predictor import EnsemblePredictor
    from proratio_quantlab.ml.feature_engineering import FeatureEngineer

    ensemble = EnsemblePredictor()
    ensemble.load("models/ensemble_model.pkl")

    print(f"📊 Engineering features...")
    fe = FeatureEngineer()
    df_features = fe.add_all_features(df.copy())
    df_clean = df_features.dropna()

    # Add missing features
    feature_columns = ensemble.feature_names
    for col in feature_columns:
        if col not in df_clean.columns:
            df_clean[col] = 0

    X = df_clean[feature_columns].values

    print(f"📊 Generating ML predictions...")
    raw_predictions = ensemble.predict(X)

    # Convert to confidence and direction
    ml_confidences = np.minimum(np.abs(raw_predictions) / 5.0, 1.0)
    ml_directions = np.sign(raw_predictions)

    print(f"✅ Generated {len(ml_confidences)} predictions")
    print(f"   Confidence range: {ml_confidences.min():.1%} to {ml_confidences.max():.1%}")

    # Run grid search
    results = grid_search_thresholds(df_clean, ml_confidences, ml_directions)

    # Display top 10 results
    print("\n" + "="*60)
    print("TOP 10 THRESHOLD COMBINATIONS (by Sharpe Ratio)")
    print("="*60)
    print(f"\n{'Rank':<5} {'ML':<6} {'LLM':<6} {'Agr':<6} {'Trades':<8} {'Win%':<7} {'Return%':<9} {'Sharpe':<8} {'MaxDD%':<8}")
    print("-" * 80)

    for i, r in enumerate(results[:10], 1):
        print(f"{i:<5} {r['ml_threshold']:.0%}  {r['llm_threshold']:.0%}  {r['agreement_threshold']:.0%}  "
              f"{r['total_trades']:<8} {r['win_rate']:.1%}  {r['total_return']:>7.2f}%  "
              f"{r['sharpe_ratio']:>6.2f}  {r['max_drawdown']:>6.2f}%")

    # Show current configuration
    print("\n" + "="*60)
    print("CURRENT CONFIGURATION")
    print("="*60)
    current = [r for r in results if r['ml_threshold'] == 0.60 and r['llm_threshold'] == 0.60 and r['agreement_threshold'] == 0.70]
    if current:
        c = current[0]
        rank = results.index(c) + 1
        print(f"\nRank: #{rank} out of {len(results)}")
        print(f"ML Threshold: {c['ml_threshold']:.0%}")
        print(f"LLM Threshold: {c['llm_threshold']:.0%}")
        print(f"Agreement Threshold: {c['agreement_threshold']:.0%}")
        print(f"Trades: {c['total_trades']}")
        print(f"Win Rate: {c['win_rate']:.1%}")
        print(f"Total Return: {c['total_return']:.2f}%")
        print(f"Sharpe Ratio: {c['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {c['max_drawdown']:.2f}%")

    # Recommendations
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)

    best = results[0]
    print(f"\n🏆 Best Configuration:")
    print(f"   ML Threshold: {best['ml_threshold']:.0%} (current: 60%)")
    print(f"   LLM Threshold: {best['llm_threshold']:.0%} (current: 60%)")
    print(f"   Agreement: {best['agreement_threshold']:.0%} (current: 70%)")
    print(f"\n   Expected Performance:")
    print(f"   - Sharpe Ratio: {best['sharpe_ratio']:.2f}")
    print(f"   - Win Rate: {best['win_rate']:.1%}")
    print(f"   - Total Return: {best['total_return']:.2f}%")
    print(f"   - Trades: {best['total_trades']}")

    # Save results
    output_path = project_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Full results saved to {output_path}")

    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)


if __name__ == "__main__":
    main()
