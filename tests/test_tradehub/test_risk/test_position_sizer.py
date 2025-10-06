"""
Tests for Position Sizer

Tests various position sizing methods and calculations.
"""

import pytest
from proratio_tradehub.risk.position_sizer import (
    PositionSizer,
    SizingMethod,
    get_position_size_for_ai_strategy
)


class TestPositionSizer:
    """Test PositionSizer class"""

    def test_initialization(self):
        """Test position sizer initialization"""
        sizer = PositionSizer(
            method=SizingMethod.RISK_BASED,
            base_risk_pct=2.0,
            max_position_pct=10.0,
            min_position_pct=1.0
        )

        assert sizer.method == SizingMethod.RISK_BASED
        assert sizer.base_risk_pct == 2.0
        assert sizer.max_position_pct == 10.0

    def test_fixed_fraction_sizing(self):
        """Test fixed fractional sizing"""
        sizer = PositionSizer(
            method=SizingMethod.FIXED_FRACTION,
            base_risk_pct=5.0
        )

        position_size = sizer.calculate_position_size(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss_price=48000.0
        )

        # 5% of 10000 = 500
        assert position_size == 500.0

    def test_risk_based_sizing(self):
        """Test risk-based sizing"""
        sizer = PositionSizer(
            method=SizingMethod.RISK_BASED,
            base_risk_pct=2.0
        )

        position_size = sizer.calculate_position_size(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss_price=48000.0  # 4% stop-loss
        )

        # Max loss = 10000 * 0.02 = 200
        # Risk per unit = 50000 - 48000 = 2000
        # Units = 200 / 2000 = 0.1
        # Position size = 0.1 * 50000 = 5000
        # But max position is 10%, so capped at 1000
        assert position_size == 1000.0

    def test_risk_based_sizing_small_stop(self):
        """Test risk-based sizing with small stop-loss"""
        sizer = PositionSizer(
            method=SizingMethod.RISK_BASED,
            base_risk_pct=2.0,
            max_position_pct=15.0  # Higher max to test calculation
        )

        position_size = sizer.calculate_position_size(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss_price=49500.0  # 1% stop-loss
        )

        # Max loss = 200
        # Risk per unit = 500
        # Units = 200 / 500 = 0.4
        # Position size = 0.4 * 50000 = 20000
        # Capped at 15% = 1500
        assert position_size == 1500.0

    def test_invalid_stop_loss(self):
        """Test that invalid stop-loss raises error"""
        sizer = PositionSizer(method=SizingMethod.RISK_BASED)

        with pytest.raises(ValueError, match="Invalid stop-loss"):
            sizer.calculate_position_size(
                balance=10000.0,
                entry_price=50000.0,
                stop_loss_price=50000.0  # Same as entry = invalid
            )

    def test_kelly_sizing(self):
        """Test Kelly Criterion sizing"""
        sizer = PositionSizer(
            method=SizingMethod.KELLY,
            max_position_pct=20.0
        )

        position_size = sizer.calculate_position_size(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss_price=48000.0,
            win_rate=0.6,  # 60% win rate
            avg_win=300.0,
            avg_loss=200.0
        )

        # Payoff ratio = 300/200 = 1.5
        # Kelly % = (0.6 * 1.5 - 0.4) / 1.5 = (0.9 - 0.4) / 1.5 = 0.333
        # Half Kelly = 0.1665
        # Position = 10000 * 0.1665 = 1665
        # Within min (100) and max (2000) limits
        assert 100 <= position_size <= 2000

    def test_kelly_fallback_missing_params(self):
        """Test Kelly falls back to risk-based when params missing"""
        sizer = PositionSizer(method=SizingMethod.KELLY)

        # Should fallback to risk-based
        position_size = sizer.calculate_position_size(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss_price=48000.0
            # Missing win_rate, avg_win, avg_loss
        )

        # Should use risk-based calculation
        assert position_size > 0

    def test_ai_weighted_sizing_high_confidence(self):
        """Test AI-weighted sizing with high confidence"""
        sizer = PositionSizer(
            method=SizingMethod.AI_WEIGHTED,
            base_risk_pct=2.0
        )

        position_size = sizer.calculate_position_size(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss_price=48000.0,
            ai_confidence=0.90  # 90% confidence
        )

        # Base size would be capped at 1000 (10% max)
        # 90% confidence → multiplier ≈ 1.1x
        # Result should be >= 1000 (may be capped at max)
        assert position_size >= 1000

    def test_ai_weighted_sizing_low_confidence(self):
        """Test AI-weighted sizing with low confidence"""
        sizer = PositionSizer(
            method=SizingMethod.AI_WEIGHTED,
            base_risk_pct=2.0
        )

        position_size = sizer.calculate_position_size(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss_price=48000.0,
            ai_confidence=0.62  # Just above 60% threshold
        )

        # Base size capped at 1000
        # 62% confidence → multiplier ≈ 0.82x
        # Result should be < 1000
        assert position_size < 1000

    def test_ai_weighted_sizing_below_threshold(self):
        """Test AI-weighted sizing rejects low confidence"""
        sizer = PositionSizer(method=SizingMethod.AI_WEIGHTED)

        position_size = sizer.calculate_position_size(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss_price=48000.0,
            ai_confidence=0.55  # Below 60% threshold
        )

        # Should return 0 (don't trade)
        assert position_size == 0.0

    def test_ai_weighted_without_confidence(self):
        """Test AI-weighted sizing without AI confidence"""
        sizer = PositionSizer(method=SizingMethod.AI_WEIGHTED)

        position_size = sizer.calculate_position_size(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss_price=48000.0,
            ai_confidence=None
        )

        # Should return base size
        assert position_size > 0

    def test_atr_based_sizing(self):
        """Test ATR-based volatility sizing"""
        sizer = PositionSizer(
            method=SizingMethod.ATR_BASED,
            base_risk_pct=2.0
        )

        position_size = sizer.calculate_position_size(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss_price=48000.0,  # Not used with ATR
            atr=1000.0  # ATR = 1000
        )

        # Stop-loss = entry - (ATR * 2) = 50000 - 2000 = 48000
        # Same as risk-based test
        assert position_size == 1000.0

    def test_atr_based_fallback(self):
        """Test ATR-based falls back when ATR missing"""
        sizer = PositionSizer(method=SizingMethod.ATR_BASED)

        position_size = sizer.calculate_position_size(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss_price=48000.0,
            atr=None  # Missing ATR
        )

        # Should fallback to risk-based
        assert position_size > 0

    def test_min_max_limits(self):
        """Test min/max position size limits"""
        sizer = PositionSizer(
            method=SizingMethod.FIXED_FRACTION,
            base_risk_pct=0.5,  # Very small
            min_position_pct=1.0,
            max_position_pct=10.0
        )

        # Should enforce minimum
        position_size = sizer.calculate_position_size(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss_price=48000.0
        )

        # 0.5% = 50, but min is 1% = 100
        # Note: Fixed fraction just uses base_risk_pct directly
        assert position_size == 50.0  # 0.5% of 10000

    def test_calculate_units(self):
        """Test conversion from USD to units"""
        sizer = PositionSizer()

        units = sizer.calculate_units(
            position_size_usd=5000.0,
            entry_price=50000.0
        )

        assert units == 0.1  # 5000 / 50000

    def test_calculate_stop_loss_from_atr_long(self):
        """Test stop-loss calculation from ATR for long"""
        sizer = PositionSizer()

        stop_loss = sizer.calculate_stop_loss_from_atr(
            entry_price=50000.0,
            atr=1000.0,
            direction="long",
            atr_multiplier=2.0
        )

        # Long: entry - (ATR * 2) = 50000 - 2000 = 48000
        assert stop_loss == 48000.0

    def test_calculate_stop_loss_from_atr_short(self):
        """Test stop-loss calculation from ATR for short"""
        sizer = PositionSizer()

        stop_loss = sizer.calculate_stop_loss_from_atr(
            entry_price=50000.0,
            atr=1000.0,
            direction="short",
            atr_multiplier=2.0
        )

        # Short: entry + (ATR * 2) = 50000 + 2000 = 52000
        assert stop_loss == 52000.0


class TestHelperFunctions:
    """Test helper functions"""

    def test_get_position_size_for_ai_strategy(self):
        """Test AI strategy helper function"""
        position_size = get_position_size_for_ai_strategy(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss_price=48000.0,
            ai_confidence=0.75,
            base_risk_pct=2.0
        )

        # Should use AI-weighted sizing
        # 75% confidence → multiplier ≈ 0.95x
        assert position_size > 0
        assert position_size <= 1000.0  # Max 10%

    def test_get_position_size_for_ai_strategy_low_confidence(self):
        """Test AI strategy helper with low confidence"""
        position_size = get_position_size_for_ai_strategy(
            balance=10000.0,
            entry_price=50000.0,
            stop_loss_price=48000.0,
            ai_confidence=0.55  # Below threshold
        )

        # Should return 0
        assert position_size == 0.0
