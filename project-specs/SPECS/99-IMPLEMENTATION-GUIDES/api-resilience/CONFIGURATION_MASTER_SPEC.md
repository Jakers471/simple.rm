---
doc_id: GUIDE-004
title: Master Configuration Specification
version: 2.0
status: DRAFT
last_updated: 2025-10-22
purpose: Consolidate all configuration requirements for API resilience and risk rules
dependencies: [RISK_CONFIG_YAML_SPEC.md, API_RESILIENCE_OVERVIEW.md]
---

# Master Configuration Specification

**Purpose:** Define the complete configuration schema for the Simple Risk Manager, consolidating API resilience, risk rules, and system settings into a unified configuration file.

---

## 📋 Table of Contents

1. [Configuration Files](#configuration-files)
2. [Master Configuration Schema](#master-configuration-schema)
3. [Configuration Precedence](#configuration-precedence)
4. [Validation Rules](#validation-rules)
5. [Configuration Loading](#configuration-loading)
6. [Hot Reloading](#hot-reloading)
7. [Environment Variables](#environment-variables)
8. [Security Considerations](#security-considerations)

---

## 📁 Configuration Files

### File Structure

```
config/
├── config.yaml              # Master configuration (API + system settings)
├── risk_config.yaml         # Risk rule configurations
├── accounts.yaml            # Account credentials (encrypted)
└── .env                     # Environment variables (not committed)
```

### File Purposes

| File | Purpose | Hot Reloadable | Contains Secrets |
|------|---------|----------------|------------------|
| `config.yaml` | API, SignalR, error handling, system settings | Yes (most settings) | No |
| `risk_config.yaml` | Risk rule configurations | Yes | No |
| `accounts.yaml` | Account credentials, API keys | No (requires restart) | Yes (encrypted) |
| `.env` | Environment variables (secrets) | No (requires restart) | Yes |

---

## ⚙️ Master Configuration Schema

### config.yaml - Complete Schema

```yaml
# config.yaml - Master configuration for Simple Risk Manager
# Version: 2.0

# ============================================================================
# API CONFIGURATION
# ============================================================================
api:
  baseUrl: "https://gateway.topstepx.com"
  timeout: 30000  # Default timeout in milliseconds
  userAgent: "SimpleRiskManager/2.0"

# ============================================================================
# AUTHENTICATION & TOKEN MANAGEMENT
# ============================================================================
authentication:
  # Token refresh strategy
  tokenRefresh:
    bufferSeconds: 7200  # Refresh 2 hours before expiry (24h tokens)
    maxRetries: 3
    retryDelays: [1000, 5000, 15000]  # Retry delays in ms
    fallbackToReauth: true  # Re-authenticate if refresh fails

  # Token storage
  storage:
    type: "encrypted"  # Options: "encrypted", "memory", "keyring"
    encryption: "AES-256"
    keySource: "environment"  # Options: "environment", "keyring", "file"
    storePath: "data/tokens.enc"  # Path for encrypted token storage

  # Security
  security:
    requireHttps: true
    validateCertificates: true
    tokenRotationDays: 30  # Force token rotation every 30 days

# ============================================================================
# SIGNALR CONNECTION MANAGEMENT
# ============================================================================
signalr:
  # User Hub (account, positions, orders, trades)
  userHub:
    url: "https://rtc.topstepx.com/hubs/user"
    enabled: true

  # Market Hub (quotes, trades, market depth)
  marketHub:
    url: "https://rtc.topstepx.com/hubs/market"
    enabled: true  # Set to false if real-time quotes not needed

  # Reconnection strategy
  reconnection:
    enabled: true
    maxAttempts: 10
    delays: [0, 2000, 10000, 30000, 60000]  # Exponential backoff in ms
    maxDelayMs: 60000
    resetOnSuccess: true
    jitter: 0.1  # 10% jitter for distributed systems

  # Health monitoring
  health:
    enabled: true
    pingInterval: 30000  # Send ping every 30 seconds
    pingTimeout: 5000    # Expect pong within 5 seconds
    staleThreshold: 120000  # Mark stale after 2 minutes
    reconnectOnStale: true

  # Event subscriptions
  subscriptions:
    autoResubscribe: true
    resubscribeDelay: 1000  # Wait 1 second after reconnect
    subscribeTimeout: 10000  # Subscription must succeed within 10 seconds
    requiredSubscriptions:
      - "positions"  # Fail if position subscription fails
      - "orders"
      - "trades"

  # Buffer settings
  buffer:
    maxSize: 1000  # Max events to buffer during disconnection
    dropOldest: true  # Drop oldest events if buffer full

# ============================================================================
# ERROR HANDLING & RESILIENCE
# ============================================================================
errorHandling:
  # Retry strategy
  retries:
    enabled: true
    maxAttempts: 5
    backoffBase: 1000  # Base delay in ms
    backoffMultiplier: 2  # Exponential multiplier
    maxBackoffMs: 60000  # Cap at 1 minute
    jitter: 0.1  # 10% jitter

    # Retryable error codes
    retryableHttpCodes:
      - 408  # Request Timeout
      - 429  # Too Many Requests
      - 500  # Internal Server Error
      - 502  # Bad Gateway
      - 503  # Service Unavailable
      - 504  # Gateway Timeout

    # Non-retryable error codes (fail immediately)
    permanentHttpCodes:
      - 400  # Bad Request
      - 401  # Unauthorized
      - 403  # Forbidden
      - 404  # Not Found
      - 405  # Method Not Allowed
      - 422  # Unprocessable Entity

  # Rate limiting (client-side)
  rateLimit:
    enabled: true

    # History endpoint (special limit)
    history:
      requests: 50
      windowSeconds: 30
      queueSize: 100
      dropOldest: false  # Don't drop history requests

    # General endpoints
    general:
      requests: 200
      windowSeconds: 60
      queueSize: 1000
      dropOldest: true

    # Backpressure
    backpressure:
      enabled: true
      maxQueueWaitMs: 30000  # Max 30 seconds wait in queue
      throwOnTimeout: false  # Don't throw, just log warning

  # Circuit breaker
  circuitBreaker:
    enabled: true
    failureThreshold: 5  # Open after 5 consecutive failures
    timeout: 60000  # Stay open for 1 minute
    halfOpenRequests: 3  # Test with 3 requests in half-open state
    successThreshold: 2  # Close after 2 consecutive successes (half-open)

    # Per-endpoint circuit breakers
    perEndpoint: false  # Use global circuit breaker
    endpoints:
      - "/api/Order/place"  # Separate circuit for order placement
      - "/api/Position/closeContract"  # Separate circuit for position close

  # Error logging
  logging:
    logAllErrors: true
    logRetries: true
    logRateLimiting: false  # Too verbose
    logCircuitBreaker: true
    includeStackTrace: false  # Only for DEBUG level

# ============================================================================
# ORDER MANAGEMENT
# ============================================================================
orderManagement:
  # Order verification
  verification:
    enabled: true
    timeout: 5000  # Max 5 seconds to verify order
    pollInterval: 500  # Check every 500ms
    maxRetries: 3

  # Idempotency (duplicate prevention)
  idempotency:
    enabled: true
    cacheTTL: 3600  # Keep cache for 1 hour
    cacheSize: 1000  # Max 1000 cached orders
    useOrderTimestamp: true  # Use timestamp in idempotency key

  # Partial fill tracking
  partialFills:
    enabled: true
    trackingTimeout: 60000  # Consider incomplete after 1 minute
    notifyOnPartial: true  # Notify when partial fill detected
    requeryInterval: 2000  # Requery order status every 2 seconds

  # Order timeouts
  timeouts:
    placement: 10000  # Order placement must complete within 10 seconds
    cancellation: 5000  # Order cancellation must complete within 5 seconds
    modification: 5000  # Order modification must complete within 5 seconds

# ============================================================================
# STATE RECONCILIATION
# ============================================================================
stateReconciliation:
  enabled: true
  onReconnect: true  # Always reconcile after reconnection
  minInterval: 5000  # Minimum 5 seconds between reconciliations
  maxInterval: 300000  # Maximum 5 minutes between reconciliations
  periodicEnabled: false  # Don't reconcile periodically (only on reconnect)

  # What to reconcile
  comparePositions: true
  compareOrders: true
  compareAccount: true
  compareTrades: false  # Trade history doesn't change

  # Discrepancy handling
  logDiscrepancies: true
  alertOnDiscrepancies: true  # Send alert if discrepancies found
  autoCorrect: true  # Automatically update state to match API

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
database:
  path: "data/risk_manager.db"
  schemaVersion: 2

  # Connection settings
  connection:
    timeout: 30000  # 30 seconds
    checkSameThread: false  # Allow multi-threaded access
    journal_mode: "WAL"  # Write-Ahead Logging for better concurrency
    synchronous: "NORMAL"  # Balance safety and performance

  # Retention policies
  retention:
    dailyUnrealizedPnl: 7  # Keep 7 days of unrealized P&L history
    enforcementLogs: 30  # Keep 30 days of enforcement logs
    orderHistory: 90  # Keep 90 days of order history
    tradeHistory: 365  # Keep 1 year of trade history
    quotesHistory: 1  # Keep 1 day of quote history (not implemented)

  # Backup settings
  backup:
    enabled: true
    interval: 86400  # Daily (seconds)
    path: "backups/"
    keepCount: 7  # Keep 7 backups
    compress: true

  # Performance
  performance:
    batchInsertSize: 100  # Batch insert 100 records at a time
    cacheSize: 10000  # SQLite cache size (pages)
    vacuumOnStartup: false  # Don't vacuum on startup (takes time)
    vacuumSchedule: "weekly"  # Vacuum weekly

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
logging:
  # General logging
  level: "INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "json"  # Options: "json", "text"

  # Log files
  files:
    daemon:
      path: "logs/daemon.log"
      maxSize: 10485760  # 10 MB
      backupCount: 5
      level: "INFO"

    enforcement:
      path: "logs/enforcement.log"
      maxSize: 10485760
      backupCount: 10
      level: "INFO"

    api:
      path: "logs/api.log"
      maxSize: 10485760
      backupCount: 5
      level: "WARNING"  # Only log warnings and errors

    errors:
      path: "logs/errors.log"
      maxSize: 10485760
      backupCount: 10
      level: "ERROR"

  # Component-specific logging
  components:
    tokenManager: "INFO"
    signalrManager: "INFO"
    errorHandler: "WARNING"
    rateLimiter: "WARNING"
    circuitBreaker: "INFO"
    stateReconciler: "INFO"
    orderManager: "INFO"
    riskRules: "INFO"

  # Log rotation
  rotation:
    enabled: true
    when: "midnight"  # Rotate at midnight
    interval: 1  # Rotate every day
    backupCount: 30  # Keep 30 days of logs

  # Performance logging
  performance:
    enabled: true
    logSlowOperations: true
    slowThresholdMs: 1000  # Log operations taking >1 second
    logLatency: true
    latencyPercentiles: [50, 90, 95, 99]

# ============================================================================
# MONITORING & METRICS
# ============================================================================
monitoring:
  enabled: true

  # Metrics collection
  metrics:
    enabled: true
    interval: 60000  # Collect metrics every 60 seconds
    retention: 86400  # Keep 24 hours of metrics

    # What to collect
    collect:
      - "event_processing_latency"
      - "api_response_times"
      - "signalr_connection_uptime"
      - "rule_breach_counts"
      - "enforcement_action_counts"
      - "token_refresh_counts"
      - "error_counts"
      - "circuit_breaker_state"

  # Health checks
  health:
    enabled: true
    interval: 30000  # Check health every 30 seconds
    endpoint: "/health"  # HTTP endpoint for health checks (if enabled)

  # Alerts
  alerts:
    enabled: false  # Not implemented yet
    webhookUrl: ""  # Webhook for alerts

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================
performance:
  # Event processing
  eventProcessing:
    batchSize: 10  # Process up to 10 events in batch
    batchTimeout: 100  # Wait max 100ms for batch to fill
    maxConcurrency: 5  # Max 5 concurrent event processors

  # Memory management
  memory:
    maxCacheSize: 104857600  # 100 MB max cache size
    cacheEvictionPolicy: "LRU"  # Least Recently Used
    gcInterval: 300000  # Run garbage collection every 5 minutes

  # Threading
  threading:
    eventProcessorThreads: 4  # 4 threads for event processing
    ioThreads: 8  # 8 threads for I/O operations
    maxThreadPoolSize: 20  # Max 20 threads total

# ============================================================================
# DEVELOPMENT & DEBUGGING
# ============================================================================
development:
  # Development mode
  devMode: false  # Set to true for development
  debugLogging: false  # Extra verbose logging
  saveRawEvents: false  # Save raw SignalR events to file

  # Testing
  testing:
    useMockApi: false  # Use mock API instead of real TopstepX
    mockDataPath: "tests/mock_data/"
    replayEvents: false  # Replay events from file
    replayPath: "tests/replay_events.json"

  # Profiling
  profiling:
    enabled: false
    outputPath: "profiling/"
    profileMemory: false
    profileCpu: false

# ============================================================================
# SYSTEM CONFIGURATION
# ============================================================================
system:
  # Timezone
  timezone: "America/Chicago"  # Chicago time (market hours)

  # Daily reset time
  dailyReset:
    enabled: true
    time: "17:00"  # 5 PM Chicago time
    timezone: "America/Chicago"

  # Graceful shutdown
  shutdown:
    gracePeriod: 10000  # 10 seconds to complete in-flight operations
    forceKillAfter: 30000  # Force kill after 30 seconds

  # Startup
  startup:
    connectTimeout: 30000  # 30 seconds to connect on startup
    retryOnFailure: true
    maxStartupRetries: 3
```

---

## 🔀 Configuration Precedence

### Precedence Order (Highest to Lowest)

1. **Environment Variables** (highest priority)
   - Example: `TOPSTEPX_API_KEY`
   - Override any config file setting

2. **Command-line Arguments**
   - Example: `--config-path=/custom/config.yaml`
   - Override environment variables for paths

3. **config.yaml** (master configuration)
   - API, SignalR, error handling, system settings

4. **risk_config.yaml** (risk rules)
   - Rule configurations (depends on config.yaml)

5. **Default Values** (lowest priority)
   - Hard-coded defaults in code

### Example Precedence

```python
# Example: Token refresh buffer
# 1. Environment variable (if set)
buffer = os.getenv("TOKEN_REFRESH_BUFFER_SECONDS")

# 2. config.yaml (if no environment variable)
if buffer is None:
    buffer = config['authentication']['tokenRefresh']['bufferSeconds']

# 3. Default value (if no config)
if buffer is None:
    buffer = 7200  # 2 hours default
```

---

## ✅ Validation Rules

### Validation Schema

```python
class ConfigValidator:
    """Validate configuration on load"""

    def validate(self, config: dict) -> ValidationResult:
        """Validate entire configuration"""
        errors = []

        # API Configuration
        errors.extend(self._validate_api(config.get('api', {})))

        # Authentication Configuration
        errors.extend(self._validate_authentication(config.get('authentication', {})))

        # SignalR Configuration
        errors.extend(self._validate_signalr(config.get('signalr', {})))

        # Error Handling Configuration
        errors.extend(self._validate_error_handling(config.get('errorHandling', {})))

        # Order Management Configuration
        errors.extend(self._validate_order_management(config.get('orderManagement', {})))

        # Database Configuration
        errors.extend(self._validate_database(config.get('database', {})))

        if errors:
            return ValidationResult(valid=False, errors=errors)
        else:
            return ValidationResult(valid=True, errors=[])

    def _validate_api(self, api_config: dict) -> list:
        """Validate API configuration"""
        errors = []

        # Base URL must be HTTPS
        base_url = api_config.get('baseUrl', '')
        if not base_url.startswith('https://'):
            errors.append("api.baseUrl must use HTTPS")

        # Timeout must be positive
        timeout = api_config.get('timeout', 30000)
        if timeout <= 0:
            errors.append("api.timeout must be positive")

        return errors

    def _validate_authentication(self, auth_config: dict) -> list:
        """Validate authentication configuration"""
        errors = []

        # Token refresh buffer must be positive and less than 24 hours
        buffer = auth_config.get('tokenRefresh', {}).get('bufferSeconds', 7200)
        if buffer <= 0:
            errors.append("authentication.tokenRefresh.bufferSeconds must be positive")
        if buffer >= 86400:
            errors.append("authentication.tokenRefresh.bufferSeconds must be less than 24 hours (86400 seconds)")

        # Storage type must be valid
        storage_type = auth_config.get('storage', {}).get('type', 'encrypted')
        if storage_type not in ['encrypted', 'memory', 'keyring']:
            errors.append(f"authentication.storage.type must be 'encrypted', 'memory', or 'keyring', got '{storage_type}'")

        return errors

    def _validate_signalr(self, signalr_config: dict) -> list:
        """Validate SignalR configuration"""
        errors = []

        # Reconnection delays must be ascending
        delays = signalr_config.get('reconnection', {}).get('delays', [])
        if delays != sorted(delays):
            errors.append("signalr.reconnection.delays must be in ascending order")

        # Ping interval must be less than stale threshold
        ping_interval = signalr_config.get('health', {}).get('pingInterval', 30000)
        stale_threshold = signalr_config.get('health', {}).get('staleThreshold', 120000)
        if ping_interval >= stale_threshold:
            errors.append("signalr.health.pingInterval must be less than staleThreshold")

        return errors

    def _validate_error_handling(self, error_config: dict) -> list:
        """Validate error handling configuration"""
        errors = []

        # Rate limit requests must be positive
        history_requests = error_config.get('rateLimit', {}).get('history', {}).get('requests', 50)
        if history_requests <= 0:
            errors.append("errorHandling.rateLimit.history.requests must be positive")

        general_requests = error_config.get('rateLimit', {}).get('general', {}).get('requests', 200)
        if general_requests <= 0:
            errors.append("errorHandling.rateLimit.general.requests must be positive")

        # Circuit breaker failure threshold must be positive
        failure_threshold = error_config.get('circuitBreaker', {}).get('failureThreshold', 5)
        if failure_threshold <= 0:
            errors.append("errorHandling.circuitBreaker.failureThreshold must be positive")

        return errors

    def _validate_order_management(self, order_config: dict) -> list:
        """Validate order management configuration"""
        errors = []

        # Verification timeout must be positive
        timeout = order_config.get('verification', {}).get('timeout', 5000)
        if timeout <= 0:
            errors.append("orderManagement.verification.timeout must be positive")

        # Idempotency cache TTL must be positive
        cache_ttl = order_config.get('idempotency', {}).get('cacheTTL', 3600)
        if cache_ttl <= 0:
            errors.append("orderManagement.idempotency.cacheTTL must be positive")

        return errors

    def _validate_database(self, db_config: dict) -> list:
        """Validate database configuration"""
        errors = []

        # Schema version must be supported
        schema_version = db_config.get('schemaVersion', 2)
        if schema_version not in [1, 2]:
            errors.append(f"database.schemaVersion must be 1 or 2, got {schema_version}")

        # Retention days must be positive
        for key, days in db_config.get('retention', {}).items():
            if days <= 0:
                errors.append(f"database.retention.{key} must be positive")

        return errors
```

---

## 📂 Configuration Loading

### Configuration Loader

```python
class ConfigurationManager:
    """Load and manage all configuration"""

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = {}
        self.risk_config = {}
        self.validator = ConfigValidator()

    def load(self):
        """Load all configuration files"""

        # 1. Load master configuration
        logger.info(f"Loading master configuration from {self.config_path}")
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # 2. Apply environment variable overrides
        self._apply_env_overrides()

        # 3. Validate configuration
        validation_result = self.validator.validate(self.config)
        if not validation_result.valid:
            raise ConfigurationError(f"Configuration validation failed: {validation_result.errors}")

        # 4. Load risk configuration
        risk_config_path = "config/risk_config.yaml"
        logger.info(f"Loading risk configuration from {risk_config_path}")
        with open(risk_config_path, 'r') as f:
            self.risk_config = yaml.safe_load(f)

        # 5. Validate risk configuration
        risk_validation = self._validate_risk_config(self.risk_config)
        if not risk_validation.valid:
            raise ConfigurationError(f"Risk configuration validation failed: {risk_validation.errors}")

        logger.info("Configuration loaded and validated successfully")

    def _apply_env_overrides(self):
        """Apply environment variable overrides"""

        # Token refresh buffer
        if 'TOKEN_REFRESH_BUFFER_SECONDS' in os.environ:
            buffer = int(os.environ['TOKEN_REFRESH_BUFFER_SECONDS'])
            self.config['authentication']['tokenRefresh']['bufferSeconds'] = buffer
            logger.info(f"Overriding token refresh buffer from environment: {buffer}s")

        # Database path
        if 'DATABASE_PATH' in os.environ:
            path = os.environ['DATABASE_PATH']
            self.config['database']['path'] = path
            logger.info(f"Overriding database path from environment: {path}")

        # Logging level
        if 'LOG_LEVEL' in os.environ:
            level = os.environ['LOG_LEVEL']
            self.config['logging']['level'] = level
            logger.info(f"Overriding log level from environment: {level}")

        # Development mode
        if 'DEV_MODE' in os.environ:
            dev_mode = os.environ['DEV_MODE'].lower() == 'true'
            self.config['development']['devMode'] = dev_mode
            logger.info(f"Overriding dev mode from environment: {dev_mode}")

    def get(self, key_path: str, default=None):
        """Get configuration value by dot-separated path"""
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def reload(self):
        """Reload configuration (hot reload)"""
        logger.info("Reloading configuration...")

        try:
            # Save old config
            old_config = self.config.copy()

            # Reload
            self.load()

            logger.info("Configuration reloaded successfully")
            return True

        except Exception as e:
            # Restore old config on failure
            self.config = old_config
            logger.error(f"Configuration reload failed, keeping old config: {e}")
            return False
```

---

## 🔄 Hot Reloading

### Hot Reload Support

**What Can Be Hot-Reloaded:**
- ✅ Logging level
- ✅ Rate limits (requests, windows)
- ✅ Circuit breaker thresholds
- ✅ Order verification timeouts
- ✅ State reconciliation settings
- ✅ Performance tuning settings
- ✅ Risk rule configurations (risk_config.yaml)

**What Requires Restart:**
- ❌ API base URL
- ❌ SignalR URLs
- ❌ Authentication settings (token storage)
- ❌ Database path
- ❌ Account credentials (accounts.yaml)

### Hot Reload Trigger

```python
class ConfigurationManager:
    def hot_reload_if_changed(self):
        """Check if config files changed and reload"""

        # Check file modification times
        config_mtime = os.path.getmtime(self.config_path)
        risk_config_mtime = os.path.getmtime("config/risk_config.yaml")

        if config_mtime > self.last_config_mtime or risk_config_mtime > self.last_risk_config_mtime:
            logger.info("Configuration files changed, reloading...")
            self.reload()
            self.last_config_mtime = config_mtime
            self.last_risk_config_mtime = risk_config_mtime
```

---

## 🔐 Environment Variables

### Supported Environment Variables

| Variable | Purpose | Example | Required |
|----------|---------|---------|----------|
| `TOPSTEPX_API_KEY` | TopstepX API key | `abc123...` | Yes |
| `TOPSTEPX_USERNAME` | TopstepX username | `trader@example.com` | Yes |
| `TOKEN_ENCRYPTION_KEY` | Token encryption key | `hex:32byte...` | No (generated if missing) |
| `DATABASE_PATH` | Database file path | `/data/risk_manager.db` | No |
| `LOG_LEVEL` | Logging level | `INFO` / `DEBUG` | No |
| `DEV_MODE` | Development mode | `true` / `false` | No |
| `CONFIG_PATH` | Config file path | `/custom/config.yaml` | No |
| `TOKEN_REFRESH_BUFFER_SECONDS` | Token refresh buffer | `7200` | No |

### .env File Example

```bash
# .env - Environment variables (DO NOT COMMIT)

# TopstepX Credentials (REQUIRED)
TOPSTEPX_API_KEY=your_api_key_here
TOPSTEPX_USERNAME=trader@example.com

# Token Encryption Key (generated automatically if missing)
TOKEN_ENCRYPTION_KEY=hex:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

# Optional Overrides
LOG_LEVEL=INFO
DEV_MODE=false
DATABASE_PATH=data/risk_manager.db

# Advanced Tuning (optional)
TOKEN_REFRESH_BUFFER_SECONDS=7200
```

---

## 🔒 Security Considerations

### Sensitive Data Handling

1. **API Keys:**
   - Store in environment variables
   - Never commit to Git
   - Rotate regularly (every 30 days)

2. **Token Encryption Key:**
   - Generated automatically if not provided
   - Stored in .env file
   - Used to encrypt stored tokens

3. **accounts.yaml Encryption:**
   - API keys encrypted with AES-256
   - Encryption key from environment variable
   - Decrypted in memory only

4. **Configuration Files:**
   - config.yaml: No secrets (safe to commit)
   - risk_config.yaml: No secrets (safe to commit)
   - accounts.yaml: Contains encrypted secrets (safe to commit if encrypted)
   - .env: Contains plaintext secrets (NEVER commit)

### .gitignore Configuration

```gitignore
# Environment variables (secrets)
.env
.env.local
.env.production

# Token storage
data/tokens.enc
data/*.enc

# Database
data/*.db
data/*.db-wal
data/*.db-shm

# Logs
logs/
*.log

# Backups
backups/
```

---

## 📝 Summary

**Configuration Files:**
- `config.yaml` - Master configuration (API, SignalR, error handling)
- `risk_config.yaml` - Risk rule configurations
- `accounts.yaml` - Account credentials (encrypted)
- `.env` - Environment variables (secrets, not committed)

**Key Features:**
- Hierarchical configuration precedence (env vars > config files > defaults)
- Comprehensive validation on load
- Hot reload support for most settings
- Secure secret management (encryption, environment variables)
- Detailed documentation for all settings

**Security:**
- API keys in environment variables
- Token encryption with AES-256
- Never commit .env files
- Rotate credentials regularly

---

**Document Status:** DRAFT - Ready for implementation
