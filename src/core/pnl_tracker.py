"""MOD-005: P&L Tracker

Centralized P&L calculation and tracking for all risk rules.

Purpose:
- Single source of truth for P&L calculations
- Separate realized vs unrealized tracking
- Daily aggregation and reset
- Database persistence
"""

import logging
from typing import Dict, Optional
from datetime import datetime, date

logger = logging.getLogger(__name__)


class PnLTracker:
    """Centralized P&L calculation and tracking

    All risk rules call these methods instead of calculating P&L themselves.
    This ensures consistency and accuracy across all rules.
    """

    def __init__(self, db=None, state_mgr=None, quote_tracker=None, contract_cache=None, log_handler=None):
        """Initialize P&L tracker

        Args:
            db: Database connection for persistence
            state_mgr: State manager for position data
            quote_tracker: Quote tracker for current prices
            contract_cache: Contract cache for tick values
            log_handler: Optional logger for tracking operations
        """
        self.db = db
        self.state_mgr = state_mgr
        self.quote_tracker = quote_tracker
        self.contract_cache = contract_cache
        self.logger = log_handler if log_handler else logger

        # In-memory state: {account_id: realized_pnl}
        self.daily_pnl: Dict[int, float] = {}

        # Unrealized P&L by position: {account_id: {contract_id: unrealized_pnl}}
        self.unrealized_pnl: Dict[int, Dict[str, float]] = {}

    def update_position_pnl(self, account_id: int, contract_id: str, unrealized_pnl: float) -> None:
        """Update unrealized P&L for a specific position

        Args:
            account_id: Account identifier
            contract_id: Contract identifier
            unrealized_pnl: Current unrealized P&L for this position
        """
        if account_id not in self.unrealized_pnl:
            self.unrealized_pnl[account_id] = {}

        self.unrealized_pnl[account_id][contract_id] = unrealized_pnl

        self.logger.debug(
            f"Updated unrealized P&L for account {account_id}, "
            f"contract {contract_id}: ${unrealized_pnl:.2f}"
        )

    def record_realized_pnl(self, account_id: int, contract_id: str, realized_pnl: float) -> float:
        """Record realized P&L from a closed position

        This is an alias for add_trade_pnl for better semantic clarity.

        Args:
            account_id: Account identifier
            contract_id: Contract identifier (for logging)
            realized_pnl: Realized P&L from the closed position

        Returns:
            Current daily realized P&L total
        """
        self.logger.info(
            f"Recording realized P&L for account {account_id}, "
            f"contract {contract_id}: ${realized_pnl:.2f}"
        )
        return self.add_trade_pnl(account_id, realized_pnl)

    def add_trade_pnl(self, account_id: int, pnl: float) -> float:
        """Add realized P&L from a trade to daily total

        Args:
            account_id: TopstepX account ID
            pnl: Realized P&L from trade (can be positive or negative)

        Returns:
            Current daily realized P&L total
        """
        # Initialize if new account
        if account_id not in self.daily_pnl:
            self.daily_pnl[account_id] = 0.0

        # Add this trade's P&L
        self.daily_pnl[account_id] += pnl

        current_total = self.daily_pnl[account_id]

        # Persist to database
        if self.db:
            try:
                self.db.execute(
                    """UPDATE daily_pnl
                       SET realized_pnl = ?
                       WHERE account_id = ? AND date = ?""",
                    (current_total, account_id, date.today())
                )
                self.logger.debug(
                    f"Persisted P&L for account {account_id}: ${current_total:.2f}"
                )
            except Exception as e:
                self.logger.error(f"Failed to persist P&L for account {account_id}: {e}")

        self.logger.info(
            f"Added P&L ${pnl:.2f} for account {account_id}, "
            f"daily total now: ${current_total:.2f}"
        )

        return current_total

    def get_daily_realized_pnl(self, account_id: int) -> float:
        """Get current daily realized P&L total

        Args:
            account_id: Account identifier

        Returns:
            Current daily realized P&L (0.0 if no trades)
        """
        return self.daily_pnl.get(account_id, 0.0)

    def get_total_unrealized_pnl(self, account_id: int) -> float:
        """Get total unrealized P&L across all positions

        Args:
            account_id: Account identifier

        Returns:
            Total unrealized P&L for all open positions
        """
        if account_id not in self.unrealized_pnl:
            return 0.0

        # Sum unrealized P&L across all positions
        total = sum(self.unrealized_pnl[account_id].values())

        self.logger.debug(f"Total unrealized P&L for account {account_id}: ${total:.2f}")

        return total

    def calculate_unrealized_pnl(self, account_id: int) -> float:
        """Calculate total unrealized P&L for all open positions

        Uses current market prices to calculate P&L for all positions.

        Args:
            account_id: Account identifier

        Returns:
            Total unrealized P&L across all positions
        """
        if not self.state_mgr or not self.quote_tracker or not self.contract_cache:
            self.logger.warning(
                f"Cannot calculate unrealized P&L for account {account_id}: "
                "missing required dependencies"
            )
            return 0.0

        # Get all open positions
        positions = self.state_mgr.get_all_positions(account_id)

        if not positions:
            self.logger.debug(f"No open positions for account {account_id}")
            return 0.0

        total_unrealized = 0.0

        for position in positions:
            contract_id = position['contractId']
            position_type = position['type']  # 1=Long, 2=Short
            size = position['size']
            entry_price = position['averagePrice']

            # Get current quote
            quote = self.quote_tracker.get_quote(contract_id)
            if quote is None:
                self.logger.warning(f"Missing quote data for {contract_id}, skipping position")
                continue

            # Extract current price
            current_price = quote.get('lastPrice')
            if current_price is None:
                self.logger.warning(f"No quote data available for {contract_id}, skipping position")
                continue

            # Get contract metadata
            try:
                contract = self.contract_cache.get_contract(contract_id)
                if contract is None:
                    self.logger.error(f"Contract metadata not found for {contract_id}")
                    continue
                tick_value = contract['tickValue']
                tick_size = contract['tickSize']
            except Exception as e:
                self.logger.error(f"Failed to get contract metadata for {contract_id}: {e}")
                continue

            # Calculate P&L
            price_diff = current_price - entry_price
            ticks_moved = price_diff / tick_size

            if position_type == 1:  # Long
                position_pnl = ticks_moved * tick_value * size
            elif position_type == 2:  # Short
                position_pnl = -ticks_moved * tick_value * size
            else:
                self.logger.warning(f"Unknown position type {position_type} for {contract_id}")
                continue

            total_unrealized += position_pnl

            # Update per-position tracking
            self.update_position_pnl(account_id, contract_id, position_pnl)

            self.logger.debug(
                f"Position P&L for {contract_id}: entry=${entry_price:.2f}, "
                f"current=${current_price:.2f}, P&L=${position_pnl:.2f}"
            )

        self.logger.info(
            f"Calculated total unrealized P&L for account {account_id}: "
            f"${total_unrealized:.2f} across {len(positions)} positions"
        )

        return total_unrealized

    def reset_daily_pnl(self, account_id: int) -> None:
        """Reset daily P&L counters (called at daily reset time)

        Args:
            account_id: Account identifier
        """
        self.logger.info(f"Resetting daily P&L for account {account_id}")

        # Reset in-memory state
        self.daily_pnl[account_id] = 0.0

        # Clear unrealized P&L tracking
        if account_id in self.unrealized_pnl:
            self.unrealized_pnl[account_id].clear()

        # Archive old data and start fresh in database
        if self.db:
            try:
                self.db.execute(
                    """INSERT OR REPLACE INTO daily_pnl
                       (account_id, realized_pnl, date)
                       VALUES (?, 0.0, ?)""",
                    (account_id, date.today())
                )
                self.logger.debug(f"Persisted P&L reset for account {account_id}")
            except Exception as e:
                self.logger.error(f"Failed to persist P&L reset for account {account_id}: {e}")

    def get_pnl_history(self, account_id: int, days: int = 7) -> list:
        """Get historical P&L data

        Args:
            account_id: Account identifier
            days: Number of days of history to retrieve

        Returns:
            List of (date, realized_pnl) tuples
        """
        if not self.db:
            self.logger.warning(f"Cannot get P&L history for account {account_id}: no database")
            return []

        try:
            rows = self.db.execute(
                """SELECT date, realized_pnl
                   FROM daily_pnl
                   WHERE account_id = ?
                   ORDER BY date DESC
                   LIMIT ?""",
                (account_id, days)
            )

            history = [(row[0], row[1]) for row in rows]

            self.logger.debug(
                f"Retrieved {len(history)} days of P&L history for account {account_id}"
            )

            return history

        except Exception as e:
            self.logger.error(f"Failed to get P&L history for account {account_id}: {e}")
            return []

    def load_pnl_from_db(self) -> None:
        """Load current day's P&L from database into memory

        Called on daemon startup to restore state.
        """
        if not self.db:
            self.logger.warning("Cannot load P&L from database: no database connection")
            return

        try:
            today = date.today()
            rows = self.db.execute(
                """SELECT account_id, realized_pnl
                   FROM daily_pnl
                   WHERE date = ?""",
                (today,)
            )

            count = 0
            for account_id, realized_pnl in rows:
                self.daily_pnl[account_id] = realized_pnl
                count += 1

            self.logger.info(f"Loaded P&L for {count} accounts from database")

        except Exception as e:
            self.logger.error(f"Failed to load P&L from database: {e}")
