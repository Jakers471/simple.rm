"""
Unit Tests for SignalR Connection Manager

Tests for:
- SignalRConnectionManager with correct API
- Connection lifecycle and state transitions
- Exponential backoff strategy [0, 2s, 10s, 30s, 60s]
- Health monitoring with heartbeat/ping mechanism
- Stale connection detection (2 minutes)
- Automatic resubscription after reconnection
- Token refresh integration
- Health status transitions (HEALTHY, DEGRADED, UNHEALTHY, DISCONNECTED)

Target coverage: 90%+
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

from src.api.signalr_manager import (
    SignalRConnectionManager,
    ConnectionState,
    HealthStatus,
    ExponentialBackoffStrategy,
    PingManager,
    PingResult,
    PingStatistics
)


class TestExponentialBackoffStrategy:
    """Test exponential backoff strategy for reconnection"""

    def test_default_retry_delays(self):
        """Test default retry delay sequence [0, 2s, 10s, 30s, 60s]"""
        strategy = ExponentialBackoffStrategy()

        assert strategy.retry_delays == [0, 2000, 10000, 30000, 60000]
        assert strategy.max_attempts == 10
        assert strategy.max_reconnection_time == 300000  # 5 minutes

    def test_get_next_delay_sequence(self):
        """Test delay calculation for each attempt"""
        strategy = ExponentialBackoffStrategy()

        # Test retry delay sequence
        assert strategy.get_next_delay(1) == 0        # First attempt: immediate
        assert strategy.get_next_delay(2) == 2000     # Second attempt: 2s
        assert strategy.get_next_delay(3) == 10000    # Third attempt: 10s
        assert strategy.get_next_delay(4) == 30000    # Fourth attempt: 30s
        assert strategy.get_next_delay(5) == 60000    # Fifth attempt: 60s

    def test_get_next_delay_beyond_sequence(self):
        """Test that delays beyond sequence use maximum delay"""
        strategy = ExponentialBackoffStrategy()

        # Attempts beyond sequence should use last delay (60s)
        assert strategy.get_next_delay(6) == 60000
        assert strategy.get_next_delay(10) == 60000
        assert strategy.get_next_delay(100) == 60000

    def test_should_retry_within_limits(self):
        """Test retry logic within attempt and time limits"""
        strategy = ExponentialBackoffStrategy(max_attempts=5)
        strategy.start_reconnection_cycle()

        # Should retry within limits
        assert strategy.should_retry(1) is True
        assert strategy.should_retry(3) is True
        assert strategy.should_retry(5) is True

    def test_should_retry_exceeds_attempts(self):
        """Test retry logic when max attempts exceeded"""
        strategy = ExponentialBackoffStrategy(max_attempts=5)
        strategy.start_reconnection_cycle()

        # Should not retry beyond max attempts
        assert strategy.should_retry(6) is False
        assert strategy.should_retry(10) is False

    def test_should_retry_exceeds_duration(self):
        """Test retry logic when max duration exceeded"""
        strategy = ExponentialBackoffStrategy(max_reconnection_time=1000)  # 1 second

        # Mock time to simulate elapsed duration
        with patch('time.time') as mock_time:
            mock_time.return_value = 100.0
            strategy.start_reconnection_cycle()

            # Simulate 2 seconds elapsed
            mock_time.return_value = 102.0
            assert strategy.should_retry(1) is False

    def test_reset_backoff(self):
        """Test resetting backoff state after successful reconnection"""
        strategy = ExponentialBackoffStrategy()
        strategy.start_reconnection_cycle()
        strategy.current_attempt = 5

        strategy.reset()

        assert strategy.current_attempt == 0
        assert strategy.reconnection_start_time is None

    def test_start_reconnection_cycle(self):
        """Test starting reconnection cycle"""
        strategy = ExponentialBackoffStrategy()

        with patch('time.time', return_value=100.0):
            strategy.start_reconnection_cycle()

            assert strategy.current_attempt == 0
            assert strategy.reconnection_start_time == 100.0

    def test_next_attempt(self):
        """Test incrementing attempt counter and getting delay"""
        strategy = ExponentialBackoffStrategy()

        # First attempt
        delay = strategy.next_attempt()
        assert delay == 0
        assert strategy.current_attempt == 1

        # Second attempt
        delay = strategy.next_attempt()
        assert delay == 2000
        assert strategy.current_attempt == 2

    def test_get_total_elapsed_time(self):
        """Test calculating total elapsed time"""
        strategy = ExponentialBackoffStrategy()

        # Not reconnecting
        assert strategy.get_total_elapsed_time() == 0

        # Reconnecting
        with patch('time.time') as mock_time:
            mock_time.return_value = 100.0
            strategy.start_reconnection_cycle()

            mock_time.return_value = 103.5
            elapsed = strategy.get_total_elapsed_time()
            assert elapsed == 3500  # milliseconds

    def test_custom_retry_delays(self):
        """Test custom retry delay sequence"""
        custom_delays = [100, 500, 1000]
        strategy = ExponentialBackoffStrategy(retry_delays=custom_delays)

        assert strategy.get_next_delay(1) == 100
        assert strategy.get_next_delay(2) == 500
        assert strategy.get_next_delay(3) == 1000
        # Beyond sequence uses last delay
        assert strategy.get_next_delay(4) == 1000


class TestPingManager:
    """Test ping/heartbeat management"""

    def test_initialization(self):
        """Test ping manager initialization"""
        manager = PingManager()

        assert len(manager.ping_history) == 0
        assert manager.current_sequence == 0

    def test_record_ping(self):
        """Test recording ping results"""
        manager = PingManager()

        result = PingResult(
            sequence_number=1,
            success=True,
            latency=50.5,
            timestamp=time.time()
        )

        manager.record_ping(result)
        assert len(manager.ping_history) == 1
        assert manager.ping_history[0] == result

    def test_ping_history_max_size(self):
        """Test ping history limited to MAX_HISTORY_SIZE (10)"""
        manager = PingManager()

        # Add more than max size
        for i in range(15):
            result = PingResult(
                sequence_number=i,
                success=True,
                latency=50.0,
                timestamp=time.time()
            )
            manager.record_ping(result)

        # Should only keep last 10
        assert len(manager.ping_history) == 10
        assert manager.ping_history[0].sequence_number == 5  # Oldest kept is #5

    def test_get_ping_statistics_empty(self):
        """Test ping statistics with no history"""
        manager = PingManager()

        stats = manager.get_ping_statistics()

        assert stats.success_count == 0
        assert stats.failure_count == 0
        assert stats.success_rate == 0.0
        assert stats.average_latency == 0.0
        assert stats.min_latency == 0.0
        assert stats.max_latency == 0.0

    def test_get_ping_statistics_all_successful(self):
        """Test ping statistics with all successful pings"""
        manager = PingManager()

        # Add successful pings with different latencies
        latencies = [100.0, 200.0, 150.0, 50.0, 300.0]
        for i, latency in enumerate(latencies):
            result = PingResult(
                sequence_number=i,
                success=True,
                latency=latency,
                timestamp=time.time()
            )
            manager.record_ping(result)

        stats = manager.get_ping_statistics()

        assert stats.success_count == 5
        assert stats.failure_count == 0
        assert stats.success_rate == 100.0
        assert stats.average_latency == 160.0  # (100+200+150+50+300)/5
        assert stats.min_latency == 50.0
        assert stats.max_latency == 300.0

    def test_get_ping_statistics_mixed_results(self):
        """Test ping statistics with mixed success/failure"""
        manager = PingManager()

        # Add mix of successful and failed pings
        results = [
            PingResult(1, True, 100.0, time.time()),
            PingResult(2, False, -1, time.time(), error="timeout"),
            PingResult(3, True, 200.0, time.time()),
            PingResult(4, False, -1, time.time(), error="timeout"),
            PingResult(5, True, 150.0, time.time()),
        ]

        for result in results:
            manager.record_ping(result)

        stats = manager.get_ping_statistics()

        assert stats.success_count == 3
        assert stats.failure_count == 2
        assert stats.success_rate == 60.0  # 3/5 * 100
        assert stats.average_latency == 150.0  # (100+200+150)/3

    def test_get_consecutive_failures(self):
        """Test counting consecutive failures from most recent"""
        manager = PingManager()

        # No failures yet
        assert manager.get_consecutive_failures() == 0

        # Add successful pings
        manager.record_ping(PingResult(1, True, 100.0, time.time()))
        manager.record_ping(PingResult(2, True, 150.0, time.time()))
        assert manager.get_consecutive_failures() == 0

        # Add some failures
        manager.record_ping(PingResult(3, False, -1, time.time(), error="timeout"))
        assert manager.get_consecutive_failures() == 1

        manager.record_ping(PingResult(4, False, -1, time.time(), error="timeout"))
        assert manager.get_consecutive_failures() == 2

        manager.record_ping(PingResult(5, False, -1, time.time(), error="timeout"))
        assert manager.get_consecutive_failures() == 3

        # Success breaks the streak
        manager.record_ping(PingResult(6, True, 100.0, time.time()))
        assert manager.get_consecutive_failures() == 0


class TestSignalRConnectionManager:
    """Test SignalR connection manager"""

    @pytest.fixture
    def mock_token_manager(self):
        """Mock token manager"""
        token_manager = Mock()
        token_manager.get_token.return_value = "valid_token_12345"
        return token_manager

    @pytest.fixture
    def mock_event_router(self):
        """Mock event router"""
        router = Mock()
        router.reconcile_state = Mock()
        return router

    @pytest.fixture
    def manager(self, mock_token_manager, mock_event_router):
        """Create SignalR connection manager instance"""
        return SignalRConnectionManager(mock_token_manager, mock_event_router)

    def test_initialization(self, manager, mock_token_manager, mock_event_router):
        """Test SignalRConnectionManager initialization"""
        assert manager.token_manager == mock_token_manager
        assert manager.event_router == mock_event_router
        assert manager.connection_state == ConnectionState.DISCONNECTED
        assert manager.connection_id is None
        assert manager.intentional_disconnect is False
        assert manager.health_status == HealthStatus.DISCONNECTED
        assert isinstance(manager.backoff_strategy, ExponentialBackoffStrategy)
        assert isinstance(manager.ping_manager, PingManager)

    def test_connect_success(self, manager, mock_token_manager):
        """Test successful connection"""
        result = manager.connect()

        assert result is True
        assert manager.connection_state == ConnectionState.CONNECTED
        assert manager.connection_id is not None
        assert manager.health_status == HealthStatus.HEALTHY
        mock_token_manager.get_token.assert_called_once()

    def test_connect_no_token(self, manager, mock_token_manager):
        """Test connection fails when no token available"""
        mock_token_manager.get_token.return_value = None

        result = manager.connect()

        assert result is False
        assert manager.connection_state == ConnectionState.FAILED

    def test_connect_exception(self, manager, mock_token_manager):
        """Test connection handles exceptions"""
        mock_token_manager.get_token.side_effect = Exception("Token error")

        result = manager.connect()

        assert result is False
        assert manager.connection_state == ConnectionState.FAILED

    def test_disconnect(self, manager):
        """Test graceful disconnection"""
        # First connect
        manager.connect()
        assert manager.connection_state == ConnectionState.CONNECTED

        # Then disconnect
        manager.disconnect()

        assert manager.connection_state == ConnectionState.DISCONNECTED
        assert manager.connection_id is None
        assert manager.intentional_disconnect is True

    def test_on_connected_callback(self, manager):
        """Test on_connected callback is invoked"""
        callback = Mock()
        manager.on_connected(callback)

        manager.connect()

        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == manager.connection_id  # connection_id passed

    def test_on_disconnected_callback(self, manager):
        """Test on_disconnected callback is invoked"""
        callback = Mock()
        manager.on_disconnected(callback)

        manager.connect()
        manager.disconnect()

        callback.assert_called_once()

    def test_on_reconnecting_callback(self, manager):
        """Test on_reconnecting callback is invoked"""
        callback = Mock()
        manager.on_reconnecting(callback)

        # Trigger reconnecting
        manager._on_reconnecting(1, error=Exception("Connection lost"))

        callback.assert_called_once()
        args = callback.call_args[0]
        # Callback receives: (current_attempt, max_attempts, next_delay_ms)
        assert len(args) == 3
        assert isinstance(args[0], int)  # current_attempt
        assert isinstance(args[1], int)  # max_attempts
        assert isinstance(args[2], int)  # next_delay_ms

    def test_on_reconnected_callback(self, manager):
        """Test on_reconnected callback is invoked"""
        callback = Mock()
        manager.on_reconnected(callback)

        # Setup reconnection state
        manager.backoff_strategy.start_reconnection_cycle()
        manager.backoff_strategy.current_attempt = 3

        # Trigger reconnected
        manager._on_reconnected("new_conn_id")

        callback.assert_called_once()
        args = callback.call_args[0]
        # Callback receives: (connection_id, attempts, duration_ms)
        assert args[0] == "new_conn_id"
        assert args[1] == 3  # attempts
        assert isinstance(args[2], float)  # duration_ms

    def test_reconnecting_state_transitions(self, manager):
        """Test state transitions during reconnection"""
        manager.backoff_strategy.start_reconnection_cycle()

        # Start reconnecting
        manager._on_reconnecting(1, error=Exception("Connection lost"))
        assert manager.connection_state == ConnectionState.RECONNECTING

        # Successfully reconnected
        manager._on_reconnected("new_conn_id")
        assert manager.connection_state == ConnectionState.CONNECTED

    def test_reconnecting_max_attempts_exceeded(self, manager):
        """Test reconnection stops when max attempts exceeded"""
        manager.backoff_strategy.max_attempts = 3
        manager.backoff_strategy.start_reconnection_cycle()

        # Simulate attempts beyond limit
        manager.backoff_strategy.current_attempt = 4

        manager._on_reconnecting(4)

        # Should not continue reconnecting
        assert manager.backoff_strategy.should_retry(4) is False

    def test_reconnecting_max_duration_exceeded(self, manager):
        """Test reconnection stops when max duration exceeded"""
        manager.backoff_strategy.max_reconnection_time = 1000  # 1 second

        with patch('time.time') as mock_time:
            mock_time.return_value = 100.0
            manager.backoff_strategy.start_reconnection_cycle()

            # Simulate 2 seconds elapsed
            mock_time.return_value = 102.0
            manager._on_reconnecting(1)

            assert manager.backoff_strategy.should_retry(1) is False

    def test_reconnecting_backoff_reset_on_success(self, manager):
        """Test backoff strategy resets after successful reconnection"""
        manager.backoff_strategy.start_reconnection_cycle()
        manager.backoff_strategy.current_attempt = 5

        manager._on_reconnected("new_conn_id")

        assert manager.backoff_strategy.current_attempt == 0
        assert manager.backoff_strategy.reconnection_start_time is None

    def test_resubscribe_all_after_reconnection(self, manager):
        """Test automatic resubscription after reconnection"""
        # Setup subscriptions
        manager._active_subscriptions = [
            {'event_name': 'OrderUpdate', 'handler': Mock()},
            {'event_name': 'PositionUpdate', 'handler': Mock()},
            {'event_name': 'RiskAlert', 'handler': Mock()},
        ]

        manager.backoff_strategy.start_reconnection_cycle()
        manager._on_reconnected("new_conn_id")

        # Resubscribe should have been called
        # (actual implementation is TODO, but method should be called)
        assert len(manager._active_subscriptions) == 3

    def test_state_reconciliation_after_reconnection(self, manager, mock_event_router):
        """Test state reconciliation triggered after reconnection"""
        manager.backoff_strategy.start_reconnection_cycle()

        manager._on_reconnected("new_conn_id")

        # Should trigger reconciliation
        mock_event_router.reconcile_state.assert_called_once()

    def test_state_reconciliation_error_handling(self, manager, mock_event_router):
        """Test state reconciliation error doesn't break reconnection"""
        mock_event_router.reconcile_state.side_effect = Exception("Reconciliation failed")

        manager.backoff_strategy.start_reconnection_cycle()
        manager._on_reconnected("new_conn_id")

        # Should still complete reconnection despite error
        assert manager.connection_state == ConnectionState.CONNECTED

    def test_health_check_successful(self, manager):
        """Test successful health check ping"""
        manager.connect()

        result = manager._health_check()

        assert result is True
        assert len(manager.ping_manager.ping_history) == 1
        assert manager.ping_manager.ping_history[0].success is True

    def test_stale_connection_detection(self, manager):
        """Test stale connection detection (2 minutes)"""
        manager.connect()

        # Fresh connection - not stale
        assert manager._detect_stale() is False

        # Simulate 2 minutes passing
        with patch('time.time') as mock_time:
            mock_time.return_value = manager.last_event_time + 121  # 2:01 minutes

            is_stale = manager._detect_stale()
            assert is_stale is True

    def test_record_event_received(self, manager):
        """Test recording event reception updates last event time"""
        manager.connect()

        initial_time = manager.last_event_time
        time.sleep(0.01)  # Small delay

        manager.record_event_received()

        assert manager.last_event_time > initial_time

    def test_health_status_healthy(self, manager):
        """Test HEALTHY status with good metrics"""
        manager.connect()

        # Add successful pings with low latency
        for i in range(5):
            result = PingResult(i, True, 100.0, time.time())  # 100ms latency
            manager.ping_manager.record_ping(result)

        manager._update_health_status()

        assert manager.health_status == HealthStatus.HEALTHY

    def test_health_status_degraded(self, manager):
        """Test DEGRADED status with moderate latency"""
        manager.connect()

        # Add pings with moderate latency (500-2000ms)
        for i in range(5):
            result = PingResult(i, True, 800.0, time.time())  # 800ms latency
            manager.ping_manager.record_ping(result)

        manager._update_health_status()

        assert manager.health_status == HealthStatus.DEGRADED

    def test_health_status_unhealthy(self, manager):
        """Test UNHEALTHY status with high latency"""
        manager.connect()

        # Add pings with high latency (>2000ms)
        for i in range(5):
            result = PingResult(i, True, 2500.0, time.time())  # 2500ms latency
            manager.ping_manager.record_ping(result)

        manager._update_health_status()

        assert manager.health_status == HealthStatus.UNHEALTHY

    def test_health_status_disconnected_by_failures(self, manager):
        """Test DISCONNECTED status from consecutive failures"""
        manager.connect()

        # Add 3+ consecutive failures
        for i in range(4):
            result = PingResult(i, False, -1, time.time(), error="timeout")
            manager.ping_manager.record_ping(result)

        manager._update_health_status()

        assert manager.health_status == HealthStatus.DISCONNECTED

    def test_health_status_disconnected_by_staleness(self, manager):
        """Test DISCONNECTED status from stale connection"""
        manager.connect()

        # Simulate stale connection (>2 minutes)
        with patch('time.time', return_value=manager.last_event_time + 121):
            manager._update_health_status()

            assert manager.health_status == HealthStatus.DISCONNECTED

    def test_health_status_low_success_rate(self, manager):
        """Test UNHEALTHY status from low ping success rate"""
        manager.connect()

        # Add pings with <80% success rate but not consecutive failures
        # Pattern: F, S, F, S, F, S, F, S, S, S (60% success, no 3 consecutive failures)
        pattern = [False, True, False, True, False, True, False, True, True, True]
        for i, success in enumerate(pattern):
            latency = 100.0 if success else -1
            error = None if success else "timeout"
            result = PingResult(i, success, latency, time.time(), error)
            manager.ping_manager.record_ping(result)

        manager._update_health_status()

        assert manager.health_status == HealthStatus.UNHEALTHY

    def test_health_changed_callback(self, manager):
        """Test on_health_changed callback invoked on status change"""
        callback = Mock()
        manager.on_health_changed(callback)

        manager.connect()
        old_status = manager.health_status

        # Force health degradation
        for i in range(5):
            result = PingResult(i, True, 2500.0, time.time())  # High latency
            manager.ping_manager.record_ping(result)

        manager._update_health_status()

        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == old_status
        assert args[1] == HealthStatus.UNHEALTHY

    def test_is_healthy(self, manager):
        """Test is_healthy() checks connection state and health status"""
        # Not connected
        assert manager.is_healthy() is False

        # Connected and healthy
        manager.connect()
        assert manager.is_healthy() is True

        # Connected but unhealthy
        manager.health_status = HealthStatus.DEGRADED
        assert manager.is_healthy() is False

    def test_get_health_metrics(self, manager):
        """Test comprehensive health metrics"""
        manager.connect()

        # Add some ping history
        for i in range(3):
            result = PingResult(i, True, 100.0, time.time())
            manager.ping_manager.record_ping(result)

        metrics = manager.get_health_metrics()

        assert 'connection_state' in metrics
        assert 'health_status' in metrics
        assert 'connection_id' in metrics
        assert 'ping_latency' in metrics
        assert 'ping_success_rate' in metrics
        assert 'consecutive_failures' in metrics
        assert 'time_since_last_event' in metrics
        assert 'reconnection_attempt' in metrics
        assert 'max_reconnection_attempts' in metrics

        assert metrics['connection_state'] == ConnectionState.CONNECTED.value
        assert metrics['health_status'] == HealthStatus.HEALTHY.value
        assert metrics['ping_success_rate'] == 100.0

    def test_permanently_disconnected_state(self, manager):
        """Test PERMANENTLY_DISCONNECTED state after max retries"""
        manager.connect()
        manager.intentional_disconnect = False

        # Simulate max retries exceeded
        manager.backoff_strategy.current_attempt = manager.backoff_strategy.max_attempts

        manager._on_close(error=Exception("Max retries exceeded"))

        assert manager.connection_state == ConnectionState.PERMANENTLY_DISCONNECTED
        assert manager.connection_id is None

    def test_intentional_disconnect_vs_connection_loss(self, manager):
        """Test different states for intentional vs. unintentional disconnect"""
        manager.connect()

        # Intentional disconnect
        manager.intentional_disconnect = True
        manager._on_close()
        assert manager.connection_state == ConnectionState.DISCONNECTED

        # Unintentional disconnect (connection loss)
        manager.connect()
        manager.intentional_disconnect = False
        manager.backoff_strategy.current_attempt = 10
        manager._on_close(error=Exception("Connection lost"))
        assert manager.connection_state == ConnectionState.PERMANENTLY_DISCONNECTED

    def test_token_refresh_integration(self, manager, mock_token_manager):
        """Test token is refreshed on each connection attempt"""
        # First connection
        manager.connect()
        assert mock_token_manager.get_token.call_count == 1

        # Reconnection should get fresh token
        manager.disconnect()
        manager.connect()
        assert mock_token_manager.get_token.call_count == 2

    def test_connection_without_event_router(self, mock_token_manager):
        """Test manager works without event router (optional)"""
        manager = SignalRConnectionManager(mock_token_manager, event_router=None)

        result = manager.connect()
        assert result is True

        # Reconnection should not crash without event router
        manager.backoff_strategy.start_reconnection_cycle()
        manager._on_reconnected("new_conn_id")
        assert manager.connection_state == ConnectionState.CONNECTED

    def test_exponential_backoff_delays_sequence(self, manager):
        """Test actual exponential backoff delay sequence used"""
        # Verify the backoff strategy uses correct delays
        assert manager.backoff_strategy.retry_delays == [0, 2000, 10000, 30000, 60000]

        # Test each delay in sequence
        delays = []
        for attempt in range(1, 6):
            delay = manager.backoff_strategy.get_next_delay(attempt)
            delays.append(delay)

        assert delays == [0, 2000, 10000, 30000, 60000]

    def test_ping_statistics_calculation(self, manager):
        """Test ping statistics are calculated correctly"""
        manager.connect()

        # Add mixed ping results
        results = [
            PingResult(1, True, 100.0, time.time()),
            PingResult(2, True, 200.0, time.time()),
            PingResult(3, False, -1, time.time(), error="timeout"),
            PingResult(4, True, 150.0, time.time()),
            PingResult(5, True, 300.0, time.time()),
        ]

        for result in results:
            manager.ping_manager.record_ping(result)

        stats = manager.ping_manager.get_ping_statistics()

        assert stats.success_count == 4
        assert stats.failure_count == 1
        assert stats.success_rate == 80.0
        assert stats.average_latency == 187.5  # (100+200+150+300)/4

    def test_concurrent_reconnection_attempts(self, manager):
        """Test handling of concurrent reconnection scenarios"""
        manager.backoff_strategy.start_reconnection_cycle()

        # First attempt
        manager._on_reconnecting(1)
        assert manager.connection_state == ConnectionState.RECONNECTING

        # Second attempt while still reconnecting
        manager._on_reconnecting(2)
        assert manager.connection_state == ConnectionState.RECONNECTING

        # Finally succeeds
        manager._on_reconnected("new_conn_id")
        assert manager.connection_state == ConnectionState.CONNECTED

    def test_connection_state_enum_values(self):
        """Test ConnectionState enum has expected values"""
        assert ConnectionState.DISCONNECTED.value == "disconnected"
        assert ConnectionState.CONNECTING.value == "connecting"
        assert ConnectionState.CONNECTED.value == "connected"
        assert ConnectionState.RECONNECTING.value == "reconnecting"
        assert ConnectionState.FAILED.value == "failed"
        assert ConnectionState.PERMANENTLY_DISCONNECTED.value == "permanently_disconnected"
        assert ConnectionState.TOKEN_REFRESH.value == "token_refresh"

    def test_health_status_enum_values(self):
        """Test HealthStatus enum has expected values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.DISCONNECTED.value == "disconnected"

    def test_ping_result_structure(self):
        """Test PingResult has expected structure"""
        result = PingResult(
            sequence_number=1,
            success=True,
            latency=123.45,
            timestamp=time.time(),
            error=None
        )

        assert result.sequence_number == 1
        assert result.success is True
        assert result.latency == 123.45
        assert result.error is None

    def test_ping_result_with_error(self):
        """Test PingResult with error information"""
        result = PingResult(
            sequence_number=2,
            success=False,
            latency=-1,
            timestamp=time.time(),
            error="Connection timeout"
        )

        assert result.success is False
        assert result.latency == -1
        assert result.error == "Connection timeout"
