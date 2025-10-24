"""
Token Manager - Proactive Token Refresh with State Machine

Implements:
- Token lifecycle state machine (INITIAL, VALID, REFRESHING, ERROR, EXPIRED)
- Proactive token refresh (2 hours before expiry)
- Request queuing during refresh
- Exponential backoff retry [30s, 60s, 120s, 300s]
- Fallback to re-authentication after failures
- Thread-safe operations with asyncio.Lock

Specification: TOKEN_REFRESH_STRATEGY_SPEC.md (SEC-001)
Test coverage: tests/unit/api/test_token_manager.py
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any, Callable
from collections import deque

logger = logging.getLogger(__name__)


class TokenState(Enum):
    """Token lifecycle states"""
    INITIAL = "initial"          # No token yet
    VALID = "valid"              # Token is valid and usable
    REFRESHING = "refreshing"    # Token refresh in progress
    ERROR = "error"              # Refresh failed, attempting recovery
    EXPIRED = "expired"          # Token expired, requires re-auth


@dataclass
class TokenInfo:
    """Token metadata and lifecycle information"""
    token: str
    issued_at: datetime
    expires_at: datetime
    refresh_trigger_time: datetime
    state: TokenState


@dataclass
class QueuedRequest:
    """Queued API request during token refresh"""
    request_id: str
    timestamp: datetime
    callback: Callable
    args: tuple
    kwargs: dict


class TokenManager:
    """
    Manages authentication token lifecycle with proactive refresh.

    Features:
    - Proactive refresh 2 hours before expiry
    - State machine for token lifecycle
    - Request queuing during refresh
    - Exponential backoff retry
    - Thread-safe operations
    """

    # Configuration constants
    REFRESH_BUFFER_SECONDS = 7200  # 2 hours before expiry
    MAX_RETRY_ATTEMPTS = 4
    RETRY_BACKOFF_DELAYS = [30, 60, 120, 300]  # seconds: 30s, 1m, 2m, 5m
    MAX_QUEUE_DEPTH = 100
    QUEUE_DRAIN_TIMEOUT = 10  # seconds

    def __init__(self, config: Dict[str, Any], auth_service: Any):
        """
        Initialize TokenManager.

        Args:
            config: Configuration dictionary with optional overrides
            auth_service: Authentication service with authenticate() and validate() methods
        """
        self.config = config
        self.auth_service = auth_service

        # Token state
        self._token_info: Optional[TokenInfo] = None
        self._refresh_lock = asyncio.Lock()
        self._request_queue: deque[QueuedRequest] = deque()
        self._retry_count = 0

        # Override defaults with config if provided
        self.refresh_buffer = config.get('refresh_buffer_seconds', self.REFRESH_BUFFER_SECONDS)
        self.max_retries = config.get('max_retries', self.MAX_RETRY_ATTEMPTS)
        self.max_queue_depth = config.get('max_queue_depth', self.MAX_QUEUE_DEPTH)

        logger.info(
            f"TokenManager initialized: refresh_buffer={self.refresh_buffer}s, "
            f"max_retries={self.max_retries}, max_queue_depth={self.max_queue_depth}"
        )

    async def get_token(self) -> str:
        """
        Get valid authentication token.

        Handles:
        - Token expiry checking
        - Proactive refresh triggering
        - Request queuing during refresh
        - State transitions

        Returns:
            Valid authentication token

        Raises:
            AuthenticationError: If token cannot be obtained
        """
        # Check if we need initial authentication
        if self._token_info is None or self._token_info.state == TokenState.INITIAL:
            await self._initial_authenticate()
            return self._token_info.token

        # Check if token needs refresh
        if self._needs_refresh():
            logger.info("Token refresh needed, current state: %s", self._token_info.state)

            # If already refreshing, queue this request
            if self._token_info.state == TokenState.REFRESHING:
                logger.debug("Refresh already in progress, queueing request")
                return await self._queue_and_wait()

            # Start refresh process
            await self._refresh_token()

        # Check token is still valid after potential refresh
        if self._token_info.state == TokenState.VALID:
            return self._token_info.token
        elif self._token_info.state == TokenState.ERROR:
            logger.error("Token in ERROR state, attempting re-authentication")
            await self._fallback_to_reauth()
            return self._token_info.token
        elif self._token_info.state == TokenState.EXPIRED:
            logger.error("Token EXPIRED, forcing re-authentication")
            await self._fallback_to_reauth()
            return self._token_info.token
        else:
            raise RuntimeError(f"Unexpected token state: {self._token_info.state}")

    def _needs_refresh(self) -> bool:
        """
        Check if token needs proactive refresh.

        Returns:
            True if refresh should be triggered
        """
        if self._token_info is None:
            return True

        now = datetime.now()

        # Check if token has expired
        if now >= self._token_info.expires_at:
            logger.warning("Token has EXPIRED")
            self._transition_state(TokenState.EXPIRED)
            return True

        # Check if we've reached refresh trigger time
        if now >= self._token_info.refresh_trigger_time:
            logger.info("Refresh trigger time reached")
            return True

        return False

    async def _check_expiry(self) -> bool:
        """
        Check token expiry and determine if refresh needed.

        Returns:
            True if token is still valid, False if expired or needs refresh
        """
        if self._token_info is None:
            return False

        now = datetime.now()
        time_until_expiry = (self._token_info.expires_at - now).total_seconds()

        logger.debug(
            f"Token expiry check: expires_at={self._token_info.expires_at}, "
            f"time_until_expiry={time_until_expiry}s"
        )

        # Token expired
        if time_until_expiry <= 0:
            logger.warning("Token has expired")
            self._transition_state(TokenState.EXPIRED)
            return False

        # Within refresh buffer window
        if time_until_expiry <= self.refresh_buffer:
            logger.info(f"Token expiring in {time_until_expiry}s, refresh needed")
            return False

        return True

    async def _refresh_token(self):
        """
        Refresh authentication token with exponential backoff retry.

        Flow:
        1. Acquire refresh lock (prevent concurrent refreshes)
        2. Transition to REFRESHING state
        3. Validate current token
        4. On failure, retry with exponential backoff
        5. After max retries, fallback to re-authentication
        6. Drain queued requests on success
        """
        async with self._refresh_lock:
            # Check if another thread already refreshed
            if self._token_info.state == TokenState.VALID and not self._needs_refresh():
                logger.debug("Token already refreshed by another thread")
                return

            logger.info("Starting token refresh process")
            self._transition_state(TokenState.REFRESHING)
            self._retry_count = 0

            # Retry loop with exponential backoff
            for attempt in range(self.max_retries):
                self._retry_count = attempt + 1

                try:
                    logger.info(f"Token refresh attempt {self._retry_count}/{self.max_retries}")

                    # Attempt to validate/refresh token
                    success = await self._validate_token()

                    if success:
                        logger.info("Token refresh successful")
                        self._transition_state(TokenState.VALID)
                        self._retry_count = 0

                        # Drain queued requests
                        await self._drain_queue()
                        return
                    else:
                        logger.warning(f"Token validation failed, attempt {self._retry_count}")

                except Exception as e:
                    logger.error(f"Token refresh error: {e}", exc_info=True)

                # If not last attempt, wait with exponential backoff
                if attempt < self.max_retries - 1:
                    backoff_delay = self.RETRY_BACKOFF_DELAYS[attempt]
                    logger.warning(
                        f"Waiting {backoff_delay}s before retry "
                        f"(attempt {self._retry_count}/{self.max_retries})"
                    )
                    await asyncio.sleep(backoff_delay)

            # All retries exhausted, fallback to re-authentication
            logger.error(
                f"Token refresh failed after {self.max_retries} attempts, "
                "falling back to re-authentication"
            )
            self._transition_state(TokenState.ERROR)
            await self._fallback_to_reauth()

    async def _validate_token(self) -> bool:
        """
        Validate current token with auth service.

        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Call auth service validate method
            if hasattr(self.auth_service, 'validate'):
                result = await self.auth_service.validate()
                return result
            else:
                # If no validate method, assume token is still valid
                # and just check expiry time
                return await self._check_expiry()

        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False

    async def _queue_request(self, callback: Callable, *args, **kwargs) -> Any:
        """
        Queue API request during token refresh.

        Args:
            callback: Function to call after refresh
            *args: Positional arguments for callback
            **kwargs: Keyword arguments for callback

        Returns:
            Result from callback after successful refresh

        Raises:
            RuntimeError: If queue is full
        """
        if len(self._request_queue) >= self.max_queue_depth:
            logger.error(f"Request queue full (depth={len(self._request_queue)})")
            raise RuntimeError("REQUEST_QUEUE_FULL: Too many queued requests")

        # Create queued request
        queued_req = QueuedRequest(
            request_id=f"req_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            callback=callback,
            args=args,
            kwargs=kwargs
        )

        self._request_queue.append(queued_req)
        logger.debug(
            f"Request queued: {queued_req.request_id}, "
            f"queue_depth={len(self._request_queue)}"
        )

        return queued_req

    async def _queue_and_wait(self) -> str:
        """
        Queue a token request and wait for refresh to complete.

        Returns:
            Valid token after refresh completes
        """
        # Wait for refresh to complete (with timeout)
        timeout = self.QUEUE_DRAIN_TIMEOUT * 2
        start_time = datetime.now()

        while self._token_info.state == TokenState.REFRESHING:
            if (datetime.now() - start_time).total_seconds() > timeout:
                logger.error("Timeout waiting for token refresh")
                raise TimeoutError("Token refresh timeout")

            await asyncio.sleep(0.1)  # Poll every 100ms

        # Check final state
        if self._token_info.state == TokenState.VALID:
            return self._token_info.token
        else:
            raise RuntimeError(f"Token refresh failed, state: {self._token_info.state}")

    async def _drain_queue(self):
        """
        Replay queued requests after successful token refresh.

        Processes all queued requests with new token.
        Logs any failures but continues processing.
        """
        if not self._request_queue:
            logger.debug("No queued requests to drain")
            return

        queue_size = len(self._request_queue)
        logger.info(f"Draining request queue: {queue_size} requests")

        start_time = datetime.now()
        success_count = 0
        failure_count = 0

        while self._request_queue:
            queued_req = self._request_queue.popleft()

            try:
                # Execute queued callback
                logger.debug(f"Replaying request: {queued_req.request_id}")
                await queued_req.callback(*queued_req.args, **queued_req.kwargs)
                success_count += 1

            except Exception as e:
                logger.error(
                    f"Failed to replay request {queued_req.request_id}: {e}",
                    exc_info=True
                )
                failure_count += 1

        drain_duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Queue drained: {success_count} succeeded, {failure_count} failed, "
            f"duration={drain_duration:.2f}s"
        )

    async def _initial_authenticate(self):
        """
        Perform initial authentication to obtain token.
        """
        logger.info("Performing initial authentication")

        try:
            # Call auth service authenticate method
            result = await self.auth_service.authenticate()

            if not result:
                raise RuntimeError("Authentication failed")

            # Extract token and expiry from auth service
            token = self.auth_service._token
            expires_at = self.auth_service._token_expiry
            issued_at = datetime.now()
            refresh_trigger_time = expires_at - timedelta(seconds=self.refresh_buffer)

            # Create token info
            self._token_info = TokenInfo(
                token=token,
                issued_at=issued_at,
                expires_at=expires_at,
                refresh_trigger_time=refresh_trigger_time,
                state=TokenState.VALID
            )

            logger.info(
                f"Initial authentication successful: "
                f"expires_at={expires_at}, "
                f"refresh_trigger_time={refresh_trigger_time}"
            )

        except Exception as e:
            logger.error(f"Initial authentication failed: {e}", exc_info=True)
            raise

    async def _fallback_to_reauth(self):
        """
        Fallback to full re-authentication after refresh failures.

        Used when:
        - Token refresh fails after all retries
        - Validate endpoint is unavailable
        - Token is in ERROR or EXPIRED state
        """
        logger.warning("Falling back to full re-authentication")

        try:
            # Clear old token
            self._token_info = None
            self._retry_count = 0

            # Perform fresh authentication
            await self._initial_authenticate()

            # Drain queue with new token
            await self._drain_queue()

            logger.info("Re-authentication successful")

        except Exception as e:
            logger.critical(
                f"Re-authentication FAILED: {e}. System cannot continue.",
                exc_info=True
            )

            # Fail all queued requests
            self._fail_queue()

            # Set to expired state
            if self._token_info:
                self._transition_state(TokenState.EXPIRED)

            raise

    def _fail_queue(self):
        """
        Fail all queued requests when refresh cannot succeed.

        Called when re-authentication fails permanently.
        """
        queue_size = len(self._request_queue)

        if queue_size > 0:
            logger.error(f"Failing {queue_size} queued requests due to auth failure")
            self._request_queue.clear()

    def _transition_state(self, new_state: TokenState):
        """
        Transition token to new state with logging.

        Args:
            new_state: New token state
        """
        old_state = self._token_info.state if self._token_info else TokenState.INITIAL

        if self._token_info:
            self._token_info.state = new_state

        logger.info(f"Token state transition: {old_state.value} -> {new_state.value}")

    def get_state(self) -> Optional[TokenState]:
        """
        Get current token state.

        Returns:
            Current TokenState or None if no token
        """
        return self._token_info.state if self._token_info else None

    def get_time_until_expiry(self) -> Optional[float]:
        """
        Get time until token expiry in seconds.

        Returns:
            Seconds until expiry, or None if no token
        """
        if self._token_info is None:
            return None

        return (self._token_info.expires_at - datetime.now()).total_seconds()

    def get_queue_depth(self) -> int:
        """
        Get current request queue depth.

        Returns:
            Number of queued requests
        """
        return len(self._request_queue)
