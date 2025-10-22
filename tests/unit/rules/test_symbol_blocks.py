"""
Unit tests for RULE-011: Symbol Blocks

Tests the rule that blacklists specific symbols - immediately closes
any position and permanently prevents trading in blocked instruments.
"""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_lockout_manager():
    """Mock lockout manager for symbol lockouts."""
    return Mock()


@pytest.fixture
def mock_actions():
    """Mock enforcement actions."""
    return Mock()


@pytest.fixture
def mock_logger():
    """Mock logger for enforcement tracking."""
    return Mock()


class TestSymbolBlocks:
    """Test suite for RULE-011: Symbol Blocks."""

    def test_check_allowed_symbol(self, mock_lockout_manager, mock_actions):
        """
        GIVEN: MNQ allowed (RTY, BTC blocked)
        WHEN: MNQ position is checked
        THEN: No breach, position allowed
        """
        # Given
        position_event = {
            "id": 456,
            "accountId": 123,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,
            "size": 2
        }

        config = {
            'enabled': True,
            'blocked_symbols': ['RTY', 'BTC'],
            'action': 'CANCEL_ORDER',
            'close_existing': True
        }

        # When
        from src.rules.symbol_blocks import SymbolBlocksRule
        from src.utils.symbol_utils import extract_symbol_root

        rule = SymbolBlocksRule(config, mock_lockout_manager, mock_actions)
        symbol = extract_symbol_root(position_event['contractId'])
        result = rule.check(position_event)

        # Then
        assert symbol == 'MNQ'
        assert result is None
        assert mock_lockout_manager.is_symbol_locked(123, 'MNQ') == False

    def test_check_blocked_symbol_position(self, mock_lockout_manager, mock_actions, mock_logger):
        """
        GIVEN: RTY in blocked list
        WHEN: RTY position is checked
        THEN: Breach detected, position closed, symbol locked
        """
        # Given
        position_event = {
            "id": 457,
            "accountId": 123,
            "contractId": "CON.F.US.RTY.H25",
            "type": 1,
            "size": 1
        }

        config = {
            'enabled': True,
            'blocked_symbols': ['RTY', 'BTC'],
            'action': 'CANCEL_ORDER',
            'close_existing': True
        }

        mock_actions.close_position.return_value = True

        # When
        from src.rules.symbol_blocks import SymbolBlocksRule
        from src.utils.symbol_utils import extract_symbol_root

        rule = SymbolBlocksRule(config, mock_lockout_manager, mock_actions, mock_logger)
        symbol = extract_symbol_root(position_event['contractId'])
        breach = rule.check(position_event)

        if breach:
            rule.enforce(123, breach)

        # Then
        assert symbol == 'RTY'
        assert breach is not None
        assert breach['breach'] == True
        assert breach['symbol_root'] == 'RTY'
        assert breach['contract_id'] == 'CON.F.US.RTY.H25'

        action = breach['action']
        assert action['type'] == 'CLOSE_POSITION_AND_SYMBOL_LOCKOUT'
        assert action['symbol'] == 'RTY'
        assert action['reason'] == 'Symbol RTY is permanently blocked'
        assert action['lockout_until'] is None  # Permanent

    def test_check_blocked_symbol_order(self, mock_lockout_manager, mock_actions, mock_logger):
        """
        GIVEN: BTC in blocked list
        WHEN: BTC order is checked
        THEN: Breach detected, order canceled
        """
        # Given
        order_event = {
            "id": 789,
            "accountId": 123,
            "contractId": "CON.F.US.BTC.Z25",
            "symbolId": "F.US.BTC",
            "status": 1,
            "type": 1,
            "side": 0,
            "size": 1
        }

        config = {
            'enabled': True,
            'blocked_symbols': ['RTY', 'BTC'],
            'action': 'CANCEL_ORDER'
        }

        # When
        from src.rules.symbol_blocks import SymbolBlocksRule
        rule = SymbolBlocksRule(config, mock_lockout_manager, mock_actions, mock_logger)

        symbol = order_event['symbolId'].split('.')[-1]
        breach = rule.check_order(order_event)

        if breach:
            rule.enforce(123, breach)

        # Then
        assert symbol == 'BTC'
        assert breach is not None
        assert breach['symbol_root'] == 'BTC'

        action = breach['action']
        assert action['type'] == 'CANCEL_ORDER'
        assert action['order_id'] == 789
        assert action['reason'] == 'Order in blocked symbol BTC'

    def test_check_similar_symbol_not_blocked(self, mock_lockout_manager, mock_actions):
        """
        GIVEN: ES blocked (not MES)
        WHEN: MES position is checked
        THEN: No breach (exact match only)
        """
        # Given
        position_event = {
            "id": 458,
            "accountId": 123,
            "contractId": "CON.F.US.MES.U25",
            "type": 1,
            "size": 4
        }

        config = {
            'enabled': True,
            'blocked_symbols': ['ES'],
            'close_existing': True
        }

        # When
        from src.rules.symbol_blocks import SymbolBlocksRule
        from src.utils.symbol_utils import extract_symbol_root

        rule = SymbolBlocksRule(config, mock_lockout_manager, mock_actions)
        symbol = extract_symbol_root(position_event['contractId'])
        result = rule.check(position_event)

        # Then
        assert symbol == 'MES'
        assert symbol != 'ES'
        assert result is None
        assert mock_lockout_manager.is_symbol_locked(123, 'MES') == False

    def test_check_multiple_contracts_same_symbol(self, mock_lockout_manager, mock_actions, mock_logger):
        """
        GIVEN: RTY blocked, multiple RTY expiry months
        WHEN: Both positions checked
        THEN: Both trigger breach (symbol-level block)
        """
        # Given
        position1 = {
            "id": 459,
            "accountId": 123,
            "contractId": "CON.F.US.RTY.H25",  # March
            "type": 1,
            "size": 1
        }

        position2 = {
            "id": 460,
            "accountId": 123,
            "contractId": "CON.F.US.RTY.M25",  # June
            "type": 1,
            "size": 1
        }

        config = {
            'enabled': True,
            'blocked_symbols': ['RTY'],
            'close_existing': True
        }

        # When
        from src.rules.symbol_blocks import SymbolBlocksRule
        from src.utils.symbol_utils import extract_symbol_root

        rule = SymbolBlocksRule(config, mock_lockout_manager, mock_actions, mock_logger)

        symbol1 = extract_symbol_root(position1['contractId'])
        symbol2 = extract_symbol_root(position2['contractId'])

        result1 = rule.check(position1)
        result2 = rule.check(position2)

        # Then
        assert symbol1 == 'RTY'
        assert symbol2 == 'RTY'

        assert result1 is not None
        assert result1['breach'] == True
        assert result1['symbol_root'] == 'RTY'

        assert result2 is not None
        assert result2['breach'] == True
        assert result2['symbol_root'] == 'RTY'

    def test_check_contract_id_parsing_edge_case(self, mock_lockout_manager, mock_actions, mock_logger):
        """
        GIVEN: Unusual contract ID format
        WHEN: Position is checked
        THEN: Fallback parsing, no breach if doesn't match
        """
        # Given
        position_event = {
            "id": 461,
            "accountId": 123,
            "contractId": "UNUSUAL.FORMAT.RTY",
            "type": 1,
            "size": 1
        }

        config = {
            'enabled': True,
            'blocked_symbols': ['RTY']
        }

        # When
        from src.rules.symbol_blocks import SymbolBlocksRule
        rule = SymbolBlocksRule(config, mock_lockout_manager, mock_actions, mock_logger)

        def extract_symbol_root_with_fallback(contract_id):
            parts = contract_id.split('.')
            if len(parts) >= 4:
                return parts[3]
            return contract_id

        symbol = extract_symbol_root_with_fallback(position_event['contractId'])
        result = rule.check(position_event)

        # Then
        assert symbol == 'UNUSUAL.FORMAT.RTY'
        assert result is None  # Doesn't match 'RTY' exactly
