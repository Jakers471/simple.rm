# ERROR LOGGING SPECIFICATION

**doc_id:** ERR-005
**version:** 1.0
**status:** DRAFT
**addresses:** Error logging standardization for all error handling specifications

---

## Overview

This specification defines structured error logging formats, PII sanitization rules, and monitoring integration for the Simple Risk Manager. It provides a consistent logging standard across all error handling mechanisms.

**Purpose:**
- Standardize error log format across all modules
- Define PII sanitization rules for GDPR/privacy compliance
- Specify log levels for different error categories
- Define error aggregation and monitoring hooks
- Enable efficient debugging and troubleshooting

---

## Requirements

### Functional Requirements

**FR-LOG-001:** All errors MUST be logged in structured JSON format
**FR-LOG-002:** System MUST sanitize PII from all logs
**FR-LOG-003:** System MUST support configurable log levels per module
**FR-LOG-004:** System MUST provide correlation IDs for request tracing
**FR-LOG-005:** System MUST log error context (stack trace, request data)
**FR-LOG-006:** System MUST support log rotation and archival
**FR-LOG-007:** System MUST integrate with monitoring systems

### Performance Requirements

**PR-LOG-001:** Logging overhead MUST be < 5ms per log entry
**PR-LOG-002:** PII sanitization MUST be < 1ms per field
**PR-LOG-003:** Log file writes MUST be asynchronous (non-blocking)

### Security Requirements

**SR-LOG-001:** PII MUST be masked/redacted in all logs
**SR-LOG-002:** Credentials MUST NEVER be logged
**SR-LOG-003:** Log files MUST have restricted permissions (owner read/write only)
**SR-LOG-004:** Log retention MUST comply with data retention policies

---

## Structured JSON Log Format

### Standard Log Entry Schema

```json
{
  "timestamp": "2025-10-22T15:30:45.123Z",
  "level": "ERROR",
  "logger": "OrderService",
  "message": "Failed to place order due to insufficient margin",
  "correlationId": "req_1729613445123_abc123",
  "sessionId": "session_xyz789",
  "context": {
    "module": "OrderService",
    "function": "placeOrder",
    "lineNumber": 142,
    "userId": "user_***456",
    "accountId": "acc_***789",
    "symbol": "EURUSD",
    "volume": 100000,
    "requestedAction": "BUY"
  },
  "error": {
    "name": "OrderRejectedError",
    "code": "ERR_ORDER_003",
    "apiErrorCode": 3,
    "httpStatus": 200,
    "message": "Insufficient margin for trade",
    "details": {
      "availableMargin": 1200.50,
      "requiredMargin": 2000.00,
      "shortfall": 799.50
    },
    "retryable": false
  },
  "stackTrace": "[SANITIZED]",
  "environment": "production",
  "version": "1.0.0",
  "hostname": "risk-manager-01",
  "pid": 12345
}
```

### Log Entry Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timestamp | ISO8601 | Yes | UTC timestamp with milliseconds |
| level | string | Yes | Log level: DEBUG, INFO, WARN, ERROR, FATAL |
| logger | string | Yes | Logger name (module/service) |
| message | string | Yes | Human-readable error message |
| correlationId | string | Yes | Unique request identifier |
| sessionId | string | No | User session identifier (if applicable) |
| context | object | Yes | Contextual information about the operation |
| error | object | Yes | Detailed error information |
| stackTrace | string | No | Stack trace (sanitized in production) |
| environment | string | Yes | Environment: development, staging, production |
| version | string | Yes | Application version |
| hostname | string | Yes | Server hostname |
| pid | number | Yes | Process ID |

---

## Log Levels

### Level Definitions

```yaml
logLevels:
  DEBUG:
    severity: 10
    description: "Detailed diagnostic information for debugging"
    use: "Development only, never in production"
    examples:
      - "Request payload: {...}"
      - "Variable values at checkpoint"
      - "API response details"

  INFO:
    severity: 20
    description: "General informational messages"
    use: "Significant events, successful operations"
    examples:
      - "Order placed successfully: orderId=123"
      - "Risk check passed for position 456"
      - "Token refreshed successfully"

  WARN:
    severity: 30
    description: "Warning messages for potentially harmful situations"
    use: "Recoverable errors, degraded service"
    examples:
      - "Rate limit approaching: 90% of quota used"
      - "Token expires in 30 minutes"
      - "Circuit breaker in HALF_OPEN state"

  ERROR:
    severity: 40
    description: "Error events that might still allow app to continue"
    use: "Operation failures, API errors"
    examples:
      - "Failed to place order: insufficient margin"
      - "Position close failed: market closed"
      - "API request timeout after 3 retries"

  FATAL:
    severity: 50
    description: "Severe errors causing application termination"
    use: "Critical failures, data corruption"
    examples:
      - "Database connection lost"
      - "Unable to authenticate (all retries exhausted)"
      - "Configuration file corrupted"
```

### Log Level Configuration by Module

```yaml
logLevelConfig:
  # Global default
  default: "INFO"

  # Module-specific overrides
  modules:
    OrderService: "WARN"         # Only warnings and errors
    RiskRuleEngine: "INFO"       # Info and above
    ApiClient: "ERROR"           # Only errors
    TokenManager: "WARN"         # Warnings and errors
    DatabaseService: "ERROR"     # Only errors
    CircuitBreaker: "INFO"       # Info and above
    RateLimiter: "WARN"          # Warnings and errors
    SignalRConnection: "INFO"    # Info and above

  # Category-specific overrides
  categories:
    authentication: "WARN"
    trading: "INFO"
    riskManagement: "INFO"
    networking: "ERROR"
    database: "ERROR"
```

---

## PII Sanitization Rules

### Sensitive Data Categories

```yaml
piiSanitization:
  enabled: true
  redactedPlaceholder: "[REDACTED]"
  maskedSuffix: 3  # Show last 3 characters

  # Always redact (never log)
  alwaysRedact:
    - password
    - apiKey
    - apiSecret
    - token
    - accessToken
    - refreshToken
    - authorization
    - privateKey
    - secret
    - credentials
    - sessionToken

  # Mask (show partial)
  mask:
    userId:
      method: "suffix"
      showLast: 3
      example: "user_abc123" → "user_***123"

    accountId:
      method: "suffix"
      showLast: 3
      example: "acc_xyz789" → "acc_***789"

    email:
      method: "email"
      example: "john.doe@example.com" → "j***@example.com"

    ipAddress:
      method: "prefix"
      showFirst: 2
      example: "192.168.1.100" → "192.168.*.*"

    phoneNumber:
      method: "suffix"
      showLast: 4
      example: "+1-555-123-4567" → "***-***-4567"

  # Safe to log (aggregated data)
  safeToLog:
    - symbol
    - volume
    - price
    - timestamp
    - orderId
    - positionId
    - errorCode
    - httpStatus
    - requestId
    - correlationId
    - margin (aggregated values)
    - balance (aggregated values)
```

### Sanitization Implementation

```typescript
interface SanitizationRule {
  field: string;
  method: 'redact' | 'mask_suffix' | 'mask_prefix' | 'mask_email';
  showCharacters?: number;
}

function sanitizeLogData(data: any): any {
  if (typeof data !== 'object' || data === null) {
    return data;
  }

  const sanitized = Array.isArray(data) ? [] : {};

  for (const [key, value] of Object.entries(data)) {
    const lowerKey = key.toLowerCase();

    // 1. Always redact sensitive fields
    if (shouldRedact(lowerKey)) {
      sanitized[key] = '[REDACTED]';
      continue;
    }

    // 2. Mask PII fields
    if (shouldMask(lowerKey)) {
      sanitized[key] = maskField(key, value);
      continue;
    }

    // 3. Recursively sanitize nested objects
    if (typeof value === 'object') {
      sanitized[key] = sanitizeLogData(value);
      continue;
    }

    // 4. Safe to log as-is
    sanitized[key] = value;
  }

  return sanitized;
}

function shouldRedact(fieldName: string): boolean {
  const redactList = [
    'password', 'apikey', 'apisecret', 'token', 'accesstoken',
    'refreshtoken', 'authorization', 'privatekey', 'secret',
    'credentials', 'sessiontoken'
  ];

  return redactList.some(term => fieldName.includes(term));
}

function shouldMask(fieldName: string): boolean {
  const maskList = ['userid', 'accountid', 'email', 'ipaddress', 'phone'];
  return maskList.some(term => fieldName.includes(term));
}

function maskField(fieldName: string, value: string): string {
  if (typeof value !== 'string') return value;

  const lowerField = fieldName.toLowerCase();

  if (lowerField.includes('email')) {
    return maskEmail(value);
  }

  if (lowerField.includes('userid') || lowerField.includes('accountid')) {
    return maskSuffix(value, 3);
  }

  if (lowerField.includes('ipaddress')) {
    return maskIpAddress(value);
  }

  return value;
}

function maskEmail(email: string): string {
  const [username, domain] = email.split('@');
  if (!domain) return email;

  const maskedUsername = username.charAt(0) + '***';
  return `${maskedUsername}@${domain}`;
}

function maskSuffix(value: string, showLast: number): string {
  if (value.length <= showLast) return value;

  const prefix = value.substring(0, value.lastIndexOf('_') + 1);
  const suffix = value.slice(-showLast);

  return `${prefix}***${suffix}`;
}

function maskIpAddress(ip: string): string {
  const parts = ip.split('.');
  if (parts.length !== 4) return ip;

  return `${parts[0]}.${parts[1]}.*.*`;
}
```

---

## Correlation and Tracing

### Request Correlation

```typescript
interface RequestContext {
  correlationId: string;       // Unique per request
  sessionId?: string;          // User session
  parentRequestId?: string;    // For nested requests
  traceId?: string;            // Distributed tracing
}

function generateCorrelationId(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 10);
  return `req_${timestamp}_${random}`;
}

function logWithCorrelation(
  level: LogLevel,
  message: string,
  context: RequestContext,
  data?: any
): void {
  const logEntry = {
    timestamp: new Date().toISOString(),
    level: level,
    message: message,
    correlationId: context.correlationId,
    sessionId: context.sessionId,
    parentRequestId: context.parentRequestId,
    traceId: context.traceId,
    ...sanitizeLogData(data)
  };

  writeLog(logEntry);
}
```

---

## Error Aggregation

### Error Grouping Strategy

```yaml
errorAggregation:
  enabled: true
  windowSeconds: 60

  # Group similar errors
  groupingRules:
    - field: "error.code"
      deduplicateCount: 10  # Only log every 10th occurrence

    - field: "error.apiErrorCode"
      deduplicateCount: 5

    - field: "context.function"
      deduplicateCount: 3

  # Summary logs
  summaryInterval: 300  # 5 minutes
  summaryFormat: |
    Error Summary (last 5 minutes):
    - OrderRejected (code 3): 15 occurrences
    - RateLimitExceeded (code 15): 23 occurrences
    - NetworkTimeout: 7 occurrences
```

### Deduplication Implementation

```typescript
interface ErrorBucket {
  signature: string;  // Unique error signature
  count: number;
  firstSeen: number;
  lastSeen: number;
  sample: LogEntry;  // First occurrence
}

class ErrorDeduplicator {
  private buckets: Map<string, ErrorBucket> = new Map();
  private deduplicateThreshold = 10;

  shouldLog(logEntry: LogEntry): boolean {
    const signature = this.getErrorSignature(logEntry);

    let bucket = this.buckets.get(signature);
    if (!bucket) {
      bucket = {
        signature,
        count: 0,
        firstSeen: Date.now(),
        lastSeen: Date.now(),
        sample: logEntry
      };
      this.buckets.set(signature, bucket);
    }

    bucket.count++;
    bucket.lastSeen = Date.now();

    // Log first occurrence, then every Nth occurrence
    if (bucket.count === 1 || bucket.count % this.deduplicateThreshold === 0) {
      return true;
    }

    return false;
  }

  private getErrorSignature(logEntry: LogEntry): string {
    return `${logEntry.error.code}:${logEntry.context.function}`;
  }

  getSummary(): string {
    const lines = ['Error Summary:'];

    for (const [signature, bucket] of this.buckets) {
      lines.push(
        `- ${signature}: ${bucket.count} occurrences (${bucket.firstSeen} - ${bucket.lastSeen})`
      );
    }

    return lines.join('\n');
  }
}
```

---

## Log Rotation and Archival

### Rotation Configuration

```yaml
logRotation:
  enabled: true

  # File-based logging
  file:
    path: "./logs"
    filename: "simple-risk-manager.log"
    maxSize: "100M"         # Rotate when file reaches 100MB
    maxFiles: 30            # Keep 30 rotated files
    compress: true          # Compress rotated files
    datePattern: "YYYY-MM-DD"

  # Archive old logs
  archive:
    enabled: true
    retentionDays: 90       # Keep logs for 90 days
    archivePath: "./logs/archive"
    compress: true
```

---

## Monitoring Integration

### Monitoring Hooks

```yaml
monitoring:
  enabled: true

  # Metrics
  metrics:
    enabled: true
    provider: "prometheus"  # or "cloudwatch", "datadog"

    # Metrics to track
    errorCount:
      type: "counter"
      labels: ["level", "module", "errorCode"]

    errorRate:
      type: "gauge"
      labels: ["module"]

    logVolume:
      type: "counter"
      labels: ["level"]

  # Alerting
  alerts:
    enabled: true
    provider: "pagerduty"  # or "slack", "email"

    rules:
      - name: "High error rate"
        condition: "error_rate > 10 per minute"
        severity: "critical"
        notification: ["pagerduty", "slack"]

      - name: "Fatal errors"
        condition: "level = FATAL"
        severity: "critical"
        notification: ["pagerduty", "email"]

      - name: "Circuit breaker open"
        condition: "circuit_breaker_state = OPEN"
        severity: "warning"
        notification: ["slack"]
```

---

## Configuration Schema

```yaml
logging:
  # Global settings
  enabled: true
  level: "INFO"
  format: "json"  # or "text"

  # Output destinations
  outputs:
    - type: "console"
      enabled: true
      level: "INFO"

    - type: "file"
      enabled: true
      level: "WARN"
      path: "./logs/error.log"
      rotation:
        maxSize: "100M"
        maxFiles: 30

    - type: "syslog"
      enabled: false
      host: "localhost"
      port: 514

  # PII sanitization
  sanitization:
    enabled: true
    redactedPlaceholder: "[REDACTED]"
    maskedSuffix: 3

  # Error aggregation
  aggregation:
    enabled: true
    windowSeconds: 60
    deduplicateThreshold: 10

  # Monitoring
  monitoring:
    enabled: true
    metricsProvider: "prometheus"
    alertProvider: "slack"
```

---

## Implementation Checklist

- [ ] Create structured logger with JSON output
- [ ] Implement PII sanitization functions
- [ ] Add correlation ID generation and tracking
- [ ] Create error deduplication mechanism
- [ ] Implement log rotation
- [ ] Add monitoring hooks (metrics, alerts)
- [ ] Create log level configuration
- [ ] Implement async log writing
- [ ] Add error aggregation and summary
- [ ] Create unit tests for sanitization
- [ ] Test log rotation
- [ ] Test monitoring integration

---

## Validation Criteria

### Test Scenarios

```yaml
test_scenarios:
  - name: "PII sanitization"
    input:
      userId: "user_abc123"
      password: "secret123"
      email: "john@example.com"
    expected:
      userId: "user_***123"
      password: "[REDACTED]"
      email: "j***@example.com"

  - name: "Error deduplication"
    actions:
      - log error (code 3) × 10
    expected:
      logged_count: 1  # First occurrence only

  - name: "Correlation tracking"
    actions:
      - create request (correlationId: req_123)
      - log error
      - log warning
    expected:
      all_logs_have_same_correlationId: true
```

---

## References

- **ERROR_CODE_MAPPING_SPEC.md** - Error code definitions
- **CIRCUIT_BREAKER_SPEC.md** - Circuit breaker state logging
- **RATE_LIMITING_SPEC.md** - Rate limit event logging
- **RETRY_STRATEGY_SPEC.md** - Retry attempt logging

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-22 | Error Handling Spec Writer | Initial draft |

---

**END OF SPECIFICATION**
