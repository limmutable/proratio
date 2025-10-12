#!/usr/bin/env python3
"""Debug CCXT connection"""

import ccxt

# Try without any API keys
exchange = ccxt.binance(
    {
        "enableRateLimit": True,
    }
)

print("Testing fetch_ticker without API keys...")
try:
    ticker = exchange.fetch_ticker("BTC/USDT")
    print(f"Success! BTC/USDT price: {ticker['last']}")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting fetch_ohlcv without API keys...")
try:
    ohlcv = exchange.fetch_ohlcv("BTC/USDT", "1h", limit=5)
    print(f"Success! Fetched {len(ohlcv)} candles")
    if ohlcv:
        print(f"Latest candle: {ohlcv[-1]}")
except Exception as e:
    print(f"Error: {e}")
