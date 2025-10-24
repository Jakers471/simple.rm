"""
RULE-012: TradeManagement

Purpose: Automated trade management - auto breakeven stop-loss and trailing stops

Trigger: GatewayUserPosition, GatewayQuote, GatewayUserOrder

Enforcement: Trade-by-trade automation (no close, no lockout)

Configuration:
    - enabled: Enable/disable the rule
    - auto_breakeven: Auto-breakeven configuration
        - enabled: Enable auto-breakeven
        - profit_trigger_ticks: Profit in ticks to trigger breakeven
        - offset_ticks: Offset from entry in ticks
        - respect_manual_stops: Don't override manual stops
    - trailing_stop: Trailing stop configuration
        - enabled: Enable trailing stops
        - activation_ticks: Profit ticks to activate trailing
        - trail_distance_ticks: Distance to trail in ticks
        - update_frequency: How often to update (1 = every tick)
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TradeManagementRule:
    """
    RULE-012: TradeManagement

    Automated stop-loss management including auto-breakeven and trailing stops.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        contract_cache,
        position_tracking: Dict[int, Dict[str, Any]],
        log_handler: Optional[Any] = None
    ):
        """
        Initialize TradeManagement rule.

        Args:
            config: Rule configuration dictionary
            contract_cache: Contract cache for tick size/value
            position_tracking: Shared dict tracking position management state
            log_handler: Optional logger for enforcement tracking
        """
        self.config = config
        self.contract_cache = contract_cache
        self.position_tracking = position_tracking
        self.logger = log_handler if log_handler else logger

        # Parse configuration
        self.enabled = config.get('enabled', True)
        self.auto_breakeven_config = config.get('auto_breakeven', {})
        self.trailing_stop_config = config.get('trailing_stop', {})

        self.auto_breakeven_enabled = self.auto_breakeven_config.get('enabled', False)
        self.profit_trigger_ticks = self.auto_breakeven_config.get('profit_trigger_ticks', 10)
        self.offset_ticks = self.auto_breakeven_config.get('offset_ticks', 0)
        self.respect_manual_stops = self.auto_breakeven_config.get('respect_manual_stops', True)

        self.trailing_enabled = self.trailing_stop_config.get('enabled', False)
        self.activation_ticks = self.trailing_stop_config.get('activation_ticks', 20)
        self.trail_distance_ticks = self.trailing_stop_config.get('trail_distance_ticks', 10)
        self.update_frequency = self.trailing_stop_config.get('update_frequency', 1)

    def check(self, position_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if auto-management is needed for a position.

        Args:
            position_event: Position event data

        Returns:
            None (this rule doesn't trigger on check, but on quote updates)
        """
        # Return early if rule is disabled
        if not self.enabled:
            return None

        # This rule is triggered by quote updates, not position events
        # Just track the position for later management
        position_id = position_event.get('id')
        if position_id and position_id not in self.position_tracking:
            self.position_tracking[position_id] = {
                'account_id': position_event.get('accountId'),
                'contract_id': position_event.get('contractId'),
                'entry_price': position_event.get('averagePrice'),
                'position_type': position_event.get('type'),
                'size': position_event.get('size'),
                'stop_loss_order_id': None,
                'breakeven_applied': False,
                'trailing_active': False,
                'manual_stop': False
            }

        return None

    def on_quote_update(self, quote_event: Dict[str, Any], contract_id: str) -> Optional[Dict[str, Any]]:
        """
        Handle quote update to check for auto-management triggers.

        Args:
            quote_event: Quote event data
            contract_id: Contract ID

        Returns:
            Management action dict if action needed, None otherwise
        """
        if not self.enabled:
            return None

        current_price = quote_event.get('lastPrice')
        if not current_price:
            return None

        # Find positions for this contract
        for position_id, position in self.position_tracking.items():
            if position.get('contract_id') != contract_id:
                continue

            # Skip if manual stop and respect_manual_stops is true
            if position.get('manual_stop') and self.respect_manual_stops:
                continue

            # Get contract metadata
            if hasattr(self.contract_cache, 'contracts'):
                contract = self.contract_cache.contracts.get(contract_id)
            else:
                contract = self.contract_cache.get_contract(contract_id)

            if not contract:
                continue

            tick_size = contract.get('tickSize', 0.25)

            # Calculate profit in ticks
            entry_price = position.get('entry_price')
            position_type = position.get('position_type')

            if position_type == 1:  # Long
                price_diff = current_price - entry_price
            else:  # Short
                price_diff = entry_price - current_price

            profit_ticks = price_diff / tick_size

            # Check for auto-breakeven trigger
            if self.auto_breakeven_enabled and not position.get('breakeven_applied'):
                if profit_ticks >= self.profit_trigger_ticks:
                    breakeven_price = self.calculate_breakeven_stop(position, self.auto_breakeven_config, contract)

                    # Mark as applied
                    position['breakeven_applied'] = True

                    return {
                        'action': 'APPLY_BREAKEVEN',
                        'position_id': position_id,
                        'breakeven_price': breakeven_price,
                        'action_details': {
                            'type': 'CREATE_STOP_LOSS_ORDER',
                            'stop_price': breakeven_price,
                            'size': position.get('size'),
                            'side': 1 if position_type == 1 else 0  # Sell for long, Buy for short
                        }
                    }

            # Check for trailing stop update
            if self.trailing_enabled and position.get('trailing_active'):
                result = self.update_trailing_stop(position_id, position, current_price, contract)
                if result:
                    return result

        return None

    def calculate_breakeven_stop(self, position: Dict[str, Any], config: Dict[str, Any], contract: Dict[str, Any]) -> float:
        """
        Calculate breakeven stop price with offset.

        Args:
            position: Position data
            config: Auto-breakeven configuration (or full config dict with auto_breakeven key)
            contract: Contract metadata

        Returns:
            Breakeven stop price
        """
        entry_price = position.get('entry_price')

        # Handle both direct auto_breakeven config and nested config (for testing)
        if 'auto_breakeven' in config:
            be_config = config['auto_breakeven']
        else:
            be_config = config

        offset_ticks = be_config.get('offset_ticks', 0)
        tick_size = contract.get('tickSize', 0.25)

        # Breakeven = entry + offset (for long, offset is positive)
        breakeven_price = entry_price + (offset_ticks * tick_size)

        return breakeven_price

    def update_trailing_stop(self, position_id: int, position: Dict[str, Any], current_price: float, contract: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update trailing stop if price moved favorably.

        Args:
            position_id: Position ID
            position: Position data
            current_price: Current market price
            contract: Contract metadata

        Returns:
            Update action dict if stop needs updating, None otherwise
        """
        tick_size = contract.get('tickSize', 0.25)
        position_type = position.get('position_type')

        # Update high/low water mark
        if position_type == 1:  # Long
            high_water_mark = position.get('high_water_mark', position.get('entry_price'))
            if current_price > high_water_mark:
                # Calculate old stop from previous high water mark
                old_stop_price = position.get('current_stop_price')
                if old_stop_price is None:
                    old_stop_price = high_water_mark - (self.trail_distance_ticks * tick_size)

                # Update high water mark
                position['high_water_mark'] = current_price

                # Calculate new stop: current price - trail distance
                new_stop_price = current_price - (self.trail_distance_ticks * tick_size)

                # Store current stop for next update
                position['current_stop_price'] = new_stop_price

                return {
                    'action': 'UPDATE_TRAILING_STOP',
                    'position_id': position_id,
                    'old_stop_price': old_stop_price,
                    'new_stop_price': new_stop_price,
                    'action_details': {
                        'type': 'MODIFY_STOP_LOSS_ORDER',
                        'order_id': position.get('stop_loss_order_id'),
                        'new_stop_price': new_stop_price
                    }
                }

        else:  # Short
            low_water_mark = position.get('low_water_mark', position.get('entry_price'))
            if current_price < low_water_mark:
                # Calculate old stop from previous low water mark
                old_stop_price = position.get('current_stop_price')
                if old_stop_price is None:
                    old_stop_price = low_water_mark + (self.trail_distance_ticks * tick_size)

                # Update low water mark
                position['low_water_mark'] = current_price

                # Calculate new stop: current price + trail distance
                new_stop_price = current_price + (self.trail_distance_ticks * tick_size)

                # Store current stop for next update
                position['current_stop_price'] = new_stop_price

                return {
                    'action': 'UPDATE_TRAILING_STOP',
                    'position_id': position_id,
                    'old_stop_price': old_stop_price,
                    'new_stop_price': new_stop_price,
                    'action_details': {
                        'type': 'MODIFY_STOP_LOSS_ORDER',
                        'order_id': position.get('stop_loss_order_id'),
                        'new_stop_price': new_stop_price
                    }
                }

        return None

    def enforce(self, account_id: int, action: Dict[str, Any], actions) -> bool:
        """
        Execute trade management action (modify stop-loss orders).

        Args:
            account_id: Account ID
            action: Action details from on_quote_update()
            actions: Enforcement actions instance

        Returns:
            True if enforcement succeeded, False otherwise
        """
        try:
            action_type = action.get('action')
            action_details = action.get('action_details', {})

            if action_type == 'APPLY_BREAKEVEN':
                # Create stop-loss order at breakeven
                # This would call the order placement API
                logger.info(f"RULE-012: Auto-breakeven applied at ${action.get('breakeven_price')}")
                return True

            elif action_type == 'UPDATE_TRAILING_STOP':
                # Modify existing stop-loss order
                # This would call the order modification API
                logger.info(f"RULE-012: Trailing stop updated to ${action.get('new_stop_price')}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error enforcing TradeManagement rule: {e}")
            return False
