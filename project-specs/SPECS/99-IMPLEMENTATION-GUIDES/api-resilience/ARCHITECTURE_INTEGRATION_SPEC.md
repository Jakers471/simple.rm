---
doc_id: GUIDE-003
title: Architecture Integration Specification
version: 2.0
status: DRAFT
last_updated: 2025-10-22
purpose: Define how all API resilience components integrate and interact
dependencies: [API_RESILIENCE_OVERVIEW.md]
---

# Architecture Integration Specification

**Purpose:** Specify how Token Manager, SignalR Manager, Error Handler, Rate Limiter, Circuit Breaker, Order Management, and State Reconciliation components work together to create a resilient API integration layer.

---

## 📋 Table of Contents

1. [Component Overview](#component-overview)
2. [Component Interactions](#component-interactions)
3. [Data Flow](#data-flow)
4. [Error Propagation](#error-propagation)
5. [State Management](#state-management)
6. [Configuration Integration](#configuration-integration)
7. [Initialization Sequence](#initialization-sequence)
8. [Shutdown Sequence](#shutdown-sequence)

---

## 🏗️ Component Overview

### Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Risk Rules Engine                        │
│          (Depends on resilient API infrastructure)           │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│              API Resilience Layer (Phase 0)                  │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Token     │  │   SignalR    │  │    Error     │       │
│  │  Manager    │  │  Connection  │  │   Handler    │       │
│  │             │  │   Manager    │  │              │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │    Rate     │  │   Circuit    │  │    State     │       │
│  │  Limiter    │  │   Breaker    │  │ Reconciler   │       │
│  │             │  │              │  │              │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
│                                                               │
│  ┌─────────────────────────────────────────────────┐        │
│  │         Order Management                         │        │
│  │  (Verification, Idempotency, Partial Fills)     │        │
│  └─────────────────────────────────────────────────┘        │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                   TopstepX Gateway API                       │
│  REST API (https://gateway.topstepx.com)                    │
│  SignalR Hubs (wss://rtc.topstepx.com)                      │
└──────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Dependencies |
|-----------|---------------|--------------|
| **Token Manager** | Token lifecycle, refresh, storage | None (foundation) |
| **SignalR Manager** | Real-time connection, reconnection | Token Manager |
| **Error Handler** | Error classification, retry logic | Rate Limiter, Circuit Breaker |
| **Rate Limiter** | Request throttling, queuing | None |
| **Circuit Breaker** | Service health, failure detection | None |
| **State Reconciler** | State sync after reconnection | SignalR Manager |
| **Order Management** | Order verification, idempotency | Error Handler, Rate Limiter |

---

## 🔄 Component Interactions

### 1. Token Manager ↔ SignalR Connection Manager

**Interaction:** SignalR Manager uses Token Manager for authentication

```python
# SignalR Connection Manager
class SignalRConnectionManager:
    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
        self.connection = None

    async def connect(self):
        """Connect to SignalR with fresh token"""
        # Get valid token from Token Manager
        token = await self.token_manager.get_valid_token()

        # Build connection with token
        self.connection = (
            HubConnectionBuilder()
            .with_url(
                f"{SIGNALR_URL}?access_token={token}",
                options={
                    "access_token_factory": lambda: self.token_manager.get_valid_token()
                }
            )
            .build()
        )

        # Subscribe to token refresh events
        self.token_manager.on_token_refreshed(self._handle_token_refresh)

        await self.connection.start()

    async def _handle_token_refresh(self, new_token: str):
        """Reconnect with new token after refresh"""
        logger.info("Token refreshed, reconnecting SignalR...")
        await self.reconnect()
```

**Key Points:**
- SignalR Manager NEVER stores tokens directly
- SignalR Manager always calls `token_manager.get_valid_token()`
- Token Manager notifies SignalR Manager on token refresh
- SignalR Manager reconnects when token refreshed

---

### 2. Error Handler ↔ Rate Limiter

**Interaction:** Error Handler uses Rate Limiter to throttle retry attempts

```python
# Error Handler
class ErrorHandler:
    def __init__(self, rate_limiter: RateLimiter, circuit_breaker: CircuitBreaker):
        self.rate_limiter = rate_limiter
        self.circuit_breaker = circuit_breaker

    async def execute(self, api_call: Callable, *args, **kwargs):
        """Execute API call with error handling"""
        attempt = 0
        max_attempts = 5

        while attempt < max_attempts:
            try:
                # Check circuit breaker
                if self.circuit_breaker.is_open():
                    raise ServiceUnavailableError("Circuit breaker open")

                # Check rate limit before attempt
                await self.rate_limiter.throttle()

                # Execute API call
                result = await api_call(*args, **kwargs)

                # Update circuit breaker on success
                self.circuit_breaker.record_success()

                return result

            except Exception as e:
                # Update circuit breaker on failure
                self.circuit_breaker.record_failure()

                # Classify error
                if self._is_transient(e):
                    attempt += 1
                    backoff = self._calculate_backoff(attempt)

                    logger.warning(f"Transient error, retry {attempt}/{max_attempts} after {backoff}ms")
                    await asyncio.sleep(backoff / 1000)
                else:
                    # Permanent error, don't retry
                    raise

        raise MaxRetriesExceededError(f"Failed after {max_attempts} attempts")
```

**Key Points:**
- Rate Limiter enforces API rate limits
- Error Handler respects rate limits during retries
- Circuit Breaker prevents cascading failures
- Transient errors retried, permanent errors raised immediately

---

### 3. SignalR Manager ↔ State Reconciler

**Interaction:** State Reconciler triggered on SignalR reconnection

```python
# SignalR Connection Manager
class SignalRConnectionManager:
    def __init__(self, token_manager: TokenManager, state_reconciler: StateReconciler):
        self.token_manager = token_manager
        self.state_reconciler = state_reconciler
        self.connection = None

    def _setup_handlers(self):
        """Setup SignalR event handlers"""

        self.connection.on_reconnected = lambda connection_id: asyncio.create_task(
            self._handle_reconnected(connection_id)
        )

    async def _handle_reconnected(self, connection_id: str):
        """Handle successful reconnection"""
        logger.info(f"SignalR reconnected: {connection_id}")

        # Resubscribe to events
        await self._resubscribe_all()

        # Trigger state reconciliation
        await self.state_reconciler.reconcile()

        logger.info("State reconciliation complete")
```

**Key Points:**
- State Reconciler triggered AFTER reconnection
- State Reconciler triggered AFTER resubscription
- State Reconciler uses REST API (not SignalR)
- State Reconciler updates cached state

---

### 4. Error Handler ↔ Circuit Breaker

**Interaction:** Circuit Breaker prevents requests when service unhealthy

```python
# Circuit Breaker
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout_ms: int = 60000):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout_ms = timeout_ms
        self.last_failure_time = None

    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)"""
        if self.state == CircuitState.OPEN:
            # Check if timeout expired
            if time.time() - self.last_failure_time > self.timeout_ms / 1000:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker: OPEN → HALF_OPEN (timeout expired)")
                return False
            return True
        return False

    def record_failure(self):
        """Record API failure"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            if self.state == CircuitState.CLOSED:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker: CLOSED → OPEN ({self.failure_count} failures)")
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning("Circuit breaker: HALF_OPEN → OPEN (failure during testing)")

    def record_success(self):
        """Record API success"""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info("Circuit breaker: HALF_OPEN → CLOSED (service recovered)")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)
```

**Key Points:**
- Circuit Breaker tracks failure rate
- Circuit Breaker blocks requests when open
- Circuit Breaker allows testing when half-open
- Circuit Breaker resets on success

---

### 5. Order Management ↔ Error Handler + Rate Limiter

**Interaction:** Order Management uses Error Handler for resilient order operations

```python
# Order Management
class OrderManager:
    def __init__(self, error_handler: ErrorHandler, idempotency_manager: IdempotencyManager):
        self.error_handler = error_handler
        self.idempotency = idempotency_manager

    async def place_order(self, order_request: OrderRequest) -> OrderResponse:
        """Place order with verification and idempotency"""

        # Check idempotency (prevent duplicates)
        if self.idempotency.is_duplicate(order_request):
            logger.warning(f"Duplicate order detected: {order_request.id}")
            return self.idempotency.get_cached_response(order_request.id)

        # Place order (wrapped in error handler)
        response = await self.error_handler.execute(
            self._place_order_internal,
            order_request
        )

        # Cache response for idempotency
        self.idempotency.cache_response(order_request.id, response)

        # Verify order was placed
        if response.success:
            verified = await self._verify_order(response.order_id)
            if not verified:
                logger.error(f"Order verification failed: {response.order_id}")
                raise OrderVerificationError("Order not found after placement")

        return response

    async def _verify_order(self, order_id: str, timeout_ms: int = 5000) -> bool:
        """Verify order exists via REST API"""
        start_time = time.time()

        while time.time() - start_time < timeout_ms / 1000:
            # Fetch order (wrapped in error handler)
            order = await self.error_handler.execute(
                self._fetch_order_by_id,
                order_id
            )

            if order is not None:
                return True

            await asyncio.sleep(0.5)

        return False
```

**Key Points:**
- Order Management wraps all API calls in Error Handler
- Error Handler applies rate limiting and retries
- Idempotency Manager prevents duplicate orders
- Order verification confirms successful placement

---

## 📊 Data Flow

### Startup Flow

```
1. Application Startup
        │
        ▼
2. Load Configuration (config.yaml)
        │
        ▼
3. Initialize Token Manager
        ├─> Load stored token (if exists)
        ├─> Validate token expiry
        └─> Authenticate if needed (POST /api/Auth/loginKey)
        │
        ▼
4. Initialize Rate Limiter
        └─> Setup sliding window trackers
        │
        ▼
5. Initialize Circuit Breaker
        └─> Set to CLOSED state
        │
        ▼
6. Initialize Error Handler
        ├─> Inject Rate Limiter
        └─> Inject Circuit Breaker
        │
        ▼
7. Initialize SignalR Connection Manager
        ├─> Inject Token Manager
        ├─> Connect to User Hub (wss://rtc.topstepx.com/hubs/user)
        ├─> Setup event handlers (onconnected, onclose, etc.)
        └─> Subscribe to events (positions, orders, trades)
        │
        ▼
8. Initialize State Reconciler
        ├─> Inject SignalR Manager
        └─> Perform initial state sync (REST API)
        │
        ▼
9. Initialize Order Manager
        ├─> Inject Error Handler
        └─> Inject Idempotency Manager
        │
        ▼
10. Initialize Risk Rules Engine
        ├─> Load rule configurations
        ├─> Inject all dependencies
        └─> Start monitoring events
```

### Event Processing Flow

```
SignalR Event Received (e.g., GatewayUserPosition)
        │
        ▼
Event Router
        │
        ├─> Log event
        ├─> Validate event structure
        └─> Route to relevant risk rules
        │
        ▼
Risk Rule Evaluation
        │
        ├─> Check if breach occurred
        ├─> Calculate severity
        └─> Determine enforcement action
        │
        ▼
Enforcement Action (if breach)
        │
        ├─> Close Position / Cancel Order
        │   │
        │   ▼
        │   Order Manager.close_position()
        │   │
        │   ▼
        │   Error Handler.execute()
        │   │
        │   ├─> Circuit Breaker.is_open()? → Block if open
        │   ├─> Rate Limiter.throttle() → Wait if needed
        │   ├─> POST /api/Position/closeContract
        │   ├─> Handle errors (retry transient, raise permanent)
        │   └─> Circuit Breaker.record_success/failure()
        │   │
        │   ▼
        │   Order Manager.verify_closure()
        │   │
        │   └─> REST API: GET /api/Position/searchOpen
        │
        └─> Update State (lockout, enforcement log)
```

### Reconnection Flow

```
SignalR Connection Lost
        │
        ▼
SignalR Manager detects disconnection (onclose)
        │
        ├─> Log disconnection
        ├─> Update connection state: DISCONNECTED
        └─> Trigger reconnection logic
        │
        ▼
Exponential Backoff Retry Loop
        │
        ├─> Attempt 1: Delay 0ms
        ├─> Attempt 2: Delay 2000ms
        ├─> Attempt 3: Delay 10000ms
        ├─> Attempt 4: Delay 30000ms
        └─> Attempt 5+: Delay 60000ms
        │
        │ (Before each attempt)
        ▼
Token Manager.get_valid_token()
        │
        ├─> Check token expiry
        ├─> Refresh if needed (POST /api/Auth/validate)
        └─> Return valid token
        │
        ▼
SignalR Reconnection Attempt
        │
        ├─> SUCCESS → onreconnected handler
        │   │
        │   ▼
        │   Resubscribe to events
        │   │
        │   ├─> SubscribePositions(accountId)
        │   ├─> SubscribeOrders(accountId)
        │   └─> SubscribeTrades(accountId)
        │   │
        │   ▼
        │   State Reconciler.reconcile()
        │   │
        │   ├─> Fetch positions (POST /api/Position/searchOpen)
        │   ├─> Fetch orders (POST /api/Order/searchOpen)
        │   ├─> Compare with cached state
        │   ├─> Detect discrepancies (missed events)
        │   └─> Update cached state
        │   │
        │   ▼
        │   Resume normal event processing
        │
        └─> FAILURE → Continue exponential backoff
```

---

## 🚨 Error Propagation Strategy

### Error Classification

```python
class ErrorClassifier:
    """Classify errors for appropriate handling"""

    @staticmethod
    def classify(error: Exception) -> ErrorType:
        """Classify error as transient or permanent"""

        # Transient errors (retry)
        if isinstance(error, (
            requests.Timeout,
            requests.ConnectionError,
            SignalRConnectionError
        )):
            return ErrorType.TRANSIENT

        # HTTP errors
        if isinstance(error, requests.HTTPError):
            status_code = error.response.status_code

            # Transient HTTP errors (retry)
            if status_code in [408, 429, 500, 502, 503, 504]:
                return ErrorType.TRANSIENT

            # Permanent HTTP errors (don't retry)
            if status_code in [400, 401, 403, 404]:
                return ErrorType.PERMANENT

        # TopstepX API errors
        if isinstance(error, TopstepXAPIError):
            if error.error_code in TRANSIENT_ERROR_CODES:
                return ErrorType.TRANSIENT
            else:
                return ErrorType.PERMANENT

        # Unknown errors (don't retry by default)
        return ErrorType.PERMANENT
```

### Error Handling Chain

```
Exception Raised
        │
        ▼
Error Handler catches
        │
        ├─> Classify error (transient vs permanent)
        │
        ├─> If TRANSIENT:
        │   │
        │   ├─> Check retry attempts < max (5)
        │   ├─> Calculate backoff delay (exponential)
        │   ├─> Wait backoff delay
        │   ├─> Update circuit breaker (record_failure)
        │   └─> Retry operation
        │
        └─> If PERMANENT:
            │
            ├─> Log error (with context)
            ├─> Update circuit breaker (record_failure)
            └─> Raise exception (propagate to caller)
                │
                ▼
        Caller handles exception
                │
                ├─> Risk Rule: Log breach detection failure
                ├─> Enforcement: Log enforcement failure
                └─> Application: Continue operation (graceful degradation)
```

---

## 💾 State Management

### State Hierarchy

```
┌──────────────────────────────────────────────────────┐
│              Application State                        │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Connection State (In-Memory)               │    │
│  │  - Token state (token, expiry, refresh_time)│    │
│  │  - SignalR state (connected/reconnecting)   │    │
│  │  - Circuit breaker state (closed/open)      │    │
│  │  - Rate limiter state (request history)     │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Trading State (SQLite + In-Memory Cache)   │    │
│  │  - Positions (id, account, contract, size)  │    │
│  │  - Orders (id, status, fill_volume)         │    │
│  │  - Trades (id, price, pnl)                  │    │
│  │  - Account (balance, can_trade)             │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Rule State (SQLite)                        │    │
│  │  - Lockouts (account, rule, expiry)         │    │
│  │  - Enforcement logs (action, reason, time)  │    │
│  │  - Daily P&L (realized, unrealized)         │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### State Synchronization

```python
class StateReconciler:
    """Reconcile state after reconnection"""

    async def reconcile(self):
        """Sync state with TopstepX API"""

        logger.info("Starting state reconciliation...")

        # Fetch current state from API
        api_positions = await self._fetch_positions()
        api_orders = await self._fetch_orders()
        api_account = await self._fetch_account()

        # Compare with cached state
        cached_positions = self.state_manager.get_positions()
        cached_orders = self.state_manager.get_orders()

        # Detect discrepancies
        new_positions = self._find_new(api_positions, cached_positions)
        closed_positions = self._find_closed(api_positions, cached_positions)
        new_orders = self._find_new(api_orders, cached_orders)
        filled_orders = self._find_filled(api_orders, cached_orders)

        # Log discrepancies (missed events)
        if new_positions:
            logger.warning(f"Missed {len(new_positions)} position open events during disconnection")
        if closed_positions:
            logger.warning(f"Missed {len(closed_positions)} position close events during disconnection")
        if new_orders:
            logger.warning(f"Missed {len(new_orders)} order place events during disconnection")
        if filled_orders:
            logger.warning(f"Missed {len(filled_orders)} order fill events during disconnection")

        # Update cached state
        self.state_manager.update_positions(api_positions)
        self.state_manager.update_orders(api_orders)
        self.state_manager.update_account(api_account)

        # Persist to database
        await self.state_manager.persist()

        logger.info("State reconciliation complete")
```

---

## ⚙️ Configuration Integration

### Configuration Hierarchy

```yaml
# config.yaml - Master configuration

# API Configuration
api:
  baseUrl: "https://gateway.topstepx.com"
  timeout: 30000

# Authentication Configuration (Token Manager)
authentication:
  tokenRefresh:
    bufferSeconds: 7200  # Used by Token Manager
    maxRetries: 3
  storage:
    type: "encrypted"  # Used by Token Manager
    encryption: "AES-256"

# SignalR Configuration (SignalR Manager)
signalr:
  reconnection:
    maxAttempts: 10  # Used by SignalR Manager
    delays: [0, 2000, 10000, 30000, 60000]  # Used by Backoff Strategy
  health:
    pingInterval: 30000  # Used by Health Monitor
    pingTimeout: 5000
    staleThreshold: 120000

# Error Handling Configuration (Error Handler, Rate Limiter, Circuit Breaker)
errorHandling:
  retries:
    maxAttempts: 5  # Used by Error Handler
    backoffBase: 1000
    backoffMultiplier: 2
  rateLimit:
    history:
      requests: 50  # Used by Rate Limiter (history endpoint)
      windowSeconds: 30
    general:
      requests: 200  # Used by Rate Limiter (general endpoints)
      windowSeconds: 60
  circuitBreaker:
    failureThreshold: 5  # Used by Circuit Breaker
    timeout: 60000

# Order Management Configuration (Order Manager)
orderManagement:
  verification:
    enabled: true  # Used by Order Manager
    timeout: 5000
  idempotency:
    enabled: true  # Used by Idempotency Manager
    cacheTTL: 3600

# State Reconciliation Configuration (State Reconciler)
stateReconciliation:
  enabled: true  # Used by State Reconciler
  onReconnect: true
  minInterval: 5000
```

### Configuration Loading

```python
class ConfigManager:
    """Load and provide configuration to all components"""

    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def get_token_manager_config(self) -> TokenManagerConfig:
        """Extract Token Manager configuration"""
        auth_config = self.config['authentication']
        return TokenManagerConfig(
            refresh_buffer_seconds=auth_config['tokenRefresh']['bufferSeconds'],
            max_refresh_retries=auth_config['tokenRefresh']['maxRetries'],
            storage_type=auth_config['storage']['type'],
            encryption=auth_config['storage']['encryption']
        )

    def get_signalr_config(self) -> SignalRConfig:
        """Extract SignalR Manager configuration"""
        signalr_config = self.config['signalr']
        return SignalRConfig(
            max_reconnect_attempts=signalr_config['reconnection']['maxAttempts'],
            reconnect_delays=signalr_config['reconnection']['delays'],
            ping_interval=signalr_config['health']['pingInterval'],
            ping_timeout=signalr_config['health']['pingTimeout'],
            stale_threshold=signalr_config['health']['staleThreshold']
        )

    # ... similar methods for other components
```

---

## 🚀 Initialization Sequence

```python
class Application:
    """Main application orchestrator"""

    async def initialize(self):
        """Initialize all components in correct order"""

        # 1. Load configuration
        self.config_manager = ConfigManager("config/config.yaml")

        # 2. Initialize Token Manager (foundation, no dependencies)
        token_config = self.config_manager.get_token_manager_config()
        self.token_manager = TokenManager(token_config)
        await self.token_manager.initialize()

        # 3. Initialize Rate Limiter (no dependencies)
        rate_config = self.config_manager.get_rate_limiter_config()
        self.rate_limiter = RateLimiter(rate_config)

        # 4. Initialize Circuit Breaker (no dependencies)
        circuit_config = self.config_manager.get_circuit_breaker_config()
        self.circuit_breaker = CircuitBreaker(circuit_config)

        # 5. Initialize Error Handler (depends on Rate Limiter, Circuit Breaker)
        error_config = self.config_manager.get_error_handler_config()
        self.error_handler = ErrorHandler(
            config=error_config,
            rate_limiter=self.rate_limiter,
            circuit_breaker=self.circuit_breaker
        )

        # 6. Initialize State Manager (for caching)
        self.state_manager = StateManager(db_path="data/risk_manager.db")
        await self.state_manager.initialize()

        # 7. Initialize SignalR Connection Manager (depends on Token Manager)
        signalr_config = self.config_manager.get_signalr_config()
        self.signalr_manager = SignalRConnectionManager(
            config=signalr_config,
            token_manager=self.token_manager
        )

        # 8. Initialize State Reconciler (depends on SignalR Manager, State Manager)
        reconciler_config = self.config_manager.get_state_reconciler_config()
        self.state_reconciler = StateReconciler(
            config=reconciler_config,
            signalr_manager=self.signalr_manager,
            state_manager=self.state_manager,
            error_handler=self.error_handler
        )

        # Inject State Reconciler into SignalR Manager
        self.signalr_manager.set_state_reconciler(self.state_reconciler)

        # 9. Initialize Order Manager (depends on Error Handler)
        order_config = self.config_manager.get_order_manager_config()
        self.order_manager = OrderManager(
            config=order_config,
            error_handler=self.error_handler
        )

        # 10. Connect SignalR
        await self.signalr_manager.connect()

        # 11. Perform initial state reconciliation
        await self.state_reconciler.reconcile()

        # 12. Initialize Risk Rules Engine (depends on all above)
        self.risk_engine = RiskRulesEngine(
            order_manager=self.order_manager,
            state_manager=self.state_manager,
            signalr_manager=self.signalr_manager
        )

        # 13. Subscribe to SignalR events and route to Risk Engine
        self.signalr_manager.on_position_event(self.risk_engine.handle_position_event)
        self.signalr_manager.on_order_event(self.risk_engine.handle_order_event)
        self.signalr_manager.on_trade_event(self.risk_engine.handle_trade_event)

        logger.info("Application initialized successfully")
```

---

## 🛑 Shutdown Sequence

```python
async def shutdown(self):
    """Gracefully shutdown all components"""

    logger.info("Starting graceful shutdown...")

    # 1. Stop accepting new events
    self.risk_engine.stop()

    # 2. Wait for in-flight operations to complete (max 10 seconds)
    await self.risk_engine.wait_for_completion(timeout=10)

    # 3. Disconnect SignalR (stop receiving events)
    await self.signalr_manager.disconnect()

    # 4. Flush state to database
    await self.state_manager.flush()

    # 5. Close database connection
    await self.state_manager.close()

    # 6. Stop Token Manager (cancel refresh timer)
    await self.token_manager.stop()

    logger.info("Graceful shutdown complete")
```

---

## 📝 Summary

**Component Integration:**
- Token Manager provides authentication for all API calls
- SignalR Manager uses Token Manager and triggers State Reconciler
- Error Handler coordinates Rate Limiter and Circuit Breaker
- Order Manager uses Error Handler for all order operations
- State Reconciler syncs state after reconnection
- All components use centralized configuration

**Initialization Order:**
1. Configuration → 2. Token Manager → 3. Rate Limiter → 4. Circuit Breaker → 5. Error Handler → 6. State Manager → 7. SignalR Manager → 8. State Reconciler → 9. Order Manager → 10. Risk Rules Engine

**Key Principles:**
- Dependency injection for all components
- Layered architecture (resilience → business logic)
- Clear component responsibilities
- Centralized configuration
- Graceful startup and shutdown

---

**Document Status:** DRAFT - Ready for implementation
