# SignalR State Reconciliation Specification

**doc_id:** SIGNALR-003
**version:** 1.0
**status:** DRAFT
**addresses:** GAP-API-SCENARIO-003 (CRITICAL) from ERRORS_AND_WARNINGS_CONSOLIDATED.md
**created:** 2025-10-22
**last_updated:** 2025-10-22

---

## Overview

This specification defines the state reconciliation strategy for synchronizing data after SignalR reconnection, including gap detection, missed event replay, REST API synchronization, and data consistency verification. It addresses GAP-API-SCENARIO-003 which identified the risk of missing critical updates during disconnection.

**Critical Gap Addressed:**
> "During reconnection: Are missed events replayed? How to detect gaps in event stream? Should REST API be polled after reconnect? Could miss critical position/order updates during disconnection."

**Design Philosophy:**
- Assume all real-time events during disconnection are lost (SignalR does NOT replay missed events)
- After reconnection, immediately sync full state from REST API
- Detect gaps by comparing REST state with local cached state
- Reconcile differences by updating local state to match REST API truth
- Notify user if critical changes occurred during disconnection

---

## Requirements

### Functional Requirements

**FR-1: Automatic Reconciliation Trigger**
- State reconciliation MUST be triggered immediately after successful SignalR reconnection
- Reconciliation MUST complete before resuming normal SignalR event processing
- Reconciliation MUST be atomic (all-or-nothing update)

**FR-2: Full State Synchronization**
- MUST fetch complete current state from REST API:
  - All open positions: `GET /api/Positions/getAllPositions`
  - All active orders: `GET /api/Orders/getAllOrders`
  - Current quotes for all active symbols: `GET /api/Quotes/getQuote` (for each symbol)
  - Account balance: `GET /api/Account/getBalance`
- MUST use single batch of requests to minimize latency
- MUST handle partial failures (some endpoints succeed, others fail)

**FR-3: Gap Detection**
- MUST compare REST API state with local cached state
- MUST detect:
  - New positions opened during disconnection
  - Positions closed during disconnection
  - Position quantity/PnL changes
  - New orders placed during disconnection (e.g., by mobile app)
  - Orders filled during disconnection
  - Orders cancelled during disconnection
  - Price changes for tracked symbols
  - Balance changes
- MUST identify the type of each gap (new, modified, deleted)

**FR-4: State Reconciliation**
- MUST update local state to match REST API state (REST API is source of truth)
- MUST emit synthetic events for missed changes to trigger downstream processing:
  - Emit `PositionUpdate` events for position changes
  - Emit `OrderUpdate` events for order changes
  - Emit `TradeExecution` events for filled orders
  - Emit `QuoteUpdate` events for price changes
- MUST NOT re-trigger risk rules that already executed server-side
- MUST trigger risk rules that depend on current state (e.g., daily loss limits)

**FR-5: User Notification**
- MUST notify user of critical changes that occurred during disconnection:
  - Positions closed (especially if by stop-loss or risk rule)
  - Orders filled (partially or fully)
  - Large PnL changes (>$100 or >5% of account)
  - New positions opened (if not by this client instance)
- Notification MUST include summary of changes
- User MUST be able to view detailed reconciliation report

**FR-6: Reconciliation Failure Handling**
- If REST API is unavailable during reconciliation, MUST retry with exponential backoff
- If reconciliation fails after max retries, MUST:
  - Show critical error to user
  - Remain in "degraded mode" with warning banner
  - Allow manual retry
  - Disable order placement until reconciliation succeeds
- MUST NOT assume local state is correct if reconciliation fails

### Non-Functional Requirements

**NFR-1: Performance**
- Reconciliation MUST complete within 5 seconds for typical accounts (<50 positions/orders)
- Reconciliation MUST complete within 15 seconds for large accounts (<200 positions/orders)
- Reconciliation MUST NOT block UI responsiveness

**NFR-2: Data Consistency**
- After successful reconciliation, local state MUST be 100% consistent with REST API state
- No stale data MUST remain in local cache after reconciliation
- Event sequence numbers MUST be reset/validated after reconciliation

**NFR-3: Observability**
- All reconciliation attempts MUST be logged with timestamps and duration
- All detected gaps MUST be logged with before/after values
- Reconciliation failures MUST be logged with error details and retry count

---

## Architecture

### Reconciliation Flow

```
SignalR Reconnected
        │
        ▼
  ┌─────────────────────┐
  │ Pause Event Queue   │ (Buffer incoming SignalR events)
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │ Fetch REST API State│
  │ (Parallel Requests) │
  │  - Positions        │
  │  - Orders           │
  │  - Quotes           │
  │  - Balance          │
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │ Compare with Local  │
  │ Cached State        │
  │ (Gap Detection)     │
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │ Update Local State  │
  │ (Reconciliation)    │
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │ Emit Synthetic      │
  │ Events for Gaps     │
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │ Notify User of      │
  │ Critical Changes    │
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │ Resume Event Queue  │
  │ (Process buffered)  │
  └──────────┬──────────┘
             │
             ▼
        Reconciliation Complete
```

### Component Responsibilities

**StateReconciliationManager:**
- Coordinates entire reconciliation process
- Triggers reconciliation on reconnection
- Orchestrates REST API calls
- Manages retry logic on failures
- Tracks reconciliation metrics

**GapDetector:**
- Compares REST state with local state
- Identifies new, modified, and deleted entities
- Calculates deltas (e.g., PnL changes, quantity changes)
- Categorizes gap severity (critical, important, informational)

**StateUpdater:**
- Applies REST API state to local cache
- Updates positions, orders, quotes, balance
- Clears stale data
- Maintains data consistency

**SyntheticEventEmitter:**
- Generates synthetic events for detected gaps
- Emits events in correct order (e.g., OrderUpdate before TradeExecution)
- Ensures events match SignalR event schema
- Prevents duplicate event processing

**ReconciliationNotifier:**
- Determines which changes warrant user notification
- Generates human-readable change summaries
- Shows notifications, toasts, or modals
- Provides detailed reconciliation report

---

## Gap Detection Algorithms

### Position Gap Detection

```typescript
interface PositionGap {
  type: 'NEW' | 'MODIFIED' | 'DELETED';
  positionId: string;
  symbol: string;
  before: Position | null;  // Local cached state
  after: Position | null;   // REST API state
  changes: {
    quantityChanged?: { from: number; to: number };
    entryPriceChanged?: { from: number; to: number };
    unrealizedPnLChanged?: { from: number; to: number };
    realizedPnLChanged?: { from: number; to: number };
  };
  severity: 'CRITICAL' | 'IMPORTANT' | 'INFORMATIONAL';
}

function detectPositionGaps(
  localPositions: Position[],
  restPositions: Position[]
): PositionGap[] {
  const gaps: PositionGap[] = [];

  // Create maps for fast lookup
  const localMap = new Map(localPositions.map(p => [p.id, p]));
  const restMap = new Map(restPositions.map(p => [p.id, p]));

  // Detect NEW positions (in REST but not local)
  for (const [positionId, restPosition] of restMap) {
    if (!localMap.has(positionId)) {
      gaps.push({
        type: 'NEW',
        positionId,
        symbol: restPosition.symbol,
        before: null,
        after: restPosition,
        changes: {},
        severity: 'IMPORTANT'
      });
    }
  }

  // Detect DELETED positions (in local but not REST)
  for (const [positionId, localPosition] of localMap) {
    if (!restMap.has(positionId)) {
      gaps.push({
        type: 'DELETED',
        positionId,
        symbol: localPosition.symbol,
        before: localPosition,
        after: null,
        changes: {},
        severity: 'CRITICAL' // Position closed during disconnection
      });
    }
  }

  // Detect MODIFIED positions (in both, but different)
  for (const [positionId, localPosition] of localMap) {
    const restPosition = restMap.get(positionId);
    if (restPosition) {
      const changes: any = {};

      if (localPosition.quantity !== restPosition.quantity) {
        changes.quantityChanged = {
          from: localPosition.quantity,
          to: restPosition.quantity
        };
      }

      if (localPosition.entryPrice !== restPosition.entryPrice) {
        changes.entryPriceChanged = {
          from: localPosition.entryPrice,
          to: restPosition.entryPrice
        };
      }

      if (localPosition.unrealizedPnL !== restPosition.unrealizedPnL) {
        changes.unrealizedPnLChanged = {
          from: localPosition.unrealizedPnL,
          to: restPosition.unrealizedPnL
        };
      }

      if (localPosition.realizedPnL !== restPosition.realizedPnL) {
        changes.realizedPnLChanged = {
          from: localPosition.realizedPnL,
          to: restPosition.realizedPnL
        };
      }

      if (Object.keys(changes).length > 0) {
        // Determine severity based on changes
        let severity: 'CRITICAL' | 'IMPORTANT' | 'INFORMATIONAL' = 'INFORMATIONAL';

        if (changes.quantityChanged) {
          // Quantity change indicates partial close or addition
          severity = 'IMPORTANT';
        }

        if (changes.unrealizedPnLChanged) {
          const pnlDelta = Math.abs(restPosition.unrealizedPnL - localPosition.unrealizedPnL);
          if (pnlDelta > 100) { // More than $100 change
            severity = 'IMPORTANT';
          }
        }

        gaps.push({
          type: 'MODIFIED',
          positionId,
          symbol: localPosition.symbol,
          before: localPosition,
          after: restPosition,
          changes,
          severity
        });
      }
    }
  }

  return gaps;
}
```

### Order Gap Detection

```typescript
interface OrderGap {
  type: 'NEW' | 'MODIFIED' | 'DELETED';
  orderId: string;
  symbol: string;
  before: Order | null;
  after: Order | null;
  changes: {
    stateChanged?: { from: OrderState; to: OrderState };
    fillVolumeChanged?: { from: number; to: number };
    filledPriceChanged?: { from: number; to: number };
  };
  severity: 'CRITICAL' | 'IMPORTANT' | 'INFORMATIONAL';
}

function detectOrderGaps(
  localOrders: Order[],
  restOrders: Order[]
): OrderGap[] {
  const gaps: OrderGap[] = [];

  const localMap = new Map(localOrders.map(o => [o.id, o]));
  const restMap = new Map(restOrders.map(o => [o.id, o]));

  // NEW orders
  for (const [orderId, restOrder] of restMap) {
    if (!localMap.has(orderId)) {
      gaps.push({
        type: 'NEW',
        orderId,
        symbol: restOrder.symbol,
        before: null,
        after: restOrder,
        changes: {},
        severity: 'IMPORTANT' // New order placed elsewhere
      });
    }
  }

  // DELETED orders
  for (const [orderId, localOrder] of localMap) {
    if (!restMap.has(orderId)) {
      // Order completed/cancelled during disconnection
      gaps.push({
        type: 'DELETED',
        orderId,
        symbol: localOrder.symbol,
        before: localOrder,
        after: null,
        changes: {},
        severity: localOrder.state === OrderState.FILLED ? 'CRITICAL' : 'IMPORTANT'
      });
    }
  }

  // MODIFIED orders
  for (const [orderId, localOrder] of localMap) {
    const restOrder = restMap.get(orderId);
    if (restOrder) {
      const changes: any = {};

      if (localOrder.state !== restOrder.state) {
        changes.stateChanged = {
          from: localOrder.state,
          to: restOrder.state
        };
      }

      if (localOrder.fillVolume !== restOrder.fillVolume) {
        changes.fillVolumeChanged = {
          from: localOrder.fillVolume,
          to: restOrder.fillVolume
        };
      }

      if (localOrder.filledPrice !== restOrder.filledPrice) {
        changes.filledPriceChanged = {
          from: localOrder.filledPrice,
          to: restOrder.filledPrice
        };
      }

      if (Object.keys(changes).length > 0) {
        let severity: 'CRITICAL' | 'IMPORTANT' | 'INFORMATIONAL' = 'INFORMATIONAL';

        if (changes.stateChanged?.to === OrderState.FILLED) {
          severity = 'CRITICAL'; // Order filled during disconnection
        } else if (changes.fillVolumeChanged) {
          severity = 'IMPORTANT'; // Partial fill
        }

        gaps.push({
          type: 'MODIFIED',
          orderId,
          symbol: localOrder.symbol,
          before: localOrder,
          after: restOrder,
          changes,
          severity
        });
      }
    }
  }

  return gaps;
}
```

### Quote Gap Detection

```typescript
interface QuoteGap {
  symbol: string;
  before: Quote | null;
  after: Quote;
  changes: {
    bidChanged?: { from: number; to: number; delta: number };
    askChanged?: { from: number; to: number; delta: number };
  };
  severity: 'CRITICAL' | 'IMPORTANT' | 'INFORMATIONAL';
}

function detectQuoteGaps(
  localQuotes: Map<string, Quote>,
  restQuotes: Quote[]
): QuoteGap[] {
  const gaps: QuoteGap[] = [];

  for (const restQuote of restQuotes) {
    const localQuote = localQuotes.get(restQuote.symbol);
    const changes: any = {};

    if (localQuote) {
      if (localQuote.bid !== restQuote.bid) {
        changes.bidChanged = {
          from: localQuote.bid,
          to: restQuote.bid,
          delta: restQuote.bid - localQuote.bid
        };
      }

      if (localQuote.ask !== restQuote.ask) {
        changes.askChanged = {
          from: localQuote.ask,
          to: restQuote.ask,
          delta: restQuote.ask - localQuote.ask
        };
      }
    } else {
      // No local quote, treat as new
      changes.bidChanged = { from: 0, to: restQuote.bid, delta: restQuote.bid };
      changes.askChanged = { from: 0, to: restQuote.ask, delta: restQuote.ask };
    }

    if (Object.keys(changes).length > 0) {
      // Determine severity based on price movement
      let severity: 'CRITICAL' | 'IMPORTANT' | 'INFORMATIONAL' = 'INFORMATIONAL';

      if (changes.bidChanged) {
        const percentChange = Math.abs(changes.bidChanged.delta / changes.bidChanged.from) * 100;
        if (percentChange > 1.0) { // >1% price change
          severity = 'IMPORTANT';
        }
        if (percentChange > 5.0) { // >5% price change
          severity = 'CRITICAL';
        }
      }

      gaps.push({
        symbol: restQuote.symbol,
        before: localQuote || null,
        after: restQuote,
        changes,
        severity
      });
    }
  }

  return gaps;
}
```

---

## Synthetic Event Generation

### Event Emission Strategy

When gaps are detected, synthetic events MUST be emitted to maintain consistency with normal SignalR event processing. These events should trigger the same downstream logic (UI updates, risk rule evaluation, database persistence) as real-time events.

**Event Emission Order:**
1. QuoteUpdate events (prices first, as they affect PnL calculations)
2. TradeExecution events (for filled orders)
3. OrderUpdate events (for order state changes)
4. PositionUpdate events (for position changes)
5. BalanceUpdate events (last, as they depend on all other updates)

### Synthetic Event Generators

```typescript
interface SyntheticEvent {
  eventType: string;
  source: 'reconciliation';
  timestamp: number;
  data: any;
}

class SyntheticEventEmitter {
  /**
   * Generate synthetic PositionUpdate events from position gaps
   */
  emitPositionEvents(gaps: PositionGap[]): void {
    for (const gap of gaps) {
      let event: SyntheticEvent;

      switch (gap.type) {
        case 'NEW':
          // Position opened during disconnection
          event = {
            eventType: 'PositionUpdate',
            source: 'reconciliation',
            timestamp: Date.now(),
            data: {
              position: gap.after,
              action: 'OPENED',
              reconciliation: true
            }
          };
          break;

        case 'DELETED':
          // Position closed during disconnection
          event = {
            eventType: 'PositionUpdate',
            source: 'reconciliation',
            timestamp: Date.now(),
            data: {
              position: gap.before,
              action: 'CLOSED',
              reconciliation: true,
              reason: 'UNKNOWN' // Could be stop-loss, take-profit, or manual close
            }
          };
          break;

        case 'MODIFIED':
          // Position modified during disconnection
          event = {
            eventType: 'PositionUpdate',
            source: 'reconciliation',
            timestamp: Date.now(),
            data: {
              position: gap.after,
              previousPosition: gap.before,
              action: 'MODIFIED',
              changes: gap.changes,
              reconciliation: true
            }
          };
          break;
      }

      // Emit event through normal event bus
      eventBus.emit('position:update', event.data);

      // Log synthetic event
      logger.info('Synthetic PositionUpdate event emitted', {
        gap: gap.type,
        positionId: gap.positionId,
        symbol: gap.symbol,
        severity: gap.severity
      });
    }
  }

  /**
   * Generate synthetic OrderUpdate events from order gaps
   */
  emitOrderEvents(gaps: OrderGap[]): void {
    for (const gap of gaps) {
      let event: SyntheticEvent;

      switch (gap.type) {
        case 'NEW':
          // Order placed during disconnection (e.g., from mobile app)
          event = {
            eventType: 'OrderUpdate',
            source: 'reconciliation',
            timestamp: Date.now(),
            data: {
              order: gap.after,
              action: 'PLACED',
              reconciliation: true,
              origin: 'EXTERNAL' // Not placed by this client
            }
          };
          break;

        case 'DELETED':
          // Order completed/cancelled during disconnection
          const action = gap.before.state === OrderState.FILLED ? 'FILLED' : 'CANCELLED';
          event = {
            eventType: 'OrderUpdate',
            source: 'reconciliation',
            timestamp: Date.now(),
            data: {
              order: gap.before,
              action,
              reconciliation: true
            }
          };

          // If filled, also emit TradeExecution event
          if (action === 'FILLED') {
            eventBus.emit('trade:execution', {
              orderId: gap.orderId,
              symbol: gap.before.symbol,
              volume: gap.before.fillVolume,
              price: gap.before.filledPrice,
              side: gap.before.side,
              timestamp: Date.now(),
              reconciliation: true
            });
          }
          break;

        case 'MODIFIED':
          // Order modified during disconnection (likely partial fill)
          event = {
            eventType: 'OrderUpdate',
            source: 'reconciliation',
            timestamp: Date.now(),
            data: {
              order: gap.after,
              previousOrder: gap.before,
              action: 'MODIFIED',
              changes: gap.changes,
              reconciliation: true
            }
          };

          // If fill volume increased, emit TradeExecution for delta
          if (gap.changes.fillVolumeChanged) {
            const fillDelta = gap.changes.fillVolumeChanged.to - gap.changes.fillVolumeChanged.from;
            eventBus.emit('trade:execution', {
              orderId: gap.orderId,
              symbol: gap.after.symbol,
              volume: fillDelta,
              price: gap.after.filledPrice,
              side: gap.after.side,
              timestamp: Date.now(),
              reconciliation: true,
              partial: true
            });
          }
          break;
      }

      // Emit event through normal event bus
      eventBus.emit('order:update', event.data);

      logger.info('Synthetic OrderUpdate event emitted', {
        gap: gap.type,
        orderId: gap.orderId,
        symbol: gap.symbol,
        severity: gap.severity
      });
    }
  }

  /**
   * Generate synthetic QuoteUpdate events from quote gaps
   */
  emitQuoteEvents(gaps: QuoteGap[]): void {
    for (const gap of gaps) {
      const event: SyntheticEvent = {
        eventType: 'QuoteUpdate',
        source: 'reconciliation',
        timestamp: Date.now(),
        data: {
          quote: gap.after,
          previousQuote: gap.before,
          changes: gap.changes,
          reconciliation: true
        }
      };

      // Emit event through normal event bus
      eventBus.emit('quote:update', event.data);

      logger.debug('Synthetic QuoteUpdate event emitted', {
        symbol: gap.symbol,
        bidChange: gap.changes.bidChanged?.delta,
        askChange: gap.changes.askChanged?.delta
      });
    }
  }
}
```

### Preventing Double-Execution of Risk Rules

**Problem:** If a risk rule (e.g., stop-loss) already executed server-side during disconnection and closed a position, we don't want to re-trigger that rule when processing the synthetic PositionUpdate event.

**Solution:** Mark synthetic events with `reconciliation: true` flag, and skip rule execution for already-completed actions.

```typescript
// In risk rule evaluation
function evaluateRule(position: Position, event: PositionUpdateEvent): void {
  // If this is a reconciliation event and position is already closed, skip rule
  if (event.reconciliation && event.action === 'CLOSED') {
    logger.info('Skipping rule evaluation for reconciliation event (position already closed server-side)', {
      positionId: position.id,
      symbol: position.symbol
    });
    return;
  }

  // Normal rule evaluation...
}
```

---

## User Notification Strategy

### Notification Severity Levels

| Severity | Description | UI Treatment | Examples |
|----------|-------------|--------------|----------|
| CRITICAL | Major changes requiring immediate attention | Modal dialog, blocks UI | Position closed by stop-loss, large loss realized |
| IMPORTANT | Significant changes user should know about | Prominent toast notification | Order filled, position PnL changed >$100 |
| INFORMATIONAL | Minor changes, background updates | Subtle notification badge | Price updated, small PnL changes |

### Notification Content Templates

```typescript
interface ReconciliationNotification {
  severity: 'CRITICAL' | 'IMPORTANT' | 'INFORMATIONAL';
  title: string;
  message: string;
  details: string[];
  actions: { label: string; onClick: () => void }[];
}

class ReconciliationNotifier {
  generateNotifications(
    positionGaps: PositionGap[],
    orderGaps: OrderGap[],
    quoteGaps: QuoteGap[]
  ): ReconciliationNotification[] {
    const notifications: ReconciliationNotification[] = [];

    // Critical: Positions closed during disconnection
    const closedPositions = positionGaps.filter(g => g.type === 'DELETED');
    if (closedPositions.length > 0) {
      notifications.push({
        severity: 'CRITICAL',
        title: `${closedPositions.length} Position(s) Closed During Disconnection`,
        message: 'Some positions were closed while you were offline. Review the changes below.',
        details: closedPositions.map(gap =>
          `${gap.symbol}: ${gap.before.quantity} units closed (PnL: ${gap.before.realizedPnL.toFixed(2)})`
        ),
        actions: [
          { label: 'View Details', onClick: () => showReconciliationReport() },
          { label: 'Acknowledge', onClick: () => dismissNotification() }
        ]
      });
    }

    // Critical: Orders filled during disconnection
    const filledOrders = orderGaps.filter(g =>
      g.type === 'DELETED' && g.before.state === OrderState.FILLED ||
      g.type === 'MODIFIED' && g.changes.stateChanged?.to === OrderState.FILLED
    );
    if (filledOrders.length > 0) {
      notifications.push({
        severity: 'CRITICAL',
        title: `${filledOrders.length} Order(s) Filled During Disconnection`,
        message: 'Some orders were executed while you were offline.',
        details: filledOrders.map(gap => {
          const order = gap.after || gap.before;
          return `${order.symbol}: ${order.type} ${order.side} ${order.fillVolume} @ ${order.filledPrice}`;
        }),
        actions: [
          { label: 'View Positions', onClick: () => navigateToPositions() },
          { label: 'Acknowledge', onClick: () => dismissNotification() }
        ]
      });
    }

    // Important: Large PnL changes
    const largePnLChanges = positionGaps.filter(gap => {
      if (gap.type !== 'MODIFIED' || !gap.changes.unrealizedPnLChanged) return false;
      const delta = Math.abs(gap.changes.unrealizedPnLChanged.to - gap.changes.unrealizedPnLChanged.from);
      return delta > 100; // More than $100 change
    });
    if (largePnLChanges.length > 0) {
      notifications.push({
        severity: 'IMPORTANT',
        title: 'Significant PnL Changes',
        message: `${largePnLChanges.length} position(s) had significant profit/loss changes.`,
        details: largePnLChanges.map(gap => {
          const delta = gap.changes.unrealizedPnLChanged.to - gap.changes.unrealizedPnLChanged.from;
          return `${gap.symbol}: ${delta > 0 ? '+' : ''}${delta.toFixed(2)} (now ${gap.after.unrealizedPnL.toFixed(2)})`;
        }),
        actions: [
          { label: 'View Report', onClick: () => showReconciliationReport() },
          { label: 'Dismiss', onClick: () => dismissNotification() }
        ]
      });
    }

    // Important: New positions/orders from external sources
    const externalPositions = positionGaps.filter(g => g.type === 'NEW');
    const externalOrders = orderGaps.filter(g => g.type === 'NEW');
    if (externalPositions.length > 0 || externalOrders.length > 0) {
      notifications.push({
        severity: 'IMPORTANT',
        title: 'External Activity Detected',
        message: `${externalPositions.length} position(s) and ${externalOrders.length} order(s) were created from another device/session.`,
        details: [
          ...externalPositions.map(gap => `Position: ${gap.symbol} (${gap.after.quantity} units)`),
          ...externalOrders.map(gap => `Order: ${gap.symbol} ${gap.after.type} ${gap.after.side}`)
        ],
        actions: [
          { label: 'View Details', onClick: () => showReconciliationReport() },
          { label: 'Dismiss', onClick: () => dismissNotification() }
        ]
      });
    }

    return notifications;
  }

  displayNotifications(notifications: ReconciliationNotification[]): void {
    // Display critical notifications as modal dialogs
    const critical = notifications.filter(n => n.severity === 'CRITICAL');
    if (critical.length > 0) {
      uiManager.showModal({
        title: 'Critical Changes During Disconnection',
        content: critical,
        blocking: true,
        closable: true
      });
    }

    // Display important notifications as toasts
    const important = notifications.filter(n => n.severity === 'IMPORTANT');
    for (const notification of important) {
      uiManager.showToast({
        type: 'warning',
        title: notification.title,
        message: notification.message,
        duration: 10000, // 10 seconds
        actions: notification.actions
      });
    }
  }
}
```

---

## Configuration Schema

```yaml
signalr:
  reconciliation:
    # Enable automatic reconciliation after reconnection
    enabled: true

    # Maximum time to wait for reconciliation to complete (milliseconds)
    timeout: 15000  # 15 seconds

    # Maximum number of retry attempts if reconciliation fails
    maxRetries: 3

    # Retry delay sequence for failed reconciliation (milliseconds)
    retryDelays: [1000, 5000, 10000]

    # Pause incoming SignalR events during reconciliation
    pauseEventsDuring: true

    # Buffer size for events received during reconciliation (max events to queue)
    eventBufferSize: 1000

  restApi:
    # Parallel request limit for reconciliation (max simultaneous REST calls)
    maxConcurrentRequests: 5

    # Timeout for individual REST API calls during reconciliation (milliseconds)
    requestTimeout: 5000

    # Fetch full state even if some endpoints fail (partial reconciliation)
    allowPartialReconciliation: true

  notifications:
    # Show notifications for changes during disconnection
    enabled: true

    # Minimum PnL change to trigger notification (dollars)
    minPnLChangeForNotification: 100

    # Minimum percentage price change to trigger notification
    minPriceChangePercentForNotification: 1.0

    # Show modal for critical changes (vs. just toast notifications)
    showModalForCriticalChanges: true

    # Auto-dismiss informational notifications after duration (milliseconds)
    autoDismissInfoDuration: 5000

  logging:
    # Log level for reconciliation events
    reconciliationEvents: INFO

    # Log all detected gaps (can be verbose)
    logAllGaps: true

    # Log synthetic event emissions
    logSyntheticEvents: true
```

---

## Implementation Checklist

### Phase 1: Core Reconciliation
- [ ] Create StateReconciliationManager class
- [ ] Integrate with SignalRConnectionManager (trigger on reconnect)
- [ ] Implement REST API batch fetching (positions, orders, quotes, balance)
- [ ] Implement parallel request execution with timeout handling
- [ ] Implement partial failure handling
- [ ] Add comprehensive logging

### Phase 2: Gap Detection
- [ ] Implement GapDetector class
- [ ] Implement detectPositionGaps() algorithm
- [ ] Implement detectOrderGaps() algorithm
- [ ] Implement detectQuoteGaps() algorithm
- [ ] Implement detectBalanceGap() algorithm
- [ ] Add gap severity classification logic
- [ ] Test gap detection with various scenarios

### Phase 3: State Updates
- [ ] Implement StateUpdater class
- [ ] Update local position cache from REST state
- [ ] Update local order cache from REST state
- [ ] Update local quote cache from REST state
- [ ] Update account balance from REST state
- [ ] Clear stale data from cache
- [ ] Ensure atomic updates (all-or-nothing)

### Phase 4: Synthetic Event Emission
- [ ] Implement SyntheticEventEmitter class
- [ ] Generate PositionUpdate synthetic events
- [ ] Generate OrderUpdate synthetic events
- [ ] Generate TradeExecution synthetic events
- [ ] Generate QuoteUpdate synthetic events
- [ ] Generate BalanceUpdate synthetic events
- [ ] Emit events in correct order
- [ ] Add reconciliation flag to all synthetic events
- [ ] Prevent double-execution of risk rules

### Phase 5: User Notifications
- [ ] Implement ReconciliationNotifier class
- [ ] Generate notifications for critical changes
- [ ] Generate notifications for important changes
- [ ] Display modal dialogs for critical changes
- [ ] Display toast notifications for important changes
- [ ] Create detailed reconciliation report UI
- [ ] Add "View Details" action buttons
- [ ] Test notification display for all scenarios

### Phase 6: Error Handling
- [ ] Implement retry logic for failed reconciliation
- [ ] Handle partial REST API failures
- [ ] Handle timeout during reconciliation
- [ ] Show error messages to user
- [ ] Provide manual retry button
- [ ] Disable order placement until reconciliation succeeds
- [ ] Test all failure scenarios

### Phase 7: Event Queue Management
- [ ] Pause incoming SignalR event processing during reconciliation
- [ ] Buffer events received during reconciliation
- [ ] Resume event processing after reconciliation complete
- [ ] Process buffered events in order
- [ ] Handle buffer overflow (too many events during reconciliation)

### Phase 8: Testing
- [ ] Unit test: Gap detection algorithms
- [ ] Unit test: Synthetic event generation
- [ ] Unit test: Notification generation
- [ ] Integration test: Full reconciliation flow
- [ ] Integration test: Partial reconciliation (some endpoints fail)
- [ ] Integration test: Reconciliation failure and retry
- [ ] Integration test: Position closed during disconnection
- [ ] Integration test: Order filled during disconnection
- [ ] Integration test: Large PnL change during disconnection
- [ ] Load test: Reconciliation with 100+ positions/orders

---

## Validation Criteria

### Functional Validation

**VC-1: Automatic Trigger**
- ✅ Reconciliation triggers immediately after SignalR reconnection
- ✅ Reconciliation completes before resuming SignalR event processing
- ✅ Incoming SignalR events are buffered during reconciliation

**VC-2: Full State Sync**
- ✅ All positions fetched from REST API
- ✅ All orders fetched from REST API
- ✅ All quotes fetched for active symbols
- ✅ Account balance fetched from REST API
- ✅ Requests execute in parallel (< 5 seconds total)

**VC-3: Gap Detection**
- ✅ New positions detected correctly
- ✅ Deleted positions detected correctly
- ✅ Modified positions detected correctly
- ✅ New orders detected correctly
- ✅ Deleted orders (filled/cancelled) detected correctly
- ✅ Modified orders (partial fills) detected correctly
- ✅ Quote changes detected correctly
- ✅ Gap severity classified correctly

**VC-4: State Updates**
- ✅ Local position cache matches REST API state after reconciliation
- ✅ Local order cache matches REST API state after reconciliation
- ✅ Local quote cache matches REST API state after reconciliation
- ✅ Account balance matches REST API state after reconciliation
- ✅ No stale data remains in cache

**VC-5: Synthetic Events**
- ✅ PositionUpdate events emitted for position gaps
- ✅ OrderUpdate events emitted for order gaps
- ✅ TradeExecution events emitted for filled orders
- ✅ QuoteUpdate events emitted for quote gaps
- ✅ Events emitted in correct order
- ✅ Events marked with reconciliation flag
- ✅ Risk rules do NOT double-execute for reconciliation events

**VC-6: User Notifications**
- ✅ Critical changes trigger modal dialog
- ✅ Important changes trigger toast notifications
- ✅ Informational changes logged but not shown
- ✅ Notification content is accurate and helpful
- ✅ "View Details" button shows full reconciliation report

**VC-7: Error Handling**
- ✅ Failed reconciliation retries with exponential backoff
- ✅ Partial failures handled gracefully
- ✅ User shown error message on persistent failure
- ✅ Manual retry button available
- ✅ Order placement disabled until reconciliation succeeds

### Performance Validation

**PV-1: Reconciliation Speed**
- ✅ Reconciliation completes in < 5 seconds for typical accounts
- ✅ Reconciliation completes in < 15 seconds for large accounts
- ✅ UI remains responsive during reconciliation

**PV-2: Memory Usage**
- ✅ Event buffer does not cause memory issues
- ✅ Reconciliation does not leak memory

### Reliability Validation

**RV-1: Data Consistency**
- ✅ After reconciliation, local state is 100% consistent with REST API
- ✅ No data corruption or inconsistencies
- ✅ All gaps are reconciled, none missed

**RV-2: Event Ordering**
- ✅ Synthetic events emitted in correct order
- ✅ Buffered SignalR events processed in correct order
- ✅ No race conditions between synthetic and real-time events

---

## Integration Points

### Dependencies
- **SignalRConnectionManager** (SIGNALR-001): Triggers reconciliation on reconnect
- **REST API Client**: Fetches full state from REST endpoints
- **EventBus**: Emits synthetic events for downstream processing
- **Logger**: Logs reconciliation activities
- **UIManager**: Displays notifications and reconciliation report

### External Systems
- **REST API Endpoints**:
  - `GET /api/Positions/getAllPositions`
  - `GET /api/Orders/getAllOrders`
  - `GET /api/Quotes/getQuote`
  - `GET /api/Account/getBalance`

---

## References

- **ERRORS_AND_WARNINGS_CONSOLIDATED.md**: Section "GAP-API-SCENARIO-003: SignalR Message Loss"
- **SIGNALR_RECONNECTION_SPEC.md**: Reconnection logic that triggers reconciliation
- **API Integration Analysis**: REST API endpoint specifications

---

**End of Specification**
