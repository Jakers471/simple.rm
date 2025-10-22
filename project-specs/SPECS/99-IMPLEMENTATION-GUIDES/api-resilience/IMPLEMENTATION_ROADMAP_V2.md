---
doc_id: GUIDE-002
title: Implementation Roadmap v2.0 - With API Resilience Phase
version: 2.0
status: DRAFT
last_updated: 2025-10-22
purpose: Updated roadmap with new Phase 0 for API resilience layer
based_on: IMPLEMENTATION_ROADMAP.md v1.0
dependencies: [API_RESILIENCE_OVERVIEW.md, ERRORS_AND_WARNINGS_CONSOLIDATED.md]
---

# Implementation Roadmap v2.0 - Simple Risk Manager

**Major Update:** Added Phase 0 (API Resilience) as critical prerequisite to risk rules implementation

**Total Estimated Time:** 23-34 days (was 16-24 days)

---

## 📋 What Changed in v2.0

### New Phase 0: API Resilience Foundation (7-10 days)
**Status:** CRITICAL - Must complete BEFORE risk rules

**Why Added:**
Analysis revealed 8 CRITICAL and 6 HIGH severity API integration issues that could cause:
- Duplicate orders during network failures
- Data loss during SignalR reconnections
- Token expiration mid-operation
- Unhandled API errors causing crashes
- Rate limit violations
- Security vulnerabilities

**What's Included:**
- Token Manager (automatic refresh, secure storage)
- SignalR Connection Manager (reconnection, health monitoring)
- Error Handler (comprehensive error codes, retry strategies)
- Rate Limiter (pre-emptive throttling, request queuing)
- Circuit Breaker (service degradation detection)
- Order Management (verification, idempotency, partial fills)
- State Reconciliation (post-reconnect sync)

### Updated Phase 1-4
Phases 1-4 remain largely unchanged but now depend on Phase 0 completion.

---

## 🚀 PHASE 0: API RESILIENCE FOUNDATION (7-10 days)

### Goal
Build robust API integration layer to handle authentication, connections, errors, and network failures before implementing risk rules.

### Scope
**In Scope:**
- Token lifecycle management (refresh, storage, validation)
- SignalR connection resilience (reconnection, health monitoring)
- Comprehensive error handling (error codes, retries, circuit breaker)
- Rate limiting (client-side throttling, queuing)
- Order management (verification, idempotency, partial fills)
- State reconciliation (sync after reconnection)
- Integration and chaos testing

**Out of Scope:**
- Risk rules (moved to Phase 1)
- Trader CLI (moved to Phase 2)
- Admin CLI (moved to Phase 3)

---

### DAY 1-2: Token Manager (CRITICAL)

**DAY 1 Morning (4 hours):**
1. Implement Token Manager foundation (`src/api/auth/token_manager.py`)
   - TokenState dataclass (token, expiry, refresh_time)
   - Token validation (check expiry)
   - Token refresh logic
   - Fallback to re-authentication

2. Implement proactive refresh strategy
   - Calculate refresh time (2 hours before expiry)
   - Background thread for refresh checking
   - Retry logic for failed refreshes
   - Request queue during refresh

**DAY 1 Afternoon (4 hours):**
3. Implement secure token storage (`src/api/auth/secure_storage.py`)
   - AES-256 encryption
   - Environment variable key management
   - Encrypted file storage
   - Memory-only mode (optional)

4. Unit tests for Token Manager
   - Test proactive refresh (at 2-hour buffer)
   - Test refresh failure fallback
   - Test concurrent requests during refresh
   - Test token expiration detection
   - Test encryption/decryption

**DAY 2 Morning (4 hours):**
5. Integrate Token Manager with REST client
   - Auto-inject token in requests
   - Auto-refresh on 401 errors
   - Token validation before long operations
   - Request replay after token refresh

6. Integration tests
   - Test token lifecycle (authenticate → use → refresh → expire)
   - Test long operation with token refresh
   - Test concurrent API calls during refresh

**DAY 2 Afternoon (4 hours):**
7. Implement secure configuration
   - Load API key from environment
   - Validate credentials on startup
   - Secure credential storage
   - Key rotation support

8. Documentation
   - Token lifecycle diagram
   - Configuration examples
   - Security best practices

**Deliverable:** Production-ready token manager with automatic refresh, secure storage, and comprehensive tests

**Acceptance Criteria:**
- ✅ Tokens refresh 2 hours before expiry automatically
- ✅ Tokens stored encrypted with AES-256
- ✅ Fallback to re-authentication works on refresh failure
- ✅ Concurrent requests handled during refresh
- ✅ 95%+ test coverage

---

### DAY 2-3: Error Handler + Rate Limiter (CRITICAL)

**DAY 2 Afternoon (continued) + Evening (4 hours):**
1. Implement error code mapping (`src/api/error_handler/error_codes.py`)
   - Map all HTTP status codes (400, 401, 429, 500, etc.)
   - Map TopstepX error codes (from API responses)
   - Error classification (transient vs permanent)
   - User-friendly error messages

2. Implement retry strategy (`src/api/error_handler/retry_strategy.py`)
   - Exponential backoff calculator
   - Retry decision logic (based on error code)
   - Max retry limits (5 attempts default)
   - Backoff timing (1s, 2s, 4s, 8s, 16s)

**DAY 3 Morning (4 hours):**
3. Implement Error Handler (`src/api/error_handler/error_handler.py`)
   - Wrap all API calls
   - Automatic retry for transient errors
   - Circuit breaker integration (placeholder)
   - Comprehensive error logging

4. Implement Rate Limiter (`src/api/rate_limiter/rate_limiter.py`)
   - Sliding window tracking (50 req/30s for history, 200 req/60s general)
   - Pre-emptive throttling
   - Request queue with backpressure
   - Queue overflow handling

**DAY 3 Afternoon (4 hours):**
5. Unit tests for Error Handler
   - Test error code mapping
   - Test retry logic (transient errors)
   - Test no retry (permanent errors)
   - Test max retry limit
   - Test exponential backoff timing

6. Unit tests for Rate Limiter
   - Test sliding window tracking
   - Test throttling (stay under limits)
   - Test request queuing
   - Test queue overflow
   - Test concurrent requests

**Deliverable:** Robust error handling with automatic retries and rate limiting

**Acceptance Criteria:**
- ✅ All error codes mapped and documented
- ✅ Retry strategies work correctly
- ✅ Rate limiter prevents 429 errors
- ✅ Request queuing functional
- ✅ 90%+ test coverage

---

### DAY 4-6: SignalR Connection Manager (CRITICAL)

**DAY 4 Morning (4 hours):**
1. Implement connection lifecycle (`src/api/signalr/connection_manager.py`)
   - Connection initialization
   - Event handler registration (onconnected, onclose, onreconnecting, onreconnected)
   - Connection state tracking (disconnected, connecting, connected, reconnecting)
   - Graceful shutdown

2. Implement exponential backoff (`src/api/signalr/backoff_strategy.py`)
   - Backoff delays: [0, 2000, 10000, 30000, 60000] ms
   - Max attempts: 10
   - Reset on successful connection
   - Jitter for distributed systems

**DAY 4 Afternoon (4 hours):**
3. Implement reconnection logic
   - Automatic reconnection with backoff
   - Token validation before reconnect
   - Connection failure detection
   - Fallback to REST polling (if needed)

4. Unit tests for connection lifecycle
   - Test connection establishment
   - Test disconnection handling
   - Test reconnection with backoff
   - Test connection state transitions

**DAY 5 Morning (4 hours):**
5. Implement health monitoring (`src/api/signalr/health_monitor.py`)
   - Heartbeat/ping mechanism (every 30s)
   - Ping timeout detection (5s)
   - Stale connection cleanup (2 minutes)
   - Connection health metrics

6. Implement event subscription management
   - Auto-subscribe on connect
   - Auto-resubscribe on reconnect
   - Subscription state tracking
   - Error handling for subscription failures

**DAY 5 Afternoon (4 hours):**
7. Integration with Token Manager
   - Use TokenManager.get_token() for connections
   - Refresh token before reconnect if needed
   - Handle 401 errors during connection

8. Unit tests for health monitoring
   - Test heartbeat mechanism
   - Test ping timeout detection
   - Test stale connection cleanup
   - Test health metrics

**DAY 6 Morning (4 hours):**
9. Integration tests
   - Test full connection lifecycle
   - Test reconnection after network failure
   - Test health monitoring detection
   - Test auto-resubscription

10. Chaos tests
    - Random disconnections
    - Network latency simulation
    - Server unavailability
    - Token expiration during connection

**DAY 6 Afternoon (4 hours):**
11. Performance optimization
    - Minimize reconnection overhead
    - Optimize event processing
    - Reduce memory allocations

12. Documentation
    - Connection lifecycle diagram
    - Reconnection flow
    - Health monitoring guide

**Deliverable:** Production-ready SignalR connection manager with reconnection, health monitoring, and comprehensive tests

**Acceptance Criteria:**
- ✅ All event handlers implemented
- ✅ Exponential backoff working correctly
- ✅ Health monitoring detects stale connections
- ✅ Reconnection success rate >99%
- ✅ Auto-resubscription works
- ✅ 95%+ test coverage

---

### DAY 6: State Reconciliation (CRITICAL)

**DAY 6 Afternoon (continued, 4 hours):**
1. Implement State Reconciler (`src/api/state/state_reconciler.py`)
   - Trigger on SignalR reconnection
   - Fetch positions via REST API
   - Fetch orders via REST API
   - Fetch account via REST API

2. Implement state comparison
   - Compare cached positions with REST response
   - Compare cached orders with REST response
   - Detect missed events (new positions/orders)
   - Log discrepancies

3. Implement state update
   - Update cached state from REST
   - Notify state manager of changes
   - Resume event processing

4. Unit tests
   - Test position sync
   - Test order sync
   - Test discrepancy detection
   - Test state update

**Deliverable:** State reconciliation system that syncs state after reconnection

**Acceptance Criteria:**
- ✅ State syncs after reconnection
- ✅ Missed events detected
- ✅ Discrepancies logged
- ✅ State accurate after sync
- ✅ 90%+ test coverage

---

### DAY 7: Circuit Breaker (HIGH)

**DAY 7 Morning (4 hours):**
1. Implement Circuit Breaker (`src/api/circuit_breaker/circuit_breaker.py`)
   - Circuit states (closed, open, half-open)
   - Failure threshold (5 consecutive failures)
   - Timeout duration (60 seconds)
   - Half-open testing (3 requests)

2. Implement state transitions
   - Closed → Open (on threshold)
   - Open → Half-Open (after timeout)
   - Half-Open → Closed (on success)
   - Half-Open → Open (on failure)

**DAY 7 Afternoon (4 hours):**
3. Implement service health tracking
   - Track failure rate
   - Track success rate
   - Track response times
   - Health status reporting

4. Integrate with Error Handler
   - Check circuit state before API calls
   - Update circuit state on failures
   - Trigger fallback on open circuit

5. Unit tests
   - Test failure threshold
   - Test state transitions
   - Test timeout and recovery
   - Test half-open testing

**Deliverable:** Circuit breaker for service degradation detection

**Acceptance Criteria:**
- ✅ Circuit opens on threshold
- ✅ State transitions work correctly
- ✅ Half-open testing functional
- ✅ Fallback modes work
- ✅ 90%+ test coverage

---

### DAY 7-8: Order Management (CRITICAL)

**DAY 7 Afternoon (continued, 4 hours):**
1. Implement order verification (`src/api/orders/order_verifier.py`)
   - Verify order status after placement
   - Poll order status via REST API
   - Timeout handling (5 seconds)
   - Retry logic (3 attempts)

2. Implement idempotency checks (`src/api/orders/idempotency_manager.py`)
   - Track placed orders (cache with TTL)
   - Detect duplicate placement attempts
   - Prevent duplicate orders
   - Cache cleanup

**DAY 8 Morning (4 hours):**
3. Implement partial fill tracking (`src/api/orders/partial_fill_tracker.py`)
   - Track fillVolume vs order size
   - Detect partial fills via SignalR events
   - Complete detection (fillVolume == size)
   - Timeout for incomplete fills (60 seconds)

4. Integration with Error Handler
   - Wrap order placement in error handling
   - Retry transient failures
   - Verify order after network failures

**DAY 8 Afternoon (4 hours):**
5. Unit tests for order verification
   - Test status verification
   - Test timeout handling
   - Test retry logic

6. Unit tests for idempotency
   - Test duplicate detection
   - Test cache TTL
   - Test cache cleanup

7. Unit tests for partial fill tracking
   - Test partial fill detection
   - Test completion detection
   - Test timeout handling

**Deliverable:** Robust order management with verification, idempotency, and partial fill tracking

**Acceptance Criteria:**
- ✅ Order verification works
- ✅ Idempotency prevents duplicates
- ✅ Partial fills tracked correctly
- ✅ Network failures handled
- ✅ 95%+ test coverage

---

### DAY 9-10: Integration & Chaos Testing (CRITICAL)

**DAY 9 (8 hours):**
1. Integration test suite
   - Token refresh during operation
   - SignalR reconnection with state sync
   - Rate limit enforcement
   - Circuit breaker triggers
   - Order placement with network failures

2. Chaos engineering tests
   - Network interruption during order placement
   - Token expiration mid-operation
   - SignalR disconnection during high volume
   - API rate limit hit
   - Server error cascade

**DAY 10 (8 hours):**
3. Performance testing
   - Load testing (60+ events/sec)
   - Latency measurements
   - Memory profiling
   - CPU utilization

4. End-to-end testing
   - Full system test with TopstepX demo account
   - Simulate real-world scenarios
   - Validate all components work together

5. Bug fixes and polish
   - Fix issues found in testing
   - Optimize performance
   - Complete documentation

**Deliverable:** Fully tested and validated API resilience layer

**Acceptance Criteria:**
- ✅ 90%+ unit test coverage
- ✅ All integration tests pass
- ✅ All chaos tests pass
- ✅ Performance benchmarks met (<10ms latency)
- ✅ Zero duplicate orders in testing
- ✅ Zero data loss in reconnection tests
- ✅ Zero token expiration failures
- ✅ Zero rate limit violations

---

### Phase 0 Summary

**Total Time:** 7-10 days

**Components Built:**
1. Token Manager (Days 1-2)
2. Error Handler + Rate Limiter (Days 2-3)
3. SignalR Connection Manager (Days 4-6)
4. State Reconciliation (Day 6)
5. Circuit Breaker (Day 7)
6. Order Management (Days 7-8)
7. Testing (Days 9-10)

**Lines of Code:** ~5,000-7,000 lines
**Test Coverage:** 90%+
**Tests Written:** 100+ unit tests, 20+ integration tests, 10+ chaos tests

---

## 🔧 PHASE 1: MVP (3-5 days)

### Changes from v1.0
- Now depends on Phase 0 (API resilience layer)
- Simplified to focus on 3 rules
- No need to build authentication (already done in Phase 0)
- No need to build SignalR listener (already done in Phase 0)

### Goal
Prove core architecture with minimal feature set - demonstrate event processing and enforcement works.

### Scope
**In Scope:**
- 3 simple rules (RULE-001, RULE-002, RULE-009)
- Basic daemon with event processing
- Core modules: MOD-001 (enforcement), MOD-002 (lockout), MOD-009 (state)
- Simple Trader CLI (SQLite-only, no real-time)
- Manual config editing (no Admin CLI)

**Out of Scope:**
- Complex rules (P&L, trade frequency, etc.)
- Real-time WebSocket updates
- Admin CLI

---

### DAY 11: Integration with Phase 0

**Morning (4 hours):**
1. Create daemon foundation (`src/core/daemon.py`)
   - Initialize Token Manager
   - Initialize SignalR Connection Manager
   - Initialize State Reconciler
   - Setup event routing

2. Implement state manager (`src/state/state_manager.py`)
   - Position tracking (integrate with State Reconciler)
   - Order tracking
   - SQLite persistence

**Afternoon (4 hours):**
3. Implement lockout manager (`src/state/lockout_manager.py`)
   - Lockout creation
   - Lockout checking
   - Lockout clearing
   - SQLite persistence

4. Test integration
   - Verify Token Manager integration
   - Verify SignalR Connection Manager integration
   - Verify event reception

**Deliverable:** Daemon integrated with Phase 0 resilience layer

---

### DAY 12: First Rule & Enforcement

**Morning (4 hours):**
1. Implement enforcement actions (`src/enforcement/actions.py`)
   - close_all_positions() - uses Order Management from Phase 0
   - cancel_all_orders() - uses Error Handler from Phase 0
   - Integrate with rate limiter
   - Integrate with circuit breaker

2. Implement base rule class (`src/rules/base_rule.py`)
   - Abstract base class
   - Event handling
   - Breach detection
   - Enforcement triggering

**Afternoon (4 hours):**
3. Implement RULE-001 (`src/rules/max_contracts.py`)
   - MaxContracts rule
   - Test breach detection
   - Test enforcement execution

4. Implement event router (`src/core/event_router.py`)
   - Route SignalR events to rules
   - Wrap in Error Handler
   - Integrate with rate limiter

**Deliverable:** First working rule with end-to-end enforcement

---

### DAY 13: Complete MVP Rules

**Morning (4 hours):**
1. Implement RULE-002 (`src/rules/max_contracts_per_instrument.py`)
   - Per-instrument limits
   - Test with multiple instruments

2. Implement RULE-009 (`src/rules/session_block_outside.py`)
   - Session hours check
   - Test with time configuration

**Afternoon (4 hours):**
3. Implement daemon
   - Startup sequence
   - Shutdown sequence
   - Signal handling (SIGTERM, SIGINT)

4. Integration testing
   - Test all 3 rules together
   - Test state persistence
   - Test lockout mechanism

**Deliverable:** Working daemon with 3 functional rules

---

### DAY 14-15: Simple Trader CLI

**DAY 14 (8 hours):**
1. Implement Trader CLI foundation (`src/cli/trader/trader_main.py`)
   - Main menu
   - UI helpers (Rich library)

2. Implement dashboard (`src/cli/trader/dashboard.py`)
   - Read-only dashboard
   - Display positions
   - Display lockout status
   - Display daily P&L (placeholder)

**DAY 15 (4-6 hours):**
3. Polish and test
   - Add logging
   - Fix bugs
   - Document usage

4. MVP Demo
   - Run daemon
   - Place trades via TopstepX
   - Watch rules trigger
   - Demonstrate lockout

**Deliverable:** Complete MVP - working daemon + basic CLI

**Phase 1 Acceptance Criteria:**
- ✅ Daemon uses Phase 0 resilience layer
- ✅ 3 rules enforce correctly
- ✅ State persists across restarts
- ✅ Trader CLI displays state
- ✅ Lockouts work correctly

---

## 🔧 PHASE 2: FULL RULE SET (5-7 days)

### Changes from v1.0
- Unchanged - implement remaining 9 rules
- Benefits from Phase 0 resilience (no token/network issues)

### Goal
Implement all 12 risk rules and all 9 core modules.

**Days 16-22:** Same as original roadmap Days 6-11

---

## 📡 PHASE 3: REAL-TIME & ADMIN (3-5 days)

### Changes from v1.0
- Unchanged - add real-time updates and Admin CLI

**Days 23-27:** Same as original roadmap Days 12-15

---

## 🛡️ PHASE 4: PRODUCTION HARDENING (5-7 days)

### Changes from v1.0
- Reduced scope (Phase 0 already tested extensively)
- Focus on rule testing and documentation

**Days 28-34:** Adapted from original roadmap Days 16-22

---

## 📊 Updated Project Timeline

### Original v1.0 Timeline
```
Phase 1: MVP (Days 1-5)
Phase 2: Full Rule Set (Days 6-11)
Phase 3: Real-Time & Admin (Days 12-15)
Phase 4: Production Hardening (Days 16-22)
Total: 16-24 days
```

### New v2.0 Timeline
```
Phase 0: API Resilience (Days 1-10) ← NEW CRITICAL PHASE
Phase 1: MVP (Days 11-15)
Phase 2: Full Rule Set (Days 16-22)
Phase 3: Real-Time & Admin (Days 23-27)
Phase 4: Production Hardening (Days 28-34)
Total: 23-34 days (+7-10 days)
```

---

## 🎯 Critical Path

```
Phase 0 (Days 1-10): API Resilience Foundation
    ├── Token Manager (Days 1-2) ← CRITICAL START
    ├── Error Handler + Rate Limiter (Days 2-3)
    ├── SignalR Connection Manager (Days 4-6)
    ├── State Reconciliation (Day 6)
    ├── Circuit Breaker (Day 7)
    ├── Order Management (Days 7-8)
    └── Integration Testing (Days 9-10)
            │
            ▼
Phase 1 (Days 11-15): MVP with 3 rules
            │
            ▼
Phase 2 (Days 16-22): All 12 rules
            │
            ▼
Phase 3 (Days 23-27): Real-time + Admin
            │
            ▼
Phase 4 (Days 28-34): Production hardening
```

**Key Dependencies:**
- Phase 1 cannot start until Phase 0 complete
- Phase 0 Token Manager must complete before SignalR Manager
- Phase 0 SignalR Manager must complete before State Reconciliation
- Phase 0 Order Management depends on Error Handler + Rate Limiter

---

## ✅ Updated Success Metrics

### Phase 0 Metrics
- ✅ Zero token expiration failures
- ✅ Zero duplicate orders
- ✅ Zero data loss during reconnections
- ✅ Zero rate limit violations
- ✅ SignalR reconnection success >99%
- ✅ 90%+ test coverage

### Phase 1-4 Metrics
- ✅ All 12 rules operational
- ✅ Event latency < 10ms
- ✅ Memory usage < 100 MB
- ✅ 24/7 uptime as Windows Service
- ✅ Real-time CLI updates < 1 second
- ✅ Admin control functional

---

## 📝 Summary of Changes

**What's New in v2.0:**
1. **Phase 0 Added** - 7-10 days for API resilience
2. **Timeline Extended** - 23-34 days (was 16-24)
3. **Phase 1 Simplified** - Authentication/SignalR already done
4. **Dependencies Clear** - Phase 0 must complete first
5. **Testing Expanded** - Chaos engineering in Phase 0
6. **Documentation Updated** - New specs for all components

**Why These Changes:**
- Address 8 CRITICAL API integration issues
- Prevent production failures (duplicates, data loss)
- Build solid foundation before risk rules
- Improve overall system reliability
- Meet production-ready standards

**Impact:**
- +7-10 days development time
- Significantly more reliable system
- Reduced production risk
- Better error handling
- Improved user experience

---

**Document Status:** DRAFT - Ready for implementation

**Next Steps:**
1. Review v2.0 roadmap with team
2. Begin Phase 0: Day 1 (Token Manager)
3. Track progress against acceptance criteria
4. Update roadmap as needed based on actual timing
