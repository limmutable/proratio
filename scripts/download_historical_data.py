#!/usr/bin/env python3
"""
Script to download historical OHLCV data for backtesting.
Run this to populate the database with 24 months of historical data.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from proratio_core.data.loaders import DataLoader


def main():
    """Download historical data for primary trading pairs"""

    # Configuration
    PAIRS = ['BTC/USDT', 'ETH/USDT']
    TIMEFRAMES = ['1h', '4h', '1d']
    MONTHS_BACK = 24  # 24 months of data

    # Calculate start date
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 * MONTHS_BACK)

    print("\n" + "="*70)
    print("PRORATIO HISTORICAL DATA DOWNLOAD")
    print("="*70)
    print(f"\nPairs: {', '.join(PAIRS)}")
    print(f"Timeframes: {', '.join(TIMEFRAMES)}")
    print(f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Duration: {MONTHS_BACK} months")
    print("\n" + "="*70 + "\n")

    # Initialize loader
    loader = DataLoader(testnet=False)  # Use mainnet for historical data

    # Test connection first
    print("Testing Binance connection...")
    if not loader.collector.test_connection():
        print("✗ Failed to connect to Binance. Check your API keys in .env")
        return 1

    print("✓ Connection successful\n")

    # Download data for all pairs and timeframes
    results = loader.download_multiple_pairs(
        pairs=PAIRS,
        timeframes=TIMEFRAMES,
        start_date=start_date,
        end_date=end_date
    )

    # Print summary
    print("\n" + "="*70)
    print("DOWNLOAD SUMMARY")
    print("="*70 + "\n")

    for key, result in results.items():
        if result['success']:
            print(f"✓ {key:20s} - {result['inserted']:,} records inserted")
        else:
            print(f"✗ {key:20s} - ERROR: {result['error']}")

    # Print data status
    print("\n" + "="*70)
    print("DATA STATUS")
    print("="*70 + "\n")

    for pair in PAIRS:
        for timeframe in TIMEFRAMES:
            status = loader.get_data_status('binance', pair, timeframe)
            print(f"{pair} {timeframe:4s} - {status['total_records']:,} records, "
                  f"latest: {status['latest_timestamp']}")

    loader.close()
    print("\n✓ Download complete!\n")
    return 0


if __name__ == '__main__':
    sys.exit(main())
