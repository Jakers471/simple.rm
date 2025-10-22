"""
MOD-007: Contract Cache

Contract metadata caching with LRU cache, TTL, and SQLite persistence.

Features:
- LRU cache with configurable max size
- Lazy loading from API
- TTL for cache entries
- SQLite persistence for daemon restarts
- Bulk preload support

Test coverage:
- tests/unit/test_contract_cache.py
"""

import time
import logging
from typing import Optional, Dict, List, Any
from collections import OrderedDict

logger = logging.getLogger(__name__)


class ContractCache:
    """
    Contract metadata cache with LRU eviction and TTL.

    Provides cached access to contract metadata (tick values, tick sizes)
    to minimize API calls and improve performance.
    """

    DEFAULT_MAX_SIZE = 1000
    DEFAULT_TTL = 3600  # 1 hour in seconds

    def __init__(self, rest_client=None, db=None, max_size: int = None, ttl: int = None):
        """
        Initialize contract cache.

        Args:
            rest_client: REST API client for fetching contracts
            db: SQLite database connection for persistence
            max_size: Maximum number of contracts to cache (default: 1000)
            ttl: Time-to-live for cache entries in seconds (default: 3600)
        """
        self.rest_client = rest_client
        self.db = db
        self.max_size = max_size or self.DEFAULT_MAX_SIZE
        self.ttl = ttl or self.DEFAULT_TTL

        # LRU cache: OrderedDict maintains insertion order
        # Key: contract_id, Value: {'data': contract_data, 'timestamp': time}
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def get_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """
        Get contract metadata from cache or API.

        Checks cache first. If not found or expired, fetches from API
        and caches the result.

        Args:
            contract_id: Contract ID (e.g., "CON.F.US.MNQ.U25")

        Returns:
            Contract metadata dict with keys:
            - id: Contract ID
            - tickSize: Tick size
            - tickValue: Tick value
            - symbolId: Symbol ID
            - name: Contract name

            Returns None if contract not found.
        """
        # Check if in cache and not expired
        if contract_id in self.cache:
            cached_entry = self.cache[contract_id]
            age = time.time() - cached_entry['timestamp']

            if age < self.ttl:
                # Move to end (most recently used)
                self.cache.move_to_end(contract_id)
                logger.debug(f"Cache hit: {contract_id} (age: {age:.1f}s)")
                return cached_entry['data']
            else:
                # Expired - remove from cache
                logger.debug(f"Cache expired: {contract_id} (age: {age:.1f}s)")
                del self.cache[contract_id]

        # Not in cache or expired - fetch from API
        if not self.rest_client:
            logger.warning(f"No REST client configured, cannot fetch {contract_id}")
            return None

        try:
            logger.debug(f"Cache miss: {contract_id}, fetching from API")
            response = self.rest_client.post(
                "/api/Contract/searchById",
                json={"contractId": contract_id}
            )

            data = response.json()
            if not data.get('success', False):
                error_msg = data.get('errorMessage', 'Unknown error')
                logger.error(f"Failed to fetch contract {contract_id}: {error_msg}")
                return None

            contract_data = data.get('contract')
            if not contract_data:
                logger.error(f"No contract data returned for {contract_id}")
                return None

            # Cache the contract
            self._cache_contract(contract_id, contract_data)

            return contract_data

        except Exception as e:
            logger.error(f"Error fetching contract {contract_id}: {e}")
            return None

    def _cache_contract(self, contract_id: str, contract_data: Dict[str, Any]) -> None:
        """
        Internal method to add contract to cache with LRU eviction.

        Args:
            contract_id: Contract ID
            contract_data: Contract metadata dict
        """
        # Normalize contract data
        normalized_data = {
            'id': contract_data.get('id', contract_id),
            'tickSize': contract_data.get('tickSize', 0.0),
            'tickValue': contract_data.get('tickValue', 0.0),
            'symbolId': contract_data.get('symbolId', ''),
            'name': contract_data.get('name', '')
        }

        # Add to cache with timestamp
        self.cache[contract_id] = {
            'data': normalized_data,
            'timestamp': time.time()
        }

        # Move to end (most recently used)
        self.cache.move_to_end(contract_id)

        # LRU eviction if over max size
        if len(self.cache) > self.max_size:
            # Remove oldest entry (first item)
            evicted_id, _ = self.cache.popitem(last=False)
            logger.debug(f"Cache full, evicted: {evicted_id}")

        # Persist to database if available
        if self.db:
            try:
                self.db.execute(
                    """
                    INSERT OR REPLACE INTO contract_cache
                    (contract_id, tick_size, tick_value, symbol_id, name, cached_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        contract_id,
                        normalized_data['tickSize'],
                        normalized_data['tickValue'],
                        normalized_data['symbolId'],
                        normalized_data['name']
                    )
                )
                self.db.commit()
            except Exception as e:
                logger.error(f"Failed to persist contract to database: {e}")

    def preload_contracts(self, contract_ids: List[str]) -> int:
        """
        Preload multiple contracts into cache.

        Useful for warming cache at startup or before processing.

        Args:
            contract_ids: List of contract IDs to preload

        Returns:
            Number of contracts successfully loaded
        """
        loaded = 0
        for contract_id in contract_ids:
            if self.get_contract(contract_id):
                loaded += 1

        logger.info(f"Preloaded {loaded}/{len(contract_ids)} contracts")
        return loaded

    def invalidate_cache(self, contract_id: str) -> bool:
        """
        Remove contract from cache.

        Forces next access to fetch fresh data from API.

        Args:
            contract_id: Contract ID to invalidate

        Returns:
            True if contract was in cache, False otherwise
        """
        if contract_id in self.cache:
            del self.cache[contract_id]
            logger.debug(f"Invalidated cache for: {contract_id}")
            return True
        return False

    def clear_all(self) -> None:
        """Clear all cached contracts."""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared all cache ({count} contracts)")

    def get_cached_contracts(self) -> List[str]:
        """
        Get list of currently cached contract IDs.

        Returns:
            List of contract IDs in cache
        """
        return list(self.cache.keys())

    def is_cached(self, contract_id: str) -> bool:
        """
        Check if contract is in cache and not expired.

        Args:
            contract_id: Contract ID to check

        Returns:
            True if cached and valid, False otherwise
        """
        if contract_id not in self.cache:
            return False

        cached_entry = self.cache[contract_id]
        age = time.time() - cached_entry['timestamp']
        return age < self.ttl

    def get_tick_value(self, contract_id: str) -> Optional[float]:
        """
        Get tick value for contract.

        Convenience method that fetches contract and returns tick value.

        Args:
            contract_id: Contract ID

        Returns:
            Tick value or None if not found
        """
        contract = self.get_contract(contract_id)
        return contract['tickValue'] if contract else None

    def get_tick_size(self, contract_id: str) -> Optional[float]:
        """
        Get tick size for contract.

        Convenience method that fetches contract and returns tick size.

        Args:
            contract_id: Contract ID

        Returns:
            Tick size or None if not found
        """
        contract = self.get_contract(contract_id)
        return contract['tickSize'] if contract else None

    def load_from_database(self) -> int:
        """
        Load cached contracts from SQLite database.

        Called at daemon startup to restore cache from previous session.

        Returns:
            Number of contracts loaded from database
        """
        if not self.db:
            logger.warning("No database configured, cannot load cache")
            return 0

        try:
            cursor = self.db.execute(
                """
                SELECT contract_id, tick_size, tick_value, symbol_id, name
                FROM contract_cache
                ORDER BY cached_at DESC
                LIMIT ?
                """,
                (self.max_size,)
            )

            rows = cursor.fetchall()
            loaded = 0

            for row in rows:
                contract_id, tick_size, tick_value, symbol_id, name = row

                contract_data = {
                    'id': contract_id,
                    'tickSize': tick_size,
                    'tickValue': tick_value,
                    'symbolId': symbol_id,
                    'name': name
                }

                # Add to in-memory cache (don't persist back to DB)
                self.cache[contract_id] = {
                    'data': contract_data,
                    'timestamp': time.time()
                }
                loaded += 1

            logger.info(f"Loaded {loaded} contracts from database")
            return loaded

        except Exception as e:
            logger.error(f"Failed to load cache from database: {e}")
            return 0
