#!/usr/bin/env python3
"""
Query Validation Results

Example script for querying stored validation results from the database.

Feature: 001-test-validation-dashboard
User Story 3: Centralized Validation Results Storage
Created: 2025-10-28

Usage:
    # Get latest validation for a strategy
    python scripts/query_validation_results.py --strategy GridTrading --latest

    # Get all validations for a strategy
    python scripts/query_validation_results.py --strategy GridTrading --limit 10

    # Get validations in last 30 days
    python scripts/query_validation_results.py --days 30

    # Get validation by ID
    python scripts/query_validation_results.py --id 123
"""

import argparse
import sys
from datetime import datetime, timedelta

from proratio_utilities.data.validation_repository import (
    ValidationRepository,
    DatabaseConnectionError,
    DatabaseQueryError,
)


def format_validation_result(result):
    """Format a ValidationResult for display."""
    print(f"\n{'='*70}")
    print(f"Validation Result #{result.id}")
    print(f"{'='*70}")
    print(f"Strategy:        {result.strategy_name}")
    print(f"Timestamp:       {result.timestamp}")
    print(f"Total Trades:    {result.total_trades}")
    print(f"Win Rate:        {result.win_rate:.2f}%" if result.win_rate else "Win Rate:        N/A")
    print(f"Total Profit:    {result.total_profit_pct:.2f}%" if result.total_profit_pct else "Total Profit:    N/A")
    print(f"Max Drawdown:    {result.max_drawdown:.2f}%" if result.max_drawdown else "Max Drawdown:    N/A")
    print(f"Sharpe Ratio:    {result.sharpe_ratio:.2f}" if result.sharpe_ratio else "Sharpe Ratio:    N/A")
    print(f"Profit Factor:   {result.profit_factor:.2f}" if result.profit_factor else "Profit Factor:   N/A")
    print(f"Git Commit:      {result.git_commit_hash[:8] if result.git_commit_hash else 'N/A'}...")
    print(f"Created At:      {result.created_at}")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Query validation results from database")

    # Query options (mutually exclusive)
    query_group = parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument("--latest", action="store_true", help="Get latest validation for strategy")
    query_group.add_argument("--id", type=int, help="Get validation by ID")
    query_group.add_argument("--list", action="store_true", help="List validations")

    # Filters
    parser.add_argument("--strategy", help="Filter by strategy name")
    parser.add_argument("--days", type=int, help="Filter last N days")
    parser.add_argument("--limit", type=int, default=10, help="Maximum results (default: 10)")
    parser.add_argument("--count", action="store_true", help="Count matching results")

    args = parser.parse_args()

    try:
        # Initialize repository
        repo = ValidationRepository()

        # Execute query based on arguments
        if args.id:
            # Get by ID
            result = repo.get_validation_by_id(args.id)
            if result:
                format_validation_result(result)
            else:
                print(f"No validation result found with ID {args.id}")
                sys.exit(1)

        elif args.latest:
            # Get latest for strategy
            if not args.strategy:
                print("Error: --strategy required with --latest")
                sys.exit(1)

            result = repo.get_latest_validation(args.strategy)
            if result:
                format_validation_result(result)
            else:
                print(f"No validation results found for strategy '{args.strategy}'")
                sys.exit(1)

        elif args.list:
            # List validations with filters
            start_date = None
            if args.days:
                start_date = datetime.utcnow() - timedelta(days=args.days)

            results = repo.query_validation_results(
                strategy_name=args.strategy,
                start_date=start_date,
                limit=args.limit,
                order_by="timestamp_desc",
            )

            if results:
                print(f"\nFound {len(results)} validation result(s):\n")
                for result in results:
                    format_validation_result(result)
            else:
                print("No validation results found matching criteria")

            # Show count if requested
            if args.count:
                count = repo.count_validations(
                    strategy_name=args.strategy, start_date=start_date
                )
                print(f"\nTotal count matching criteria: {count}")

        else:
            parser.print_help()
            sys.exit(1)

    except DatabaseConnectionError as e:
        print(f"Error: Could not connect to database: {e}")
        print("\nTroubleshooting:")
        print("  1. Check DATABASE_URL or VALIDATION_DB_URL in .env")
        print("  2. Verify database is running")
        print("  3. Run: python scripts/create_validation_schema.py")
        sys.exit(1)

    except DatabaseQueryError as e:
        print(f"Error: Query failed: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
