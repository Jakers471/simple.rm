# Token Rotation Specification

**doc_id:** SEC-005
**version:** 1.0
**status:** DRAFT
**priority:** MEDIUM
**addresses:** SEC-API-002 from ERRORS_AND_WARNINGS_CONSOLIDATED.md

## Overview

This specification defines token rotation strategy, frequency, and mechanisms to minimize the impact of compromised tokens. While the TradeStation API doesn't explicitly require rotation, implementing periodic rotation enhances security by limiting the window of exposure for any compromised token.

## Problem Statement

**From SEC-API-002:**
- No guidance on token rotation frequency
- No process for old token invalidation
- No revocation mechanism documented
- Stale tokens could be exploited if compromised
- No emergency lockdown procedures

## Requirements

### Functional Requirements

**FR-1: Rotation Frequency**
- System SHOULD rotate tokens every 12 hours (recommended)
- System MUST support configurable rotation intervals (1-24 hours)
- System MAY skip rotation if no activity in past 24 hours (idle optimization)
- System MUST rotate token immediately on suspected compromise

**FR-2: Token Invalidation**
- System MUST invalidate old token after successful rotation
- System MUST maintain old token for grace period (5 minutes)
- System MUST NOT use old token after grace period expires
- System MUST clear old token from memory and storage

**FR-3: Revocation Mechanism**
- System MUST support manual token revocation
- System MUST revoke token on logout (if logout endpoint available)
- System MUST revoke token on compromise detection
- System MUST prevent usage of revoked tokens

**FR-4: Rotation State Management**
- System MUST track rotation history
- System MUST record rotation timestamps
- System MUST track rotation success/failure
- System MUST maintain rotation audit trail

**FR-5: Graceful Rotation**
- System MUST NOT interrupt active operations during rotation
- System MUST queue new requests during rotation
- System MUST complete in-flight requests with old token
- System MUST transition to new token only after validation

### Non-Functional Requirements

**NFR-1: Performance**
- Token rotation MUST complete in < 5 seconds (P95)
- Rotation MUST NOT cause noticeable service degradation
- System MUST handle concurrent requests during rotation

**NFR-2: Security**
- Old tokens MUST be cleared from memory securely
- Rotation MUST use secure authentication
- Rotation events MUST be logged (with sanitized tokens)
- Revoked tokens MUST be stored in blacklist

**NFR-3: Reliability**
- Rotation failure MUST NOT invalidate current token
- System MUST fall back to current token on rotation failure
- System MUST retry rotation with exponential backoff
- System MUST alert on repeated rotation failures

**NFR-4: Observability**
- System MUST expose rotation metrics (success rate, duration)
- System MUST log all rotation events
- System MUST alert on rotation anomalies
- System MUST provide rotation health dashboard

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    TokenRotationManager                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Rotation Orchestrator                               │   │
│  │  - schedule_rotation() -> None                       │   │
│  │  - execute_rotation() -> RotationResult              │   │
│  │  - validate_new_token(token: str) -> bool            │   │
│  │  - invalidate_old_token(token: str) -> None          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Revocation Service                                  │   │
│  │  - revoke_token(token: str, reason: str) -> None     │   │
│  │  - is_revoked(token: str) -> bool                    │   │
│  │  - blacklist: Set[str]                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Rotation History                                    │   │
│  │  - record_rotation(event: RotationEvent) -> None     │   │
│  │  - get_history(limit: int) -> List[RotationEvent]   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ TokenManager │ │ AuthService  │ │ Scheduler    │
  │ (from        │ │ (refresh/    │ │ (cron jobs)  │
  │  TOKEN_      │ │  revoke)     │ │              │
  │  REFRESH_    │ │              │ │              │
  │  STRATEGY)   │ │              │ │              │
  └──────────────┘ └──────────────┘ └──────────────┘
```

### Token Rotation Flow

```
Scheduler    RotationManager    TokenManager    AuthService    API
    │              │                 │               │          │
    │─rotate()────►│                 │               │          │
    │              │                 │               │          │
    │              ├─check_conditions()              │          │
    │              │ [Rotation needed?]              │          │
    │              │                 │               │          │
    │              ├─queue_requests()│               │          │
    │              │ [Pause new ops] │               │          │
    │              │                 │               │          │
    │              ├─get_current_token()            │          │
    │              │◄────token───────┤               │          │
    │              │                 │               │          │
    │              ├─refresh_token()─┼──────────────►│          │
    │              │                 │               │──POST───►│
    │              │                 │               │◄─token───│
    │              │                 │◄──new_token───┤          │
    │              │                 │               │          │
    │              ├─validate_new_token()            │          │
    │              │                 │               │──POST───►│
    │              │                 │               │  /validate
    │              │                 │               │◄──200────│
    │              │                 │               │          │
    │              ├─store_new_token()──────────────►│          │
    │              │                 │               │          │
    │              │ [Grace period: 5 minutes]       │          │
    │              │ [Old token still valid]         │          │
    │              │                 │               │          │
    │              ├─drain_queue()───┤               │          │
    │              │ [Resume ops     │               │          │
    │              │  with new token]│               │          │
    │              │                 │               │          │
    │              ├─invalidate_old()┤               │          │
    │              │ [After grace    │               │          │
    │              │  period expires]│               │          │
    │              │                 │               │          │
    │◄─success─────┤                 │               │          │
```

### Emergency Revocation Flow

```
Admin/Alert    RevocationService    TokenManager    TokenBlacklist
    │                │                   │                │
    │─revoke()──────►│                   │                │
    │  "Compromised" │                   │                │
    │                │                   │                │
    │                ├─get_current()────►│                │
    │                │◄──token───────────┤                │
    │                │                   │                │
    │                ├─add_to_blacklist()┼───────────────►│
    │                │                   │                │
    │                ├─clear_token()────►│                │
    │                │ [Remove from      │                │
    │                │  storage]         │                │
    │                │                   │                │
    │                ├─trigger_refresh()►│                │
    │                │ [Get new token    │                │
    │                │  immediately]     │                │
    │                │                   │                │
    │                ├─notify_monitoring()                │
    │                │ [Alert security   │                │
    │                │  team]            │                │
    │                │                   │                │
    │◄─complete──────┤                   │                │
    │                │                   │                │
    │  [All subsequent requests use new token]            │
    │  [Old token rejected if used]       │                │
```

## State Machines / Workflows

### Rotation State Machine

```
                    ┌──────────────┐
          ┌────────►│    IDLE      │◄────────┐
          │         └──────┬───────┘         │
          │                │                 │
          │   rotation     │ schedule        │ success
          │   complete     │ triggered       │
          │                ▼                 │
          │         ┌──────────────┐         │
          │         │  SCHEDULED   │         │
          │         └──────┬───────┘         │
          │                │                 │
          │   conditions   │ met             │
          │   met          │                 │
          │                ▼                 │
          │         ┌──────────────┐         │
          │         │  ROTATING    │─────────┘
          │         └──────┬───────┘
          │                │
          │   validation   │ validation
          │   failed       │ succeeded
          │                ▼
          │         ┌──────────────┐
          │         │  VALIDATING  │
          │         └──────┬───────┘
          │                │
          │   grace period │ started
          │                ▼
          │         ┌──────────────┐
          └─────────│ GRACE_PERIOD │
                    └──────┬───────┘
                           │
                  grace    │ expired
                  period   │
                           ▼
                    ┌──────────────┐
                    │ INVALIDATING │
                    └──────┬───────┘
                           │
                    old    │ token
                    token  │ cleared
                           ▼
                    ┌──────────────┐
                    │   COMPLETE   │
                    └──────────────┘
```

### Token Lifecycle with Rotation

```
Time: 00:00   Token A issued (expires 24:00)
      ├─────────────────────────────────────►
      │
      │  [Normal operations with Token A]
      │
Time: 12:00   Rotation scheduled
      ├─────► [ROTATION TRIGGERED]
      │
      │       - Get new Token B
      │       - Validate Token B
      │       - Store Token B
      │
Time: 12:01   Token B active
      ├─────► [GRACE PERIOD START]
      │
      │       - New operations use Token B
      │       - In-flight operations with Token A allowed
      │
Time: 12:06   Grace period expires
      ├─────► [TOKEN A INVALIDATED]
      │
      │       - Token A cleared from memory
      │       - Token A added to blacklist (optional)
      │       - Only Token B accepted
      │
Time: 24:00   Token B scheduled for rotation
      ├─────► [NEXT ROTATION CYCLE]
```

## Data Structures

### RotationEvent Structure

```yaml
RotationEvent:
  rotation_id:
    type: string (UUID)
    example: "550e8400-e29b-41d4-a716-446655440000"
    description: "Unique identifier for rotation event"

  timestamp:
    type: datetime (ISO 8601)
    example: "2025-10-22T12:00:00Z"
    description: "Rotation trigger timestamp"

  old_token_id:
    type: string (UUID)
    description: "Identifier of token being rotated"

  new_token_id:
    type: string (UUID)
    description: "Identifier of new token"

  reason:
    type: enum
    values: [scheduled, manual, compromise_detected, error_recovery]
    description: "Reason for rotation"

  status:
    type: enum
    values: [initiated, in_progress, succeeded, failed, rolled_back]
    description: "Rotation status"

  duration_ms:
    type: integer
    description: "Rotation duration in milliseconds"

  error_message:
    type: string (optional)
    description: "Error message if rotation failed"

  grace_period_end:
    type: datetime (ISO 8601)
    description: "Timestamp when old token will be invalidated"
```

### RotationConfig Structure

```yaml
RotationConfig:
  enabled:
    type: boolean
    default: true
    description: "Enable automatic token rotation"

  interval_hours:
    type: integer
    min: 1
    max: 24
    default: 12
    description: "Hours between automatic rotations"

  grace_period_seconds:
    type: integer
    default: 300  # 5 minutes
    description: "Seconds to keep old token valid after rotation"

  idle_optimization:
    type: boolean
    default: true
    description: "Skip rotation if no activity in past 24 hours"

  retry_policy:
    max_attempts: 3
    backoff_delays_seconds: [30, 60, 120]
    description: "Retry policy for failed rotations"

  emergency_rotation:
    enabled: true
    trigger_on_compromise: true
    immediate_invalidation: true  # Skip grace period on emergency
    description: "Emergency rotation settings"
```

### TokenBlacklist Structure

```yaml
TokenBlacklist:
  token_id:
    type: string (UUID)
    description: "Identifier of revoked token (not full token value)"

  revoked_at:
    type: datetime (ISO 8601)
    description: "Revocation timestamp"

  reason:
    type: enum
    values: [manual_revoke, compromise_detected, rotation, expired]
    description: "Revocation reason"

  revoked_by:
    type: string
    example: "admin@example.com"
    description: "User or system that triggered revocation"

  expires_at:
    type: datetime (ISO 8601)
    description: "When blacklist entry can be removed (24 hours after revocation)"
```

## Configuration

### Rotation Configuration (YAML)

```yaml
# config/rotation_config.yaml

token_rotation:
  # Enable automatic rotation
  enabled: true

  # Rotation schedule
  schedule:
    interval_hours: 12  # Rotate every 12 hours
    time_of_day: null   # null = every N hours, or "02:00" for fixed time

    # Idle optimization
    skip_if_idle: true
    idle_threshold_hours: 24

  # Rotation behavior
  rotation:
    grace_period_seconds: 300  # 5 minutes
    validate_new_token: true
    clear_old_token: true
    queue_requests_during_rotation: true

    # Retry policy
    retry_policy:
      max_attempts: 3
      backoff_delays_seconds: [30, 60, 120]

  # Emergency rotation
  emergency:
    enabled: true
    trigger_on_compromise: true
    immediate_invalidation: true  # Skip grace period
    alert_security_team: true

  # Token blacklist
  blacklist:
    enabled: true
    storage: "memory"  # or "redis", "database"
    retention_hours: 24  # Remove after 24 hours

    # Redis configuration (if storage = redis)
    redis:
      host: "localhost"
      port: 6379
      db: 0
      key_prefix: "token_blacklist:"

  # Rotation history
  history:
    enabled: true
    max_records: 1000
    retention_days: 30
    storage: "database"  # or "file", "memory"

  # Monitoring and alerts
  monitoring:
    log_all_rotations: true
    alert_on_rotation_failure: true
    alert_threshold_failures: 2  # Alert after 2 consecutive failures

    # Metrics
    expose_metrics: true
    metrics_endpoint: "/metrics"
```

### Scheduler Configuration

```yaml
# config/scheduler_config.yaml

scheduler:
  # Token rotation job
  token_rotation_job:
    enabled: true
    schedule: "0 */12 * * *"  # Every 12 hours (cron format)
    timezone: "UTC"

    # Retry on failure
    retry_on_failure: true
    max_retries: 3

    # Execution timeout
    timeout_seconds: 30

  # Blacklist cleanup job
  blacklist_cleanup_job:
    enabled: true
    schedule: "0 0 * * *"  # Daily at midnight
    retention_hours: 24

  # Rotation health check job
  rotation_health_check_job:
    enabled: true
    schedule: "*/5 * * * *"  # Every 5 minutes
    alert_on_overdue: true
```

## Security Considerations

### S-001: Secure Token Invalidation

**Requirements:**
- Old tokens MUST be cleared from memory immediately after grace period
- Old tokens MUST be overwritten (not just freed) to prevent memory dumps
- Old tokens SHOULD be added to blacklist for verification

**Implementation:**
```python
import ctypes

def secure_invalidate_token(token: str) -> None:
    """Securely invalidate and clear token from memory."""
    # Add to blacklist
    blacklist.add(get_token_id(token))

    # Overwrite token in memory
    token_bytes = bytearray(token.encode())
    ctypes.memset(id(token_bytes), 0, len(token_bytes))

    # Delete reference
    del token
    del token_bytes
```

### S-002: Grace Period Security

**Rationale:**
- Grace period allows in-flight requests to complete
- Prevents failed requests during rotation
- Minimizes user-facing errors

**Risk Mitigation:**
- Keep grace period short (5 minutes maximum)
- Track usage of old token during grace period
- Alert if old token used after grace period expires

### S-003: Revocation vs Rotation

**Distinction:**
- **Rotation**: Proactive, scheduled token replacement
- **Revocation**: Reactive, immediate token invalidation

**When to Use:**
- **Rotation**: Regular security hygiene (every 12 hours)
- **Revocation**: Compromise detected, emergency logout

### S-004: Token Blacklist Security

**Requirements:**
- Blacklist MUST be checked before accepting any token
- Blacklist lookups MUST be fast (< 10ms)
- Blacklist entries MUST expire after token natural expiry + 1 hour
- Blacklist MUST survive application restarts

**Implementation:**
```python
# In-memory blacklist with TTL
from datetime import datetime, timedelta
from typing import Dict, Optional

class TokenBlacklist:
    def __init__(self):
        self._blacklist: Dict[str, datetime] = {}

    def add(self, token_id: str, expires_at: datetime) -> None:
        """Add token to blacklist."""
        self._blacklist[token_id] = expires_at

    def is_revoked(self, token_id: str) -> bool:
        """Check if token is revoked."""
        if token_id not in self._blacklist:
            return False

        # Check if blacklist entry expired
        if datetime.utcnow() > self._blacklist[token_id]:
            del self._blacklist[token_id]
            return False

        return True

    def cleanup_expired(self) -> int:
        """Remove expired blacklist entries."""
        now = datetime.utcnow()
        expired = [tid for tid, exp in self._blacklist.items() if now > exp]
        for tid in expired:
            del self._blacklist[tid]
        return len(expired)
```

## Error Handling

### Error Scenarios

**E-001: Rotation Fails During Token Refresh**
```
Scenario: New token request returns 500 error
Response:
  1. Log error: "Token rotation failed - refresh error"
  2. Do NOT invalidate current token
  3. Retry with exponential backoff (30s, 60s, 120s)
  4. If all retries fail: Log warning, schedule next rotation
  5. Alert on repeated rotation failures (>= 2 consecutive)
```

**E-002: New Token Validation Fails**
```
Scenario: New token fails /validate endpoint
Response:
  1. Log error: "Token rotation failed - validation error"
  2. Discard new token
  3. Keep using current token
  4. Retry rotation after backoff period
  5. Alert if validation fails repeatedly
```

**E-003: Grace Period Request with Old Token**
```
Scenario: Request arrives with old token during grace period
Response:
  1. Allow request (old token still valid)
  2. Log info: "Request using old token during grace period"
  3. Track usage count of old token
  4. After grace period expires, reject old token
```

**E-004: Request with Revoked Token**
```
Scenario: Request arrives with revoked (blacklisted) token
Response:
  1. Reject request immediately with 401 Unauthorized
  2. Log warning: "Revoked token used"
  3. Increment revoked token usage counter
  4. If usage count > 5: Alert security team (possible attack)
```

**E-005: Emergency Rotation Triggered**
```
Scenario: Compromise detected, emergency rotation needed
Response:
  1. Log critical: "Emergency rotation triggered"
  2. Revoke current token immediately (no grace period)
  3. Clear current token from memory and storage
  4. Request new token
  5. Alert security team
  6. Continue with new token
```

### Error Codes

| Error Code | Description | Recovery Action |
|------------|-------------|-----------------|
| ROTATION_FAILED | Token rotation failed | Keep current token, retry later |
| VALIDATION_FAILED | New token validation failed | Discard new token, retry |
| REVOKED_TOKEN_USED | Revoked token used in request | Reject request, alert if repeated |
| GRACE_PERIOD_EXPIRED | Old token used after grace period | Reject request, log warning |
| EMERGENCY_ROTATION | Emergency rotation triggered | Immediate revocation and refresh |

## Implementation Checklist

### Phase 1: Core Rotation Logic
- [ ] Create TokenRotationManager class
- [ ] Implement rotation orchestrator
- [ ] Implement grace period handling
- [ ] Implement old token invalidation
- [ ] Add unit tests for rotation logic

### Phase 2: Scheduling
- [ ] Implement rotation scheduler (cron-based)
- [ ] Implement idle optimization (skip if no activity)
- [ ] Implement configurable rotation intervals
- [ ] Add unit tests for scheduler

### Phase 3: Revocation Service
- [ ] Implement TokenBlacklist class
- [ ] Implement add/check/cleanup operations
- [ ] Implement persistent storage (Redis or database)
- [ ] Add unit tests for blacklist operations

### Phase 4: Emergency Rotation
- [ ] Implement emergency rotation trigger
- [ ] Implement immediate invalidation (no grace period)
- [ ] Implement security team alerting
- [ ] Add integration tests for emergency scenarios

### Phase 5: Rotation History
- [ ] Implement rotation event logging
- [ ] Implement history storage (database or file)
- [ ] Implement history query API
- [ ] Add audit reporting

### Phase 6: Integration
- [ ] Integrate with TokenManager (TOKEN_REFRESH_STRATEGY_SPEC.md)
- [ ] Integrate with AuthService
- [ ] Add configuration file parsing
- [ ] Add command-line tools for manual rotation

### Phase 7: Monitoring and Metrics
- [ ] Add metrics for rotation success/failure rate
- [ ] Add metrics for rotation duration
- [ ] Add metrics for blacklist size
- [ ] Add alerts for rotation anomalies
- [ ] Add dashboard for rotation health

## Validation Criteria

### Functional Validation

**FV-1: Scheduled Rotation Works**
```
Test: Schedule rotation for 12:00, verify rotation occurs
Expected: Token rotated at 12:00, new token active after grace period
Validation: Check rotation history for event at 12:00
```

**FV-2: Grace Period Honored**
```
Test: Rotate token, send request with old token at T+2 minutes
Expected: Request succeeds (within grace period)
Validation: Check response is 200 OK
```

**FV-3: Old Token Rejected After Grace Period**
```
Test: Rotate token, send request with old token at T+6 minutes
Expected: Request fails with 401 Unauthorized
Validation: Check response is 401, error message indicates revoked token
```

**FV-4: Emergency Rotation Works**
```
Test: Trigger emergency rotation
Expected: Current token revoked immediately, new token issued
Validation: Old token rejected immediately, no grace period
```

**FV-5: Blacklist Prevents Revoked Token Usage**
```
Test: Revoke token, attempt to use it
Expected: Request fails with 401, blacklist check prevents usage
Validation: Check blacklist contains token ID
```

### Performance Validation

**PV-1: Rotation Duration**
```
Metric: Token rotation duration (P95)
Target: < 5 seconds
Measurement: Monitor rotation_duration_seconds metric
```

**PV-2: Blacklist Lookup Performance**
```
Metric: Blacklist lookup duration (P95)
Target: < 10ms
Measurement: Monitor blacklist_lookup_duration_ms metric
```

### Security Validation

**SV-1: Old Token Cleared from Memory**
```
Test: Rotate token, inspect memory for old token value
Expected: Old token overwritten, not found in memory dump
Validation: Memory inspection shows no plaintext old token
```

**SV-2: Rotation Events Logged**
```
Test: Rotate token, review audit logs
Expected: Rotation event logged with timestamp, old/new token IDs (sanitized)
Validation: Check logs contain "Token rotated" with metadata
```

## References

### Related Specifications
- **TOKEN_REFRESH_STRATEGY_SPEC.md**: Token refresh integration
- **TOKEN_STORAGE_SECURITY_SPEC.md**: Secure token storage
- **SESSION_INVALIDATION_SPEC.md**: Token revocation and logout

### Error Analysis References
- **ERRORS_AND_WARNINGS_CONSOLIDATED.md**:
  - Line 289-295: SEC-API-002 (No Token Rotation Strategy)

### Security Standards
- **NIST SP 800-63B**: Digital Identity Guidelines (Token Lifecycle)
- **OWASP**: Session Management Cheat Sheet
- **RFC 7009**: OAuth 2.0 Token Revocation

---

**Document Status:** DRAFT v1.0
**Last Updated:** 2025-10-22
**Next Review:** After security audit
**Approval Required:** Security Team
