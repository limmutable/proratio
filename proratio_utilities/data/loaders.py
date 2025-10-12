"""
Data loader for downloading and storing historical market data.
Coordinates between collectors (CCXT) and storage (PostgreSQL).
"""

from typing import List, Optional
from datetime import datetime, timedelta
from proratio_utilities.data.collectors import BinanceCollector
from proratio_utilities.data.storage import DatabaseStorage


class DataLoader:
    """
    Orchestrates downloading historical data and storing it in the database.
    """

    def __init__(self, testnet: bool = False):
        """
        Initialize data loader.

        Args:
            testnet: If True, use Binance testnet
        """
        self.collector = BinanceCollector(testnet=testnet)
        self.storage = DatabaseStorage()

    def download_and_store(
        self,
        pair: str,
        timeframe: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        exchange: str = "binance",
    ) -> int:
        """
        Download historical data and store in database.

        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '1h', '4h', '1d')
            start_date: Start date for historical data
            end_date: End date (default: now)
            exchange: Exchange name (default: 'binance')

        Returns:
            Number of records inserted
        """
        print(f"\n{'=' * 60}")
        print(f"Downloading {exchange.upper()} {pair} {timeframe} data")
        print(f"From: {start_date}")
        print(f"To: {end_date or 'now'}")
        print(f"{'=' * 60}\n")

        # Fetch data
        data = self.collector.fetch_historical_data(
            pair=pair, timeframe=timeframe, start_date=start_date, end_date=end_date
        )

        if not data:
            print("No data fetched!")
            return 0

        # Store in database
        print(f"\nStoring {len(data)} records in database...")
        inserted = self.storage.insert_ohlcv(
            exchange=exchange, pair=pair, timeframe=timeframe, data=data
        )

        print(f"✓ Inserted {inserted} new records (duplicates skipped)")
        return inserted

    def download_multiple_pairs(
        self,
        pairs: List[str],
        timeframes: List[str],
        start_date: datetime,
        end_date: Optional[datetime] = None,
        exchange: str = "binance",
    ) -> dict:
        """
        Download data for multiple pairs and timeframes.

        Args:
            pairs: List of trading pairs
            timeframes: List of timeframes
            start_date: Start date
            end_date: End date (default: now)
            exchange: Exchange name

        Returns:
            Dictionary with results per pair/timeframe
        """
        results = {}

        for pair in pairs:
            for timeframe in timeframes:
                key = f"{pair}_{timeframe}"
                try:
                    inserted = self.download_and_store(
                        pair=pair,
                        timeframe=timeframe,
                        start_date=start_date,
                        end_date=end_date,
                        exchange=exchange,
                    )
                    results[key] = {"success": True, "inserted": inserted}
                except Exception as e:
                    print(f"✗ Error downloading {key}: {e}")
                    results[key] = {"success": False, "error": str(e)}

        return results

    def get_data_status(self, exchange: str, pair: str, timeframe: str) -> dict:
        """
        Get status of stored data for a pair/timeframe.

        Args:
            exchange: Exchange name
            pair: Trading pair
            timeframe: Timeframe

        Returns:
            Dictionary with data statistics
        """
        count = self.storage.count_ohlcv_records(exchange, pair, timeframe)
        latest = self.storage.get_latest_timestamp(exchange, pair, timeframe)

        return {
            "exchange": exchange,
            "pair": pair,
            "timeframe": timeframe,
            "total_records": count,
            "latest_timestamp": latest,
            "data_available": count > 0,
        }

    def update_recent_data(
        self, pair: str, timeframe: str, exchange: str = "binance"
    ) -> int:
        """
        Update with most recent data (from last stored timestamp to now).

        Args:
            pair: Trading pair
            timeframe: Timeframe
            exchange: Exchange name

        Returns:
            Number of new records inserted
        """
        # Get latest timestamp in database
        latest = self.storage.get_latest_timestamp(exchange, pair, timeframe)

        if latest is None:
            print(
                f"No existing data for {pair} {timeframe}. Use download_and_store() first."
            )
            return 0

        # Download from last timestamp to now
        start_date = latest + timedelta(seconds=1)  # Start after last record
        print(f"Updating {pair} {timeframe} from {start_date} to now...")

        return self.download_and_store(
            pair=pair,
            timeframe=timeframe,
            start_date=start_date,
            end_date=None,
            exchange=exchange,
        )

    def close(self):
        """Close database connection"""
        self.storage.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
