"""
Comprehensive tests for RateLimiter implementation.

Tests cover:
- Rate limit enforcement with sliding window
- Token bucket refill mechanism
- Per-endpoint classification
- Concurrent request handling
- Wait time calculation
- Statistics tracking
- Thread safety

Target: 90%+ coverage
"""

import pytest
import time
from datetime import datetime, timedelta
from threading import Thread
from unittest.mock import patch
from src.api.rate_limiter import RateLimiter


class TestRateLimiterInitialization:
    """Test rate limiter initialization and configuration."""

    def test_initialization_defaults(self):
        """Test rate limiter initializes with correct defaults."""
        limiter = RateLimiter()

        # Verify default limits
        assert limiter.DEFAULT_LIMIT == 200
        assert limiter.DEFAULT_WINDOW == 60
        assert limiter.HISTORY_LIMIT == 50
        assert limiter.HISTORY_WINDOW == 30

        # Verify internal state initialization
        assert 'history' in limiter._windows
        assert 'general' in limiter._windows
        assert len(limiter._windows['history']) == 0
        assert len(limiter._windows['general']) == 0

        # Verify token buckets are full
        assert limiter._tokens['history'] == 50.0
        assert limiter._tokens['general'] == 200.0

        # Verify statistics are zeroed
        assert limiter._total_requests == 0
        assert limiter._total_waits == 0
        assert limiter._total_wait_time == 0.0

    def test_endpoint_type_classifications(self):
        """Test endpoint classification mappings are defined."""
        limiter = RateLimiter()

        # Verify history endpoints are classified
        assert '/api/Position/searchHistory' in limiter.ENDPOINT_TYPES['history']
        assert '/api/Order/searchHistory' in limiter.ENDPOINT_TYPES['history']
        assert '/api/Trade/searchHistory' in limiter.ENDPOINT_TYPES['history']

        # Verify general endpoints are classified
        assert '/api/Position/searchOpen' in limiter.ENDPOINT_TYPES['general']
        assert '/api/Order/place' in limiter.ENDPOINT_TYPES['general']
        assert '/api/Auth/loginKey' in limiter.ENDPOINT_TYPES['general']


class TestEndpointClassification:
    """Test endpoint type classification."""

    def test_classify_history_endpoints(self):
        """Test history endpoints are classified correctly."""
        limiter = RateLimiter()

        assert limiter._classify_endpoint('/api/Position/searchHistory') == 'history'
        assert limiter._classify_endpoint('/api/Order/searchHistory') == 'history'
        assert limiter._classify_endpoint('/api/Trade/searchHistory') == 'history'

    def test_classify_general_endpoints(self):
        """Test general endpoints are classified correctly."""
        limiter = RateLimiter()

        assert limiter._classify_endpoint('/api/Order/place') == 'general'
        assert limiter._classify_endpoint('/api/Position/searchOpen') == 'general'
        assert limiter._classify_endpoint('/api/Contract/searchById') == 'general'

    def test_classify_unknown_endpoint_defaults_to_general(self):
        """Test unknown endpoints default to general classification."""
        limiter = RateLimiter()

        assert limiter._classify_endpoint('/api/Unknown/endpoint') == 'general'
        assert limiter._classify_endpoint('/api/Custom/action') == 'general'
        assert limiter._classify_endpoint('') == 'general'

    def test_classify_endpoint_partial_match(self):
        """Test endpoint classification handles partial matches."""
        limiter = RateLimiter()

        # Should match even with query parameters
        assert limiter._classify_endpoint('/api/Order/searchHistory?limit=100') == 'history'
        assert limiter._classify_endpoint('/api/Position/searchHistory/details') == 'history'


class TestAcquireBasicBehavior:
    """Test basic acquire() behavior without rate limiting."""

    def test_acquire_returns_zero_when_under_limit(self):
        """Test acquire returns 0 wait time when under limit."""
        limiter = RateLimiter()

        wait_time = limiter.acquire('/api/Order/place')

        assert wait_time == 0.0
        assert limiter._total_requests == 1
        assert len(limiter._windows['general']) == 1

    def test_acquire_increments_request_count(self):
        """Test acquire increments total request counter."""
        limiter = RateLimiter()

        for i in range(5):
            limiter.acquire('/api/Order/place')
            assert limiter._total_requests == i + 1

    def test_acquire_consumes_tokens(self):
        """Test acquire consumes tokens from bucket."""
        limiter = RateLimiter()
        initial_tokens = limiter._tokens['general']

        limiter.acquire('/api/Order/place')

        assert limiter._tokens['general'] == initial_tokens - 1

    def test_acquire_adds_timestamp_to_window(self):
        """Test acquire adds timestamp to sliding window."""
        limiter = RateLimiter()

        before = datetime.now()
        limiter.acquire('/api/Order/place')
        after = datetime.now()

        assert len(limiter._windows['general']) == 1
        timestamp = limiter._windows['general'][0]
        assert before <= timestamp <= after

    def test_acquire_different_endpoints_use_different_limits(self):
        """Test different endpoint types have separate limits."""
        limiter = RateLimiter()

        # Acquire on history endpoint
        limiter.acquire('/api/Order/searchHistory')
        assert len(limiter._windows['history']) == 1
        assert len(limiter._windows['general']) == 0

        # Acquire on general endpoint
        limiter.acquire('/api/Order/place')
        assert len(limiter._windows['history']) == 1
        assert len(limiter._windows['general']) == 1


class TestRateLimitEnforcement:
    """Test rate limit enforcement with waiting."""

    def test_acquire_waits_when_token_bucket_empty(self):
        """Test acquire waits when no tokens available."""
        limiter = RateLimiter()

        # Fill the window AND drain all tokens to force wait
        for _ in range(200):
            limiter._windows['general'].append(datetime.now())
        limiter._tokens['general'] = 0.0

        start = time.time()
        wait_time = limiter.acquire('/api/Order/place')
        elapsed = time.time() - start

        # Should have waited for token refill
        assert wait_time > 0
        assert elapsed >= wait_time * 0.9  # Allow 10% timing variance
        assert limiter._total_waits == 1
        assert limiter._total_wait_time > 0

    def test_acquire_waits_when_window_full(self):
        """Test acquire waits when sliding window is full."""
        limiter = RateLimiter()

        # Fill the history window (50 requests)
        for _ in range(50):
            limiter._windows['history'].append(datetime.now())

        # Ensure no tokens available
        limiter._tokens['history'] = 0.0

        start = time.time()
        wait_time = limiter.acquire('/api/Order/searchHistory')
        elapsed = time.time() - start

        assert wait_time > 0
        assert elapsed >= wait_time * 0.9
        assert limiter._total_waits == 1

    @pytest.mark.slow
    def test_acquire_respects_history_limit(self):
        """Test history endpoints respect 50/30s limit."""
        limiter = RateLimiter()

        # Make 50 requests rapidly (should all succeed)
        for i in range(50):
            wait = limiter.acquire('/api/Order/searchHistory')
            if i < 50:  # First 50 should not wait (have tokens)
                assert wait == 0.0 or wait < 0.1  # Allow small refill waits

        # 51st request should wait
        assert limiter._tokens['history'] < 1.0

    @pytest.mark.slow
    def test_acquire_respects_general_limit(self):
        """Test general endpoints respect 200/60s limit."""
        limiter = RateLimiter()

        # Make 200 requests rapidly
        for i in range(200):
            wait = limiter.acquire('/api/Order/place')
            if i < 200:
                assert wait == 0.0 or wait < 0.1

        # 201st request should wait
        assert limiter._tokens['general'] < 1.0


class TestSlidingWindow:
    """Test sliding window algorithm."""

    def test_cleanup_window_removes_old_timestamps(self):
        """Test old timestamps are removed from window."""
        limiter = RateLimiter()

        # Add old timestamps
        old_time = datetime.now() - timedelta(seconds=70)
        limiter._windows['general'].append(old_time)
        limiter._windows['general'].append(old_time)

        # Add recent timestamp
        limiter._windows['general'].append(datetime.now())

        # Cleanup should remove old timestamps
        limiter._cleanup_window('general')

        assert len(limiter._windows['general']) == 1

    def test_cleanup_window_preserves_recent_timestamps(self):
        """Test recent timestamps are kept in window."""
        limiter = RateLimiter()

        # Add recent timestamps
        now = datetime.now()
        limiter._windows['general'].append(now - timedelta(seconds=10))
        limiter._windows['general'].append(now - timedelta(seconds=5))
        limiter._windows['general'].append(now)

        limiter._cleanup_window('general')

        assert len(limiter._windows['general']) == 3

    def test_cleanup_window_handles_empty_window(self):
        """Test cleanup handles empty window gracefully."""
        limiter = RateLimiter()

        limiter._cleanup_window('general')  # Should not raise

        assert len(limiter._windows['general']) == 0

    def test_cleanup_respects_different_window_sizes(self):
        """Test cleanup uses correct window size for each endpoint type."""
        limiter = RateLimiter()

        # Add timestamp 40 seconds old
        old_time = datetime.now() - timedelta(seconds=40)

        # Should be removed from history (30s window)
        limiter._windows['history'].append(old_time)
        limiter._cleanup_window('history')
        assert len(limiter._windows['history']) == 0

        # Should be kept in general (60s window)
        limiter._windows['general'].append(old_time)
        limiter._cleanup_window('general')
        assert len(limiter._windows['general']) == 1


class TestTokenBucketRefill:
    """Test token bucket refill mechanism."""

    def test_refill_tokens_adds_tokens_over_time(self):
        """Test tokens are refilled based on elapsed time."""
        limiter = RateLimiter()

        # Consume some tokens
        limiter._tokens['general'] = 100.0
        limiter._last_refill['general'] = datetime.now() - timedelta(seconds=10)

        initial_tokens = limiter._tokens['general']
        limiter._refill_tokens('general')

        # Should have refilled some tokens
        # Rate: 200 tokens / 60s = 3.33 tokens/s
        # 10 seconds = ~33.3 tokens
        assert limiter._tokens['general'] > initial_tokens
        assert limiter._tokens['general'] <= 200.0  # Capped at max

    def test_refill_tokens_caps_at_maximum(self):
        """Test token refill doesn't exceed maximum limit."""
        limiter = RateLimiter()

        limiter._tokens['general'] = 50.0
        limiter._last_refill['general'] = datetime.now() - timedelta(seconds=3600)  # 1 hour

        limiter._refill_tokens('general')

        # Should cap at 200, not exceed
        assert limiter._tokens['general'] == 200.0

    def test_refill_tokens_updates_last_refill_time(self):
        """Test last refill timestamp is updated."""
        limiter = RateLimiter()

        old_time = datetime.now() - timedelta(seconds=10)
        limiter._last_refill['general'] = old_time

        before = datetime.now()
        limiter._refill_tokens('general')
        after = datetime.now()

        assert before <= limiter._last_refill['general'] <= after

    def test_refill_tokens_handles_zero_elapsed_time(self):
        """Test refill handles zero elapsed time gracefully."""
        limiter = RateLimiter()

        limiter._tokens['general'] = 100.0
        limiter._last_refill['general'] = datetime.now()

        limiter._refill_tokens('general')

        # Should not significantly change tokens (allow tiny refill due to microsecond elapsed time)
        assert abs(limiter._tokens['general'] - 100.0) < 0.01

    def test_refill_tokens_uses_correct_rate_for_endpoint_type(self):
        """Test refill uses correct rate for each endpoint type."""
        limiter = RateLimiter()

        # History: 50 tokens / 30s = 1.67 tokens/s
        limiter._tokens['history'] = 0.0
        limiter._last_refill['history'] = datetime.now() - timedelta(seconds=10)
        limiter._refill_tokens('history')
        # 10s * 1.67 = ~16.7 tokens
        assert 15.0 <= limiter._tokens['history'] <= 18.0

        # General: 200 tokens / 60s = 3.33 tokens/s
        limiter._tokens['general'] = 0.0
        limiter._last_refill['general'] = datetime.now() - timedelta(seconds=10)
        limiter._refill_tokens('general')
        # 10s * 3.33 = ~33.3 tokens
        assert 32.0 <= limiter._tokens['general'] <= 35.0


class TestWaitTimeCalculation:
    """Test wait time calculation."""

    def test_calculate_wait_time_zero_when_tokens_available(self):
        """Test wait time is zero when tokens available."""
        limiter = RateLimiter()

        limiter._tokens['general'] = 10.0

        wait_time = limiter._calculate_wait_time('general')

        assert wait_time == 0.0

    def test_calculate_wait_time_zero_when_window_not_full(self):
        """Test wait time is zero when window not full."""
        limiter = RateLimiter()

        limiter._tokens['general'] = 0.5  # Less than 1 token
        # Add only 50 requests (limit is 200)
        for _ in range(50):
            limiter._windows['general'].append(datetime.now())

        wait_time = limiter._calculate_wait_time('general')

        assert wait_time == 0.0

    def test_calculate_wait_time_nonzero_when_limited(self):
        """Test wait time is calculated when rate limited."""
        limiter = RateLimiter()

        # Fill window with old requests
        old_time = datetime.now() - timedelta(seconds=50)
        for _ in range(200):
            limiter._windows['general'].append(old_time)

        limiter._tokens['general'] = 0.0

        wait_time = limiter._calculate_wait_time('general')

        # Should wait ~10 seconds (60s window - 50s elapsed)
        assert 8.0 <= wait_time <= 12.0

    def test_calculate_wait_time_uses_oldest_timestamp(self):
        """Test wait time is based on oldest timestamp in window."""
        limiter = RateLimiter()

        # Add requests at different times
        limiter._windows['general'].append(datetime.now() - timedelta(seconds=55))
        for _ in range(199):
            limiter._windows['general'].append(datetime.now() - timedelta(seconds=10))

        limiter._tokens['general'] = 0.0

        wait_time = limiter._calculate_wait_time('general')

        # Should wait ~5 seconds (60s - 55s)
        assert 3.0 <= wait_time <= 7.0


class TestPublicMethods:
    """Test public API methods."""

    def test_get_wait_time(self):
        """Test get_wait_time returns estimated wait time."""
        limiter = RateLimiter()

        # Under limit - should be 0
        wait_time = limiter.get_wait_time('/api/Order/place')
        assert wait_time == 0.0

        # Fill window
        for _ in range(200):
            limiter._windows['general'].append(datetime.now() - timedelta(seconds=50))
        limiter._tokens['general'] = 0.0

        wait_time = limiter.get_wait_time('/api/Order/place')
        assert wait_time > 0.0

    def test_get_remaining_requests(self):
        """Test get_remaining_requests returns correct count."""
        limiter = RateLimiter()

        # Initially should have full limit
        remaining = limiter.get_remaining_requests('/api/Order/place')
        assert remaining == 200

        # After 50 requests
        for _ in range(50):
            limiter._windows['general'].append(datetime.now())

        remaining = limiter.get_remaining_requests('/api/Order/place')
        assert remaining == 150

    def test_get_reset_time(self):
        """Test get_reset_time returns correct reset time."""
        limiter = RateLimiter()

        # Empty window - should return now
        reset_time = limiter.get_reset_time('/api/Order/place')
        assert (reset_time - datetime.now()).total_seconds() < 1

        # With requests
        now = datetime.now()
        limiter._windows['general'].append(now)

        reset_time = limiter.get_reset_time('/api/Order/place')
        expected = now + timedelta(seconds=60)

        # Should be ~60 seconds from now
        diff = (reset_time - expected).total_seconds()
        assert abs(diff) < 1

    def test_release_does_nothing(self):
        """Test release() is a no-op (for context manager compatibility)."""
        limiter = RateLimiter()

        limiter.release()  # Should not raise

    def test_context_manager(self):
        """Test rate limiter works as context manager."""
        limiter = RateLimiter()

        with limiter as lim:
            assert lim is limiter

        # Should not raise


class TestStatistics:
    """Test statistics tracking."""

    def test_get_statistics_initial_state(self):
        """Test statistics are zero initially."""
        limiter = RateLimiter()

        stats = limiter.get_statistics()

        assert stats['total_requests'] == 0
        assert stats['total_waits'] == 0
        assert stats['total_wait_time'] == 0.0
        assert stats['average_wait_time'] == 0.0

    def test_get_statistics_after_requests(self):
        """Test statistics are updated after requests."""
        limiter = RateLimiter()

        # Make some requests
        for _ in range(10):
            limiter.acquire('/api/Order/place')

        stats = limiter.get_statistics()

        assert stats['total_requests'] == 10
        assert stats['current_windows']['general'] == 10

    def test_get_statistics_includes_window_counts(self):
        """Test statistics include current window counts."""
        limiter = RateLimiter()

        limiter.acquire('/api/Order/searchHistory')
        limiter.acquire('/api/Order/searchHistory')
        limiter.acquire('/api/Order/place')

        stats = limiter.get_statistics()

        assert stats['current_windows']['history'] == 2
        assert stats['current_windows']['general'] == 1

    def test_get_statistics_includes_token_counts(self):
        """Test statistics include current token counts."""
        limiter = RateLimiter()

        stats = limiter.get_statistics()

        assert 'history' in stats['current_tokens']
        assert 'general' in stats['current_tokens']
        assert stats['current_tokens']['general'] == 200.0

    def test_get_statistics_average_wait_time(self):
        """Test average wait time calculation."""
        limiter = RateLimiter()

        # Force waits
        limiter._tokens['general'] = 0.0
        limiter.acquire('/api/Order/place')  # Will wait
        limiter.acquire('/api/Order/place')  # Will wait

        stats = limiter.get_statistics()

        assert stats['total_waits'] == 2
        assert stats['average_wait_time'] > 0
        assert stats['average_wait_time'] == stats['total_wait_time'] / 2

    def test_reset_statistics(self):
        """Test reset_statistics clears counters."""
        limiter = RateLimiter()

        # Generate some statistics
        for _ in range(5):
            limiter.acquire('/api/Order/place')

        limiter.reset_statistics()

        assert limiter._total_requests == 0
        assert limiter._total_waits == 0
        assert limiter._total_wait_time == 0.0


class TestReset:
    """Test reset functionality."""

    def test_reset_clears_windows(self):
        """Test reset clears all sliding windows."""
        limiter = RateLimiter()

        # Add some requests
        for _ in range(10):
            limiter.acquire('/api/Order/place')
            limiter.acquire('/api/Order/searchHistory')

        limiter.reset()

        assert len(limiter._windows['general']) == 0
        assert len(limiter._windows['history']) == 0

    def test_reset_refills_tokens(self):
        """Test reset refills tokens to maximum."""
        limiter = RateLimiter()

        # Drain tokens
        limiter._tokens['general'] = 50.0
        limiter._tokens['history'] = 10.0

        limiter.reset()

        assert limiter._tokens['general'] == 200.0
        assert limiter._tokens['history'] == 50.0

    def test_reset_clears_statistics(self):
        """Test reset clears all statistics."""
        limiter = RateLimiter()

        # Generate statistics
        for _ in range(5):
            limiter.acquire('/api/Order/place')

        limiter.reset()

        assert limiter._total_requests == 0
        assert limiter._total_waits == 0
        assert limiter._total_wait_time == 0.0

    def test_reset_updates_last_refill_time(self):
        """Test reset updates last refill timestamp."""
        limiter = RateLimiter()

        old_time = datetime.now() - timedelta(hours=1)
        limiter._last_refill['general'] = old_time

        before = datetime.now()
        limiter.reset()
        after = datetime.now()

        assert before <= limiter._last_refill['general'] <= after


class TestConcurrency:
    """Test thread safety and concurrent access."""

    def test_concurrent_acquires_are_thread_safe(self):
        """Test multiple threads can safely acquire."""
        limiter = RateLimiter()
        results = []

        def worker():
            for _ in range(10):
                wait = limiter.acquire('/api/Order/place')
                results.append(wait)

        # Spawn 5 threads, each making 10 requests
        threads = [Thread(target=worker) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have 50 total requests
        assert limiter._total_requests == 50
        assert len(results) == 50

    def test_concurrent_different_endpoints(self):
        """Test concurrent access to different endpoint types."""
        limiter = RateLimiter()

        def history_worker():
            for _ in range(20):
                limiter.acquire('/api/Order/searchHistory')

        def general_worker():
            for _ in range(20):
                limiter.acquire('/api/Order/place')

        threads = [
            Thread(target=history_worker),
            Thread(target=general_worker),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have requests in both windows
        stats = limiter.get_statistics()
        assert stats['current_windows']['history'] == 20
        assert stats['current_windows']['general'] == 20

    def test_statistics_thread_safe(self):
        """Test statistics remain accurate under concurrent access."""
        limiter = RateLimiter()

        def worker():
            for _ in range(50):
                limiter.acquire('/api/Order/place')

        threads = [Thread(target=worker) for _ in range(4)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Total requests should be exactly 200
        assert limiter._total_requests == 200


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_endpoint_string(self):
        """Test handling of empty endpoint string."""
        limiter = RateLimiter()

        # Should default to general
        wait_time = limiter.acquire('')
        assert wait_time == 0.0
        assert len(limiter._windows['general']) == 1

    def test_very_long_endpoint_string(self):
        """Test handling of very long endpoint string."""
        limiter = RateLimiter()

        long_endpoint = '/api/' + 'a' * 1000
        wait_time = limiter.acquire(long_endpoint)

        assert wait_time == 0.0

    def test_multiple_resets(self):
        """Test multiple consecutive resets."""
        limiter = RateLimiter()

        for _ in range(5):
            limiter.reset()

        # Should still work normally
        wait_time = limiter.acquire('/api/Order/place')
        assert wait_time == 0.0

    def test_acquire_after_long_idle_period(self):
        """Test acquire after long idle period refills tokens."""
        limiter = RateLimiter()

        # Drain tokens
        limiter._tokens['general'] = 0.0
        limiter._last_refill['general'] = datetime.now() - timedelta(hours=1)

        # Should refill and not wait
        wait_time = limiter.acquire('/api/Order/place')

        # After 1 hour idle, should have refilled completely
        assert limiter._tokens['general'] > 100.0

    def test_negative_token_count_handled(self):
        """Test handling of negative token count edge case."""
        limiter = RateLimiter()

        # Artificially set negative tokens
        limiter._tokens['general'] = -5.0

        # Should still calculate wait time correctly
        wait_time = limiter._calculate_wait_time('general')
        assert wait_time >= 0.0
