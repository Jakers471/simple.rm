"""
RULE-004: DailyUnrealizedLoss

Purpose: Enforce hard daily floating loss limit - stops trading when unrealized P&L drops below threshold

Trigger: GatewayUserPosition, GatewayQuote (continuous monitoring)

Enforcement: Close position (per_position) or close all + lockout (total)

Configuration:
    - enabled: Enable/disable the rule
    - loss_limit: Unrealized loss limit (e.g., 300.00)
    - scope: 'per_position' or 'total'
    - action: 'CLOSE_POSITION' or 'CLOSE_ALL_AND_LOCKOUT'
    - lockout: Whether to lock out on breach
    - reset_time: Reset time for lockout
"""

from typing import Optional, Dict, Any
import datetime
import logging

logger = logging.getLogger(__name__)


class DailyUnrealizedLossRule:
    """
    RULE-004: DailyUnrealizedLoss

    Enforces unrealized floating loss limits with position closure or lockout.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        pnl_tracker,
        actions,
        lockout_manager,
        log_handler: Optional[Any] = None
    ):
        """
        Initialize DailyUnrealizedLoss rule.

        Args:
            config: Rule configuration dictionary
            pnl_tracker: PNL tracker instance for unrealized P&L calculation
            actions: EnforcementActions instance for closing positions
            lockout_manager: LockoutManager instance for lockout management
            log_handler: Optional logger for enforcement tracking
        """
        self.config = config
        self.pnl_tracker = pnl_tracker
        self.actions = actions
        self.lockout_manager = lockout_manager
        self.logger = log_handler if log_handler else logger

        # Parse configuration
        self.enabled = config.get('enabled', True)
        self.loss_limit = config.get('loss_limit', 300.00)
        self.scope = config.get('scope', 'total')  # 'per_position' or 'total'
        self.action = config.get('action', 'CLOSE_ALL_AND_LOCKOUT')
        self.lockout = config.get('lockout', True)
        self.reset_time = config.get('reset_time', '17:00')

    def check_with_current_prices(self, account_id: int) -> Optional[Dict[str, Any]]:
        """
        Check if unrealized loss limit is breached using current quotes.

        Args:
            account_id: Account ID to check

        Returns:
            Breach info dict if breached, None otherwise
        """
        # Return early if rule is disabled
        if not self.enabled:
            return None

        if self.scope == 'total':
            # Calculate total unrealized P&L across all positions
            unrealized_pnl = self.pnl_tracker.calculate_unrealized_pnl(account_id)

            # Check if breach occurred (loss exceeds limit)
            # Convert limit to negative for comparison
            if unrealized_pnl <= -self.loss_limit:
                return {
                    'rule_id': 'RULE-004',
                    'action': self.action,
                    'unrealized_pnl': unrealized_pnl,
                    'limit': -self.loss_limit,
                    'scope': 'total',
                    'reason': f'Total unrealized loss: ${unrealized_pnl:.2f} exceeds limit ${-self.loss_limit:.2f}'
                }

        elif self.scope == 'per_position':
            # Calculate unrealized P&L for each position
            per_position_pnl = self.pnl_tracker.calculate_per_position_pnl(account_id)

            # Check each position for breach
            for contract_id, pnl in per_position_pnl.items():
                if pnl <= -self.loss_limit:
                    return {
                        'rule_id': 'RULE-004',
                        'action': 'CLOSE_POSITION',
                        'unrealized_pnl': pnl,
                        'limit': -self.loss_limit,
                        'scope': 'per_position',
                        'contract_id': contract_id,
                        'reason': f'Position {contract_id} unrealized loss: ${pnl:.2f} exceeds limit ${-self.loss_limit:.2f}'
                    }

        # No breach
        return None

    def enforce(self, account_id: int, breach: Dict[str, Any]) -> bool:
        """
        Execute enforcement action for a breach.

        Args:
            account_id: Account ID to enforce on
            breach: Breach information from check_with_current_prices()

        Returns:
            True if enforcement succeeded, False otherwise
        """
        try:
            action = breach.get('action')
            scope = breach.get('scope')
            unrealized_pnl = breach.get('unrealized_pnl')

            if action == 'CLOSE_POSITION' and scope == 'per_position':
                # Close specific position
                contract_id = breach.get('contract_id')
                success = self.actions.close_position(account_id, contract_id)

                # Log enforcement
                if self.logger and hasattr(self.logger, 'log_enforcement'):
                    log_message = (
                        f"RULE-004: Unrealized loss breach (per_position) - "
                        f"Closed position {contract_id} with P&L: ${unrealized_pnl:.2f}"
                    )
                    self.logger.log_enforcement(log_message)

                return success

            elif action == 'CLOSE_ALL_AND_LOCKOUT':
                # Close all positions
                close_success = self.actions.close_all_positions(account_id)

                # Cancel all orders
                cancel_success = self.actions.cancel_all_orders(account_id)

                # Set lockout if configured
                if self.lockout:
                    now = datetime.datetime.now()
                    reset_hour, reset_minute = map(int, self.reset_time.split(':'))

                    # Use replace() to set time to reset time (works with mocked datetime)
                    lockout_until = now.replace(hour=reset_hour, minute=reset_minute, second=0, microsecond=0)

                    # If current time is past reset time, lockout until next day
                    if now.time() >= datetime.time(reset_hour, reset_minute):
                        lockout_until = lockout_until + datetime.timedelta(days=1)

                    self.lockout_manager.set_lockout(
                        account_id=account_id,
                        reason=f"Unrealized loss limit: ${unrealized_pnl:.2f}",
                        until=lockout_until
                    )

                # Log enforcement
                if self.logger and hasattr(self.logger, 'log_enforcement'):
                    log_message = (
                        f"RULE-004: Unrealized loss breach (total) - "
                        f"P&L: ${unrealized_pnl:.2f} - "
                        f"Closed all positions and set lockout"
                    )
                    self.logger.log_enforcement(log_message)

                return close_success and cancel_success

            else:
                logger.error(f"Unknown enforcement action: {action}")
                return False

        except Exception as e:
            logger.error(f"Error enforcing DailyUnrealizedLoss rule: {e}")
            return False
