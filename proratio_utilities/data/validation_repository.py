"""
Validation Repository Implementation

This module implements the ValidationRepository interface for storing and retrieving
backtest validation results using SQLAlchemy Core.

Feature: 001-test-validation-dashboard
Created: 2025-10-28

Constitutional Alignment:
- IV. Configuration as Code: Database credentials from .env via Pydantic Settings
- VII. Observability: Uses Python logging module (not print statements)
- VIII. Code Quality: Type hints on all methods, docstrings with Google style
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    DECIMAL,
    TIMESTAMP,
    MetaData,
    Table,
    create_engine,
    select,
    and_,
    desc,
    asc,
    func,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from dataclasses import dataclass

from proratio_utilities.config.settings import get_settings

# Setup logging
logger = logging.getLogger(__name__)


# Custom Exceptions
class DatabaseConnectionError(Exception):
    """Raised when database connection fails (e.g., credentials invalid, server unreachable)."""

    pass


class DatabaseWriteError(Exception):
    """Raised when database insert/update operation fails (e.g., constraint violation, disk full)."""

    pass


class DatabaseQueryError(Exception):
    """Raised when database query execution fails (e.g., syntax error, timeout)."""

    pass


@dataclass
class ValidationResult:
    """
    Data class representing a single backtest validation result.

    Attributes:
        id: Unique identifier for this validation run (assigned by database)
        strategy_name: Name of the strategy being validated
        timestamp: When the backtest validation completed (UTC)
        total_trades: Total number of trades executed during backtest
        win_rate: Percentage of winning trades (0.00 to 100.00), None if no trades
        total_profit_pct: Total profit/loss as percentage, can be negative
        max_drawdown: Maximum drawdown as percentage (negative value)
        sharpe_ratio: Risk-adjusted return measure
        profit_factor: Ratio of gross profit to gross loss (>1 is profitable)
        git_commit_hash: Git SHA-1 hash of code version, None if git unavailable
        created_at: When this record was inserted into database
    """

    id: int
    strategy_name: str
    timestamp: datetime
    total_trades: int
    win_rate: Optional[float]
    total_profit_pct: Optional[float]
    max_drawdown: Optional[float]
    sharpe_ratio: Optional[float]
    profit_factor: Optional[float]
    git_commit_hash: Optional[str]
    created_at: datetime


class ValidationRepository:
    """
    Repository for storing and retrieving backtest validation results.

    Uses SQLAlchemy Core (not ORM) with declarative table definitions and connection pooling.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the ValidationRepository.

        Args:
            database_url: Database connection string. If None, uses DATABASE_URL from settings.

        Raises:
            DatabaseConnectionError: If database connection cannot be established.
        """
        # Get database URL from settings or use provided URL
        if database_url is None:
            settings = get_settings()
            # Use validation_db_url if set, otherwise fall back to database_url
            database_url = settings.validation_db_url or settings.database_url

        self.database_url = database_url

        # Create SQLAlchemy engine with connection pooling
        try:
            self.engine: Engine = create_engine(
                database_url,
                pool_pre_ping=True,  # Verify connections before using
                pool_size=5,  # Connection pool size
                max_overflow=10,  # Additional connections beyond pool_size
                echo=False,  # Set to True for SQL debugging
            )
            logger.info("ValidationRepository initialized successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database engine: {e}")
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")

        # Define table schema
        self.metadata = MetaData()
        self.validation_results = Table(
            "validation_results",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("strategy_name", String(255), nullable=False),
            Column("timestamp", TIMESTAMP, nullable=False),
            Column("created_at", TIMESTAMP, nullable=False),
            Column("total_trades", Integer, nullable=False),
            Column("win_rate", DECIMAL(5, 2)),
            Column("total_profit_pct", DECIMAL(10, 4)),
            Column("max_drawdown", DECIMAL(10, 4)),
            Column("sharpe_ratio", DECIMAL(10, 4)),
            Column("profit_factor", DECIMAL(10, 4)),
            Column("git_commit_hash", String(40)),
        )

    def insert_validation_result(
        self,
        strategy_name: str,
        timestamp: datetime,
        total_trades: int,
        win_rate: Optional[float] = None,
        total_profit_pct: Optional[float] = None,
        max_drawdown: Optional[float] = None,
        sharpe_ratio: Optional[float] = None,
        profit_factor: Optional[float] = None,
        git_commit_hash: Optional[str] = None,
    ) -> int:
        """
        Insert a new validation result into the database.

        Args:
            strategy_name: Name of the strategy (e.g., "GridTrading")
            timestamp: When the backtest validation completed (UTC)
            total_trades: Total number of trades executed (must be >= 0)
            win_rate: Percentage of winning trades (0-100), None if no trades
            total_profit_pct: Total profit/loss as percentage, can be negative
            max_drawdown: Max drawdown as percentage (must be <= 0), None if no trades
            sharpe_ratio: Risk-adjusted return measure, None if no trades
            profit_factor: Gross profit / gross loss ratio (must be >= 0), None if no trades
            git_commit_hash: Git SHA-1 hash (40 hex chars), None if git unavailable

        Returns:
            int: Database ID of the inserted record

        Raises:
            ValueError: If validation rules are violated (e.g., negative win_rate,
                        future timestamp, invalid git hash format)
            DatabaseConnectionError: If database connection fails
            DatabaseWriteError: If insert operation fails
        """
        # Validation rules
        self._validate_insert_params(
            strategy_name,
            timestamp,
            total_trades,
            win_rate,
            max_drawdown,
            profit_factor,
            git_commit_hash,
        )

        # Prepare insert values
        insert_values = {
            "strategy_name": strategy_name,
            "timestamp": timestamp,
            "created_at": datetime.utcnow(),
            "total_trades": total_trades,
            "win_rate": win_rate,
            "total_profit_pct": total_profit_pct,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "profit_factor": profit_factor,
            "git_commit_hash": git_commit_hash,
        }

        # Insert into database
        try:
            with self.engine.begin() as conn:
                result = conn.execute(
                    self.validation_results.insert().values(**insert_values)
                )
                inserted_id = result.inserted_primary_key[0]
                logger.info(
                    f"Inserted validation result for {strategy_name} with ID {inserted_id}"
                )
                return inserted_id
        except SQLAlchemyError as e:
            logger.error(f"Failed to insert validation result: {e}")
            raise DatabaseWriteError(f"Failed to insert validation result: {e}")

    def query_validation_results(
        self,
        strategy_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        git_commit_hash: Optional[str] = None,
        limit: int = 100,
        order_by: str = "timestamp_desc",
    ) -> List[ValidationResult]:
        """
        Query validation results with optional filtering.

        Args:
            strategy_name: Filter by strategy name (exact match), None = all strategies
            start_date: Filter results >= this timestamp, None = no start limit
            end_date: Filter results <= this timestamp, None = no end limit
            git_commit_hash: Filter by git commit (exact match), None = all commits
            limit: Maximum number of results to return (default: 100, max: 1000)
            order_by: Sort order - one of:
                - "timestamp_desc" (default): Most recent first
                - "timestamp_asc": Oldest first
                - "strategy_name_asc": Alphabetical by strategy
                - "win_rate_desc": Highest win rate first
                - "total_profit_desc": Most profitable first

        Returns:
            List[ValidationResult]: List of validation results matching filters,
                                     ordered as specified. Empty list if no matches.

        Raises:
            ValueError: If invalid order_by or limit > 1000
            DatabaseConnectionError: If database connection fails
            DatabaseQueryError: If query execution fails
        """
        # Validation
        if limit > 1000:
            raise ValueError("Limit cannot exceed 1000")

        valid_order_by = [
            "timestamp_desc",
            "timestamp_asc",
            "strategy_name_asc",
            "win_rate_desc",
            "total_profit_desc",
        ]
        if order_by not in valid_order_by:
            raise ValueError(
                f"Invalid order_by '{order_by}'. Must be one of: {valid_order_by}"
            )

        # Build query
        query = select(self.validation_results)

        # Apply filters
        filters = []
        if strategy_name is not None:
            filters.append(self.validation_results.c.strategy_name == strategy_name)
        if start_date is not None:
            filters.append(self.validation_results.c.timestamp >= start_date)
        if end_date is not None:
            filters.append(self.validation_results.c.timestamp <= end_date)
        if git_commit_hash is not None:
            filters.append(self.validation_results.c.git_commit_hash == git_commit_hash)

        if filters:
            query = query.where(and_(*filters))

        # Apply ordering
        order_column = self._get_order_column(order_by)
        query = query.order_by(order_column).limit(limit)

        # Execute query
        try:
            with self.engine.connect() as conn:
                results = conn.execute(query).fetchall()
                logger.info(f"Query returned {len(results)} validation results")
                return [self._row_to_validation_result(row) for row in results]
        except SQLAlchemyError as e:
            logger.error(f"Failed to query validation results: {e}")
            raise DatabaseQueryError(f"Failed to query validation results: {e}")

    def get_latest_validation(self, strategy_name: str) -> Optional[ValidationResult]:
        """
        Get the most recent validation result for a specific strategy.

        Args:
            strategy_name: Name of the strategy (exact match)

        Returns:
            ValidationResult if found, None if strategy has no validation results

        Raises:
            DatabaseConnectionError: If database connection fails
            DatabaseQueryError: If query execution fails
        """
        results = self.query_validation_results(
            strategy_name=strategy_name, limit=1, order_by="timestamp_desc"
        )
        return results[0] if results else None

    def get_validation_by_id(self, validation_id: int) -> Optional[ValidationResult]:
        """
        Get a specific validation result by its database ID.

        Args:
            validation_id: Database ID of the validation result

        Returns:
            ValidationResult if found, None if ID doesn't exist

        Raises:
            DatabaseConnectionError: If database connection fails
            DatabaseQueryError: If query execution fails
        """
        query = select(self.validation_results).where(
            self.validation_results.c.id == validation_id
        )

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query).fetchone()
                if result:
                    logger.info(f"Found validation result with ID {validation_id}")
                    return self._row_to_validation_result(result)
                else:
                    logger.info(f"No validation result found with ID {validation_id}")
                    return None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get validation by ID: {e}")
            raise DatabaseQueryError(f"Failed to get validation by ID: {e}")

    def count_validations(
        self,
        strategy_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Count validation results matching the given filters.

        Args:
            strategy_name: Filter by strategy name, None = all strategies
            start_date: Filter results >= this timestamp, None = no start limit
            end_date: Filter results <= this timestamp, None = no end limit

        Returns:
            int: Number of validation results matching filters

        Raises:
            DatabaseConnectionError: If database connection fails
            DatabaseQueryError: If query execution fails
        """
        # Build query
        query = select(func.count()).select_from(self.validation_results)

        # Apply filters
        filters = []
        if strategy_name is not None:
            filters.append(self.validation_results.c.strategy_name == strategy_name)
        if start_date is not None:
            filters.append(self.validation_results.c.timestamp >= start_date)
        if end_date is not None:
            filters.append(self.validation_results.c.timestamp <= end_date)

        if filters:
            query = query.where(and_(*filters))

        # Execute query
        try:
            with self.engine.connect() as conn:
                count = conn.execute(query).scalar()
                logger.info(f"Count query returned {count} validation results")
                return count
        except SQLAlchemyError as e:
            logger.error(f"Failed to count validation results: {e}")
            raise DatabaseQueryError(f"Failed to count validation results: {e}")

    # Helper methods

    def _validate_insert_params(
        self,
        strategy_name: str,
        timestamp: datetime,
        total_trades: int,
        win_rate: Optional[float],
        max_drawdown: Optional[float],
        profit_factor: Optional[float],
        git_commit_hash: Optional[str],
    ) -> None:
        """Validate insert parameters."""
        # Strategy name validation
        if not strategy_name or not strategy_name.strip():
            raise ValueError("strategy_name cannot be empty")
        if not re.match(r"^[A-Za-z0-9_-]+$", strategy_name):
            raise ValueError(
                "strategy_name must contain only alphanumeric characters, underscores, and hyphens"
            )

        # Timestamp validation
        if timestamp > datetime.utcnow():
            raise ValueError("timestamp cannot be in the future")

        # Total trades validation
        if total_trades < 0:
            raise ValueError("total_trades must be >= 0")

        # Win rate validation
        if win_rate is not None and (win_rate < 0 or win_rate > 100):
            raise ValueError("win_rate must be between 0 and 100")

        # Max drawdown validation
        if max_drawdown is not None and max_drawdown > 0:
            raise ValueError("max_drawdown must be <= 0 (negative value)")

        # Profit factor validation
        if profit_factor is not None and profit_factor < 0:
            raise ValueError("profit_factor must be >= 0")

        # Git commit hash validation
        if git_commit_hash is not None:
            if not re.match(r"^[0-9a-f]{40}$", git_commit_hash):
                raise ValueError(
                    "git_commit_hash must be exactly 40 hexadecimal characters"
                )

    def _get_order_column(self, order_by: str):
        """Get SQLAlchemy order column based on order_by string."""
        if order_by == "timestamp_desc":
            return desc(self.validation_results.c.timestamp)
        elif order_by == "timestamp_asc":
            return asc(self.validation_results.c.timestamp)
        elif order_by == "strategy_name_asc":
            return asc(self.validation_results.c.strategy_name)
        elif order_by == "win_rate_desc":
            return desc(self.validation_results.c.win_rate)
        elif order_by == "total_profit_desc":
            return desc(self.validation_results.c.total_profit_pct)
        else:
            return desc(self.validation_results.c.timestamp)

    def _row_to_validation_result(self, row) -> ValidationResult:
        """Convert database row to ValidationResult dataclass."""
        return ValidationResult(
            id=row.id,
            strategy_name=row.strategy_name,
            timestamp=row.timestamp,
            total_trades=row.total_trades,
            win_rate=float(row.win_rate) if row.win_rate is not None else None,
            total_profit_pct=(
                float(row.total_profit_pct)
                if row.total_profit_pct is not None
                else None
            ),
            max_drawdown=(
                float(row.max_drawdown) if row.max_drawdown is not None else None
            ),
            sharpe_ratio=(
                float(row.sharpe_ratio) if row.sharpe_ratio is not None else None
            ),
            profit_factor=(
                float(row.profit_factor) if row.profit_factor is not None else None
            ),
            git_commit_hash=row.git_commit_hash,
            created_at=row.created_at,
        )
