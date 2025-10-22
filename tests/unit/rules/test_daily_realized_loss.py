"""
Unit tests for RULE-003: DailyRealizedLoss

Tests the DailyRealizedLoss rule which enforces daily loss limits
and triggers lockout until reset time.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, time


@pytest.fixture
def mock_pnl_tracker():
    """Mock P&L tracker for realized P&L calculations."""
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


class TestDailyRealizedLoss:
    """Test suite for RULE-003: DailyRealizedLoss."""

    def test_check_under_limit(self, mock_pnl_tracker, mock_actions, mock_lockout_manager):
        """
        GIVEN: Limit=-500, daily P&L=-400
        WHEN: Trade is checked
        THEN: No breach, P&L tracker updated, no enforcement
        """
        # Given
        config = {
            'enabled': True,
            'limit': -500,
            'reset_time': '17:00',
            'timezone': 'America/New_York',
            'enforcement': 'close_all_and_lockout',
            'lockout_until_reset': True
        }

        mock_pnl_tracker.get_daily_realized_pnl.return_value = -400

        trade_event = {
            'id': 101112,
            'accountId': 123,
            'profitAndLoss': -50,
            'contractId': 'CON.F.US.MNQ.U25'
        }

        # When
        from src.rules.daily_realized_loss import DailyRealizedLossRule
        rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)
        result = rule.check(trade_event)

        # Then
        assert result is None
        mock_pnl_tracker.add_trade_pnl.assert_called_once_with(123, -50)
        mock_actions.close_all_positions.assert_not_called()
        mock_lockout_manager.set_lockout.assert_not_called()

    def test_check_at_limit(self, mock_pnl_tracker, mock_actions, mock_lockout_manager):
        """
        GIVEN: Limit=-500, daily P&L=-500 (exactly at limit)
        WHEN: Trade is checked
        THEN: No breach (at limit is acceptable)
        """
        # Given
        config = {
            'enabled': True,
            'limit': -500
        }

        mock_pnl_tracker.add_trade_pnl.return_value = -500

        trade_event = {
            'accountId': 123,
            'profitAndLoss': -100
        }

        # When
        from src.rules.daily_realized_loss import DailyRealizedLossRule
        rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)
        result = rule.check(trade_event)

        # Then
        assert result is None
        mock_actions.close_all_positions.assert_not_called()
        mock_lockout_manager.set_lockout.assert_not_called()

    def test_check_breach_by_one_dollar(self, mock_pnl_tracker, mock_actions, mock_lockout_manager, mock_logger):
        """
        GIVEN: Limit=-500, trade causes daily P&L=-501
        WHEN: Trade is checked and enforced
        THEN: Breach detected, all positions closed, lockout set until reset
        """
        # Given
        config = {
            'enabled': True,
            'limit': -500,
            'reset_time': '17:00',
            'timezone': 'America/New_York',
            'lockout_until_reset': True
        }

        mock_pnl_tracker.add_trade_pnl.return_value = -501  # Breach!
        mock_actions.close_all_positions.return_value = True
        mock_actions.cancel_all_orders.return_value = True

        mock_now = datetime(2025, 1, 17, 14, 30, 0)
        expected_reset = datetime.combine(mock_now.date(), time(17, 0))

        trade_event = {
            'accountId': 123,
            'profitAndLoss': -201
        }

        # When
        from src.rules.daily_realized_loss import DailyRealizedLossRule
        rule = DailyRealizedLossRule(
            config,
            mock_pnl_tracker,
            mock_actions,
            mock_lockout_manager,
            mock_logger
        )

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now

            breach = rule.check(trade_event)

            if breach:
                rule.enforce(123, breach)

        # Then
        assert breach is not None
        assert breach['rule_id'] == 'RULE-003'
        assert breach['action'] == 'CLOSE_ALL_AND_LOCKOUT'
        assert breach['daily_pnl'] == -501
        assert breach['limit'] == -500

        mock_actions.close_all_positions.assert_called_once_with(123)
        mock_actions.cancel_all_orders.assert_called_once_with(123)

        mock_lockout_manager.set_lockout.assert_called_once()
        lockout_call = mock_lockout_manager.set_lockout.call_args
        assert lockout_call[1]['account_id'] == 123
        assert lockout_call[1]['until'] == expected_reset
        assert 'Daily loss limit hit' in lockout_call[1]['reason']

        mock_logger.log_enforcement.assert_called_once()

    def test_check_lockout_until_next_reset(self, mock_pnl_tracker, mock_actions, mock_lockout_manager):
        """
        GIVEN: Limit=-500, breach at 2:00 PM
        WHEN: Breach is enforced
        THEN: Lockout set until 5:00 PM same day (3 hours)
        """
        # Given
        config = {
            'enabled': True,
            'limit': -500,
            'reset_time': '17:00',
            'lockout_until_reset': True
        }

        mock_pnl_tracker.add_trade_pnl.return_value = -550

        mock_now = datetime(2025, 1, 17, 14, 0, 0)
        expected_reset = datetime(2025, 1, 17, 17, 0, 0)

        trade_event = {
            'accountId': 123,
            'profitAndLoss': -550
        }

        # When
        from src.rules.daily_realized_loss import DailyRealizedLossRule
        rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.combine = datetime.combine

            breach = rule.check(trade_event)
            if breach:
                rule.enforce(123, breach)

        # Then
        mock_lockout_manager.set_lockout.assert_called_once()
        lockout_call = mock_lockout_manager.set_lockout.call_args[1]
        assert lockout_call['until'] == expected_reset
        assert (expected_reset - mock_now).total_seconds() == 3 * 3600

    def test_check_after_daily_reset(self, mock_pnl_tracker, mock_actions, mock_lockout_manager):
        """
        GIVEN: After daily reset, P&L=0
        WHEN: First trade after reset (-50)
        THEN: No breach, trading allowed
        """
        # Given
        config = {
            'enabled': True,
            'limit': -500
        }

        mock_pnl_tracker.get_daily_realized_pnl.return_value = 0
        mock_pnl_tracker.add_trade_pnl.return_value = -50

        trade_event = {
            'accountId': 123,
            'profitAndLoss': -50
        }

        # When
        from src.rules.daily_realized_loss import DailyRealizedLossRule
        rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)
        result = rule.check(trade_event)

        # Then
        assert result is None
        mock_actions.close_all_positions.assert_not_called()
        mock_lockout_manager.set_lockout.assert_not_called()

    def test_check_ignores_half_turn_trades(self, mock_pnl_tracker, mock_actions):
        """
        GIVEN: Trade with profitAndLoss=None (half-turn)
        WHEN: Trade is checked
        THEN: P&L tracker not updated, no check performed
        """
        # Given
        config = {
            'enabled': True,
            'limit': -500
        }

        trade_event = {
            'accountId': 123,
            'profitAndLoss': None,  # Half-turn
            'contractId': 'CON.F.US.MNQ.U25',
            'side': 0,
            'size': 1
        }

        # When
        from src.rules.daily_realized_loss import DailyRealizedLossRule
        rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, None)
        result = rule.check(trade_event)

        # Then
        assert result is None
        mock_pnl_tracker.add_trade_pnl.assert_not_called()

    def test_check_multiple_trades_accumulation(self, mock_pnl_tracker, mock_actions, mock_lockout_manager):
        """
        GIVEN: Limit=-500, multiple trades accumulating
        WHEN: 4 trades processed: +100, -50, -200, -450
        THEN: First 3 pass, 4th triggers breach (-600 total)
        """
        # Given
        config = {
            'enabled': True,
            'limit': -500
        }

        daily_pnl_sequence = [
            100,    # Trade 1
            -50,    # Trade 2
            -150,   # Trade 3
            -600    # Trade 4: BREACH!
        ]

        mock_pnl_tracker.add_trade_pnl.side_effect = daily_pnl_sequence

        trades = [
            {'accountId': 123, 'profitAndLoss': 100},
            {'accountId': 123, 'profitAndLoss': -150},
            {'accountId': 123, 'profitAndLoss': -200},
            {'accountId': 123, 'profitAndLoss': -350}
        ]

        # When
        from src.rules.daily_realized_loss import DailyRealizedLossRule
        rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)

        results = []
        for trade in trades:
            result = rule.check(trade)
            results.append(result)

        # Then
        assert results[0] is None
        assert results[1] is None
        assert results[2] is None

        assert results[3] is not None
        assert results[3]['daily_pnl'] == -600

        assert mock_pnl_tracker.add_trade_pnl.call_count == 4

    def test_check_lockout_after_5pm_goes_to_next_day(self, mock_pnl_tracker, mock_actions, mock_lockout_manager):
        """
        GIVEN: Breach at 6:00 PM (after 5:00 PM reset time)
        WHEN: Breach is enforced
        THEN: Lockout set until next day 5:00 PM
        """
        # Given
        config = {
            'enabled': True,
            'limit': -500,
            'reset_time': '17:00',
            'lockout_until_reset': True
        }

        mock_pnl_tracker.add_trade_pnl.return_value = -600

        mock_now = datetime(2025, 1, 17, 18, 0, 0)
        expected_reset = datetime(2025, 1, 18, 17, 0, 0)

        trade_event = {
            'accountId': 123,
            'profitAndLoss': -600
        }

        # When
        from src.rules.daily_realized_loss import DailyRealizedLossRule
        rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.combine = datetime.combine

            breach = rule.check(trade_event)
            if breach:
                rule.enforce(123, breach)

        # Then
        mock_lockout_manager.set_lockout.assert_called_once()
        lockout_call = mock_lockout_manager.set_lockout.call_args[1]
        assert lockout_call['until'] == expected_reset
        assert lockout_call['until'].day == 18
