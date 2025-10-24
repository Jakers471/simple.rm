"""
RULE-009: SessionBlockOutsideHours

Purpose: Block trading outside configured session hours and on holidays

Trigger: GatewayUserPosition (position opens outside session), background timer (session end), holiday check

Enforcement: Hard lockout (session-based)

Configuration:
    - enabled: Enable/disable the rule
    - session_hours: Global session configuration
        - start: Start time (e.g., "09:30")
        - end: End time (e.g., "16:00")
        - timezone: Timezone (e.g., "America/New_York")
    - per_instrument_sessions: Per-instrument session overrides
    - check_holidays: Whether to check for holidays
    - holidays: List of holiday dates
    - action: Action type (e.g., 'CLOSE_ALL_AND_LOCKOUT')
    - auto_close_at_end: Auto-close positions at session end
"""

from typing import Optional, Dict, Any
import datetime
import logging
import pytz

logger = logging.getLogger(__name__)


class SessionBlockOutsideHoursRule:
    """
    RULE-009: SessionBlockOutsideHours

    Prevents trading outside configured session hours and on market holidays.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        lockout_manager,
        log_handler: Optional[Any] = None
    ):
        """
        Initialize SessionBlockOutsideHours rule.

        Args:
            config: Rule configuration dictionary
            lockout_manager: LockoutManager instance for lockout management
            log_handler: Optional logger for enforcement tracking
        """
        self.config = config
        self.lockout_manager = lockout_manager
        self.logger = log_handler if log_handler else logger

        # Parse configuration
        self.enabled = config.get('enabled', True)
        self.session_hours = config.get('session_hours', {})
        self.default_session = config.get('default_session', self.session_hours)
        self.per_instrument_sessions = config.get('per_instrument_sessions', {})
        self.check_holidays = config.get('check_holidays', False)
        self.holidays = config.get('holidays', [])
        self.action = config.get('action', 'CLOSE_ALL_AND_LOCKOUT')
        self.auto_close_at_end = config.get('auto_close_at_end', False)

        # Parse session times
        self.start_time = self.session_hours.get('start', '09:30')
        self.end_time = self.session_hours.get('end', '16:00')
        self.timezone = self.session_hours.get('timezone', 'America/New_York')

    def check(self, position_event: Dict[str, Any], symbol: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Check if trading is allowed at current time.

        Args:
            position_event: Position event data
            symbol: Optional symbol for per-instrument session check

        Returns:
            Breach info dict if outside session, None otherwise
        """
        # Return early if rule is disabled
        if not self.enabled:
            return None

        # Get session configuration (check per-instrument override if symbol provided)
        session_timezone = self.timezone
        if symbol and symbol in self.per_instrument_sessions:
            session = self.per_instrument_sessions[symbol]
            start_time_str = session.get('start', self.start_time)
            end_time_str = session.get('end', self.end_time)
            session_timezone = session.get('timezone', self.timezone)
        else:
            start_time_str = self.start_time
            end_time_str = self.end_time

        # Get current time in the session's timezone
        tz = pytz.timezone(session_timezone)
        now = datetime.datetime.now(tz)

        # Check for holidays
        if self.check_holidays:
            today_str = now.strftime('%Y-%m-%d')
            if today_str in self.holidays:
                return {
                    'breach': True,
                    'reason': 'Trading on market holiday',
                    'date': today_str,
                    'action': {
                        'type': self.action
                    }
                }

        # Parse times
        start_hour, start_minute = map(int, start_time_str.split(':'))
        end_hour, end_minute = map(int, end_time_str.split(':'))

        start_time = datetime.time(start_hour, start_minute)
        end_time = datetime.time(end_hour, end_minute)

        current_time = now.time()

        # Handle sessions that wrap around midnight (e.g., 18:00-17:00)
        if start_time > end_time:
            # Session wraps around midnight
            # Valid if: current_time >= start_time OR current_time < end_time
            is_within_session = current_time >= start_time or current_time < end_time
        else:
            # Normal session (e.g., 09:30-16:00)
            # Valid if: start_time <= current_time < end_time
            is_within_session = start_time <= current_time < end_time

        # Check if outside session hours
        if not is_within_session:
            # Determine if we're before start or after end
            if start_time > end_time:
                # Wrapped session: we're in the gap between end and start
                return {
                    'breach': True,
                    'reason': 'Trading outside session hours',
                    'current_time': current_time.strftime('%H:%M:%S'),
                    'session_start': start_time.strftime('%H:%M:%S'),
                    'session_end': end_time.strftime('%H:%M:%S'),
                    'action': {
                        'type': self.action
                    }
                }
            elif current_time < start_time:
                return {
                    'breach': True,
                    'reason': 'Trading outside session hours',
                    'current_time': current_time.strftime('%H:%M:%S'),
                    'session_start': start_time.strftime('%H:%M:%S'),
                    'action': {
                        'type': self.action
                    }
                }
            else:
                # current_time >= end_time
                # Check if this is auto-close at end or breach
                if current_time == end_time and self.auto_close_at_end:
                    return {
                        'breach': True,
                        'reason': 'Session end - auto-close',
                        'current_time': current_time.strftime('%H:%M:%S'),
                        'session_end': end_time.strftime('%H:%M:%S'),
                        'action': {
                            'type': 'CLOSE_ALL_POSITIONS'
                        }
                    }
                else:
                    return {
                        'breach': True,
                        'reason': 'Trading outside session hours',
                        'current_time': current_time.strftime('%H:%M:%S'),
                        'session_end': end_time.strftime('%H:%M:%S'),
                        'action': {
                            'type': self.action
                        }
                    }

        # Within session hours
        return None

    def enforce(self, account_id: int, breach: Dict[str, Any], actions) -> bool:
        """
        Execute enforcement action.

        Args:
            account_id: Account ID to enforce on
            breach: Breach information from check()
            actions: Enforcement actions instance

        Returns:
            True if enforcement succeeded, False otherwise
        """
        try:
            action_type = breach.get('action', {}).get('type', self.action)
            reason = breach.get('reason')

            if action_type == 'CLOSE_ALL_POSITIONS':
                # Close all positions (no lockout)
                success = actions.close_all_positions(account_id)

                # Log enforcement
                if self.logger and hasattr(self.logger, 'log_enforcement'):
                    log_message = f"RULE-009: {reason} - Closed all positions"
                    self.logger.log_enforcement(log_message)

                return success

            elif action_type == 'CLOSE_ALL_AND_LOCKOUT':
                # Close all positions
                close_success = actions.close_all_positions(account_id)

                # Cancel all orders
                cancel_success = actions.cancel_all_orders(account_id)

                # Set lockout until next session start
                # Calculate next session start time
                tz = pytz.timezone(self.timezone)
                now = datetime.datetime.now(tz)
                start_hour, start_minute = map(int, self.start_time.split(':'))

                # Next day at session start
                next_session = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                if next_session <= now:
                    next_session += datetime.timedelta(days=1)

                self.lockout_manager.set_lockout(
                    account_id=account_id,
                    reason=reason,
                    until=next_session
                )

                # Log enforcement
                if self.logger and hasattr(self.logger, 'log_enforcement'):
                    log_message = (
                        f"RULE-009: {reason} - "
                        f"Closed all positions and set lockout until {next_session}"
                    )
                    self.logger.log_enforcement(log_message)

                return close_success and cancel_success

            else:
                logger.error(f"Unknown enforcement action: {action_type}")
                return False

        except Exception as e:
            logger.error(f"Error enforcing SessionBlockOutsideHours rule: {e}")
            return False
