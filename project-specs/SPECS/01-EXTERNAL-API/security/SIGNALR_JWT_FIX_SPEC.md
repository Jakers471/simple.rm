# SignalR JWT Security Fix Specification

**doc_id:** SEC-003
**version:** 1.0
**status:** DRAFT
**priority:** HIGH
**addresses:** SEC-API-001 from ERRORS_AND_WARNINGS_CONSOLIDATED.md

## Overview

This specification defines the secure method for authenticating SignalR connections without exposing JWT tokens in query strings. Currently, the TradeStation API example code passes tokens via query parameters, which exposes them in server logs, browser history, and proxy logs.

## Problem Statement

**From SEC-API-001:**
- SignalR connection uses query string for authentication: `?access_token=YOUR_JWT_TOKEN`
- **Risks:**
  - Tokens logged in server access logs
  - Tokens exposed in browser history
  - Tokens visible in proxy logs
  - Network monitoring can intercept tokens
  - Tokens persist in URL caches
- Current example code shows both query string AND `accessTokenFactory`, causing confusion

## Requirements

### Functional Requirements

**FR-1: Remove Query String Token**
- System MUST NOT pass tokens via URL query parameters
- SignalR connection URL MUST NOT contain `access_token` parameter
- System MUST remove any query string token usage from codebase

**FR-2: Use accessTokenFactory Exclusively**
- System MUST implement `accessTokenFactory` function for token provision
- `accessTokenFactory` MUST return valid JWT token at connection time
- `accessTokenFactory` MUST handle token refresh transparently

**FR-3: Authorization Header Support**
- System SHOULD attempt to use `Authorization: Bearer <token>` header if supported
- System MUST verify SignalR library supports header-based authentication
- System MUST fall back to `accessTokenFactory` if headers not supported

**FR-4: Token Refresh Integration**
- `accessTokenFactory` MUST integrate with TokenManager (TOKEN_REFRESH_STRATEGY_SPEC.md)
- `accessTokenFactory` MUST return fresh token if current token near expiry
- `accessTokenFactory` MUST trigger refresh if needed before returning token

**FR-5: Logging Sanitization**
- System MUST sanitize tokens from all log messages
- System MUST NOT log SignalR connection URLs with tokens
- System MUST redact tokens in error messages and debug output

### Non-Functional Requirements

**NFR-1: Security**
- Token transmission MUST use HTTPS only
- Token MUST NOT appear in any URL
- Token MUST NOT be cached by browser or proxies
- Token MUST be transmitted in request headers only

**NFR-2: Compatibility**
- Solution MUST work with Microsoft SignalR JavaScript client v7.0+
- Solution MUST work with Microsoft SignalR .NET client v7.0+
- Solution MUST be compatible with TradeStation API SignalR implementation

**NFR-3: Performance**
- `accessTokenFactory` MUST complete in < 100ms (P95)
- Token retrieval MUST NOT block connection establishment
- Token refresh during connection MUST NOT cause disconnection

**NFR-4: Observability**
- System MUST log SignalR authentication attempts (with sanitized tokens)
- System MUST log authentication failures
- System MUST expose metrics for authentication success/failure rate

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  SignalRConnectionManager                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Connection Builder                                  │   │
│  │  - build_connection() -> HubConnection               │   │
│  │  - configure_authentication()                        │   │
│  │  - configure_reconnection()                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  accessTokenFactory                                  │   │
│  │  - get_token() -> str                                │   │
│  │  - refresh_if_needed() -> str                        │   │
│  │  - handle_errors() -> str                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Token Sanitizer                                     │   │
│  │  - sanitize_url(url: str) -> str                     │   │
│  │  - sanitize_log(message: str) -> str                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ TokenManager │ (from TOKEN_REFRESH_STRATEGY_SPEC.md)
                   │ - get_token()│
                   │ - refresh()  │
                   └──────────────┘
```

### Authentication Flow Diagram

```
SignalRClient    accessTokenFactory    TokenManager    TradeStationAPI
    │                   │                    │                │
    │─start()──────────►│                    │                │
    │                   │                    │                │
    │                   ├──get_token()──────►│                │
    │                   │                    │                │
    │                   │  [Check if token   │                │
    │                   │   near expiry]     │                │
    │                   │                    │                │
    │                   │  [< 2hrs to expiry]│                │
    │                   │                    │                │
    │                   │                    ├──refresh()────►│
    │                   │                    │◄───new_token───│
    │                   │                    │                │
    │                   │◄───return_token────┤                │
    │                   │                    │                │
    │◄──token───────────┤                    │                │
    │                   │                    │                │
    │──negotiate────────┼────────────────────┼───────────────►│
    │  (with Bearer token in Authorization header)            │
    │◄─connection_info──┼────────────────────┼────────────────│
    │                   │                    │                │
    │──connect (WSS)────┼────────────────────┼───────────────►│
    │◄─connected────────┼────────────────────┼────────────────│
```

### Before vs After Comparison

**BEFORE (Insecure):**
```javascript
// ❌ INSECURE: Token in URL query string
const connection = new HubConnection(
  "wss://sim-api.tradestation.com/v3/brokerage/stream" +
  "?access_token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."  // ❌ Exposed in logs!
);

// Token visible in:
// - Server access logs
// - Browser history
// - Proxy logs
// - Network monitoring tools
```

**AFTER (Secure):**
```javascript
// ✅ SECURE: Token provided via accessTokenFactory
const connection = new HubConnection(
  "wss://sim-api.tradestation.com/v3/brokerage/stream",  // ✅ No token in URL
  {
    accessTokenFactory: async () => {
      // Token retrieved securely from TokenManager
      const token = await tokenManager.getToken();
      return token;
    }
  }
);

// Token transmitted in Authorization header:
// Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
// ✅ Not logged in server access logs
// ✅ Not in browser history
// ✅ Not in proxy logs
```

## Implementation Examples

### JavaScript/TypeScript Implementation

```typescript
import { HubConnectionBuilder, HubConnection, LogLevel } from '@microsoft/signalr';
import { TokenManager } from './token_manager';

/**
 * SignalR Connection Manager with Secure Authentication
 */
class SignalRConnectionManager {
  private connection: HubConnection | null = null;
  private tokenManager: TokenManager;
  private hubUrl: string;

  constructor(tokenManager: TokenManager) {
    this.tokenManager = tokenManager;
    // ✅ SECURE: No token in base URL
    this.hubUrl = 'wss://sim-api.tradestation.com/v3/brokerage/stream';
  }

  /**
   * Build SignalR connection with secure authentication
   */
  public async buildConnection(): Promise<HubConnection> {
    this.connection = new HubConnectionBuilder()
      .withUrl(this.hubUrl, {
        // ✅ SECURE: Token provided via factory function
        accessTokenFactory: async () => {
          return await this.getSecureToken();
        },
        // Additional options
        skipNegotiation: false,
        transport: 1 // WebSockets only
      })
      .withAutomaticReconnect([0, 2000, 10000, 30000, 60000])
      .configureLogging(LogLevel.Information)
      .build();

    // Configure event handlers
    this.configureEventHandlers();

    return this.connection;
  }

  /**
   * Secure token retrieval with refresh logic
   */
  private async getSecureToken(): Promise<string> {
    try {
      // Get token from TokenManager (handles refresh automatically)
      const token = await this.tokenManager.getToken();

      // Validate token before returning
      if (!token || token.length === 0) {
        throw new Error('Empty token received from TokenManager');
      }

      // Log sanitized token (for debugging)
      console.log(`Token retrieved for SignalR: ${this.sanitizeToken(token)}`);

      return token;
    } catch (error) {
      console.error('Failed to retrieve token for SignalR:', error);
      throw error;
    }
  }

  /**
   * Sanitize token for logging (show only first/last 4 chars)
   */
  private sanitizeToken(token: string): string {
    if (!token || token.length < 10) {
      return '[REDACTED]';
    }
    return `${token.substring(0, 4)}...${token.substring(token.length - 4)}`;
  }

  /**
   * Configure SignalR event handlers
   */
  private configureEventHandlers(): void {
    if (!this.connection) return;

    // Reconnecting handler
    this.connection.onreconnecting((error) => {
      console.warn('SignalR reconnecting:', error?.message || 'Unknown reason');
      // Token will be refreshed automatically via accessTokenFactory
    });

    // Reconnected handler
    this.connection.onreconnected((connectionId) => {
      console.info(`SignalR reconnected with connection ID: ${connectionId}`);
      // accessTokenFactory was called again with fresh token
    });

    // Close handler
    this.connection.onclose((error) => {
      if (error) {
        console.error('SignalR connection closed with error:', error.message);
        // Check if error is due to authentication failure
        if (error.message.includes('401') || error.message.includes('Unauthorized')) {
          console.error('Authentication failed - token may be expired');
          // Trigger token refresh and reconnection
          this.handleAuthenticationFailure();
        }
      } else {
        console.info('SignalR connection closed normally');
      }
    });
  }

  /**
   * Handle authentication failure during connection
   */
  private async handleAuthenticationFailure(): Promise<void> {
    console.log('Handling authentication failure - refreshing token');
    try {
      // Force token refresh
      await this.tokenManager.refreshToken();

      // Attempt to reconnect with new token
      if (this.connection) {
        await this.connection.start();
        console.log('Reconnected successfully with refreshed token');
      }
    } catch (error) {
      console.error('Failed to recover from authentication failure:', error);
      // Escalate to system monitoring/alerting
      throw error;
    }
  }

  /**
   * Start SignalR connection
   */
  public async start(): Promise<void> {
    if (!this.connection) {
      await this.buildConnection();
    }

    try {
      await this.connection!.start();
      console.log('SignalR connection established successfully');
    } catch (error) {
      console.error('Failed to start SignalR connection:', error);
      throw error;
    }
  }

  /**
   * Stop SignalR connection
   */
  public async stop(): Promise<void> {
    if (this.connection) {
      await this.connection.stop();
      console.log('SignalR connection stopped');
    }
  }
}

export default SignalRConnectionManager;
```

### Python Implementation (signalrcore library)

```python
import asyncio
from signalrcore.hub_connection_builder import HubConnectionBuilder
from typing import Callable
import logging

class SignalRConnectionManager:
    """SignalR Connection Manager with Secure Authentication"""

    def __init__(self, token_manager):
        self.token_manager = token_manager
        # ✅ SECURE: No token in base URL
        self.hub_url = "wss://sim-api.tradestation.com/v3/brokerage/stream"
        self.connection = None
        self.logger = logging.getLogger(__name__)

    def build_connection(self):
        """Build SignalR connection with secure authentication"""

        # ✅ SECURE: Token provided via headers, not query string
        self.connection = HubConnectionBuilder() \
            .with_url(
                self.hub_url,
                options={
                    "access_token_factory": self._get_secure_token,
                    "skip_negotiation": False,
                    "headers": {
                        # Token will be added to Authorization header automatically
                    }
                }
            ) \
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 10,
                "reconnect_interval": 5,
                "max_attempts": 5
            }) \
            .build()

        # Configure event handlers
        self._configure_event_handlers()

        return self.connection

    async def _get_secure_token(self) -> str:
        """Secure token retrieval with refresh logic"""
        try:
            # Get token from TokenManager (handles refresh automatically)
            token = await self.token_manager.get_token()

            # Validate token before returning
            if not token:
                raise ValueError("Empty token received from TokenManager")

            # Log sanitized token (for debugging)
            self.logger.info(f"Token retrieved for SignalR: {self._sanitize_token(token)}")

            return token
        except Exception as e:
            self.logger.error(f"Failed to retrieve token for SignalR: {e}")
            raise

    def _sanitize_token(self, token: str) -> str:
        """Sanitize token for logging (show only first/last 4 chars)"""
        if not token or len(token) < 10:
            return "[REDACTED]"
        return f"{token[:4]}...{token[-4:]}"

    def _configure_event_handlers(self):
        """Configure SignalR event handlers"""

        # Reconnecting handler
        self.connection.on_reconnecting(lambda:
            self.logger.warning("SignalR reconnecting...")
        )

        # Reconnected handler
        self.connection.on_reconnected(lambda connection_id:
            self.logger.info(f"SignalR reconnected with ID: {connection_id}")
        )

        # Close handler
        self.connection.on_close(lambda:
            self.logger.info("SignalR connection closed")
        )

        # Error handler
        self.connection.on_error(lambda error:
            self._handle_connection_error(error)
        )

    def _handle_connection_error(self, error):
        """Handle connection errors"""
        self.logger.error(f"SignalR connection error: {error}")

        # Check if error is due to authentication failure
        if "401" in str(error) or "Unauthorized" in str(error):
            self.logger.error("Authentication failed - token may be expired")
            # Trigger token refresh and reconnection
            asyncio.create_task(self._handle_authentication_failure())

    async def _handle_authentication_failure(self):
        """Handle authentication failure during connection"""
        self.logger.info("Handling authentication failure - refreshing token")
        try:
            # Force token refresh
            await self.token_manager.refresh_token()

            # Attempt to reconnect with new token
            if self.connection:
                self.connection.start()
                self.logger.info("Reconnected successfully with refreshed token")
        except Exception as e:
            self.logger.error(f"Failed to recover from authentication failure: {e}")
            raise

    def start(self):
        """Start SignalR connection"""
        if not self.connection:
            self.build_connection()

        try:
            self.connection.start()
            self.logger.info("SignalR connection established successfully")
        except Exception as e:
            self.logger.error(f"Failed to start SignalR connection: {e}")
            raise

    def stop(self):
        """Stop SignalR connection"""
        if self.connection:
            self.connection.stop()
            self.logger.info("SignalR connection stopped")
```

## Configuration

### SignalR Configuration (YAML)

```yaml
# config/signalr_config.yaml

signalr:
  connection:
    # ✅ SECURE: No token in URL
    hub_url: "wss://sim-api.tradestation.com/v3/brokerage/stream"

    # Authentication
    authentication:
      method: "accessTokenFactory"  # REQUIRED: Use factory function
      use_query_string: false        # CRITICAL: NEVER use query string
      use_authorization_header: true # PREFERRED: Use Authorization header

    # Reconnection policy
    reconnection:
      enabled: true
      delays_ms: [0, 2000, 10000, 30000, 60000]
      max_attempts: 5

    # Connection options
    options:
      skip_negotiation: false
      transport: "WebSockets"  # WebSockets only for security
      timeout_ms: 30000

    # Token refresh integration
    token_refresh:
      check_before_connect: true     # Check token validity before connecting
      refresh_if_near_expiry: true   # Refresh if < 2 hours to expiry
      buffer_seconds: 7200           # Refresh trigger: 2 hours before expiry

  # Logging configuration
  logging:
    level: "Information"  # Trace, Debug, Information, Warning, Error, Critical
    sanitize_tokens: true  # CRITICAL: ALWAYS sanitize tokens in logs
    log_connection_events: true
    log_authentication_attempts: true

  # Monitoring
  monitoring:
    track_connection_state: true
    alert_on_auth_failure: true
    alert_on_repeated_disconnects: true
    alert_threshold_disconnects: 3  # Alert after 3 disconnects in 5 minutes
```

### Logging Configuration

```yaml
# config/logging_config.yaml

logging:
  version: 1
  disable_existing_loggers: false

  formatters:
    standard:
      format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # ✅ SECURE: Sanitized formatter for SignalR logs
    sanitized:
      format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
      # This formatter should use TokenSanitizer to redact tokens

  filters:
    # ✅ SECURE: Filter to sanitize tokens in log messages
    token_sanitizer:
      (): 'myapp.logging.TokenSanitizerFilter'

  handlers:
    console:
      class: logging.StreamHandler
      level: INFO
      formatter: sanitized
      filters: [token_sanitizer]
      stream: ext://sys.stdout

    file:
      class: logging.handlers.RotatingFileHandler
      level: DEBUG
      formatter: sanitized
      filters: [token_sanitizer]
      filename: logs/signalr.log
      maxBytes: 10485760  # 10MB
      backupCount: 5
      mode: 'a'

  loggers:
    signalr:
      level: INFO
      handlers: [console, file]
      propagate: false

    # ✅ SECURE: Specific logger for authentication events
    signalr.auth:
      level: INFO
      handlers: [console, file]
      propagate: false

  root:
    level: INFO
    handlers: [console]
```

## Security Considerations

### S-001: Never Use Query String for Tokens

**Rationale:**
- Query strings are logged in server access logs
- Query strings persist in browser history
- Query strings are visible to proxies and CDNs
- Query strings can be cached

**Enforcement:**
```typescript
// Code review checklist:
// ❌ REJECT code that contains:
const badUrl = `${hubUrl}?access_token=${token}`;
const badUrl = hubUrl + "?access_token=" + token;
const badUrl = `${hubUrl}?token=${token}`;

// ✅ APPROVE code that uses:
const connection = new HubConnectionBuilder()
  .withUrl(hubUrl, {
    accessTokenFactory: () => getToken()
  })
  .build();
```

### S-002: Token Sanitization

**Implementation:**
```typescript
class TokenSanitizer {
  /**
   * Sanitize token for logging
   */
  static sanitizeToken(token: string): string {
    if (!token || token.length < 10) {
      return '[REDACTED]';
    }
    return `${token.substring(0, 4)}...${token.substring(token.length - 4)}`;
  }

  /**
   * Sanitize URL (remove any token query parameters)
   */
  static sanitizeUrl(url: string): string {
    try {
      const urlObj = new URL(url);
      // Remove token-related query parameters
      urlObj.searchParams.delete('access_token');
      urlObj.searchParams.delete('token');
      urlObj.searchParams.delete('auth');
      return urlObj.toString();
    } catch {
      return url; // Return as-is if not a valid URL
    }
  }

  /**
   * Sanitize log message (replace any tokens)
   */
  static sanitizeLogMessage(message: string): string {
    // Regex to match JWT tokens (header.payload.signature)
    const jwtRegex = /eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g;
    return message.replace(jwtRegex, '[TOKEN_REDACTED]');
  }
}
```

### S-003: Authorization Header Transmission

**Verification:**
```typescript
// Verify Authorization header is used (not query string)
// Check network traffic in browser DevTools:

// ✅ CORRECT: Authorization header present
Request URL: wss://sim-api.tradestation.com/v3/brokerage/stream
Request Headers:
  Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
  Connection: Upgrade
  Upgrade: websocket

// ❌ INCORRECT: Token in query string
Request URL: wss://sim-api.tradestation.com/v3/brokerage/stream?access_token=eyJhbGc...
```

### S-004: Token Refresh During Connection

**Strategy:**
- Check token expiry before connecting
- Refresh proactively if < 2 hours to expiry
- Handle authentication failure gracefully
- Reconnect automatically with new token

**Implementation:**
```typescript
class SignalRConnectionManager {
  /**
   * Start connection with token validation
   */
  async start(): Promise<void> {
    // Check if token is near expiry before connecting
    const tokenInfo = await this.tokenManager.getTokenInfo();
    const timeToExpiry = tokenInfo.expires_at - Date.now();
    const twoHours = 2 * 60 * 60 * 1000;

    if (timeToExpiry < twoHours) {
      console.log('Token near expiry, refreshing before SignalR connection');
      await this.tokenManager.refreshToken();
    }

    // Now start connection
    await this.connection!.start();
  }
}
```

## Error Handling

### Error Scenarios

**E-001: Token Expired During Connection**
```
Scenario: Token expires while SignalR connection is active
Response:
  1. SignalR connection closes with 401 Unauthorized
  2. onclose handler detects authentication failure
  3. TokenManager refreshes token automatically
  4. Connection automatically reconnects via withAutomaticReconnect()
  5. accessTokenFactory provides new token
  6. Connection re-established
```

**E-002: accessTokenFactory Returns Empty Token**
```
Scenario: TokenManager fails to provide token
Response:
  1. accessTokenFactory throws error
  2. SignalR connection fails to start
  3. Log error: "Failed to retrieve token for SignalR"
  4. Trigger re-authentication flow
  5. Retry connection after successful re-authentication
```

**E-003: Authentication Failure on Connect**
```
Scenario: TradeStation API rejects token during SignalR negotiate
Response:
  1. Connection fails with 401 error
  2. Check if token is expired
  3. If expired: Refresh token and retry
  4. If still failing: Full re-authentication
  5. Log incident for security monitoring
```

**E-004: Token in Logs Detected**
```
Scenario: Automated log scanning detects JWT pattern in logs
Response:
  1. Trigger security alert: "Token exposure detected in logs"
  2. Identify source of leak (line number, module)
  3. Rotate compromised token immediately
  4. Fix code to use TokenSanitizer
  5. Add unit test to prevent regression
```

## Implementation Checklist

### Phase 1: Remove Query String Tokens
- [ ] Audit codebase for query string token usage
- [ ] Remove all `?access_token=` patterns
- [ ] Verify no tokens in URL construction
- [ ] Add linter rule to prevent query string tokens

### Phase 2: Implement accessTokenFactory
- [ ] Create SignalRConnectionManager class
- [ ] Implement accessTokenFactory with TokenManager integration
- [ ] Add token refresh check before connection
- [ ] Add token validation in factory function

### Phase 3: Token Sanitization
- [ ] Implement TokenSanitizer class
- [ ] Sanitize tokens in all log messages
- [ ] Sanitize URLs before logging
- [ ] Add logging filter for token redaction

### Phase 4: Error Handling
- [ ] Implement authentication failure handler
- [ ] Implement token expiry detection
- [ ] Add automatic reconnection with fresh token
- [ ] Add alerting for repeated auth failures

### Phase 5: Testing
- [ ] Unit tests for accessTokenFactory
- [ ] Unit tests for TokenSanitizer
- [ ] Integration tests for SignalR connection
- [ ] Security tests: verify no tokens in logs
- [ ] Performance tests: accessTokenFactory latency

### Phase 6: Monitoring
- [ ] Add metrics for SignalR authentication success/failure
- [ ] Add metrics for connection uptime
- [ ] Add alerts for authentication failures
- [ ] Add dashboard for SignalR connection health

## Validation Criteria

### Security Validation

**SV-1: No Tokens in URLs**
```
Test: Scan all network requests in browser DevTools
Expected: No access_token query parameters found
Validation: Filter by "access_token", should return 0 results
```

**SV-2: No Tokens in Logs**
```
Test: Review all log files after SignalR connection
Expected: No JWT tokens (eyJ...) found in logs
Validation: grep -r "eyJ[A-Za-z0-9_-]" logs/ should return 0 matches
```

**SV-3: Authorization Header Used**
```
Test: Inspect SignalR negotiate request in network traffic
Expected: Authorization: Bearer <token> header present
Validation: Verify header exists, query string empty
```

**SV-4: Token Refresh During Connection**
```
Test: Connect SignalR with token expiring in 1 hour
Expected: Token refreshed automatically before expiry
Validation: Connection remains active, no authentication errors
```

### Functional Validation

**FV-1: Connection Established Successfully**
```
Test: Start SignalR connection with valid token
Expected: Connection established, messages received
Validation: Check connection state = Connected
```

**FV-2: Reconnection After Token Refresh**
```
Test: Disconnect SignalR, refresh token, reconnect
Expected: Reconnection successful with new token
Validation: New token used in Authorization header
```

**FV-3: Authentication Failure Handling**
```
Test: Connect with expired token
Expected: Connection fails, token refreshed, retry succeeds
Validation: Check logs for refresh and retry sequence
```

## References

### Related Specifications
- **TOKEN_REFRESH_STRATEGY_SPEC.md**: Token refresh integration
- **TOKEN_STORAGE_SECURITY_SPEC.md**: Secure token storage
- **LONG_OPERATION_TOKEN_HANDLING_SPEC.md**: Token management during long connections

### Error Analysis References
- **ERRORS_AND_WARNINGS_CONSOLIDATED.md**:
  - Line 255-275: SEC-API-001 (JWT in Query String)

### SignalR Documentation
- Microsoft SignalR JavaScript Client: https://docs.microsoft.com/en-us/javascript/api/@microsoft/signalr/
- SignalR Authentication: https://docs.microsoft.com/en-us/aspnet/core/signalr/authn-and-authz
- TradeStation API SignalR: https://api.tradestation.com/docs/fundamentals/websockets/

### Security Best Practices
- OWASP Authentication Cheat Sheet
- NIST SP 800-63B: Digital Identity Guidelines
- RFC 6750: The OAuth 2.0 Authorization Framework: Bearer Token Usage

---

**Document Status:** DRAFT v1.0
**Last Updated:** 2025-10-22
**Next Review:** After security audit
**Approval Required:** Security Team, Architecture Team
