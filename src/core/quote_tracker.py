"""MOD-006: Quote Tracker

Real-time price tracking from Market Hub - all rules call these functions.

Purpose:
- Single source of truth for current prices
- Consistency: All rules use same price data
- Stale data handling: Centralized quote age checking
- Performance: In-memory cache for fast lookups

Dependencies:
- API-INT-001: GatewayQuote event payload
- market_hub.py: Calls update_quote() on events

Used By:
- MOD-005 (PNL Tracker)
- RULE-004, RULE-005, RULE-012
"""

from datetime import datetime, timezone
from typing import Dict, Optional, Callable, List


class QuoteTracker:
    """Real-time price tracking from Market Hub

    Manages in-memory quote cache with staleness detection.
    All quote data centralized here - rules never directly handle GatewayQuote events.
    """

    def __init__(self):
        """Initialize quote tracker with empty state"""
        # In-memory quote storage: {contract_id: quote_data}
        self.quotes: Dict[str, Dict] = {}

        # Subscription callbacks: {contract_id: [callbacks]}
        self._subscriptions: Dict[str, List[Callable]] = {}

    def update_quote(self, contract_id: str, bid: float, ask: float,
                    last: float, timestamp: datetime) -> None:
        """Update quote from Market Hub event

        Args:
            contract_id: Contract ID (e.g., "CON.F.US.MNQ.U25")
            bid: Best bid price
            ask: Best ask price
            last: Last traded price
            timestamp: Quote timestamp from exchange

        Example:
            tracker.update_quote(
                "CON.F.US.MNQ.U25",
                bid=20949.75,
                ask=20950.25,
                last=20950.00,
                timestamp=datetime(2024, 7, 21, 13, 45, 0)
            )
        """
        # Store quote with both exchange timestamp and local update time
        self.quotes[contract_id] = {
            'lastPrice': last,
            'bestBid': bid,
            'bestAsk': ask,
            'timestamp': timestamp,
            'lastUpdated': datetime.now()
        }

        # Notify subscribers
        if contract_id in self._subscriptions:
            for callback in self._subscriptions[contract_id]:
                try:
                    callback(contract_id, self.quotes[contract_id])
                except Exception:
                    # Silently ignore callback errors to prevent disruption
                    pass

    def get_latest_quote(self, contract_id: str) -> Optional[Dict]:
        """Get complete quote data for contract

        Args:
            contract_id: Contract ID

        Returns:
            Quote dictionary with lastPrice, bestBid, bestAsk, timestamp, lastUpdated
            or None if no quote available
        """
        return self.quotes.get(contract_id)

    def get_last_price(self, contract_id: str) -> Optional[float]:
        """Get most recent price for contract

        Args:
            contract_id: Contract ID (e.g., "CON.F.US.MNQ.U25")

        Returns:
            Last price, or None if no quote available

        Used By:
            - MOD-005 (PNL Tracker)
            - RULE-004, RULE-005, RULE-012
        """
        if contract_id not in self.quotes:
            return None

        return self.quotes[contract_id]['lastPrice']

    def is_quote_stale(self, contract_id: str, max_age_seconds: int = 10) -> bool:
        """Check if quote is stale (too old)

        Args:
            contract_id: Contract ID
            max_age_seconds: Maximum acceptable age (default 10s)

        Returns:
            True if quote is stale or missing

        Used By:
            - RULE-004, RULE-005 (to warn about stale data)
        """
        if contract_id not in self.quotes:
            return True

        age = (datetime.now() - self.quotes[contract_id]['lastUpdated']).total_seconds()
        return age > max_age_seconds

    def get_quote_age(self, contract_id: str) -> Optional[float]:
        """Get seconds since last update

        Args:
            contract_id: Contract ID

        Returns:
            Age in seconds, or None if no quote available
        """
        if contract_id not in self.quotes:
            return None

        return (datetime.now() - self.quotes[contract_id]['lastUpdated']).total_seconds()

    def subscribe_to_quotes(self, contract_ids: List[str], callback: Callable) -> None:
        """Subscribe to quote updates for contracts

        Args:
            contract_ids: List of contract IDs to subscribe to
            callback: Function to call on updates, signature: callback(contract_id, quote_data)

        Example:
            def on_quote_update(contract_id, quote_data):
                print(f"New quote for {contract_id}: {quote_data['lastPrice']}")

            tracker.subscribe_to_quotes(["CON.F.US.MNQ.U25"], on_quote_update)
        """
        for contract_id in contract_ids:
            if contract_id not in self._subscriptions:
                self._subscriptions[contract_id] = []

            if callback not in self._subscriptions[contract_id]:
                self._subscriptions[contract_id].append(callback)

    def unsubscribe_from_quotes(self, contract_ids: List[str], callback: Optional[Callable] = None) -> None:
        """Unsubscribe from quote updates

        Args:
            contract_ids: List of contract IDs to unsubscribe from
            callback: Specific callback to remove, or None to remove all callbacks

        Example:
            # Remove specific callback
            tracker.unsubscribe_from_quotes(["CON.F.US.MNQ.U25"], on_quote_update)

            # Remove all callbacks for contract
            tracker.unsubscribe_from_quotes(["CON.F.US.MNQ.U25"])
        """
        for contract_id in contract_ids:
            if contract_id not in self._subscriptions:
                continue

            if callback is None:
                # Remove all callbacks
                self._subscriptions[contract_id] = []
            else:
                # Remove specific callback
                if callback in self._subscriptions[contract_id]:
                    self._subscriptions[contract_id].remove(callback)
