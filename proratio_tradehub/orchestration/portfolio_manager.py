"""
Multi-Strategy Portfolio Manager

Coordinates multiple trading strategies and allocates capital based on:
- Market conditions (trending vs. ranging vs. volatile)
- Strategy performance history
- Risk parameters
- AI market regime detection

Strategies managed:
- Trend Following (AIEnhancedStrategy)
- Mean Reversion (MeanReversionStrategy)
- Grid Trading (GridTradingStrategy)

Portfolio allocation approaches:
- Equal weight: All strategies get equal allocation
- Performance-based: Allocate more to better performers
- Market-adaptive: Allocate based on detected market regime
- AI-driven: Use AI to determine optimal allocation
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from proratio_tradehub.strategies.base_strategy import BaseStrategy, TradeSignal
from proratio_tradehub.strategies.mean_reversion import MeanReversionStrategy
from proratio_tradehub.strategies.grid_trading import GridTradingStrategy
from proratio_signals import SignalOrchestrator


@dataclass
class StrategyAllocation:
    """Represents allocation for a single strategy"""

    strategy_name: str
    weight: float  # 0.0 to 1.0 (percentage of total portfolio)
    enabled: bool
    performance_score: float  # Recent performance metric
    market_suitability: float  # How suitable is current market for this strategy (0-1)


@dataclass
class MarketRegime:
    """Detected market regime"""

    regime_type: str  # 'trending_up', 'trending_down', 'ranging', 'volatile', 'uncertain'
    confidence: float  # 0.0 to 1.0
    indicators: Dict[str, float]  # Supporting indicators
    timestamp: datetime


class PortfolioManager:
    """
    Multi-strategy portfolio management and capital allocation.

    Responsibilities:
    - Detect market regime
    - Allocate capital across strategies
    - Monitor strategy performance
    - Rebalance portfolio based on conditions
    """

    def __init__(
        self,
        total_capital: float,
        allocation_method: str = "market_adaptive",  # or "equal", "performance", "ai_driven"
        rebalance_frequency_hours: int = 24,
        min_strategy_allocation: float = 0.10,  # Minimum 10% per strategy
        max_strategy_allocation: float = 0.60,  # Maximum 60% per strategy
        use_ai_regime_detection: bool = True
    ):
        """
        Initialize Portfolio Manager.

        Args:
            total_capital: Total portfolio capital to manage
            allocation_method: Method for capital allocation
            rebalance_frequency_hours: How often to rebalance portfolio
            min_strategy_allocation: Minimum allocation per strategy
            max_strategy_allocation: Maximum allocation per strategy
            use_ai_regime_detection: Whether to use AI for market regime detection
        """
        self.total_capital = total_capital
        self.allocation_method = allocation_method
        self.rebalance_frequency_hours = rebalance_frequency_hours
        self.min_strategy_allocation = min_strategy_allocation
        self.max_strategy_allocation = max_strategy_allocation
        self.use_ai_regime_detection = use_ai_regime_detection

        # Initialize strategies (these would be instantiated by the user)
        self.strategies: Dict[str, BaseStrategy] = {}
        self.allocations: Dict[str, StrategyAllocation] = {}

        # Performance tracking
        self.performance_history: Dict[str, List[float]] = {}  # strategy_name -> list of returns
        self.last_rebalance: Optional[datetime] = None

        # AI orchestrator for regime detection
        self.orchestrator = None
        if self.use_ai_regime_detection:
            try:
                self.orchestrator = SignalOrchestrator()
            except Exception as e:
                print(f"Warning: Could not initialize AI orchestrator: {e}")
                self.use_ai_regime_detection = False

        # Current market regime
        self.current_regime: Optional[MarketRegime] = None

    def register_strategy(self, strategy: BaseStrategy, initial_weight: float = None) -> None:
        """
        Register a strategy with the portfolio manager.

        Args:
            strategy: Strategy instance to register
            initial_weight: Initial allocation weight (None = equal weight)
        """
        self.strategies[strategy.name] = strategy

        # Initialize allocation
        if initial_weight is None:
            # Equal weight allocation
            initial_weight = 1.0 / max(len(self.strategies), 1)

        self.allocations[strategy.name] = StrategyAllocation(
            strategy_name=strategy.name,
            weight=initial_weight,
            enabled=True,
            performance_score=0.0,
            market_suitability=0.5  # Neutral
        )

        # Initialize performance tracking
        self.performance_history[strategy.name] = []

        print(f"✓ Registered strategy: {strategy.name} (weight: {initial_weight:.1%})")

    def detect_market_regime(self, dataframe: pd.DataFrame, pair: str = "BTC/USDT") -> MarketRegime:
        """
        Detect current market regime using technical indicators and AI.

        Market regimes:
        - trending_up: Strong uptrend (use trend-following)
        - trending_down: Strong downtrend (avoid or use shorts)
        - ranging: Sideways movement (use mean reversion)
        - volatile: High volatility, no clear direction (use grid trading)
        - uncertain: Mixed signals

        Args:
            dataframe: OHLCV data with indicators
            pair: Trading pair

        Returns:
            MarketRegime indicating detected regime
        """
        # Calculate regime indicators
        indicators = {}

        # Trend strength (ADX)
        if 'adx' in dataframe.columns:
            indicators['adx'] = dataframe['adx'].iloc[-1]
        else:
            indicators['adx'] = 0

        # Trend direction (EMA slope)
        if 'ema_fast' in dataframe.columns and 'ema_slow' in dataframe.columns:
            ema_fast = dataframe['ema_fast'].iloc[-1]
            ema_slow = dataframe['ema_slow'].iloc[-1]
            ema_diff_pct = (ema_fast - ema_slow) / ema_slow
            indicators['ema_diff_pct'] = ema_diff_pct
        else:
            indicators['ema_diff_pct'] = 0

        # Volatility (ATR%)
        if 'atr' in dataframe.columns:
            atr_pct = dataframe['atr'].iloc[-1] / dataframe['close'].iloc[-1]
            indicators['atr_pct'] = atr_pct
        else:
            indicators['atr_pct'] = 0

        # Range vs. trend (BB width)
        if 'bb_width' in dataframe.columns:
            indicators['bb_width'] = dataframe['bb_width'].iloc[-1]
        else:
            indicators['bb_width'] = 0

        # RSI (overbought/oversold)
        if 'rsi' in dataframe.columns:
            indicators['rsi'] = dataframe['rsi'].iloc[-1]
        else:
            indicators['rsi'] = 50

        # Determine regime based on indicators
        adx = indicators.get('adx', 0)
        ema_diff = indicators.get('ema_diff_pct', 0)
        atr_pct = indicators.get('atr_pct', 0)
        bb_width = indicators.get('bb_width', 0)

        # Decision logic
        if adx > 25 and abs(ema_diff) > 0.03:
            # Strong trend
            if ema_diff > 0:
                regime_type = 'trending_up'
                confidence = min(0.9, adx / 40)
            else:
                regime_type = 'trending_down'
                confidence = min(0.9, adx / 40)

        elif atr_pct > 0.025 and bb_width > 0.04:
            # High volatility, wide range
            regime_type = 'volatile'
            confidence = min(0.85, atr_pct / 0.05)

        elif adx < 20 and abs(ema_diff) < 0.02:
            # Low trend strength, ranging
            regime_type = 'ranging'
            confidence = 0.7

        else:
            # Uncertain
            regime_type = 'uncertain'
            confidence = 0.4

        # AI enhancement (optional)
        if self.use_ai_regime_detection and self.orchestrator:
            try:
                ai_signal = self.orchestrator.generate_signal(pair, dataframe)

                # Adjust confidence based on AI
                if ai_signal.direction.lower() == 'long' and regime_type == 'trending_up':
                    confidence = min(1.0, confidence * 1.2)
                elif ai_signal.direction.lower() == 'short' and regime_type == 'trending_down':
                    confidence = min(1.0, confidence * 1.2)
                elif ai_signal.direction.lower() == 'neutral' and regime_type == 'ranging':
                    confidence = min(1.0, confidence * 1.15)

            except Exception as e:
                print(f"Warning: AI regime detection failed: {e}")

        regime = MarketRegime(
            regime_type=regime_type,
            confidence=confidence,
            indicators=indicators,
            timestamp=datetime.now()
        )

        self.current_regime = regime
        return regime

    def calculate_strategy_suitability(
        self,
        strategy_name: str,
        market_regime: MarketRegime
    ) -> float:
        """
        Calculate how suitable a strategy is for the current market regime.

        Args:
            strategy_name: Name of the strategy
            market_regime: Current market regime

        Returns:
            Suitability score 0.0 to 1.0
        """
        regime_type = market_regime.regime_type

        # Suitability matrix
        suitability_map = {
            'AIEnhancedStrategy': {
                'trending_up': 0.9,
                'trending_down': 0.3,  # Spot trading, no shorts
                'ranging': 0.4,
                'volatile': 0.5,
                'uncertain': 0.6
            },
            'MeanReversion': {
                'trending_up': 0.3,
                'trending_down': 0.3,
                'ranging': 0.9,
                'volatile': 0.6,
                'uncertain': 0.5
            },
            'GridTrading': {
                'trending_up': 0.4,
                'trending_down': 0.4,
                'ranging': 0.7,
                'volatile': 0.9,
                'uncertain': 0.5
            }
        }

        base_suitability = suitability_map.get(strategy_name, {}).get(regime_type, 0.5)

        # Adjust by regime confidence
        adjusted_suitability = base_suitability * market_regime.confidence

        return adjusted_suitability

    def allocate_capital(self, market_regime: MarketRegime) -> Dict[str, StrategyAllocation]:
        """
        Allocate capital across strategies based on market regime and allocation method.

        Args:
            market_regime: Current market regime

        Returns:
            Dictionary of strategy allocations
        """
        if self.allocation_method == "equal":
            return self._allocate_equal()
        elif self.allocation_method == "performance":
            return self._allocate_by_performance()
        elif self.allocation_method == "market_adaptive":
            return self._allocate_market_adaptive(market_regime)
        elif self.allocation_method == "ai_driven":
            return self._allocate_ai_driven(market_regime)
        else:
            raise ValueError(f"Unknown allocation method: {self.allocation_method}")

    def _allocate_equal(self) -> Dict[str, StrategyAllocation]:
        """Equal weight allocation"""
        num_enabled = sum(1 for alloc in self.allocations.values() if alloc.enabled)
        equal_weight = 1.0 / max(num_enabled, 1)

        for alloc in self.allocations.values():
            if alloc.enabled:
                alloc.weight = equal_weight
            else:
                alloc.weight = 0.0

        return self.allocations

    def _allocate_by_performance(self) -> Dict[str, StrategyAllocation]:
        """Allocate based on recent performance"""
        # Calculate performance scores
        total_score = 0.0

        for strategy_name, alloc in self.allocations.items():
            if not alloc.enabled:
                continue

            # Use recent performance (last 10 trades)
            recent_returns = self.performance_history.get(strategy_name, [])[-10:]
            if recent_returns:
                avg_return = np.mean(recent_returns)
                # Normalize to positive (shift by worst return + buffer)
                alloc.performance_score = max(0.1, avg_return + 0.05)
            else:
                alloc.performance_score = 0.5  # Neutral for new strategies

            total_score += alloc.performance_score

        # Allocate proportionally to performance
        for alloc in self.allocations.values():
            if alloc.enabled and total_score > 0:
                raw_weight = alloc.performance_score / total_score
                # Apply min/max constraints
                alloc.weight = np.clip(raw_weight, self.min_strategy_allocation, self.max_strategy_allocation)
            else:
                alloc.weight = 0.0

        # Normalize to sum to 1.0
        total_weight = sum(alloc.weight for alloc in self.allocations.values())
        if total_weight > 0:
            for alloc in self.allocations.values():
                alloc.weight /= total_weight

        return self.allocations

    def _allocate_market_adaptive(self, market_regime: MarketRegime) -> Dict[str, StrategyAllocation]:
        """Allocate based on market regime suitability"""
        total_suitability = 0.0

        for strategy_name, alloc in self.allocations.items():
            if not alloc.enabled:
                continue

            # Calculate suitability
            suitability = self.calculate_strategy_suitability(strategy_name, market_regime)
            alloc.market_suitability = suitability
            total_suitability += suitability

        # Allocate proportionally to suitability
        for alloc in self.allocations.values():
            if alloc.enabled and total_suitability > 0:
                raw_weight = alloc.market_suitability / total_suitability
                alloc.weight = np.clip(raw_weight, self.min_strategy_allocation, self.max_strategy_allocation)
            else:
                alloc.weight = 0.0

        # Normalize
        total_weight = sum(alloc.weight for alloc in self.allocations.values())
        if total_weight > 0:
            for alloc in self.allocations.values():
                alloc.weight /= total_weight

        return self.allocations

    def _allocate_ai_driven(self, market_regime: MarketRegime) -> Dict[str, StrategyAllocation]:
        """Allocate using AI recommendations (placeholder for future)"""
        # For now, combine market-adaptive and performance
        # In future, this could use AI to predict optimal allocation

        # Get market-adaptive allocation
        market_alloc = self._allocate_market_adaptive(market_regime)

        # Adjust by performance
        for strategy_name, alloc in market_alloc.items():
            recent_returns = self.performance_history.get(strategy_name, [])[-10:]
            if recent_returns:
                avg_return = np.mean(recent_returns)
                # Boost good performers, reduce poor performers
                performance_multiplier = 1.0 + (avg_return * 2.0)  # ±20% adjustment
                alloc.weight *= np.clip(performance_multiplier, 0.5, 1.5)

        # Normalize
        total_weight = sum(alloc.weight for alloc in market_alloc.values())
        if total_weight > 0:
            for alloc in market_alloc.values():
                alloc.weight /= total_weight

        return market_alloc

    def should_rebalance(self) -> bool:
        """
        Check if portfolio should be rebalanced.

        Returns:
            True if rebalance needed
        """
        if self.last_rebalance is None:
            return True

        time_since_rebalance = datetime.now() - self.last_rebalance
        return time_since_rebalance > timedelta(hours=self.rebalance_frequency_hours)

    def rebalance_portfolio(self, dataframe: pd.DataFrame, pair: str = "BTC/USDT") -> Dict[str, StrategyAllocation]:
        """
        Rebalance portfolio based on current market conditions.

        Args:
            dataframe: OHLCV data with indicators
            pair: Trading pair

        Returns:
            Updated strategy allocations
        """
        # Detect market regime
        market_regime = self.detect_market_regime(dataframe, pair)

        print(f"\n🔄 Portfolio Rebalance")
        print(f"  Market Regime: {market_regime.regime_type} (confidence: {market_regime.confidence:.1%})")
        print(f"  Indicators: ADX={market_regime.indicators.get('adx', 0):.1f}, "
              f"ATR={market_regime.indicators.get('atr_pct', 0):.2%}")

        # Allocate capital
        allocations = self.allocate_capital(market_regime)

        # Log allocations
        print(f"  Capital Allocation ({self.allocation_method}):")
        for strategy_name, alloc in allocations.items():
            if alloc.enabled:
                capital = self.total_capital * alloc.weight
                print(f"    {strategy_name}: {alloc.weight:.1%} (${capital:.2f}) "
                      f"- Suitability: {alloc.market_suitability:.1%}")

        self.last_rebalance = datetime.now()
        return allocations

    def get_strategy_capital(self, strategy_name: str) -> float:
        """
        Get allocated capital for a strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Allocated capital amount
        """
        alloc = self.allocations.get(strategy_name)
        if alloc and alloc.enabled:
            return self.total_capital * alloc.weight
        return 0.0

    def update_strategy_performance(self, strategy_name: str, return_pct: float) -> None:
        """
        Update performance history for a strategy.

        Args:
            strategy_name: Name of the strategy
            return_pct: Return percentage (e.g., 0.05 = 5%)
        """
        if strategy_name not in self.performance_history:
            self.performance_history[strategy_name] = []

        self.performance_history[strategy_name].append(return_pct)

        # Keep only recent history (last 50 trades)
        self.performance_history[strategy_name] = self.performance_history[strategy_name][-50:]

    def get_portfolio_summary(self) -> Dict:
        """
        Get summary of current portfolio state.

        Returns:
            Dictionary with portfolio metrics
        """
        total_allocated = sum(alloc.weight for alloc in self.allocations.values() if alloc.enabled)

        summary = {
            'total_capital': self.total_capital,
            'allocation_method': self.allocation_method,
            'last_rebalance': self.last_rebalance,
            'current_regime': self.current_regime.regime_type if self.current_regime else 'unknown',
            'regime_confidence': self.current_regime.confidence if self.current_regime else 0.0,
            'strategies': {
                name: {
                    'weight': alloc.weight,
                    'capital': self.total_capital * alloc.weight,
                    'enabled': alloc.enabled,
                    'performance_score': alloc.performance_score,
                    'market_suitability': alloc.market_suitability
                }
                for name, alloc in self.allocations.items()
            },
            'total_allocated_pct': total_allocated
        }

        return summary

    def __repr__(self) -> str:
        num_strategies = len(self.strategies)
        num_enabled = sum(1 for alloc in self.allocations.values() if alloc.enabled)

        return (
            f"PortfolioManager("
            f"capital=${self.total_capital:.2f}, "
            f"strategies={num_enabled}/{num_strategies}, "
            f"method={self.allocation_method})"
        )
