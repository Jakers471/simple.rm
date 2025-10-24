# Configuration Architecture

## Overview

The Simple Risk Manager uses a multi-file configuration system that separates concerns into:
1. **Logging configuration** (`config/logging.yaml`) - Controls all logging behavior
2. **Risk rule configuration** (`config/risk_config.yaml`) - Defines risk rule parameters
3. **Account credentials** (`config/accounts.yaml`) - Stores monitored account credentials
4. **Admin authentication** (`config/admin_password.hash`) - Secures Admin CLI access

The configuration system supports hot-reloading for most settings, provides comprehensive validation, and implements security best practices for sensitive data.

---

## Configuration Sources

### File-Based Configuration

| File | Purpose | Hot-Reloadable | Contains Secrets |
|------|---------|----------------|------------------|
| `config/logging.yaml` | Logging behavior, rotation, masking | No (restart required) | No |
| `config/risk_config.yaml` | Risk rule parameters and limits | Yes (via Admin CLI) | No |
| `config/accounts.yaml` | Account credentials and API keys | No (restart required) | Yes |
| `config/admin_password.hash` | Admin password bcrypt hash | No | Yes (hashed) |

### Environment Variables

The system supports environment variable overrides for deployment scenarios:
- Used primarily for secrets and deployment-specific paths
- Not currently implemented in codebase but specified in SPECS
- Future enhancement for production deployments

**Proposed Environment Variables:**
```bash
TOPSTEPX_API_KEY=sk_live_...        # API key override
DATABASE_PATH=/var/data/risk.db     # Database path
LOG_LEVEL=INFO                      # Logging level
DEV_MODE=false                      # Development mode flag
```

---

## Complete Configuration Schema

### 1. Logging Configuration (`config/logging.yaml`)

**Purpose:** Control all logging behavior including levels, rotation, and sensitive data masking.

**Schema:**
```yaml
# Log directory
log_dir: "logs"

# Global log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
log_level: "INFO"

# Enable console output
enable_console: true

# Enable JSON structured logging
enable_json: true

# Log rotation settings
rotation:
  max_mb: 10                    # Max file size before rotation
  backup_count: 7               # Number of backups to keep
  compress: true                # Compress old logs

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
  threshold_ms: 100             # Log slow operations >100ms
  include_metrics: true

# Context tracking
context:
  correlation_ids: true         # Enable correlation ID tracking
  auto_generate: true           # Auto-generate if not provided

# Security
security:
  mask_sensitive: true          # Mask API keys, passwords, tokens
  additional_patterns: []       # Custom regex patterns to mask
  mask_emails: true             # Mask email addresses

# Development settings
development:
  colored_console: true         # Use colored output
  full_traces: true             # Include full stack traces
  console_duplicate: true       # Duplicate logs to console
```

**Current Implementation:**
- Located at: `src/risk_manager/logging/config.py`
- Provides `LogConfig` class with setup methods
- Creates specialized loggers (daemon, enforcement, api, error)
- Implements `MaskingFilter` for sensitive data
- Uses `RotatingFileHandler` for automatic rotation

**Validation Rules:**
- `log_level` must be valid level name (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- `log_dir` must be writable directory
- `rotation.max_mb` must be > 0
- `rotation.backup_count` must be > 0
- `performance.threshold_ms` must be > 0

---

### 2. Risk Rule Configuration (`config/risk_config.yaml`)

**Purpose:** Define parameters for all 12 risk rules with per-rule enable/disable.

**Schema:**
```yaml
# Global settings (optional)
global:
  strict_mode: false            # If true, any breach causes lockout
  logging_level: "INFO"

# Rule configurations
rules:
  # RULE-001: Max Contracts
  max_contracts:
    enabled: true
    limit: 5
    count_type: "net"           # "net" or "gross"

  # RULE-002: Max Contracts Per Instrument
  max_contracts_per_instrument:
    enabled: true
    limits:
      MNQ: 2                    # Per-symbol limits
      NQ: 1
      ES: 1
      MES: 3
    enforcement: "reduce_to_limit"
    unknown_symbol_action: "allow_with_limit:1"

  # RULE-003: Daily Realized Loss
  daily_realized_loss:
    enabled: true
    loss_limit: 500.00
    action: "CLOSE_ALL_AND_LOCKOUT"
    lockout_until: "daily_reset"

  # RULE-004: Daily Unrealized Loss
  daily_unrealized_loss:
    enabled: true
    loss_limit: 300.00
    scope: "per_position"
    action: "CLOSE_POSITION"
    lockout: false

  # RULE-005: Max Unrealized Profit
  max_unrealized_profit:
    enabled: true
    mode: "profit_target"       # "profit_target" or "breakeven"
    profit_target: 1000.00
    scope: "per_position"
    action: "CLOSE_POSITION"

  # RULE-006: Trade Frequency Limit
  trade_frequency_limit:
    enabled: true
    max_trades: 30
    time_window_minutes: 60

  # RULE-007: Cooldown After Loss
  cooldown_after_loss:
    enabled: true
    loss_threshold: 100.00
    cooldown_seconds: 300

  # RULE-008: No Stop-Loss Grace Period
  no_stop_loss_grace:
    enabled: true
    grace_period_seconds: 30
    action: "CLOSE_POSITION"

  # RULE-009: Session Block Outside Hours
  session_block_outside:
    enabled: true
    allowed_hours:
      start: "08:30"
      end: "15:00"
    timezone: "America/Chicago"
    action: "CANCEL_ORDER"

  # RULE-010: Auth Loss Guard
  auth_loss_guard:
    enabled: true
    action: "CLOSE_ALL_AND_LOCKOUT"

  # RULE-011: Symbol Blocks
  symbol_blocks:
    enabled: true
    blocked_symbols:
      - "RTY"
      - "BTC"
    action: "CANCEL_ORDER"
    close_existing: true

  # RULE-012: Trade Management
  trade_management:
    enabled: false              # Disabled by default
    auto_stop_loss: true
    stop_loss_ticks: 10
```

**Current Implementation:**
- Not yet implemented in codebase
- Specified in: `project-specs/SPECS/08-CONFIGURATION/RISK_CONFIG_YAML_SPEC.md`
- To be loaded by: `src/config/loader.py` (not yet created)

**Validation Rules:**
- All numeric limits must be > 0
- Time formats must be valid HH:MM
- Timezone must be valid IANA timezone
- Actions must be valid enforcement action types
- Symbol lists must be arrays of strings

---

### 3. Account Configuration (`config/accounts.yaml`)

**Purpose:** Define TopstepX accounts to monitor with authentication credentials.

**Schema:**
```yaml
accounts:
  - account_id: 123456              # TopstepX account ID
    username: "trader@example.com"  # TopstepX username/email
    api_key: "sk_live_abc123..."    # TopstepX API key
    enabled: true                    # Enable/disable monitoring
    nickname: "John's Main Account" # Display name (optional)

  - account_id: 789012
    username: "trader2@example.com"
    api_key: "sk_live_def456..."
    enabled: false                   # Disabled account
    nickname: "Test Account"
```

**Current Implementation:**
- Not yet implemented in codebase
- Specified in: `project-specs/SPECS/08-CONFIGURATION/ACCOUNTS_YAML_SPEC.md`
- To be loaded by: `src/config/loader.py` (not yet created)

**Security:**
- ⚠️ **NEVER commit with real API keys**
- Should be in `.gitignore`
- API keys must start with `sk_live_` or `sk_test_`
- File permissions should be 600 (owner read/write only)

**Validation Rules:**
- `account_id` must be positive integer and unique
- `username` must be valid email format
- `api_key` must start with `sk_live_` or `sk_test_`
- `enabled` must be boolean (defaults to true)
- At least one account must be configured

---

### 4. Admin Password (`config/admin_password.hash`)

**Purpose:** Secure Admin CLI access with bcrypt-hashed password.

**Format:** Binary file containing bcrypt hash
```
$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5oDWEM7WQGhKy
```

**Password Requirements:**
- Minimum: 8 characters
- Maximum: 72 characters (bcrypt limit)
- Recommended: 12+ characters with mixed complexity
- Must not be common dictionary words

**Bcrypt Configuration:**
- Algorithm: bcrypt
- Cost factor: 12 (recommended)
- Salt: Auto-generated per password
- Hash length: 60 characters

**Current Implementation:**
- Not yet implemented in codebase
- Specified in: `project-specs/SPECS/08-CONFIGURATION/ADMIN_PASSWORD_SPEC.md`
- To be used by Admin CLI for authentication

**Security Features:**
- No password recovery (by design)
- 3 login attempts per session
- File permissions 600
- Hash validated on daemon startup

---

## Configuration Loading

### Loading Process (Daemon Startup)

**Sequence:**
```
1. Initialize logging configuration
   ↓
2. Load logging.yaml
   ↓
3. Setup loggers and handlers
   ↓
4. Load accounts.yaml
   ↓
5. Validate account credentials
   ↓
6. Load risk_config.yaml
   ↓
7. Validate rule configurations
   ↓
8. Initialize daemon with config
```

### Current Implementation

**Logging Configuration:**
```python
# src/risk_manager/logging/config.py
from risk_manager.logging import setup_logging, get_logger

# At daemon startup
setup_logging(
    log_dir=Path("logs"),
    log_level=logging.INFO,
    enable_console=True,
    enable_json=True,
    max_bytes=10*1024*1024,
    backup_count=7
)

# Get logger in modules
logger = get_logger(__name__)
```

**Risk Configuration (Not Yet Implemented):**
```python
# Future: src/config/loader.py
def load_risk_config(file_path='config/risk_config.yaml'):
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)

    # Validate required fields
    if 'rules' not in config:
        raise ValidationError("Missing 'rules' key")

    # Load each rule config
    rule_configs = {}
    for rule_name, rule_data in config['rules'].items():
        rule_config = RuleConfig(
            rule_id=f"RULE-{rule_name}",
            name=rule_name,
            enabled=rule_data.get('enabled', True),
            params=rule_data
        )
        validate_rule_config(rule_name, rule_data)
        rule_configs[rule_name] = rule_config

    return rule_configs
```

### Validation

**Validation Stages:**

1. **File Existence:** All required config files must exist
2. **YAML Syntax:** Files must parse without errors
3. **Schema Validation:** Required fields must be present
4. **Value Validation:** Field values must meet constraints
5. **Cross-Field Validation:** Related fields must be consistent

**Error Handling:**
- Invalid config → Daemon refuses to start
- Detailed error messages logged
- Admin CLI displays validation errors

---

## Runtime Configuration Changes

### Hot-Reloadable Settings

**Via Admin CLI "Reload Config" Command:**

✅ **Can Be Hot-Reloaded:**
- Risk rule enable/disable (`risk_config.yaml`)
- Risk rule parameters (limits, thresholds)
- Global strict mode setting

**Hot Reload Process:**
```
1. Admin edits risk_config.yaml
   ↓
2. Admin runs "Reload Config" in Admin CLI
   ↓
3. Daemon reloads YAML file
   ↓
4. Daemon validates new configuration
   ↓
5. If valid → Apply new config
   If invalid → Keep old config, show error
```

❌ **Requires Daemon Restart:**
- Logging configuration changes
- Account credentials changes
- Admin password changes
- Code changes (module updates)

### Configuration Update Mechanism (Not Yet Implemented)

```python
class ConfigurationManager:
    def reload_risk_config(self):
        """Hot reload risk configuration"""
        try:
            # Save old config
            old_config = self.risk_config.copy()

            # Reload from file
            new_config = load_risk_config()

            # Validate
            if validate_risk_config(new_config):
                self.risk_config = new_config
                logger.info("Risk configuration reloaded successfully")
                return True
            else:
                logger.error("Invalid risk configuration, keeping old config")
                return False
        except Exception as e:
            logger.error(f"Config reload failed: {e}")
            return False
```

---

## Validation

### Logging Configuration Validation

**Implemented in:** `src/risk_manager/logging/config.py`

**Checks:**
- Log directory is writable
- Log level is valid Python logging level
- Rotation parameters are positive integers
- Specialized log configs are valid

**Example:**
```python
class LogConfig:
    def __init__(self, log_dir, log_level, ...):
        # Validate log directory
        self.log_dir = log_dir or DEFAULT_LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Validate log level
        if log_level not in [DEBUG, INFO, WARNING, ERROR, CRITICAL]:
            raise ValueError(f"Invalid log level: {log_level}")
```

### Risk Configuration Validation (Not Yet Implemented)

**Validation Per Rule:**

```python
def validate_rule_config(rule_name: str, rule_data: dict):
    """Validate individual rule configuration"""

    # RULE-001: Max Contracts
    if rule_name == "max_contracts":
        if rule_data.get('limit', 0) <= 0:
            raise ValidationError("max_contracts.limit must be > 0")

        count_type = rule_data.get('count_type', 'net')
        if count_type not in ['net', 'gross']:
            raise ValidationError(f"Invalid count_type: {count_type}")

    # RULE-003: Daily Realized Loss
    elif rule_name == "daily_realized_loss":
        if rule_data.get('loss_limit', 0) <= 0:
            raise ValidationError("loss_limit must be > 0")

        lockout = rule_data.get('lockout_until', 'daily_reset')
        if lockout not in ['daily_reset', 'permanent']:
            raise ValidationError(f"Invalid lockout_until: {lockout}")

    # ... (validate all 12 rules)
```

### Account Configuration Validation (Not Yet Implemented)

```python
def validate_account_config(accounts: list):
    """Validate account configuration"""

    if not accounts:
        raise ValidationError("Must have at least one account")

    seen_ids = set()
    for account in accounts:
        # Check required fields
        if 'account_id' not in account:
            raise ValidationError("Missing account_id")

        account_id = account['account_id']

        # Check for duplicates
        if account_id in seen_ids:
            raise ValidationError(f"Duplicate account_id: {account_id}")
        seen_ids.add(account_id)

        # Validate account_id
        if not isinstance(account_id, int) or account_id <= 0:
            raise ValidationError(f"Invalid account_id: {account_id}")

        # Validate API key format
        api_key = account.get('api_key', '')
        if not (api_key.startswith('sk_live_') or api_key.startswith('sk_test_')):
            raise ValidationError(f"Invalid API key format for account {account_id}")
```

---

## Example Configurations

### Development Configuration

**config/logging.yaml:**
```yaml
log_dir: "logs"
log_level: "DEBUG"              # Verbose for development
enable_console: true
enable_json: false              # Human-readable
rotation:
  max_mb: 5                     # Smaller files
  backup_count: 3
  compress: false               # Faster
security:
  mask_sensitive: true
  mask_emails: false            # Keep visible in dev
development:
  colored_console: true
  full_traces: true
  console_duplicate: true
```

**config/risk_config.yaml:**
```yaml
global:
  strict_mode: false
  logging_level: "DEBUG"

rules:
  max_contracts:
    enabled: true
    limit: 10                   # Higher for testing
    count_type: "net"

  daily_realized_loss:
    enabled: true
    loss_limit: 1000.00         # Higher for testing
    action: "CLOSE_ALL_AND_LOCKOUT"
```

### Production Configuration

**config/logging.yaml:**
```yaml
log_dir: "/var/log/risk-manager"
log_level: "INFO"               # Less verbose
enable_console: false           # Use log files only
enable_json: true               # Structured for parsing
rotation:
  max_mb: 50                    # Larger files
  backup_count: 30              # 30 days retention
  compress: true                # Save space
security:
  mask_sensitive: true
  mask_emails: true
development:
  colored_console: false
  full_traces: false
  console_duplicate: false
```

**config/risk_config.yaml:**
```yaml
global:
  strict_mode: false
  logging_level: "INFO"

rules:
  max_contracts:
    enabled: true
    limit: 5
    count_type: "net"

  daily_realized_loss:
    enabled: true
    loss_limit: 500.00
    action: "CLOSE_ALL_AND_LOCKOUT"
    lockout_until: "daily_reset"

  # All 12 rules configured...
```

---

## SPECS Files Analyzed

**Configuration SPECS:**
1. `project-specs/SPECS/08-CONFIGURATION/LOGGING_CONFIG_SPEC.md` - Logging configuration
2. `project-specs/SPECS/08-CONFIGURATION/RISK_CONFIG_YAML_SPEC.md` - Risk rules configuration
3. `project-specs/SPECS/08-CONFIGURATION/ACCOUNTS_YAML_SPEC.md` - Account credentials
4. `project-specs/SPECS/08-CONFIGURATION/ADMIN_PASSWORD_SPEC.md` - Admin authentication

**Related SPECS:**
5. `project-specs/SPECS/99-IMPLEMENTATION-GUIDES/api-resilience/CONFIGURATION_MASTER_SPEC.md` - Master config (future enhancement)

**Rule SPECS (referenced by risk_config.yaml):**
- `project-specs/SPECS/03-RISK-RULES/rules/01_max_contracts.md` through `12_trade_management.md`

---

## Current Implementation Status

### ✅ Implemented

**Logging System:**
- `src/risk_manager/logging/config.py` - LogConfig class
- `src/risk_manager/logging/formatters.py` - StructuredFormatter, MaskingFilter
- Specialized loggers (daemon, enforcement, api, error)
- Rotating file handlers
- JSON structured logging
- Sensitive data masking

**Actual Configuration Files:**
- `config/logging.yaml` - Complete logging configuration
- `tests/logging_config.yaml` - Test logging configuration

**Reset Scheduler (uses config):**
- `src/core/reset_scheduler.py` - Daily reset with timezone support
- Holiday calendar loading from YAML

### ❌ Not Yet Implemented

**Configuration Loading:**
- `src/config/loader.py` - Not yet created
- Risk config loading
- Account config loading
- Admin password validation

**Configuration Files:**
- `config/risk_config.yaml` - Not yet created
- `config/accounts.yaml` - Not yet created
- `config/admin_password.hash` - Not yet created

**Hot Reload:**
- Configuration reload mechanism
- Admin CLI reload command
- Configuration change detection

**Environment Variable Support:**
- Environment variable overrides
- `.env` file loading
- Configuration precedence system

---

## Integration Points

### Daemon Startup

```python
# Daemon initialization (not yet implemented)
def initialize_daemon():
    # 1. Setup logging
    setup_logging(
        log_dir=Path("logs"),
        log_level=logging.INFO
    )
    logger = get_logger(__name__)
    logger.info("Starting Risk Manager daemon")

    # 2. Load configurations
    accounts = load_account_config("config/accounts.yaml")
    risk_config = load_risk_config("config/risk_config.yaml")

    # 3. Validate admin password
    validate_admin_password("config/admin_password.hash")

    # 4. Initialize components
    daemon = RiskManagerDaemon(accounts, risk_config)

    # 5. Start daemon
    daemon.start()
```

### Admin CLI

```python
# Admin CLI (not yet implemented)
def admin_cli_main():
    # 1. Authenticate admin
    if not authenticate_admin():
        print("Authentication failed")
        sys.exit(1)

    # 2. Load current config
    config_mgr = ConfigurationManager()
    config_mgr.load()

    # 3. Show menu
    while True:
        choice = show_admin_menu()

        if choice == "Reload Config":
            if config_mgr.reload_risk_config():
                print("✅ Configuration reloaded")
            else:
                print("❌ Configuration reload failed")
```

---

## Security Considerations

### Sensitive Data Protection

**API Keys:**
- Stored in `accounts.yaml`
- Must NOT be committed to Git
- Masked in all log output via `MaskingFilter`
- Pattern: `sk_live_***MASKED***`

**Admin Password:**
- Hashed with bcrypt (cost factor 12)
- Stored in binary hash file
- No password recovery mechanism
- File permissions 600

**Logging Security:**
- Implemented in `src/risk_manager/logging/formatters.py`
- `MaskingFilter` automatically masks:
  - API keys (sk_live_, sk_test_)
  - Passwords
  - Bearer tokens
  - Email addresses (partial masking)

**File Permissions:**
```bash
# Linux/Mac
chmod 600 config/accounts.yaml
chmod 600 config/admin_password.hash
chmod 644 config/logging.yaml
chmod 644 config/risk_config.yaml

# Logs directory
chmod 700 logs/
chmod 640 logs/*.log
```

### .gitignore Configuration

```gitignore
# Configuration files with secrets
config/accounts.yaml
config/admin_password.hash

# Environment variables
.env
.env.local
.env.production

# Database
data/*.db
data/*.db-wal

# Logs
logs/
*.log

# Backups
backups/
```

---

## Future Enhancements

### Master Configuration File

**Proposed:** `config/config.yaml` - Consolidate API, SignalR, error handling settings
- See: `project-specs/SPECS/99-IMPLEMENTATION-GUIDES/api-resilience/CONFIGURATION_MASTER_SPEC.md`
- Would include API URLs, retry strategies, circuit breaker settings
- Not yet implemented, but fully specified

### Environment Variable Support

**Proposed Environment Variables:**
```bash
TOPSTEPX_API_KEY=sk_live_...
DATABASE_PATH=/var/data/risk.db
LOG_LEVEL=INFO
CONFIG_PATH=/custom/config.yaml
TOKEN_REFRESH_BUFFER_SECONDS=7200
```

**Configuration Precedence:**
1. Environment variables (highest)
2. Command-line arguments
3. Configuration files
4. Default values (lowest)

### Configuration Hot-Reload

**Proposed File Watching:**
```python
import watchdog

class ConfigWatcher:
    def on_modified(self, event):
        if event.src_path == "config/risk_config.yaml":
            logger.info("Config file changed, reloading...")
            self.config_mgr.reload()
```

---

## Summary

**Configuration System:**
- Multi-file approach separating concerns
- YAML format for human readability
- Comprehensive validation on load
- Hot-reload support for risk rules
- Security-first design for sensitive data

**Current State:**
- ✅ Logging configuration fully implemented
- ❌ Risk config, accounts, admin password not yet implemented
- ❌ Hot-reload mechanism not yet implemented
- ❌ Environment variable support not yet implemented

**Key Files:**
- `config/logging.yaml` - Exists and working
- `config/risk_config.yaml` - Spec complete, not created
- `config/accounts.yaml` - Spec complete, not created
- `config/admin_password.hash` - Spec complete, not created

**Implementation Priority:**
1. Create config loader (`src/config/loader.py`)
2. Create initial `risk_config.yaml` and `accounts.yaml`
3. Implement validation for all config types
4. Add hot-reload support to daemon
5. Add Admin CLI reload command
6. Add environment variable support

---

**Status:** Configuration architecture documented. Logging system implemented. Other configurations specified but not yet implemented.
