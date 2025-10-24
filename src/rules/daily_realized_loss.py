"""
RULE-003: DailyRealizedLoss

Purpose: Enforce hard daily realized P&L limit - stops trading when daily loss threshold is hit

Trigger: GatewayUserTrade events (only trades with P&L, not half-turns)

Enforcement: Hard lockout until reset time (17:00)

Configuration:
    - enabled: Enable/disable the rule
    - limit: Daily realized loss limit (e.g., -500)
    - reset_time: Time to unlock (e.g., "17:00")
    - timezone: Timezone for reset time
    - enforcement: Action type (e.g., "close_all_and_lockout")
    - lockout_until_reset: Lock out until reset time
"""

from typing import Optional, Dict, Any
import datetime
import logging

logger = logging.getLogger(__name__)


class DailyRealizedLossRule:
    """
    RULE-003: DailyRealizedLoss

    Enforces daily realized P&L limits with hard lockout until reset time.
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
        Initialize DailyRealizedLoss rule.

        Args:
            config: Rule configuration dictionary
            pnl_tracker: PNL tracker instance for daily P&L calculation
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
        self.limit = config.get('limit', -500)  # Negative value
        self.reset_time = config.get('reset_time', '17:00')
        self.timezone = config.get('timezone', 'America/New_York')
        self.enforcement = config.get('enforcement', 'close_all_and_lockout')
        self.lockout_until_reset = config.get('lockout_until_reset', True)

    def check(self, trade_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if the DailyRealizedLoss rule is breached.

        Args:
            trade_event: Trade event from TopstepX

        Returns:
            Breach info dict if breached, None otherwise
        """
        # Return early if rule is disabled
        if not self.enabled:
            return None

        # Extract account ID from event
        account_id = trade_event.get('accountId')
        if account_id is None:
            logger.warning("Trade event missing accountId")
            return None

        # Check if trade has P&L (ignore half-turns)
        profit_and_loss = trade_event.get('profitAndLoss')
        if profit_and_loss is None:
            return None  # Half-turn, no P&L

        # Add trade P&L to tracker and get daily total
        daily_pnl = self.pnl_tracker.add_trade_pnl(account_id, profit_and_loss)

        # Check if breach occurred (strictly less than limit)
        if daily_pnl < self.limit:
            return {
                'rule_id': 'RULE-003',
                'action': 'CLOSE_ALL_AND_LOCKOUT',
                'daily_pnl': daily_pnl,
                'limit': self.limit,
                'reason': f'Daily loss limit hit: ${daily_pnl:.2f} < ${self.limit:.2f}'
            }

        # No breach - within or at limit
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
            daily_pnl = breach.get('daily_pnl')
            limit = breach.get('limit')

            # Close all positions
            close_success = self.actions.close_all_positions(account_id)

            # Cancel all orders
            cancel_success = self.actions.cancel_all_orders(account_id)

            # Calculate lockout until time
            if self.lockout_until_reset:
                now = datetime.datetime.now()
                reset_hour, reset_minute = map(int, self.reset_time.split(':'))

                # Use replace() to set time to reset time (works with mocked datetime)
                lockout_until = now.replace(hour=reset_hour, minute=reset_minute, second=0, microsecond=0)

                # If current time is past reset time, lockout until next day
                if now.time() >= datetime.time(reset_hour, reset_minute):
                    lockout_until = lockout_until + datetime.timedelta(days=1)

                # Set lockout
                self.lockout_manager.set_lockout(
                    account_id=account_id,
                    reason=f"Daily loss limit hit: ${daily_pnl:.2f}",
                    until=lockout_until
                )

            # Log enforcement
            if self.logger and hasattr(self.logger, 'log_enforcement'):
                log_message = (
                    f"RULE-003: Daily realized loss breach - "
                    f"P&L: ${daily_pnl:.2f}, Limit: ${limit:.2f} - "
                    f"Closed all positions and set lockout until {self.reset_time}"
                )
                self.logger.log_enforcement(log_message)

            return close_success and cancel_success

        except Exception as e:
            logger.error(f"Error enforcing DailyRealizedLoss rule: {e}")
            return False
