# SignalR Connection Health Monitoring Specification

**doc_id:** SIGNALR-004
**version:** 1.0
**status:** DRAFT
**addresses:** GAP-API-005 (HIGH) from ERRORS_AND_WARNINGS_CONSOLIDATED.md
**created:** 2025-10-22
**last_updated:** 2025-10-22

---

## Overview

This specification defines the connection health monitoring strategy for SignalR, including heartbeat/ping mechanisms, connection timeout detection, stale connection cleanup, and health check intervals. It addresses GAP-API-005 which identified the lack of connection health monitoring.

**Critical Gap Addressed:**
> "No specification for heartbeat/ping mechanisms, connection timeout detection, stale connection cleanup, or health check intervals. Cannot detect stale/dead connections, leading to missed updates."

**Design Philosophy:**
- Proactively detect dead connections before user notices missing updates
- Use periodic ping/pong to verify bidirectional communication
- Detect server-side connection timeouts
- Clean up zombie connections that appear alive but are not receiving data
- Provide visual feedback of connection health to user

---

## Requirements

### Functional Requirements

**FR-1: Heartbeat/Ping Mechanism**
- System MUST send periodic "ping" messages to server to verify connection
- Server MUST respond with "pong" message
- Ping interval MUST be configurable (default: 30 seconds)
- Ping timeout MUST be configurable (default: 5 seconds)
- If ping fails, system MUST treat connection as unhealthy

**FR-2: Connection Timeout Detection**
- System MUST detect when no data received from server for extended period
- Timeout threshold MUST be configurable (default: 120 seconds / 2 minutes)
- Stale connection MUST trigger reconnection attempt
- User MUST be notified when connection becomes stale

**FR-3: Bidirectional Health Check**
- System MUST verify both client→server and server→client communication
- Client→server: Ping requests succeed
- Server→client: SignalR events received within expected timeframe
- Connection health status MUST reflect both directions

**FR-4: Health Status Tracking**
- System MUST maintain current connection health status: HEALTHY, DEGRADED, UNHEALTHY, DISCONNECTED
- Health status MUST be based on:
  - Ping latency (round-trip time)
  - Ping success rate (last 10 pings)
  - Time since last received event
  - Reconnection attempt count
- Health status transitions MUST be logged

**FR-5: Stale Connection Cleanup**
- System MUST detect zombie connections (appear connected but not receiving data)
- Zombie detection criteria:
  - No server events received in last 2 minutes
  - Ping fails 3 consecutive times
  - Ping latency exceeds 10 seconds
- Zombie connections MUST be forcibly closed and reconnected

**FR-6: Health Metrics**
- System MUST track connection health metrics:
  - Current ping latency (milliseconds)
  - Average ping latency (last 10 pings)
  - Ping success rate (%)
  - Last successful ping timestamp
  - Last received event timestamp
  - Total uptime
  - Total downtime
  - Reconnection count
- Metrics MUST be exposed to UI for display

### Non-Functional Requirements

**NFR-1: Performance**
- Ping mechanism MUST NOT add significant overhead (< 1KB payload)
- Health checks MUST NOT block SignalR event processing
- Health status calculation MUST execute in < 50ms

**NFR-2: Network Efficiency**
- Ping interval MUST balance detection speed with network overhead
- Ping payload MUST be minimal (timestamp only)
- Pong response MUST be minimal (echo timestamp)

**NFR-3: User Experience**
- Health status MUST be visible to user (icon, indicator, tooltip)
- Degraded connection MUST show warning before disconnection
- Health metrics MUST be accessible in debug/diagnostics UI

---

## Architecture

### Connection Health States

```
┌─────────────┐
│  HEALTHY    │  Ping latency < 500ms, success rate > 95%
└─────┬───────┘
      │
      │ Ping latency 500-2000ms OR success rate 80-95%
      ▼
┌─────────────┐
│  DEGRADED   │  Elevated latency or occasional failures
└─────┬───────┘
      │
      │ Ping latency > 2000ms OR success rate < 80%
      ▼
┌─────────────┐
│ UNHEALTHY   │  High latency or frequent failures
└─────┬───────┘
      │
      │ 3 consecutive ping failures OR no events for 2 minutes
      ▼
┌──────────────┐
│ DISCONNECTED │  Connection dead, trigger reconnection
└──────────────┘
```

### Component Architecture

```
┌─────────────────────────────────────────────────┐
│      ConnectionHealthMonitor                    │
├─────────────────────────────────────────────────┤
│ - pingInterval: number                          │
│ - pingTimeout: number                           │
│ - staleThreshold: number                        │
│ - currentHealth: HealthStatus                   │
│ - lastEventTime: number                         │
│ - pingStats: PingStatistics                     │
├─────────────────────────────────────────────────┤
│ + startMonitoring(): void                       │
│ + stopMonitoring(): void                        │
│ + sendPing(): Promise<PingResult>               │
│ + recordEventReceived(): void                   │
│ + getHealthStatus(): HealthStatus               │
│ + getHealthMetrics(): HealthMetrics             │
│ + isConnectionStale(): boolean                  │
└─────────────────────────────────────────────────┘
                      │
                      │ Uses
                      ▼
┌─────────────────────────────────────────────────┐
│          PingManager                            │
├─────────────────────────────────────────────────┤
│ - pingHistory: PingResult[]                     │
│ - pendingPing: Promise<PingResult> | null       │
├─────────────────────────────────────────────────┤
│ + executePing(): Promise<PingResult>            │
│ + getPingStatistics(): PingStatistics           │
│ + getAverageLatency(): number                   │
│ + getSuccessRate(): number                      │
└─────────────────────────────────────────────────┘
```

---

## Ping Mechanism Design

### Ping Message Format

```typescript
interface PingMessage {
  type: 'ping';
  timestamp: number;        // Client send time (Unix milliseconds)
  sequenceNumber: number;   // Monotonically increasing ping ID
}

interface PongMessage {
  type: 'pong';
  timestamp: number;        // Echo of client timestamp
  sequenceNumber: number;   // Echo of sequence number
  serverTime: number;       // Server receive time (for clock skew detection)
}

interface PingResult {
  sequenceNumber: number;
  success: boolean;
  latency: number;          // Round-trip time in milliseconds
  timestamp: number;        // Ping send time
  error?: string;           // Error message if failed
}
```

### Ping Execution Flow

```
1. Timer triggers (every 30 seconds)
        │
        ▼
2. Client sends PingMessage
   { type: 'ping', timestamp: Date.now(), sequenceNumber: N }
        │
        ▼
3. Start timeout timer (5 seconds)
        │
        ▼
4. Server receives ping, responds with PongMessage
   { type: 'pong', timestamp: <echoed>, sequenceNumber: N, serverTime: ... }
        │
   ┌────┴────┐
   │         │
SUCCESS    TIMEOUT
   │         │
   ▼         ▼
5a. Calculate latency    5b. Mark as failed
    latency = now - sent     latency = null
    success = true           success = false
        │                        │
        └────────┬───────────────┘
                 │
                 ▼
6. Record PingResult in history
        │
        ▼
7. Update health status based on statistics
        │
        ▼
8. If unhealthy, trigger warnings or reconnection
```

### Ping Implementation

```typescript
class PingManager {
  private pingHistory: PingResult[] = [];
  private currentSequence: number = 0;
  private maxHistorySize: number = 10;

  /**
   * Execute a ping and return result
   */
  async executePing(
    connection: HubConnection,
    timeout: number = 5000
  ): Promise<PingResult> {
    const sequenceNumber = ++this.currentSequence;
    const sendTime = Date.now();

    const pingMessage: PingMessage = {
      type: 'ping',
      timestamp: sendTime,
      sequenceNumber
    };

    try {
      // Send ping to server with timeout
      const pongMessage = await Promise.race([
        connection.invoke('Ping', pingMessage),
        this.timeout(timeout)
      ]) as PongMessage;

      const receiveTime = Date.now();
      const latency = receiveTime - sendTime;

      // Validate pong response
      if (pongMessage.sequenceNumber !== sequenceNumber) {
        throw new Error(`Sequence mismatch: expected ${sequenceNumber}, got ${pongMessage.sequenceNumber}`);
      }

      const result: PingResult = {
        sequenceNumber,
        success: true,
        latency,
        timestamp: sendTime
      };

      this.recordPing(result);
      return result;

    } catch (error) {
      const result: PingResult = {
        sequenceNumber,
        success: false,
        latency: -1,
        timestamp: sendTime,
        error: error.message
      };

      this.recordPing(result);
      return result;
    }
  }

  private timeout(ms: number): Promise<never> {
    return new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Ping timeout')), ms)
    );
  }

  private recordPing(result: PingResult): void {
    this.pingHistory.push(result);

    // Keep only last N pings
    if (this.pingHistory.length > this.maxHistorySize) {
      this.pingHistory.shift();
    }
  }

  /**
   * Calculate ping statistics from recent history
   */
  getPingStatistics(): PingStatistics {
    if (this.pingHistory.length === 0) {
      return {
        successCount: 0,
        failureCount: 0,
        successRate: 0,
        averageLatency: 0,
        minLatency: 0,
        maxLatency: 0,
        lastPingTime: 0,
        lastSuccessfulPingTime: 0
      };
    }

    const successfulPings = this.pingHistory.filter(p => p.success);
    const latencies = successfulPings.map(p => p.latency);

    return {
      successCount: successfulPings.length,
      failureCount: this.pingHistory.length - successfulPings.length,
      successRate: (successfulPings.length / this.pingHistory.length) * 100,
      averageLatency: latencies.length > 0
        ? latencies.reduce((a, b) => a + b, 0) / latencies.length
        : 0,
      minLatency: latencies.length > 0 ? Math.min(...latencies) : 0,
      maxLatency: latencies.length > 0 ? Math.max(...latencies) : 0,
      lastPingTime: this.pingHistory[this.pingHistory.length - 1].timestamp,
      lastSuccessfulPingTime: successfulPings.length > 0
        ? successfulPings[successfulPings.length - 1].timestamp
        : 0
    };
  }

  getAverageLatency(): number {
    return this.getPingStatistics().averageLatency;
  }

  getSuccessRate(): number {
    return this.getPingStatistics().successRate;
  }

  getConsecutiveFailures(): number {
    let failures = 0;
    for (let i = this.pingHistory.length - 1; i >= 0; i--) {
      if (this.pingHistory[i].success) {
        break;
      }
      failures++;
    }
    return failures;
  }
}
```

---

## Health Status Determination

### Health Status Enum

```typescript
enum HealthStatus {
  HEALTHY = 'healthy',           // All metrics good
  DEGRADED = 'degraded',         // Some metrics concerning
  UNHEALTHY = 'unhealthy',       // Multiple metrics bad
  DISCONNECTED = 'disconnected'  // Connection dead
}
```

### Health Calculation Algorithm

```typescript
class ConnectionHealthMonitor {
  private pingManager: PingManager;
  private lastEventTime: number = Date.now();
  private lastHealthStatus: HealthStatus = HealthStatus.DISCONNECTED;

  /**
   * Calculate current health status based on multiple factors
   */
  getHealthStatus(connectionState: ConnectionState): HealthStatus {
    // If SignalR connection is not CONNECTED, return DISCONNECTED
    if (connectionState !== ConnectionState.CONNECTED) {
      return HealthStatus.DISCONNECTED;
    }

    const stats = this.pingManager.getPingStatistics();
    const avgLatency = stats.averageLatency;
    const successRate = stats.successRate;
    const consecutiveFailures = this.pingManager.getConsecutiveFailures();
    const timeSinceLastEvent = Date.now() - this.lastEventTime;

    // DISCONNECTED: Connection is dead
    if (consecutiveFailures >= 3) {
      return HealthStatus.DISCONNECTED;
    }

    if (timeSinceLastEvent > 120000) { // 2 minutes
      return HealthStatus.DISCONNECTED;
    }

    // UNHEALTHY: High latency or low success rate
    if (avgLatency > 2000 || successRate < 80) {
      return HealthStatus.UNHEALTHY;
    }

    // DEGRADED: Moderate latency or occasional failures
    if (avgLatency > 500 || successRate < 95) {
      return HealthStatus.DEGRADED;
    }

    // HEALTHY: All metrics good
    return HealthStatus.HEALTHY;
  }

  /**
   * Record that an event was received from server
   * (updates lastEventTime for stale detection)
   */
  recordEventReceived(): void {
    this.lastEventTime = Date.now();
  }

  /**
   * Check if connection is stale (no events in 2 minutes)
   */
  isConnectionStale(): boolean {
    const timeSinceLastEvent = Date.now() - this.lastEventTime;
    return timeSinceLastEvent > 120000; // 2 minutes
  }

  /**
   * Get comprehensive health metrics
   */
  getHealthMetrics(): HealthMetrics {
    const stats = this.pingManager.getPingStatistics();
    const currentHealth = this.getHealthStatus(connectionState);

    return {
      status: currentHealth,
      pingLatency: stats.averageLatency,
      pingSuccessRate: stats.successRate,
      consecutiveFailures: this.pingManager.getConsecutiveFailures(),
      timeSinceLastEvent: Date.now() - this.lastEventTime,
      lastPingTime: stats.lastPingTime,
      uptime: this.calculateUptime(),
      reconnectionCount: this.reconnectionCount
    };
  }
}
```

### Health Status Transition Logic

```
HEALTHY → DEGRADED:
  - Average ping latency increases to 500-2000ms
  - Ping success rate drops to 80-95%
  - 1-2 consecutive ping failures

DEGRADED → UNHEALTHY:
  - Average ping latency exceeds 2000ms
  - Ping success rate drops below 80%
  - Frequent packet loss or timeouts

UNHEALTHY → DISCONNECTED:
  - 3+ consecutive ping failures
  - No events received in 2 minutes
  - SignalR reports disconnection

DISCONNECTED → HEALTHY:
  - After successful reconnection
  - First ping succeeds with low latency
  - Events resume

DEGRADED → HEALTHY:
  - Latency improves below 500ms
  - Success rate improves above 95%
  - No recent failures
```

---

## Stale Connection Detection

### Zombie Connection Criteria

A connection is considered a "zombie" (stale) if:
1. SignalR connection state is CONNECTED, BUT
2. No server events received in last 2 minutes, OR
3. Last 3 pings failed, OR
4. Ping latency consistently > 10 seconds

### Stale Detection Implementation

```typescript
class ConnectionHealthMonitor {
  private staleThreshold: number = 120000; // 2 minutes

  /**
   * Check if connection meets zombie criteria
   */
  isZombieConnection(connectionState: ConnectionState): boolean {
    // Must appear connected
    if (connectionState !== ConnectionState.CONNECTED) {
      return false;
    }

    // Check if stale (no events in 2 minutes)
    if (this.isConnectionStale()) {
      return true;
    }

    // Check if pings consistently failing
    const consecutiveFailures = this.pingManager.getConsecutiveFailures();
    if (consecutiveFailures >= 3) {
      return true;
    }

    // Check if latency is extremely high
    const avgLatency = this.pingManager.getAverageLatency();
    if (avgLatency > 10000) { // 10 seconds
      return true;
    }

    return false;
  }

  /**
   * Force cleanup of zombie connection
   */
  async cleanupZombieConnection(connection: HubConnection): Promise<void> {
    logger.warn('Zombie connection detected, forcing cleanup', {
      timeSinceLastEvent: Date.now() - this.lastEventTime,
      consecutiveFailures: this.pingManager.getConsecutiveFailures(),
      avgLatency: this.pingManager.getAverageLatency()
    });

    // Stop connection
    await connection.stop();

    // Clear local state
    this.lastEventTime = Date.now();
    this.lastHealthStatus = HealthStatus.DISCONNECTED;

    // Trigger reconnection
    await connection.start();
  }
}
```

---

## Configuration Schema

```yaml
signalr:
  health:
    # Ping/heartbeat configuration
    ping:
      # Interval between ping messages (milliseconds)
      interval: 30000  # 30 seconds

      # Timeout for ping response (milliseconds)
      timeout: 5000  # 5 seconds

      # Number of consecutive failures before considering connection dead
      maxConsecutiveFailures: 3

      # Enable ping mechanism (disable for debugging)
      enabled: true

    # Stale connection detection
    stale:
      # Time without events before considering connection stale (milliseconds)
      threshold: 120000  # 2 minutes

      # Enable automatic cleanup of stale connections
      autoCleanup: true

      # Interval for checking stale connections (milliseconds)
      checkInterval: 60000  # 1 minute

    # Health status thresholds
    thresholds:
      # Latency thresholds (milliseconds)
      healthyMaxLatency: 500
      degradedMaxLatency: 2000
      unhealthyMaxLatency: 10000

      # Success rate thresholds (percentage)
      healthyMinSuccessRate: 95
      degradedMinSuccessRate: 80
      unhealthyMinSuccessRate: 50

    # Health metrics
    metrics:
      # Number of ping results to keep in history
      pingHistorySize: 10

      # Enable detailed health metrics logging
      enableDetailedLogging: false

      # Interval for logging health metrics (milliseconds)
      logInterval: 300000  # 5 minutes

    # UI indicators
    ui:
      # Show connection health indicator in header
      showHealthIndicator: true

      # Show latency in health tooltip
      showLatencyInTooltip: true

      # Show warning when connection degraded
      warnOnDegradedConnection: true

      # Colors for health status
      colors:
        healthy: '#00C851'     # Green
        degraded: '#FFB800'    # Yellow
        unhealthy: '#FF4444'   # Red
        disconnected: '#AAAAAA' # Gray
```

---

## Health Monitoring Loop

### Monitoring Lifecycle

```typescript
class ConnectionHealthMonitor {
  private pingTimer: NodeJS.Timeout | null = null;
  private staleCheckTimer: NodeJS.Timeout | null = null;
  private config: HealthConfig;

  /**
   * Start health monitoring
   */
  startMonitoring(connection: HubConnection): void {
    logger.info('Starting connection health monitoring', {
      pingInterval: this.config.ping.interval,
      staleThreshold: this.config.stale.threshold
    });

    // Start ping loop
    this.pingTimer = setInterval(async () => {
      const result = await this.pingManager.executePing(
        connection,
        this.config.ping.timeout
      );

      // Update health status
      const previousHealth = this.lastHealthStatus;
      const currentHealth = this.getHealthStatus(connection.state);

      if (previousHealth !== currentHealth) {
        this.onHealthStatusChanged(previousHealth, currentHealth);
      }

      // Check if connection should be considered dead
      if (currentHealth === HealthStatus.DISCONNECTED) {
        logger.error('Connection health is DISCONNECTED, triggering reconnection');
        await connection.stop(); // Triggers reconnection
      }

    }, this.config.ping.interval);

    // Start stale connection check loop
    if (this.config.stale.autoCleanup) {
      this.staleCheckTimer = setInterval(() => {
        if (this.isZombieConnection(connection.state)) {
          this.cleanupZombieConnection(connection);
        }
      }, this.config.stale.checkInterval);
    }

    // Hook into SignalR events to track received data
    this.hookSignalREvents(connection);
  }

  /**
   * Stop health monitoring
   */
  stopMonitoring(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }

    if (this.staleCheckTimer) {
      clearInterval(this.staleCheckTimer);
      this.staleCheckTimer = null;
    }

    logger.info('Connection health monitoring stopped');
  }

  /**
   * Hook into SignalR event handlers to track received data
   */
  private hookSignalREvents(connection: HubConnection): void {
    // Wrap all SignalR event handlers to record event receipt
    const originalOn = connection.on.bind(connection);
    connection.on = (methodName: string, newMethod: (...args: any[]) => void) => {
      const wrappedMethod = (...args: any[]) => {
        this.recordEventReceived();
        newMethod(...args);
      };
      originalOn(methodName, wrappedMethod);
    };
  }

  /**
   * Handle health status changes
   */
  private onHealthStatusChanged(
    previousHealth: HealthStatus,
    currentHealth: HealthStatus
  ): void {
    this.lastHealthStatus = currentHealth;

    logger.info('Connection health status changed', {
      from: previousHealth,
      to: currentHealth,
      metrics: this.getHealthMetrics()
    });

    // Emit event for UI updates
    eventBus.emit('connection:health-changed', {
      previousHealth,
      currentHealth,
      metrics: this.getHealthMetrics()
    });

    // Show user warnings if connection degraded
    if (currentHealth === HealthStatus.DEGRADED && this.config.ui.warnOnDegradedConnection) {
      uiManager.showWarning('Connection quality degraded. You may experience delays.');
    }

    if (currentHealth === HealthStatus.UNHEALTHY) {
      uiManager.showWarning('Poor connection quality. Attempting to reconnect...');
    }
  }
}
```

---

## UI Integration

### Health Indicator Component

```typescript
interface HealthIndicatorProps {
  status: HealthStatus;
  metrics: HealthMetrics;
  onClick?: () => void;
}

function HealthIndicator({ status, metrics, onClick }: HealthIndicatorProps) {
  const getStatusIcon = () => {
    switch (status) {
      case HealthStatus.HEALTHY:
        return '●'; // Green dot
      case HealthStatus.DEGRADED:
        return '●'; // Yellow dot
      case HealthStatus.UNHEALTHY:
        return '●'; // Red dot
      case HealthStatus.DISCONNECTED:
        return '○'; // Gray hollow circle
    }
  };

  const getStatusLabel = () => {
    switch (status) {
      case HealthStatus.HEALTHY:
        return 'Connected';
      case HealthStatus.DEGRADED:
        return 'Degraded';
      case HealthStatus.UNHEALTHY:
        return 'Unstable';
      case HealthStatus.DISCONNECTED:
        return 'Disconnected';
    }
  };

  const getTooltipContent = () => {
    if (status === HealthStatus.DISCONNECTED) {
      return 'Disconnected - Attempting to reconnect...';
    }

    return `
      Status: ${getStatusLabel()}
      Latency: ${metrics.pingLatency.toFixed(0)}ms
      Success Rate: ${metrics.pingSuccessRate.toFixed(1)}%
      Last Event: ${formatTimeSince(metrics.timeSinceLastEvent)}
    `;
  };

  return (
    <div className="health-indicator" onClick={onClick}>
      <span className={`status-icon status-${status}`}>
        {getStatusIcon()}
      </span>
      <span className="status-label">{getStatusLabel()}</span>
      <Tooltip content={getTooltipContent()} />
    </div>
  );
}
```

### Health Metrics Dashboard (Debug View)

```typescript
function HealthMetricsDashboard({ metrics }: { metrics: HealthMetrics }) {
  return (
    <div className="health-metrics-dashboard">
      <h3>Connection Health Metrics</h3>

      <div className="metric-row">
        <span className="metric-label">Status:</span>
        <span className={`metric-value status-${metrics.status}`}>
          {metrics.status.toUpperCase()}
        </span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Ping Latency:</span>
        <span className="metric-value">{metrics.pingLatency.toFixed(0)}ms</span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Success Rate:</span>
        <span className="metric-value">{metrics.pingSuccessRate.toFixed(1)}%</span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Consecutive Failures:</span>
        <span className="metric-value">{metrics.consecutiveFailures}</span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Last Event:</span>
        <span className="metric-value">
          {formatTimeSince(metrics.timeSinceLastEvent)}
        </span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Uptime:</span>
        <span className="metric-value">{formatDuration(metrics.uptime)}</span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Reconnections:</span>
        <span className="metric-value">{metrics.reconnectionCount}</span>
      </div>
    </div>
  );
}
```

---

## Implementation Checklist

### Phase 1: Core Ping Mechanism
- [ ] Implement PingManager class
- [ ] Implement executePing() method with timeout
- [ ] Implement ping history tracking (last 10 pings)
- [ ] Implement getPingStatistics() method
- [ ] Add server-side Ping hub method (if needed)
- [ ] Test ping/pong round-trip

### Phase 2: Health Status Tracking
- [ ] Implement ConnectionHealthMonitor class
- [ ] Implement getHealthStatus() algorithm
- [ ] Implement health status transition logic
- [ ] Implement recordEventReceived() tracking
- [ ] Implement isConnectionStale() detection
- [ ] Add logging for all health status changes

### Phase 3: Monitoring Loop
- [ ] Implement startMonitoring() with ping timer
- [ ] Implement stopMonitoring() cleanup
- [ ] Implement stale connection check timer
- [ ] Hook into SignalR event handlers for event tracking
- [ ] Implement onHealthStatusChanged() handler
- [ ] Test monitoring loop lifecycle

### Phase 4: Zombie Connection Cleanup
- [ ] Implement isZombieConnection() detection
- [ ] Implement cleanupZombieConnection() forced reconnection
- [ ] Test zombie detection with network simulation
- [ ] Test automatic cleanup and reconnection

### Phase 5: Configuration
- [ ] Load health monitoring config from YAML
- [ ] Implement configuration validation
- [ ] Add configuration hot-reload (optional)
- [ ] Document all configuration options

### Phase 6: UI Integration
- [ ] Create HealthIndicator component (status icon)
- [ ] Create health status tooltip with metrics
- [ ] Create HealthMetricsDashboard (debug view)
- [ ] Add health indicator to application header
- [ ] Show warnings when connection degraded
- [ ] Test UI updates on health status changes

### Phase 7: Testing
- [ ] Unit test: Ping execution and timeout
- [ ] Unit test: Health status calculation
- [ ] Unit test: Stale connection detection
- [ ] Integration test: Full monitoring loop
- [ ] Integration test: Zombie connection cleanup
- [ ] Network simulation test: High latency
- [ ] Network simulation test: Packet loss
- [ ] Network simulation test: Connection drop

---

## Validation Criteria

### Functional Validation

**VC-1: Ping Mechanism**
- ✅ Pings sent every 30 seconds
- ✅ Ping timeout at 5 seconds
- ✅ Pong response received and validated
- ✅ Latency calculated correctly (round-trip time)
- ✅ Ping failures detected and recorded

**VC-2: Health Status**
- ✅ HEALTHY status when latency < 500ms and success > 95%
- ✅ DEGRADED status when latency 500-2000ms or success 80-95%
- ✅ UNHEALTHY status when latency > 2000ms or success < 80%
- ✅ DISCONNECTED status after 3 consecutive failures or 2min stale

**VC-3: Stale Detection**
- ✅ Connection marked stale after 2 minutes without events
- ✅ Zombie connection detected with 3 consecutive ping failures
- ✅ Zombie connection automatically cleaned up and reconnected

**VC-4: Event Tracking**
- ✅ lastEventTime updated on every SignalR event received
- ✅ Stale timer resets when events received
- ✅ Event tracking does not interfere with normal event processing

**VC-5: UI Indicators**
- ✅ Health status icon updates in real-time
- ✅ Health tooltip shows accurate metrics
- ✅ User warned when connection becomes degraded
- ✅ Debug dashboard shows comprehensive metrics

### Performance Validation

**PV-1: Ping Overhead**
- ✅ Ping payload < 1KB
- ✅ Ping execution does not block event processing
- ✅ Monitoring loop uses < 1% CPU

**PV-2: Health Calculation Speed**
- ✅ getHealthStatus() executes in < 50ms
- ✅ UI updates do not lag

### Reliability Validation

**RV-1: Detection Accuracy**
- ✅ Unhealthy connections detected within 90 seconds
- ✅ Stale connections detected within 2 minutes + 1 check interval
- ✅ False positives < 1% (healthy connections not flagged)

**RV-2: Cleanup Effectiveness**
- ✅ Zombie connections successfully cleaned up and reconnected
- ✅ No memory leaks from monitoring loop
- ✅ No zombie connections persist after cleanup

---

## Integration Points

### Dependencies
- **SignalRConnectionManager** (SIGNALR-001): Connection state and lifecycle
- **HubConnection**: SignalR connection for ping/pong
- **EventBus**: Health status change notifications
- **Logger**: Health monitoring logs
- **UIManager**: Health indicator display

### External Systems
- **SignalR Hub**: Ping hub method (server-side)

---

## References

- **ERRORS_AND_WARNINGS_CONSOLIDATED.md**: Section "GAP-API-005: Missing Connection Health Monitoring"
- **SIGNALR_RECONNECTION_SPEC.md**: Reconnection logic triggered by unhealthy status
- **EXPONENTIAL_BACKOFF_SPEC.md**: Retry delays for reconnection

---

**End of Specification**
