#!/usr/bin/env python3
"""
Validation Report Generator

Generates comprehensive validation summary reports for strategies.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


def generate_summary_report(strategy: str, report_file: Path) -> Dict:
    """
    Generate summary report based on validation results.

    Returns summary statistics and recommendations.
    """
    # Read the validation report
    if not report_file.exists():
        return {"error": f"Report file not found: {report_file}"}

    with open(report_file, "r") as f:
        report_content = f.read()

    # Parse key metrics from report (simple text parsing)
    summary = {
        "strategy": strategy,
        "timestamp": datetime.now().isoformat(),
        "checks_passed": 0,
        "checks_failed": 0,
        "warnings": 0,
        "errors": 0,
    }

    # Count pass/fail markers
    summary["checks_passed"] = report_content.count("✓")
    summary["checks_failed"] = report_content.count("✗")
    summary["warnings"] = report_content.count("⚠")

    # Determine overall status
    if "✗ VALIDATION FAILED" in report_content:
        summary["status"] = "FAILED"
        summary["status_emoji"] = "❌"
    elif summary["checks_failed"] > 0:
        summary["status"] = "FAILED"
        summary["status_emoji"] = "❌"
    elif summary["warnings"] > 0:
        summary["status"] = "PASSED_WITH_WARNINGS"
        summary["status_emoji"] = "⚠️"
    else:
        summary["status"] = "PASSED"
        summary["status_emoji"] = "✅"

    return summary


def format_summary_report(summary: Dict) -> str:
    """Format summary report as text."""
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("VALIDATION SUMMARY")
    lines.append("=" * 60)
    lines.append(f"Strategy:        {summary['strategy']}")
    lines.append(f"Status:          {summary['status_emoji']} {summary['status']}")
    lines.append(f"Checks Passed:   {summary['checks_passed']}")
    lines.append(f"Checks Failed:   {summary['checks_failed']}")
    lines.append(f"Warnings:        {summary['warnings']}")
    lines.append(f"Timestamp:       {summary['timestamp']}")
    lines.append("=" * 60)
    lines.append("")

    # Add recommendations based on status
    if summary["status"] == "PASSED":
        lines.append("✅ READY FOR DEPLOYMENT")
        lines.append("")
        lines.append("Next steps:")
        lines.append("  1. Strategy passed all validation checks")
        lines.append("  2. Ready for paper trading or live deployment")
        lines.append("  3. Monitor performance in production")
        lines.append("")

    elif summary["status"] == "PASSED_WITH_WARNINGS":
        lines.append("⚠️ PASSED WITH WARNINGS")
        lines.append("")
        lines.append("Recommendations:")
        lines.append("  1. Review warnings in the full report")
        lines.append("  2. Consider addressing warnings before deployment")
        lines.append("  3. Proceed with caution if deploying")
        lines.append("")

    else:  # FAILED
        lines.append("❌ VALIDATION FAILED")
        lines.append("")
        lines.append("Required actions:")
        lines.append("  1. Review failed checks in the full report")
        lines.append("  2. Fix critical issues before deployment")
        lines.append("  3. Re-run validation after fixes")
        lines.append("  4. DO NOT deploy until validation passes")
        lines.append("")

    lines.append("Full report available at:")
    lines.append(f"  {summary.get('report_file', 'See validation output')}")
    lines.append("")

    return "\n".join(lines)


def save_json_summary(summary: Dict, strategy: str):
    """Save summary as JSON for programmatic access."""
    results_dir = Path("validation_results")
    results_dir.mkdir(exist_ok=True)

    json_file = results_dir / f"{strategy}_summary_latest.json"

    with open(json_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"JSON summary saved: {json_file}")


def print_quick_reference():
    """Print quick reference guide for validation results."""
    print("\n" + "=" * 60)
    print("VALIDATION FRAMEWORK - QUICK REFERENCE")
    print("=" * 60)
    print()
    print("Status Meanings:")
    print("  ✅ PASSED              - All checks passed, ready for deployment")
    print("  ⚠️  PASSED WITH WARNINGS - Passed but has minor issues")
    print("  ❌ FAILED              - Critical issues, DO NOT deploy")
    print()
    print("Validation Criteria:")
    print("  - Minimum trades:      >= 5 trades")
    print("  - Win rate:            >= 45%")
    print("  - Max drawdown:        < 25%")
    print("  - Sharpe ratio:        >= 0.5")
    print("  - Profit factor:       >= 1.0")
    print("  - Total profit:        >= 0%")
    print()
    print("To adjust criteria, edit:")
    print("  scripts/validate_backtest_results.py")
    print()
    print("=" * 60)
    print()


def main():
    parser = argparse.ArgumentParser(description="Generate validation summary report")
    parser.add_argument("--strategy", required=True, help="Strategy name")
    parser.add_argument("--report", required=True, help="Path to validation report file")
    parser.add_argument("--json", action="store_true", help="Save JSON summary")
    parser.add_argument("--quiet", action="store_true", help="Suppress detailed output")

    args = parser.parse_args()

    try:
        report_file = Path(args.report)

        # Generate summary
        summary = generate_summary_report(args.strategy, report_file)
        summary["report_file"] = str(report_file)

        if "error" in summary:
            print(f"Error: {summary['error']}", file=sys.stderr)
            sys.exit(1)

        # Save JSON if requested
        if args.json:
            save_json_summary(summary, args.strategy)

        # Print summary
        if not args.quiet:
            summary_text = format_summary_report(summary)
            print(summary_text)

            # Print quick reference
            print_quick_reference()

        # Exit with appropriate code
        sys.exit(0 if summary["status"] in ["PASSED", "PASSED_WITH_WARNINGS"] else 1)

    except Exception as e:
        print(f"Error generating report: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
