"""MOD-001: Enforcement Actions

Centralized enforcement logic - all rules call these functions to execute actions.

Purpose:
- Provides unified API for closing positions, canceling orders, applying lockouts
- Ensures consistent enforcement across all risk rules
- Handles logging and error recovery
- Thread-safe for concurrent rule execution

Dependencies:
- src/api/rest_client.py - TopstepX REST API client
- Database for enforcement logging
- State manager for lockout tracking

Test Coverage:
- tests/unit/test_enforcement_actions.py (8 test scenarios)
"""

import logging
from datetime import datetime
from typing import Optional
from threading import Lock

logger = logging.getLogger(__name__)


class EnforcementActions:
    """Centralized enforcement actions for all risk rules"""

    def __init__(self, rest_client, state_mgr=None, db=None):
        """Initialize enforcement actions

        Args:
            rest_client: RestClient instance for API calls
            state_mgr: State manager (optional, for position tracking)
            db: Database connection (optional, for enforcement logging)
        """
        self.rest_client = rest_client
        self.state_mgr = state_mgr
        self.db = db
        self._lock = Lock()  # For thread-safe operations

    def close_all_positions(self, account_id: int) -> bool:
        """Close all open positions for an account

        Args:
            account_id: TopstepX account ID

        Returns:
            True if successful, False otherwise

        Used by: RULE-001, 003, 009 (all "close all" rules)
        """
        try:
            logger.info(f"Closing all positions for account {account_id}")

            # Step 1: Get all open positions
            positions = self.rest_client.search_open_positions(account_id)

            if not positions:
                logger.info(f"No positions to close for account {account_id}")
                return True

            # Step 2: Close each position
            closed_count = 0
            for position in positions:
                try:
                    self.rest_client.close_position(account_id, position.contract_id)
                    closed_count += 1
                except Exception as e:
                    logger.error(f"Error closing position {position.contract_id}: {e}")
                    # Continue closing other positions even if one fails

            logger.info(f"Closed {closed_count} positions for account {account_id}")

            # Log enforcement action
            self.log_enforcement(
                action_type="CLOSE_ALL_POSITIONS",
                account_id=account_id,
                reason=f"Closed {closed_count} positions",
                details={"count": closed_count}
            )

            return True

        except Exception as e:
            logger.error(f"Error closing positions for account {account_id}: {e}")
            return False

    def cancel_all_orders(self, account_id: int) -> bool:
        """Cancel all open orders for an account

        Args:
            account_id: TopstepX account ID

        Returns:
            True if successful, False otherwise

        Used by: RULE-003, 009 (lockout rules)
        """
        try:
            logger.info(f"Canceling all orders for account {account_id}")

            # Get all open orders
            payload = {"accountId": account_id}
            response = self.rest_client._make_authenticated_request(
                'POST', '/api/Order/searchOpen', payload
            )

            orders = response.get('orders', [])

            if not orders:
                logger.info(f"No orders to cancel for account {account_id}")
                return True

            # Cancel each order
            canceled_count = 0
            for order in orders:
                try:
                    self.rest_client.cancel_order(account_id, order['id'])
                    canceled_count += 1
                except Exception as e:
                    logger.error(f"Error canceling order {order['id']}: {e}")
                    # Continue canceling other orders even if one fails

            logger.info(f"Cancelled {canceled_count} orders for account {account_id}")

            # Log enforcement action
            self.log_enforcement(
                action_type="CANCEL_ALL_ORDERS",
                account_id=account_id,
                reason=f"Cancelled {canceled_count} orders",
                details={"count": canceled_count}
            )

            return True

        except Exception as e:
            logger.error(f"Error cancelling orders for account {account_id}: {e}")
            return False

    def apply_lockout(self, account_id: int, reason: str, duration_hours: Optional[int] = None) -> bool:
        """Apply lockout to an account

        Args:
            account_id: TopstepX account ID
            reason: Reason for lockout
            duration_hours: Lockout duration in hours (None = permanent)

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                logger.info(f"Applying lockout to account {account_id}: {reason}")

                # Calculate expiry time
                expiry = None
                if duration_hours:
                    from datetime import timedelta
                    expiry = datetime.now() + timedelta(hours=duration_hours)

                # Store in state manager if available
                if self.state_mgr:
                    self.state_mgr.set_lockout(account_id, reason, expiry)

                # Log enforcement action
                self.log_enforcement(
                    action_type="APPLY_LOCKOUT",
                    account_id=account_id,
                    reason=reason,
                    details={
                        "duration_hours": duration_hours,
                        "expiry": expiry.isoformat() if expiry else None
                    }
                )

                return True

        except Exception as e:
            logger.error(f"Error applying lockout to account {account_id}: {e}")
            return False

    def remove_lockout(self, account_id: int) -> bool:
        """Remove lockout from an account

        Args:
            account_id: TopstepX account ID

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                logger.info(f"Removing lockout from account {account_id}")

                # Remove from state manager if available
                if self.state_mgr:
                    self.state_mgr.clear_lockout(account_id)

                # Log enforcement action
                self.log_enforcement(
                    action_type="REMOVE_LOCKOUT",
                    account_id=account_id,
                    reason="Lockout removed",
                    details={}
                )

                return True

        except Exception as e:
            logger.error(f"Error removing lockout from account {account_id}: {e}")
            return False

    def log_enforcement(self, action_type: str, account_id: int,
                       reason: str, details: dict) -> None:
        """Log enforcement action to database

        Args:
            action_type: Type of enforcement action
            account_id: Account ID
            reason: Reason for action
            details: Additional details as dict
        """
        try:
            timestamp = datetime.now()

            # Write to database if available
            if self.db:
                query = """
                    INSERT INTO enforcement_log
                    (timestamp, action_type, account_id, reason, details)
                    VALUES (?, ?, ?, ?, ?)
                """
                import json
                self.db.execute(query, (
                    timestamp,
                    action_type,
                    account_id,
                    reason,
                    json.dumps(details)
                ))

            # Also write to file log
            log_msg = f"{action_type}: account={account_id}, reason={reason}"
            if details:
                detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
                log_msg += f", {detail_str}"

            logger.info(f"Enforcement: {log_msg}")

        except Exception as e:
            logger.error(f"Error logging enforcement action: {e}")
