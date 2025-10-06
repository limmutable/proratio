#!/usr/bin/env python3
"""
Quick test script to verify the data pipeline works.
Downloads a small amount of recent data to test the full pipeline.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from proratio_core.data.loaders import DataLoader


def main():
    """Test the data pipeline with a small download"""

    print("\n" + "="*70)
    print("TESTING DATA PIPELINE")
    print("="*70 + "\n")

    # Initialize loader (no API keys needed for public data)
    loader = DataLoader(testnet=False)

    # Test connection
    print("1. Testing Binance connection...")
    if loader.collector.test_connection():
        print("   ✓ Connection successful\n")
    else:
        print("   ✗ Connection failed\n")
        return 1

    # Download small amount of recent data
    print("2. Downloading 100 candles of BTC/USDT 1h data...")
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=100)

    try:
        inserted = loader.download_and_store(
            pair='BTC/USDT',
            timeframe='1h',
            start_date=start_date,
            end_date=end_date,
            exchange='binance'
        )
        print(f"   ✓ Successfully inserted {inserted} records\n")
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return 1

    # Check data status
    print("3. Checking data status...")
    status = loader.get_data_status('binance', 'BTC/USDT', '1h')
    print(f"   Total records: {status['total_records']}")
    print(f"   Latest timestamp: {status['latest_timestamp']}")
    print(f"   Data available: {status['data_available']}\n")

    # Test update functionality
    print("4. Testing update (fetch new data since last timestamp)...")
    try:
        new_records = loader.update_recent_data(
            pair='BTC/USDT',
            timeframe='1h',
            exchange='binance'
        )
        print(f"   ✓ Updated with {new_records} new records\n")
    except Exception as e:
        print(f"   ✗ Error: {e}\n")

    loader.close()

    print("="*70)
    print("✓ DATA PIPELINE TEST COMPLETE!")
    print("="*70 + "\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
