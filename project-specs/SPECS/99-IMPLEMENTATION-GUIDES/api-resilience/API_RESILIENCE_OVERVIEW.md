---
doc_id: GUIDE-001
title: API Resilience Layer - Overview and Integration
version: 2.0
status: DRAFT
last_updated: 2025-10-22
purpose: Executive summary of all 41 API resilience issues and their integration
dependencies: [ERRORS_AND_WARNINGS_CONSOLIDATED.md, api-integration-analysis.md]
---

# API Resilience Layer - Overview and Integration

**Critical Understanding:** This specification defines the foundational API resilience layer that MUST be implemented BEFORE risk rules implementation begins.

---

## 📋 Executive Summary

Analysis of the TopstepX Gateway API integration revealed **41 critical issues** across authentication, SignalR connections, error handling, and network resilience. These issues must be addressed before risk rules implementation to prevent:

- Duplicate orders during network failures
- Data loss during reconnections
- Token expiration mid-operation
- Unhandled API errors causing crashes
- Rate limit violations causing service throttling
- Authentication bypass vulnerabilities

**Severity Breakdown:**
- **8 CRITICAL** - Must fix before MVP
- **6 HIGH** - Security and reliability concerns
- **5 MEDIUM** - Missing scenarios and edge cases
- **22 LOW** - Enhancements and documentation

---

## 🎯 Component Architecture

### Dependency Graph

```
                    ┌─────────────────────────┐
                    │   Token Manager         │
                    │  (Foundation Layer)     │
                    │  - Token refresh        │
                    │  - Secure storage       │
                    │  - Lifecycle mgmt       │
                    └───────────┬─────────────┘
                                │ provides tokens
                                ▼
┌────────────────────────────────────────────────────────┐
│              SignalR Connection Manager                 │
│              (Real-time Communication)                  │
│  - Connection lifecycle (connect/reconnect/close)      │
│  - Exponential backoff                                 │
│  - Health monitoring                                   │
│  - Event subscription                                  │
└───────────────────┬────────────────────────────────────┘
                    │ triggers on reconnect
                    ▼
            ┌───────────────────┐
            │  State Reconciler │
            │  - Sync positions │
            │  - Sync orders    │
            │  - Verify state   │
            └────────┬──────────┘
                     │ uses
                     ▼
    ┌─────────────────────────────────────┐
    │         Error Handler               │
    │   (Central Error Processing)        │
    │   - Error code mapping              │
    │   - Retry strategies                │
    │   - Circuit breaker                 │
    │   - Fallback modes                  │
    └────────┬────────────────────────────┘
             │ coordinates with
             ▼
    ┌────────────────────┐      ┌──────────────────┐
    │   Rate Limiter     │      │ Circuit Breaker  │
    │   - Request queue  │      │ - Failure detect │
    │   - Throttling     │      │ - Service health │
    │   - Backpressure   │      │ - Auto-recovery  │
    └────────────────────┘      └──────────────────┘
             │                           │
             └───────────┬───────────────┘
                         │ protects
                         ▼
             ┌───────────────────────┐
             │  Order Management     │
             │  - Order verification │
             │  - Idempotency        │
             │  - Partial fills      │
             └───────────────────────┘
```

### Integration Flow

```
Startup Sequence:
┌──────────────────────────────────────────────────────┐
│ 1. Token Manager initializes                         │
│    └─> Load/decrypt stored token OR authenticate     │
│                                                       │
│ 2. SignalR Connection Manager starts                 │
│    └─> Connect with token from Token Manager         │
│                                                       │
│ 3. State Reconciler performs initial sync            │
│    └─> Fetch positions, orders, account from REST    │
│                                                       │
│ 4. Error Handler + Rate Limiter initialize           │
│    └─> Ready to handle requests with protection      │
│                                                       │
│ 5. Risk Rules Engine starts (depends on above)       │
│    └─> Begin monitoring with resilient infrastructure│
└──────────────────────────────────────────────────────┘

Event Processing Flow:
┌──────────────────────────────────────────────────────┐
│ SignalR Event Received                               │
│         │                                             │
│         ▼                                             │
│ Error Handler wraps processing                       │
│         │                                             │
│         ▼                                             │
│ Rate Limiter checks throttling                       │
│         │                                             │
│         ▼                                             │
│ Risk Rule processes event                            │
│         │                                             │
│         ▼                                             │
│ Enforcement Action (if needed)                       │
│         │                                             │
│         ├─> Order Placement                          │
│         │   └─> Idempotency check                    │
│         │   └─> Rate limit check                     │
│         │   └─> Circuit breaker check                │
│         │   └─> Order verification                   │
│         │                                             │
│         └─> Position Close                           │
│             └─> Same protection layers               │
└──────────────────────────────────────────────────────┘

Reconnection Flow:
┌──────────────────────────────────────────────────────┐
│ SignalR Connection Lost                              │
│         │                                             │
│         ▼                                             │
│ Connection Manager detects loss                      │
│         │                                             │
│         ▼                                             │
│ Exponential backoff retry logic                     │
│  Delays: [0ms, 2s, 10s, 30s, 60s]                   │
│         │                                             │
│         ▼                                             │
│ Token Manager validates token                        │
│         │                                             │
│         ├─> If expired: Refresh token                │
│         └─> If valid: Use existing                   │
│         │                                             │
│         ▼                                             │
│ Reconnection succeeds                                │
│         │                                             │
│         ▼                                             │
│ State Reconciler triggered                           │
│         │                                             │
│         ├─> Fetch latest positions (REST)            │
│         ├─> Fetch latest orders (REST)               │
│         ├─> Compare with cached state                │
│         ├─> Detect missed events                     │
│         └─> Update state and resume                  │
└──────────────────────────────────────────────────────┘
```

---

## 🚨 Critical Issues Summary

### Authentication Layer (8 issues)

**GAP-API-001: Token Refresh Strategy**
- **Severity:** CRITICAL
- **Issue:** No proactive refresh, tokens expire during operations
- **Solution:** Refresh 2 hours before expiry
- **Spec:** `TOKEN_REFRESH_STRATEGY_SPEC.md`

**GAP-API-002: Token Storage Security**
- **Severity:** HIGH
- **Issue:** No secure storage guidance
- **Solution:** Encrypted storage with AES-256
- **Spec:** `TOKEN_STORAGE_SECURITY_SPEC.md`

**GAP-API-SCENARIO-005: Token Expiration During Long Operations**
- **Severity:** CRITICAL
- **Issue:** Operations fail mid-execution
- **Solution:** Pre-operation token validation + refresh
- **Spec:** `TOKEN_REFRESH_STRATEGY_SPEC.md`

### SignalR Connection Layer (4 issues)

**GAP-API-003: Incomplete Reconnection Logic**
- **Severity:** CRITICAL
- **Issue:** Missing onclose, onreconnecting handlers
- **Solution:** Complete handler implementation
- **Spec:** `SIGNALR_RECONNECTION_SPEC.md`

**GAP-API-004: No Exponential Backoff**
- **Severity:** CRITICAL
- **Issue:** Rapid reconnection attempts overwhelm server
- **Solution:** Exponential backoff: [0, 2s, 10s, 30s, 60s]
- **Spec:** `EXPONENTIAL_BACKOFF_SPEC.md`

**GAP-API-005: Missing Health Monitoring**
- **Severity:** HIGH
- **Issue:** Can't detect stale connections
- **Solution:** Heartbeat mechanism with timeouts
- **Spec:** `CONNECTION_HEALTH_MONITORING_SPEC.md`

**GAP-API-SCENARIO-003: SignalR Message Loss**
- **Severity:** CRITICAL
- **Issue:** Missed events during reconnection
- **Solution:** State reconciliation via REST after reconnect
- **Spec:** `STATE_RECONCILIATION_SPEC.md`

### Error Handling Layer (3 issues)

**GAP-API-006: Inadequate Error Code Documentation**
- **Severity:** CRITICAL
- **Issue:** Only success/401 documented, missing 400/429/500 codes
- **Solution:** Comprehensive error code mapping
- **Spec:** `ERROR_CODE_MAPPING_SPEC.md`

**GAP-API-007: No Rate Limit Tracking**
- **Severity:** CRITICAL
- **Issue:** Client hits 429 errors, no pre-emptive throttling
- **Solution:** Client-side rate limiter with queuing
- **Spec:** `RATE_LIMITING_SPEC.md`

**GAP-API-008: No Circuit Breaker**
- **Severity:** HIGH
- **Issue:** Repeated failures cascade
- **Solution:** Circuit breaker pattern
- **Spec:** `CIRCUIT_BREAKER_SPEC.md`

### Order Management Layer (2 issues)

**GAP-API-SCENARIO-001: Network Interruption During Order Placement**
- **Severity:** CRITICAL
- **Issue:** Duplicate orders or lost orders
- **Solution:** Order verification + idempotency
- **Spec:** `ORDER_VERIFICATION_IDEMPOTENCY_SPEC.md`

**GAP-API-SCENARIO-002: Partial Order Fills**
- **Severity:** HIGH
- **Issue:** Incorrect position tracking
- **Solution:** Track partial fills via SignalR events
- **Spec:** `PARTIAL_FILL_TRACKING_SPEC.md`

---

## 📊 Implementation Phases

### Phase 0: API Resilience Foundation (7-10 days)
**Status:** NEW CRITICAL PHASE - MUST COMPLETE BEFORE RISK RULES

#### Week 1: Core Infrastructure (3-5 days)

**Day 1-2: Token Manager (CRITICAL)**
- Token refresh strategy (2-hour buffer before expiry)
- Secure token storage (AES-256 encryption)
- Lifecycle management (validate/refresh/re-authenticate)
- **Acceptance:** Tokens never expire during operations, stored securely

**Day 2-3: Error Handler + Retry Strategy (CRITICAL)**
- Error code mapping (all HTTP codes + TopstepX error codes)
- Retry strategies (exponential backoff for transient errors)
- Error classification (transient vs permanent)
- **Acceptance:** All errors handled gracefully, appropriate retries

**Day 3: Rate Limiter (CRITICAL)**
- Request tracking (sliding window)
- Pre-emptive throttling (stay under 50/30s and 200/60s)
- Request queuing with backpressure
- **Acceptance:** Zero 429 errors, smooth request flow

#### Week 2: Resilience Layer (4-5 days)

**Day 4-6: SignalR Connection Manager (CRITICAL)**
- Connection lifecycle (connect/reconnect/close handlers)
- Exponential backoff ([0, 2000, 10000, 30000, 60000] ms)
- Health monitoring (heartbeat every 30s)
- Connection state management
- **Acceptance:** Reconnection works, no message loss, health tracking

**Day 6: State Reconciliation (CRITICAL)**
- Post-reconnect state sync
- Position/order verification via REST
- Detect and log missed events
- **Acceptance:** State accurate after reconnection

**Day 7: Circuit Breaker (HIGH)**
- Failure threshold detection (5 failures)
- Circuit states (closed/open/half-open)
- Service health tracking
- **Acceptance:** Service degradation detected, fallback works

**Day 7-8: Order Management (CRITICAL)**
- Order verification after placement
- Idempotency checks (prevent duplicates)
- Partial fill tracking
- Order timeout handling
- **Acceptance:** Zero duplicate orders, partial fills tracked

**Day 9-10: Integration Testing**
- Chaos testing (network failures, token expiration)
- Load testing (rate limits, circuit breaker)
- Reconnection testing (SignalR disconnect/reconnect)
- End-to-end testing (order placement with failures)
- **Acceptance:** All chaos tests pass, 90%+ coverage

### Phase 1: Risk Rules MVP (3-5 days)
**Depends on:** Phase 0 complete

Continue with existing roadmap - now with resilient API foundation.

---

## 🔧 Configuration Integration

### Master Configuration Schema

```yaml
# config.yaml - Master configuration for all resilience components

api:
  baseUrl: "https://gateway.topstepx.com"
  timeout: 30000  # 30 seconds default

authentication:
  tokenRefresh:
    bufferSeconds: 7200  # 2 hours before expiry
    maxRetries: 3
    retryDelayMs: [1000, 5000, 15000]
  storage:
    type: "encrypted"  # "encrypted" or "memory"
    encryption: "AES-256"
    keySource: "environment"  # "environment" or "keyring"

signalr:
  reconnection:
    maxAttempts: 10
    delays: [0, 2000, 10000, 30000, 60000]  # Exponential backoff
    maxDelayMs: 60000
  health:
    pingInterval: 30000  # 30 seconds
    pingTimeout: 5000    # 5 seconds
    staleThreshold: 120000  # 2 minutes
  subscriptions:
    autoResubscribe: true
    resubscribeDelay: 1000  # 1 second after reconnect

errorHandling:
  retries:
    maxAttempts: 5
    backoffBase: 1000  # 1 second
    backoffMultiplier: 2  # Exponential
    maxBackoffMs: 60000  # 1 minute cap
    retryableErrors:
      - 408  # Request Timeout
      - 429  # Too Many Requests
      - 500  # Internal Server Error
      - 502  # Bad Gateway
      - 503  # Service Unavailable
      - 504  # Gateway Timeout
  rateLimit:
    history:
      requests: 50
      windowSeconds: 30
    general:
      requests: 200
      windowSeconds: 60
    queueSize: 1000
    dropOldest: true
  circuitBreaker:
    failureThreshold: 5
    timeout: 60000  # 1 minute
    halfOpenRequests: 3

orderManagement:
  verification:
    enabled: true
    timeout: 5000  # 5 seconds
    maxRetries: 3
  partialFills:
    trackingEnabled: true
    completeTimeout: 60000  # 1 minute
  idempotency:
    enabled: true
    cacheTTL: 3600  # 1 hour

stateReconciliation:
  enabled: true
  onReconnect: true
  minInterval: 5000  # Minimum 5 seconds between reconciliations
  comparePositions: true
  compareOrders: true
  compareAccount: true

database:
  schemaVersion: 2
  retention:
    dailyUnrealizedPnl: 7  # days
    enforcementLogs: 30
    orderHistory: 90

logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  resilience:
    tokenRefresh: true
    reconnections: true
    errorRetries: true
    rateLimit: true
    circuitBreaker: true
```

---

## 🧪 Testing Requirements

### Unit Tests Per Component

**Token Manager (15+ tests)**
- Proactive refresh at buffer threshold
- Fallback to re-authentication on refresh failure
- Token expiration detection
- Secure storage encryption/decryption
- Concurrent request handling during refresh

**SignalR Connection Manager (20+ tests)**
- Connection lifecycle (connect/disconnect)
- Reconnection with exponential backoff
- Health monitoring (heartbeat/timeout)
- Event subscription/resubscription
- Connection state transitions

**Error Handler (25+ tests)**
- Error code mapping (all HTTP codes)
- Retry strategy (exponential backoff)
- Retry limit enforcement
- Transient vs permanent error classification
- Error logging and reporting

**Rate Limiter (10+ tests)**
- Sliding window tracking
- Pre-emptive throttling
- Request queuing
- Queue overflow handling
- Concurrent request throttling

**Circuit Breaker (12+ tests)**
- Failure threshold detection
- Circuit state transitions (closed/open/half-open)
- Half-open request testing
- Timeout and recovery
- Service health tracking

**Order Verification (15+ tests)**
- Order status verification after placement
- Idempotency check (duplicate detection)
- Partial fill tracking
- Network failure during placement
- Timeout handling

### Integration Tests

1. **Token Refresh During Active Operation**
   - Start long-running operation
   - Trigger token refresh during operation
   - Verify operation completes successfully
   - **Pass Criteria:** Zero operation failures

2. **SignalR Reconnection with State Sync**
   - Establish SignalR connection
   - Disconnect network
   - Place order via separate channel (simulate missed event)
   - Reconnect network
   - Verify state reconciliation detects order
   - **Pass Criteria:** State accurate after reconnection

3. **Rate Limit Enforcement**
   - Submit burst of requests (>50 in 30s)
   - Verify throttling occurs
   - Verify no 429 errors
   - Verify all requests eventually complete
   - **Pass Criteria:** Zero rate limit errors

4. **Circuit Breaker Triggers Fallback**
   - Simulate 5 consecutive API failures
   - Verify circuit opens
   - Verify fallback mode activates
   - Wait for timeout
   - Verify circuit half-opens
   - Verify successful requests close circuit
   - **Pass Criteria:** Circuit breaker prevents cascade

5. **Order Placement Network Failure**
   - Place order
   - Disconnect network after send but before response
   - Reconnect network
   - Verify order verification detects order status
   - Verify no duplicate order placed
   - **Pass Criteria:** Zero duplicates, order verified

### Chaos Engineering Tests

1. **Network Failure During Order Placement**
   - Disconnect at random point during order placement
   - Verify order verification recovers state
   - Verify idempotency prevents duplicates

2. **Token Expiration Mid-Operation**
   - Start operation with token near expiry
   - Let token expire during operation
   - Verify automatic refresh and retry
   - Verify operation completes

3. **SignalR Disconnection During High Volume**
   - Subscribe to all events
   - Generate high event volume (60+ events/sec)
   - Disconnect SignalR randomly
   - Verify reconnection and state sync
   - Verify no data loss

4. **API Rate Limit Hit**
   - Submit burst exceeding rate limit
   - Verify throttling works
   - Verify request queuing
   - Verify all requests complete

5. **Server Error Cascade**
   - Simulate repeated 500 errors
   - Verify circuit breaker opens
   - Verify fallback mode
   - Verify recovery after server returns

---

## ✅ Acceptance Criteria

### Phase 0 Complete When:

**Token Management:**
- [ ] Tokens refresh automatically 2 hours before expiry
- [ ] Tokens stored encrypted (AES-256)
- [ ] Fallback to re-authentication works
- [ ] Zero token expiration failures in testing
- [ ] Concurrent request handling during refresh

**SignalR Connection:**
- [ ] All event handlers implemented (onconnected, onclose, onreconnecting, onreconnected)
- [ ] Exponential backoff working correctly
- [ ] Health monitoring detects stale connections
- [ ] Reconnection success rate >99%
- [ ] Zero message loss in reconnection tests

**Error Handling:**
- [ ] All error codes mapped and documented
- [ ] Retry strategies work correctly
- [ ] Circuit breaker triggers at threshold
- [ ] Fallback modes functional
- [ ] Error logging comprehensive

**Rate Limiting:**
- [ ] Zero 429 errors in testing
- [ ] Request queuing works correctly
- [ ] Throttling stays under limits
- [ ] Backpressure handled gracefully

**Order Management:**
- [ ] Zero duplicate orders in failure tests
- [ ] Order verification detects status correctly
- [ ] Idempotency checks prevent duplicates
- [ ] Partial fills tracked accurately
- [ ] Network failure tests pass 100%

**Testing:**
- [ ] 90%+ unit test coverage
- [ ] All integration tests pass
- [ ] All chaos tests pass
- [ ] Performance benchmarks met
- [ ] Code review completed

**Documentation:**
- [ ] All specification documents complete
- [ ] Implementation guides written
- [ ] Configuration examples provided
- [ ] Troubleshooting guide created

---

## 📈 Implementation Order

**CRITICAL: Follow this exact sequence**

```
Phase 0: API Resilience (7-10 days)
├── 1. Token Manager                  (Days 1-2) ← START HERE
│   ├── Token refresh strategy
│   ├── Secure storage
│   └── Lifecycle management
│
├── 2. Error Handler + Rate Limiter   (Days 2-3)
│   ├── Error code mapping
│   ├── Retry strategies
│   └── Rate limiting
│
├── 3. SignalR Connection Manager     (Days 4-6)
│   ├── Connection lifecycle
│   ├── Exponential backoff
│   ├── Health monitoring
│   └── Event subscriptions
│
├── 4. State Reconciliation          (Day 6)
│   ├── Post-reconnect sync
│   ├── Position/order verification
│   └── Missed event detection
│
├── 5. Circuit Breaker               (Day 7)
│   ├── Failure detection
│   ├── Circuit states
│   └── Service health
│
├── 6. Order Management              (Days 7-8)
│   ├── Order verification
│   ├── Idempotency
│   └── Partial fill tracking
│
└── 7. Integration Testing           (Days 9-10)
    ├── Unit tests
    ├── Integration tests
    ├── Chaos tests
    └── Performance tests

Phase 1: Risk Rules MVP (3-5 days)
└── (Existing roadmap continues with resilient foundation)
```

**Dependencies:**
- SignalR Connection Manager depends on Token Manager
- State Reconciliation depends on SignalR Connection Manager
- Order Management depends on Error Handler + Rate Limiter
- Risk Rules depend on ALL Phase 0 components

---

## 🔗 Related Specifications

### Authentication & Security
- `/01-EXTERNAL-API/security/TOKEN_REFRESH_STRATEGY_SPEC.md`
- `/01-EXTERNAL-API/security/TOKEN_STORAGE_SECURITY_SPEC.md`
- `/01-EXTERNAL-API/security/SECURE_KEY_MANAGEMENT_SPEC.md`

### SignalR Connection
- `/01-EXTERNAL-API/signalr/SIGNALR_RECONNECTION_SPEC.md`
- `/01-EXTERNAL-API/signalr/EXPONENTIAL_BACKOFF_SPEC.md`
- `/01-EXTERNAL-API/signalr/CONNECTION_HEALTH_MONITORING_SPEC.md`
- `/01-EXTERNAL-API/signalr/STATE_RECONCILIATION_SPEC.md`

### Error Handling
- `/01-EXTERNAL-API/error-handling/ERROR_CODE_MAPPING_SPEC.md`
- `/01-EXTERNAL-API/error-handling/RETRY_STRATEGY_SPEC.md`
- `/01-EXTERNAL-API/error-handling/RATE_LIMITING_SPEC.md`
- `/01-EXTERNAL-API/error-handling/CIRCUIT_BREAKER_SPEC.md`

### Order Management
- `/01-EXTERNAL-API/order-management/ORDER_VERIFICATION_IDEMPOTENCY_SPEC.md`
- `/01-EXTERNAL-API/order-management/PARTIAL_FILL_TRACKING_SPEC.md`

### Database
- `/07-DATA-MODELS/schema-v2/DATABASE_SCHEMA_V2_SPEC.md`
- `/07-DATA-MODELS/schema-v2/MIGRATION_V1_TO_V2_SPEC.md`

### Configuration
- `/08-CONFIGURATION/CONFIGURATION_MASTER_SPEC.md`
- `/08-CONFIGURATION/RISK_CONFIG_YAML_SPEC.md`

---

## 📝 Summary

**Total Issues Addressed:** 41
- 8 CRITICAL (authentication, SignalR, error handling, orders)
- 6 HIGH (security, health monitoring, partial fills)
- 5 MEDIUM (edge cases, scenarios)
- 22 LOW (enhancements, documentation)

**Implementation Time:** 7-10 days (Phase 0)

**Dependencies:** Phase 0 must complete before risk rules

**Success Metrics:**
- Zero token expiration failures
- Zero duplicate orders
- Zero data loss during reconnections
- Zero rate limit violations
- 90%+ test coverage
- All chaos tests passing

**Critical Path:**
Token Manager → SignalR Manager → State Reconciliation → Order Management → Risk Rules

---

**Document Status:** DRAFT - Ready for review and implementation

**Next Steps:**
1. Review this overview with team
2. Create detailed specifications for each component
3. Begin Phase 0 implementation
4. Track progress with acceptance criteria
