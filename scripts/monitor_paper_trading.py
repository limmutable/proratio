#!/usr/bin/env python3
"""
Monitor Proratio Paper Trading Session
Real-time display of trades, performance, and AI decisions
"""

import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from proratio_utilities.config.settings import get_settings


class PaperTradingMonitor:
    """Monitor paper trading performance and AI decisions"""

    def __init__(self, db_path: str = "user_data/tradesv3_dryrun.sqlite"):
        self.db_path = db_path
        self.settings = get_settings()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def get_open_trades(self) -> List[Dict]:
        """Get currently open trades"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                id, pair, open_date, open_rate, amount, stake_amount,
                stop_loss, initial_stop_loss
            FROM trades
            WHERE is_open = 1
            ORDER BY open_date DESC
        """

        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]

        trades = []
        for row in cursor.fetchall():
            trade = dict(zip(columns, row))
            trades.append(trade)

        conn.close()
        return trades

    def get_closed_trades(self, limit: int = 10) -> List[Dict]:
        """Get recently closed trades"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                id, pair, open_date, close_date, open_rate, close_rate,
                amount, stake_amount, close_profit_abs, close_profit
            FROM trades
            WHERE is_open = 0
            ORDER BY close_date DESC
            LIMIT ?
        """

        cursor.execute(query, (limit,))
        columns = [desc[0] for desc in cursor.description]

        trades = []
        for row in cursor.fetchall():
            trade = dict(zip(columns, row))
            trades.append(trade)

        conn.close()
        return trades

    def get_performance_stats(self) -> Dict:
        """Get overall performance statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Closed trades stats
        query = """
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN close_profit > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(close_profit_abs) as total_profit_usdt,
                AVG(close_profit) as avg_profit_pct,
                MAX(close_profit) as max_profit_pct,
                MIN(close_profit) as max_loss_pct
            FROM trades
            WHERE is_open = 0
        """

        cursor.execute(query)
        row = cursor.fetchone()

        if row[0] == 0:  # No closed trades yet
            conn.close()
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "win_rate": 0,
                "total_profit_usdt": 0,
                "avg_profit_pct": 0,
                "max_profit_pct": 0,
                "max_loss_pct": 0,
            }

        stats = {
            "total_trades": row[0],
            "winning_trades": row[1],
            "win_rate": (row[1] / row[0] * 100) if row[0] > 0 else 0,
            "total_profit_usdt": row[2] or 0,
            "avg_profit_pct": row[3] or 0,
            "max_profit_pct": row[4] or 0,
            "max_loss_pct": row[5] or 0,
        }

        conn.close()
        return stats

    def display_dashboard(self):
        """Display monitoring dashboard"""
        # Clear screen
        print("\033[2J\033[H", end="")

        print("=" * 80)
        print(" " * 20 + "PRORATIO PAPER TRADING MONITOR")
        print("=" * 80)
        print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Performance Stats
        stats = self.get_performance_stats()

        print("📊 PERFORMANCE SUMMARY")
        print("-" * 80)
        print(f"Total Trades:    {stats['total_trades']}")
        print(f"Winning Trades:  {stats['winning_trades']}")
        print(f"Win Rate:        {stats['win_rate']:.1f}%")
        print(f"Total Profit:    ${stats['total_profit_usdt']:.2f} USDT")
        print(f"Avg Profit:      {stats['avg_profit_pct']:.2f}%")
        print(f"Max Win:         {stats['max_profit_pct']:.2f}%")
        print(f"Max Loss:        {stats['max_loss_pct']:.2f}%")
        print()

        # Open Trades
        open_trades = self.get_open_trades()

        print(f"🔓 OPEN TRADES ({len(open_trades)})")
        print("-" * 80)

        if open_trades:
            for trade in open_trades:
                print(f"#{trade['id']} {trade['pair']}")
                print(f"  Opened:     {trade['open_date']}")
                print(f"  Entry:      ${trade['open_rate']:.2f}")
                print(f"  Amount:     {trade['amount']:.4f}")
                print(f"  Stake:      ${trade['stake_amount']:.2f} USDT")
                print(f"  Stop Loss:  ${trade['stop_loss']:.2f}")
                print()
        else:
            print("  No open trades")
            print()

        # Recent Closed Trades
        closed_trades = self.get_closed_trades(limit=5)

        print("🔒 RECENT CLOSED TRADES (Last 5)")
        print("-" * 80)

        if closed_trades:
            for trade in closed_trades:
                profit_sign = "+" if trade["close_profit"] > 0 else ""
                emoji = "✅" if trade["close_profit"] > 0 else "❌"

                print(f"{emoji} #{trade['id']} {trade['pair']}")
                print(f"  Opened:     {trade['open_date']}")
                print(f"  Closed:     {trade['close_date']}")
                print(f"  Entry:      ${trade['open_rate']:.2f}")
                print(f"  Exit:       ${trade['close_rate']:.2f}")
                print(
                    f"  Profit:     {profit_sign}${trade['close_profit_abs']:.2f} USDT ({profit_sign}{trade['close_profit']:.2f}%)"
                )
                print()
        else:
            print("  No closed trades yet")
            print()

        print("=" * 80)
        print("Press Ctrl+C to stop monitoring")
        print("=" * 80)

    def monitor_loop(self, interval: int = 10):
        """Continuously monitor and display dashboard"""
        print("Starting Proratio Paper Trading Monitor...")
        print(f"Monitoring database: {self.db_path}")
        print()

        try:
            while True:
                self.display_dashboard()
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")

        except Exception as e:
            print(f"\n\nError: {e}")
            raise


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor Proratio Paper Trading")
    parser.add_argument(
        "--db",
        default="user_data/tradesv3_dryrun.sqlite",
        help="Path to Freqtrade database (default: user_data/tradesv3_dryrun.sqlite)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Update interval in seconds (default: 10)",
    )
    parser.add_argument(
        "--once", action="store_true", help="Show dashboard once and exit (no loop)"
    )

    args = parser.parse_args()

    # Check if database exists
    if not Path(args.db).exists():
        print(f"Error: Database not found at {args.db}")
        print("Make sure Freqtrade is running in paper trading mode.")
        return 1

    monitor = PaperTradingMonitor(db_path=args.db)

    if args.once:
        monitor.display_dashboard()
    else:
        monitor.monitor_loop(interval=args.interval)

    return 0


if __name__ == "__main__":
    sys.exit(main())
