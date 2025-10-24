"""
Unit tests for RULE-004: DailyUnrealizedLoss

Tests the DailyUnrealizedLoss rule which monitors unrealized P&L
and closes positions when loss limit is exceeded.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime


@pytest.fixture
def mock_pnl_tracker():
    """Mock P&L tracker for unrealized P&L calculations."""
    return Mock()


@pytest.fixture
def mock_actions():
    """Mock enforcement actions."""
    return Mock()


@pytest.fixture
def mock_lockout_manager():
    """Mock lockout manager."""
    return Mock()


@pytest.fixture
def mock_logger():
    """Mock logger for enforcement tracking."""
    return Mock()


@pytest.fixture
def mock_state_manager():
    """Mock state manager for positions."""
    return Mock()


@pytest.fixture
def mock_contract_cache():
    """Mock contract cache for contract details."""
    return Mock()


@pytest.fixture
def mock_quote_tracker():
    """Mock quote tracker for current prices."""
    return Mock()


class TestDailyUnrealizedLoss:
    """Test suite for RULE-004: DailyUnrealizedLoss."""

    def test_check_under_limit(self, mock_pnl_tracker, mock_actions, mock_lockout_manager):
        """
        GIVEN: Loss limit=300, unrealized P&L=-250
        WHEN: Position is checked
        THEN: No breach, no enforcement
        """
        # Given
        config = {
            'enabled': True,
            'loss_limit': 300.00,
            'scope': 'total',
            'action': 'CLOSE_ALL_AND_LOCKOUT',
            'lockout': True
        }

        mock_pnl_tracker.calculate_unrealized_pnl.return_value = -250.00

        position_event = {
            'accountId': 123,
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 1,
            'size': 2,
            'averagePrice': 21000.00
        }

        # When
        from src.rules.daily_unrealized_loss import DailyUnrealizedLossRule
        rule = DailyUnrealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)
        result = rule.check_with_current_prices(123)

        # Then
        assert result is None
        mock_actions.close_all_positions.assert_not_called()
        mock_lockout_manager.set_lockout.assert_not_called()

    def test_check_breach(self, mock_pnl_tracker, mock_actions, mock_lockout_manager, mock_logger):
        """
        GIVEN: Loss limit=300, unrealized P&L=-350
        WHEN: Check is performed and enforced
        THEN: Breach detected, all positions closed, lockout set
        """
        # Given
        config = {
            'enabled': True,
            'loss_limit': 300.00,
            'scope': 'total',
            'action': 'CLOSE_ALL_AND_LOCKOUT',
            'lockout': True,
            'reset_time': '17:00'
        }

        mock_pnl_tracker.calculate_unrealized_pnl.return_value = -350.00
        mock_actions.close_all_positions.return_value = True
        mock_actions.cancel_all_orders.return_value = True

        mock_now = datetime(2025, 1, 17, 14, 30, 0)
        expected_reset = datetime(2025, 1, 17, 17, 0, 0)

        # When
        from src.rules.daily_unrealized_loss import DailyUnrealizedLossRule
        rule = DailyUnrealizedLossRule(
            config,
            mock_pnl_tracker,
            mock_actions,
            mock_lockout_manager,
            mock_logger
        )

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.combine = datetime.combine

            breach = rule.check_with_current_prices(123)

            if breach:
                rule.enforce(123, breach)

        # Then
        assert breach is not None
        assert breach['rule_id'] == 'RULE-004'
        assert breach['action'] == 'CLOSE_ALL_AND_LOCKOUT'
        assert breach['unrealized_pnl'] == -350.00
        assert breach['limit'] == -300.00

        mock_actions.close_all_positions.assert_called_once_with(123)
        mock_actions.cancel_all_orders.assert_called_once_with(123)

        mock_lockout_manager.set_lockout.assert_called_once()
        lockout_call = mock_lockout_manager.set_lockout.call_args[1]
        assert lockout_call['account_id'] == 123
        assert lockout_call['until'] == expected_reset

        mock_logger.log_enforcement.assert_called_once()

    def test_check_with_multiple_positions(self, mock_pnl_tracker, mock_actions, mock_lockout_manager):
        """
        GIVEN: Loss limit=300, Position 1:-150, Position 2:-200, Total:-350
        WHEN: Total unrealized P&L checked
        THEN: Breach detected with combined P&L
        """
        # Given
        config = {
            'enabled': True,
            'loss_limit': 300.00,
            'scope': 'total'
        }

        mock_pnl_tracker.calculate_unrealized_pnl.return_value = -350.00

        # When
        from src.rules.daily_unrealized_loss import DailyUnrealizedLossRule
        rule = DailyUnrealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)
        breach = rule.check_with_current_prices(123)

        # Then
        assert breach is not None
        assert breach['unrealized_pnl'] == -350.00
        mock_pnl_tracker.calculate_unrealized_pnl.assert_called_once_with(123)

    def test_check_triggered_by_quote_update(self, mock_pnl_tracker, mock_actions, mock_lockout_manager):
        """
        GIVEN: Loss limit=300, quotes update causing P&L to change
        WHEN: Two quote updates: first -250, second -310
        THEN: First check passes, second triggers breach
        """
        # Given
        config = {
            'enabled': True,
            'loss_limit': 300.00
        }

        unrealized_sequence = [
            -250.00,  # First quote
            -310.00   # Second quote: BREACH!
        ]
        mock_pnl_tracker.calculate_unrealized_pnl.side_effect = unrealized_sequence

        # When
        from src.rules.daily_unrealized_loss import DailyUnrealizedLossRule
        rule = DailyUnrealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)

        result1 = rule.check_with_current_prices(123)
        result2 = rule.check_with_current_prices(123)

        # Then
        assert result1 is None
        assert result2 is not None
        assert result2['unrealized_pnl'] == -310.00
        assert mock_pnl_tracker.calculate_unrealized_pnl.call_count == 2

    def test_check_long_position_losing(self, mock_state_manager, mock_contract_cache, mock_quote_tracker, mock_actions):
        """
        GIVEN: Long 2 MNQ @ 21000, current 20950 = -$200
        WHEN: Unrealized P&L calculated
        THEN: Correctly calculates -$200 loss
        """
        # Given
        config = {
            'enabled': True,
            'loss_limit': 300.00
        }

        mock_contract_cache.get_contract.return_value = {
            'tickSize': 0.25,
            'tickValue': 0.50
        }

        mock_quote_tracker.get_quote.return_value = {
            'lastPrice': 20950.00
        }

        mock_state_manager.get_all_positions.return_value = [{
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 1,  # Long
            'size': 2,
            'averagePrice': 21000.00
        }]

        # When
        from src.core.pnl_tracker import PnLTracker
        pnl_tracker = PnLTracker(
            db=None,
            state_mgr=mock_state_manager,
            quote_tracker=mock_quote_tracker,
            contract_cache=mock_contract_cache
        )

        from src.rules.daily_unrealized_loss import DailyUnrealizedLossRule
        rule = DailyUnrealizedLossRule(config, pnl_tracker, mock_actions, None)

        unrealized_pnl = pnl_tracker.calculate_unrealized_pnl(123)

        # Then
        # Ticks moved: (20950 - 21000) / 0.25 = -200 ticks
        # P&L: -200 * 0.50 * 2 = -$200
        assert unrealized_pnl == -200.00

        breach = rule.check_with_current_prices(123)
        assert breach is None  # Under limit

    def test_check_short_position_losing(self, mock_state_manager, mock_contract_cache, mock_quote_tracker, mock_actions):
        """
        GIVEN: Short 2 MNQ @ 21000, current 21050 = -$200
        WHEN: Unrealized P&L calculated
        THEN: Correctly calculates -$200 loss
        """
        # Given
        config = {
            'enabled': True,
            'loss_limit': 300.00
        }

        mock_contract_cache.get_contract.return_value = {
            'tickSize': 0.25,
            'tickValue': 0.50
        }

        mock_quote_tracker.get_quote.return_value = {
            'lastPrice': 21050.00  # Price went up
        }

        mock_state_manager.get_all_positions.return_value = [{
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 2,  # Short
            'size': 2,
            'averagePrice': 21000.00
        }]

        # When
        from src.core.pnl_tracker import PnLTracker
        pnl_tracker = PnLTracker(
            db=None,
            state_mgr=mock_state_manager,
            quote_tracker=mock_quote_tracker,
            contract_cache=mock_contract_cache
        )

        from src.rules.daily_unrealized_loss import DailyUnrealizedLossRule
        rule = DailyUnrealizedLossRule(config, pnl_tracker, mock_actions, None)

        unrealized_pnl = pnl_tracker.calculate_unrealized_pnl(123)

        # Then
        # Short loses when price goes up
        # Ticks moved: (21050 - 21000) / 0.25 = 200 ticks
        # P&L for short: -200 * 0.50 * 2 = -$200
        assert unrealized_pnl == -200.00

        breach = rule.check_with_current_prices(123)
        assert breach is None

    def test_check_missing_quote_data(self, mock_state_manager, mock_contract_cache, mock_quote_tracker, mock_actions, mock_logger):
        """
        GIVEN: Position exists but quote data unavailable
        WHEN: Unrealized P&L calculated
        THEN: Returns 0 (skips position), warning logged
        """
        # Given
        config = {
            'enabled': True,
            'loss_limit': 300.00
        }

        mock_quote_tracker.get_quote.return_value = None  # No quote

        mock_state_manager.get_all_positions.return_value = [{
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 1,
            'size': 2,
            'averagePrice': 21000.00
        }]

        # When
        from src.core.pnl_tracker import PnLTracker
        pnl_tracker = PnLTracker(
            db=None,
            state_mgr=mock_state_manager,
            quote_tracker=mock_quote_tracker,
            contract_cache=mock_contract_cache,
            log_handler=mock_logger
        )

        from src.rules.daily_unrealized_loss import DailyUnrealizedLossRule
        rule = DailyUnrealizedLossRule(config, pnl_tracker, mock_actions, None, mock_logger)

        unrealized_pnl = pnl_tracker.calculate_unrealized_pnl(123)

        # Then
        assert unrealized_pnl == 0.00

        mock_logger.warning.assert_called()
        warning_message = mock_logger.warning.call_args[0][0]
        assert 'Missing quote' in warning_message or 'No quote' in warning_message

        breach = rule.check_with_current_prices(123)
        assert breach is None

    def test_check_per_position_scope(self, mock_pnl_tracker, mock_actions, mock_lockout_manager, mock_logger):
        """
        GIVEN: scope='per_position', MNQ:-350 (breach), ES:+100 (OK)
        WHEN: Check is performed and enforced
        THEN: Only MNQ position closed, ES remains open
        """
        # Given
        config = {
            'enabled': True,
            'loss_limit': 300.00,
            'scope': 'per_position',
            'action': 'CLOSE_POSITION',
            'lockout': False
        }

        def calculate_per_position_pnl(account_id):
            return {
                'CON.F.US.MNQ.U25': -350.00,  # Breach!
                'CON.F.US.ES.U25': 100.00     # OK
            }

        mock_pnl_tracker.calculate_per_position_pnl.return_value = calculate_per_position_pnl(123)

        # When
        from src.rules.daily_unrealized_loss import DailyUnrealizedLossRule
        rule = DailyUnrealizedLossRule(
            config,
            mock_pnl_tracker,
            mock_actions,
            mock_lockout_manager,
            mock_logger
        )

        breach = rule.check_with_current_prices(123)

        if breach:
            rule.enforce(123, breach)

        # Then
        assert breach is not None
        assert breach['contract_id'] == 'CON.F.US.MNQ.U25'
        assert breach['unrealized_pnl'] == -350.00

        mock_actions.close_position.assert_called_once_with(123, 'CON.F.US.MNQ.U25')
        assert mock_actions.close_all_positions.call_count == 0
        mock_lockout_manager.set_lockout.assert_not_called()
