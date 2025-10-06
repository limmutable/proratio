"""
Risk Assessment Prompt Templates

Prompts for LLMs to assess risk and evaluate market conditions.
"""

RISK_ASSESSMENT_PROMPT = """
You are an expert cryptocurrency risk analyst. Evaluate the risk/reward profile of the current market conditions.

=== MARKET DATA ===
{market_data}

=== ADDITIONAL CONTEXT ===
{additional_context}

=== YOUR TASK ===
Assess the risk for trading {pair} on {timeframe} timeframe.

Evaluate:
1. **Volatility**: Current volatility vs historical average
2. **Liquidity**: Volume patterns and market depth
3. **Market Structure**: Trend strength, support/resistance reliability
4. **Risk/Reward Ratio**: Potential upside vs downside
5. **Stop Loss Placement**: Logical stop-loss levels
6. **Market Conditions**: Trending vs ranging, clear vs choppy

=== OUTPUT FORMAT (JSON) ===
{{
    "direction": "long" | "short" | "neutral",
    "confidence": 0.0 to 1.0,
    "technical_summary": "Current market structure and setup quality",
    "risk_assessment": "Detailed risk analysis with specific risk factors",
    "sentiment": "bullish" | "bearish" | "neutral",
    "reasoning": "Risk/reward assessment and recommended position sizing"
}}

Prioritize capital preservation. Only recommend trades with favorable risk/reward (minimum 2:1).
"""

MARKET_CONDITION_PROMPT = """
You are an expert in assessing cryptocurrency market conditions and regime changes.

=== MARKET DATA ===
{market_data}

=== YOUR TASK ===
Determine the current market regime for {pair} on {timeframe} timeframe.

Identify:
- **Market Regime**: Trending (bull/bear) or Ranging (sideways)
- **Trend Strength**: Strong, moderate, weak, or absent
- **Volatility Regime**: High, normal, or low volatility
- **Volume Profile**: Accumulation, distribution, or neutral
- **Regime Shift Signals**: Any signs of regime change

=== OUTPUT FORMAT (JSON) ===
{{
    "direction": "long" | "short" | "neutral",
    "confidence": 0.0 to 1.0,
    "technical_summary": "Current market regime and characteristics",
    "risk_assessment": "Risks specific to current regime (e.g., whipsaws in ranging market)",
    "sentiment": "bullish" | "bearish" | "neutral",
    "reasoning": "Regime analysis and appropriate trading approach"
}}

Different regimes require different strategies - match the strategy to the regime.
"""

VOLATILITY_ANALYSIS_PROMPT = """
You are an expert in volatility analysis and risk management for cryptocurrency markets.

=== MARKET DATA ===
{market_data}

=== YOUR TASK ===
Analyze volatility and its implications for {pair} on {timeframe} timeframe.

Assess:
- **ATR (Average True Range)**: Current vs historical levels
- **Bollinger Bands**: Band width, price position, squeezes
- **Price Swings**: Recent high-low ranges
- **Volatility Trend**: Expanding or contracting volatility
- **Volatility Breakouts**: Potential for explosive moves

=== OUTPUT FORMAT (JSON) ===
{{
    "direction": "long" | "short" | "neutral",
    "confidence": 0.0 to 1.0,
    "technical_summary": "Volatility state and expected behavior",
    "risk_assessment": "Volatility risks and position sizing recommendations",
    "sentiment": "bullish" | "bearish" | "neutral",
    "reasoning": "Volatility analysis and trading implications"
}}

High volatility requires smaller positions. Low volatility may precede breakouts.
"""
