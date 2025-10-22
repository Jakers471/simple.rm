# End-to-End Test Specifications - Complete Workflows

**Document ID:** E2E-TEST-SPEC-001
**Version:** 1.0
**Generated:** 2025-10-22
**Purpose:** Detailed E2E test specifications for complete trading workflows
**Status:** Implementation Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Test Environment Setup](#test-environment-setup)
3. [Complete Trading Flow Tests](#complete-trading-flow-tests)
4. [Rule Violation Workflows](#rule-violation-workflows)
5. [SignalR Event-Triggered Workflows](#signalr-event-triggered-workflows)
6. [Daily Reset Workflows](#daily-reset-workflows)
7. [Authentication & Token Management](#authentication--token-management)
8. [Network & Recovery Workflows](#network--recovery-workflows)
9. [Performance Tests](#performance-tests)
10. [Test Data Requirements](#test-data-requirements)

---

## Overview

### Test Approach

End-to-end tests verify **complete workflows** from start to finish, simulating real-world trading scenarios. Each test follows the **Given/When/Then** format and covers the entire system stack:

- **Daemon startup/shutdown**
- **TopstepX API integration** (REST + SignalR)
- **Real-time event processing**
- **Rule evaluation**
- **Enforcement actions**
- **State persistence**
- **CLI displays**

### Coverage Summary

| Category | Test Count | Description |
|----------|------------|-------------|
| Complete Trading Flows | 5 | Full lifecycle from daemon start to result |
| Rule Violations | 8 | Each major rule breach scenario |
| SignalR Event Workflows | 5 | Quote updates triggering rules |
| Daily Reset Workflows | 3 | Reset time handling |
| Auth & Token Management | 3 | Authentication lifecycle |
| Network & Recovery | 4 | Disconnection and recovery |
| Performance Tests | 2 | Load and stress testing |
| **Total** | **30** | **Comprehensive E2E coverage** |

---

## Test Environment Setup

### Prerequisites

```yaml
test_environment:
  - Mock TopstepX REST API (all endpoints)
  - Mock SignalR User Hub (event simulation)
  - Mock SignalR Market Hub (quote simulation)
  - Test SQLite database (isolated from production)
  - Test configuration files (accounts.yaml, risk_config.yaml)
  - Daemon running in test mode (not Windows Service)
  - Admin CLI and Trader CLI test instances
```

### Mock API Configuration

```python
# Mock endpoints required
mock_rest_api = {
    "POST /api/Auth/validateKey": "JWT token generation",
    "POST /api/Position/searchOpen": "Return test positions",
    "POST /api/Position/closeContract": "Simulate position close",
    "POST /api/Order/searchOpen": "Return test orders",
    "POST /api/Order/cancel": "Simulate order cancel",
    "POST /api/Order/placeOrder": "Simulate order placement",
    "POST /api/Contract/searchById": "Return contract metadata"
}

# Mock SignalR events
mock_signalr_events = [
    "GatewayUserTrade",
    "GatewayUserPosition",
    "GatewayUserOrder",
    "GatewayUserAccount",
    "MarketQuote"
]
```

---

## Complete Trading Flow Tests

### E2E-001: Normal Trading Flow (No Violations)

**Test ID:** E2E-001
**Category:** Complete Trading Flow
**Priority:** Critical
**Estimated Duration:** 2 minutes

#### Given

```yaml
Initial State:
  - Daemon stopped
  - Empty SQLite database
  - Test account configured:
      account_id: 12345
      username: "test_trader"
      api_key: "test_key_123"
  - Risk config:
      max_contracts: 5
      daily_realized_loss: -500
```

#### When

```yaml
Step 1: Start daemon
  - Admin CLI: "Start Daemon"
  - Daemon executes 29-step startup sequence

Step 2: Trader places order
  - SignalR User Hub sends: GatewayUserOrder
    {
      "id": 1001,
      "accountId": 12345,
      "contractId": "CON.F.US.MNQ.U25",
      "type": 2,  # Limit
      "side": 1,  # Buy
      "size": 2,
      "limitPrice": 21000.00,
      "state": 1  # Working
    }

Step 3: Order fills
  - SignalR User Hub sends: GatewayUserOrder (state change)
    {
      "id": 1001,
      "state": 2,  # Filled
      "averageFillPrice": 21000.25
    }

Step 4: Position opens
  - SignalR User Hub sends: GatewayUserPosition
    {
      "id": 5001,
      "accountId": 12345,
      "contractId": "CON.F.US.MNQ.U25",
      "type": 1,  # Long
      "size": 2,
      "averagePrice": 21000.25
    }

Step 5: Quote updates (price moves up)
  - SignalR Market Hub sends: MarketQuote
    {
      "symbol": "F.US.MNQ",
      "lastPrice": 21050.00,
      "timestamp": "2025-01-17T14:25:00Z"
    }

Step 6: Trader closes position
  - REST API: POST /api/Position/closeContract
  - SignalR User Hub sends: GatewayUserPosition (size = 0)

Step 7: Trade P&L realized
  - SignalR User Hub sends: GatewayUserTrade
    {
      "id": 7001,
      "accountId": 12345,
      "profitAndLoss": 49.75,  # Positive trade
      "contractId": "CON.F.US.MNQ.U25"
    }

Step 8: Shutdown daemon
  - Admin CLI: "Stop Daemon"
  - Daemon executes graceful shutdown
```

#### Then

```yaml
Expected Outcomes:
  1. Daemon Startup:
     - ✅ All 29 startup steps complete successfully
     - ✅ SignalR User Hub connected
     - ✅ SignalR Market Hub connected
     - ✅ All background threads started
     - ✅ Logged: "Daemon started successfully"

  2. Order Placement:
     - ✅ State Manager tracks order (id=1001, state=Working)
     - ✅ No rule violations (within limits)
     - ✅ Logged: "Order placed: MNQ x2 @ 21000.00"

  3. Order Fill:
     - ✅ State Manager updates order (state=Filled)
     - ✅ Position created in State Manager

  4. Position Tracking:
     - ✅ State Manager tracks position (id=5001, Long 2 MNQ)
     - ✅ Position count: 2 (within max_contracts=5)
     - ✅ No rule violations
     - ✅ Market Hub subscribes to MNQ quotes

  5. Quote Updates:
     - ✅ Quote Tracker updates MNQ last price: 21050.00
     - ✅ Unrealized P&L calculated: +$49.75
     - ✅ No unrealized loss breach (profit, not loss)
     - ✅ Trader CLI shows: "Unrealized P&L: +$49.75"

  6. Position Close:
     - ✅ REST API called: POST /api/Position/closeContract
     - ✅ State Manager removes position (size=0)
     - ✅ Market Hub unsubscribes from MNQ quotes

  7. P&L Realization:
     - ✅ PNL Tracker adds trade: +$49.75
     - ✅ Daily realized P&L: +$49.75
     - ✅ Trade Counter records trade
     - ✅ No daily loss breach (positive P&L)
     - ✅ Trader CLI shows: "Daily P&L: +$49.75"

  8. Daemon Shutdown:
     - ✅ SignalR connections closed
     - ✅ All background threads stopped
     - ✅ State flushed to SQLite:
         - daily_pnl table: +$49.75
         - trade_history table: 1 trade
         - enforcement_log table: no entries (no violations)
     - ✅ Database connection closed
     - ✅ Logged: "Daemon stopped"

  9. SQLite Persistence Verified:
     - ✅ daily_pnl table contains: account_id=12345, realized_pnl=49.75
     - ✅ trade_history table contains: 1 trade record
     - ✅ positions table is empty (position closed)
     - ✅ orders table is empty (order filled)
     - ✅ lockouts table is empty (no violations)
```

---

### E2E-002: Complete Trading Flow with Stop-Loss

**Test ID:** E2E-002
**Category:** Complete Trading Flow
**Priority:** High
**Estimated Duration:** 2 minutes

#### Given

```yaml
Initial State:
  - Daemon running and connected
  - Test account active
  - Risk config:
      no_stop_loss_grace:
        enabled: true
        grace_period_seconds: 30
        action: "close_all_and_lockout"
```

#### When

```yaml
Step 1: Trader opens position (no stop-loss)
  - SignalR: GatewayUserPosition
    {
      "id": 5002,
      "accountId": 12345,
      "contractId": "CON.F.US.ES.U25",
      "type": 1,  # Long
      "size": 1,
      "averagePrice": 5800.00
    }

Step 2: Wait 10 seconds (within grace period)
  - Timer Manager starts 30-second grace timer
  - No action yet

Step 3: Trader places stop-loss order
  - SignalR: GatewayUserOrder
    {
      "id": 1002,
      "accountId": 12345,
      "contractId": "CON.F.US.ES.U25",
      "type": 3,  # Stop
      "side": 2,  # Sell (opposite of Long position)
      "size": 1,
      "stopPrice": 5790.00
    }

Step 4: Rule validates stop-loss
  - RULE-008 detects valid stop-loss order
  - Grace timer cancelled
```

#### Then

```yaml
Expected Outcomes:
  1. Position Without SL:
     - ✅ RULE-008 detects position without stop-loss
     - ✅ Timer Manager starts 30-second grace timer
     - ✅ Trader CLI shows: "⏱️ Stop-loss required in 20s"
     - ✅ No enforcement action yet

  2. Stop-Loss Placed:
     - ✅ RULE-008 validates order:
         - Type = Stop (3)
         - Side = Sell (opposite of Long)
         - Contract = ES (matches position)
         - Size = 1 (matches position size)
     - ✅ Timer Manager cancels grace timer
     - ✅ Trader CLI shows: "✅ Stop-loss active @ 5790.00"
     - ✅ No enforcement action
     - ✅ Logged: "RULE-008: Stop-loss validated for position 5002"

  3. No Lockout:
     - ✅ Lockout Manager: is_locked_out(12345) = False
     - ✅ No enforcement log entry
```

---

### E2E-003: Daemon Restart with State Recovery

**Test ID:** E2E-003
**Category:** Complete Trading Flow
**Priority:** Critical
**Estimated Duration:** 3 minutes

#### Given

```yaml
Initial State:
  - Daemon running
  - Active position:
      Long 3 MNQ @ 21000.00
  - Daily P&L: -$250
  - Active lockout: None
  - SQLite database populated with state
```

#### When

```yaml
Step 1: Daemon crashes unexpectedly
  - Exception thrown in main event loop
  - Emergency shutdown executes:
      - Flushes lockouts to SQLite
      - Flushes daily P&L to SQLite
      - Daemon exits (code 1)

Step 2: Daemon restarts (auto-restart)
  - Startup sequence begins
  - Load state from SQLite (Step 7-15)

Step 3: Resume monitoring
  - SignalR reconnects
  - Continue processing events
```

#### Then

```yaml
Expected Outcomes:
  1. Emergency Shutdown:
     - ✅ Logged: "EMERGENCY SHUTDOWN - Attempting to save state"
     - ✅ SQLite tables written:
         - daily_pnl: -$250
         - positions: Long 3 MNQ @ 21000.00 (may be slightly stale)
     - ✅ Daemon exits with code 1

  2. Startup After Crash:
     - ✅ All 29 startup steps complete
     - ✅ MOD-005 loads daily P&L: -$250
     - ✅ MOD-009 loads positions: Long 3 MNQ @ 21000.00
     - ✅ MOD-002 loads lockouts: None
     - ✅ Logged: "State recovered from database after crash"

  3. State Verification:
     - ✅ pnl_tracker.get_daily_realized_pnl(12345) = -250
     - ✅ state_manager.get_position_count(12345) = 3
     - ✅ lockout_manager.is_locked_out(12345) = False
     - ✅ Market Hub subscribes to MNQ quotes (position still open)

  4. Resume Monitoring:
     - ✅ New events processed correctly
     - ✅ Rules evaluate with recovered state
     - ✅ Trader CLI displays recovered state
     - ✅ Data loss: < 5 seconds of events (acceptable)
```

---

### E2E-004: Multi-Account Monitoring

**Test ID:** E2E-004
**Category:** Complete Trading Flow
**Priority:** High
**Estimated Duration:** 3 minutes

#### Given

```yaml
Initial State:
  - Daemon stopped
  - Multiple accounts configured:
      Account 1: account_id=12345
      Account 2: account_id=67890
  - Both accounts authenticated
```

#### When

```yaml
Step 1: Start daemon
  - Daemon authenticates both accounts
  - Two JWT tokens stored

Step 2: Account 1 trades (within limits)
  - SignalR: GatewayUserTrade (account=12345, pnl=-100)

Step 3: Account 2 trades (breach limit)
  - SignalR: GatewayUserTrade (account=67890, pnl=-550)
  - Daily loss limit: -500

Step 4: Verify independent enforcement
  - Account 2 locked out
  - Account 1 unaffected
```

#### Then

```yaml
Expected Outcomes:
  1. Daemon Authenticates Both Accounts:
     - ✅ auth.authenticate(username1, api_key1) → JWT token 1
     - ✅ auth.authenticate(username2, api_key2) → JWT token 2
     - ✅ account_tokens dictionary:
         {12345: "jwt_token_1", 67890: "jwt_token_2"}
     - ✅ Logged: "Monitoring 2 accounts"

  2. Account 1 Trades (No Breach):
     - ✅ PNL Tracker adds trade: account=12345, pnl=-100
     - ✅ Daily P&L: -100 (within -500 limit)
     - ✅ No enforcement action
     - ✅ Account 1 NOT locked out

  3. Account 2 Trades (Breach):
     - ✅ PNL Tracker adds trade: account=67890, pnl=-550
     - ✅ RULE-003 detects breach: -550 <= -500
     - ✅ Enforcement executes:
         - close_all_positions(67890)
         - cancel_all_orders(67890)
         - set_lockout(67890, until=17:00)
     - ✅ Account 2 locked out
     - ✅ Logged: "RULE-003: Account 67890 locked out - daily loss limit"

  4. Account 1 Can Still Trade:
     - ✅ lockout_manager.is_locked_out(12345) = False
     - ✅ lockout_manager.is_locked_out(67890) = True
     - ✅ Account 1 events processed normally
     - ✅ Account 2 events skipped (locked out)
     - ✅ Trader CLI shows both accounts independently:
         - Account 12345: "🟢 OK TO TRADE - P&L: -$100"
         - Account 67890: "🔴 LOCKED OUT - Daily loss - Reset at 5:00 PM"
```

---

### E2E-005: Full Trading Day Simulation (8 Hours)

**Test ID:** E2E-005
**Category:** Complete Trading Flow
**Priority:** Medium
**Estimated Duration:** 10 minutes (time-accelerated simulation)

#### Given

```yaml
Initial State:
  - Daemon running
  - Test account active
  - Time-acceleration enabled (1 minute = 1 hour)
  - All 12 rules enabled
```

#### When

```yaml
Simulated Timeline (8 hours compressed to 8 minutes):

9:30 AM (Session Start):
  - Position opens: Long 2 MNQ @ 21000
  - Stop-loss placed within grace period

10:00 AM (Morning trading):
  - 5 trades executed (all profitable)
  - Daily P&L: +$150

11:00 AM (Frequency test):
  - 4 trades in 60 seconds (breach per_minute=3)
  - Cooldown triggered (60 seconds)

12:00 PM (Unrealized loss):
  - Price drops to 20700 (-$300 unrealized)
  - Still within -500 limit

1:00 PM (Max contracts):
  - Positions: Long 3 MNQ, Long 2 ES (net=5)
  - At limit, no breach

2:00 PM (Realized loss):
  - Large losing trade: -$400
  - Daily P&L: -$250 (still safe)

3:30 PM (Final trades):
  - Close all positions
  - Final P&L: -$300

5:00 PM (Daily Reset):
  - Reset scheduler triggers
  - P&L resets to 0
  - Lockouts cleared
```

#### Then

```yaml
Expected Outcomes:
  1. Session Start (9:30 AM):
     - ✅ RULE-009 allows trading (within session hours)
     - ✅ RULE-008 grace period started (30s)
     - ✅ Stop-loss placed within grace → no enforcement

  2. Morning Trading (10:00 AM):
     - ✅ Trade Counter records 5 trades
     - ✅ PNL Tracker: daily P&L = +$150
     - ✅ No rule violations

  3. Frequency Breach (11:00 AM):
     - ✅ RULE-006 detects 4 trades in 60s (limit=3)
     - ✅ Lockout Manager sets cooldown (60 seconds)
     - ✅ Timer Manager counts down
     - ✅ Trader CLI shows: "⏱️ Cooldown: 45s remaining"
     - ✅ After 60s: cooldown expires, trading allowed

  4. Unrealized Loss (12:00 PM):
     - ✅ Quote Tracker updates: MNQ = 20700
     - ✅ RULE-004 calculates: unrealized = -$300
     - ✅ No breach (-300 > -500 limit)

  5. Max Contracts (1:00 PM):
     - ✅ State Manager: net contracts = 5
     - ✅ RULE-001 check: 5 <= 5 (at limit, no breach)
     - ✅ No enforcement action

  6. Realized Loss (2:00 PM):
     - ✅ PNL Tracker: daily P&L = -$250
     - ✅ RULE-003 check: -250 > -500 (still safe)
     - ✅ Trader CLI shows: "⚠️ Daily P&L: -$250 / -$500 (50%)"

  7. Position Closes (3:30 PM):
     - ✅ All positions closed
     - ✅ Final daily P&L: -$300
     - ✅ No lockout (within limit)

  8. Daily Reset (5:00 PM):
     - ✅ Reset Scheduler triggers: check_reset_times() → [12345]
     - ✅ PNL Tracker: reset_daily_pnl(12345) → P&L = 0
     - ✅ Lockout Manager: clear_daily_lockouts(12345)
     - ✅ Trade Counter: reset_daily_count(12345)
     - ✅ Trader CLI shows: "🟢 Daily reset complete - Ready for trading"
     - ✅ Logged: "Daily reset complete for account 12345"

  9. All Rules Tested:
     - ✅ RULE-001: Max Contracts
     - ✅ RULE-003: Daily Realized Loss
     - ✅ RULE-004: Daily Unrealized Loss
     - ✅ RULE-006: Trade Frequency Limit
     - ✅ RULE-008: No Stop-Loss Grace
     - ✅ RULE-009: Session Block Outside
```

---

## Rule Violation Workflows

### E2E-006: RULE-001 Violation - Max Contracts Exceeded

**Test ID:** E2E-006
**Category:** Rule Violation
**Priority:** High
**Estimated Duration:** 1 minute

#### Given

```yaml
Initial State:
  - Daemon running
  - Risk config:
      max_contracts:
        enabled: true
        limit: 5
        count_type: "net"
        close_all: true
        lockout_on_breach: false
  - Current positions: Long 4 MNQ
```

#### When

```yaml
Step 1: Trader opens additional position
  - SignalR: GatewayUserPosition
    {
      "id": 5003,
      "accountId": 12345,
      "contractId": "CON.F.US.ES.U25",
      "type": 1,  # Long
      "size": 2,  # This puts total at 6
      "averagePrice": 5800.00
    }

Step 2: Event router processes event
  - State Manager updates: net contracts = 6
  - RULE-001 evaluates: 6 > 5 (BREACH)

Step 3: Enforcement executes
  - MOD-001: close_all_positions(12345)
```

#### Then

```yaml
Expected Outcomes:
  1. State Update:
     - ✅ State Manager tracks both positions:
         - Position 5001: Long 4 MNQ
         - Position 5003: Long 2 ES
     - ✅ get_position_count(12345) = 6

  2. Rule Breach Detection:
     - ✅ RULE-001 check() evaluates:
         - total_net = 6
         - limit = 5
         - 6 > 5 → BREACH
     - ✅ Logged: "RULE-001: Max contracts breach detected (6 > 5)"

  3. Enforcement Action:
     - ✅ actions.close_all_positions(12345) called
     - ✅ REST API calls:
         - POST /api/Position/searchOpen → [5001, 5003]
         - POST /api/Position/closeContract (contract=MNQ)
         - POST /api/Position/closeContract (contract=ES)
     - ✅ State Manager updates: all positions size=0
     - ✅ Logged: "Closed 2 positions via REST API"

  4. NO Lockout:
     - ✅ lockout_manager.is_locked_out(12345) = False
     - ✅ Trader can place next order immediately

  5. Trader CLI Display:
     - ✅ Shows: "⚠️ Max Contracts Breach - All positions closed (6 > 5)"
     - ✅ Shows: "🟢 OK TO TRADE - No lockout"
     - ✅ Recent Enforcement:
         "[14:23:15] MaxContracts breach - Closed all positions"

  6. Enforcement Log:
     - ✅ SQLite enforcement_log table entry:
         - account_id: 12345
         - rule_id: "RULE-001"
         - action: "CLOSE_ALL_POSITIONS"
         - reason: "Max contracts exceeded (6 > 5)"
         - timestamp: 2025-01-17 14:23:15
```

---

### E2E-007: RULE-003 Violation - Daily Realized Loss Limit

**Test ID:** E2E-007
**Category:** Rule Violation
**Priority:** Critical
**Estimated Duration:** 2 minutes

#### Given

```yaml
Initial State:
  - Daemon running
  - Risk config:
      daily_realized_loss:
        enabled: true
        limit: -500
        reset_time: "17:00"
        timezone: "America/New_York"
        enforcement: "close_all_and_lockout"
  - Current state:
      Daily P&L: -$450 (from previous trades)
      Open positions: Long 2 MNQ
      Time: 2:00 PM (5 hours before reset)
```

#### When

```yaml
Step 1: Large losing trade executes
  - SignalR: GatewayUserTrade
    {
      "id": 7002,
      "accountId": 12345,
      "contractId": "CON.F.US.MNQ.U25",
      "profitAndLoss": -75.50,  # This puts total at -525.50
      "price": 20950.00
    }

Step 2: Event router processes event
  - PNL Tracker adds trade: -75.50
  - New daily P&L: -525.50
  - RULE-003 evaluates: -525.50 <= -500 (BREACH)

Step 3: Enforcement executes
  - Close all positions
  - Cancel all orders
  - Set lockout until 5:00 PM

Step 4: Wait 30 seconds, try to place order
  - Order placement blocked by lockout gate
```

#### Then

```yaml
Expected Outcomes:
  1. P&L Update:
     - ✅ pnl_tracker.add_trade_pnl(12345, -75.50)
     - ✅ New daily P&L: -450 + (-75.50) = -525.50
     - ✅ SQLite daily_pnl table updated: -525.50

  2. Rule Breach Detection:
     - ✅ RULE-003 check() evaluates:
         - current_pnl = -525.50
         - limit = -500
         - -525.50 <= -500 → BREACH
     - ✅ Logged: "RULE-003: Daily realized loss limit breached (-$525.50 / -$500.00)"

  3. Enforcement Action:
     - ✅ actions.close_all_positions(12345)
     - ✅ REST API: POST /api/Position/closeContract (MNQ x2)
     - ✅ actions.cancel_all_orders(12345)
     - ✅ REST API: POST /api/Order/cancel (any working orders)
     - ✅ Logged: "Enforcement: Closed 1 position, canceled 0 orders"

  4. Lockout Set:
     - ✅ Calculate reset time:
         - Current: 2:00 PM
         - Reset: 5:00 PM (same day)
         - Duration: 3 hours
     - ✅ lockout_manager.set_lockout():
         - account_id: 12345
         - reason: "Daily loss limit hit (-$525.50 / -$500.00)"
         - until: 2025-01-17 17:00:00
     - ✅ SQLite lockouts table entry created
     - ✅ Logged: "Lockout set until 5:00 PM (3h 0m remaining)"

  5. Lockout Gate Blocks Events:
     - ✅ Attempt to place order → event arrives
     - ✅ event_router.route_event() checks:
         - is_locked_out(12345) → True
         - Skip rule evaluation
         - Return immediately
     - ✅ Order not processed (ignored)
     - ✅ Logged: "Event skipped - account 12345 locked out"

  6. Trader CLI Display:
     - ✅ Shows lockout banner:
         "🔴 LOCKED OUT"
         "Reason: Daily loss limit hit (-$525.50 / -$500.00)"
         "Unlocks at: 5:00 PM (2h 59m remaining)"
     - ✅ Countdown timer updates every second
     - ✅ All positions shown as closed
     - ✅ Recent Enforcement:
         "[14:23:15] DailyRealizedLoss LOCKOUT - P&L: -$525.50"
```

---

### E2E-008: RULE-004 Violation - Daily Unrealized Loss (Per Position)

**Test ID:** E2E-008
**Category:** Rule Violation
**Priority:** High
**Estimated Duration:** 2 minutes

#### Given

```yaml
Initial State:
  - Daemon running
  - Risk config:
      daily_unrealized_loss:
        enabled: true
        loss_limit: 300.00
        scope: "per_position"
        action: "CLOSE_POSITION"
        lockout: false
  - Current state:
      Position 5004: Long 2 MNQ @ 21000.00
      Last quote: 21000.00 (no unrealized P&L yet)
```

#### When

```yaml
Step 1: Price drops significantly
  - SignalR Market Hub: MarketQuote
    {
      "symbol": "F.US.MNQ",
      "lastPrice": 20700.00,  # -300 points = -$300 unrealized
      "timestamp": "2025-01-17T14:25:00Z"
    }

Step 2: Quote Tracker updates price
  - quote_tracker.update_quote("F.US.MNQ", 20700.00)

Step 3: Background check or next event triggers rule
  - RULE-004 check_with_current_prices()
  - Calculate unrealized P&L per position

Step 4: Enforcement executes
  - Close only the losing position (not all positions)
```

#### Then

```yaml
Expected Outcomes:
  1. Quote Update:
     - ✅ Quote Tracker: MNQ last_price = 20700.00
     - ✅ Market Hub event logged
     - ✅ Position 5004 still open (size=2)

  2. Unrealized P&L Calculation:
     - ✅ RULE-004 calculates per position:
         - Entry: 21000.00
         - Current: 20700.00
         - Diff: -300 points
         - Tick size: 0.25
         - Tick value: $0.50
         - Ticks: -300 / 0.25 = -1200 ticks
         - P&L: -1200 * $0.50 * 2 = -$1200
     - ✅ Per-position scope: check each position independently
     - ✅ Position 5004: -$1200 > -$300 limit → BREACH

  3. Rule Breach Detection:
     - ✅ RULE-004 check() evaluates:
         - scope: "per_position"
         - Position 5004 unrealized: -$1200
         - loss_limit: $300
         - |-1200| > 300 → BREACH
     - ✅ Logged: "RULE-004: Position 5004 unrealized loss breach (-$1200 > -$300)"

  4. Enforcement Action (CLOSE_POSITION):
     - ✅ actions.close_position(12345, position_id=5004)
     - ✅ REST API: POST /api/Position/closeContract
         {
           "accountId": 12345,
           "contractId": "CON.F.US.MNQ.U25"
         }
     - ✅ State Manager: position 5004 size=0 (removed)
     - ✅ Market Hub: unsubscribe from MNQ quotes (no more positions)
     - ✅ Logged: "Closed position 5004 (MNQ x2) - unrealized loss limit"

  5. NO Lockout:
     - ✅ lockout: false (per config)
     - ✅ lockout_manager.is_locked_out(12345) = False
     - ✅ Trader can open new position immediately

  6. Trader CLI Display:
     - ✅ Shows: "⚠️ Position Closed - Unrealized loss limit (-$1200 > -$300)"
     - ✅ Positions list: empty (position closed)
     - ✅ Shows: "🟢 OK TO TRADE - No lockout"
     - ✅ Recent Enforcement:
         "[14:25:30] DailyUnrealizedLoss - Closed position 5004 (MNQ)"
```

---

### E2E-009: RULE-008 Violation - No Stop-Loss Grace Period Expired

**Test ID:** E2E-009
**Category:** Rule Violation
**Priority:** High
**Estimated Duration:** 45 seconds

#### Given

```yaml
Initial State:
  - Daemon running
  - Risk config:
      no_stop_loss_grace:
        enabled: true
        grace_period_seconds: 30
        action: "close_all_and_lockout"
        lockout_duration: 3600  # 1 hour
  - Current state: No positions
```

#### When

```yaml
Step 1: Trader opens position (no stop-loss)
  - SignalR: GatewayUserPosition
    {
      "id": 5005,
      "accountId": 12345,
      "contractId": "CON.F.US.MNQ.U25",
      "type": 1,  # Long
      "size": 2,
      "averagePrice": 21000.00,
      "timestamp": "2025-01-17T14:30:00Z"
    }

Step 2: Wait 30 seconds (no stop-loss placed)
  - Timer Manager counts down grace period
  - No GatewayUserOrder event (no SL placed)

Step 3: Grace period expires
  - Timer Manager callback fires: on_grace_expired()
  - RULE-008 enforcement executes
```

#### Then

```yaml
Expected Outcomes:
  1. Position Opens (No SL):
     - ✅ State Manager: position 5005 tracked
     - ✅ RULE-008 detects: no stop-loss order exists
     - ✅ Timer Manager: start_timer("no_sl_grace_12345_5005", 30s)
     - ✅ Logged: "RULE-008: Grace period started (30s) for position 5005"

  2. Grace Period Active:
     - ✅ Timer Manager: get_remaining_time("no_sl_grace_12345_5005") → 20s, 15s, 10s...
     - ✅ Trader CLI shows countdown:
         "⏱️ Stop-loss required in 15s (position 5005)"
     - ✅ RULE-008 status: IN_GRACE_PERIOD

  3. Grace Period Expires (No SL Placed):
     - ✅ Timer Manager: timer expires at 30 seconds
     - ✅ Callback fires: on_grace_expired(12345, 5005)
     - ✅ RULE-008 check(): still no stop-loss → BREACH
     - ✅ Logged: "RULE-008: Grace period expired - no stop-loss for position 5005"

  4. Enforcement Action:
     - ✅ actions.close_all_positions(12345)
     - ✅ REST API: POST /api/Position/closeContract (MNQ)
     - ✅ actions.cancel_all_orders(12345)
     - ✅ State Manager: position 5005 removed
     - ✅ Logged: "Enforcement: Closed position 5005 (grace expired)"

  5. Lockout Set (1 Hour):
     - ✅ Calculate lockout expiry:
         - Current: 14:30:30
         - Duration: 3600 seconds (1 hour)
         - Until: 15:30:30
     - ✅ lockout_manager.set_lockout():
         - account_id: 12345
         - reason: "No stop-loss placed within grace period"
         - until: 2025-01-17 15:30:30
     - ✅ SQLite lockouts table entry created
     - ✅ Logged: "Lockout set for 1 hour (until 3:30 PM)"

  6. Trader CLI Display:
     - ✅ Shows lockout banner:
         "🔴 LOCKED OUT"
         "Reason: No stop-loss placed within grace period"
         "Unlocks at: 3:30 PM (59m 55s remaining)"
     - ✅ Countdown timer updates every second
     - ✅ Recent Enforcement:
         "[14:30:30] NoStopLossGrace - Position closed, 1h lockout"
```

---

### E2E-010: RULE-011 Violation - Blocked Symbol Position

**Test ID:** E2E-010
**Category:** Rule Violation
**Priority:** High
**Estimated Duration:** 1 minute

#### Given

```yaml
Initial State:
  - Daemon running
  - Risk config:
      symbol_blocks:
        enabled: true
        blocked_symbols: ["BTC", "ETH", "GC"]
        action: "close_all_and_lockout"
        lockout_duration: 86400  # 24 hours
```

#### When

```yaml
Step 1: Trader opens position in blocked symbol
  - SignalR: GatewayUserPosition
    {
      "id": 5006,
      "accountId": 12345,
      "contractId": "CON.F.US.BTC.U25",  # Bitcoin futures (BLOCKED)
      "type": 1,  # Long
      "size": 1,
      "averagePrice": 95000.00
    }

Step 2: Event router processes event
  - State Manager updates
  - RULE-011 evaluates: BTC in blocked list → BREACH

Step 3: Enforcement executes
  - Close all positions (including BTC)
  - Set 24-hour lockout
```

#### Then

```yaml
Expected Outcomes:
  1. Position Opens:
     - ✅ State Manager: position 5006 tracked
     - ✅ Contract ID: "CON.F.US.BTC.U25"

  2. Rule Breach Detection:
     - ✅ RULE-011 check() evaluates:
         - Extract symbol from contract ID: "BTC"
         - Check blocked list: ["BTC", "ETH", "GC"]
         - "BTC" in blocked_symbols → BREACH
     - ✅ Logged: "RULE-011: Blocked symbol detected - BTC"

  3. Enforcement Action:
     - ✅ actions.close_all_positions(12345)
     - ✅ REST API: POST /api/Position/closeContract (BTC)
     - ✅ State Manager: position 5006 removed
     - ✅ Logged: "Enforcement: Closed blocked symbol position (BTC)"

  4. Lockout Set (24 Hours):
     - ✅ Calculate lockout expiry:
         - Current: 14:30:00
         - Duration: 86400 seconds (24 hours)
         - Until: 2025-01-18 14:30:00 (next day)
     - ✅ lockout_manager.set_lockout():
         - account_id: 12345
         - reason: "Trading in blocked symbol: BTC"
         - until: 2025-01-18 14:30:00
     - ✅ SQLite lockouts table entry created
     - ✅ Logged: "Lockout set for 24 hours (until tomorrow 2:30 PM)"

  5. Trader CLI Display:
     - ✅ Shows lockout banner:
         "🔴 LOCKED OUT"
         "Reason: Trading in blocked symbol: BTC"
         "Unlocks at: Tomorrow 2:30 PM (23h 59m remaining)"
     - ✅ Position closed immediately
     - ✅ Recent Enforcement:
         "[14:30:00] SymbolBlocks - Blocked symbol BTC - 24h lockout"
```

---

### E2E-011: RULE-006 Violation - Trade Frequency Limit (Per Minute)

**Test ID:** E2E-011
**Category:** Rule Violation
**Priority:** Medium
**Estimated Duration:** 2 minutes

#### Given

```yaml
Initial State:
  - Daemon running
  - Risk config:
      trade_frequency_limit:
        enabled: true
        limits:
          per_minute: 3
          per_hour: 10
          per_session: 50
        cooldown_on_breach:
          enabled: true
          per_minute_breach: 60  # 60 second cooldown
```

#### When

```yaml
Step 1: Execute 4 trades in 60 seconds
  - t=0s: GatewayUserTrade (id=7001)
  - t=15s: GatewayUserTrade (id=7002)
  - t=30s: GatewayUserTrade (id=7003)
  - t=45s: GatewayUserTrade (id=7004)  # 4th trade → BREACH

Step 2: RULE-006 detects breach on 4th trade
  - Trade Counter: get_trades_in_window(60s) → 4 trades
  - Limit: 3 trades per minute
  - 4 > 3 → BREACH

Step 3: Cooldown set
  - Lockout Manager: set_cooldown(60 seconds)

Step 4: Wait 60 seconds
  - Timer Manager counts down
  - Cooldown expires

Step 5: Try to place 5th trade
  - Event arrives after cooldown expired
  - Processed normally
```

#### Then

```yaml
Expected Outcomes:
  1. Trades 1-3 (Normal):
     - ✅ Trade Counter records each trade with timestamp
     - ✅ get_trades_in_window(60s):
         - After trade 1: [7001] → count=1
         - After trade 2: [7001, 7002] → count=2
         - After trade 3: [7001, 7002, 7003] → count=3
     - ✅ No breach yet (3 <= 3)

  2. Trade 4 (Breach):
     - ✅ Trade Counter: records trade 7004
     - ✅ get_trades_in_window(60s): [7001, 7002, 7003, 7004] → count=4
     - ✅ RULE-006 check():
         - per_minute limit: 3
         - current trades in 60s: 4
         - 4 > 3 → BREACH
     - ✅ Logged: "RULE-006: Trade frequency breach - 4 trades in 60s (limit 3)"

  3. Cooldown Set:
     - ✅ lockout_manager.set_cooldown():
         - account_id: 12345
         - reason: "Trade frequency limit (4 trades/minute, limit 3)"
         - duration: 60 seconds
     - ✅ Calculate expiry:
         - Current: 14:30:45
         - Duration: 60s
         - Until: 14:31:45
     - ✅ SQLite lockouts table entry created
     - ✅ Logged: "Cooldown set for 60 seconds"

  4. Cooldown Active:
     - ✅ Timer Manager: start_timer("cooldown_12345", 60s)
     - ✅ Trader CLI shows:
         "⏱️ COOLDOWN - Trade frequency limit"
         "Resume trading in: 45s"
     - ✅ Countdown updates every second
     - ✅ Any new events skipped (locked out)

  5. Cooldown Expires:
     - ✅ Timer Manager: timer expires at 60 seconds
     - ✅ Lockout Manager: clear_lockout(12345)
     - ✅ SQLite lockouts table: entry removed
     - ✅ Logged: "Cooldown expired - trading allowed"
     - ✅ Trader CLI shows: "🟢 OK TO TRADE - Cooldown complete"

  6. Next Trade Allowed:
     - ✅ Trade 5 arrives (t=120s)
     - ✅ lockout_manager.is_locked_out(12345) → False
     - ✅ Event processed normally
     - ✅ Trade Counter: get_trades_in_window(60s) → [7005] (only 1 in last 60s)
     - ✅ No breach
```

---

### E2E-012: RULE-009 Violation - Session Block Outside Hours

**Test ID:** E2E-012
**Category:** Rule Violation
**Priority:** High
**Estimated Duration:** 1 minute

#### Given

```yaml
Initial State:
  - Daemon running
  - Risk config:
      session_block_outside:
        enabled: true
        global_session:
          enabled: true
          start: "09:30"
          end: "16:00"
          timezone: "America/New_York"
        close_positions_at_session_end: true
        lockout_outside_session: true
  - Current time: 4:00 PM (session end time)
  - Open positions: Long 2 MNQ
```

#### When

```yaml
Step 1: Clock hits 4:00 PM (session end)
  - Reset Scheduler checks session times
  - RULE-009 detects: time >= session end

Step 2: Auto-close enforcement
  - Close all positions (session end)
  - Set lockout until next session start (9:30 AM tomorrow)

Step 3: Trader tries to place order at 4:01 PM
  - Order event arrives
  - Lockout gate blocks event
```

#### Then

```yaml
Expected Outcomes:
  1. Session End Detection:
     - ✅ Current time: 16:00:00 (4:00 PM)
     - ✅ Session end time: 16:00:00
     - ✅ RULE-009 check(): time >= session_end → BREACH
     - ✅ Logged: "RULE-009: Session end reached - closing positions"

  2. Auto-Close Enforcement:
     - ✅ actions.close_all_positions(12345)
     - ✅ REST API: POST /api/Position/closeContract (MNQ x2)
     - ✅ State Manager: all positions removed
     - ✅ Logged: "Enforcement: Closed 1 position at session end"

  3. Lockout Set (Until Next Session):
     - ✅ Calculate next session start:
         - Current: 2025-01-17 16:00:00
         - Next start: 2025-01-18 09:30:00 (tomorrow)
         - Duration: 17.5 hours
     - ✅ lockout_manager.set_lockout():
         - account_id: 12345
         - reason: "Trading outside session hours"
         - until: 2025-01-18 09:30:00
     - ✅ SQLite lockouts table entry created
     - ✅ Logged: "Lockout set until 9:30 AM tomorrow (17h 30m)"

  4. Lockout Gate Blocks Events:
     - ✅ Order event arrives at 4:01 PM
     - ✅ event_router.route_event():
         - is_locked_out(12345) → True
         - Skip processing
         - Return immediately
     - ✅ Logged: "Event skipped - outside session hours"

  5. Trader CLI Display:
     - ✅ Shows lockout banner:
         "🔴 LOCKED OUT"
         "Reason: Trading outside session hours"
         "Unlocks at: Tomorrow 9:30 AM (17h 29m remaining)"
     - ✅ Session status: "Session closed - resumes 9:30 AM"
     - ✅ Countdown timer shows hours:minutes:seconds

  6. Next Day - Auto-Unlock:
     - ✅ At 9:30 AM next day:
         - Reset Scheduler: check_expired_lockouts()
         - Lockout Manager: clear_lockout(12345)
         - Logged: "Lockout expired - session opened"
     - ✅ Trader CLI shows: "🟢 OK TO TRADE - Session open"
```

---

### E2E-013: RULE-005 Violation - Max Unrealized Profit

**Test ID:** E2E-013
**Category:** Rule Violation
**Priority:** Medium
**Estimated Duration:** 1 minute

#### Given

```yaml
Initial State:
  - Daemon running
  - Risk config:
      max_unrealized_profit:
        enabled: true
        profit_limit: 2000.00
        action: "close_all_and_lockout"
        lockout_duration: 3600
  - Current position: Long 10 ES @ 5800.00
```

#### When

```yaml
Step 1: Price rises significantly
  - SignalR Market Hub: MarketQuote
    {
      "symbol": "F.US.ES",
      "lastPrice": 5816.00,  # +16 points = +$2,000 unrealized
      "timestamp": "2025-01-17T14:30:00Z"
    }

Step 2: Quote updates, rule evaluates
  - Quote Tracker: ES = 5816.00
  - RULE-005: calculate_unrealized_pnl() → +$2,000 (exactly at limit)

Step 3: Price rises +1 more point
  - MarketQuote: lastPrice = 5816.25
  - Unrealized: +$2,012.50 → BREACH

Step 4: Enforcement executes
  - Close all positions (lock in profit)
  - Set 1-hour lockout
```

#### Then

```yaml
Expected Outcomes:
  1. Quote Update (At Limit):
     - ✅ Quote Tracker: ES last_price = 5816.00
     - ✅ RULE-005 calculates:
         - Entry: 5800.00
         - Current: 5816.00
         - Diff: +16 points
         - Tick size: 0.25
         - Tick value: $12.50
         - Ticks: 16 / 0.25 = 64 ticks
         - P&L: 64 * $12.50 * 10 = +$8,000
     - ✅ Wait, that's $8,000 not $2,000... recalculate:
         - Actually: +16 points * $50/point * 10 contracts = +$8,000
         - This would breach immediately at +$2,000 limit
     - ✅ Let's fix the test case...

Actually, correct calculation for ES:
  - ES tick = 0.25 points
  - ES tick value = $12.50
  - +16 points = 64 ticks
  - P&L = 64 * $12.50 * 10 = $8,000 (way over limit)

Let me fix the test to be more realistic:

Step 1 (Fixed): Price rises modestly
  - Position: Long 10 ES @ 5800.00
  - New price: 5804.00 (+4 points = +$2,000)
  - Calculation:
      - Diff: +4 points
      - Ticks: 4 / 0.25 = 16 ticks
      - P&L: 16 * $12.50 * 10 = +$2,000
  - At limit, no breach yet

Step 2 (Fixed): Price rises +0.25 more
  - New price: 5804.25 (+4.25 points = +$2,012.50)
  - BREACH: $2,012.50 > $2,000

Expected Outcomes (Fixed):
  1. Quote at Limit:
     - ✅ RULE-005: unrealized = +$2,000
     - ✅ profit_limit = $2,000
     - ✅ $2,000 <= $2,000 → No breach (at limit OK)
     - ✅ Logged: "RULE-005: At profit limit (+$2,000 / $2,000)"

  2. Quote Exceeds Limit:
     - ✅ RULE-005: unrealized = +$2,012.50
     - ✅ $2,012.50 > $2,000 → BREACH
     - ✅ Logged: "RULE-005: Max unrealized profit breach (+$2,012.50 > +$2,000)"

  3. Enforcement Action:
     - ✅ actions.close_all_positions(12345)
     - ✅ REST API: POST /api/Position/closeContract (ES x10)
     - ✅ State Manager: position removed
     - ✅ Logged: "Enforcement: Closed position (lock in profit)"

  4. Lockout Set:
     - ✅ lockout_manager.set_lockout(12345, 3600s)
     - ✅ Reason: "Max unrealized profit exceeded (+$2,012.50)"
     - ✅ Until: 15:30:00 (1 hour from now)

  5. Trader CLI Display:
     - ✅ Shows: "🟢 Position closed - profit target reached"
     - ✅ Shows: "⏱️ COOLDOWN - Max profit reached (59m 55s)"
     - ✅ Recent Enforcement:
         "[14:30:00] MaxUnrealizedProfit - Closed, locked 1h"
```

---

## SignalR Event-Triggered Workflows

### E2E-014: Quote Update Triggers Unrealized Loss Rule

**Test ID:** E2E-014
**Category:** SignalR Event Workflow
**Priority:** High
**Estimated Duration:** 2 minutes

#### Given

```yaml
Initial State:
  - Daemon running
  - Open position: Long 3 MNQ @ 21000.00
  - Current quote: 21000.00 (no unrealized P&L)
  - Risk config:
      daily_unrealized_loss:
        loss_limit: 300.00
        scope: "total"
        action: "close_all_and_lockout"
```

#### When

```yaml
Step 1: Market drops gradually
  - t=0s: MarketQuote (lastPrice: 21000.00) → unrealized: $0
  - t=5s: MarketQuote (lastPrice: 20950.00) → unrealized: -$150
  - t=10s: MarketQuote (lastPrice: 20900.00) → unrealized: -$300
  - t=15s: MarketQuote (lastPrice: 20850.00) → unrealized: -$450 → BREACH

Step 2: RULE-004 triggered by quote update
  - Event router receives MarketQuote event
  - Routes to RULE-004 (unrealized loss rule)
  - Calculates total unrealized P&L

Step 3: Enforcement executes
  - Close all positions
  - Set lockout
```

#### Then

```yaml
Expected Outcomes:
  1. Quotes Update Gradually:
     - ✅ t=0s: Quote Tracker updates MNQ = 21000.00
         - RULE-004: unrealized = $0
         - No breach
     - ✅ t=5s: Quote Tracker updates MNQ = 20950.00
         - RULE-004: unrealized = -$150
         - -150 > -300 → No breach
     - ✅ t=10s: Quote Tracker updates MNQ = 20900.00
         - RULE-004: unrealized = -$300
         - -300 == -300 → No breach (at limit)
     - ✅ t=15s: Quote Tracker updates MNQ = 20850.00
         - RULE-004: unrealized = -$450
         - -450 < -300 → BREACH

  2. Event Routing (MarketQuote):
     - ✅ SignalR Market Hub receives event
     - ✅ Quote Tracker: update_quote("F.US.MNQ", 20850.00)
     - ✅ Event Router: route_event("MarketQuote", payload)
     - ✅ Routes to: RULE-004, RULE-005, RULE-012 (only these check quotes)
     - ✅ Logged: "MarketQuote event: MNQ = 20850.00"

  3. Rule Evaluation:
     - ✅ RULE-004.check_with_current_prices():
         - Get position: Long 3 MNQ @ 21000.00
         - Get quote: 20850.00
         - Calculate: -$450
         - Check: -450 < -300 → BREACH
     - ✅ Logged: "RULE-004: Unrealized loss breach (-$450 > -$300)"

  4. Enforcement:
     - ✅ actions.close_all_positions(12345)
     - ✅ actions.cancel_all_orders(12345)
     - ✅ lockout_manager.set_lockout(12345, until=17:00)
     - ✅ Positions closed at market price (20850.00)
     - ✅ Realized loss: -$450 (unrealized → realized)

  5. P&L Impact:
     - ✅ Before: Unrealized -$450, Realized $0
     - ✅ After close: Unrealized $0, Realized -$450
     - ✅ PNL Tracker updates daily P&L: -$450
     - ✅ May trigger RULE-003 if daily limit also breached

  6. Trader CLI Display:
     - ✅ Shows quote update: "MNQ: 20850.00 (-150 pts)"
     - ✅ Shows unrealized P&L: "-$450" (red, flashing)
     - ✅ Position closed notification
     - ✅ Lockout banner appears immediately
```

---

### E2E-015: Multiple Positions, Different Quote Updates

**Test ID:** E2E-015
**Category:** SignalR Event Workflow
**Priority:** Medium
**Estimated Duration:** 2 minutes

#### Given

```yaml
Initial State:
  - Daemon running
  - Open positions:
      Position 1: Long 2 MNQ @ 21000.00
      Position 2: Long 1 ES @ 5800.00
  - Subscribed to quotes: MNQ, ES
  - Risk config:
      daily_unrealized_loss:
        loss_limit: 300.00
        scope: "total"  # Combined loss
```

#### When

```yaml
Step 1: Both markets drop simultaneously
  - t=0s: MarketQuote (MNQ: 20900.00) → MNQ unrealized: -$200
  - t=1s: MarketQuote (ES: 5792.00) → ES unrealized: -$200
  - Total unrealized: -$400 → BREACH

Step 2: RULE-004 triggered
  - Calculate combined unrealized P&L
  - -$400 < -$300 → BREACH
```

#### Then

```yaml
Expected Outcomes:
  1. First Quote (MNQ Drops):
     - ✅ Quote Tracker: MNQ = 20900.00
     - ✅ RULE-004 calculates:
         - Position 1 (MNQ): -$200
         - Position 2 (ES): $0 (no new quote yet)
         - Total: -$200
     - ✅ -200 > -300 → No breach yet

  2. Second Quote (ES Drops):
     - ✅ Quote Tracker: ES = 5792.00
     - ✅ RULE-004 calculates:
         - Position 1 (MNQ): -$200 (from earlier quote)
         - Position 2 (ES): -$200 (new quote)
         - Total: -$400
     - ✅ -400 < -300 → BREACH

  3. Enforcement:
     - ✅ Close all positions (both MNQ and ES)
     - ✅ REST API calls:
         - POST /api/Position/closeContract (MNQ x2)
         - POST /api/Position/closeContract (ES x1)
     - ✅ Lockout set

  4. Market Hub Unsubscribes:
     - ✅ No more positions → unsubscribe from both:
         - market_hub.unsubscribe("F.US.MNQ")
         - market_hub.unsubscribe("F.US.ES")
     - ✅ No more quote events received
```

---

### E2E-016: Order Event Triggers Stop-Loss Detection

**Test ID:** E2E-016
**Category:** SignalR Event Workflow
**Priority:** High
**Estimated Duration:** 1 minute

#### Given

```yaml
Initial State:
  - Daemon running
  - Position: Long 2 MNQ @ 21000.00
  - Grace timer active (25 seconds remaining)
  - Risk config:
      no_stop_loss_grace:
        grace_period_seconds: 30
```

#### When

```yaml
Step 1: Trader places stop-loss order
  - SignalR: GatewayUserOrder
    {
      "id": 1003,
      "accountId": 12345,
      "contractId": "CON.F.US.MNQ.U25",
      "type": 3,  # Stop
      "side": 2,  # Sell
      "size": 2,
      "stopPrice": 20980.00,
      "state": 1  # Working
    }

Step 2: Event router processes order
  - State Manager tracks order
  - Routes to RULE-008

Step 3: RULE-008 validates stop-loss
  - Checks: Type=Stop, Side=opposite, Contract=match, Size=match
  - All valid → Cancel grace timer
```

#### Then

```yaml
Expected Outcomes:
  1. Order Event Arrives:
     - ✅ SignalR User Hub receives GatewayUserOrder
     - ✅ State Manager: track order (id=1003)
     - ✅ Event Router: route to RULE-008
     - ✅ Logged: "Order event: Stop-loss for MNQ"

  2. RULE-008 Validation:
     - ✅ Find position: Long 2 MNQ
     - ✅ Find order: id=1003
     - ✅ Validate stop-loss:
         - Type: 3 (Stop) ✅
         - Side: 2 (Sell, opposite of Long) ✅
         - Contract: MNQ (matches position) ✅
         - Size: 2 (matches position) ✅
         - State: 1 (Working) ✅
     - ✅ All checks pass → Valid stop-loss
     - ✅ Logged: "RULE-008: Valid stop-loss detected for position"

  3. Grace Timer Cancelled:
     - ✅ timer_manager.cancel_timer("no_sl_grace_12345_5001")
     - ✅ Timer removed from active timers
     - ✅ Logged: "Grace timer cancelled - stop-loss placed"

  4. No Enforcement:
     - ✅ No breach
     - ✅ No lockout
     - ✅ Position remains open
     - ✅ Stop-loss order remains active

  5. Trader CLI Display:
     - ✅ Grace timer disappears
     - ✅ Shows: "✅ Stop-loss active @ 20980.00"
     - ✅ Position list shows SL price:
         "Long 2 MNQ @ 21000.00 | SL: 20980.00"
```

---

### E2E-017: Account Event Triggers Auth Loss Guard

**Test ID:** E2E-017
**Category:** SignalR Event Workflow
**Priority:** Low
**Estimated Duration:** 1 minute

#### Given

```yaml
Initial State:
  - Daemon running
  - Position: Long 1 ES
  - Risk config:
      auth_loss_guard:
        enabled: true
        action: "close_all_and_lockout"
```

#### When

```yaml
Step 1: TopstepX gateway sends suspicious account event
  - SignalR: GatewayUserAccount
    {
      "accountId": 12345,
      "eventType": "AuthorizationLost",  # Suspicious
      "timestamp": "2025-01-17T14:30:00Z"
    }

Step 2: Event router processes
  - Routes to RULE-010
  - RULE-010 detects auth event

Step 3: Enforcement executes (defensive)
  - Close all positions immediately
  - Lock account permanently
```

#### Then

```yaml
Expected Outcomes:
  1. Event Detection:
     - ✅ SignalR User Hub receives GatewayUserAccount
     - ✅ Event Router: route to RULE-010
     - ✅ Logged: "Account event: AuthorizationLost"

  2. RULE-010 Analysis:
     - ✅ Check event type: "AuthorizationLost"
     - ✅ Signature: matches auth loss pattern
     - ✅ BREACH: Potential auth bypass detected
     - ✅ Logged: "RULE-010: Auth loss event detected - defensive close"

  3. Enforcement:
     - ✅ actions.close_all_positions(12345)
     - ✅ REST API: POST /api/Position/closeContract (ES)
     - ✅ lockout_manager.set_lockout(12345, permanent=True)
     - ✅ Logged: "CRITICAL: Account 12345 permanently locked (auth loss)"

  4. Permanent Lockout:
     - ✅ Lockout with until=None (permanent)
     - ✅ SQLite lockouts table: locked_until=NULL
     - ✅ Manual admin intervention required to unlock

  5. Trader CLI Display:
     - ✅ Shows: "🔴 ACCOUNT LOCKED - Authorization lost"
     - ✅ Shows: "Contact administrator to unlock"
     - ✅ No countdown timer (permanent)
```

---

### E2E-018: High-Frequency Quote Updates (Stress Test)

**Test ID:** E2E-018
**Category:** SignalR Event Workflow
**Priority:** Medium
**Estimated Duration:** 30 seconds

#### Given

```yaml
Initial State:
  - Daemon running
  - Position: Long 5 MNQ @ 21000.00
  - Risk config: All rules enabled
```

#### When

```yaml
Step 1: Simulate 100 quote updates in 10 seconds
  - Market Hub sends 10 quotes/second
  - Prices fluctuate: 20995 → 21005 → 20998 → 21003...

Step 2: Daemon processes all quotes
  - Quote Tracker updates prices
  - RULE-004, RULE-005 evaluate on each quote
  - No breaches (prices within range)

Step 3: Verify performance
  - All quotes processed
  - No missed events
  - Latency < 10ms per quote
```

#### Then

```yaml
Expected Outcomes:
  1. Quote Processing:
     - ✅ 100 quotes received in 10 seconds
     - ✅ Quote Tracker updates: 100 updates
     - ✅ All quotes logged to api.log
     - ✅ No quotes dropped

  2. Rule Evaluation:
     - ✅ RULE-004 evaluated 100 times
     - ✅ RULE-005 evaluated 100 times
     - ✅ Average latency: < 5ms per quote
     - ✅ Max latency: < 10ms

  3. Performance Metrics:
     - ✅ CPU usage: < 20% during burst
     - ✅ Memory usage: stable (no leak)
     - ✅ No race conditions
     - ✅ No thread deadlocks

  4. State Consistency:
     - ✅ Quote Tracker: final price = last quote
     - ✅ Position unchanged (no enforcement)
     - ✅ All background threads running

  5. Trader CLI Display:
     - ✅ Price updates smoothly (no lag)
     - ✅ Unrealized P&L updates in real-time
     - ✅ No UI freezing
```

---

## Daily Reset Workflows

### E2E-019: Daily Reset at 5:00 PM

**Test ID:** E2E-019
**Category:** Daily Reset
**Priority:** Critical
**Estimated Duration:** 2 minutes (time-accelerated)

#### Given

```yaml
Initial State:
  - Daemon running
  - Current time: 4:59:50 PM (10 seconds before reset)
  - Account state:
      Daily P&L: -$450
      Active lockout: Daily loss limit (until 5:00 PM)
      Trade count: 15 trades today
  - Reset config:
      reset_time: "17:00"  # 5:00 PM
      timezone: "America/New_York"
```

#### When

```yaml
Step 1: Wait for reset time
  - Reset Scheduler checks every 10 seconds
  - Clock hits 5:00:00 PM

Step 2: Reset triggered
  - reset_scheduler.check_reset_times() → [12345]
  - reset_scheduler.reset_daily_counters(12345)

Step 3: All counters reset
  - PNL Tracker: reset daily P&L
  - Lockout Manager: clear daily lockouts
  - Trade Counter: reset trade count
```

#### Then

```yaml
Expected Outcomes:
  1. Reset Detection:
     - ✅ Current time: 17:00:00
     - ✅ Reset time: 17:00:00
     - ✅ reset_scheduler.check_reset_times() → [12345]
     - ✅ Logged: "Daily reset triggered for account 12345"

  2. P&L Reset:
     - ✅ pnl_tracker.reset_daily_pnl(12345)
     - ✅ SQLite daily_pnl table:
         - Before: realized_pnl=-450, date=2025-01-17
         - After: realized_pnl=0, date=2025-01-18
     - ✅ Logged: "Daily P&L reset: -$450 → $0"

  3. Lockout Cleared:
     - ✅ lockout_manager.clear_daily_lockouts(12345)
     - ✅ SQLite lockouts table:
         - Before: is_locked=1, reason="Daily loss limit"
         - After: Entry removed
     - ✅ is_locked_out(12345) → False
     - ✅ Logged: "Daily lockout cleared"

  4. Trade Counter Reset:
     - ✅ trade_counter.reset_daily_count(12345)
     - ✅ SQLite trade_history:
         - Before: 15 trades for date=2025-01-17
         - After: 0 trades for date=2025-01-18
     - ✅ Logged: "Trade count reset: 15 → 0"

  5. Trader CLI Display:
     - ✅ Lockout banner disappears immediately
     - ✅ Shows: "🟢 DAILY RESET COMPLETE"
     - ✅ Shows: "Daily P&L: $0.00"
     - ✅ Shows: "Trades today: 0"
     - ✅ Shows: "OK to trade"

  6. Next Trade Allowed:
     - ✅ Trader places order at 5:00:01 PM
     - ✅ Event processed normally
     - ✅ No lockout
```

---

### E2E-020: Holiday Detection (No Reset)

**Test ID:** E2E-020
**Category:** Daily Reset
**Priority:** Medium
**Estimated Duration:** 1 minute

#### Given

```yaml
Initial State:
  - Daemon running
  - Current date: July 4, 2025 (Independence Day)
  - Holiday config:
      holidays:
        - date: "2025-07-04"
          name: "Independence Day"
  - Session config:
      respect_holidays: true
```

#### When

```yaml
Step 1: Trader tries to place order
  - SignalR: GatewayUserPosition event

Step 2: RULE-009 checks holiday
  - reset_scheduler.is_holiday("2025-07-04") → True
  - Session block rule triggers
```

#### Then

```yaml
Expected Outcomes:
  1. Holiday Detection:
     - ✅ reset_scheduler.is_holiday("2025-07-04") → True
     - ✅ Logged: "Holiday detected: Independence Day"

  2. RULE-009 Enforcement:
     - ✅ Session block rule triggers
     - ✅ actions.close_all_positions(12345) (if any open)
     - ✅ lockout_manager.set_lockout(until=next_trading_day)
     - ✅ Next trading day: 2025-07-07 (Monday) 9:30 AM

  3. No Daily Reset:
     - ✅ reset_scheduler does NOT reset on holiday
     - ✅ P&L persists from previous day
     - ✅ Lockouts remain active

  4. Trader CLI Display:
     - ✅ Shows: "🔴 HOLIDAY - Market closed"
     - ✅ Shows: "Independence Day"
     - ✅ Shows: "Resumes: Monday 7/7 @ 9:30 AM"
```

---

### E2E-021: Weekend Lockout Until Monday

**Test ID:** E2E-021
**Category:** Daily Reset
**Priority:** Medium
**Estimated Duration:** 1 minute (simulated)

#### Given

```yaml
Initial State:
  - Daemon running
  - Current time: Friday 4:00 PM
  - Session end triggered
  - Weekend approaching
```

#### When

```yaml
Step 1: Session ends Friday 4:00 PM
  - RULE-009: close_positions_at_session_end
  - Set lockout until Monday 9:30 AM

Step 2: Saturday/Sunday
  - Daemon continues running (monitoring)
  - No events expected
  - Lockout remains active

Step 3: Monday 9:30 AM
  - Lockout expires automatically
  - Trading allowed
```

#### Then

```yaml
Expected Outcomes:
  1. Friday Session End:
     - ✅ Time: Friday 16:00:00
     - ✅ RULE-009: session end enforcement
     - ✅ Close all positions
     - ✅ Set lockout:
         - Until: Monday 09:30:00
         - Duration: ~65.5 hours (Fri 4pm → Mon 9:30am)

  2. Weekend (Daemon Running):
     - ✅ Daemon remains active
     - ✅ No SignalR events (market closed)
     - ✅ Lockout remains active
     - ✅ All background threads running
     - ✅ State persisted to SQLite

  3. Monday Morning Unlock:
     - ✅ Time: Monday 09:30:00
     - ✅ Lockout Manager: check_expired_lockouts()
     - ✅ Lockout expired → clear_lockout(12345)
     - ✅ Logged: "Weekend lockout cleared - Monday session open"

  4. Trader CLI Display:
     - ✅ Friday 4pm: "🔴 Weekend - Resumes Monday 9:30 AM"
     - ✅ Saturday/Sunday: Same message, countdown continues
     - ✅ Monday 9:30am: "🟢 OK TO TRADE - Session open"
```

---

## Authentication & Token Management

### E2E-022: Token Refresh at 20 Hours

**Test ID:** E2E-022
**Category:** Authentication
**Priority:** High
**Estimated Duration:** 30 seconds (simulated)

#### Given

```yaml
Initial State:
  - Daemon running for 20 hours
  - Current JWT token:
      Issued: 20 hours ago
      Expires: 24 hours from issue
      Time remaining: 4 hours
  - Token refresh thread active
```

#### When

```yaml
Step 1: Token refresh checker runs (hourly)
  - Check token expiry: 4 hours remaining
  - < 4 hours threshold → Trigger refresh

Step 2: Refresh token via API
  - Call: auth.validate_and_refresh_token(current_token)
  - Receive new token (valid 24 hours)

Step 3: Update connections
  - User Hub: update_token(new_token)
  - Market Hub: update_token(new_token)
  - REST client: update_token(new_token)
```

#### Then

```yaml
Expected Outcomes:
  1. Token Expiry Detection:
     - ✅ Token refresh checker thread running
     - ✅ Check runs every hour
     - ✅ Token expires in: 4 hours
     - ✅ 4 hours < 4 hour threshold → Refresh needed
     - ✅ Logged: "Token refresh triggered (4h remaining)"

  2. API Token Refresh:
     - ✅ Call: auth.validate_and_refresh_token()
     - ✅ REST API: POST /api/Auth/validateKey
     - ✅ Response: new JWT token
     - ✅ New token valid: 24 hours
     - ✅ Logged: "Token refreshed successfully"

  3. Connection Updates:
     - ✅ user_hub.update_token(new_token)
     - ✅ market_hub.update_token(new_token)
     - ✅ rest_client.set_tokens({12345: new_token})
     - ✅ SignalR connections remain active (no disconnect)
     - ✅ Logged: "All connections updated with new token"

  4. Monitoring Continues:
     - ✅ No interruption to event processing
     - ✅ No disconnections
     - ✅ No missed events
     - ✅ State persisted correctly

  5. Verification:
     - ✅ account_tokens[12345] = new_token
     - ✅ Next refresh: 20 hours from now
     - ✅ Daemon remains healthy
```

---

### E2E-023: Authentication Failure on Startup

**Test ID:** E2E-023
**Category:** Authentication
**Priority:** High
**Estimated Duration:** 10 seconds

#### Given

```yaml
Initial State:
  - Daemon stopped
  - Test account configured:
      account_id: 12345
      username: "test_trader"
      api_key: "INVALID_KEY"  # Invalid
```

#### When

```yaml
Step 1: Start daemon
  - Daemon begins startup sequence
  - Phase 4: Authenticate accounts (Step 16)

Step 2: Authentication fails
  - Call: auth.authenticate("test_trader", "INVALID_KEY")
  - TopstepX API returns 401 Unauthorized

Step 3: Startup fails
  - Log error
  - Exit daemon with error code
```

#### Then

```yaml
Expected Outcomes:
  1. Startup Sequence Begins:
     - ✅ Steps 1-15 complete (config, database, modules)
     - ✅ Reached Step 16: Authenticate accounts
     - ✅ Logged: "Authenticating account 12345..."

  2. Authentication Failure:
     - ✅ REST API call: POST /api/Auth/validateKey
     - ✅ Response: 401 Unauthorized
     - ✅ Exception raised: AuthenticationError
     - ✅ Logged: "❌ Authentication failed for account 12345: Invalid API key"

  3. Startup Aborts:
     - ✅ Daemon does NOT continue to Step 17+
     - ✅ No SignalR connections established
     - ✅ No background threads started
     - ✅ Exit with code 1 (error)

  4. User Feedback:
     - ✅ Admin CLI shows:
         "❌ Daemon failed to start"
         "Error: Authentication failed for account 12345"
         "Check config/accounts.yaml - verify API key"
     - ✅ Error logged to logs/error.log

  5. Recovery:
     - ✅ Admin fixes API key in accounts.yaml
     - ✅ Admin restarts daemon
     - ✅ Authentication succeeds
     - ✅ Daemon starts normally
```

---

### E2E-024: Multi-Account Token Management

**Test ID:** E2E-024
**Category:** Authentication
**Priority:** Medium
**Estimated Duration:** 1 minute

#### Given

```yaml
Initial State:
  - Daemon running
  - Multiple accounts:
      Account 1: 12345 (token expires in 2 hours)
      Account 2: 67890 (token expires in 22 hours)
  - Token refresh thread active
```

#### When

```yaml
Step 1: Token refresh checker runs
  - Check all account tokens
  - Account 1: 2 hours < 4 hours → Refresh
  - Account 2: 22 hours > 4 hours → Skip

Step 2: Refresh Account 1 only
  - Call: auth.validate_and_refresh_token(token1)
  - Update Account 1 connections

Step 3: Account 2 unchanged
  - Keep existing token
  - No API calls
```

#### Then

```yaml
Expected Outcomes:
  1. Token Expiry Check (All Accounts):
     - ✅ account_tokens = {12345: token1, 67890: token2}
     - ✅ Check token1 expiry: 2 hours remaining
     - ✅ Check token2 expiry: 22 hours remaining
     - ✅ Logged: "Account 12345: refresh needed (2h remaining)"
     - ✅ Logged: "Account 67890: token OK (22h remaining)"

  2. Selective Refresh:
     - ✅ Refresh token1 only
     - ✅ REST API: POST /api/Auth/validateKey (for account 12345)
     - ✅ New token1 received
     - ✅ NO API call for account 67890 (unnecessary)

  3. Connection Updates:
     - ✅ Account 1 connections updated with new token1
     - ✅ Account 2 connections unchanged (still using token2)
     - ✅ No disconnections for either account

  4. Verification:
     - ✅ account_tokens = {12345: new_token1, 67890: token2}
     - ✅ Both accounts monitoring correctly
     - ✅ All events processed normally
```

---

## Network & Recovery Workflows

### E2E-025: SignalR Disconnection and Reconnection

**Test ID:** E2E-025
**Category:** Network Recovery
**Priority:** Critical
**Estimated Duration:** 30 seconds

#### Given

```yaml
Initial State:
  - Daemon running
  - SignalR User Hub connected
  - Active position: Long 2 MNQ
  - Network: stable
```

#### When

```yaml
Step 1: Network interruption
  - Simulate network drop
  - SignalR User Hub disconnects

Step 2: SignalR auto-reconnect
  - SignalR client detects disconnection
  - Attempts reconnect (5 attempts)

Step 3: Reconnection succeeds
  - User Hub reconnects on 2nd attempt
  - Resume event processing

Step 4: Verify state consistency
  - Position still tracked
  - No events missed (or minimal loss)
```

#### Then

```yaml
Expected Outcomes:
  1. Disconnection Detection:
     - ✅ SignalR connection closed
     - ✅ user_hub.is_connected() → False
     - ✅ Logged: "⚠️ User Hub disconnected - attempting reconnect"

  2. Auto-Reconnect Attempts:
     - ✅ Attempt 1 (after 5 seconds): Failed
     - ✅ Attempt 2 (after 10 seconds): Success
     - ✅ user_hub.is_connected() → True
     - ✅ Logged: "✅ User Hub reconnected (attempt 2)"

  3. Event Processing Resumes:
     - ✅ SignalR event handlers active
     - ✅ Next event processed normally
     - ✅ Event: GatewayUserPosition (received after reconnect)
     - ✅ Position still tracked in State Manager

  4. State Consistency:
     - ✅ In-memory state unchanged:
         - Position: Long 2 MNQ @ 21000.00
         - Daily P&L: -$250
         - Lockouts: None
     - ✅ No data loss (state persisted during disconnection)

  5. Event Loss Analysis:
     - ✅ Events during disconnection (~10 seconds): potentially lost
     - ✅ Impact: minimal (quotes will resume, positions rebuild on next event)
     - ✅ Acceptable loss window: < 15 seconds

  6. Daemon Remains Healthy:
     - ✅ All background threads running
     - ✅ No crash or restart
     - ✅ Trader CLI shows: "⚠️ Connection restored"
```

---

### E2E-026: REST API Failure During Enforcement

**Test ID:** E2E-026
**Category:** Network Recovery
**Priority:** High
**Estimated Duration:** 30 seconds

#### Given

```yaml
Initial State:
  - Daemon running
  - Position: Long 3 MNQ @ 21000.00
  - Daily P&L: -$480
  - About to breach daily loss limit
```

#### When

```yaml
Step 1: Breach triggers enforcement
  - Trade P&L: -$50
  - Daily P&L: -$530 → BREACH
  - RULE-003: close_all_and_lockout

Step 2: REST API fails (network error)
  - Call: POST /api/Position/closeContract
  - Response: 500 Internal Server Error (or timeout)

Step 3: Retry logic executes
  - Retry 1: Failed
  - Retry 2: Failed
  - Retry 3: Success (API recovers)

Step 4: Enforcement completes
  - Position closed on 3rd attempt
  - Lockout set
```

#### Then

```yaml
Expected Outcomes:
  1. Rule Breach:
     - ✅ RULE-003: -$530 <= -$500 → BREACH
     - ✅ Enforcement triggered
     - ✅ Logged: "RULE-003: Daily loss breach - closing positions"

  2. REST API Failure (Attempts 1-2):
     - ✅ Call: POST /api/Position/closeContract
     - ✅ Response: 500 Internal Server Error
     - ✅ Exception caught: APIError
     - ✅ Logged: "❌ API call failed (attempt 1/3) - retrying in 2s"
     - ✅ Wait 2 seconds
     - ✅ Retry: POST /api/Position/closeContract
     - ✅ Response: Timeout (30s)
     - ✅ Logged: "❌ API call failed (attempt 2/3) - retrying in 2s"

  3. REST API Success (Attempt 3):
     - ✅ Wait 2 seconds
     - ✅ Retry: POST /api/Position/closeContract
     - ✅ Response: 200 OK (API recovered)
     - ✅ Position closed successfully
     - ✅ Logged: "✅ Position closed (attempt 3/3)"

  4. Enforcement Completes:
     - ✅ actions.close_all_positions() → True
     - ✅ State Manager: position removed
     - ✅ lockout_manager.set_lockout(12345, until=17:00)
     - ✅ Logged: "Enforcement complete - lockout set"

  5. Trader CLI Display:
     - ✅ Shows: "⚠️ Enforcement delayed (API issues)"
     - ✅ Shows: "Position closed after 3 attempts"
     - ✅ Shows lockout banner

  6. Failure Scenario (All Retries Fail):
     - If all 3 retries fail:
         - ✅ actions.close_all_positions() → False
         - ✅ Logged: "❌ CRITICAL: Enforcement failed after 3 attempts"
         - ✅ Lockout still set (defensive)
         - ✅ Position remains open (manual intervention required)
         - ✅ Alert admin via critical log
```

---

### E2E-027: Database Corruption Recovery

**Test ID:** E2E-027
**Category:** Network Recovery
**Priority:** Medium
**Estimated Duration:** 1 minute

#### Given

```yaml
Initial State:
  - Daemon running
  - SQLite database: data/state.db
  - Database becomes corrupted (simulated)
```

#### When

```yaml
Step 1: Database write fails
  - State writer thread attempts batch write
  - SQLite error: "database disk image is malformed"

Step 2: Corruption detected
  - Run: PRAGMA integrity_check
  - Result: corruption detected

Step 3: Recovery procedure
  - Backup corrupted database
  - Rebuild database (CREATE TABLES)
  - Re-sync state from TopstepX API
```

#### Then

```yaml
Expected Outcomes:
  1. Corruption Detection:
     - ✅ State writer: batch write fails
     - ✅ SQLite error: "database disk image is malformed"
     - ✅ Run: PRAGMA integrity_check → FAIL
     - ✅ Logged: "❌ CRITICAL: Database corruption detected"

  2. Backup Corrupted DB:
     - ✅ Copy: data/state.db → data/backups/state.db.corrupted.20250117
     - ✅ Logged: "Corrupted database backed up"

  3. Rebuild Database:
     - ✅ Delete: data/state.db
     - ✅ Create new: data/state.db
     - ✅ Run: CREATE TABLE IF NOT EXISTS (all 9 tables)
     - ✅ Logged: "Database rebuilt successfully"

  4. Re-Sync State:
     - ✅ Fetch from TopstepX API:
         - GET /api/Position/searchOpen → [positions]
         - GET /api/Order/searchOpen → [orders]
     - ✅ Populate State Manager
     - ✅ Write to new database
     - ✅ Logged: "State re-synced from API (5 positions, 2 orders)"

  5. Resume Monitoring:
     - ✅ State Manager populated with fresh data
     - ✅ Event processing resumes
     - ✅ Data loss: historical data only (recent state intact)

  6. Trader CLI Display:
     - ✅ Shows: "⚠️ Database recovered - historical data lost"
     - ✅ Shows current state (positions, P&L)
     - ✅ Note: Enforcement logs lost (not critical)
```

---

### E2E-028: Daemon Crash and Auto-Restart

**Test ID:** E2E-028
**Category:** Network Recovery
**Priority:** Critical
**Estimated Duration:** 30 seconds

#### Given

```yaml
Initial State:
  - Daemon running as Windows Service
  - Active position: Long 2 MNQ
  - Daily P&L: -$300
  - Active lockout: None
  - Windows Service configured: auto-restart on failure
```

#### When

```yaml
Step 1: Daemon crashes (unhandled exception)
  - Exception in main event loop
  - emergency_shutdown() executes

Step 2: Windows Service detects crash
  - Service status: STOPPED (error code 1)
  - Auto-restart policy triggers

Step 3: Daemon restarts
  - Execute 29-step startup sequence
  - Load state from SQLite

Step 4: Resume monitoring
  - SignalR reconnects
  - Continue processing events
```

#### Then

```yaml
Expected Outcomes:
  1. Daemon Crash:
     - ✅ Exception in main loop (simulated)
     - ✅ emergency_shutdown() executes:
         - Flush lockouts to SQLite
         - Flush daily P&L to SQLite
         - Exit with code 1
     - ✅ Logged: "EMERGENCY SHUTDOWN - Daemon crashed"
     - ✅ Process terminates

  2. Windows Service Auto-Restart:
     - ✅ Service Manager detects: STOPPED (code 1)
     - ✅ Auto-restart policy: restart after 5 seconds
     - ✅ Service status: START_PENDING
     - ✅ Logged (Windows Event Log): "Service restarting..."

  3. Daemon Restarts:
     - ✅ Execute 29-step startup sequence
     - ✅ Load state from SQLite:
         - Daily P&L: -$300
         - Positions: Long 2 MNQ (may be slightly stale)
         - Lockouts: None
     - ✅ All 29 steps complete
     - ✅ Service status: RUNNING
     - ✅ Logged: "Daemon restarted after crash - state recovered"

  4. State Verification:
     - ✅ pnl_tracker.get_daily_realized_pnl(12345) = -300
     - ✅ state_manager.get_position_count(12345) = 2
     - ✅ lockout_manager.is_locked_out(12345) = False

  5. Resume Monitoring:
     - ✅ SignalR User Hub reconnected
     - ✅ Market Hub reconnected
     - ✅ Event processing active
     - ✅ Next event processed correctly

  6. Downtime Analysis:
     - ✅ Downtime: ~10-15 seconds (emergency shutdown + restart)
     - ✅ Data loss: < 5 seconds of events (acceptable)
     - ✅ Critical state preserved (P&L, lockouts)

  7. Trader CLI Display:
     - ✅ Shows: "⚠️ Daemon restarted - monitoring resumed"
     - ✅ Shows current state (positions, P&L)
     - ✅ Connection status: "Connected"
```

---

## Performance Tests

### E2E-029: High-Volume Event Processing (100 Orders/Minute)

**Test ID:** E2E-029
**Category:** Performance
**Priority:** High
**Estimated Duration:** 2 minutes

#### Given

```yaml
Initial State:
  - Daemon running
  - Performance monitoring enabled
  - All 12 rules enabled
  - Test account active
```

#### When

```yaml
Step 1: Generate 100 events in 60 seconds
  - 60 GatewayUserOrder events (1/second)
  - 30 GatewayUserPosition events
  - 10 GatewayUserTrade events
  - 100 MarketQuote events (continuous)

Step 2: Daemon processes all events
  - State Manager updates
  - All rules evaluate
  - No breaches (all within limits)

Step 3: Measure performance
  - Event latency
  - CPU usage
  - Memory usage
  - Rule evaluation time
```

#### Then

```yaml
Expected Outcomes:
  1. Event Processing:
     - ✅ Total events: 200 events in 60 seconds
     - ✅ Average rate: 3.33 events/second
     - ✅ All events processed successfully
     - ✅ No events dropped

  2. Performance Metrics:
     - ✅ Average event latency: < 10ms
         - Receive event → State update → Rules → Return: < 10ms
     - ✅ Max event latency: < 50ms
     - ✅ 95th percentile: < 15ms
     - ✅ 99th percentile: < 30ms

  3. Rule Evaluation Time:
     - ✅ Average per rule: < 2ms
     - ✅ All 12 rules evaluated in < 20ms total
     - ✅ No rule takes > 10ms

  4. CPU Usage:
     - ✅ Average: < 20% CPU
     - ✅ Peak: < 40% CPU (during event bursts)
     - ✅ Idle (no events): < 5% CPU

  5. Memory Usage:
     - ✅ Start: 75 MB RAM
     - ✅ During test: 90 MB RAM
     - ✅ After test: 80 MB RAM (minor leak, acceptable)
     - ✅ No memory leaks detected

  6. State Manager Performance:
     - ✅ Position updates: < 1ms each
     - ✅ Order updates: < 1ms each
     - ✅ SQLite batched writes: every 5 seconds (no blocking)

  7. Thread Health:
     - ✅ All 6 threads running smoothly
     - ✅ No deadlocks
     - ✅ No race conditions
     - ✅ No thread crashes

  8. Trader CLI Performance:
     - ✅ UI updates in real-time
     - ✅ No lag or freezing
     - ✅ WebSocket broadcasts: < 5ms
```

---

### E2E-030: Long-Running Stability Test (8 Hours)

**Test ID:** E2E-030
**Category:** Performance
**Priority:** Medium
**Estimated Duration:** 8 hours (can be run overnight)

#### Given

```yaml
Initial State:
  - Daemon running
  - Performance monitoring enabled
  - All 12 rules enabled
  - Simulated trading day (8 hours)
```

#### When

```yaml
Step 1: Run daemon for 8 hours
  - Continuous event stream (moderate volume)
  - ~10 events/minute average
  - ~4,800 total events

Step 2: Monitor system health
  - CPU usage over time
  - Memory usage over time
  - Thread health
  - Database size

Step 3: Verify stability
  - No crashes
  - No memory leaks
  - No performance degradation
```

#### Then

```yaml
Expected Outcomes:
  1. Daemon Stability:
     - ✅ Uptime: 8 hours continuous
     - ✅ No crashes or restarts
     - ✅ All background threads running
     - ✅ SignalR connections stable

  2. Memory Usage (Over Time):
     - ✅ Start (t=0h): 75 MB
     - ✅ t=2h: 85 MB
     - ✅ t=4h: 90 MB
     - ✅ t=6h: 92 MB
     - ✅ t=8h: 95 MB
     - ✅ Growth rate: < 20 MB / 8 hours (acceptable)
     - ✅ No runaway memory leak

  3. CPU Usage (Average):
     - ✅ Average: < 10% CPU
     - ✅ Peak: < 30% CPU (during bursts)
     - ✅ Idle: < 5% CPU
     - ✅ No CPU usage spikes

  4. Event Processing:
     - ✅ Total events: ~4,800
     - ✅ All events processed
     - ✅ Average latency: < 10ms (stable over time)
     - ✅ No performance degradation

  5. Database Performance:
     - ✅ SQLite database size: ~500 KB (after 8 hours)
     - ✅ Write performance: stable
     - ✅ No locking errors
     - ✅ No corruption

  6. Thread Health:
     - ✅ All 6 threads alive and responsive
     - ✅ No thread hangs
     - ✅ No deadlocks
     - ✅ Thread CPU: balanced

  7. Token Refresh:
     - ✅ Token refreshed once (at 20 hours from initial)
     - ✅ No disconnections during refresh
     - ✅ Monitoring uninterrupted

  8. Daily Reset:
     - ✅ Reset triggered at 5:00 PM (if test includes)
     - ✅ P&L reset successfully
     - ✅ Lockouts cleared
     - ✅ No issues after reset

  9. Log Files:
     - ✅ daemon.log: ~5 MB (reasonable size)
     - ✅ api.log: ~10 MB (high event count)
     - ✅ enforcement.log: ~1 MB (depends on breaches)
     - ✅ No log rotation issues

  10. Trader CLI Connection:
      - ✅ WebSocket connections stable
      - ✅ Real-time updates working
      - ✅ No disconnections
      - ✅ UI responsive
```

---

## Test Data Requirements

### Mock Data Sets

```yaml
# accounts.yaml (test configuration)
accounts:
  - account_id: 12345
    username: "test_trader_1"
    api_key: "test_key_12345_valid"
  - account_id: 67890
    username: "test_trader_2"
    api_key: "test_key_67890_valid"

# risk_config.yaml (test configuration)
max_contracts:
  enabled: true
  limit: 5

daily_realized_loss:
  enabled: true
  limit: -500
  reset_time: "17:00"

# Mock contract metadata
mock_contracts:
  - contract_id: "CON.F.US.MNQ.U25"
    tick_size: 0.25
    tick_value: 0.50
    symbol_id: "F.US.MNQ"
    name: "Micro E-mini NASDAQ-100"

  - contract_id: "CON.F.US.ES.U25"
    tick_size: 0.25
    tick_value: 12.50
    symbol_id: "F.US.ES"
    name: "E-mini S&P 500"

# Mock SignalR events (samples)
mock_events:
  gateway_user_trade:
    - id: 7001
      accountId: 12345
      contractId: "CON.F.US.MNQ.U25"
      profitAndLoss: 49.75
      price: 21050.25
      size: 2

  gateway_user_position:
    - id: 5001
      accountId: 12345
      contractId: "CON.F.US.MNQ.U25"
      type: 1  # Long
      size: 2
      averagePrice: 21000.25

  market_quote:
    - symbol: "F.US.MNQ"
      lastPrice: 21000.00
      bestBid: 20999.75
      bestAsk: 21000.25
      timestamp: "2025-01-17T14:30:00Z"
```

### Test Fixtures

```python
# pytest fixtures for E2E tests

@pytest.fixture
def daemon_instance():
    """Create and start test daemon instance."""
    daemon = RiskManagerDaemon()
    daemon.start()
    yield daemon
    daemon.shutdown()

@pytest.fixture
def mock_topstepx_api():
    """Mock TopstepX REST API endpoints."""
    with responses.RequestsMock() as rsps:
        # Mock authentication
        rsps.add(
            responses.POST,
            "https://gateway.topstepx.com/api/Auth/validateKey",
            json={"token": "mock_jwt_token_12345"},
            status=200
        )

        # Mock position endpoints
        rsps.add(
            responses.POST,
            "https://gateway.topstepx.com/api/Position/searchOpen",
            json={"positions": []},
            status=200
        )

        rsps.add(
            responses.POST,
            "https://gateway.topstepx.com/api/Position/closeContract",
            json={"success": True},
            status=200
        )

        yield rsps

@pytest.fixture
def mock_signalr_hub():
    """Mock SignalR User Hub for event simulation."""
    hub = MockSignalRHub()
    yield hub
    hub.disconnect()

@pytest.fixture
def test_database():
    """Create temporary test database."""
    db_path = "data/test_state.db"
    conn = sqlite3.connect(db_path)
    create_tables(conn)
    yield conn
    conn.close()
    os.remove(db_path)
```

---

## Summary

**Total E2E Tests:** 30 comprehensive scenarios

**Coverage:**
- ✅ Complete trading lifecycles (daemon start → trade → enforcement → shutdown)
- ✅ All 12 risk rules validated in realistic workflows
- ✅ SignalR event processing (User Hub + Market Hub)
- ✅ Daily reset and lockout management
- ✅ Authentication and token refresh
- ✅ Network failures and recovery
- ✅ Performance and stability under load

**Test Execution Estimates:**
- Individual test: 30 seconds - 2 minutes
- Full E2E suite: ~2 hours (sequential)
- Parallel execution: ~30 minutes (with proper test isolation)

**Next Steps:**
1. Implement test fixtures and mock services
2. Set up CI/CD pipeline for automated E2E testing
3. Create test data generation scripts
4. Implement performance monitoring and metrics collection
5. Integrate with test management system

---

**Document Status:** ✅ Complete and Implementation Ready
**Last Updated:** 2025-10-22
**Version:** 1.0
