"""
Validation Repository Interface

This module defines the contract for interacting with the validation_results database table.
Implements FR-009: System MUST provide a mechanism to query stored validation results
programmatically for future analysis and visualization.

Feature: 001-test-validation-dashboard
Created: 2025-10-27

Implementation: proratio_utilities/data/validation_repository.py
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass


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
    Repository interface for storing and retrieving backtest validation results.

    This is an abstract interface defining the contract. The concrete implementation
    will use SQLAlchemy Core for database access.

    Constitutional Alignment:
    - IV. Configuration as Code: Database credentials from .env via Pydantic Settings
    - VII. Observability: Uses Python logging module (not print statements)
    - VIII. Code Quality: Type hints on all methods, docstrings with Google style
    """

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

        Example:
            >>> repo = ValidationRepository()
            >>> result_id = repo.insert_validation_result(
            ...     strategy_name='GridTrading',
            ...     timestamp=datetime.utcnow(),
            ...     total_trades=150,
            ...     win_rate=65.33,
            ...     total_profit_pct=12.45,
            ...     max_drawdown=-8.75,
            ...     sharpe_ratio=1.82,
            ...     profit_factor=1.65,
            ...     git_commit_hash='a1b2c3d4...'
            ... )
            >>> print(f"Inserted validation result with ID: {result_id}")
        """
        raise NotImplementedError("Must be implemented by concrete repository class")

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

        Example:
            >>> repo = ValidationRepository()
            >>> # Get last 50 validations for GridTrading strategy
            >>> results = repo.query_validation_results(
            ...     strategy_name='GridTrading',
            ...     limit=50,
            ...     order_by='timestamp_desc'
            ... )
            >>> for result in results:
            ...     print(f"{result.timestamp}: {result.win_rate}% win rate")
        """
        raise NotImplementedError("Must be implemented by concrete repository class")

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

        Example:
            >>> repo = ValidationRepository()
            >>> latest = repo.get_latest_validation('GridTrading')
            >>> if latest:
            ...     print(f"Latest run: {latest.timestamp}, {latest.win_rate}% win rate")
            ... else:
            ...     print("No validation results found for this strategy")
        """
        raise NotImplementedError("Must be implemented by concrete repository class")

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

        Example:
            >>> repo = ValidationRepository()
            >>> result = repo.get_validation_by_id(12345)
            >>> if result:
            ...     print(f"Strategy: {result.strategy_name}, Profit: {result.total_profit_pct}%")
        """
        raise NotImplementedError("Must be implemented by concrete repository class")

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

        Example:
            >>> repo = ValidationRepository()
            >>> # Count total validations in the last 30 days
            >>> from datetime import timedelta
            >>> count = repo.count_validations(
            ...     start_date=datetime.utcnow() - timedelta(days=30)
            ... )
            >>> print(f"Validation runs in last 30 days: {count}")
        """
        raise NotImplementedError("Must be implemented by concrete repository class")


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


# Type aliases for convenience

ValidationMetrics = Dict[str, Optional[float]]
"""Dictionary containing validation performance metrics (win_rate, profit, etc.)"""

ValidationFilters = Dict[str, Optional[str | datetime | int]]
"""Dictionary containing query filters (strategy_name, start_date, etc.)"""
