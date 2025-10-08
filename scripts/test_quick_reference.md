# 3-Hour Test - Quick Reference Card

## Start Test
```bash
./scripts/run_3h_test.sh
```

## Monitor Test
```bash
# Watch logs
tail -f user_data/logs/test_3h_*.log

# Watch signals
tail -f user_data/logs/test_3h_*.log | grep "ENTRY OPPORTUNITY"

# Check status
curl http://localhost:8081/api/v1/status
```

## Stop Test Manually
```bash
# Find process
pgrep -f freqtrade

# Stop gracefully
pkill -f freqtrade

# Force stop if needed
pkill -9 -f freqtrade
```

## Quick Analysis
```bash
# Count signals
grep "ENTRY OPPORTUNITY" user_data/logs/test_3h_*.log | wc -l

# Count trades
grep "TRADE ENTRY" user_data/logs/test_3h_*.log | wc -l

# View all trades
grep -E "ENTRY|EXIT" user_data/logs/test_3h_*.log
```

## Troubleshooting
```bash
# Check Docker
docker ps | grep proratio

# Start Docker if needed
docker-compose up -d postgres redis

# Check if already running
pgrep -f freqtrade

# View recent errors
tail -50 user_data/logs/test_3h_*.log | grep -i error
```

## Test Configuration
- **Strategy:** MeanReversionTest
- **Timeframe:** 1h
- **Pairs:** BTC/USDT, ETH/USDT
- **Duration:** 3 hours
- **Mode:** Dry-run (paper trading)
- **Wallet:** $10,000 USDT (fake)
- **Stake:** $100 per trade
- **Max trades:** 2 concurrent

## Entry Conditions
- RSI < 35 (oversold)
- Price < Bollinger Band lower
- No AI confirmation

## Exit Conditions
- Price >= BB middle (mean reversion)
- RSI >= 50 (neutralized)
- ROI hit (2% / 1% / 0.5%)
- Stop-loss (-2%)

## Files
- **Strategy:** `user_data/strategies/MeanReversionTest.py`
- **Config:** `proratio_utilities/config/freqtrade/config_test_3h.json`
- **Script:** `scripts/run_3h_test.sh`
- **Guide:** `docs/3hour_test_guide.md`
