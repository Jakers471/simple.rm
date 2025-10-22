"""
Unit tests for RULE-007: Cooldown After Loss

Tests the cooldown rule which forces a break after losing trades
to prevent revenge trading and emotional decision-making.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime


@pytest.fixture
def mock_lockout_manager():
    """Mock lockout manager for cooldown tracking."""
    return Mock()


@pytest.fixture
def mock_trade_counter():
    """Mock trade counter for P&L tracking."""
    return Mock()


class TestCooldownAfterLoss:
    """Test suite for RULE-007: Cooldown After Loss."""

    def test_check_profitable_trade_no_trigger(self, mock_lockout_manager, mock_trade_counter):
        """
        GIVEN: Trade with profit (+150.50)
        WHEN: Trade is checked
        THEN: No breach, no cooldown
        """
        # Given
        trade_event = {
            "id": 101112,
            "accountId": 123,
            "contractId": "CON.F.US.EP.U25",
            "profitAndLoss": 150.50,  # Profit
            "fees": 2.50
        }

        config = {
            'loss_thresholds': [
                {'loss_amount': -100, 'cooldown_duration': 300},
                {'loss_amount': -200, 'cooldown_duration': 900}
            ]
        }

        mock_lockout_manager.active_cooldowns = {}

        # When
        from src.rules.cooldown_after_loss import CooldownAfterLossRule
        rule = CooldownAfterLossRule(config, mock_lockout_manager, mock_trade_counter)
        result = rule.check(trade_event)

        # Then
        assert result is None
        assert 123 not in mock_lockout_manager.active_cooldowns

    def test_check_small_loss_under_threshold(self, mock_lockout_manager, mock_trade_counter):
        """
        GIVEN: Loss of $75 (below -$100 threshold)
        WHEN: Trade is checked
        THEN: No breach, no cooldown
        """
        # Given
        trade_event = {
            "accountId": 123,
            "profitAndLoss": -75.00  # Below threshold
        }

        config = {
            'loss_thresholds': [
                {'loss_amount': -100, 'cooldown_duration': 300}
            ]
        }

        # When
        from src.rules.cooldown_after_loss import CooldownAfterLossRule
        rule = CooldownAfterLossRule(config, mock_lockout_manager, mock_trade_counter)
        result = rule.check(trade_event)

        # Then
        assert result is None

    def test_check_loss_at_first_threshold(self, mock_lockout_manager, mock_trade_counter):
        """
        GIVEN: Loss of exactly $100 (first threshold)
        WHEN: Trade is checked
        THEN: Breach detected, 5-minute cooldown action returned
        """
        # Given
        trade_event = {
            "accountId": 123,
            "profitAndLoss": -100.00  # At threshold
        }

        config = {
            'loss_thresholds': [
                {'loss_amount': -100, 'cooldown_duration': 300},
                {'loss_amount': -200, 'cooldown_duration': 900}
            ]
        }

        # When
        from src.rules.cooldown_after_loss import CooldownAfterLossRule
        rule = CooldownAfterLossRule(config, mock_lockout_manager, mock_trade_counter)
        result = rule.check(trade_event)

        # Then
        assert result is not None
        assert result['breach'] == True
        assert result['loss_amount'] == -100.00
        assert result['cooldown_duration'] == 300

        action = result['action']
        assert action['type'] == 'SET_COOLDOWN'
        assert action['duration'] == 300

    def test_check_large_loss_at_middle_threshold(self, mock_lockout_manager, mock_trade_counter):
        """
        GIVEN: Loss of $150 (triggers -$100 threshold, not -$200)
        WHEN: Trade is checked
        THEN: First exceeded threshold triggered (5 min)
        """
        # Given
        trade_event = {
            "accountId": 123,
            "profitAndLoss": -150.00
        }

        config = {
            'loss_thresholds': [
                {'loss_amount': -100, 'cooldown_duration': 300},
                {'loss_amount': -200, 'cooldown_duration': 900}
            ]
        }

        # When
        from src.rules.cooldown_after_loss import CooldownAfterLossRule
        rule = CooldownAfterLossRule(config, mock_lockout_manager, mock_trade_counter)
        result = rule.check(trade_event)

        # Then
        assert result is not None
        assert result['loss_amount'] == -100.00  # First threshold
        assert result['cooldown_duration'] == 300

    def test_check_severe_loss_at_highest_threshold(self, mock_lockout_manager, mock_trade_counter):
        """
        GIVEN: Loss of $350 (triggers -$300 threshold)
        WHEN: Trade is checked
        THEN: Highest threshold triggered with 30-minute cooldown
        """
        # Given
        trade_event = {
            "accountId": 123,
            "profitAndLoss": -350.00
        }

        config = {
            'loss_thresholds': [
                {'loss_amount': -100, 'cooldown_duration': 300},
                {'loss_amount': -200, 'cooldown_duration': 900},
                {'loss_amount': -300, 'cooldown_duration': 1800}
            ]
        }

        # When
        from src.rules.cooldown_after_loss import CooldownAfterLossRule
        rule = CooldownAfterLossRule(config, mock_lockout_manager, mock_trade_counter)
        result = rule.check(trade_event)

        # Then
        assert result is not None
        assert result['loss_amount'] == -300.00
        assert result['cooldown_duration'] == 1800

        action = result['action']
        assert action['duration'] == 1800
        assert 'take a break' in action['reason'].lower()

    def test_check_half_turn_trade(self, mock_lockout_manager, mock_trade_counter):
        """
        GIVEN: Trade with profitAndLoss=None (half-turn)
        WHEN: Trade is checked
        THEN: No breach, no cooldown
        """
        # Given
        trade_event = {
            "accountId": 123,
            "profitAndLoss": None  # Half-turn
        }

        config = {
            'loss_thresholds': [
                {'loss_amount': -100, 'cooldown_duration': 300}
            ]
        }

        # When
        from src.rules.cooldown_after_loss import CooldownAfterLossRule
        rule = CooldownAfterLossRule(config, mock_lockout_manager, mock_trade_counter)
        result = rule.check(trade_event)

        # Then
        assert result is None
