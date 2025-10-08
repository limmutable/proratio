# Proratio Troubleshooting Guide

This guide covers common issues and their solutions when setting up and running Proratio.

---

## Installation Issues

### 1. `docker-compose: command not found`

**Symptom:**
```bash
$ docker-compose up -d postgres redis
zsh: command not found: docker-compose
```

**Cause:** Docker Desktop is not installed on your system.

**Solution:**
```bash
# Install Docker Desktop (includes Docker Compose)
brew install --cask docker

# Open Docker Desktop from Applications to start the Docker daemon

# Verify installation
docker --version
docker-compose --version
```

**Alternative:** If you have Docker but not Docker Compose:
```bash
# Install Docker Compose separately
brew install docker-compose
```

---

### 2. `ModuleNotFoundError: No module named 'ccxt'`

**Symptom:**
```bash
$ python scripts/download_historical_data.py
ModuleNotFoundError: No module named 'ccxt'
```

**Cause:** Running the script with system Python instead of the UV-managed environment.

**Solution:**
```bash
# ✅ CORRECT: Always use UV to run Python scripts
uv run python scripts/download_historical_data.py

# ❌ WRONG: This uses system Python (3.9.6) without dependencies
python scripts/download_historical_data.py
```

**Why this happens:**
- The project uses UV for Python environment management
- System Python (`/usr/bin/python3`) doesn't have project dependencies
- UV manages a project-specific `.venv/` with all packages installed

**Verify which Python is being used:**
```bash
which python           # Shows system Python
uv run which python    # Shows UV's Python in .venv/
```

---

### 3. Database error: "relation 'ohlcv' does not exist"

**Symptom:**
```bash
✗ Error downloading BTC/USDT_1h: relation "ohlcv" does not exist
LINE 2: INSERT INTO ohlcv (exchange, pair, timeframe, ti...
```

**Cause:** PostgreSQL database tables haven't been created yet.

**Solution:**
```bash
# 1. Ensure PostgreSQL is running
docker ps  # Should show proratio_postgres container

# 2. Initialize database schema
docker exec -i proratio_postgres psql -U proratio -d proratio < proratio_core/data/schema.sql

# 3. Verify tables were created
docker exec -it proratio_postgres psql -U proratio -d proratio -c "\dt"

# Expected output:
#             List of relations
#  Schema |      Name       | Type  |  Owner
# --------+-----------------+-------+---------
#  public | ai_signals      | table | proratio
#  public | ohlcv           | table | proratio
#  public | system_metadata | table | proratio
#  public | trades          | table | proratio
```

**If schema initialization fails:**
```bash
# Check PostgreSQL logs
docker logs proratio_postgres

# Restart PostgreSQL
docker-compose restart postgres

# Try again
docker exec -i proratio_postgres psql -U proratio -d proratio < proratio_core/data/schema.sql
```

---

### 4. PostgreSQL connection refused

**Symptom:**
```bash
psycopg2.OperationalError: connection to server at "localhost" (::1), port 5432 failed: Connection refused
```

**Cause:** PostgreSQL container is not running.

**Solution:**
```bash
# 1. Check if containers are running
docker ps

# 2. If not running, start them
docker-compose up -d postgres redis

# 3. Verify they're running
docker ps
# Should show:
# - proratio_postgres (port 5432)
# - proratio_redis (port 6379)

# 4. Check container logs
docker logs proratio_postgres
docker logs proratio_redis
```

**If containers fail to start:**
```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Start fresh
docker-compose up -d postgres redis
```

---

## Runtime Issues

### 5. Freqtrade data download fails

**Symptom:**
```bash
freqtrade download-data: Error downloading data from Binance
```

**Solutions:**

**Option A: Use Proratio's custom data downloader**
```bash
# Uses CCXT to download to PostgreSQL
uv run python scripts/download_historical_data.py
```

**Option B: Fix Freqtrade download**
```bash
# Ensure testnet mode (if using testnet)
export BINANCE_TESTNET=true

# Try with fewer days first
freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT \
  --timeframe 4h \
  --days 30 \
  --userdir user_data
```

---

### 6. Import errors: `Cannot import proratio modules`

**Symptom:**
```python
from proratio_core.config import get_settings
ModuleNotFoundError: No module named 'proratio_core'
```

**Solution:**
```bash
# 1. Ensure you're in the project root
pwd  # Should show /Users/jlim/Projects/proratio

# 2. Use UV to run scripts
uv run python scripts/your_script.py

# 3. For interactive Python/Jupyter
uv run jupyter lab
uv run python
```

**For pytest:**
```bash
# Pytest automatically adds project root to PYTHONPATH
pytest

# Or explicitly with UV
uv run pytest
```

---

### 7. UV command not found

**Symptom:**
```bash
$ uv run python script.py
zsh: command not found: uv
```

**Solution:**
```bash
# Install UV (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv

# Verify installation
uv --version

# Initialize project
uv python install 3.13
uv python pin 3.13
uv pip install -r requirements.txt
```

---

## Data Management Issues

### 8. "Inserted 0 records" when downloading data

**Symptom:**
```bash
✓ Inserted 0 new records (duplicates skipped)
```

**Cause:** Data already exists in the database (this is normal behavior).

**To verify:**
```bash
# Check data status
uv run python scripts/download_historical_data.py

# View download summary at the end:
# ======================================================================
# DATA STATUS
# ======================================================================
# BTC/USDT 1h   - 17,280 records, latest: 2025-10-08 11:00:00
```

**To force re-download (deletes existing data):**
```bash
# Connect to PostgreSQL
docker exec -it proratio_postgres psql -U proratio -d proratio

# Delete specific pair/timeframe
DELETE FROM ohlcv WHERE exchange='binance' AND pair='BTC/USDT' AND timeframe='1h';

# Or delete all OHLCV data
TRUNCATE TABLE ohlcv;

# Exit
\q

# Re-download
uv run python scripts/download_historical_data.py
```

---

### 9. Data export to Freqtrade fails

**Symptom:**
```bash
No data found in PostgreSQL for export
```

**Solution:**
```bash
# 1. Verify data exists in PostgreSQL
docker exec -it proratio_postgres psql -U proratio -d proratio

# Check record count
SELECT COUNT(*) FROM ohlcv;

# Exit
\q

# 2. If no data, download first
uv run python scripts/download_historical_data.py

# 3. Then export
uv run python scripts/export_data_for_freqtrade.py
```

---

## Environment Issues

### 10. `.env` file not loading

**Symptom:**
```python
Settings validation error: OPENAI_API_KEY field required
```

**Solution:**
```bash
# 1. Ensure .env exists
ls -la .env

# 2. If not, create from template
cp .env.example .env

# 3. Edit with your API keys
nano .env

# 4. Verify format (no spaces around =)
# ✅ CORRECT:
OPENAI_API_KEY=sk-abc123
DATABASE_URL=postgresql://proratio:password@localhost:5432/proratio

# ❌ WRONG:
OPENAI_API_KEY = sk-abc123  # spaces
DATABASE_URL = postgresql://proratio:password@localhost:5432/proratio
```

---

## Docker Issues

### 11. Container names conflict

**Symptom:**
```bash
Error: Container name "proratio_postgres" already in use
```

**Solution:**
```bash
# Stop and remove existing containers
docker-compose down

# If still issues, force remove
docker rm -f proratio_postgres proratio_redis

# Start fresh
docker-compose up -d postgres redis
```

---

### 12. Port already in use (5432 or 6379)

**Symptom:**
```bash
Error: bind: address already in use (port 5432)
```

**Cause:** Another PostgreSQL/Redis instance is running on the same port.

**Solution:**
```bash
# Find what's using the port
lsof -i :5432  # For PostgreSQL
lsof -i :6379  # For Redis

# Stop the conflicting service
# For Homebrew PostgreSQL:
brew services stop postgresql

# Or change Proratio's port in docker-compose.yml:
# postgres:
#   ports:
#     - "5433:5432"  # Use 5433 instead of 5432

# Update .env DATABASE_URL accordingly:
# DATABASE_URL=postgresql://proratio:password@localhost:5433/proratio
```

---

## Testing Issues

### 13. Tests fail with import errors

**Symptom:**
```bash
$ pytest
ModuleNotFoundError: No module named 'proratio_signals'
```

**Solution:**
```bash
# Run pytest with UV
uv run pytest

# Or run specific tests
uv run pytest tests/test_signals/
uv run pytest tests/test_core/test_config.py
```

---

### 14. Database tests fail

**Symptom:**
```bash
Tests fail with "could not connect to database"
```

**Solution:**
```bash
# 1. Ensure test database is running
docker ps | grep postgres

# 2. Tests should use separate test database
# Check tests/conftest.py for test database setup

# 3. Some tests may need PostgreSQL running
docker-compose up -d postgres

# 4. Run tests
uv run pytest
```

---

## Quick Diagnostic Commands

Run these commands to check system health:

```bash
# 1. Check Docker
docker ps
docker-compose ps

# 2. Check database
docker exec -it proratio_postgres psql -U proratio -d proratio -c "SELECT COUNT(*) FROM ohlcv;"

# 3. Check Python environment
uv run python --version
uv run python -c "import ccxt; print('ccxt:', ccxt.__version__)"

# 4. Check UV installation
uv --version
which uv

# 5. Check project structure
ls -la proratio_core/ proratio_signals/ proratio_quantlab/ proratio_tradehub/

# 6. Run minimal test
uv run python -c "from proratio_core.config.settings import get_settings; print('✅ Config loaded')"
```

---

## Still Having Issues?

1. **Check logs:**
   ```bash
   # Docker logs
   docker logs proratio_postgres
   docker logs proratio_redis

   # Freqtrade logs
   tail -f user_data/logs/freqtrade.log
   ```

2. **Verify prerequisites:**
   ```bash
   # Python version
   uv run python --version  # Should be 3.11+

   # Docker version
   docker --version
   docker-compose --version

   # UV version
   uv --version
   ```

3. **Clean installation:**
   ```bash
   # Stop all services
   docker-compose down -v

   # Remove virtual environment
   rm -rf .venv/

   # Reinstall
   uv python install 3.13
   uv pip install -r requirements.txt

   # Start fresh
   docker-compose up -d postgres redis
   docker exec -i proratio_postgres psql -U proratio -d proratio < proratio_core/data/schema.sql
   uv run python scripts/download_historical_data.py
   ```

4. **Review documentation:**
   - [QUICKSTART.md](./QUICKSTART.md) - Setup guide
   - [CLAUDE.md](../CLAUDE.md) - Developer guide
   - [PLAN.md](../PLAN.md) - Implementation plan

---

**Last Updated:** 2025-10-08
