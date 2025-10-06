"""
Sentiment Analysis Prompt Templates

Prompts for LLMs to analyze market sentiment and trend direction.
"""

SENTIMENT_ANALYSIS_PROMPT = """
You are an expert in cryptocurrency market sentiment analysis and trend direction.

=== MARKET DATA ===
{market_data}

=== ADDITIONAL CONTEXT ===
{additional_context}

=== YOUR TASK ===
Determine the overall market sentiment for {pair} on {timeframe} timeframe.

Analyze:
1. **Price Trend**: Direction and strength of current trend
2. **Volume Behavior**: Buying vs selling pressure
3. **Market Participation**: Increasing or decreasing interest
4. **Momentum Shift**: Any signs of sentiment change
5. **Overall Bias**: Bullish, bearish, or neutral sentiment

=== OUTPUT FORMAT (JSON) ===
{{
    "direction": "long" | "short" | "neutral",
    "confidence": 0.0 to 1.0,
    "technical_summary": "Sentiment state and trend direction",
    "risk_assessment": "Sentiment risks (e.g., overheated market, capitulation)",
    "sentiment": "bullish" | "bearish" | "neutral",
    "reasoning": "Sentiment indicators and trend analysis"
}}

Sentiment often leads price - identify early shifts in market psychology.
"""

TREND_DIRECTION_PROMPT = """
You are an expert in identifying and confirming cryptocurrency trends.

=== MARKET DATA ===
{market_data}

=== YOUR TASK ===
Identify the primary trend direction for {pair} on {timeframe} timeframe.

Determine:
- **Primary Trend**: Uptrend, downtrend, or sideways
- **Trend Phase**: Early, middle, or late stage
- **Trend Strength**: Strong, moderate, or weak
- **Pullback Levels**: Healthy retracement zones
- **Trend Continuation**: Likelihood of trend continuing

=== OUTPUT FORMAT (JSON) ===
{{
    "direction": "long" | "short" | "neutral",
    "confidence": 0.0 to 1.0,
    "technical_summary": "Trend classification and phase",
    "risk_assessment": "Trend exhaustion risks and reversal signs",
    "sentiment": "bullish" | "bearish" | "neutral",
    "reasoning": "Trend analysis with specific trend indicators"
}}

The trend is your friend - trade with the trend, not against it.
"""

MOMENTUM_SENTIMENT_PROMPT = """
You are an expert in momentum and market psychology for cryptocurrency markets.

=== MARKET DATA ===
{market_data}

=== YOUR TASK ===
Assess momentum and crowd psychology for {pair} on {timeframe} timeframe.

Evaluate:
- **Momentum Direction**: Increasing or decreasing
- **Momentum Divergence**: Price vs momentum indicators
- **Crowd Behavior**: FOMO, fear, greed, capitulation
- **Extreme Readings**: Overbought/oversold extremes
- **Momentum Shifts**: Early signs of momentum change

=== OUTPUT FORMAT (JSON) ===
{{
    "direction": "long" | "short" | "neutral",
    "confidence": 0.0 to 1.0,
    "technical_summary": "Momentum state and psychological indicators",
    "risk_assessment": "Extreme sentiment risks and contrarian signals",
    "sentiment": "bullish" | "bearish" | "neutral",
    "reasoning": "Momentum psychology analysis"
}}

Extreme sentiment often precedes reversals - be contrarian at extremes.
"""
