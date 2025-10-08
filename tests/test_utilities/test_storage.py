"""
Tests for database storage module.
"""

import pytest
from datetime import datetime
from proratio_utilities.data.storage import DatabaseStorage


class TestDatabaseStorage:
    """Tests for DatabaseStorage"""

    @pytest.fixture
    def storage(self):
        """Fixture to provide DatabaseStorage instance"""
        return DatabaseStorage()

    def test_connection(self, storage):
        """Test database connection"""
        conn = storage.get_connection()
        assert conn is not None
        assert not conn.closed

    def test_insert_and_query_ohlcv(self, storage):
        """Test inserting and querying OHLCV data"""
        # Test data
        test_data = [
            (datetime(2024, 1, 1, 0, 0), 42000, 42500, 41800, 42200, 100.5),
            (datetime(2024, 1, 1, 1, 0), 42200, 42800, 42100, 42600, 150.2),
        ]

        # Insert
        inserted = storage.insert_ohlcv(
            exchange='binance',
            pair='BTC/USDT',
            timeframe='1h',
            data=test_data
        )
        assert inserted >= 0  # May be 0 if duplicates

        # Query
        df = storage.get_ohlcv(
            exchange='binance',
            pair='BTC/USDT',
            timeframe='1h',
            start_time=datetime(2024, 1, 1),
            limit=10
        )

        assert not df.empty
        assert 'timestamp' in df.columns
        assert 'close' in df.columns

    def test_latest_timestamp(self, storage):
        """Test getting latest timestamp"""
        latest = storage.get_latest_timestamp(
            exchange='binance',
            pair='BTC/USDT',
            timeframe='1h'
        )
        # Should return datetime or None
        assert latest is None or isinstance(latest, datetime)

    def test_count_records(self, storage):
        """Test counting records"""
        count = storage.count_ohlcv_records(
            exchange='binance',
            pair='BTC/USDT',
            timeframe='1h'
        )
        assert isinstance(count, int)
        assert count >= 0

    def test_metadata(self, storage):
        """Test metadata operations"""
        # Update
        storage.update_metadata('test_key', {'status': 'testing'})

        # Get
        value = storage.get_metadata('test_key')
        assert value is not None
        assert value['status'] == 'testing'

    def test_context_manager(self):
        """Test context manager protocol"""
        with DatabaseStorage() as storage:
            assert storage is not None
            conn = storage.get_connection()
            assert not conn.closed

        # Connection should be closed after context
        assert conn.closed
