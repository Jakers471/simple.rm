# SignalR Reconnection Management Specification

**doc_id:** SIGNALR-001
**version:** 1.0
**status:** DRAFT
**addresses:** GAP-API-003 (CRITICAL) from ERRORS_AND_WARNINGS_CONSOLIDATED.md
**created:** 2025-10-22
**last_updated:** 2025-10-22

---

## Overview

This specification defines the complete SignalR reconnection strategy for handling connection failures, including automatic reconnection attempts, connection state management, failure detection, and fallback mechanisms to REST API polling. It addresses GAP-API-003 which identified missing `onclose` handler, `onreconnecting` handler, maximum reconnection limits, and fallback strategies.

**Critical Gap Addressed:**
> "Example code shows `.withAutomaticReconnect()` and `onreconnected` handler, but missing: `onclose` handler for permanent disconnections, `onreconnecting` handler for connection state updates, maximum reconnection attempt limits, connection failure detection and fallback"

---

## Requirements

### Functional Requirements

**FR-1: Automatic Reconnection**
- SignalR connection MUST automatically attempt to reconnect after disconnection
- Reconnection attempts MUST follow exponential backoff strategy (see EXPONENTIAL_BACKOFF_SPEC.md)
- Maximum reconnection attempts MUST be configurable with a default of 10 attempts
- Each reconnection attempt MUST use the current valid JWT token

**FR-2: Connection State Handlers**
- MUST implement `onreconnecting` handler for reconnection attempt notifications
- MUST implement `onreconnected` handler for successful reconnection
- MUST implement `onclose` handler for permanent connection closure
- MUST track connection state transitions: DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING, FAILED

**FR-3: Permanent Disconnection Detection**
- System MUST detect when reconnection attempts have been exhausted
- System MUST detect when connection closure is intentional (e.g., user logout, token expiration)
- System MUST distinguish between temporary network failures and permanent failures

**FR-4: Fallback to REST Polling**
- Upon permanent disconnection, system MUST automatically fall back to REST API polling
- REST polling MUST maintain real-time data updates at configurable intervals (default: 5 seconds)
- REST polling MUST be disabled once SignalR connection is re-established
- System MUST notify user of degraded mode operation

**FR-5: Token Expiration Handling**
- If JWT token expires during reconnection attempts, system MUST refresh token (see GAP-API-001)
- Reconnection attempts MUST pause during token refresh
- Reconnection attempts MUST resume with new token after successful refresh
- If token refresh fails, connection MUST be closed permanently

**FR-6: Connection Closure Scenarios**
- System MUST handle graceful disconnection (user logout, application shutdown)
- System MUST handle forced disconnection (token revocation, server shutdown)
- System MUST handle network interruption (timeout, DNS failure)
- System MUST clean up resources on permanent closure

### Non-Functional Requirements

**NFR-1: Performance**
- Connection state change handlers MUST execute in < 100ms
- Reconnection decision logic MUST execute in < 50ms
- Fallback to REST polling MUST activate within 2 seconds of permanent failure

**NFR-2: Reliability**
- Reconnection logic MUST NOT cause memory leaks on repeated attempts
- Connection state MUST be accurately tracked at all times
- State transitions MUST be atomic and thread-safe

**NFR-3: Observability**
- All connection state changes MUST be logged with timestamps
- Reconnection attempts MUST be logged with attempt number and delay duration
- Permanent failures MUST be logged with failure reason

---

## Architecture

### Connection Lifecycle

```
┌─────────────────┐
│  DISCONNECTED   │ (Initial state)
└────────┬────────┘
         │ .start()
         ▼
┌─────────────────┐
│   CONNECTING    │ (First connection attempt)
└────────┬────────┘
         │
    ┌────┴────┐
    │ Success │ Failure
    ▼         ▼
┌─────────┐ ┌──────────┐
│CONNECTED│ │  FAILED  │ (Retry exhausted)
└────┬────┘ └──────────┘
     │
     │ Network failure / Server disconnect
     ▼
┌─────────────────┐
│  RECONNECTING   │ (Automatic reconnection)
└────────┬────────┘
         │
    ┌────┴────┐
    │ Success │ Max attempts exceeded
    ▼         ▼
┌─────────┐ ┌──────────────┐
│CONNECTED│ │PERMANENTLY   │
└─────────┘ │ DISCONNECTED │
            └──────────────┘
                    │
                    ▼
            ┌──────────────┐
            │REST POLLING  │
            │ FALLBACK     │
            └──────────────┘
```

### Component Responsibilities

**SignalRConnectionManager:**
- Manages HubConnection lifecycle
- Implements all event handlers (onreconnecting, onreconnected, onclose)
- Tracks connection state and attempt count
- Coordinates with TokenManager for token refresh
- Triggers fallback to REST polling on permanent failure

**ConnectionStateTracker:**
- Maintains current connection state
- Provides state transition validation
- Emits state change events for UI updates
- Tracks connection metrics (uptime, reconnection count)

**RestPollingFallback:**
- Polls REST API endpoints at regular intervals
- Mimics SignalR event structure for seamless integration
- Automatically disables when SignalR reconnects
- Provides degraded mode notification to user

---

## State Transitions

```
DISCONNECTED --[.start()]--> CONNECTING
CONNECTING --[connection success]--> CONNECTED
CONNECTING --[connection failure]--> FAILED
CONNECTED --[network failure]--> RECONNECTING
CONNECTED --[.stop()]--> DISCONNECTED
RECONNECTING --[attempt N < MAX]--> RECONNECTING
RECONNECTING --[success]--> CONNECTED
RECONNECTING --[attempt N = MAX]--> PERMANENTLY_DISCONNECTED
RECONNECTING --[token expired]--> TOKEN_REFRESH
TOKEN_REFRESH --[refresh success]--> RECONNECTING
TOKEN_REFRESH --[refresh failure]--> PERMANENTLY_DISCONNECTED
PERMANENTLY_DISCONNECTED --[fallback enabled]--> REST_POLLING_MODE
REST_POLLING_MODE --[manual reconnect]--> CONNECTING
FAILED --[manual retry]--> CONNECTING
```

### State Definitions

| State | Description | Entry Actions | Exit Actions |
|-------|-------------|---------------|--------------|
| DISCONNECTED | No active connection, initial state | None | None |
| CONNECTING | First connection attempt in progress | Log attempt, start timeout timer | Clear timeout timer |
| CONNECTED | Active SignalR connection established | Subscribe to events, clear retry count | Unsubscribe from events |
| RECONNECTING | Automatic reconnection in progress | Log attempt number, apply backoff delay | None |
| FAILED | Connection failed, manual intervention required | Log failure, notify user | Clear error state |
| PERMANENTLY_DISCONNECTED | Max retries exceeded or intentional closure | Log reason, cleanup resources | None |
| TOKEN_REFRESH | Paused reconnection for token refresh | Request new token | Resume reconnection |
| REST_POLLING_MODE | Fallback polling active | Start polling timer | Stop polling timer |

---

## Configuration Schema

```yaml
signalr:
  reconnection:
    # Maximum number of reconnection attempts before giving up
    maxAttempts: 10

    # Retry delay sequence in milliseconds (see EXPONENTIAL_BACKOFF_SPEC.md)
    # [0ms, 2s, 10s, 30s, 60s] - then repeats 60s
    retryDelays: [0, 2000, 10000, 30000, 60000]

    # Maximum total reconnection time before permanent failure (5 minutes)
    maxReconnectionTime: 300000

    # Whether to automatically reconnect on disconnection
    autoReconnect: true

    # Whether to refresh token if expired during reconnection
    refreshTokenOnExpiry: true

  fallback:
    # Enable REST API polling fallback on permanent disconnection
    enablePollingFallback: true

    # Polling interval in milliseconds (5 seconds)
    pollingInterval: 5000

    # Maximum polling duration before requiring user action (10 minutes)
    maxPollingDuration: 600000

    # Whether to notify user when entering degraded mode
    notifyDegradedMode: true

  health:
    # Connection timeout for initial connection (30 seconds)
    connectionTimeout: 30000

    # Timeout for each reconnection attempt (10 seconds)
    reconnectionTimeout: 10000

  logging:
    # Log level for connection events (DEBUG, INFO, WARN, ERROR)
    connectionEvents: INFO

    # Log level for reconnection attempts
    reconnectionAttempts: INFO

    # Log level for permanent failures
    permanentFailures: ERROR
```

---

## Event Flows

### Scenario 1: Normal Disconnection and Successful Reconnection

```
1. User has active SignalR connection (CONNECTED)
2. Network interruption occurs
   - SignalR client detects disconnection
   - onreconnecting(error) handler fires
   - State transitions: CONNECTED → RECONNECTING
   - Log: "Connection lost, attempting reconnection (attempt 1/10)"
   - UI notification: "Connection interrupted, reconnecting..."

3. First reconnection attempt (immediate, 0ms delay)
   - SignalR attempts reconnection
   - Connection fails (network still down)
   - State remains: RECONNECTING
   - Schedule next attempt in 2000ms

4. Second reconnection attempt (2-second delay)
   - SignalR attempts reconnection
   - Connection succeeds
   - onreconnected(connectionId) handler fires
   - State transitions: RECONNECTING → CONNECTED
   - Log: "Reconnection successful (attempt 2/10)"
   - UI notification: "Connection restored"
   - Trigger state reconciliation (see STATE_RECONCILIATION_SPEC.md)
```

### Scenario 2: Permanent Disconnection with REST Fallback

```
1. User has active SignalR connection (CONNECTED)
2. Server goes offline permanently
   - SignalR client detects disconnection
   - onreconnecting(error) handler fires
   - State transitions: CONNECTED → RECONNECTING

3. Reconnection attempts 1-10 (following exponential backoff)
   - Attempt 1: 0ms delay → FAIL
   - Attempt 2: 2000ms delay → FAIL
   - Attempt 3: 10000ms delay → FAIL
   - Attempt 4: 30000ms delay → FAIL
   - Attempt 5: 60000ms delay → FAIL
   - Attempts 6-10: 60000ms delay each → FAIL
   - Total time: ~6.7 minutes
   - All attempts logged with attempt number and error

4. Max attempts exceeded
   - onclose(error) handler fires with reason: "Max reconnection attempts exceeded"
   - State transitions: RECONNECTING → PERMANENTLY_DISCONNECTED
   - Log: "Permanent disconnection after 10 failed attempts"
   - UI notification: "Unable to reconnect, switching to polling mode"

5. Fallback to REST polling activates
   - RestPollingFallback.start()
   - State transitions: PERMANENTLY_DISCONNECTED → REST_POLLING_MODE
   - Poll /api/Positions/getAllPositions every 5 seconds
   - Poll /api/Orders/getAllOrders every 5 seconds
   - Poll /api/Quotes/getQuote for tracked symbols every 5 seconds
   - Log: "REST polling fallback active (5-second interval)"
   - UI indicator: "Degraded Mode - Limited Real-Time Updates"
```

### Scenario 3: Token Expiration During Reconnection

```
1. User has active SignalR connection (CONNECTED)
2. Network interruption occurs
   - State transitions: CONNECTED → RECONNECTING
   - Begin reconnection attempts

3. Reconnection attempt 3 (10-second delay)
   - SignalR attempts reconnection with JWT token
   - Server returns 401 Unauthorized (token expired)
   - onreconnecting(error) handler receives token expiry error
   - State transitions: RECONNECTING → TOKEN_REFRESH
   - Log: "Token expired during reconnection, refreshing..."
   - Pause reconnection attempts

4. Token refresh process
   - Call TokenManager.refreshToken()
   - POST /api/Auth/validate with current token
   - Receive new JWT token (24-hour validity)
   - Update SignalR connection with new access token
   - Log: "Token refreshed successfully"

5. Resume reconnection
   - State transitions: TOKEN_REFRESH → RECONNECTING
   - Reset attempt counter to 1
   - Attempt reconnection immediately with new token
   - Connection succeeds
   - onreconnected(connectionId) fires
   - State transitions: RECONNECTING → CONNECTED
   - Log: "Reconnection successful after token refresh"
```

### Scenario 4: Graceful Disconnection (User Logout)

```
1. User has active SignalR connection (CONNECTED)
2. User clicks "Logout" button
   - Application calls SignalRConnectionManager.disconnect()
   - Set intentionalDisconnect flag = true
   - Call connection.stop()

3. Connection closes
   - onclose(error) handler fires with error = null
   - Check intentionalDisconnect flag = true
   - State transitions: CONNECTED → DISCONNECTED
   - Do NOT trigger reconnection
   - Do NOT activate fallback polling
   - Log: "Connection closed intentionally (user logout)"
   - Clean up resources
```

---

## Handler Implementations

### onreconnecting Handler

**Purpose:** Notified when connection lost and automatic reconnection begins

**Signature:**
```typescript
onreconnecting(error?: Error): void
```

**Responsibilities:**
1. Log reconnection attempt with attempt number and error details
2. Update connection state to RECONNECTING
3. Increment reconnection attempt counter
4. Check if max attempts exceeded → trigger onclose if true
5. Check if error is token expiry → trigger token refresh
6. Notify UI of reconnection in progress
7. Record reconnection start time for metrics

**Error Types:**
- `TimeoutError`: Connection attempt timed out
- `ServerError`: Server returned 5xx error
- `AuthenticationError`: Token expired or invalid (trigger token refresh)
- `NetworkError`: DNS failure, network unreachable
- `UnknownError`: Unspecified error

**Example Implementation:**
```typescript
connection.onreconnecting((error?: Error) => {
  state.attemptCount++;
  state.connectionState = ConnectionState.RECONNECTING;

  logger.warn(`SignalR reconnection attempt ${state.attemptCount}/${config.maxAttempts}`, {
    error: error?.message,
    errorType: error?.name,
    timestamp: Date.now()
  });

  // Check max attempts
  if (state.attemptCount >= config.maxAttempts) {
    logger.error('Max reconnection attempts exceeded');
    connection.stop(); // Triggers onclose
    return;
  }

  // Check token expiry
  if (error instanceof AuthenticationError || error?.message.includes('401')) {
    handleTokenExpiry();
    return;
  }

  // Notify UI
  eventBus.emit('connection:reconnecting', {
    attempt: state.attemptCount,
    maxAttempts: config.maxAttempts,
    error: error?.message
  });

  // Update UI indicator
  uiManager.showReconnectingStatus(state.attemptCount, config.maxAttempts);
});
```

### onreconnected Handler

**Purpose:** Notified when connection successfully re-established after disconnection

**Signature:**
```typescript
onreconnected(connectionId?: string): void
```

**Responsibilities:**
1. Log successful reconnection with duration and attempt count
2. Update connection state to CONNECTED
3. Reset reconnection attempt counter to 0
4. Re-subscribe to all SignalR events
5. Trigger state reconciliation to catch missed updates (see STATE_RECONCILIATION_SPEC.md)
6. Notify UI of successful reconnection
7. Record connection uptime metrics

**Example Implementation:**
```typescript
connection.onreconnected((connectionId?: string) => {
  const reconnectionDuration = Date.now() - state.reconnectionStartTime;

  logger.info('SignalR reconnection successful', {
    connectionId,
    attempts: state.attemptCount,
    duration: reconnectionDuration,
    timestamp: Date.now()
  });

  // Update state
  state.connectionState = ConnectionState.CONNECTED;
  state.connectionId = connectionId;
  const previousAttempts = state.attemptCount;
  state.attemptCount = 0;
  state.reconnectionStartTime = null;

  // Re-subscribe to events (they should persist, but verify)
  resubscribeToAllEvents();

  // Trigger state reconciliation to catch missed updates
  stateReconciliation.reconcile({
    reason: 'reconnection',
    disconnectedAt: state.lastDisconnectTime,
    reconnectedAt: Date.now(),
    missedDuration: reconnectionDuration
  });

  // Notify UI
  eventBus.emit('connection:restored', {
    attempts: previousAttempts,
    duration: reconnectionDuration
  });

  uiManager.showConnectionRestoredNotification();
  uiManager.hideReconnectingStatus();

  // Update metrics
  metricsCollector.recordReconnection({
    attempts: previousAttempts,
    duration: reconnectionDuration,
    success: true
  });
});
```

### onclose Handler

**Purpose:** Notified when connection closed and will not reconnect (permanent failure)

**Signature:**
```typescript
onclose(error?: Error): void
```

**Responsibilities:**
1. Log permanent disconnection with reason
2. Determine disconnection cause (intentional, max retries, server shutdown, token revocation)
3. Update connection state to PERMANENTLY_DISCONNECTED or DISCONNECTED
4. Clean up resources (timers, subscriptions, buffers)
5. Trigger fallback to REST polling if enabled and not intentional
6. Notify UI of permanent disconnection
7. Record failure metrics

**Disconnection Scenarios:**
- **Intentional:** User logout, application shutdown → No fallback
- **Max Retries:** Exhausted reconnection attempts → Activate fallback
- **Token Revoked:** Authentication failure → Logout user
- **Server Shutdown:** Server unavailable → Activate fallback

**Example Implementation:**
```typescript
connection.onclose((error?: Error) => {
  const isIntentional = state.intentionalDisconnect;
  const maxRetriesExceeded = state.attemptCount >= config.maxAttempts;
  const isTokenRevoked = error instanceof AuthenticationError;

  logger.error('SignalR connection closed permanently', {
    error: error?.message,
    intentional: isIntentional,
    maxRetriesExceeded,
    tokenRevoked: isTokenRevoked,
    finalAttempts: state.attemptCount,
    timestamp: Date.now()
  });

  // Update state
  state.connectionState = isIntentional
    ? ConnectionState.DISCONNECTED
    : ConnectionState.PERMANENTLY_DISCONNECTED;
  state.connectionId = null;

  // Clean up resources
  clearAllTimers();
  unsubscribeFromAllEvents();
  clearEventBuffers();

  // Handle different scenarios
  if (isIntentional) {
    // User logout or app shutdown - do nothing
    logger.info('Connection closed intentionally, no action required');
    return;
  }

  if (isTokenRevoked) {
    // Token revoked - force logout
    logger.error('Token revoked, forcing user logout');
    authManager.logout();
    uiManager.showAuthenticationError('Your session has been terminated');
    return;
  }

  if (maxRetriesExceeded || error) {
    // Permanent failure - activate fallback
    logger.warn('Activating REST polling fallback');

    if (config.fallback.enablePollingFallback) {
      restPollingFallback.start({
        interval: config.fallback.pollingInterval,
        maxDuration: config.fallback.maxPollingDuration
      });

      state.connectionState = ConnectionState.REST_POLLING_MODE;

      if (config.fallback.notifyDegradedMode) {
        uiManager.showDegradedModeNotification({
          reason: 'Unable to establish real-time connection',
          pollingInterval: config.fallback.pollingInterval,
          manualReconnectAvailable: true
        });
      }
    } else {
      uiManager.showError('Connection lost. Please refresh the page.');
    }
  }

  // Update metrics
  metricsCollector.recordPermanentDisconnection({
    reason: error?.message || 'unknown',
    attempts: state.attemptCount,
    fallbackActivated: config.fallback.enablePollingFallback
  });

  // Notify UI
  eventBus.emit('connection:closed', {
    error: error?.message,
    intentional: isIntentional,
    fallbackActive: state.connectionState === ConnectionState.REST_POLLING_MODE
  });
});
```

---

## Error Handling

### Connection Errors

| Error Type | HTTP Code | Description | Recovery Strategy |
|------------|-----------|-------------|-------------------|
| TimeoutError | - | Connection attempt timed out | Retry with exponential backoff |
| NetworkError | - | Network unreachable, DNS failure | Retry with exponential backoff |
| AuthenticationError | 401 | Token expired or invalid | Refresh token, then retry |
| AuthorizationError | 403 | Token valid but insufficient permissions | Force logout, notify user |
| ServerError | 500-599 | Server-side error | Retry with exponential backoff |
| TooManyRequestsError | 429 | Rate limit exceeded | Wait for rate limit reset, then retry |
| BadRequestError | 400 | Invalid connection parameters | Log error, notify developer |
| UnknownError | - | Unspecified error | Retry with exponential backoff |

### Token Refresh Failures

If token refresh fails during reconnection:
1. Log token refresh failure with error details
2. Stop reconnection attempts
3. Transition to PERMANENTLY_DISCONNECTED state
4. Force user logout
5. Clear stored tokens
6. Redirect to login page
7. Show notification: "Session expired, please log in again"

### REST Polling Fallback Failures

If REST polling encounters errors:
1. Log polling failure with error type
2. Retry failed request with exponential backoff (max 3 retries)
3. If token expired, refresh token and retry
4. If persistent failures (5 consecutive failures), stop polling
5. Show critical error notification: "Unable to retrieve data"
6. Offer manual reconnect button

---

## Implementation Checklist

### Phase 1: Core Reconnection Logic
- [ ] Implement SignalRConnectionManager class
- [ ] Implement ConnectionStateTracker
- [ ] Configure `.withAutomaticReconnect()` with custom retry delays
- [ ] Implement onreconnecting handler with attempt tracking
- [ ] Implement onreconnected handler with state reconciliation trigger
- [ ] Implement onclose handler with permanent failure detection
- [ ] Add connection state change event emitter
- [ ] Add comprehensive logging for all handlers

### Phase 2: Token Expiration Handling
- [ ] Integrate with TokenManager (see GAP-API-001)
- [ ] Detect token expiration in onreconnecting handler
- [ ] Implement token refresh pause/resume logic
- [ ] Update SignalR connection with refreshed token
- [ ] Handle token refresh failures gracefully
- [ ] Test token expiration during reconnection

### Phase 3: REST Polling Fallback
- [ ] Implement RestPollingFallback class
- [ ] Create polling timer with configurable interval
- [ ] Implement position polling (`/api/Positions/getAllPositions`)
- [ ] Implement order polling (`/api/Orders/getAllOrders`)
- [ ] Implement quote polling (`/api/Quotes/getQuote`)
- [ ] Convert REST responses to SignalR event format
- [ ] Add automatic fallback activation on permanent disconnect
- [ ] Add manual reconnect button in degraded mode
- [ ] Implement fallback deactivation on successful reconnect

### Phase 4: UI Integration
- [ ] Create reconnecting status indicator (loading spinner + attempt count)
- [ ] Create connection restored notification (success toast)
- [ ] Create degraded mode notification (warning banner)
- [ ] Create manual reconnect button
- [ ] Add connection status icon in header (green/yellow/red)
- [ ] Implement connection health tooltip with metrics

### Phase 5: Testing
- [ ] Unit test: onreconnecting handler
- [ ] Unit test: onreconnected handler
- [ ] Unit test: onclose handler
- [ ] Integration test: Network interruption recovery
- [ ] Integration test: Token expiration during reconnection
- [ ] Integration test: Max retries exceeded fallback
- [ ] Integration test: Graceful disconnection
- [ ] Integration test: REST polling fallback
- [ ] Load test: Rapid connection/disconnection cycles
- [ ] Load test: Multiple simultaneous reconnection attempts

---

## Validation Criteria

### Functional Validation

**VC-1: Automatic Reconnection**
- ✅ Connection automatically attempts to reconnect after network failure
- ✅ Reconnection follows exponential backoff delays
- ✅ Maximum 10 reconnection attempts are made
- ✅ onreconnecting handler fires on each attempt

**VC-2: Successful Reconnection**
- ✅ onreconnected handler fires on successful reconnect
- ✅ Connection state transitions to CONNECTED
- ✅ Event subscriptions are maintained after reconnect
- ✅ State reconciliation is triggered
- ✅ UI shows "Connection Restored" notification

**VC-3: Permanent Disconnection**
- ✅ onclose handler fires after max retries exceeded
- ✅ Connection state transitions to PERMANENTLY_DISCONNECTED
- ✅ REST polling fallback activates automatically
- ✅ UI shows "Degraded Mode" notification

**VC-4: Token Expiration During Reconnection**
- ✅ Token expiration is detected in onreconnecting handler
- ✅ Reconnection pauses for token refresh
- ✅ New token is applied to connection
- ✅ Reconnection resumes with new token
- ✅ If token refresh fails, connection is closed permanently

**VC-5: Graceful Disconnection**
- ✅ User logout does NOT trigger reconnection
- ✅ User logout does NOT activate REST polling fallback
- ✅ Connection state transitions to DISCONNECTED (not PERMANENTLY_DISCONNECTED)

### Performance Validation

**PV-1: Handler Execution Time**
- ✅ onreconnecting handler executes in < 100ms
- ✅ onreconnected handler executes in < 100ms
- ✅ onclose handler executes in < 100ms

**PV-2: Reconnection Speed**
- ✅ First reconnection attempt is immediate (0ms delay)
- ✅ Subsequent attempts follow configured backoff delays
- ✅ State reconciliation completes within 5 seconds of reconnection

**PV-3: Fallback Activation**
- ✅ REST polling fallback starts within 2 seconds of permanent failure
- ✅ First polling request completes within 5 seconds

### Reliability Validation

**RV-1: Memory Management**
- ✅ No memory leaks after 100 reconnection cycles
- ✅ Event listeners are properly cleaned up on disconnection
- ✅ Timers are cleared on connection closure

**RV-2: State Consistency**
- ✅ Connection state always matches actual connection status
- ✅ State transitions are atomic and race-condition-free
- ✅ Attempt counter is accurate across all reconnection cycles

**RV-3: Logging**
- ✅ All reconnection attempts are logged with attempt number
- ✅ All permanent failures are logged with failure reason
- ✅ All token refresh operations are logged

---

## Integration Points

### Dependencies
- **TokenManager** (GAP-API-001): Token refresh during reconnection
- **StateReconciliation** (SIGNALR-003): Sync missed updates after reconnection
- **ExponentialBackoff** (SIGNALR-002): Retry delay calculations
- **EventBus**: Connection state change notifications
- **Logger**: Connection event logging
- **MetricsCollector**: Connection metrics tracking

### External Systems
- **SignalR Hub**: `/tradeHub` WebSocket endpoint
- **REST API Endpoints** (fallback mode):
  - `/api/Positions/getAllPositions`
  - `/api/Orders/getAllOrders`
  - `/api/Quotes/getQuote`
- **Authentication Service**: Token validation and refresh

---

## References

- **ERRORS_AND_WARNINGS_CONSOLIDATED.md**: Section "GAP-API-003: Incomplete SignalR Reconnection Logic"
- **EXPONENTIAL_BACKOFF_SPEC.md**: Retry delay sequence specification
- **STATE_RECONCILIATION_SPEC.md**: Post-reconnection data sync specification
- **CONNECTION_HEALTH_MONITORING_SPEC.md**: Health check and ping mechanisms
- **SIGNALR_EVENT_SUBSCRIPTION_SPEC.md**: Event subscription management
- **API Integration Analysis**: Section 2.2 "SignalR Connection Management"

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-22 | SignalR Resilience Spec Writer | Initial specification addressing GAP-API-003 |

---

## Appendices

### Appendix A: Connection State Enum

```typescript
enum ConnectionState {
  DISCONNECTED = 'disconnected',           // No connection, initial state
  CONNECTING = 'connecting',               // First connection attempt
  CONNECTED = 'connected',                 // Active connection established
  RECONNECTING = 'reconnecting',           // Automatic reconnection in progress
  FAILED = 'failed',                       // Connection failed, manual retry required
  PERMANENTLY_DISCONNECTED = 'permanently_disconnected', // Max retries exceeded
  TOKEN_REFRESH = 'token_refresh',         // Paused for token refresh
  REST_POLLING_MODE = 'rest_polling_mode'  // Fallback polling active
}
```

### Appendix B: Example Configuration File

```yaml
# config/signalr.yaml
signalr:
  hub:
    url: "https://api.provider.com/tradeHub"

  reconnection:
    maxAttempts: 10
    retryDelays: [0, 2000, 10000, 30000, 60000]
    maxReconnectionTime: 300000  # 5 minutes
    autoReconnect: true
    refreshTokenOnExpiry: true

  fallback:
    enablePollingFallback: true
    pollingInterval: 5000  # 5 seconds
    maxPollingDuration: 600000  # 10 minutes
    notifyDegradedMode: true

  health:
    connectionTimeout: 30000  # 30 seconds
    reconnectionTimeout: 10000  # 10 seconds

  logging:
    connectionEvents: INFO
    reconnectionAttempts: INFO
    permanentFailures: ERROR
```

### Appendix C: Metrics to Track

**Connection Metrics:**
- Total connection attempts
- Successful connections
- Failed connections
- Average connection duration
- Total uptime
- Total downtime

**Reconnection Metrics:**
- Total reconnection attempts
- Successful reconnections
- Failed reconnections
- Average reconnection duration
- Average attempts per reconnection cycle
- Permanent disconnection count

**Fallback Metrics:**
- Fallback activation count
- Total time in fallback mode
- Average polling latency
- Polling request success rate
- Manual reconnect attempts

---

**End of Specification**
