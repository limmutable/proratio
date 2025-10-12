#!/usr/bin/env python3
"""
Diagnostic script to analyze mean reversion strategy opportunities in backtest period.
"""

import pandas as pd
from datetime import datetime
from proratio_utilities.data.storage import DatabaseStorage


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_bollinger_bands(series: pd.Series, period: int = 20, std: float = 2.0):
    """Calculate Bollinger Bands."""
    sma = series.rolling(window=period).mean()
    std_dev = series.rolling(window=period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    return lower, sma, upper


def main():
    storage = DatabaseStorage()

    # Load data for backtest period
    start_date = datetime(2025, 4, 1)
    end_date = datetime(2025, 10, 8)

    pairs = ["BTC/USDT", "ETH/USDT"]

    for pair in pairs:
        print(f"\n{'=' * 80}")
        print(f"Analyzing {pair}")
        print(f"{'=' * 80}")

        # Fetch data
        df = storage.get_ohlcv(
            exchange="binance",
            pair=pair,
            timeframe="4h",
            start_time=start_date,
            end_time=end_date,
            limit=None,  # Get all records
        )

        if df.empty:
            print(f"❌ No data found for {pair}")
            continue

        print(
            f"✅ Loaded {len(df)} candles from {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}"
        )

        # Calculate indicators
        df["rsi"] = calculate_rsi(df["close"], period=14)
        df["bb_lower"], df["bb_middle"], df["bb_upper"] = calculate_bollinger_bands(
            df["close"], period=20, std=2.0
        )

        # Remove NaN rows (first 20 rows for BB calculation)
        df = df.dropna()

        print("\n📊 Indicator Statistics:")
        print(
            f"   RSI: min={df['rsi'].min():.2f}, max={df['rsi'].max():.2f}, mean={df['rsi'].mean():.2f}"
        )
        print(
            f"   Price vs BB: min={(df['close'] - df['bb_lower']).min():.2f}, max={(df['close'] - df['bb_upper']).max():.2f}"
        )

        # Check for LONG opportunities (RSI < 30 AND price < BB_lower)
        long_conditions = (df["rsi"] < 30) & (df["close"] < df["bb_lower"])
        long_opportunities = df[long_conditions]

        print("\n🔍 LONG Entry Opportunities (RSI < 30 AND price < BB_lower):")
        print(f"   Count: {len(long_opportunities)}")

        if len(long_opportunities) > 0:
            print("\n   Sample opportunities:")
            for idx, row in long_opportunities.head(5).iterrows():
                print(
                    f"   - {idx}: RSI={row['rsi']:.2f}, Price={row['close']:.2f}, BB_lower={row['bb_lower']:.2f}"
                )

        # Check for SHORT opportunities (RSI > 70 AND price > BB_upper)
        short_conditions = (df["rsi"] > 70) & (df["close"] > df["bb_upper"])
        short_opportunities = df[short_conditions]

        print("\n🔍 SHORT Entry Opportunities (RSI > 70 AND price > BB_upper):")
        print(f"   Count: {len(short_opportunities)}")

        if len(short_opportunities) > 0:
            print("\n   Sample opportunities:")
            for idx, row in short_opportunities.head(5).iterrows():
                print(
                    f"   - {idx}: RSI={row['rsi']:.2f}, Price={row['close']:.2f}, BB_upper={row['bb_upper']:.2f}"
                )

        # Check for relaxed conditions (just RSI)
        print("\n🔍 Relaxed Conditions (RSI only):")
        rsi_oversold = df["rsi"] < 30
        rsi_overbought = df["rsi"] > 70
        print(f"   RSI < 30: {rsi_oversold.sum()} times")
        print(f"   RSI > 70: {rsi_overbought.sum()} times")

        # Check for relaxed BB conditions (just BB breach)
        below_bb = df["close"] < df["bb_lower"]
        above_bb = df["close"] > df["bb_upper"]
        print(f"   Price < BB_lower: {below_bb.sum()} times")
        print(f"   Price > BB_upper: {above_bb.sum()} times")

        # Show times when RSI was close to threshold
        near_oversold = (df["rsi"] < 35) & (df["rsi"] >= 30)
        near_overbought = (df["rsi"] > 65) & (df["rsi"] <= 70)
        print("\n📈 Near-threshold conditions:")
        print(f"   RSI 30-35: {near_oversold.sum()} times")
        print(f"   RSI 65-70: {near_overbought.sum()} times")


if __name__ == "__main__":
    main()
