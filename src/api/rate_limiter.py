"""
Rate Limiter for API Resilience

Implements:
- Sliding window rate limiting
- Per-endpoint rate limits
- Automatic wait time calculation
- Request tracking and throttling
- Token bucket algorithm for burst handling

Rate Limits:
- History endpoint: 50 requests per 30 seconds
- General endpoints: 200 requests per 60 seconds

Test coverage:
- tests/unit/api/test_rate_limiter.py
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from threading import Lock
from collections import deque

# Configure logging
logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter with sliding window tracking.

    Features:
    - Per-endpoint rate limiting
    - Sliding window algorithm
    - Thread-safe operation
    - Automatic throttling
    - Burst support with token bucket
    - Detailed rate limit tracking
    """

    # Default rate limits
    DEFAULT_LIMIT = 200  # requests per window
    DEFAULT_WINDOW = 60  # seconds

    # Special endpoint limits
    HISTORY_LIMIT = 50  # requests per window
    HISTORY_WINDOW = 30  # seconds

    # Endpoint type classifications
    ENDPOINT_TYPES = {
        'history': [
            '/api/Position/searchHistory',
            '/api/Order/searchHistory',
            '/api/Trade/searchHistory',
        ],
        'general': [
            '/api/Position/searchOpen',
            '/api/Position/closeContract',
            '/api/Order/place',
            '/api/Order/modify',
            '/api/Order/cancel',
            '/api/Contract/searchById',
            '/api/Auth/loginKey',
        ]
    }

    def __init__(self):
        """Initialize rate limiter with default limits"""
        self._lock = Lock()

        # Sliding window tracking per endpoint type
        self._windows: Dict[str, deque] = {
            'history': deque(),
            'general': deque(),
        }

        # Token bucket for burst handling
        self._tokens: Dict[str, float] = {
            'history': float(self.HISTORY_LIMIT),
            'general': float(self.DEFAULT_LIMIT),
        }

        # Last refill timestamp
        self._last_refill: Dict[str, datetime] = {
            'history': datetime.now(),
            'general': datetime.now(),
        }

        # Rate limit configuration
        self._limits: Dict[str, int] = {
            'history': self.HISTORY_LIMIT,
            'general': self.DEFAULT_LIMIT,
        }

        self._windows_size: Dict[str, int] = {
            'history': self.HISTORY_WINDOW,
            'general': self.DEFAULT_WINDOW,
        }

        # Statistics tracking
        self._total_requests = 0
        self._total_waits = 0
        self._total_wait_time = 0.0

        logger.debug("Rate limiter initialized with limits: "
                    f"history={self.HISTORY_LIMIT}/{self.HISTORY_WINDOW}s, "
                    f"general={self.DEFAULT_LIMIT}/{self.DEFAULT_WINDOW}s")

    def acquire(self, endpoint: str) -> float:
        """
        Acquire permission to make request, waiting if necessary.

        Args:
            endpoint: API endpoint path

        Returns:
            Time waited in seconds (0 if no wait needed)

        Example:
            wait_time = limiter.acquire('/api/Order/place')
            # Returns 0 if under limit, or waits and returns wait duration
        """
        endpoint_type = self._classify_endpoint(endpoint)

        with self._lock:
            # Refill tokens based on elapsed time
            self._refill_tokens(endpoint_type)

            # Clean up old timestamps from sliding window
            self._cleanup_window(endpoint_type)

            # Check if we need to wait
            wait_time = self._calculate_wait_time(endpoint_type)

            if wait_time > 0:
                logger.warning(
                    f"Rate limit approaching for {endpoint_type} endpoints. "
                    f"Waiting {wait_time:.2f}s"
                )
                self._total_waits += 1
                self._total_wait_time += wait_time

                # Release lock during wait to allow other threads
                self._lock.release()
                try:
                    time.sleep(wait_time)
                finally:
                    self._lock.acquire()

                # Re-check after waiting
                self._refill_tokens(endpoint_type)
                self._cleanup_window(endpoint_type)

            # Consume a token and record timestamp
            self._tokens[endpoint_type] -= 1
            self._windows[endpoint_type].append(datetime.now())
            self._total_requests += 1

            logger.debug(
                f"Request acquired for {endpoint_type}: "
                f"tokens={self._tokens[endpoint_type]:.1f}, "
                f"window_count={len(self._windows[endpoint_type])}"
            )

            return wait_time

    def release(self):
        """
        Mark request as complete (for compatibility with context managers).

        Note: In sliding window implementation, release is automatic
        as old timestamps are cleaned up based on time.
        """
        pass

    def get_wait_time(self, endpoint: str) -> float:
        """
        Calculate how long to wait before next request without acquiring.

        Args:
            endpoint: API endpoint path

        Returns:
            Estimated wait time in seconds
        """
        endpoint_type = self._classify_endpoint(endpoint)

        with self._lock:
            self._cleanup_window(endpoint_type)
            return self._calculate_wait_time(endpoint_type)

    def get_remaining_requests(self, endpoint: str) -> int:
        """
        Get number of remaining requests in current window.

        Args:
            endpoint: API endpoint path

        Returns:
            Number of requests available before rate limit
        """
        endpoint_type = self._classify_endpoint(endpoint)

        with self._lock:
            self._cleanup_window(endpoint_type)
            limit = self._limits[endpoint_type]
            used = len(self._windows[endpoint_type])
            return max(0, limit - used)

    def get_reset_time(self, endpoint: str) -> datetime:
        """
        Get when the rate limit window will reset.

        Args:
            endpoint: API endpoint path

        Returns:
            DateTime when window resets
        """
        endpoint_type = self._classify_endpoint(endpoint)

        with self._lock:
            if not self._windows[endpoint_type]:
                return datetime.now()

            # Oldest timestamp + window size = reset time
            oldest = self._windows[endpoint_type][0]
            window_size = self._windows_size[endpoint_type]
            return oldest + timedelta(seconds=window_size)

    def _classify_endpoint(self, endpoint: str) -> str:
        """
        Classify endpoint into rate limit category.

        Args:
            endpoint: API endpoint path

        Returns:
            Endpoint type ('history' or 'general')
        """
        # Check if it's a history endpoint
        for history_endpoint in self.ENDPOINT_TYPES['history']:
            if history_endpoint in endpoint:
                return 'history'

        # Default to general
        return 'general'

    def _cleanup_window(self, endpoint_type: str):
        """
        Remove timestamps outside the sliding window.

        Args:
            endpoint_type: Type of endpoint ('history' or 'general')
        """
        now = datetime.now()
        window_size = self._windows_size[endpoint_type]
        cutoff = now - timedelta(seconds=window_size)

        # Remove old timestamps
        window = self._windows[endpoint_type]
        while window and window[0] < cutoff:
            window.popleft()

    def _refill_tokens(self, endpoint_type: str):
        """
        Refill tokens based on elapsed time (token bucket algorithm).

        Args:
            endpoint_type: Type of endpoint ('history' or 'general')
        """
        now = datetime.now()
        last_refill = self._last_refill[endpoint_type]
        elapsed = (now - last_refill).total_seconds()

        if elapsed <= 0:
            return

        # Calculate refill rate (tokens per second)
        limit = self._limits[endpoint_type]
        window = self._windows_size[endpoint_type]
        refill_rate = limit / window

        # Refill tokens
        tokens_to_add = elapsed * refill_rate
        current_tokens = self._tokens[endpoint_type]
        new_tokens = min(limit, current_tokens + tokens_to_add)

        self._tokens[endpoint_type] = new_tokens
        self._last_refill[endpoint_type] = now

        logger.debug(
            f"Token refill for {endpoint_type}: "
            f"elapsed={elapsed:.2f}s, added={tokens_to_add:.2f}, "
            f"new_total={new_tokens:.1f}/{limit}"
        )

    def _calculate_wait_time(self, endpoint_type: str) -> float:
        """
        Calculate how long to wait before next request is allowed.

        Args:
            endpoint_type: Type of endpoint ('history' or 'general')

        Returns:
            Wait time in seconds (0 if no wait needed)
        """
        limit = self._limits[endpoint_type]
        window = self._windows[endpoint_type]
        window_size = self._windows_size[endpoint_type]

        # If we have tokens available, no wait needed
        if self._tokens[endpoint_type] >= 1:
            return 0.0

        # If window is not full, no wait needed
        if len(window) < limit:
            return 0.0

        # Calculate when oldest request will expire
        now = datetime.now()
        oldest = window[0]
        expires_at = oldest + timedelta(seconds=window_size)
        wait_seconds = (expires_at - now).total_seconds()

        return max(0.0, wait_seconds)

    def get_statistics(self) -> Dict[str, any]:
        """
        Get rate limiter statistics.

        Returns:
            Dictionary with statistics:
            - total_requests: Total requests processed
            - total_waits: Number of times had to wait
            - total_wait_time: Total time spent waiting
            - average_wait_time: Average wait time when throttled
            - current_windows: Current window sizes
            - current_tokens: Current token counts
        """
        with self._lock:
            stats = {
                'total_requests': self._total_requests,
                'total_waits': self._total_waits,
                'total_wait_time': self._total_wait_time,
                'average_wait_time': (
                    self._total_wait_time / self._total_waits
                    if self._total_waits > 0 else 0.0
                ),
                'current_windows': {
                    endpoint_type: len(window)
                    for endpoint_type, window in self._windows.items()
                },
                'current_tokens': self._tokens.copy(),
                'limits': self._limits.copy(),
                'window_sizes': self._windows_size.copy(),
            }

            return stats

    def reset_statistics(self):
        """Reset statistics counters"""
        with self._lock:
            self._total_requests = 0
            self._total_waits = 0
            self._total_wait_time = 0.0

    def reset(self):
        """
        Reset rate limiter state completely.

        Clears all windows and resets tokens to maximum.
        """
        with self._lock:
            for endpoint_type in self._windows:
                self._windows[endpoint_type].clear()
                self._tokens[endpoint_type] = float(self._limits[endpoint_type])
                self._last_refill[endpoint_type] = datetime.now()

            self.reset_statistics()

            logger.info("Rate limiter reset")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()
        return False
