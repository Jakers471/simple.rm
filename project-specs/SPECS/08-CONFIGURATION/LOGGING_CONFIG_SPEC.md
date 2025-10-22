---
doc_id: CONFIG-004
title: Logging Configuration Specification
version: 1.0
last_updated: 2025-10-21
created_by: Configuration Auditor Agent
---

# Logging Configuration Specification

**Purpose:** Complete specification for logging system configuration

**File Location:** `config/logging.yaml`

**Format:** YAML

---

## 🎯 Overview

The `logging.yaml` file controls all logging behavior for the Risk Manager daemon including:
- Log levels and verbosity
- Log file locations and rotation
- Performance monitoring
- Security and sensitive data masking
- Development vs production settings

**Key Features:**
- Multiple specialized log files
- Automatic log rotation
- JSON structured logging option
- Performance tracking
- Security-aware sensitive data masking

---

## 📋 Complete Schema

```yaml
# logging.yaml - Risk Manager Logging Configuration

# Log directory (relative to project root or absolute path)
log_dir: "logs"

# Global log level
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
log_level: "INFO"

# Enable console output (useful for development)
enable_console: true

# Enable JSON structured logging
# false = human-readable logs (development)
# true = structured logs (production)
enable_json: true

# Log rotation settings
rotation:
  # Maximum size per log file (in MB)
  max_mb: 10

  # Number of backup files to keep (days)
  backup_count: 7

  # Compress old log files
  compress: true

# Specialized log files
log_files:
  daemon:
    enabled: true
    filename: "daemon.log"
    level: "DEBUG"
    description: "All daemon activity and operations"

  enforcement:
    enabled: true
    filename: "enforcement.log"
    level: "INFO"
    description: "Rule breaches and enforcement actions"

  api:
    enabled: true
    filename: "api.log"
    level: "DEBUG"
    description: "TopstepX API calls and responses"

  error:
    enabled: true
    filename: "error.log"
    level: "ERROR"
    description: "Errors and exceptions only"

# Performance logging
performance:
  enabled: true
  # Log operations slower than threshold (milliseconds)
  threshold_ms: 100
  # Include performance metrics in logs
  include_metrics: true

# Context tracking
context:
  # Enable correlation IDs
  correlation_ids: true
  # Auto-generate correlation IDs if not provided
  auto_generate: true

# Security
security:
  # Mask sensitive data in logs
  mask_sensitive: true
  # Additional patterns to mask (regex)
  additional_patterns: []
  # Mask email addresses
  mask_emails: true

# Development settings (disable in production)
development:
  # Use colored console output
  colored_console: true
  # Include full stack traces
  full_traces: true
  # Log to console as well as files
  console_duplicate: true
```

---

## 🔧 Field Specifications

### **log_dir** (string, required)

Directory where log files are stored.

**Default:** `"logs"`
**Format:** Relative path (from project root) or absolute path
**Example:** `"logs"` or `"/var/log/risk-manager"`

**Validation:**
- Must be valid directory path
- Directory must be writable
- Created automatically if doesn't exist

**Recommendations:**
- Use relative path for portability
- Ensure sufficient disk space
- Consider logrotate or similar for long-term storage

---

### **log_level** (string, required)

Global logging level controlling verbosity.

**Default:** `"INFO"`
**Options:** `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`

**Level Meanings:**
- `DEBUG`: Everything (very verbose, for development)
- `INFO`: General info + warnings + errors (recommended)
- `WARNING`: Warnings + errors only
- `ERROR`: Errors only
- `CRITICAL`: Critical errors only

**Validation:**
- Must be one of the valid level names
- Case-sensitive

**Note:** Individual log files can override this with their own `level` setting.

---

### **enable_console** (boolean, optional)

Enable logging to console (stdout/stderr).

**Default:** `true`
**Use Cases:**
- `true`: Development, debugging, systemd journal
- `false`: Production with log aggregation tools

**Behavior:**
- If `true`: Logs appear in terminal and files
- If `false`: Logs only written to files

---

### **enable_json** (boolean, optional)

Enable JSON structured logging format.

**Default:** `true`
**Format Comparison:**

**Human-Readable (enable_json: false):**
```
2025-10-21 14:30:45 INFO [daemon] Starting Risk Manager v1.0
2025-10-21 14:30:46 DEBUG [api] Authenticating account 123456
```

**JSON Structured (enable_json: true):**
```json
{"timestamp":"2025-10-21T14:30:45Z","level":"INFO","logger":"daemon","message":"Starting Risk Manager v1.0"}
{"timestamp":"2025-10-21T14:30:46Z","level":"DEBUG","logger":"api","message":"Authenticating account 123456","account_id":123456}
```

**Recommendations:**
- `false`: Development, manual log reading
- `true`: Production, log aggregation (ELK, Splunk, etc.)

---

### **rotation** (object, required)

Log rotation configuration.

#### **max_mb** (integer, required)

Maximum size per log file before rotation.

**Default:** `10`
**Range:** 1-1000 MB
**Example:** `10` = 10 megabytes

**Behavior:**
- When log file reaches `max_mb`, it's rotated
- Old file renamed to `filename.1`, `filename.2`, etc.
- New log file created

#### **backup_count** (integer, required)

Number of rotated log files to keep.

**Default:** `7`
**Range:** 1-365
**Example:** `7` = Keep 7 days of logs

**Behavior:**
- Older backups are deleted
- Effective retention: `max_mb * backup_count` MB per log file

#### **compress** (boolean, optional)

Compress rotated log files.

**Default:** `true`
**Format:** gzip (.gz)

**Benefits:**
- Saves disk space (typically 10:1 compression)
- Automatic decompression when viewed

**Recommendations:**
- `true`: Production (save space)
- `false`: Development (faster, easier viewing)

---

### **log_files** (object, required)

Specialized log file configurations.

Each log file has:
- `enabled` (bool): Enable this log file
- `filename` (string): Log file name (in `log_dir`)
- `level` (string): Minimum log level for this file
- `description` (string): Human-readable description

#### **daemon** (object, required)

All daemon activity and operations.

**Default:**
```yaml
daemon:
  enabled: true
  filename: "daemon.log"
  level: "DEBUG"
```

**Contains:**
- Startup/shutdown messages
- Configuration loading
- State changes
- Module initialization

#### **enforcement** (object, required)

Rule breaches and enforcement actions.

**Default:**
```yaml
enforcement:
  enabled: true
  filename: "enforcement.log"
  level: "INFO"
```

**Contains:**
- Rule breach events
- Enforcement actions (CLOSE_ALL, LOCKOUT, etc.)
- Trader notifications
- Account lockout/unlock events

**Critical for:** Compliance auditing, breach analysis

#### **api** (object, required)

TopstepX API calls and responses.

**Default:**
```yaml
api:
  enabled: true
  filename: "api.log"
  level: "DEBUG"
```

**Contains:**
- API authentication
- WebSocket events
- REST API requests/responses
- Connection errors

**Critical for:** Debugging API issues, rate limiting analysis

#### **error** (object, required)

Errors and exceptions only.

**Default:**
```yaml
error:
  enabled: true
  filename: "error.log"
  level: "ERROR"
```

**Contains:**
- Exception stack traces
- Unhandled errors
- Critical failures

**Critical for:** Quick error identification

---

### **performance** (object, optional)

Performance monitoring configuration.

#### **enabled** (boolean, optional)

Enable performance logging.

**Default:** `true`

#### **threshold_ms** (integer, optional)

Log operations slower than threshold.

**Default:** `100`
**Unit:** Milliseconds
**Example:** `100` = Log operations taking >100ms

**Use Cases:**
- Identify slow API calls
- Detect performance regressions
- Optimize critical paths

#### **include_metrics** (boolean, optional)

Include detailed performance metrics in logs.

**Default:** `true`

**Metrics Included:**
- Execution time (ms)
- Memory usage
- Database query count
- API call count

---

### **context** (object, optional)

Context tracking configuration.

#### **correlation_ids** (boolean, optional)

Enable correlation ID tracking.

**Default:** `true`

**Purpose:**
- Track requests across multiple log entries
- Correlate related events
- Essential for debugging complex flows

**Example:**
```json
{"correlation_id":"abc-123","message":"Processing order"}
{"correlation_id":"abc-123","message":"Order validated"}
{"correlation_id":"abc-123","message":"Order executed"}
```

#### **auto_generate** (boolean, optional)

Auto-generate correlation IDs if not provided.

**Default:** `true`

**Behavior:**
- If `true`: Generate UUID for each request
- If `false`: Only use explicit correlation IDs

---

### **security** (object, required)

Security and sensitive data masking.

#### **mask_sensitive** (boolean, required)

Mask sensitive data in logs.

**Default:** `true`

**Masked Data:**
- API keys: `sk_live_abc123...` → `sk_live_***MASKED***`
- Passwords: `password123` → `***MASKED***`
- Session tokens: `eyJhbGc...` → `***MASKED***`

#### **additional_patterns** (array, optional)

Additional regex patterns to mask.

**Default:** `[]`
**Format:** Array of regex strings

**Example:**
```yaml
additional_patterns:
  - 'ssn=\d{3}-\d{2}-\d{4}'    # Social Security Numbers
  - 'account_number=\d+'        # Account numbers
```

#### **mask_emails** (boolean, optional)

Mask email addresses in logs.

**Default:** `true`

**Behavior:**
- `trader@example.com` → `***@example.com`
- Or: `trader@example.com` → `t***r@example.com`

---

### **development** (object, optional)

Development-specific settings (disable in production).

#### **colored_console** (boolean, optional)

Use colored console output.

**Default:** `true`

**Colors:**
- DEBUG: Gray
- INFO: White
- WARNING: Yellow
- ERROR: Red
- CRITICAL: Bright Red

**Recommendation:** Disable in production (ANSI codes can interfere with log parsers)

#### **full_traces** (boolean, optional)

Include full stack traces for all exceptions.

**Default:** `true`

**Behavior:**
- `true`: Full stack trace (development)
- `false`: Condensed stack trace (production)

#### **console_duplicate** (boolean, optional)

Duplicate file logs to console.

**Default:** `true`

**Behavior:**
- If `true`: Logs written to both files and console
- If `false`: Logs written to files only (unless `enable_console` is true for daemon logs)

---

## ✅ Validation Rules

### **File-Level Validation**

1. **File must exist:** `config/logging.yaml` must be present
2. **Valid YAML:** Must parse without syntax errors
3. **Required fields:** All required fields must be present
4. **Valid log level:** Log levels must be valid strings

### **Field-Level Validation**

| Field | Validation |
|-------|------------|
| `log_dir` | Must be valid path, writable |
| `log_level` | Must be DEBUG/INFO/WARNING/ERROR/CRITICAL |
| `enable_console` | Must be boolean |
| `enable_json` | Must be boolean |
| `rotation.max_mb` | Must be integer > 0 |
| `rotation.backup_count` | Must be integer > 0 |
| `rotation.compress` | Must be boolean |
| `performance.threshold_ms` | Must be integer > 0 |
| `log_files.*.enabled` | Must be boolean |
| `log_files.*.level` | Must be valid log level |

---

## 🔒 Security Considerations

### **Sensitive Data Masking**

**Critical Patterns to Mask:**

```python
SENSITIVE_PATTERNS = [
    # API Keys
    (r'sk_live_[a-zA-Z0-9]+', 'sk_live_***MASKED***'),
    (r'sk_test_[a-zA-Z0-9]+', 'sk_test_***MASKED***'),

    # Passwords
    (r'"password"\s*:\s*"[^"]*"', '"password":"***MASKED***"'),
    (r'password=\S+', 'password=***MASKED***'),

    # Tokens
    (r'token"\s*:\s*"[^"]*"', 'token":"***MASKED***"'),
    (r'Bearer [a-zA-Z0-9\-._~+/]+', 'Bearer ***MASKED***'),

    # Email addresses (partial masking)
    (r'([a-zA-Z0-9._-]+)@([a-zA-Z0-9.-]+)', r'\1***@\2'),
]
```

### **Log File Permissions**

**Linux/Mac:**
```bash
chmod 640 logs/*.log
# Owner: read+write, Group: read, Others: none
```

**Windows:**
```powershell
icacls logs\*.log /inheritance:r /grant:r "%USERNAME%:(R,W)"
```

### **Log Retention**

**Compliance Considerations:**
- Financial regulations may require specific retention periods
- Check with compliance team before auto-deleting logs
- Consider separate long-term archival process

---

## 🛠️ Configuration Loader Implementation

**Location:** `src/config/logging_loader.py`

**Pseudocode:**

```python
import yaml
import logging
import logging.handlers
import os

def load_logging_config(file_path='config/logging.yaml'):
    """
    Load and apply logging configuration.

    Returns:
        dict: Logging configuration
    """
    # Read YAML
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)

    # Validate required fields
    required_fields = ['log_dir', 'log_level']
    for field in required_fields:
        if field not in config:
            raise ValidationError(f"Missing required field: {field}")

    # Create log directory
    log_dir = config['log_dir']
    os.makedirs(log_dir, exist_ok=True)

    # Validate log level
    log_level = config['log_level']
    if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        raise ValidationError(f"Invalid log_level: {log_level}")

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s'
    )

    # Configure specialized log files
    for log_name, log_config in config.get('log_files', {}).items():
        if not log_config.get('enabled', True):
            continue

        logger = logging.getLogger(log_name)
        logger.setLevel(getattr(logging, log_config['level']))

        # Create rotating file handler
        log_file = os.path.join(log_dir, log_config['filename'])
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=config['rotation']['max_mb'] * 1024 * 1024,
            backupCount=config['rotation']['backup_count']
        )

        # Set formatter
        if config.get('enable_json', False):
            handler.setFormatter(JsonFormatter())
        else:
            handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s [%(name)s] %(message)s'
            ))

        logger.addHandler(handler)

    return config
```

---

## 📖 Example Configurations

### **Development Configuration**

```yaml
log_dir: "logs"
log_level: "DEBUG"
enable_console: true
enable_json: false  # Human-readable

rotation:
  max_mb: 5
  backup_count: 3
  compress: false  # Faster for dev

log_files:
  daemon:
    enabled: true
    filename: "daemon.log"
    level: "DEBUG"
  enforcement:
    enabled: true
    filename: "enforcement.log"
    level: "DEBUG"
  api:
    enabled: true
    filename: "api.log"
    level: "DEBUG"
  error:
    enabled: true
    filename: "error.log"
    level: "ERROR"

performance:
  enabled: true
  threshold_ms: 50  # Lower threshold for dev
  include_metrics: true

security:
  mask_sensitive: true
  mask_emails: false  # Keep emails visible in dev

development:
  colored_console: true
  full_traces: true
  console_duplicate: true
```

### **Production Configuration**

```yaml
log_dir: "/var/log/risk-manager"
log_level: "INFO"
enable_console: false  # Use log files only
enable_json: true  # Structured logs

rotation:
  max_mb: 50  # Larger files
  backup_count: 30  # 30 days retention
  compress: true  # Save space

log_files:
  daemon:
    enabled: true
    filename: "daemon.log"
    level: "INFO"
  enforcement:
    enabled: true
    filename: "enforcement.log"
    level: "INFO"
  api:
    enabled: true
    filename: "api.log"
    level: "INFO"
  error:
    enabled: true
    filename: "error.log"
    level: "ERROR"

performance:
  enabled: true
  threshold_ms: 200  # Higher threshold
  include_metrics: true

context:
  correlation_ids: true
  auto_generate: true

security:
  mask_sensitive: true
  mask_emails: true
  additional_patterns:
    - 'account_number=\d+'

development:
  colored_console: false
  full_traces: false
  console_duplicate: false
```

---

## 📝 Summary

**Configuration File:** `config/logging.yaml`

**Purpose:** Control all logging behavior

**Key Settings:**
- `log_level`: Global verbosity
- `enable_json`: Structured vs human-readable
- `rotation`: Automatic log file rotation
- `log_files`: Specialized log streams
- `security`: Sensitive data masking

**Hot Reloadable:** No (requires daemon restart)

**Validation:** On daemon startup

---

**Related Files:**
- `src/config/logging_loader.py` - Configuration loader
- `src/logging/json_formatter.py` - JSON log formatter
- `src/logging/sensitive_mask.py` - Sensitive data masking
- `02-BACKEND-DAEMON/DAEMON_ARCHITECTURE.md` - Daemon logging integration

---

**Status:** Complete and ready for implementation
