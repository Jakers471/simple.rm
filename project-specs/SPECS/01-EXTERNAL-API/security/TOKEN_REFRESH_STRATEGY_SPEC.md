# Token Refresh Strategy Specification

**doc_id:** SEC-001
**version:** 1.0
**status:** DRAFT
**priority:** CRITICAL
**addresses:** GAP-API-001, GAP-API-SCENARIO-005 from ERRORS_AND_WARNINGS_CONSOLIDATED.md

## Overview

This specification defines the strategy for proactively refreshing authentication tokens to prevent service disruption. The TradeStation API tokens expire after 24 hours, and this specification addresses when to refresh, how to handle refresh failures, concurrent request handling during refresh, and fallback mechanisms.

## Problem Statement

**From GAP-API-001:**
- Tokens expire in 24 hours
- No guidance on when to refresh (proactive vs reactive)
- No handling for refresh failures
- No strategy for validate endpoint unavailability
- No concurrent request handling during refresh
- Token expiration during long operations (historical data retrieval, SignalR connections)

## Requirements

### Functional Requirements

**FR-1: Proactive Token Refresh**
- System MUST attempt token refresh 2 hours (7200 seconds) before expiry
- System MUST track token issue time and expiration time
- System MUST calculate refresh trigger time: `expiry_time - 7200 seconds`

**FR-2: Token Lifecycle State Machine**
- System MUST maintain token state: `VALID`, `REFRESHING`, `EXPIRED`, `ERROR`
- System MUST prevent concurrent refresh attempts
- System MUST queue requests during token refresh

**FR-3: Refresh Failure Handling**
- System MUST retry refresh with exponential backoff: [30s, 60s, 120s, 300s]
- System MUST fall back to full re-authentication after 4 failed refresh attempts
- System MUST notify monitoring system of refresh failures

**FR-4: Concurrent Request Handling**
- System MUST queue API requests when token state is `REFRESHING`
- System MUST replay queued requests after successful refresh
- System MUST fail queued requests if refresh fails permanently

**FR-5: Long Operation Token Management**
- System MUST check token expiry before operations exceeding 1 hour
- System MUST refresh token proactively for long operations
- System MUST handle mid-operation token expiry with request replay

**FR-6: Validate Endpoint Fallback**
- System MUST attempt full re-authentication if `/validate` endpoint fails
- System MUST NOT wait for token expiry if validation consistently fails

### Non-Functional Requirements

**NFR-1: Performance**
- Token refresh MUST complete within 5 seconds (P95)
- Request queue depth MUST NOT exceed 100 requests
- Queue processing MUST drain within 10 seconds after successful refresh

**NFR-2: Reliability**
- Token refresh success rate MUST be > 99.5%
- Zero token expiration incidents during normal operation

**NFR-3: Security**
- Tokens MUST be stored encrypted (see TOKEN_STORAGE_SECURITY_SPEC.md)
- Token refresh MUST use secure HTTPS connections
- Old tokens MUST be invalidated immediately after refresh

**NFR-4: Observability**
- System MUST log all token state transitions
- System MUST expose token refresh metrics (success/failure rate, duration)
- System MUST alert on repeated refresh failures

## Architecture

### Component Diagram (Text-Based)

```
┌─────────────────────────────────────────────────────────────┐
│                     TokenManager                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Token State Machine                                 │   │
│  │  - current_state: TokenState                         │   │
│  │  - token: str (encrypted)                            │   │
│  │  - issued_at: datetime                               │   │
│  │  - expires_at: datetime                              │   │
│  │  - refresh_trigger_time: datetime                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Request Queue                                       │   │
│  │  - pending_requests: Queue[APIRequest]               │   │
│  │  - max_queue_depth: int = 100                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Refresh Orchestrator                                │   │
│  │  - retry_policy: ExponentialBackoff                  │   │
│  │  - refresh_lock: asyncio.Lock                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ AuthService  │ │ APIClient    │ │ Monitoring   │
  │ - refresh()  │ │ - request()  │ │ - log()      │
  │ - validate() │ │ - queue()    │ │ - alert()    │
  └──────────────┘ └──────────────┘ └──────────────┘
```

### Token State Machine

```
                    ┌──────────────┐
                    │   INITIAL    │
                    └──────┬───────┘
                           │ authenticate()
                           ▼
                    ┌──────────────┐
          ┌─────────│    VALID     │◄────────┐
          │         └──────┬───────┘         │
          │                │                 │
          │   2hrs before  │ expiry          │ refresh
          │   expiry       │                 │ success
          │                ▼                 │
          │         ┌──────────────┐         │
          │         │  REFRESHING  │─────────┘
          │         └──────┬───────┘
          │                │
          │   refresh      │ retry limit
          │   failed       │ exceeded
          │                ▼
          │         ┌──────────────┐
          └────────►│    ERROR     │
                    └──────┬───────┘
                           │ re-auth attempt
                           ▼
                    ┌──────────────┐
                    │   EXPIRED    │
                    └──────────────┘
```

### Sequence Diagram: Proactive Token Refresh

```
APIClient    TokenManager    AuthService    TradeStationAPI    RequestQueue
    │             │               │                │                │
    │─request()──►│               │                │                │
    │             │               │                │                │
    │             ├─check_expiry()│                │                │
    │             │               │                │                │
    │             │  [< 2hrs to expiry]            │                │
    │             │               │                │                │
    │             ├─set_state(REFRESHING)          │                │
    │             │               │                │                │
    │             ├─queue_request()────────────────┼───────────────►│
    │             │               │                │                │
    │             ├──validate()──►│                │                │
    │             │               │──POST /validate►                │
    │             │               │◄────200 OK─────│                │
    │             │               │                │                │
    │             │  [token still valid]           │                │
    │             │               │                │                │
    │             ├─set_state(VALID)               │                │
    │             │               │                │                │
    │             ├─drain_queue()◄────────────────┼────────────────│
    │             │               │                │                │
    │◄─response───┤               │                │                │
```

### Sequence Diagram: Refresh Failure with Retry

```
TokenManager    AuthService    TradeStationAPI    RetryPolicy
    │                │                │                │
    ├──validate()───►│                │                │
    │                │──POST /validate►                │
    │                │◄────500 Error──│                │
    │                │                │                │
    ├──on_failure()──────────────────┼───────────────►│
    │                │                │                │
    │◄─retry_delay(30s)───────────────┼────────────────┤
    │                │                │                │
    [wait 30 seconds]                 │                │
    │                │                │                │
    ├──validate()───►│                │                │
    │                │──POST /validate►                │
    │                │◄────500 Error──│                │
    │                │                │                │
    ├──on_failure()──────────────────┼───────────────►│
    │                │                │                │
    │◄─retry_delay(60s)───────────────┼────────────────┤
    │                │                │                │
    [wait 60 seconds]                 │                │
    │                │                │                │
    ├──validate()───►│                │                │
    │                │──POST /validate►                │
    │                │◄────200 OK─────│                │
    │                │                │                │
    ├──set_state(VALID)               │                │
```

## State Machines / Workflows

### Token State Transitions

| Current State | Event | Next State | Action |
|---------------|-------|------------|--------|
| INITIAL | authenticate_success | VALID | Store token, set expiry timer |
| INITIAL | authenticate_failure | ERROR | Log error, retry authentication |
| VALID | refresh_trigger_reached | REFRESHING | Lock token, queue requests |
| VALID | token_expired | EXPIRED | Fail pending requests, re-auth |
| REFRESHING | refresh_success | VALID | Drain queue, resume operations |
| REFRESHING | refresh_failure (retries left) | REFRESHING | Wait backoff, retry |
| REFRESHING | refresh_failure (no retries) | ERROR | Fail queued requests |
| ERROR | re_auth_success | VALID | Resume operations |
| ERROR | re_auth_failure | EXPIRED | System halt, admin intervention |
| EXPIRED | re_auth_success | VALID | Resume operations |

### Request Handling During Refresh

```
┌─────────────────────────────────────────────┐
│  Incoming API Request                       │
└─────────────┬───────────────────────────────┘
              │
              ▼
       ┌──────────────┐
       │ Check Token  │
       │    State     │
       └──────┬───────┘
              │
       ┌──────┴──────┐
       │             │
   VALID         REFRESHING
       │             │
       ▼             ▼
┌──────────────┐ ┌──────────────┐
│ Execute      │ │ Queue        │
│ Request      │ │ Request      │
│ Immediately  │ │              │
└──────────────┘ └──────┬───────┘
                        │
                        ▼
              ┌──────────────────┐
              │ Wait for Refresh │
              │   to Complete    │
              └──────┬───────────┘
                     │
              ┌──────┴──────┐
              │             │
         SUCCESS         FAILURE
              │             │
              ▼             ▼
       ┌──────────────┐ ┌──────────────┐
       │ Replay with  │ │ Return Error │
       │  New Token   │ │  to Caller   │
       └──────────────┘ └──────────────┘
```

## Data Structures

### TokenInfo Structure

```yaml
TokenInfo:
  token:
    type: string
    encrypted: true
    description: "JWT access token (encrypted at rest)"

  issued_at:
    type: datetime (ISO 8601)
    example: "2025-10-22T10:30:00Z"
    description: "Token issue timestamp"

  expires_at:
    type: datetime (ISO 8601)
    example: "2025-10-23T10:30:00Z"
    description: "Token expiration timestamp (24 hours from issue)"

  refresh_trigger_time:
    type: datetime (ISO 8601)
    example: "2025-10-23T08:30:00Z"
    description: "Time to trigger proactive refresh (2 hours before expiry)"

  state:
    type: enum
    values: [VALID, REFRESHING, EXPIRED, ERROR]
    description: "Current token lifecycle state"

  refresh_attempts:
    type: integer
    min: 0
    max: 4
    description: "Number of refresh attempts since last success"
```

### APIRequest Structure (for queuing)

```yaml
APIRequest:
  request_id:
    type: string (UUID)
    example: "550e8400-e29b-41d4-a716-446655440000"
    description: "Unique request identifier"

  timestamp:
    type: datetime (ISO 8601)
    description: "Time request was queued"

  endpoint:
    type: string
    example: "/api/Order/placeOrder"
    description: "API endpoint to call"

  method:
    type: enum
    values: [GET, POST, PUT, DELETE]
    description: "HTTP method"

  payload:
    type: object
    description: "Request body (for POST/PUT)"

  headers:
    type: object
    description: "Additional headers"

  timeout_ms:
    type: integer
    default: 30000
    description: "Request timeout in milliseconds"

  retry_count:
    type: integer
    default: 0
    description: "Number of retry attempts"
```

### RefreshResult Structure

```yaml
RefreshResult:
  success:
    type: boolean
    description: "Whether refresh succeeded"

  new_token:
    type: string (optional)
    description: "New token if successful"

  new_expiry:
    type: datetime (optional)
    description: "New expiration time if successful"

  error_code:
    type: string (optional)
    values: [NETWORK_ERROR, AUTH_FAILED, RATE_LIMITED, UNKNOWN]
    description: "Error code if failed"

  retry_after_seconds:
    type: integer (optional)
    description: "Suggested retry delay (exponential backoff)"
```

## Configuration

### YAML Configuration Example

```yaml
# config/auth_config.yaml

authentication:
  token_refresh:
    # Refresh token 2 hours (7200 seconds) before expiry
    proactive_refresh_buffer_seconds: 7200

    # Exponential backoff retry policy
    retry_policy:
      max_attempts: 4
      backoff_delays_seconds: [30, 60, 120, 300]  # 30s, 1m, 2m, 5m
      backoff_multiplier: 2.0

    # Request queue configuration
    request_queue:
      max_depth: 100
      queue_timeout_seconds: 60
      drain_timeout_seconds: 10

    # Token validation
    validation:
      endpoint: "/validate"
      timeout_seconds: 5
      validate_on_startup: true

    # Monitoring and alerts
    monitoring:
      log_all_state_transitions: true
      alert_on_refresh_failure: true
      alert_threshold_failures: 2  # Alert after 2 consecutive failures

  # Token storage (see TOKEN_STORAGE_SECURITY_SPEC.md)
  token_storage:
    encryption_required: true
    storage_backend: "encrypted_file"  # or "memory_only"

  # Re-authentication fallback
  re_authentication:
    api_key_env_var: "TRADESTATION_API_KEY"
    auto_retry_on_validation_failure: true
    max_auth_attempts: 3
```

### Environment Variables

```bash
# .env (NEVER commit this file)

# API credentials
TRADESTATION_API_KEY=your_api_key_here

# Optional: Override default refresh timing
TOKEN_REFRESH_BUFFER_SECONDS=7200

# Optional: Override retry policy
TOKEN_REFRESH_MAX_RETRIES=4

# Optional: Enable debug logging
TOKEN_MANAGER_DEBUG=false
```

## Error Handling

### Error Scenarios and Responses

**E-001: Refresh Fails During First Attempt**
```
Scenario: Token refresh returns 500 error
Response:
  1. Log error with details
  2. Set state to REFRESHING (keep trying)
  3. Wait 30 seconds (first backoff)
  4. Retry refresh
  5. Queue continues to hold requests
```

**E-002: Refresh Fails After All Retries**
```
Scenario: 4 consecutive refresh failures
Response:
  1. Set state to ERROR
  2. Attempt full re-authentication
  3. If re-auth succeeds:
     - Set state to VALID
     - Drain queue with new token
  4. If re-auth fails:
     - Set state to EXPIRED
     - Fail all queued requests with error
     - Trigger critical alert
```

**E-003: Token Expires During Long Operation**
```
Scenario: Historical data retrieval takes 3 hours, token expires at 2 hours
Response:
  1. Before starting operation, check token TTL
  2. If TTL < operation_estimate, refresh proactively
  3. If refresh fails, abort operation
  4. Return error: "TOKEN_EXPIRED_DURING_OPERATION"
```

**E-004: Request Queue Overflow**
```
Scenario: More than 100 requests queued during refresh
Response:
  1. Reject new requests with error: "REQUEST_QUEUE_FULL"
  2. Log warning with queue depth
  3. Prioritize completing refresh
  4. Return HTTP 503 Service Unavailable to clients
```

**E-005: Validate Endpoint Unavailable**
```
Scenario: /validate endpoint returns 503 or times out
Response:
  1. Skip validation step
  2. Attempt full re-authentication immediately
  3. Log incident for monitoring
  4. Do NOT wait for token expiry
```

**E-006: Concurrent Refresh Attempts**
```
Scenario: Multiple threads try to refresh simultaneously
Response:
  1. First thread acquires refresh_lock
  2. Other threads wait on lock
  3. After refresh completes, waiting threads:
     - Check if state is now VALID
     - If VALID, skip refresh and proceed
     - If still ERROR, attempt own refresh
```

### Error Codes

| Error Code | HTTP Status | Description | Recovery Action |
|------------|-------------|-------------|-----------------|
| TOKEN_EXPIRED | 401 | Token has expired | Trigger refresh or re-auth |
| REFRESH_IN_PROGRESS | 503 | Refresh already in progress | Queue request, wait |
| REFRESH_FAILED | 500 | Refresh failed after retries | Re-authenticate |
| QUEUE_FULL | 503 | Request queue at capacity | Reject request, retry later |
| VALIDATION_FAILED | 401 | Token validation failed | Re-authenticate |
| RE_AUTH_FAILED | 401 | Re-authentication failed | Critical error, halt system |

## Security Considerations

**S-001: Token Exposure Prevention**
- Tokens MUST be encrypted at rest (AES-256)
- Tokens MUST NOT be logged in plaintext
- Tokens MUST NOT be exposed in error messages
- Tokens MUST be transmitted only over HTTPS

**S-002: Token Invalidation**
- Old tokens MUST be immediately invalidated after refresh
- System MUST NOT keep multiple valid tokens simultaneously
- Failed tokens MUST be cleared from memory

**S-003: Refresh Lock Security**
- Refresh lock MUST have timeout (5 seconds) to prevent deadlock
- Lock MUST be released in finally block
- Lock MUST be process-safe (asyncio.Lock or threading.Lock)

**S-004: Request Queue Security**
- Queued requests MUST NOT contain sensitive data in logs
- Queue MUST have maximum depth to prevent memory exhaustion
- Queue MUST be cleared on system shutdown

**S-005: Monitoring and Alerting**
- Log all token state transitions (sanitize token value)
- Alert on repeated refresh failures (>= 2 consecutive)
- Monitor queue depth and alert on overflow
- Track refresh latency and alert on P95 > 5 seconds

## Implementation Checklist

### Phase 1: Core Token Management
- [ ] Create TokenManager class with state machine
- [ ] Implement token storage encryption (see TOKEN_STORAGE_SECURITY_SPEC.md)
- [ ] Implement proactive refresh trigger (2 hours before expiry)
- [ ] Implement refresh lock to prevent concurrent refreshes
- [ ] Add token expiry calculation and tracking

### Phase 2: Refresh Logic
- [ ] Implement /validate endpoint call
- [ ] Implement exponential backoff retry policy
- [ ] Implement fallback to re-authentication after 4 failures
- [ ] Add refresh success/failure logging
- [ ] Add refresh metrics collection

### Phase 3: Request Queue
- [ ] Implement request queue with max depth 100
- [ ] Implement queue request during REFRESHING state
- [ ] Implement drain queue after successful refresh
- [ ] Implement fail queue on permanent refresh failure
- [ ] Add queue depth monitoring

### Phase 4: Long Operation Support
- [ ] Add pre-operation token TTL check
- [ ] Implement proactive refresh for long operations
- [ ] Add mid-operation token expiry detection
- [ ] Implement request replay mechanism
- [ ] Add operation checkpoint/resume logic

### Phase 5: Error Handling
- [ ] Implement all error scenarios (E-001 through E-006)
- [ ] Add error code mapping
- [ ] Add error logging with context
- [ ] Add error alerts for critical failures

### Phase 6: Monitoring and Observability
- [ ] Add token state transition logging
- [ ] Add refresh latency metrics
- [ ] Add refresh success/failure rate metrics
- [ ] Add queue depth metrics
- [ ] Configure alerts for refresh failures

### Phase 7: Testing
- [ ] Unit tests for TokenManager state machine
- [ ] Unit tests for refresh retry logic
- [ ] Integration tests for token refresh flow
- [ ] Integration tests for request queueing
- [ ] Load tests for queue capacity
- [ ] Chaos tests for network failures during refresh

## Validation Criteria

### Success Criteria

**SC-1: Proactive Refresh Works**
```
Test: Start system with token expiring in 2 hours
Expected: Token refresh triggers automatically 2 hours before expiry
Validation: Check logs for "Token refresh triggered" message
```

**SC-2: Request Queue Works**
```
Test: Trigger refresh, send 10 API requests during refresh
Expected: All 10 requests queued, then replayed after refresh
Validation: All 10 requests return successful responses
```

**SC-3: Retry Logic Works**
```
Test: Mock /validate to fail 2 times, then succeed
Expected: Refresh retries with backoff, then succeeds
Validation: Check logs for 2 failures, then 1 success, with correct delays
```

**SC-4: Re-Authentication Fallback Works**
```
Test: Mock /validate to fail 4 times
Expected: System falls back to re-authentication
Validation: Check logs for "Re-authentication triggered" after 4 failures
```

**SC-5: No Token Expiration During Operations**
```
Test: Run system for 48 hours with continuous API calls
Expected: Zero token expiration errors
Validation: Check logs for zero "TOKEN_EXPIRED" errors
```

### Performance Validation

**PV-1: Refresh Latency**
```
Metric: Token refresh duration (P95)
Target: < 5 seconds
Measurement: Monitor refresh_duration_seconds metric
```

**PV-2: Queue Drain Time**
```
Metric: Time to drain request queue after refresh
Target: < 10 seconds
Measurement: Monitor queue_drain_duration_seconds metric
```

**PV-3: Refresh Success Rate**
```
Metric: Refresh success rate over 7 days
Target: > 99.5%
Measurement: Monitor (refresh_success_count / refresh_total_count)
```

## References

### Related Specifications
- **TOKEN_STORAGE_SECURITY_SPEC.md**: Token encryption and secure storage
- **SIGNALR_JWT_FIX_SPEC.md**: Token usage in SignalR connections
- **LONG_OPERATION_TOKEN_HANDLING_SPEC.md**: Token management for extended operations

### Error Analysis References
- **ERRORS_AND_WARNINGS_CONSOLIDATED.md**:
  - Line 135-145: GAP-API-001 (Token Refresh Strategy Undefined)
  - Line 205-213: GAP-API-SCENARIO-005 (Token Expiration During Long Operation)

### TradeStation API Documentation
- Authentication endpoint: `/authorize`
- Token validation endpoint: `/validate`
- Token expiry: 24 hours from issue

### Security Standards
- Token encryption: AES-256
- Token storage: Encrypted at rest
- Token transmission: HTTPS only
- Token logging: Sanitize before logging

---

**Document Status:** DRAFT v1.0
**Last Updated:** 2025-10-22
**Next Review:** After implementation phase 1 completion
**Approval Required:** Security Team, Architecture Team
