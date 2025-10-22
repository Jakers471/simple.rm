"""
Unit tests for RULE-008: No Stop Loss Grace Period

Tests the rule that enforces stop-loss placement within a grace period
after position opens.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime


@pytest.fixture
def mock_positions_pending_stop():
    """Mock position tracking for stop-loss grace checks."""
    return {}


class TestNoStopLossGrace:
    """Test suite for RULE-008: No Stop Loss Grace Period."""

    def test_check_position_with_stop_loss(self, mock_positions_pending_stop):
        """
        GIVEN: Position with stop-loss already placed
        WHEN: Position is checked
        THEN: No breach, position removed from tracking
        """
        # Given
        position = {
            'contract_id': 'CON.F.US.MNQ.U25',
            'account_id': 123,
            'entry_price': 21000.25,
            'position_type': 1,
            'opened_at': datetime(2024, 7, 21, 14, 0, 0),
            'has_stop_loss': True
        }

        config = {
            'grace_period_seconds': 30
        }

        # When
        from src.rules.no_stop_loss_grace import NoStopLossGraceRule
        rule = NoStopLossGraceRule(config, mock_positions_pending_stop)
        result = rule.check(456, position)

        # Then
        assert result is None
        assert 456 not in mock_positions_pending_stop

    def test_check_position_within_grace_period(self, mock_positions_pending_stop):
        """
        GIVEN: Position opened 15s ago (within 30s grace)
        WHEN: Position is checked
        THEN: No breach yet
        """
        # Given
        mock_positions_pending_stop[456] = {
            'contract_id': 'CON.F.US.MNQ.U25',
            'account_id': 123,
            'opened_at': datetime(2024, 7, 21, 14, 0, 0),
            'has_stop_loss': False
        }

        config = {
            'grace_period_seconds': 30
        }

        # When
        from src.rules.no_stop_loss_grace import NoStopLossGraceRule
        rule = NoStopLossGraceRule(config, mock_positions_pending_stop)

        with Mock() as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 7, 21, 14, 0, 15)
            result = rule.check(456, mock_positions_pending_stop[456])

        # Then
        assert result is None
        assert 456 in mock_positions_pending_stop

    def test_check_stop_loss_added_within_grace(self, mock_positions_pending_stop):
        """
        GIVEN: Position opened 10s ago, stop-loss now added
        WHEN: Order event processed
        THEN: Position marked as having stop, tracking stops
        """
        # Given
        mock_positions_pending_stop[456] = {
            'contract_id': 'CON.F.US.MNQ.U25',
            'account_id': 123,
            'opened_at': datetime(2024, 7, 21, 14, 0, 0),
            'has_stop_loss': False
        }

        order_event = {
            "id": 790,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 4,  # Stop
            "side": 1,  # Sell
            "stopPrice": 20995.00
        }

        config = {
            'grace_period_seconds': 30
        }

        # When
        from src.rules.no_stop_loss_grace import NoStopLossGraceRule
        rule = NoStopLossGraceRule(config, mock_positions_pending_stop)
        rule.on_order_placed(order_event, mock_positions_pending_stop)
        result = rule.check(456, mock_positions_pending_stop[456])

        # Then
        assert mock_positions_pending_stop[456]['has_stop_loss'] == True
        assert result is None

    def test_check_grace_period_expired(self, mock_positions_pending_stop):
        """
        GIVEN: Position opened 35s ago (beyond 30s grace)
        WHEN: Position is checked
        THEN: Breach detected, close position action
        """
        # Given
        mock_positions_pending_stop[456] = {
            'contract_id': 'CON.F.US.MNQ.U25',
            'account_id': 123,
            'opened_at': datetime(2024, 7, 21, 14, 0, 0),
            'has_stop_loss': False
        }

        config = {
            'grace_period_seconds': 30,
            'action': 'CLOSE_POSITION'
        }

        # When
        from src.rules.no_stop_loss_grace import NoStopLossGraceRule
        rule = NoStopLossGraceRule(config, mock_positions_pending_stop)

        with Mock() as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 7, 21, 14, 0, 35)
            result = rule.check(456, mock_positions_pending_stop[456])

        # Then
        assert result is not None
        assert result['breach'] == True
        assert result['elapsed_time'] == 35

        action = result['action']
        assert action['type'] == 'CLOSE_POSITION'
        assert action['reason'] == 'No stop-loss within 30s grace period'

    def test_check_stop_loss_detection_by_order_type(self):
        """
        GIVEN: Long position, different stop order types
        WHEN: Orders checked
        THEN: All stop types detected (Stop, StopLimit, TrailingStop)
        """
        # Given
        position = {
            'entry_price': 21000.00,
            'position_type': 1  # Long
        }

        stop_limit_order = {
            "type": 3,  # StopLimit
            "side": 1,  # Sell
            "stopPrice": 20990.00
        }

        stop_order = {
            "type": 4,  # Stop
            "side": 1,
            "stopPrice": 20990.00
        }

        trailing_stop = {
            "type": 5,  # TrailingStop
            "side": 1,
            "stopPrice": 20990.00
        }

        # When
        from src.rules.no_stop_loss_grace import NoStopLossGraceRule
        rule = NoStopLossGraceRule({}, {})

        result1 = rule.is_stop_loss_order(stop_limit_order, position)
        result2 = rule.is_stop_loss_order(stop_order, position)
        result3 = rule.is_stop_loss_order(trailing_stop, position)

        # Then
        assert result1 == True
        assert result2 == True
        assert result3 == True

    def test_check_wrong_direction_not_detected(self):
        """
        GIVEN: Short position, Sell order (wrong direction)
        WHEN: Order checked
        THEN: Not detected as valid stop-loss
        """
        # Given
        position = {
            'entry_price': 21000.00,
            'position_type': 2  # Short
        }

        wrong_order = {
            "type": 4,
            "side": 1,  # Sell (wrong for short!)
            "stopPrice": 20990.00
        }

        correct_order = {
            "type": 4,
            "side": 0,  # Buy (correct)
            "stopPrice": 21010.00
        }

        # When
        from src.rules.no_stop_loss_grace import NoStopLossGraceRule
        rule = NoStopLossGraceRule({}, {})

        wrong_result = rule.is_stop_loss_order(wrong_order, position)
        correct_result = rule.is_stop_loss_order(correct_order, position)

        # Then
        assert wrong_result == False
        assert correct_result == True
