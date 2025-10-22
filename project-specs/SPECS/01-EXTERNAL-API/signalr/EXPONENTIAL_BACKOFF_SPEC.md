# SignalR Exponential Backoff Strategy Specification

**doc_id:** SIGNALR-002
**version:** 1.0
**status:** DRAFT
**addresses:** GAP-API-004 (CRITICAL) from ERRORS_AND_WARNINGS_CONSOLIDATED.md
**created:** 2025-10-22
**last_updated:** 2025-10-22

---

## Overview

This specification defines the exponential backoff strategy for SignalR reconnection attempts, including retry delay sequences, maximum retry caps, backoff multiplier calculations, and maximum attempt limits. It addresses GAP-API-004 which identified the lack of reconnection timing guidance.

**Critical Gap Addressed:**
> "No guidance on reconnection timing (initial retry delay, maximum retry delay, backoff multiplier, maximum retry attempts). Could overwhelm server with rapid reconnection attempts."

**Design Philosophy:**
- Start fast: Immediate first retry for transient network blips
- Back off quickly: Exponential delays prevent server overload
- Cap delays: Maximum 60-second delays prevent excessive wait times
- Limit attempts: Maximum 10 attempts prevent indefinite retry loops

---

## Requirements

### Functional Requirements

**FR-1: Retry Delay Sequence**
- MUST use predefined retry delay sequence: `[0, 2000, 10000, 30000, 60000]` milliseconds
- First retry (attempt 1) MUST be immediate (0ms delay) for transient network issues
- Second retry (attempt 2) MUST wait 2 seconds (2000ms)
- Third retry (attempt 3) MUST wait 10 seconds (10000ms)
- Fourth retry (attempt 4) MUST wait 30 seconds (30000ms)
- Fifth and subsequent retries (attempts 5+) MUST wait 60 seconds (60000ms)
- Delays MUST NOT exceed 60 seconds (hard cap)

**FR-2: Maximum Retry Attempts**
- MUST enforce maximum of 10 reconnection attempts
- After 10 failed attempts, MUST trigger permanent disconnection (onclose handler)
- Attempt counter MUST reset to 0 on successful reconnection
- Attempt counter MUST persist across token refresh cycles

**FR-3: Backoff Configuration**
- Retry delay sequence MUST be configurable via YAML config
- Maximum retry attempts MUST be configurable via YAML config
- Configuration changes MUST NOT require code changes
- Invalid configurations MUST fall back to safe defaults

**FR-4: Backoff Calculation**
- For attempts 1-5, use delays from retry sequence array
- For attempts 6+, repeat the maximum delay (60000ms)
- Delays MUST be deterministic (no jitter by default)
- Optional jitter MAY be added for distributed systems (not required for single-instance)

**FR-5: Total Reconnection Time**
- Total reconnection time across all 10 attempts: ~6.7 minutes
- Calculation: 0 + 2 + 10 + 30 + 60 + 60 + 60 + 60 + 60 + 60 = 402 seconds
- Maximum reconnection duration MUST be configurable (default: 5 minutes)
- If max duration exceeded, MUST trigger permanent disconnection regardless of attempt count

### Non-Functional Requirements

**NFR-1: Performance**
- Backoff calculation MUST execute in < 10ms
- No blocking operations during delay waiting
- Use asynchronous timers for delay implementation

**NFR-2: Predictability**
- Backoff delays MUST be consistent across all reconnection cycles
- Users MUST be able to predict when next retry will occur
- Delay sequence MUST be documented in user-facing UI

**NFR-3: Server Protection**
- Exponential backoff MUST prevent server overload during outages
- Delays MUST allow server recovery time between retry attempts
- Rate limiting MUST NOT be triggered by reconnection attempts

---

## Architecture

### Backoff Strategy Components

```
┌─────────────────────────────────────────────────┐
│        ExponentialBackoffStrategy               │
├─────────────────────────────────────────────────┤
│ - retryDelays: number[]                         │
│ - maxAttempts: number                           │
│ - maxReconnectionTime: number                   │
│ - currentAttempt: number                        │
│ - reconnectionStartTime: number                 │
├─────────────────────────────────────────────────┤
│ + getNextDelay(attempt: number): number         │
│ + shouldRetry(attempt: number): boolean         │
│ + getTotalElapsedTime(): number                 │
│ + isMaxDurationExceeded(): boolean              │
│ + reset(): void                                 │
│ + getDelaySequenceDescription(): string         │
└─────────────────────────────────────────────────┘
```

### Integration with SignalR

```
┌──────────────────────┐
│ HubConnectionBuilder │
└──────────┬───────────┘
           │
           │ .withAutomaticReconnect(retryDelays)
           ▼
┌──────────────────────┐
│   HubConnection      │
├──────────────────────┤
│ - retryPolicy        │  ◄───┐
├──────────────────────┤      │
│ onreconnecting       │      │
│ onreconnected        │      │ Uses
│ onclose              │      │
└──────────┬───────────┘      │
           │                  │
           │ Delegates to     │
           ▼                  │
┌─────────────────────────────┴────┐
│ ExponentialBackoffStrategy       │
│ (Custom IRetryPolicy)             │
└───────────────────────────────────┘
```

---

## Retry Delay Sequence

### Delay Table

| Attempt # | Delay (ms) | Delay (human) | Cumulative Time (s) | Formula |
|-----------|-----------|---------------|---------------------|---------|
| 1 | 0 | Immediate | 0 | retryDelays[0] |
| 2 | 2,000 | 2 seconds | 2 | retryDelays[1] |
| 3 | 10,000 | 10 seconds | 12 | retryDelays[2] |
| 4 | 30,000 | 30 seconds | 42 | retryDelays[3] |
| 5 | 60,000 | 1 minute | 102 | retryDelays[4] |
| 6 | 60,000 | 1 minute | 162 | retryDelays[4] (cap) |
| 7 | 60,000 | 1 minute | 222 | retryDelays[4] (cap) |
| 8 | 60,000 | 1 minute | 282 | retryDelays[4] (cap) |
| 9 | 60,000 | 1 minute | 342 | retryDelays[4] (cap) |
| 10 | 60,000 | 1 minute | 402 | retryDelays[4] (cap) |

**Total Reconnection Time:** 402 seconds (~6.7 minutes)

### Delay Calculation Algorithm

```typescript
function getNextDelay(attemptNumber: number, retryDelays: number[]): number {
  // Attempt 1 = index 0, Attempt 2 = index 1, etc.
  const index = attemptNumber - 1;

  // If within sequence bounds, return corresponding delay
  if (index < retryDelays.length) {
    return retryDelays[index];
  }

  // Otherwise, return maximum delay (last element in array)
  return retryDelays[retryDelays.length - 1];
}

// Examples:
getNextDelay(1, [0, 2000, 10000, 30000, 60000]); // Returns 0
getNextDelay(2, [0, 2000, 10000, 30000, 60000]); // Returns 2000
getNextDelay(5, [0, 2000, 10000, 30000, 60000]); // Returns 60000
getNextDelay(8, [0, 2000, 10000, 30000, 60000]); // Returns 60000 (capped)
```

---

## Configuration Schema

```yaml
signalr:
  reconnection:
    # Retry delay sequence in milliseconds
    # [attempt 1, attempt 2, attempt 3, attempt 4, attempt 5+]
    retryDelays: [0, 2000, 10000, 30000, 60000]

    # Maximum number of reconnection attempts before permanent failure
    maxAttempts: 10

    # Maximum total reconnection duration in milliseconds (5 minutes)
    # If exceeded, triggers permanent disconnection regardless of attempt count
    maxReconnectionTime: 300000

    # Optional: Add random jitter to delays (0-100% of delay)
    # Set to 0 for deterministic delays, 0.25 for ±25% jitter
    # Useful for distributed systems to prevent thundering herd
    jitterFactor: 0.0

    # Optional: Minimum delay for any retry attempt (milliseconds)
    # Ensures first retry isn't truly immediate if network stack needs time
    minRetryDelay: 0

    # Optional: Maximum delay for any retry attempt (milliseconds)
    # Hard cap on retry delays, overrides retryDelays array
    maxRetryDelay: 60000

  validation:
    # Validate configuration on startup
    validateConfig: true

    # Fail startup if configuration is invalid (vs. using defaults)
    failOnInvalidConfig: false
```

### Configuration Validation Rules

**Valid Configuration:**
- `retryDelays` MUST be an array of positive integers
- `retryDelays` MUST have at least 1 element
- `retryDelays` MUST be in ascending order (allowing equal consecutive values)
- `maxAttempts` MUST be a positive integer ≥ 1
- `maxReconnectionTime` MUST be a positive integer ≥ 10000 (10 seconds)
- `jitterFactor` MUST be between 0.0 and 1.0
- `minRetryDelay` MUST be ≥ 0
- `maxRetryDelay` MUST be > `minRetryDelay`

**Invalid Configuration Handling:**
```typescript
function validateConfig(config: ReconnectionConfig): ValidationResult {
  const errors: string[] = [];

  if (!Array.isArray(config.retryDelays) || config.retryDelays.length === 0) {
    errors.push('retryDelays must be non-empty array');
  }

  if (config.retryDelays.some(delay => delay < 0)) {
    errors.push('retryDelays must contain only positive integers');
  }

  for (let i = 1; i < config.retryDelays.length; i++) {
    if (config.retryDelays[i] < config.retryDelays[i-1]) {
      errors.push('retryDelays must be in ascending order');
    }
  }

  if (config.maxAttempts < 1) {
    errors.push('maxAttempts must be at least 1');
  }

  if (config.maxReconnectionTime < 10000) {
    errors.push('maxReconnectionTime must be at least 10000ms (10 seconds)');
  }

  if (config.jitterFactor < 0 || config.jitterFactor > 1) {
    errors.push('jitterFactor must be between 0.0 and 1.0');
  }

  if (config.maxRetryDelay <= config.minRetryDelay) {
    errors.push('maxRetryDelay must be greater than minRetryDelay');
  }

  return {
    isValid: errors.length === 0,
    errors,
    shouldUseSafeDefaults: errors.length > 0 && !config.validation.failOnInvalidConfig
  };
}
```

**Safe Default Configuration:**
```yaml
# Fallback configuration if validation fails
signalr:
  reconnection:
    retryDelays: [0, 2000, 10000, 30000, 60000]
    maxAttempts: 10
    maxReconnectionTime: 300000
    jitterFactor: 0.0
    minRetryDelay: 0
    maxRetryDelay: 60000
```

---

## Backoff Implementation

### SignalR HubConnectionBuilder Integration

```typescript
import { HubConnectionBuilder, HubConnection } from '@microsoft/signalr';

interface ReconnectionConfig {
  retryDelays: number[];
  maxAttempts: number;
  maxReconnectionTime: number;
  jitterFactor: number;
  minRetryDelay: number;
  maxRetryDelay: number;
}

class ExponentialBackoffStrategy {
  private config: ReconnectionConfig;
  private currentAttempt: number = 0;
  private reconnectionStartTime: number | null = null;

  constructor(config: ReconnectionConfig) {
    this.config = config;
  }

  /**
   * Calculate delay for next reconnection attempt
   * @param attemptNumber Current attempt number (1-based)
   * @returns Delay in milliseconds
   */
  public getNextDelay(attemptNumber: number): number {
    const index = attemptNumber - 1;

    // Get base delay from sequence
    let delay: number;
    if (index < this.config.retryDelays.length) {
      delay = this.config.retryDelays[index];
    } else {
      delay = this.config.retryDelays[this.config.retryDelays.length - 1];
    }

    // Apply jitter if configured
    if (this.config.jitterFactor > 0) {
      const jitter = delay * this.config.jitterFactor;
      const randomOffset = (Math.random() - 0.5) * 2 * jitter;
      delay = delay + randomOffset;
    }

    // Apply min/max constraints
    delay = Math.max(delay, this.config.minRetryDelay);
    delay = Math.min(delay, this.config.maxRetryDelay);

    return Math.round(delay);
  }

  /**
   * Check if reconnection should be attempted
   * @param attemptNumber Current attempt number (1-based)
   * @returns True if should retry, false if should give up
   */
  public shouldRetry(attemptNumber: number): boolean {
    // Check attempt limit
    if (attemptNumber > this.config.maxAttempts) {
      return false;
    }

    // Check time limit
    if (this.isMaxDurationExceeded()) {
      return false;
    }

    return true;
  }

  /**
   * Get total elapsed time since reconnection started
   * @returns Elapsed time in milliseconds, or 0 if not reconnecting
   */
  public getTotalElapsedTime(): number {
    if (this.reconnectionStartTime === null) {
      return 0;
    }
    return Date.now() - this.reconnectionStartTime;
  }

  /**
   * Check if maximum reconnection duration has been exceeded
   * @returns True if max duration exceeded, false otherwise
   */
  public isMaxDurationExceeded(): boolean {
    const elapsedTime = this.getTotalElapsedTime();
    return elapsedTime > this.config.maxReconnectionTime;
  }

  /**
   * Reset backoff state (called on successful reconnection)
   */
  public reset(): void {
    this.currentAttempt = 0;
    this.reconnectionStartTime = null;
  }

  /**
   * Start reconnection cycle (called when disconnection detected)
   */
  public startReconnectionCycle(): void {
    this.currentAttempt = 0;
    this.reconnectionStartTime = Date.now();
  }

  /**
   * Increment attempt counter and get delay for next attempt
   * @returns Delay in milliseconds for next attempt
   */
  public nextAttempt(): number {
    this.currentAttempt++;
    return this.getNextDelay(this.currentAttempt);
  }

  /**
   * Get human-readable description of delay sequence for UI
   * @returns Description string
   */
  public getDelaySequenceDescription(): string {
    const delays = this.config.retryDelays.map((delay, index) => {
      const attemptNum = index + 1;
      const humanDelay = this.formatDelay(delay);
      return `Attempt ${attemptNum}: ${humanDelay}`;
    });

    if (this.config.maxAttempts > this.config.retryDelays.length) {
      const remainingAttempts = this.config.maxAttempts - this.config.retryDelays.length;
      const maxDelay = this.config.retryDelays[this.config.retryDelays.length - 1];
      delays.push(`Attempts ${this.config.retryDelays.length + 1}-${this.config.maxAttempts}: ${this.formatDelay(maxDelay)} each`);
    }

    return delays.join(', ');
  }

  private formatDelay(ms: number): string {
    if (ms === 0) return 'Immediate';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${ms / 1000}s`;
    return `${ms / 60000}min`;
  }
}

// Create SignalR connection with exponential backoff
function createSignalRConnection(
  hubUrl: string,
  config: ReconnectionConfig
): HubConnection {
  const backoffStrategy = new ExponentialBackoffStrategy(config);

  const connection = new HubConnectionBuilder()
    .withUrl(hubUrl, {
      accessTokenFactory: () => tokenManager.getAccessToken()
    })
    .withAutomaticReconnect(config.retryDelays)
    .build();

  // Track reconnection state
  connection.onreconnecting((error) => {
    if (backoffStrategy.reconnectionStartTime === null) {
      backoffStrategy.startReconnectionCycle();
    }

    const nextDelay = backoffStrategy.nextAttempt();
    const shouldRetry = backoffStrategy.shouldRetry(backoffStrategy.currentAttempt);

    logger.info('Reconnection attempt', {
      attempt: backoffStrategy.currentAttempt,
      maxAttempts: config.maxAttempts,
      nextDelay,
      elapsedTime: backoffStrategy.getTotalElapsedTime(),
      shouldRetry
    });

    if (!shouldRetry) {
      logger.error('Max reconnection attempts or duration exceeded');
      connection.stop(); // Triggers onclose
    }
  });

  connection.onreconnected(() => {
    logger.info('Reconnection successful', {
      attempts: backoffStrategy.currentAttempt,
      totalTime: backoffStrategy.getTotalElapsedTime()
    });
    backoffStrategy.reset();
  });

  connection.onclose((error) => {
    logger.error('Connection closed', {
      attempts: backoffStrategy.currentAttempt,
      totalTime: backoffStrategy.getTotalElapsedTime(),
      error: error?.message
    });
    backoffStrategy.reset();
  });

  return connection;
}
```

---

## Retry Decision Logic

### Flowchart

```
Disconnection Detected
        │
        ▼
  Start Reconnection Cycle
  (Record start time)
        │
        ▼
  Attempt Counter = 1
        │
        ▼
  ┌─────────────────────┐
  │ Should Retry Check? │
  └─────────┬───────────┘
            │
       ┌────┴────┐
       │         │
    YES│         │NO
       │         │
       ▼         ▼
  Get Next Delay    Permanent Failure
  from Sequence     Trigger onclose()
       │             Stop Reconnection
       ▼
  Wait for Delay
  (async timer)
       │
       ▼
  Attempt Reconnection
       │
   ┌───┴───┐
   │       │
SUCCESS   FAIL
   │       │
   ▼       ▼
 Reset  Increment
 State  Attempt Counter
   │       │
   ▼       └──────┐
  Done            │
                  ▼
           ┌─────────────────────┐
           │ Attempt <= Max?     │
           │ AND                 │
           │ Time <= Max?        │
           └──────┬──────────────┘
                  │
             ┌────┴────┐
             │         │
          YES│         │NO
             │         │
             └─────┐   └──────┐
                   │          │
                   ▼          ▼
              Loop Back   Permanent
              to Delay    Failure
              Calculation
```

### shouldRetry() Decision Matrix

| Condition | Attempt Count | Elapsed Time | Result | Action |
|-----------|---------------|--------------|--------|---------|
| Normal | 1-9 | < 5 min | RETRY | Continue with next delay |
| Max Attempts | 10 | Any | STOP | Trigger onclose |
| Max Duration | Any | ≥ 5 min | STOP | Trigger onclose |
| Token Expired | Any | Any | PAUSE | Refresh token, then RETRY |
| Intentional Disconnect | N/A | N/A | STOP | Do not retry |

---

## Jitter Implementation (Optional)

### Purpose of Jitter

Jitter adds randomness to retry delays to prevent "thundering herd" problems where many clients reconnect simultaneously after a server outage, potentially overwhelming the server again.

**When to Use Jitter:**
- ✅ Multi-instance deployments with 10+ simultaneous clients
- ✅ Load-balanced server infrastructure
- ✅ High-traffic production environments
- ❌ Single-instance applications (not needed)
- ❌ Development/testing environments

### Jitter Calculation

```typescript
function applyJitter(baseDelay: number, jitterFactor: number): number {
  // jitterFactor of 0.25 means ±25% randomness
  // Example: 10000ms base with 0.25 jitter → 7500-12500ms range

  const jitterAmount = baseDelay * jitterFactor;
  const randomOffset = (Math.random() - 0.5) * 2 * jitterAmount;
  const delayWithJitter = baseDelay + randomOffset;

  return Math.round(Math.max(0, delayWithJitter));
}

// Examples:
applyJitter(10000, 0.0);  // Always returns 10000 (no jitter)
applyJitter(10000, 0.25); // Returns 7500-12500 (±25% jitter)
applyJitter(10000, 0.50); // Returns 5000-15000 (±50% jitter)
```

### Jitter Configuration Examples

```yaml
# No jitter (deterministic, recommended for single instance)
signalr:
  reconnection:
    jitterFactor: 0.0

# Light jitter (±10%, recommended for small deployments)
signalr:
  reconnection:
    jitterFactor: 0.1

# Moderate jitter (±25%, recommended for large deployments)
signalr:
  reconnection:
    jitterFactor: 0.25

# Heavy jitter (±50%, extreme cases only)
signalr:
  reconnection:
    jitterFactor: 0.5
```

---

## User Experience Considerations

### UI Reconnection Status Display

```typescript
// Show reconnection status to user
function displayReconnectionStatus(
  attemptNumber: number,
  maxAttempts: number,
  nextDelay: number
): void {
  const percentage = (attemptNumber / maxAttempts) * 100;
  const timeUntilNextAttempt = formatDelay(nextDelay);

  uiManager.showNotification({
    type: 'warning',
    title: 'Connection Lost',
    message: `Reconnecting... (Attempt ${attemptNumber}/${maxAttempts})`,
    subtitle: `Next attempt in ${timeUntilNextAttempt}`,
    progress: percentage,
    dismissible: false,
    actions: [
      { label: 'Manual Retry', onClick: () => connection.start() },
      { label: 'Switch to Offline Mode', onClick: () => activateOfflineMode() }
    ]
  });
}

// Examples:
// Attempt 1: "Reconnecting... (Attempt 1/10) - Next attempt immediately"
// Attempt 2: "Reconnecting... (Attempt 2/10) - Next attempt in 2 seconds"
// Attempt 5: "Reconnecting... (Attempt 5/10) - Next attempt in 1 minute"
// Attempt 10: "Reconnecting... (Attempt 10/10) - Final attempt in 1 minute"
```

### Progress Visualization

```
Reconnection Progress Bar:

Attempt 1/10:  ▓░░░░░░░░░ 10%
Attempt 5/10:  ▓▓▓▓▓░░░░░ 50%
Attempt 10/10: ▓▓▓▓▓▓▓▓▓▓ 100% (switching to fallback mode...)
```

---

## Implementation Checklist

### Phase 1: Core Backoff Logic
- [ ] Create ExponentialBackoffStrategy class
- [ ] Implement getNextDelay() method with array-based delays
- [ ] Implement shouldRetry() method with attempt and time limits
- [ ] Implement getTotalElapsedTime() method
- [ ] Implement isMaxDurationExceeded() method
- [ ] Implement reset() and startReconnectionCycle() methods
- [ ] Add comprehensive logging for all backoff decisions

### Phase 2: Configuration Management
- [ ] Load reconnection config from YAML file
- [ ] Implement configuration validation logic
- [ ] Define safe default configuration
- [ ] Handle invalid configuration gracefully
- [ ] Add configuration hot-reload support (optional)

### Phase 3: SignalR Integration
- [ ] Integrate ExponentialBackoffStrategy with HubConnectionBuilder
- [ ] Pass retryDelays array to .withAutomaticReconnect()
- [ ] Implement onreconnecting handler with backoff logic
- [ ] Implement onreconnected handler with state reset
- [ ] Implement onclose handler for max attempts exceeded

### Phase 4: Jitter Implementation (Optional)
- [ ] Implement applyJitter() function
- [ ] Add jitterFactor configuration option
- [ ] Integrate jitter into getNextDelay() method
- [ ] Test jitter distribution (ensure reasonable randomness)
- [ ] Document when to use jitter vs. deterministic delays

### Phase 5: UI Integration
- [ ] Display reconnection attempt counter in UI
- [ ] Display next retry countdown timer
- [ ] Show progress bar for reconnection attempts
- [ ] Add manual retry button
- [ ] Add "Switch to Offline Mode" button
- [ ] Show delay sequence explanation in settings/help

### Phase 6: Testing
- [ ] Unit test: getNextDelay() with all attempt numbers
- [ ] Unit test: shouldRetry() with various conditions
- [ ] Unit test: Configuration validation
- [ ] Unit test: Jitter calculation (if implemented)
- [ ] Integration test: Full reconnection cycle
- [ ] Integration test: Max attempts exceeded scenario
- [ ] Integration test: Max duration exceeded scenario
- [ ] Performance test: Backoff calculation speed
- [ ] Load test: Multiple simultaneous reconnections with jitter

---

## Validation Criteria

### Functional Validation

**VC-1: Retry Delay Sequence**
- ✅ Attempt 1 has 0ms delay (immediate)
- ✅ Attempt 2 has 2000ms delay (2 seconds)
- ✅ Attempt 3 has 10000ms delay (10 seconds)
- ✅ Attempt 4 has 30000ms delay (30 seconds)
- ✅ Attempt 5+ have 60000ms delay (1 minute)

**VC-2: Maximum Attempts**
- ✅ Exactly 10 reconnection attempts are made
- ✅ After 10 failed attempts, onclose handler fires
- ✅ Attempt counter resets to 0 on successful reconnection

**VC-3: Maximum Duration**
- ✅ Reconnection stops if max duration (5 minutes) exceeded
- ✅ Max duration check is independent of attempt count
- ✅ Time calculation is accurate to ±1 second

**VC-4: Configuration**
- ✅ Custom retry delays can be loaded from YAML config
- ✅ Custom max attempts can be loaded from YAML config
- ✅ Invalid configuration triggers safe defaults
- ✅ Configuration validation errors are logged

**VC-5: Jitter (if enabled)**
- ✅ Jitter adds randomness within configured factor range
- ✅ Delays with jitter are never negative
- ✅ Jitter respects min/max delay constraints

### Performance Validation

**PV-1: Calculation Speed**
- ✅ getNextDelay() executes in < 10ms
- ✅ shouldRetry() executes in < 10ms
- ✅ No performance degradation over 100 reconnection cycles

**PV-2: Memory Usage**
- ✅ No memory leaks after 100 reconnection cycles
- ✅ Backoff strategy uses < 1KB memory

### Reliability Validation

**RV-1: Predictability**
- ✅ Without jitter, delays are 100% deterministic
- ✅ With jitter, delays follow expected distribution
- ✅ Delay sequence is documented and user-visible

**RV-2: Server Protection**
- ✅ Delays prevent rapid reconnection attempts
- ✅ Exponential backoff gives server recovery time
- ✅ Max delay cap prevents excessive waiting

---

## Integration Points

### Dependencies
- **SignalR Client Library**: @microsoft/signalr
- **Configuration Manager**: YAML config loading
- **Logger**: Backoff decision logging
- **TokenManager**: Token refresh during reconnection (GAP-API-001)

### Used By
- **SignalRConnectionManager** (SIGNALR-001): Uses backoff strategy for reconnection logic
- **ConnectionHealthMonitoring** (SIGNALR-004): Uses delay calculations for timeout detection

---

## References

- **ERRORS_AND_WARNINGS_CONSOLIDATED.md**: Section "GAP-API-004: No Exponential Backoff Strategy"
- **SIGNALR_RECONNECTION_SPEC.md**: Complete reconnection handler implementation
- **CONNECTION_HEALTH_MONITORING_SPEC.md**: Connection timeout and health checks
- **Microsoft SignalR Documentation**: https://docs.microsoft.com/en-us/aspnet/core/signalr/javascript-client#reconnect-clients

---

## Appendices

### Appendix A: Delay Calculation Examples

```typescript
const strategy = new ExponentialBackoffStrategy({
  retryDelays: [0, 2000, 10000, 30000, 60000],
  maxAttempts: 10,
  maxReconnectionTime: 300000,
  jitterFactor: 0.0,
  minRetryDelay: 0,
  maxRetryDelay: 60000
});

// Example 1: Normal reconnection cycle
strategy.startReconnectionCycle();
console.log(strategy.getNextDelay(1));  // 0
console.log(strategy.getNextDelay(2));  // 2000
console.log(strategy.getNextDelay(3));  // 10000
console.log(strategy.getNextDelay(4));  // 30000
console.log(strategy.getNextDelay(5));  // 60000
console.log(strategy.getNextDelay(6));  // 60000 (capped)
console.log(strategy.getNextDelay(10)); // 60000 (capped)

// Example 2: Checking retry eligibility
console.log(strategy.shouldRetry(5));   // true (within limits)
console.log(strategy.shouldRetry(10));  // true (exactly at max)
console.log(strategy.shouldRetry(11));  // false (exceeded max attempts)

// Example 3: Time duration check
strategy.startReconnectionCycle();
// ... simulate 5 minutes passing
console.log(strategy.isMaxDurationExceeded()); // true
console.log(strategy.shouldRetry(5)); // false (time limit exceeded)
```

### Appendix B: Alternative Backoff Strategies (Not Recommended)

**Exponential Doubling (Not Used):**
```
Attempt 1: 1s
Attempt 2: 2s (2^1)
Attempt 3: 4s (2^2)
Attempt 4: 8s (2^3)
Attempt 5: 16s (2^4)
Attempt 6: 32s (2^5)
Attempt 7: 64s (2^6)

Problem: Delays grow too fast, user waits too long for later attempts
```

**Linear Backoff (Not Used):**
```
Attempt 1: 5s
Attempt 2: 10s
Attempt 3: 15s
Attempt 4: 20s
Attempt 5: 25s

Problem: Not aggressive enough at beginning, doesn't protect server
```

**Why Our Sequence is Optimal:**
1. Fast first retry (0ms) catches transient issues
2. Quick escalation (2s → 10s) handles brief outages
3. Moderate delays (30s) protect server during recovery
4. Capped maximum (60s) prevents excessive user waiting
5. Total duration (6.7 min) is reasonable before giving up

---

**End of Specification**
