# Session Invalidation Specification

**doc_id:** SEC-006
**version:** 1.0
**status:** DRAFT
**priority:** MEDIUM
**addresses:** SEC-API-004 from ERRORS_AND_WARNINGS_CONSOLIDATED.md

## Overview

This specification defines session invalidation and logout mechanisms for the Simple Risk Manager. Since the TradeStation API does not provide a logout endpoint, this spec details alternative strategies for token invalidation, server-side revocation simulation, and session cleanup procedures.

## Problem Statement

**From SEC-API-004:**
- No logout endpoint documented in TradeStation API
- No way to invalidate tokens server-side
- No server-side revocation mechanism available
- Cannot force logout of compromised sessions
- No session cleanup procedures

## Requirements

### Functional Requirements

**FR-1: Client-Side Token Invalidation**
- System MUST provide logout function that clears local token
- System MUST clear token from memory on logout
- System MUST clear token from persistent storage on logout
- System MUST prevent token reuse after logout

**FR-2: Token Blacklist (Revocation Simulation)**
- System MUST maintain client-side blacklist of invalidated tokens
- System MUST check blacklist before using token for requests
- System MUST persist blacklist across application restarts
- System MUST expire blacklist entries after token natural expiry

**FR-3: Multi-Session Management**
- System SHOULD support tracking multiple active sessions
- System MUST invalidate specific session by session ID
- System MUST support "logout all sessions" functionality
- System MUST track session creation and last activity timestamps

**FR-4: Emergency Lockdown**
- System MUST support immediate session termination on compromise
- System MUST clear all active sessions on emergency lockdown
- System MUST prevent re-authentication for lockdown duration (optional)
- System MUST alert security team on emergency lockdown

**FR-5: Session Cleanup**
- System MUST automatically clean up expired sessions
- System MUST remove stale sessions (no activity > 24 hours)
- System MUST expire blacklist entries after token expiry + 1 hour
- System MUST log all session cleanup events

### Non-Functional Requirements

**NFR-1: Performance**
- Logout operation MUST complete in < 1 second
- Blacklist check MUST complete in < 10ms
- Session cleanup MUST NOT impact active operations

**NFR-2: Security**
- Invalidated tokens MUST NOT be usable
- Tokens MUST be cleared securely from memory (overwrite, not just delete)
- Blacklist MUST persist across restarts
- Session data MUST be encrypted at rest

**NFR-3: Reliability**
- Logout MUST succeed even if network unavailable
- Blacklist MUST survive application crashes
- Session state MUST be recoverable after restart

**NFR-4: Auditability**
- System MUST log all logout events
- System MUST log all session invalidations
- System MUST maintain audit trail of session lifecycle
- System MUST track logout reason (user logout, timeout, compromise)

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  SessionInvalidationManager                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Session Manager                                     │   │
│  │  - create_session() -> Session                       │   │
│  │  - invalidate_session(session_id: str) -> None       │   │
│  │  - logout_all() -> None                              │   │
│  │  - get_active_sessions() -> List[Session]            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Token Blacklist                                     │   │
│  │  - add_token(token_id: str, expires_at: dt) -> None  │   │
│  │  - is_blacklisted(token_id: str) -> bool             │   │
│  │  - cleanup_expired() -> int                          │   │
│  │  - persist() -> None                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Session Cleaner                                     │   │
│  │  - cleanup_expired() -> int                          │   │
│  │  - cleanup_stale(threshold_hours: int) -> int        │   │
│  │  - schedule_cleanup() -> None                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ TokenManager │ │ AuditLogger  │ │ Storage      │
  │ (clear       │ │ (log events) │ │ (persist     │
  │  tokens)     │ │              │ │  blacklist)  │
  └──────────────┘ └──────────────┘ └──────────────┘
```

### Logout Flow

```
User         SessionManager    TokenBlacklist    TokenManager    Storage
 │                │                  │                │            │
 │─logout()──────►│                  │                │            │
 │                │                  │                │            │
 │                ├─get_session_info()               │            │
 │                │  [token_id,      │               │            │
 │                │   expires_at]    │               │            │
 │                │                  │               │            │
 │                ├─add_to_blacklist()──────────────►│            │
 │                │  [Prevent reuse] │               │            │
 │                │                  │               │            │
 │                │                  ├─persist()─────┼───────────►│
 │                │                  │ [Save to disk]│            │
 │                │                  │               │            │
 │                ├─clear_token()────┼───────────────►            │
 │                │  [Remove from    │               │            │
 │                │   memory/storage]│               │            │
 │                │                  │               │            │
 │                ├─mark_invalidated()               │            │
 │                │  [Update session │               │            │
 │                │   status]        │               │            │
 │                │                  │               │            │
 │                ├─log_logout()     │               │            │
 │                │  "User logout"   │               │            │
 │                │                  │               │            │
 │◄─success───────┤                  │               │            │
```

### Emergency Lockdown Flow

```
Admin/Alert    SessionManager    TokenBlacklist    TokenManager
    │               │                  │                │
    │─emergency()──►│                  │                │
    │  lockdown     │                  │                │
    │               │                  │                │
    │               ├─get_all_sessions()               │
    │               │  [All active     │               │
    │               │   sessions]      │               │
    │               │                  │               │
    │               │  FOR EACH SESSION:               │
    │               │                  │               │
    │               ├─blacklist()──────►               │
    │               │                  │               │
    │               ├─clear_token()────┼───────────────►
    │               │                  │               │
    │               ├─mark_compromised()               │
    │               │                  │               │
    │               ├─log_lockdown()   │               │
    │               │  "Emergency      │               │
    │               │   lockdown"      │               │
    │               │                  │               │
    │               ├─notify_security()                │
    │               │  [Alert team]    │               │
    │               │                  │               │
    │               ├─disable_auth()   │               │
    │               │  [Optional:      │               │
    │               │   Block re-auth  │               │
    │               │   for 30min]     │               │
    │               │                  │               │
    │◄─complete─────┤                  │               │
```

### Blacklist Check Flow (on every request)

```
APIClient    TokenManager    TokenBlacklist    TradeStationAPI
    │             │                │                  │
    │─request()──►│                │                  │
    │             │                │                  │
    │             ├─get_token()    │                  │
    │             │                │                  │
    │             ├─check_blacklist()─────────────────►
    │             │                │                  │
    │             │  [Lookup token_id in blacklist]   │
    │             │                │                  │
    │             │◄─is_valid──────┤                  │
    │             │  (not blacklisted)                │
    │             │                │                  │
    │             ├─execute_request()────────────────►│
    │             │                │                  │
    │◄─response───┤                │                  │
```

## Data Structures

### Session Structure

```yaml
Session:
  session_id:
    type: string (UUID)
    example: "550e8400-e29b-41d4-a716-446655440000"
    description: "Unique session identifier"

  token_id:
    type: string (UUID)
    description: "Associated token identifier"

  created_at:
    type: datetime (ISO 8601)
    example: "2025-10-22T10:30:00Z"
    description: "Session creation timestamp"

  last_activity:
    type: datetime (ISO 8601)
    description: "Last API request timestamp"

  expires_at:
    type: datetime (ISO 8601)
    description: "Session expiration (24 hours from creation)"

  status:
    type: enum
    values: [active, invalidated, expired, compromised]
    description: "Current session status"

  invalidation_reason:
    type: enum (optional)
    values: [user_logout, timeout, compromise_detected, emergency_lockdown]
    description: "Reason for session invalidation"

  invalidated_at:
    type: datetime (ISO 8601, optional)
    description: "Timestamp when session was invalidated"

  metadata:
    type: object
    description: "Additional session metadata"
    properties:
      user_id: string
      client_ip: string (optional)
      user_agent: string (optional)
```

### BlacklistEntry Structure

```yaml
BlacklistEntry:
  token_id:
    type: string (UUID)
    description: "Token identifier (not full token value)"

  blacklisted_at:
    type: datetime (ISO 8601)
    example: "2025-10-22T14:30:00Z"
    description: "Blacklist addition timestamp"

  expires_at:
    type: datetime (ISO 8601)
    description: "When entry can be removed (token expiry + 1 hour)"

  reason:
    type: enum
    values: [user_logout, session_timeout, compromise_detected, emergency_lockdown]
    description: "Reason for blacklisting"

  session_id:
    type: string (UUID)
    description: "Associated session identifier"

  metadata:
    type: object
    description: "Additional blacklist metadata"
    properties:
      user_id: string
      triggered_by: string  # user, system, admin
```

### LogoutResult Structure

```yaml
LogoutResult:
  success:
    type: boolean
    description: "Whether logout succeeded"

  session_id:
    type: string (UUID)
    description: "Invalidated session identifier"

  token_cleared:
    type: boolean
    description: "Whether token was cleared from storage"

  blacklisted:
    type: boolean
    description: "Whether token was added to blacklist"

  timestamp:
    type: datetime (ISO 8601)
    description: "Logout timestamp"

  message:
    type: string
    example: "Session invalidated successfully"
    description: "Logout status message"
```

## Configuration

### Session Invalidation Configuration (YAML)

```yaml
# config/session_config.yaml

session_invalidation:
  # Session management
  session:
    max_duration_hours: 24  # Maximum session duration
    idle_timeout_hours: 8   # Logout after 8 hours of inactivity
    track_last_activity: true

    # Multi-session support
    allow_multiple_sessions: false  # One active session per user
    max_concurrent_sessions: 1

  # Logout behavior
  logout:
    clear_token_from_memory: true
    clear_token_from_storage: true
    add_to_blacklist: true
    log_logout_event: true

    # Confirmation
    require_confirmation: false  # No confirmation dialog

  # Token blacklist
  blacklist:
    enabled: true
    storage: "file"  # file, redis, database
    persist_on_change: true

    # File storage (if storage = file)
    file:
      path: "${HOME}/.simple-risk-manager/secure/blacklist.json"
      permissions: "0600"
      backup_enabled: true

    # Redis storage (if storage = redis)
    redis:
      host: "localhost"
      port: 6379
      db: 0
      key_prefix: "blacklist:"

    # Cleanup
    cleanup:
      enabled: true
      interval_hours: 1  # Clean up every hour
      retention_after_expiry_hours: 1  # Keep for 1 hour after token expiry

  # Emergency lockdown
  emergency:
    enabled: true
    invalidate_all_sessions: true
    clear_all_tokens: true
    disable_auth_duration_minutes: 30  # Disable re-auth for 30 minutes
    alert_security_team: true
    alert_channels: ["email", "slack"]

  # Session cleanup
  cleanup:
    enabled: true
    schedule: "0 * * * *"  # Every hour (cron format)

    # Cleanup rules
    rules:
      - type: "expired"
        description: "Remove sessions past expiration"
      - type: "stale"
        threshold_hours: 24
        description: "Remove sessions with no activity for 24 hours"
      - type: "invalidated"
        retention_hours: 168  # Keep invalidated sessions for 7 days
        description: "Remove old invalidated sessions"

  # Audit logging
  audit:
    enabled: true
    log_file: "${HOME}/.simple-risk-manager/logs/session_audit.log"
    log_permissions: "0600"

    # Events to log
    log_events:
      - "session_created"
      - "session_invalidated"
      - "logout"
      - "emergency_lockdown"
      - "blacklist_check"
      - "cleanup_executed"

    # Include metadata
    include_metadata: true
    sanitize_tokens: true  # NEVER log plaintext tokens
```

### Environment Variables

```bash
# .env

# Session configuration
SESSION_MAX_DURATION_HOURS=24
SESSION_IDLE_TIMEOUT_HOURS=8

# Blacklist storage
BLACKLIST_STORAGE=file
BLACKLIST_FILE_PATH=${HOME}/.simple-risk-manager/secure/blacklist.json

# Emergency lockdown
EMERGENCY_LOCKDOWN_ENABLED=true
EMERGENCY_AUTH_DISABLE_MINUTES=30

# Cleanup schedule
SESSION_CLEANUP_ENABLED=true
SESSION_CLEANUP_INTERVAL_HOURS=1
```

## Security Considerations

### S-001: Client-Side Blacklist Limitations

**Limitation:** Client-side blacklist cannot prevent token reuse on server side

**Mitigation Strategies:**
1. **Rapid Token Rotation**: Rotate tokens frequently (every 12 hours)
2. **Short Token Lifetime**: Prefer shorter token expiry (if API supports)
3. **Compromise Detection**: Monitor for suspicious activity
4. **Multi-Factor Verification**: Add additional authentication factors for critical operations

**Acceptance:**
- Acknowledge that without server-side revocation, complete prevention is impossible
- Focus on making token reuse difficult and detectable
- Implement defense in depth

### S-002: Secure Token Clearing

**Requirements:**
- Tokens MUST be overwritten in memory (not just deleted)
- Tokens MUST be cleared from all storage locations
- Token clearing MUST be atomic (all-or-nothing)

**Implementation:**
```python
import ctypes
import os

def secure_clear_token(token: str) -> None:
    """Securely clear token from memory."""
    # Overwrite token string in memory
    token_bytes = bytearray(token.encode())
    ctypes.memset(id(token_bytes), 0, len(token_bytes))

    # Clear from storage
    token_storage_path = get_token_storage_path()
    if os.path.exists(token_storage_path):
        # Overwrite file content before deletion
        with open(token_storage_path, 'rb') as f:
            file_size = os.path.getsize(token_storage_path)

        with open(token_storage_path, 'wb') as f:
            f.write(b'\x00' * file_size)

        # Delete file
        os.remove(token_storage_path)

    # Delete references
    del token
    del token_bytes
```

### S-003: Blacklist Persistence

**Requirements:**
- Blacklist MUST survive application restarts
- Blacklist MUST be protected from tampering
- Blacklist file MUST have restrictive permissions (0600)

**Implementation:**
```python
import json
import os
from datetime import datetime
from typing import Dict, List

class PersistentBlacklist:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._blacklist: Dict[str, BlacklistEntry] = {}
        self._load()

    def _load(self) -> None:
        """Load blacklist from file."""
        if not os.path.exists(self.file_path):
            return

        # Validate file permissions
        file_stat = os.stat(self.file_path)
        if file_stat.st_mode & 0o077:  # Check if group/other have permissions
            raise SecurityError(f"Insecure permissions on {self.file_path}")

        with open(self.file_path, 'r') as f:
            data = json.load(f)
            for entry in data:
                self._blacklist[entry['token_id']] = BlacklistEntry(**entry)

    def _save(self) -> None:
        """Save blacklist to file."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.file_path), mode=0o700, exist_ok=True)

        # Write to temporary file first (atomic write)
        temp_path = f"{self.file_path}.tmp"
        with open(temp_path, 'w') as f:
            json.dump([entry.to_dict() for entry in self._blacklist.values()], f)

        # Set restrictive permissions
        os.chmod(temp_path, 0o600)

        # Atomic rename
        os.replace(temp_path, self.file_path)

    def add(self, entry: BlacklistEntry) -> None:
        """Add entry to blacklist."""
        self._blacklist[entry.token_id] = entry
        self._save()  # Persist immediately

    def is_blacklisted(self, token_id: str) -> bool:
        """Check if token is blacklisted."""
        return token_id in self._blacklist

    def cleanup_expired(self) -> int:
        """Remove expired blacklist entries."""
        now = datetime.utcnow()
        expired = [tid for tid, entry in self._blacklist.items() if now > entry.expires_at]

        for tid in expired:
            del self._blacklist[tid]

        if expired:
            self._save()

        return len(expired)
```

### S-004: Emergency Lockdown Procedures

**Trigger Conditions:**
- Compromise detected (repeated auth failures, anomalous activity)
- Manual trigger by administrator
- Automated security system alert

**Lockdown Actions:**
1. Invalidate all active sessions immediately
2. Clear all tokens from storage
3. Add all tokens to blacklist
4. Disable authentication for lockdown_duration_minutes (optional)
5. Alert security team via all channels (email, Slack, PagerDuty)
6. Log detailed lockdown event with triggering reason

**Recovery:**
- Wait for lockdown duration to expire
- Manually verify security incident resolved
- Re-enable authentication
- Users must re-authenticate with API key

### S-005: Audit Trail

**Requirements:**
- Log all logout events with timestamp, session ID, reason
- Log all blacklist additions with token ID (sanitized)
- Log all emergency lockdown events
- Maintain audit trail for minimum 90 days

**Sanitization:**
```python
def log_logout(session_id: str, token_id: str, reason: str) -> None:
    """Log logout event with sanitized token."""
    logger.info(
        f"Session invalidated: "
        f"session_id={session_id}, "
        f"token_id={sanitize_token_id(token_id)}, "
        f"reason={reason}, "
        f"timestamp={datetime.utcnow().isoformat()}"
    )

def sanitize_token_id(token_id: str) -> str:
    """Sanitize token ID for logging."""
    if not token_id or len(token_id) < 10:
        return "[REDACTED]"
    return f"{token_id[:8]}...{token_id[-4:]}"
```

## Error Handling

### Error Scenarios

**E-001: Logout with No Active Session**
```
Scenario: User calls logout but no active session exists
Response:
  1. Log info: "Logout called with no active session"
  2. Return success (idempotent operation)
  3. Ensure no tokens in storage
  4. Display message: "Already logged out"
```

**E-002: Blacklist File Corrupted**
```
Scenario: Blacklist file cannot be parsed
Response:
  1. Log error: "Blacklist file corrupted"
  2. Backup corrupted file (blacklist.json.corrupt)
  3. Create new empty blacklist
  4. Log warning: "Blacklist reset - some tokens may not be blacklisted"
  5. Alert administrator
```

**E-003: Blacklist Persistence Fails**
```
Scenario: Cannot write blacklist to disk
Response:
  1. Log error: "Failed to persist blacklist"
  2. Keep blacklist in memory only (temporary)
  3. Retry persistence with exponential backoff
  4. Alert administrator if retries exhausted
  5. Log warning: "Blacklist not persisted - will be lost on restart"
```

**E-004: Emergency Lockdown While Offline**
```
Scenario: Emergency lockdown triggered while network unavailable
Response:
  1. Log critical: "Emergency lockdown (offline mode)"
  2. Invalidate all local sessions
  3. Clear all tokens from storage
  4. Blacklist all tokens in memory
  5. Queue security team alert for when network available
  6. Display error: "Emergency lockdown active - system offline"
```

**E-005: Session Cleanup Failure**
```
Scenario: Session cleanup job fails
Response:
  1. Log error: "Session cleanup failed"
  2. Record failed cleanup in metrics
  3. Retry cleanup on next scheduled run
  4. Alert if cleanup fails 3 consecutive times
```

### Error Codes

| Error Code | Description | Recovery Action |
|------------|-------------|-----------------|
| NO_ACTIVE_SESSION | No active session to logout | Return success (idempotent) |
| BLACKLIST_CORRUPTED | Blacklist file corrupted | Reset blacklist, backup old |
| BLACKLIST_PERSIST_FAILED | Cannot save blacklist | Keep in memory, retry |
| EMERGENCY_LOCKDOWN_OFFLINE | Lockdown while offline | Local lockdown, queue alert |
| CLEANUP_FAILED | Session cleanup failed | Retry on next run |
| TOKEN_CLEAR_FAILED | Cannot clear token from storage | Log error, manual cleanup |

## Implementation Checklist

### Phase 1: Core Session Management
- [ ] Create SessionManager class
- [ ] Implement session creation and tracking
- [ ] Implement session invalidation
- [ ] Add session status tracking (active, invalidated, expired)
- [ ] Add unit tests for session management

### Phase 2: Token Blacklist
- [ ] Create TokenBlacklist class
- [ ] Implement in-memory blacklist
- [ ] Implement persistent blacklist (file storage)
- [ ] Implement blacklist check on every request
- [ ] Add unit tests for blacklist operations

### Phase 3: Logout Function
- [ ] Implement logout() method
- [ ] Implement token clearing from memory
- [ ] Implement token clearing from storage
- [ ] Integrate with blacklist
- [ ] Add unit tests for logout

### Phase 4: Emergency Lockdown
- [ ] Implement emergency_lockdown() method
- [ ] Implement invalidate all sessions
- [ ] Implement clear all tokens
- [ ] Implement optional auth disabling
- [ ] Add security team alerting
- [ ] Add integration tests for lockdown

### Phase 5: Session Cleanup
- [ ] Implement cleanup scheduler
- [ ] Implement cleanup for expired sessions
- [ ] Implement cleanup for stale sessions
- [ ] Implement cleanup for old blacklist entries
- [ ] Add unit tests for cleanup logic

### Phase 6: Audit Logging
- [ ] Implement audit log writer
- [ ] Log all session events
- [ ] Log all logout events
- [ ] Log all emergency lockdown events
- [ ] Implement token sanitization for logs

### Phase 7: Integration
- [ ] Integrate with TokenManager
- [ ] Integrate with APIClient (blacklist check on requests)
- [ ] Add configuration file parsing
- [ ] Add command-line tools for manual operations
- [ ] Add integration tests

## Validation Criteria

### Functional Validation

**FV-1: Logout Clears Token**
```
Test: Call logout(), verify token cleared from storage
Expected: Token file deleted, token not in memory
Validation: Check token_storage_path does not exist
```

**FV-2: Blacklisted Token Rejected**
```
Test: Logout, attempt to use old token for API request
Expected: Request rejected, blacklist check prevents usage
Validation: Check request fails with "Token blacklisted" error
```

**FV-3: Blacklist Persists Across Restart**
```
Test: Logout, restart application, check blacklist
Expected: Token still in blacklist after restart
Validation: Load blacklist from file, verify token_id present
```

**FV-4: Emergency Lockdown Works**
```
Test: Trigger emergency lockdown
Expected: All sessions invalidated, all tokens cleared
Validation: Check no active sessions, no tokens in storage
```

**FV-5: Session Cleanup Removes Expired**
```
Test: Create session 25 hours ago, run cleanup
Expected: Expired session removed from tracking
Validation: Check session no longer in active sessions list
```

### Security Validation

**SV-1: Token Cleared from Memory**
```
Test: Logout, inspect memory for token value
Expected: Token overwritten, not found in memory dump
Validation: Memory inspection shows no plaintext token
```

**SV-2: Blacklist File Permissions Correct**
```
Test: Check blacklist file permissions
Expected: Permissions = 0600 (owner read/write only)
Validation: stat blacklist.json | check mode = 0600
```

**SV-3: Audit Log Contains Logout Events**
```
Test: Logout, review audit logs
Expected: Logout event logged with session_id, reason, timestamp
Validation: grep "Session invalidated" session_audit.log
```

### Performance Validation

**PV-1: Logout Duration**
```
Metric: Logout operation duration
Target: < 1 second
Measurement: Time logout() function call
```

**PV-2: Blacklist Check Duration**
```
Metric: Blacklist lookup duration (P95)
Target: < 10ms
Measurement: Time is_blacklisted() function call
```

## References

### Related Specifications
- **TOKEN_ROTATION_SPEC.md**: Token blacklist integration
- **TOKEN_REFRESH_STRATEGY_SPEC.md**: Token lifecycle management
- **TOKEN_STORAGE_SECURITY_SPEC.md**: Secure token clearing

### Error Analysis References
- **ERRORS_AND_WARNINGS_CONSOLIDATED.md**:
  - Line 298-303: SEC-API-004 (No Session Invalidation)

### Security Standards
- **OWASP**: Session Management Cheat Sheet
- **NIST SP 800-63B**: Digital Identity Guidelines (Session Management)
- **RFC 7009**: OAuth 2.0 Token Revocation

### Alternative Approaches (for API providers with logout support)
- **OAuth 2.0 Token Revocation**: https://tools.ietf.org/html/rfc7009
- **OpenID Connect Session Management**: https://openid.net/specs/openid-connect-session-1_0.html

---

**Document Status:** DRAFT v1.0
**Last Updated:** 2025-10-22
**Next Review:** After security audit
**Approval Required:** Security Team
