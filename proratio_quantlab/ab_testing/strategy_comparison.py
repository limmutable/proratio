"""
A/B Testing Framework for Strategy Comparison

Provides tools to compare multiple trading strategies side-by-side:
- Parallel backtesting across same time period
- Statistical significance testing
- Performance metrics comparison
- Risk-adjusted returns analysis
- Visual comparison charts

Use cases:
- Compare strategy variants (e.g., different parameters)
- Test new vs. existing strategies
- Evaluate strategy combinations
- Validate strategy improvements
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy import stats


@dataclass
class StrategyResult:
    """Results from a single strategy backtest"""

    strategy_name: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    profit_factor: float
    avg_trade_return_pct: float
    avg_win_pct: float
    avg_loss_pct: float
    best_trade_pct: float
    worst_trade_pct: float
    avg_trade_duration_hours: float
    total_fees: float
    returns_distribution: List[float] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ComparisonResult:
    """Results from comparing two strategies"""

    strategy_a: StrategyResult
    strategy_b: StrategyResult
    winner: str  # Which strategy performed better
    confidence: float  # Statistical confidence in the result (0-1)
    metrics_comparison: Dict[str, Dict]  # Detailed metric-by-metric comparison
    statistical_tests: Dict[str, float]  # p-values from statistical tests
    recommendation: str  # Human-readable recommendation


class StrategyComparer:
    """
    A/B testing framework for strategy comparison.

    Compares strategies across multiple dimensions:
    - Returns and profitability
    - Risk metrics
    - Trade statistics
    - Statistical significance
    """

    def __init__(
        self,
        significance_level: float = 0.05,  # 5% significance level
        min_trades_for_significance: int = 30  # Minimum trades for valid comparison
    ):
        """
        Initialize Strategy Comparer.

        Args:
            significance_level: P-value threshold for statistical significance
            min_trades_for_significance: Minimum trades required for valid stats
        """
        self.significance_level = significance_level
        self.min_trades_for_significance = min_trades_for_significance

    def compare_strategies(
        self,
        strategy_a: StrategyResult,
        strategy_b: StrategyResult
    ) -> ComparisonResult:
        """
        Compare two strategies comprehensively.

        Args:
            strategy_a: Results from first strategy
            strategy_b: Results from second strategy

        Returns:
            ComparisonResult with detailed comparison
        """
        # Metrics comparison
        metrics_comparison = self._compare_metrics(strategy_a, strategy_b)

        # Statistical tests
        statistical_tests = self._run_statistical_tests(strategy_a, strategy_b)

        # Determine winner
        winner, confidence = self._determine_winner(metrics_comparison, statistical_tests)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            strategy_a, strategy_b, winner, confidence, metrics_comparison
        )

        return ComparisonResult(
            strategy_a=strategy_a,
            strategy_b=strategy_b,
            winner=winner,
            confidence=confidence,
            metrics_comparison=metrics_comparison,
            statistical_tests=statistical_tests,
            recommendation=recommendation
        )

    def _compare_metrics(
        self,
        strategy_a: StrategyResult,
        strategy_b: StrategyResult
    ) -> Dict[str, Dict]:
        """
        Compare individual metrics between strategies.

        Returns:
            Dict with comparison for each metric
        """
        comparisons = {}

        # Return comparison
        comparisons['total_return'] = {
            'a': strategy_a.total_return_pct,
            'b': strategy_b.total_return_pct,
            'diff': strategy_b.total_return_pct - strategy_a.total_return_pct,
            'pct_change': ((strategy_b.total_return_pct - strategy_a.total_return_pct) /
                          abs(strategy_a.total_return_pct) * 100) if strategy_a.total_return_pct != 0 else 0,
            'winner': 'b' if strategy_b.total_return_pct > strategy_a.total_return_pct else 'a'
        }

        # Sharpe ratio comparison
        comparisons['sharpe_ratio'] = {
            'a': strategy_a.sharpe_ratio,
            'b': strategy_b.sharpe_ratio,
            'diff': strategy_b.sharpe_ratio - strategy_a.sharpe_ratio,
            'pct_change': ((strategy_b.sharpe_ratio - strategy_a.sharpe_ratio) /
                          abs(strategy_a.sharpe_ratio) * 100) if strategy_a.sharpe_ratio != 0 else 0,
            'winner': 'b' if strategy_b.sharpe_ratio > strategy_a.sharpe_ratio else 'a'
        }

        # Max drawdown comparison (lower is better)
        comparisons['max_drawdown'] = {
            'a': strategy_a.max_drawdown_pct,
            'b': strategy_b.max_drawdown_pct,
            'diff': strategy_a.max_drawdown_pct - strategy_b.max_drawdown_pct,  # Reversed
            'pct_change': ((strategy_a.max_drawdown_pct - strategy_b.max_drawdown_pct) /
                          abs(strategy_a.max_drawdown_pct) * 100) if strategy_a.max_drawdown_pct != 0 else 0,
            'winner': 'b' if strategy_b.max_drawdown_pct < strategy_a.max_drawdown_pct else 'a'
        }

        # Win rate comparison
        comparisons['win_rate'] = {
            'a': strategy_a.win_rate,
            'b': strategy_b.win_rate,
            'diff': strategy_b.win_rate - strategy_a.win_rate,
            'pct_change': ((strategy_b.win_rate - strategy_a.win_rate) /
                          strategy_a.win_rate * 100) if strategy_a.win_rate != 0 else 0,
            'winner': 'b' if strategy_b.win_rate > strategy_a.win_rate else 'a'
        }

        # Profit factor comparison
        comparisons['profit_factor'] = {
            'a': strategy_a.profit_factor,
            'b': strategy_b.profit_factor,
            'diff': strategy_b.profit_factor - strategy_a.profit_factor,
            'pct_change': ((strategy_b.profit_factor - strategy_a.profit_factor) /
                          strategy_a.profit_factor * 100) if strategy_a.profit_factor != 0 else 0,
            'winner': 'b' if strategy_b.profit_factor > strategy_a.profit_factor else 'a'
        }

        # Total trades comparison
        comparisons['total_trades'] = {
            'a': strategy_a.total_trades,
            'b': strategy_b.total_trades,
            'diff': strategy_b.total_trades - strategy_a.total_trades,
            'pct_change': ((strategy_b.total_trades - strategy_a.total_trades) /
                          strategy_a.total_trades * 100) if strategy_a.total_trades != 0 else 0,
            'winner': 'neutral'  # More trades isn't necessarily better
        }

        return comparisons

    def _run_statistical_tests(
        self,
        strategy_a: StrategyResult,
        strategy_b: StrategyResult
    ) -> Dict[str, float]:
        """
        Run statistical tests to determine if differences are significant.

        Returns:
            Dict with p-values from various tests
        """
        tests = {}

        # Check if we have enough data
        if (len(strategy_a.returns_distribution) < self.min_trades_for_significance or
            len(strategy_b.returns_distribution) < self.min_trades_for_significance):
            tests['warning'] = 'insufficient_data'
            tests['t_test'] = 1.0  # Not significant
            tests['mann_whitney'] = 1.0
            return tests

        # T-test for mean returns
        try:
            t_stat, t_pvalue = stats.ttest_ind(
                strategy_a.returns_distribution,
                strategy_b.returns_distribution,
                equal_var=False  # Welch's t-test
            )
            tests['t_test'] = t_pvalue
        except Exception as e:
            tests['t_test'] = 1.0
            tests['t_test_error'] = str(e)

        # Mann-Whitney U test (non-parametric alternative)
        try:
            u_stat, u_pvalue = stats.mannwhitneyu(
                strategy_a.returns_distribution,
                strategy_b.returns_distribution,
                alternative='two-sided'
            )
            tests['mann_whitney'] = u_pvalue
        except Exception as e:
            tests['mann_whitney'] = 1.0
            tests['mann_whitney_error'] = str(e)

        # Kolmogorov-Smirnov test (distribution similarity)
        try:
            ks_stat, ks_pvalue = stats.ks_2samp(
                strategy_a.returns_distribution,
                strategy_b.returns_distribution
            )
            tests['ks_test'] = ks_pvalue
        except Exception as e:
            tests['ks_test'] = 1.0
            tests['ks_test_error'] = str(e)

        # Variance test (F-test)
        try:
            var_a = np.var(strategy_a.returns_distribution, ddof=1)
            var_b = np.var(strategy_b.returns_distribution, ddof=1)
            f_stat = var_a / var_b if var_b != 0 else 0
            df1 = len(strategy_a.returns_distribution) - 1
            df2 = len(strategy_b.returns_distribution) - 1
            f_pvalue = 2 * min(stats.f.cdf(f_stat, df1, df2), 1 - stats.f.cdf(f_stat, df1, df2))
            tests['variance_test'] = f_pvalue
        except Exception as e:
            tests['variance_test'] = 1.0
            tests['variance_test_error'] = str(e)

        return tests

    def _determine_winner(
        self,
        metrics_comparison: Dict[str, Dict],
        statistical_tests: Dict[str, float]
    ) -> Tuple[str, float]:
        """
        Determine overall winner and confidence level.

        Args:
            metrics_comparison: Comparison of individual metrics
            statistical_tests: Results from statistical tests

        Returns:
            Tuple of (winner_name, confidence_score)
        """
        # Count metric wins
        a_wins = sum(1 for metric in metrics_comparison.values() if metric.get('winner') == 'a')
        b_wins = sum(1 for metric in metrics_comparison.values() if metric.get('winner') == 'b')

        # Determine winner
        if b_wins > a_wins:
            winner = 'strategy_b'
            win_ratio = b_wins / (a_wins + b_wins)
        elif a_wins > b_wins:
            winner = 'strategy_a'
            win_ratio = a_wins / (a_wins + b_wins)
        else:
            winner = 'tie'
            win_ratio = 0.5

        # Calculate confidence based on statistical significance
        if 'warning' in statistical_tests:
            confidence = 0.3  # Low confidence due to insufficient data
        else:
            # Use t-test p-value as primary significance test
            t_pvalue = statistical_tests.get('t_test', 1.0)

            if t_pvalue < self.significance_level:
                # Statistically significant difference
                confidence = 0.7 + (0.3 * win_ratio)  # 0.7 to 1.0
            else:
                # Not statistically significant
                confidence = 0.3 + (0.4 * win_ratio)  # 0.3 to 0.7

        return winner, confidence

    def _generate_recommendation(
        self,
        strategy_a: StrategyResult,
        strategy_b: StrategyResult,
        winner: str,
        confidence: float,
        metrics_comparison: Dict[str, Dict]
    ) -> str:
        """
        Generate human-readable recommendation.

        Returns:
            Recommendation text
        """
        lines = []

        # Overall verdict
        if winner == 'tie':
            lines.append(f"🤝 TIE: Both strategies show similar performance (confidence: {confidence:.1%})")
        elif winner == 'strategy_b':
            lines.append(f"🏆 WINNER: {strategy_b.strategy_name} (confidence: {confidence:.1%})")
        else:
            lines.append(f"🏆 WINNER: {strategy_a.strategy_name} (confidence: {confidence:.1%})")

        lines.append("")

        # Key improvements
        lines.append("📊 Key Differences:")

        return_comp = metrics_comparison.get('total_return', {})
        if abs(return_comp.get('diff', 0)) > 1:
            lines.append(f"  • Returns: {return_comp['diff']:+.2f}% "
                        f"({'✅' if return_comp['winner'] == 'b' else '❌'} Strategy B)")

        sharpe_comp = metrics_comparison.get('sharpe_ratio', {})
        if abs(sharpe_comp.get('diff', 0)) > 0.2:
            lines.append(f"  • Sharpe: {sharpe_comp['diff']:+.2f} "
                        f"({'✅' if sharpe_comp['winner'] == 'b' else '❌'} Strategy B)")

        dd_comp = metrics_comparison.get('max_drawdown', {})
        if abs(dd_comp.get('diff', 0)) > 2:
            lines.append(f"  • Drawdown: {dd_comp['diff']:+.2f}% "
                        f"({'✅' if dd_comp['winner'] == 'b' else '❌'} Strategy B)")

        # Recommendation
        lines.append("")
        if confidence > 0.7:
            if winner == 'strategy_b':
                lines.append(f"✅ RECOMMENDATION: Deploy {strategy_b.strategy_name}")
                lines.append(f"   Strong evidence of superior performance.")
            elif winner == 'strategy_a':
                lines.append(f"❌ RECOMMENDATION: Keep {strategy_a.strategy_name}")
                lines.append(f"   Strategy B does not show improvement.")
            else:
                lines.append(f"⚖️ RECOMMENDATION: Either strategy is acceptable")
        elif confidence > 0.5:
            lines.append(f"⚠️ RECOMMENDATION: More testing needed")
            lines.append(f"   Moderate evidence, consider longer backtest period.")
        else:
            lines.append(f"❓ RECOMMENDATION: Insufficient evidence")
            lines.append(f"   Increase sample size (more trades/longer period).")

        return "\n".join(lines)

    def print_comparison_report(self, comparison: ComparisonResult) -> None:
        """
        Print a detailed comparison report.

        Args:
            comparison: ComparisonResult to report
        """
        print("=" * 80)
        print(" " * 25 + "STRATEGY COMPARISON REPORT")
        print("=" * 80)
        print()

        # Strategy names
        print(f"Strategy A: {comparison.strategy_a.strategy_name}")
        print(f"Strategy B: {comparison.strategy_b.strategy_name}")
        print()

        # Performance metrics table
        print("-" * 80)
        print(f"{'Metric':<25} {'Strategy A':>15} {'Strategy B':>15} {'Difference':>15} {'Winner':>8}")
        print("-" * 80)

        for metric_name, metric_data in comparison.metrics_comparison.items():
            a_val = metric_data['a']
            b_val = metric_data['b']
            diff = metric_data['diff']
            winner = metric_data['winner']

            # Format values based on metric type
            if 'pct' in metric_name or 'rate' in metric_name or 'return' in metric_name:
                a_str = f"{a_val:.2f}%"
                b_str = f"{b_val:.2f}%"
                diff_str = f"{diff:+.2f}%"
            elif 'ratio' in metric_name or 'factor' in metric_name:
                a_str = f"{a_val:.2f}"
                b_str = f"{b_val:.2f}"
                diff_str = f"{diff:+.2f}"
            else:
                a_str = f"{a_val}"
                b_str = f"{b_val}"
                diff_str = f"{diff:+.0f}"

            winner_symbol = "A" if winner == 'a' else "B" if winner == 'b' else "-"

            print(f"{metric_name.replace('_', ' ').title():<25} {a_str:>15} {b_str:>15} {diff_str:>15} {winner_symbol:>8}")

        print("-" * 80)
        print()

        # Statistical tests
        print("Statistical Significance Tests:")
        print("-" * 80)
        for test_name, p_value in comparison.statistical_tests.items():
            if 'error' in test_name or 'warning' in test_name:
                continue

            sig_level = "***" if p_value < 0.01 else "**" if p_value < 0.05 else "*" if p_value < 0.10 else "n.s."
            print(f"{test_name.replace('_', ' ').title():<30} p={p_value:.4f} {sig_level:>6}")

        print("-" * 80)
        print()

        # Recommendation
        print(comparison.recommendation)
        print()
        print("=" * 80)


def create_strategy_result_from_backtest(
    strategy_name: str,
    backtest_data: Dict
) -> StrategyResult:
    """
    Create StrategyResult from Freqtrade backtest output.

    Args:
        strategy_name: Name of the strategy
        backtest_data: Dictionary with backtest results

    Returns:
        StrategyResult instance
    """
    # Extract metrics from backtest data
    # This is a helper function - actual implementation depends on backtest format

    return StrategyResult(
        strategy_name=strategy_name,
        total_trades=backtest_data.get('total_trades', 0),
        winning_trades=backtest_data.get('winning_trades', 0),
        losing_trades=backtest_data.get('losing_trades', 0),
        win_rate=backtest_data.get('win_rate', 0.0),
        total_return_pct=backtest_data.get('total_return_pct', 0.0),
        sharpe_ratio=backtest_data.get('sharpe_ratio', 0.0),
        max_drawdown_pct=backtest_data.get('max_drawdown_pct', 0.0),
        profit_factor=backtest_data.get('profit_factor', 0.0),
        avg_trade_return_pct=backtest_data.get('avg_trade_return_pct', 0.0),
        avg_win_pct=backtest_data.get('avg_win_pct', 0.0),
        avg_loss_pct=backtest_data.get('avg_loss_pct', 0.0),
        best_trade_pct=backtest_data.get('best_trade_pct', 0.0),
        worst_trade_pct=backtest_data.get('worst_trade_pct', 0.0),
        avg_trade_duration_hours=backtest_data.get('avg_trade_duration_hours', 0.0),
        total_fees=backtest_data.get('total_fees', 0.0),
        returns_distribution=backtest_data.get('returns_distribution', []),
        equity_curve=backtest_data.get('equity_curve', pd.Series()),
        metadata=backtest_data.get('metadata', {})
    )
