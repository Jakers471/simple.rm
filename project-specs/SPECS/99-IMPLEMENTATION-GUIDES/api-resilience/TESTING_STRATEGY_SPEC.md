---
doc_id: GUIDE-005
title: Testing Strategy Specification
version: 2.0
status: DRAFT
last_updated: 2025-10-22
purpose: Comprehensive testing strategy for API resilience layer and risk rules
dependencies: [API_RESILIENCE_OVERVIEW.md, IMPLEMENTATION_ROADMAP_V2.md]
---

# Testing Strategy Specification

**Purpose:** Define comprehensive testing requirements for the API resilience layer, risk rules engine, and integration points to ensure production-ready reliability.

---

## 📋 Table of Contents

1. [Testing Overview](#testing-overview)
2. [Unit Testing](#unit-testing)
3. [Integration Testing](#integration-testing)
4. [Chaos Engineering](#chaos-engineering)
5. [Performance Testing](#performance-testing)
6. [End-to-End Testing](#end-to-end-testing)
7. [Test Coverage Requirements](#test-coverage-requirements)
8. [Test Data Management](#test-data-management)
9. [CI/CD Integration](#cicd-integration)

---

## 🎯 Testing Overview

### Testing Pyramid

```
                    ┌─────────────┐
                    │   E2E (5%)  │
                    │  Manual +   │
                    │  Automated  │
                    └─────────────┘
                 ┌──────────────────┐
                 │  Integration (15%)│
                 │  Component Tests │
                 └──────────────────┘
            ┌─────────────────────────────┐
            │      Chaos Tests (10%)      │
            │  Network Failures, Errors   │
            └─────────────────────────────┘
     ┌────────────────────────────────────────────┐
     │           Unit Tests (70%)                  │
     │  Functions, Classes, Modules               │
     └────────────────────────────────────────────┘
```

### Testing Goals

| Goal | Target | Priority |
|------|--------|----------|
| **Unit Test Coverage** | 90%+ | CRITICAL |
| **Integration Test Coverage** | 80%+ | HIGH |
| **Chaos Test Pass Rate** | 100% | CRITICAL |
| **Performance Benchmarks** | <10ms latency | CRITICAL |
| **Zero Duplicates** | In all network failure tests | CRITICAL |
| **Zero Data Loss** | In reconnection tests | CRITICAL |

---

## 🧪 Unit Testing

### Test Framework

```python
# Using pytest for all unit tests
# pytest-asyncio for async tests
# pytest-mock for mocking
# pytest-cov for coverage

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
```

### 1. Token Manager Tests (15+ tests)

```python
# tests/api/auth/test_token_manager.py

class TestTokenManager:
    """Unit tests for Token Manager"""

    @pytest_asyncio.fixture
    async def token_manager(self):
        """Create Token Manager instance for testing"""
        config = TokenManagerConfig(
            refresh_buffer_seconds=7200,
            max_refresh_retries=3,
            storage_type='memory'
        )
        manager = TokenManager(config)
        await manager.initialize()
        return manager

    async def test_token_refresh_at_buffer_threshold(self, token_manager):
        """Test token refreshes automatically 2 hours before expiry"""
        # Set token that expires in 2 hours
        token_manager._token_state = TokenState(
            token="test_token",
            expiry=datetime.now() + timedelta(hours=2, minutes=1),
            refresh_time=datetime.now()
        )

        # Should not refresh yet (1 minute buffer remaining)
        assert not token_manager._needs_refresh()

        # Move time forward 2 minutes
        token_manager._token_state.expiry = datetime.now() + timedelta(hours=1, minutes=59)

        # Should refresh now (within 2-hour buffer)
        assert token_manager._needs_refresh()

    async def test_token_refresh_failure_fallback(self, token_manager):
        """Test fallback to re-authentication on refresh failure"""
        # Mock refresh endpoint to fail
        with patch.object(token_manager, '_refresh_token', side_effect=APIError("Refresh failed")):
            # Mock re-authentication to succeed
            with patch.object(token_manager, '_authenticate', return_value="new_token"):
                result = await token_manager.get_valid_token()

                # Should have re-authenticated
                assert result == "new_token"

    async def test_concurrent_requests_during_refresh(self, token_manager):
        """Test concurrent token requests during refresh"""
        # Simulate 10 concurrent requests during refresh
        tasks = [token_manager.get_valid_token() for _ in range(10)]

        # All should get the same token (only one refresh)
        tokens = await asyncio.gather(*tasks)
        assert all(t == tokens[0] for t in tokens)

    async def test_token_encryption_decryption(self, token_manager):
        """Test token encryption and decryption"""
        original_token = "test_token_12345"

        # Encrypt
        encrypted = token_manager._encrypt_token(original_token)
        assert encrypted != original_token

        # Decrypt
        decrypted = token_manager._decrypt_token(encrypted)
        assert decrypted == original_token

    async def test_token_expiration_detection(self, token_manager):
        """Test detection of expired tokens"""
        # Set expired token
        token_manager._token_state = TokenState(
            token="expired_token",
            expiry=datetime.now() - timedelta(hours=1),
            refresh_time=datetime.now() - timedelta(hours=25)
        )

        # Should detect expiration
        assert token_manager._is_expired()

    # ... 10+ more tests
```

### 2. SignalR Connection Manager Tests (20+ tests)

```python
# tests/api/signalr/test_connection_manager.py

class TestSignalRConnectionManager:
    """Unit tests for SignalR Connection Manager"""

    @pytest_asyncio.fixture
    async def connection_manager(self, token_manager_mock):
        """Create SignalR Connection Manager for testing"""
        config = SignalRConfig(
            max_reconnect_attempts=10,
            reconnect_delays=[0, 2000, 10000, 30000, 60000],
            ping_interval=30000,
            ping_timeout=5000
        )
        manager = SignalRConnectionManager(config, token_manager_mock)
        return manager

    async def test_connection_lifecycle(self, connection_manager):
        """Test connect -> connected -> disconnect lifecycle"""
        # Start disconnected
        assert connection_manager.state == ConnectionState.DISCONNECTED

        # Connect
        await connection_manager.connect()
        assert connection_manager.state == ConnectionState.CONNECTED

        # Disconnect
        await connection_manager.disconnect()
        assert connection_manager.state == ConnectionState.DISCONNECTED

    async def test_exponential_backoff_delays(self, connection_manager):
        """Test exponential backoff follows configured delays"""
        connection_manager._connection = Mock()
        connection_manager._connection.start = AsyncMock(side_effect=ConnectionError("Connection failed"))

        delays_used = []

        original_sleep = asyncio.sleep
        async def mock_sleep(delay):
            delays_used.append(delay * 1000)  # Convert to ms
            await original_sleep(0.001)  # Sleep 1ms instead

        with patch('asyncio.sleep', side_effect=mock_sleep):
            try:
                await connection_manager._reconnect_loop()
            except MaxReconnectAttemptsError:
                pass

        # Should have used configured delays (converted from ms to seconds)
        expected_delays = [0, 2000, 10000, 30000, 60000]
        assert delays_used[:5] == expected_delays

    async def test_health_monitoring_detects_stale_connection(self, connection_manager):
        """Test health monitor detects stale connections"""
        # Set up connection with stale last_ping_time
        connection_manager._connection = Mock()
        connection_manager._connection_state = ConnectionState.CONNECTED
        connection_manager._last_ping_time = datetime.now() - timedelta(minutes=3)

        # Check health
        is_healthy = await connection_manager._check_health()

        # Should detect stale connection (>2 minutes)
        assert not is_healthy

    async def test_auto_resubscribe_on_reconnect(self, connection_manager):
        """Test automatic resubscription after reconnection"""
        # Mock subscriptions
        connection_manager._subscriptions = ["positions", "orders", "trades"]
        connection_manager._connection = Mock()
        connection_manager._connection.invoke = AsyncMock()

        # Trigger reconnection
        await connection_manager._handle_reconnected("conn_123")

        # Should have resubscribed to all
        assert connection_manager._connection.invoke.call_count == 3

    async def test_onclose_handler_triggers_reconnection(self, connection_manager):
        """Test onclose handler triggers reconnection"""
        connection_manager._connection = Mock()
        connection_manager._reconnect_loop = AsyncMock()

        # Trigger close
        await connection_manager._handle_close(None)

        # Should have triggered reconnection
        connection_manager._reconnect_loop.assert_called_once()

    # ... 15+ more tests
```

### 3. Error Handler Tests (25+ tests)

```python
# tests/api/error_handler/test_error_handler.py

class TestErrorHandler:
    """Unit tests for Error Handler"""

    @pytest.fixture
    def error_handler(self, rate_limiter_mock, circuit_breaker_mock):
        """Create Error Handler for testing"""
        config = ErrorHandlerConfig(
            max_attempts=5,
            backoff_base=1000,
            backoff_multiplier=2
        )
        handler = ErrorHandler(config, rate_limiter_mock, circuit_breaker_mock)
        return handler

    async def test_retry_transient_errors(self, error_handler):
        """Test retries transient errors (429, 500, 503)"""
        call_count = 0

        async def api_call_with_transient_error():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise APIError("Service unavailable", status_code=503)
            return "success"

        result = await error_handler.execute(api_call_with_transient_error)

        # Should have retried twice and succeeded on 3rd attempt
        assert call_count == 3
        assert result == "success"

    async def test_no_retry_permanent_errors(self, error_handler):
        """Test doesn't retry permanent errors (400, 401, 404)"""
        call_count = 0

        async def api_call_with_permanent_error():
            nonlocal call_count
            call_count += 1
            raise APIError("Bad request", status_code=400)

        with pytest.raises(APIError):
            await error_handler.execute(api_call_with_permanent_error)

        # Should have failed immediately without retry
        assert call_count == 1

    async def test_max_retry_limit(self, error_handler):
        """Test stops after max retry attempts"""
        call_count = 0

        async def api_call_always_fails():
            nonlocal call_count
            call_count += 1
            raise APIError("Service unavailable", status_code=503)

        with pytest.raises(MaxRetriesExceededError):
            await error_handler.execute(api_call_always_fails)

        # Should have tried 5 times (1 initial + 4 retries)
        assert call_count == 5

    async def test_exponential_backoff_timing(self, error_handler):
        """Test exponential backoff delays"""
        delays_used = []

        async def failing_call():
            raise APIError("Temporary failure", status_code=503)

        original_sleep = asyncio.sleep
        async def mock_sleep(delay):
            delays_used.append(delay * 1000)  # Convert to ms
            await original_sleep(0.001)

        with patch('asyncio.sleep', side_effect=mock_sleep):
            with pytest.raises(MaxRetriesExceededError):
                await error_handler.execute(failing_call)

        # Should use exponential backoff: 1s, 2s, 4s, 8s
        expected_delays = [1000, 2000, 4000, 8000]
        assert delays_used == expected_delays

    async def test_circuit_breaker_integration(self, error_handler):
        """Test integration with circuit breaker"""
        # Open circuit breaker
        error_handler.circuit_breaker.is_open = Mock(return_value=True)

        async def api_call():
            return "success"

        with pytest.raises(ServiceUnavailableError):
            await error_handler.execute(api_call)

    # ... 20+ more tests
```

### 4. Rate Limiter Tests (10+ tests)

```python
# tests/api/rate_limiter/test_rate_limiter.py

class TestRateLimiter:
    """Unit tests for Rate Limiter"""

    @pytest.fixture
    def rate_limiter(self):
        """Create Rate Limiter for testing"""
        config = RateLimiterConfig(
            requests=50,
            window_seconds=30,
            queue_size=100
        )
        limiter = RateLimiter(config)
        return limiter

    async def test_allows_requests_under_limit(self, rate_limiter):
        """Test allows requests when under limit"""
        # Make 49 requests (under limit of 50)
        for _ in range(49):
            await rate_limiter.throttle()

        # Should complete without throttling
        # (test passes if no exception raised)

    async def test_throttles_requests_over_limit(self, rate_limiter):
        """Test throttles requests when over limit"""
        # Make 50 requests (at limit)
        for _ in range(50):
            await rate_limiter.throttle()

        # 51st request should be throttled
        start_time = time.time()
        await rate_limiter.throttle()
        elapsed_time = time.time() - start_time

        # Should have waited (at least 1ms)
        assert elapsed_time > 0.001

    async def test_sliding_window_tracking(self, rate_limiter):
        """Test sliding window removes old requests"""
        # Make 50 requests
        for _ in range(50):
            await rate_limiter.throttle()

        # Wait for window to expire (30 seconds)
        await asyncio.sleep(30.1)

        # Should allow new requests (window expired)
        await rate_limiter.throttle()  # Should not throttle

    async def test_queue_overflow_handling(self, rate_limiter):
        """Test handles queue overflow"""
        # Fill queue
        rate_limiter._queue_size = 5
        tasks = [rate_limiter.throttle() for _ in range(100)]

        # Should handle overflow gracefully
        await asyncio.gather(*tasks, return_exceptions=True)

    # ... 6+ more tests
```

### 5. Circuit Breaker Tests (12+ tests)

```python
# tests/api/circuit_breaker/test_circuit_breaker.py

class TestCircuitBreaker:
    """Unit tests for Circuit Breaker"""

    @pytest.fixture
    def circuit_breaker(self):
        """Create Circuit Breaker for testing"""
        config = CircuitBreakerConfig(
            failure_threshold=5,
            timeout=60000,
            half_open_requests=3
        )
        breaker = CircuitBreaker(config)
        return breaker

    def test_starts_in_closed_state(self, circuit_breaker):
        """Test circuit starts in closed state"""
        assert circuit_breaker.state == CircuitState.CLOSED
        assert not circuit_breaker.is_open()

    def test_opens_after_threshold_failures(self, circuit_breaker):
        """Test circuit opens after failure threshold"""
        # Record 5 failures
        for _ in range(5):
            circuit_breaker.record_failure()

        # Should be open now
        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.is_open()

    def test_transitions_to_half_open_after_timeout(self, circuit_breaker):
        """Test circuit transitions to half-open after timeout"""
        # Open circuit
        for _ in range(5):
            circuit_breaker.record_failure()

        # Fast-forward time past timeout
        circuit_breaker._last_failure_time = time.time() - 61  # 61 seconds ago

        # Check if open (should transition to half-open)
        is_open = circuit_breaker.is_open()

        assert circuit_breaker.state == CircuitState.HALF_OPEN
        assert not is_open

    def test_closes_on_success_in_half_open(self, circuit_breaker):
        """Test circuit closes on success in half-open state"""
        # Set to half-open
        circuit_breaker.state = CircuitState.HALF_OPEN

        # Record success
        circuit_breaker.record_success()

        # Should be closed
        assert circuit_breaker.state == CircuitState.CLOSED

    # ... 8+ more tests
```

### 6. Order Management Tests (15+ tests)

```python
# tests/api/orders/test_order_manager.py

class TestOrderManager:
    """Unit tests for Order Manager"""

    @pytest_asyncio.fixture
    async def order_manager(self, error_handler_mock):
        """Create Order Manager for testing"""
        config = OrderManagerConfig(
            verification_enabled=True,
            verification_timeout=5000,
            idempotency_enabled=True
        )
        manager = OrderManager(config, error_handler_mock)
        return manager

    async def test_order_verification_after_placement(self, order_manager):
        """Test verifies order exists after placement"""
        # Mock successful order placement
        order_manager.error_handler.execute = AsyncMock(return_value=OrderResponse(
            success=True,
            order_id="order_123"
        ))

        # Mock order verification
        order_manager._fetch_order_by_id = AsyncMock(return_value=Order(
            id="order_123",
            status=OrderStatus.OPEN
        ))

        result = await order_manager.place_order(OrderRequest(
            account_id=1,
            contract_id="NQ",
            size=1,
            type=OrderType.MARKET
        ))

        # Should have verified order
        assert result.success
        order_manager._fetch_order_by_id.assert_called_once_with("order_123")

    async def test_idempotency_prevents_duplicates(self, order_manager):
        """Test idempotency prevents duplicate orders"""
        order_request = OrderRequest(
            id="req_123",
            account_id=1,
            contract_id="NQ",
            size=1,
            type=OrderType.MARKET
        )

        # Place order first time
        order_manager.error_handler.execute = AsyncMock(return_value=OrderResponse(
            success=True,
            order_id="order_123"
        ))
        result1 = await order_manager.place_order(order_request)

        # Place same order again (duplicate)
        result2 = await order_manager.place_order(order_request)

        # Second call should return cached response
        assert result1.order_id == result2.order_id
        # Error handler should have been called only once
        assert order_manager.error_handler.execute.call_count == 1

    async def test_partial_fill_tracking(self, order_manager):
        """Test tracks partial fills correctly"""
        order_id = "order_123"

        # Simulate partial fill event
        await order_manager.handle_order_event(OrderEvent(
            order_id=order_id,
            fill_volume=5,
            size=10
        ))

        # Check partial fill tracking
        fill_status = order_manager.get_fill_status(order_id)
        assert fill_status.is_partial
        assert fill_status.fill_percent == 0.5

    # ... 12+ more tests
```

---

## 🔗 Integration Testing

### Integration Test Scenarios

```python
# tests/integration/test_api_resilience_integration.py

class TestAPIResilienceIntegration:
    """Integration tests for API resilience layer"""

    @pytest_asyncio.fixture
    async def integrated_system(self):
        """Setup integrated system with all components"""
        # Load configuration
        config = ConfigurationManager("tests/fixtures/test_config.yaml")
        config.load()

        # Initialize all components
        token_manager = TokenManager(config.get_token_manager_config())
        await token_manager.initialize()

        rate_limiter = RateLimiter(config.get_rate_limiter_config())
        circuit_breaker = CircuitBreaker(config.get_circuit_breaker_config())
        error_handler = ErrorHandler(config.get_error_handler_config(), rate_limiter, circuit_breaker)

        signalr_manager = SignalRConnectionManager(
            config.get_signalr_config(),
            token_manager
        )

        state_manager = StateManager("tests/fixtures/test.db")
        await state_manager.initialize()

        state_reconciler = StateReconciler(
            config.get_state_reconciler_config(),
            signalr_manager,
            state_manager,
            error_handler
        )

        order_manager = OrderManager(
            config.get_order_manager_config(),
            error_handler
        )

        return IntegratedSystem(
            token_manager=token_manager,
            signalr_manager=signalr_manager,
            state_reconciler=state_reconciler,
            order_manager=order_manager,
            error_handler=error_handler
        )

    async def test_token_refresh_during_active_operation(self, integrated_system):
        """Test token refreshes automatically during long operation"""
        # Set token to expire soon
        integrated_system.token_manager._token_state.expiry = datetime.now() + timedelta(hours=1, minutes=59)

        # Start long operation
        async def long_operation():
            # Should trigger token refresh during this operation
            for i in range(10):
                await integrated_system.order_manager.fetch_orders()
                await asyncio.sleep(0.5)

        await long_operation()

        # Token should have been refreshed
        assert integrated_system.token_manager._token_state.expiry > datetime.now() + timedelta(hours=22)

    async def test_signalr_reconnection_with_state_sync(self, integrated_system):
        """Test SignalR reconnects and syncs state"""
        # Connect SignalR
        await integrated_system.signalr_manager.connect()

        # Simulate disconnection
        await integrated_system.signalr_manager._handle_close(None)

        # Wait for reconnection
        await asyncio.sleep(5)

        # Should have reconnected and reconciled state
        assert integrated_system.signalr_manager.state == ConnectionState.CONNECTED
        # State reconciler should have been called
        # (verify via logs or mock tracking)

    async def test_rate_limit_enforcement_across_components(self, integrated_system):
        """Test rate limiting works across all components"""
        # Submit burst of requests (>50 in 30s for history endpoint)
        tasks = [
            integrated_system.order_manager.fetch_historical_data()
            for _ in range(60)
        ]

        start_time = time.time()
        await asyncio.gather(*tasks)
        elapsed_time = time.time() - start_time

        # Should have taken longer due to throttling
        assert elapsed_time > 30  # At least 30 seconds for rate limit window

    async def test_circuit_breaker_triggers_fallback(self, integrated_system):
        """Test circuit breaker opens and triggers fallback"""
        # Simulate 5 consecutive failures
        with patch.object(integrated_system.order_manager, '_place_order_internal', side_effect=APIError("Server error", 500)):
            for _ in range(5):
                try:
                    await integrated_system.order_manager.place_order(test_order_request)
                except:
                    pass

        # Circuit should be open
        assert integrated_system.error_handler.circuit_breaker.is_open()

        # Next request should fail immediately (circuit open)
        with pytest.raises(ServiceUnavailableError):
            await integrated_system.order_manager.place_order(test_order_request)

    async def test_order_placement_with_network_failure(self, integrated_system):
        """Test order placement handles network failure gracefully"""
        # Simulate network failure after order sent but before response
        with patch.object(integrated_system.order_manager, '_place_order_internal', side_effect=ConnectionError("Network error")):
            with pytest.raises(ConnectionError):
                await integrated_system.order_manager.place_order(test_order_request)

        # Verify order verification was attempted
        # (Should not create duplicate order on retry)
```

---

## 💥 Chaos Engineering Tests

### Chaos Test Suite

```python
# tests/chaos/test_network_failures.py

class TestNetworkChaos:
    """Chaos engineering tests for network failures"""

    async def test_network_interruption_during_order_placement(self, integrated_system):
        """Test network failure during order placement"""
        # Mock network to fail randomly
        failure_injector = NetworkFailureInjector(failure_rate=0.5)

        with failure_injector:
            # Place 100 orders
            results = []
            for i in range(100):
                try:
                    result = await integrated_system.order_manager.place_order(
                        create_test_order(f"order_{i}")
                    )
                    results.append(result)
                except Exception as e:
                    # Network failures expected
                    pass

        # Verify no duplicate orders created
        order_ids = [r.order_id for r in results]
        assert len(order_ids) == len(set(order_ids))  # All unique

    async def test_token_expiration_mid_operation(self, integrated_system):
        """Test handles token expiration during operation"""
        # Set token to expire soon
        integrated_system.token_manager._token_state.expiry = datetime.now() + timedelta(seconds=5)

        # Start long operation
        async def long_operation():
            for i in range(20):
                await integrated_system.order_manager.fetch_orders()
                await asyncio.sleep(1)

        # Should complete despite token expiration
        await long_operation()

    async def test_signalr_disconnection_during_high_volume(self, integrated_system):
        """Test SignalR handles disconnection during high event volume"""
        # Connect SignalR
        await integrated_system.signalr_manager.connect()

        # Start high-volume event stream
        event_generator = HighVolumeEventGenerator(events_per_second=60)

        # Inject random disconnections
        disconnection_injector = SignalRDisconnectionInjector(disconnect_probability=0.1)

        with event_generator, disconnection_injector:
            # Run for 60 seconds
            await asyncio.sleep(60)

        # Verify no data loss
        # All events should have been processed or reconciled
        assert integrated_system.state_manager.verify_state_consistency()

    async def test_api_rate_limit_hit(self, integrated_system):
        """Test handles API rate limit gracefully"""
        # Submit burst exceeding rate limit
        tasks = [
            integrated_system.order_manager.fetch_orders()
            for _ in range(300)  # Exceeds 200 req/60s limit
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Should have completed all requests (with throttling)
        # No 429 errors should have occurred
        errors_429 = [r for r in results if isinstance(r, APIError) and r.status_code == 429]
        assert len(errors_429) == 0

    async def test_server_error_cascade(self, integrated_system):
        """Test handles cascading server errors"""
        # Simulate repeated 500 errors
        error_count = 0

        async def failing_api_call():
            nonlocal error_count
            error_count += 1
            if error_count < 20:
                raise APIError("Internal server error", status_code=500)
            return "success"

        with patch.object(integrated_system.order_manager, '_fetch_orders', side_effect=failing_api_call):
            # Should eventually recover (circuit breaker opens, then recovers)
            for attempt in range(30):
                try:
                    await integrated_system.order_manager.fetch_orders()
                    break  # Success
                except:
                    await asyncio.sleep(1)

        # Should have recovered after circuit breaker timeout
        assert error_count >= 5  # Circuit breaker opened
```

---

## ⚡ Performance Testing

### Performance Benchmarks

```python
# tests/performance/test_latency_benchmarks.py

class TestPerformanceBenchmarks:
    """Performance benchmarks for event processing"""

    @pytest.mark.benchmark
    async def test_event_processing_latency(self, integrated_system, benchmark):
        """Benchmark event processing latency (<10ms target)"""
        # Create test event
        event = create_test_position_event()

        # Benchmark event processing
        def process_event():
            asyncio.run(integrated_system.risk_engine.handle_position_event(event))

        result = benchmark(process_event)

        # Assert latency < 10ms
        assert result.stats.mean < 0.010  # 10ms

    @pytest.mark.benchmark
    async def test_api_call_throughput(self, integrated_system, benchmark):
        """Benchmark API call throughput"""
        async def make_api_calls():
            tasks = [integrated_system.order_manager.fetch_orders() for _ in range(100)]
            await asyncio.gather(*tasks)

        result = benchmark.pedantic(make_api_calls, rounds=10)

        # Assert can handle 100 calls in reasonable time
        assert result.stats.mean < 5.0  # 5 seconds for 100 calls

    @pytest.mark.benchmark
    async def test_signalr_event_throughput(self, integrated_system, benchmark):
        """Benchmark SignalR event handling throughput"""
        events = [create_test_position_event() for _ in range(1000)]

        async def process_events():
            for event in events:
                await integrated_system.risk_engine.handle_position_event(event)

        result = benchmark.pedantic(process_events, rounds=5)

        # Assert can handle 60+ events/second (1000 events in <17 seconds)
        assert result.stats.mean < 17.0

    @pytest.mark.benchmark
    async def test_memory_usage(self, integrated_system):
        """Test memory usage stays under 100 MB"""
        import tracemalloc
        tracemalloc.start()

        # Process 10,000 events
        for i in range(10000):
            event = create_test_position_event()
            await integrated_system.risk_engine.handle_position_event(event)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Assert peak memory < 100 MB
        assert peak < 100 * 1024 * 1024  # 100 MB
```

---

## 🎭 End-to-End Testing

### E2E Test Scenarios

```python
# tests/e2e/test_full_system.py

class TestFullSystemE2E:
    """End-to-end tests with real TopstepX demo account"""

    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_complete_trading_workflow(self, live_system):
        """Test complete workflow from startup to enforcement"""
        # 1. System startup
        await live_system.startup()
        assert live_system.is_running()

        # 2. Place trade (via external platform)
        logger.info("Place a trade in TopstepX platform now...")
        await asyncio.sleep(10)  # Wait for manual trade

        # 3. Wait for event
        position_event = await live_system.wait_for_event("position", timeout=30)
        assert position_event is not None

        # 4. Verify state updated
        positions = await live_system.state_manager.get_positions()
        assert len(positions) > 0

        # 5. Trigger rule breach (manually or via API)
        # ... test enforcement

        # 6. Graceful shutdown
        await live_system.shutdown()

    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_24_hour_reliability(self, live_system):
        """Test 24-hour continuous operation"""
        await live_system.startup()

        start_time = time.time()
        errors = []

        # Run for 24 hours (or shorter for testing)
        while time.time() - start_time < 86400:
            try:
                # Check health every minute
                health = await live_system.health_check()
                if not health.is_healthy:
                    errors.append(f"Health check failed at {time.time() - start_time}s")

                await asyncio.sleep(60)

            except Exception as e:
                errors.append(f"Error at {time.time() - start_time}s: {e}")

        # Assert zero errors
        assert len(errors) == 0

        await live_system.shutdown()
```

---

## 📊 Test Coverage Requirements

### Coverage Targets

| Component | Unit Tests | Integration Tests | Chaos Tests | Coverage Target |
|-----------|-----------|------------------|-------------|-----------------|
| Token Manager | 15+ | 3+ | 2+ | 95%+ |
| SignalR Manager | 20+ | 5+ | 3+ | 95%+ |
| Error Handler | 25+ | 5+ | 5+ | 90%+ |
| Rate Limiter | 10+ | 3+ | 2+ | 90%+ |
| Circuit Breaker | 12+ | 3+ | 2+ | 90%+ |
| Order Manager | 15+ | 5+ | 3+ | 95%+ |
| State Reconciler | 10+ | 3+ | 2+ | 90%+ |
| Risk Rules | 50+ | 12+ | 6+ | 100%+ |

### Coverage Measurement

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html

# Enforce coverage thresholds
pytest --cov=src --cov-fail-under=90
```

---

## 📝 Summary

**Testing Strategy:**
- 70% Unit tests (fast, isolated)
- 10% Chaos tests (network failures, errors)
- 15% Integration tests (component interactions)
- 5% E2E tests (full system)

**Key Metrics:**
- 90%+ unit test coverage (CRITICAL)
- 100% chaos test pass rate (CRITICAL)
- <10ms event processing latency (CRITICAL)
- Zero duplicates in network failure tests (CRITICAL)
- Zero data loss in reconnection tests (CRITICAL)

**Test Execution:**
- Unit tests: Run on every commit (CI/CD)
- Integration tests: Run on every PR
- Chaos tests: Run nightly
- E2E tests: Run weekly with demo account
- Performance tests: Run before releases

---

**Document Status:** DRAFT - Ready for implementation
