"""
RULE-005: MaxUnrealizedProfit

Purpose: Enforce profit target - close positions when unrealized profit hits target to lock in gains

Trigger: GatewayUserPosition, GatewayQuote

Enforcement: Close position or close all + lockout

Configuration:
    - enabled: Enable/disable the rule
    - mode: 'profit_target' or 'breakeven'
    - profit_target: Profit target amount (e.g., 1000.00)
    - scope: 'per_position' or 'total'
    - action: 'CLOSE_POSITION' or 'CLOSE_ALL_AND_LOCKOUT'
    - lockout: Whether to lock out on breach
    - reset_time: Reset time for lockout
"""

from typing import Optional, Dict, Any
from datetime import datetime, time, timedelta
import logging

logger = logging.getLogger(__name__)


class MaxUnrealizedProfitRule:
    """
    RULE-005: MaxUnrealizedProfit

    Enforces profit targets to lock in gains and prevent giving back profits.
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
        Initialize MaxUnrealizedProfit rule.

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
        self.mode = config.get('mode', 'profit_target')  # 'profit_target' or 'breakeven'
        self.profit_target = config.get('profit_target', 1000.00)
        self.scope = config.get('scope', 'total')  # 'per_position' or 'total'
        self.action = config.get('action', 'CLOSE_ALL_AND_LOCKOUT')
        self.lockout = config.get('lockout', True)
        self.reset_time = config.get('reset_time', '17:00')

    def check_with_current_prices(self, account_id: int) -> Optional[Dict[str, Any]]:
        """
        Check if profit target is hit using current quotes.

        Args:
            account_id: Account ID to check

        Returns:
            Breach info dict if breached, None otherwise
        """
        # Return early if rule is disabled
        if not self.enabled:
            return None

        if self.mode == 'breakeven':
            # Breakeven mode - close when position returns to breakeven
            if self.scope == 'per_position':
                per_position_pnl = self.pnl_tracker.calculate_per_position_pnl(account_id)

                for contract_id, pnl in per_position_pnl.items():
                    if pnl == 0.00:  # At breakeven
                        return {
                            'rule_id': 'RULE-005',
                            'action': 'CLOSE_POSITION',
                            'mode': 'breakeven',
                            'unrealized_pnl': 0.00,
                            'contract_id': contract_id,
                            'reason': f'Position {contract_id} at breakeven'
                        }

        elif self.mode == 'profit_target':
            # Profit target mode - close when target is hit
            if self.scope == 'total':
                unrealized_pnl = self.pnl_tracker.calculate_unrealized_pnl(account_id)

                # Check if profit target hit
                if unrealized_pnl >= self.profit_target:
                    return {
                        'rule_id': 'RULE-005',
                        'action': self.action,
                        'mode': 'profit_target',
                        'unrealized_pnl': unrealized_pnl,
                        'target': self.profit_target,
                        'scope': 'total',
                        'reason': f'Profit target hit: ${unrealized_pnl:.2f} >= ${self.profit_target:.2f}'
                    }

            elif self.scope == 'per_position':
                per_position_pnl = self.pnl_tracker.calculate_per_position_pnl(account_id)

                for contract_id, pnl in per_position_pnl.items():
                    if pnl >= self.profit_target:
                        return {
                            'rule_id': 'RULE-005',
                            'action': 'CLOSE_POSITION',
                            'mode': 'profit_target',
                            'unrealized_pnl': pnl,
                            'target': self.profit_target,
                            'scope': 'per_position',
                            'contract_id': contract_id,
                            'reason': f'Position {contract_id} profit target: ${pnl:.2f} >= ${self.profit_target:.2f}'
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
            mode = breach.get('mode')

            if action == 'CLOSE_POSITION':
                # Close specific position
                contract_id = breach.get('contract_id')
                success = self.actions.close_position(account_id, contract_id)

                # Log enforcement
                if self.logger and hasattr(self.logger, 'log_enforcement'):
                    log_message = (
                        f"RULE-005: Profit target hit ({mode}) - "
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
                if self.lockout_manager:
                    now = datetime.now()
                    reset_hour, reset_minute = map(int, self.reset_time.split(':'))

                    # Use replace() to set time to reset time (works with mocked datetime)
                    lockout_until = now.replace(hour=reset_hour, minute=reset_minute, second=0, microsecond=0)

                    # If current time is past reset time, lockout until next day
                    if now.time() >= time(reset_hour, reset_minute):
                        lockout_until = lockout_until + timedelta(days=1)

                    self.lockout_manager.set_lockout(
                        account_id=account_id,
                        reason=f"Profit target hit: ${unrealized_pnl:.2f}",
                        until=lockout_until
                    )

                # Log enforcement
                if self.logger and hasattr(self.logger, 'log_enforcement'):
                    log_message = (
                        f"RULE-005: Profit target hit - "
                        f"P&L: ${unrealized_pnl:.2f} - "
                        f"Closed all positions and set lockout"
                    )
                    self.logger.log_enforcement(log_message)

                return close_success and cancel_success

            else:
                logger.error(f"Unknown enforcement action: {action}")
                return False

        except Exception as e:
            logger.error(f"Error enforcing MaxUnrealizedProfit rule: {e}")
            return False
