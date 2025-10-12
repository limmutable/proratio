"""
Dashboard Data Fetcher

Utilities for fetching real-time trading data from Freqtrade API,
database, and AI signal orchestrator.
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime
import sqlite3
from pathlib import Path

from proratio_utilities.config.trading_config import TradingConfig
from proratio_signals.orchestrator import SignalOrchestrator


class FreqtradeAPIClient:
    """Client for Freqtrade REST API"""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        username: str = "",
        password: str = "",
    ):
        """
        Initialize Freqtrade API client

        Args:
            base_url: Freqtrade API base URL
            username: API username (if auth enabled)
            password: API password (if auth enabled)
        """
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password) if username and password else None
        self.session = requests.Session()

    def _get(self, endpoint: str) -> Dict:
        """Make GET request to Freqtrade API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(url, auth=self.auth, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {endpoint}: {e}")
            return {}

    def _post(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make POST request to Freqtrade API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.post(url, json=data, auth=self.auth, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error posting to {endpoint}: {e}")
            return {}

    def get_status(self) -> Dict:
        """Get current bot status"""
        return self._get("/api/v1/status")

    def get_profit(self) -> Dict:
        """Get profit summary"""
        return self._get("/api/v1/profit")

    def get_performance(self) -> List[Dict]:
        """Get performance by pair"""
        return self._get("/api/v1/performance")

    def get_balance(self) -> Dict:
        """Get wallet balance"""
        return self._get("/api/v1/balance")

    def get_trades(self, limit: int = 50) -> Dict:
        """Get recent trades"""
        return self._get(f"/api/v1/trades?limit={limit}")

    def get_open_trades(self) -> List[Dict]:
        """Get currently open trades"""
        status = self.get_status()
        return status.get("data", []) if status else []

    def force_exit(self, trade_id: int) -> Dict:
        """Force exit a specific trade"""
        return self._post("/api/v1/forceexit", {"tradeid": trade_id})

    def force_exit_all(self) -> Dict:
        """Force exit all open trades"""
        return self._post("/api/v1/forceexit")

    def start_trading(self) -> Dict:
        """Start the trading bot"""
        return self._post("/api/v1/start")

    def stop_trading(self) -> Dict:
        """Stop the trading bot"""
        return self._post("/api/v1/stop")

    def reload_config(self) -> Dict:
        """Reload configuration"""
        return self._post("/api/v1/reload_config")


class TradeDatabaseReader:
    """Reader for Freqtrade trade database"""

    def __init__(self, db_path: str = "user_data/db/tradesv3.dryrun.sqlite"):
        """
        Initialize database reader

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        return sqlite3.connect(self.db_path)

    def get_all_trades(self, limit: int = 100) -> List[Dict]:
        """Get all trades from database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            id, pair, is_open, open_date, close_date,
            open_rate, close_rate, amount, stake_amount,
            close_profit, close_profit_abs
        FROM trades
        ORDER BY open_date DESC
        LIMIT ?
        """

        cursor.execute(query, (limit,))
        columns = [desc[0] for desc in cursor.description]
        trades = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return trades

    def get_open_trades(self) -> List[Dict]:
        """Get currently open trades"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            id, pair, open_date, open_rate, amount, stake_amount
        FROM trades
        WHERE is_open = 1
        ORDER BY open_date DESC
        """

        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        trades = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return trades

    def get_trade_statistics(self) -> Dict:
        """Get overall trade statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Total trades
        cursor.execute("SELECT COUNT(*) FROM trades WHERE is_open = 0")
        total_trades = cursor.fetchone()[0]

        # Winning trades
        cursor.execute(
            "SELECT COUNT(*) FROM trades WHERE is_open = 0 AND close_profit > 0"
        )
        winning_trades = cursor.fetchone()[0]

        # Losing trades
        cursor.execute(
            "SELECT COUNT(*) FROM trades WHERE is_open = 0 AND close_profit <= 0"
        )
        losing_trades = cursor.fetchone()[0]

        # Total profit
        cursor.execute("SELECT SUM(close_profit_abs) FROM trades WHERE is_open = 0")
        total_profit = cursor.fetchone()[0] or 0.0

        # Average profit
        cursor.execute(
            "SELECT AVG(close_profit) FROM trades WHERE is_open = 0 AND close_profit > 0"
        )
        avg_profit = cursor.fetchone()[0] or 0.0

        # Average loss
        cursor.execute(
            "SELECT AVG(close_profit) FROM trades WHERE is_open = 0 AND close_profit <= 0"
        )
        avg_loss = cursor.fetchone()[0] or 0.0

        conn.close()

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "total_profit": total_profit,
            "avg_profit": avg_profit * 100,  # Convert to percentage
            "avg_loss": avg_loss * 100,  # Convert to percentage
        }


class DashboardDataFetcher:
    """
    Main data fetcher for dashboard

    Aggregates data from multiple sources:
    - Freqtrade API (live trading status)
    - Trade Database (historical data)
    - AI Signal Orchestrator (AI signals)
    - Trading Config (current settings)
    """

    def __init__(
        self,
        freqtrade_url: str = "http://127.0.0.1:8080",
        db_path: str = "user_data/db/tradesv3.dryrun.sqlite",
        config_path: str = "proratio_utilities/config/trading_config.json",
    ):
        """
        Initialize data fetcher

        Args:
            freqtrade_url: Freqtrade API URL
            db_path: Path to trade database
            config_path: Path to trading config
        """
        self.api = FreqtradeAPIClient(freqtrade_url)
        self.db = TradeDatabaseReader(db_path)
        self.config_path = config_path
        self.signal_orchestrator = None  # Lazy load

    def get_orchestrator(self) -> SignalOrchestrator:
        """Get or create signal orchestrator"""
        if self.signal_orchestrator is None:
            self.signal_orchestrator = SignalOrchestrator()
        return self.signal_orchestrator

    def get_trading_status(self) -> Dict:
        """Get comprehensive trading status"""
        # Get from API
        api_status = self.api.get_status()
        api_profit = self.api.get_profit()

        # Get from database
        db_stats = self.db.get_trade_statistics()
        open_trades = self.db.get_open_trades()

        # Load config
        config = TradingConfig.load_from_file(self.config_path)

        # Combine data
        return {
            "total_pnl": api_profit.get("profit_all_coin", 0.0),
            "total_pnl_pct": api_profit.get("profit_all_ratio_mean", 0.0) * 100,
            "win_rate": db_stats["win_rate"],
            "total_trades": db_stats["total_trades"],
            "winning_trades": db_stats["winning_trades"],
            "losing_trades": db_stats["losing_trades"],
            "open_positions": len(open_trades),
            "max_positions": config.risk.max_concurrent_positions,
            "avg_profit": db_stats["avg_profit"],
            "avg_loss": db_stats["avg_loss"],
            "current_drawdown": 0.0,  # TODO: Calculate from recent trades
            "max_drawdown": config.risk.max_total_drawdown_pct,
            "trading_enabled": api_status.get("state", "unknown") == "running",
        }

    def get_ai_signals(self, pairs: List[str]) -> Dict:
        """
        Get AI signals for specified pairs

        Args:
            pairs: List of trading pairs (e.g., ["BTC/USDT", "ETH/USDT"])

        Returns:
            Dict of signals by pair
        """
        orchestrator = self.get_orchestrator()
        signals = {}

        for pair in pairs:
            try:
                # Get latest signal
                # TODO: This needs actual OHLCV data - implement data fetching
                # For now, return None to indicate not implemented
                signals[pair.replace("/", "_").lower()] = None
            except Exception as e:
                print(f"Error getting signal for {pair}: {e}")
                signals[pair.replace("/", "_").lower()] = None

        return signals

    def get_active_trades_detail(self) -> List[Dict]:
        """Get detailed information about active trades"""
        open_trades = self.api.get_open_trades()

        detailed_trades = []
        for trade in open_trades:
            # Calculate duration
            open_timestamp = trade.get("open_timestamp", 0)
            duration_seconds = datetime.now().timestamp() - open_timestamp / 1000
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            duration_str = f"{hours}h {minutes}m"

            detailed_trades.append(
                {
                    "pair": trade.get("pair"),
                    "entry_price": trade.get("open_rate"),
                    "current_price": trade.get("current_rate"),
                    "pnl_pct": trade.get("profit_ratio", 0) * 100,
                    "pnl_usd": trade.get("profit_abs", 0),
                    "duration": duration_str,
                    "trade_id": trade.get("trade_id"),
                    "amount": trade.get("amount"),
                }
            )

        return detailed_trades

    def emergency_stop_all(self) -> Dict:
        """Emergency stop - close all positions and stop trading"""
        result = {"trades_closed": 0, "bot_stopped": False, "errors": []}

        try:
            # Force exit all trades
            exit_result = self.api.force_exit_all()
            result["trades_closed"] = exit_result.get("trades_closed", 0)

            # Stop the bot
            stop_result = self.api.stop_trading()
            result["bot_stopped"] = stop_result.get("status") == "success"

        except Exception as e:
            result["errors"].append(str(e))

        return result
