"""
Unit tests for RULE-006: TradeFrequencyLimit

Tests the TradeFrequencyLimit rule which enforces per-minute, per-hour,
and per-session trade frequency limits with cooldown periods.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta


@pytest.fixture
def mock_trade_counter():
    """Mock trade counter for frequency tracking."""
    return Mock()


@pytest.fixture
def mock_lockout_manager():
    """Mock lockout manager for cooldowns."""
    return Mock()


@pytest.fixture
def mock_logger():
    """Mock logger for enforcement tracking."""
    return Mock()


class TestTradeFrequencyLimit:
    """Test suite for RULE-006: TradeFrequencyLimit."""

    def test_check_under_per_minute_limit(self, mock_trade_counter, mock_lockout_manager):
        """
        GIVEN: Limit=3/minute, account has 2 trades this minute
        WHEN: Trade is checked
        THEN: No breach, trade recorded, no cooldown
        """
        # Given
        config = {
            'enabled': True,
            'limits': {
                'per_minute': 3,
                'per_hour': 10,
                'per_session': 50
            },
            'cooldown_on_breach': {
                'enabled': True,
                'per_minute_breach': 60
            }
        }

        mock_trade_counter.record_trade.return_value = {
            'minute': 2,
            'hour': 5,
            'session': 15
        }

        trade_event = {
            'id': 101112,
            'accountId': 123,
            'contractId': 'CON.F.US.MNQ.U25',
            'creationTimestamp': '2025-01-17T14:30:00Z'
        }

        # When
        from src.rules.trade_frequency_limit import TradeFrequencyLimitRule
        rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager)
        result = rule.check(trade_event)

        # Then
        assert result is None
        mock_trade_counter.record_trade.assert_called_once()
        mock_lockout_manager.set_cooldown.assert_not_called()

    def test_check_breach_per_minute(self, mock_trade_counter, mock_lockout_manager, mock_logger):
        """
        GIVEN: Limit=3/minute, this is 4th trade in minute
        WHEN: Trade is checked and enforced
        THEN: Breach detected, 60-second cooldown set
        """
        # Given
        config = {
            'enabled': True,
            'limits': {
                'per_minute': 3
            },
            'cooldown_on_breach': {
                'enabled': True,
                'per_minute_breach': 60
            }
        }

        mock_trade_counter.record_trade.return_value = {
            'minute': 4,  # Breach!
            'hour': 4,
            'session': 4
        }

        trade_event = {
            'accountId': 123,
            'creationTimestamp': '2025-01-17T14:30:30Z'
        }

        # When
        from src.rules.trade_frequency_limit import TradeFrequencyLimitRule
        rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager, mock_logger)
        breach = rule.check(trade_event)

        if breach:
            rule.enforce(123, breach)

        # Then
        assert breach is not None
        assert breach['rule_id'] == 'RULE-006'
        assert breach['breach_type'] == 'per_minute'
        assert breach['trade_count'] == 4
        assert breach['limit'] == 3

        mock_lockout_manager.set_cooldown.assert_called_once()
        cooldown_call = mock_lockout_manager.set_cooldown.call_args[1]
        assert cooldown_call['account_id'] == 123
        assert cooldown_call['duration_seconds'] == 60
        assert '4/3 trades' in cooldown_call['reason']

        mock_logger.log_enforcement.assert_called_once()

    def test_check_breach_per_hour(self, mock_trade_counter, mock_lockout_manager, mock_logger):
        """
        GIVEN: Limit=10/hour, this is 11th trade in hour
        WHEN: Trade is checked and enforced
        THEN: Breach detected, 30-minute cooldown set
        """
        # Given
        config = {
            'enabled': True,
            'limits': {
                'per_minute': 10,
                'per_hour': 10
            },
            'cooldown_on_breach': {
                'enabled': True,
                'per_hour_breach': 1800  # 30 minutes
            }
        }

        mock_trade_counter.record_trade.return_value = {
            'minute': 1,
            'hour': 11,  # Breach!
            'session': 20
        }

        trade_event = {
            'accountId': 123,
            'creationTimestamp': '2025-01-17T14:45:00Z'
        }

        # When
        from src.rules.trade_frequency_limit import TradeFrequencyLimitRule
        rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager, mock_logger)
        breach = rule.check(trade_event)

        if breach:
            rule.enforce(123, breach)

        # Then
        assert breach is not None
        assert breach['breach_type'] == 'per_hour'
        assert breach['trade_count'] == 11
        assert breach['limit'] == 10

        mock_lockout_manager.set_cooldown.assert_called_once()
        cooldown_call = mock_lockout_manager.set_cooldown.call_args[1]
        assert cooldown_call['duration_seconds'] == 1800

    def test_check_breach_per_session(self, mock_trade_counter, mock_lockout_manager, mock_logger):
        """
        GIVEN: Limit=50/session, this is 51st trade
        WHEN: Trade is checked and enforced
        THEN: Breach detected, 1-hour cooldown set
        """
        # Given
        config = {
            'enabled': True,
            'limits': {
                'per_minute': 10,
                'per_hour': 20,
                'per_session': 50
            },
            'cooldown_on_breach': {
                'enabled': True,
                'per_session_breach': 3600  # 1 hour
            }
        }

        mock_trade_counter.record_trade.return_value = {
            'minute': 1,
            'hour': 5,
            'session': 51  # Breach!
        }

        trade_event = {
            'accountId': 123,
            'creationTimestamp': '2025-01-17T15:30:00Z'
        }

        # When
        from src.rules.trade_frequency_limit import TradeFrequencyLimitRule
        rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager, mock_logger)
        breach = rule.check(trade_event)

        if breach:
            rule.enforce(123, breach)

        # Then
        assert breach is not None
        assert breach['breach_type'] == 'per_session'
        assert breach['trade_count'] == 51
        assert breach['limit'] == 50

        mock_lockout_manager.set_cooldown.assert_called_once()
        cooldown_call = mock_lockout_manager.set_cooldown.call_args[1]
        assert cooldown_call['duration_seconds'] == 3600

    def test_check_cooldown_duration(self, mock_trade_counter, mock_lockout_manager):
        """
        GIVEN: Custom cooldown duration = 120 seconds
        WHEN: Breach is enforced
        THEN: Cooldown matches configured duration
        """
        # Given
        config = {
            'enabled': True,
            'limits': {
                'per_minute': 3
            },
            'cooldown_on_breach': {
                'enabled': True,
                'per_minute_breach': 120  # 2 minutes
            }
        }

        mock_trade_counter.record_trade.return_value = {
            'minute': 4,
            'hour': 4,
            'session': 4
        }

        trade_event = {
            'accountId': 123,
            'creationTimestamp': '2025-01-17T14:30:00Z'
        }

        # When
        from src.rules.trade_frequency_limit import TradeFrequencyLimitRule
        rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager)
        breach = rule.check(trade_event)

        if breach:
            rule.enforce(123, breach)

        # Then
        mock_lockout_manager.set_cooldown.assert_called_once()
        cooldown_call = mock_lockout_manager.set_cooldown.call_args[1]
        assert cooldown_call['duration_seconds'] == 120

    def test_check_ignores_voided_trades(self, mock_trade_counter, mock_lockout_manager):
        """
        GIVEN: 4 trades, but 1 is voided
        WHEN: All trades checked
        THEN: Only 3 non-voided trades counted
        """
        # Given
        config = {
            'enabled': True,
            'limits': {
                'per_minute': 3
            }
        }

        mock_trade_counter.record_trade.side_effect = [
            {'minute': 1, 'hour': 1, 'session': 1},
            {'minute': 2, 'hour': 2, 'session': 2},
            {'minute': 2, 'hour': 2, 'session': 2},  # Voided (doesn't increment)
            {'minute': 3, 'hour': 3, 'session': 3}
        ]

        trades = [
            {'accountId': 123, 'voided': False},
            {'accountId': 123, 'voided': False},
            {'accountId': 123, 'voided': True},   # Should be ignored
            {'accountId': 123, 'voided': False}
        ]

        # When
        from src.rules.trade_frequency_limit import TradeFrequencyLimitRule
        rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager)

        results = []
        for trade in trades:
            if not trade.get('voided'):
                result = rule.check(trade)
                results.append(result)

        # Then
        assert all(r is None for r in results)
        assert mock_trade_counter.record_trade.call_count == 3

    def test_check_rolling_window(self, mock_trade_counter, mock_lockout_manager):
        """
        GIVEN: 3 trades at t=0, 10s, 20s, 4th trade at t=70s
        WHEN: 4th trade checked (first aged out)
        THEN: Only 2 trades in rolling minute window, no breach
        """
        # Given
        config = {
            'enabled': True,
            'limits': {
                'per_minute': 3
            }
        }

        mock_trade_counter.record_trade.side_effect = [
            {'minute': 1, 'hour': 1, 'session': 1},
            {'minute': 2, 'hour': 2, 'session': 2},
            {'minute': 3, 'hour': 3, 'session': 3},  # At limit
            {'minute': 3, 'hour': 4, 'session': 4}   # After 70s, only 2 in window
        ]

        base_time = datetime(2025, 1, 17, 14, 0, 0)

        trades = [
            {'accountId': 123, 'creationTimestamp': base_time.isoformat()},
            {'accountId': 123, 'creationTimestamp': (base_time + timedelta(seconds=10)).isoformat()},
            {'accountId': 123, 'creationTimestamp': (base_time + timedelta(seconds=20)).isoformat()},
            {'accountId': 123, 'creationTimestamp': (base_time + timedelta(seconds=70)).isoformat()}
        ]

        # When
        from src.rules.trade_frequency_limit import TradeFrequencyLimitRule
        rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager)

        results = []
        for trade in trades:
            result = rule.check(trade)
            results.append(result)

        # Then
        assert all(r is None for r in results)

    def test_check_multiple_breach_types(self, mock_trade_counter, mock_lockout_manager, mock_logger):
        """
        GIVEN: Limits per_minute=3, per_hour=10, trade breaches BOTH
        WHEN: Trade is checked and enforced
        THEN: Most severe cooldown applied (hour > minute)
        """
        # Given
        config = {
            'enabled': True,
            'limits': {
                'per_minute': 3,
                'per_hour': 10
            },
            'cooldown_on_breach': {
                'enabled': True,
                'per_minute_breach': 60,
                'per_hour_breach': 1800
            }
        }

        mock_trade_counter.record_trade.return_value = {
            'minute': 4,  # Breach minute
            'hour': 11,   # Breach hour
            'session': 15
        }

        trade_event = {
            'accountId': 123,
            'creationTimestamp': '2025-01-17T14:30:00Z'
        }

        # When
        from src.rules.trade_frequency_limit import TradeFrequencyLimitRule
        rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager, mock_logger)
        breach = rule.check(trade_event)

        if breach:
            rule.enforce(123, breach)

        # Then
        assert breach is not None

        mock_lockout_manager.set_cooldown.assert_called_once()
        cooldown_call = mock_lockout_manager.set_cooldown.call_args[1]
        assert cooldown_call['duration_seconds'] == 1800  # Hour cooldown

        mock_logger.log_enforcement.assert_called()
        log_message = mock_logger.log_enforcement.call_args[0][0]
        assert ('per_minute' in log_message or 'per_hour' in log_message)
