"""
RULE-006: TradeFrequencyLimit

Prevents overtrading by limiting trades per time window (minute/hour/session).
Uses MOD-008 (Trade Counter) for rolling window tracking.

File: src/rules/trade_frequency_limit.py
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TradeFrequencyLimitRule:
    """
    RULE-006: TradeFrequencyLimit

    Enforces trade frequency limits across multiple time windows:
    - Per minute (60-second rolling window)
    - Per hour (60-minute rolling window)
    - Per session (from reset time to next reset)

    Trigger Event: GatewayUserTrade
    Enforcement: Cooldown timer (no position close)
    """

    def __init__(self, config: Dict[str, Any], trade_counter, lockout_manager, custom_logger=None):
        """
        Initialize TradeFrequencyLimit rule.

        Args:
            config: Rule configuration dict with limits and cooldown settings
            trade_counter: MOD-008 TradeCounter instance for tracking
            lockout_manager: MOD-002 LockoutManager for cooldowns
            custom_logger: Optional custom logger (for testing)
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.trade_counter = trade_counter
        self.lockout_manager = lockout_manager
        self.logger = custom_logger if custom_logger is not None else logger

        # Parse limits
        self.limits = config.get('limits', {})
        self.per_minute_limit = self.limits.get('per_minute')
        self.per_hour_limit = self.limits.get('per_hour')
        self.per_session_limit = self.limits.get('per_session')

        # Parse cooldown durations
        self.cooldown_config = config.get('cooldown_on_breach', {})
        self.cooldown_enabled = self.cooldown_config.get('enabled', True)
        self.per_minute_cooldown = self.cooldown_config.get('per_minute_breach', 60)
        self.per_hour_cooldown = self.cooldown_config.get('per_hour_breach', 1800)
        self.per_session_cooldown = self.cooldown_config.get('per_session_breach', 3600)

    def check(self, trade_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if trade frequency limits are breached.

        Args:
            trade_event: GatewayUserTrade event data

        Returns:
            Dict with breach details if breached, None otherwise
            Breach dict format: {
                'rule_id': 'RULE-006',
                'breach_type': 'per_minute' | 'per_hour' | 'per_session',
                'trade_count': int,
                'limit': int
            }
        """
        if not self.enabled:
            return None

        # Extract trade details
        account_id = trade_event.get('accountId')
        contract_id = trade_event.get('contractId', '')

        # Parse timestamp
        timestamp_str = trade_event.get('creationTimestamp')
        if timestamp_str:
            # Handle both ISO format strings and datetime objects
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = timestamp_str
        else:
            timestamp = datetime.now()

        # Record trade and get current counts
        counts = self.trade_counter.record_trade(account_id, contract_id, timestamp)

        # Check limits in order of severity (session > hour > minute)
        # Return most severe breach first

        # Check session limit
        if self.per_session_limit and counts['session'] > self.per_session_limit:
            return {
                'rule_id': 'RULE-006',
                'breach_type': 'per_session',
                'trade_count': counts['session'],
                'limit': self.per_session_limit
            }

        # Check hour limit
        if self.per_hour_limit and counts['hour'] > self.per_hour_limit:
            return {
                'rule_id': 'RULE-006',
                'breach_type': 'per_hour',
                'trade_count': counts['hour'],
                'limit': self.per_hour_limit
            }

        # Check minute limit
        if self.per_minute_limit and counts['minute'] > self.per_minute_limit:
            return {
                'rule_id': 'RULE-006',
                'breach_type': 'per_minute',
                'trade_count': counts['minute'],
                'limit': self.per_minute_limit
            }

        # No breach
        return None

    def enforce(self, account_id: int, breach: Dict[str, Any]) -> None:
        """
        Enforce trade frequency breach with cooldown timer.

        Args:
            account_id: Account that breached the rule
            breach: Breach details from check() method
        """
        if not self.cooldown_enabled:
            return

        breach_type = breach['breach_type']
        trade_count = breach['trade_count']
        limit = breach['limit']

        # Determine cooldown duration based on breach type
        cooldown_durations = {
            'per_minute': self.per_minute_cooldown,
            'per_hour': self.per_hour_cooldown,
            'per_session': self.per_session_cooldown
        }

        cooldown_seconds = cooldown_durations.get(breach_type, 60)

        # Create descriptive reason
        reason = f"Trade frequency limit: {trade_count}/{limit} trades"

        # Set cooldown via lockout manager
        self.lockout_manager.set_cooldown(
            account_id=account_id,
            reason=reason,
            duration_seconds=cooldown_seconds
        )

        # Log enforcement
        log_message = (
            f"RULE-006: Trade frequency limit breach - "
            f"{breach_type}: {trade_count} trades - "
            f"Cooldown for {cooldown_seconds}s"
        )

        # Use log_enforcement if available (mock), otherwise use info
        if hasattr(self.logger, 'log_enforcement'):
            self.logger.log_enforcement(log_message)
        else:
            self.logger.info(log_message)
