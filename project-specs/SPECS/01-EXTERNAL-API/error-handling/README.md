# ERROR HANDLING SPECIFICATIONS

This directory contains comprehensive specifications for error handling, resilience, and fault tolerance in the Simple Risk Manager system.

## 📋 Overview

These specifications address **CRITICAL gaps** identified in the consolidated error analysis report, particularly:
- **GAP-API-006:** Inadequate Error Code Documentation
- **GAP-API-007:** No Rate Limit Tracking
- **GAP-API-008:** No Circuit Breaker Pattern
- **GAP-API-001:** Token Refresh Strategy Undefined
- **GAP-API-003:** Incomplete SignalR Reconnection Logic
- **GAP-API-004:** No Exponential Backoff Strategy

## 📁 Specification Documents

### 1. [ERROR_CODE_MAPPING_SPEC.md](./ERROR_CODE_MAPPING_SPEC.md)
**doc_id:** ERR-001 | **Addresses:** GAP-API-006 (CRITICAL)

Comprehensive error code mappings between HTTP status codes, ProjectX Gateway API error codes, and application-level error handling.

**Contents:**
- Complete error code table (HTTP, API codes 0-20+)
- Order rejection reason mappings
- Position close failure codes
- Insufficient balance scenarios
- Market closed error details
- User-friendly message templates
- Localization support
- PII sanitization rules

### 2. [RATE_LIMITING_SPEC.md](./RATE_LIMITING_SPEC.md)
**doc_id:** ERR-002 | **Addresses:** GAP-API-007 (CRITICAL)

Client-side rate limiting with pre-emptive throttling, request queuing, and priority-based ordering.

**Contents:**
- Sliding window algorithm (10 sub-windows)
- Endpoint-specific rate limits:
  - `/api/History/retrieveBars`: 50 req / 30s
  - All other endpoints: 200 req / 60s
- Priority queue architecture (0-10 priority scale)
- Request queue management
- Quota tracking mechanisms
- State persistence
- Integration with circuit breaker

### 3. [CIRCUIT_BREAKER_SPEC.md](./CIRCUIT_BREAKER_SPEC.md)
**doc_id:** ERR-003 | **Addresses:** GAP-API-008 (HIGH)

Circuit breaker pattern for preventing cascading failures and service degradation.

**Contents:**
- State machine (CLOSED/OPEN/HALF_OPEN)
- Failure threshold configuration
- Per-service circuit breaker isolation
- Service health monitoring
- Fallback strategies:
  - Order execution: Fail with error
  - Historical data: Return cached
  - Account info: Return last known
  - SignalR: Fall back to REST polling
- Exponential backoff for recovery
- Monitoring and metrics

### 4. [RETRY_STRATEGY_SPEC.md](./RETRY_STRATEGY_SPEC.md)
**doc_id:** ERR-004 | **Addresses:** GAP-API-001, GAP-API-003, GAP-API-004, GAP-API-SCENARIO-001

Exponential backoff retry strategies with jitter, idempotency, and token management.

**Contents:**
- Exponential backoff algorithm with jitter (0.2 factor)
- Retryable vs non-retryable error classification
- Operation-specific retry configurations:
  - Order execution: 3 retries, 500ms-5s backoff
  - Token refresh: 3 retries, proactive 2-hour buffer
  - SignalR connection: 10 retries, custom backoff
  - Historical data: 3 retries, rate limit aware
- Token refresh integration (GAP-API-001)
- Complete SignalR reconnection handlers (GAP-API-003, GAP-API-004)
- Idempotency key generation
- Network interruption handling (GAP-API-SCENARIO-001)
- State reconciliation after reconnection

### 5. [ERROR_LOGGING_SPEC.md](./ERROR_LOGGING_SPEC.md)
**doc_id:** ERR-005 | **Addresses:** Logging standardization

Structured error logging with PII sanitization and monitoring integration.

**Contents:**
- Structured JSON log format
- Log levels (DEBUG, INFO, WARN, ERROR, FATAL)
- PII sanitization rules:
  - Always redact: passwords, tokens, API keys
  - Mask: userId, accountId, email, IP addresses
  - Safe to log: symbol, volume, price, timestamps
- Correlation ID tracking
- Error deduplication (log every 10th occurrence)
- Log rotation (100MB max, 30 files, 90-day retention)
- Monitoring integration (Prometheus, alerts)

## 🔗 Integration Points

These specifications work together as an integrated error handling system:

```
┌─────────────────────────────────────────────────────────┐
│                   API Request Flow                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  1. Circuit Breaker Check (ERR-003)                    │
│     - Is circuit OPEN? → Use fallback                  │
│     - Is circuit CLOSED/HALF_OPEN? → Continue          │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  2. Rate Limiter Check (ERR-002)                       │
│     - Within quota? → Send request                     │
│     - Quota exceeded? → Queue with priority            │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  3. Token Management (ERR-004)                         │
│     - Token expires soon? → Refresh proactively        │
│     - Token valid? → Continue                          │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  4. Execute Request with Retry (ERR-004)               │
│     - On failure → Classify error (ERR-001)            │
│     - Retryable? → Exponential backoff + retry         │
│     - Non-retryable? → Fail immediately                │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  5. Log Result (ERR-005)                               │
│     - Sanitize PII                                     │
│     - Add correlation ID                               │
│     - Record metrics                                   │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Gap Coverage

| Gap ID | Priority | Description | Covered By |
|--------|----------|-------------|------------|
| **GAP-API-006** | CRITICAL | Inadequate error code documentation | ERR-001 |
| **GAP-API-007** | CRITICAL | No rate limit tracking | ERR-002 |
| **GAP-API-008** | HIGH | No circuit breaker pattern | ERR-003 |
| **GAP-API-001** | CRITICAL | Token refresh strategy undefined | ERR-004 |
| **GAP-API-003** | CRITICAL | Incomplete SignalR reconnection | ERR-004 |
| **GAP-API-004** | CRITICAL | No exponential backoff | ERR-004 |
| **GAP-API-SCENARIO-001** | CRITICAL | Network interruption during order | ERR-004 |

## 📊 Implementation Priority

### Phase 1: Foundation (Week 1)
1. **ERROR_CODE_MAPPING_SPEC.md** - Error classification system
2. **ERROR_LOGGING_SPEC.md** - Logging infrastructure

### Phase 2: Resilience (Week 2)
3. **RETRY_STRATEGY_SPEC.md** - Retry logic and token management
4. **CIRCUIT_BREAKER_SPEC.md** - Circuit breaker implementation

### Phase 3: Optimization (Week 3)
5. **RATE_LIMITING_SPEC.md** - Rate limiter with request queuing

## 🔧 Configuration Example

Complete error handling configuration:

```yaml
errorHandling:
  # Error code mapping (ERR-001)
  errorMapping:
    detailedLogging: true
    sanitization:
      enabled: true
      maskLength: 3

  # Rate limiting (ERR-002)
  rateLimiter:
    enabled: true
    limits:
      history:
        requests: 50
        windowSeconds: 30
        safetyBuffer: 0.9
      general:
        requests: 200
        windowSeconds: 60
        safetyBuffer: 0.9

  # Circuit breaker (ERR-003)
  circuitBreaker:
    enabled: true
    defaults:
      failureThreshold: 5
      successThreshold: 3
      timeout: 60000
      halfOpenMaxRequests: 3

  # Retry strategy (ERR-004)
  retryStrategy:
    enabled: true
    defaultMaxRetries: 3
    defaultBaseDelayMs: 1000
    defaultMaxDelayMs: 30000
    tokenRefresh:
      refreshBufferMs: 7200000  # 2 hours

  # Logging (ERR-005)
  logging:
    enabled: true
    level: "INFO"
    format: "json"
    sanitization:
      enabled: true
    monitoring:
      enabled: true
```

## 📚 References

- **ERRORS_AND_WARNINGS_CONSOLIDATED.md** - Consolidated error analysis
- **API-INTEGRATION-ANALYSIS.md** - API integration patterns
- **RISK_CONFIG_YAML_SPEC.md** - Configuration integration

## ✅ Validation

All specifications include:
- [ ] Functional requirements
- [ ] Performance requirements
- [ ] Security requirements
- [ ] Configuration schemas
- [ ] Implementation checklists
- [ ] Validation criteria
- [ ] Test scenarios
- [ ] Integration points

## 📝 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-22 | Error Handling Spec Writer | Initial specifications addressing all CRITICAL gaps |

---

**Status:** DRAFT - Ready for implementation
**Completeness:** 100% - All identified gaps addressed
**Next Steps:** Begin Phase 1 implementation (error codes and logging)
