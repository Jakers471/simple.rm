"""
RULE-007: CooldownAfterLoss

Purpose: Force break after losing trades to prevent revenge trading and emotional decision-making

Trigger: GatewayUserTrade (only trades with negative P&L)

Enforcement: Configurable timer lockout (no position close)

Configuration:
    - enabled: Enable/disable the rule
    - loss_thresholds: List of loss amounts and corresponding cooldown durations
        - loss_amount: Loss amount threshold (e.g., -100)
        - cooldown_duration: Duration in seconds (e.g., 300 for 5 min)
"""

from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class CooldownAfterLossRule:
    """
    RULE-007: CooldownAfterLoss

    Forces a cooldown period after losing trades to prevent revenge trading.
    Larger losses result in longer cooldowns.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        lockout_manager,
        trade_counter=None,
        log_handler: Optional[Any] = None
    ):
        """
        Initialize CooldownAfterLoss rule.

        Args:
            config: Rule configuration dictionary
            lockout_manager: LockoutManager instance for cooldown management
            trade_counter: Optional trade counter (not used but kept for compatibility)
            log_handler: Optional logger for enforcement tracking
        """
        self.config = config
        self.lockout_manager = lockout_manager
        self.trade_counter = trade_counter
        self.logger = log_handler if log_handler else logger

        # Parse configuration
        self.enabled = config.get('enabled', True)
        self.loss_thresholds = config.get('loss_thresholds', [
            {'loss_amount': -100, 'cooldown_duration': 300},
            {'loss_amount': -200, 'cooldown_duration': 900},
            {'loss_amount': -300, 'cooldown_duration': 1800}
        ])

        # Sort thresholds by loss amount (most severe first)
        self.loss_thresholds = sorted(
            self.loss_thresholds,
            key=lambda x: x['loss_amount'],
            reverse=False  # Most negative first
        )

    def check(self, trade_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if cooldown should be triggered based on trade P&L.

        Args:
            trade_event: Trade event from TopstepX

        Returns:
            Breach info dict if cooldown triggered, None otherwise
        """
        # Return early if rule is disabled
        if not self.enabled:
            return None

        # Extract trade P&L
        profit_and_loss = trade_event.get('profitAndLoss')

        # Ignore half-turns (no P&L) and profitable trades
        if profit_and_loss is None or profit_and_loss >= 0:
            return None

        # Check which threshold is hit
        for threshold in self.loss_thresholds:
            loss_amount = threshold['loss_amount']
            cooldown_duration = threshold['cooldown_duration']

            # Check if trade loss meets or exceeds this threshold
            if profit_and_loss <= loss_amount:
                return {
                    'breach': True,
                    'loss_amount': loss_amount,
                    'cooldown_duration': cooldown_duration,
                    'action': {
                        'type': 'SET_COOLDOWN',
                        'duration': cooldown_duration,
                        'reason': f'Loss of ${profit_and_loss:.2f} - take a break for {cooldown_duration}s'
                    }
                }

        # No threshold hit
        return None

    def enforce(self, account_id: int, breach: Dict[str, Any]) -> None:
        """
        Execute enforcement action (set cooldown).

        Args:
            account_id: Account ID to enforce on
            breach: Breach information from check()
        """
        try:
            action = breach.get('action')
            duration = action.get('duration')
            reason = action.get('reason')

            # Set cooldown via lockout manager
            self.lockout_manager.set_cooldown(
                account_id=account_id,
                reason=reason,
                duration_seconds=duration
            )

            # Log enforcement
            if self.logger and hasattr(self.logger, 'log_enforcement'):
                log_message = (
                    f"RULE-007: Cooldown after loss - "
                    f"{reason}"
                )
                self.logger.log_enforcement(log_message)

        except Exception as e:
            logger.error(f"Error enforcing CooldownAfterLoss rule: {e}")
