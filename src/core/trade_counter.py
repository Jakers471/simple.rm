"""MOD-008: Trade Counter

Track trade frequency across time windows (minute/hour/session).
Used by RULE-006 (TradeFrequencyLimit) and MOD-004 (Reset Scheduler).

File: src/core/trade_counter.py
Author: Claude Code
"""

from datetime import datetime, timedelta, time
from typing import Dict, List, Optional


class TradeCounter:
    """Track trade frequency across multiple time windows"""

    def __init__(self, db=None):
        """Initialize trade counter.

        Args:
            db: SQLite database connection (optional)
        """
        self.db = db
        self.trade_history: Dict[int, List[datetime]] = {}
        self.session_starts: Dict[int, datetime] = {}

    def record_trade(self, account_id: int, contract_id: str, timestamp: datetime) -> Dict[str, int]:
        """Record a new trade and return current counts.

        Args:
            account_id: TopstepX account ID
            contract_id: Contract ID (for potential future use)
            timestamp: Trade timestamp from GatewayUserTrade event

        Returns:
            Dict with keys 'minute', 'hour', 'session' containing trade counts
        """
        # Initialize if needed
        if account_id not in self.trade_history:
            self.trade_history[account_id] = []

        # Add this trade
        self.trade_history[account_id].append(timestamp)

        # Clean old trades (older than 1 hour)
        cutoff = timestamp - timedelta(hours=1)
        self.trade_history[account_id] = [
            t for t in self.trade_history[account_id] if t > cutoff
        ]

        # Persist to SQLite
        if self.db:
            self.db.execute(
                "INSERT INTO trade_history (account_id, timestamp) VALUES (?, ?)",
                (account_id, timestamp)
            )

        # Return current counts
        return self.get_trade_count(account_id, 60)

    def get_trade_count(self, account_id: int, window_minutes: int) -> Dict[str, int]:
        """Get trade counts for all time windows.

        Args:
            account_id: TopstepX account ID
            window_minutes: Time window in minutes (typically 60)

        Returns:
            Dict with keys 'minute', 'hour', 'session' containing trade counts
        """
        current_time = datetime.now()

        if account_id not in self.trade_history:
            return {'minute': 0, 'hour': 0, 'session': 0}

        trades = self.trade_history[account_id]

        # Count trades in each window
        minute_cutoff = current_time - timedelta(minutes=1)
        hour_cutoff = current_time - timedelta(hours=1)
        session_start = self._get_session_start_internal(account_id)

        return {
            'minute': len([t for t in trades if t > minute_cutoff]),
            'hour': len([t for t in trades if t > hour_cutoff]),
            'session': len([t for t in trades if t > session_start])
        }

    def get_trades_in_window(self, account_id: int, window_minutes: int) -> List[datetime]:
        """Get list of trades in the specified time window.

        Args:
            account_id: TopstepX account ID
            window_minutes: Time window in minutes

        Returns:
            List of trade timestamps in the window
        """
        if account_id not in self.trade_history:
            return []

        current_time = datetime.now()
        cutoff = current_time - timedelta(minutes=window_minutes)

        return [t for t in self.trade_history[account_id] if t > cutoff]

    def reset_counter(self, account_id: int) -> None:
        """Reset session trade count (alias for reset_session).

        Called by MOD-004 (Reset Scheduler) at reset_time.

        Args:
            account_id: TopstepX account ID
        """
        self.reset_session(account_id)

    def reset_session(self, account_id: int) -> None:
        """Reset session trade count.

        Called by MOD-004 (Reset Scheduler) at reset_time.

        Args:
            account_id: TopstepX account ID
        """
        # Clear in-memory history
        self.trade_history[account_id] = []

        # Update session start time
        self.session_starts[account_id] = datetime.now()

        # Archive to SQLite
        if self.db:
            self.db.execute(
                "UPDATE session_state SET session_start = ? WHERE account_id = ?",
                (self.session_starts[account_id], account_id)
            )

    def get_last_trade_time(self, account_id: int) -> Optional[datetime]:
        """Get timestamp of the last trade.

        Args:
            account_id: TopstepX account ID

        Returns:
            Datetime of last trade or None if no trades
        """
        if account_id not in self.trade_history or not self.trade_history[account_id]:
            return None

        return max(self.trade_history[account_id])

    def cleanup_old_trades(self, cutoff_time: datetime) -> int:
        """Remove trades older than cutoff time.

        Args:
            cutoff_time: Remove trades older than this timestamp

        Returns:
            Number of trades removed
        """
        removed_count = 0

        for account_id in list(self.trade_history.keys()):
            original_count = len(self.trade_history[account_id])
            self.trade_history[account_id] = [
                t for t in self.trade_history[account_id] if t > cutoff_time
            ]
            removed_count += original_count - len(self.trade_history[account_id])

        return removed_count

    def _get_session_start_internal(self, account_id: int) -> datetime:
        """Get session start time (internal method).

        Args:
            account_id: TopstepX account ID

        Returns:
            Session start datetime
        """
        if account_id not in self.session_starts:
            # Default to today's reset time if not set
            reset_time_obj = time(17, 0)  # 5:00 PM from config
            self.session_starts[account_id] = datetime.combine(
                datetime.now().date(),
                reset_time_obj
            )
            if datetime.now() < self.session_starts[account_id]:
                # Before reset time, use yesterday's reset
                self.session_starts[account_id] -= timedelta(days=1)

        return self.session_starts[account_id]

    def load_from_database(self) -> None:
        """Load trade history from SQLite on daemon startup."""
        if not self.db:
            return

        # Load recent trades (last hour)
        cutoff = datetime.now() - timedelta(hours=1)
        cursor = self.db.execute(
            "SELECT account_id, timestamp FROM trade_history WHERE timestamp > ? ORDER BY timestamp",
            (cutoff,)
        )

        rows = cursor.fetchall()

        # Restore trade history
        for account_id, timestamp in rows:
            if account_id not in self.trade_history:
                self.trade_history[account_id] = []
            self.trade_history[account_id].append(timestamp)

        # Load session start times
        cursor = self.db.execute("SELECT account_id, session_start FROM session_state")
        for account_id, session_start in cursor.fetchall():
            self.session_starts[account_id] = session_start
