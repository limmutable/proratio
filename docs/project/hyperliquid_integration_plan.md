# Hyperliquid Integration Plan

**Phase 5.1: Multi-Exchange Support - Hyperliquid Integration**

**Date**: 2025-10-17
**Objective**: Add Hyperliquid spot and perpetuals trading support alongside existing Binance integration, with Hyperliquid as the default exchange.

---

## 📋 Overview

### What is Hyperliquid?

Hyperliquid is a high-performance L1 blockchain with a fully on-chain order book and matching engine. It offers:
- **Perpetual Futures**: Up to 50x leverage
- **Spot Trading**: Direct token trading
- **Fully on-chain**: All trades settled on L1
- **Low fees**: Maker rebates, competitive taker fees
- **No gas fees**: Users don't pay gas for trading
- **Native APIs**: Purpose-built for trading

### Why Add Hyperliquid?

1. **Lower Fees**: Maker rebates vs Binance fees
2. **On-Chain Transparency**: All trades verifiable on-chain
3. **No KYC Required**: Decentralized access
4. **Better for Algorithmic Trading**: Native API, no throttling like CEXs
5. **Perpetuals Focus**: Built for leverage trading from the ground up
6. **Portfolio Diversification**: Multi-exchange reduces single-point-of-failure risk

---

## 🎯 Goals

### Primary Goals
1. ✅ Add Hyperliquid as a supported exchange alongside Binance
2. ✅ Support both Spot and Perpetuals trading on Hyperliquid
3. ✅ Make Hyperliquid the **default exchange** in configuration
4. ✅ Add CLI command to switch between Binance and Hyperliquid
5. ✅ Maintain backward compatibility with existing Binance integration

### Success Criteria
- [ ] Can download historical data from Hyperliquid
- [ ] Can place orders on Hyperliquid testnet
- [ ] Can switch exchanges via CLI command
- [ ] All existing strategies work with both exchanges
- [ ] Paper trading works with Hyperliquid
- [ ] Live trading works with Hyperliquid (testnet validation)

---

## 📚 API Documentation References

### Official Resources
- **Main Documentation**: https://hyperliquid.gitbook.io/hyperliquid-docs
- **API Docs**: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
- **Python SDK**: https://github.com/hyperliquid-dex/hyperliquid-python-sdk
- **Builder Tools**: https://hyperliquid.gitbook.io/hyperliquid-docs/builder-tools/hypercore-tools

### API Endpoints
- **Mainnet**: `https://api.hyperliquid.xyz`
- **Testnet**: `https://api.hyperliquid-testnet.xyz`

### Key APIs
1. **Info Endpoint** (`POST /info`):
   - Market data (allMids, l2Book, candleSnapshot)
   - User data (openOrders, userFills, portfolio)
   - Rate limits (userRateLimit)

2. **Exchange Endpoint** (`POST /exchange`):
   - Order placement (limit, market, trigger)
   - Order cancellation
   - Order modification
   - Requires signed requests with nonce + signature

3. **WebSocket API**:
   - Real-time market data
   - Order updates
   - Subscription-based

### Community Resources
- **CCXT Integration**: Available in CCXT library
- **TypeScript SDKs**:
  - https://github.com/nktkas/hyperliquid
  - https://github.com/nomeida/hyperliquid
- **Explorers**:
  - https://app.hyperliquid.xyz
  - Flowscan
  - HypurrScan

---

## 🏗️ Architecture Design

### Current Architecture (Binance-only)
```
┌─────────────────────────────────────┐
│  Proratio Trading System            │
│                                     │
│  ┌───────────────────────────────┐ │
│  │  BinanceCollector (CCXT)      │ │
│  └───────────────────────────────┘ │
│              ↓                      │
│  ┌───────────────────────────────┐ │
│  │  DatabaseStorage (PostgreSQL) │ │
│  └───────────────────────────────┘ │
│              ↓                      │
│  ┌───────────────────────────────┐ │
│  │  Freqtrade (Execution)        │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

### New Architecture (Multi-Exchange)
```
┌─────────────────────────────────────────────────────┐
│  Proratio Trading System                            │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  ExchangeFactory                            │   │
│  │  ┌────────────────┐  ┌───────────────────┐ │   │
│  │  │ BinanceAdapter │  │ HyperliquidAdapter│ │   │
│  │  └────────────────┘  └───────────────────┘ │   │
│  └─────────────────────────────────────────────┘   │
│              ↓                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │  UnifiedDataCollector                       │   │
│  │  (works with any exchange adapter)          │   │
│  └─────────────────────────────────────────────┘   │
│              ↓                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │  DatabaseStorage (PostgreSQL)               │   │
│  │  + exchange_name column for multi-exchange  │   │
│  └─────────────────────────────────────────────┘   │
│              ↓                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │  Trading Execution Layer                    │   │
│  │  ┌────────────┐  ┌────────────────────────┐ │   │
│  │  │ Freqtrade  │  │ HyperliquidExecutor   │ │   │
│  │  │ (Binance)  │  │ (Native SDK)          │ │   │
│  │  └────────────┘  └────────────────────────┘ │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Design Principles

1. **Abstraction Layer**: Create `BaseExchangeAdapter` interface that both Binance and Hyperliquid implement
2. **Factory Pattern**: `ExchangeFactory` creates the appropriate adapter based on config
3. **Unified Interface**: All exchange-specific logic hidden behind common interface
4. **Database Schema**: Add `exchange` column to track data source
5. **Configuration-Driven**: Switch exchanges via config file + CLI command
6. **Backward Compatibility**: Existing code continues to work with Binance

---

## 📝 Implementation Tasks

### Phase 5.1.1: Core Infrastructure (Week 1)

#### Task 1: Create Exchange Adapter Interface
**File**: `proratio_utilities/exchanges/base.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd

class BaseExchangeAdapter(ABC):
    """Abstract base class for exchange adapters"""

    @abstractmethod
    def fetch_ohlcv(self, pair: str, timeframe: str, since: datetime, limit: int) -> pd.DataFrame:
        """Fetch OHLCV data"""
        pass

    @abstractmethod
    def fetch_ticker(self, pair: str) -> Dict:
        """Fetch current ticker"""
        pass

    @abstractmethod
    def fetch_order_book(self, pair: str, limit: int = 20) -> Dict:
        """Fetch order book"""
        pass

    @abstractmethod
    def place_order(self, pair: str, side: str, order_type: str, amount: float, price: Optional[float] = None) -> Dict:
        """Place an order"""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str, pair: str) -> Dict:
        """Cancel an order"""
        pass

    @abstractmethod
    def fetch_open_orders(self, pair: Optional[str] = None) -> List[Dict]:
        """Fetch open orders"""
        pass

    @abstractmethod
    def fetch_balance(self) -> Dict:
        """Fetch account balance"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Exchange name"""
        pass

    @property
    @abstractmethod
    def supports_perpetuals(self) -> bool:
        """Whether exchange supports perpetual futures"""
        pass
```

**Estimated Time**: 2 hours

---

#### Task 2: Implement Binance Adapter
**File**: `proratio_utilities/exchanges/binance_adapter.py`

Wrap existing `BinanceCollector` in the new adapter interface.

```python
from .base import BaseExchangeAdapter
from ..data.collectors import BinanceCollector
import ccxt
import pandas as pd

class BinanceAdapter(BaseExchangeAdapter):
    """Binance exchange adapter using CCXT"""

    def __init__(self, testnet: bool = False):
        self.collector = BinanceCollector(testnet=testnet)
        self.exchange = self.collector.exchange
        self._testnet = testnet

    @property
    def name(self) -> str:
        return "binance" if not self._testnet else "binance_testnet"

    @property
    def supports_perpetuals(self) -> bool:
        return True  # Binance supports futures

    def fetch_ohlcv(self, pair: str, timeframe: str, since: datetime, limit: int) -> pd.DataFrame:
        # Delegate to existing BinanceCollector
        data = self.collector.fetch_ohlcv(pair, timeframe, since, limit)
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df

    # ... implement other methods using CCXT
```

**Estimated Time**: 4 hours

---

#### Task 3: Implement Hyperliquid Adapter
**File**: `proratio_utilities/exchanges/hyperliquid_adapter.py`

Use the official Hyperliquid Python SDK.

```python
from .base import BaseExchangeAdapter
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

class HyperliquidAdapter(BaseExchangeAdapter):
    """Hyperliquid exchange adapter using official Python SDK"""

    def __init__(self, testnet: bool = False, api_wallet: Optional[str] = None):
        """
        Initialize Hyperliquid adapter

        Args:
            testnet: Use testnet if True
            api_wallet: API wallet address (for authenticated requests)
        """
        self.api_url = constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL
        self.info = Info(self.api_url, skip_ws=True)
        self.exchange = None
        self._testnet = testnet

        if api_wallet:
            # Initialize exchange for trading (requires private key)
            from proratio_utilities.config.settings import get_settings
            settings = get_settings()
            self.exchange = Exchange(
                api_wallet,
                settings.hyperliquid_secret_key,
                base_url=self.api_url
            )

    @property
    def name(self) -> str:
        return "hyperliquid" if not self._testnet else "hyperliquid_testnet"

    @property
    def supports_perpetuals(self) -> bool:
        return True

    def fetch_ohlcv(self, pair: str, timeframe: str, since: datetime, limit: int) -> pd.DataFrame:
        """
        Fetch OHLCV data from Hyperliquid

        Args:
            pair: Trading pair (e.g., 'BTC')  # Note: Hyperliquid uses coin names, not pairs
            timeframe: Timeframe ('1m', '1h', '1d')
            since: Start datetime
            limit: Number of candles

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        # Convert pair format (BTC/USDT -> BTC)
        coin = pair.split('/')[0] if '/' in pair else pair

        # Convert timeframe to Hyperliquid format
        interval_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d'
        }
        interval = interval_map.get(timeframe, '1h')

        # Fetch candle snapshot
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int(since.timestamp() * 1000)

        candles = self.info.candle_snapshot(
            coin=coin,
            interval=interval,
            startTime=start_time,
            endTime=end_time
        )

        # Convert to DataFrame
        df = pd.DataFrame(candles)
        df.rename(columns={
            't': 'timestamp',
            'o': 'open',
            'h': 'high',
            'l': 'low',
            'c': 'close',
            'v': 'volume'
        }, inplace=True)

        # Convert timestamp from ms to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        return df.tail(limit)

    def fetch_ticker(self, pair: str) -> Dict:
        """Fetch current ticker"""
        coin = pair.split('/')[0] if '/' in pair else pair
        all_mids = self.info.all_mids()
        return {'last': all_mids.get(coin)}

    def fetch_order_book(self, pair: str, limit: int = 20) -> Dict:
        """Fetch order book"""
        coin = pair.split('/')[0] if '/' in pair else pair
        book = self.info.l2_snapshot(coin)
        return {
            'bids': book['levels'][0][:limit],  # Buy side
            'asks': book['levels'][1][:limit]   # Sell side
        }

    def place_order(self, pair: str, side: str, order_type: str, amount: float, price: Optional[float] = None) -> Dict:
        """Place an order"""
        if not self.exchange:
            raise ValueError("Exchange not initialized for trading")

        coin = pair.split('/')[0] if '/' in pair else pair
        is_buy = (side.lower() == 'buy')

        # Get asset index
        meta = self.info.meta()
        asset_idx = None
        for i, asset in enumerate(meta['universe']):
            if asset['name'] == coin:
                asset_idx = i
                break

        if asset_idx is None:
            raise ValueError(f"Asset {coin} not found")

        # Place order
        if order_type.lower() == 'limit':
            order = self.exchange.order(
                coin=coin,
                is_buy=is_buy,
                sz=amount,
                limit_px=price,
                order_type={'limit': {'tif': 'Gtc'}}
            )
        else:  # market order
            order = self.exchange.market_order(
                coin=coin,
                is_buy=is_buy,
                sz=amount
            )

        return order

    def cancel_order(self, order_id: str, pair: str) -> Dict:
        """Cancel an order"""
        if not self.exchange:
            raise ValueError("Exchange not initialized for trading")

        coin = pair.split('/')[0] if '/' in pair else pair
        return self.exchange.cancel(coin, order_id)

    def fetch_open_orders(self, pair: Optional[str] = None) -> List[Dict]:
        """Fetch open orders"""
        if not self.exchange:
            raise ValueError("Exchange not initialized for trading")

        # Hyperliquid requires user address
        user_state = self.info.user_state(self.exchange.wallet.address)
        return user_state.get('openOrders', [])

    def fetch_balance(self) -> Dict:
        """Fetch account balance"""
        if not self.exchange:
            raise ValueError("Exchange not initialized for trading")

        user_state = self.info.user_state(self.exchange.wallet.address)
        return {
            'total': user_state.get('marginSummary', {}).get('accountValue', 0),
            'free': user_state.get('withdrawable', 0),
            'used': user_state.get('marginSummary', {}).get('totalMarginUsed', 0)
        }
```

**Estimated Time**: 8 hours

---

#### Task 4: Create Exchange Factory
**File**: `proratio_utilities/exchanges/factory.py`

```python
from typing import Optional
from .base import BaseExchangeAdapter
from .binance_adapter import BinanceAdapter
from .hyperliquid_adapter import HyperliquidAdapter

class ExchangeFactory:
    """Factory for creating exchange adapters"""

    _adapters = {
        'binance': BinanceAdapter,
        'hyperliquid': HyperliquidAdapter,
    }

    @classmethod
    def create(cls, exchange_name: str, testnet: bool = False, **kwargs) -> BaseExchangeAdapter:
        """
        Create an exchange adapter

        Args:
            exchange_name: Name of exchange ('binance' or 'hyperliquid')
            testnet: Use testnet if True
            **kwargs: Additional arguments for the adapter

        Returns:
            Exchange adapter instance
        """
        exchange_name = exchange_name.lower()

        if exchange_name not in cls._adapters:
            raise ValueError(f"Unsupported exchange: {exchange_name}")

        adapter_class = cls._adapters[exchange_name]
        return adapter_class(testnet=testnet, **kwargs)

    @classmethod
    def supported_exchanges(cls) -> list:
        """Get list of supported exchanges"""
        return list(cls._adapters.keys())
```

**Estimated Time**: 2 hours

---

### Phase 5.1.2: Configuration Updates (Week 1)

#### Task 5: Update .env Configuration
**File**: `.env.example`

Add Hyperliquid API credentials:

```bash
# ============================================
# EXCHANGE SELECTION
# ============================================
DEFAULT_EXCHANGE=hyperliquid  # Options: binance, hyperliquid
EXCHANGE_TESTNET=true  # Use testnet for selected exchange

# ============================================
# BINANCE API
# ============================================
BINANCE_API_KEY=your-binance-api-key
BINANCE_API_SECRET=your-binance-secret
BINANCE_TESTNET=true

# ============================================
# HYPERLIQUID API
# ============================================
HYPERLIQUID_API_WALLET=0x...  # Your Hyperliquid wallet address
HYPERLIQUID_SECRET_KEY=0x...  # Your private key (keep secret!)
HYPERLIQUID_TESTNET=true
```

**Estimated Time**: 1 hour

---

#### Task 6: Update Settings Module
**File**: `proratio_utilities/config/settings.py`

Add Hyperliquid settings:

```python
class Settings(BaseSettings):
    # Existing fields...

    # Exchange selection
    default_exchange: str = "hyperliquid"
    exchange_testnet: bool = True

    # Hyperliquid API
    hyperliquid_api_wallet: Optional[str] = None
    hyperliquid_secret_key: Optional[str] = None
    hyperliquid_testnet: bool = True
```

**Estimated Time**: 1 hour

---

### Phase 5.1.3: Database Schema Updates (Week 1)

#### Task 7: Add Exchange Column to Database
**File**: `proratio_utilities/data/schema.sql`

```sql
-- Add exchange column to ohlcv_data table
ALTER TABLE ohlcv_data
ADD COLUMN IF NOT EXISTS exchange VARCHAR(50) DEFAULT 'binance';

-- Create index on exchange for faster queries
CREATE INDEX IF NOT EXISTS idx_ohlcv_exchange ON ohlcv_data(exchange);

-- Update existing records to have 'binance' as exchange
UPDATE ohlcv_data SET exchange = 'binance' WHERE exchange IS NULL;
```

**Migration Script**: `scripts/migrations/add_exchange_column.py`

```python
import psycopg2
from proratio_utilities.config.settings import get_settings

def migrate():
    settings = get_settings()
    conn = psycopg2.connect(settings.database_url)
    cur = conn.cursor()

    # Add column
    cur.execute("""
        ALTER TABLE ohlcv_data
        ADD COLUMN IF NOT EXISTS exchange VARCHAR(50) DEFAULT 'binance'
    """)

    # Create index
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ohlcv_exchange ON ohlcv_data(exchange)
    """)

    # Update existing records
    cur.execute("""
        UPDATE ohlcv_data SET exchange = 'binance' WHERE exchange IS NULL
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Migration complete: added exchange column")

if __name__ == "__main__":
    migrate()
```

**Estimated Time**: 2 hours

---

### Phase 5.1.4: CLI Updates (Week 2)

#### Task 8: Add Exchange Command
**File**: `proratio_cli/commands/exchange.py` (NEW)

```python
import typer
from rich.console import Console
from rich.table import Table
from proratio_utilities.config.settings import get_settings
from proratio_utilities.exchanges.factory import ExchangeFactory

app = typer.Typer()
console = Console()

@app.command()
def list():
    """List all supported exchanges"""
    exchanges = ExchangeFactory.supported_exchanges()
    settings = get_settings()
    current = settings.default_exchange

    table = Table(title="Supported Exchanges")
    table.add_column("Exchange", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Perpetuals", style="yellow")

    for exchange_name in exchanges:
        adapter = ExchangeFactory.create(exchange_name, testnet=True)
        is_current = "✓ Current" if exchange_name == current else ""
        perps = "✓" if adapter.supports_perpetuals else "✗"
        table.add_row(exchange_name.title(), is_current, perps)

    console.print(table)

@app.command()
def set(
    name: str = typer.Argument(..., help="Exchange name (binance or hyperliquid)"),
    testnet: bool = typer.Option(True, help="Use testnet")
):
    """Set default exchange"""
    if name.lower() not in ExchangeFactory.supported_exchanges():
        console.print(f"[red]❌ Unsupported exchange: {name}[/red]")
        console.print(f"Supported: {', '.join(ExchangeFactory.supported_exchanges())}")
        raise typer.Exit(1)

    # Update .env file
    import os
    from pathlib import Path

    env_file = Path('.env')
    if env_file.exists():
        content = env_file.read_text()
        # Update DEFAULT_EXCHANGE line
        lines = content.split('\n')
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('DEFAULT_EXCHANGE='):
                lines[i] = f'DEFAULT_EXCHANGE={name.lower()}'
                updated = True
            elif line.startswith('EXCHANGE_TESTNET='):
                lines[i] = f'EXCHANGE_TESTNET={str(testnet).lower()}'

        if not updated:
            lines.append(f'DEFAULT_EXCHANGE={name.lower()}')
            lines.append(f'EXCHANGE_TESTNET={str(testnet).lower()}')

        env_file.write_text('\n'.join(lines))

    console.print(f"[green]✓ Default exchange set to: {name}[/green]")
    console.print(f"[yellow]⚠ Restart the CLI for changes to take effect[/yellow]")

@app.command()
def current():
    """Show current exchange"""
    settings = get_settings()
    console.print(f"Current exchange: [cyan]{settings.default_exchange}[/cyan]")
    console.print(f"Testnet mode: [yellow]{settings.exchange_testnet}[/yellow]")

@app.command()
def status(
    exchange: str = typer.Option(None, help="Specific exchange to check")
):
    """Check exchange connection status"""
    settings = get_settings()
    exchange_name = exchange or settings.default_exchange

    try:
        adapter = ExchangeFactory.create(
            exchange_name,
            testnet=settings.exchange_testnet
        )

        # Test connection by fetching ticker
        ticker = adapter.fetch_ticker('BTC/USDT')

        console.print(f"[green]✓ {exchange_name.title()} connected[/green]")
        console.print(f"  BTC/USDT price: ${ticker.get('last', 'N/A')}")

    except Exception as e:
        console.print(f"[red]❌ {exchange_name.title()} connection failed[/red]")
        console.print(f"  Error: {str(e)}")
```

**Estimated Time**: 4 hours

---

#### Task 9: Update CLI Main App
**File**: `proratio_cli/app.py`

Add exchange command to CLI:

```python
from proratio_cli.commands import exchange

# ... existing imports

app = typer.Typer()
app.add_typer(exchange.app, name="exchange", help="Manage exchanges")
# ... existing command additions
```

**Estimated Time**: 1 hour

---

### Phase 5.1.5: Data Collection Updates (Week 2)

#### Task 10: Update Data Loaders
**File**: `proratio_utilities/data/loaders.py`

Refactor to use ExchangeFactory:

```python
from proratio_utilities.exchanges.factory import ExchangeFactory
from proratio_utilities.config.settings import get_settings

class DataLoader:
    def __init__(self, exchange: Optional[str] = None, testnet: bool = False):
        """
        Initialize data loader

        Args:
            exchange: Exchange name (default: from settings)
            testnet: Use testnet (default: from settings)
        """
        settings = get_settings()
        self.exchange_name = exchange or settings.default_exchange
        self.testnet = testnet or settings.exchange_testnet
        self.adapter = ExchangeFactory.create(self.exchange_name, testnet=self.testnet)
        self.storage = DatabaseStorage()

    def download_and_store(
        self,
        pair: str,
        timeframe: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Download data using selected exchange"""
        df = self.adapter.fetch_ohlcv(
            pair=pair,
            timeframe=timeframe,
            since=start_date,
            limit=1000
        )

        # Store with exchange tag
        return self.storage.insert_ohlcv(
            exchange=self.exchange_name,
            pair=pair,
            timeframe=timeframe,
            data=df
        )
```

**Estimated Time**: 4 hours

---

#### Task 11: Update Storage Layer
**File**: `proratio_utilities/data/storage.py`

Add exchange parameter to all methods:

```python
def insert_ohlcv(
    self,
    exchange: str,  # NEW parameter
    pair: str,
    timeframe: str,
    data: pd.DataFrame
) -> int:
    """Insert OHLCV data with exchange tag"""
    # ... existing logic but include exchange in INSERT
```

**Estimated Time**: 2 hours

---

### Phase 5.1.6: Testing & Validation (Week 3)

#### Task 12: Create Test Script
**File**: `scripts/test_hyperliquid_integration.py`

```python
#!/usr/bin/env python3
"""
Test Hyperliquid integration

Tests:
1. Connection to Hyperliquid testnet
2. Fetch market data
3. Fetch OHLCV data
4. Place test order (testnet)
5. Cancel test order
"""

from proratio_utilities.exchanges.factory import ExchangeFactory
from datetime import datetime, timedelta

def test_connection():
    """Test basic connection"""
    print("Testing Hyperliquid connection...")
    adapter = ExchangeFactory.create('hyperliquid', testnet=True)
    ticker = adapter.fetch_ticker('BTC')
    print(f"✓ BTC price: ${ticker['last']}")

def test_ohlcv():
    """Test OHLCV data fetching"""
    print("\nTesting OHLCV data...")
    adapter = ExchangeFactory.create('hyperliquid', testnet=True)
    since = datetime.now() - timedelta(days=7)
    df = adapter.fetch_ohlcv('BTC', '1h', since, 100)
    print(f"✓ Fetched {len(df)} candles")
    print(df.head())

def test_order_book():
    """Test order book"""
    print("\nTesting order book...")
    adapter = ExchangeFactory.create('hyperliquid', testnet=True)
    book = adapter.fetch_order_book('BTC', limit=5)
    print(f"✓ Bids: {len(book['bids'])}, Asks: {len(book['asks'])}")

def test_trading():
    """Test order placement (testnet only!)"""
    print("\nTesting order placement (testnet)...")
    from proratio_utilities.config.settings import get_settings
    settings = get_settings()

    if not settings.hyperliquid_api_wallet:
        print("⚠ Skipping: No API wallet configured")
        return

    adapter = ExchangeFactory.create(
        'hyperliquid',
        testnet=True,
        api_wallet=settings.hyperliquid_api_wallet
    )

    # Place a small test order
    order = adapter.place_order(
        pair='BTC',
        side='buy',
        order_type='limit',
        amount=0.001,  # Small size
        price=10000     # Far from market
    )
    print(f"✓ Order placed: {order}")

    # Cancel it
    if order.get('orderId'):
        cancel_result = adapter.cancel_order(order['orderId'], 'BTC')
        print(f"✓ Order cancelled: {cancel_result}")

if __name__ == "__main__":
    test_connection()
    test_ohlcv()
    test_order_book()
    test_trading()

    print("\n✅ All tests passed!")
```

**Estimated Time**: 4 hours

---

#### Task 13: Integration Tests
**File**: `tests/test_exchanges/test_hyperliquid_adapter.py`

Full pytest test suite for Hyperliquid adapter.

**Estimated Time**: 6 hours

---

### Phase 5.1.7: Documentation (Week 3)

#### Task 14: Update Documentation
**Files to Update**:
- `README.md` - Add Hyperliquid support to features
- `docs/getting_started.md` - Add Hyperliquid setup steps
- `docs/guides/fresh_machine_setup.md` - Include Hyperliquid credentials
- Create `docs/guides/hyperliquid_trading_guide.md` - Complete Hyperliquid guide

**Estimated Time**: 4 hours

---

## 📊 Implementation Timeline

### Week 1: Core Infrastructure
- Days 1-2: Tasks 1-4 (Adapters & Factory)
- Days 3-4: Tasks 5-6 (Configuration)
- Day 5: Task 7 (Database schema)

### Week 2: CLI & Data Collection
- Days 1-2: Tasks 8-9 (CLI commands)
- Days 3-4: Tasks 10-11 (Data loaders)
- Day 5: Buffer/polish

### Week 3: Testing & Documentation
- Days 1-2: Tasks 12-13 (Testing)
- Days 3-4: Task 14 (Documentation)
- Day 5: Final validation & deployment

**Total Estimated Time**: ~55 hours over 3 weeks

---

## 🔧 Technical Considerations

### Hyperliquid-Specific Details

1. **Pair Format**: Hyperliquid uses coin names (`BTC`) not pairs (`BTC/USDT`)
   - All perpetuals are settled in USD
   - Spot uses native token pairs

2. **Asset IDs**: Each tradable asset has a numeric ID
   - Must query `meta()` endpoint to get mappings

3. **Order Types**:
   - Limit orders: `{limit: {tif: 'Gtc'}}`
   - Market orders: Use `market_order()` method
   - Trigger orders: `{trigger: {triggerPx, isMarket, tpsl}}`

4. **Authentication**:
   - Requires wallet address + private key
   - All requests signed with EIP-712
   - Python SDK handles signing automatically

5. **Rate Limits**:
   - Info endpoint: ~10 req/sec
   - Exchange endpoint: ~5 req/sec
   - WebSocket: Unlimited subscriptions

6. **Testnet**:
   - Separate testnet at `https://api.hyperliquid-testnet.xyz`
   - Get testnet funds from faucet
   - Testnet has same API as mainnet

---

## ⚠️ Migration Path

### For Existing Users

1. **Backward Compatibility**: All existing Binance code continues to work
2. **Gradual Migration**: Can test Hyperliquid while keeping Binance active
3. **Data Separation**: Each exchange's data stored separately in DB
4. **Configuration**: Simple CLI command to switch: `/exchange set hyperliquid`

### Migration Steps
```bash
# 1. Keep existing Binance setup
# No changes needed - everything works as before

# 2. Add Hyperliquid credentials to .env
HYPERLIQUID_API_WALLET=0x...
HYPERLIQUID_SECRET_KEY=0x...

# 3. Test Hyperliquid connection
./start.sh
proratio> /exchange status hyperliquid

# 4. Download Hyperliquid data
proratio> /data download --exchange hyperliquid --pair BTC --days 180

# 5. Switch to Hyperliquid as default
proratio> /exchange set hyperliquid

# 6. Run strategies on Hyperliquid
proratio> /strategy validate a014_hybrid-ml-llm --exchange hyperliquid
```

---

## 🎯 Success Metrics

### Phase 5.1 Complete When:
- [ ] Can fetch OHLCV data from Hyperliquid
- [ ] Can place/cancel orders on Hyperliquid testnet
- [ ] CLI `/exchange` command works
- [ ] All 3 analysis scripts work with Hyperliquid data
- [ ] Paper trading works with Hyperliquid
- [ ] Documentation complete
- [ ] Tests passing (>90% coverage)

### Performance Targets:
- Data fetching: <1s for 1000 candles
- Order placement: <500ms
- CLI exchange switch: <1s

---

## 📝 Dependencies

### New Python Packages
```bash
# Add to requirements.txt
hyperliquid-python-sdk==0.5.0  # Official SDK
```

### API Requirements
- Hyperliquid wallet (testnet + mainnet)
- Private key (keep secret!)
- Testnet funds (from faucet)

---

## 🚀 Next Steps After Phase 5.1

### Phase 5.2: Advanced Features
- WebSocket real-time data
- Hyperliquid-specific strategies (funding arbitrage)
- Multi-exchange portfolio balancing
- Cross-exchange price comparison

### Phase 5.3: Live Trading
- 24-48 hour testnet validation
- Mainnet deployment with small capital
- Multi-exchange risk management

---

**Document Version**: 1.0
**Last Updated**: 2025-10-17
**Status**: Ready for Implementation
**Estimated Completion**: 3 weeks
