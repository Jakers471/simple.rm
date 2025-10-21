---
doc_id: PIPE-001
version: 1.0
last_updated: 2025-10-21
dependencies: [ARCH-V2.2, MOD-001, MOD-002, MOD-003, MOD-004, MOD-005, MOD-006, MOD-007, MOD-008, MOD-009, API-INT-001]
---

# Event Processing Pipeline

**Purpose:** Complete event flow from TopstepX SignalR → State Updates → Lockout Check → Rule Routing → Enforcement

**File Coverage:** `src/core/event_router.py`, `src/api/signalr_listener.py`

---

## 🎯 Core Architecture Decisions

### **1. Event Processing Order (CRITICAL)**
```
TopstepX Event → Update State FIRST → Check Lockout → Route to Rules → Enforcement
                    ↑
                    MUST happen before rule checks
```

**Why state updates BEFORE rule checks:**
- Rules need current state to make decisions
- Avoids race conditions (stale position counts, P&L, etc.)
- Ensures rules always see the most recent data

### **2. Lockout Gating (CRITICAL)**
```
Check is_locked_out() BEFORE routing events to rules
```

**Why:**
- Performance: Don't waste CPU running rules if account is locked
- Correctness: Locked accounts shouldn't trigger more enforcement
- User experience: No noise in logs from locked accounts

### **3. Unrealized P&L Checks (CRITICAL)**
```
ONLY check unrealized P&L on events (position/quote changes)
DO NOT poll in background
```

**Why:**
- Event-driven = only calculate when something changes
- Background polling wastes CPU (checking same values repeatedly)
- Quote events trigger frequently enough (1-4 per second per instrument)

---

## 📊 Complete Event Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TOPSTEPX SIGNALR HUBS                            │
│  User Hub:   wss://rtc.topstepx.com/hubs/user                          │
│  Market Hub: wss://rtc.topstepx.com/hubs/market                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
                ┌─────────────────┴─────────────────┐
                │                                   │
                ▼                                   ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│  GatewayUserTrade            │   │  MarketQuote                 │
│  GatewayUserPosition         │   │  (real-time price updates)   │
│  GatewayUserOrder            │   │                              │
│  GatewayUserAccount          │   │  Received by:                │
│                              │   │  src/api/market_hub.py       │
│  Received by:                │   │                              │
│  src/api/signalr_listener.py │   │  Updates:                    │
└────────────────┬─────────────┘   │  - MOD-006 (Quote Tracker)   │
                 │                 └────────────────┬─────────────┘
                 │                                  │
                 │ Raw Event Payload                │ Quote Update
                 │                                  │
                 ▼                                  │
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: EVENT PARSING & VALIDATION                                    │
│  src/api/signalr_listener.py / market_hub.py                           │
│                                                                         │
│  - Parse JSON payload                                                  │
│  - Validate required fields (accountId, contractId, etc.)              │
│  - Log raw event to logs/api.log                                       │
│  - Convert to internal Event dict                                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  │ Parsed Event Dict
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 2: STATE UPDATE (BEFORE RULE ROUTING) ⭐ CRITICAL                │
│  src/core/event_router.py                                              │
│                                                                         │
│  Event Type → State Update:                                            │
│                                                                         │
│  GatewayUserTrade → MOD-005 (PNL Tracker)                              │
│    - pnl_tracker.add_trade_pnl(account_id, pnl)                        │
│    - MOD-008 (Trade Counter)                                           │
│      trade_counter.record_trade(account_id, timestamp)                 │
│                                                                         │
│  GatewayUserPosition → MOD-009 (State Manager)                         │
│    - state_manager.update_position(position)                           │
│                                                                         │
│  GatewayUserOrder → MOD-009 (State Manager)                            │
│    - state_manager.update_order(order)                                 │
│                                                                         │
│  MarketQuote → MOD-006 (Quote Tracker)                                 │
│    - quote_tracker.update_quote(contract_id, bid, ask)                 │
│                                                                         │
│  **State is NOW current - rules will see updated values**              │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  │ State Updated
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 3: LOCKOUT GATING CHECK ⭐ CRITICAL                              │
│  src/core/event_router.py                                              │
│                                                                         │
│  if lockout_manager.is_locked_out(account_id):                         │
│      logger.debug(f"Account {account_id} locked - skipping rules")     │
│      return  # STOP - don't route to rules                             │
│                                                                         │
│  **Performance optimization: Don't run rules if account is locked**    │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  │ Account NOT Locked
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 4: RULE ROUTING                                                  │
│  src/core/event_router.py                                              │
│                                                                         │
│  Route event to relevant rules based on event type:                    │
│                                                                         │
│  GatewayUserTrade:                                                     │
│    → RULE-003 (DailyRealizedLoss)    - Check daily P&L                │
│    → RULE-006 (TradeFrequencyLimit)  - Check trade count/rate         │
│    → RULE-007 (CooldownAfterLoss)    - Check if loss trade            │
│    → RULE-012 (TradeManagement)      - Auto stop-loss enforcement      │
│                                                                         │
│  GatewayUserPosition:                                                  │
│    → RULE-001 (MaxContracts)         - Check total net contracts      │
│    → RULE-002 (MaxContractsPerInstrument) - Check per-instrument      │
│    → RULE-004 (DailyUnrealizedLoss)  - Check unrealized P&L           │
│    → RULE-005 (MaxUnrealizedProfit)  - Check unrealized P&L           │
│    → RULE-008 (NoStopLossGrace)      - Check if position has stop     │
│    → RULE-009 (SessionBlockOutside)  - Check if session active        │
│    → RULE-011 (SymbolBlocks)         - Check if symbol allowed        │
│                                                                         │
│  GatewayUserOrder:                                                     │
│    → RULE-008 (NoStopLossGrace)      - Check if stop-loss exists      │
│    → RULE-011 (SymbolBlocks)         - Check if symbol allowed        │
│                                                                         │
│  MarketQuote (Quote Update):                                           │
│    → RULE-004 (DailyUnrealizedLoss)  - Recalc unrealized P&L          │
│    → RULE-005 (MaxUnrealizedProfit)  - Recalc unrealized P&L          │
│                                                                         │
│  GatewayUserAccount:                                                   │
│    → RULE-010 (AuthLossGuard)        - Check if auth event            │
│                                                                         │
│  **Each rule.check(event) called sequentially**                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  │ For Each Rule
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 5: RULE EXECUTION                                                │
│  src/rules/<rule_name>.py                                              │
│                                                                         │
│  rule.check(event):                                                    │
│    - Read current state (via MOD-005, MOD-006, MOD-009, etc.)          │
│    - Calculate breach condition                                        │
│    - Return EnforcementAction if breach detected                       │
│                                                                         │
│  Example (RULE-001 MaxContracts):                                      │
│    total_net = state_manager.get_position_count(account_id)            │
│    if total_net > config['limit']:                                     │
│        return EnforcementAction(                                       │
│            type="CLOSE_ALL_POSITIONS",                                 │
│            reason=f"MaxContracts breach ({total_net} > {limit})"       │
│        )                                                               │
│                                                                         │
│  Example (RULE-003 DailyRealizedLoss):                                 │
│    daily_pnl = pnl_tracker.get_daily_pnl(account_id)                   │
│    if daily_pnl <= config['limit']:                                    │
│        return EnforcementAction(                                       │
│            type="CLOSE_ALL_AND_LOCKOUT",                               │
│            lockout_until=next_reset_time                               │
│        )                                                               │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  │ EnforcementAction (if breach)
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 6: ENFORCEMENT EXECUTION                                         │
│  src/enforcement/enforcement_engine.py                                 │
│                                                                         │
│  if action is not None:                                                │
│      execute_enforcement(action)                                       │
│                                                                         │
│  Enforcement Types:                                                    │
│                                                                         │
│  1. CLOSE_ALL_POSITIONS (Trade-by-Trade rules)                         │
│     - MOD-001.close_all_positions(account_id)                          │
│     - Log enforcement                                                  │
│     - NO lockout                                                       │
│                                                                         │
│  2. CLOSE_ALL_AND_LOCKOUT (Hard lockout rules)                         │
│     - MOD-001.close_all_positions(account_id)                          │
│     - MOD-001.cancel_all_orders(account_id)                            │
│     - MOD-002.set_lockout(account_id, reason, until)                   │
│     - Log enforcement                                                  │
│                                                                         │
│  3. COOLDOWN (Timer lockout rules)                                     │
│     - MOD-001.close_all_positions(account_id)                          │
│     - MOD-001.cancel_all_orders(account_id)                            │
│     - MOD-002.set_cooldown(account_id, reason, duration_seconds)       │
│     - Log enforcement                                                  │
│                                                                         │
│  4. REJECT_ORDER (Pre-trade blocking)                                  │
│     - MOD-001.cancel_order(order_id)                                   │
│     - Log enforcement                                                  │
│     - NO lockout                                                       │
│                                                                         │
│  5. AUTO_STOP_LOSS (RULE-012 only)                                     │
│     - MOD-001.place_stop_loss_order(position)                          │
│     - Log enforcement                                                  │
│                                                                         │
│  **All enforcement actions call MOD-001 (no direct API calls)**        │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
                ┌─────────────────┴─────────────────┐
                │                                   │
                ▼                                   ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│  MOD-001: Enforcement        │   │  MOD-002: Lockout Manager    │
│  actions.py                  │   │  lockout_manager.py          │
│                              │   │                              │
│  - close_all_positions()     │   │  - set_lockout()             │
│  - close_position()          │   │  - set_cooldown()            │
│  - cancel_all_orders()       │   │  - Persist to SQLite         │
│  - place_stop_loss_order()   │   │  - Update in-memory state    │
│                              │   │                              │
│  (REST API calls)            │   │  (SYNC SQLite write)         │
└────────────────┬─────────────┘   └──────────────────────────────┘
                 │
                 │ REST API Calls
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  TOPSTEPX REST API                                                     │
│  POST /api/Position/closeContract                                      │
│  POST /api/Position/partialCloseContract                               │
│  POST /api/Order/cancel                                                │
│  POST /api/Order/placeOrder (for auto stop-loss)                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Event Type → Rule Mapping (Complete)

### **GatewayUserTrade (Full-Turn Trade Execution)**

**State Updates (BEFORE rule checks):**
```python
# MOD-005: PNL Tracker
if trade['profitAndLoss'] is not None:
    pnl_tracker.add_trade_pnl(trade['accountId'], trade['profitAndLoss'])

# MOD-008: Trade Counter
trade_counter.record_trade(trade['accountId'], trade['timestamp'])

# MOD-007: Contract Cache (lazy cache)
if trade['contractId'] not in contract_cache:
    contract_cache.fetch_and_cache(trade['contractId'])
```

**Rules Triggered:**
| Rule ID | Rule Name | What It Checks |
|---------|-----------|----------------|
| RULE-003 | DailyRealizedLoss | Daily realized P&L <= limit? |
| RULE-006 | TradeFrequencyLimit | Trades in window > max trades? |
| RULE-007 | CooldownAfterLoss | Was this trade a loss? |
| RULE-012 | TradeManagement | Does position need auto stop-loss? |

**Processing Order:**
1. Update MOD-005, MOD-008 state
2. Check lockout (skip rules if locked)
3. RULE-003 → RULE-006 → RULE-007 → RULE-012 (sequential)
4. Execute first breach enforcement (stop after first breach)

---

### **GatewayUserPosition (Position Opened/Closed/Updated)**

**State Updates (BEFORE rule checks):**
```python
# MOD-009: State Manager
if position['size'] == 0:
    state_manager.remove_position(position['id'])
else:
    state_manager.update_position(position)
```

**Rules Triggered:**
| Rule ID | Rule Name | What It Checks |
|---------|-----------|----------------|
| RULE-001 | MaxContracts | Total net contracts > limit? |
| RULE-002 | MaxContractsPerInstrument | Contracts for this instrument > limit? |
| RULE-004 | DailyUnrealizedLoss | Unrealized P&L <= limit? |
| RULE-005 | MaxUnrealizedProfit | Unrealized P&L >= limit? |
| RULE-008 | NoStopLossGrace | New position without stop-loss? |
| RULE-009 | SessionBlockOutside | Position opened outside session? |
| RULE-011 | SymbolBlocks | Position in blocked symbol? |

**Processing Order:**
1. Update MOD-009 state
2. Check lockout (skip rules if locked)
3. RULE-001 through RULE-011 (sequential)
4. Execute first breach enforcement

**Special Case: Unrealized P&L Calculation (RULE-004, RULE-005)**
```python
# Calculate unrealized P&L using current quotes
for position in state_manager.get_positions(account_id):
    quote = quote_tracker.get_quote(position['contractId'])
    if quote:
        unrealized_pnl += calculate_position_pnl(position, quote)
```

---

### **GatewayUserOrder (Order Placed/Canceled/Filled)**

**State Updates (BEFORE rule checks):**
```python
# MOD-009: State Manager
if order['state'] == OrderState.CANCELED or order['state'] == OrderState.FILLED:
    state_manager.remove_order(order['id'])
else:
    state_manager.update_order(order)
```

**Rules Triggered:**
| Rule ID | Rule Name | What It Checks |
|---------|-----------|----------------|
| RULE-008 | NoStopLossGrace | Position has stop-loss order? |
| RULE-011 | SymbolBlocks | Order for blocked symbol? |

**Processing Order:**
1. Update MOD-009 state
2. Check lockout (skip rules if locked)
3. RULE-008 → RULE-011 (sequential)
4. Execute first breach enforcement

---

### **MarketQuote (Real-Time Price Update)**

**State Updates (BEFORE rule checks):**
```python
# MOD-006: Quote Tracker
quote_tracker.update_quote(
    contract_id=quote['contractId'],
    bid=quote['bid'],
    ask=quote['ask'],
    last=quote['last']
)
```

**Rules Triggered:**
| Rule ID | Rule Name | What It Checks |
|---------|-----------|----------------|
| RULE-004 | DailyUnrealizedLoss | Unrealized P&L <= limit? (with new quote) |
| RULE-005 | MaxUnrealizedProfit | Unrealized P&L >= limit? (with new quote) |

**Processing Order:**
1. Update MOD-006 state
2. Check lockout (skip rules if locked)
3. RULE-004 → RULE-005 (sequential)
4. Execute first breach enforcement

**Why quotes trigger unrealized P&L checks:**
- Unrealized P&L = `(current_price - entry_price) * position_size * tick_value`
- When price changes, unrealized P&L changes
- Must check if new unrealized P&L breaches limits

**Frequency:**
- Quotes arrive 1-4 times per second per instrument
- Each quote triggers unrealized P&L recalculation for all positions in that instrument
- No background polling needed (event-driven)

---

### **GatewayUserAccount (Account State Change)**

**State Updates (BEFORE rule checks):**
```python
# No state updates for account events (informational only)
```

**Rules Triggered:**
| Rule ID | Rule Name | What It Checks |
|---------|-----------|----------------|
| RULE-010 | AuthLossGuard | Account authenticated (potential auth bypass)? |

**Processing Order:**
1. Check lockout (skip rules if locked)
2. RULE-010 only
3. Execute enforcement if auth event detected

---

## 🔄 Event Processing Implementation

### **Event Router (src/core/event_router.py)**

**Core routing logic:**
```python
class EventRouter:
    """Routes SignalR events to state updates and risk rules."""

    def __init__(self, state_manager, pnl_tracker, quote_tracker,
                 contract_cache, trade_counter, lockout_manager,
                 rule_engine):
        self.state_manager = state_manager
        self.pnl_tracker = pnl_tracker
        self.quote_tracker = quote_tracker
        self.contract_cache = contract_cache
        self.trade_counter = trade_counter
        self.lockout_manager = lockout_manager
        self.rule_engine = rule_engine

    def route_event(self, event_type: str, payload: dict):
        """
        Main event routing entry point.

        CRITICAL: State updates happen BEFORE rule checks.
        """
        logger.debug(f"Routing event: {event_type}")

        # STEP 1: Update state FIRST (before rule checks)
        self._update_state(event_type, payload)

        # STEP 2: Check if account is locked (skip rules if locked)
        account_id = payload.get('accountId')
        if account_id and self.lockout_manager.is_locked_out(account_id):
            logger.debug(f"Account {account_id} locked - skipping rule checks")
            return

        # STEP 3: Route to relevant rules
        self._route_to_rules(event_type, payload)

    def _update_state(self, event_type: str, payload: dict):
        """Update state based on event type."""

        if event_type == "GatewayUserTrade":
            # Update P&L tracker
            if payload.get('profitAndLoss') is not None:
                self.pnl_tracker.add_trade_pnl(
                    payload['accountId'],
                    payload['profitAndLoss']
                )

            # Update trade counter
            self.trade_counter.record_trade(
                payload['accountId'],
                payload['timestamp']
            )

            # Lazy cache contract metadata
            if payload['contractId'] not in self.contract_cache:
                self.contract_cache.fetch_and_cache(payload['contractId'])

        elif event_type == "GatewayUserPosition":
            # Update position state
            if payload['size'] == 0:
                self.state_manager.remove_position(payload['id'])
            else:
                self.state_manager.update_position(payload)

        elif event_type == "GatewayUserOrder":
            # Update order state
            if payload['state'] in [OrderState.CANCELED, OrderState.FILLED]:
                self.state_manager.remove_order(payload['id'])
            else:
                self.state_manager.update_order(payload)

        elif event_type == "MarketQuote":
            # Update quote tracker
            self.quote_tracker.update_quote(
                payload['contractId'],
                payload['bid'],
                payload['ask'],
                payload.get('last')
            )

    def _route_to_rules(self, event_type: str, payload: dict):
        """Route event to relevant rules based on event type."""

        # Map event type to rule list
        rule_map = {
            "GatewayUserTrade": [
                "RULE-003",  # DailyRealizedLoss
                "RULE-006",  # TradeFrequencyLimit
                "RULE-007",  # CooldownAfterLoss
                "RULE-012",  # TradeManagement
            ],
            "GatewayUserPosition": [
                "RULE-001",  # MaxContracts
                "RULE-002",  # MaxContractsPerInstrument
                "RULE-004",  # DailyUnrealizedLoss
                "RULE-005",  # MaxUnrealizedProfit
                "RULE-008",  # NoStopLossGrace
                "RULE-009",  # SessionBlockOutside
                "RULE-011",  # SymbolBlocks
            ],
            "GatewayUserOrder": [
                "RULE-008",  # NoStopLossGrace
                "RULE-011",  # SymbolBlocks
            ],
            "MarketQuote": [
                "RULE-004",  # DailyUnrealizedLoss
                "RULE-005",  # MaxUnrealizedProfit
            ],
            "GatewayUserAccount": [
                "RULE-010",  # AuthLossGuard
            ],
        }

        # Get rules for this event type
        rule_ids = rule_map.get(event_type, [])

        # Execute each rule sequentially
        for rule_id in rule_ids:
            action = self.rule_engine.check_rule(rule_id, payload)

            # If breach detected, execute enforcement and STOP
            if action is not None:
                self._execute_enforcement(action, payload['accountId'])
                break  # Only execute first breach

    def _execute_enforcement(self, action: EnforcementAction, account_id: int):
        """Execute enforcement action via enforcement engine."""
        from .enforcement_engine import execute_enforcement
        execute_enforcement(action, account_id)
```

---

### **SignalR Event Listener (src/api/signalr_listener.py)**

**Event handler registration:**
```python
class SignalRListener:
    """Listens to TopstepX SignalR User Hub events."""

    def __init__(self, jwt_token, event_router):
        self.jwt_token = jwt_token
        self.event_router = event_router
        self.connection = None

    def setup_user_hub(self):
        """Setup SignalR User Hub connection and register event handlers."""

        self.connection = HubConnectionBuilder() \
            .with_url(
                f"https://rtc.topstepx.com/hubs/user?access_token={self.jwt_token}",
                options={
                    "skip_negotiation": True,
                    "transport": "WebSockets",
                }
            ) \
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 10,
                "reconnect_interval": 5,
                "max_reconnect_attempts": 5
            }) \
            .build()

        # Register event handlers
        self.connection.on("GatewayUserTrade", self._on_trade)
        self.connection.on("GatewayUserPosition", self._on_position)
        self.connection.on("GatewayUserOrder", self._on_order)
        self.connection.on("GatewayUserAccount", self._on_account)

        # Start connection
        self.connection.start()
        logger.info("SignalR User Hub connected")

    def _on_trade(self, payload):
        """Handle trade event."""
        logger.debug(f"Trade event: {payload}")
        self.event_router.route_event("GatewayUserTrade", payload[0])

    def _on_position(self, payload):
        """Handle position event."""
        logger.debug(f"Position event: {payload}")
        self.event_router.route_event("GatewayUserPosition", payload[0])

    def _on_order(self, payload):
        """Handle order event."""
        logger.debug(f"Order event: {payload}")
        self.event_router.route_event("GatewayUserOrder", payload[0])

    def _on_account(self, payload):
        """Handle account event."""
        logger.debug(f"Account event: {payload}")
        self.event_router.route_event("GatewayUserAccount", payload[0])
```

---

### **Market Hub Listener (src/api/market_hub.py)**

**Quote event handler:**
```python
class MarketHubListener:
    """Listens to TopstepX SignalR Market Hub for real-time quotes."""

    def __init__(self, jwt_token, event_router):
        self.jwt_token = jwt_token
        self.event_router = event_router
        self.connection = None

    def setup_market_hub(self):
        """Setup SignalR Market Hub connection."""

        self.connection = HubConnectionBuilder() \
            .with_url(
                f"https://rtc.topstepx.com/hubs/market?access_token={self.jwt_token}",
                options={
                    "skip_negotiation": True,
                    "transport": "WebSockets",
                }
            ) \
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 10,
                "reconnect_interval": 5,
                "max_reconnect_attempts": 5
            }) \
            .build()

        # Register quote handler
        self.connection.on("MarketQuote", self._on_quote)

        # Start connection
        self.connection.start()
        logger.info("SignalR Market Hub connected")

    def _on_quote(self, payload):
        """Handle market quote event."""
        # Forward to event router for processing
        self.event_router.route_event("MarketQuote", payload[0])

    def subscribe_to_contract(self, contract_id: str):
        """Subscribe to real-time quotes for a contract."""
        self.connection.invoke("SubscribeToContract", contract_id)
        logger.debug(f"Subscribed to quotes for {contract_id}")

    def unsubscribe_from_contract(self, contract_id: str):
        """Unsubscribe from quotes for a contract."""
        self.connection.invoke("UnsubscribeFromContract", contract_id)
        logger.debug(f"Unsubscribed from quotes for {contract_id}")
```

---

## 🚨 Error Handling in Event Pipeline

### **1. SignalR Disconnection**
```python
# Automatic reconnect with exponential backoff
reconnect_policy = {
    "type": "raw",
    "keep_alive_interval": 10,  # Ping every 10 seconds
    "reconnect_interval": 5,    # Wait 5 seconds before reconnect
    "max_reconnect_attempts": 5 # Try 5 times before giving up
}
```

**Behavior:**
- Connection drops → Auto-reconnect in 5 seconds
- After 5 failed attempts → Log error, restart daemon
- On reconnect → Re-subscribe to all contracts

### **2. Invalid Event Payload**
```python
def route_event(self, event_type: str, payload: dict):
    """Route event with validation."""
    try:
        # Validate required fields
        if event_type in ["GatewayUserTrade", "GatewayUserPosition", "GatewayUserOrder"]:
            if 'accountId' not in payload:
                logger.error(f"Missing accountId in {event_type}: {payload}")
                return

        # Continue processing...
        self._update_state(event_type, payload)

    except Exception as e:
        logger.error(f"Error routing event {event_type}: {e}", exc_info=True)
        # Continue processing other events (don't crash daemon)
```

### **3. Rule Execution Error**
```python
def _route_to_rules(self, event_type: str, payload: dict):
    """Route to rules with error handling."""
    for rule_id in rule_ids:
        try:
            action = self.rule_engine.check_rule(rule_id, payload)
            if action:
                self._execute_enforcement(action, payload['accountId'])
                break

        except Exception as e:
            logger.error(f"Error executing {rule_id}: {e}", exc_info=True)
            # Continue to next rule (don't let one rule crash pipeline)
```

### **4. Enforcement API Failure**
```python
def close_all_positions(account_id: int) -> bool:
    """Close positions with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # REST API call
            response = rest_client.post("/api/Position/closeContract", ...)
            return True

        except Exception as e:
            logger.error(f"Enforcement failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait 2 seconds before retry

    # All retries failed
    logger.critical(f"ENFORCEMENT FAILED: Could not close positions for account {account_id}")
    return False
```

---

## ⏱️ Background Tasks (Not Event-Driven)

### **1. Timer & Lockout Expiry Check**
```python
def timer_background_task():
    """Check timer expiry every 1 second (not event-driven)."""
    while daemon_running:
        time.sleep(1)

        # Check for expired lockouts
        lockout_manager.check_expired_lockouts()

        # Check for expired timers
        timer_manager.check_expired_timers()
```

**Why background task:**
- Lockouts expire at specific times (need to check every second)
- Not triggered by events (time-based, not event-based)

### **2. Daily Reset Scheduler**
```python
def daily_reset_background_task():
    """Check for daily reset every 10 seconds."""
    while daemon_running:
        time.sleep(10)

        # Check if reset time reached
        reset_scheduler.check_and_execute_resets()
```

**Why background task:**
- Daily reset at specific time (e.g., 5:00 PM)
- Not triggered by events (time-based)

### **3. State Writers (Already covered in STATE_MANAGEMENT.md)**
```python
def state_writer():
    """Write batched state to SQLite every 5 seconds."""
    while daemon_running:
        time.sleep(5)
        # Process queues and batch write to SQLite
```

---

## 📊 Performance Characteristics

### **Event Processing Latency**

**Target:** < 10ms from event arrival to enforcement execution

**Breakdown:**
1. SignalR event arrival → Event router: **< 1ms**
2. State update (MOD-005, MOD-009, etc.): **< 2ms**
3. Lockout check: **< 0.1ms** (in-memory dict lookup)
4. Rule checks (7 rules max): **< 5ms** (mostly in-memory calculations)
5. Enforcement execution: **< 50ms** (REST API call to TopstepX)

**Total latency: < 60ms** (includes network round-trip)

### **Event Throughput**

**Expected load:**
- Quotes: 1-4 per second per instrument (10 instruments = 10-40 quotes/sec)
- Positions: 1-5 per minute (trader opens/closes positions)
- Orders: 2-10 per minute (order placement/cancellation)
- Trades: 1-5 per minute (full-turn trades)

**Total: ~40-60 events per second (peak)**

**System capacity:**
- Single-threaded event processing: 1000+ events/sec
- Bottleneck: REST API calls (enforcement), not event processing

### **Memory Usage**

**Event pipeline (in-memory):**
- Event queue: ~10 KB (max 100 queued events)
- State objects: ~27 KB (see STATE_MANAGEMENT.md)
- Rule engines: ~5 KB (rule instances)

**Total: ~50 KB** (negligible)

---

## 🧪 Testing Event Pipeline

### **1. Unit Tests (Individual Components)**
```python
def test_event_router_updates_state_before_rules():
    """Test that state updates happen BEFORE rule checks."""
    event_router = EventRouter(...)

    # Mock rule check to capture state at check time
    captured_state = None
    def mock_rule_check(event):
        nonlocal captured_state
        captured_state = pnl_tracker.get_daily_pnl(account_id)

    # Send trade event with P&L
    event_router.route_event("GatewayUserTrade", {
        'accountId': 123,
        'profitAndLoss': -100
    })

    # Assert state was updated BEFORE rule check
    assert captured_state == -100
```

### **2. Integration Tests (End-to-End)**
```python
def test_trade_event_triggers_daily_loss_lockout():
    """Test complete flow: Trade event → State update → Rule check → Lockout."""
    # Setup
    event_router = EventRouter(...)

    # Send trade event that breaches daily loss limit
    event_router.route_event("GatewayUserTrade", {
        'accountId': 123,
        'profitAndLoss': -600  # Limit is -500
    })

    # Assert lockout was set
    assert lockout_manager.is_locked_out(123)
    assert lockout_manager.get_lockout_reason(123) == "Daily loss limit hit"
```

### **3. Performance Tests (Latency & Throughput)**
```python
def test_event_processing_latency():
    """Test event processing latency < 10ms."""
    start = time.perf_counter()

    event_router.route_event("GatewayUserPosition", {...})

    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 10, f"Latency too high: {elapsed_ms:.2f}ms"
```

---

## 📝 Summary

**Key Points:**

1. **State updates BEFORE rule checks** - Rules always see current data
2. **Lockout gating BEFORE rule routing** - Performance optimization
3. **Unrealized P&L checks on events ONLY** - No background polling
4. **Event-driven architecture** - Only background tasks are timers/resets
5. **Error handling at every layer** - Don't let one error crash pipeline
6. **< 10ms event processing latency** - Fast enough for real-time trading
7. **Modular design** - All enforcement via MOD-001, all lockouts via MOD-002

**Files to Implement:**
- `src/core/event_router.py` (~150 lines)
- `src/api/signalr_listener.py` (~150 lines)
- `src/api/market_hub.py` (~120 lines)
- `src/enforcement/enforcement_engine.py` (~100 lines)

**Total: ~520 lines** (event pipeline core logic)

---

**Next Step:** Implement DAEMON_ARCHITECTURE.md (startup sequence, threading model, main loop)
