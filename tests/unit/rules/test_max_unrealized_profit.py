"""
Unit tests for RULE-005: MaxUnrealizedProfit

Tests the MaxUnrealizedProfit rule which triggers profit targets
to lock in gains and prevent giving back profits.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, time, timedelta


@pytest.fixture
def mock_pnl_tracker():
    """Mock P&L tracker for unrealized profit calculations."""
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


class TestMaxUnrealizedProfit:
    """Test suite for RULE-005: MaxUnrealizedProfit."""

    def test_check_under_limit(self, mock_pnl_tracker, mock_actions, mock_lockout_manager):
        """
        GIVEN: Profit target=1000, unrealized P&L=800
        WHEN: Position is checked
        THEN: No breach, no enforcement
        """
        # Given
        config = {
            'enabled': True,
            'mode': 'profit_target',
            'profit_target': 1000.00,
            'scope': 'total',
            'action': 'CLOSE_ALL_AND_LOCKOUT'
        }

        mock_pnl_tracker.calculate_unrealized_pnl.return_value = 800.00

        # When
        from src.rules.max_unrealized_profit import MaxUnrealizedProfitRule
        rule = MaxUnrealizedProfitRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)
        result = rule.check_with_current_prices(123)

        # Then
        assert result is None
        mock_actions.close_all_positions.assert_not_called()
        mock_lockout_manager.set_lockout.assert_not_called()

    def test_check_breach(self, mock_pnl_tracker, mock_actions, mock_lockout_manager, mock_logger):
        """
        GIVEN: Profit target=1000, unrealized P&L=1100
        WHEN: Check is performed and enforced
        THEN: Breach detected, all positions closed, lockout set
        """
        # Given
        config = {
            'enabled': True,
            'mode': 'profit_target',
            'profit_target': 1000.00,
            'scope': 'total',
            'action': 'CLOSE_ALL_AND_LOCKOUT',
            'reset_time': '17:00'
        }

        mock_pnl_tracker.calculate_unrealized_pnl.return_value = 1100.00
        mock_actions.close_all_positions.return_value = True
        mock_actions.cancel_all_orders.return_value = True

        mock_now = datetime(2025, 1, 17, 14, 30, 0)
        expected_reset = datetime(2025, 1, 17, 17, 0, 0)

        # When
        from src.rules.max_unrealized_profit import MaxUnrealizedProfitRule
        rule = MaxUnrealizedProfitRule(
            config,
            mock_pnl_tracker,
            mock_actions,
            mock_lockout_manager,
            mock_logger
        )

        with patch('src.rules.max_unrealized_profit.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.time = time
            mock_datetime.timedelta = timedelta

            breach = rule.check_with_current_prices(123)

            if breach:
                rule.enforce(123, breach)

        # Then
        assert breach is not None
        assert breach['rule_id'] == 'RULE-005'
        assert breach['action'] == 'CLOSE_ALL_AND_LOCKOUT'
        assert breach['unrealized_pnl'] == 1100.00
        assert breach['target'] == 1000.00

        mock_actions.close_all_positions.assert_called_once_with(123)
        mock_actions.cancel_all_orders.assert_called_once_with(123)

        mock_lockout_manager.set_lockout.assert_called_once()
        lockout_call = mock_lockout_manager.set_lockout.call_args[1]
        assert 'profit target hit' in lockout_call['reason'].lower()

        mock_logger.log_enforcement.assert_called_once()
        log_message = mock_logger.log_enforcement.call_args[0][0]
        assert 'profit target' in log_message.lower()

    def test_check_long_position_winning(self, mock_state_manager, mock_contract_cache, mock_quote_tracker, mock_actions):
        """
        GIVEN: Long 2 MNQ @ 21000, current 21100 = +$400
        WHEN: Unrealized P&L calculated
        THEN: Correctly calculates +$400 profit
        """
        # Given
        config = {
            'enabled': True,
            'profit_target': 1000.00
        }

        mock_contract_cache.get_contract.return_value = {
            'tickSize': 0.25,
            'tickValue': 0.50
        }

        mock_quote_tracker.get_quote.return_value = {
            'lastPrice': 21100.00  # Price went up
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

        from src.rules.max_unrealized_profit import MaxUnrealizedProfitRule
        rule = MaxUnrealizedProfitRule(config, pnl_tracker, mock_actions, None)

        unrealized_pnl = pnl_tracker.calculate_unrealized_pnl(123)

        # Then
        # Ticks moved: (21100 - 21000) / 0.25 = 400 ticks
        # P&L: 400 * 0.50 * 2 = +$400
        assert unrealized_pnl == 400.00

        breach = rule.check_with_current_prices(123)
        assert breach is None  # Under target

    def test_check_short_position_winning(self, mock_state_manager, mock_contract_cache, mock_quote_tracker, mock_actions):
        """
        GIVEN: Short 2 MNQ @ 21000, current 20900 = +$400
        WHEN: Unrealized P&L calculated
        THEN: Correctly calculates +$400 profit
        """
        # Given
        config = {
            'enabled': True,
            'profit_target': 1000.00
        }

        mock_contract_cache.get_contract.return_value = {
            'tickSize': 0.25,
            'tickValue': 0.50
        }

        mock_quote_tracker.get_quote.return_value = {
            'lastPrice': 20900.00  # Price went down
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

        from src.rules.max_unrealized_profit import MaxUnrealizedProfitRule
        rule = MaxUnrealizedProfitRule(config, pnl_tracker, mock_actions, None)

        unrealized_pnl = pnl_tracker.calculate_unrealized_pnl(123)

        # Then
        # Short profits when price goes down
        # Ticks moved: (21000 - 20900) / 0.25 = 400 ticks
        # P&L for short: 400 * 0.50 * 2 = +$400
        assert unrealized_pnl == 400.00

        breach = rule.check_with_current_prices(123)
        assert breach is None

    def test_check_breakeven_mode(self, mock_pnl_tracker, mock_actions, mock_logger):
        """
        GIVEN: mode='breakeven', position back to breakeven (P&L=0)
        WHEN: Check is performed and enforced
        THEN: Position closed at breakeven
        """
        # Given
        config = {
            'enabled': True,
            'mode': 'breakeven',
            'scope': 'per_position',
            'action': 'CLOSE_POSITION'
        }

        mock_pnl_tracker.calculate_per_position_pnl.return_value = {
            'CON.F.US.MNQ.U25': 0.00  # Breakeven
        }

        # When
        from src.rules.max_unrealized_profit import MaxUnrealizedProfitRule
        rule = MaxUnrealizedProfitRule(config, mock_pnl_tracker, mock_actions, None, mock_logger)
        breach = rule.check_with_current_prices(123)

        if breach:
            rule.enforce(123, breach)

        # Then
        assert breach is not None
        assert breach['mode'] == 'breakeven'
        assert breach['unrealized_pnl'] == 0.00

        mock_actions.close_position.assert_called_once_with(123, 'CON.F.US.MNQ.U25')

    def test_check_per_position_scope(self, mock_pnl_tracker, mock_actions, mock_logger):
        """
        GIVEN: scope='per_position', MNQ:+1100 (hit target), ES:+500 (OK)
        WHEN: Check is performed and enforced
        THEN: Only MNQ position closed, ES remains open
        """
        # Given
        config = {
            'enabled': True,
            'profit_target': 1000.00,
            'scope': 'per_position',
            'action': 'CLOSE_POSITION',
            'lockout': False
        }

        def calculate_per_position_pnl(account_id):
            return {
                'CON.F.US.MNQ.U25': 1100.00,  # Hit target!
                'CON.F.US.ES.U25': 500.00     # Still has room
            }

        mock_pnl_tracker.calculate_per_position_pnl.return_value = calculate_per_position_pnl(123)

        # When
        from src.rules.max_unrealized_profit import MaxUnrealizedProfitRule
        rule = MaxUnrealizedProfitRule(config, mock_pnl_tracker, mock_actions, None, mock_logger)
        breach = rule.check_with_current_prices(123)

        if breach:
            rule.enforce(123, breach)

        # Then
        assert breach is not None
        assert breach['contract_id'] == 'CON.F.US.MNQ.U25'
        assert breach['unrealized_pnl'] == 1100.00

        mock_actions.close_position.assert_called_once_with(123, 'CON.F.US.MNQ.U25')
        mock_actions.close_all_positions.assert_not_called()
