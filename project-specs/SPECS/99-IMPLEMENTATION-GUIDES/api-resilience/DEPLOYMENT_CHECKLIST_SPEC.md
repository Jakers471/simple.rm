---
doc_id: GUIDE-006
title: Deployment Checklist Specification
version: 2.0
status: DRAFT
last_updated: 2025-10-22
purpose: Pre-deployment validation, production configuration, monitoring setup, and rollback procedures
dependencies: [API_RESILIENCE_OVERVIEW.md, CONFIGURATION_MASTER_SPEC.md]
---

# Deployment Checklist Specification

**Purpose:** Define complete deployment checklist to ensure production-ready system with proper validation, configuration, monitoring, and rollback capabilities.

---

## 📋 Table of Contents

1. [Pre-Deployment Validation](#pre-deployment-validation)
2. [Production Configuration](#production-configuration)
3. [Security Hardening](#security-hardening)
4. [Monitoring and Alerting Setup](#monitoring-and-alerting-setup)
5. [Deployment Process](#deployment-process)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Rollback Procedures](#rollback-procedures)
8. [Operational Runbook](#operational-runbook)

---

## ✅ Pre-Deployment Validation

### Code Quality Checks

```bash
# 1. Run all unit tests
pytest tests/unit/ -v --cov=src --cov-report=term

# Expected: 90%+ coverage, all tests pass
# ✅ Pass Criteria: 0 failures, 90%+ coverage

# 2. Run integration tests
pytest tests/integration/ -v

# Expected: All integration tests pass
# ✅ Pass Criteria: 0 failures

# 3. Run chaos engineering tests
pytest tests/chaos/ -v

# Expected: All chaos tests pass (network failures, token expiration)
# ✅ Pass Criteria: 0 failures

# 4. Run performance benchmarks
pytest tests/performance/ -v --benchmark-only

# Expected: Event latency <10ms, memory <100MB
# ✅ Pass Criteria: All benchmarks meet targets

# 5. Code linting
flake8 src/ --max-line-length=120 --ignore=E501,W503

# ✅ Pass Criteria: 0 linting errors

# 6. Type checking
mypy src/ --strict

# ✅ Pass Criteria: 0 type errors

# 7. Security scan
bandit -r src/ -ll

# ✅ Pass Criteria: 0 high/medium severity issues
```

### Acceptance Criteria Verification

**Phase 0 (API Resilience) Acceptance:**
- [ ] Token Manager: Tokens refresh automatically 2 hours before expiry
- [ ] Token Manager: Tokens stored encrypted (AES-256)
- [ ] Token Manager: Zero token expiration failures in testing
- [ ] SignalR Manager: All event handlers implemented (onconnected, onclose, onreconnecting, onreconnected)
- [ ] SignalR Manager: Exponential backoff working correctly
- [ ] SignalR Manager: Reconnection success rate >99%
- [ ] SignalR Manager: Zero message loss in reconnection tests
- [ ] Error Handler: All error codes mapped and documented
- [ ] Error Handler: Retry strategies work correctly
- [ ] Error Handler: Circuit breaker triggers at threshold
- [ ] Rate Limiter: Zero 429 errors in testing
- [ ] Rate Limiter: Request queuing works correctly
- [ ] Order Management: Zero duplicate orders in failure tests
- [ ] Order Management: Order verification detects status correctly
- [ ] Order Management: Idempotency prevents duplicates
- [ ] Order Management: Partial fills tracked accurately
- [ ] Testing: 90%+ unit test coverage
- [ ] Testing: All integration tests pass
- [ ] Testing: All chaos tests pass
- [ ] Testing: Performance benchmarks met

**Phase 1-4 Acceptance:**
- [ ] All 12 risk rules implemented and tested
- [ ] Event processing latency < 10ms
- [ ] Memory usage < 100 MB
- [ ] Trader CLI updates < 1 second
- [ ] Admin CLI fully functional
- [ ] Windows Service stable
- [ ] Documentation complete

### Environment Preparation

```bash
# 1. Create production environment
python -m venv venv_prod
source venv_prod/bin/activate  # Windows: venv_prod\Scripts\activate

# 2. Install production dependencies
pip install -r requirements.txt --no-dev

# 3. Verify Python version
python --version
# ✅ Required: Python 3.10+

# 4. Verify system dependencies
# - Windows 10/11 or Windows Server 2019/2022
# - 4 GB RAM minimum, 8 GB recommended
# - 1 GB free disk space
# - Internet connection for TopstepX API

# 5. Create directory structure
mkdir -p config data logs backups

# 6. Set file permissions
chmod 700 config/  # Config files (owner only)
chmod 700 data/    # Database (owner only)
chmod 755 logs/    # Logs (readable by others)
```

---

## 🔧 Production Configuration

### 1. config.yaml Production Settings

```yaml
# config/config.yaml - Production configuration

api:
  baseUrl: "https://gateway.topstepx.com"
  timeout: 30000

authentication:
  tokenRefresh:
    bufferSeconds: 7200  # 2 hours
    maxRetries: 3
  storage:
    type: "encrypted"
    encryption: "AES-256"
    keySource: "environment"
    storePath: "data/tokens.enc"

signalr:
  userHub:
    url: "https://rtc.topstepx.com/hubs/user"
    enabled: true
  marketHub:
    url: "https://rtc.topstepx.com/hubs/market"
    enabled: true
  reconnection:
    enabled: true
    maxAttempts: 10
    delays: [0, 2000, 10000, 30000, 60000]
  health:
    enabled: true
    pingInterval: 30000
    pingTimeout: 5000
    staleThreshold: 120000

errorHandling:
  retries:
    enabled: true
    maxAttempts: 5
    backoffBase: 1000
    backoffMultiplier: 2
  rateLimit:
    enabled: true
    history:
      requests: 50
      windowSeconds: 30
    general:
      requests: 200
      windowSeconds: 60
  circuitBreaker:
    enabled: true
    failureThreshold: 5
    timeout: 60000

orderManagement:
  verification:
    enabled: true
    timeout: 5000
  idempotency:
    enabled: true
    cacheTTL: 3600
  partialFills:
    enabled: true
    trackingTimeout: 60000

stateReconciliation:
  enabled: true
  onReconnect: true
  minInterval: 5000

database:
  path: "data/risk_manager.db"
  schemaVersion: 2
  connection:
    timeout: 30000
    journal_mode: "WAL"
    synchronous: "NORMAL"
  retention:
    dailyUnrealizedPnl: 7
    enforcementLogs: 30
    orderHistory: 90
    tradeHistory: 365
  backup:
    enabled: true
    interval: 86400  # Daily
    path: "backups/"
    keepCount: 7

logging:
  level: "INFO"  # Production: INFO, Debugging: DEBUG
  format: "json"
  rotation:
    enabled: true
    when: "midnight"
    backupCount: 30

monitoring:
  enabled: true
  metrics:
    enabled: true
    interval: 60000

system:
  timezone: "America/Chicago"
  dailyReset:
    enabled: true
    time: "17:00"
    timezone: "America/Chicago"
  shutdown:
    gracePeriod: 10000
    forceKillAfter: 30000

# Production: Disable development features
development:
  devMode: false
  debugLogging: false
  saveRawEvents: false
  testing:
    useMockApi: false
  profiling:
    enabled: false
```

### 2. risk_config.yaml Production Settings

```yaml
# config/risk_config.yaml - Production risk rules

global:
  strict_mode: false  # Normal mode
  logging_level: "INFO"

rules:
  max_contracts:
    enabled: true
    limit: 5  # Adjust per account
    count_type: "net"

  max_contracts_per_instrument:
    enabled: true
    limits:
      MNQ: 2
      NQ: 1
      ES: 1
      MES: 3
    enforcement: "reduce_to_limit"

  daily_realized_loss:
    enabled: true
    loss_limit: 500.00  # Adjust per account risk tolerance
    action: "CLOSE_ALL_AND_LOCKOUT"
    lockout_until: "daily_reset"

  daily_unrealized_loss:
    enabled: true
    loss_limit: 300.00  # Adjust per position size
    scope: "per_position"
    action: "CLOSE_POSITION"

  max_unrealized_profit:
    enabled: true
    mode: "profit_target"
    profit_target: 1000.00  # Adjust per strategy
    scope: "per_position"

  trade_frequency_limit:
    enabled: true
    max_trades: 30
    time_window_minutes: 60

  cooldown_after_loss:
    enabled: true
    loss_threshold: 100.00
    cooldown_seconds: 300

  no_stop_loss_grace:
    enabled: true
    grace_period_seconds: 30

  session_block_outside:
    enabled: true
    allowed_hours:
      start: "08:30"
      end: "15:00"
    timezone: "America/Chicago"

  auth_loss_guard:
    enabled: true

  symbol_blocks:
    enabled: true
    blocked_symbols:
      - "RTY"  # Adjust per risk tolerance
    close_existing: true

  trade_management:
    enabled: false  # Test thoroughly before enabling
```

### 3. Environment Variables (.env)

```bash
# .env - Production environment variables (DO NOT COMMIT)

# TopstepX Credentials (REQUIRED)
TOPSTEPX_API_KEY=your_production_api_key_here
TOPSTEPX_USERNAME=your_production_username_here

# Token Encryption Key (REQUIRED)
# Generate: python -c "import secrets; print('hex:' + secrets.token_hex(32))"
TOKEN_ENCRYPTION_KEY=hex:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

# Admin Password (REQUIRED)
# Generate: python -c "import bcrypt; print(bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode())"
ADMIN_PASSWORD_HASH=$2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUV

# Optional Overrides
LOG_LEVEL=INFO
DATABASE_PATH=data/risk_manager.db
CONFIG_PATH=config/config.yaml

# Production: Disable development mode
DEV_MODE=false
```

### 4. Configuration Validation

```bash
# Validate configuration before deployment
python scripts/validate_config.py

# Expected output:
# ✅ config.yaml: Valid
# ✅ risk_config.yaml: Valid
# ✅ .env: All required variables present
# ✅ Environment: Python 3.10+, dependencies installed
# ✅ Directories: config/, data/, logs/, backups/ exist
# ✅ Permissions: Correct file permissions set
```

---

## 🔒 Security Hardening

### Security Checklist

- [ ] **Credentials Management:**
  - [ ] API keys stored in environment variables (not config files)
  - [ ] Tokens encrypted with AES-256
  - [ ] Encryption key from environment variable
  - [ ] Admin password hashed with bcrypt
  - [ ] .env file NOT committed to Git
  - [ ] .gitignore includes .env, *.enc, *.db

- [ ] **File Permissions:**
  - [ ] config/ directory: 700 (owner only)
  - [ ] data/ directory: 700 (owner only)
  - [ ] logs/ directory: 755 (readable by others)
  - [ ] .env file: 600 (owner read/write only)
  - [ ] Database file: 600 (owner read/write only)
  - [ ] Encrypted token file: 600 (owner read/write only)

- [ ] **Network Security:**
  - [ ] API calls use HTTPS only
  - [ ] Certificate validation enabled
  - [ ] No insecure cipher suites
  - [ ] Firewall rules configured (allow outbound to TopstepX only)

- [ ] **Code Security:**
  - [ ] No hardcoded secrets
  - [ ] No SQL injection vulnerabilities (using parameterized queries)
  - [ ] No eval() or exec() calls
  - [ ] Input validation on all external data
  - [ ] Error messages don't expose sensitive data

- [ ] **Service Security:**
  - [ ] Windows Service runs as restricted user (not SYSTEM)
  - [ ] Service can only be stopped by administrators
  - [ ] Admin CLI requires password authentication
  - [ ] Admin CLI requires Windows admin privileges

### Security Scan

```bash
# Run security scan
bandit -r src/ -ll -o security_report.txt

# Expected: 0 high/medium severity issues
# ✅ Pass Criteria: No security vulnerabilities found

# Check for secrets in Git history
git secrets --scan-history

# Expected: No secrets found
# ✅ Pass Criteria: No credentials in Git
```

---

## 📊 Monitoring and Alerting Setup

### Monitoring Configuration

```yaml
# config/monitoring.yaml - Monitoring configuration

monitoring:
  enabled: true

  # Health checks
  health:
    enabled: true
    interval: 30000  # 30 seconds
    checks:
      - signalr_connection
      - token_validity
      - database_connection
      - circuit_breaker_state
      - memory_usage
      - disk_space

  # Metrics collection
  metrics:
    enabled: true
    interval: 60000  # 1 minute
    collect:
      # Latency metrics
      - event_processing_latency_p50
      - event_processing_latency_p95
      - event_processing_latency_p99
      - api_response_time_p50
      - api_response_time_p95

      # Throughput metrics
      - events_processed_per_second
      - api_requests_per_minute
      - orders_placed_per_hour

      # Reliability metrics
      - signalr_connection_uptime_percent
      - token_refresh_success_rate
      - api_error_rate
      - circuit_breaker_open_count

      # Business metrics
      - rule_breach_counts_by_rule
      - enforcement_action_counts
      - lockout_counts

      # Resource metrics
      - memory_usage_mb
      - cpu_usage_percent
      - database_size_mb
      - disk_space_remaining_mb

  # Alerting
  alerts:
    enabled: true
    channels:
      - type: "log"  # Always log alerts
        path: "logs/alerts.log"

      - type: "email"  # Optional: email alerts
        enabled: false
        smtp_host: "smtp.gmail.com"
        smtp_port: 587
        from_email: "alerts@example.com"
        to_emails:
          - "admin@example.com"

      - type: "webhook"  # Optional: webhook alerts
        enabled: false
        url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

    rules:
      # Critical alerts
      - name: "SignalR Connection Lost"
        condition: "signalr_connection_state == 'DISCONNECTED' for 60s"
        severity: "critical"
        message: "SignalR connection lost for >60 seconds"

      - name: "Token Expiration Imminent"
        condition: "token_expiry_in_seconds < 1800"
        severity: "critical"
        message: "Token expires in <30 minutes, refresh failing"

      - name: "Circuit Breaker Open"
        condition: "circuit_breaker_state == 'OPEN'"
        severity: "critical"
        message: "Circuit breaker opened, API calls blocked"

      - name: "Memory Usage High"
        condition: "memory_usage_mb > 150"
        severity: "warning"
        message: "Memory usage >150 MB (target <100 MB)"

      - name: "Database Size Large"
        condition: "database_size_mb > 1000"
        severity: "warning"
        message: "Database >1 GB, consider cleanup"

      - name: "Event Processing Slow"
        condition: "event_processing_latency_p95 > 50"
        severity: "warning"
        message: "95th percentile latency >50ms (target <10ms)"

      - name: "High Error Rate"
        condition: "api_error_rate > 0.05"
        severity: "critical"
        message: "API error rate >5%"

      # Business alerts
      - name: "Frequent Lockouts"
        condition: "lockout_counts > 5 in 1h"
        severity: "warning"
        message: "More than 5 lockouts in 1 hour"

      - name: "High Enforcement Rate"
        condition: "enforcement_action_counts > 20 in 1h"
        severity: "info"
        message: "More than 20 enforcement actions in 1 hour"
```

### Logging Configuration

```yaml
# config/logging.yaml - Production logging configuration

logging:
  level: "INFO"
  format: "json"

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
      level: "WARNING"

    errors:
      path: "logs/errors.log"
      maxSize: 10485760
      backupCount: 10
      level: "ERROR"

    alerts:
      path: "logs/alerts.log"
      maxSize: 5242880  # 5 MB
      backupCount: 10
      level: "WARNING"

  rotation:
    enabled: true
    when: "midnight"
    backupCount: 30
```

### Monitoring Dashboard (Optional)

```bash
# Install monitoring dashboard (optional)
pip install grafana-cli

# Setup Grafana dashboard
# - Data source: SQLite database
# - Panels: Event latency, API errors, memory usage, rule breaches
# - Refresh: Every 5 seconds

# Access dashboard: http://localhost:3000
```

---

## 🚀 Deployment Process

### Step-by-Step Deployment

```bash
# ============================================================================
# STEP 1: PRE-DEPLOYMENT VALIDATION
# ============================================================================

# 1.1: Run all tests
pytest tests/ -v --cov=src --cov-report=term
# ✅ Expected: All tests pass, 90%+ coverage

# 1.2: Security scan
bandit -r src/ -ll
# ✅ Expected: No high/medium severity issues

# 1.3: Configuration validation
python scripts/validate_config.py
# ✅ Expected: All validations pass

# ============================================================================
# STEP 2: BACKUP EXISTING SYSTEM (if upgrading)
# ============================================================================

# 2.1: Stop existing service
net stop RiskManagerService

# 2.2: Backup database
cp data/risk_manager.db backups/risk_manager_$(date +%Y%m%d_%H%M%S).db

# 2.3: Backup configuration
cp -r config/ backups/config_$(date +%Y%m%d_%H%M%S)/

# 2.4: Backup logs (optional)
cp -r logs/ backups/logs_$(date +%Y%m%d_%H%M%S)/

# ============================================================================
# STEP 3: INSTALL APPLICATION
# ============================================================================

# 3.1: Create deployment directory
mkdir -p /opt/risk-manager
cd /opt/risk-manager

# 3.2: Copy application files
cp -r src/ /opt/risk-manager/
cp requirements.txt /opt/risk-manager/

# 3.3: Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3.4: Copy configuration files
cp config/*.yaml /opt/risk-manager/config/
cp .env /opt/risk-manager/.env

# 3.5: Set file permissions
chmod 700 config/
chmod 700 data/
chmod 600 .env
chmod 600 config/accounts.yaml

# ============================================================================
# STEP 4: INITIALIZE DATABASE
# ============================================================================

# 4.1: Create database (first install only)
python scripts/init_database.py

# 4.2: Run migrations (if upgrading)
python scripts/migrate_database.py --from-version 1 --to-version 2

# 4.3: Verify database
python scripts/verify_database.py
# ✅ Expected: Schema v2, all tables present

# ============================================================================
# STEP 5: TEST IN CONSOLE MODE
# ============================================================================

# 5.1: Run daemon in console mode
python scripts/dev_run.py

# 5.2: In another terminal, test Trader CLI
python -m src.cli.trader.trader_main

# 5.3: In another terminal, test Admin CLI
python -m src.cli.admin.admin_main

# 5.4: Verify functionality:
#   - Token refresh works
#   - SignalR connection established
#   - Events received
#   - State persistence works
#   - Rules trigger correctly
#   - Trader CLI updates
#   - Admin CLI authentication works

# 5.5: Stop console mode (Ctrl+C)

# ============================================================================
# STEP 6: INSTALL WINDOWS SERVICE
# ============================================================================

# 6.1: Install service (requires admin privileges)
python scripts/install_service.py

# Expected output:
# ✅ Service installed: RiskManagerService
# ✅ Service configured to auto-start
# ✅ Service runs as: NT AUTHORITY\NetworkService

# 6.2: Verify service installation
sc qc RiskManagerService

# Expected output:
# SERVICE_NAME: RiskManagerService
# START_TYPE: AUTO_START
# SERVICE_START_NAME: NT AUTHORITY\NetworkService

# ============================================================================
# STEP 7: START SERVICE
# ============================================================================

# 7.1: Start service
net start RiskManagerService

# 7.2: Check service status
sc query RiskManagerService

# Expected output:
# STATE: RUNNING

# 7.3: Check logs
tail -f logs/daemon.log

# Expected output:
# [INFO] Application initialized successfully
# [INFO] Token Manager: Token valid until 2025-10-23 12:00:00
# [INFO] SignalR Manager: Connected to User Hub
# [INFO] SignalR Manager: Subscribed to positions, orders, trades
# [INFO] State Reconciler: Initial reconciliation complete
# [INFO] Risk Rules Engine: Monitoring started
```

---

## ✅ Post-Deployment Verification

### Verification Checklist

```bash
# ============================================================================
# IMMEDIATE VERIFICATION (0-5 minutes)
# ============================================================================

# 1. Service Running
sc query RiskManagerService
# ✅ Expected: STATE = RUNNING

# 2. Token Manager Initialized
grep "Token valid" logs/daemon.log
# ✅ Expected: Token expiry logged

# 3. SignalR Connected
grep "SignalR.*Connected" logs/daemon.log
# ✅ Expected: Connection success logged

# 4. Events Received
grep "GatewayUserPosition" logs/daemon.log
# ✅ Expected: At least one position event logged

# 5. No Critical Errors
grep "ERROR" logs/errors.log
# ✅ Expected: No critical errors (minor warnings acceptable)

# 6. Trader CLI Access
python -m src.cli.trader.trader_main
# ✅ Expected: CLI displays current positions/orders

# 7. Admin CLI Access
python -m src.cli.admin.admin_main
# ✅ Expected: Password prompt, authentication works

# ============================================================================
# SHORT-TERM VERIFICATION (1 hour)
# ============================================================================

# 8. Token Refresh Scheduled
grep "Token refresh scheduled" logs/daemon.log
# ✅ Expected: Refresh scheduled for ~22 hours from now

# 9. Health Monitoring Active
grep "Health check" logs/daemon.log
# ✅ Expected: Periodic health checks logged

# 10. No Reconnections
grep "reconnecting" logs/daemon.log
# ✅ Expected: Zero reconnection attempts (connection stable)

# 11. Rule Evaluations
grep "Rule evaluation" logs/daemon.log
# ✅ Expected: Rules evaluated for each event

# 12. Memory Usage
ps aux | grep risk_manager
# ✅ Expected: RSS < 100 MB

# 13. CPU Usage
top -p $(pgrep -f risk_manager)
# ✅ Expected: CPU < 5% (idle)

# ============================================================================
# LONG-TERM VERIFICATION (24 hours)
# ============================================================================

# 14. Token Refreshed Automatically
grep "Token refreshed successfully" logs/daemon.log
# ✅ Expected: Token refresh after ~22 hours

# 15. Daily Reset Executed
grep "Daily reset" logs/daemon.log
# ✅ Expected: Reset at 5 PM Chicago time

# 16. No Memory Leaks
# Check memory usage after 24 hours
ps aux | grep risk_manager
# ✅ Expected: RSS < 100 MB (no growth)

# 17. Database Size Reasonable
ls -lh data/risk_manager.db
# ✅ Expected: < 100 MB after 24 hours

# 18. Logs Rotated
ls -l logs/
# ✅ Expected: Old logs archived (.1, .2, etc.)

# 19. No Service Crashes
grep "crash" logs/daemon.log
# ✅ Expected: Zero crashes

# 20. Performance Benchmarks Met
# Check average event latency from metrics
python scripts/analyze_metrics.py --last-24h
# ✅ Expected: P95 latency < 10ms
```

---

## 🔄 Rollback Procedures

### Rollback Decision Criteria

**Rollback immediately if:**
- Service crashes repeatedly (>3 times in 10 minutes)
- Critical errors in logs (token expiration, API failures)
- Data loss detected (positions/orders missing)
- Performance degradation (latency >100ms)
- Security vulnerability discovered
- Risk rules not enforcing correctly

### Rollback Procedure

```bash
# ============================================================================
# STEP 1: STOP NEW SYSTEM
# ============================================================================

# 1.1: Stop service
net stop RiskManagerService

# 1.2: Verify stopped
sc query RiskManagerService
# ✅ Expected: STATE = STOPPED

# ============================================================================
# STEP 2: RESTORE BACKUP
# ============================================================================

# 2.1: Restore database
cp backups/risk_manager_20251022_120000.db data/risk_manager.db

# 2.2: Restore configuration
cp -r backups/config_20251022_120000/* config/

# 2.3: Restore code (if needed)
# Revert to previous Git commit
git checkout v1.0.0

# 2.4: Reinstall dependencies
pip install -r requirements.txt

# ============================================================================
# STEP 3: RESTART OLD SYSTEM
# ============================================================================

# 3.1: Reinstall service
python scripts/install_service.py

# 3.2: Start service
net start RiskManagerService

# 3.3: Verify running
sc query RiskManagerService
# ✅ Expected: STATE = RUNNING

# 3.4: Verify functionality
python -m src.cli.trader.trader_main
# ✅ Expected: CLI works, shows positions

# ============================================================================
# STEP 4: POST-ROLLBACK VALIDATION
# ============================================================================

# 4.1: Check logs for errors
tail -f logs/daemon.log
# ✅ Expected: No critical errors

# 4.2: Verify state consistency
python scripts/verify_state.py
# ✅ Expected: All positions/orders present

# 4.3: Test order placement
# Place test order via TopstepX platform
# ✅ Expected: Order detected and processed

# ============================================================================
# STEP 5: INVESTIGATE AND FIX
# ============================================================================

# 5.1: Collect logs from failed deployment
cp logs/daemon.log investigation/daemon_failed.log
cp logs/errors.log investigation/errors_failed.log

# 5.2: Analyze root cause
python scripts/analyze_failure.py investigation/

# 5.3: Fix issues in development environment
# 5.4: Test thoroughly
# 5.5: Redeploy when ready
```

---

## 📖 Operational Runbook

### Common Operations

**Daily Operations:**
```bash
# Check service status
sc query RiskManagerService

# View recent logs
tail -f logs/daemon.log

# Check memory/CPU usage
ps aux | grep risk_manager
```

**Weekly Operations:**
```bash
# Review metrics
python scripts/analyze_metrics.py --last-7d

# Check database size
ls -lh data/risk_manager.db

# Review enforcement logs
grep "Enforcement" logs/enforcement.log | wc -l

# Verify backups
ls -l backups/
```

**Monthly Operations:**
```bash
# Rotate API keys (if needed)
# 1. Generate new API key in TopstepX platform
# 2. Update .env file
# 3. Restart service

# Cleanup old backups
find backups/ -mtime +30 -delete

# Vacuum database
sqlite3 data/risk_manager.db "VACUUM;"

# Review security
bandit -r src/ -ll
```

### Troubleshooting Guide

**Problem: Service won't start**
```bash
# Check logs
cat logs/daemon.log | tail -100

# Check configuration
python scripts/validate_config.py

# Check credentials
# Verify TOPSTEPX_API_KEY in .env

# Check permissions
ls -l data/
# Ensure service account has read/write access
```

**Problem: SignalR disconnects frequently**
```bash
# Check network connectivity
ping rtc.topstepx.com

# Check logs
grep "SignalR" logs/daemon.log

# Increase reconnection delays (if needed)
# Edit config.yaml: signalr.reconnection.delays

# Check firewall rules
netsh advfirewall firewall show rule name=all
```

**Problem: High memory usage**
```bash
# Check current memory
ps aux | grep risk_manager

# Check for memory leaks
python scripts/profile_memory.py

# Reduce cache sizes (if needed)
# Edit config.yaml: performance.memory.maxCacheSize

# Restart service
net stop RiskManagerService
net start RiskManagerService
```

**Problem: Slow event processing**
```bash
# Check latency metrics
python scripts/analyze_metrics.py --metric=latency

# Check CPU usage
top -p $(pgrep -f risk_manager)

# Profile performance
python scripts/profile_performance.py

# Optimize configuration (if needed)
# Edit config.yaml: performance.*
```

---

## 📝 Summary

**Pre-Deployment:**
- ✅ All tests pass (unit, integration, chaos, performance)
- ✅ Security scan clean
- ✅ Configuration validated
- ✅ Acceptance criteria met

**Deployment:**
- ✅ Backup existing system
- ✅ Install new system
- ✅ Test in console mode
- ✅ Install Windows Service
- ✅ Verify post-deployment

**Monitoring:**
- ✅ Health checks configured
- ✅ Metrics collected
- ✅ Alerts configured
- ✅ Logs rotated

**Rollback:**
- ✅ Rollback criteria defined
- ✅ Rollback procedure documented
- ✅ Backups maintained

**Operations:**
- ✅ Daily/weekly/monthly checklists
- ✅ Troubleshooting guide
- ✅ Common operations documented

---

**Document Status:** DRAFT - Ready for implementation
