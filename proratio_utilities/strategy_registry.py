"""
Strategy Registry System

Central registry for managing all trading strategies in the Proratio system.
Provides a single source of truth for strategy metadata, performance tracking,
and status management.

Author: Proratio Team
Date: 2025-10-16
"""

from pathlib import Path
from typing import List, Dict, Optional
import json
from datetime import datetime
from dataclasses import dataclass, asdict
import secrets


@dataclass
class StrategyMetadata:
    """Strategy metadata from registry"""

    id: str
    name: str
    class_name: str
    status: str  # experimental, active, archived, paused
    category: str
    created_datetime: str  # ISO 8601 timestamp
    last_edited: str  # ISO 8601 timestamp
    version: str
    author: str
    description: str
    tags: List[str]
    path: Dict[str, str]
    parameters: Dict
    performance: Dict
    dependencies: Optional[Dict] = None
    validation: Optional[Dict] = None
    notes: Optional[str] = None
    archived_reason: Optional[str] = None
    archived_datetime: Optional[str] = None


class StrategyRegistry:
    """Central strategy registry manager"""

    def __init__(self, registry_path: str = "strategies/registry.json"):
        """
        Initialize strategy registry.

        Args:
            registry_path: Path to registry.json file
        """
        self.registry_path = Path(registry_path)
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict:
        """Load registry from JSON file"""
        if not self.registry_path.exists():
            return {
                "version": "1.0.0",
                "strategies": {},
                "categories": {},
                "statuses": {},
            }
        with open(self.registry_path) as f:
            return json.load(f)

    def save_registry(self):
        """Save registry to JSON file"""
        self.registry["last_updated"] = datetime.now().isoformat()
        with open(self.registry_path, "w") as f:
            json.dump(self.registry, f, indent=2)

    def list_strategies(
        self, status: Optional[str] = None, category: Optional[str] = None
    ) -> List[StrategyMetadata]:
        """
        List all strategies (optionally filtered).

        Args:
            status: Filter by status (experimental, active, archived, paused)
            category: Filter by category (ai-enhanced, grid, mean-reversion, etc.)

        Returns:
            List of StrategyMetadata objects
        """
        strategies = []
        for strategy_id, data in self.registry["strategies"].items():
            if status and data.get("status") != status:
                continue
            if category and data.get("category") != category:
                continue
            strategies.append(StrategyMetadata(**data))
        return strategies

    def get_strategy(self, strategy_id: str) -> Optional[StrategyMetadata]:
        """
        Get strategy by ID.

        Args:
            strategy_id: Strategy ID (e.g., 'a014_hybrid-ml-llm')

        Returns:
            StrategyMetadata object or None if not found
        """
        data = self.registry["strategies"].get(strategy_id)
        if data:
            return StrategyMetadata(**data)
        return None

    def get_active_strategies(self) -> List[StrategyMetadata]:
        """Get all active (production-ready) strategies"""
        return self.list_strategies(status="active")

    def get_experimental_strategies(self) -> List[StrategyMetadata]:
        """Get all experimental strategies"""
        return self.list_strategies(status="experimental")

    def get_archived_strategies(self) -> List[StrategyMetadata]:
        """Get all archived strategies"""
        return self.list_strategies(status="archived")

    def register_strategy(self, metadata: StrategyMetadata):
        """
        Register a new strategy.

        Args:
            metadata: StrategyMetadata object with all required fields
        """
        self.registry["strategies"][metadata.id] = asdict(metadata)
        self.save_registry()

    def update_strategy(self, strategy_id: str, updates: Dict):
        """
        Update strategy metadata.

        Args:
            strategy_id: Strategy ID to update
            updates: Dictionary of fields to update
        """
        if strategy_id in self.registry["strategies"]:
            self.registry["strategies"][strategy_id].update(updates)
            self.registry["strategies"][strategy_id]["last_edited"] = (
                datetime.now().isoformat()
            )
            self.save_registry()

    def update_performance(self, strategy_id: str, performance_data: Dict):
        """
        Update strategy performance metrics.

        Args:
            strategy_id: Strategy ID
            performance_data: Performance metrics dictionary
        """
        if strategy_id in self.registry["strategies"]:
            self.registry["strategies"][strategy_id]["performance"] = performance_data
            self.registry["strategies"][strategy_id]["last_edited"] = (
                datetime.now().isoformat()
            )
            self.save_registry()

    def archive_strategy(self, strategy_id: str, reason: str):
        """
        Archive a strategy.

        Args:
            strategy_id: Strategy ID to archive
            reason: Reason for archiving
        """
        if strategy_id in self.registry["strategies"]:
            self.registry["strategies"][strategy_id]["status"] = "archived"
            self.registry["strategies"][strategy_id]["archived_reason"] = reason
            self.registry["strategies"][strategy_id]["archived_datetime"] = (
                datetime.now().isoformat()
            )
            self.registry["strategies"][strategy_id]["last_edited"] = (
                datetime.now().isoformat()
            )
            self.save_registry()

    def activate_strategy(self, strategy_id: str):
        """
        Activate a strategy (change status to 'active').

        Args:
            strategy_id: Strategy ID to activate
        """
        if strategy_id in self.registry["strategies"]:
            self.registry["strategies"][strategy_id]["status"] = "active"
            self.registry["strategies"][strategy_id]["last_edited"] = (
                datetime.now().isoformat()
            )
            self.save_registry()

    def pause_strategy(self, strategy_id: str):
        """
        Pause a strategy (temporarily disable).

        Args:
            strategy_id: Strategy ID to pause
        """
        if strategy_id in self.registry["strategies"]:
            self.registry["strategies"][strategy_id]["status"] = "paused"
            self.registry["strategies"][strategy_id]["last_edited"] = (
                datetime.now().isoformat()
            )
            self.save_registry()

    @staticmethod
    def generate_strategy_id(strategy_name: str) -> str:
        """
        Generate a unique strategy ID with random hash.

        Args:
            strategy_name: Human-readable strategy name (e.g., "Hybrid ML+LLM")

        Returns:
            Strategy ID (e.g., "a3f7_hybrid-ml-llm")
        """
        # Generate 4-character random hex
        hash_part = secrets.token_hex(2)

        # Convert name to kebab-case
        name_part = (
            strategy_name.lower()
            .replace(" ", "-")
            .replace("+", "")
            .replace("/", "-")
            .replace("_", "-")
        )

        return f"{hash_part}_{name_part}"

    def get_strategy_count(self) -> Dict[str, int]:
        """
        Get count of strategies by status.

        Returns:
            Dictionary with counts per status
        """
        counts = {"active": 0, "experimental": 0, "archived": 0, "paused": 0}
        for data in self.registry["strategies"].values():
            status = data.get("status", "unknown")
            if status in counts:
                counts[status] += 1
        return counts

    def search_strategies(self, query: str) -> List[StrategyMetadata]:
        """
        Search strategies by name, description, or tags.

        Args:
            query: Search query string

        Returns:
            List of matching StrategyMetadata objects
        """
        query_lower = query.lower()
        results = []

        for strategy_id, data in self.registry["strategies"].items():
            # Search in name, description, tags
            if (
                query_lower in data.get("name", "").lower()
                or query_lower in data.get("description", "").lower()
                or query_lower in data.get("class_name", "").lower()
                or any(query_lower in tag.lower() for tag in data.get("tags", []))
            ):
                results.append(StrategyMetadata(**data))

        return results


# Convenience function for quick access
def get_strategy_registry() -> StrategyRegistry:
    """Get the default strategy registry instance"""
    return StrategyRegistry()


if __name__ == "__main__":
    # Example usage
    registry = StrategyRegistry()

    print("=== Strategy Registry ===")
    print(f"Total strategies: {len(registry.registry['strategies'])}")
    print(f"Status counts: {registry.get_strategy_count()}")
    print()

    print("=== Active Strategies ===")
    for strategy in registry.get_active_strategies():
        print(f"  - {strategy.name} ({strategy.id})")
        print(f"    Class: {strategy.class_name}")
        print(f"    Category: {strategy.category}")
        print()

    print("=== Archived Strategies ===")
    for strategy in registry.get_archived_strategies():
        print(f"  - {strategy.name} ({strategy.id})")
        print(f"    Archived: {strategy.archived_datetime}")
        print(f"    Reason: {strategy.archived_reason}")
        print()
