# SignalR Event Subscription Management Specification

**doc_id:** SIGNALR-005
**version:** 1.0
**status:** DRAFT
**addresses:** Event subscription persistence and re-subscription after reconnection
**created:** 2025-10-22
**last_updated:** 2025-10-22

---

## Overview

This specification defines the SignalR event subscription management strategy, including automatic re-subscription after reconnection, subscription tracking, event handler registration, and hub-specific subscription patterns. While not explicitly called out as a GAP in the error analysis, proper subscription management is critical to prevent lost event handlers after reconnection.

**Design Philosophy:**
- Event subscriptions MUST persist across reconnections
- Event handlers MUST be automatically re-registered after reconnection
- Subscription state MUST be tracked and validated
- Hub-specific subscriptions MUST be managed separately
- Missing subscriptions MUST be detected and reported

---

## Requirements

### Functional Requirements

**FR-1: Subscription Persistence**
- All event subscriptions MUST persist across disconnections and reconnections
- Event handler references MUST NOT be lost during reconnection
- Subscription state MUST be maintained in memory throughout application lifecycle

**FR-2: Automatic Re-subscription**
- After successful reconnection, all previous event subscriptions MUST be automatically re-registered
- Re-subscription MUST occur before processing new SignalR events
- Re-subscription MUST complete within 2 seconds of reconnection

**FR-3: Event Handler Registration**
- System MUST support registering multiple event handlers for same event type
- Event handlers MUST be called in registration order
- Event handler errors MUST NOT prevent other handlers from executing

**FR-4: Hub-Specific Subscriptions**
- System MUST support hub-specific event subscriptions (e.g., PositionUpdate, OrderUpdate)
- System MUST support server-side subscription methods (e.g., SubscribeToSymbol)
- System MUST track which symbols/entities are subscribed
- System MUST re-subscribe to all symbols/entities after reconnection

**FR-5: Subscription Tracking**
- System MUST maintain registry of all active subscriptions
- System MUST track subscription state: REGISTERED, ACTIVE, PENDING_RESUBSCRIPTION, FAILED
- System MUST detect missing subscriptions (expected but not active)

**FR-6: Subscription Validation**
- After reconnection, system MUST validate that all expected events are being received
- If events not received within timeout, system MUST retry re-subscription
- Persistent re-subscription failures MUST be logged and reported to user

### Non-Functional Requirements

**NFR-1: Performance**
- Re-subscription process MUST NOT block UI
- Re-subscription MUST complete within 2 seconds for typical applications (<50 subscriptions)
- Event handler execution MUST NOT exceed 100ms per handler

**NFR-2: Reliability**
- Subscription state MUST be crash-resistant (recoverable after application restart)
- Event handler failures MUST NOT crash application
- Missing subscriptions MUST be detected within 30 seconds

**NFR-3: Observability**
- All subscription registrations MUST be logged
- All re-subscription attempts MUST be logged
- Subscription failures MUST be logged with error details

---

## Architecture

### Subscription Management Components

```
┌────────────────────────────────────────────────┐
│     EventSubscriptionManager                   │
├────────────────────────────────────────────────┤
│ - subscriptions: Map<string, Subscription>     │
│ - handlers: Map<string, EventHandler[]>        │
│ - hubSubscriptions: HubSubscription[]          │
├────────────────────────────────────────────────┤
│ + subscribe(event, handler): SubscriptionId    │
│ + unsubscribe(subscriptionId): void            │
│ + resubscribeAll(): Promise<void>              │
│ + validateSubscriptions(): ValidationResult    │
│ + getActiveSubscriptions(): Subscription[]     │
└────────────────────────────────────────────────┘
                      │
                      │ Manages
                      ▼
┌────────────────────────────────────────────────┐
│          Subscription                          │
├────────────────────────────────────────────────┤
│ - id: string                                   │
│ - eventName: string                            │
│ - handler: EventHandler                        │
│ - state: SubscriptionState                     │
│ - registeredAt: number                         │
│ - lastEventAt: number                          │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│       HubSubscription (Server-Side)            │
├────────────────────────────────────────────────┤
│ - type: 'symbol' | 'account' | 'custom'        │
│ - method: string (e.g., "SubscribeToSymbol")   │
│ - parameters: any[]                            │
│ - state: SubscriptionState                     │
└────────────────────────────────────────────────┘
```

### Subscription Lifecycle

```
Registration
     │
     ▼
┌──────────────┐
│ REGISTERED   │ Subscription created, handler stored
└─────┬────────┘
      │
      │ Connection established
      ▼
┌──────────────┐
│   ACTIVE     │ Events being received
└─────┬────────┘
      │
      │ Disconnection occurs
      ▼
┌─────────────────────┐
│ PENDING_            │ Waiting for reconnection
│ RESUBSCRIPTION      │
└─────┬───────────────┘
      │
      │ Reconnection successful
      ▼
┌──────────────┐
│ Re-register  │ Call connection.on() again
└─────┬────────┘
      │
      ├─── Success ─────► ACTIVE
      │
      └─── Failure ─────► FAILED
```

---

## Event Subscription API

### Client-Side Event Subscriptions

SignalR uses `connection.on(eventName, handler)` for client-side event subscriptions. These subscriptions persist automatically in SignalR client, but we need to track them for validation.

```typescript
interface EventHandler {
  (data: any): void | Promise<void>;
}

interface Subscription {
  id: string;                    // Unique subscription ID (UUID)
  eventName: string;             // SignalR event name (e.g., "PositionUpdate")
  handler: EventHandler;         // Event handler function
  state: SubscriptionState;      // Current subscription state
  registeredAt: number;          // Timestamp when subscribed
  lastEventAt: number | null;    // Timestamp of last event received
  eventCount: number;            // Total events received
}

enum SubscriptionState {
  REGISTERED = 'registered',               // Subscription created
  ACTIVE = 'active',                       // Events being received
  PENDING_RESUBSCRIPTION = 'pending',      // Waiting for reconnection
  FAILED = 'failed'                        // Re-subscription failed
}

class EventSubscriptionManager {
  private subscriptions: Map<string, Subscription> = new Map();
  private connection: HubConnection;

  /**
   * Subscribe to a SignalR event
   * @param eventName SignalR event name (e.g., "PositionUpdate")
   * @param handler Event handler function
   * @returns Subscription ID for later unsubscription
   */
  subscribe(eventName: string, handler: EventHandler): string {
    const subscriptionId = generateUUID();

    const subscription: Subscription = {
      id: subscriptionId,
      eventName,
      handler,
      state: SubscriptionState.REGISTERED,
      registeredAt: Date.now(),
      lastEventAt: null,
      eventCount: 0
    };

    // Wrap handler to track events
    const wrappedHandler = async (data: any) => {
      subscription.lastEventAt = Date.now();
      subscription.eventCount++;
      subscription.state = SubscriptionState.ACTIVE;

      try {
        await handler(data);
      } catch (error) {
        logger.error('Event handler error', {
          eventName,
          subscriptionId,
          error: error.message
        });
        // Continue executing other handlers
      }
    };

    // Register with SignalR connection
    this.connection.on(eventName, wrappedHandler);

    // Store subscription
    this.subscriptions.set(subscriptionId, subscription);

    logger.info('Event subscription registered', {
      subscriptionId,
      eventName
    });

    return subscriptionId;
  }

  /**
   * Unsubscribe from event
   * @param subscriptionId Subscription ID returned from subscribe()
   */
  unsubscribe(subscriptionId: string): void {
    const subscription = this.subscriptions.get(subscriptionId);
    if (!subscription) {
      logger.warn('Subscription not found', { subscriptionId });
      return;
    }

    // Remove from SignalR connection
    this.connection.off(subscription.eventName, subscription.handler);

    // Remove from tracking
    this.subscriptions.delete(subscriptionId);

    logger.info('Event subscription removed', {
      subscriptionId,
      eventName: subscription.eventName
    });
  }

  /**
   * Get all active subscriptions
   */
  getActiveSubscriptions(): Subscription[] {
    return Array.from(this.subscriptions.values());
  }

  /**
   * Get subscriptions for specific event
   */
  getSubscriptionsByEvent(eventName: string): Subscription[] {
    return Array.from(this.subscriptions.values())
      .filter(sub => sub.eventName === eventName);
  }
}
```

### Server-Side Hub Subscriptions

Some SignalR hubs require explicit server-side subscription via hub methods (e.g., `SubscribeToSymbol`, `SubscribeToAccount`). These MUST be re-invoked after reconnection.

```typescript
interface HubSubscription {
  id: string;                      // Unique subscription ID
  type: 'symbol' | 'account' | 'custom';
  method: string;                  // Hub method name (e.g., "SubscribeToSymbol")
  parameters: any[];               // Method parameters (e.g., ["EURUSD"])
  state: SubscriptionState;
  registeredAt: number;
  lastResubscribedAt: number | null;
}

class HubSubscriptionManager {
  private hubSubscriptions: Map<string, HubSubscription> = new Map();
  private connection: HubConnection;

  /**
   * Subscribe to server-side hub method
   * @param method Hub method name
   * @param parameters Method parameters
   * @returns Subscription ID
   */
  async subscribeHub(
    method: string,
    parameters: any[],
    type: 'symbol' | 'account' | 'custom' = 'custom'
  ): Promise<string> {
    const subscriptionId = generateUUID();

    const subscription: HubSubscription = {
      id: subscriptionId,
      type,
      method,
      parameters,
      state: SubscriptionState.REGISTERED,
      registeredAt: Date.now(),
      lastResubscribedAt: null
    };

    try {
      // Invoke hub method
      await this.connection.invoke(method, ...parameters);

      subscription.state = SubscriptionState.ACTIVE;
      subscription.lastResubscribedAt = Date.now();

      logger.info('Hub subscription registered', {
        subscriptionId,
        method,
        parameters
      });

    } catch (error) {
      subscription.state = SubscriptionState.FAILED;

      logger.error('Hub subscription failed', {
        subscriptionId,
        method,
        parameters,
        error: error.message
      });

      throw error;
    }

    this.hubSubscriptions.set(subscriptionId, subscription);
    return subscriptionId;
  }

  /**
   * Unsubscribe from server-side hub method
   * @param subscriptionId Subscription ID
   * @param unsubscribeMethod Optional hub method to call for unsubscription
   */
  async unsubscribeHub(
    subscriptionId: string,
    unsubscribeMethod?: string
  ): Promise<void> {
    const subscription = this.hubSubscriptions.get(subscriptionId);
    if (!subscription) {
      return;
    }

    // If unsubscribe method provided, call it
    if (unsubscribeMethod) {
      try {
        await this.connection.invoke(unsubscribeMethod, ...subscription.parameters);
      } catch (error) {
        logger.error('Hub unsubscription failed', {
          subscriptionId,
          method: unsubscribeMethod,
          error: error.message
        });
      }
    }

    this.hubSubscriptions.delete(subscriptionId);

    logger.info('Hub subscription removed', {
      subscriptionId,
      method: subscription.method
    });
  }

  /**
   * Get all hub subscriptions
   */
  getHubSubscriptions(): HubSubscription[] {
    return Array.from(this.hubSubscriptions.values());
  }
}
```

---

## Re-subscription After Reconnection

### Re-subscription Strategy

After SignalR reconnection, we must:
1. Client-side subscriptions: Already persist, but validate they're working
2. Server-side hub subscriptions: MUST be re-invoked

```typescript
class EventSubscriptionManager {
  /**
   * Re-establish all subscriptions after reconnection
   * Called by SignalRConnectionManager.onreconnected()
   */
  async resubscribeAll(): Promise<void> {
    logger.info('Re-subscribing to all events after reconnection');

    // Mark all subscriptions as pending
    for (const subscription of this.subscriptions.values()) {
      subscription.state = SubscriptionState.PENDING_RESUBSCRIPTION;
    }

    for (const hubSubscription of this.hubSubscriptions.values()) {
      hubSubscription.state = SubscriptionState.PENDING_RESUBSCRIPTION;
    }

    // Client-side event subscriptions persist automatically in SignalR client
    // We just need to validate they're working by waiting for events
    // (handled by validateSubscriptions() called after reconciliation)

    // Server-side hub subscriptions MUST be re-invoked
    await this.resubscribeHubMethods();

    logger.info('Re-subscription complete');
  }

  /**
   * Re-invoke all server-side hub subscription methods
   */
  private async resubscribeHubMethods(): Promise<void> {
    const hubSubscriptions = Array.from(this.hubSubscriptions.values());

    const results = await Promise.allSettled(
      hubSubscriptions.map(async (subscription) => {
        try {
          await this.connection.invoke(subscription.method, ...subscription.parameters);

          subscription.state = SubscriptionState.ACTIVE;
          subscription.lastResubscribedAt = Date.now();

          logger.info('Hub re-subscription successful', {
            subscriptionId: subscription.id,
            method: subscription.method
          });

        } catch (error) {
          subscription.state = SubscriptionState.FAILED;

          logger.error('Hub re-subscription failed', {
            subscriptionId: subscription.id,
            method: subscription.method,
            error: error.message
          });

          throw error;
        }
      })
    );

    // Check for failures
    const failures = results.filter(r => r.status === 'rejected');
    if (failures.length > 0) {
      logger.error(`${failures.length} hub re-subscriptions failed`);
      // Don't throw - allow partial success
    }
  }

  /**
   * Validate that all subscriptions are receiving events
   * Called 30 seconds after reconnection
   */
  validateSubscriptions(): ValidationResult {
    const now = Date.now();
    const validationThreshold = 30000; // 30 seconds
    const staleSubscriptions: Subscription[] = [];

    for (const subscription of this.subscriptions.values()) {
      // If subscription has never received an event, mark as stale
      if (subscription.lastEventAt === null) {
        // Exception: If subscription registered less than 30 seconds ago, skip
        if (now - subscription.registeredAt < validationThreshold) {
          continue;
        }
        staleSubscriptions.push(subscription);
      }
      // If subscription hasn't received event in last 30 seconds, mark as stale
      else if (now - subscription.lastEventAt > validationThreshold) {
        staleSubscriptions.push(subscription);
      }
    }

    if (staleSubscriptions.length > 0) {
      logger.warn('Stale subscriptions detected', {
        count: staleSubscriptions.length,
        subscriptions: staleSubscriptions.map(s => ({
          id: s.id,
          eventName: s.eventName,
          lastEventAt: s.lastEventAt,
          timeSinceLastEvent: s.lastEventAt ? now - s.lastEventAt : null
        }))
      });
    }

    return {
      isValid: staleSubscriptions.length === 0,
      totalSubscriptions: this.subscriptions.size,
      activeSubscriptions: this.subscriptions.size - staleSubscriptions.length,
      staleSubscriptions,
      hubSubscriptionFailures: Array.from(this.hubSubscriptions.values())
        .filter(s => s.state === SubscriptionState.FAILED)
    };
  }
}
```

### Integration with Reconnection Flow

```typescript
// In SignalRConnectionManager.onreconnected()
connection.onreconnected(async (connectionId) => {
  logger.info('SignalR reconnected, re-establishing subscriptions');

  // 1. Re-subscribe to all events
  await eventSubscriptionManager.resubscribeAll();

  // 2. Trigger state reconciliation (see STATE_RECONCILIATION_SPEC.md)
  await stateReconciliation.reconcile();

  // 3. Wait 30 seconds, then validate subscriptions
  setTimeout(() => {
    const validation = eventSubscriptionManager.validateSubscriptions();

    if (!validation.isValid) {
      logger.error('Subscription validation failed', validation);

      // Notify user
      uiManager.showWarning(
        `${validation.staleSubscriptions.length} event subscription(s) may not be working. Some updates may be delayed.`
      );

      // Attempt re-subscription for failed subscriptions
      eventSubscriptionManager.retryFailedSubscriptions();
    } else {
      logger.info('All subscriptions validated successfully');
    }
  }, 30000);
});
```

---

## Common Subscription Patterns

### Position Updates

```typescript
// Subscribe to position updates
const positionUpdateSubId = eventSubscriptionManager.subscribe(
  'PositionUpdate',
  (positionData: PositionUpdateData) => {
    logger.debug('Position update received', positionData);

    // Update local position cache
    positionStore.updatePosition(positionData.position);

    // Evaluate risk rules
    riskEngine.evaluatePosition(positionData.position);

    // Update UI
    uiManager.updatePositionDisplay(positionData.position);
  }
);
```

### Order Updates

```typescript
// Subscribe to order updates
const orderUpdateSubId = eventSubscriptionManager.subscribe(
  'OrderUpdate',
  (orderData: OrderUpdateData) => {
    logger.debug('Order update received', orderData);

    // Update local order cache
    orderStore.updateOrder(orderData.order);

    // If order filled, update positions
    if (orderData.order.state === OrderState.FILLED) {
      positionStore.handleOrderFilled(orderData.order);
    }

    // Update UI
    uiManager.updateOrderDisplay(orderData.order);
  }
);
```

### Quote Updates (with Symbol Subscription)

```typescript
// Subscribe to quote events (client-side)
const quoteUpdateSubId = eventSubscriptionManager.subscribe(
  'QuoteUpdate',
  (quoteData: QuoteUpdateData) => {
    logger.debug('Quote update received', quoteData);

    // Update quote cache
    quoteStore.updateQuote(quoteData.quote);

    // Recalculate position PnL
    positionStore.recalculatePnL(quoteData.quote.symbol);

    // Update UI
    uiManager.updateQuoteDisplay(quoteData.quote);
  }
);

// Subscribe to specific symbol (server-side)
const symbolSubId = await hubSubscriptionManager.subscribeHub(
  'SubscribeToSymbol',
  ['EURUSD'],
  'symbol'
);

// Later, unsubscribe from symbol
await hubSubscriptionManager.unsubscribeHub(symbolSubId, 'UnsubscribeFromSymbol');
```

### Trade Execution Events

```typescript
// Subscribe to trade executions
const tradeExecutionSubId = eventSubscriptionManager.subscribe(
  'TradeExecution',
  (tradeData: TradeExecutionData) => {
    logger.info('Trade execution received', tradeData);

    // Record trade in database
    tradeStore.recordTrade(tradeData);

    // Update position and realized PnL
    positionStore.applyTradeExecution(tradeData);

    // Show notification to user
    uiManager.showNotification({
      type: 'success',
      title: 'Trade Executed',
      message: `${tradeData.side} ${tradeData.volume} ${tradeData.symbol} @ ${tradeData.price}`
    });
  }
);
```

---

## Configuration Schema

```yaml
signalr:
  subscriptions:
    # Automatic re-subscription after reconnection
    autoResubscribe: true

    # Validate subscriptions after reconnection
    validateAfterReconnection: true

    # Time to wait before validating subscriptions (milliseconds)
    validationDelay: 30000  # 30 seconds

    # Threshold for considering subscription stale (no events received)
    staleThreshold: 30000  # 30 seconds

    # Retry failed subscriptions
    retryFailedSubscriptions: true

    # Maximum retry attempts for failed subscriptions
    maxRetryAttempts: 3

    # Delay between retry attempts (milliseconds)
    retryDelay: 5000  # 5 seconds

  logging:
    # Log all subscription registrations
    logSubscriptions: true

    # Log all event receptions (can be very verbose)
    logEventReceptions: false

    # Log subscription validation results
    logValidation: true
```

---

## Implementation Checklist

### Phase 1: Event Subscription Management
- [ ] Implement EventSubscriptionManager class
- [ ] Implement subscribe() method with handler wrapping
- [ ] Implement unsubscribe() method
- [ ] Implement subscription state tracking
- [ ] Implement getActiveSubscriptions() query method
- [ ] Add logging for all subscription operations

### Phase 2: Hub Subscription Management
- [ ] Implement HubSubscriptionManager class
- [ ] Implement subscribeHub() method for server-side subscriptions
- [ ] Implement unsubscribeHub() method
- [ ] Track hub subscription state
- [ ] Handle hub subscription failures gracefully

### Phase 3: Re-subscription Logic
- [ ] Implement resubscribeAll() method
- [ ] Implement resubscribeHubMethods() for server-side subscriptions
- [ ] Integrate with SignalRConnectionManager.onreconnected()
- [ ] Handle partial re-subscription failures
- [ ] Test re-subscription after reconnection

### Phase 4: Subscription Validation
- [ ] Implement validateSubscriptions() method
- [ ] Detect stale subscriptions (no events in 30 seconds)
- [ ] Detect failed hub subscriptions
- [ ] Implement retryFailedSubscriptions() method
- [ ] Notify user of validation failures

### Phase 5: Common Subscription Patterns
- [ ] Implement PositionUpdate subscription
- [ ] Implement OrderUpdate subscription
- [ ] Implement QuoteUpdate subscription with symbol subscription
- [ ] Implement TradeExecution subscription
- [ ] Implement BalanceUpdate subscription (if available)

### Phase 6: Testing
- [ ] Unit test: Subscription registration and unregistration
- [ ] Unit test: Event handler execution
- [ ] Unit test: Multiple handlers for same event
- [ ] Integration test: Re-subscription after reconnection
- [ ] Integration test: Hub method re-subscription
- [ ] Integration test: Subscription validation
- [ ] Integration test: Failed subscription retry
- [ ] Test: Event handler errors don't crash application

---

## Validation Criteria

### Functional Validation

**VC-1: Subscription Registration**
- ✅ Events can be subscribed with handler functions
- ✅ Subscription returns unique ID
- ✅ Multiple handlers can be registered for same event
- ✅ Handlers execute in registration order

**VC-2: Event Reception**
- ✅ Subscribed events are received and handled correctly
- ✅ Event data is passed to handlers
- ✅ Handler errors don't prevent other handlers from executing
- ✅ Subscription state updates to ACTIVE after first event

**VC-3: Re-subscription**
- ✅ All client-side subscriptions persist after reconnection
- ✅ All server-side hub subscriptions re-invoked after reconnection
- ✅ Re-subscription completes within 2 seconds
- ✅ Events resume flowing after re-subscription

**VC-4: Validation**
- ✅ Stale subscriptions detected after 30 seconds without events
- ✅ Failed hub subscriptions detected and reported
- ✅ User notified of subscription failures
- ✅ Failed subscriptions automatically retried

**VC-5: Unsubscription**
- ✅ Subscriptions can be removed by ID
- ✅ Removed subscriptions stop receiving events
- ✅ Hub unsubscription methods called when available

### Performance Validation

**PV-1: Event Handling Speed**
- ✅ Event handlers execute in < 100ms
- ✅ Multiple handlers don't cause significant delay
- ✅ Re-subscription completes in < 2 seconds

### Reliability Validation

**RV-1: Subscription Persistence**
- ✅ Subscriptions persist across reconnections
- ✅ No subscriptions lost during reconnection
- ✅ Event handlers not garbage collected

**RV-2: Error Handling**
- ✅ Handler errors logged but don't crash application
- ✅ Failed re-subscriptions logged and retried
- ✅ Validation failures handled gracefully

---

## Integration Points

### Dependencies
- **SignalRConnectionManager** (SIGNALR-001): Connection lifecycle, triggers re-subscription
- **HubConnection**: SignalR connection for event registration
- **Logger**: Subscription operation logging
- **UIManager**: Subscription failure notifications

### Used By
- **PositionStore**: Receives PositionUpdate events
- **OrderStore**: Receives OrderUpdate events
- **QuoteStore**: Receives QuoteUpdate events
- **RiskEngine**: Receives events for rule evaluation

---

## References

- **SIGNALR_RECONNECTION_SPEC.md**: Reconnection triggers re-subscription
- **STATE_RECONCILIATION_SPEC.md**: Reconciliation after re-subscription
- **Microsoft SignalR Documentation**: https://docs.microsoft.com/en-us/aspnet/core/signalr/javascript-client

---

**End of Specification**
