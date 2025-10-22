# Order Status Verification Specification

**doc_id:** ORDER-001
**version:** 1.0
**status:** DRAFT
**addresses:** GAP-API-SCENARIO-001 (CRITICAL) from ERRORS_AND_WARNINGS_CONSOLIDATED.md
**created:** 2025-10-22
**category:** Order Management / Network Resilience

---

## Overview

This specification defines the order status verification system that handles network interruptions during order placement. When a network failure occurs after an order has been sent but before the response is received, the system must intelligently verify whether the order was successfully placed, prevent duplicate orders, and maintain accurate state without user intervention.

**Problem Statement:**
If network fails after order sent but before response received:
- How to verify order status?
- Is idempotency supported?
- How to prevent duplicate orders?
- How to detect if order was partially filled?

**Solution:**
Multi-phase verification strategy with idempotency key generation and intelligent order matching.

---

## Requirements

### Functional Requirements

**FR-001: Automatic Network Failure Detection**
- MUST detect network timeout during order placement
- MUST distinguish between timeout and rejection
- MUST trigger verification workflow automatically
- MUST log failure timestamp and context

**FR-002: Order Status Verification**
- MUST verify order status after network interruption
- MUST support multi-phase verification strategy
- MUST handle cases where order ID is unknown
- MUST retrieve complete order state (status, fill volume, price)

**FR-003: Duplicate Order Prevention**
- MUST prevent duplicate orders through idempotency
- MUST generate unique idempotency keys
- MUST cache idempotency keys with TTL
- MUST validate against cache before retry

**FR-004: Order Matching by Characteristics**
- MUST match orders by symbol, side, quantity, and timestamp
- MUST use time window search (±60 seconds default)
- MUST handle multiple potential matches
- MUST prioritize closest timestamp match

**FR-005: State Reconciliation**
- MUST update internal state based on verification result
- MUST synchronize with positions and risk calculations
- MUST emit appropriate events for state changes
- MUST handle partial fills discovered during verification

### Non-Functional Requirements

**NFR-001: Performance**
- Verification latency MUST be < 500ms (Phase 1: direct lookup)
- Time window search MUST complete < 2000ms (Phase 2)
- Total verification timeout MUST NOT exceed 5000ms
- Idempotency check MUST be < 1ms (memory lookup)

**NFR-002: Reliability**
- Verification success rate MUST be > 99.9% for existing orders
- False negative rate (missing existing order) MUST be < 0.1%
- False positive rate (matching wrong order) MUST be 0%
- System MUST handle concurrent verifications

**NFR-003: Observability**
- MUST log all verification attempts with outcomes
- MUST track verification method used (direct/search/timeout)
- MUST emit metrics for monitoring
- MUST provide clear error messages for failures

---

## Order Status Verification State Machine

```
NETWORK_TIMEOUT
    |
    v
VERIFICATION_INITIATED
    |
    +---> PHASE_1: Direct Order ID Query
    |         |
    |         +---> FOUND → ORDER_VERIFIED
    |         |
    |         +---> NOT_FOUND → PHASE_2
    |
    +---> PHASE_2: Time Window Search
    |         |
    |         +---> MATCH_FOUND → ORDER_VERIFIED
    |         |
    |         +---> NO_MATCH → PHASE_3
    |
    +---> PHASE_3: Timeout Handling
              |
              +---> RETRY_ALLOWED → RETRY_ORDER
              |
              +---> RETRY_EXCEEDED → MANUAL_REVIEW

ORDER_VERIFIED
    |
    +---> UPDATE_INTERNAL_STATE
    |
    +---> EMIT_VERIFICATION_EVENT
    |
    +---> VERIFICATION_COMPLETE
```

### State Descriptions

1. **NETWORK_TIMEOUT**: Initial state when network failure detected
2. **VERIFICATION_INITIATED**: Verification workflow started
3. **PHASE_1**: Attempting direct order ID lookup via API
4. **PHASE_2**: Searching for order by characteristics in time window
5. **PHASE_3**: Verification failed, evaluating retry policy
6. **ORDER_VERIFIED**: Order found and state confirmed
7. **RETRY_ORDER**: Idempotency check passed, safe to retry
8. **MANUAL_REVIEW**: Verification failed, requires human intervention
9. **VERIFICATION_COMPLETE**: Process completed with state synchronized

---

## Idempotency Key Generation

### Key Format

```
Idempotency Key = SHA256(accountId + symbol + side + quantity + floor(timestamp/60000))
```

**Components:**
- `accountId`: String - Trading account identifier
- `symbol`: String - Trading symbol (e.g., "AAPL", "EURUSD")
- `side`: Enum - BUY or SELL
- `quantity`: Float - Order quantity (rounded to 8 decimals)
- `floor(timestamp/60000)`: Integer - Minute-level epoch timestamp

**Rationale:**
- SHA-256 provides 256-bit unique identifiers
- Minute-level timestamp allows retry within same minute
- Quantity included to distinguish different order sizes
- Side prevents buy/sell collision
- Account scoping for multi-account support

### Example

```yaml
Input:
  accountId: "ACC123456"
  symbol: "AAPL"
  side: "BUY"
  quantity: 100.0
  timestamp: 1729636823456  # 2025-10-22 14:13:43.456

Calculation:
  timestampMinute: floor(1729636823456 / 60000) = 28827280
  rawString: "ACC123456AAPLBUY100.028827280"
  idempotencyKey: "a7f3c9d8e1b2f4a6c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1"

Cache Entry:
  key: "a7f3c9d8e1b2f4a6c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1"
  value: "ORD-789654123"
  expiry: timestamp + 3600000  # 1 hour TTL
```

---

## Multi-Phase Verification Strategy

### Phase 1: Direct Order ID Query

**Objective:** Verify order using known order ID (if available from partial response)

**Prerequisites:**
- Order ID received before network failure
- Authentication token valid

**Process:**
1. Call `/api/Order/getOrder` with order ID
2. Parse response for order status
3. Validate order matches expected characteristics
4. Return verification result

**API Call:**
```http
GET /api/Order/getOrder?orderId=ORD-789654123
Authorization: Bearer {jwt_token}
```

**Success Response:**
```json
{
  "errorCode": 0,
  "errorMessage": "",
  "result": {
    "orderId": "ORD-789654123",
    "accountId": "ACC123456",
    "symbol": "AAPL",
    "side": "BUY",
    "quantity": 100.0,
    "orderType": "MARKET",
    "status": "FILLED",
    "fillVolume": 100.0,
    "filledPrice": 178.45,
    "timestamp": 1729636823789
  }
}
```

**Validation:**
- Verify `accountId` matches expected
- Verify `symbol` matches expected
- Verify `side` matches expected
- Verify `quantity` matches expected (±0.00000001 tolerance)
- If mismatch detected → Log warning and proceed to Phase 2

**Outcome:**
- **FOUND**: Order verified, update internal state
- **NOT_FOUND**: Proceed to Phase 2

---

### Phase 2: Time Window Search

**Objective:** Find order by characteristics when order ID unknown

**Prerequisites:**
- Phase 1 failed or order ID unavailable
- Order characteristics known (symbol, side, quantity, approximate timestamp)

**Process:**
1. Calculate search time window (default ±60 seconds)
2. Call `/api/Order/listOrders` with filters
3. Filter results by exact match on symbol, side, quantity
4. Select best match by timestamp proximity
5. Validate match quality score
6. Return verification result

**API Call:**
```http
GET /api/Order/listOrders?accountId=ACC123456&startTime=1729636763456&endTime=1729636883456&symbol=AAPL
Authorization: Bearer {jwt_token}
```

**Success Response:**
```json
{
  "errorCode": 0,
  "errorMessage": "",
  "result": {
    "orders": [
      {
        "orderId": "ORD-789654123",
        "accountId": "ACC123456",
        "symbol": "AAPL",
        "side": "BUY",
        "quantity": 100.0,
        "orderType": "MARKET",
        "status": "FILLED",
        "fillVolume": 100.0,
        "filledPrice": 178.45,
        "timestamp": 1729636823789
      }
    ]
  }
}
```

**Matching Algorithm:**
```python
def find_matching_order(orders, expected):
    exact_matches = []

    for order in orders:
        # Exact match criteria
        if (order.symbol == expected.symbol and
            order.side == expected.side and
            abs(order.quantity - expected.quantity) < 0.00000001 and
            order.accountId == expected.accountId):

            # Calculate match score (lower is better)
            time_diff = abs(order.timestamp - expected.timestamp)
            match_score = time_diff

            exact_matches.append({
                'order': order,
                'score': match_score,
                'time_diff_ms': time_diff
            })

    if not exact_matches:
        return None

    # Return closest timestamp match
    best_match = min(exact_matches, key=lambda x: x['score'])

    # Validate match quality
    if best_match['time_diff_ms'] > 60000:  # More than 60 seconds
        log_warning("Match found but timestamp diff > 60s")

    return best_match['order']
```

**Match Quality Thresholds:**
- Excellent: time_diff < 5000ms (5 seconds)
- Good: time_diff < 30000ms (30 seconds)
- Acceptable: time_diff < 60000ms (60 seconds)
- Suspicious: time_diff > 60000ms (requires manual review)

**Outcome:**
- **MATCH_FOUND**: Order verified, update internal state
- **NO_MATCH**: Proceed to Phase 3
- **MULTIPLE_MATCHES**: Select best match by timestamp, log warning

---

### Phase 3: Timeout Handling

**Objective:** Determine safe course of action when order cannot be verified

**Prerequisites:**
- Phase 1 and Phase 2 both failed
- Retry policy not exceeded

**Decision Tree:**
```
NO_MATCH_FOUND
    |
    +---> Check idempotency cache
    |         |
    |         +---> KEY_EXISTS → Order previously submitted → WAIT_AND_RETRY_VERIFICATION
    |         |
    |         +---> KEY_NOT_EXISTS → SAFE_TO_RETRY_ORDER
    |
    +---> Check retry count
              |
              +---> retries < maxRetries → RETRY_ORDER_PLACEMENT
              |
              +---> retries >= maxRetries → MANUAL_REVIEW_REQUIRED
```

**Retry Policy:**
- Maximum verification attempts: 3
- Retry interval: [2s, 5s, 10s] (exponential backoff)
- Maximum total verification time: 30 seconds
- After max retries → Escalate to manual review

**Safe Retry Criteria:**
```yaml
SafeToRetry: true
Conditions:
  - idempotencyKey NOT in cache
  - OR cacheEntry.age > 60 seconds
  - AND retryCount < maxRetries
  - AND totalElapsedTime < 30000ms
```

**Outcome:**
- **RETRY_ALLOWED**: Re-attempt order placement with same idempotency key
- **RETRY_EXCEEDED**: Mark for manual review, alert operator
- **WAIT_AND_VERIFY**: Wait for order settlement, retry verification

---

## Configuration Schema

```yaml
orderManagement:
  verification:
    # Phase 1: Direct lookup
    directLookupTimeout: 500       # milliseconds
    directLookupRetries: 2

    # Phase 2: Time window search
    timeWindowSeconds: 60          # ±60 seconds from expected timestamp
    searchTimeout: 2000            # milliseconds
    searchRetries: 1

    # Phase 3: Retry handling
    maxVerificationAttempts: 3
    verificationRetryIntervals: [2000, 5000, 10000]  # ms, exponential backoff
    totalVerificationTimeout: 30000  # 30 seconds max

    # Match quality
    matchQualityThresholds:
      excellent: 5000              # 5 seconds
      good: 30000                  # 30 seconds
      acceptable: 60000            # 60 seconds
      suspicious: 120000           # 2 minutes (requires manual review)

    # Validation
    quantityTolerance: 0.00000001  # Float comparison tolerance

  idempotency:
    # Cache configuration
    enabled: true
    cacheTTL: 3600000              # 1 hour = 3600000ms
    cacheCleanupInterval: 300000   # 5 minutes
    hashAlgorithm: "SHA256"

    # Key generation
    timestampResolution: 60000     # 1 minute = 60000ms
    includeQuantity: true
    includeSide: true

  alerting:
    # Notification thresholds
    alertOnVerificationFailure: true
    alertOnMultipleMatches: true
    alertOnSuspiciousMatch: true
    alertOnRetryExceeded: true

  logging:
    # Detailed logging for troubleshooting
    logAllVerifications: true
    logIdempotencyChecks: true
    logMatchScores: true
```

---

## Data Structures

### OrderVerificationRequest

```yaml
OrderVerificationRequest:
  orderId: string | null                    # If known from partial response
  expectedOrder:
    accountId: string                       # Required
    symbol: string                          # Required
    side: "BUY" | "SELL"                    # Required
    quantity: float                         # Required
    orderType: "MARKET" | "LIMIT" | "STOP" | "STOP_LIMIT"  # Required
    limitPrice: float | null                # For LIMIT/STOP_LIMIT
    stopPrice: float | null                 # For STOP/STOP_LIMIT
    timestamp: integer                      # Milliseconds since epoch
  context:
    requestId: string                       # Unique request identifier
    retryCount: integer                     # Current retry attempt
    failureTimestamp: integer               # When network failure occurred
    timeoutDuration: integer                # How long before timeout
```

### OrderVerificationResult

```yaml
OrderVerificationResult:
  success: boolean                          # True if order found and verified
  verificationMethod: "direct" | "search" | "timeout" | "failed"
  order: Order | null                       # Complete order details if found
  matchQuality: "excellent" | "good" | "acceptable" | "suspicious" | null
  timeDifferenceMs: integer | null          # Timestamp difference for search matches
  phase: 1 | 2 | 3                          # Which phase found the order
  message: string                           # Human-readable result description
  metadata:
    verificationStartTime: integer          # Timestamp
    verificationEndTime: integer            # Timestamp
    verificationDurationMs: integer         # Total time taken
    attemptNumber: integer                  # Which verification attempt
    apiCallsRequired: integer               # Number of API calls made
```

### IdempotencyCache

```yaml
IdempotencyCacheEntry:
  idempotencyKey: string                    # SHA-256 hash
  orderId: string | null                    # Linked order ID (if known)
  orderDetails:
    accountId: string
    symbol: string
    side: "BUY" | "SELL"
    quantity: float
    orderType: string
  timestamps:
    created: integer                        # When key was generated
    expiry: integer                         # When cache entry expires
    lastAccessed: integer                   # Last cache hit
  status: "pending" | "submitted" | "verified" | "failed"
  metadata:
    requestId: string
    retryCount: integer
```

---

## Error Scenarios & Recovery

### Scenario 1: Network Failure After Order Sent

**Situation:**
- Order placement API call sent successfully
- Network timeout before receiving response
- Order status unknown

**Detection:**
```python
try:
    response = api.placeOrder(order)
except NetworkTimeout as e:
    # Network failure detected
    initiate_verification(order, e.request_id)
```

**Recovery:**
1. Log network failure with context
2. Initiate Phase 1 verification (direct lookup if order ID known)
3. If Phase 1 fails → Phase 2 (time window search)
4. If Phase 2 fails → Phase 3 (retry policy)
5. Update internal state based on verification result
6. If order found → Synchronize state, no retry
7. If order not found → Check idempotency, potentially retry

**Expected Outcome:**
- Order verified OR safely determined as not placed
- No duplicate orders created
- Internal state accurate

---

### Scenario 2: Partial Response Received

**Situation:**
- API response started but connection dropped mid-transmission
- Order ID received but status unknown

**Detection:**
```python
try:
    response = api.placeOrder(order)
    order_id = response.get('orderId')  # Got ID
    status = response.get('status')      # Connection dropped before this
except PartialResponseError as e:
    initiate_verification(order, e.order_id)
```

**Recovery:**
1. Use Phase 1 (direct lookup) with known order ID
2. Retrieve complete order state
3. Validate order characteristics match expected
4. Update internal state with verified details

**Expected Outcome:**
- Order status confirmed
- State synchronized accurately
- No verification delay

---

### Scenario 3: Multiple Matching Orders Found

**Situation:**
- Phase 2 search returns multiple orders matching characteristics
- Timestamp-based disambiguation needed

**Detection:**
```python
matches = search_orders(symbol, side, quantity, time_window)
if len(matches) > 1:
    log_warning(f"Multiple matches found: {len(matches)}")
```

**Recovery:**
1. Calculate match score for each candidate
2. Select order with closest timestamp
3. Log warning with all candidate order IDs
4. If timestamp difference > 60s → Escalate to manual review
5. Otherwise → Verify selected match
6. Store verification result with "multiple_matches" flag

**Expected Outcome:**
- Best match selected by timestamp proximity
- Manual review triggered if ambiguous
- Verification logged with warning flag

---

### Scenario 4: Verification API Failure

**Situation:**
- Network recovered but verification API calls fail
- Cannot confirm order status

**Detection:**
```python
try:
    result = api.getOrder(order_id)
except APIError as e:
    if e.is_retryable:
        schedule_retry_verification()
    else:
        escalate_to_manual_review()
```

**Recovery:**
1. Classify error type (retryable vs fatal)
2. If retryable (500, timeout) → Retry with exponential backoff
3. If fatal (401, 403) → Check authentication, refresh token
4. If persistent failure → Escalate to manual review
5. Alert monitoring system

**Expected Outcome:**
- Transient errors handled with retries
- Authentication errors trigger token refresh
- Persistent failures escalated appropriately

---

### Scenario 5: Idempotency Cache Hit on Retry

**Situation:**
- Order placement failed with timeout
- Retry attempted after verification
- Idempotency key exists in cache from previous attempt

**Detection:**
```python
idempotency_key = generate_key(order)
if idempotency_key in cache:
    cached_order = cache.get(idempotency_key)
    # Order was previously submitted
```

**Recovery:**
1. Check cache entry status
2. If status = "pending" → Order still processing, wait and verify
3. If status = "submitted" → Retrieve order ID, run Phase 1 verification
4. If status = "verified" → Return cached verification result
5. If cache expired → Safe to retry placement

**Expected Outcome:**
- Duplicate order prevented
- Existing order status retrieved
- No unnecessary retries

---

## Implementation Checklist

### Phase 1 Implementation
- [ ] Implement direct order ID lookup
- [ ] Add timeout handling (500ms)
- [ ] Validate order characteristics match
- [ ] Return structured verification result

### Phase 2 Implementation
- [ ] Implement time window calculation (±60s)
- [ ] Build order search query with filters
- [ ] Implement matching algorithm with scoring
- [ ] Handle multiple matches scenario
- [ ] Add match quality assessment

### Phase 3 Implementation
- [ ] Implement retry policy with exponential backoff
- [ ] Add manual review escalation
- [ ] Build retry eligibility checker
- [ ] Implement retry limit enforcement

### Idempotency System
- [ ] Implement SHA-256 key generation
- [ ] Build in-memory cache with TTL
- [ ] Add cache cleanup job (5-minute interval)
- [ ] Implement cache hit/miss metrics
- [ ] Add idempotency validation before retry

### Error Handling
- [ ] Classify error types (retryable vs fatal)
- [ ] Implement network timeout detection
- [ ] Add partial response handling
- [ ] Build error context logging
- [ ] Implement alert notifications

### State Management
- [ ] Update internal order state on verification
- [ ] Synchronize positions after verification
- [ ] Emit verification events for listeners
- [ ] Handle partial fills discovered during verification
- [ ] Update risk calculations based on verified state

### Configuration & Testing
- [ ] Load verification configuration from YAML
- [ ] Validate configuration on startup
- [ ] Add configuration override mechanism
- [ ] Write unit tests for all phases
- [ ] Write integration tests for network scenarios
- [ ] Test idempotency key generation
- [ ] Test concurrent verifications

---

## Validation Criteria

### Zero Duplicate Orders
**Target:** 0% duplicate order rate during network failures
- No duplicate orders even with multiple retry attempts
- Idempotency cache prevents double-submission
- Verification detects existing orders before retry

**Validation Method:**
- Simulate 1000 network failures during order placement
- Verify exactly 1 order placed per original request
- Check database for duplicate orders by idempotency key

### High Verification Success Rate
**Target:** >99.9% verification success for existing orders
- Phase 1 finds orders when ID available (>99% success)
- Phase 2 finds orders by characteristics (>95% success)
- Combined verification rate >99.9%

**Validation Method:**
- Place 10,000 orders with simulated network failures
- Track verification success rate per phase
- Measure false negative rate (missing existing orders)

### Fast Verification Performance
**Target:** Average verification latency <500ms
- Phase 1: <200ms average
- Phase 2: <1500ms average
- 95th percentile: <2000ms

**Validation Method:**
- Measure verification duration across 10,000 attempts
- Calculate p50, p95, p99 latencies
- Identify bottlenecks in slow verifications

### Accurate Order Matching
**Target:** 0% false positive matches
- Never match wrong order to request
- Strict validation on all order characteristics
- Timestamp proximity scoring prevents mismatches

**Validation Method:**
- Create test scenarios with similar orders (same symbol, different quantity)
- Verify matching algorithm selects correct order
- Test edge cases (simultaneous orders, rapid retries)

---

## Metrics & Monitoring

### Verification Metrics
```yaml
Metrics:
  - name: "order_verification_attempts_total"
    type: counter
    labels: [phase, outcome]
    description: "Total verification attempts by phase and outcome"

  - name: "order_verification_duration_ms"
    type: histogram
    labels: [phase]
    description: "Verification duration distribution"
    buckets: [100, 200, 500, 1000, 2000, 5000]

  - name: "order_verification_success_rate"
    type: gauge
    labels: [phase]
    description: "Verification success rate per phase"

  - name: "order_verification_match_quality"
    type: histogram
    labels: [quality]
    description: "Distribution of match quality scores"

  - name: "idempotency_cache_hits"
    type: counter
    description: "Number of idempotency cache hits"

  - name: "idempotency_cache_misses"
    type: counter
    description: "Number of idempotency cache misses"

  - name: "duplicate_orders_prevented"
    type: counter
    description: "Number of duplicate orders prevented by idempotency"

  - name: "manual_review_escalations"
    type: counter
    labels: [reason]
    description: "Number of verifications escalated to manual review"
```

### Alerting Rules
```yaml
Alerts:
  - name: "HighVerificationFailureRate"
    condition: "order_verification_success_rate < 0.95"
    severity: "HIGH"
    message: "Order verification success rate dropped below 95%"

  - name: "FrequentManualReviewEscalations"
    condition: "rate(manual_review_escalations[5m]) > 5"
    severity: "MEDIUM"
    message: "More than 5 manual reviews required in 5 minutes"

  - name: "SlowVerificationPerformance"
    condition: "histogram_quantile(0.95, order_verification_duration_ms) > 3000"
    severity: "MEDIUM"
    message: "95th percentile verification latency > 3 seconds"

  - name: "IdempotencyCacheFailure"
    condition: "idempotency_cache_hits == 0 for 5m"
    severity: "HIGH"
    message: "Idempotency cache not functioning"
```

---

## References

1. **ERRORS_AND_WARNINGS_CONSOLIDATED.md**
   - GAP-API-SCENARIO-001: Network interruption during order placement (CRITICAL)
   - Lines 182-191

2. **Related Specifications**
   - ORDER_IDEMPOTENCY_SPEC.md (Idempotency key details)
   - PARTIAL_FILL_TRACKING_SPEC.md (Partial fill handling)
   - ORDER_LIFECYCLE_SPEC.md (Complete state machine)

3. **API Documentation**
   - `/api/Order/placeOrder` - Order placement
   - `/api/Order/getOrder` - Order status retrieval
   - `/api/Order/listOrders` - Order search

---

**Document Status:** DRAFT - Ready for Technical Review
**Next Steps:**
1. Technical review by architecture team
2. Security review of idempotency implementation
3. Performance validation with load testing
4. Integration with existing order management system
5. Update to APPROVED status after review
