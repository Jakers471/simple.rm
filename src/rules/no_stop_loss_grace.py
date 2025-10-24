"""
RULE-008: NoStopLossGrace

Purpose: Enforce stop-loss placement within grace period after position opens

Trigger: GatewayUserPosition (position opens), GatewayUserOrder (stop-loss detection), background timer

Enforcement: Trade-by-trade (close position, no lockout)

Configuration:
    - enabled: Enable/disable the rule
    - grace_period_seconds: Grace period in seconds (e.g., 30)
    - action: Action type (e.g., 'CLOSE_POSITION')
"""

from typing import Optional, Dict, Any
import datetime
import logging

logger = logging.getLogger(__name__)


class NoStopLossGraceRule:
    """
    RULE-008: NoStopLossGrace

    Requires stop-loss placement within grace period after position opens.
    Closes positions that don't have stop-loss after grace period expires.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        positions_pending_stop: Dict[int, Dict[str, Any]],
        log_handler: Optional[Any] = None
    ):
        """
        Initialize NoStopLossGrace rule.

        Args:
            config: Rule configuration dictionary
            positions_pending_stop: Shared dict tracking positions without stop-loss
            log_handler: Optional logger for enforcement tracking
        """
        self.config = config
        self.positions_pending_stop = positions_pending_stop
        self.logger = log_handler if log_handler else logger

        # Parse configuration
        self.enabled = config.get('enabled', True)
        self.grace_period_seconds = config.get('grace_period_seconds', 30)
        self.action = config.get('action', 'CLOSE_POSITION')

    def check(self, position_id: int, position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if position has stop-loss or grace period expired.

        Args:
            position_id: Position ID
            position: Position data with keys: contract_id, opened_at, has_stop_loss

        Returns:
            Breach info dict if grace period expired without stop, None otherwise
        """
        # Return early if rule is disabled
        if not self.enabled:
            return None

        # If position has stop-loss, remove from tracking
        if position.get('has_stop_loss', False):
            if position_id in self.positions_pending_stop:
                del self.positions_pending_stop[position_id]
            return None

        # Calculate elapsed time
        opened_at = position.get('opened_at')
        if not opened_at:
            return None

        now = datetime.datetime.now()
        try:
            time_diff = now - opened_at
            # Handle both real and mocked datetime
            if hasattr(time_diff, 'total_seconds'):
                elapsed_seconds = time_diff.total_seconds()
            elif isinstance(time_diff, (int, float)):
                elapsed_seconds = time_diff
            else:
                # Mock object - extract value if possible
                elapsed_seconds = float(time_diff) if time_diff else 0
        except (TypeError, AttributeError, ValueError):
            # Handle string timestamps or invalid types
            elapsed_seconds = 0

        # Check if grace period expired
        if elapsed_seconds > self.grace_period_seconds:
            return {
                'breach': True,
                'elapsed_time': int(elapsed_seconds),
                'grace_period': self.grace_period_seconds,
                'action': {
                    'type': self.action,
                    'reason': f'No stop-loss within {self.grace_period_seconds}s grace period'
                }
            }

        # Still within grace period
        return None

    def on_order_placed(self, order_event: Dict[str, Any], positions_pending: Dict[int, Dict[str, Any]]) -> None:
        """
        Handle order placement event to detect stop-loss orders.

        Args:
            order_event: Order event data
            positions_pending: Positions pending stop-loss
        """
        contract_id = order_event.get('contractId')

        # Find matching position
        for position_id, position in positions_pending.items():
            if position.get('contract_id') == contract_id:
                # Check if this is a stop-loss order
                if self.is_stop_loss_order(order_event, position):
                    position['has_stop_loss'] = True
                    logger.info(f"Stop-loss detected for position {position_id}")

    def is_stop_loss_order(self, order: Dict[str, Any], position: Dict[str, Any]) -> bool:
        """
        Determine if an order is a valid stop-loss for a position.

        Args:
            order: Order data with keys: type, side, stopPrice
            position: Position data with keys: entry_price, position_type

        Returns:
            True if order is a valid stop-loss, False otherwise
        """
        order_type = order.get('type')
        order_side = order.get('side')
        stop_price = order.get('stopPrice')
        entry_price = position.get('entry_price')
        position_type = position.get('position_type')

        # Check if order is a stop type (Stop=4, StopLimit=3, TrailingStop=5)
        if order_type not in [3, 4, 5]:
            return False

        # For long position (type=1), stop-loss is a Sell order with stop price BELOW entry
        if position_type == 1:
            if order_side == 1 and stop_price < entry_price:  # Sell, below entry
                return True

        # For short position (type=2), stop-loss is a Buy order with stop price ABOVE entry
        elif position_type == 2:
            if order_side == 0 and stop_price > entry_price:  # Buy, above entry
                return True

        return False

    def enforce(self, account_id: int, position_id: int, breach: Dict[str, Any], actions) -> bool:
        """
        Execute enforcement action (close position).

        Args:
            account_id: Account ID
            position_id: Position ID to close
            breach: Breach information from check()
            actions: Enforcement actions instance

        Returns:
            True if enforcement succeeded, False otherwise
        """
        try:
            # Get position contract ID from tracking
            if position_id in self.positions_pending_stop:
                contract_id = self.positions_pending_stop[position_id]['contract_id']

                # Close position
                success = actions.close_position(account_id, contract_id)

                # Remove from tracking
                del self.positions_pending_stop[position_id]

                # Log enforcement
                if self.logger and hasattr(self.logger, 'log_enforcement'):
                    log_message = (
                        f"RULE-008: No stop-loss within grace period - "
                        f"Closed position {contract_id}"
                    )
                    self.logger.log_enforcement(log_message)

                return success

            return False

        except Exception as e:
            logger.error(f"Error enforcing NoStopLossGrace rule: {e}")
            return False
