"""
RULE-001: MaxContracts

Purpose: Cap net contract exposure across all instruments to prevent over-leveraging.

Configuration:
    - enabled: Enable/disable the rule
    - limit: Maximum net contracts allowed
    - count_type: 'net' or 'gross' contract counting
    - close_all: Close all positions on breach (default: True)
    - reduce_to_limit: Reduce positions to limit instead of closing all
    - lockout_on_breach: Apply lockout on breach (default: False)

Trigger: GatewayUserPosition events

Enforcement: Trade-by-trade (no lockout by default)
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MaxContractsRule:
    """
    RULE-001: MaxContracts

    Enforces maximum net contract limits across all positions in an account.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        state_manager,
        actions,
        log_handler: Optional[Any] = None
    ):
        """
        Initialize MaxContracts rule.

        Args:
            config: Rule configuration dictionary
            state_manager: StateManager instance for position tracking
            actions: EnforcementActions instance for closing positions
            log_handler: Optional logger for enforcement tracking
        """
        self.config = config
        self.state_manager = state_manager
        self.actions = actions
        self.logger = log_handler if log_handler else logger

        # Parse configuration
        self.enabled = config.get('enabled', True)
        self.limit = config.get('limit', 5)
        self.count_type = config.get('count_type', 'net')
        self.close_all = config.get('close_all', True)
        self.reduce_to_limit = config.get('reduce_to_limit', False)
        self.lockout_on_breach = config.get('lockout_on_breach', False)

    def check(self, position_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if the MaxContracts rule is breached.

        Args:
            position_event: Position event from TopstepX

        Returns:
            Breach info dict if breached, None otherwise
        """
        # Return early if rule is disabled
        if not self.enabled:
            return None

        # Extract account ID from event
        account_id = position_event.get('accountId')
        if account_id is None:
            logger.warning("Position event missing accountId")
            return None

        # Get current net contract count from state manager
        current_count = self.state_manager.get_position_count(account_id)

        # Check if breach occurred (strictly greater than limit)
        if current_count > self.limit:
            # Determine action type based on configuration
            if self.reduce_to_limit:
                action = 'REDUCE_TO_LIMIT'
            else:
                action = 'CLOSE_ALL_POSITIONS'

            return {
                'rule_id': 'RULE-001',
                'action': action,
                'reason': f'MaxContracts breach (net={current_count}, limit={self.limit})',
                'current_count': current_count,
                'limit': self.limit
            }

        # No breach - at or under limit
        return None

    def enforce(self, account_id: int, breach: Dict[str, Any]) -> bool:
        """
        Execute enforcement action for a breach.

        Args:
            account_id: Account ID to enforce on
            breach: Breach information from check()

        Returns:
            True if enforcement succeeded, False otherwise
        """
        try:
            action = breach.get('action')
            current_count = breach.get('current_count')

            if action == 'CLOSE_ALL_POSITIONS':
                # Close all positions
                success = self.actions.close_all_positions(account_id)

                if success and self.logger:
                    log_message = f"MaxContracts breach - Closed all positions (net={current_count}, limit={self.limit})"
                    self.logger.log_enforcement(log_message)

                return success

            elif action == 'REDUCE_TO_LIMIT':
                # Reduce positions to limit
                success = self.actions.reduce_positions_to_limit(
                    account_id,
                    target_net=self.limit
                )

                if success and self.logger:
                    log_message = f"MaxContracts breach - Reduced to limit (from {current_count} to {self.limit})"
                    self.logger.log_enforcement(log_message)

                return success

            else:
                logger.error(f"Unknown enforcement action: {action}")
                return False

        except Exception as e:
            logger.error(f"Error enforcing MaxContracts rule: {e}")
            return False
