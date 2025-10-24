"""
RULE-010: AuthLossGuard

Purpose: Monitor TopstepX canTrade status and enforce lockout when API signals account restriction

Trigger: GatewayUserAccount (account status updates)

Enforcement: Hard lockout (API-driven, indefinite)

Configuration:
    - enabled: Enable/disable the rule
    - enforcement: Action type (e.g., 'close_all_and_lockout')
    - auto_unlock_on_restore: Auto-unlock when canTrade returns to true
    - check_on_startup: Check canTrade status on daemon startup
"""

from typing import Optional, Dict, Any
import datetime
import logging

logger = logging.getLogger(__name__)


class AuthLossGuardRule:
    """
    RULE-010: AuthLossGuard

    Monitors TopstepX canTrade status and enforces lockout when account is restricted.
    Auto-unlocks when canTrade is restored (if configured).
    """

    def __init__(
        self,
        config: Dict[str, Any],
        state_manager,
        lockout_manager,
        actions=None,
        log_handler: Optional[Any] = None
    ):
        """
        Initialize AuthLossGuard rule.

        Args:
            config: Rule configuration dictionary
            state_manager: StateManager instance for canTrade tracking
            lockout_manager: LockoutManager instance for lockout management
            actions: Optional enforcement actions instance
            log_handler: Optional logger for enforcement tracking
        """
        self.config = config
        self.state_manager = state_manager
        self.lockout_manager = lockout_manager
        self.actions = actions
        self.logger = log_handler if log_handler else logger

        # Parse configuration
        self.enabled = config.get('enabled', True)
        self.enforcement = config.get('enforcement', 'close_all_and_lockout')
        self.auto_unlock_on_restore = config.get('auto_unlock_on_restore', True)
        self.check_on_startup = config.get('check_on_startup', True)

    def check(self, account_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if canTrade status changed.

        Args:
            account_event: Account event from TopstepX

        Returns:
            Breach info dict if status changed, None otherwise
        """
        # Return early if rule is disabled
        if not self.enabled:
            return None

        account_id = account_event.get('id')
        current_can_trade = account_event.get('canTrade', True)

        # Get previous state
        if not hasattr(self.state_manager, 'can_trade_status'):
            self.state_manager.can_trade_status = {}

        previous_can_trade = self.state_manager.can_trade_status.get(account_id)

        # Update state
        self.state_manager.can_trade_status[account_id] = current_can_trade

        # Check for state change
        if previous_can_trade is not None and previous_can_trade != current_can_trade:
            if not current_can_trade:
                # canTrade disabled - breach!
                return {
                    'breach': True,
                    'event_type': 'canTrade_disabled',
                    'previous_state': previous_can_trade,
                    'current_state': current_can_trade,
                    'action': {
                        'type': 'CLOSE_ALL_AND_LOCKOUT',
                        'reason': 'Account restricted by TopstepX (canTrade=false)',
                        'lockout_until': None  # Indefinite
                    }
                }
            else:
                # canTrade restored
                if self.auto_unlock_on_restore:
                    return {
                        'breach': False,
                        'event_type': 'canTrade_enabled',
                        'previous_state': previous_can_trade,
                        'current_state': current_can_trade,
                        'action': {
                            'type': 'REMOVE_LOCKOUT',
                            'reason': 'TopstepX restored trading (canTrade=true)'
                        }
                    }

        # No state change or first time seeing this account
        return None

    def check_initial_state(self, account_id: int, account_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check canTrade status on daemon startup.

        Args:
            account_id: Account ID
            account_info: Account information from API

        Returns:
            Breach info dict if canTrade=false, None otherwise
        """
        if not self.enabled or not self.check_on_startup:
            return None

        can_trade = account_info.get('canTrade', True)

        # Initialize state
        if not hasattr(self.state_manager, 'can_trade_status'):
            self.state_manager.can_trade_status = {}

        self.state_manager.can_trade_status[account_id] = can_trade

        # If canTrade is false on startup, trigger breach
        if not can_trade:
            return {
                'breach': True,
                'event_type': 'canTrade_disabled_on_startup',
                'current_state': can_trade,
                'action': {
                    'type': 'CLOSE_ALL_AND_LOCKOUT',
                    'reason': 'Account has canTrade=false on startup',
                    'lockout_until': None  # Indefinite
                }
            }

        return None

    def enforce(self, account_id: int, breach: Dict[str, Any]) -> bool:
        """
        Execute enforcement action.

        Args:
            account_id: Account ID to enforce on
            breach: Breach information from check()

        Returns:
            True if enforcement succeeded, False otherwise
        """
        try:
            action_type = breach.get('action', {}).get('type')
            reason = breach.get('action', {}).get('reason')

            if action_type == 'CLOSE_ALL_AND_LOCKOUT':
                # Close all positions
                close_success = True
                if self.actions:
                    close_success = self.actions.close_all_positions(account_id)

                # Cancel all orders
                cancel_success = True
                if self.actions:
                    cancel_success = self.actions.cancel_all_orders(account_id)

                # Set indefinite lockout
                self.lockout_manager.set_lockout(
                    account_id=account_id,
                    reason=reason,
                    until=None  # Indefinite
                )

                # Get positions count for logging
                positions_count = 0
                if hasattr(self.state_manager, 'positions') and account_id in self.state_manager.positions:
                    positions_count = len(self.state_manager.positions[account_id])

                # Log enforcement
                if self.logger and hasattr(self.logger, 'log_enforcement'):
                    log_message = (
                        f"RULE-010: {reason} - "
                        f"Closed {positions_count} positions and set indefinite lockout"
                    )
                    self.logger.log_enforcement(log_message)

                return close_success and cancel_success

            elif action_type == 'REMOVE_LOCKOUT':
                # Remove lockout
                if hasattr(self.lockout_manager, 'remove_lockout'):
                    self.lockout_manager.remove_lockout(account_id)
                elif hasattr(self.lockout_manager, 'active_lockouts') and account_id in self.lockout_manager.active_lockouts:
                    del self.lockout_manager.active_lockouts[account_id]

                # Log enforcement
                if self.logger and hasattr(self.logger, 'log_enforcement'):
                    log_message = f"RULE-010: {reason} - Lockout removed"
                    self.logger.log_enforcement(log_message)

                return True

            else:
                logger.error(f"Unknown enforcement action: {action_type}")
                return False

        except Exception as e:
            logger.error(f"Error enforcing AuthLossGuard rule: {e}")
            return False
