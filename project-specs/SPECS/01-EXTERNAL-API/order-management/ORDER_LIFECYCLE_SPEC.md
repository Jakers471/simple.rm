# Order Lifecycle Specification

**doc_id:** ORDER-005
**version:** 1.0
**status:** DRAFT
**addresses:** Complete order state machine and lifecycle management
**created:** 2025-10-22
**category:** Order Management / State Management

---

## Overview

This specification defines the complete order lifecycle from creation through terminal states, including all state transitions, event triggers, data requirements, and cleanup procedures. The order lifecycle encompasses order placement, acknowledgment, fills, modifications, cancellations, and terminal state handling.

**Problem Statement:**
- What are all possible order states?
- What triggers state transitions?
- Which states are terminal vs transient?
- How are state changes persisted and communicated?
- When is order cleanup performed?

**Solution:**
Comprehensive state machine with clearly defined states, transitions, events, validation rules, and terminal state handling with automatic cleanup.

---

## Requirements

### Functional Requirements

**FR-001: Complete State Machine**
- MUST define all possible order states
- MUST define all valid state transitions
- MUST define transition triggers (events)
- MUST validate transitions before applying
- MUST reject invalid state transitions

**FR-002: State Persistence**
- MUST persist state changes to database
- MUST maintain state change history
- MUST timestamp all state transitions
- MUST record transition reasons
- MUST support state rollback on error

**FR-003: Event Emission**
- MUST emit event on every state transition
- MUST include previous and new state
- MUST include transition trigger
- MUST include order details
- MUST support event subscribers

**FR-004: Terminal State Handling**
- MUST identify terminal states clearly
- MUST prevent transitions from terminal states
- MUST trigger cleanup on terminal state
- MUST archive terminal orders
- MUST emit completion metrics

**FR-005: State Query & Monitoring**
- MUST support querying current order state
- MUST support querying state history
- MUST track time in each state
- MUST calculate state metrics
- MUST detect stuck orders

### Non-Functional Requirements

**NFR-001: Performance**
- State transition MUST be < 10ms
- State persistence MUST be async
- State query MUST be < 5ms
- Event emission MUST NOT block transition
- Cleanup MUST NOT impact active orders

**NFR-002: Reliability**
- Zero lost state transitions
- Atomic state changes (all or nothing)
- Consistent state across restarts
- State recovery after crash
- Audit trail preservation

**NFR-003: Observability**
- MUST log all state transitions
- MUST track transition frequency
- MUST detect abnormal patterns
- MUST alert on stuck orders
- MUST provide state dashboards

---

## Order States

### State Definitions

```yaml
OrderStates:

  # Initial States
  DRAFT:
    description: "Order created but not yet submitted"
    terminal: false
    canModify: true
    canCancel: true
    nextStates: [PENDING, CANCELLED]

  PENDING:
    description: "Order validation in progress"
    terminal: false
    canModify: false
    canCancel: true
    nextStates: [SUBMITTED, REJECTED, CANCELLED]

  SUBMITTED:
    description: "Order sent to broker/exchange"
    terminal: false
    canModify: true
    canCancel: true
    nextStates: [ACKNOWLEDGED, REJECTED, CANCELLED]

  # Active States
  ACKNOWLEDGED:
    description: "Order confirmed by broker"
    terminal: false
    canModify: true
    canCancel: true
    nextStates: [PARTIALLY_FILLED, FILLED, CANCELLED, EXPIRED]

  PARTIALLY_FILLED:
    description: "Order partially executed"
    terminal: false
    canModify: false
    canCancel: true
    nextStates: [FILLED, CANCELLED, PARTIAL_FILL_TIMEOUT]

  # Terminal States
  FILLED:
    description: "Order fully executed"
    terminal: true
    canModify: false
    canCancel: false
    nextStates: []

  CANCELLED:
    description: "Order cancelled (user or system)"
    terminal: true
    canModify: false
    canCancel: false
    nextStates: []

  REJECTED:
    description: "Order rejected by broker/risk rules"
    terminal: true
    canModify: false
    canCancel: false
    nextStates: []

  EXPIRED:
    description: "Order expired (time-in-force)"
    terminal: true
    canModify: false
    canCancel: false
    nextStates: []

  PARTIAL_FILL_TIMEOUT:
    description: "Partial fill timeout reached"
    terminal: true
    canModify: false
    canCancel: false
    nextStates: []

  # Error States
  FAILED:
    description: "Order processing failed"
    terminal: true
    canModify: false
    canCancel: false
    nextStates: []
```

---

## State Machine Diagram

```
                    +--------+
                    | DRAFT  |
                    +--------+
                         |
                   [submit_order]
                         |
                         v
                   +-----------+
                   | PENDING   |
                   +-----------+
                    /    |    \
      [validation_pass] [validation_fail] [user_cancel]
                  /      |        \
                 v       v         v
          +-----------+ +----------+ +-----------+
          | SUBMITTED | | REJECTED | | CANCELLED |
          +-----------+ +----------+ +-----------+
                 |           ^            ^
           [broker_ack]      |            |
                 |           |            |
                 v           |            |
          +---------------+  |            |
          | ACKNOWLEDGED  |  |            |
          +---------------+  |            |
            /      |      \  |            |
  [first_fill] [full_fill] [cancel] [reject]
          /        |        \              |
         v         v         v              v
  +--------+  +--------+ +-----------+ +----------+
  |PARTIAL |  | FILLED | | CANCELLED | | REJECTED |
  | FILLED |  +--------+ +-----------+ +----------+
  +--------+       |           |             |
    /    |    \    |           |             |
   /     |     \   |           |             |
  v      v      v  v           v             v
[more]  [timeout] [complete]  [Terminal States]
fills

Legend:
  [event_trigger] - Causes transition
  UPPERCASE - State name
  Terminal States - No outgoing transitions
```

---

## State Transitions

### Transition Rules

```python
from enum import Enum
from typing import List, Optional

class OrderState(Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    PARTIAL_FILL_TIMEOUT = "PARTIAL_FILL_TIMEOUT"
    FAILED = "FAILED"


class TransitionRule:
    """
    Define valid state transitions.
    """
    VALID_TRANSITIONS = {
        OrderState.DRAFT: [
            OrderState.PENDING,
            OrderState.CANCELLED
        ],
        OrderState.PENDING: [
            OrderState.SUBMITTED,
            OrderState.REJECTED,
            OrderState.CANCELLED
        ],
        OrderState.SUBMITTED: [
            OrderState.ACKNOWLEDGED,
            OrderState.REJECTED,
            OrderState.CANCELLED
        ],
        OrderState.ACKNOWLEDGED: [
            OrderState.PARTIALLY_FILLED,
            OrderState.FILLED,
            OrderState.CANCELLED,
            OrderState.EXPIRED
        ],
        OrderState.PARTIALLY_FILLED: [
            OrderState.FILLED,
            OrderState.CANCELLED,
            OrderState.PARTIAL_FILL_TIMEOUT
        ],
        # Terminal states have no outgoing transitions
        OrderState.FILLED: [],
        OrderState.CANCELLED: [],
        OrderState.REJECTED: [],
        OrderState.EXPIRED: [],
        OrderState.PARTIAL_FILL_TIMEOUT: [],
        OrderState.FAILED: []
    }

    TERMINAL_STATES = {
        OrderState.FILLED,
        OrderState.CANCELLED,
        OrderState.REJECTED,
        OrderState.EXPIRED,
        OrderState.PARTIAL_FILL_TIMEOUT,
        OrderState.FAILED
    }

    @classmethod
    def is_valid_transition(
        cls,
        from_state: OrderState,
        to_state: OrderState
    ) -> bool:
        """
        Check if state transition is valid.
        """
        if from_state not in cls.VALID_TRANSITIONS:
            return False

        return to_state in cls.VALID_TRANSITIONS[from_state]

    @classmethod
    def is_terminal(cls, state: OrderState) -> bool:
        """
        Check if state is terminal.
        """
        return state in cls.TERMINAL_STATES

    @classmethod
    def get_valid_next_states(
        cls,
        current_state: OrderState
    ) -> List[OrderState]:
        """
        Get list of valid next states.
        """
        return cls.VALID_TRANSITIONS.get(current_state, [])
```

---

## State Transition Implementation

```python
from dataclasses import dataclass
from typing import Optional, Callable
import time

@dataclass
class StateTransition:
    """
    Represents a state transition event.
    """
    order_id: str
    from_state: OrderState
    to_state: OrderState
    trigger: str              # What caused the transition
    timestamp: int            # Milliseconds since epoch
    metadata: dict            # Additional context
    reason: Optional[str]     # Human-readable reason


class OrderStateMachine:
    """
    Manage order state transitions with validation and events.
    """
    def __init__(self):
        self.transition_listeners: List[Callable] = []
        self.state_history: Dict[str, List[StateTransition]] = {}

    def transition(
        self,
        order_id: str,
        current_state: OrderState,
        new_state: OrderState,
        trigger: str,
        reason: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Attempt state transition with validation.

        Returns:
            True if transition successful, False otherwise
        """
        # 1. Validate transition
        if not TransitionRule.is_valid_transition(current_state, new_state):
            log_error(
                f"Invalid transition: {current_state} -> {new_state} "
                f"for order {order_id}"
            )
            return False

        # 2. Check if already in terminal state
        if TransitionRule.is_terminal(current_state):
            log_warning(
                f"Cannot transition from terminal state {current_state} "
                f"for order {order_id}"
            )
            return False

        # 3. Create transition record
        transition = StateTransition(
            order_id=order_id,
            from_state=current_state,
            to_state=new_state,
            trigger=trigger,
            timestamp=int(time.time() * 1000),
            metadata=metadata or {},
            reason=reason
        )

        # 4. Persist transition (async)
        self._persist_transition(transition)

        # 5. Update order state (atomic)
        self._update_order_state(order_id, new_state)

        # 6. Record in history
        if order_id not in self.state_history:
            self.state_history[order_id] = []
        self.state_history[order_id].append(transition)

        # 7. Emit transition event
        self._emit_transition_event(transition)

        # 8. Notify listeners
        for listener in self.transition_listeners:
            try:
                listener(transition)
            except Exception as e:
                log_error(f"Transition listener error: {e}")

        # 9. Handle terminal state
        if TransitionRule.is_terminal(new_state):
            self._handle_terminal_state(order_id, new_state)

        log_info(
            f"Order {order_id}: {current_state} -> {new_state} "
            f"(trigger: {trigger})"
        )

        return True

    def _persist_transition(self, transition: StateTransition):
        """
        Persist transition to database (async).
        """
        # Async database write
        async_db_write(
            table="order_state_transitions",
            record={
                'order_id': transition.order_id,
                'from_state': transition.from_state.value,
                'to_state': transition.to_state.value,
                'trigger': transition.trigger,
                'timestamp': transition.timestamp,
                'reason': transition.reason,
                'metadata': json.dumps(transition.metadata)
            }
        )

    def _update_order_state(self, order_id: str, new_state: OrderState):
        """
        Update order's current state (atomic).
        """
        update_order(
            order_id=order_id,
            updates={'state': new_state.value, 'updated_at': time.time()}
        )

    def _emit_transition_event(self, transition: StateTransition):
        """
        Emit state transition event for subscribers.
        """
        event = {
            'event_type': 'order_state_changed',
            'order_id': transition.order_id,
            'from_state': transition.from_state.value,
            'to_state': transition.to_state.value,
            'trigger': transition.trigger,
            'timestamp': transition.timestamp,
            'reason': transition.reason
        }

        emit_event('order_lifecycle', event)

    def _handle_terminal_state(
        self,
        order_id: str,
        terminal_state: OrderState
    ):
        """
        Handle order reaching terminal state.
        """
        # 1. Record completion time
        update_order(
            order_id=order_id,
            updates={'completed_at': time.time()}
        )

        # 2. Emit completion metrics
        emit_metric(
            'order_completed',
            labels={
                'state': terminal_state.value,
                'order_id': order_id
            }
        )

        # 3. Trigger cleanup after delay (e.g., 24 hours)
        schedule_cleanup(order_id, delay_hours=24)

        # 4. Archive order data
        schedule_archival(order_id, delay_hours=48)

        log_info(f"Order {order_id} reached terminal state: {terminal_state}")

    def get_state_history(self, order_id: str) -> List[StateTransition]:
        """
        Get complete state history for order.
        """
        return self.state_history.get(order_id, [])

    def get_time_in_state(
        self,
        order_id: str,
        state: OrderState
    ) -> Optional[int]:
        """
        Calculate time spent in specific state (milliseconds).
        """
        history = self.get_state_history(order_id)

        time_in_state = 0
        enter_time = None

        for i, transition in enumerate(history):
            if transition.to_state == state:
                enter_time = transition.timestamp

            if enter_time and (
                i + 1 < len(history) and
                history[i + 1].from_state == state
            ):
                # Exited the state
                exit_time = history[i + 1].timestamp
                time_in_state += (exit_time - enter_time)
                enter_time = None

        # If still in state
        if enter_time:
            time_in_state += (int(time.time() * 1000) - enter_time)

        return time_in_state if time_in_state > 0 else None
```

---

## Event Triggers

### Trigger Definitions

```yaml
EventTriggers:

  # User Actions
  user_submit_order:
    triggerState: DRAFT -> PENDING
    source: "user"
    description: "User submits order for placement"

  user_cancel_order:
    triggerStates:
      - PENDING -> CANCELLED
      - SUBMITTED -> CANCELLED
      - ACKNOWLEDGED -> CANCELLED
      - PARTIALLY_FILLED -> CANCELLED
    source: "user"
    description: "User cancels order"

  user_modify_order:
    triggerStates:
      - DRAFT -> DRAFT
      - SUBMITTED -> SUBMITTED
      - ACKNOWLEDGED -> ACKNOWLEDGED
    source: "user"
    description: "User modifies order parameters"

  # System Events
  validation_pass:
    triggerState: PENDING -> SUBMITTED
    source: "system"
    description: "Order passed validation checks"

  validation_fail:
    triggerState: PENDING -> REJECTED
    source: "system"
    description: "Order failed validation"

  api_acknowledged:
    triggerState: SUBMITTED -> ACKNOWLEDGED
    source: "broker_api"
    description: "Broker acknowledged order"

  api_rejected:
    triggerStates:
      - PENDING -> REJECTED
      - SUBMITTED -> REJECTED
    source: "broker_api"
    description: "Broker rejected order"

  # Fill Events
  first_fill_received:
    triggerState: ACKNOWLEDGED -> PARTIALLY_FILLED
    source: "signalr"
    description: "First fill event received"

  subsequent_fill:
    triggerState: PARTIALLY_FILLED -> PARTIALLY_FILLED
    source: "signalr"
    description: "Additional fill received"

  order_complete:
    triggerStates:
      - ACKNOWLEDGED -> FILLED
      - PARTIALLY_FILLED -> FILLED
    source: "signalr"
    description: "Order fully filled"

  # Timeout Events
  partial_fill_timeout:
    triggerState: PARTIALLY_FILLED -> PARTIAL_FILL_TIMEOUT
    source: "system"
    description: "Partial fill timeout reached"

  order_expired:
    triggerState: ACKNOWLEDGED -> EXPIRED
    source: "system"
    description: "Order expired (time-in-force)"

  # Risk Events
  risk_rule_cancel:
    triggerStates:
      - ACKNOWLEDGED -> CANCELLED
      - PARTIALLY_FILLED -> CANCELLED
    source: "risk_rule"
    description: "Risk rule triggered cancellation"

  risk_rule_reject:
    triggerState: PENDING -> REJECTED
    source: "risk_rule"
    description: "Risk rule rejected order"

  # Error Events
  processing_error:
    triggerState: ANY -> FAILED
    source: "system"
    description: "Unrecoverable processing error"
```

---

## Terminal State Cleanup

### Cleanup Strategy

```python
class OrderCleanup:
    """
    Manage cleanup of orders in terminal states.
    """
    def __init__(self):
        self.cleanup_delay_hours = 24
        self.archival_delay_hours = 48
        self.deletion_delay_days = 90

    def schedule_cleanup(self, order_id: str):
        """
        Schedule cleanup for order after delay.
        """
        # 1. Schedule hot data cleanup (24 hours)
        schedule_task(
            task=self.cleanup_hot_data,
            args=[order_id],
            delay_hours=self.cleanup_delay_hours
        )

        # 2. Schedule archival (48 hours)
        schedule_task(
            task=self.archive_order,
            args=[order_id],
            delay_hours=self.archival_delay_hours
        )

        # 3. Schedule deletion (90 days)
        schedule_task(
            task=self.delete_archived_order,
            args=[order_id],
            delay_days=self.deletion_delay_days
        )

    def cleanup_hot_data(self, order_id: str):
        """
        Clean up real-time tracking data (24 hours after completion).
        """
        # Remove from active order cache
        remove_from_cache(order_id)

        # Remove from SignalR subscriptions
        unsubscribe_order_events(order_id)

        # Remove from timeout timers
        cancel_order_timers(order_id)

        # Remove from idempotency cache (if expired)
        cleanup_idempotency_entries(order_id)

        log_info(f"Cleaned up hot data for order: {order_id}")

    def archive_order(self, order_id: str):
        """
        Archive order to cold storage (48 hours after completion).
        """
        # Retrieve complete order record
        order = get_order_complete(order_id)

        # Archive to cold storage (e.g., S3, data warehouse)
        archive_to_cold_storage(
            order=order,
            storage_path=f"orders/archive/{order.completed_year}/{order.completed_month}/"
        )

        # Update database to mark as archived
        update_order(
            order_id=order_id,
            updates={'archived': True, 'archived_at': time.time()}
        )

        log_info(f"Archived order: {order_id}")

    def delete_archived_order(self, order_id: str):
        """
        Delete archived order (90 days after completion).
        """
        # Verify archival complete
        order = get_order(order_id)

        if not order.archived:
            log_error(f"Cannot delete non-archived order: {order_id}")
            return

        # Delete from primary database
        delete_order(order_id)

        # Keep archived copy in cold storage (for compliance)

        log_info(f"Deleted order from primary database: {order_id}")
```

---

## Configuration Schema

```yaml
orderLifecycle:
  states:
    # State configuration
    enableAllStates: true
    terminalStates: [FILLED, CANCELLED, REJECTED, EXPIRED, PARTIAL_FILL_TIMEOUT, FAILED]

  transitions:
    # Validation
    validateTransitions: true
    rejectInvalidTransitions: true
    logInvalidAttempts: true

    # Persistence
    persistTransitions: true
    asyncPersistence: true
    transitionHistoryRetention: 90  # Days

  events:
    # Event emission
    emitTransitionEvents: true
    emitToSignalR: true
    emitToWebhooks: false
    eventBatchSize: 100

  cleanup:
    # Cleanup schedule
    enabled: true
    hotDataCleanupDelay: 24      # Hours
    archivalDelay: 48            # Hours
    deletionDelay: 90            # Days

    # Archival
    archiveToS3: true
    archiveBucket: "orders-archive"
    compressionEnabled: true

  monitoring:
    # Observability
    trackTimeInState: true
    detectStuckOrders: true
    stuckOrderThreshold: 3600    # Seconds (1 hour)
    alertOnStuckOrders: true
```

---

## Implementation Checklist

- [ ] Define all order states
- [ ] Build state transition validation
- [ ] Implement OrderStateMachine
- [ ] Add state persistence
- [ ] Implement transition history
- [ ] Add event emission
- [ ] Build terminal state detection
- [ ] Implement cleanup scheduling
- [ ] Add archival system
- [ ] Build state query API
- [ ] Add time-in-state calculation
- [ ] Implement stuck order detection
- [ ] Write unit tests for transitions
- [ ] Write integration tests
- [ ] Test cleanup and archival

---

## Validation Criteria

### Valid Transitions Only
**Target:** 100% transition validation
- Invalid transitions rejected
- Terminal states prevent outgoing transitions
- State machine rules enforced

### Complete Audit Trail
**Target:** Zero lost state changes
- All transitions persisted
- History queryable
- Timestamps accurate

---

## Metrics & Monitoring

```yaml
Metrics:
  - name: "order_state_transitions_total"
    type: counter
    labels: [from_state, to_state, trigger]

  - name: "order_time_in_state_ms"
    type: histogram
    labels: [state]

  - name: "order_stuck_total"
    type: counter
    labels: [stuck_state]

  - name: "order_terminal_state_reached_total"
    type: counter
    labels: [terminal_state]

Alerts:
  - name: "StuckOrdersDetected"
    condition: "order_stuck_total > 0"
    severity: "HIGH"

  - name: "HighRejectionRate"
    condition: "rate(order_terminal_state_reached_total{terminal_state='REJECTED'}[5m]) > 10"
    severity: "MEDIUM"
```

---

## References

1. **Related Specifications**
   - ORDER_STATUS_VERIFICATION_SPEC.md
   - PARTIAL_FILL_TRACKING_SPEC.md
   - CONCURRENCY_HANDLING_SPEC.md
   - ORDER_IDEMPOTENCY_SPEC.md

---

**Document Status:** DRAFT - Ready for Technical Review
