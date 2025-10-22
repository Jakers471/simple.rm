"""MOD-003: Timer Manager

Countdown timers for cooldowns, session checks, and scheduled tasks.

Thread-safe timer management with callback execution on expiry.

Author: Risk Manager System
Version: 1.0
"""

import threading
from datetime import datetime, timedelta
from typing import Dict, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class TimerManager:
    """Thread-safe countdown timer manager with callback execution."""

    def __init__(self):
        """Initialize timer manager with empty timer state."""
        self.timers: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._callbacks: list[Callable] = []
        logger.info("Timer Manager initialized")

    def start_timer(self, name: str, duration_seconds: int, callback: Optional[Callable] = None) -> None:
        """
        Start countdown timer with optional callback.

        Args:
            name: Unique timer identifier
            duration_seconds: Duration in seconds
            callback: Optional function to call when timer expires

        Example:
            start_timer("lockout_123", 1800, lambda: clear_lockout(123))
        """
        with self._lock:
            expires_at = datetime.now() + timedelta(seconds=duration_seconds)
            self.timers[name] = {
                "expires_at": expires_at,
                "callback": callback,
                "duration": duration_seconds,
                "started_at": datetime.now()
            }
            logger.info(f"Timer started: {name}, duration: {duration_seconds}s, expires: {expires_at}")

    def is_timer_active(self, name: str) -> bool:
        """
        Check if timer is currently active.

        Args:
            name: Timer identifier

        Returns:
            True if timer exists and hasn't expired
        """
        with self._lock:
            if name not in self.timers:
                return False

            # Check if expired
            now = datetime.now()
            if now >= self.timers[name]["expires_at"]:
                return False

            return True

    def get_remaining_time(self, name: str) -> int:
        """
        Get seconds remaining on timer.

        Args:
            name: Timer identifier

        Returns:
            Remaining seconds (0 if timer doesn't exist or expired)
        """
        with self._lock:
            if name not in self.timers:
                return 0

            now = datetime.now()
            remaining = (self.timers[name]["expires_at"] - now).total_seconds()
            return max(0, int(remaining))

    def cancel_timer(self, name: str) -> bool:
        """
        Cancel timer before expiry.

        Args:
            name: Timer identifier

        Returns:
            True if timer was cancelled, False if timer didn't exist
        """
        with self._lock:
            if name in self.timers:
                del self.timers[name]
                logger.info(f"Timer cancelled: {name}")
                return True
            return False

    def get_all_active_timers(self) -> Dict[str, Dict]:
        """Get all active timers with their details."""
        with self._lock:
            active_timers = {}
            now = datetime.now()
            for name, timer_info in self.timers.items():
                if now < timer_info["expires_at"]:
                    remaining = (timer_info["expires_at"] - now).total_seconds()
                    active_timers[name] = {
                        "remaining_time": max(0, int(remaining)),
                        "expires_at": timer_info["expires_at"],
                        "duration": timer_info["duration"],
                        "started_at": timer_info["started_at"]
                    }
            return active_timers

    def on_timer_expired(self, callback: Callable) -> None:
        """Register a global callback for any timer expiration."""
        with self._lock:
            self._callbacks.append(callback)
            logger.debug(f"Global timer expiration callback registered")

    def check_timers(self) -> None:
        """Background task: check timers and fire callbacks. Called every second."""
        now = datetime.now()
        expired_timers = []

        # Find expired timers
        with self._lock:
            for name, timer_info in list(self.timers.items()):
                if now >= timer_info["expires_at"]:
                    expired_timers.append((name, timer_info))

        # Execute callbacks outside lock to prevent deadlocks
        for name, timer_info in expired_timers:
            logger.info(f"Timer expired: {name}")

            # Execute timer-specific callback
            if timer_info["callback"] is not None:
                try:
                    timer_info["callback"]()
                    logger.debug(f"Timer callback executed: {name}")
                except Exception as e:
                    logger.error(f"Error executing timer callback for {name}: {e}")

            # Execute global callbacks
            for callback in self._callbacks:
                try:
                    callback(name)
                except Exception as e:
                    logger.error(f"Error executing global timer callback: {e}")

        # Remove expired timers
        with self._lock:
            for name, _ in expired_timers:
                if name in self.timers:
                    del self.timers[name]

    def get_timer_info(self, name: str) -> Optional[Dict]:
        """Get detailed information about a specific timer."""
        with self._lock:
            if name not in self.timers:
                return None
            timer_info = self.timers[name]
            now = datetime.now()
            remaining = (timer_info["expires_at"] - now).total_seconds()
            return {
                "name": name,
                "remaining_time": max(0, int(remaining)),
                "expires_at": timer_info["expires_at"],
                "duration": timer_info["duration"],
                "started_at": timer_info["started_at"],
                "is_expired": now >= timer_info["expires_at"]
            }
