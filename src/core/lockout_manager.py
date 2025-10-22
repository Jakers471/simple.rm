"""MOD-002: Lockout Manager

Centralized lockout state management for all risk rules.
Handles hard lockouts, cooldowns, auto-expiry, and persistence.

File: src/core/lockout_manager.py
Version: 2.0
Dependencies: MOD-003 (timer_manager.py), SQLite
"""

import logging
from datetime import datetime, timedelta
from threading import Lock
from typing import Optional, Dict, Any


logger = logging.getLogger(__name__)


class LockoutManager:
    """Manages account lockout states with persistence and auto-expiry"""

    def __init__(self, db=None):
        """Initialize lockout manager with optional database connection

        Args:
            db: Database connection for persistence (optional)
        """
        self.db = db
        self.lockout_state: Dict[int, Dict[str, Any]] = {}
        self._lock = Lock()  # Thread-safety for concurrent access

        logger.info("LockoutManager initialized")

    def apply_lockout(self, account_id: int, reason: str, duration_hours: float) -> None:
        """Apply lockout with duration in hours

        Args:
            account_id: TopstepX account ID
            reason: Human-readable lockout reason
            duration_hours: Lockout duration in hours
        """
        until = datetime.now() + timedelta(hours=duration_hours)
        self.set_lockout(account_id, reason, until)

    def set_lockout(self, account_id: int, reason: str, until: Optional[datetime]) -> None:
        """Set hard lockout until specific datetime

        Args:
            account_id: TopstepX account ID
            reason: Human-readable lockout reason
            until: Datetime when lockout expires (None for permanent)
        """
        with self._lock:
            self.lockout_state[account_id] = {
                "reason": reason,
                "until": until,
                "type": "hard_lockout" if until else "permanent",
                "created_at": datetime.now()
            }

            # Persist to SQLite if database available
            if self.db:
                try:
                    self.db.execute(
                        "INSERT OR REPLACE INTO lockouts (account_id, reason, expires_at, created_at) VALUES (?, ?, ?, ?)",
                        (account_id, reason, until, datetime.now())
                    )
                except Exception as e:
                    logger.error(f"Failed to persist lockout to database: {e}")

            logger.info(f"Lockout set for account {account_id}: {reason} until {until}")

    def is_locked_out(self, account_id: int) -> bool:
        """Check if account is currently locked out

        Args:
            account_id: TopstepX account ID

        Returns:
            True if locked out, False otherwise
        """
        with self._lock:
            if account_id not in self.lockout_state:
                return False

            lockout = self.lockout_state[account_id]

            # Permanent lockout (until is None)
            if lockout['until'] is None:
                return True

            # Check if lockout expired
            if datetime.now() >= lockout['until']:
                self._clear_lockout_internal(account_id)
                return False

            return True

    def get_lockout_expiry(self, account_id: int) -> Optional[datetime]:
        """Get lockout expiry time

        Args:
            account_id: TopstepX account ID

        Returns:
            Datetime of expiry, or None if not locked out
        """
        with self._lock:
            if account_id not in self.lockout_state:
                return None
            return self.lockout_state[account_id].get('until')

    def remove_lockout(self, account_id: int) -> bool:
        """Remove lockout (manual unlock)

        Args:
            account_id: TopstepX account ID

        Returns:
            True if lockout was removed, False if no lockout existed
        """
        with self._lock:
            if account_id not in self.lockout_state:
                return False

            self._clear_lockout_internal(account_id)
            return True

    def clear_lockout(self, account_id: int) -> None:
        """Clear lockout for account (alias for remove_lockout)

        Args:
            account_id: TopstepX account ID
        """
        self.remove_lockout(account_id)

    def _clear_lockout_internal(self, account_id: int) -> None:
        """Internal method to clear lockout (assumes lock already held)

        Args:
            account_id: TopstepX account ID
        """
        if account_id in self.lockout_state:
            reason = self.lockout_state[account_id]['reason']
            del self.lockout_state[account_id]

            # Remove from SQLite if database available
            if self.db:
                try:
                    self.db.execute("DELETE FROM lockouts WHERE account_id=?", (account_id,))
                except Exception as e:
                    logger.error(f"Failed to remove lockout from database: {e}")

            logger.info(f"Lockout cleared for account {account_id}: {reason}")

    def get_active_lockouts(self) -> Dict[int, Dict[str, Any]]:
        """Get all active lockouts

        Returns:
            Dictionary of account_id -> lockout info
        """
        with self._lock:
            return dict(self.lockout_state)

    def cleanup_expired_lockouts(self) -> None:
        """Background task to auto-clear expired lockouts

        Called periodically by daemon main loop.
        """
        with self._lock:
            now = datetime.now()
            expired_accounts = []

            for account_id, lockout in self.lockout_state.items():
                # Skip permanent lockouts
                if lockout['until'] is None:
                    continue

                if now >= lockout['until']:
                    expired_accounts.append(account_id)

            for account_id in expired_accounts:
                self._clear_lockout_internal(account_id)
                logger.info(f"Auto-cleared expired lockout for account {account_id}")

    def check_expired_lockouts(self) -> None:
        """Alias for cleanup_expired_lockouts for backward compatibility"""
        self.cleanup_expired_lockouts()

    def get_lockout_info(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get lockout information for display

        Args:
            account_id: TopstepX account ID

        Returns:
            Dict with lockout details, or None if not locked out

        Example Return:
            {
                "reason": "Daily loss limit hit",
                "until": datetime(2025, 1, 17, 17, 0),
                "remaining_seconds": 9845,
                "type": "hard_lockout"
            }
        """
        if not self.is_locked_out(account_id):
            return None

        with self._lock:
            lockout = self.lockout_state[account_id]

            # Calculate remaining time
            remaining_seconds = 0
            if lockout['until']:
                remaining = (lockout['until'] - datetime.now()).total_seconds()
                remaining_seconds = max(0, int(remaining))

            return {
                "reason": lockout['reason'],
                "until": lockout['until'],
                "remaining_seconds": remaining_seconds,
                "type": lockout['type']
            }

    def load_lockouts_from_db(self) -> None:
        """Load lockouts from SQLite on daemon startup"""
        if not self.db:
            logger.warning("No database connection, skipping lockout loading")
            return

        try:
            with self._lock:
                rows = self.db.execute(
                    "SELECT account_id, reason, expires_at FROM lockouts WHERE expires_at > ? OR expires_at IS NULL",
                    (datetime.now(),)
                )

                loaded_count = 0
                for row in rows:
                    account_id, reason, until = row
                    self.lockout_state[account_id] = {
                        "reason": reason,
                        "until": until,
                        "type": "hard_lockout" if until else "permanent",
                        "created_at": datetime.now()
                    }
                    loaded_count += 1

                logger.info(f"Loaded {loaded_count} lockouts from database")
        except Exception as e:
            logger.error(f"Failed to load lockouts from database: {e}")
