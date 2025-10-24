"""
RULE-011: Symbol Blocks

Blacklist specific symbols - immediately close any position and
permanently prevent trading in blocked instruments.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def extract_symbol_root(contract_id: str) -> str:
    """
    Extract symbol root from contract ID.

    Examples:
    - "CON.F.US.RTY.H25" → "RTY"
    - "CON.F.US.ES.U25" → "ES"
    - "CON.F.US.MNQ.M25" → "MNQ"

    Args:
        contract_id: Full contract identifier

    Returns:
        Symbol root
    """
    parts = contract_id.split('.')
    if len(parts) >= 4:
        return parts[3]
    logger.warning(f"Unexpected contract ID format: {contract_id}")
    return contract_id


class SymbolBlocksRule:
    """
    RULE-011: Symbol Blocks

    Blocks trading in specific symbols by checking contract IDs.
    When a position or order is detected in a blocked symbol:
    - Close the position immediately
    - Cancel the order
    - Set permanent symbol lockout
    """

    def __init__(self, config: Dict[str, Any], lockout_manager=None,
                 actions=None, enforcement_logger=None):
        """
        Initialize Symbol Blocks rule.

        Args:
            config: Rule configuration with 'enabled', 'blocked_symbols', etc.
            lockout_manager: Manager for symbol-specific lockouts
            actions: Enforcement actions (close positions, cancel orders)
            enforcement_logger: Logger for enforcement tracking
        """
        self.config = config
        self.lockout_manager = lockout_manager
        self.actions = actions
        self.enforcement_logger = enforcement_logger or logger

        # Parse configuration
        self.enabled = config.get('enabled', True)
        self.blocked_symbols = config.get('blocked_symbols', [])
        self.action = config.get('action', 'CANCEL_ORDER')
        self.close_existing = config.get('close_existing', True)

    def check(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if position is in a blocked symbol.

        Args:
            event_data: Position event data with 'contractId', 'accountId', etc.

        Returns:
            Breach dict if symbol is blocked, None otherwise
        """
        if not self.enabled:
            return None

        contract_id = event_data.get('contractId')
        if not contract_id:
            return None

        # Extract symbol root from contract ID
        symbol_root = extract_symbol_root(contract_id)

        # Check if symbol is blocked
        if symbol_root in self.blocked_symbols:
            account_id = event_data.get('accountId')
            position_id = event_data.get('id')

            logger.warning(
                f"RULE-011 BREACH: Position {position_id} opened in blocked symbol "
                f"{symbol_root} - Contract: {contract_id}"
            )

            return {
                'breach': True,
                'symbol_root': symbol_root,
                'contract_id': contract_id,
                'action': {
                    'type': 'CLOSE_POSITION_AND_SYMBOL_LOCKOUT',
                    'symbol': symbol_root,
                    'reason': f'Symbol {symbol_root} is permanently blocked',
                    'lockout_until': None  # Permanent
                }
            }

        return None

    def check_order(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if order is for a blocked symbol.

        Args:
            event_data: Order event data with 'symbolId', 'orderId', etc.

        Returns:
            Breach dict if symbol is blocked, None otherwise
        """
        if not self.enabled:
            return None

        # Try symbolId first (easier to parse)
        symbol_id = event_data.get('symbolId')
        if symbol_id:
            # "F.US.RTY" → "RTY"
            symbol_root = symbol_id.split('.')[-1]
        else:
            # Fallback to contractId
            contract_id = event_data.get('contractId')
            if not contract_id:
                return None
            symbol_root = extract_symbol_root(contract_id)

        # Check if symbol is blocked
        if symbol_root in self.blocked_symbols:
            order_id = event_data.get('id')
            account_id = event_data.get('accountId')

            logger.warning(
                f"RULE-011 BREACH: Order {order_id} in blocked symbol {symbol_root}"
            )

            return {
                'breach': True,
                'symbol_root': symbol_root,
                'action': {
                    'type': self.action,
                    'order_id': order_id,
                    'reason': f'Order in blocked symbol {symbol_root}'
                }
            }

        return None

    def enforce(self, account_id: int, breach: Dict[str, Any]) -> None:
        """
        Enforce the symbol block (close position, set lockout).

        Args:
            account_id: Account ID that breached
            breach: Breach information from check() or check_order()
        """
        action = breach.get('action', {})
        action_type = action.get('type')
        symbol = breach.get('symbol_root')

        if action_type == 'CLOSE_POSITION_AND_SYMBOL_LOCKOUT':
            # Close the position
            contract_id = breach.get('contract_id')
            if self.actions and contract_id:
                success = self.actions.close_position(contract_id)

                if success and self.enforcement_logger:
                    self.enforcement_logger.info(
                        f"RULE-011: Closed position in blocked symbol {symbol} - "
                        f"Contract: {contract_id}"
                    )

            # Set permanent symbol lockout
            if self.lockout_manager:
                reason = action.get('reason', f'Symbol {symbol} is blocked')
                self.lockout_manager.set_symbol_lockout(
                    account_id=account_id,
                    symbol=symbol,
                    reason=reason,
                    until=None  # Permanent
                )

                if self.enforcement_logger:
                    self.enforcement_logger.info(
                        f"RULE-011: Permanent lockout for symbol {symbol} - "
                        f"Account {account_id} cannot trade this instrument"
                    )

        elif action_type == 'CANCEL_ORDER':
            # Cancel the order
            order_id = action.get('order_id')
            if self.actions and order_id:
                self.actions.cancel_order(order_id)

                if self.enforcement_logger:
                    self.enforcement_logger.info(
                        f"RULE-011: Canceled order {order_id} in blocked symbol {symbol}"
                    )
