# CIRCUIT BREAKER SPECIFICATION

**doc_id:** ERR-003
**version:** 1.0
**status:** DRAFT
**addresses:** GAP-API-008 from ERRORS_AND_WARNINGS_CONSOLIDATED.md

---

## Overview

This specification defines a circuit breaker pattern for external API resilience. It addresses **GAP-API-008: No Circuit Breaker Pattern** by implementing failure detection, service health monitoring, and fallback strategies.

**Problem Statement:**
No guidance on:
- Handling repeated API failures
- Detecting service degradation
- Implementing fallback strategies
- Preventing cascading failures

**Impact:**
Repeated failures could cascade, overwhelming both client and server with unnecessary requests.

---

## Requirements

### Functional Requirements

**FR-CB-001:** System MUST implement circuit breaker for all external API calls
**FR-CB-002:** System MUST support three states: CLOSED, OPEN, HALF_OPEN
**FR-CB-003:** System MUST transition states based on failure/success thresholds
**FR-CB-004:** System MUST provide per-service circuit breaker isolation
**FR-CB-005:** System MUST implement timeout detection for service health
**FR-CB-006:** System MUST support configurable recovery timings
**FR-CB-007:** System MUST provide fallback mechanisms when circuit is OPEN

### Performance Requirements

**PR-CB-001:** Circuit breaker state check MUST be < 0.1ms
**PR-CB-002:** State transition logic MUST be thread-safe
**PR-CB-003:** Metrics collection overhead MUST be < 1ms

### Reliability Requirements

**RR-CB-001:** Circuit breaker state MUST persist across restarts
**RR-CB-002:** State transitions MUST be atomic (no race conditions)
**RR-CB-003:** System MUST detect service recovery automatically

---

## Circuit Breaker State Machine

```
                    ┌─────────────────┐
                    │     CLOSED      │
                    │  (Normal flow)  │
                    └────────┬────────┘
                             │
                     Failures < threshold
                             │
                    ┌────────▼────────┐
                    │   Monitoring    │
                    │   Failures      │
                    └────────┬────────┘
                             │
                  Failures >= threshold
                             │
                    ┌────────▼────────┐
                    │      OPEN       │
                    │  (Fail fast)    │
                    └────────┬────────┘
                             │
                      Timeout elapsed
                             │
                    ┌────────▼────────┐
                    │   HALF_OPEN     │
                    │  (Test calls)   │
                    └────────┬────────┘
                             │
                    ┌────────┴─────────┐
                    │                  │
          Success >= threshold    Failure detected
                    │                  │
          ┌─────────▼────────┐   ┌────▼─────────┐
          │     CLOSED       │   │     OPEN     │
          │   (Recovered)    │   │  (Still down)│
          └──────────────────┘   └──────────────┘
```

### State Descriptions

**CLOSED (Normal Operation):**
- All requests flow through normally
- Monitor failure rate
- If failures exceed threshold → transition to OPEN

**OPEN (Fail Fast):**
- Reject all requests immediately without attempting API call
- Return cached/fallback response
- After timeout period → transition to HALF_OPEN

**HALF_OPEN (Testing Recovery):**
- Allow limited number of test requests
- Monitor success rate
- If success rate high enough → transition to CLOSED
- If any failure detected → transition back to OPEN

---

## Configuration Schema

```yaml
circuitBreaker:
  # Global settings
  enabled: true
  persistState: true
  persistenceFile: "./data/circuit_breaker_state.json"

  # Default settings (can be overridden per service)
  defaults:
    failureThreshold: 5           # Open circuit after 5 consecutive failures
    successThreshold: 3           # Close circuit after 3 consecutive successes in HALF_OPEN
    timeout: 60000                # 60 seconds before attempting recovery
    halfOpenMaxRequests: 3        # Allow 3 test requests in HALF_OPEN state
    volumeThreshold: 10           # Minimum requests before evaluating failure rate
    errorThresholdPercentage: 50  # Open circuit if >50% of requests fail
    rollingWindowMs: 10000        # Evaluate failures over 10-second window

  # Service-specific configurations
  services:
    # ProjectX Gateway API - General endpoints
    projectx_general:
      endpoints: ["*"]
      failureThreshold: 5
      successThreshold: 3
      timeout: 60000
      halfOpenMaxRequests: 3
      errorThresholdPercentage: 50

    # ProjectX Gateway API - Order execution (critical)
    projectx_orders:
      endpoints: ["/api/Order/execute", "/api/Order/modifyTrade"]
      failureThreshold: 3           # More sensitive to failures
      successThreshold: 5           # Require more successes before recovery
      timeout: 30000                # Faster recovery attempt
      halfOpenMaxRequests: 5
      errorThresholdPercentage: 30  # Lower threshold for critical operations

    # ProjectX Gateway API - Historical data
    projectx_history:
      endpoints: ["/api/History/retrieveBars"]
      failureThreshold: 10          # More tolerant of failures
      successThreshold: 2
      timeout: 120000               # Longer recovery timeout
      halfOpenMaxRequests: 2
      errorThresholdPercentage: 70  # Higher threshold for non-critical

    # SignalR WebSocket connection
    signalr_connection:
      endpoints: ["signalr://"]
      failureThreshold: 3
      successThreshold: 2
      timeout: 10000                # Quick recovery for real-time connection
      halfOpenMaxRequests: 1
      errorThresholdPercentage: 30

  # Failure classification
  failureDetection:
    # HTTP status codes that count as failures
    failureHttpCodes: [500, 502, 503, 504]

    # API error codes that count as failures
    failureApiCodes: [20]  # ServerError

    # Timeouts count as failures
    timeoutIsFailure: true

    # Network errors count as failures
    networkErrorIsFailure: true

    # Errors that do NOT count as failures (business logic errors)
    ignoredErrorCodes: [3, 5, 6]  # OrderRejected, InsufficientBalance, MarketClosed
```

---

## State Transition Rules

### CLOSED → OPEN

**Trigger Conditions (ANY of the following):**

1. **Consecutive Failures:**
   ```
   IF consecutive_failures >= failureThreshold
   THEN transition to OPEN
   ```

2. **Error Rate:**
   ```
   IF requests_in_window >= volumeThreshold
      AND error_rate >= errorThresholdPercentage
   THEN transition to OPEN
   ```

3. **Critical Failure:**
   ```
   IF error_code IN [500, 502, 503, 504]
      AND consecutive_failures >= 2
   THEN transition to OPEN
   ```

**Actions on Transition:**
- Log state change with timestamp
- Record failure details
- Start timeout timer
- Notify monitoring system
- Persist new state to disk

### OPEN → HALF_OPEN

**Trigger Condition:**
```
IF time_since_open >= timeout
THEN transition to HALF_OPEN
```

**Actions on Transition:**
- Log state change
- Reset test request counter
- Allow limited requests through
- Monitor success rate closely

### HALF_OPEN → CLOSED

**Trigger Condition:**
```
IF consecutive_successes >= successThreshold
   AND test_requests_sent >= halfOpenMaxRequests
THEN transition to CLOSED
```

**Actions on Transition:**
- Log successful recovery
- Reset all failure counters
- Resume normal operation
- Notify monitoring system

### HALF_OPEN → OPEN

**Trigger Condition:**
```
IF any_failure_detected
THEN transition to OPEN
```

**Actions on Transition:**
- Log failed recovery attempt
- Increment recovery attempt counter
- Increase timeout exponentially (up to max)
- Return to fail-fast mode

---

## Failure Detection

### Classifying Failures vs Success

```typescript
function classifyResponse(response: ApiResponse): ResponseStatus {
  // 1. HTTP-level failures
  if (response.httpStatus >= 500) {
    return ResponseStatus.FAILURE;
  }

  // 2. Timeout
  if (response.timedOut) {
    return ResponseStatus.FAILURE;
  }

  // 3. Network errors
  if (response.networkError) {
    return ResponseStatus.FAILURE;
  }

  // 4. API error codes
  if (response.body?.d?.errorCode === 20) {  // ServerError
    return ResponseStatus.FAILURE;
  }

  // 5. Business logic errors (NOT failures)
  if ([3, 5, 6].includes(response.body?.d?.errorCode)) {
    return ResponseStatus.SUCCESS;  // System is working, just business rule violation
  }

  // 6. Authentication errors (NOT failures - system working correctly)
  if (response.body?.d?.errorCode === 1) {  // AuthFailure
    return ResponseStatus.SUCCESS;
  }

  // 7. Success
  if (response.body?.d?.errorCode === 0) {
    return ResponseStatus.SUCCESS;
  }

  // 8. Unknown - default to failure for safety
  return ResponseStatus.FAILURE;
}
```

### Rolling Window Failure Tracking

```typescript
interface FailureWindow {
  buckets: Map<number, Bucket>;  // timestamp -> bucket
  windowMs: number;
  bucketSizeMs: number;
}

interface Bucket {
  timestamp: number;
  totalRequests: number;
  failedRequests: number;
  successfulRequests: number;
}

function recordRequest(
  window: FailureWindow,
  success: boolean
): void {
  const now = Date.now();
  const bucketTimestamp = Math.floor(now / window.bucketSizeMs) * window.bucketSizeMs;

  let bucket = window.buckets.get(bucketTimestamp);
  if (!bucket) {
    bucket = {
      timestamp: bucketTimestamp,
      totalRequests: 0,
      failedRequests: 0,
      successfulRequests: 0
    };
    window.buckets.set(bucketTimestamp, bucket);
  }

  bucket.totalRequests++;
  if (success) {
    bucket.successfulRequests++;
  } else {
    bucket.failedRequests++;
  }

  // Prune old buckets
  pruneOldBuckets(window, now);
}

function getErrorRate(window: FailureWindow): number {
  const now = Date.now();
  let totalRequests = 0;
  let failedRequests = 0;

  for (const [timestamp, bucket] of window.buckets) {
    if (now - timestamp <= window.windowMs) {
      totalRequests += bucket.totalRequests;
      failedRequests += bucket.failedRequests;
    }
  }

  if (totalRequests === 0) return 0;
  return (failedRequests / totalRequests) * 100;
}
```

---

## Service Health Monitoring

### Health Check Mechanism

```yaml
healthCheck:
  enabled: true
  interval: 30000  # Check every 30 seconds
  timeout: 5000    # 5 second timeout per check
  endpoint: "/api/Account/read"  # Lightweight endpoint

  # Health check only runs when circuit is OPEN
  onlyWhenOpen: true

  # Success criteria
  successCriteria:
    httpStatus: [200]
    responseTime: 3000  # Must respond within 3 seconds
    errorCode: [0, 1]   # Success or auth error (system working)
```

### Proactive Health Monitoring

```typescript
async function monitorServiceHealth(
  service: string,
  config: HealthCheckConfig
): Promise<void> {
  const state = getCircuitState(service);

  // Only run health checks when circuit is OPEN
  if (state !== CircuitState.OPEN) {
    return;
  }

  try {
    const startTime = Date.now();
    const response = await axios.get(config.endpoint, {
      timeout: config.timeout,
      headers: { Authorization: `Bearer ${token}` }
    });

    const responseTime = Date.now() - startTime;

    // Check if service is healthy
    const isHealthy =
      config.successCriteria.httpStatus.includes(response.status) &&
      responseTime <= config.successCriteria.responseTime &&
      config.successCriteria.errorCode.includes(response.data?.d?.errorCode);

    if (isHealthy) {
      // Service appears healthy, transition to HALF_OPEN
      transitionState(service, CircuitState.HALF_OPEN);
    }
  } catch (error) {
    // Service still unhealthy, remain in OPEN state
    console.log(`Service ${service} still unhealthy:`, error.message);
  }
}
```

---

## Fallback Strategies

### Fallback Mechanisms by Service

```yaml
fallbacks:
  # Order execution - NO fallback (must fail gracefully)
  projectx_orders:
    strategy: "fail_with_error"
    errorMessage: "Trading service temporarily unavailable. Please try again later."
    notifyUser: true

  # Historical data - Return cached data if available
  projectx_history:
    strategy: "return_cached"
    cacheTTL: 300000  # 5 minutes
    staleCacheAcceptable: true
    errorMessage: "Using cached historical data."

  # Account info - Return last known state
  projectx_account:
    strategy: "return_last_known"
    errorMessage: "Account data may be stale."
    showWarning: true

  # Quotes - Fall back to last known quote with warning
  projectx_quotes:
    strategy: "return_last_known"
    errorMessage: "Quote data may be outdated."
    maxStaleness: 30000  # 30 seconds max staleness
    showWarning: true

  # SignalR - Fall back to REST polling
  signalr_connection:
    strategy: "fallback_to_rest"
    pollingInterval: 5000  # Poll every 5 seconds
    errorMessage: "Using fallback mode. Real-time updates may be delayed."
```

### Fallback Implementation

```typescript
async function executeWithCircuitBreaker(
  service: string,
  request: ApiRequest
): Promise<ApiResponse> {
  const state = getCircuitState(service);

  switch (state) {
    case CircuitState.CLOSED:
      // Normal operation
      return await executeRequest(request);

    case CircuitState.OPEN:
      // Circuit is open - use fallback
      return await executeFallback(service, request);

    case CircuitState.HALF_OPEN:
      // Test if service recovered
      if (canSendTestRequest(service)) {
        try {
          const response = await executeRequest(request);
          recordSuccess(service);
          return response;
        } catch (error) {
          recordFailure(service);
          return await executeFallback(service, request);
        }
      } else {
        // Max test requests reached, use fallback
        return await executeFallback(service, request);
      }
  }
}

async function executeFallback(
  service: string,
  request: ApiRequest
): Promise<ApiResponse> {
  const config = getFallbackConfig(service);

  switch (config.strategy) {
    case "fail_with_error":
      throw new CircuitBreakerError(config.errorMessage);

    case "return_cached":
      const cached = await getFromCache(request);
      if (cached && !isCacheStale(cached, config.cacheTTL)) {
        return cached;
      } else if (cached && config.staleCacheAcceptable) {
        return cached;  // Return stale cache if acceptable
      }
      throw new CircuitBreakerError("No cached data available");

    case "return_last_known":
      const lastKnown = await getLastKnownState(service);
      if (lastKnown && !isTooStale(lastKnown, config.maxStaleness)) {
        return lastKnown;
      }
      throw new CircuitBreakerError("No last known state available");

    case "fallback_to_rest":
      return await executeRestFallback(request, config.pollingInterval);
  }
}
```

---

## Exponential Backoff for Recovery

### Recovery Timeout Calculation

```typescript
function calculateRecoveryTimeout(
  baseTimeout: number,
  attemptNumber: number,
  maxTimeout: number
): number {
  // Exponential backoff: baseTimeout * 2^(attemptNumber - 1)
  const timeout = baseTimeout * Math.pow(2, attemptNumber - 1);

  // Cap at maximum timeout
  return Math.min(timeout, maxTimeout);
}

// Example:
// Attempt 1: 60s * 2^0 = 60 seconds
// Attempt 2: 60s * 2^1 = 120 seconds
// Attempt 3: 60s * 2^2 = 240 seconds
// Attempt 4: 60s * 2^3 = 480 seconds (capped at maxTimeout)
```

---

## State Persistence

### Persistent State Schema

```json
{
  "version": "1.0",
  "lastUpdated": "2025-10-22T15:30:45.123Z",
  "circuits": {
    "projectx_general": {
      "state": "CLOSED",
      "consecutiveFailures": 0,
      "consecutiveSuccesses": 5,
      "lastFailureTimestamp": null,
      "lastSuccessTimestamp": "2025-10-22T15:30:45.000Z",
      "openedAt": null,
      "recoveryAttempts": 0,
      "metrics": {
        "totalRequests": 1250,
        "successfulRequests": 1245,
        "failedRequests": 5,
        "errorRate": 0.4
      }
    },
    "projectx_orders": {
      "state": "OPEN",
      "consecutiveFailures": 5,
      "consecutiveSuccesses": 0,
      "lastFailureTimestamp": "2025-10-22T15:28:30.000Z",
      "lastSuccessTimestamp": "2025-10-22T15:20:00.000Z",
      "openedAt": "2025-10-22T15:28:30.123Z",
      "nextRetryAt": "2025-10-22T15:29:30.123Z",
      "recoveryAttempts": 1,
      "metrics": {
        "totalRequests": 320,
        "successfulRequests": 315,
        "failedRequests": 5,
        "errorRate": 1.56
      }
    }
  }
}
```

---

## Integration with Rate Limiter

Circuit breaker and rate limiter work together:

```typescript
async function executeRequest(request: ApiRequest): Promise<ApiResponse> {
  // 1. Check circuit breaker
  const cbState = getCircuitState(request.service);
  if (cbState === CircuitState.OPEN) {
    return executeFallback(request.service, request);
  }

  // 2. Check rate limiter
  const rateLimitCheck = canSendRequest(request.endpoint, request.priority);
  if (!rateLimitCheck.allowed) {
    // Queue request
    return queueRequest(request, rateLimitCheck.waitMs);
  }

  // 3. Execute request
  try {
    const response = await sendApiRequest(request);

    // 4. Record success in circuit breaker
    recordCircuitBreakerSuccess(request.service);

    // 5. Record request in rate limiter
    recordRateLimitRequest(request.endpoint);

    return response;
  } catch (error) {
    // 6. Record failure in circuit breaker
    recordCircuitBreakerFailure(request.service, error);

    throw error;
  }
}
```

---

## Monitoring and Metrics

### Key Metrics

```yaml
metrics:
  circuit_breaker:
    state:
      type: gauge
      labels: [service, state]
      description: Current circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)

    state_transitions:
      type: counter
      labels: [service, from_state, to_state]
      description: Total state transitions

    failures:
      type: counter
      labels: [service, failure_type]
      description: Total failures detected

    successes:
      type: counter
      labels: [service]
      description: Total successful requests

    fallback_used:
      type: counter
      labels: [service, fallback_strategy]
      description: Fallback mechanism invoked

    recovery_attempts:
      type: counter
      labels: [service, success]
      description: Recovery attempts (success/failure)

    error_rate:
      type: gauge
      labels: [service]
      description: Current error rate percentage
```

---

## Implementation Checklist

- [ ] Create circuit breaker state machine
- [ ] Implement state transition logic with atomic operations
- [ ] Create failure detection classifier
- [ ] Implement rolling window for error rate calculation
- [ ] Create service health monitoring
- [ ] Implement fallback strategies
- [ ] Add exponential backoff for recovery
- [ ] Create state persistence mechanism
- [ ] Integrate with rate limiter
- [ ] Add monitoring and metrics
- [ ] Create unit tests for all state transitions
- [ ] Test fallback mechanisms
- [ ] Test concurrent request handling
- [ ] Performance test state check overhead

---

## Validation Criteria

### Test Scenarios

```yaml
test_scenarios:
  - name: "Open circuit after threshold failures"
    actions:
      - send_request: { expected: FAILURE }
      - send_request: { expected: FAILURE }
      - send_request: { expected: FAILURE }
      - send_request: { expected: FAILURE }
      - send_request: { expected: FAILURE }
      - send_request: { expected: FALLBACK }
    expected_state: OPEN

  - name: "Transition to HALF_OPEN after timeout"
    actions:
      - set_state: OPEN
      - wait: 61000  # 61 seconds
      - send_request: { expected: ATTEMPT }
    expected_state: HALF_OPEN

  - name: "Close circuit after successful recovery"
    actions:
      - set_state: HALF_OPEN
      - send_request: { expected: SUCCESS }
      - send_request: { expected: SUCCESS }
      - send_request: { expected: SUCCESS }
    expected_state: CLOSED

  - name: "Reopen circuit on failure in HALF_OPEN"
    actions:
      - set_state: HALF_OPEN
      - send_request: { expected: SUCCESS }
      - send_request: { expected: FAILURE }
    expected_state: OPEN

  - name: "Business errors do not trigger circuit"
    actions:
      - send_request: { errorCode: 5 }  # InsufficientBalance
      - send_request: { errorCode: 6 }  # MarketClosed
    expected_state: CLOSED
```

---

## References

- **ERRORS_AND_WARNINGS_CONSOLIDATED.md** - Section 5, GAP-API-008 (lines 211-218)
- **API-INTEGRATION-ANALYSIS.md** - Section 2.3 Error Handling & Resilience
- **ERROR_CODE_MAPPING_SPEC.md** - Failure classification
- **RATE_LIMITING_SPEC.md** - Integration with rate limiter
- **RETRY_STRATEGY_SPEC.md** - Retry logic coordination

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-22 | Error Handling Spec Writer | Initial draft addressing GAP-API-008 |

---

**END OF SPECIFICATION**
