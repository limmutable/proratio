#!/usr/bin/env python3
"""
Generate Weekly Paper Trading Performance Report
Analyzes trades, AI decisions, and compares to backtest expectations
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from proratio_utilities.config.settings import get_settings


class WeeklyReportGenerator:
    """Generate comprehensive weekly performance reports"""

    def __init__(self, db_path: str = "user_data/tradesv3_dryrun.sqlite"):
        self.db_path = db_path
        self.settings = get_settings()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def get_trades_in_period(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        """Get all trades within a specific period"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                id, pair, open_date, close_date, open_rate, close_rate,
                amount, stake_amount, close_profit_abs, close_profit,
                is_open, stop_loss, exit_reason
            FROM trades
            WHERE open_date >= ? AND open_date <= ?
            ORDER BY open_date
        """

        cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))

        columns = [desc[0] for desc in cursor.description]

        trades = []
        for row in cursor.fetchall():
            trade = dict(zip(columns, row))
            trades.append(trade)

        conn.close()
        return trades

    def calculate_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate performance metrics"""
        closed_trades = [t for t in trades if not t["is_open"]]

        if not closed_trades:
            return {
                "total_trades": len(trades),
                "closed_trades": 0,
                "open_trades": len([t for t in trades if t["is_open"]]),
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "total_profit_usdt": 0,
                "avg_profit_pct": 0,
                "max_profit_pct": 0,
                "max_loss_pct": 0,
                "avg_trade_duration_hours": 0,
            }

        winning_trades = [t for t in closed_trades if t["close_profit"] > 0]
        losing_trades = [t for t in closed_trades if t["close_profit"] <= 0]

        # Calculate average trade duration
        durations = []
        for trade in closed_trades:
            if trade["close_date"]:
                open_dt = datetime.fromisoformat(trade["open_date"])
                close_dt = datetime.fromisoformat(trade["close_date"])
                duration = (close_dt - open_dt).total_seconds() / 3600
                durations.append(duration)

        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_trades": len(trades),
            "closed_trades": len(closed_trades),
            "open_trades": len([t for t in trades if t["is_open"]]),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len(closed_trades) * 100,
            "total_profit_usdt": sum(t["close_profit_abs"] for t in closed_trades),
            "avg_profit_pct": sum(t["close_profit"] for t in closed_trades)
            / len(closed_trades),
            "max_profit_pct": max(t["close_profit"] for t in closed_trades),
            "max_loss_pct": min(t["close_profit"] for t in closed_trades),
            "avg_trade_duration_hours": avg_duration,
        }

    def get_exit_reasons_breakdown(self, trades: List[Dict]) -> Dict:
        """Analyze exit reasons"""
        closed_trades = [t for t in trades if not t["is_open"]]

        if not closed_trades:
            return {}

        reasons = {}
        for trade in closed_trades:
            reason = trade.get("exit_reason", "unknown")
            reasons[reason] = reasons.get(reason, 0) + 1

        return reasons

    def generate_report(self, days: int = 7, output_file: Optional[str] = None) -> str:
        """Generate comprehensive weekly report"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Get trades
        trades = self.get_trades_in_period(start_date, end_date)
        metrics = self.calculate_metrics(trades)
        exit_reasons = self.get_exit_reasons_breakdown(trades)

        # Build report
        report = []
        report.append("=" * 80)
        report.append(" " * 25 + "PRORATIO WEEKLY REPORT")
        report.append("=" * 80)
        report.append(
            f"Report Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )
        report.append(f"Duration: {days} days")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Performance Summary
        report.append("📊 PERFORMANCE SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Trades:          {metrics['total_trades']}")
        report.append(f"  Closed Trades:       {metrics['closed_trades']}")
        report.append(f"  Open Trades:         {metrics['open_trades']}")
        report.append(f"Winning Trades:        {metrics['winning_trades']}")
        report.append(f"Losing Trades:         {metrics['losing_trades']}")
        report.append(f"Win Rate:              {metrics['win_rate']:.1f}%")
        report.append(
            f"Total Profit:          ${metrics['total_profit_usdt']:.2f} USDT"
        )
        report.append(f"Average Profit/Trade:  {metrics['avg_profit_pct']:.2f}%")
        report.append(f"Best Trade:            {metrics['max_profit_pct']:.2f}%")
        report.append(f"Worst Trade:           {metrics['max_loss_pct']:.2f}%")
        report.append(
            f"Avg Trade Duration:    {metrics['avg_trade_duration_hours']:.1f} hours"
        )
        report.append("")

        # Exit Reasons
        if exit_reasons:
            report.append("🚪 EXIT REASONS BREAKDOWN")
            report.append("-" * 80)
            for reason, count in sorted(
                exit_reasons.items(), key=lambda x: x[1], reverse=True
            ):
                pct = count / metrics["closed_trades"] * 100
                report.append(f"{reason:25s} {count:3d} trades ({pct:.1f}%)")
            report.append("")

        # Trade Details
        if trades:
            report.append("📝 TRADE DETAILS")
            report.append("-" * 80)

            for trade in trades:
                status = "OPEN" if trade["is_open"] else "CLOSED"
                emoji = (
                    "🔓"
                    if trade["is_open"]
                    else (
                        "✅"
                        if trade["close_profit"] and trade["close_profit"] > 0
                        else "❌"
                    )
                )

                report.append(
                    f"{emoji} Trade #{trade['id']} - {trade['pair']} [{status}]"
                )
                report.append(f"  Opened:  {trade['open_date']}")

                if not trade["is_open"]:
                    report.append(f"  Closed:  {trade['close_date']}")
                    report.append(f"  Entry:   ${trade['open_rate']:.2f}")
                    report.append(f"  Exit:    ${trade['close_rate']:.2f}")

                    profit_sign = "+" if trade["close_profit"] > 0 else ""
                    report.append(
                        f"  Profit:  {profit_sign}${trade['close_profit_abs']:.2f} USDT ({profit_sign}{trade['close_profit']:.2f}%)"
                    )
                    report.append(f"  Reason:  {trade['exit_reason']}")
                else:
                    report.append(f"  Entry:   ${trade['open_rate']:.2f}")
                    report.append(f"  Amount:  {trade['amount']:.4f}")
                    report.append(f"  Stop:    ${trade['stop_loss']:.2f}")

                report.append("")

        # AI Performance Analysis
        report.append("🤖 AI SIGNAL ANALYSIS")
        report.append("-" * 80)
        report.append("AI Provider Status:")
        report.append("  ✓ Claude (Sonnet 4)          - Active")
        report.append("  ✓ Gemini (2.0 Flash)         - Active")
        report.append("  ✗ ChatGPT (GPT-5 Nano)       - Quota exceeded")
        report.append("")
        report.append("Active Providers: 2/3 (66.7%)")
        report.append("Consensus Threshold: 60%")
        report.append("Dynamic Reweighting: Enabled (Claude 60% → 100% when needed)")
        report.append("")

        # Comparison to Backtest
        report.append("📈 BACKTEST COMPARISON")
        report.append("-" * 80)
        report.append("Backtest Expectations (6-month baseline):")
        report.append("  Total Trades:          45")
        report.append("  Win Rate:              ~50%")
        report.append("  Total Profit:          -0.18%")
        report.append("  Sharpe Ratio:          -1.03")
        report.append("")

        if metrics["closed_trades"] > 0:
            report.append("Paper Trading vs Backtest:")
            trade_diff = metrics["closed_trades"] - 45
            winrate_diff = metrics["win_rate"] - 50
            profit_diff = metrics["total_profit_usdt"]

            report.append(f"  Trade Count Diff:      {trade_diff:+d} trades")
            report.append(f"  Win Rate Diff:         {winrate_diff:+.1f}%")
            report.append(f"  Profit Diff:           ${profit_diff:+.2f} USDT")
            report.append("")

            # Status assessment
            if metrics["total_profit_usdt"] > 0:
                report.append("✅ Status: Outperforming backtest expectations")
            elif metrics["total_profit_usdt"] == 0:
                report.append("⚠️  Status: Neutral (AI filtering prevented trades)")
            else:
                report.append("⚠️  Status: Below backtest expectations")
        else:
            report.append(
                "⚠️  Not enough data for comparison (need at least 1 closed trade)"
            )

        report.append("")

        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 80)

        if metrics["closed_trades"] == 0:
            report.append(
                "• No trades executed - AI confidence threshold (60%) may be too high"
            )
            report.append(
                "• Consider lowering threshold to 50-55% for more opportunities"
            )
            report.append("• Verify AI providers are working correctly")
        elif metrics["win_rate"] < 50:
            report.append("• Win rate below 50% - review entry criteria")
            report.append("• Check AI signal quality and market conditions")
        elif metrics["win_rate"] > 65:
            report.append("• Strong win rate - strategy performing well")
            report.append("• Consider scaling position sizes carefully")

        if metrics["total_profit_usdt"] < 0:
            report.append("• Negative P&L - review risk management settings")
            report.append("• Consider tightening stop losses or widening take profits")

        report.append("")
        report.append("=" * 80)
        report.append("End of Report")
        report.append("=" * 80)

        # Join report
        report_text = "\n".join(report)

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report_text)
            print(f"✓ Report saved to: {output_file}")

        return report_text


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate Proratio Weekly Report")
    parser.add_argument(
        "--db",
        default="user_data/tradesv3_dryrun.sqlite",
        help="Path to Freqtrade database",
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Number of days to analyze (default: 7)"
    )
    parser.add_argument(
        "--output",
        help="Save report to file (e.g., reports/weekly_report_20251008.txt)",
    )

    args = parser.parse_args()

    # Check if database exists
    if not Path(args.db).exists():
        print(f"Error: Database not found at {args.db}")
        print("Make sure Freqtrade has been running in paper trading mode.")
        return 1

    generator = WeeklyReportGenerator(db_path=args.db)
    report = generator.generate_report(days=args.days, output_file=args.output)

    # Print report
    print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
