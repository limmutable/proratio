"""
Database storage layer for Proratio Core.
Handles all database operations for OHLCV data, signals, and trades.
"""

import psycopg2
from psycopg2.extras import execute_batch
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pandas as pd
from proratio_core.config.settings import get_settings


class DatabaseStorage:
    """Database storage manager for Proratio"""

    def __init__(self):
        self.settings = get_settings()
        self._conn = None

    def get_connection(self):
        """Get or create database connection"""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self.settings.database_url)
        return self._conn

    def close(self):
        """Close database connection"""
        if self._conn and not self._conn.closed:
            self._conn.close()

    # ========================================================================
    # OHLCV Data Operations
    # ========================================================================

    def insert_ohlcv(
        self,
        exchange: str,
        pair: str,
        timeframe: str,
        data: List[Tuple]
    ) -> int:
        """
        Insert OHLCV data into database.

        Args:
            exchange: Exchange name (e.g., 'binance')
            pair: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '1h', '4h')
            data: List of tuples (timestamp, open, high, low, close, volume)

        Returns:
            Number of rows inserted
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO ohlcv (exchange, pair, timeframe, timestamp, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (exchange, pair, timeframe, timestamp) DO NOTHING
        """

        # Prepare data with exchange, pair, and timeframe
        rows = [
            (exchange, pair, timeframe, *row)
            for row in data
        ]

        execute_batch(cursor, query, rows, page_size=1000)
        conn.commit()
        inserted = cursor.rowcount
        cursor.close()

        return inserted

    def get_ohlcv(
        self,
        exchange: str,
        pair: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = 1000
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from database.

        Args:
            exchange: Exchange name
            pair: Trading pair
            timeframe: Timeframe
            start_time: Start timestamp (optional)
            end_time: End timestamp (optional)
            limit: Maximum rows to return (None = all records)

        Returns:
            DataFrame with OHLCV data
        """
        conn = self.get_connection()

        query = """
            SELECT timestamp, open, high, low, close, volume
            FROM ohlcv
            WHERE exchange = %s AND pair = %s AND timeframe = %s
        """
        params = [exchange, pair, timeframe]

        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)

        query += " ORDER BY timestamp ASC"

        # Only add limit if specified
        if limit is not None:
            query += " LIMIT %s"
            params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)

        # Convert timestamp to datetime if not already
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df

    def get_latest_timestamp(
        self,
        exchange: str,
        pair: str,
        timeframe: str
    ) -> Optional[datetime]:
        """Get the latest timestamp for a given pair/timeframe"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT MAX(timestamp)
            FROM ohlcv
            WHERE exchange = %s AND pair = %s AND timeframe = %s
        """

        cursor.execute(query, (exchange, pair, timeframe))
        result = cursor.fetchone()
        cursor.close()

        return result[0] if result[0] else None

    def count_ohlcv_records(
        self,
        exchange: str,
        pair: str,
        timeframe: str
    ) -> int:
        """Count total OHLCV records for a pair/timeframe"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT COUNT(*)
            FROM ohlcv
            WHERE exchange = %s AND pair = %s AND timeframe = %s
        """

        cursor.execute(query, (exchange, pair, timeframe))
        count = cursor.fetchone()[0]
        cursor.close()

        return count

    # ========================================================================
    # System Metadata Operations
    # ========================================================================

    def update_metadata(self, key: str, value: Dict) -> None:
        """Update system metadata"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO system_metadata (key, value, updated_at)
            VALUES (%s, %s::jsonb, CURRENT_TIMESTAMP)
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
        """

        import json
        cursor.execute(query, (key, json.dumps(value)))
        conn.commit()
        cursor.close()

    def get_metadata(self, key: str) -> Optional[Dict]:
        """Get system metadata"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT value FROM system_metadata WHERE key = %s"
        cursor.execute(query, (key,))
        result = cursor.fetchone()
        cursor.close()

        return result[0] if result else None

    # ========================================================================
    # Context Manager Support
    # ========================================================================

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
