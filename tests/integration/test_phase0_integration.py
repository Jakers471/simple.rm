"""
Integration Tests for Phase 0 Components

Tests end-to-end integration of TokenManager, TokenStorage, ErrorHandler,
RateLimiter, and SignalRManager working together.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import tempfile
from pathlib import Path

# Import all Phase 0 components
from src.api.token_manager import TokenManager, TokenState
from src.api.token_storage import TokenStorage
from src.api.error_handler import ErrorHandler, ServerError, RateLimitError
from src.api.rate_limiter import RateLimiter, RateLimitExceeded
from src.api.signalr_manager import SignalRManager, ConnectionState


class TestTokenRefreshDuringOperation:
    """Test token refresh integration during API operations"""

    @pytest.mark.asyncio
    async def test_token_refresh_with_storage_persistence(self):
        """Test that token refresh persists to storage"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "tokens.enc"

            # Create storage and token manager
            storage = TokenStorage(
                storage_path=storage_path,
                password="test_password"
            )

            token_manager = TokenManager(
                client_id="test_client",
                client_secret="test_secret",
                storage=storage,
                refresh_buffer_seconds=7200
            )

            # Mock authentication
            async def mock_auth():
                return {
                    "access_token": "new_token_123",
                    "refresh_token": "refresh_456",
                    "expires_in": 14400
                }

            with patch.object(token_manager, '_authenticate', mock_auth):
                token = await token_manager.get_valid_token()

            # Verify token was stored
            stored_data = storage.load()
            assert stored_data["access_token"] == "new_token_123"
            assert stored_data["refresh_token"] == "refresh_456"

    @pytest.mark.asyncio
    async def test_token_refresh_with_error_handling(self):
        """Test token refresh with error handler integration"""
        error_handler = ErrorHandler(max_retries=3)
        token_manager = TokenManager(
            client_id="test_client",
            client_secret="test_secret",
            error_handler=error_handler
        )

        attempt_count = 0

        async def flaky_auth():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ServerError(status=503, message="Service unavailable")
            return {
                "access_token": "token_after_retry",
                "expires_in": 3600
            }

        with patch.object(token_manager, '_authenticate', flaky_auth):
            # Should retry and eventually succeed
            token = await token_manager.get_valid_token()

        assert token == "token_after_retry"
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_token_refresh_with_rate_limiting(self):
        """Test token refresh respects rate limiting"""
        rate_limiter = RateLimiter(
            max_requests=2,
            time_window_seconds=1.0
        )

        token_manager = TokenManager(
            client_id="test_client",
            client_secret="test_secret",
            rate_limiter=rate_limiter
        )

        refresh_count = 0

        async def counting_auth():
            nonlocal refresh_count
            await rate_limiter.acquire()
            refresh_count += 1
            return {
                "access_token": f"token_{refresh_count}",
                "expires_in": 3600
            }

        with patch.object(token_manager, '_authenticate', counting_auth):
            # Make 3 token requests - 3rd should wait for rate limit
            tasks = [
                asyncio.create_task(token_manager.get_valid_token())
                for _ in range(3)
            ]

            start = asyncio.get_event_loop().time()
            tokens = await asyncio.gather(*tasks)
            elapsed = asyncio.get_event_loop().time() - start

            # Should have been rate limited
            assert elapsed > 0.5  # Had to wait for rate limit window

    @pytest.mark.asyncio
    async def test_concurrent_operations_during_refresh(self):
        """Test that concurrent API operations queue during token refresh"""
        token_manager = TokenManager(
            client_id="test_client",
            client_secret="test_secret"
        )

        async def slow_auth():
            await asyncio.sleep(0.5)  # Simulate slow auth
            return {
                "access_token": "refreshed_token",
                "expires_in": 3600
            }

        with patch.object(token_manager, '_authenticate', slow_auth):
            # Start 10 concurrent operations during refresh
            tasks = [
                asyncio.create_task(token_manager.get_valid_token())
                for _ in range(10)
            ]

            tokens = await asyncio.gather(*tasks)

            # All should get the same refreshed token
            assert len(set(tokens)) == 1
            assert tokens[0] == "refreshed_token"


class TestSignalRReconnection:
    """Test SignalR reconnection integration"""

    @pytest.mark.asyncio
    async def test_signalr_reconnect_with_token_refresh(self):
        """Test SignalR reconnection with token refresh"""
        token_manager = TokenManager(
            client_id="test_client",
            client_secret="test_secret"
        )

        signalr_manager = SignalRManager(
            hub_url="https://api.example.com/signalr",
            access_token_provider=token_manager.get_valid_token
        )

        token_refresh_count = 0

        async def counting_auth():
            nonlocal token_refresh_count
            token_refresh_count += 1
            return {
                "access_token": f"token_{token_refresh_count}",
                "expires_in": 3600
            }

        with patch.object(token_manager, '_authenticate', counting_auth):
            # Mock SignalR connection
            mock_connection = AsyncMock()
            with patch.object(signalr_manager, '_create_connection', return_value=mock_connection):
                # Initial connection
                await signalr_manager.connect()
                assert token_refresh_count == 1

                # Simulate disconnection and reconnection
                signalr_manager.state = ConnectionState.DISCONNECTED
                await signalr_manager.connect()

                # Should have refreshed token again
                assert token_refresh_count == 2

    @pytest.mark.asyncio
    async def test_signalr_resubscribe_after_reconnect(self):
        """Test SignalR resubscribes to channels after reconnection"""
        signalr_manager = SignalRManager(
            hub_url="https://api.example.com/signalr"
        )

        # Add subscriptions
        channels = ["orders", "positions", "trades"]
        for channel in channels:
            signalr_manager.add_subscription(channel)

        resubscribed = []

        async def track_subscribe(channel):
            resubscribed.append(channel)

        mock_connection = AsyncMock()
        signalr_manager._connection = mock_connection

        with patch.object(signalr_manager, '_subscribe_channel', track_subscribe):
            # Simulate reconnection
            await signalr_manager._resubscribe_all()

        # All channels should be resubscribed
        assert set(resubscribed) == set(channels)

    @pytest.mark.asyncio
    async def test_signalr_with_error_handler(self):
        """Test SignalR with error handler integration"""
        error_handler = ErrorHandler(max_retries=3)

        signalr_manager = SignalRManager(
            hub_url="https://api.example.com/signalr",
            error_handler=error_handler
        )

        connection_attempts = 0

        async def flaky_connection():
            nonlocal connection_attempts
            connection_attempts += 1
            if connection_attempts < 3:
                raise ServerError(status=503, message="Service unavailable")
            return AsyncMock()

        with patch.object(signalr_manager, '_create_connection', flaky_connection):
            # Should retry and eventually connect
            await signalr_manager.connect()

        assert connection_attempts == 3
        assert signalr_manager.state == ConnectionState.CONNECTED


class TestRateLimitEnforcement:
    """Test rate limit enforcement across components"""

    @pytest.mark.asyncio
    async def test_rate_limit_with_error_handler(self):
        """Test rate limit integration with error handler"""
        rate_limiter = RateLimiter(
            max_requests=5,
            time_window_seconds=1.0
        )

        error_handler = ErrorHandler()

        request_count = 0

        async def rate_limited_request():
            nonlocal request_count
            await rate_limiter.acquire()
            request_count += 1
            return "success"

        # Make 10 requests - some will be rate limited
        tasks = [
            asyncio.create_task(rate_limited_request())
            for _ in range(10)
        ]

        # Let some complete, some should be throttled
        await asyncio.sleep(2.0)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should eventually complete
        assert request_count == 10

    @pytest.mark.asyncio
    async def test_rate_limit_with_backoff(self):
        """Test rate limiting with exponential backoff"""
        rate_limiter = RateLimiter(
            max_requests=3,
            time_window_seconds=1.0,
            throttle=True
        )

        error_handler = ErrorHandler(
            base_backoff_seconds=0.1,
            max_retries=5
        )

        async def rate_limited_operation():
            # This will be rate limited
            await rate_limiter.acquire()

            # Simulate API call that might fail
            if await rate_limiter.is_allowed():
                return "success"
            else:
                raise RateLimitError(
                    status=429,
                    message="Rate limit exceeded",
                    retry_after=1
                )

        # Execute with retry
        result = await error_handler.execute_with_retry(rate_limited_operation)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_distributed_rate_limiting(self):
        """Test rate limiting across multiple components"""
        # Global rate limiter
        global_limiter = RateLimiter(
            max_requests=100,
            time_window_seconds=60
        )

        # Per-endpoint rate limiters
        order_limiter = RateLimiter(
            max_requests=10,
            time_window_seconds=60
        )

        position_limiter = RateLimiter(
            max_requests=20,
            time_window_seconds=60
        )

        order_count = 0
        position_count = 0

        async def order_request():
            nonlocal order_count
            await global_limiter.acquire()
            await order_limiter.acquire()
            order_count += 1

        async def position_request():
            nonlocal position_count
            await global_limiter.acquire()
            await position_limiter.acquire()
            position_count += 1

        # Make mixed requests
        tasks = []
        for i in range(30):
            if i % 2 == 0:
                tasks.append(asyncio.create_task(order_request()))
            else:
                tasks.append(asyncio.create_task(position_request()))

        await asyncio.sleep(2.0)
        await asyncio.gather(*tasks, return_exceptions=True)

        # Verify rate limits were enforced
        assert order_count <= 10  # Endpoint limit
        assert position_count <= 20  # Endpoint limit
        assert (order_count + position_count) <= 30  # Total attempted


class TestEndToEndResilience:
    """Test end-to-end resilience with all components"""

    @pytest.mark.asyncio
    async def test_complete_workflow_with_failures(self):
        """Test complete workflow with various failures"""
        # Set up all components
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = TokenStorage(
                storage_path=Path(tmpdir) / "tokens.enc",
                password="test_password"
            )

            error_handler = ErrorHandler(max_retries=3)

            rate_limiter = RateLimiter(
                max_requests=10,
                time_window_seconds=1.0
            )

            token_manager = TokenManager(
                client_id="test_client",
                client_secret="test_secret",
                storage=storage,
                error_handler=error_handler,
                rate_limiter=rate_limiter
            )

            signalr_manager = SignalRManager(
                hub_url="https://api.example.com/signalr",
                access_token_provider=token_manager.get_valid_token,
                error_handler=error_handler
            )

            # Simulate various failures
            auth_attempt = 0

            async def flaky_auth():
                nonlocal auth_attempt
                auth_attempt += 1

                # Fail first 2 attempts
                if auth_attempt <= 2:
                    raise ServerError(status=503, message="Service unavailable")

                return {
                    "access_token": "final_token",
                    "expires_in": 3600
                }

            connection_attempt = 0

            async def flaky_connection():
                nonlocal connection_attempt
                connection_attempt += 1

                # Fail first attempt
                if connection_attempt == 1:
                    raise ServerError(status=502, message="Bad gateway")

                return AsyncMock()

            with patch.object(token_manager, '_authenticate', flaky_auth):
                with patch.object(signalr_manager, '_create_connection', flaky_connection):
                    # Get token (should retry auth)
                    token = await token_manager.get_valid_token()
                    assert token == "final_token"
                    assert auth_attempt == 3

                    # Connect SignalR (should retry connection)
                    await signalr_manager.connect()
                    assert connection_attempt == 2
                    assert signalr_manager.state == ConnectionState.CONNECTED

                    # Verify token was persisted
                    stored = storage.load()
                    assert stored["access_token"] == "final_token"

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation when components fail"""
        # Token manager without storage (memory-only fallback)
        token_manager = TokenManager(
            client_id="test_client",
            client_secret="test_secret",
            storage=None  # No storage
        )

        async def mock_auth():
            return {
                "access_token": "memory_token",
                "expires_in": 3600
            }

        with patch.object(token_manager, '_authenticate', mock_auth):
            # Should still work with memory-only tokens
            token = await token_manager.get_valid_token()
            assert token == "memory_token"

    @pytest.mark.asyncio
    async def test_recovery_from_cascade_failure(self):
        """Test recovery from cascading failures"""
        error_handler = ErrorHandler(max_retries=5)

        rate_limiter = RateLimiter(
            max_requests=5,
            time_window_seconds=1.0
        )

        operation_count = 0
        failure_count = 0

        async def unstable_operation():
            nonlocal operation_count, failure_count
            operation_count += 1

            # Respect rate limit
            await rate_limiter.acquire()

            # Fail sometimes
            if operation_count % 3 == 0:
                failure_count += 1
                raise ServerError(status=500, message="Server error")

            return "success"

        # Execute multiple operations with retry
        results = []
        for _ in range(15):
            try:
                result = await error_handler.execute_with_retry(unstable_operation)
                results.append(result)
            except:
                pass

        # Should have recovered from failures
        assert len(results) > 0
        assert failure_count > 0  # Some failures occurred
        assert len(results) < 15  # But not all succeeded due to rate limit


class TestComponentInteroperability:
    """Test interoperability between Phase 0 components"""

    @pytest.mark.asyncio
    async def test_token_manager_with_all_components(self):
        """Test token manager integrates with all other components"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create all components
            storage = TokenStorage(
                storage_path=Path(tmpdir) / "tokens.enc",
                password="test_password"
            )

            error_handler = ErrorHandler(max_retries=3)

            rate_limiter = RateLimiter(
                max_requests=10,
                time_window_seconds=1.0
            )

            token_manager = TokenManager(
                client_id="test_client",
                client_secret="test_secret",
                storage=storage,
                error_handler=error_handler,
                rate_limiter=rate_limiter
            )

            # Verify all components are integrated
            assert token_manager.storage == storage
            assert token_manager.error_handler == error_handler
            assert token_manager.rate_limiter == rate_limiter

            # Test workflow
            async def mock_auth():
                return {
                    "access_token": "integrated_token",
                    "expires_in": 3600
                }

            with patch.object(token_manager, '_authenticate', mock_auth):
                token = await token_manager.get_valid_token()

            # Verify persistence
            stored = storage.load()
            assert stored["access_token"] == "integrated_token"

    @pytest.mark.asyncio
    async def test_signalr_with_all_components(self):
        """Test SignalR manager integrates with all other components"""
        error_handler = ErrorHandler()

        async def token_provider():
            return "signalr_token"

        signalr_manager = SignalRManager(
            hub_url="https://api.example.com/signalr",
            access_token_provider=token_provider,
            error_handler=error_handler
        )

        # Verify integration
        assert signalr_manager.access_token_provider == token_provider
        assert signalr_manager.error_handler == error_handler

        # Test functionality
        mock_connection = AsyncMock()
        with patch.object(signalr_manager, '_create_connection', return_value=mock_connection):
            await signalr_manager.connect()

        assert signalr_manager.state == ConnectionState.CONNECTED
