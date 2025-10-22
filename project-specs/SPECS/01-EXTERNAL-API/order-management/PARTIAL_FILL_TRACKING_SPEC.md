# Partial Fill Tracking Specification

**doc_id:** ORDER-002
**version:** 1.0
**status:** DRAFT
**addresses:** GAP-API-SCENARIO-002 (HIGH) from ERRORS_AND_WARNINGS_CONSOLIDATED.md
**created:** 2025-10-22
**category:** Order Management / Real-Time Tracking

---

## Overview

This specification defines the real-time partial fill tracking system for orders. Order responses show `fillVolume` and `filledPrice`, but the system must track partial fills as they occur, calculate weighted average fill prices, determine when orders are complete, and handle fill timeouts appropriately.

**Problem Statement:**
- How to track partial fills in real-time?
- When is an order considered complete?
- How to handle partial fill timeout?
- How to calculate accurate weighted average fill price?
- What happens if fills arrive out of order?

**Solution:**
Real-time fill tracking via SignalR events with completion criteria, weighted average price calculation, fill history persistence, and configurable timeout handling.

---

## Requirements

### Functional Requirements

**FR-001: Real-Time Fill Event Processing**
- MUST subscribe to order fill events via SignalR
- MUST process fill events in real-time (<100ms latency)
- MUST handle out-of-order fill events
- MUST deduplicate fill events (handle replays)
- MUST emit internal events on each fill update

**FR-002: Partial Fill State Tracking**
- MUST track cumulative fill volume
- MUST track remaining unfilled quantity
- MUST track number of individual fills
- MUST maintain fill history with timestamps
- MUST calculate fill completion percentage

**FR-003: Weighted Average Fill Price Calculation**
- MUST calculate weighted average price across all fills
- MUST handle multiple fill prices for same order
- MUST update average as new fills arrive
- MUST round to appropriate precision for symbol
- MUST validate price reasonableness

**FR-004: Order Completion Criteria**
- MUST detect when order fully filled (fillVolume == quantity)
- MUST detect timeout for partial fills (default 60s)
- MUST detect explicit cancellation
- MUST detect rejection after partial fill
- MUST mark order with completion reason

**FR-005: Fill History Persistence**
- MUST store each individual fill with details
- MUST persist fill timestamps
- MUST store fill price and volume
- MUST link fills to parent order
- MUST enable fill audit trail

**FR-006: Timeout Handling**
- MUST detect when fills stop arriving
- MUST apply configurable timeout (default 60s)
- MUST mark partially filled orders as timed out
- MUST update positions based on actual fills
- MUST emit timeout event for monitoring

### Non-Functional Requirements

**NFR-001: Performance**
- Fill event processing MUST be < 100ms
- Weighted average calculation MUST be < 1ms
- Timeout detection MUST occur within 1s of expiry
- State updates MUST be atomic
- Database writes MUST be async (non-blocking)

**NFR-002: Reliability**
- Zero fill events lost (guaranteed delivery)
- Exactly-once fill processing (deduplication)
- Consistent state during concurrent fills
- Graceful handling of SignalR reconnection
- State recovery after restart

**NFR-003: Observability**
- MUST log all fill events
- MUST track fill latency metrics
- MUST monitor timeout frequency
- MUST alert on unusual fill patterns
- MUST provide fill history query API

---

## Fill Tracking State Machine

```
ORDER_SUBMITTED
    |
    v
PENDING_FILL
    |
    +---> [First Fill Event] ---> PARTIALLY_FILLED
    |                                   |
    |                                   +---> [Subsequent Fill] ---> PARTIALLY_FILLED (loop)
    |                                   |
    |                                   +---> [Fill Complete] ---> FULLY_FILLED
    |                                   |
    |                                   +---> [Timeout] ---> PARTIAL_FILL_TIMEOUT
    |                                   |
    |                                   +---> [Cancelled] ---> CANCELLED_PARTIALLY_FILLED
    |                                   |
    |                                   +---> [Rejected] ---> REJECTED_AFTER_PARTIAL_FILL
    |
    +---> [Full Fill Event] ---> FULLY_FILLED
    |
    +---> [Timeout (No Fills)] ---> UNFILLED_TIMEOUT
    |
    +---> [Cancelled] ---> CANCELLED
    |
    +---> [Rejected] ---> REJECTED

FULLY_FILLED
    |
    +---> UPDATE_POSITION
    |
    +---> EMIT_COMPLETION_EVENT
    |
    +---> TRACKING_COMPLETE

PARTIAL_FILL_TIMEOUT
    |
    +---> UPDATE_POSITION (partial quantity)
    |
    +---> EMIT_TIMEOUT_EVENT
    |
    +---> REQUIRE_MANUAL_RESOLUTION
```

### State Descriptions

1. **PENDING_FILL**: Order submitted, waiting for first fill
2. **PARTIALLY_FILLED**: Order has received partial fills, not yet complete
3. **FULLY_FILLED**: Order completely filled (fillVolume == quantity)
4. **PARTIAL_FILL_TIMEOUT**: Fills stopped, timeout reached with remaining quantity
5. **CANCELLED_PARTIALLY_FILLED**: Order cancelled by user/system after partial fills
6. **REJECTED_AFTER_PARTIAL_FILL**: Order rejected after receiving partial fills
7. **UNFILLED_TIMEOUT**: Timeout reached with zero fills
8. **TRACKING_COMPLETE**: Fill tracking finished, state finalized

---

## Order Completion Criteria

### Criterion 1: Fully Filled

**Condition:**
```python
fillVolume >= quantity - quantity_tolerance
```

**Details:**
- `fillVolume`: Cumulative filled quantity from all fill events
- `quantity`: Original order quantity
- `quantity_tolerance`: 0.00000001 (floating point tolerance)

**Example:**
```yaml
Order:
  orderId: "ORD-123456"
  symbol: "AAPL"
  quantity: 100.0
  fillVolume: 100.0
  status: FULLY_FILLED

Completion:
  criteria: "fully_filled"
  timestamp: 1729636825123
  totalFills: 3
  averagePrice: 178.45
```

**Actions:**
- Mark order status as FULLY_FILLED
- Stop timeout timer
- Update position with total filled quantity
- Calculate final weighted average price
- Emit order completion event
- Store final fill record

---

### Criterion 2: Timeout Reached

**Condition:**
```python
current_time - last_fill_timestamp > fill_timeout_ms
AND fillVolume < quantity
```

**Details:**
- `fill_timeout_ms`: Configurable timeout (default 60000ms = 60s)
- `last_fill_timestamp`: Timestamp of most recent fill event
- Timer starts after first fill or order submission

**Example:**
```yaml
Order:
  orderId: "ORD-123456"
  symbol: "AAPL"
  quantity: 100.0
  fillVolume: 75.0          # Partially filled
  status: PARTIAL_FILL_TIMEOUT

Completion:
  criteria: "timeout"
  timestamp: 1729636885123
  totalFills: 2
  averagePrice: 178.42
  unfilledQuantity: 25.0
  timeoutDuration: 60000
```

**Actions:**
- Mark order status as PARTIAL_FILL_TIMEOUT
- Stop timeout timer
- Update position with actual filled quantity
- Calculate weighted average price for fills received
- Emit timeout event with unfilled quantity
- Store timeout record for analysis
- Alert monitoring system

---

### Criterion 3: Cancelled by User/System

**Condition:**
```python
order_cancelled_event_received
AND fillVolume < quantity
```

**Details:**
- Cancellation can be user-initiated or system-initiated (e.g., risk rule)
- May occur after partial fills received
- Must account for fills up to cancellation time

**Example:**
```yaml
Order:
  orderId: "ORD-123456"
  symbol: "AAPL"
  quantity: 100.0
  fillVolume: 50.0          # Partially filled before cancel
  status: CANCELLED_PARTIALLY_FILLED

Completion:
  criteria: "cancelled"
  timestamp: 1729636830000
  totalFills: 1
  averagePrice: 178.40
  unfilledQuantity: 50.0
  cancelledBy: "user"
```

**Actions:**
- Mark order status as CANCELLED_PARTIALLY_FILLED
- Stop timeout timer
- Update position with fills received before cancellation
- Calculate weighted average price for fills received
- Emit cancellation event
- Do NOT attempt to fill remaining quantity

---

### Criterion 4: Rejected After Partial Fill

**Condition:**
```python
order_rejection_event_received
AND fillVolume > 0
```

**Details:**
- Rare scenario: broker rejects order after partial fills
- Can occur due to margin requirements, market conditions, or errors
- Must honor fills already executed

**Example:**
```yaml
Order:
  orderId: "ORD-123456"
  symbol: "AAPL"
  quantity: 100.0
  fillVolume: 25.0          # Partial fill before rejection
  status: REJECTED_AFTER_PARTIAL_FILL

Completion:
  criteria: "rejected"
  timestamp: 1729636828500
  totalFills: 1
  averagePrice: 178.50
  unfilledQuantity: 75.0
  rejectionReason: "insufficient_margin"
```

**Actions:**
- Mark order status as REJECTED_AFTER_PARTIAL_FILL
- Stop timeout timer
- Update position with fills received before rejection
- Log rejection reason
- Emit rejection event with partial fill details
- Alert monitoring system (unusual scenario)

---

## Weighted Average Fill Price Calculation

### Algorithm

```python
def calculate_weighted_average_price(fills: List[Fill]) -> float:
    """
    Calculate weighted average fill price across multiple fills.

    Formula:
    weighted_avg = sum(fill_price * fill_volume) / sum(fill_volume)
    """
    if not fills:
        return 0.0

    total_value = 0.0
    total_volume = 0.0

    for fill in fills:
        total_value += fill.price * fill.volume
        total_volume += fill.volume

    if total_volume == 0:
        return 0.0

    weighted_avg = total_value / total_volume

    # Round to appropriate precision (e.g., 2 decimals for stocks)
    return round(weighted_avg, get_price_precision(symbol))
```

### Example Calculation

```yaml
Order:
  orderId: "ORD-123456"
  symbol: "AAPL"
  quantity: 100.0

Fills:
  - fill_1:
      timestamp: 1729636823000
      price: 178.40
      volume: 30.0

  - fill_2:
      timestamp: 1729636823500
      price: 178.45
      volume: 50.0

  - fill_3:
      timestamp: 1729636824000
      price: 178.50
      volume: 20.0

Calculation:
  fill_1_value: 178.40 * 30.0 = 5352.00
  fill_2_value: 178.45 * 50.0 = 8922.50
  fill_3_value: 178.50 * 20.0 = 3570.00

  total_value: 5352.00 + 8922.50 + 3570.00 = 17844.50
  total_volume: 30.0 + 50.0 + 20.0 = 100.0

  weighted_avg: 17844.50 / 100.0 = 178.445
  rounded: 178.45 (2 decimal precision)

Result:
  averageFillPrice: 178.45
  totalFills: 3
  fillVolume: 100.0
```

### Incremental Update (Optimization)

For real-time updates without recalculating from history:

```python
def update_weighted_average_incremental(
    current_avg: float,
    current_volume: float,
    new_fill_price: float,
    new_fill_volume: float
) -> float:
    """
    Update weighted average with new fill without full recalculation.
    """
    current_total_value = current_avg * current_volume
    new_total_value = current_total_value + (new_fill_price * new_fill_volume)
    new_total_volume = current_volume + new_fill_volume

    new_avg = new_total_value / new_total_volume
    return round(new_avg, get_price_precision(symbol))
```

**Benefits:**
- O(1) time complexity vs O(n)
- Suitable for real-time SignalR event processing
- Maintains accuracy with proper rounding

---

## SignalR Fill Event Handling

### Event Structure

```yaml
SignalREvent:
  eventType: "order_fill"
  payload:
    orderId: "ORD-123456"
    accountId: "ACC123456"
    symbol: "AAPL"
    side: "BUY"
    fillId: "FILL-789012"         # Unique fill identifier
    fillPrice: 178.45             # This fill's execution price
    fillVolume: 50.0              # This fill's quantity
    totalFillVolume: 75.0         # Cumulative filled quantity
    remainingVolume: 25.0         # Unfilled quantity
    timestamp: 1729636823500      # Fill execution timestamp
    orderStatus: "PARTIALLY_FILLED" | "FILLED"
```

### Event Processing Flow

```python
async def handle_fill_event(event: SignalREvent):
    """
    Process incoming fill event from SignalR.
    """
    # 1. Validate event structure
    validate_fill_event(event)

    # 2. Check for duplicate (idempotency)
    if is_duplicate_fill(event.fillId):
        log_warning(f"Duplicate fill event: {event.fillId}")
        return

    # 3. Retrieve order state
    order = get_order(event.orderId)

    # 4. Apply fill to order
    order.add_fill(Fill(
        fillId=event.fillId,
        price=event.fillPrice,
        volume=event.fillVolume,
        timestamp=event.timestamp
    ))

    # 5. Update weighted average price
    order.averagePrice = calculate_weighted_average_price(order.fills)

    # 6. Update fill volume
    order.fillVolume = event.totalFillVolume
    order.remainingVolume = event.remainingVolume

    # 7. Check completion criteria
    if order.fillVolume >= order.quantity - QUANTITY_TOLERANCE:
        mark_order_complete(order, "fully_filled")
    else:
        # Reset timeout timer (fill activity detected)
        reset_fill_timeout_timer(order.orderId)

    # 8. Update position
    update_position_with_fill(order, event.fillVolume - order.previousFillVolume)

    # 9. Persist fill to database (async)
    await store_fill_record(event)

    # 10. Emit internal event
    emit_fill_event(order, event)

    # 11. Log fill for audit
    log_fill(f"Order {order.orderId}: Filled {event.fillVolume} @ {event.fillPrice}")
```

### Deduplication Strategy

```python
class FillDeduplicator:
    """
    Prevent duplicate fill processing during reconnections.
    """
    def __init__(self):
        self.processed_fills: Set[str] = set()  # fillId set
        self.cache_ttl = 3600000  # 1 hour
        self.cleanup_interval = 300000  # 5 minutes

    def is_duplicate(self, fill_id: str) -> bool:
        """Check if fill already processed."""
        return fill_id in self.processed_fills

    def mark_processed(self, fill_id: str):
        """Mark fill as processed."""
        self.processed_fills.add(fill_id)
        # Schedule cleanup after TTL
        schedule_cleanup(fill_id, self.cache_ttl)

    def cleanup_expired(self):
        """Remove old fill IDs from cache."""
        # Called every 5 minutes
        current_time = get_current_time()
        expired = [fid for fid in self.processed_fills
                   if get_fill_timestamp(fid) < current_time - self.cache_ttl]
        for fid in expired:
            self.processed_fills.remove(fid)
```

### Out-of-Order Event Handling

**Scenario:** Fills arrive out of chronological order due to network conditions.

```python
def handle_out_of_order_fills(order: Order, new_fill: Fill):
    """
    Handle fills that arrive out of chronological order.
    """
    # 1. Insert fill in correct chronological position
    order.fills = sorted(order.fills + [new_fill], key=lambda f: f.timestamp)

    # 2. Recalculate weighted average (still accurate regardless of order)
    order.averagePrice = calculate_weighted_average_price(order.fills)

    # 3. Verify totalFillVolume matches sum of individual fills
    calculated_total = sum(f.volume for f in order.fills)
    if abs(calculated_total - order.fillVolume) > QUANTITY_TOLERANCE:
        log_error(f"Fill volume mismatch: calculated={calculated_total}, reported={order.fillVolume}")
        # Use SignalR event totalFillVolume as source of truth

    # 4. No action required for position (already updated on first receipt)
    # Position updates are idempotent by fill ID
```

---

## Fill History Persistence

### Database Schema

```sql
CREATE TABLE order_fills (
    fill_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,              -- BUY or SELL
    fill_price REAL NOT NULL,
    fill_volume REAL NOT NULL,
    cumulative_volume REAL NOT NULL,  -- Total filled up to this point
    remaining_volume REAL NOT NULL,
    fill_timestamp INTEGER NOT NULL,  -- Milliseconds since epoch
    event_received_timestamp INTEGER, -- When we received SignalR event
    processing_latency_ms INTEGER,    -- Event latency metric
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE INDEX idx_order_fills_order_id ON order_fills(order_id);
CREATE INDEX idx_order_fills_timestamp ON order_fills(fill_timestamp);
CREATE INDEX idx_order_fills_symbol_time ON order_fills(symbol, fill_timestamp);
```

### Fill Record Structure

```yaml
FillRecord:
  fillId: "FILL-789012"
  orderId: "ORD-123456"
  accountId: "ACC123456"
  symbol: "AAPL"
  side: "BUY"
  fillPrice: 178.45
  fillVolume: 50.0
  cumulativeVolume: 75.0
  remainingVolume: 25.0
  fillTimestamp: 1729636823500
  eventReceivedTimestamp: 1729636823580
  processingLatencyMs: 80
  metadata:
    eventSequence: 2              # Which fill in order sequence
    priceDeviation: 0.05          # Deviation from limit price (if applicable)
    marketCondition: "normal"
```

### Audit Trail Query

```sql
-- Retrieve complete fill history for an order
SELECT
    fill_id,
    fill_price,
    fill_volume,
    cumulative_volume,
    remaining_volume,
    fill_timestamp,
    processing_latency_ms
FROM order_fills
WHERE order_id = 'ORD-123456'
ORDER BY fill_timestamp ASC;

-- Calculate weighted average from history
SELECT
    order_id,
    SUM(fill_price * fill_volume) / SUM(fill_volume) AS weighted_avg_price,
    SUM(fill_volume) AS total_filled,
    COUNT(*) AS num_fills,
    MAX(fill_timestamp) - MIN(fill_timestamp) AS fill_duration_ms
FROM order_fills
WHERE order_id = 'ORD-123456'
GROUP BY order_id;
```

---

## Timeout Handling Logic

### Timeout Timer Management

```python
class FillTimeoutManager:
    """
    Manage fill timeout timers for active orders.
    """
    def __init__(self):
        self.timers: Dict[str, Timer] = {}
        self.default_timeout_ms = 60000  # 60 seconds

    def start_timer(self, order_id: str, timeout_ms: int = None):
        """Start timeout timer for an order."""
        timeout = timeout_ms or self.default_timeout_ms

        timer = Timer(
            timeout_ms=timeout,
            callback=lambda: self.handle_timeout(order_id)
        )
        timer.start()
        self.timers[order_id] = timer

    def reset_timer(self, order_id: str):
        """Reset timer when fill activity detected."""
        if order_id in self.timers:
            self.timers[order_id].cancel()
        self.start_timer(order_id)

    def cancel_timer(self, order_id: str):
        """Cancel timer when order completes."""
        if order_id in self.timers:
            self.timers[order_id].cancel()
            del self.timers[order_id]

    def handle_timeout(self, order_id: str):
        """Handle fill timeout expiration."""
        order = get_order(order_id)

        if order.fillVolume < order.quantity:
            # Partial fill timeout
            mark_order_complete(order, "timeout")
            update_position_final(order, order.fillVolume)
            emit_timeout_event(order)
            log_timeout(order)

        # Remove timer
        del self.timers[order_id]
```

### Timeout Configuration

```yaml
partialFillTracking:
  timeout:
    enabled: true
    defaultTimeoutMs: 60000        # 60 seconds
    timeoutBySymbolType:
      stocks: 60000                # 60 seconds for stocks
      forex: 30000                 # 30 seconds for forex (faster fills)
      crypto: 120000               # 2 minutes for crypto (slower fills)
    timeoutByOrderType:
      MARKET: 30000                # Market orders fill faster
      LIMIT: 120000                # Limit orders may take longer
      STOP: 60000
      STOP_LIMIT: 120000

  behavior:
    startTimerAfter: "first_fill"  # "order_submit" or "first_fill"
    resetOnFill: true               # Reset timer on each new fill
    alertOnTimeout: true
    requireManualResolution: true   # Require manual review of timeouts
```

### Timeout Scenarios

**Scenario 1: Partial Fill Then Timeout**
```yaml
Timeline:
  T+0ms:   Order submitted (quantity: 100)
  T+1000ms: First fill received (volume: 50)
  T+2000ms: Second fill received (volume: 25)
  T+62000ms: Timeout (no fills for 60s)

Outcome:
  status: PARTIAL_FILL_TIMEOUT
  fillVolume: 75.0
  remainingVolume: 25.0
  averagePrice: 178.43
  action: Update position with 75 shares, alert operator
```

**Scenario 2: No Fills Then Timeout**
```yaml
Timeline:
  T+0ms:   Order submitted (quantity: 100)
  T+60000ms: Timeout (no fills received)

Outcome:
  status: UNFILLED_TIMEOUT
  fillVolume: 0.0
  remainingVolume: 100.0
  action: Order never executed, alert operator, investigate
```

**Scenario 3: Fill Complete Before Timeout**
```yaml
Timeline:
  T+0ms:   Order submitted (quantity: 100)
  T+1000ms: First fill received (volume: 60)
  T+2500ms: Second fill received (volume: 40)
  T+3000ms: Order complete (fillVolume: 100)

Outcome:
  status: FULLY_FILLED
  fillVolume: 100.0
  averagePrice: 178.45
  action: Timer cancelled, position updated, normal completion
```

---

## Configuration Schema

```yaml
partialFillTracking:
  realtime:
    enabled: true
    signalrEventType: "order_fill"
    processingTimeout: 100         # Max processing time per event (ms)
    maxConcurrentProcessing: 10    # Max fills processed simultaneously

  completion:
    quantityTolerance: 0.00000001  # Floating point comparison tolerance
    markCompleteOn:
      - "fully_filled"
      - "timeout"
      - "cancelled"
      - "rejected"

  pricing:
    calculationMethod: "weighted_average"
    precisionByAssetType:
      stocks: 2                    # 2 decimal places
      forex: 5                     # 5 decimal places
      crypto: 8                    # 8 decimal places
    priceReasonablenessCheck: true
    maxPriceDeviationPercent: 5.0  # Alert if fill price > 5% from expected

  history:
    persistFills: true
    asyncWrites: true              # Non-blocking database writes
    retentionDays: 90              # Keep fill history for 90 days
    compressOldRecords: true       # Compress records > 30 days old

  timeout:
    # See timeout configuration section above

  deduplication:
    enabled: true
    cacheType: "in_memory"         # "in_memory" or "redis"
    cacheTTL: 3600000              # 1 hour
    cleanupInterval: 300000        # 5 minutes

  monitoring:
    trackFillLatency: true
    trackTimeoutFrequency: true
    alertOnUnusualFillPatterns: true
    alertOnHighTimeoutRate: true   # Alert if timeout rate > 5%
```

---

## Data Structures

### Fill

```yaml
Fill:
  fillId: string                   # Unique fill identifier
  price: float                     # Execution price for this fill
  volume: float                    # Quantity filled in this event
  timestamp: integer               # Milliseconds since epoch
  metadata:
    venue: string | null           # Exchange/venue (if available)
    liquidity: "maker" | "taker" | null
    commission: float | null
```

### PartialFillTracker

```yaml
PartialFillTracker:
  orderId: string
  fills: List[Fill]
  state:
    totalFills: integer            # Number of fill events
    fillVolume: float              # Cumulative filled quantity
    remainingVolume: float         # Unfilled quantity
    averagePrice: float            # Weighted average fill price
    completionPercent: float       # (fillVolume / quantity) * 100
  timing:
    firstFillTimestamp: integer | null
    lastFillTimestamp: integer | null
    timeoutDeadline: integer | null
  status: "pending" | "partially_filled" | "fully_filled" | "timed_out" | "cancelled"
  completionReason: "fully_filled" | "timeout" | "cancelled" | "rejected" | null
```

### FillEvent (Internal)

```yaml
FillEvent:
  eventType: "fill_received" | "order_complete" | "fill_timeout"
  orderId: string
  fill: Fill | null              # Null for timeout events
  cumulativeState:
    fillVolume: float
    remainingVolume: float
    averagePrice: float
    completionPercent: float
  timestamp: integer
```

---

## Error Scenarios & Recovery

### Scenario 1: SignalR Disconnection During Fills

**Situation:**
- Order partially filled
- SignalR connection drops
- Missing fill events during disconnection

**Detection:**
```python
@signalr_connection.on_reconnected
async def on_reconnected():
    # Connection restored
    await reconcile_fill_state_after_reconnection()
```

**Recovery:**
1. Query order status via REST API after reconnection
2. Retrieve complete fill history from API
3. Compare with internal fill records
4. Apply any missed fills
5. Recalculate weighted average price
6. Resume real-time tracking

**Expected Outcome:**
- No missed fills
- Accurate fill state restored
- Position synchronized correctly

---

### Scenario 2: Duplicate Fill Events

**Situation:**
- SignalR replay sends duplicate fill events
- Fill already processed

**Detection:**
```python
if is_duplicate_fill(event.fillId):
    log_warning(f"Duplicate fill: {event.fillId}")
    return  # Ignore duplicate
```

**Recovery:**
1. Check fillId against processed set
2. If duplicate → Ignore event
3. Log duplicate for monitoring
4. No state changes applied

**Expected Outcome:**
- Fill processed exactly once
- No position double-counting
- Accurate tracking maintained

---

### Scenario 3: Out-of-Order Fill Events

**Situation:**
- Fill #3 arrives before Fill #2
- Chronological order disrupted

**Detection:**
```python
if new_fill.timestamp < order.lastFillTimestamp:
    log_info("Out-of-order fill detected")
```

**Recovery:**
1. Insert fill into correct chronological position
2. Recalculate weighted average (order-independent calculation)
3. Verify cumulative fill volume consistency
4. Continue normal tracking

**Expected Outcome:**
- Fills sorted by timestamp in history
- Weighted average still accurate (order doesn't matter)
- Position already updated correctly (by fill ID idempotency)

---

### Scenario 4: Fill Exceeds Order Quantity

**Situation:**
- Cumulative fills exceed original order quantity
- Data inconsistency or API error

**Detection:**
```python
if order.fillVolume > order.quantity + QUANTITY_TOLERANCE:
    log_error(f"Fill volume {order.fillVolume} exceeds quantity {order.quantity}")
```

**Recovery:**
1. Log critical error
2. Alert monitoring system
3. Snapshot order and fill state for investigation
4. Use API fillVolume as source of truth
5. Require manual review before proceeding

**Expected Outcome:**
- Error detected and logged
- Manual review triggered
- Position not corrupted
- Investigate root cause (API bug, data error)

---

### Scenario 5: Timeout with Zero Fills

**Situation:**
- Order submitted successfully
- Timeout reached with no fills
- Order status unclear

**Detection:**
```python
if order.fillVolume == 0 and timeout_reached:
    # No fills received
    mark_order_complete(order, "unfilled_timeout")
```

**Recovery:**
1. Query order status via REST API
2. Verify order truly unfilled or check for missed events
3. If confirmed unfilled → Mark as UNFILLED_TIMEOUT
4. Alert operator (unusual scenario)
5. Investigate why order never filled

**Expected Outcome:**
- Order status clarified
- No position update (no fills)
- Investigation initiated

---

## Implementation Checklist

### Real-Time Processing
- [ ] Subscribe to SignalR order fill events
- [ ] Implement fill event handler (<100ms processing)
- [ ] Add fill deduplication by fillId
- [ ] Handle out-of-order fill events
- [ ] Emit internal fill events

### State Tracking
- [ ] Track cumulative fill volume
- [ ] Track remaining unfilled quantity
- [ ] Maintain fill history list
- [ ] Calculate completion percentage
- [ ] Implement state synchronization

### Weighted Average Calculation
- [ ] Implement full recalculation algorithm
- [ ] Implement incremental update optimization
- [ ] Add precision rounding by symbol type
- [ ] Validate price reasonableness
- [ ] Handle edge cases (zero volume, single fill)

### Completion Detection
- [ ] Detect fully filled condition
- [ ] Detect timeout condition
- [ ] Detect cancellation after partial fill
- [ ] Detect rejection after partial fill
- [ ] Mark completion reason

### Timeout Management
- [ ] Implement fill timeout timer
- [ ] Reset timer on fill activity
- [ ] Cancel timer on completion
- [ ] Configure timeout by symbol/order type
- [ ] Handle timeout expiration

### Fill History
- [ ] Design database schema
- [ ] Implement async fill persistence
- [ ] Create fill audit queries
- [ ] Add fill history retention policy
- [ ] Implement history compression

### Error Handling
- [ ] Handle SignalR reconnection
- [ ] Implement state reconciliation
- [ ] Handle duplicate events
- [ ] Handle out-of-order events
- [ ] Detect fill volume inconsistencies

### Configuration & Testing
- [ ] Load configuration from YAML
- [ ] Validate configuration on startup
- [ ] Write unit tests for calculations
- [ ] Write integration tests for SignalR scenarios
- [ ] Test timeout handling
- [ ] Test concurrent fill processing

---

## Validation Criteria

### Accurate Weighted Average Calculation
**Target:** 100% accuracy with proper rounding
- Weighted average matches manual calculation
- Handles multiple fills correctly
- Incremental updates match full recalculation
- Precision appropriate for symbol type

**Validation Method:**
- Test with 1000 multi-fill orders
- Compare against reference implementation
- Verify incremental == full calculation
- Test edge cases (1 fill, 100 fills)

### Fast Fill Processing
**Target:** <100ms average processing latency
- Fill event processing < 100ms p50
- Fill event processing < 200ms p95
- No blocking operations in event handler
- Async database writes

**Validation Method:**
- Measure processing time for 10,000 fill events
- Calculate p50, p95, p99 latencies
- Profile slow operations
- Optimize bottlenecks

### Zero Missed Fills
**Target:** 100% fill capture rate
- All fill events processed
- SignalR reconnection recovers missed fills
- State reconciliation after disconnection
- Duplicate detection prevents double-counting

**Validation Method:**
- Simulate SignalR disconnections during fills
- Verify fill count matches API history
- Test rapid fill sequences
- Verify no duplicate processing

### Correct Timeout Detection
**Target:** Timeout detection within 1s of expiry
- Timeout fires when fills stop
- Timeout cancelled on order completion
- Timeout reset on new fill activity
- Partial fills correctly marked

**Validation Method:**
- Test timeout with various fill patterns
- Measure timeout detection accuracy
- Test timer cancellation on completion
- Test timer reset on fill activity

---

## Metrics & Monitoring

```yaml
Metrics:
  - name: "order_fill_events_total"
    type: counter
    labels: [symbol, order_type]
    description: "Total fill events processed"

  - name: "order_fill_processing_duration_ms"
    type: histogram
    buckets: [10, 50, 100, 200, 500, 1000]
    description: "Fill event processing latency"

  - name: "order_partial_fill_timeout_total"
    type: counter
    labels: [symbol, timeout_reason]
    description: "Number of partial fill timeouts"

  - name: "order_weighted_avg_calculation_duration_ms"
    type: histogram
    buckets: [1, 5, 10, 50]
    description: "Weighted average calculation time"

  - name: "order_fill_deduplication_hits"
    type: counter
    description: "Number of duplicate fill events detected"

  - name: "order_out_of_order_fills"
    type: counter
    description: "Number of out-of-order fill events"

  - name: "order_completion_by_reason"
    type: counter
    labels: [reason]
    description: "Order completions by reason (fully_filled, timeout, cancelled)"

Alerts:
  - name: "HighFillProcessingLatency"
    condition: "histogram_quantile(0.95, order_fill_processing_duration_ms) > 200"
    severity: "MEDIUM"
    message: "95th percentile fill processing latency > 200ms"

  - name: "FrequentPartialFillTimeouts"
    condition: "rate(order_partial_fill_timeout_total[5m]) > 5"
    severity: "HIGH"
    message: "More than 5 partial fill timeouts in 5 minutes"

  - name: "HighFillDeduplicationRate"
    condition: "rate(order_fill_deduplication_hits[5m]) / rate(order_fill_events_total[5m]) > 0.1"
    severity: "MEDIUM"
    message: "More than 10% of fill events are duplicates"
```

---

## References

1. **ERRORS_AND_WARNINGS_CONSOLIDATED.md**
   - GAP-API-SCENARIO-002: Partial order fills (HIGH)
   - Lines 276-286

2. **Related Specifications**
   - ORDER_STATUS_VERIFICATION_SPEC.md (Network failure handling)
   - ORDER_LIFECYCLE_SPEC.md (Complete state machine)
   - CONCURRENCY_HANDLING_SPEC.md (Concurrent fill processing)

3. **API Documentation**
   - SignalR Events: `order_fill` event structure
   - `/api/Order/getOrder` - Order status with fill details
   - `/api/Order/listOrders` - Fill history retrieval

---

**Document Status:** DRAFT - Ready for Technical Review
**Next Steps:**
1. Technical review by architecture team
2. Performance validation with load testing
3. Integration with SignalR event system
4. Database schema review
5. Update to APPROVED status after review
