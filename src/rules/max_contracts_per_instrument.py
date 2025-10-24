"""
RULE-002: MaxContractsPerInstrument

Purpose: Enforce per-symbol contract limits to prevent concentration risk.

Trigger Events: GatewayUserPosition
Enforcement: REDUCE_POSITION or CLOSE_ALL (no lockout)
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MaxContractsPerInstrumentRule:
    """
    RULE-002: MaxContractsPerInstrument

    Enforces per-symbol position size limits to prevent concentration risk.
    Each instrument (MNQ, ES, NQ, etc.) can have its own contract limit.

    Configuration:
        enabled: Enable/disable the rule
        limits: Dict mapping symbols to max contracts (e.g., {'MNQ': 2, 'ES': 1})
        enforcement: 'reduce_to_limit' or 'close_all'
        unknown_symbol_action: 'block', 'allow_with_limit:N', or 'allow_unlimited'

    Enforcement:
        - reduce_to_limit: Close only excess contracts
        - close_all: Close entire position in that symbol
    """

    def __init__(self, config: Dict[str, Any], state_mgr, enforcement_actions,
                 enforcement_logger=None):
        """
        Initialize the MaxContractsPerInstrument rule.

        Args:
            config: Rule configuration dict with keys:
                - enabled: bool
                - limits: Dict[str, int] mapping symbols to max contracts
                - enforcement: str ('reduce_to_limit' or 'close_all')
                - unknown_symbol_action: str ('block', 'allow_with_limit:N', 'allow_unlimited')
            state_mgr: State manager for position tracking
            enforcement_actions: Enforcement actions object with reduce_position() and close_position()
            enforcement_logger: Optional logger for enforcement tracking
        """
        self.enabled = config.get('enabled', True)
        self.limits = config.get('limits', {})
        self.enforcement_mode = config.get('enforcement', 'reduce_to_limit')
        self.unknown_symbol_action = config.get('unknown_symbol_action', 'block')
        self.state_mgr = state_mgr
        self.actions = enforcement_actions
        self.enforcement_logger = enforcement_logger

    def check(self, position_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if rule is breached for a position event.

        Args:
            position_event: Position event dict with keys:
                - accountId: int
                - contractId: str (e.g., 'CON.F.US.MNQ.U25')
                - type: int
                - size: int

        Returns:
            Breach dict if rule is breached, None otherwise
            Breach dict contains:
                - rule_id: str
                - action: str ('REDUCE_POSITION' or 'CLOSE_ALL')
                - symbol: str
                - current_size: int
                - limit: int
                - contract_id: str
                - reason: str (for unknown symbols)
        """
        # Return early if rule disabled
        if not self.enabled:
            return None

        # Extract data from event
        account_id = position_event.get('accountId')
        contract_id = position_event.get('contractId')

        if not account_id or not contract_id:
            return None

        # Extract symbol from contract ID (CON.F.US.MNQ.U25 → MNQ)
        symbol = self._extract_symbol(contract_id)

        # Get current contract count for this instrument
        current_size = self.state_mgr.get_contract_count(account_id, contract_id)

        # Check if symbol has configured limit
        if symbol in self.limits:
            limit = self.limits[symbol]
            if current_size > limit:
                # Breach detected
                action = 'CLOSE_ALL' if self.enforcement_mode == 'close_all' else 'REDUCE_POSITION'
                return {
                    'rule_id': 'RULE-002',
                    'action': action,
                    'symbol': symbol,
                    'current_size': current_size,
                    'limit': limit,
                    'contract_id': contract_id
                }
        else:
            # Unknown symbol - handle based on configuration
            if self.unknown_symbol_action == 'block':
                if current_size > 0:
                    # Block any position in unlisted symbol
                    return {
                        'rule_id': 'RULE-002',
                        'action': 'CLOSE_POSITION',
                        'symbol': symbol,
                        'current_size': current_size,
                        'limit': 0,
                        'contract_id': contract_id,
                        'reason': 'Unknown symbol not in configured limits'
                    }
            elif self.unknown_symbol_action.startswith('allow_with_limit:'):
                # Extract limit from config (e.g., 'allow_with_limit:3' → 3)
                try:
                    limit = int(self.unknown_symbol_action.split(':')[1])
                    if current_size > limit:
                        action = 'CLOSE_ALL' if self.enforcement_mode == 'close_all' else 'REDUCE_POSITION'
                        return {
                            'rule_id': 'RULE-002',
                            'action': action,
                            'symbol': symbol,
                            'current_size': current_size,
                            'limit': limit,
                            'contract_id': contract_id
                        }
                except (IndexError, ValueError):
                    logger.warning(f"Invalid unknown_symbol_action format: {self.unknown_symbol_action}")
            # else: 'allow_unlimited' - no breach

        return None

    def enforce(self, account_id: int, breach: Dict[str, Any]) -> None:
        """
        Execute enforcement action for a breach.

        Args:
            account_id: Account ID that breached
            breach: Breach dict from check() containing action, contract_id, etc.
        """
        action = breach['action']
        contract_id = breach['contract_id']
        symbol = breach['symbol']
        current_size = breach['current_size']
        limit = breach['limit']

        if action == 'REDUCE_POSITION':
            # Reduce to limit
            excess = current_size - limit
            self.actions.reduce_position(account_id, contract_id, reduce_by=excess)

            # Log enforcement
            if self.enforcement_logger:
                log_message = f"MaxContractsPerInstrument - {symbol}: Reduced from {current_size} to {limit}"
                self.enforcement_logger.log_enforcement(log_message)

        elif action in ('CLOSE_ALL', 'CLOSE_POSITION'):
            # Close entire position
            self.actions.close_position(account_id, contract_id)

            # Log enforcement
            if self.enforcement_logger:
                if 'reason' in breach:
                    log_message = f"MaxContractsPerInstrument - {symbol}: {breach['reason']}"
                else:
                    log_message = f"MaxContractsPerInstrument - {symbol}: Closed entire position (size={current_size}, limit={limit})"
                self.enforcement_logger.log_enforcement(log_message)

    def _extract_symbol(self, contract_id: str) -> str:
        """
        Extract symbol from contract ID.

        Args:
            contract_id: Contract ID (e.g., 'CON.F.US.MNQ.U25')

        Returns:
            Symbol (e.g., 'MNQ')
        """
        if '.' in contract_id:
            parts = contract_id.split('.')
            if len(parts) >= 4:
                return parts[3]
        return contract_id
