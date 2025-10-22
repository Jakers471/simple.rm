# ERROR CODE MAPPING SPECIFICATION

**doc_id:** ERR-001
**version:** 1.0
**status:** DRAFT
**addresses:** GAP-API-006 from ERRORS_AND_WARNINGS_CONSOLIDATED.md

---

## Overview

This specification defines comprehensive error code mappings between HTTP status codes, ProjectX Gateway API error codes, and application-level error handling. It addresses **GAP-API-006: Inadequate Error Code Documentation** by providing complete error code semantics, user-friendly messages, and retry strategies.

**Problem Statement:**
Current API documentation only shows success case (errorCode: 0) and generic 401 error. Missing comprehensive error code mapping for:
- Rate limit exceeded (429)
- Invalid parameters (400)
- Server errors (500+)
- Order rejection reasons
- Position close failures
- Insufficient balance errors
- Market closed errors

**Impact:**
Cannot properly handle or communicate errors to users, leading to poor user experience and unclear system behavior during failures.

---

## Requirements

### Functional Requirements

**FR-ERR-001:** System MUST map all HTTP status codes to application error codes
**FR-ERR-002:** System MUST provide user-friendly error messages for all error codes
**FR-ERR-003:** System MUST classify errors as retryable or non-retryable
**FR-ERR-004:** System MUST support localization keys for error messages
**FR-ERR-005:** System MUST log structured error context for debugging
**FR-ERR-006:** System MUST handle API-specific error codes (0-20+)
**FR-ERR-007:** System MUST sanitize PII from error logs

### Performance Requirements

**PR-ERR-001:** Error code lookup MUST complete in < 1ms
**PR-ERR-002:** Error logging overhead MUST be < 5ms
**PR-ERR-003:** Error message formatting MUST be < 2ms

### Security Requirements

**SR-ERR-001:** Error messages exposed to users MUST NOT contain sensitive data
**SR-ERR-002:** Detailed technical errors MUST be logged server-side only
**SR-ERR-003:** API keys, tokens, and credentials MUST be scrubbed from logs

---

## Error Code Mapping Table

### HTTP Status Code → Application Error Mapping

| HTTP | API Code | Error Name | Category | User Message | Technical Details | Retry? | Max Retries |
|------|----------|------------|----------|--------------|-------------------|--------|-------------|
| 200  | 0        | Success    | SUCCESS  | Operation successful | - | No | 0 |
| 200  | 1        | AuthFailure | AUTH | Authentication failed. Please log in again. | Invalid or expired token | Yes | 3 |
| 200  | 2        | InvalidRequest | VALIDATION | Invalid request parameters. | Missing or malformed fields | No | 0 |
| 200  | 3        | OrderRejected | TRADING | Order rejected by broker. | Insufficient margin, invalid symbol | No | 0 |
| 200  | 4        | PositionNotFound | TRADING | Position not found. | Position ID does not exist | No | 0 |
| 200  | 5        | InsufficientBalance | TRADING | Insufficient account balance. | Account balance < required margin | No | 0 |
| 200  | 6        | MarketClosed | TRADING | Market is currently closed. | Trading hours ended | No | 0 |
| 200  | 7        | SymbolNotFound | TRADING | Symbol not available. | Symbol not supported by broker | No | 0 |
| 200  | 8        | InvalidVolume | VALIDATION | Invalid trade volume. | Volume outside min/max limits | No | 0 |
| 200  | 9        | InvalidPrice | VALIDATION | Invalid price specified. | Price outside tick size or limits | No | 0 |
| 200  | 10       | OrderNotFound | TRADING | Order not found. | Order ID does not exist | No | 0 |
| 200  | 11       | PositionAlreadyClosed | TRADING | Position already closed. | Attempting to close non-existent position | No | 0 |
| 200  | 12       | StopLossInvalid | VALIDATION | Stop loss level is invalid. | SL too close to market or violates rules | No | 0 |
| 200  | 13       | TakeProfitInvalid | VALIDATION | Take profit level is invalid. | TP too close to market or violates rules | No | 0 |
| 200  | 14       | OrderExpired | TRADING | Order has expired. | Pending order exceeded expiration time | No | 0 |
| 200  | 15       | TooManyRequests | RATE_LIMIT | Too many requests. Please slow down. | Rate limit exceeded | Yes | 5 |
| 200  | 16       | DuplicateOrder | TRADING | Duplicate order detected. | Idempotency check failed | No | 0 |
| 200  | 17       | AccountDisabled | AUTH | Account is disabled. Contact support. | Account suspended or locked | No | 0 |
| 200  | 18       | MaintenanceMode | SYSTEM | System maintenance in progress. | Scheduled maintenance window | Yes | 10 |
| 200  | 19       | DataUnavailable | SYSTEM | Historical data unavailable. | Data service temporarily down | Yes | 3 |
| 200  | 20       | ServerError | SYSTEM | Internal server error. Please try again. | Unhandled exception on server | Yes | 3 |
| 400  | -        | BadRequest | VALIDATION | Invalid request format. | Malformed JSON, missing headers | No | 0 |
| 401  | -        | Unauthorized | AUTH | Unauthorized. Please log in. | Missing or invalid Authorization header | Yes | 3 |
| 403  | -        | Forbidden | AUTH | Access denied. | Valid token but insufficient permissions | No | 0 |
| 404  | -        | NotFound | ROUTING | Endpoint not found. | Invalid URL path | No | 0 |
| 429  | -        | RateLimitExceeded | RATE_LIMIT | Rate limit exceeded. Please wait. | Too many requests in time window | Yes | 5 |
| 500  | -        | InternalServerError | SYSTEM | Server error. Please try again. | Unhandled server exception | Yes | 3 |
| 502  | -        | BadGateway | NETWORK | Service temporarily unavailable. | Upstream service failure | Yes | 5 |
| 503  | -        | ServiceUnavailable | SYSTEM | Service unavailable. Please retry. | Server overloaded or down | Yes | 5 |
| 504  | -        | GatewayTimeout | NETWORK | Request timeout. Please retry. | Upstream service timeout | Yes | 3 |

---

## Order Rejection Reasons (ErrorCode: 3)

When `errorCode = 3` (OrderRejected), the API may provide additional context in `d.description` or `d.errorDescription`. Mapping:

| Rejection Reason | User Message | Retry? | Action Required |
|------------------|--------------|--------|-----------------|
| INSUFFICIENT_MARGIN | Insufficient margin for this trade. | No | Reduce position size or deposit funds |
| SYMBOL_NOT_TRADABLE | Symbol is not available for trading. | No | Choose different symbol |
| VOLUME_TOO_LOW | Trade volume below minimum. | No | Increase volume to meet minimum |
| VOLUME_TOO_HIGH | Trade volume exceeds maximum. | No | Reduce volume to allowed maximum |
| PRICE_OUT_OF_RANGE | Price is outside allowed range. | No | Adjust price within tick size limits |
| MARKET_CLOSED | Market is closed for this symbol. | No | Wait for market open or use different symbol |
| DUPLICATE_REQUEST | Duplicate order request detected. | No | Check existing orders before retrying |
| INVALID_STOP_LOSS | Stop loss level violates exchange rules. | No | Adjust stop loss to valid level |
| INVALID_TAKE_PROFIT | Take profit level violates exchange rules. | No | Adjust take profit to valid level |
| ORDER_TOO_CLOSE_TO_MARKET | Order price too close to current market price. | No | Adjust order price with proper distance |
| MAX_ORDERS_EXCEEDED | Maximum number of pending orders reached. | No | Cancel existing orders before placing new |

---

## Position Close Failure Codes (ErrorCode: 4)

When attempting to close positions via `/api/Order/execute` with `volume > 0` to close existing position:

| Failure Reason | User Message | Retry? | Action Required |
|----------------|--------------|--------|-----------------|
| POSITION_NOT_FOUND | Position does not exist or already closed. | No | Refresh positions list |
| POSITION_LOCKED | Position is locked due to pending modification. | Yes | Wait and retry after 2 seconds |
| INSUFFICIENT_LIQUIDITY | Insufficient market liquidity to close position. | Yes | Retry with limit order or smaller chunks |
| MARKET_CLOSED | Cannot close position while market is closed. | No | Wait for market open |
| CLOSE_ONLY_MODE | Account in close-only mode. | No | Contact support |
| PARTIAL_CLOSE_NOT_ALLOWED | Broker does not allow partial position closing. | No | Close entire position or none |

---

## Insufficient Balance Scenarios (ErrorCode: 5)

| Scenario | User Message | Retry? | Action Required |
|----------|--------------|--------|-----------------|
| NEW_ORDER_INSUFFICIENT_MARGIN | Insufficient margin to open new position. | No | Reduce position size or deposit funds |
| MODIFY_ORDER_INSUFFICIENT_MARGIN | Insufficient margin to modify order. | No | Cancel modification or deposit funds |
| PENDING_ORDER_MARGIN_CALL | Account in margin call. Cannot place orders. | No | Close positions or deposit funds immediately |
| NEGATIVE_BALANCE | Account balance is negative. | No | Deposit funds to restore positive balance |

---

## Market Closed Error Details (ErrorCode: 6)

| Market State | User Message | Retry? | Retry After |
|--------------|--------------|--------|-------------|
| PRE_MARKET_CLOSED | Market opens at {time}. | No | Calculate time to market open |
| POST_MARKET_CLOSED | Market closed for the day. Opens at {time}. | No | Next market open time |
| WEEKEND_CLOSED | Markets closed on weekends. Opens Monday at {time}. | No | Monday market open |
| HOLIDAY_CLOSED | Markets closed for {holiday}. Opens on {date}. | No | Next trading day |
| SYMBOL_HALTED | Trading halted for this symbol. | Yes | Check every 5 minutes |
| CIRCUIT_BREAKER | Trading suspended due to circuit breaker. | Yes | Check every 10 minutes |

---

## Error Response Format

All API errors MUST be returned in the following JSON format:

```json
{
  "d": {
    "errorCode": 3,
    "errorDescription": "ORDER_REJECTED: INSUFFICIENT_MARGIN",
    "errorContext": {
      "symbol": "EURUSD",
      "requestedVolume": 100000,
      "availableMargin": 1200.50,
      "requiredMargin": 2000.00
    },
    "timestamp": "2025-10-22T15:30:45.123Z",
    "requestId": "req_1234567890"
  }
}
```

---

## Error Message Localization

### Message Template System

All user-facing messages MUST support localization via message key:

```yaml
error_messages:
  en:
    AUTH_FAILURE: "Authentication failed. Please log in again."
    ORDER_REJECTED_INSUFFICIENT_MARGIN: "Insufficient margin for this trade. Available: ${availableMargin}, Required: ${requiredMargin}."
    MARKET_CLOSED: "Market is currently closed. Opens at ${nextOpenTime}."
  es:
    AUTH_FAILURE: "Error de autenticación. Por favor, inicie sesión nuevamente."
    ORDER_REJECTED_INSUFFICIENT_MARGIN: "Margen insuficiente para esta operación. Disponible: ${availableMargin}, Requerido: ${requiredMargin}."
    MARKET_CLOSED: "El mercado está cerrado. Abre a las ${nextOpenTime}."
```

---

## Error Logging Format

### Structured JSON Log Format

```json
{
  "timestamp": "2025-10-22T15:30:45.123Z",
  "level": "ERROR",
  "category": "API_ERROR",
  "errorCode": 3,
  "errorName": "OrderRejected",
  "httpStatus": 200,
  "message": "Order rejected due to insufficient margin",
  "context": {
    "module": "OrderService",
    "function": "placeOrder",
    "requestId": "req_1234567890",
    "userId": "user_***456",
    "accountId": "acc_***789",
    "symbol": "EURUSD",
    "volume": 100000,
    "availableMargin": 1200.50,
    "requiredMargin": 2000.00
  },
  "stackTrace": "[REDACTED in production]",
  "sanitized": true,
  "retryable": false
}
```

### PII Sanitization Rules

**MUST be sanitized/masked:**
- `userId`: Show only last 3 characters (`user_***456`)
- `accountId`: Show only last 3 characters (`acc_***789`)
- `email`: Mask username (`j***@example.com`)
- `apiKey`: Never log (use `[REDACTED]`)
- `token`: Never log (use `[REDACTED]`)
- `password`: Never log (use `[REDACTED]`)

**CAN be logged:**
- `symbol`, `volume`, `price`, `requestId`
- `timestamp`, `errorCode`, `httpStatus`
- `margin` values, `balance` (aggregated only)

---

## Configuration Schema

```yaml
errorMapping:
  # Enable detailed error logging
  detailedLogging: true

  # Log level for different error categories
  logLevels:
    AUTH: "WARN"
    VALIDATION: "INFO"
    TRADING: "WARN"
    SYSTEM: "ERROR"
    RATE_LIMIT: "WARN"
    NETWORK: "ERROR"

  # PII sanitization rules
  sanitization:
    enabled: true
    maskLength: 3  # Show last 3 characters
    redactedPlaceholder: "[REDACTED]"

  # Retry configuration per error code
  retryConfig:
    errorCode1:  # AuthFailure
      retryable: true
      maxRetries: 3
      backoffMs: [1000, 2000, 4000]

    errorCode15:  # TooManyRequests
      retryable: true
      maxRetries: 5
      backoffMs: [2000, 5000, 10000, 20000, 30000]

    errorCode18:  # MaintenanceMode
      retryable: true
      maxRetries: 10
      backoffMs: [5000, 10000, 30000, 60000]

  # Localization
  localization:
    defaultLanguage: "en"
    supportedLanguages: ["en", "es", "fr", "de"]
    messageTemplatesPath: "./locales/"
```

---

## Implementation Checklist

- [ ] Create ErrorCode enum with all 0-20+ codes
- [ ] Implement HTTP status → ErrorCode mapper
- [ ] Create user-friendly message templates
- [ ] Implement PII sanitization function
- [ ] Create structured error logger
- [ ] Add retry classification logic
- [ ] Implement localization support
- [ ] Create error context builder
- [ ] Add unit tests for all error codes
- [ ] Create error handling middleware
- [ ] Document all new error codes

---

## Validation Criteria

### Testing Requirements

1. **Error Code Coverage:** All 20+ error codes MUST have test cases
2. **Retry Logic:** Verify retryable vs non-retryable classification
3. **Message Formatting:** Test localization and template variable substitution
4. **PII Sanitization:** Verify sensitive data is masked in logs
5. **Performance:** Error handling overhead < 5ms per request
6. **HTTP Mapping:** All HTTP status codes correctly mapped

### Test Scenarios

```yaml
test_scenarios:
  - name: "Auth failure triggers retry"
    input:
      httpStatus: 200
      errorCode: 1
    expected:
      retryable: true
      maxRetries: 3
      userMessage: "Authentication failed. Please log in again."

  - name: "Insufficient margin is not retryable"
    input:
      httpStatus: 200
      errorCode: 5
    expected:
      retryable: false
      maxRetries: 0
      userMessage: "Insufficient account balance."

  - name: "PII sanitization in logs"
    input:
      userId: "user_abc123"
      accountId: "acc_xyz789"
    expected:
      loggedUserId: "user_***123"
      loggedAccountId: "acc_***789"
```

---

## References

- **ERRORS_AND_WARNINGS_CONSOLIDATED.md** - Section 5, GAP-API-006 (lines 159-175)
- **API-INTEGRATION-ANALYSIS.md** - Section 2.3 Error Handling & Resilience
- **RISK_CONFIG_YAML_SPEC.md** - External API configuration
- **RETRY_STRATEGY_SPEC.md** - Retry logic integration
- **ERROR_LOGGING_SPEC.md** - Logging format standards

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-22 | Error Handling Spec Writer | Initial draft addressing GAP-API-006 |

---

**END OF SPECIFICATION**
