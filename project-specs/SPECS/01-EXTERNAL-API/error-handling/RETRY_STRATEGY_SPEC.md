# RETRY STRATEGY SPECIFICATION

**doc_id:** ERR-004
**version:** 1.0
**status:** DRAFT
**addresses:** Retry mechanisms for GAP-API-001, GAP-API-003, GAP-API-004, GAP-API-SCENARIO-001

---

## Overview

This specification defines comprehensive retry strategies for external API calls, addressing multiple gaps identified in ERRORS_AND_WARNINGS_CONSOLIDATED.md related to network failures, token refresh, and SignalR reconnection.

**Addresses:**
- **GAP-API-001:** Token refresh strategy undefined
- **GAP-API-003:** Incomplete SignalR reconnection logic
- **GAP-API-004:** No exponential backoff strategy
- **GAP-API-SCENARIO-001:** Network interruption during order placement
- **GAP-API-SCENARIO-005:** Token expiration during long operations

**Problem Statement:**
Need systematic retry logic to handle:
- Transient network failures
- Token expiration and refresh
- Service unavailability
- Rate limiting
- Partial failures

---

## Requirements

### Functional Requirements

**FR-RETRY-001:** System MUST implement exponential backoff for retries
**FR-RETRY-002:** System MUST classify errors as retryable vs non-retryable
**FR-RETRY-003:** System MUST support maximum retry attempts per operation
**FR-RETRY-004:** System MUST implement jitter to prevent thundering herd
**FR-RETRY-005:** System MUST handle token refresh during retries
**FR-RETRY-006:** System MUST preserve request idempotency during retries
**FR-RETRY-007:** System MUST support circuit breaker integration

### Performance Requirements

**PR-RETRY-001:** Retry decision logic MUST complete in < 0.5ms
**PR-RETRY-002:** Backoff calculation MUST be < 0.1ms
**PR-RETRY-003:** Total retry overhead MUST be < 2ms per attempt

### Reliability Requirements

**RR-RETRY-001:** Retry state MUST survive process restarts for critical operations
**RR-RETRY-002:** Idempotency keys MUST be unique and persistent
**RR-RETRY-003:** Retry attempts MUST be logged for debugging

---

## Retry Classification

### Retryable Errors

```yaml
retryableErrors:
  # Network errors
  network:
    - ECONNREFUSED
    - ECONNRESET
    - ETIMEDOUT
    - ENOTFOUND
    - ENETUNREACH
    - EAI_AGAIN

  # HTTP status codes
  httpStatus:
    - 408  # Request Timeout
    - 429  # Too Many Requests
    - 500  # Internal Server Error
    - 502  # Bad Gateway
    - 503  # Service Unavailable
    - 504  # Gateway Timeout

  # API error codes
  apiErrorCodes:
    - 1   # AuthFailure (token refresh needed)
    - 15  # TooManyRequests
    - 18  # MaintenanceMode
    - 19  # DataUnavailable
    - 20  # ServerError

  # SignalR connection errors
  signalr:
    - ConnectionClosed
    - ConnectionSlow
    - ServerTimeout
    - TransportFailed
```

### Non-Retryable Errors

```yaml
nonRetryableErrors:
  # HTTP status codes
  httpStatus:
    - 400  # Bad Request (client error)
    - 401  # Unauthorized (need to re-authenticate)
    - 403  # Forbidden (no permissions)
    - 404  # Not Found
    - 405  # Method Not Allowed
    - 422  # Unprocessable Entity

  # API error codes
  apiErrorCodes:
    - 2   # InvalidRequest
    - 3   # OrderRejected (business rule)
    - 4   # PositionNotFound
    - 5   # InsufficientBalance
    - 6   # MarketClosed
    - 7   # SymbolNotFound
    - 8   # InvalidVolume
    - 9   # InvalidPrice
    - 10  # OrderNotFound
    - 11  # PositionAlreadyClosed
    - 12  # StopLossInvalid
    - 13  # TakeProfitInvalid
    - 14  # OrderExpired
    - 16  # DuplicateOrder
    - 17  # AccountDisabled
```

---

## Exponential Backoff Algorithm

### Base Algorithm

```typescript
function calculateBackoff(
  attemptNumber: number,
  baseDelayMs: number,
  maxDelayMs: number,
  jitterFactor: number = 0.2
): number {
  // Exponential: baseDelay * 2^(attempt - 1)
  const exponentialDelay = baseDelayMs * Math.pow(2, attemptNumber - 1);

  // Cap at maximum
  const cappedDelay = Math.min(exponentialDelay, maxDelayMs);

  // Add jitter: random value between -jitterFactor and +jitterFactor
  const jitter = cappedDelay * jitterFactor * (Math.random() * 2 - 1);

  return Math.max(0, cappedDelay + jitter);
}

// Examples with baseDelay=1000, maxDelay=60000, jitter=0.2:
// Attempt 1: 1000ms * 2^0 = 1000ms ± 200ms = [800-1200ms]
// Attempt 2: 1000ms * 2^1 = 2000ms ± 400ms = [1600-2400ms]
// Attempt 3: 1000ms * 2^2 = 4000ms ± 800ms = [3200-4800ms]
// Attempt 4: 1000ms * 2^3 = 8000ms ± 1600ms = [6400-9600ms]
// Attempt 5: 1000ms * 2^4 = 16000ms ± 3200ms = [12800-19200ms]
// Attempt 6: 1000ms * 2^5 = 32000ms ± 6400ms = [25600-38400ms]
// Attempt 7: 1000ms * 2^6 = 60000ms (capped) ± 12000ms = [48000-60000ms]
```

### Jitter Explanation

**Why Jitter?**
- Prevents "thundering herd" problem
- Distributes retry attempts over time
- Reduces server load spikes
- Improves overall system stability

**Jitter Factor:** 0.2 (20%) provides good distribution without excessive delay variance.

---

## Retry Configuration by Operation Type

```yaml
retryStrategies:
  # Critical operations (order execution)
  orderExecution:
    maxRetries: 3
    baseDelayMs: 500
    maxDelayMs: 5000
    jitterFactor: 0.1  # Low jitter for time-sensitive ops
    timeoutMs: 5000
    retryOn: [500, 502, 503, 504, NETWORK_ERROR]
    idempotencyRequired: true

  # Position close (critical)
  positionClose:
    maxRetries: 5
    baseDelayMs: 1000
    maxDelayMs: 10000
    jitterFactor: 0.15
    timeoutMs: 5000
    retryOn: [500, 502, 503, 504, NETWORK_ERROR]
    idempotencyRequired: true

  # Token refresh (auth)
  tokenRefresh:
    maxRetries: 3
    baseDelayMs: 1000
    maxDelayMs: 5000
    jitterFactor: 0.2
    timeoutMs: 10000
    retryOn: [500, 502, 503, 504, NETWORK_ERROR]
    fallbackToReauth: true

  # SignalR connection
  signalrConnect:
    maxRetries: 10
    baseDelayMs: 2000
    maxDelayMs: 60000
    jitterFactor: 0.3  # Higher jitter for connection attempts
    timeoutMs: 30000
    retryOn: [CONNECTION_CLOSED, CONNECTION_SLOW, NETWORK_ERROR]
    exponentialBackoff: [0, 2000, 10000, 30000, 60000]  # Custom backoff

  # Historical data retrieval
  historyRetrieval:
    maxRetries: 3
    baseDelayMs: 2000
    maxDelayMs: 30000
    jitterFactor: 0.25
    timeoutMs: 60000
    retryOn: [429, 500, 502, 503, 504, NETWORK_ERROR]
    respectRateLimit: true

  # Account info
  accountInfo:
    maxRetries: 3
    baseDelayMs: 1000
    maxDelayMs: 10000
    jitterFactor: 0.2
    timeoutMs: 10000
    retryOn: [500, 502, 503, 504, NETWORK_ERROR]
    idempotencyRequired: false

  # Quote updates
  quoteUpdate:
    maxRetries: 2
    baseDelayMs: 500
    maxDelayMs: 2000
    jitterFactor: 0.2
    timeoutMs: 3000
    retryOn: [500, 502, 503, 504, NETWORK_ERROR]
    idempotencyRequired: false
```

---

## Token Refresh Integration

### Proactive Token Refresh (GAP-API-001)

```typescript
interface TokenRefreshStrategy {
  // Refresh token 2 hours before expiration
  refreshBufferMs: 7200000;  // 2 hours

  // Check token validity before each request
  validateBeforeRequest: true;

  // Refresh in background if token expires soon
  backgroundRefresh: true;

  // Retry request after successful token refresh
  retryAfterRefresh: true;

  // Maximum refresh attempts before forcing re-auth
  maxRefreshAttempts: 3;
}

async function executeWithTokenManagement(
  request: ApiRequest
): Promise<ApiResponse> {
  // 1. Check if token needs refresh
  if (shouldRefreshToken()) {
    await refreshToken();
  }

  // 2. Execute request
  try {
    return await executeRequest(request);
  } catch (error) {
    // 3. If auth failure, try token refresh once
    if (error.errorCode === 1) {  // AuthFailure
      await refreshToken();

      // 4. Retry request with new token
      return await executeRequest(request);
    }

    throw error;
  }
}

function shouldRefreshToken(): boolean {
  const token = getStoredToken();
  if (!token || !token.expiresAt) {
    return true;
  }

  const now = Date.now();
  const expiresAt = token.expiresAt;
  const bufferMs = 7200000;  // 2 hours

  return (expiresAt - now) < bufferMs;
}

async function refreshToken(): Promise<void> {
  const currentToken = getStoredToken();

  try {
    // Call /api/Authentication/validate endpoint
    const response = await axios.post(
      `${API_BASE_URL}/api/Authentication/validate`,
      { token: currentToken.value },
      { timeout: 10000 }
    );

    if (response.data?.d?.errorCode === 0) {
      // Token still valid, update expiration
      currentToken.expiresAt = Date.now() + 86400000;  // +24 hours
      storeToken(currentToken);
    } else {
      // Token invalid, need to re-authenticate
      await reAuthenticate();
    }
  } catch (error) {
    // Refresh failed, retry with exponential backoff
    throw new TokenRefreshError("Failed to refresh token", error);
  }
}
```

### Token Expiration During Long Operations (GAP-API-SCENARIO-005)

```typescript
async function executeLongRunningOperation(
  operation: () => Promise<any>,
  estimatedDurationMs: number
): Promise<any> {
  // 1. Check if token will expire during operation
  const token = getStoredToken();
  const timeUntilExpiry = token.expiresAt - Date.now();

  if (timeUntilExpiry < estimatedDurationMs + 600000) {  // +10 min buffer
    // 2. Refresh token before starting operation
    await refreshToken();
  }

  // 3. Execute operation with periodic token checks
  const checkInterval = setInterval(async () => {
    if (shouldRefreshToken()) {
      await refreshToken();
    }
  }, 300000);  // Check every 5 minutes

  try {
    return await operation();
  } finally {
    clearInterval(checkInterval);
  }
}

// Example usage for historical data retrieval
async function retrieveHistoricalBars(
  symbol: string,
  fromDate: Date,
  toDate: Date
): Promise<Bar[]> {
  // Estimate duration: ~20,000 bars at 50 req/30s = ~200 seconds
  const estimatedDurationMs = 200000;

  return executeLongRunningOperation(
    async () => {
      const bars = [];
      let currentDate = fromDate;

      while (currentDate < toDate) {
        const batch = await fetchBarsWithRetry(symbol, currentDate);
        bars.push(...batch);
        currentDate = addDays(currentDate, 1);
      }

      return bars;
    },
    estimatedDurationMs
  );
}
```

---

## SignalR Reconnection Strategy (GAP-API-003, GAP-API-004)

### Complete Reconnection Handlers

```typescript
const signalrConnection = new signalR.HubConnectionBuilder()
  .withUrl(`${API_BASE_URL}/signalr`, {
    accessTokenFactory: () => getStoredToken().value
  })
  .withAutomaticReconnect({
    nextRetryDelayInMilliseconds: (retryContext) => {
      // Custom exponential backoff with jitter
      const delays = [0, 2000, 10000, 30000, 60000];

      if (retryContext.previousRetryCount >= delays.length) {
        // Max retries reached, give up
        return null;
      }

      const baseDelay = delays[retryContext.previousRetryCount];
      const jitter = baseDelay * 0.3 * (Math.random() * 2 - 1);

      return baseDelay + jitter;
    }
  })
  .configureLogging(signalR.LogLevel.Information)
  .build();

// onreconnecting - Connection attempting to reconnect
signalrConnection.onreconnecting((error) => {
  console.warn('SignalR reconnecting:', error?.message);

  // Update UI to show connection issue
  updateConnectionStatus('reconnecting');

  // Increment reconnection attempt counter
  incrementReconnectionAttempts();
});

// onreconnected - Successfully reconnected
signalrConnection.onreconnected(async (connectionId) => {
  console.log('SignalR reconnected:', connectionId);

  // 1. Update connection status
  updateConnectionStatus('connected');

  // 2. Re-subscribe to events
  await resubscribeToSignalREvents();

  // 3. Reconcile state via REST API
  await reconcileStateAfterReconnection();

  // 4. Reset reconnection counter
  resetReconnectionAttempts();
});

// onclose - Connection closed permanently (GAP-API-003)
signalrConnection.onclose(async (error) => {
  console.error('SignalR connection closed:', error?.message);

  // 1. Update connection status
  updateConnectionStatus('disconnected');

  // 2. Notify user
  showNotification(
    'Real-time connection lost. Switching to fallback mode.',
    'warning'
  );

  // 3. Fall back to REST polling
  startRestPollingFallback();

  // 4. Attempt manual reconnection after delay
  setTimeout(() => {
    attemptManualReconnection();
  }, 60000);  // Try again in 60 seconds
});

// State reconciliation after reconnection (GAP-API-SCENARIO-003)
async function reconcileStateAfterReconnection(): Promise<void> {
  console.log('Reconciling state after SignalR reconnection...');

  try {
    // 1. Fetch current positions
    const positions = await fetchPositions();

    // 2. Fetch current orders
    const orders = await fetchOrders();

    // 3. Fetch current account state
    const account = await fetchAccountInfo();

    // 4. Update local state
    updateLocalState({ positions, orders, account });

    // 5. Re-run risk checks
    await runRiskChecksOnAllPositions();

    console.log('State reconciliation complete');
  } catch (error) {
    console.error('State reconciliation failed:', error);

    // Fall back to polling if reconciliation fails
    startRestPollingFallback();
  }
}

// Manual reconnection attempt
async function attemptManualReconnection(): Promise<void> {
  const maxAttempts = 5;
  let attempt = 0;

  while (attempt < maxAttempts) {
    attempt++;

    try {
      console.log(`Manual reconnection attempt ${attempt}/${maxAttempts}`);

      await signalrConnection.start();

      console.log('Manual reconnection successful');

      // Stop REST polling fallback
      stopRestPollingFallback();

      return;
    } catch (error) {
      console.error(`Reconnection attempt ${attempt} failed:`, error.message);

      const delay = calculateBackoff(attempt, 5000, 60000, 0.3);
      await sleep(delay);
    }
  }

  console.error('All manual reconnection attempts failed');

  // Continue with REST polling indefinitely
  showNotification(
    'Unable to restore real-time connection. Using fallback mode.',
    'error'
  );
}
```

---

## Idempotency for Retries

### Idempotency Key Generation

```typescript
interface IdempotencyConfig {
  enabled: boolean;
  keyPrefix: string;
  keyTTLSeconds: number;
  storageBackend: 'memory' | 'redis' | 'database';
}

function generateIdempotencyKey(
  operation: string,
  params: any
): string {
  // Create deterministic hash of operation + params
  const input = JSON.stringify({ operation, params });
  const hash = crypto.createHash('sha256').update(input).digest('hex');

  return `idempotency:${operation}:${hash}`;
}

async function executeWithIdempotency(
  operation: string,
  params: any,
  executor: () => Promise<any>
): Promise<any> {
  const idempotencyKey = generateIdempotencyKey(operation, params);

  // 1. Check if request already processed
  const cachedResult = await getIdempotentResult(idempotencyKey);
  if (cachedResult) {
    console.log('Returning cached idempotent result');
    return cachedResult;
  }

  // 2. Execute operation
  try {
    const result = await executor();

    // 3. Cache result
    await storeIdempotentResult(idempotencyKey, result, 300);  // 5 min TTL

    return result;
  } catch (error) {
    // Don't cache errors (allow retry)
    throw error;
  }
}

// Example usage for order placement
async function placeOrderWithIdempotency(
  order: OrderRequest
): Promise<OrderResponse> {
  return executeWithIdempotency(
    'placeOrder',
    { symbol: order.symbol, volume: order.volume, accountId: order.accountId },
    async () => {
      return await apiClient.post('/api/Order/execute', order);
    }
  );
}
```

---

## Network Interruption Handling (GAP-API-SCENARIO-001)

### Order Placement Resilience

```typescript
async function placeOrderWithNetworkResilience(
  order: OrderRequest
): Promise<OrderResponse> {
  const maxRetries = 3;
  let attempt = 0;

  while (attempt < maxRetries) {
    attempt++;

    try {
      // 1. Send order request
      const response = await apiClient.post('/api/Order/execute', order, {
        timeout: 5000
      });

      // 2. Success
      return response.data;

    } catch (error) {
      console.error(`Order placement attempt ${attempt} failed:`, error.message);

      // 3. Network error - verify order status
      if (isNetworkError(error)) {
        // Check if order was actually placed
        const orderStatus = await verifyOrderStatus(order);

        if (orderStatus === 'placed') {
          // Order was placed, return success
          console.log('Order was placed despite network error');
          return await fetchOrderDetails(order);
        } else if (orderStatus === 'not_found') {
          // Order not placed, safe to retry
          console.log('Order not placed, retrying...');

          if (attempt < maxRetries) {
            const delay = calculateBackoff(attempt, 1000, 5000, 0.1);
            await sleep(delay);
            continue;
          }
        }
      }

      // 4. Non-retryable error
      if (!isRetryableError(error)) {
        throw error;
      }

      // 5. Retryable error - backoff and retry
      if (attempt < maxRetries) {
        const delay = calculateBackoff(attempt, 1000, 5000, 0.1);
        await sleep(delay);
      } else {
        throw new MaxRetriesExceededError(
          `Failed to place order after ${maxRetries} attempts`
        );
      }
    }
  }
}

// Verify order status after network failure
async function verifyOrderStatus(
  order: OrderRequest
): Promise<'placed' | 'not_found' | 'unknown'> {
  try {
    // Fetch recent orders
    const orders = await apiClient.get('/api/Order/readOrders', {
      params: { accountId: order.accountId },
      timeout: 5000
    });

    // Look for matching order (by symbol, volume, timestamp)
    const recentOrders = orders.data.d?.orders || [];
    const matchingOrder = recentOrders.find((o) => {
      return (
        o.symbol === order.symbol &&
        Math.abs(o.volume - order.volume) < 0.01 &&
        Date.now() - new Date(o.createdAt).getTime() < 60000  // Within last minute
      );
    });

    if (matchingOrder) {
      return 'placed';
    } else {
      return 'not_found';
    }
  } catch (error) {
    console.error('Failed to verify order status:', error);
    return 'unknown';
  }
}
```

---

## Configuration Schema

```yaml
retryStrategy:
  # Global settings
  enabled: true
  defaultMaxRetries: 3
  defaultBaseDelayMs: 1000
  defaultMaxDelayMs: 30000
  defaultJitterFactor: 0.2

  # Idempotency
  idempotency:
    enabled: true
    keyPrefix: "simple-risk-manager"
    keyTTLSeconds: 300
    storageBackend: "memory"  # or "redis" for production

  # Token management
  tokenRefresh:
    enabled: true
    refreshBufferMs: 7200000  # 2 hours
    validateBeforeRequest: true
    backgroundRefresh: true
    maxRefreshAttempts: 3

  # Operation-specific configurations
  operations:
    orderExecution: { ... }
    positionClose: { ... }
    tokenRefresh: { ... }
    signalrConnect: { ... }
    historyRetrieval: { ... }
```

---

## Implementation Checklist

- [ ] Implement exponential backoff calculator with jitter
- [ ] Create retry classification logic (retryable vs non-retryable)
- [ ] Implement operation-specific retry strategies
- [ ] Create token refresh integration
- [ ] Implement proactive token refresh
- [ ] Create complete SignalR reconnection handlers
- [ ] Implement state reconciliation after reconnection
- [ ] Create idempotency key generator
- [ ] Implement order status verification
- [ ] Add retry metrics and monitoring
- [ ] Create unit tests for all retry scenarios
- [ ] Test token expiration during long operations
- [ ] Test network interruption handling
- [ ] Performance test retry overhead

---

## Validation Criteria

### Test Scenarios

```yaml
test_scenarios:
  - name: "Exponential backoff calculation"
    baseDelay: 1000
    maxDelay: 60000
    attempts: [1, 2, 3, 4, 5]
    expected: [~1000, ~2000, ~4000, ~8000, ~16000]

  - name: "Retry on network error"
    error: "ECONNREFUSED"
    maxRetries: 3
    expected: "retry_3_times"

  - name: "No retry on business error"
    errorCode: 5  # InsufficientBalance
    expected: "fail_immediately"

  - name: "Token refresh before expiry"
    tokenExpiresIn: 3600000  # 1 hour
    expected: "refresh_token"

  - name: "State reconciliation after reconnection"
    actions:
      - disconnect_signalr
      - modify_positions_server_side
      - reconnect_signalr
    expected: "local_state_updated"
```

---

## References

- **ERRORS_AND_WARNINGS_CONSOLIDATED.md** - Multiple GAPs
- **ERROR_CODE_MAPPING_SPEC.md** - Error classification
- **CIRCUIT_BREAKER_SPEC.md** - Integration with circuit breaker
- **RATE_LIMITING_SPEC.md** - Rate limit integration

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-22 | Error Handling Spec Writer | Initial draft |

---

**END OF SPECIFICATION**
