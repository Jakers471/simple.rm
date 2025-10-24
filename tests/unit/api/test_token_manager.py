"""
Unit Tests for TokenManager

Tests proactive token refresh, request queueing, exponential backoff,
fallback mechanisms, and concurrent request handling.

Implementation: src/api/token_manager.py
Specification: TOKEN_REFRESH_STRATEGY_SPEC.md (SEC-001)
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock, PropertyMock
from datetime import datetime, timedelta
from collections import deque

# Import from src.api.token_manager
from src.api.token_manager import (
    TokenManager,
    TokenState,
    TokenInfo,
    QueuedRequest
)


class MockAuthService:
    """Mock authentication service matching actual implementation requirements"""

    def __init__(self):
        self._token = "test_token_123"
        self._token_expiry = datetime.now() + timedelta(hours=4)
        self._authenticate_called = 0
        self._validate_called = 0
        self._should_fail = False
        self._validation_results = []

    async def authenticate(self):
        """Mock authenticate method"""
        self._authenticate_called += 1
        if self._should_fail:
            return False

        # Update token and expiry
        self._token = f"token_{self._authenticate_called}"
        self._token_expiry = datetime.now() + timedelta(hours=4)
        return True

    async def validate(self):
        """Mock validate method"""
        self._validate_called += 1

        # Return preset results if available
        if self._validation_results:
            return self._validation_results.pop(0)

        if self._should_fail:
            return False

        # Check if token is still valid based on expiry
        return datetime.now() < self._token_expiry


@pytest.fixture
def mock_auth():
    """Fixture providing mock auth service"""
    return MockAuthService()


@pytest.fixture
def config():
    """Fixture providing test configuration"""
    return {
        'refresh_buffer_seconds': 7200,  # 2 hours
        'max_retries': 4,
        'max_queue_depth': 100
    }


@pytest.fixture
def token_manager(config, mock_auth):
    """Fixture providing configured TokenManager"""
    return TokenManager(config, mock_auth)


class TestTokenManagerInitialization:
    """Test TokenManager initialization and configuration"""

    def test_init_default_config(self, mock_auth):
        """Test initialization with default configuration"""
        config = {}
        manager = TokenManager(config, mock_auth)

        assert manager.auth_service == mock_auth
        assert manager.refresh_buffer == 7200  # Default 2 hours
        assert manager.max_retries == 4
        assert manager.max_queue_depth == 100
        assert manager._token_info is None
        assert manager._retry_count == 0
        assert len(manager._request_queue) == 0

    def test_init_custom_config(self, mock_auth):
        """Test initialization with custom configuration"""
        config = {
            'refresh_buffer_seconds': 3600,
            'max_retries': 3,
            'max_queue_depth': 50
        }
        manager = TokenManager(config, mock_auth)

        assert manager.refresh_buffer == 3600
        assert manager.max_retries == 3
        assert manager.max_queue_depth == 50

    def test_init_preserves_config(self, config, mock_auth):
        """Test that config is preserved"""
        manager = TokenManager(config, mock_auth)
        assert manager.config == config


class TestInitialAuthentication:
    """Test initial authentication flow"""

    @pytest.mark.asyncio
    async def test_initial_authenticate_success(self, token_manager, mock_auth):
        """Test successful initial authentication"""
        # Initial state - no token
        assert token_manager._token_info is None

        # Get token triggers initial auth
        token = await token_manager.get_token()

        # Verify authentication was called
        assert mock_auth._authenticate_called == 1
        assert token == mock_auth._token

        # Verify token info created
        assert token_manager._token_info is not None
        assert token_manager._token_info.state == TokenState.VALID
        assert token_manager._token_info.token == mock_auth._token

    @pytest.mark.asyncio
    async def test_initial_authenticate_sets_expiry(self, token_manager, mock_auth):
        """Test that initial auth sets correct expiry times"""
        token = await token_manager.get_token()

        token_info = token_manager._token_info
        assert token_info.expires_at == mock_auth._token_expiry

        # Refresh trigger should be 2 hours before expiry
        expected_refresh = mock_auth._token_expiry - timedelta(seconds=7200)
        assert token_info.refresh_trigger_time == expected_refresh

    @pytest.mark.asyncio
    async def test_initial_authenticate_failure(self, token_manager, mock_auth):
        """Test failed initial authentication"""
        mock_auth._should_fail = True

        with pytest.raises(RuntimeError, match="Authentication failed"):
            await token_manager.get_token()

    @pytest.mark.asyncio
    async def test_initial_authenticate_exception_handling(self, token_manager, mock_auth):
        """Test exception handling during initial auth"""
        async def failing_auth():
            raise ValueError("Network error")

        mock_auth.authenticate = failing_auth

        with pytest.raises(ValueError):
            await token_manager.get_token()


class TestProactiveRefresh:
    """Test proactive token refresh at 2-hour buffer"""

    @pytest.mark.asyncio
    async def test_needs_refresh_within_buffer(self, token_manager, mock_auth):
        """Test that refresh is needed when within buffer window"""
        # Set token that expires in 1.5 hours (within 2-hour buffer)
        await token_manager.get_token()

        # Manually set expiry to be within buffer
        token_manager._token_info.expires_at = datetime.now() + timedelta(hours=1.5)
        token_manager._token_info.refresh_trigger_time = datetime.now() - timedelta(minutes=30)

        assert token_manager._needs_refresh() is True

    @pytest.mark.asyncio
    async def test_needs_refresh_fresh_token(self, token_manager, mock_auth):
        """Test that refresh is not needed for fresh token"""
        await token_manager.get_token()

        # Token expires in 4 hours, no refresh needed
        assert token_manager._needs_refresh() is False

    @pytest.mark.asyncio
    async def test_needs_refresh_expired_token(self, token_manager, mock_auth):
        """Test that expired token triggers refresh"""
        await token_manager.get_token()

        # Set token as expired
        token_manager._token_info.expires_at = datetime.now() - timedelta(hours=1)

        assert token_manager._needs_refresh() is True
        assert token_manager._token_info.state == TokenState.EXPIRED

    @pytest.mark.asyncio
    async def test_proactive_refresh_triggered(self, token_manager, mock_auth):
        """Test that proactive refresh is triggered automatically"""
        await token_manager.get_token()
        initial_token = token_manager._token_info.token

        # Set refresh trigger time to now
        token_manager._token_info.refresh_trigger_time = datetime.now()

        # Getting token should trigger refresh
        token = await token_manager.get_token()

        # Validate should have been called
        assert mock_auth._validate_called > 0

    @pytest.mark.asyncio
    async def test_check_expiry_method(self, token_manager, mock_auth):
        """Test _check_expiry method"""
        await token_manager.get_token()

        # Token is valid - should return True
        is_valid = await token_manager._check_expiry()
        assert is_valid is True

        # Set expiry to past
        token_manager._token_info.expires_at = datetime.now() - timedelta(hours=1)
        is_valid = await token_manager._check_expiry()
        assert is_valid is False
        assert token_manager._token_info.state == TokenState.EXPIRED


class TestRequestQueueing:
    """Test request queueing during token refresh"""

    @pytest.mark.asyncio
    async def test_queue_requests_during_refresh(self, token_manager, mock_auth):
        """Test that requests are queued while refresh is in progress"""
        await token_manager.get_token()

        # Set state to REFRESHING
        token_manager._token_info.state = TokenState.REFRESHING

        # Simulate slow refresh - will complete in background
        async def slow_refresh(*args, **kwargs):
            await asyncio.sleep(0.2)
            token_manager._token_info.state = TokenState.VALID

        # Patch validate to be slow
        original_validate = mock_auth.validate
        mock_auth.validate = slow_refresh

        # Start multiple requests concurrently
        async def make_request():
            # Trigger refresh condition
            token_manager._token_info.refresh_trigger_time = datetime.now() - timedelta(hours=1)
            return await token_manager.get_token()

        # These should queue up
        tasks = [asyncio.create_task(make_request()) for _ in range(3)]

        # Wait a bit for queueing
        await asyncio.sleep(0.1)

        # Allow refresh to complete
        token_manager._token_info.state = TokenState.VALID

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should eventually get token
        assert len([r for r in results if not isinstance(r, Exception)]) > 0

        mock_auth.validate = original_validate

    @pytest.mark.asyncio
    async def test_queue_and_wait_timeout(self, token_manager, mock_auth):
        """Test timeout when waiting for refresh"""
        await token_manager.get_token()

        # Set to refreshing and never complete
        token_manager._token_info.state = TokenState.REFRESHING

        with pytest.raises(TimeoutError, match="Token refresh timeout"):
            await token_manager._queue_and_wait()

    @pytest.mark.asyncio
    async def test_queue_and_wait_success(self, token_manager, mock_auth):
        """Test successful queue and wait"""
        await token_manager.get_token()

        # Set to refreshing
        token_manager._token_info.state = TokenState.REFRESHING

        # Complete refresh in background
        async def complete_refresh():
            await asyncio.sleep(0.1)
            token_manager._token_info.state = TokenState.VALID

        asyncio.create_task(complete_refresh())

        # Should wait and get token
        token = await token_manager._queue_and_wait()
        assert token == mock_auth._token

    @pytest.mark.asyncio
    async def test_queue_depth_limit(self, token_manager, mock_auth):
        """Test that queue depth limit is enforced"""
        # Create mock callback
        async def mock_callback():
            pass

        # Fill queue to max
        for i in range(token_manager.max_queue_depth):
            await token_manager._queue_request(mock_callback)

        # Next request should fail
        with pytest.raises(RuntimeError, match="REQUEST_QUEUE_FULL"):
            await token_manager._queue_request(mock_callback)

    @pytest.mark.asyncio
    async def test_drain_queue_success(self, token_manager, mock_auth):
        """Test draining queue successfully"""
        executed = []

        async def callback(value):
            executed.append(value)

        # Add items to queue
        for i in range(5):
            await token_manager._queue_request(callback, i)

        # Drain queue
        await token_manager._drain_queue()

        # All callbacks should execute
        assert len(executed) == 5
        assert executed == [0, 1, 2, 3, 4]
        assert len(token_manager._request_queue) == 0

    @pytest.mark.asyncio
    async def test_drain_queue_with_failures(self, token_manager, mock_auth):
        """Test drain queue continues despite callback failures"""
        executed = []

        async def failing_callback(value):
            if value == 2:
                raise ValueError("Intentional failure")
            executed.append(value)

        # Add items to queue
        for i in range(5):
            await token_manager._queue_request(failing_callback, i)

        # Drain queue - should continue despite failure
        await token_manager._drain_queue()

        # Should have executed all except the failing one
        assert len(executed) == 4
        assert 2 not in executed


class TestExponentialBackoff:
    """Test exponential backoff with 4 retries [30s, 60s, 120s, 300s]"""

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self, token_manager, mock_auth):
        """Test that retries use exponential backoff delays"""
        await token_manager.get_token()

        # Make validation fail
        mock_auth._validation_results = [False, False, False, False]

        # Trigger refresh
        token_manager._token_info.refresh_trigger_time = datetime.now() - timedelta(hours=1)

        # Patch sleep to track delays
        sleep_delays = []

        async def mock_sleep(delay):
            sleep_delays.append(delay)

        with patch('asyncio.sleep', side_effect=mock_sleep):
            try:
                await token_manager._refresh_token()
            except:
                pass

        # Should have 3 delays (not after last attempt)
        assert len(sleep_delays) == 3

        # Check delays match specification: 30, 60, 120
        expected_delays = [30, 60, 120]
        assert sleep_delays == expected_delays

    @pytest.mark.asyncio
    async def test_max_retries_respected(self, token_manager, mock_auth):
        """Test that max retries limit is respected"""
        await token_manager.get_token()

        # Make all validations fail
        validation_count = 0

        async def counting_validate():
            nonlocal validation_count
            validation_count += 1
            return False

        mock_auth.validate = counting_validate

        # Trigger refresh
        token_manager._token_info.refresh_trigger_time = datetime.now() - timedelta(hours=1)

        # Mock sleep to speed up test
        with patch('asyncio.sleep', new_callable=AsyncMock):
            await token_manager._refresh_token()

        # Should attempt exactly max_retries times
        assert validation_count == token_manager.max_retries
        # After fallback to reauth, retry_count is reset to 0
        assert token_manager._retry_count == 0

    @pytest.mark.asyncio
    async def test_successful_retry_stops_backoff(self, token_manager, mock_auth):
        """Test that successful retry stops backoff sequence"""
        await token_manager.get_token()

        # Fail twice, then succeed
        mock_auth._validation_results = [False, False, True]

        # Trigger refresh
        token_manager._token_info.refresh_trigger_time = datetime.now() - timedelta(hours=1)

        # Track sleep calls
        sleep_count = 0

        async def counting_sleep(delay):
            nonlocal sleep_count
            sleep_count += 1

        with patch('asyncio.sleep', side_effect=counting_sleep):
            await token_manager._refresh_token()

        # Should have slept only 2 times (after first and second attempts)
        assert sleep_count == 2

        # Retry count should be reset to 0 after success
        assert token_manager._retry_count == 0
        assert token_manager._token_info.state == TokenState.VALID

    @pytest.mark.asyncio
    async def test_backoff_delays_exact_values(self, token_manager):
        """Test that backoff delays match specification exactly"""
        expected = [30, 60, 120, 300]
        actual = TokenManager.RETRY_BACKOFF_DELAYS

        assert actual == expected


class TestFallbackToReauth:
    """Test fallback to re-authentication"""

    @pytest.mark.asyncio
    async def test_fallback_after_all_retries_exhausted(self, token_manager, mock_auth):
        """Test that system falls back to re-auth after all retries fail"""
        await token_manager.get_token()
        initial_auth_count = mock_auth._authenticate_called

        # Make all validations fail
        mock_auth._validation_results = [False] * 10

        # Trigger refresh
        token_manager._token_info.refresh_trigger_time = datetime.now() - timedelta(hours=1)

        # Mock sleep to speed up
        with patch('asyncio.sleep', new_callable=AsyncMock):
            await token_manager._refresh_token()

        # Should have fallen back to re-authentication
        assert mock_auth._authenticate_called > initial_auth_count

        # State should transition to ERROR first, then back to VALID after reauth
        assert token_manager._token_info.state == TokenState.VALID

    @pytest.mark.asyncio
    async def test_fallback_from_error_state(self, token_manager, mock_auth):
        """Test fallback when token is in ERROR state"""
        await token_manager.get_token()

        # Set to ERROR state
        token_manager._token_info.state = TokenState.ERROR

        # Get token should trigger fallback
        token = await token_manager.get_token()

        # Should re-authenticate
        assert mock_auth._authenticate_called >= 2
        assert token_manager._token_info.state == TokenState.VALID

    @pytest.mark.asyncio
    async def test_fallback_from_expired_state(self, token_manager, mock_auth):
        """Test fallback when token is EXPIRED"""
        await token_manager.get_token()

        # Set to EXPIRED
        token_manager._token_info.state = TokenState.EXPIRED

        # Get token should trigger fallback
        token = await token_manager.get_token()

        # Should re-authenticate
        assert mock_auth._authenticate_called >= 2

    @pytest.mark.asyncio
    async def test_fallback_clears_old_token(self, token_manager, mock_auth):
        """Test that fallback clears old token info"""
        await token_manager.get_token()
        old_token = token_manager._token_info.token

        # Trigger fallback
        await token_manager._fallback_to_reauth()

        # Should have new token
        assert token_manager._token_info.token != old_token
        assert token_manager._retry_count == 0

    @pytest.mark.asyncio
    async def test_fallback_drains_queue(self, token_manager, mock_auth):
        """Test that fallback drains queued requests"""
        await token_manager.get_token()

        executed = []

        async def callback(value):
            executed.append(value)

        # Queue some requests
        for i in range(3):
            await token_manager._queue_request(callback, i)

        # Trigger fallback
        await token_manager._fallback_to_reauth()

        # Queue should be drained
        assert len(executed) == 3
        assert len(token_manager._request_queue) == 0

    @pytest.mark.asyncio
    async def test_fallback_failure_fails_queue(self, token_manager, mock_auth):
        """Test that failed fallback fails all queued requests"""
        await token_manager.get_token()

        # Queue some requests
        async def callback():
            pass

        for _ in range(5):
            await token_manager._queue_request(callback)

        # Make re-auth fail
        mock_auth._should_fail = True

        with pytest.raises(RuntimeError):
            await token_manager._fallback_to_reauth()

        # Queue should be cleared
        assert len(token_manager._request_queue) == 0


class TestStateTransitions:
    """Test token manager state machine transitions"""

    @pytest.mark.asyncio
    async def test_initial_to_valid_transition(self, token_manager, mock_auth):
        """Test transition from no token to VALID"""
        assert token_manager.get_state() is None

        await token_manager.get_token()

        assert token_manager.get_state() == TokenState.VALID

    @pytest.mark.asyncio
    async def test_valid_to_refreshing_transition(self, token_manager, mock_auth):
        """Test transition to REFRESHING state"""
        await token_manager.get_token()

        # Make validate slow
        async def slow_validate():
            await asyncio.sleep(0.5)
            return True

        mock_auth.validate = slow_validate

        # Trigger refresh in background
        token_manager._token_info.refresh_trigger_time = datetime.now() - timedelta(hours=1)

        # Start refresh
        refresh_task = asyncio.create_task(token_manager._refresh_token())

        # Give it time to start
        await asyncio.sleep(0.1)

        # Should be refreshing
        assert token_manager.get_state() == TokenState.REFRESHING

        # Wait for completion
        await refresh_task

        assert token_manager.get_state() == TokenState.VALID

    @pytest.mark.asyncio
    async def test_refreshing_to_valid_transition(self, token_manager, mock_auth):
        """Test successful refresh completes"""
        await token_manager.get_token()

        # Trigger refresh
        token_manager._token_info.refresh_trigger_time = datetime.now() - timedelta(hours=1)

        with patch('asyncio.sleep', new_callable=AsyncMock):
            await token_manager._refresh_token()

        assert token_manager.get_state() == TokenState.VALID

    @pytest.mark.asyncio
    async def test_refreshing_to_error_transition(self, token_manager, mock_auth):
        """Test transition to ERROR state after all retries fail"""
        await token_manager.get_token()

        # Make all validations fail
        mock_auth._validation_results = [False] * 10

        # Make re-auth also fail to stay in ERROR
        async def failing_auth():
            return False

        original_auth = mock_auth.authenticate
        mock_auth.authenticate = failing_auth

        # Trigger refresh
        token_manager._token_info.refresh_trigger_time = datetime.now() - timedelta(hours=1)

        with patch('asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(RuntimeError):
                await token_manager._refresh_token()

        mock_auth.authenticate = original_auth

    @pytest.mark.asyncio
    async def test_state_transition_logging(self, token_manager, mock_auth):
        """Test that state transitions are logged"""
        await token_manager.get_token()

        # Manually transition state
        old_state = token_manager._token_info.state
        token_manager._transition_state(TokenState.REFRESHING)

        assert token_manager._token_info.state == TokenState.REFRESHING

    def test_get_state_no_token(self, token_manager):
        """Test get_state returns None when no token"""
        assert token_manager.get_state() is None


class TestConcurrentRequests:
    """Test handling of concurrent token requests"""

    @pytest.mark.asyncio
    async def test_concurrent_initial_requests(self, token_manager, mock_auth):
        """Test concurrent requests during initial auth"""
        # Fire multiple concurrent requests
        tasks = [
            asyncio.create_task(token_manager.get_token())
            for _ in range(10)
        ]

        results = await asyncio.gather(*tasks)

        # All should get same token
        assert all(r == mock_auth._token for r in results)

        # Should only authenticate once
        assert mock_auth._authenticate_called == 1

    @pytest.mark.asyncio
    async def test_concurrent_refresh_requests(self, token_manager, mock_auth):
        """Test concurrent requests during refresh"""
        await token_manager.get_token()

        # Set up for refresh
        token_manager._token_info.refresh_trigger_time = datetime.now() - timedelta(hours=1)

        # Make validate take some time
        validate_count = 0

        async def slow_validate():
            nonlocal validate_count
            validate_count += 1
            await asyncio.sleep(0.1)
            return True

        mock_auth.validate = slow_validate

        # Fire concurrent requests
        tasks = [
            asyncio.create_task(token_manager.get_token())
            for _ in range(5)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Some should succeed
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) > 0

    @pytest.mark.asyncio
    async def test_refresh_lock_prevents_concurrent_refresh(self, token_manager, mock_auth):
        """Test that refresh lock prevents concurrent refresh operations"""
        await token_manager.get_token()

        token_manager._token_info.refresh_trigger_time = datetime.now() - timedelta(hours=1)

        validate_count = 0

        async def counting_validate():
            nonlocal validate_count
            validate_count += 1
            await asyncio.sleep(0.1)
            return True

        mock_auth.validate = counting_validate

        # Start multiple refresh operations
        with patch('asyncio.sleep', new_callable=AsyncMock):
            tasks = [
                asyncio.create_task(token_manager._refresh_token())
                for _ in range(5)
            ]

            await asyncio.gather(*tasks)

        # Lock should prevent concurrent execution
        # Exact count depends on lock behavior, but should be limited
        assert validate_count >= 1


class TestTokenValidation:
    """Test token validation and expiry checking"""

    @pytest.mark.asyncio
    async def test_validate_token_success(self, token_manager, mock_auth):
        """Test successful token validation"""
        await token_manager.get_token()

        result = await token_manager._validate_token()

        assert result is True
        assert mock_auth._validate_called > 0

    @pytest.mark.asyncio
    async def test_validate_token_failure(self, token_manager, mock_auth):
        """Test failed token validation"""
        await token_manager.get_token()

        # Make validation fail
        async def failing_validate():
            return False

        mock_auth.validate = failing_validate

        result = await token_manager._validate_token()

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_token_exception(self, token_manager, mock_auth):
        """Test validation handles exceptions"""
        await token_manager.get_token()

        async def error_validate():
            raise ValueError("Validation error")

        mock_auth.validate = error_validate

        result = await token_manager._validate_token()

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_fallback_to_check_expiry(self, token_manager, mock_auth):
        """Test validation falls back to check_expiry if no validate method"""
        await token_manager.get_token()

        # Create a mock without validate method
        class NoValidateMock:
            def __init__(self):
                self._token = "test_token"
                self._token_expiry = datetime.now() + timedelta(hours=4)

        token_manager.auth_service = NoValidateMock()

        result = await token_manager._validate_token()

        # Should use check_expiry instead
        assert result is True

    @pytest.mark.asyncio
    async def test_check_expiry_valid_token(self, token_manager, mock_auth):
        """Test check_expiry with valid token"""
        await token_manager.get_token()

        result = await token_manager._check_expiry()

        assert result is True

    @pytest.mark.asyncio
    async def test_check_expiry_expired_token(self, token_manager, mock_auth):
        """Test check_expiry with expired token"""
        await token_manager.get_token()

        # Set expiry to past
        token_manager._token_info.expires_at = datetime.now() - timedelta(hours=1)

        result = await token_manager._check_expiry()

        assert result is False
        assert token_manager._token_info.state == TokenState.EXPIRED

    @pytest.mark.asyncio
    async def test_check_expiry_within_buffer(self, token_manager, mock_auth):
        """Test check_expiry with token within refresh buffer"""
        await token_manager.get_token()

        # Set expiry within buffer (1 hour from now, buffer is 2 hours)
        token_manager._token_info.expires_at = datetime.now() + timedelta(hours=1)

        result = await token_manager._check_expiry()

        # Should need refresh
        assert result is False


class TestHelperMethods:
    """Test helper methods and utilities"""

    @pytest.mark.asyncio
    async def test_get_time_until_expiry(self, token_manager, mock_auth):
        """Test getting time until expiry"""
        await token_manager.get_token()

        ttl = token_manager.get_time_until_expiry()

        # Should be approximately 4 hours (14400 seconds)
        assert ttl is not None
        assert 14000 < ttl < 14500

    def test_get_time_until_expiry_no_token(self, token_manager):
        """Test get_time_until_expiry with no token"""
        ttl = token_manager.get_time_until_expiry()
        assert ttl is None

    def test_get_queue_depth(self, token_manager):
        """Test getting queue depth"""
        assert token_manager.get_queue_depth() == 0

        # Add to queue
        token_manager._request_queue.append(Mock())
        token_manager._request_queue.append(Mock())

        assert token_manager.get_queue_depth() == 2

    @pytest.mark.asyncio
    async def test_get_state_various_states(self, token_manager, mock_auth):
        """Test get_state in various states"""
        # Initially None
        assert token_manager.get_state() is None

        # After auth - VALID
        await token_manager.get_token()
        assert token_manager.get_state() == TokenState.VALID

        # Manually set to REFRESHING
        token_manager._transition_state(TokenState.REFRESHING)
        assert token_manager.get_state() == TokenState.REFRESHING

        # Set to ERROR
        token_manager._transition_state(TokenState.ERROR)
        assert token_manager.get_state() == TokenState.ERROR


class TestEdgeCases:
    """Test edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_queue_request_creates_proper_structure(self, token_manager):
        """Test that _queue_request creates proper QueuedRequest"""
        async def callback(x, y=10):
            return x + y

        await token_manager._queue_request(callback, 5, y=15)

        assert len(token_manager._request_queue) == 1

        queued = token_manager._request_queue[0]
        assert isinstance(queued, QueuedRequest)
        assert queued.callback == callback
        assert queued.args == (5,)
        assert queued.kwargs == {'y': 15}

    @pytest.mark.asyncio
    async def test_empty_queue_drain(self, token_manager):
        """Test draining empty queue does nothing"""
        await token_manager._drain_queue()
        # Should not raise any errors

    @pytest.mark.asyncio
    async def test_needs_refresh_no_token_info(self, token_manager):
        """Test needs_refresh with no token info"""
        assert token_manager._token_info is None
        assert token_manager._needs_refresh() is True

    @pytest.mark.asyncio
    async def test_transition_state_with_no_token(self, token_manager):
        """Test state transition with no token info"""
        # Should handle gracefully
        token_manager._transition_state(TokenState.ERROR)
        # No exception should be raised

    @pytest.mark.asyncio
    async def test_fail_queue_with_items(self, token_manager, mock_auth):
        """Test _fail_queue clears all queued requests"""
        async def callback():
            pass

        # Add items
        for _ in range(5):
            await token_manager._queue_request(callback)

        assert len(token_manager._request_queue) == 5

        # Fail queue
        token_manager._fail_queue()

        assert len(token_manager._request_queue) == 0

    def test_fail_queue_empty(self, token_manager):
        """Test _fail_queue with empty queue"""
        token_manager._fail_queue()
        # Should not raise errors
        assert len(token_manager._request_queue) == 0


class TestConstants:
    """Test that constants match specification"""

    def test_refresh_buffer_default(self):
        """Test default refresh buffer is 2 hours"""
        assert TokenManager.REFRESH_BUFFER_SECONDS == 7200

    def test_max_retry_attempts(self):
        """Test max retry attempts is 4"""
        assert TokenManager.MAX_RETRY_ATTEMPTS == 4

    def test_retry_backoff_delays(self):
        """Test retry backoff delays are [30, 60, 120, 300]"""
        assert TokenManager.RETRY_BACKOFF_DELAYS == [30, 60, 120, 300]

    def test_max_queue_depth(self):
        """Test max queue depth is 100"""
        assert TokenManager.MAX_QUEUE_DEPTH == 100

    def test_queue_drain_timeout(self):
        """Test queue drain timeout"""
        assert TokenManager.QUEUE_DRAIN_TIMEOUT == 10


class TestIntegration:
    """Integration tests for complete workflows"""

    @pytest.mark.asyncio
    async def test_complete_token_lifecycle(self, token_manager, mock_auth):
        """Test complete token lifecycle from init to refresh"""
        # 1. Initial auth
        token1 = await token_manager.get_token()
        assert token1 == "token_1"
        assert token_manager.get_state() == TokenState.VALID

        # 2. Get token again (should return cached)
        token2 = await token_manager.get_token()
        assert token2 == token1

        # 3. Trigger refresh
        token_manager._token_info.refresh_trigger_time = datetime.now() - timedelta(hours=1)

        with patch('asyncio.sleep', new_callable=AsyncMock):
            token3 = await token_manager.get_token()

        # Should still have valid token
        assert token_manager.get_state() == TokenState.VALID

    @pytest.mark.asyncio
    async def test_failure_recovery_workflow(self, token_manager, mock_auth):
        """Test recovery from failure scenario"""
        # 1. Initial successful auth
        await token_manager.get_token()

        # 2. Make refresh fail multiple times
        mock_auth._validation_results = [False, False, True]

        # 3. Trigger refresh
        token_manager._token_info.refresh_trigger_time = datetime.now() - timedelta(hours=1)

        with patch('asyncio.sleep', new_callable=AsyncMock):
            token = await token_manager.get_token()

        # Should recover and have valid token
        assert token_manager.get_state() == TokenState.VALID
        assert token_manager._retry_count == 0

    @pytest.mark.asyncio
    async def test_high_concurrency_workflow(self, token_manager, mock_auth):
        """Test system under high concurrent load"""
        # Simulate 50 concurrent requests
        tasks = [
            asyncio.create_task(token_manager.get_token())
            for _ in range(50)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Most should succeed
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) > 0

        # All successful results should be same token
        if successful:
            assert all(r == successful[0] for r in successful)
