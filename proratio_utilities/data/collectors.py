"""
CCXT-based data collectors for cryptocurrency exchanges.
Handles fetching OHLCV data from Binance (and other exchanges).
"""

import ccxt
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import time
from proratio_utilities.config.settings import get_settings


class BinanceCollector:
    """Binance data collector using CCXT"""

    def __init__(self, testnet: bool = False):
        """
        Initialize Binance collector.

        Args:
            testnet: If True, use Binance testnet (default: False, use mainnet)
        """
        self.settings = get_settings()
        self.testnet = testnet
        self.exchange = self._init_exchange()

    def _init_exchange(self) -> ccxt.binance:
        """Initialize CCXT Binance exchange object"""
        config = {
            "enableRateLimit": True,  # Respect rate limits
            "options": {
                "defaultType": "spot",  # 'spot', 'future', 'swap'
            },
        }

        # Only add API keys if they're configured (not needed for public data)
        # Check for non-empty strings and exclude placeholder values
        api_key = self.settings.binance_api_key
        api_secret = self.settings.binance_api_secret

        if (
            api_key
            and api_secret
            and api_key.strip()
            and api_secret.strip()
            and "your_" not in api_key.lower()  # Exclude placeholders
            and "here" not in api_key.lower()
        ):
            config["apiKey"] = api_key
            config["secret"] = api_secret

        if self.testnet:
            config["urls"] = {
                "api": {
                    "public": "https://testnet.binance.vision/api/v3",
                    "private": "https://testnet.binance.vision/api/v3",
                }
            }

        return ccxt.binance(config)

    def fetch_ohlcv(
        self,
        pair: str,
        timeframe: str = "1h",
        since: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Tuple]:
        """
        Fetch OHLCV data from Binance.

        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            since: Start datetime (default: None, fetches most recent)
            limit: Number of candles to fetch (default: 1000, max: 1000)

        Returns:
            List of tuples: (timestamp, open, high, low, close, volume)
        """
        # Convert datetime to milliseconds since epoch
        since_ms = None
        if since:
            since_ms = int(since.timestamp() * 1000)

        # Fetch OHLCV data
        ohlcv = self.exchange.fetch_ohlcv(
            symbol=pair, timeframe=timeframe, since=since_ms, limit=limit
        )

        # Convert to (timestamp, open, high, low, close, volume) tuples
        # CCXT returns: [timestamp_ms, open, high, low, close, volume]
        result = []
        for candle in ohlcv:
            timestamp = datetime.fromtimestamp(candle[0] / 1000)
            result.append(
                (
                    timestamp,
                    candle[1],  # open
                    candle[2],  # high
                    candle[3],  # low
                    candle[4],  # close
                    candle[5],  # volume
                )
            )

        return result

    def fetch_historical_data(
        self,
        pair: str,
        timeframe: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> List[Tuple]:
        """
        Fetch historical OHLCV data for a date range.
        Handles pagination automatically (Binance limit: 1000 candles per request).

        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe ('1h', '4h', '1d')
            start_date: Start datetime
            end_date: End datetime (default: now)

        Returns:
            List of tuples: (timestamp, open, high, low, close, volume)
        """
        if end_date is None:
            end_date = datetime.now()

        all_data = []
        current_date = start_date
        limit = 1000  # Binance max

        # Calculate timeframe duration in seconds
        timeframe_duration = self._parse_timeframe_to_seconds(timeframe)

        print(f"Fetching {pair} {timeframe} data from {start_date} to {end_date}...")

        while current_date < end_date:
            # Fetch batch
            batch = self.fetch_ohlcv(
                pair=pair, timeframe=timeframe, since=current_date, limit=limit
            )

            if not batch:
                break

            all_data.extend(batch)

            # Move to next batch (last timestamp + 1 candle)
            last_timestamp = batch[-1][0]
            current_date = last_timestamp + timedelta(seconds=timeframe_duration)

            # Rate limiting: sleep to avoid hitting limits
            time.sleep(0.2)  # 200ms delay between requests

            print(f"  Fetched {len(batch)} candles, last: {last_timestamp}")

        print(f"Total fetched: {len(all_data)} candles")
        return all_data

    def _parse_timeframe_to_seconds(self, timeframe: str) -> int:
        """
        Convert timeframe string to seconds.

        Args:
            timeframe: Timeframe string (e.g., '1m', '1h', '1d')

        Returns:
            Seconds as integer
        """
        unit = timeframe[-1]
        amount = int(timeframe[:-1])

        multipliers = {
            "m": 60,  # minutes
            "h": 3600,  # hours
            "d": 86400,  # days
            "w": 604800,  # weeks
        }

        return amount * multipliers.get(unit, 3600)

    def get_exchange_info(self) -> dict:
        """Get exchange information (markets, limits, etc.)"""
        return self.exchange.load_markets()

    def get_supported_pairs(self) -> List[str]:
        """Get list of supported trading pairs"""
        markets = self.get_exchange_info()
        return list(markets.keys())

    def test_connection(self) -> bool:
        """
        Test connection to Binance.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.exchange.fetch_ticker("BTC/USDT")
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


class MultiExchangeCollector:
    """
    Collector that can fetch data from multiple exchanges.
    (Future extension - placeholder for now)
    """

    def __init__(self):
        self.collectors = {
            "binance": BinanceCollector(),
        }

    def fetch_ohlcv(
        self,
        exchange: str,
        pair: str,
        timeframe: str = "1h",
        since: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Tuple]:
        """
        Fetch OHLCV from specified exchange.

        Args:
            exchange: Exchange name ('binance', etc.)
            pair: Trading pair
            timeframe: Timeframe
            since: Start datetime
            limit: Max candles

        Returns:
            List of tuples: (timestamp, open, high, low, close, volume)
        """
        collector = self.collectors.get(exchange.lower())
        if not collector:
            raise ValueError(f"Exchange '{exchange}' not supported")

        return collector.fetch_ohlcv(pair, timeframe, since, limit)
