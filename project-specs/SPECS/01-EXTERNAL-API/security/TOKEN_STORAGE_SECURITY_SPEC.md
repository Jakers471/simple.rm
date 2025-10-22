# Token Storage Security Specification

**doc_id:** SEC-002
**version:** 1.0
**status:** DRAFT
**priority:** HIGH
**addresses:** GAP-API-002 from ERRORS_AND_WARNINGS_CONSOLIDATED.md

## Overview

This specification defines secure token storage requirements to prevent token exposure, unauthorized access, and credential compromise. The TradeStation API uses JWT tokens that are valid for 24 hours and provide full account access, making secure storage critical.

## Problem Statement

**From GAP-API-002:**
- No documentation on secure token storage
- No encryption requirements specified
- No guidance on token exposure prevention
- No specification of storage locations and permissions
- Risk of tokens being exposed in logs, memory dumps, or unauthorized access

## Requirements

### Functional Requirements

**FR-1: Encryption at Rest**
- System MUST encrypt tokens using AES-256-GCM before storage
- System MUST use unique encryption keys per deployment
- System MUST derive encryption keys from secure master secret
- System MUST rotate encryption keys on security events

**FR-2: Storage Location**
- System MUST store tokens in encrypted files with restrictive permissions (0600)
- System MUST NOT store tokens in environment variables
- System MUST NOT store tokens in configuration files
- System MUST support memory-only mode (no persistent storage)

**FR-3: Access Control**
- Token files MUST have permissions: owner read/write only (chmod 0600)
- Token storage directory MUST have permissions: owner access only (chmod 0700)
- System MUST validate permissions on startup
- System MUST reject operation if permissions are too permissive

**FR-4: Token Exposure Prevention**
- System MUST NOT log tokens in plaintext
- System MUST sanitize tokens in error messages
- System MUST redact tokens in debug output
- System MUST clear tokens from memory after use

**FR-5: Multi-Environment Support**
- System MUST support different storage backends: file, memory-only, secure vault
- System MUST allow per-environment storage configuration
- Development environments MAY use memory-only storage
- Production environments MUST use encrypted file or secure vault storage

### Non-Functional Requirements

**NFR-1: Performance**
- Token encryption/decryption MUST complete in < 10ms (P95)
- Token read from storage MUST complete in < 50ms (P95)
- Encryption operations MUST NOT block other operations

**NFR-2: Security**
- Encryption MUST use FIPS 140-2 validated algorithms
- Keys MUST be derived using PBKDF2 with minimum 100,000 iterations
- Keys MUST have minimum 256-bit entropy
- System MUST support Hardware Security Module (HSM) integration

**NFR-3: Reliability**
- Encrypted token storage MUST survive system restarts
- Corrupted token files MUST NOT crash application
- System MUST fall back to re-authentication on storage failure

**NFR-4: Auditability**
- System MUST log all token storage access attempts
- System MUST log all decryption failures
- System MUST maintain audit trail of token lifecycle events

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    TokenStorageManager                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SecureStorage Interface                             │   │
│  │  - store(token: str) -> None                         │   │
│  │  - retrieve() -> str                                 │   │
│  │  - delete() -> None                                  │   │
│  │  - validate_permissions() -> bool                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  EncryptionProvider                                  │   │
│  │  - encrypt(plaintext: str) -> bytes                  │   │
│  │  - decrypt(ciphertext: bytes) -> str                 │   │
│  │  - derive_key(secret: str, salt: bytes) -> bytes     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ FileStorage  │ │ MemoryStorage│ │ VaultStorage │
  │ (encrypted   │ │ (no persist) │ │ (HashiCorp   │
  │  file)       │ │              │ │  Vault/AWS)  │
  └──────────────┘ └──────────────┘ └──────────────┘
```

### Encryption Flow Diagram

```
     ┌──────────────┐
     │  JWT Token   │
     │  (plaintext) │
     └──────┬───────┘
            │
            ▼
     ┌──────────────────────┐
     │  Generate Random     │
     │  Initialization      │
     │  Vector (IV)         │
     │  - 96 bits           │
     └──────┬───────────────┘
            │
            ▼
     ┌──────────────────────┐
     │  Derive Encryption   │
     │  Key from Master     │
     │  Secret (PBKDF2)     │
     │  - 256-bit key       │
     │  - 100k iterations   │
     └──────┬───────────────┘
            │
            ▼
     ┌──────────────────────┐
     │  AES-256-GCM         │
     │  Encryption          │
     │  - Authenticated     │
     │  - Tag: 128 bits     │
     └──────┬───────────────┘
            │
            ▼
     ┌──────────────────────┐
     │  Encrypted Blob      │
     │  Format:             │
     │  [IV][Ciphertext]    │
     │  [Auth Tag]          │
     └──────┬───────────────┘
            │
            ▼
     ┌──────────────────────┐
     │  Write to File       │
     │  - Permissions: 0600 │
     │  - Owner: app user   │
     └──────────────────────┘
```

### Storage Hierarchy

```
$HOME/.simple-risk-manager/
│
├── secure/                     (chmod 0700)
│   ├── token.enc              (chmod 0600) - Encrypted token
│   ├── token.salt             (chmod 0600) - Random salt for key derivation
│   └── token.metadata         (chmod 0600) - Token expiry, issue time
│
├── config/                    (chmod 0755)
│   └── storage_config.yaml    (chmod 0644) - Storage configuration
│
└── logs/                      (chmod 0700)
    └── token_audit.log        (chmod 0600) - Token access audit log
```

## Data Structures

### EncryptedTokenBlob

```yaml
EncryptedTokenBlob:
  version:
    type: integer
    value: 1
    description: "Blob format version for future compatibility"

  algorithm:
    type: string
    value: "AES-256-GCM"
    description: "Encryption algorithm identifier"

  iv:
    type: bytes
    length: 96 bits (12 bytes)
    description: "Initialization vector (random, unique per encryption)"

  ciphertext:
    type: bytes
    description: "Encrypted JWT token"

  auth_tag:
    type: bytes
    length: 128 bits (16 bytes)
    description: "GCM authentication tag for integrity verification"

  encrypted_at:
    type: datetime (ISO 8601)
    example: "2025-10-22T10:30:00Z"
    description: "Timestamp when encryption occurred"

# Binary format (total size ~512 bytes for typical JWT):
# [1 byte: version][3 bytes: algorithm_id][12 bytes: IV]
# [N bytes: ciphertext][16 bytes: auth_tag][8 bytes: timestamp]
```

### TokenMetadata

```yaml
TokenMetadata:
  token_id:
    type: string (UUID)
    example: "550e8400-e29b-41d4-a716-446655440000"
    description: "Unique identifier for token lifecycle"

  issued_at:
    type: datetime (ISO 8601)
    description: "Token issue timestamp"

  expires_at:
    type: datetime (ISO 8601)
    description: "Token expiration timestamp"

  storage_location:
    type: string
    example: "/home/appuser/.simple-risk-manager/secure/token.enc"
    description: "Path to encrypted token file"

  encryption_algorithm:
    type: string
    value: "AES-256-GCM"
    description: "Algorithm used for encryption"

  last_accessed:
    type: datetime (ISO 8601)
    description: "Last time token was retrieved from storage"

  access_count:
    type: integer
    description: "Number of times token has been accessed"
```

### KeyDerivationConfig

```yaml
KeyDerivationConfig:
  algorithm:
    type: string
    value: "PBKDF2-HMAC-SHA256"
    description: "Key derivation function"

  iterations:
    type: integer
    min: 100000
    default: 310000  # OWASP recommended as of 2024
    description: "PBKDF2 iteration count"

  salt_length:
    type: integer
    value: 32
    description: "Salt length in bytes"

  key_length:
    type: integer
    value: 32
    description: "Derived key length in bytes (256 bits)"
```

## Configuration

### Storage Configuration (YAML)

```yaml
# config/storage_config.yaml

token_storage:
  # Storage backend: file, memory, vault
  backend: "file"

  # File storage settings (if backend = file)
  file:
    storage_dir: "${HOME}/.simple-risk-manager/secure"
    token_filename: "token.enc"
    metadata_filename: "token.metadata"
    salt_filename: "token.salt"

    # File permissions (octal)
    dir_permissions: "0700"
    file_permissions: "0600"

    # Validate permissions on startup
    validate_permissions: true

    # Reject operation if permissions are wrong
    strict_permissions: true

  # Memory storage settings (if backend = memory)
  memory:
    # No persistent storage, token lost on restart
    persist_on_shutdown: false

    # Clear memory on exit
    secure_clear: true

  # Vault storage settings (if backend = vault)
  vault:
    # HashiCorp Vault or AWS Secrets Manager
    provider: "hashicorp_vault"  # or "aws_secrets_manager"

    # Vault connection
    url: "https://vault.example.com:8200"
    token_env_var: "VAULT_TOKEN"

    # Secret path
    secret_path: "secret/simple-risk-manager/token"

    # TLS verification
    verify_tls: true
    ca_cert_path: "/etc/ssl/certs/vault-ca.crt"

encryption:
  # Encryption algorithm
  algorithm: "AES-256-GCM"

  # Key derivation
  key_derivation:
    function: "PBKDF2-HMAC-SHA256"
    iterations: 310000  # OWASP 2024 recommendation
    salt_length: 32
    key_length: 32

  # Master secret source
  master_secret:
    # Source: env_var, file, vault
    source: "env_var"
    env_var_name: "TOKEN_MASTER_SECRET"

    # Alternative: read from file
    # source: "file"
    # file_path: "/etc/simple-risk-manager/master.key"

    # Validate secret strength
    min_entropy_bits: 256

  # IV generation
  iv_length: 12  # 96 bits for GCM

  # Authentication tag
  auth_tag_length: 16  # 128 bits

audit:
  # Audit logging
  enabled: true
  log_file: "${HOME}/.simple-risk-manager/logs/token_audit.log"
  log_permissions: "0600"

  # Events to log
  log_events:
    - "token_stored"
    - "token_retrieved"
    - "token_deleted"
    - "encryption_failed"
    - "decryption_failed"
    - "permission_violation"
    - "key_derived"

  # Include metadata in logs (sanitize sensitive data)
  include_metadata: true
  sanitize_tokens: true  # CRITICAL: never log plaintext tokens
```

### Environment Variables

```bash
# .env (NEVER commit this file)

# Master secret for encryption key derivation
# CRITICAL: Generate with: openssl rand -base64 32
TOKEN_MASTER_SECRET=your_base64_encoded_256bit_secret_here

# Optional: Override storage location
TOKEN_STORAGE_DIR=/custom/path/to/secure/storage

# Optional: Override storage backend
TOKEN_STORAGE_BACKEND=file  # file, memory, vault

# Optional: Vault configuration (if using vault backend)
VAULT_TOKEN=your_vault_token
VAULT_ADDR=https://vault.example.com:8200

# Optional: Enable debug logging (NEVER in production)
TOKEN_STORAGE_DEBUG=false
```

### Generating Master Secret

```bash
# Generate 256-bit (32-byte) random secret
openssl rand -base64 32

# Example output:
# 7x9K2LpQz3vN8mR1wY4tE6sD5fG7hJ9kL0pM3nB2vC8a=

# Store in .env file:
echo "TOKEN_MASTER_SECRET=7x9K2LpQz3vN8mR1wY4tE6sD5fG7hJ9kL0pM3nB2vC8a=" >> .env

# Set file permissions
chmod 0600 .env
```

## Security Considerations

### S-001: Encryption Algorithm

**Requirement:** AES-256-GCM (Galois/Counter Mode)

**Rationale:**
- FIPS 140-2 validated
- Authenticated encryption (prevents tampering)
- 128-bit authentication tag provides integrity verification
- Recommended by NIST for sensitive data

**Implementation:**
```python
# Use cryptography library (Python example)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Encrypt
aesgcm = AESGCM(encryption_key)  # 256-bit key
iv = os.urandom(12)  # 96-bit IV
ciphertext = aesgcm.encrypt(iv, plaintext.encode(), None)

# Decrypt (raises InvalidTag on tampering)
plaintext = aesgcm.decrypt(iv, ciphertext, None)
```

### S-002: Key Derivation

**Requirement:** PBKDF2-HMAC-SHA256 with 310,000 iterations

**Rationale:**
- OWASP recommendation as of 2024
- Resistant to brute force attacks
- Supported by all major crypto libraries
- Balances security and performance

**Implementation:**
```python
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Derive encryption key from master secret
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,  # 256 bits
    salt=salt,  # 32-byte random salt
    iterations=310000,
)
encryption_key = kdf.derive(master_secret.encode())
```

### S-003: File Permissions

**Critical Requirements:**

```bash
# Storage directory: owner access only
chmod 0700 ~/.simple-risk-manager/secure/

# Token files: owner read/write only
chmod 0600 ~/.simple-risk-manager/secure/token.enc
chmod 0600 ~/.simple-risk-manager/secure/token.salt
chmod 0600 ~/.simple-risk-manager/secure/token.metadata

# Audit log: owner read/write only
chmod 0600 ~/.simple-risk-manager/logs/token_audit.log
```

**Validation on Startup:**
```python
import stat
import os

def validate_permissions(filepath, expected_mode):
    actual_mode = stat.S_IMODE(os.stat(filepath).st_mode)
    if actual_mode != expected_mode:
        raise SecurityError(
            f"Insecure permissions on {filepath}: "
            f"expected {oct(expected_mode)}, got {oct(actual_mode)}"
        )
```

### S-004: Token Sanitization in Logs

**Critical:** Never log tokens in plaintext

**Implementation:**
```python
def sanitize_token(token: str) -> str:
    """Sanitize token for logging."""
    if not token or len(token) < 10:
        return "[REDACTED]"

    # Show first 4 and last 4 characters only
    return f"{token[:4]}...{token[-4:]}"

# Example usage in logs:
logger.info(f"Token stored: {sanitize_token(token)}")
# Output: "Token stored: eyJh...fG7Q"
```

### S-005: Memory Security

**Requirements:**
- Clear sensitive data from memory after use
- Avoid string copies (use bytes)
- Use secure comparison for authentication tags

**Implementation:**
```python
import ctypes

def secure_zero_memory(data: bytearray):
    """Securely zero out memory."""
    ctypes.memset(id(data), 0, len(data))

# Usage:
token_bytes = bytearray(token.encode())
try:
    # Use token_bytes
    pass
finally:
    secure_zero_memory(token_bytes)
```

### S-006: Secure Comparison

**Requirement:** Use constant-time comparison to prevent timing attacks

**Implementation:**
```python
import hmac

def secure_compare(a: bytes, b: bytes) -> bool:
    """Constant-time comparison."""
    return hmac.compare_digest(a, b)

# Usage:
if secure_compare(computed_auth_tag, stored_auth_tag):
    # Authentication successful
    pass
```

### S-007: Rotation and Revocation

**Master Secret Rotation Process:**
1. Generate new master secret
2. Re-encrypt existing token with new secret
3. Store new salt for new key derivation
4. Delete old encrypted blob
5. Update TOKEN_MASTER_SECRET environment variable
6. Restart application

**Token Revocation:**
- Delete encrypted token file
- Clear token from memory
- Force re-authentication
- Log revocation event in audit log

## Error Handling

### Error Scenarios

**E-001: Decryption Failure**
```
Scenario: Encrypted token is corrupted or tampered with
Response:
  1. Log error: "Token decryption failed - authentication tag mismatch"
  2. Delete corrupted token file
  3. Trigger re-authentication
  4. Alert security team if repeated failures
```

**E-002: Insecure Permissions Detected**
```
Scenario: Token file has permissions 0644 (world-readable)
Response:
  1. Log critical error: "Insecure permissions on token file"
  2. If strict_permissions=true: Halt application startup
  3. If strict_permissions=false: Attempt to fix permissions with chmod
  4. Alert administrator immediately
```

**E-003: Master Secret Not Found**
```
Scenario: TOKEN_MASTER_SECRET environment variable not set
Response:
  1. Log critical error: "Master secret not configured"
  2. Halt application startup
  3. Display error message with instructions
  4. Do NOT fall back to insecure storage
```

**E-004: Storage Directory Not Accessible**
```
Scenario: ~/.simple-risk-manager/secure/ doesn't exist or not writable
Response:
  1. Attempt to create directory with permissions 0700
  2. If creation fails: Log error and halt startup
  3. If created successfully: Log info and continue
```

**E-005: Key Derivation Failure**
```
Scenario: PBKDF2 key derivation fails
Response:
  1. Log error with exception details
  2. Check if master secret is corrupted
  3. Halt application startup
  4. Require administrator intervention
```

**E-006: Vault Connection Failure**
```
Scenario: Cannot connect to HashiCorp Vault
Response:
  1. Log error: "Vault connection failed"
  2. Retry with exponential backoff (3 attempts)
  3. If all retries fail: Fall back to re-authentication
  4. Alert operations team
```

### Error Codes

| Error Code | Description | Recovery Action |
|------------|-------------|-----------------|
| DECRYPTION_FAILED | Token decryption failed | Delete token, re-authenticate |
| INSECURE_PERMISSIONS | File permissions too permissive | Fix permissions or halt |
| MASTER_SECRET_MISSING | Master secret not configured | Require admin configuration |
| STORAGE_DIR_INACCESSIBLE | Cannot access storage directory | Create directory or halt |
| KEY_DERIVATION_FAILED | PBKDF2 key derivation failed | Require admin intervention |
| VAULT_CONNECTION_FAILED | Vault connection failed | Retry or fall back to re-auth |
| AUTH_TAG_MISMATCH | Authentication tag verification failed | Delete token, re-authenticate |
| CORRUPTED_BLOB | Encrypted blob format invalid | Delete blob, re-authenticate |

## Implementation Checklist

### Phase 1: Core Encryption
- [ ] Implement EncryptionProvider with AES-256-GCM
- [ ] Implement PBKDF2 key derivation with 310,000 iterations
- [ ] Implement secure random IV generation
- [ ] Implement authentication tag verification
- [ ] Add unit tests for encryption/decryption

### Phase 2: File Storage Backend
- [ ] Implement FileStorage class with SecureStorage interface
- [ ] Implement storage directory creation with chmod 0700
- [ ] Implement file permissions validation on startup
- [ ] Implement encrypted blob serialization/deserialization
- [ ] Add unit tests for file operations

### Phase 3: Memory Storage Backend
- [ ] Implement MemoryStorage class (no persistence)
- [ ] Implement secure memory clearing on shutdown
- [ ] Add configuration to enable memory-only mode
- [ ] Add unit tests for memory operations

### Phase 4: Vault Storage Backend (Optional)
- [ ] Implement VaultStorage class for HashiCorp Vault
- [ ] Implement Vault connection and authentication
- [ ] Implement secret read/write operations
- [ ] Add integration tests with Vault instance

### Phase 5: Security Features
- [ ] Implement token sanitization for logging
- [ ] Implement secure memory zeroing
- [ ] Implement constant-time comparison for auth tags
- [ ] Implement master secret validation (min entropy check)
- [ ] Add security audit logging

### Phase 6: Configuration and Integration
- [ ] Implement storage_config.yaml parsing
- [ ] Implement environment variable configuration
- [ ] Integrate with TokenManager (from TOKEN_REFRESH_STRATEGY_SPEC.md)
- [ ] Add storage backend selection logic

### Phase 7: Error Handling and Recovery
- [ ] Implement all error scenarios (E-001 through E-006)
- [ ] Implement error code mapping
- [ ] Implement automatic recovery where possible
- [ ] Add alerting for critical security events

### Phase 8: Testing and Validation
- [ ] Unit tests for all encryption operations
- [ ] Unit tests for all storage backends
- [ ] Integration tests for token lifecycle
- [ ] Security tests: tampering detection, permission validation
- [ ] Performance tests: encryption/decryption latency
- [ ] Penetration testing: attempt to extract tokens

## Validation Criteria

### Security Validation

**SV-1: Encryption Strength**
```
Test: Attempt to decrypt token without correct key
Expected: Decryption fails with authentication tag mismatch
Validation: Verify InvalidTag exception is raised
```

**SV-2: Tampering Detection**
```
Test: Modify single byte in encrypted blob
Expected: Decryption fails due to authentication tag mismatch
Validation: Verify decryption fails immediately, token is deleted
```

**SV-3: Insecure Permissions Rejected**
```
Test: Set token file permissions to 0644 (world-readable)
Expected: Application refuses to start if strict_permissions=true
Validation: Check application exits with error code 1
```

**SV-4: Token Not Logged**
```
Test: Review all log files after token operations
Expected: No plaintext tokens found in logs
Validation: grep for JWT pattern, should return no matches
```

**SV-5: Master Secret Required**
```
Test: Start application without TOKEN_MASTER_SECRET
Expected: Application refuses to start
Validation: Check error message indicates missing master secret
```

### Performance Validation

**PV-1: Encryption Latency**
```
Metric: Encryption duration (P95)
Target: < 10ms
Measurement: Time encrypt() function call
```

**PV-2: Decryption Latency**
```
Metric: Decryption duration (P95)
Target: < 10ms
Measurement: Time decrypt() function call
```

**PV-3: Key Derivation Latency**
```
Metric: PBKDF2 key derivation duration
Target: < 500ms (acceptable for startup/re-auth)
Measurement: Time derive_key() function call
```

### Reliability Validation

**RV-1: Persistent Storage**
```
Test: Store token, restart application, retrieve token
Expected: Token successfully retrieved and decrypted
Validation: Compare retrieved token with original
```

**RV-2: Corruption Recovery**
```
Test: Corrupt encrypted token file, attempt retrieval
Expected: Decryption fails, system triggers re-authentication
Validation: New token stored after re-authentication
```

**RV-3: Concurrent Access**
```
Test: Multiple threads attempt to read token simultaneously
Expected: All threads successfully retrieve token
Validation: No race conditions, no decryption errors
```

## References

### Related Specifications
- **TOKEN_REFRESH_STRATEGY_SPEC.md**: Integration point for token refresh
- **API_KEY_MANAGEMENT_SPEC.md**: Similar security requirements for API keys
- **SIGNALR_JWT_FIX_SPEC.md**: Token usage in SignalR connections

### Error Analysis References
- **ERRORS_AND_WARNINGS_CONSOLIDATED.md**:
  - Line 232-238: GAP-API-002 (No Token Storage Security Guidelines)

### Security Standards
- **NIST SP 800-38D**: AES-GCM mode specification
- **NIST SP 800-132**: PBKDF2 key derivation specification
- **OWASP**: Password storage cheat sheet (PBKDF2 iterations)
- **FIPS 140-2**: Cryptographic module validation

### Cryptography Libraries
- **Python**: `cryptography` library (PyPI)
- **Node.js**: `crypto` module (built-in)
- **Go**: `crypto/aes`, `crypto/cipher` packages
- **Rust**: `aes-gcm`, `ring` crates

---

**Document Status:** DRAFT v1.0
**Last Updated:** 2025-10-22
**Next Review:** After security audit
**Approval Required:** Security Team, Compliance Team
