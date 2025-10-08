#!/usr/bin/env python3
"""
Export OHLCV data from PostgreSQL to Freqtrade's JSON format.
Freqtrade expects data in user_data/data/{exchange}/ directory.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from proratio_utilities.data.storage import DatabaseStorage


def export_to_freqtrade_json(
    storage: DatabaseStorage,
    exchange: str,
    pair: str,
    timeframe: str,
    output_dir: Path,
    start_date=None,
    end_date=None
):
    """
    Export OHLCV data to Freqtrade JSON format.

    Args:
        storage: DatabaseStorage instance
        exchange: Exchange name (e.g., 'binance')
        pair: Trading pair (e.g., 'BTC/USDT')
        timeframe: Timeframe (e.g., '1h')
        output_dir: Output directory path
        start_date: Optional start date filter
        end_date: Optional end date filter
    """
    print(f"Exporting {pair} {timeframe} data...")

    # Get ALL data from database (no limit)
    df = storage.get_ohlcv(
        exchange=exchange,
        pair=pair,
        timeframe=timeframe,
        start_time=start_date,
        end_time=end_date,
        limit=None  # Get ALL records
    )

    if df.empty:
        print(f"  No data found for {pair} {timeframe}")
        return

    # Prepare DataFrame for Freqtrade feather format
    # Freqtrade expects columns: date, open, high, low, close, volume
    df_export = df.rename(columns={'timestamp': 'date'})
    df_export = df_export[['date', 'open', 'high', 'low', 'close', 'volume']]

    # Ensure date is datetime64[ms] (Freqtrade requirement)
    df_export['date'] = df_export['date'].astype('datetime64[ms]')

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Freqtrade filename format: {pair}-{timeframe}.feather
    # Replace / with _ for filesystem compatibility
    pair_filename = pair.replace('/', '_')
    output_file = output_dir / f"{pair_filename}-{timeframe}.feather"

    # Write feather format (Freqtrade's default)
    df_export.reset_index(drop=True).to_feather(output_file)

    print(f"  ✓ Exported {len(df_export)} candles to {output_file}")


def main():
    """Export all data to Freqtrade format"""

    # Configuration
    EXCHANGE = 'binance'
    PAIRS = ['BTC/USDT', 'ETH/USDT']
    TIMEFRAMES = ['1h', '4h', '1d']

    # Output directory (Freqtrade's data directory)
    output_dir = Path('user_data/data') / EXCHANGE
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*70)
    print("EXPORTING DATA TO FREQTRADE FORMAT")
    print("="*70 + "\n")
    print(f"Exchange: {EXCHANGE}")
    print(f"Pairs: {', '.join(PAIRS)}")
    print(f"Timeframes: {', '.join(TIMEFRAMES)}")
    print(f"Output: {output_dir}/\n")
    print("="*70 + "\n")

    # Initialize storage
    storage = DatabaseStorage()

    # Export all combinations
    for pair in PAIRS:
        for timeframe in TIMEFRAMES:
            export_to_freqtrade_json(
                storage=storage,
                exchange=EXCHANGE,
                pair=pair,
                timeframe=timeframe,
                output_dir=output_dir
            )

    storage.close()

    print("\n" + "="*70)
    print("✓ EXPORT COMPLETE!")
    print("="*70)
    print(f"\nData available in: {output_dir}/")
    print("\nYou can now run backtests with:")
    print("  freqtrade backtesting --strategy SimpleTestStrategy --timeframe 1h")
    print("\n")


if __name__ == '__main__':
    main()
