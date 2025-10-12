# Advanced AI Trading Strategies

**Last Updated**: 2025-10-12
**Status**: Roadmap Phase 4-10
**Prerequisites**: Phase 1-3 Complete (Multi-LLM + ML Ensemble)

---

## 📋 Overview

This document outlines advanced AI-driven trading strategies for the Proratio system. These strategies leverage the existing multi-LLM consensus (ChatGPT, Claude, Gemini) and ML ensemble (LSTM + LightGBM + XGBoost) to create sophisticated, intelligent trading systems.

**Current Capabilities (Phase 1-3)**:
- ✅ Multi-LLM consensus signal generation
- ✅ ML ensemble predictions (LSTM + LightGBM + XGBoost)
- ✅ Three base strategies (Trend Following, Mean Reversion, Grid Trading)
- ✅ Portfolio manager with market regime detection
- ✅ Risk management and position sizing

**Target Capabilities (Phase 4-10)**:
- 🎯 Multi-timeframe AI analysis
- 🎯 Enhanced regime detection with AI
- 🎯 Dynamic risk management with AI
- 🎯 Cross-asset correlation analysis
- 🎯 News event-driven trading
- 🎯 AI-generated trading plans
- 🎯 **Hybrid ML+LLM system** (Highest priority)

---

## 🚀 Phase 4: Multi-Timeframe LLM Analysis

### Concept
Use LLMs to analyze multiple timeframes simultaneously (1h, 4h, 1d, 1w) and detect conflicting/confirming signals across different time horizons.

### Why This Works
- **Pattern Recognition**: LLMs excel at identifying patterns across different scales
- **Reduced False Signals**: Single-timeframe analysis often produces whipsaws
- **Specialized Analysis**:
  - ChatGPT → Technical pattern recognition
  - Claude → Risk assessment and divergence detection
  - Gemini → Sentiment and market structure

### Implementation

```python
# proratio_signals/multi_timeframe_analyzer.py

from typing import Dict, List
from dataclasses import dataclass

@dataclass
class TimeframeAnalysis:
    """Analysis result for a single timeframe"""
    timeframe: str  # '1h', '4h', '1d', '1w'
    direction: str  # 'bullish', 'bearish', 'neutral'
    confidence: float  # 0.0 - 1.0
    key_patterns: List[str]
    reasoning: str

@dataclass
class MultiTimeframeSignal:
    """Combined signal from multiple timeframes"""
    alignment_score: float  # 0-100%, how aligned are timeframes
    dominant_trend: str  # 'bullish', 'bearish', 'neutral', 'mixed'
    timeframe_analyses: Dict[str, TimeframeAnalysis]
    divergences: List[str]  # e.g., "1h bearish divergence on RSI"
    final_confidence: float
    recommended_action: str  # 'enter_long', 'enter_short', 'wait', 'exit'

class MultiTimeframeAnalyzer:
    """
    Uses LLMs to analyze multiple timeframes simultaneously
    Detects divergences and confirms trends across timeframes
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.timeframes = ['1h', '4h', '1d', '1w']

    def analyze_all_timeframes(self, pair: str) -> MultiTimeframeSignal:
        """
        Analyze all timeframes and generate consensus signal

        Returns MultiTimeframeSignal with:
        - Individual timeframe analyses
        - Alignment score (% agreement across timeframes)
        - Divergences (where timeframes conflict)
        - Final recommended action
        """
        analyses = {}

        for tf in self.timeframes:
            # Get OHLCV data for this timeframe
            data = self.get_ohlcv_data(pair, tf)

            # Query LLMs for this specific timeframe
            prompt = self._create_timeframe_prompt(tf, data)
            llm_response = self.orchestrator.analyze_market(pair, prompt)

            analyses[tf] = TimeframeAnalysis(
                timeframe=tf,
                direction=llm_response['direction'],
                confidence=llm_response['confidence'],
                key_patterns=llm_response.get('patterns', []),
                reasoning=llm_response['reasoning']
            )

        # Calculate alignment
        alignment_score = self._calculate_alignment(analyses)
        divergences = self._detect_divergences(analyses)
        dominant_trend = self._determine_dominant_trend(analyses)

        # Generate final signal
        return MultiTimeframeSignal(
            alignment_score=alignment_score,
            dominant_trend=dominant_trend,
            timeframe_analyses=analyses,
            divergences=divergences,
            final_confidence=self._calculate_final_confidence(analyses, alignment_score),
            recommended_action=self._get_recommended_action(dominant_trend, alignment_score)
        )

    def _create_timeframe_prompt(self, timeframe: str, data) -> str:
        """Create specialized prompt for each timeframe"""
        prompts = {
            '1h': "Analyze short-term momentum and intraday patterns. Focus on immediate entry/exit signals.",
            '4h': "Analyze intraday trend and swing trading opportunities. Focus on 2-7 day position holding.",
            '1d': "Analyze daily trend and medium-term market structure. Focus on 1-4 week positions.",
            '1w': "Analyze long-term bias and major market cycles. Focus on macro trend direction."
        }
        return prompts[timeframe]

    def _calculate_alignment(self, analyses: Dict[str, TimeframeAnalysis]) -> float:
        """Calculate % alignment across timeframes"""
        directions = [a.direction for a in analyses.values()]
        bullish_count = directions.count('bullish')
        bearish_count = directions.count('bearish')
        total = len(directions)

        max_alignment = max(bullish_count, bearish_count)
        return (max_alignment / total) * 100

    def _detect_divergences(self, analyses: Dict[str, TimeframeAnalysis]) -> List[str]:
        """Identify conflicting signals between timeframes"""
        divergences = []

        # Check for higher TF bearish while lower TF bullish
        if analyses['1w'].direction == 'bearish' and analyses['1h'].direction == 'bullish':
            divergences.append("⚠️ Short-term bullish against long-term bearish trend")

        # Check for lower TF divergence
        if analyses['1h'].direction != analyses['4h'].direction:
            divergences.append(f"⚠️ 1h {analyses['1h'].direction} vs 4h {analyses['4h'].direction}")

        return divergences

    def _determine_dominant_trend(self, analyses: Dict[str, TimeframeAnalysis]) -> str:
        """Determine overall market direction with weighting"""
        # Weight higher timeframes more heavily
        weights = {'1w': 0.4, '1d': 0.3, '4h': 0.2, '1h': 0.1}

        bullish_score = sum(
            weights[tf] * (1 if a.direction == 'bullish' else 0)
            for tf, a in analyses.items()
        )
        bearish_score = sum(
            weights[tf] * (1 if a.direction == 'bearish' else 0)
            for tf, a in analyses.items()
        )

        if bullish_score > 0.6:
            return 'bullish'
        elif bearish_score > 0.6:
            return 'bearish'
        elif bullish_score > 0.4 or bearish_score > 0.4:
            return 'neutral'
        else:
            return 'mixed'
```

### Trading Rules

**Entry Conditions:**
1. Alignment score > 75% → High confidence entry
2. Alignment score 60-75% + dominant trend → Medium confidence entry
3. Alignment score < 60% → Wait for clarity

**Position Sizing:**
- 75-100% alignment → Full position (1.0x base)
- 60-75% alignment → Reduced position (0.7x base)
- < 60% alignment → Skip trade

**Exit Conditions:**
1. Higher timeframe (1d, 1w) reverses → Exit full position
2. Lower timeframe (1h, 4h) reverses → Scale out 50%
3. Divergence appears → Move stop to breakeven

### Backtest Metrics to Target
- **Win rate improvement**: +10-15% vs single timeframe
- **False signal reduction**: 30-40%
- **Sharpe ratio**: > 1.8

---

## 🎯 Phase 5: AI-Enhanced Regime Detection

### Concept
Enhance your existing portfolio manager's regime detection by using LLMs to classify markets into 8 nuanced regimes instead of just 3 (trending/ranging/volatile).

### Current vs Enhanced

**Current (Technical Indicators Only)**:
- Trending (ADX > 25)
- Ranging (ADX < 25, low volatility)
- Volatile (high ATR)

**Enhanced with AI (8 Regimes)**:
1. **Strong Bull Trend** - Clear uptrend, high volume, strong momentum
2. **Weak Bull Trend** - Uptrend but with hesitation, lower volume
3. **Bull Range-bound** - Sideways but with bullish bias
4. **Bear Range-bound** - Sideways but with bearish undertone
5. **Weak Bear Trend** - Downtrend but with potential reversal signals
6. **Strong Bear Trend** - Clear downtrend, panic selling
7. **High Volatility Expansion** - Sharp price swings, uncertainty
8. **Low Volatility Compression** - Tight range, coiling for breakout

### Implementation

```python
# proratio_signals/ai_regime_classifier.py

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional

class MarketRegime(Enum):
    """8 distinct market regimes"""
    STRONG_BULL = "strong_bull"
    WEAK_BULL = "weak_bull"
    BULL_RANGE = "bull_range"
    BEAR_RANGE = "bear_range"
    WEAK_BEAR = "weak_bear"
    STRONG_BEAR = "strong_bear"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"

@dataclass
class RegimeClassification:
    """Result of regime classification"""
    regime: MarketRegime
    confidence: float  # 0.0 - 1.0
    probability_distribution: Dict[MarketRegime, float]
    reasoning: str
    recommended_strategy: str
    risk_level: str  # 'low', 'medium', 'high'

class AIRegimeClassifier:
    """
    Uses LLMs to classify market regimes with nuanced understanding
    Combines technical indicators with AI pattern recognition
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def classify_regime(
        self,
        pair: str,
        ohlcv_data,
        news_context: Optional[str] = None
    ) -> RegimeClassification:
        """
        Classify current market regime using AI

        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            ohlcv_data: Last 30 days of price data
            news_context: Optional recent news/sentiment

        Returns:
            RegimeClassification with regime type and confidence
        """

        # Prepare analysis prompt for LLMs
        prompt = self._create_regime_prompt(ohlcv_data, news_context)

        # Get LLM consensus
        llm_response = self.orchestrator.analyze_market(pair, prompt)

        # Parse regime classification
        regime = self._parse_regime(llm_response['regime'])
        probabilities = self._extract_probabilities(llm_response)

        # Map regime to recommended strategy
        strategy = self._map_regime_to_strategy(regime)
        risk_level = self._assess_risk_level(regime, probabilities)

        return RegimeClassification(
            regime=regime,
            confidence=llm_response['confidence'],
            probability_distribution=probabilities,
            reasoning=llm_response['reasoning'],
            recommended_strategy=strategy,
            risk_level=risk_level
        )

    def _create_regime_prompt(self, ohlcv_data, news_context) -> str:
        """Create prompt for regime classification"""
        prompt = f"""
Analyze the following market data and classify into one of 8 regimes:

Price Action (Last 30 days):
- High: {ohlcv_data['high'].max()}
- Low: {ohlcv_data['low'].min()}
- Current: {ohlcv_data['close'].iloc[-1]}
- 30d Change: {((ohlcv_data['close'].iloc[-1] / ohlcv_data['close'].iloc[0]) - 1) * 100:.2f}%

Volume Profile:
- Avg Volume: {ohlcv_data['volume'].mean():.2f}
- Recent Volume Trend: {self._analyze_volume_trend(ohlcv_data)}

Technical Indicators:
- RSI: {self._calculate_rsi(ohlcv_data)}
- ADX: {self._calculate_adx(ohlcv_data)}
- ATR: {self._calculate_atr(ohlcv_data)}

{f"Recent News: {news_context}" if news_context else ""}

Classify into one of these 8 regimes:
1. Strong Bull Trend - Clear uptrend, high volume, strong momentum
2. Weak Bull Trend - Uptrend with hesitation, lower volume
3. Bull Range-bound - Sideways with bullish bias
4. Bear Range-bound - Sideways with bearish undertone
5. Weak Bear Trend - Downtrend with potential reversal
6. Strong Bear Trend - Clear downtrend, panic
7. High Volatility Expansion - Sharp swings
8. Low Volatility Compression - Tight range

Provide:
- Regime classification
- Confidence (0-1)
- Reasoning
- Probability distribution across all 8 regimes
"""
        return prompt

    def _map_regime_to_strategy(self, regime: MarketRegime) -> str:
        """Map regime to best trading strategy"""
        strategy_map = {
            MarketRegime.STRONG_BULL: "AIEnhancedTrendFollowing",
            MarketRegime.WEAK_BULL: "AIEnhancedTrendFollowing",
            MarketRegime.BULL_RANGE: "MeanReversionStrategy",
            MarketRegime.BEAR_RANGE: "MeanReversionStrategy",
            MarketRegime.WEAK_BEAR: "AIEnhancedTrendFollowing (Short)",
            MarketRegime.STRONG_BEAR: "CashOrShort",
            MarketRegime.HIGH_VOLATILITY: "GridTradingStrategy (Wide)",
            MarketRegime.LOW_VOLATILITY: "GridTradingStrategy (Tight) or Wait"
        }
        return strategy_map[regime]

    def _assess_risk_level(self, regime: MarketRegime, probabilities: Dict) -> str:
        """Assess overall risk level of current market"""
        high_risk_regimes = [
            MarketRegime.STRONG_BEAR,
            MarketRegime.HIGH_VOLATILITY
        ]

        if regime in high_risk_regimes:
            return 'high'

        # If regime classification is uncertain (probabilities spread)
        max_prob = max(probabilities.values())
        if max_prob < 0.5:
            return 'medium'

        return 'low'
```

### Integration with Portfolio Manager

```python
# proratio_tradehub/orchestration/portfolio_manager.py

def allocate_capital_ai_regime(self, pair: str, ohlcv_data) -> Dict[str, float]:
    """
    Allocate capital based on AI regime classification
    """
    # Get AI regime classification
    regime_result = self.regime_classifier.classify_regime(pair, ohlcv_data)

    # Adjust strategy allocations based on regime
    if regime_result.regime == MarketRegime.STRONG_BULL:
        return {
            'AIEnhancedTrendFollowing': 0.80,
            'MeanReversionStrategy': 0.15,
            'GridTradingStrategy': 0.05
        }
    elif regime_result.regime in [MarketRegime.BULL_RANGE, MarketRegime.BEAR_RANGE]:
        return {
            'MeanReversionStrategy': 0.70,
            'GridTradingStrategy': 0.25,
            'AIEnhancedTrendFollowing': 0.05
        }
    elif regime_result.risk_level == 'high':
        return {
            'Cash': 0.60,  # Reduce exposure
            'MeanReversionStrategy': 0.30,
            'GridTradingStrategy': 0.10
        }
    # ... etc
```

### Expected Performance
- **Better regime identification**: 25-35% improvement vs technical-only
- **Reduced whipsaws**: 40-50% fewer false regime changes
- **Capital efficiency**: 15-20% better capital allocation

---

## 🛡️ Phase 6: AI-Driven Dynamic Risk Management

### Concept
Instead of fixed percentage stop losses (e.g., -5%), use LLMs to identify logical support/resistance levels for smarter stop placement.

### Problem with Fixed % Stops
- Arbitrary levels (why 5%, not 4.8%?)
- Market makers hunt common stop levels
- Ignores market structure
- Poor risk/reward ratios

### AI-Enhanced Solution
LLMs analyze chart and identify:
- Recent swing lows/highs
- Key support/resistance zones
- Volume profile nodes
- Psychological levels ($30k, $35k, etc.)
- Fibonacci retracements

### Implementation

```python
# proratio_tradehub/risk/ai_dynamic_risk.py

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class PriceLevel:
    """Identified support/resistance level"""
    price: float
    level_type: str  # 'support', 'resistance', 'psychological'
    strength: float  # 0.0-1.0, how strong is this level
    touches: int  # how many times price tested this level
    reasoning: str

@dataclass
class DynamicRiskLevels:
    """AI-generated risk management levels"""
    entry_price: float
    stop_loss: float
    take_profit_levels: List[float]  # Multiple TPs
    risk_reward_ratio: float
    stop_reasoning: str
    tp_reasoning: str

class AIDynamicRiskManager:
    """
    Uses LLMs to determine dynamic stop loss and take profit levels
    based on market structure, not arbitrary percentages
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def get_dynamic_levels(
        self,
        pair: str,
        entry_price: float,
        direction: str,  # 'long' or 'short'
        ohlcv_data,
        max_risk_pct: float = 0.05  # 5% max risk
    ) -> DynamicRiskLevels:
        """
        Get AI-generated stop loss and take profit levels

        Args:
            pair: Trading pair
            entry_price: Planned entry price
            direction: 'long' or 'short'
            ohlcv_data: Recent price history
            max_risk_pct: Maximum acceptable risk %

        Returns:
            DynamicRiskLevels with stop and target prices
        """

        # Identify support/resistance levels using AI
        key_levels = self._identify_key_levels(pair, ohlcv_data, direction)

        # Find appropriate stop loss level
        stop_loss = self._find_optimal_stop(
            entry_price,
            direction,
            key_levels,
            max_risk_pct
        )

        # Find take profit levels (multiple targets)
        take_profits = self._find_take_profit_levels(
            entry_price,
            direction,
            key_levels
        )

        # Calculate risk/reward
        risk = abs(entry_price - stop_loss) / entry_price
        reward = abs(take_profits[0] - entry_price) / entry_price
        risk_reward = reward / risk if risk > 0 else 0

        return DynamicRiskLevels(
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_levels=take_profits,
            risk_reward_ratio=risk_reward,
            stop_reasoning=self._explain_stop_placement(stop_loss, key_levels),
            tp_reasoning=self._explain_tp_placement(take_profits, key_levels)
        )

    def _identify_key_levels(
        self,
        pair: str,
        ohlcv_data,
        direction: str
    ) -> List[PriceLevel]:
        """
        Use LLMs to identify key price levels
        """
        prompt = f"""
Analyze the following price chart for {pair} and identify key levels:

Price Range (Last 60 days):
- High: {ohlcv_data['high'].max()}
- Low: {ohlcv_data['low'].min()}
- Current: {ohlcv_data['close'].iloc[-1]}

Recent Swing Points:
{self._format_swing_points(ohlcv_data)}

Trading Direction: {direction}

Identify:
1. Strong support levels (if going long, for stop loss placement)
2. Strong resistance levels (if going long, for take profit)
3. Psychological levels (round numbers like $30k, $35k)
4. Volume-weighted levels (high volume nodes)

For each level, provide:
- Price
- Type (support/resistance/psychological)
- Strength (0-1)
- Number of touches
- Reasoning
"""

        llm_response = self.orchestrator.analyze_market(pair, prompt)
        return self._parse_levels(llm_response)

    def _find_optimal_stop(
        self,
        entry_price: float,
        direction: str,
        key_levels: List[PriceLevel],
        max_risk_pct: float
    ) -> float:
        """
        Find optimal stop loss level

        Rules:
        1. Place stop below nearest strong support (long) or above resistance (short)
        2. Ensure stop is within max_risk_pct
        3. Prefer levels with high touch count (stronger support)
        """

        if direction == 'long':
            # Find support levels below entry
            supports = [
                level for level in key_levels
                if level.level_type == 'support' and level.price < entry_price
            ]
            supports.sort(key=lambda x: x.price, reverse=True)  # Nearest first

            # Find nearest strong support within risk tolerance
            for support in supports:
                risk = (entry_price - support.price) / entry_price
                if risk <= max_risk_pct and support.strength > 0.6:
                    return support.price * 0.998  # Slightly below support

            # Fallback: use max_risk_pct
            return entry_price * (1 - max_risk_pct)

        else:  # short
            # Find resistance levels above entry
            resistances = [
                level for level in key_levels
                if level.level_type == 'resistance' and level.price > entry_price
            ]
            resistances.sort(key=lambda x: x.price)  # Nearest first

            for resistance in resistances:
                risk = (resistance.price - entry_price) / entry_price
                if risk <= max_risk_pct and resistance.strength > 0.6:
                    return resistance.price * 1.002  # Slightly above resistance

            # Fallback
            return entry_price * (1 + max_risk_pct)

    def _find_take_profit_levels(
        self,
        entry_price: float,
        direction: str,
        key_levels: List[PriceLevel]
    ) -> List[float]:
        """
        Find multiple take profit levels

        Returns 3 take profit targets:
        TP1: Nearest resistance/support (70% position)
        TP2: Next level (20% position)
        TP3: Extended target (10% position, runner)
        """

        if direction == 'long':
            # Find resistance levels above entry
            resistances = [
                level for level in key_levels
                if level.level_type == 'resistance' and level.price > entry_price
            ]
            resistances.sort(key=lambda x: x.price)

            if len(resistances) >= 3:
                return [
                    resistances[0].price * 0.998,  # TP1: Just before first resistance
                    resistances[1].price * 0.998,  # TP2: Second resistance
                    resistances[2].price * 0.998   # TP3: Third resistance
                ]
            elif len(resistances) == 2:
                return [
                    resistances[0].price * 0.998,
                    resistances[1].price * 0.998,
                    resistances[1].price * 1.05   # Extended target
                ]
            else:
                # Fallback: use R multiples
                r = abs(entry_price - self._find_optimal_stop(entry_price, direction, key_levels, 0.05))
                return [
                    entry_price + (r * 2),  # 2R
                    entry_price + (r * 3),  # 3R
                    entry_price + (r * 5)   # 5R
                ]

        else:  # short - similar logic but inverted
            supports = [
                level for level in key_levels
                if level.level_type == 'support' and level.price < entry_price
            ]
            supports.sort(key=lambda x: x.price, reverse=True)

            if len(supports) >= 3:
                return [s.price * 1.002 for s in supports[:3]]
            # ... similar fallback logic
```

### Trading Workflow with Dynamic Stops

```python
# In your strategy entry logic:

def enter_trade(self, pair, direction, current_price, ohlcv_data):
    """Enter trade with AI-generated risk levels"""

    # Get dynamic risk levels from AI
    risk_levels = self.ai_risk_manager.get_dynamic_levels(
        pair=pair,
        entry_price=current_price,
        direction=direction,
        ohlcv_data=ohlcv_data
    )

    # Validate risk/reward
    if risk_levels.risk_reward_ratio < 2.0:
        return None  # Skip trade, poor R:R

    # Calculate position size based on stop distance
    stop_distance = abs(current_price - risk_levels.stop_loss)
    position_size = self.calculate_position_size(
        risk_per_trade=0.02,  # 2% account risk
        stop_distance=stop_distance
    )

    # Execute trade with multiple TPs
    order = {
        'pair': pair,
        'direction': direction,
        'entry': current_price,
        'size': position_size,
        'stop_loss': risk_levels.stop_loss,
        'take_profits': [
            {'price': risk_levels.take_profit_levels[0], 'size': position_size * 0.7},
            {'price': risk_levels.take_profit_levels[1], 'size': position_size * 0.2},
            {'price': risk_levels.take_profit_levels[2], 'size': position_size * 0.1}
        ]
    }

    return order
```

### Expected Benefits
- **Better stop placement**: 30-40% fewer stop-outs
- **Improved R:R**: Average 2.5:1 vs 1.5:1 with fixed %
- **Higher win rate**: 10-15% improvement
- **Professional execution**: Stops at logical levels like institutions

---

## 🔗 Phase 7: Multi-Asset Correlation Analysis

### Concept
Use LLMs to analyze relationships between BTC, ETH, and altcoins to identify leading indicators and divergences.

### Why This Matters
- BTC often leads altcoin movements
- ETH/BTC ratio signals market phases
- Divergences reveal market structure changes
- Correlation breakdowns = opportunity or danger

### Implementation

```python
# proratio_signals/correlation_analyzer.py

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class CorrelationSignal:
    """Cross-asset correlation analysis"""
    market_phase: str  # 'risk_on', 'risk_off', 'rotation', 'uncertain'
    leading_asset: str  # Which asset is leading
    divergences: List[str]  # Notable divergences
    trade_recommendations: Dict[str, str]  # pair -> action
    confidence: float
    reasoning: str

class AICorrelationAnalyzer:
    """
    Analyzes cross-asset relationships using LLM pattern recognition
    """

    def analyze_cross_asset_signals(
        self,
        assets: List[str] = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'MATIC/USDT']
    ) -> CorrelationSignal:
        """
        Analyze relationships between multiple crypto assets
        """

        # Get recent performance for all assets
        performance = {}
        for asset in assets:
            data = self.get_ohlcv_data(asset, timeframe='1d', limit=30)
            performance[asset] = {
                '1d': self._calculate_change(data, days=1),
                '7d': self._calculate_change(data, days=7),
                '30d': self._calculate_change(data, days=30),
                'volume_trend': self._analyze_volume(data)
            }

        # Create correlation analysis prompt
        prompt = self._create_correlation_prompt(performance)

        # Get LLM analysis
        llm_response = self.orchestrator.analyze_market('CORRELATION', prompt)

        # Parse response
        return CorrelationSignal(
            market_phase=llm_response['market_phase'],
            leading_asset=llm_response['leading_asset'],
            divergences=llm_response['divergences'],
            trade_recommendations=llm_response['recommendations'],
            confidence=llm_response['confidence'],
            reasoning=llm_response['reasoning']
        )

    def _create_correlation_prompt(self, performance: Dict) -> str:
        """Create prompt for correlation analysis"""
        prompt = f"""
Analyze the following crypto asset performance and identify market structure:

Performance (Last 1d / 7d / 30d):
"""
        for asset, perf in performance.items():
            prompt += f"\n{asset}:"
            prompt += f"\n  1d: {perf['1d']:+.2f}%"
            prompt += f"\n  7d: {perf['7d']:+.2f}%"
            prompt += f"\n  30d: {perf['30d']:+.2f}%"
            prompt += f"\n  Volume: {perf['volume_trend']}"

        prompt += """

Analyze:
1. Market Phase:
   - Risk-on: Altcoins outperforming BTC (late bull cycle)
   - Risk-off: BTC dominance increasing (bear market or correction)
   - Rotation: Capital rotating between assets
   - Uncertain: No clear pattern

2. Leading Indicator:
   - Which asset is leading? (Usually BTC leads, but sometimes ETH)
   - Is there a divergence? (e.g., BTC weak but ETH strong)

3. Trading Implications:
   - Which assets to trade?
   - Which to avoid?
   - Any rotation opportunities?

Provide:
- Market phase classification
- Leading asset identification
- Divergences (if any)
- Trading recommendations for each asset
"""
        return prompt

class CorrelationTradingStrategy:
    """
    Trading strategy based on cross-asset correlation
    """

    def generate_signals(self, correlation_signal: CorrelationSignal) -> Dict:
        """
        Generate trading signals based on correlation analysis
        """
        signals = {}

        if correlation_signal.market_phase == 'risk_on':
            # Altcoins outperforming = late bull cycle
            # Strategy: Trade strong altcoins, be cautious with new longs
            signals['BTC/USDT'] = 'HOLD'  # Don't chase
            signals['ETH/USDT'] = 'LONG'  # Usually strong in risk-on
            signals['SOL/USDT'] = 'LONG'  # Altcoins benefit
            signals['risk_level'] = 'MEDIUM'  # Late cycle = higher risk

        elif correlation_signal.market_phase == 'risk_off':
            # BTC dominance increasing = bear market
            # Strategy: Avoid altcoins, focus on BTC or cash
            signals['BTC/USDT'] = 'LONG_CAUTIOUS'
            signals['ETH/USDT'] = 'AVOID'
            signals['SOL/USDT'] = 'AVOID'
            signals['risk_level'] = 'HIGH'

        elif correlation_signal.market_phase == 'rotation':
            # Capital rotating between assets
            # Strategy: Follow the flow, trade the leader
            leading_asset = correlation_signal.leading_asset
            signals[leading_asset] = 'LONG'
            signals['risk_level'] = 'LOW'  # Rotation = healthy market

        else:  # uncertain
            signals['BTC/USDT'] = 'WAIT'
            signals['risk_level'] = 'MEDIUM'

        return signals
```

### Trading Rules

**Risk-On Mode (Altcoins Outperforming)**:
- ✅ Trade strong altcoins (ETH, SOL, etc.)
- ⚠️ Be cautious - late bull cycle
- 📊 Reduce position sizes (60-70% of normal)
- 🎯 Tighter stops (market can reverse quickly)

**Risk-Off Mode (BTC Dominance Rising)**:
- ❌ Avoid altcoins completely
- ✅ Focus on BTC only (or cash)
- 📊 Smaller positions (40-50% of normal)
- 🎯 Very tight stops

**Rotation Mode (Capital Flowing)**:
- ✅ Trade the leading asset
- ✅ Follow ETH/BTC ratio for rotation signals
- 📊 Normal position sizes
- 🎯 Standard stops

### Expected Performance
- **Better pair selection**: 25-30% improvement
- **Avoid bad setups**: 40% fewer losing trades in wrong assets
- **Timing improvement**: Enter when momentum is clear

---

## 📰 Phase 8: LLM News Event Trading

### Concept
Feed real-time crypto news to LLMs for event-driven trade decisions.

### News Sources (API Integration)
- **CryptoPanic API** (free tier: 100 requests/day)
- **NewsAPI** (crypto news articles)
- **Twitter/X API** (official crypto accounts)
- **Reddit API** (r/cryptocurrency sentiment)
- **CoinGecko API** (trending coins, social metrics)

### Implementation

```python
# proratio_signals/news_event_trader.py

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import requests

@dataclass
class NewsEvent:
    """Structured news event"""
    title: str
    source: str
    published_at: datetime
    sentiment: str  # 'bullish', 'bearish', 'neutral'
    importance: int  # 1-10 scale
    affected_assets: List[str]
    url: str

@dataclass
class NewsImpactAnalysis:
    """LLM analysis of news impact"""
    event_type: str  # 'regulatory', 'adoption', 'technical', 'macro'
    market_impact: str  # 'bullish', 'bearish', 'neutral'
    time_horizon: str  # 'immediate', 'short_term', 'long_term'
    confidence: float
    reasoning: str
    recommended_action: str  # 'buy', 'sell', 'wait', 'scale_in'
    entry_strategy: str
    risk_assessment: str

class AINewsEventTrader:
    """
    Monitors news and uses LLMs to assess trading impact
    """

    def __init__(self, orchestrator, cryptopanic_api_key: str):
        self.orchestrator = orchestrator
        self.cryptopanic_api_key = cryptopanic_api_key
        self.base_url = "https://cryptopanic.com/api/v1"

    def fetch_recent_news(
        self,
        currencies: List[str] = ['BTC', 'ETH'],
        limit: int = 20
    ) -> List[NewsEvent]:
        """
        Fetch recent crypto news from CryptoPanic
        """
        url = f"{self.base_url}/posts/"
        params = {
            'auth_token': self.cryptopanic_api_key,
            'currencies': ','.join(currencies),
            'filter': 'important',  # Only important news
            'limit': limit
        }

        response = requests.get(url, params=params)
        data = response.json()

        news_events = []
        for post in data['results']:
            news_events.append(NewsEvent(
                title=post['title'],
                source=post['source']['title'],
                published_at=datetime.fromisoformat(post['published_at'].replace('Z', '+00:00')),
                sentiment=post['votes'].get('sentiment', 'neutral'),
                importance=self._calculate_importance(post),
                affected_assets=post.get('currencies', []),
                url=post['url']
            ))

        return news_events

    def analyze_news_impact(
        self,
        news_event: NewsEvent,
        current_market_data
    ) -> NewsImpactAnalysis:
        """
        Use LLMs to analyze news event impact on trading
        """

        prompt = f"""
Analyze the following crypto news event and its trading implications:

News: {news_event.title}
Source: {news_event.source}
Sentiment: {news_event.sentiment}
Affected Assets: {', '.join(news_event.affected_assets)}

Current Market Context:
- BTC Price: {current_market_data['BTC/USDT']['price']}
- BTC 24h Change: {current_market_data['BTC/USDT']['change_24h']}%
- Market Cap: {current_market_data['market_cap']}B

Historical Pattern Analysis:
Similar news events in the past have resulted in:
{self._get_historical_patterns(news_event)}

Questions to answer:
1. Event Type: Is this regulatory, adoption, technical, or macro news?
2. Market Impact: Bullish, bearish, or neutral?
3. Time Horizon: Immediate (0-4h), short-term (1-3d), or long-term (1w+)?
4. Trading Strategy:
   - Should we enter immediately or wait?
   - If wait, what's the ideal entry zone?
   - What's the risk of FOMO vs waiting for pullback?
   - What's the expected price movement?

Provide:
- Detailed reasoning
- Recommended action (buy/sell/wait/scale_in)
- Entry strategy
- Risk level (low/medium/high)
"""

        llm_response = self.orchestrator.analyze_market('NEWS_EVENT', prompt)

        return NewsImpactAnalysis(
            event_type=llm_response['event_type'],
            market_impact=llm_response['market_impact'],
            time_horizon=llm_response['time_horizon'],
            confidence=llm_response['confidence'],
            reasoning=llm_response['reasoning'],
            recommended_action=llm_response['recommended_action'],
            entry_strategy=llm_response['entry_strategy'],
            risk_assessment=llm_response['risk_assessment']
        )

    def monitor_news_feed(self, check_interval_seconds: int = 300):
        """
        Continuously monitor news feed for trading opportunities

        Args:
            check_interval_seconds: How often to check for new news (default 5 min)
        """
        while True:
            # Fetch latest news
            news_events = self.fetch_recent_news()

            # Filter for high-importance events
            important_events = [
                event for event in news_events
                if event.importance >= 7
            ]

            for event in important_events:
                # Check if already processed
                if self._is_processed(event):
                    continue

                # Analyze impact
                market_data = self._get_current_market_data()
                analysis = self.analyze_news_impact(event, market_data)

                # Generate trading signal if high confidence
                if analysis.confidence > 0.7:
                    self._send_trading_signal(event, analysis)

                # Mark as processed
                self._mark_processed(event)

            # Wait before next check
            time.sleep(check_interval_seconds)

    def _get_historical_patterns(self, news_event: NewsEvent) -> str:
        """
        Retrieve similar historical events and their market impact
        """
        # This would query your database of historical news events
        # and their subsequent price movements
        return "ETF approval news: +10-15% within 24h, then -30-40% pullback"

class NewsBasedTradingStrategy:
    """
    Trading strategy triggered by news events
    """

    def execute_news_trade(
        self,
        news_event: NewsEvent,
        analysis: NewsImpactAnalysis
    ):
        """
        Execute trade based on news analysis
        """

        if analysis.recommended_action == 'wait':
            # Wait for pullback
            return {
                'action': 'WAIT_FOR_PULLBACK',
                'entry_zone': analysis.entry_strategy,
                'monitoring': True
            }

        elif analysis.recommended_action == 'buy':
            if analysis.time_horizon == 'immediate':
                # Enter immediately but with reduced size
                return {
                    'action': 'BUY_MARKET',
                    'position_size': 0.5,  # 50% of normal size
                    'reason': 'Immediate news impact'
                }
            else:
                # Scale in gradually
                return {
                    'action': 'SCALE_IN',
                    'entry_1': {'price': 'current', 'size': 0.3},
                    'entry_2': {'price': '-2%', 'size': 0.4},
                    'entry_3': {'price': '-5%', 'size': 0.3}
                }

        elif analysis.recommended_action == 'sell':
            # Exit positions or enter short
            return {
                'action': 'EXIT_LONGS',
                'reason': f'Bearish news: {news_event.title}'
            }
```

### Event Types to Trade

**1. Regulatory Events**
- SEC approvals/rejections
- New regulations
- Exchange bans
- *Typical impact: High volatility, 5-15% moves*

**2. Adoption News**
- Major company buying BTC
- Payment integration
- Institutional adoption
- *Typical impact: Bullish, 3-8% moves*

**3. Technical Events**
- Network upgrades
- Hard forks
- Security breaches
- *Typical impact: Variable, 2-10% moves*

**4. Macro Events**
- Fed interest rate decisions
- Inflation reports
- Global economic news
- *Typical impact: Indirect, 1-5% moves*

### Trading Rules

**Immediate Action Events (0-4h window)**:
- Enter with 50% position size
- Tight stops (2-3%)
- Quick take-profit targets (3-5%)
- Example: Exchange hack, major regulatory announcement

**Wait for Pullback Events (1-3 days)**:
- Initial spike usually retraces 30-50%
- Wait for pullback to support
- Enter with full position
- Example: ETF approval, major adoption news

**Long-term Thesis Events (1+ weeks)**:
- Scale in over multiple entries
- Wider stops (5-8%)
- Larger profit targets (15-30%)
- Example: Halving cycle, macro trends

### Expected Performance
- **Capture major moves**: 60-70% of significant news-driven rallies
- **Avoid FOMO**: 50% fewer emotional entries at tops
- **Better timing**: 30-40% better entry prices vs immediate entry

---

## 📋 Phase 9: AI-Generated Weekly Trading Plans

### Concept
Use LLMs to generate complete, structured trading plans for the week rather than reactive trade-by-trade decisions.

### Why This Works
- **Reduces emotional trading**: Pre-defined scenarios
- **Forces structured thinking**: Plan-driven vs reactive
- **Better risk management**: Weekly risk allocation
- **Professional approach**: How institutions trade

### Implementation

```python
# proratio_signals/ai_trading_planner.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional

@dataclass
class ScenarioRule:
    """If-then trading rule"""
    condition: str  # "BTC breaks above $35,900"
    action: str  # "Add 50% position, target $37,200"
    reasoning: str

@dataclass
class WeeklyTradingPlan:
    """Complete trading plan for the week"""
    pair: str
    week_start: datetime
    market_bias: str  # 'bullish', 'bearish', 'neutral'
    bias_confidence: float

    key_support_levels: List[float]
    key_resistance_levels: List[float]

    scenarios: List[ScenarioRule]

    risk_allocation: Dict[str, float]  # How much capital per scenario
    max_weekly_risk: float  # Total risk for the week

    macro_context: str
    technical_context: str
    ai_reasoning: str

class AITradingPlanGenerator:
    """
    Generates structured weekly trading plans using LLMs
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def generate_weekly_plan(
        self,
        pair: str,
        portfolio_state: Dict,
        current_market_data
    ) -> WeeklyTradingPlan:
        """
        Generate comprehensive trading plan for the upcoming week
        """

        # Gather market context
        technical_analysis = self._analyze_technicals(pair, current_market_data)
        macro_context = self._analyze_macro_context()
        sentiment_analysis = self._analyze_sentiment(pair)

        # Create planning prompt
        prompt = self._create_planning_prompt(
            pair,
            technical_analysis,
            macro_context,
            sentiment_analysis,
            portfolio_state
        )

        # Get LLM-generated plan
        llm_response = self.orchestrator.analyze_market(pair, prompt)

        # Parse and structure the plan
        plan = self._parse_trading_plan(llm_response, pair)

        return plan

    def _create_planning_prompt(
        self,
        pair: str,
        technical: Dict,
        macro: Dict,
        sentiment: Dict,
        portfolio: Dict
    ) -> str:
        """
        Create comprehensive prompt for weekly planning
        """
        prompt = f"""
Generate a detailed trading plan for {pair} for the upcoming week.

CURRENT MARKET STATE:
-------------------
Price: {technical['current_price']}
Range: {technical['week_high']} - {technical['week_low']}

Technical Indicators:
- Trend: {technical['trend']}
- RSI: {technical['rsi']}
- MACD: {technical['macd']}
- Volume: {technical['volume_analysis']}

Support Levels: {', '.join(map(str, technical['support_levels']))}
Resistance Levels: {', '.join(map(str, technical['resistance_levels']))}

MACRO CONTEXT:
--------------
{macro['summary']}

SENTIMENT:
----------
{sentiment['summary']}

PORTFOLIO STATE:
----------------
Current Position: {portfolio.get('current_position', 'None')}
Available Capital: ${portfolio['available_capital']}
Max Risk This Week: {portfolio['max_risk_pct']}%

TASK:
-----
Generate a complete trading plan with the following sections:

1. MARKET BIAS (Bullish/Bearish/Neutral + Confidence %)
   - What's your overall directional bias?
   - Why? (3-5 bullet points)

2. KEY LEVELS TO WATCH
   - 3 support levels (for buying or stop placement)
   - 3 resistance levels (for profit targets or avoiding)
   - Reasoning for each level

3. TRADING SCENARIOS (If-Then Rules)
   Create 3-5 scenarios covering different outcomes:

   Scenario A: Bullish Breakout
   - Condition: If price breaks above $X with volume
   - Action: Enter Y% position, target $Z
   - Stop loss: $W
   - Risk/Reward: 1:X

   Scenario B: Bearish Breakdown
   - Condition: If price breaks below $X
   - Action: Exit all longs / Enter short
   - Reasoning: Why this invalidates bull case

   Scenario C: Range-Bound
   - Condition: If price stays between $X and $Y
   - Action: Mean reversion trades or wait

   [Add more scenarios as needed]

4. RISK MANAGEMENT
   - Maximum position size for each scenario
   - Total capital allocation this week
   - Position sizing rules
   - When to sit out (conditions to avoid trading)

5. EXIT STRATEGY
   - Profit target rules
   - Stop loss rules
   - Trailing stop strategy
   - Time stops (max hold time)

6. DAILY CHECKLIST
   - What to monitor each day
   - Key news events this week
   - Market hours to watch
   - Review times

Format your response as a structured plan that can be followed mechanically.
"""
        return prompt

    def _parse_trading_plan(
        self,
        llm_response: Dict,
        pair: str
    ) -> WeeklyTradingPlan:
        """
        Parse LLM response into structured WeeklyTradingPlan
        """

        # Extract scenarios
        scenarios = []
        for scenario_data in llm_response['scenarios']:
            scenarios.append(ScenarioRule(
                condition=scenario_data['condition'],
                action=scenario_data['action'],
                reasoning=scenario_data['reasoning']
            ))

        # Build plan
        plan = WeeklyTradingPlan(
            pair=pair,
            week_start=datetime.now(),
            market_bias=llm_response['market_bias'],
            bias_confidence=llm_response['bias_confidence'],
            key_support_levels=llm_response['support_levels'],
            key_resistance_levels=llm_response['resistance_levels'],
            scenarios=scenarios,
            risk_allocation=llm_response['risk_allocation'],
            max_weekly_risk=llm_response['max_weekly_risk'],
            macro_context=llm_response['macro_context'],
            technical_context=llm_response['technical_context'],
            ai_reasoning=llm_response['reasoning']
        )

        return plan

    def monitor_plan_execution(
        self,
        plan: WeeklyTradingPlan,
        current_price: float
    ) -> Optional[ScenarioRule]:
        """
        Check if any scenario conditions are triggered

        Returns:
            Triggered scenario rule if conditions met, None otherwise
        """

        for scenario in plan.scenarios:
            if self._check_scenario_condition(scenario.condition, current_price):
                return scenario

        return None

# Example usage in main trading loop:

class PlanBasedTradingSystem:
    """
    Trading system that operates based on weekly plans
    """

    def __init__(self):
        self.plan_generator = AITradingPlanGenerator(orchestrator)
        self.current_plan = None

    def run_weekly_cycle(self):
        """
        Main trading loop - plan-driven approach
        """

        # Generate plan at start of week (Sunday evening)
        if self._is_start_of_week():
            portfolio_state = self._get_portfolio_state()
            market_data = self._get_market_data()

            self.current_plan = self.plan_generator.generate_weekly_plan(
                pair='BTC/USDT',
                portfolio_state=portfolio_state,
                current_market_data=market_data
            )

            # Log and display plan
            self._log_weekly_plan(self.current_plan)
            self._send_plan_to_dashboard(self.current_plan)

        # During the week: Monitor plan execution
        current_price = self._get_current_price('BTC/USDT')

        triggered_scenario = self.plan_generator.monitor_plan_execution(
            self.current_plan,
            current_price
        )

        if triggered_scenario:
            # Execute the planned trade
            self._execute_scenario_action(triggered_scenario)

            # Log execution
            self._log_scenario_execution(triggered_scenario, current_price)

    def _execute_scenario_action(self, scenario: ScenarioRule):
        """
        Execute the action defined in triggered scenario
        """
        # Parse action string and execute trade
        # Example: "Add 50% position, target $37,200"

        action_params = self._parse_action(scenario.action)

        if action_params['type'] == 'add_position':
            self.execute_trade(
                pair='BTC/USDT',
                direction='long',
                size=action_params['size'],
                target=action_params['target'],
                reasoning=scenario.reasoning
            )

        elif action_params['type'] == 'exit':
            self.exit_all_positions(reason=scenario.reasoning)

        # etc...
```

### Example Weekly Plan Output

```
╔═══════════════════════════════════════════════════════════════╗
║           WEEKLY TRADING PLAN: BTC/USDT                       ║
║                  Week of October 14-20, 2025                  ║
╚═══════════════════════════════════════════════════════════════╝

MARKET BIAS: Cautiously Bullish (65% confidence)
────────────────────────────────────────────────
- Price consolidated above $33k support (bullish structure)
- Higher highs and higher lows on 4h chart
- Volume decreasing (needs confirmation breakout)
- RSI neutral at 55 (room to move up)
- Fed dovish = positive for risk assets

KEY LEVELS TO WATCH:
────────────────────
Support Levels:
  $33,800 - Previous swing low, strong buying
  $32,500 - Major support zone, high volume node
  $31,200 - Critical support, if broken = bearish

Resistance Levels:
  $35,900 - Local top, needs to clear with volume
  $37,200 - Major resistance from August
  $39,000 - Psychological level, strong selling

TRADING SCENARIOS:
──────────────────

📈 Scenario A: Bullish Breakout
   Condition: Price breaks and CLOSES above $35,900 with volume > avg
   Action:
     • Add 50% position at $36,000
     • Target: $37,200 (take 70%), $39,000 (take 30%)
     • Stop loss: $34,800 (below breakout)
     • Risk/Reward: 1:2.5
   Reasoning: Clean breakout with volume confirms continuation

📉 Scenario B: Failed Breakout
   Condition: Price rejects at $35,900 and closes below $35,000
   Action:
     • Close any longs
     • Wait for retest of $33,800 support
   Reasoning: Rejection at resistance = need to reassess

📊 Scenario C: Continued Consolidation
   Condition: Price stays between $33,800 - $35,500 for 3+ days
   Action:
     • Switch to range trading strategy
     • Buy support, sell resistance
     • Small positions (30% of normal)
   Reasoning: Low volatility = mean reversion opportunities

❌ Scenario D: Bearish Breakdown
   Condition: Price breaks and closes below $33,800
   Action:
     • Exit ALL longs immediately
     • Move to cash or short with 30% position
     • Target: $32,500
   Reasoning: Break of support invalidates bull case

🎯 Scenario E: Pullback to $34k
   Condition: Price pulls back to $34,000-$34,500 zone
   Action:
     • Scale in: 30% at $34,500, 40% at $34,000, 30% at $33,800
     • Target: $37,200
     • Stop: $33,500
   Reasoning: Healthy pullback to breakout zone = buying opportunity

RISK MANAGEMENT:
────────────────
• Max position size: 5% of portfolio per trade
• Max weekly drawdown: 10% of portfolio
• If 2 stops hit this week: STOP TRADING, reassess
• Capital allocation:
  - Scenario A (breakout): 50% of available capital
  - Scenario C (range): 30% of available capital
  - Scenario E (pullback): 60% of available capital

EXIT STRATEGY:
──────────────
• Take Profit: 70% at first target, 30% as runner
• Stop Loss: Always honored, no exceptions
• Trailing Stop: Move to breakeven after +3% profit
• Time Stop: Close position after 7 days regardless

DAILY CHECKLIST:
────────────────
□ Check price action at open (9 AM UTC)
□ Review scenario conditions (3 PM UTC)
□ Monitor volume during US session (2-8 PM UTC)
□ News check: Fed speakers, macro data
□ Update plan if major news breaks

KEY NEWS THIS WEEK:
───────────────────
• Wednesday: US CPI Data (8:30 AM ET) - HIGH IMPACT
• Thursday: ECB Rate Decision (8:15 AM ET) - MEDIUM IMPACT
• Friday: Options Expiry - Expect volatility

NOTES:
──────
• Fed dovish pivot still supporting risk assets
• Bitcoin ETF flows have been positive
• Altcoin season has NOT started yet (BTC dominance high)
• Overall: Cautiously bullish, but respect resistance

═══════════════════════════════════════════════════════════════
This plan is generated by AI and should be reviewed before execution.
Always validate scenario conditions manually before entering trades.
═══════════════════════════════════════════════════════════════
```

### Benefits of Plan-Based Trading

1. **Removes Emotion**: You already know what to do in each scenario
2. **Forces Preparation**: Think through scenarios before they happen
3. **Better Risk Management**: Pre-defined position sizes
4. **Professional Approach**: How institutions trade
5. **Reduced FOMO**: You have a plan to enter on pullbacks
6. **Clear Review**: Easy to review what worked/didn't work

### Expected Performance
- **Reduced emotional trades**: 60-70% fewer impulsive entries
- **Better entry prices**: 20-30% improvement vs reactive trading
- **Higher consistency**: 40-50% more consistent results
- **Improved discipline**: 80%+ adherence to risk rules

---

## ⭐ Phase 10: Hybrid ML+LLM System (HIGHEST PRIORITY)

### Concept
Combine your LSTM/ML ensemble predictions (quantitative) with LLM analysis (qualitative) for superior signal generation.

### Why This Is Your Best Opportunity

**Your Current System**:
- ✅ ML Ensemble: LSTM + LightGBM + XGBoost (19.66% better than base)
- ✅ LLM Consensus: ChatGPT + Claude + Gemini (multi-AI signals)

**The Hybrid Opportunity**:
- 🎯 ML captures statistical patterns (math)
- 🎯 LLMs capture narrative/context (intuition)
- 🎯 Agreement = very strong signal
- 🎯 Disagreement = caution flag

### Expected Performance Impact
- **Reduce false signals**: 40-60%
- **Increase win rate**: +10-15%
- **Better risk-adjusted returns**: Sharpe ratio +0.3 to +0.5
- **Lower drawdowns**: -20-30% max drawdown

### Architecture

```python
# proratio_signals/hybrid_predictor.py

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class SignalStrength(Enum):
    """Signal strength levels"""
    VERY_STRONG = "very_strong"  # ML + LLM perfect agreement
    STRONG = "strong"            # ML + LLM directional agreement
    MODERATE = "moderate"        # ML strong but LLM uncertain
    WEAK = "weak"                # ML weak or LLM weak
    CONFLICT = "conflict"        # ML vs LLM disagreement
    NO_SIGNAL = "no_signal"      # Both uncertain

@dataclass
class MLPrediction:
    """ML Ensemble prediction"""
    direction: str  # 'up', 'down', 'neutral'
    confidence: float  # 0.0-1.0
    predicted_return: float  # Expected % return
    model_agreement: float  # How much LSTM+LGB+XGB agree
    contributing_models: Dict[str, float]  # Individual model predictions

@dataclass
class LLMPrediction:
    """LLM Consensus prediction"""
    direction: str  # 'bullish', 'bearish', 'neutral'
    confidence: float  # 0.0-1.0
    reasoning: str
    key_factors: List[str]
    provider_agreement: float  # How much GPT+Claude+Gemini agree

@dataclass
class HybridSignal:
    """Combined ML + LLM signal"""
    action: str  # 'ENTER_LONG', 'ENTER_SHORT', 'EXIT', 'WAIT'
    strength: SignalStrength
    combined_confidence: float
    ml_prediction: MLPrediction
    llm_prediction: LLMPrediction
    agreement_score: float  # 0-100%, how aligned are ML and LLM
    recommended_position_size: float  # 0.0-1.0 multiplier
    reasoning: str

class HybridMLLLMPredictor:
    """
    Combines ML ensemble and LLM consensus for superior predictions

    Stage 1: ML Ensemble generates quantitative prediction
    Stage 2: LLM Consensus generates qualitative analysis
    Stage 3: Combine signals with conflict resolution
    """

    def __init__(self, ensemble_model, llm_orchestrator):
        self.ensemble = ensemble_model
        self.llm_orchestrator = llm_orchestrator

        # Tunable parameters
        self.min_ml_confidence = 0.60
        self.min_llm_confidence = 0.60
        self.min_agreement_for_trade = 0.70

    def generate_hybrid_signal(
        self,
        pair: str,
        ohlcv_data,
        market_context: Optional[str] = None
    ) -> HybridSignal:
        """
        Generate hybrid signal combining ML and LLM predictions

        Returns HybridSignal with:
        - Combined action recommendation
        - Signal strength classification
        - Individual ML and LLM predictions
        - Agreement analysis
        """

        # Stage 1: Get ML Ensemble Prediction
        ml_pred = self._get_ml_prediction(pair, ohlcv_data)

        # Stage 2: Get LLM Consensus Prediction
        llm_pred = self._get_llm_prediction(pair, ohlcv_data, market_context)

        # Stage 3: Combine predictions
        hybrid_signal = self._combine_predictions(ml_pred, llm_pred)

        return hybrid_signal

    def _get_ml_prediction(self, pair: str, ohlcv_data) -> MLPrediction:
        """
        Get prediction from ML ensemble
        """
        # Prepare features
        features = self.ensemble.prepare_features(ohlcv_data)

        # Get ensemble prediction
        prediction = self.ensemble.predict(features)

        # Parse prediction
        direction = 'up' if prediction['direction'] > 0 else 'down'
        confidence = abs(prediction['confidence'])
        predicted_return = prediction['predicted_return']

        # Get individual model contributions
        model_contributions = prediction.get('model_contributions', {})

        # Calculate model agreement
        if model_contributions:
            predictions = list(model_contributions.values())
            agreement = self._calculate_agreement(predictions)
        else:
            agreement = confidence

        return MLPrediction(
            direction=direction,
            confidence=confidence,
            predicted_return=predicted_return,
            model_agreement=agreement,
            contributing_models=model_contributions
        )

    def _get_llm_prediction(
        self,
        pair: str,
        ohlcv_data,
        market_context: Optional[str]
    ) -> LLMPrediction:
        """
        Get prediction from LLM consensus
        """
        # Create enhanced prompt with ML context
        prompt = self._create_enhanced_prompt(pair, ohlcv_data, market_context)

        # Get LLM consensus
        llm_response = self.llm_orchestrator.generate_signal(pair, prompt)

        return LLMPrediction(
            direction=llm_response['direction'],
            confidence=llm_response['confidence'],
            reasoning=llm_response['reasoning'],
            key_factors=llm_response.get('key_factors', []),
            provider_agreement=llm_response.get('provider_agreement', 0.0)
        )

    def _combine_predictions(
        self,
        ml_pred: MLPrediction,
        llm_pred: LLMPrediction
    ) -> HybridSignal:
        """
        Combine ML and LLM predictions with conflict resolution
        """

        # Normalize directions (ML: up/down, LLM: bullish/bearish)
        ml_direction = ml_pred.direction
        llm_direction = 'up' if llm_pred.direction == 'bullish' else 'down'

        # Calculate agreement score
        directional_match = (ml_direction == llm_direction)
        agreement_score = self._calculate_hybrid_agreement(ml_pred, llm_pred)

        # Determine signal strength
        signal_strength = self._classify_signal_strength(
            ml_pred, llm_pred, directional_match, agreement_score
        )

        # Generate action recommendation
        action = self._determine_action(
            ml_pred, llm_pred, signal_strength, directional_match
        )

        # Calculate combined confidence
        combined_confidence = self._calculate_combined_confidence(
            ml_pred, llm_pred, agreement_score
        )

        # Determine position size
        position_size = self._calculate_position_size(
            signal_strength, combined_confidence
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            ml_pred, llm_pred, directional_match, agreement_score, action
        )

        return HybridSignal(
            action=action,
            strength=signal_strength,
            combined_confidence=combined_confidence,
            ml_prediction=ml_pred,
            llm_prediction=llm_pred,
            agreement_score=agreement_score,
            recommended_position_size=position_size,
            reasoning=reasoning
        )

    def _classify_signal_strength(
        self,
        ml_pred: MLPrediction,
        llm_pred: LLMPrediction,
        directional_match: bool,
        agreement_score: float
    ) -> SignalStrength:
        """
        Classify signal strength based on ML+LLM alignment
        """

        # Perfect agreement: Both high confidence + same direction
        if (directional_match and
            ml_pred.confidence > 0.75 and
            llm_pred.confidence > 0.75 and
            agreement_score > 0.85):
            return SignalStrength.VERY_STRONG

        # Strong: Both agree + decent confidence
        if (directional_match and
            ml_pred.confidence > 0.65 and
            llm_pred.confidence > 0.65 and
            agreement_score > 0.70):
            return SignalStrength.STRONG

        # Moderate: ML strong but LLM uncertain
        if (directional_match and
            ml_pred.confidence > 0.70 and
            llm_pred.confidence > 0.50):
            return SignalStrength.MODERATE

        # Weak: Low confidence from either
        if (ml_pred.confidence < 0.60 or llm_pred.confidence < 0.60):
            return SignalStrength.WEAK

        # Conflict: Disagree on direction
        if not directional_match:
            return SignalStrength.CONFLICT

        # Default
        return SignalStrength.NO_SIGNAL

    def _determine_action(
        self,
        ml_pred: MLPrediction,
        llm_pred: LLMPrediction,
        strength: SignalStrength,
        directional_match: bool
    ) -> str:
        """
        Determine trading action based on signal strength
        """

        if strength == SignalStrength.VERY_STRONG:
            # High confidence trade
            direction = ml_pred.direction.upper()
            return f'ENTER_{direction}'

        elif strength == SignalStrength.STRONG:
            # Normal confidence trade
            direction = ml_pred.direction.upper()
            return f'ENTER_{direction}'

        elif strength == SignalStrength.MODERATE:
            # Reduced size trade
            direction = ml_pred.direction.upper()
            return f'ENTER_{direction}_SMALL'

        elif strength == SignalStrength.CONFLICT:
            # ML vs LLM disagreement - SKIP
            return 'WAIT_CONFLICT'

        else:  # WEAK or NO_SIGNAL
            return 'WAIT'

    def _calculate_combined_confidence(
        self,
        ml_pred: MLPrediction,
        llm_pred: LLMPrediction,
        agreement_score: float
    ) -> float:
        """
        Calculate combined confidence score

        Uses weighted average with agreement bonus:
        - Base: 60% ML + 40% LLM (ML slightly favored for quant data)
        - Bonus: +10-20% if high agreement
        """

        # Weighted average
        base_confidence = (ml_pred.confidence * 0.6) + (llm_pred.confidence * 0.4)

        # Agreement bonus (0-20% boost)
        agreement_bonus = (agreement_score - 0.5) * 0.4  # 50% agreement = 0 bonus, 100% = 20% bonus
        agreement_bonus = max(0, agreement_bonus)  # No penalty for disagreement

        combined = base_confidence + agreement_bonus

        return min(combined, 1.0)  # Cap at 100%

    def _calculate_position_size(
        self,
        strength: SignalStrength,
        combined_confidence: float
    ) -> float:
        """
        Calculate recommended position size multiplier

        Returns 0.0-1.0 multiplier on base position size
        """

        if strength == SignalStrength.VERY_STRONG:
            # Oversized position: 1.2-1.5x
            return 1.0 + (combined_confidence * 0.5)

        elif strength == SignalStrength.STRONG:
            # Full position: 1.0x
            return 1.0

        elif strength == SignalStrength.MODERATE:
            # Reduced position: 0.5-0.7x
            return 0.5 + (combined_confidence * 0.2)

        else:
            # No trade
            return 0.0

    def _generate_reasoning(
        self,
        ml_pred: MLPrediction,
        llm_pred: LLMPrediction,
        directional_match: bool,
        agreement_score: float,
        action: str
    ) -> str:
        """
        Generate human-readable reasoning for the signal
        """

        if 'ENTER' in action:
            direction = 'UP' if ml_pred.direction == 'up' else 'DOWN'

            reasoning = f"""
HYBRID SIGNAL: {action}
════════════════════════════════════════════════

ML ENSEMBLE ANALYSIS:
  Direction: {ml_pred.direction.upper()}
  Confidence: {ml_pred.confidence:.1%}
  Predicted Return: {ml_pred.predicted_return:+.2%}
  Model Agreement: {ml_pred.model_agreement:.1%}

  Contributing Models:
"""
            for model, pred in ml_pred.contributing_models.items():
                reasoning += f"    {model}: {pred:+.2%}\n"

            reasoning += f"""
LLM CONSENSUS ANALYSIS:
  Direction: {llm_pred.direction.upper()}
  Confidence: {llm_pred.confidence:.1%}
  Provider Agreement: {llm_pred.provider_agreement:.1%}

  Key Factors:
"""
            for factor in llm_pred.key_factors:
                reasoning += f"    • {factor}\n"

            reasoning += f"""
  Reasoning: {llm_pred.reasoning}

HYBRID ANALYSIS:
  Agreement Score: {agreement_score:.1%}
  Combined Confidence: {self._calculate_combined_confidence(ml_pred, llm_pred, agreement_score):.1%}

"""
            if directional_match and agreement_score > 0.80:
                reasoning += "  ✅ STRONG AGREEMENT: ML and LLM both predict same direction with high confidence\n"
            elif directional_match:
                reasoning += "  ✅ DIRECTIONAL AGREEMENT: ML and LLM agree on direction\n"
            else:
                reasoning += "  ⚠️ CONFLICT: ML and LLM disagree - recommend waiting\n"

        else:  # WAIT
            reasoning = f"""
HYBRID SIGNAL: {action}
════════════════════════════════════════════════

ML Prediction: {ml_pred.direction.upper()} ({ml_pred.confidence:.1%} confidence)
LLM Prediction: {llm_pred.direction.upper()} ({llm_pred.confidence:.1%} confidence)

Agreement Score: {agreement_score:.1%}

"""
            if not directional_match:
                reasoning += "⚠️ CONFLICT DETECTED: ML and LLM predict opposite directions\n"
                reasoning += f"  ML says: {ml_pred.direction.upper()}\n"
                reasoning += f"  LLM says: {llm_pred.direction.upper()}\n"
                reasoning += "\nRecommendation: WAIT for clarity before entering trade\n"
            else:
                reasoning += "⚠️ LOW CONFIDENCE: Both ML and LLM show uncertainty\n"
                reasoning += "\nRecommendation: WAIT for stronger setup\n"

        return reasoning
```

### Integration with Existing System

```python
# In your main trading strategy:

class HybridTradingStrategy(IStrategy):
    """
    Trading strategy using Hybrid ML+LLM signals
    """

    def __init__(self):
        super().__init__()

        # Initialize components
        self.ensemble_model = EnsemblePredictor.load('models/ensemble_model.pkl')
        self.llm_orchestrator = SignalOrchestrator()

        # Initialize hybrid predictor
        self.hybrid_predictor = HybridMLLLMPredictor(
            ensemble_model=self.ensemble_model,
            llm_orchestrator=self.llm_orchestrator
        )

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Generate entry signals using hybrid approach
        """

        pair = metadata['pair']

        # Generate hybrid signal
        hybrid_signal = self.hybrid_predictor.generate_hybrid_signal(
            pair=pair,
            ohlcv_data=dataframe,
            market_context=self._get_market_context()
        )

        # Log signal details
        logger.info(f"\n{hybrid_signal.reasoning}")

        # Only enter if signal is STRONG or VERY_STRONG
        if hybrid_signal.strength in [SignalStrength.VERY_STRONG, SignalStrength.STRONG]:

            if 'LONG' in hybrid_signal.action or 'UP' in hybrid_signal.action:
                dataframe.loc[dataframe.index[-1], 'enter_long'] = 1
                dataframe.loc[dataframe.index[-1], 'enter_tag'] = (
                    f'{hybrid_signal.strength.value}_'
                    f'ml_{hybrid_signal.ml_prediction.confidence:.0%}_'
                    f'llm_{hybrid_signal.llm_prediction.confidence:.0%}'
                )

            elif 'SHORT' in hybrid_signal.action or 'DOWN' in hybrid_signal.action:
                dataframe.loc[dataframe.index[-1], 'enter_short'] = 1

        # Store signal metadata for position sizing
        dataframe.loc[dataframe.index[-1], 'signal_confidence'] = hybrid_signal.combined_confidence
        dataframe.loc[dataframe.index[-1], 'position_size_multiplier'] = hybrid_signal.recommended_position_size

        return dataframe

    def custom_stake_amount(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_stake: float,
        min_stake: float,
        max_stake: float,
        **kwargs
    ) -> float:
        """
        Adjust position size based on hybrid signal confidence
        """

        dataframe = self.dp.get_pair_dataframe(pair, self.timeframe)

        if len(dataframe) == 0:
            return proposed_stake

        # Get signal metadata
        multiplier = dataframe.iloc[-1].get('position_size_multiplier', 1.0)

        # Adjust stake
        adjusted_stake = proposed_stake * multiplier

        # Respect min/max limits
        return max(min_stake, min(adjusted_stake, max_stake))
```

### Conflict Resolution Rules

**When ML and LLM Disagree:**

1. **Strong ML + Weak LLM**:
   - Action: Enter with reduced size (50-70%)
   - Reasoning: Trust quantitative data but hedge against qualitative uncertainty

2. **Weak ML + Strong LLM**:
   - Action: Enter with reduced size (50-70%)
   - Reasoning: LLM may see narrative factors ML misses

3. **Strong ML + Strong LLM + Opposite Directions**:
   - Action: **WAIT** (no trade)
   - Reasoning: Significant conflict = high uncertainty

4. **Weak ML + Weak LLM**:
   - Action: **WAIT** (no trade)
   - Reasoning: Not enough conviction from either system

### Expected Performance Metrics

**Backtest Targets (vs ML-only or LLM-only)**:

| Metric | ML-Only | LLM-Only | Hybrid Target |
|--------|---------|----------|---------------|
| Win Rate | 55% | 52% | **65%** (+10-13%) |
| Sharpe Ratio | 1.2 | 0.9 | **1.8** (+50%) |
| Max Drawdown | -18% | -22% | **-12%** (-33%) |
| Profit Factor | 1.5 | 1.3 | **2.1** (+40%) |
| False Signals | 100 | 120 | **50** (-50-60%) |

**Real-World Benefits**:
- Fewer losing trades (better entries)
- Higher confidence in signals (better psychology)
- Adaptive to changing markets (combines quant + narrative)
- Reduced overfitting (two independent systems validate each other)

---

## 📊 Implementation Roadmap Summary

### Phase 4: Multi-Timeframe Analysis (1-2 weeks)
- ⏱️ **Effort**: Medium
- 💰 **Value**: High (30-40% false signal reduction)
- 🎯 **Priority**: 2/5

### Phase 5: AI Regime Detection (1 week)
- ⏱️ **Effort**: Low-Medium
- 💰 **Value**: High (better strategy selection)
- 🎯 **Priority**: 3/5

### Phase 6: Dynamic Risk Management (1 week)
- ⏱️ **Effort**: Medium
- 💰 **Value**: Very High (30-40% fewer stop-outs)
- 🎯 **Priority**: 4/5

### Phase 7: Correlation Analysis (1 week)
- ⏱️ **Effort**: Low-Medium
- 💰 **Value**: Medium (better pair selection)
- 🎯 **Priority**: 5/5

### Phase 8: News Event Trading (2 weeks)
- ⏱️ **Effort**: High (API integrations)
- 💰 **Value**: Medium (captures major moves)
- 🎯 **Priority**: 6/5

### Phase 9: Weekly Trading Plans (1 week)
- ⏱️ **Effort**: Low
- 💰 **Value**: Very High (reduces emotional trading)
- 🎯 **Priority**: 4/5

### Phase 10: Hybrid ML+LLM System (2-3 weeks) ⭐
- ⏱️ **Effort**: High
- 💰 **Value**: **VERY HIGH** (40-60% false signal reduction)
- 🎯 **Priority**: **1/5 (HIGHEST)**

---

## 🎯 Recommended Implementation Order

**Quarter 1 (Next 3 months)**:
1. ⭐ **Phase 10: Hybrid ML+LLM** (2-3 weeks) - Highest ROI
2. **Phase 9: Weekly Plans** (1 week) - Quick win, improves discipline
3. **Phase 6: Dynamic Risk** (1 week) - Better stop placement
4. **Phase 4: Multi-Timeframe** (1-2 weeks) - Reduces false signals

**Quarter 2**:
5. **Phase 5: Regime Detection** (1 week)
6. **Phase 7: Correlation Analysis** (1 week)
7. **Phase 8: News Trading** (2 weeks)

---

## 📈 Combined System Performance Estimate

If all phases are implemented, your system would have:

**Signal Generation**:
- Multi-timeframe alignment (reduces whipsaws 30-40%)
- Hybrid ML+LLM validation (reduces false signals 40-60%)
- News event awareness (captures major moves 60-70%)
- **Combined false signal reduction: 70-80%**

**Risk Management**:
- Dynamic stops at logical levels (30-40% fewer stop-outs)
- AI-generated risk levels (better R:R ratios)
- Regime-aware position sizing (capital efficiency +15-20%)

**Trading Discipline**:
- Weekly trading plans (reduces emotional trades 60-70%)
- Pre-defined scenarios (improves execution quality)
- Cross-asset analysis (better pair selection 25-30%)

**Expected Overall Performance**:
- **Win Rate**: 65-70% (vs 45-50% baseline)
- **Sharpe Ratio**: 2.0-2.5 (vs 1.0-1.2 baseline)
- **Max Drawdown**: -10-12% (vs -18-22% baseline)
- **Profit Factor**: 2.5-3.0 (vs 1.3-1.5 baseline)

This would put your system in the **top 10% of retail algo traders** in terms of risk-adjusted returns.

---

## 🚀 Next Steps

1. **Review this document** with the team
2. **Start with Phase 10 (Hybrid)** - highest priority, biggest impact
3. **Run backtests** to validate each phase
4. **Paper trade** each phase for 2-4 weeks before live
5. **Measure and iterate** - track metrics for each phase

---

**Questions or need help implementing?** Check the main [roadmap.md](roadmap.md) for project status and [strategy_development_guide.md](strategy_development_guide.md) for implementation details.
