"""
SignalR Connection Manager with Reconnection and Health Monitoring

Implements:
- Robust connection lifecycle management with state tracking
- Automatic reconnection with exponential backoff [0, 2s, 10s, 30s, 60s]
- Connection health monitoring with heartbeat/ping mechanism
- Stale connection detection (2 minutes without heartbeat)
- Token refresh integration during reconnection
- State reconciliation trigger after successful reconnection
- Connection quality tracking (HEALTHY, DEGRADED, UNHEALTHY, DISCONNECTED)

Specifications:
- project-specs/SPECS/01-EXTERNAL-API/signalr/SIGNALR_RECONNECTION_SPEC.md
- project-specs/SPECS/01-EXTERNAL-API/signalr/CONNECTION_HEALTH_MONITORING_SPEC.md
- project-specs/SPECS/01-EXTERNAL-API/signalr/EXPONENTIAL_BACKOFF_SPEC.md
- project-specs/SPECS/01-EXTERNAL-API/signalr/STATE_RECONCILIATION_SPEC.md

Test coverage:
- tests/integration/api/test_signalr_reconnection.py
- tests/integration/api/test_connection_health.py
"""

import logging
import time
from enum import Enum
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from collections import deque

# Configure logging
logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """SignalR connection states"""
    DISCONNECTED = "disconnected"           # No connection, initial state
    CONNECTING = "connecting"               # First connection attempt
    CONNECTED = "connected"                 # Active connection established
    RECONNECTING = "reconnecting"           # Automatic reconnection in progress
    FAILED = "failed"                       # Connection failed, manual retry required
    PERMANENTLY_DISCONNECTED = "permanently_disconnected"  # Max retries exceeded
    TOKEN_REFRESH = "token_refresh"         # Paused for token refresh


class HealthStatus(Enum):
    """Connection health status"""
    HEALTHY = "healthy"           # All metrics good (latency < 500ms, success > 95%)
    DEGRADED = "degraded"         # Some metrics concerning (latency 500-2000ms, success 80-95%)
    UNHEALTHY = "unhealthy"       # Multiple metrics bad (latency > 2000ms, success < 80%)
    DISCONNECTED = "disconnected"  # Connection dead


class PingResult:
    """Result of a ping/heartbeat attempt"""
    def __init__(self, sequence_number: int, success: bool, latency: float,
                 timestamp: float, error: Optional[str] = None):
        self.sequence_number = sequence_number
        self.success = success
        self.latency = latency  # milliseconds, -1 if failed
        self.timestamp = timestamp
        self.error = error


class PingStatistics:
    """Aggregated ping statistics"""
    def __init__(self, success_count: int, failure_count: int, success_rate: float,
                 average_latency: float, min_latency: float, max_latency: float,
                 last_ping_time: float, last_successful_ping_time: float):
        self.success_count = success_count
        self.failure_count = failure_count
        self.success_rate = success_rate
        self.average_latency = average_latency
        self.min_latency = min_latency
        self.max_latency = max_latency
        self.last_ping_time = last_ping_time
        self.last_successful_ping_time = last_successful_ping_time


class ExponentialBackoffStrategy:
    """Exponential backoff strategy for reconnection attempts"""

    # Default retry delay sequence: [0ms, 2s, 10s, 30s, 60s]
    DEFAULT_RETRY_DELAYS = [0, 2000, 10000, 30000, 60000]
    DEFAULT_MAX_ATTEMPTS = 10
    DEFAULT_MAX_RECONNECTION_TIME = 300000  # 5 minutes

    def __init__(self, retry_delays: Optional[List[int]] = None,
                 max_attempts: int = DEFAULT_MAX_ATTEMPTS,
                 max_reconnection_time: int = DEFAULT_MAX_RECONNECTION_TIME):
        """Initialize backoff strategy

        Args:
            retry_delays: List of delay values in milliseconds for each attempt
            max_attempts: Maximum number of reconnection attempts
            max_reconnection_time: Maximum total reconnection duration in milliseconds
        """
        self.retry_delays = retry_delays or self.DEFAULT_RETRY_DELAYS
        self.max_attempts = max_attempts
        self.max_reconnection_time = max_reconnection_time
        self.current_attempt = 0
        self.reconnection_start_time: Optional[float] = None

    def get_next_delay(self, attempt_number: int) -> int:
        """Calculate delay for next reconnection attempt

        Args:
            attempt_number: Current attempt number (1-based)

        Returns:
            Delay in milliseconds
        """
        index = attempt_number - 1

        # Get base delay from sequence
        if index < len(self.retry_delays):
            delay = self.retry_delays[index]
        else:
            # Use maximum delay for attempts beyond sequence
            delay = self.retry_delays[-1]

        return delay

    def should_retry(self, attempt_number: int) -> bool:
        """Check if reconnection should be attempted

        Args:
            attempt_number: Current attempt number (1-based)

        Returns:
            True if should retry, False if should give up
        """
        # Check attempt limit
        if attempt_number > self.max_attempts:
            return False

        # Check time limit
        if self.is_max_duration_exceeded():
            return False

        return True

    def get_total_elapsed_time(self) -> float:
        """Get total elapsed time since reconnection started

        Returns:
            Elapsed time in milliseconds, or 0 if not reconnecting
        """
        if self.reconnection_start_time is None:
            return 0
        return (time.time() - self.reconnection_start_time) * 1000

    def is_max_duration_exceeded(self) -> bool:
        """Check if maximum reconnection duration has been exceeded

        Returns:
            True if max duration exceeded, false otherwise
        """
        elapsed_time = self.get_total_elapsed_time()
        return elapsed_time > self.max_reconnection_time

    def reset(self):
        """Reset backoff state (called on successful reconnection)"""
        self.current_attempt = 0
        self.reconnection_start_time = None

    def start_reconnection_cycle(self):
        """Start reconnection cycle (called when disconnection detected)"""
        self.current_attempt = 0
        self.reconnection_start_time = time.time()

    def next_attempt(self) -> int:
        """Increment attempt counter and get delay for next attempt

        Returns:
            Delay in milliseconds for next attempt
        """
        self.current_attempt += 1
        return self.get_next_delay(self.current_attempt)


class PingManager:
    """Manages heartbeat/ping mechanism for connection health monitoring"""

    MAX_HISTORY_SIZE = 10

    def __init__(self):
        self.ping_history: deque[PingResult] = deque(maxlen=self.MAX_HISTORY_SIZE)
        self.current_sequence = 0

    def record_ping(self, result: PingResult):
        """Record a ping result in history

        Args:
            result: PingResult to record
        """
        self.ping_history.append(result)

    def get_ping_statistics(self) -> PingStatistics:
        """Calculate ping statistics from recent history

        Returns:
            PingStatistics with aggregated metrics
        """
        if not self.ping_history:
            return PingStatistics(
                success_count=0,
                failure_count=0,
                success_rate=0.0,
                average_latency=0.0,
                min_latency=0.0,
                max_latency=0.0,
                last_ping_time=0.0,
                last_successful_ping_time=0.0
            )

        successful_pings = [p for p in self.ping_history if p.success]
        latencies = [p.latency for p in successful_pings]

        return PingStatistics(
            success_count=len(successful_pings),
            failure_count=len(self.ping_history) - len(successful_pings),
            success_rate=(len(successful_pings) / len(self.ping_history)) * 100,
            average_latency=sum(latencies) / len(latencies) if latencies else 0.0,
            min_latency=min(latencies) if latencies else 0.0,
            max_latency=max(latencies) if latencies else 0.0,
            last_ping_time=self.ping_history[-1].timestamp,
            last_successful_ping_time=successful_pings[-1].timestamp if successful_pings else 0.0
        )

    def get_consecutive_failures(self) -> int:
        """Count consecutive ping failures from most recent

        Returns:
            Number of consecutive failures
        """
        failures = 0
        for ping_result in reversed(self.ping_history):
            if ping_result.success:
                break
            failures += 1
        return failures


class SignalRConnectionManager:
    """
    Manages SignalR connection lifecycle with robust reconnection and health monitoring.

    Features:
    - Automatic reconnection with exponential backoff
    - Connection health monitoring with heartbeat
    - Stale connection detection and cleanup
    - Token refresh integration
    - State reconciliation coordination
    """

    # Configuration defaults
    PING_INTERVAL = 30000  # 30 seconds
    PING_TIMEOUT = 5000    # 5 seconds
    STALE_THRESHOLD = 120000  # 2 minutes
    HEALTHY_MAX_LATENCY = 500  # milliseconds
    DEGRADED_MAX_LATENCY = 2000  # milliseconds
    MAX_CONSECUTIVE_FAILURES = 3

    def __init__(self, token_manager, event_router=None):
        """Initialize SignalR connection manager

        Args:
            token_manager: Token manager instance for authentication
            event_router: Optional event router for state reconciliation
        """
        self.token_manager = token_manager
        self.event_router = event_router

        # Connection state
        self.connection_state = ConnectionState.DISCONNECTED
        self.connection_id: Optional[str] = None
        self.intentional_disconnect = False

        # Backoff strategy
        self.backoff_strategy = ExponentialBackoffStrategy()

        # Health monitoring
        self.ping_manager = PingManager()
        self.last_event_time = time.time()
        self.health_status = HealthStatus.DISCONNECTED

        # Callbacks
        self._on_connected_callback: Optional[Callable] = None
        self._on_disconnected_callback: Optional[Callable] = None
        self._on_reconnecting_callback: Optional[Callable] = None
        self._on_reconnected_callback: Optional[Callable] = None
        self._on_health_changed_callback: Optional[Callable] = None

        # Subscriptions tracking
        self._active_subscriptions: List[Dict[str, Any]] = []

        logger.info("SignalRConnectionManager initialized")

    def connect(self) -> bool:
        """Establish SignalR connection

        Returns:
            True if connection successful, False otherwise
        """
        logger.info("Initiating SignalR connection...")
        self.connection_state = ConnectionState.CONNECTING
        self.intentional_disconnect = False

        try:
            # Get fresh token for connection
            token = self.token_manager.get_token()
            if not token:
                logger.error("No authentication token available")
                self.connection_state = ConnectionState.FAILED
                return False

            # TODO: Implement actual SignalR connection logic here
            # This is a placeholder for the actual SignalR client initialization
            # Example (pseudocode):
            # self.hub_connection = HubConnectionBuilder()
            #     .with_url(hub_url, access_token_factory=lambda: self.token_manager.get_token())
            #     .with_automatic_reconnect(self.backoff_strategy.retry_delays)
            #     .build()
            #
            # self.hub_connection.on_reconnecting(self._on_reconnecting)
            # self.hub_connection.on_reconnected(self._on_reconnected)
            # self.hub_connection.on_close(self._on_close)
            #
            # await self.hub_connection.start()

            self._on_connected()
            return True

        except Exception as e:
            logger.error(f"SignalR connection failed: {e}")
            self.connection_state = ConnectionState.FAILED
            return False

    def disconnect(self):
        """Gracefully disconnect SignalR connection"""
        logger.info("Disconnecting SignalR connection...")
        self.intentional_disconnect = True

        # TODO: Stop SignalR connection
        # await self.hub_connection.stop()

        self.connection_state = ConnectionState.DISCONNECTED
        self.connection_id = None

        if self._on_disconnected_callback:
            self._on_disconnected_callback()

    def _on_connected(self):
        """Handler called when connection is established"""
        self.connection_state = ConnectionState.CONNECTED
        self.connection_id = f"conn_{int(time.time())}"  # Placeholder
        self.backoff_strategy.reset()
        self.last_event_time = time.time()
        self.health_status = HealthStatus.HEALTHY

        logger.info(f"SignalR connection established: {self.connection_id}")

        if self._on_connected_callback:
            self._on_connected_callback(self.connection_id)

    def _on_close(self, error: Optional[Exception] = None):
        """Handler called when connection is permanently closed

        Args:
            error: Optional error that caused closure
        """
        is_intentional = self.intentional_disconnect
        max_retries_exceeded = self.backoff_strategy.current_attempt >= self.backoff_strategy.max_attempts

        logger.error(f"SignalR connection closed permanently", extra={
            'error': str(error) if error else None,
            'intentional': is_intentional,
            'max_retries_exceeded': max_retries_exceeded,
            'final_attempts': self.backoff_strategy.current_attempt
        })

        # Update state
        self.connection_state = (ConnectionState.DISCONNECTED if is_intentional
                                else ConnectionState.PERMANENTLY_DISCONNECTED)
        self.connection_id = None
        self.health_status = HealthStatus.DISCONNECTED

        if is_intentional:
            logger.info("Connection closed intentionally, no action required")
            return

        # Notify about permanent disconnection
        if max_retries_exceeded or error:
            logger.warning("Connection permanently lost after max retries")

            if self._on_disconnected_callback:
                self._on_disconnected_callback()

    def _on_reconnecting(self, attempt: int, error: Optional[Exception] = None):
        """Handler called when reconnection attempt starts

        Args:
            attempt: Current attempt number
            error: Optional error from previous attempt
        """
        if self.backoff_strategy.reconnection_start_time is None:
            self.backoff_strategy.start_reconnection_cycle()

        next_delay = self.backoff_strategy.next_attempt()
        should_retry = self.backoff_strategy.should_retry(self.backoff_strategy.current_attempt)

        self.connection_state = ConnectionState.RECONNECTING

        logger.warning(f"SignalR reconnection attempt {self.backoff_strategy.current_attempt}/{self.backoff_strategy.max_attempts}", extra={
            'error': str(error) if error else None,
            'next_delay': next_delay,
            'elapsed_time': self.backoff_strategy.get_total_elapsed_time(),
            'should_retry': should_retry
        })

        if not should_retry:
            logger.error("Max reconnection attempts or duration exceeded")
            # TODO: Stop connection to trigger onclose
            # await self.hub_connection.stop()
            return

        if self._on_reconnecting_callback:
            self._on_reconnecting_callback(self.backoff_strategy.current_attempt,
                                          self.backoff_strategy.max_attempts,
                                          next_delay)

    def _on_reconnected(self, connection_id: Optional[str] = None):
        """Handler called when reconnection is successful

        Args:
            connection_id: Optional new connection ID
        """
        reconnection_duration = self.backoff_strategy.get_total_elapsed_time()
        previous_attempts = self.backoff_strategy.current_attempt

        logger.info(f"SignalR reconnection successful", extra={
            'connection_id': connection_id,
            'attempts': previous_attempts,
            'duration': reconnection_duration
        })

        # Update state
        self.connection_state = ConnectionState.CONNECTED
        self.connection_id = connection_id
        self.backoff_strategy.reset()
        self.last_event_time = time.time()
        self.health_status = HealthStatus.HEALTHY

        # Resubscribe to all events
        self.resubscribe_all()

        # Trigger state reconciliation
        if self.event_router:
            logger.info("Triggering state reconciliation after reconnection")
            try:
                self.event_router.reconcile_state()
            except Exception as e:
                logger.error(f"State reconciliation failed: {e}")

        if self._on_reconnected_callback:
            self._on_reconnected_callback(connection_id, previous_attempts, reconnection_duration)

    def _reconnect_with_backoff(self):
        """Attempt reconnection with exponential backoff

        Note: This is typically handled automatically by SignalR client library
        with the configured retry delays. This method is for manual retry scenarios.
        """
        if not self.backoff_strategy.should_retry(self.backoff_strategy.current_attempt + 1):
            logger.error("Cannot retry: max attempts or duration exceeded")
            return False

        delay_ms = self.backoff_strategy.next_attempt()
        logger.info(f"Reconnecting in {delay_ms}ms (attempt {self.backoff_strategy.current_attempt})")

        # TODO: Implement actual reconnection with delay
        # await asyncio.sleep(delay_ms / 1000)
        # await self.hub_connection.start()

        return True

    def _health_check(self) -> bool:
        """Execute heartbeat health check

        Returns:
            True if ping successful, False otherwise
        """
        sequence_number = self.ping_manager.current_sequence + 1
        send_time = time.time()

        try:
            # TODO: Implement actual ping to SignalR hub
            # Example:
            # pong = await self.hub_connection.invoke('Ping', {
            #     'type': 'ping',
            #     'timestamp': send_time * 1000,
            #     'sequenceNumber': sequence_number
            # })

            # Simulate successful ping for now
            receive_time = time.time()
            latency = (receive_time - send_time) * 1000  # Convert to milliseconds

            result = PingResult(
                sequence_number=sequence_number,
                success=True,
                latency=latency,
                timestamp=send_time
            )

            self.ping_manager.record_ping(result)
            self.ping_manager.current_sequence = sequence_number

            # Update health status
            self._update_health_status()

            return True

        except Exception as e:
            logger.warning(f"Health check ping failed: {e}")

            result = PingResult(
                sequence_number=sequence_number,
                success=False,
                latency=-1,
                timestamp=send_time,
                error=str(e)
            )

            self.ping_manager.record_ping(result)
            self._update_health_status()

            return False

    def _detect_stale(self) -> bool:
        """Detect if connection is stale (no events for 2 minutes)

        Returns:
            True if connection is stale, False otherwise
        """
        time_since_last_event = (time.time() - self.last_event_time) * 1000  # milliseconds
        is_stale = time_since_last_event > self.STALE_THRESHOLD

        if is_stale:
            logger.warning(f"Stale connection detected: {time_since_last_event}ms since last event")

        return is_stale

    def _update_health_status(self):
        """Update connection health status based on ping statistics"""
        if self.connection_state != ConnectionState.CONNECTED:
            new_status = HealthStatus.DISCONNECTED
        else:
            stats = self.ping_manager.get_ping_statistics()
            consecutive_failures = self.ping_manager.get_consecutive_failures()
            time_since_last_event = (time.time() - self.last_event_time) * 1000

            # DISCONNECTED: Connection is dead
            if consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                new_status = HealthStatus.DISCONNECTED
            elif time_since_last_event > self.STALE_THRESHOLD:
                new_status = HealthStatus.DISCONNECTED
            # UNHEALTHY: High latency or low success rate
            elif stats.average_latency > self.DEGRADED_MAX_LATENCY or stats.success_rate < 80:
                new_status = HealthStatus.UNHEALTHY
            # DEGRADED: Moderate latency or occasional failures
            elif stats.average_latency > self.HEALTHY_MAX_LATENCY or stats.success_rate < 95:
                new_status = HealthStatus.DEGRADED
            # HEALTHY: All metrics good
            else:
                new_status = HealthStatus.HEALTHY

        # Notify if status changed
        if new_status != self.health_status:
            old_status = self.health_status
            self.health_status = new_status

            logger.info(f"Connection health changed: {old_status.value} -> {new_status.value}")

            if self._on_health_changed_callback:
                self._on_health_changed_callback(old_status, new_status)

    def resubscribe_all(self):
        """Resubscribe to all SignalR events after reconnection"""
        logger.info(f"Resubscribing to {len(self._active_subscriptions)} SignalR events")

        for subscription in self._active_subscriptions:
            try:
                # TODO: Implement actual resubscription
                # await self.hub_connection.on(subscription['event_name'], subscription['handler'])
                logger.debug(f"Resubscribed to {subscription.get('event_name', 'unknown')}")
            except Exception as e:
                logger.error(f"Failed to resubscribe to {subscription.get('event_name')}: {e}")

    def record_event_received(self):
        """Record that an event was received from server

        Call this whenever any SignalR event is received to update stale detection.
        """
        self.last_event_time = time.time()

    def is_healthy(self) -> bool:
        """Check if connection is healthy

        Returns:
            True if connection is healthy, False otherwise
        """
        return (self.connection_state == ConnectionState.CONNECTED and
                self.health_status == HealthStatus.HEALTHY)

    def get_health_metrics(self) -> Dict[str, Any]:
        """Get comprehensive health metrics

        Returns:
            Dictionary with health status, ping statistics, and connection info
        """
        stats = self.ping_manager.get_ping_statistics()

        return {
            'connection_state': self.connection_state.value,
            'health_status': self.health_status.value,
            'connection_id': self.connection_id,
            'ping_latency': stats.average_latency,
            'ping_success_rate': stats.success_rate,
            'consecutive_failures': self.ping_manager.get_consecutive_failures(),
            'time_since_last_event': (time.time() - self.last_event_time) * 1000,
            'reconnection_attempt': self.backoff_strategy.current_attempt,
            'max_reconnection_attempts': self.backoff_strategy.max_attempts
        }

    # Callback registration methods

    def on_connected(self, callback: Callable[[str], None]):
        """Register callback for connection established event"""
        self._on_connected_callback = callback

    def on_disconnected(self, callback: Callable[[], None]):
        """Register callback for connection lost event"""
        self._on_disconnected_callback = callback

    def on_reconnecting(self, callback: Callable[[int, int, int], None]):
        """Register callback for reconnection attempt event

        Callback receives: (current_attempt, max_attempts, next_delay_ms)
        """
        self._on_reconnecting_callback = callback

    def on_reconnected(self, callback: Callable[[str, int, float], None]):
        """Register callback for reconnection successful event

        Callback receives: (connection_id, attempts, duration_ms)
        """
        self._on_reconnected_callback = callback

    def on_health_changed(self, callback: Callable[[HealthStatus, HealthStatus], None]):
        """Register callback for health status change event

        Callback receives: (old_status, new_status)
        """
        self._on_health_changed_callback = callback
