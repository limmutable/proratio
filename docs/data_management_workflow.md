# Data Management Workflow

**Last Updated**: October 6, 2025
**Status**: Production-ready

---

## Overview

Proratio uses **PostgreSQL as the single source of truth** for all historical market data. Data is collected once, stored in PostgreSQL, and exported to Freqtrade's format only when needed for backtesting.

This approach prevents:
- ❌ Data duplication issues
- ❌ Inconsistencies between data sources
- ❌ Unnecessary API calls to exchanges
- ❌ Manual data synchronization

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              SINGLE SOURCE OF TRUTH: PostgreSQL                 │
│                                                                 │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  Historical OHLCV Data (24 months)                   │    │
│   │  - BTC/USDT: 17,280 1h + 4,320 4h + 720 daily       │    │
│   │  - ETH/USDT: 17,280 1h + 4,320 4h + 720 daily       │    │
│   │  - Total: 44,640 records                             │    │
│   └──────────────────────────────────────────────────────┘    │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ Export when needed
                        ▼
        ┌───────────────────────────────┐
        │ Freqtrade Data Directory      │
        │ (user_data/data/binance/)     │
        │                               │
        │ - BTC_USDT-1h.feather         │
        │ - ETH_USDT-1h.feather         │
        │ - ... (6 files total)         │
        └───────────────────────────────┘
                        │
                        │ Used by
                        ▼
                ┌───────────────┐
                │  Freqtrade    │
                │  Backtesting  │
                └───────────────┘
```

---

## Step-by-Step Workflow

### 1. Initial Data Collection (One Time)

Download 24 months of historical data from Binance to PostgreSQL:

```bash
python scripts/download_historical_data.py
```

**What it does:**
- Connects to Binance via CCXT (public API, no auth needed)
- Downloads OHLCV data for configured pairs/timeframes
- Stores in PostgreSQL with duplicate prevention
- Takes ~5 minutes for 24 months of 2 pairs × 3 timeframes

**Output:**
```
✓ BTC/USDT 1h   - 17,280 records
✓ BTC/USDT 4h   - 4,320 records
✓ BTC/USDT 1d   - 720 records
✓ ETH/USDT 1h   - 17,280 records
✓ ETH/USDT 4h   - 4,320 records
✓ ETH/USDT 1d   - 720 records
```

---

### 2. Export to Freqtrade Format (When Needed)

Export PostgreSQL data to Freqtrade's feather format:

```bash
python scripts/export_data_for_freqtrade.py
```

**What it does:**
- Reads ALL data from PostgreSQL (no limits)
- Converts to Freqtrade's expected format:
  - Columns: `date, open, high, low, close, volume`
  - Format: Apache Arrow feather (binary, fast)
- Exports to `user_data/data/binance/`
- Takes <10 seconds

**When to run:**
- ✅ Before backtesting
- ✅ After updating PostgreSQL with new data
- ✅ After adding new pairs/timeframes
- ❌ NOT after every data collection (PostgreSQL is always current)

---

### 3. Update with New Data (Regular Updates)

Update PostgreSQL with latest candles:

```bash
# Re-run the download script (it skips duplicates)
python scripts/download_historical_data.py

# OR update specific pair manually
python -c "
from proratio_utilities.data.loaders import DataLoader
loader = DataLoader()
loader.update_recent_data('BTC/USDT', '1h')
"
```

**What it does:**
- Checks latest timestamp in PostgreSQL
- Downloads only new candles since then
- Prevents duplicates with `ON CONFLICT DO NOTHING`
- Fast (~1 second for recent data)

**Then re-export for Freqtrade:**
```bash
python scripts/export_data_for_freqtrade.py
```

---

### 4. Run Backtests

With data exported, run Freqtrade backtests:

```bash
# Backtest full year 2024
freqtrade backtesting \
  --strategy SimpleTestStrategy \
  --timeframe 1h \
  --timerange 20240101-20250101

# Backtest specific period
freqtrade backtesting \
  --strategy SimpleTestStrategy \
  --timeframe 1h \
  --timerange 20240601-20241001
```

**Data used:** Feather files in `user_data/data/binance/`
**Source:** PostgreSQL (exported earlier)

---

## File Locations

| Purpose | Location | Format | Size |
|---------|----------|--------|------|
| **Master data** | PostgreSQL database | SQL | ~10 MB |
| **Freqtrade data** | `user_data/data/binance/*.feather` | Feather | ~2 MB |
| **Export script** | `scripts/export_data_for_freqtrade.py` | Python | - |
| **Download script** | `scripts/download_historical_data.py` | Python | - |
| **Data loader** | `proratio_utilities/data/loaders.py` | Python | - |

---

## Configuration

### PostgreSQL Connection

Configured in `.env`:
```bash
DATABASE_URL=postgresql://proratio:proratio_password@localhost:5432/proratio
```

### Pairs and Timeframes

Configured in scripts (e.g., `download_historical_data.py`):
```python
PAIRS = ['BTC/USDT', 'ETH/USDT']
TIMEFRAMES = ['1h', '4h', '1d']
MONTHS_BACK = 24
```

**To add more pairs/timeframes:**
1. Edit the configuration in the script
2. Run `python scripts/download_historical_data.py`
3. Run `python scripts/export_data_for_freqtrade.py`

---

## Data Integrity

### Duplicate Prevention

PostgreSQL schema includes UNIQUE constraint:
```sql
UNIQUE(exchange, pair, timeframe, timestamp)
```

**Result:** Running download scripts multiple times won't create duplicates.

### Data Validation

Test the data pipeline:
```bash
python scripts/test_data_pipeline.py
```

Checks:
- ✅ Database connection
- ✅ Data insertion
- ✅ Data retrieval
- ✅ Update functionality

---

## Maintenance Commands

### Check Data Status
```bash
python -c "
from proratio_utilities.data.loaders import DataLoader
loader = DataLoader()
status = loader.get_data_status('binance', 'BTC/USDT', '1h')
print(f\"Records: {status['total_records']}\")
print(f\"Latest: {status['latest_timestamp']}\")
"
```

### Clean Up Old Freqtrade Data
```bash
# Remove exported files (PostgreSQL data remains safe)
rm -f user_data/data/binance/*.feather

# Re-export when needed
python scripts/export_data_for_freqtrade.py
```

### Verify Export Consistency
```bash
# Check PostgreSQL record count
psql $DATABASE_URL -c \
  "SELECT COUNT(*) FROM ohlcv WHERE pair='BTC/USDT' AND timeframe='1h';"

# Check Freqtrade file
freqtrade list-data --config proratio_utilities/config/freqtrade/config_dry.json
```

---

## Advantages of This Approach

### ✅ Single Source of Truth
- All data lives in PostgreSQL
- No confusion about which data is "correct"
- Easy to query, analyze, and backup

### ✅ Flexible Analysis
- Can query PostgreSQL directly for custom analytics
- Not limited to Freqtrade's format
- Easy to export to other formats (CSV, Parquet, etc.)

### ✅ Efficient Updates
- Download new data only (no re-downloading 24 months)
- Duplicate prevention built-in
- Fast updates (~1 second for recent data)

### ✅ Cost Savings
- Minimize API calls to Binance
- No rate limiting issues
- Data stored locally forever

### ✅ Reproducibility
- Export script generates identical files
- Backtests are reproducible
- Easy to share data snapshots

---

## Common Workflows

### Scenario 1: Daily Data Update
```bash
# 1. Update PostgreSQL with latest data
python scripts/download_historical_data.py

# 2. Re-export for Freqtrade
python scripts/export_data_for_freqtrade.py

# 3. Run backtests
freqtrade backtesting --strategy MyStrategy --timeframe 1h
```

### Scenario 2: Adding New Pair
```bash
# 1. Edit scripts/download_historical_data.py
# Add 'SOL/USDT' to PAIRS list

# 2. Download data
python scripts/download_historical_data.py

# 3. Export all pairs
python scripts/export_data_for_freqtrade.py

# 4. Update Freqtrade config
# Add SOL/USDT to pair_whitelist in config_dry.json
```

### Scenario 3: Testing New Strategy
```bash
# Data already in PostgreSQL and exported
# Just run backtests:
freqtrade backtesting --strategy NewStrategy --timeframe 4h
```

### Scenario 4: Custom Analysis
```python
# Query PostgreSQL directly (no Freqtrade needed)
from proratio_utilities.data.storage import DatabaseStorage

storage = DatabaseStorage()
df = storage.get_ohlcv('binance', 'BTC/USDT', '1h', limit=None)

# Analyze with pandas, plotly, etc.
print(df.describe())
df['close'].plot()
```

---

## Troubleshooting

### Issue: Freqtrade says "No data found"
**Solution:**
```bash
# Re-export from PostgreSQL
python scripts/export_data_for_freqtrade.py

# Verify files exist
ls -lh user_data/data/binance/
```

### Issue: Old data in Freqtrade
**Solution:**
```bash
# Remove exported files
rm -f user_data/data/binance/*.feather

# Re-export fresh data
python scripts/export_data_for_freqtrade.py
```

### Issue: PostgreSQL connection error
**Solution:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart if needed
docker-compose restart postgres

# Test connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM ohlcv;"
```

### Issue: Pandas SQLAlchemy warning
**Note:** This is a deprecation warning, not an error. The code works fine.
**Future fix:** Migrate from psycopg2 to SQLAlchemy (Phase 1.2)

---

## Best Practices

1. **Always update PostgreSQL first**, then export
2. **Never manually edit Freqtrade data files** (they'll be overwritten)
3. **Keep PostgreSQL backed up** (it's the only source)
4. **Re-export after major updates** (new pairs, timeframes, or data)
5. **Use version control for scripts** (not data files)

---

## Future Enhancements

- [ ] Automated daily data updates (cron job)
- [ ] Data quality checks (gap detection, outlier detection)
- [ ] Export to multiple formats (CSV, Parquet, HDF5)
- [ ] Web UI for data management
- [ ] Real-time data streaming (WebSocket)

---

**Questions?** Check:
- [CLAUDE.md](../CLAUDE.md) - Development guidelines
- [roadmap.md](../roadmap.md) - Implementation roadmap
- Project documentation - Phase 1.0 results (see [project_progress.md](project_progress.md))

