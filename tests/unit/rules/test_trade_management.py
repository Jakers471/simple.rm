"""
Unit tests for RULE-012: Trade Management

Tests automated trade management features including auto breakeven
stop-loss and trailing stops.
"""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_contract_cache():
    """Mock contract cache for tick metadata."""
    return Mock()


@pytest.fixture
def mock_position_tracking():
    """Mock position tracking dictionary."""
    return {}


class TestTradeManagement:
    """Test suite for RULE-012: Trade Management."""

    def test_check_position_without_auto_sl(self, mock_contract_cache, mock_position_tracking):
        """
        GIVEN: Auto-management disabled
        WHEN: Position is checked
        THEN: No action taken
        """
        # Given
        position_event = {
            "id": 456,
            "accountId": 123,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,
            "size": 2,
            "averagePrice": 21000.25
        }

        config = {
            'enabled': False,
            'auto_breakeven': {
                'enabled': False
            },
            'trailing_stop': {
                'enabled': False
            }
        }

        mock_contract_cache.contracts = {
            'CON.F.US.MNQ.U25': {
                'tickSize': 0.25,
                'tickValue': 0.50
            }
        }

        # When
        from src.rules.trade_management import TradeManagementRule
        rule = TradeManagementRule(config, mock_contract_cache, mock_position_tracking)
        result = rule.check(position_event)

        # Then
        assert result is None
        assert 456 not in mock_position_tracking

    def test_check_position_needs_auto_breakeven(self, mock_contract_cache, mock_position_tracking):
        """
        GIVEN: Long @ 21000, current 21002.50 (+10 ticks profit)
        WHEN: Quote update triggers check
        THEN: Breakeven stop action created
        """
        # Given
        mock_position_tracking[456] = {
            'account_id': 123,
            'contract_id': 'CON.F.US.MNQ.U25',
            'entry_price': 21000.00,
            'position_type': 1,
            'size': 2,
            'stop_loss_order_id': None,
            'breakeven_applied': False,
            'trailing_active': False
        }

        config = {
            'enabled': True,
            'auto_breakeven': {
                'enabled': True,
                'profit_trigger_ticks': 10,
                'offset_ticks': 0
            }
        }

        mock_contract_cache.contracts = {
            'CON.F.US.MNQ.U25': {
                'tickSize': 0.25,
                'tickValue': 0.50
            }
        }

        quote_event = {
            "symbol": "F.US.MNQ",
            "lastPrice": 21002.50  # +10 ticks
        }

        # When
        from src.rules.trade_management import TradeManagementRule
        rule = TradeManagementRule(config, mock_contract_cache, mock_position_tracking)
        result = rule.on_quote_update(quote_event, 'CON.F.US.MNQ.U25')

        # Then
        assert result is not None
        assert result['action'] == 'APPLY_BREAKEVEN'
        assert result['position_id'] == 456
        assert result['breakeven_price'] == 21000.00

        action = result['action_details']
        assert action['type'] == 'CREATE_STOP_LOSS_ORDER'
        assert action['stop_price'] == 21000.00
        assert action['size'] == 2
        assert action['side'] == 1  # Sell to close long

        assert mock_position_tracking[456]['breakeven_applied'] == True

    def test_check_auto_sl_price_calculation_long(self, mock_contract_cache):
        """
        GIVEN: Long @ 21000, breakeven + 2 tick offset
        WHEN: Breakeven stop calculated
        THEN: Stop price = 21000.50 (entry + 2 ticks)
        """
        # Given
        position = {
            'entry_price': 21000.00,
            'position_type': 1,
            'size': 1
        }

        config = {
            'auto_breakeven': {
                'profit_trigger_ticks': 10,
                'offset_ticks': 2
            }
        }

        contract = {
            'tickSize': 0.25
        }

        # When
        from src.rules.trade_management import TradeManagementRule
        rule = TradeManagementRule(config, mock_contract_cache, {})
        breakeven_price = rule.calculate_breakeven_stop(position, config, contract)

        # Then
        # Breakeven = entry + offset = 21000.00 + (2 * 0.25) = 21000.50
        assert breakeven_price == 21000.50

        stop_order = {
            'type': 4,
            'side': 1,  # Sell
            'stopPrice': 21000.50,
            'size': 1
        }

        assert stop_order['side'] == 1
        assert stop_order['stopPrice'] > position['entry_price']

    def test_check_trailing_stop_update_price_rises(self, mock_contract_cache, mock_position_tracking):
        """
        GIVEN: Long @ 21000, high water mark 21005, current 21010
        WHEN: Trailing stop updated
        THEN: Stop moves from 21002.50 to 21007.50
        """
        # Given
        mock_position_tracking[456] = {
            'account_id': 123,
            'contract_id': 'CON.F.US.MNQ.U25',
            'entry_price': 21000.00,
            'position_type': 1,
            'size': 2,
            'stop_loss_order_id': 789,
            'breakeven_applied': True,
            'trailing_active': True,
            'high_water_mark': 21005.00
        }

        config = {
            'trailing_stop': {
                'enabled': True,
                'activation_ticks': 20,
                'trail_distance_ticks': 10,
                'update_frequency': 1
            }
        }

        contract = {
            'tickSize': 0.25
        }

        current_price = 21010.00
        current_stop_price = 21002.50

        # When
        from src.rules.trade_management import TradeManagementRule
        rule = TradeManagementRule(config, mock_contract_cache, mock_position_tracking)
        result = rule.update_trailing_stop(456, mock_position_tracking[456], current_price, contract)

        # Then
        assert mock_position_tracking[456]['high_water_mark'] == 21010.00

        # New stop: 21010.00 - (10 * 0.25) = 21007.50
        new_stop_price = 21010.00 - (10 * 0.25)
        assert new_stop_price == 21007.50

        assert result is not None
        assert result['action'] == 'UPDATE_TRAILING_STOP'
        assert result['old_stop_price'] == 21002.50
        assert result['new_stop_price'] == 21007.50

        action = result['action_details']
        assert action['type'] == 'MODIFY_STOP_LOSS_ORDER'
        assert action['order_id'] == 789
        assert action['new_stop_price'] == 21007.50

    def test_check_position_already_has_manual_sl(self, mock_contract_cache, mock_position_tracking):
        """
        GIVEN: Position with manual stop-loss, respect_manual_stops=true
        WHEN: Quote triggers breakeven threshold
        THEN: No auto-management (respects manual stop)
        """
        # Given
        mock_position_tracking[456] = {
            'account_id': 123,
            'contract_id': 'CON.F.US.MNQ.U25',
            'entry_price': 21000.00,
            'position_type': 1,
            'size': 2,
            'stop_loss_order_id': 788,
            'breakeven_applied': False,
            'trailing_active': False,
            'manual_stop': True
        }

        config = {
            'enabled': True,
            'auto_breakeven': {
                'enabled': True,
                'respect_manual_stops': True
            }
        }

        current_price = 21002.50  # Would trigger breakeven

        # When
        from src.rules.trade_management import TradeManagementRule
        rule = TradeManagementRule(config, mock_contract_cache, mock_position_tracking)
        result = rule.on_quote_update({'lastPrice': current_price}, 'CON.F.US.MNQ.U25')

        # Then
        assert result is None
        assert mock_position_tracking[456]['stop_loss_order_id'] == 788
        assert mock_position_tracking[456]['manual_stop'] == True
        assert mock_position_tracking[456]['breakeven_applied'] == False

    def test_check_short_position_trailing_stop_price_drops(self, mock_contract_cache, mock_position_tracking):
        """
        GIVEN: Short @ 21000, low water mark 20995, current 20990
        WHEN: Trailing stop updated
        THEN: Stop moves from 20997.50 to 20992.50
        """
        # Given
        mock_position_tracking[457] = {
            'account_id': 123,
            'contract_id': 'CON.F.US.MNQ.U25',
            'entry_price': 21000.00,
            'position_type': 2,  # Short
            'size': 1,
            'stop_loss_order_id': 790,
            'breakeven_applied': False,
            'trailing_active': True,
            'low_water_mark': 20995.00
        }

        config = {
            'trailing_stop': {
                'enabled': True,
                'trail_distance_ticks': 10
            }
        }

        contract = {
            'tickSize': 0.25
        }

        current_price = 20990.00  # New low
        current_stop_price = 20997.50

        # When
        from src.rules.trade_management import TradeManagementRule
        rule = TradeManagementRule(config, mock_contract_cache, mock_position_tracking)
        result = rule.update_trailing_stop(457, mock_position_tracking[457], current_price, contract)

        # Then
        assert mock_position_tracking[457]['low_water_mark'] == 20990.00

        # New stop: 20990.00 + (10 * 0.25) = 20992.50
        new_stop_price = 20990.00 + (10 * 0.25)
        assert new_stop_price == 20992.50

        assert result is not None
        assert result['action'] == 'UPDATE_TRAILING_STOP'
        assert result['new_stop_price'] == 20992.50
        assert result['new_stop_price'] < current_stop_price  # Moved down

        action = result['action_details']
        assert action['type'] == 'MODIFY_STOP_LOSS_ORDER'
        assert action['order_id'] == 790
        assert action['new_stop_price'] == 20992.50
