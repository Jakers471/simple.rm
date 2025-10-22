"""
Unit tests for RULE-010: Auth Loss Guard

Tests the rule that monitors TopstepX canTrade status and enforces
lockout when API signals account is restricted.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime


@pytest.fixture
def mock_state_manager():
    """Mock state manager for canTrade tracking."""
    manager = Mock()
    manager.can_trade_status = {}
    manager.positions = {}
    return manager


@pytest.fixture
def mock_lockout_manager():
    """Mock lockout manager."""
    manager = Mock()
    manager.active_lockouts = {}
    return manager


@pytest.fixture
def mock_actions():
    """Mock enforcement actions."""
    return Mock()


class TestAuthLossGuard:
    """Test suite for RULE-010: Auth Loss Guard."""

    def test_check_normal_trading_event(self, mock_state_manager, mock_lockout_manager):
        """
        GIVEN: Account with canTrade=true
        WHEN: Account event is checked
        THEN: No breach, trading allowed
        """
        # Given
        account_event = {
            "id": 123,
            "name": "Main Trading Account",
            "balance": 10000.50,
            "canTrade": True,
            "isVisible": True
        }

        config = {
            'enabled': True,
            'enforcement': 'close_all_and_lockout'
        }

        mock_state_manager.can_trade_status = {123: True}

        # When
        from src.rules.auth_loss_guard import AuthLossGuardRule
        rule = AuthLossGuardRule(config, mock_state_manager, mock_lockout_manager)
        result = rule.check(account_event)

        # Then
        assert result is None
        assert mock_lockout_manager.is_locked_out(123) == False
        assert mock_state_manager.can_trade_status[123] == True

    def test_check_auth_event_detected(self, mock_state_manager, mock_lockout_manager, mock_actions):
        """
        GIVEN: canTrade changes from true to false
        WHEN: Account event is checked
        THEN: Breach detected, close all and lockout
        """
        # Given
        account_event = {
            "id": 123,
            "canTrade": False,  # Restricted!
            "balance": 10000.50
        }

        config = {
            'enabled': True,
            'enforcement': 'close_all_and_lockout',
            'auto_unlock_on_restore': True
        }

        mock_state_manager.can_trade_status = {123: True}  # Was true
        mock_state_manager.positions = {
            123: [
                {'id': 456, 'contractId': 'CON.F.US.MNQ.U25'},
                {'id': 457, 'contractId': 'CON.F.US.ES.U25'}
            ]
        }

        # When
        from src.rules.auth_loss_guard import AuthLossGuardRule
        rule = AuthLossGuardRule(config, mock_state_manager, mock_lockout_manager, mock_actions)
        result = rule.check(account_event)

        # Then
        assert result is not None
        assert result['breach'] == True
        assert result['event_type'] == 'canTrade_disabled'
        assert result['previous_state'] == True
        assert result['current_state'] == False

        action = result['action']
        assert action['type'] == 'CLOSE_ALL_AND_LOCKOUT'
        assert action['reason'] == 'Account restricted by TopstepX (canTrade=false)'
        assert action['lockout_until'] is None  # Indefinite

        assert mock_state_manager.can_trade_status[123] == False

    def test_check_auth_restored(self, mock_state_manager, mock_lockout_manager):
        """
        GIVEN: canTrade changes from false to true
        WHEN: Account event is checked
        THEN: Lockout removed
        """
        # Given
        account_event = {
            "id": 123,
            "canTrade": True,  # Restored!
            "balance": 10000.50
        }

        config = {
            'enabled': True,
            'auto_unlock_on_restore': True
        }

        mock_state_manager.can_trade_status = {123: False}  # Was false
        mock_lockout_manager.active_lockouts = {
            123: {
                'reason': 'Account restricted by TopstepX',
                'until': None,
                'applied_at': datetime(2024, 7, 21, 14, 0, 0)
            }
        }

        # When
        from src.rules.auth_loss_guard import AuthLossGuardRule
        rule = AuthLossGuardRule(config, mock_state_manager, mock_lockout_manager)
        result = rule.check(account_event)

        # Then
        assert result is not None
        assert result['breach'] == False
        assert result['event_type'] == 'canTrade_enabled'
        assert result['previous_state'] == False
        assert result['current_state'] == True

        action = result['action']
        assert action['type'] == 'REMOVE_LOCKOUT'
        assert action['reason'] == 'TopstepX restored trading (canTrade=true)'

        assert mock_state_manager.can_trade_status[123] == True

    def test_check_daemon_starts_with_restricted_account(self, mock_state_manager, mock_lockout_manager, mock_actions):
        """
        GIVEN: Daemon startup with canTrade=false
        WHEN: Initial state checked
        THEN: Lockout applied immediately
        """
        # Given
        account_info = {
            "id": 123,
            "canTrade": False,  # Already restricted
            "balance": 10000.50
        }

        config = {
            'enabled': True,
            'check_on_startup': True,
            'enforcement': 'close_all_and_lockout'
        }

        mock_state_manager.can_trade_status = {}  # No previous state
        mock_state_manager.positions = {
            123: [{'id': 456, 'contractId': 'CON.F.US.MNQ.U25'}]
        }

        # When
        from src.rules.auth_loss_guard import AuthLossGuardRule
        rule = AuthLossGuardRule(config, mock_state_manager, mock_lockout_manager, mock_actions)
        result = rule.check_initial_state(123, account_info)

        # Then
        assert result is not None
        assert result['breach'] == True
        assert result['event_type'] == 'canTrade_disabled_on_startup'

        action = result['action']
        assert action['type'] == 'CLOSE_ALL_AND_LOCKOUT'
        assert action['reason'] == 'Account has canTrade=false on startup'

        assert mock_state_manager.can_trade_status[123] == False

    def test_check_no_position_to_close(self, mock_state_manager, mock_lockout_manager):
        """
        GIVEN: canTrade=false but no open positions
        WHEN: Account event is checked
        THEN: Lockout still applied
        """
        # Given
        account_event = {
            "id": 123,
            "canTrade": False
        }

        config = {
            'enabled': True,
            'enforcement': 'close_all_and_lockout'
        }

        mock_state_manager.can_trade_status = {123: True}
        mock_state_manager.positions = {123: []}  # No positions

        # When
        from src.rules.auth_loss_guard import AuthLossGuardRule
        rule = AuthLossGuardRule(config, mock_state_manager, mock_lockout_manager)
        result = rule.check(account_event)

        # Then
        assert result is not None
        assert result['breach'] == True

        action = result['action']
        assert action['type'] == 'CLOSE_ALL_AND_LOCKOUT'
        assert action['positions_to_close'] == 0

    def test_check_rapid_toggle(self, mock_state_manager, mock_lockout_manager):
        """
        GIVEN: canTrade toggles: true→false→true→false
        WHEN: Events processed in sequence
        THEN: Each state change handled independently
        """
        # Given
        config = {
            'enabled': True,
            'auto_unlock_on_restore': True
        }

        mock_state_manager.can_trade_status = {123: True}
        mock_lockout_manager.active_lockouts = {}

        event1 = {"id": 123, "canTrade": False}
        event2 = {"id": 123, "canTrade": True}
        event3 = {"id": 123, "canTrade": False}

        # When
        from src.rules.auth_loss_guard import AuthLossGuardRule
        rule = AuthLossGuardRule(config, mock_state_manager, mock_lockout_manager)

        result1 = rule.check(event1)
        mock_state_manager.can_trade_status[123] = False

        result2 = rule.check(event2)
        mock_state_manager.can_trade_status[123] = True

        result3 = rule.check(event3)
        mock_state_manager.can_trade_status[123] = False

        # Then
        assert result1['breach'] == True
        assert result1['event_type'] == 'canTrade_disabled'

        assert result2['breach'] == False
        assert result2['event_type'] == 'canTrade_enabled'

        assert result3['breach'] == True
        assert result3['event_type'] == 'canTrade_disabled'

        assert mock_state_manager.can_trade_status[123] == False
