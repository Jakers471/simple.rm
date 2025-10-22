# Long Operation Token Handling Specification

**doc_id:** SEC-007
**version:** 1.0
**status:** DRAFT
**priority:** CRITICAL
**addresses:** GAP-API-SCENARIO-005 from ERRORS_AND_WARNINGS_CONSOLIDATED.md

## Overview

This specification defines token management strategies for long-running operations that may span multiple hours, including historical data retrieval, active SignalR connections, and continuous monitoring sessions. The goal is to prevent token expiration during operations and ensure seamless token refresh without service interruption.

## Problem Statement

**From GAP-API-SCENARIO-005:**
- Token expires during long operations (historical data retrieval can take hours)
- Token expires during active SignalR connections (24/7 monitoring)
- Token expires during long polling sessions
- No strategy for token refresh during operations
- No request replay mechanism after token refresh
- Operation failure mid-execution if token expires

## Requirements

### Functional Requirements

**FR-1: Pre-Operation Token Validation**
- System MUST check token expiry before starting long operations
- System MUST estimate operation duration and compare with token TTL
- System MUST refresh token proactively if TTL < operation estimate
- System MUST abort operation if token refresh fails

**FR-2: Mid-Operation Token Refresh**
- System MUST monitor token expiry during long operations
- System MUST trigger refresh when TTL < 30 minutes during operation
- System MUST pause operation during token refresh
- System MUST resume operation with new token after successful refresh

**FR-3: Request Replay Mechanism**
- System MUST support replaying failed requests with new token
- System MUST track request state (in-progress, completed, failed)
- System MUST implement idempotency for replay safety
- System MUST limit replay attempts (max 3 retries)

**FR-4: Operation Checkpointing**
- System MUST checkpoint progress during long operations
- System MUST support resuming from checkpoint after token refresh
- System MUST support resuming from checkpoint after failure
- System MUST clean up checkpoints after successful completion

**FR-5: SignalR Connection Token Refresh**
- System MUST refresh token during active SignalR connections
- System MUST update accessTokenFactory to return fresh token
- System MUST NOT disconnect SignalR during token refresh
- System MUST handle authentication errors during refresh

### Non-Functional Requirements

**NFR-1: Performance**
- Token refresh MUST complete in < 5 seconds
- Operation pause during refresh MUST be < 10 seconds
- Checkpoint save MUST be < 1 second
- Request replay MUST add < 2 seconds overhead

**NFR-2: Reliability**
- Operations MUST NOT fail due to token expiry
- Token refresh MUST succeed > 99.5% of the time
- Checkpoints MUST survive application crashes
- Request replay MUST maintain data consistency

**NFR-3: Transparency**
- Token refresh MUST be transparent to operation logic
- Operation code MUST NOT need token refresh awareness
- User MUST NOT experience interruption during refresh

**NFR-4: Observability**
- System MUST log all token refreshes during operations
- System MUST track operation duration and token refreshes
- System MUST alert on repeated refresh failures during operations
- System MUST expose metrics for long operation success rate

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              LongOperationTokenManager                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Operation Wrapper                                   │   │
│  │  - wrap_long_operation(op: Callable) -> Result       │   │
│  │  - check_token_before_start() -> bool                │   │
│  │  - monitor_token_during_operation() -> None          │   │
│  │  - refresh_if_needed() -> bool                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Checkpoint Manager                                  │   │
│  │  - save_checkpoint(state: dict) -> str               │   │
│  │  - load_checkpoint(checkpoint_id: str) -> dict       │   │
│  │  - delete_checkpoint(checkpoint_id: str) -> None     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  │  Request Replay Manager                              │   │
│  │  - record_request(req: Request) -> None              │   │
│  │  - replay_request(req_id: str) -> Response           │   │
│  │  - is_idempotent(req: Request) -> bool               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ TokenManager │ │ APIClient    │ │ SignalR      │
  │ (refresh)    │ │ (requests)   │ │ (connections)│
  └──────────────┘ └──────────────┘ └──────────────┘
```

### Long Operation Flow with Token Refresh

```
Operation    OperationWrapper    TokenManager    APIClient    TradeStationAPI
    │             │                   │               │               │
    │─start()────►│                   │               │               │
    │             │                   │               │               │
    │             ├─check_token_ttl()►               │               │
    │             │◄──ttl=22hrs───────┤               │               │
    │             │                   │               │               │
    │             │  [Operation estimate: 3 hours]    │               │
    │             │  [TTL sufficient: 22hrs > 3hrs]   │               │
    │             │                   │               │               │
    │             ├─execute_operation()──────────────►│               │
    │             │                   │               │               │
    │             │  [Operation runs for 2 hours]     │               │
    │             │                   │               │               │
    │             │  [Background monitor checks TTL]  │               │
    │             │                   │               │               │
    │             ├─check_token_ttl()►               │               │
    │             │◄──ttl=20hrs───────┤               │               │
    │             │                   │               │               │
    │             │  [Still safe: 20hrs > 1hr remaining]              │
    │             │                   │               │               │
    │             │  [Operation continues...]         │               │
    │             │                   │               │               │
    │◄─complete───┤                   │               │               │
```

### Token Expiry During Operation with Refresh

```
Operation    OperationWrapper    TokenManager    APIClient    TradeStationAPI
    │             │                   │               │               │
    │─start()────►│                   │               │               │
    │             │                   │               │               │
    │             ├─check_token_ttl()►               │               │
    │             │◄──ttl=1.5hrs──────┤               │               │
    │             │                   │               │               │
    │             │  [Operation estimate: 3 hours]    │               │
    │             │  [TTL insufficient: 1.5hrs < 3hrs]│               │
    │             │  [REFRESH NEEDED BEFORE START]    │               │
    │             │                   │               │               │
    │             ├─refresh_token()───►               │               │
    │             │                   ├──/validate───►               │
    │             │                   │◄──new_token───┤               │
    │             │◄──success─────────┤               │               │
    │             │                   │               │               │
    │             │  [New TTL: 24 hours]              │               │
    │             │                   │               │               │
    │             ├─execute_operation()──────────────►│               │
    │             │                   │               │──GET /bars───►│
    │             │                   │               │◄──data────────│
    │             │                   │               │               │
    │             │  [Operation runs for 1 hour]      │               │
    │             │                   │               │               │
    │             │  [Background monitor checks TTL]  │               │
    │             │                   │               │               │
    │             ├─check_token_ttl()►               │               │
    │             │◄──ttl=23hrs───────┤               │               │
    │             │                   │               │               │
    │             │  [Safe: 23hrs > 2hrs remaining]   │               │
    │             │                   │               │               │
    │◄─complete───┤                   │               │               │
```

### Operation Checkpointing with Failure Recovery

```
Operation    CheckpointManager    OperationWrapper    TokenManager
    │             │                     │                  │
    │─start()────►│                     │                  │
    │             │                     │                  │
    │             │  [Process 1000 bars]│                  │
    │             │                     │                  │
    │             ├─save_checkpoint()──►                   │
    │             │  {last_bar: 1000,   │                  │
    │             │   timestamp: ...}   │                  │
    │             │◄──checkpoint_id─────┤                  │
    │             │                     │                  │
    │             │  [Process 1000 more bars]              │
    │             │                     │                  │
    │             ├─save_checkpoint()──►                   │
    │             │  {last_bar: 2000}   │                  │
    │             │                     │                  │
    │             │  [Token expires, refresh needed]       │
    │             │                     │                  │
    │             │                     ├─refresh()───────►│
    │             │                     │◄─new_token───────┤
    │             │                     │                  │
    │             │  [Resume from checkpoint]              │
    │             │                     │                  │
    │             ├─load_checkpoint()──►                   │
    │             │◄──{last_bar: 2000}──┤                  │
    │             │                     │                  │
    │             │  [Continue from bar 2000]              │
    │             │                     │                  │
    │◄─complete───┤                     │                  │
```

## Data Structures

### OperationContext Structure

```yaml
OperationContext:
  operation_id:
    type: string (UUID)
    example: "550e8400-e29b-41d4-a716-446655440000"
    description: "Unique operation identifier"

  operation_type:
    type: enum
    values: [historical_data_retrieval, signalr_connection, polling_session, batch_operation]
    description: "Type of long operation"

  started_at:
    type: datetime (ISO 8601)
    description: "Operation start timestamp"

  estimated_duration_seconds:
    type: integer
    description: "Estimated operation duration"

  token_id:
    type: string (UUID)
    description: "Initial token identifier"

  token_ttl_at_start:
    type: integer
    description: "Token TTL in seconds when operation started"

  refreshes_performed:
    type: integer
    default: 0
    description: "Number of token refreshes during operation"

  checkpoints_saved:
    type: integer
    default: 0
    description: "Number of checkpoints saved"

  status:
    type: enum
    values: [running, paused, completed, failed, aborted]
    description: "Current operation status"
```

### Checkpoint Structure

```yaml
Checkpoint:
  checkpoint_id:
    type: string (UUID)
    example: "550e8400-e29b-41d4-a716-446655440000"
    description: "Unique checkpoint identifier"

  operation_id:
    type: string (UUID)
    description: "Associated operation identifier"

  timestamp:
    type: datetime (ISO 8601)
    description: "Checkpoint creation timestamp"

  progress:
    type: object
    description: "Operation-specific progress state"
    example:
      last_processed_bar: 2000
      total_bars: 20000
      last_timestamp: "2025-01-01T00:00:00Z"
      items_processed: 2000
      items_remaining: 18000

  metadata:
    type: object
    description: "Additional checkpoint metadata"
    properties:
      token_id: string (UUID)
      token_ttl_seconds: integer
      retry_count: integer

  storage_location:
    type: string
    description: "Path to checkpoint data file"
    example: "/tmp/checkpoints/550e8400-e29b-41d4-a716-446655440000.json"
```

### RequestRecord Structure (for replay)

```yaml
RequestRecord:
  request_id:
    type: string (UUID)
    description: "Unique request identifier"

  timestamp:
    type: datetime (ISO 8601)
    description: "Original request timestamp"

  endpoint:
    type: string
    example: "/api/History/retrieveBars"
    description: "API endpoint"

  method:
    type: enum
    values: [GET, POST, PUT, DELETE]
    description: "HTTP method"

  parameters:
    type: object
    description: "Request parameters"

  status:
    type: enum
    values: [pending, in_progress, completed, failed, replaying]
    description: "Request status"

  retry_count:
    type: integer
    default: 0
    max: 3
    description: "Number of replay attempts"

  idempotency_key:
    type: string (optional)
    description: "Idempotency key for safe replay"

  original_token_id:
    type: string (UUID)
    description: "Token ID when request was first made"
```

## Configuration

### Long Operation Configuration (YAML)

```yaml
# config/long_operation_config.yaml

long_operations:
  # Token monitoring
  token_monitoring:
    enabled: true
    check_interval_seconds: 300  # Check every 5 minutes
    refresh_threshold_seconds: 1800  # Refresh if TTL < 30 minutes
    abort_on_refresh_failure: true

  # Pre-operation validation
  pre_operation:
    check_token_ttl: true
    refresh_if_insufficient: true
    minimum_ttl_multiplier: 1.5  # TTL must be 1.5x operation estimate

  # Checkpointing
  checkpointing:
    enabled: true
    checkpoint_interval_seconds: 600  # Save checkpoint every 10 minutes
    checkpoint_dir: "/tmp/simple-risk-manager/checkpoints"
    max_checkpoint_age_hours: 24  # Delete checkpoints older than 24 hours

    # Checkpoint storage
    storage:
      format: "json"  # json, binary
      compression: true
      encryption: false  # Optional: encrypt sensitive checkpoint data

  # Request replay
  request_replay:
    enabled: true
    max_retry_attempts: 3
    retry_backoff_seconds: [5, 10, 30]  # Exponential backoff
    verify_idempotency: true

  # Operation types configuration
  operation_types:
    historical_data_retrieval:
      estimated_duration_seconds: 10800  # 3 hours
      checkpoint_interval_seconds: 600   # 10 minutes
      enable_resume: true

    signalr_connection:
      estimated_duration_seconds: 86400  # 24 hours (continuous)
      token_refresh_interval_seconds: 43200  # Refresh every 12 hours
      enable_auto_reconnect: true

    polling_session:
      estimated_duration_seconds: 3600  # 1 hour
      checkpoint_interval_seconds: 300  # 5 minutes
      enable_resume: true

    batch_operation:
      estimated_duration_seconds: 7200  # 2 hours
      checkpoint_interval_seconds: 600  # 10 minutes
      enable_resume: true

  # Monitoring and alerts
  monitoring:
    log_operation_start: true
    log_token_refresh: true
    log_checkpoint_save: true
    log_operation_complete: true

    # Metrics
    expose_metrics: true
    metrics:
      - operation_duration_seconds
      - token_refreshes_per_operation
      - checkpoints_per_operation
      - operation_success_rate

    # Alerts
    alert_on_operation_failure: true
    alert_on_token_refresh_failure: true
    alert_threshold_failures: 2
```

### Operation Duration Estimates

```yaml
# config/operation_estimates.yaml

operation_estimates:
  # Historical data retrieval estimates
  historical_data:
    # Estimate based on number of bars requested
    bars_per_second: 100  # API can retrieve ~100 bars/second
    overhead_seconds: 60   # Add 1 minute overhead per request

    # Example calculations:
    # 1,000 bars = 10 seconds + 60 seconds = 70 seconds
    # 10,000 bars = 100 seconds + 60 seconds = 160 seconds
    # 20,000 bars = 200 seconds + 60 seconds = 260 seconds

  # SignalR connection (continuous)
  signalr_connection:
    expected_duration_hours: 24  # Default: 24/7 monitoring
    token_refresh_frequency_hours: 12  # Refresh every 12 hours

  # Polling session
  polling_session:
    default_duration_minutes: 60
    max_duration_hours: 4

  # Batch operations
  batch_operation:
    items_per_second: 10
    overhead_seconds: 120  # 2 minutes overhead
```

## Implementation Examples

### Historical Data Retrieval with Token Handling

```python
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

class HistoricalDataRetriever:
    """Retrieve historical data with token refresh handling."""

    def __init__(
        self,
        token_manager: TokenManager,
        api_client: APIClient,
        checkpoint_manager: CheckpointManager
    ):
        self.token_manager = token_manager
        self.api_client = api_client
        self.checkpoint_manager = checkpoint_manager

    async def retrieve_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1min"
    ) -> List[dict]:
        """
        Retrieve historical bars with token refresh handling.

        This operation may take hours for large date ranges.
        Token refresh is handled automatically.
        """
        # Estimate operation duration
        total_days = (end_date - start_date).days
        estimated_duration_seconds = self._estimate_duration(total_days, interval)

        # Check if token TTL is sufficient
        token_ttl = await self.token_manager.get_token_ttl()

        if token_ttl < estimated_duration_seconds * 1.5:
            # Insufficient TTL - refresh before starting
            logger.info(
                f"Token TTL ({token_ttl}s) insufficient for operation "
                f"(estimated {estimated_duration_seconds}s). Refreshing..."
            )
            await self.token_manager.refresh_token()

        # Create operation context
        operation_id = str(uuid.uuid4())
        operation_context = OperationContext(
            operation_id=operation_id,
            operation_type="historical_data_retrieval",
            started_at=datetime.utcnow(),
            estimated_duration_seconds=estimated_duration_seconds,
            token_id=await self.token_manager.get_token_id(),
            token_ttl_at_start=await self.token_manager.get_token_ttl()
        )

        logger.info(
            f"Starting historical data retrieval: "
            f"operation_id={operation_id}, "
            f"symbol={symbol}, "
            f"estimated_duration={estimated_duration_seconds}s"
        )

        # Start background token monitor
        monitor_task = asyncio.create_task(
            self._monitor_token(operation_context)
        )

        try:
            # Execute operation with checkpointing
            result = await self._retrieve_with_checkpointing(
                operation_id,
                symbol,
                start_date,
                end_date,
                interval
            )

            logger.info(
                f"Historical data retrieval complete: "
                f"operation_id={operation_id}, "
                f"bars_retrieved={len(result)}"
            )

            return result

        finally:
            # Stop token monitor
            monitor_task.cancel()

            # Clean up checkpoints
            await self.checkpoint_manager.delete_checkpoints(operation_id)

    async def _monitor_token(self, context: OperationContext) -> None:
        """
        Background task to monitor token TTL during operation.
        Triggers refresh if TTL drops below threshold.
        """
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                token_ttl = await self.token_manager.get_token_ttl()

                if token_ttl < 1800:  # Less than 30 minutes remaining
                    logger.warning(
                        f"Token TTL low during operation: "
                        f"operation_id={context.operation_id}, "
                        f"ttl={token_ttl}s. Refreshing..."
                    )

                    # Refresh token
                    await self.token_manager.refresh_token()

                    context.refreshes_performed += 1

                    logger.info(
                        f"Token refreshed during operation: "
                        f"operation_id={context.operation_id}, "
                        f"new_ttl={await self.token_manager.get_token_ttl()}s"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Token monitor error: {e}")

    async def _retrieve_with_checkpointing(
        self,
        operation_id: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> List[dict]:
        """Retrieve bars with periodic checkpointing."""
        # Check for existing checkpoint
        checkpoint = await self.checkpoint_manager.load_checkpoint(operation_id)

        if checkpoint:
            logger.info(f"Resuming from checkpoint: {checkpoint.checkpoint_id}")
            current_date = checkpoint.progress["last_date"]
            all_bars = checkpoint.progress["accumulated_bars"]
        else:
            current_date = start_date
            all_bars = []

        # Retrieve data in chunks (1 day at a time)
        while current_date < end_date:
            next_date = min(current_date + timedelta(days=1), end_date)

            # Retrieve bars for this chunk
            bars = await self.api_client.retrieve_bars(
                symbol=symbol,
                start=current_date,
                end=next_date,
                interval=interval
            )

            all_bars.extend(bars)

            # Save checkpoint every 10 chunks (10 days)
            if len(all_bars) % 1000 == 0:
                await self.checkpoint_manager.save_checkpoint(
                    operation_id=operation_id,
                    progress={
                        "last_date": next_date.isoformat(),
                        "accumulated_bars": all_bars,
                        "total_bars": len(all_bars)
                    }
                )

            current_date = next_date

        return all_bars

    def _estimate_duration(self, total_days: int, interval: str) -> int:
        """Estimate operation duration based on parameters."""
        # Rough estimate: 100 bars per second throughput
        bars_per_day = {
            "1min": 390,   # 6.5 hours of market data per day
            "5min": 78,
            "15min": 26,
            "1hour": 6
        }.get(interval, 390)

        total_bars = total_days * bars_per_day
        bars_per_second = 100

        estimated_seconds = (total_bars / bars_per_second) + 60  # Add 1 min overhead

        return int(estimated_seconds)
```

### SignalR Connection with Token Refresh

```typescript
import { HubConnection, HubConnectionBuilder } from '@microsoft/signalr';
import { TokenManager } from './token_manager';

/**
 * SignalR Connection Manager with Long-Running Token Refresh
 */
class SignalRLongConnectionManager {
  private connection: HubConnection;
  private tokenManager: TokenManager;
  private refreshInterval: NodeJS.Timeout | null = null;

  constructor(tokenManager: TokenManager) {
    this.tokenManager = tokenManager;
  }

  /**
   * Start SignalR connection with automatic token refresh
   */
  async start(): Promise<void> {
    // Build connection with accessTokenFactory
    this.connection = new HubConnectionBuilder()
      .withUrl('wss://sim-api.tradestation.com/v3/brokerage/stream', {
        accessTokenFactory: async () => {
          // Always get fresh token (TokenManager handles caching)
          return await this.tokenManager.getToken();
        }
      })
      .withAutomaticReconnect([0, 2000, 10000, 30000, 60000])
      .build();

    // Start connection
    await this.connection.start();
    console.log('SignalR connection established');

    // Schedule periodic token refresh (every 12 hours)
    this.scheduleTokenRefresh();
  }

  /**
   * Schedule periodic token refresh during long-running connection
   */
  private scheduleTokenRefresh(): void {
    const refreshIntervalHours = 12;
    const refreshIntervalMs = refreshIntervalHours * 60 * 60 * 1000;

    this.refreshInterval = setInterval(async () => {
      console.log('Scheduled token refresh for SignalR connection');

      try {
        // Refresh token (TokenManager handles the actual refresh)
        await this.tokenManager.refreshToken();

        console.log('Token refreshed successfully during SignalR connection');

        // Note: SignalR automatically uses new token via accessTokenFactory
        // on next request. No need to disconnect/reconnect.

      } catch (error) {
        console.error('Failed to refresh token during SignalR connection:', error);

        // If refresh fails, attempt to reconnect
        // (this will trigger accessTokenFactory with potentially recovered token)
        await this.handleRefreshFailure();
      }
    }, refreshIntervalMs);

    console.log(`Token refresh scheduled every ${refreshIntervalHours} hours`);
  }

  /**
   * Handle token refresh failure during long-running connection
   */
  private async handleRefreshFailure(): Promise<void> {
    console.warn('Handling token refresh failure - attempting reconnection');

    try {
      // Stop current connection
      await this.connection.stop();

      // Wait 5 seconds
      await new Promise(resolve => setTimeout(resolve, 5000));

      // Attempt to reconnect (will trigger new token via accessTokenFactory)
      await this.connection.start();

      console.log('Reconnected successfully after token refresh failure');

    } catch (error) {
      console.error('Failed to reconnect after token refresh failure:', error);
      // Escalate to system monitoring
      throw error;
    }
  }

  /**
   * Stop connection and cleanup
   */
  async stop(): Promise<void> {
    // Clear refresh interval
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }

    // Stop connection
    if (this.connection) {
      await this.connection.stop();
      console.log('SignalR connection stopped');
    }
  }
}

export default SignalRLongConnectionManager;
```

## Error Handling

### Error Scenarios

**E-001: Token Expires Before Operation Starts**
```
Scenario: Operation estimated 3 hours, token TTL = 1 hour
Response:
  1. Detect insufficient TTL in pre-operation check
  2. Log: "Token TTL insufficient, refreshing before start"
  3. Refresh token
  4. If refresh succeeds: Start operation with new token
  5. If refresh fails: Abort operation, log error, return failure
```

**E-002: Token Expires Mid-Operation**
```
Scenario: Operation running for 2 hours, token expires
Response:
  1. Background monitor detects TTL < 30 minutes
  2. Pause operation (save checkpoint)
  3. Log: "Token expiring during operation, refreshing"
  4. Refresh token
  5. If refresh succeeds: Resume operation from checkpoint
  6. If refresh fails: Abort operation, return failure with checkpoint ID
```

**E-003: Token Refresh Fails During SignalR Connection**
```
Scenario: Scheduled token refresh fails during 24/7 connection
Response:
  1. Log error: "Token refresh failed during SignalR connection"
  2. Attempt to reconnect SignalR (triggers accessTokenFactory)
  3. If reconnect succeeds: Continue with new token
  4. If reconnect fails: Alert monitoring, escalate to admin
```

**E-004: Checkpoint Save Fails**
```
Scenario: Disk full, cannot save checkpoint
Response:
  1. Log error: "Failed to save checkpoint"
  2. Continue operation without checkpoint (at risk)
  3. Alert monitoring system
  4. If operation fails later: Cannot resume, must restart from beginning
```

**E-005: Request Replay Exceeds Max Retries**
```
Scenario: Request fails 3 times during replay
Response:
  1. Log error: "Request replay failed after 3 attempts"
  2. Mark request as permanently failed
  3. Save checkpoint before failure
  4. Return error to operation with checkpoint ID
  5. Allow manual resume from checkpoint
```

## Validation Criteria

### Functional Validation

**FV-1: Pre-Operation Token Check Works**
```
Test: Start operation with token expiring in 1 hour, operation estimated 3 hours
Expected: Token refreshed before operation starts
Validation: Check logs for "Token TTL insufficient, refreshing before start"
```

**FV-2: Mid-Operation Token Refresh Works**
```
Test: Run 3-hour operation, monitor token refresh
Expected: Token refreshed when TTL drops below 30 minutes
Validation: Check logs for "Token expiring during operation, refreshing"
```

**FV-3: Operation Resumes from Checkpoint**
```
Test: Start operation, save checkpoint, stop application, restart, resume
Expected: Operation resumes from checkpoint, completes successfully
Validation: Check final result includes all data from start to finish
```

**FV-4: SignalR Connection Survives Token Refresh**
```
Test: Start SignalR connection, trigger scheduled refresh after 12 hours
Expected: Connection remains active, no disconnection
Validation: Check messages continue to arrive before and after refresh
```

**FV-5: Request Replay Succeeds After Token Refresh**
```
Test: Send request, token expires, refresh token, replay request
Expected: Request replayed successfully with new token
Validation: Check request completes, response received
```

## References

### Related Specifications
- **TOKEN_REFRESH_STRATEGY_SPEC.md**: Core token refresh logic
- **SIGNALR_JWT_FIX_SPEC.md**: SignalR token handling
- **TOKEN_ROTATION_SPEC.md**: Token rotation during operations

### Error Analysis References
- **ERRORS_AND_WARNINGS_CONSOLIDATED.md**:
  - Line 205-213: GAP-API-SCENARIO-005 (Token Expiration During Long Operation)

### Implementation Patterns
- **Circuit Breaker Pattern**: Handle repeated refresh failures
- **Retry with Exponential Backoff**: Request replay strategy
- **Checkpoint/Resume Pattern**: Fault-tolerant long operations

---

**Document Status:** DRAFT v1.0
**Last Updated:** 2025-10-22
**Next Review:** After implementation phase 1
**Approval Required:** Architecture Team, Security Team
