# RATE LIMITING SPECIFICATION

**doc_id:** ERR-002
**version:** 1.0
**status:** DRAFT
**addresses:** GAP-API-007 from ERRORS_AND_WARNINGS_CONSOLIDATED.md

---

## Overview

This specification defines client-side rate limiting mechanisms for the ProjectX Gateway API. It addresses **GAP-API-007: No Rate Limit Tracking** by implementing pre-emptive throttling, request queuing, and priority-based ordering.

**Problem Statement:**
Rate limits are documented but:
- No response headers for remaining quota
- No pre-emptive throttling guidance
- No queue management for bursts

**Rate Limits (from API documentation):**
- `/api/History/retrieveBars`: 50 requests / 30 seconds
- All other endpoints: 200 requests / 60 seconds

**Impact:**
Application could be throttled/blocked by API, causing service disruption and poor user experience.

---

## Requirements

### Functional Requirements

**FR-RATE-001:** System MUST enforce client-side rate limits before sending requests
**FR-RATE-002:** System MUST support endpoint-specific rate limit configurations
**FR-RATE-003:** System MUST queue requests when rate limit is reached
**FR-RATE-004:** System MUST support priority-based request ordering (0-10 scale)
**FR-RATE-005:** System MUST implement sliding window algorithm for accurate counting
**FR-RATE-006:** System MUST provide rate limit status via API
**FR-RATE-007:** System MUST support configurable rate limit buffers (safety margin)

### Performance Requirements

**PR-RATE-001:** Rate limit check overhead MUST be < 1ms per request
**PR-RATE-002:** Request queue operations MUST be O(log n) or better
**PR-RATE-003:** Memory usage MUST be < 100KB for request tracking
**PR-RATE-004:** Queue processing latency MUST be < 5ms

### Reliability Requirements

**RR-RATE-001:** Rate limiter MUST survive application restarts (persist state)
**RR-RATE-002:** Rate limiter MUST handle clock skew gracefully
**RR-RATE-003:** Queue MUST not lose requests during system failures

---

## Rate Limit Configuration

### Endpoint Rate Limits

```yaml
rateLimits:
  # Historical data endpoint (most restrictive)
  history:
    endpoint: "/api/History/retrieveBars"
    requests: 50
    windowSeconds: 30
    burstAllowance: 5  # Allow 5 extra requests for bursts
    safetyBuffer: 0.9  # Use only 90% of limit (45 req/30s)
    priority: 5  # Medium priority

  # All other endpoints (general limit)
  general:
    endpoint: "*"
    requests: 200
    windowSeconds: 60
    burstAllowance: 10
    safetyBuffer: 0.9  # Use only 90% of limit (180 req/60s)
    priority: 5

  # Critical endpoints (override general limit with higher priority)
  orderExecution:
    endpoint: "/api/Order/execute"
    requests: 200
    windowSeconds: 60
    burstAllowance: 0  # No burst for order execution
    safetyBuffer: 0.95  # Use 95% of limit
    priority: 10  # Highest priority

  positionClose:
    endpoint: "/api/Order/execute"  # Same endpoint but tagged differently
    requests: 200
    windowSeconds: 60
    burstAllowance: 0
    safetyBuffer: 0.95
    priority: 9  # High priority

  # Low priority endpoints
  accountInfo:
    endpoint: "/api/Account/read"
    requests: 200
    windowSeconds: 60
    burstAllowance: 20
    safetyBuffer: 0.8  # Use only 80% of limit
    priority: 3  # Low priority

  quotes:
    endpoint: "/api/Quote/read"
    requests: 200
    windowSeconds: 60
    burstAllowance: 10
    safetyBuffer: 0.85
    priority: 7  # High priority for risk calculations
```

---

## Sliding Window Algorithm

### Algorithm Choice: Fixed Window with Sub-Windows

**Rationale:** Balance between accuracy and performance.

**Implementation:**
- Divide rate limit window into 10 sub-windows
- Track request count per sub-window
- Sum recent sub-windows for accurate rate calculation
- Evict old sub-windows automatically

**Example for 60-second window:**
```
Window: 60 seconds
Sub-window: 6 seconds each
Number of sub-windows: 10

[0-6s] [6-12s] [12-18s] ... [54-60s]
  12      15       18    ...    20

Total requests in last 60s = sum of all sub-windows
```

**Advantages:**
- More accurate than fixed window
- Less memory than true sliding window
- O(1) insertion and query time

---

## Request Queue Architecture

### Priority Queue Design

```
┌─────────────────────────────────┐
│      Rate Limiter Gateway       │
└─────────────────┬───────────────┘
                  │
         ┌────────▼─────────┐
         │ Endpoint Matcher │
         └────────┬─────────┘
                  │
         ┌────────▼─────────┐
         │  Rate Calculator  │
         │ (Sliding Window)  │
         └────────┬─────────┘
                  │
         ┌────────▼─────────┐
         │   Allow/Queue?   │
         └──┬───────────┬───┘
            │           │
      ALLOW │           │ QUEUE
            │           │
     ┌──────▼─────┐ ┌──▼───────────────┐
     │  Execute   │ │  Priority Queue   │
     │  Request   │ │  (Min-Heap)       │
     └────────────┘ └──┬───────────────┘
                       │
                ┌──────▼─────────┐
                │ Queue Processor │
                │  (Background)   │
                └────────────────┘
```

### Queue Data Structure

```typescript
interface QueuedRequest {
  id: string;                    // Unique request ID
  endpoint: string;              // API endpoint
  priority: number;              // 0-10 (10 = highest)
  queuedAt: number;              // Timestamp (ms)
  maxWaitMs: number;             // Max time in queue before timeout
  request: PendingRequest;       // Original request data
  retryCount: number;            // Number of retry attempts
  onSuccess: (response) => void; // Success callback
  onError: (error) => void;      // Error callback
  onTimeout: () => void;         // Timeout callback
}

interface PriorityQueue {
  heap: QueuedRequest[];         // Min-heap by (priority, queuedAt)
  size: number;                  // Current queue size
  maxSize: number;               // Maximum queue capacity

  insert(request: QueuedRequest): void;
  extractMax(): QueuedRequest | null;
  peek(): QueuedRequest | null;
  remove(id: string): boolean;
  clear(): void;
}
```

---

## Pre-Emptive Throttling Logic

### Rate Limit Check Algorithm

```typescript
function canSendRequest(endpoint: string, priority: number): {
  allowed: boolean;
  waitMs: number;
  reason?: string;
} {
  // 1. Get rate limit config for endpoint
  const config = getRateLimitConfig(endpoint);

  // 2. Calculate current request count in window
  const currentCount = getRequestCountInWindow(
    endpoint,
    config.windowSeconds
  );

  // 3. Calculate effective limit with safety buffer
  const effectiveLimit = Math.floor(
    config.requests * config.safetyBuffer
  );

  // 4. Check if within limit
  if (currentCount < effectiveLimit) {
    return { allowed: true, waitMs: 0 };
  }

  // 5. Check if burst allowance available
  if (currentCount < config.requests + config.burstAllowance) {
    if (priority >= 8) {  // Only high priority can use burst
      return { allowed: true, waitMs: 0 };
    }
  }

  // 6. Calculate wait time until oldest request expires
  const oldestRequest = getOldestRequestTimestamp(endpoint);
  const waitMs = Math.max(0,
    config.windowSeconds * 1000 - (Date.now() - oldestRequest)
  );

  return {
    allowed: false,
    waitMs: waitMs,
    reason: `Rate limit reached: ${currentCount}/${effectiveLimit} requests`
  };
}
```

---

## Queue Management

### Queue Processing Rules

**Enqueue Rules:**
1. Check rate limit before enqueuing
2. If rate limit reached, add to priority queue
3. Enforce maximum queue size (reject if full)
4. Set max wait time based on request priority

**Dequeue Rules:**
1. Background processor checks queue every 100ms
2. Extract highest priority request
3. Re-check rate limit before sending
4. If rate limit still reached, re-queue with increased wait time
5. If max wait time exceeded, timeout request

**Priority Rules:**
```yaml
priorityLevels:
  10: CRITICAL      # Order execution, position close
  9:  HIGH          # Risk rule enforcement
  8:  ELEVATED      # Stop loss updates
  7:  ABOVE_NORMAL  # Quote updates for open positions
  6:  NORMAL_HIGH   # Position queries
  5:  NORMAL        # General API calls
  4:  BELOW_NORMAL  # Account info
  3:  LOW           # Historical data (non-critical)
  2:  VERY_LOW      # Background refresh
  1:  MINIMAL       # Analytics, logging
  0:  DEFERRED      # Can be delayed indefinitely
```

### Maximum Wait Times by Priority

```yaml
maxWaitTimes:
  priority10: 1000    # 1 second max wait
  priority9:  2000    # 2 seconds
  priority8:  5000    # 5 seconds
  priority7:  10000   # 10 seconds
  priority6:  15000   # 15 seconds
  priority5:  30000   # 30 seconds
  priority4:  60000   # 1 minute
  priority3:  120000  # 2 minutes
  priority2:  300000  # 5 minutes
  priority1:  600000  # 10 minutes
  priority0:  null    # No timeout (deferred)
```

---

## Quota Tracking Mechanism

### Request Tracking Data Structure

```typescript
interface RequestWindow {
  endpoint: string;
  subWindows: Map<number, number>;  // timestamp -> request count
  totalCount: number;
  windowStartMs: number;
  windowEndMs: number;
}

interface QuotaTracker {
  windows: Map<string, RequestWindow>;  // endpoint -> window

  recordRequest(endpoint: string, timestamp: number): void;
  getRequestCount(endpoint: string, windowSeconds: number): number;
  getRemainingQuota(endpoint: string): number;
  resetWindow(endpoint: string): void;
  pruneOldWindows(): void;
}
```

### Quota Calculation

```typescript
function getRemainingQuota(endpoint: string): {
  remaining: number;
  resetInSeconds: number;
  percentUsed: number;
} {
  const config = getRateLimitConfig(endpoint);
  const currentCount = getRequestCountInWindow(
    endpoint,
    config.windowSeconds
  );

  const effectiveLimit = Math.floor(
    config.requests * config.safetyBuffer
  );

  const remaining = Math.max(0, effectiveLimit - currentCount);

  const oldestTimestamp = getOldestRequestTimestamp(endpoint);
  const resetInSeconds = Math.ceil(
    (oldestTimestamp + config.windowSeconds * 1000 - Date.now()) / 1000
  );

  const percentUsed = (currentCount / effectiveLimit) * 100;

  return { remaining, resetInSeconds, percentUsed };
}
```

---

## State Persistence

### Persistent Storage Schema

```json
{
  "version": "1.0",
  "lastUpdated": "2025-10-22T15:30:45.123Z",
  "windows": {
    "/api/History/retrieveBars": {
      "subWindows": {
        "1729613440000": 12,
        "1729613446000": 15,
        "1729613452000": 18
      },
      "totalCount": 45,
      "windowStartMs": 1729613440000,
      "windowEndMs": 1729613470000
    },
    "*": {
      "subWindows": {
        "1729613400000": 30,
        "1729613406000": 25
      },
      "totalCount": 55,
      "windowStartMs": 1729613400000,
      "windowEndMs": 1729613460000
    }
  },
  "queue": {
    "pending": [
      {
        "id": "req_123",
        "endpoint": "/api/History/retrieveBars",
        "priority": 3,
        "queuedAt": 1729613460000,
        "maxWaitMs": 120000
      }
    ],
    "size": 1,
    "maxSize": 1000
  }
}
```

**Persistence Rules:**
- Save state every 5 seconds (if changed)
- Save state on graceful shutdown
- Load state on startup
- Prune expired requests on load

---

## Configuration Schema

```yaml
rateLimiter:
  # Global settings
  enabled: true
  persistState: true
  persistenceInterval: 5000  # 5 seconds
  persistenceFile: "./data/rate_limiter_state.json"

  # Queue settings
  queue:
    enabled: true
    maxSize: 1000
    processingInterval: 100  # Check every 100ms
    timeoutCheckInterval: 1000  # Check timeouts every 1s

  # Window settings
  window:
    algorithm: "sliding_sub_windows"
    subWindowCount: 10
    pruneInterval: 60000  # Prune old windows every 60s

  # Monitoring
  monitoring:
    enabled: true
    logRateLimitReached: true
    logQueueDepth: true
    metricsInterval: 10000  # Report metrics every 10s

  # Endpoint-specific limits (see earlier section)
  limits:
    history: { ... }
    general: { ... }
    orderExecution: { ... }
```

---

## Rate Limiter State Machine

```
┌──────────┐
│   IDLE   │
└────┬─────┘
     │ Request received
     │
┌────▼─────────┐
│ CHECK_LIMIT  │
└────┬─────────┘
     │
     ├─ Within limit ──────┐
     │                     │
     │              ┌──────▼──────┐
     │              │   ALLOWED   │
     │              └──────┬──────┘
     │                     │ Execute request
     │                     │
     │              ┌──────▼──────┐
     │              │  RECORDING  │
     │              └──────┬──────┘
     │                     │ Record timestamp
     │                     │
     │              ┌──────▼──────┐
     │              │  COMPLETE   │
     │              └─────────────┘
     │
     └─ Limit reached ─────┐
                           │
                    ┌──────▼──────┐
                    │   QUEUED    │
                    └──────┬──────┘
                           │ Add to priority queue
                           │
                    ┌──────▼──────────┐
                    │ WAITING_QUOTA   │
                    └──────┬──────────┘
                           │
                           ├─ Quota available ─────┐
                           │                       │
                           │                ┌──────▼──────┐
                           │                │  DEQUEUED   │
                           │                └──────┬──────┘
                           │                       │ Re-check limit
                           │                       │
                           │                       └─ Back to CHECK_LIMIT
                           │
                           └─ Timeout reached ─────┐
                                                    │
                                             ┌──────▼──────┐
                                             │   TIMEOUT   │
                                             └──────┬──────┘
                                                    │ Invoke timeout callback
                                                    │
                                             ┌──────▼──────┐
                                             │   FAILED    │
                                             └─────────────┘
```

---

## Implementation Checklist

- [ ] Implement sliding window algorithm with sub-windows
- [ ] Create priority queue (min-heap) for request queuing
- [ ] Implement endpoint matcher (regex or glob patterns)
- [ ] Create rate limit configuration loader
- [ ] Implement pre-emptive throttling checks
- [ ] Create background queue processor
- [ ] Implement quota tracking and reporting
- [ ] Add state persistence (save/load)
- [ ] Create rate limiter middleware/interceptor
- [ ] Implement timeout handling for queued requests
- [ ] Add monitoring and metrics
- [ ] Create unit tests for all algorithms
- [ ] Performance test with high request volume
- [ ] Test queue overflow scenarios
- [ ] Test clock skew handling

---

## Validation Criteria

### Performance Tests

1. **Rate Limit Accuracy:**
   - Send 200 requests in 60 seconds → All should succeed
   - Send 201 requests in 60 seconds → 1 should queue
   - Send 50 requests to /retrieveBars in 30s → All should succeed

2. **Queue Performance:**
   - Enqueue 1000 requests → Complete in < 100ms
   - Dequeue 1000 requests → Complete in < 200ms
   - Priority ordering → Highest priority always processed first

3. **Overhead:**
   - Rate limit check → < 1ms per request
   - Queue operation → < 0.5ms per operation
   - Memory usage → < 100KB for 10,000 tracked requests

### Test Scenarios

```yaml
test_scenarios:
  - name: "Respect history endpoint rate limit"
    endpoint: "/api/History/retrieveBars"
    requests: 60
    duration: 30
    expected:
      allowed: 45  # 50 * 0.9 safety buffer
      queued: 15

  - name: "Priority ordering in queue"
    queue:
      - { priority: 3, id: "req1" }
      - { priority: 10, id: "req2" }
      - { priority: 7, id: "req3" }
    expected_order: ["req2", "req3", "req1"]

  - name: "Timeout low priority requests"
    request:
      priority: 2
      maxWaitMs: 5000
    delay: 6000
    expected: "TIMEOUT"

  - name: "Persist and restore state"
    actions:
      - send 100 requests
      - shutdown
      - restart
      - send 100 more requests
    expected: rate_limit_state_preserved
```

---

## Monitoring and Metrics

### Key Metrics to Track

```yaml
metrics:
  rate_limiter:
    requests_total:
      type: counter
      labels: [endpoint, status]
      description: Total requests processed

    requests_queued:
      type: counter
      labels: [endpoint, priority]
      description: Total requests queued

    requests_timeout:
      type: counter
      labels: [endpoint, priority]
      description: Total requests that timed out

    queue_depth:
      type: gauge
      description: Current queue size

    quota_remaining:
      type: gauge
      labels: [endpoint]
      description: Remaining quota for endpoint

    rate_limit_overhead_ms:
      type: histogram
      buckets: [0.5, 1, 2, 5, 10]
      description: Rate limit check duration
```

---

## Integration with Error Handling

### Error Codes for Rate Limiting

```yaml
errors:
  RATE_LIMIT_REACHED:
    code: "RATE_LIMIT_001"
    message: "Rate limit reached. Request queued."
    retryAfterSeconds: "{calculated}"

  QUEUE_FULL:
    code: "RATE_LIMIT_002"
    message: "Request queue is full. Please retry later."
    httpStatus: 503

  REQUEST_TIMEOUT:
    code: "RATE_LIMIT_003"
    message: "Request timed out in queue."
    retryAfterSeconds: 60
```

---

## References

- **ERRORS_AND_WARNINGS_CONSOLIDATED.md** - Section 5, GAP-API-007 (lines 177-209)
- **API-INTEGRATION-ANALYSIS.md** - Section 2.3 Rate Limit Tracking
- **ERROR_CODE_MAPPING_SPEC.md** - Error code 15 (TooManyRequests)
- **RETRY_STRATEGY_SPEC.md** - Retry logic for rate-limited requests
- **CIRCUIT_BREAKER_SPEC.md** - Integration with circuit breaker

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-22 | Error Handling Spec Writer | Initial draft addressing GAP-API-007 |

---

**END OF SPECIFICATION**
