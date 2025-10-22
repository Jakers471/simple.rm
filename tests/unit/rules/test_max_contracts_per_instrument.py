"""
Unit tests for RULE-002: MaxContractsPerInstrument

Tests the MaxContractsPerInstrument rule which enforces per-symbol
position size limits.
"""

import pytest
from unittest.mock import Mock


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


class TestMaxContractsPerInstrument:
    """Test suite for RULE-002: MaxContractsPerInstrument."""

    def test_check_under_limit(self, mock_state_manager, mock_actions):
        """
        GIVEN: MNQ limit=2, account has 2 MNQ contracts
        WHEN: MNQ position is checked
        THEN: No breach (at limit), no enforcement
        """
        # Given
        config = {
            'enabled': True,
            'limits': {
                'MNQ': 2,
                'ES': 1,
                'NQ': 1
            },
            'enforcement': 'reduce_to_limit',
            'unknown_symbol_action': 'block'
        }

        mock_state_manager.get_contract_count.return_value = 2

        position_event = {
            'accountId': 123,
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 1,
            'size': 2
        }

        # When
        from src.rules.max_contracts_per_instrument import MaxContractsPerInstrumentRule
        rule = MaxContractsPerInstrumentRule(config, mock_state_manager, mock_actions)
        result = rule.check(position_event)

        # Then
        assert result is None
        mock_actions.reduce_position.assert_not_called()
        mock_actions.close_position.assert_not_called()

    def test_check_breach_for_instrument(self, mock_state_manager, mock_actions, mock_logger):
        """
        GIVEN: MNQ limit=3, account has 4 MNQ contracts
        WHEN: Position is checked and enforced
        THEN: Breach detected, reduce_position called to reduce by 1
        """
        # Given
        config = {
            'enabled': True,
            'limits': {
                'MNQ': 3,
                'ES': 1
            },
            'enforcement': 'reduce_to_limit'
        }

        mock_state_manager.get_contract_count.return_value = 4  # Breach!
        mock_actions.reduce_position.return_value = True

        position_event = {
            'accountId': 123,
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 1,
            'size': 4
        }

        # When
        from src.rules.max_contracts_per_instrument import MaxContractsPerInstrumentRule
        rule = MaxContractsPerInstrumentRule(config, mock_state_manager, mock_actions, mock_logger)
        breach = rule.check(position_event)

        if breach:
            rule.enforce(123, breach)

        # Then
        assert breach is not None
        assert breach['rule_id'] == 'RULE-002'
        assert breach['action'] == 'REDUCE_POSITION'
        assert breach['symbol'] == 'MNQ'
        assert breach['current_size'] == 4
        assert breach['limit'] == 3

        mock_actions.reduce_position.assert_called_once_with(
            123,
            'CON.F.US.MNQ.U25',
            reduce_by=1
        )

        log_message = mock_logger.log_enforcement.call_args[0][0]
        assert 'MNQ' in log_message
        assert 'Reduced from 4 to 3' in log_message

    def test_check_unknown_symbol_block(self, mock_state_manager, mock_actions, mock_logger):
        """
        GIVEN: RTY not in configured limits, unknown_symbol_action='block'
        WHEN: RTY position is checked
        THEN: Breach detected, close_position called
        """
        # Given
        config = {
            'enabled': True,
            'limits': {
                'MNQ': 2,
                'ES': 1
            },
            'enforcement': 'close_all',
            'unknown_symbol_action': 'block'
        }

        mock_state_manager.get_contract_count.return_value = 1
        mock_actions.close_position.return_value = True

        position_event = {
            'accountId': 123,
            'contractId': 'CON.F.US.RTY.U25',  # RTY not in limits
            'type': 1,
            'size': 1
        }

        # When
        from src.rules.max_contracts_per_instrument import MaxContractsPerInstrumentRule
        rule = MaxContractsPerInstrumentRule(config, mock_state_manager, mock_actions, mock_logger)
        breach = rule.check(position_event)

        if breach:
            rule.enforce(123, breach)

        # Then
        assert breach is not None
        assert breach['action'] == 'CLOSE_POSITION'
        assert breach['reason'] == 'Unknown symbol not in configured limits'
        assert breach['symbol'] == 'RTY'

        mock_actions.close_position.assert_called_once_with(
            123,
            'CON.F.US.RTY.U25'
        )

        log_message = mock_logger.log_enforcement.call_args[0][0]
        assert 'Unknown symbol' in log_message or 'RTY' in log_message

    def test_check_multiple_instruments(self, mock_state_manager, mock_actions):
        """
        GIVEN: MNQ limit=2, ES limit=1, both positions within limits
        WHEN: Both positions checked
        THEN: No breaches for either
        """
        # Given
        config = {
            'enabled': True,
            'limits': {
                'MNQ': 2,
                'ES': 1
            },
            'enforcement': 'reduce_to_limit'
        }

        def get_contract_count_side_effect(account_id, contract_id):
            if 'MNQ' in contract_id:
                return 2
            elif 'ES' in contract_id:
                return 1
            return 0

        mock_state_manager.get_contract_count.side_effect = get_contract_count_side_effect

        mnq_event = {
            'accountId': 123,
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 1,
            'size': 2
        }

        es_event = {
            'accountId': 123,
            'contractId': 'CON.F.US.ES.U25',
            'type': 1,
            'size': 1
        }

        # When
        from src.rules.max_contracts_per_instrument import MaxContractsPerInstrumentRule
        rule = MaxContractsPerInstrumentRule(config, mock_state_manager, mock_actions)
        result_mnq = rule.check(mnq_event)
        result_es = rule.check(es_event)

        # Then
        assert result_mnq is None
        assert result_es is None
        mock_actions.reduce_position.assert_not_called()
        mock_actions.close_position.assert_not_called()

    def test_check_net_per_instrument(self, mock_state_manager, mock_actions):
        """
        GIVEN: MNQ limit=3, account has Long 4 Short 2 = Net 2 MNQ
        WHEN: Position is checked
        THEN: Net 2 within limit of 3, no breach
        """
        # Given
        config = {
            'enabled': True,
            'limits': {
                'MNQ': 3
            },
            'enforcement': 'reduce_to_limit'
        }

        mock_state_manager.get_contract_count.return_value = 2  # Net

        position_event = {
            'accountId': 123,
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 1,
            'size': 4
        }

        # When
        from src.rules.max_contracts_per_instrument import MaxContractsPerInstrumentRule
        rule = MaxContractsPerInstrumentRule(config, mock_state_manager, mock_actions)
        result = rule.check(position_event)

        # Then
        assert result is None
        mock_state_manager.get_contract_count.assert_called_with(123, 'CON.F.US.MNQ.U25')

    def test_check_close_all_enforcement_mode(self, mock_state_manager, mock_actions, mock_logger):
        """
        GIVEN: enforcement='close_all', MNQ limit=2, account has 3 MNQ
        WHEN: Position is checked and enforced
        THEN: Entire position closed (not reduced)
        """
        # Given
        config = {
            'enabled': True,
            'limits': {
                'MNQ': 2
            },
            'enforcement': 'close_all'
        }

        mock_state_manager.get_contract_count.return_value = 3
        mock_actions.close_position.return_value = True

        position_event = {
            'accountId': 123,
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 1,
            'size': 3
        }

        # When
        from src.rules.max_contracts_per_instrument import MaxContractsPerInstrumentRule
        rule = MaxContractsPerInstrumentRule(config, mock_state_manager, mock_actions, mock_logger)
        breach = rule.check(position_event)

        if breach:
            rule.enforce(123, breach)

        # Then
        assert breach is not None
        assert breach['action'] == 'CLOSE_ALL'

        mock_actions.close_position.assert_called_once_with(
            123,
            'CON.F.US.MNQ.U25'
        )
        mock_actions.reduce_position.assert_not_called()

        log_message = mock_logger.log_enforcement.call_args[0][0]
        assert 'Closed entire position' in log_message
