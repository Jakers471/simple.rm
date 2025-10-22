# API Key Management Specification

**doc_id:** SEC-004
**version:** 1.0
**status:** DRAFT
**priority:** HIGH
**addresses:** SEC-API-003 from ERRORS_AND_WARNINGS_CONSOLIDATED.md

## Overview

This specification defines secure API key storage, rotation, and lifecycle management for TradeStation API credentials. The API key is the root credential used for initial authentication and must be protected with the highest security standards.

## Problem Statement

**From SEC-API-003:**
- API key required for initial authentication but no guidance on secure storage
- No specification for environment variable usage
- No key rotation procedures defined
- No compromise detection and response strategy
- No key lifecycle management

## Requirements

### Functional Requirements

**FR-1: Secure Storage**
- System MUST store API keys in environment variables (preferred) OR encrypted files
- System MUST NOT store API keys in source code
- System MUST NOT store API keys in configuration files
- System MUST NOT store API keys in version control
- System MUST validate API key format on load

**FR-2: Key Rotation**
- System MUST support API key rotation without service interruption
- System MUST track key age and warn when rotation is due
- System MUST maintain old key during transition period (grace period)
- System MUST invalidate old key after successful rotation verification

**FR-3: Compromise Detection**
- System MUST monitor for suspicious authentication patterns
- System MUST detect repeated authentication failures
- System MUST detect authentication from unexpected IP addresses (if available)
- System MUST trigger alerts on compromise indicators

**FR-4: Key Lifecycle Management**
- System MUST track key creation date
- System MUST track last usage timestamp
- System MUST enforce maximum key age (recommendation: 90 days)
- System MUST provide key rotation reminders

**FR-5: Multi-Environment Support**
- System MUST support different keys per environment (dev, staging, production)
- System MUST prevent production keys from being used in development
- System MUST clearly identify which environment a key belongs to

### Non-Functional Requirements

**NFR-1: Security**
- API keys MUST be minimum 32 characters in length
- API keys MUST have high entropy (validated at load)
- API keys MUST be stored encrypted if not using environment variables
- API key files MUST have restrictive permissions (0600)

**NFR-2: Auditability**
- System MUST log all API key usage (sanitized)
- System MUST log key rotation events
- System MUST maintain audit trail of key lifecycle events
- System MUST alert security team on compromise detection

**NFR-3: Reliability**
- Key rotation MUST NOT cause service interruption
- System MUST validate new key before deactivating old key
- System MUST fall back to old key if new key fails validation
- System MUST provide clear error messages for key issues

**NFR-4: Compliance**
- System MUST comply with PCI-DSS key management requirements
- System MUST support security audits
- System MUST provide key usage reports
- System MUST support regulatory compliance reporting

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    APIKeyManager                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Key Provider Interface                              │   │
│  │  - load_key() -> str                                 │   │
│  │  - validate_key(key: str) -> bool                    │   │
│  │  - rotate_key(new_key: str) -> None                  │   │
│  │  - get_key_metadata() -> KeyMetadata                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Key Validator                                       │   │
│  │  - validate_format(key: str) -> bool                 │   │
│  │  - check_entropy(key: str) -> float                  │   │
│  │  - test_authentication(key: str) -> bool             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Compromise Detector                                 │   │
│  │  - monitor_auth_failures() -> None                   │   │
│  │  - detect_anomalies() -> List[Alert]                 │   │
│  │  - trigger_lockdown() -> None                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ EnvProvider  │ │ FileProvider │ │ VaultProvider│
  │ (env vars)   │ │ (encrypted)  │ │ (HashiCorp)  │
  └──────────────┘ └──────────────┘ └──────────────┘
```

### Key Rotation Flow

```
Administrator    APIKeyManager    TradeStationAPI    TokenManager
    │                 │                    │               │
    │─new_key────────►│                    │               │
    │                 │                    │               │
    │                 ├─validate_format()  │               │
    │                 │  [Check length,    │               │
    │                 │   entropy, format] │               │
    │                 │                    │               │
    │                 ├─test_auth()───────►│               │
    │                 │  (POST /authorize  │               │
    │                 │   with new key)    │               │
    │                 │◄────200 OK─────────│               │
    │                 │  {token: ...}      │               │
    │                 │                    │               │
    │                 ├─store_new_key()    │               │
    │                 │  [Keep old key     │               │
    │                 │   as backup]       │               │
    │                 │                    │               │
    │                 ├─notify()───────────┼──────────────►│
    │                 │  "New key active"  │               │
    │                 │                    │               │
    │                 │  [Grace period:    │               │
    │                 │   Old key still    │               │
    │                 │   valid for 24h]   │               │
    │                 │                    │               │
    │◄─success────────┤                    │               │
    │                 │                    │               │
    │  [Wait 24 hours for validation]      │               │
    │                 │                    │               │
    │─deactivate_old─►│                    │               │
    │                 │                    │               │
    │                 ├─delete_old_key()   │               │
    │                 │                    │               │
    │◄─complete───────┤                    │               │
```

### Compromise Detection Flow

```
APIKeyManager    AuthMonitor    CompromiseDetector    SecurityTeam
    │                 │                  │                 │
    │─auth_attempt───►│                  │                 │
    │  (failed)       │                  │                 │
    │                 │                  │                 │
    │                 ├─log_failure()    │                 │
    │                 │                  │                 │
    │                 ├─check_pattern()─►│                 │
    │                 │                  │                 │
    │                 │  [10 failures    │                 │
    │                 │   in 5 minutes]  │                 │
    │                 │                  │                 │
    │                 │◄─threshold_exceeded                │
    │                 │                  │                 │
    │                 ├─trigger_alert()──┼────────────────►│
    │                 │  "Possible       │                 │
    │                 │   compromise"    │                 │
    │                 │                  │                 │
    │◄────lockdown────┤◄─lockdown_mode()─┤                 │
    │  "Key disabled" │                  │                 │
    │                 │                  │                 │
    │  [Manual intervention required]    │                 │
```

## Data Structures

### APIKey Structure

```yaml
APIKey:
  key_id:
    type: string (UUID)
    example: "550e8400-e29b-41d4-a716-446655440000"
    description: "Unique identifier for key lifecycle tracking"

  key_value:
    type: string
    min_length: 32
    description: "API key value (encrypted at rest, never logged)"

  environment:
    type: enum
    values: [development, staging, production]
    description: "Environment this key is valid for"

  created_at:
    type: datetime (ISO 8601)
    example: "2025-10-22T10:30:00Z"
    description: "Key creation timestamp"

  last_used:
    type: datetime (ISO 8601)
    description: "Last successful authentication timestamp"

  expires_at:
    type: datetime (ISO 8601)
    example: "2026-01-20T10:30:00Z"
    description: "Key expiration (90 days from creation)"

  status:
    type: enum
    values: [active, rotating, revoked, expired]
    description: "Current key status"

  rotation_due:
    type: boolean
    description: "True if key age > 80 days (rotation warning)"

  usage_count:
    type: integer
    description: "Number of times key has been used for authentication"

  failure_count:
    type: integer
    description: "Number of consecutive authentication failures"
```

### KeyMetadata Structure

```yaml
KeyMetadata:
  key_id:
    type: string (UUID)
    description: "Key identifier"

  environment:
    type: enum
    values: [development, staging, production]

  age_days:
    type: integer
    description: "Days since key creation"

  days_until_expiry:
    type: integer
    description: "Days until key expires (90 - age_days)"

  rotation_recommended:
    type: boolean
    description: "True if age_days >= 80"

  rotation_required:
    type: boolean
    description: "True if age_days >= 90"

  last_used:
    type: datetime (ISO 8601)
    description: "Last usage timestamp"

  health:
    type: enum
    values: [healthy, warning, critical, compromised]
    description: "Key health status"

  compromise_indicators:
    type: array
    items:
      - type: string
      examples: ["repeated_failures", "unexpected_ip", "unusual_usage_pattern"]
```

### RotationConfig Structure

```yaml
RotationConfig:
  max_key_age_days:
    type: integer
    default: 90
    description: "Maximum key age before forced rotation"

  rotation_warning_days:
    type: integer
    default: 80
    description: "Days before expiry to trigger rotation warning"

  grace_period_hours:
    type: integer
    default: 24
    description: "Hours to keep old key active during rotation"

  test_new_key:
    type: boolean
    default: true
    description: "Test new key before deactivating old key"

  auto_rotate:
    type: boolean
    default: false
    description: "Automatically rotate keys (requires admin approval)"

  notification_channels:
    type: array
    items:
      - email
      - slack
      - pagerduty
    description: "Channels to notify on rotation events"
```

## Configuration

### API Key Configuration (YAML)

```yaml
# config/api_key_config.yaml

api_key:
  # Storage provider: env_var, encrypted_file, vault
  storage_provider: "env_var"

  # Environment variable configuration (if storage_provider = env_var)
  env_var:
    # Environment variable name for API key
    key_name: "TRADESTATION_API_KEY"

    # Validate environment on startup
    validate_environment: true

    # Expected environment (development, staging, production)
    expected_environment: "production"

  # Encrypted file configuration (if storage_provider = encrypted_file)
  encrypted_file:
    file_path: "${HOME}/.simple-risk-manager/secure/api_key.enc"
    file_permissions: "0600"
    encryption_algorithm: "AES-256-GCM"

    # Key derivation (same as TOKEN_STORAGE_SECURITY_SPEC.md)
    key_derivation:
      function: "PBKDF2-HMAC-SHA256"
      iterations: 310000
      salt_length: 32

    # Master secret for encryption
    master_secret_env_var: "API_KEY_MASTER_SECRET"

  # Vault configuration (if storage_provider = vault)
  vault:
    provider: "hashicorp_vault"
    url: "https://vault.example.com:8200"
    token_env_var: "VAULT_TOKEN"
    secret_path: "secret/simple-risk-manager/api-key"

  # Key validation
  validation:
    min_length: 32
    max_length: 256
    min_entropy_bits: 128
    validate_format: true
    test_authentication: true  # Test key with real API call

  # Key rotation
  rotation:
    max_age_days: 90
    warning_age_days: 80
    grace_period_hours: 24
    auto_rotate: false
    require_admin_approval: true

    # Notification channels
    notifications:
      email:
        enabled: true
        recipients: ["admin@example.com", "security@example.com"]
      slack:
        enabled: true
        webhook_url_env_var: "SLACK_WEBHOOK_URL"
        channel: "#security-alerts"

  # Compromise detection
  compromise_detection:
    enabled: true

    # Failure thresholds
    max_consecutive_failures: 5
    failure_window_minutes: 5

    # Anomaly detection
    unusual_usage_multiplier: 3.0  # Alert if usage > 3x average

    # IP address monitoring (optional)
    monitor_ip_addresses: false
    expected_ip_ranges: []  # e.g., ["10.0.0.0/8", "192.168.1.0/24"]

    # Response actions
    actions:
      alert_security_team: true
      temporary_lockdown: true
      lockdown_duration_minutes: 30
      require_manual_unlock: true

  # Audit logging
  audit:
    enabled: true
    log_file: "${HOME}/.simple-risk-manager/logs/api_key_audit.log"
    log_permissions: "0600"

    # Events to log
    log_events:
      - "key_loaded"
      - "key_used"
      - "key_rotated"
      - "key_revoked"
      - "auth_failure"
      - "compromise_detected"
      - "lockdown_triggered"

    # Sanitize keys in logs (CRITICAL)
    sanitize_keys: true  # NEVER log plaintext keys
```

### Environment Variables

```bash
# .env (NEVER commit this file)

# ============================================
# PRODUCTION ENVIRONMENT
# ============================================

# TradeStation API Key (CRITICAL: Keep secret)
# Obtain from: https://developer.tradestation.com/
TRADESTATION_API_KEY=your_production_api_key_here

# Environment identifier
API_KEY_ENVIRONMENT=production

# Optional: Master secret for encrypted file storage
# Generate with: openssl rand -base64 32
API_KEY_MASTER_SECRET=your_base64_encoded_secret_here

# Optional: Vault configuration
VAULT_TOKEN=your_vault_token
VAULT_ADDR=https://vault.example.com:8200

# Optional: Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# ============================================
# SECURITY SETTINGS
# ============================================

# Maximum key age (days)
API_KEY_MAX_AGE_DAYS=90

# Enable compromise detection
API_KEY_COMPROMISE_DETECTION=true

# Enable audit logging
API_KEY_AUDIT_ENABLED=true
```

### Generating API Key

```bash
# Step 1: Register for TradeStation API account
# Visit: https://developer.tradestation.com/

# Step 2: Create new application
# Application Type: Server-side
# Redirect URI: Not applicable for server-side

# Step 3: Obtain API Key
# Copy API Key from developer portal

# Step 4: Store API Key securely
echo "TRADESTATION_API_KEY=your_api_key_here" >> .env
chmod 0600 .env

# Step 5: Validate API Key
# Test authentication:
curl -X POST "https://sim-api.tradestation.com/v3/authorize" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=your_api_key_here"

# Step 6: Document key creation date
echo "# API Key Created: $(date -Iseconds)" >> .env
echo "# API Key Expires: $(date -d '+90 days' -Iseconds)" >> .env
```

## Security Considerations

### S-001: Never Commit API Keys to Version Control

**Prevention Strategies:**

1. **.gitignore Configuration:**
```bash
# .gitignore
.env
.env.*
*.key
*.secret
*credentials*
api_key.enc
```

2. **Pre-commit Hook:**
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Scan for potential API keys in staged files
if git diff --cached | grep -E "(TRADESTATION_API_KEY|api_key.*=)"; then
  echo "ERROR: API key detected in staged files!"
  echo "Remove API key before committing."
  exit 1
fi
```

3. **GitHub Secret Scanning:**
- Enable GitHub secret scanning for repository
- Configure custom patterns for TradeStation API keys
- Set up alerts for secret detection

### S-002: Environment Isolation

**Requirements:**
- Production keys MUST NEVER be used in development
- Development keys MUST NEVER access production accounts
- Each environment MUST have separate API keys

**Validation:**
```python
def validate_environment(api_key: str, expected_env: str) -> bool:
    """Validate API key matches expected environment."""
    # Check key metadata or prefix
    key_env = get_key_environment(api_key)

    if key_env != expected_env:
        raise EnvironmentMismatchError(
            f"Key belongs to {key_env} environment, "
            f"but running in {expected_env}"
        )
    return True
```

### S-003: Key Entropy Validation

**Requirement:** API keys must have sufficient randomness

**Implementation:**
```python
import math
from collections import Counter

def calculate_entropy(key: str) -> float:
    """Calculate Shannon entropy of API key."""
    if not key:
        return 0.0

    # Count character frequencies
    char_counts = Counter(key)
    key_length = len(key)

    # Calculate Shannon entropy
    entropy = 0.0
    for count in char_counts.values():
        probability = count / key_length
        entropy -= probability * math.log2(probability)

    return entropy

def validate_key_entropy(key: str, min_bits: int = 128) -> bool:
    """Validate key has sufficient entropy."""
    entropy = calculate_entropy(key)
    entropy_bits = entropy * len(key)

    if entropy_bits < min_bits:
        raise InsufficientEntropyError(
            f"API key has {entropy_bits:.1f} bits of entropy, "
            f"minimum {min_bits} bits required"
        )
    return True
```

### S-004: Key Sanitization in Logs

**Critical:** Never log API keys in plaintext

**Implementation:**
```python
def sanitize_api_key(key: str) -> str:
    """Sanitize API key for logging."""
    if not key or len(key) < 10:
        return "[REDACTED]"

    # Show first 4 and last 4 characters only
    return f"{key[:4]}...{key[-4:]}"

# Example usage:
logger.info(f"API key loaded: {sanitize_api_key(api_key)}")
# Output: "API key loaded: ts12...xy89"
```

### S-005: Secure Key Comparison

**Requirement:** Use constant-time comparison to prevent timing attacks

**Implementation:**
```python
import hmac

def validate_api_key(provided_key: str, expected_key: str) -> bool:
    """Validate API key using constant-time comparison."""
    return hmac.compare_digest(
        provided_key.encode(),
        expected_key.encode()
    )
```

### S-006: Compromise Response Procedures

**Immediate Actions on Compromise Detection:**

1. **Automatic Lockdown:**
   - Disable API key immediately
   - Block all authentication attempts
   - Send critical alerts to security team

2. **Investigation:**
   - Review audit logs for suspicious activity
   - Identify source of compromise
   - Assess impact and data exposure

3. **Recovery:**
   - Generate new API key
   - Update all systems with new key
   - Test authentication with new key
   - Monitor for continued suspicious activity

4. **Post-Incident:**
   - Document incident timeline
   - Update security procedures
   - Conduct root cause analysis
   - Implement additional safeguards

## Error Handling

### Error Scenarios

**E-001: API Key Not Found**
```
Scenario: TRADESTATION_API_KEY environment variable not set
Response:
  1. Log critical error: "API key not configured"
  2. Display error message with setup instructions
  3. Halt application startup
  4. Exit with error code 1
```

**E-002: API Key Format Invalid**
```
Scenario: API key fails format validation
Response:
  1. Log error: "Invalid API key format"
  2. Check key length (min 32 characters)
  3. Check key entropy (min 128 bits)
  4. Display error with validation failures
  5. Halt application startup
```

**E-003: API Key Authentication Fails**
```
Scenario: API key rejected by TradeStation API
Response:
  1. Log error: "API key authentication failed"
  2. Increment failure counter
  3. If failure_count > 5: Trigger compromise detection
  4. Display error: "API key invalid or expired"
  5. Suggest key rotation procedure
```

**E-004: API Key Expired**
```
Scenario: API key age > 90 days
Response:
  1. Log warning: "API key expired"
  2. Send notification to administrators
  3. If auto_rotate enabled: Initiate rotation
  4. If auto_rotate disabled: Halt startup, require manual rotation
```

**E-005: Environment Mismatch**
```
Scenario: Production key used in development environment
Response:
  1. Log critical error: "Environment mismatch detected"
  2. Display: "Production key cannot be used in development"
  3. Halt application startup
  4. Alert security team (potential security violation)
```

**E-006: Compromise Detected**
```
Scenario: 10 authentication failures in 5 minutes
Response:
  1. Log critical alert: "Possible API key compromise"
  2. Trigger automatic lockdown (if enabled)
  3. Send alerts to security team (email, Slack, PagerDuty)
  4. Disable API key for lockdown_duration_minutes
  5. Require manual unlock by administrator
```

### Error Codes

| Error Code | Description | Recovery Action |
|------------|-------------|-----------------|
| KEY_NOT_FOUND | API key not configured | Set TRADESTATION_API_KEY |
| KEY_INVALID_FORMAT | Key format validation failed | Check key from provider |
| KEY_AUTH_FAILED | Authentication failed | Verify key is active |
| KEY_EXPIRED | Key age exceeds maximum | Rotate key |
| KEY_COMPROMISED | Compromise detected | Rotate key immediately |
| ENV_MISMATCH | Wrong environment | Use correct key for environment |
| INSUFFICIENT_ENTROPY | Key lacks randomness | Obtain new key from provider |

## Implementation Checklist

### Phase 1: Core Key Management
- [ ] Create APIKeyManager class
- [ ] Implement environment variable key provider
- [ ] Implement key format validation
- [ ] Implement key entropy validation
- [ ] Add unit tests for key loading

### Phase 2: Encrypted File Storage
- [ ] Implement encrypted file key provider
- [ ] Reuse encryption logic from TOKEN_STORAGE_SECURITY_SPEC.md
- [ ] Implement file permissions validation
- [ ] Add unit tests for encrypted storage

### Phase 3: Key Rotation
- [ ] Implement key rotation workflow
- [ ] Implement grace period handling
- [ ] Implement new key validation
- [ ] Add notification system for rotation events
- [ ] Add unit tests for rotation logic

### Phase 4: Compromise Detection
- [ ] Implement authentication failure tracking
- [ ] Implement anomaly detection algorithms
- [ ] Implement automatic lockdown mechanism
- [ ] Add alerting for compromise indicators
- [ ] Add unit tests for detection logic

### Phase 5: Audit Logging
- [ ] Implement audit log writer
- [ ] Implement key sanitization for logs
- [ ] Implement audit trail for key lifecycle
- [ ] Add log rotation and retention
- [ ] Add unit tests for audit logging

### Phase 6: Integration
- [ ] Integrate with AuthService
- [ ] Integrate with TokenManager
- [ ] Add configuration file parsing
- [ ] Add command-line tools for key management
- [ ] Add integration tests

### Phase 7: Monitoring and Alerting
- [ ] Add metrics for key usage
- [ ] Add metrics for authentication success/failure
- [ ] Add alerts for key expiry
- [ ] Add alerts for compromise detection
- [ ] Add dashboard for key health monitoring

## Validation Criteria

### Security Validation

**SV-1: Key Not in Version Control**
```
Test: Search git history for API keys
Expected: No API keys found in commits
Validation: git log -p | grep -i "api_key" should return no sensitive data
```

**SV-2: Key Not Logged**
```
Test: Review all log files after API key usage
Expected: No plaintext API keys in logs
Validation: grep -r "TRADESTATION_API_KEY\|ts[a-z0-9]{32,}" logs/ should return 0 matches
```

**SV-3: Environment Isolation**
```
Test: Attempt to use production key in development
Expected: Application refuses to start, logs environment mismatch
Validation: Check error message indicates environment violation
```

**SV-4: Compromise Detection Works**
```
Test: Trigger 10 authentication failures in 5 minutes
Expected: Automatic lockdown triggered, alerts sent
Validation: Key disabled, security team notified
```

**SV-5: Key Rotation Successful**
```
Test: Rotate API key with new key
Expected: New key validated, old key deactivated after grace period
Validation: Authentication works with new key, fails with old key
```

### Functional Validation

**FV-1: Key Loads Successfully**
```
Test: Start application with valid API key
Expected: Key loads, authentication succeeds
Validation: Check logs for "API key loaded" message
```

**FV-2: Key Validation Detects Issues**
```
Test: Use API key with length < 32 characters
Expected: Validation fails, startup halted
Validation: Check error message indicates insufficient length
```

**FV-3: Key Expiry Detected**
```
Test: Use API key with age = 91 days
Expected: System detects expiry, requires rotation
Validation: Check logs for "API key expired" warning
```

## References

### Related Specifications
- **TOKEN_STORAGE_SECURITY_SPEC.md**: Encryption methods for key storage
- **TOKEN_REFRESH_STRATEGY_SPEC.md**: Integration with authentication flow
- **ADMIN_PASSWORD_SPEC.md** (if exists): Similar key management patterns

### Error Analysis References
- **ERRORS_AND_WARNINGS_CONSOLIDATED.md**:
  - Line 268-274: SEC-API-003 (API Key Storage Best Practices)

### TradeStation Documentation
- Developer Portal: https://developer.tradestation.com/
- API Key Management: https://api.tradestation.com/docs/fundamentals/authentication/
- Security Best Practices: https://api.tradestation.com/docs/fundamentals/security/

### Security Standards
- **NIST SP 800-57**: Key Management Recommendations
- **PCI-DSS**: Payment Card Industry Data Security Standard (Key Management)
- **OWASP**: Cryptographic Storage Cheat Sheet
- **ISO 27001**: Information Security Management

---

**Document Status:** DRAFT v1.0
**Last Updated:** 2025-10-22
**Next Review:** After security audit
**Approval Required:** Security Team, Compliance Team
