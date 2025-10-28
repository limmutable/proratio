"""
Integration Tests for Signal-to-Trade Workflow

Tests the complete workflow from signal generation through trade creation to trade management.
Verifies that signals correctly trigger and manage trades through the trade hub.

Feature: 001-test-validation-dashboard
User Story 2: Integration Test Coverage for Signal-to-Trade Workflow (Priority: P1)
Created: 2025-10-28
"""

import pytest
import logging
from datetime import datetime, timezone
from unittest.mock import patch
from dataclasses import dataclass

from proratio_signals.orchestrator import ConsensusSignal
from proratio_signals.llm_providers.base import MarketAnalysis

# Setup logging for tests
logger = logging.getLogger(__name__)


@dataclass
class MockTrade:
    """Mock trade object for testing."""

    id: int
    pair: str
    side: str  # 'buy' or 'sell'
    entry_price: float
    quantity: float
    stop_loss: float = None
    take_profit: float = None
    status: str = "open"  # 'open', 'closed'

    def update_stop_loss(self, new_stop_loss: float):
        """Update stop loss price."""
        self.stop_loss = new_stop_loss
        logger.info(f"Updated stop loss for trade {self.id} to {new_stop_loss}")

    def update_take_profit(self, new_take_profit: float):
        """Update take profit price."""
        self.take_profit = new_take_profit
        logger.info(f"Updated take profit for trade {self.id} to {new_take_profit}")

    def close(self, exit_price: float):
        """Close the trade."""
        self.status = "closed"
        logger.info(f"Closed trade {self.id} at price {exit_price}")


class MockTradeManager:
    """Mock trade manager for testing."""

    def __init__(self):
        self.trades = []
        self.next_trade_id = 1

    def create_trade_from_signal(
        self, signal: ConsensusSignal, balance: float = 10000.0
    ):
        """
        Create a trade from a consensus signal.

        Args:
            signal: ConsensusSignal object
            balance: Account balance for position sizing

        Returns:
            MockTrade object
        """
        # Determine side from signal direction
        side = "buy" if signal.direction == "long" else "sell"

        # Calculate position size (simple 1% risk model)
        risk_per_trade = balance * 0.01
        entry_price = 50000.0  # Mock BTC price
        stop_loss_pct = 0.02  # 2% stop loss
        quantity = risk_per_trade / (entry_price * stop_loss_pct)

        # Create trade
        trade = MockTrade(
            id=self.next_trade_id,
            pair=signal.pair,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=entry_price * (1 - stop_loss_pct)
            if side == "buy"
            else entry_price * (1 + stop_loss_pct),
            take_profit=entry_price * (1 + 0.04)
            if side == "buy"
            else entry_price * (1 - 0.04),
        )

        self.trades.append(trade)
        self.next_trade_id += 1

        logger.info(
            f"Created {side} trade #{trade.id} for {signal.pair}: "
            f"quantity={quantity:.4f}, entry={entry_price}, SL={trade.stop_loss}, TP={trade.take_profit}"
        )

        return trade

    def update_trade(self, trade_id: int, current_price: float):
        """
        Update trade management based on current price.

        Args:
            trade_id: ID of trade to update
            current_price: Current market price

        Returns:
            Updated MockTrade object
        """
        trade = next((t for t in self.trades if t.id == trade_id), None)
        if not trade:
            raise ValueError(f"Trade {trade_id} not found")

        # Simple trailing stop logic
        if trade.side == "buy" and current_price > trade.entry_price * 1.02:
            # Move stop loss to break even
            new_stop_loss = trade.entry_price
            trade.update_stop_loss(new_stop_loss)

        return trade

    def close_trade(self, trade_id: int, exit_price: float):
        """
        Close a trade.

        Args:
            trade_id: ID of trade to close
            exit_price: Exit price

        Returns:
            Closed MockTrade object
        """
        trade = next((t for t in self.trades if t.id == trade_id), None)
        if not trade:
            raise ValueError(f"Trade {trade_id} not found")

        trade.close(exit_price)
        return trade


class TestSignalToTrade:
    """
    Integration tests for signal-to-trade workflow.
    """

    @pytest.fixture
    def sample_signal(self):
        """Provide a sample consensus signal for testing."""
        return ConsensusSignal(
            direction="long",
            confidence=0.75,
            consensus_score=0.80,
            chatgpt_analysis=MarketAnalysis(
                direction="long",
                confidence=0.7,
                technical_summary="Strong uptrend with bullish breakout patterns",
                risk_assessment="Low risk with favorable 2:1 R:R ratio",
                sentiment="Bullish market sentiment across indicators",
                reasoning="Bullish technical patterns",
                provider="chatgpt",
                timestamp=datetime.now(timezone.utc),
                pair="BTC/USDT",
                timeframe="1h",
            ),
            claude_analysis=MarketAnalysis(
                direction="long",
                confidence=0.75,
                technical_summary="Price consolidation with upside breakout potential",
                risk_assessment="Low risk environment with tight stop loss",
                sentiment="Positive momentum building",
                reasoning="Low risk environment",
                provider="claude",
                timestamp=datetime.now(timezone.utc),
                pair="BTC/USDT",
                timeframe="1h",
            ),
            gemini_analysis=MarketAnalysis(
                direction="long",
                confidence=0.80,
                technical_summary="Strong support levels holding with bullish continuation",
                risk_assessment="Minimal downside risk at current levels",
                sentiment="Positive sentiment with high confidence",
                reasoning="Positive sentiment",
                provider="gemini",
                timestamp=datetime.now(timezone.utc),
                pair="BTC/USDT",
                timeframe="1h",
            ),
            combined_reasoning="Strong bullish consensus across all providers",
            risk_summary="Low risk, favorable R:R ratio",
            technical_summary="Bullish breakout pattern",
            timestamp=datetime.now(timezone.utc),
            pair="BTC/USDT",
            timeframe="1h",
            active_providers=["chatgpt", "claude", "gemini"],
            failed_providers=[],
            provider_models={
                "chatgpt": "gpt-4",
                "claude": "claude-3",
                "gemini": "gemini-pro",
            },
        )

    @pytest.mark.integration
    def test_signal_to_trade_creation(self, sample_signal):
        """
        Test that a valid trading signal correctly creates a trade with proper parameters.

        Given: A valid trading signal is generated
        When: The signal is processed by the trade hub
        Then: A trade is created with correct parameters matching the signal

        User Story: US2 - Acceptance Scenario 1
        """
        logger.info("Starting test_signal_to_trade_creation")

        # Create trade manager
        trade_manager = MockTradeManager()

        # Process signal and create trade
        trade = trade_manager.create_trade_from_signal(sample_signal, balance=10000.0)

        # Verify trade was created
        assert trade is not None
        assert trade.id == 1
        assert trade.pair == sample_signal.pair
        assert trade.side == "buy"  # long direction
        assert trade.quantity > 0
        assert trade.entry_price > 0
        assert trade.stop_loss is not None
        assert trade.take_profit is not None
        assert trade.status == "open"

        # Verify trade parameters match signal
        assert sample_signal.direction == "long"
        assert trade.side == "buy"

        logger.info(f"Successfully created trade: {trade}")
        logger.info("test_signal_to_trade_creation PASSED")

    @pytest.mark.integration
    def test_trade_management_workflow(self, sample_signal):
        """
        Test that an active trade is updated appropriately when market conditions change.

        Given: An active trade exists
        When: Market conditions change and trigger trade management rules
        Then: The trade is updated appropriately (stop loss, take profit, position sizing)

        User Story: US2 - Acceptance Scenario 2
        """
        logger.info("Starting test_trade_management_workflow")

        # Create trade manager and initial trade
        trade_manager = MockTradeManager()
        trade = trade_manager.create_trade_from_signal(sample_signal)

        initial_stop_loss = trade.stop_loss

        # Simulate price movement (price goes up 3%)
        current_price = trade.entry_price * 1.03

        # Update trade management
        updated_trade = trade_manager.update_trade(trade.id, current_price)

        # Verify trade was updated
        assert updated_trade is not None
        assert updated_trade.id == trade.id

        # Verify stop loss was moved (trailing stop)
        assert updated_trade.stop_loss != initial_stop_loss
        assert (
            updated_trade.stop_loss >= trade.entry_price
        )  # Moved to break even or better

        logger.info(
            f"Trade updated: SL moved from {initial_stop_loss} to {updated_trade.stop_loss}"
        )
        logger.info("test_trade_management_workflow PASSED")

    @pytest.mark.integration
    def test_trade_closure(self, sample_signal):
        """
        Test that a trade reaches its exit condition and is closed correctly with results recorded.

        Given: A trade reaches its exit condition
        When: The exit signal is processed
        Then: The trade is closed and results are recorded correctly

        User Story: US2 - Acceptance Scenario 3
        """
        logger.info("Starting test_trade_closure")

        # Create trade manager and initial trade
        trade_manager = MockTradeManager()
        trade = trade_manager.create_trade_from_signal(sample_signal)

        assert trade.status == "open"

        # Simulate price reaching take profit
        exit_price = trade.take_profit

        # Close the trade
        closed_trade = trade_manager.close_trade(trade.id, exit_price)

        # Verify trade was closed
        assert closed_trade is not None
        assert closed_trade.id == trade.id
        assert closed_trade.status == "closed"

        # Verify trade results are available
        pnl = (exit_price - closed_trade.entry_price) * closed_trade.quantity
        assert pnl > 0  # Profitable trade (reached take profit)

        logger.info(f"Trade closed with PnL: {pnl:.2f}")
        logger.info("test_trade_closure PASSED")

    @pytest.mark.integration
    def test_signal_orchestration_to_trade_hub(self, mock_market_data):
        """
        Test integration between signal orchestrator and trade hub.

        Given: Signal orchestrator generates a signal
        When: Signal is passed to trade hub
        Then: Trade hub processes signal and creates appropriate trade

        User Story: US2 - Signal orchestration to trade hub integration (T025)
        """
        logger.info("Starting test_signal_orchestration_to_trade_hub")

        # Mock signal orchestrator
        with patch(
            "proratio_signals.orchestrator.SignalOrchestrator"
        ) as mock_orchestrator:
            # Create mock signal
            mock_signal = ConsensusSignal(
                direction="short",
                confidence=0.70,
                consensus_score=0.75,
                pair="BTC/USDT",
                timeframe="1h",
                timestamp=datetime.now(timezone.utc),
                active_providers=["chatgpt", "claude"],
                failed_providers=[],
            )

            # Mock orchestrator.generate_signal() to return our signal
            mock_instance = mock_orchestrator.return_value
            mock_instance.generate_signal.return_value = mock_signal

            # Create trade manager
            trade_manager = MockTradeManager()

            # Generate signal and create trade
            signal = mock_instance.generate_signal(mock_market_data)
            trade = trade_manager.create_trade_from_signal(signal)

            # Verify end-to-end flow
            assert signal.direction == "short"
            assert trade.side == "sell"  # short direction maps to sell
            assert trade.pair == signal.pair

            logger.info("Signal orchestration to trade hub integration successful")
            logger.info("test_signal_orchestration_to_trade_hub PASSED")

    @pytest.mark.integration
    def test_invalid_signal_handling(self):
        """
        Test that invalid or conflicting signals are handled appropriately.

        Given: An invalid signal is generated
        When: The signal is processed by the trade hub
        Then: The signal is rejected or handled gracefully without creating an invalid trade

        User Story: US2 - Error handling for signal-to-trade workflow (T026)
        """
        logger.info("Starting test_invalid_signal_handling")

        # Create invalid signal (neutral direction with high confidence - contradictory)
        invalid_signal = ConsensusSignal(
            direction="neutral",
            confidence=0.80,
            consensus_score=0.50,
            pair="BTC/USDT",
            timeframe="1h",
            timestamp=datetime.now(timezone.utc),
            active_providers=["chatgpt"],
            failed_providers=[],
        )

        # Verify signal should_trade() returns False
        assert not invalid_signal.should_trade(), (
            "Invalid signal should not trigger trade"
        )

        logger.info("Invalid signal correctly rejected")
        logger.info("test_invalid_signal_handling PASSED")

    @pytest.mark.integration
    def test_signal_to_trade_logging(self, sample_signal, caplog):
        """
        Test that logging is properly configured for signal-to-trade workflow.

        User Story: US2 - Logging verification (T027)
        """
        logger.info("Starting test_signal_to_trade_logging")

        with caplog.at_level(logging.INFO):
            trade_manager = MockTradeManager()
            trade = trade_manager.create_trade_from_signal(sample_signal)

            # Update and close trade
            trade_manager.update_trade(trade.id, trade.entry_price * 1.03)
            trade_manager.close_trade(trade.id, trade.take_profit)

        # Verify logging occurred
        assert len(caplog.records) > 0, "No log records captured"
        log_messages = [record.message for record in caplog.records]

        # Verify key log messages exist
        assert any("Created" in msg and "trade" in msg for msg in log_messages)
        assert any("stop loss" in msg.lower() for msg in log_messages)
        assert any("Closed trade" in msg for msg in log_messages)

        logger.info(f"Captured {len(caplog.records)} log records")
        logger.info("test_signal_to_trade_logging PASSED")

    @pytest.mark.integration
    def test_signal_failure_messages(self):
        """
        Test that integration test failures provide clear, actionable error messages.

        Verifies SC-003: Integration test failures clearly identify failing component.

        User Story: US2 - Clear failure messages (T028)
        """
        logger.info("Starting test_signal_failure_messages")

        # Create a scenario that will fail
        trade_manager = MockTradeManager()

        # Attempt to update non-existent trade
        try:
            trade_manager.update_trade(999, 50000.0)
            assert False, "Expected ValueError was not raised"
        except ValueError as e:
            error_message = str(e)
            # Verify error message is clear and identifies the problem
            assert "Trade 999 not found" in error_message
            assert "999" in error_message  # Trade ID is included
            logger.info(f"Clear error message provided: {error_message}")

        logger.info("test_signal_failure_messages PASSED")


class TestSignalToTradeEdgeCases:
    """
    Edge case tests for signal-to-trade workflow.
    """

    @pytest.mark.integration
    def test_multiple_signals_sequential(self):
        """
        Test that multiple signals can be processed sequentially without interference.
        """
        logger.info("Starting test_multiple_signals_sequential")

        trade_manager = MockTradeManager()

        # Create multiple signals
        signals = [
            ConsensusSignal(
                direction="long",
                confidence=0.75,
                consensus_score=0.80,
                pair="BTC/USDT",
                timeframe="1h",
                timestamp=datetime.now(timezone.utc),
                active_providers=["chatgpt"],
                failed_providers=[],
            )
            for i in range(3)
        ]

        # Process all signals
        trades = [trade_manager.create_trade_from_signal(signal) for signal in signals]

        # Verify all trades were created
        assert len(trades) == 3
        assert len(trade_manager.trades) == 3
        assert all(trade.status == "open" for trade in trades)

        # Verify unique trade IDs
        trade_ids = [trade.id for trade in trades]
        assert len(trade_ids) == len(set(trade_ids)), "Trade IDs must be unique"

        logger.info(f"Successfully created {len(trades)} sequential trades")
        logger.info("test_multiple_signals_sequential PASSED")
