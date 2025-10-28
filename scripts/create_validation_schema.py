#!/usr/bin/env python3
"""
Database Migration Script for Validation Results

Creates the validation_results table in the database by executing the schema SQL.

Feature: 001-test-validation-dashboard
User Story 3: Centralized Validation Results Storage (Priority: P2)
Created: 2025-10-28

Usage:
    python scripts/create_validation_schema.py
"""

import sys
import logging
from pathlib import Path

from proratio_utilities.config.settings import get_settings
from proratio_utilities.data.validation_repository import (
    ValidationRepository,
    DatabaseConnectionError,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_validation_schema():
    """
    Create validation_results table in the database.

    Uses the ValidationRepository's table metadata to create the table.
    """
    try:
        # Get settings
        settings = get_settings()
        database_url = settings.validation_db_url or settings.database_url

        logger.info(f"Connecting to database...")
        logger.info(f"Database URL: {database_url[:20]}...")  # Show only prefix

        # Initialize repository (this creates the engine)
        repo = ValidationRepository(database_url=database_url)

        # Create tables from metadata
        logger.info("Creating validation_results table...")
        repo.metadata.create_all(repo.engine)

        logger.info("✓ validation_results table created successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Verify table exists:")
        logger.info("     psql -U postgres -d proratio -c '\\d+ validation_results'")
        logger.info("  2. Run a backtest validation:")
        logger.info(
            "     python scripts/validate_backtest_results.py --strategy GridTrading"
        )
        logger.info("  3. Check that results were stored:")
        logger.info(
            "     psql -U postgres -d proratio -c 'SELECT * FROM validation_results;'"
        )

        return True

    except DatabaseConnectionError as e:
        logger.error(f"Failed to connect to database: {e}")
        logger.error("")
        logger.error("Troubleshooting steps:")
        logger.error("  1. Check that PostgreSQL is running")
        logger.error("  2. Verify DATABASE_URL or VALIDATION_DB_URL in .env file")
        logger.error(
            "  3. Test connection: psql -U postgres -d proratio -c 'SELECT 1;'"
        )
        return False

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    logger.info("=" * 70)
    logger.info("Validation Results Schema Creation")
    logger.info("=" * 70)
    logger.info("")

    success = create_validation_schema()

    logger.info("")
    logger.info("=" * 70)

    if success:
        logger.info("Schema creation completed successfully!")
        sys.exit(0)
    else:
        logger.error("Schema creation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
