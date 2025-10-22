"""
Unit tests for RULE-001: MaxContracts

Tests the MaxContracts rule which enforces maximum net contract limits
across all positions in an account.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime


@pytest.fixture
def mock_state_manager():
    """Mock state manager for position tracking."""
    return Mock()


@pytest.fixture
def mock_actions():
    """Mock enforcement actions."""
    return Mock()


@pytest.fixture
def mock_logger():
    """Mock logger for enforcement tracking."""
    return Mock()


class TestMaxContracts:
    """Test suite for RULE-001: MaxContracts."""

    def test_check_under_limit(self, mock_state_manager, mock_actions):
        """
        GIVEN: Configuration with limit=5, account has 4 net contracts
        WHEN: Position event is checked
        THEN: No breach detected, no enforcement actions called
        """
        # Given
        config = {
            'enabled': True,
            'limit': 5,
            'count_type': 'net',
            'close_all': True,
            'lockout_on_breach': False
        }

        mock_state_manager.get_position_count.return_value = 4  # Net 4 contracts

        position_event = {
            'id': 456,
            'accountId': 123,
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 1,  # Long
            'size': 2,
            'averagePrice': 21000.5
        }

        # When
        from src.rules.max_contracts import MaxContractsRule
        rule = MaxContractsRule(config, mock_state_manager, mock_actions)
        result = rule.check(position_event)

        # Then
        assert result is None
        mock_actions.close_all_positions.assert_not_called()
        mock_state_manager.get_position_count.assert_called_once_with(123)

    def test_check_at_limit(self, mock_state_manager, mock_actions):
        """
        GIVEN: Configuration with limit=5, account has exactly 5 contracts
        WHEN: Position event is checked
        THEN: No breach (at limit is acceptable)
        """
        # Given
        config = {
            'enabled': True,
            'limit': 5,
            'count_type': 'net',
            'close_all': True
        }

        mock_state_manager.get_position_count.return_value = 5

        position_event = {
            'accountId': 123,
            'contractId': 'CON.F.US.ES.U25',
            'type': 1,
            'size': 2
        }

        # When
        from src.rules.max_contracts import MaxContractsRule
        rule = MaxContractsRule(config, mock_state_manager, mock_actions)
        result = rule.check(position_event)

        # Then
        assert result is None
        mock_actions.close_all_positions.assert_not_called()

    def test_check_breach_by_one(self, mock_state_manager, mock_actions, mock_logger):
        """
        GIVEN: Configuration with limit=5, account has 6 contracts
        WHEN: Position event is checked and enforced
        THEN: Breach detected, close_all_positions called, enforcement logged
        """
        # Given
        config = {
            'enabled': True,
            'limit': 5,
            'count_type': 'net',
            'close_all': True,
            'lockout_on_breach': False
        }

        mock_state_manager.get_position_count.return_value = 6  # Breach!
        mock_actions.close_all_positions.return_value = True

        position_event = {
            'accountId': 123,
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 1,
            'size': 3
        }

        # When
        from src.rules.max_contracts import MaxContractsRule
        rule = MaxContractsRule(config, mock_state_manager, mock_actions, mock_logger)
        breach = rule.check(position_event)

        if breach:
            rule.enforce(123, breach)

        # Then
        assert breach is not None
        assert breach['rule_id'] == 'RULE-001'
        assert breach['action'] == 'CLOSE_ALL_POSITIONS'
        assert breach['reason'] == 'MaxContracts breach (net=6, limit=5)'

        mock_actions.close_all_positions.assert_called_once_with(123)
        mock_logger.log_enforcement.assert_called_once()

        log_message = mock_logger.log_enforcement.call_args[0][0]
        assert 'MaxContracts breach' in log_message
        assert 'net=6' in log_message
        assert 'limit=5' in log_message

    def test_check_net_calculation(self, mock_state_manager, mock_actions):
        """
        GIVEN: Account with Long 7, Short 2 = Net 5
        WHEN: Position is checked
        THEN: Net calculation correctly computed, no breach at limit
        """
        # Given
        config = {
            'enabled': True,
            'limit': 5,
            'count_type': 'net'
        }

        # Mock returns net calculation result
        mock_state_manager.get_position_count.return_value = 5

        position_event = {
            'accountId': 123,
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 1,
            'size': 7
        }

        # When
        from src.rules.max_contracts import MaxContractsRule
        rule = MaxContractsRule(config, mock_state_manager, mock_actions)
        result = rule.check(position_event)

        # Then
        assert result is None
        mock_state_manager.get_position_count.assert_called_once_with(123)

    def test_check_reduce_to_limit_mode(self, mock_state_manager, mock_actions, mock_logger):
        """
        GIVEN: reduce_to_limit enabled, account has 6 contracts (limit=5)
        WHEN: Position is checked and enforced
        THEN: reduce_positions_to_limit called instead of close_all
        """
        # Given
        config = {
            'enabled': True,
            'limit': 5,
            'count_type': 'net',
            'close_all': False,
            'reduce_to_limit': True
        }

        mock_state_manager.get_position_count.return_value = 6
        mock_state_manager.get_all_positions.return_value = [
            {'contract_id': 'CON.F.US.MNQ.U25', 'size': 3},
            {'contract_id': 'CON.F.US.ES.U25', 'size': 3}
        ]

        mock_actions.reduce_positions_to_limit.return_value = True

        position_event = {
            'accountId': 123,
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 1,
            'size': 3
        }

        # When
        from src.rules.max_contracts import MaxContractsRule
        rule = MaxContractsRule(config, mock_state_manager, mock_actions, mock_logger)
        breach = rule.check(position_event)

        if breach:
            rule.enforce(123, breach)

        # Then
        assert breach is not None
        assert breach['action'] == 'REDUCE_TO_LIMIT'

        mock_actions.reduce_positions_to_limit.assert_called_once_with(123, target_net=5)
        mock_actions.close_all_positions.assert_not_called()

        log_message = mock_logger.log_enforcement.call_args[0][0]
        assert 'Reduced' in log_message
        assert 'from 6 to 5' in log_message

    def test_check_ignores_closed_positions(self, mock_state_manager, mock_actions):
        """
        GIVEN: Account has 2 open positions and 1 closed (size=0)
        WHEN: Position is checked
        THEN: Closed positions not counted, net = 3
        """
        # Given
        config = {
            'enabled': True,
            'limit': 3,
            'count_type': 'net'
        }

        # State manager returns count excluding closed positions
        mock_state_manager.get_position_count.return_value = 3

        position_event = {
            'accountId': 123,
            'contractId': 'CON.F.US.NQ.U25',
            'type': 1,
            'size': 1
        }

        # When
        from src.rules.max_contracts import MaxContractsRule
        rule = MaxContractsRule(config, mock_state_manager, mock_actions)
        result = rule.check(position_event)

        # Then
        assert result is None
        mock_state_manager.get_position_count.assert_called_once_with(123)
