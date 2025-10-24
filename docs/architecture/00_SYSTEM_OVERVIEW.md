# Simple Risk Manager - Complete System Architecture

## Purpose

The **Simple Risk Manager** is a daemon-based risk management system designed to monitor and enforce trading rules for TopstepX futures trading accounts in real-time. It intercepts trading activity via API integration, evaluates positions and orders against a configurable set of risk rules, and automatically enforces protective actions (position closures, order cancellations, trader lockouts) to prevent rule violations.

**Key Capabilities:**
- Real-time position and order monitoring via REST + SignalR
- 12 configurable risk rules (contract limits, loss limits, trade frequency, etc.)
- Automated enforcement (close positions, cancel orders, trader lockouts)
- Dual CLI interfaces (trader status monitoring + admin configuration)
- SQLite persistence for state recovery
- Comprehensive logging and audit trail

## System Components

### 1. Daemon (Main Process)
**File:** `src/daemon/daemon.py` (not yet implemented)

The daemon is the central orchestrator that runs continuously as a background process. It:
- Loads configuration from YAML/JSON files
- Initializes API clients (REST + SignalR)
- Subscribes to real-time TopstepX events (positions, orders, trades)
- Routes events through the conversion layer
- Dispatches events to all active risk rules
- Executes enforcement actions when violations detected
- Persists state to SQLite for crash recovery
- Handles IPC communication with CLI tools

**Status:** ❌ Not Started
**Reference:** See detailed architecture in future `01_DAEMON_ARCHITECTURE.md`

---

### 2. Trader CLI
**File:** `src/cli/trader_cli.py` (not yet implemented)

A command-line interface for traders to monitor their account status without requiring admin privileges.

**Commands:**
- `status` - Current positions, orders, P&L, rule violations
- `monitor` - Live feed of risk rule checks and enforcement actions
- `history` - Recent trades, violations, lockouts

**Access:** Read-only, no configuration changes allowed
**IPC:** Communicates with daemon via socket/pipe
**Status:** ❌ Not Started
**Reference:** See detailed architecture in future `02_CLI_ARCHITECTURE.md`

---

### 3. Admin CLI
**File:** `src/cli/admin_cli.py` (not yet implemented)

A password-protected command-line interface for administrators to configure and manage the system.

**Commands:**
- `config edit` - Edit risk rules, accounts, thresholds
- `config reload` - Hot-reload configuration without daemon restart
- `lockout clear` - Clear trader lockouts
- `logs view` - View execution, error, and enforcement logs
- `daemon start/stop/restart` - Control daemon process

**Access:** Password-protected (bcrypt hash in config)
**IPC:** Communicates with daemon via socket/pipe
**Status:** ❌ Not Started
**Reference:** See detailed architecture in future `02_CLI_ARCHITECTURE.md`

---

### 4. Core Modules (9 modules)
**Directory:** `src/core/`

Nine foundational modules that provide shared functionality used by risk rules and the daemon.

**Modules:**
1. **StateManager** (`state_manager.py`) - ✅ COMPLETE (212 lines)
   - Centralized position and order tracking
   - In-memory cache with SQLite persistence
   - Handles GatewayUserPosition/Order events

2. **EnforcementActions** (`enforcement_actions.py`) - 🟡 STUB
   - Close positions, cancel orders, reduce positions
   - Coordinates with REST client for API calls

3. **LockoutManager** (`lockout_manager.py`) - 🟡 STUB
   - Trader lockout tracking with expiration
   - Cooldown period enforcement

4. **PnLTracker** (`pnl_tracker.py`) - 🟡 STUB
   - Daily realized/unrealized P&L tracking
   - Session reset on daily rollover

5. **QuoteTracker** (`quote_tracker.py`) - 🟡 STUB
   - Real-time market quote tracking
   - Used for unrealized P&L calculations

6. **ContractCache** (`contract_cache.py`) - 🟡 STUB
   - Contract metadata caching (tick size, tick value, etc.)
   - Reduces API calls for contract lookups

7. **TradeCounter** (`trade_counter.py`) - 🟡 STUB
   - Rolling window trade frequency tracking
   - Per-minute, per-hour, per-session counters

8. **TimerManager** (`timer_manager.py`) - 🟡 STUB
   - Cooldown and grace period timers
   - Expiration tracking

9. **ResetScheduler** (`reset_scheduler.py`) - 🟡 STUB
   - Daily state reset logic (4:45 PM CT)
   - Session boundary detection

**Status:** 1/9 Complete (StateManager), 8/9 Stubs
**Test Coverage:** 33.79% overall (87% for implemented rules)
**Reference:** See detailed module specs in future `03_CORE_MODULES.md`

---

### 5. Risk Rules (12 rules)
**Directory:** `src/rules/`

Twelve configurable risk enforcement rules that evaluate trading activity and trigger protective actions.

**Implemented (4/12):** ✅
- **RULE-001:** MaxContracts (147 lines, 6/6 tests, 84% coverage)
- **RULE-002:** MaxContractsPerInstrument (194 lines, 6/6 tests, 83% coverage)
- **RULE-006:** TradeFrequencyLimit (174 lines, 8/8 tests, 94% coverage)
- **RULE-011:** SymbolBlocks (210 lines, 4/6 tests, 88% coverage)

**Not Yet Implemented (8/12):** ❌
- RULE-003: DailyRealizedLoss
- RULE-004: DailyUnrealizedLoss
- RULE-005: MaxUnrealizedProfit
- RULE-007: CooldownAfterLoss
- RULE-008: NoStopLossGrace
- RULE-009: SessionBlockOutside
- RULE-010: AuthLossGuard
- RULE-012: TradeManagement

**Status:** 33% Complete (4/12 rules)
**Test Pass Rate:** 92.3% (24/26 tests passing)
**Reference:** See detailed rule specs in future `04_RISK_RULES.md`

---

### 6. API Integration
**Directory:** `src/api/`

Handles all communication with the TopstepX Gateway API (REST + SignalR WebSocket).

**Components:**

1. **REST Client** (`rest_client.py`) - ✅ COMPLETE (382 lines, 14/14 tests passing)
   - JWT authentication with token refresh
   - Rate limiting (200 req/60s sliding window)
   - Retry logic with exponential backoff
   - 7 endpoints: accounts, positions, orders, contracts, trades

2. **SignalR Client** (`signalr_client.py`) - ❌ NOT STARTED
   - WebSocket real-time event subscription
   - Auto-reconnection with backoff
   - Event parsing and dispatch
   - Handles: GatewayUserPosition, GatewayUserOrder, GatewayUserTrade, GatewayUserQuote

3. **Converters** (`converters.py`) - ✅ COMPLETE (476 lines, comprehensive tests)
   - API format (camelCase) ↔ Internal format (snake_case)
   - Handles all data types: accounts, orders, positions, trades, contracts, quotes
   - Enum conversions (order side, position type, order status)
   - Timestamp parsing (ISO 8601)

4. **Enums** (`enums.py`) - ✅ COMPLETE (305 lines)
   - API enum definitions (OrderType, OrderSide, OrderStatus, PositionType)
   - Conversion functions between API and internal formats

5. **Exceptions** (`exceptions.py`) - ✅ COMPLETE
   - AuthenticationError, APIError, NetworkError

**Status:** 60% Complete (REST + Converters done, SignalR pending)
**Reference:** See detailed API integration in future `05_API_INTEGRATION.md`

---

### 7. Configuration System
**Directory:** `config/`

YAML-based configuration files for risk rules, accounts, and logging.

**Configuration Files:**
- `risk_config.yaml` - Risk rule thresholds and enforcement modes
- `accounts.yaml` - Account IDs and trader assignments
- `logging.yaml` - Log levels, file paths, rotation settings
- `admin_password.yaml` - Bcrypt hash for admin CLI authentication

**Features:**
- Hot-reload without daemon restart
- Schema validation on load
- Environment variable substitution
- Default values for missing fields

**Status:** ✅ Specs Complete (YAML schemas defined)
**Reference:** See configuration specs in future `06_CONFIGURATION.md`

---

### 8. Converters (NEW - Just Built)
**File:** `src/api/converters.py` (476 lines)

A comprehensive data conversion layer that normalizes TopstepX API data into the internal backend format.

**Purpose:**
- TopstepX API returns camelCase fields (e.g., `accountId`, `limitPrice`, `unrealizedProfitLoss`)
- Internal backend uses snake_case (e.g., `account_id`, `limit_price`, `unrealized_pnl`)
- Converters provide bidirectional mapping for all API data types

**Key Functions:**
- `api_to_internal_account()` - Account data normalization
- `api_to_internal_order()` - Order data with state enum conversion
- `api_to_internal_position()` - Position data with type conversion
- `api_to_internal_trade()` - Trade execution data
- `api_to_internal_contract()` - Contract metadata
- `api_to_internal_quote()` - Market quote data
- `internal_to_api_order_request()` - Reverse conversion for placing orders
- `internal_to_api_position_close_request()` - Reverse conversion for closing positions

**Special Handling:**
- Timestamp parsing (ISO 8601 with timezone)
- Enum conversions (OrderSide: 0/1 → buy/sell, PositionType: 1/2 → long/short)
- Backward compatibility (supports old and new API field names)
- Graceful degradation (returns None/defaults for missing fields)

**Status:** ✅ COMPLETE AND TESTED (500-line test suite)

---

## Complete System Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              USER LAYER                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│  Trader CLI (read-only)           Admin CLI (password-protected)             │
│  - status                          - config edit/reload                       │
│  - monitor                         - lockout clear                            │
│  - history                         - logs view                                │
│                                    - daemon control                           │
└────────────┬────────────────────────────────┬─────────────────────────────────┘
             │ IPC (socket/pipe)              │ IPC (socket/pipe)
             │                                │
┌────────────▼────────────────────────────────▼─────────────────────────────────┐
│                          DAEMON PROCESS                                       │
│  ┌────────────────────────────────────────────────────────────────┐          │
│  │  Startup & Configuration                                       │          │
│  │  - Load config/risk_config.yaml                                │          │
│  │  - Load config/accounts.yaml                                   │          │
│  │  - Initialize logging (config/logging.yaml)                    │          │
│  │  - Restore state from SQLite (if crash recovery)               │          │
│  └────────────────────────────────────────────────────────────────┘          │
│                                                                                │
│  ┌─────────────────── API LAYER (src/api/) ──────────────────────┐          │
│  │                                                                 │          │
│  │  ┌──────────────┐              ┌─────────────────────┐        │          │
│  │  │ REST Client  │              │  SignalR Client     │        │          │
│  │  │ (COMPLETE)   │              │  (NOT STARTED)      │        │          │
│  │  ├──────────────┤              ├─────────────────────┤        │          │
│  │  │ - JWT auth   │              │ - WebSocket conn    │        │          │
│  │  │ - Rate limit │              │ - Auto-reconnect    │        │          │
│  │  │ - Retry logic│              │ - Event stream      │        │          │
│  │  │ - 7 endpoints│              │ - Subscribe to:     │        │          │
│  │  │              │              │   · GatewayUserPos  │        │          │
│  │  │              │              │   · GatewayUserOrd  │        │          │
│  │  │              │              │   · GatewayUserTrade│        │          │
│  │  │              │              │   · GatewayUserQuote│        │          │
│  │  └──────┬───────┘              └──────────┬──────────┘        │          │
│  │         │ camelCase                       │ camelCase         │          │
│  │         │                                 │                   │          │
│  │  ┌──────▼─────────────────────────────────▼──────────┐        │          │
│  │  │         CONVERTERS (COMPLETE)                     │        │          │
│  │  │  - api_to_internal_*() for all data types        │        │          │
│  │  │  - internal_to_api_*() for outbound requests     │        │          │
│  │  │  - Enum conversions (side, type, status)         │        │          │
│  │  │  - Timestamp parsing (ISO 8601)                  │        │          │
│  │  └──────┬───────────────────────────────────────────┘        │          │
│  │         │ snake_case                                          │          │
│  └─────────┼─────────────────────────────────────────────────────┘          │
│            │                                                                  │
│  ┌─────────▼─────────────────────────────────────────────────────┐          │
│  │  Event Router (NOT STARTED)                                   │          │
│  │  - Receives normalized events from converters                 │          │
│  │  - Dispatches to StateManager for tracking                    │          │
│  │  - Dispatches to all active risk rules for evaluation         │          │
│  └─────────┬─────────────────────────────────────────────────────┘          │
│            │                                                                  │
│  ┌─────────▼─────────────────────────────────────────────────────┐          │
│  │  STATE MANAGER (COMPLETE) + 8 OTHER MODULES (STUBS)           │          │
│  │                                                                 │          │
│  │  MOD-009: StateManager (✅ 212 lines, fully implemented)       │          │
│  │  - In-memory position/order cache                              │          │
│  │  - SQLite persistence                                           │          │
│  │  - get_positions(), get_orders(), get_position_count()         │          │
│  │                                                                 │          │
│  │  MOD-001: EnforcementActions (🟡 stub)                         │          │
│  │  MOD-002: LockoutManager (🟡 stub)                             │          │
│  │  MOD-003: TimerManager (🟡 stub)                               │          │
│  │  MOD-004: ResetScheduler (🟡 stub)                             │          │
│  │  MOD-005: PnLTracker (🟡 stub)                                 │          │
│  │  MOD-006: QuoteTracker (🟡 stub)                               │          │
│  │  MOD-007: ContractCache (🟡 stub)                              │          │
│  │  MOD-008: TradeCounter (🟡 stub)                               │          │
│  └─────────┬─────────────────────────────────────────────────────┘          │
│            │ state changes (positions, orders, trades, quotes)               │
│  ┌─────────▼─────────────────────────────────────────────────────┐          │
│  │  RISK RULES ENGINE (4/12 rules implemented)                   │          │
│  │                                                                 │          │
│  │  ✅ RULE-001: MaxContracts (147 lines, 84% cov)               │          │
│  │  ✅ RULE-002: MaxContractsPerInstrument (194 lines, 83% cov)  │          │
│  │  ✅ RULE-006: TradeFrequencyLimit (174 lines, 94% cov)        │          │
│  │  ✅ RULE-011: SymbolBlocks (210 lines, 88% cov)               │          │
│  │                                                                 │          │
│  │  ❌ RULE-003: DailyRealizedLoss (not started)                 │          │
│  │  ❌ RULE-004: DailyUnrealizedLoss (not started)               │          │
│  │  ❌ RULE-005: MaxUnrealizedProfit (not started)               │          │
│  │  ❌ RULE-007: CooldownAfterLoss (not started)                 │          │
│  │  ❌ RULE-008: NoStopLossGrace (not started)                   │          │
│  │  ❌ RULE-009: SessionBlockOutside (not started)               │          │
│  │  ❌ RULE-010: AuthLossGuard (not started)                     │          │
│  │  ❌ RULE-012: TradeManagement (not started)                   │          │
│  │                                                                 │          │
│  │  Each rule evaluates: check(account_id, config) -> violation? │          │
│  └─────────┬─────────────────────────────────────────────────────┘          │
│            │ violation detected                                              │
│  ┌─────────▼─────────────────────────────────────────────────────┐          │
│  │  ENFORCEMENT ENGINE (part of MOD-001, stub)                    │          │
│  │  - close_all_positions(account_id)                             │          │
│  │  - close_position(account_id, position_id)                     │          │
│  │  - reduce_positions_to_limit(account_id, limit)                │          │
│  │  - cancel_order(account_id, order_id)                          │          │
│  │  - set_lockout(account_id, duration_minutes)                   │          │
│  └─────────┬─────────────────────────────────────────────────────┘          │
│            │ enforcement actions (converted to API format)                   │
│  ┌─────────▼─────────────────────────────────────────────────────┐          │
│  │  REST Client (via converters)                                  │          │
│  │  - internal_to_api_order_cancel_request()                      │          │
│  │  - internal_to_api_position_close_request()                    │          │
│  │  - POST /api/Position/close                                    │          │
│  │  - DELETE /api/Order/{orderId}                                 │          │
│  └─────────┬─────────────────────────────────────────────────────┘          │
│            │ camelCase HTTP requests                                         │
└────────────┼─────────────────────────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────────────────────────┐
│                          TopstepX Gateway API                                 │
│  - REST: https://gateway.topstepx.com/api/                                   │
│  - SignalR: wss://gateway.topstepx.com/hubs/GatewayHub                      │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Examples

### Example 1: Position Update Event (Real-Time)

**Trigger:** Trader opens a new position on TopstepX platform

```
1. TopstepX SignalR Hub
   └─> Emits: GatewayUserPosition event
       {
         "accountId": 465,
         "id": 12345,
         "contractId": "CON.F.US.MNQ.U25",
         "type": 1,  // LONG
         "size": 2,
         "averagePrice": 18500.00,
         "creationTimestamp": "2025-10-23T10:30:00Z"
       }

2. SignalR Client (src/api/signalr_client.py) ❌ NOT IMPLEMENTED
   └─> Receives WebSocket event
   └─> Passes to Converter

3. Converter (src/api/converters.py) ✅ READY
   └─> api_to_internal_position(event)
   └─> Output:
       {
         "position_id": 12345,
         "account_id": 465,
         "contract_id": "CON.F.US.MNQ.U25",
         "position_type": "long",
         "quantity": 2,
         "average_price": 18500.00,
         "creation_timestamp": datetime(2025, 10, 23, 10, 30, 0)
       }

4. Event Router (src/daemon/event_router.py) ❌ NOT IMPLEMENTED
   └─> Dispatches to StateManager
   └─> Dispatches to all active risk rules

5. StateManager (src/core/state_manager.py) ✅ IMPLEMENTED
   └─> update_position(event)
   └─> Stores in memory: self.positions[465][12345] = {...}
   └─> Persists to SQLite: INSERT INTO positions (...)

6. Risk Rules Check (src/rules/)
   └─> RULE-001: MaxContracts.check(465, config)
       - Calls: state_manager.get_position_count(465)
       - Returns: 2 contracts total
       - Limit: 4 contracts (from risk_config.yaml)
       - Result: PASS (under limit)

   └─> RULE-002: MaxContractsPerInstrument.check(465, config)
       - Calls: state_manager.get_contract_count(465, "CON.F.US.MNQ.U25")
       - Returns: 2 MNQ contracts
       - Limit: 2 MNQ (from risk_config.yaml)
       - Result: PASS (at limit, no new orders allowed for MNQ)

   └─> RULE-011: SymbolBlocks.check(465, config)
       - Extracts symbol: "MNQ" from "CON.F.US.MNQ.U25"
       - Checks blocked list: ["RTY", "BTC"]
       - Result: PASS (MNQ not blocked)

7. All Rules Pass
   └─> No enforcement action needed
   └─> Position remains open
   └─> Trader can continue trading (within remaining limits)
```

---

### Example 2: CLI Status Command

**Trigger:** Trader runs `simple-risk status` from terminal

```
1. Trader CLI (src/cli/trader_cli.py) ❌ NOT IMPLEMENTED
   └─> Parses command: "status"
   └─> Sends IPC message to daemon: {"command": "get_status", "account_id": 465}

2. Daemon IPC Handler (src/daemon/daemon.py) ❌ NOT IMPLEMENTED
   └─> Receives message
   └─> Queries StateManager for current state

3. StateManager (src/core/state_manager.py) ✅ IMPLEMENTED
   └─> get_positions(465)
       Returns: [
         {"position_id": 12345, "contract_id": "MNQ.U25", "quantity": 2, ...},
         {"position_id": 12346, "contract_id": "ES.H25", "quantity": 1, ...}
       ]
   └─> get_orders(465)
       Returns: [
         {"order_id": 26974, "contract_id": "MNQ.U25", "side": "buy", "quantity": 1, ...}
       ]

4. PnLTracker (src/core/pnl_tracker.py) 🟡 STUB
   └─> get_daily_pnl(465)
       Returns: {"realized": 150.00, "unrealized": -75.00}

5. LockoutManager (src/core/lockout_manager.py) 🟡 STUB
   └─> is_locked_out(465)
       Returns: False

6. Daemon Formats Response
   └─> {
       "account_id": 465,
       "positions": [...],
       "orders": [...],
       "daily_pnl": {"realized": 150.00, "unrealized": -75.00},
       "locked_out": False,
       "total_contracts": 3,
       "recent_violations": []
     }

7. Trader CLI Displays
   └─> Formatted output:
       ╔═══════════════════════════════════════╗
       ║  Account Status - ID: 465             ║
       ╠═══════════════════════════════════════╣
       ║  Positions: 2                         ║
       ║  - MNQ.U25: 2 contracts (LONG)        ║
       ║  - ES.H25:  1 contract  (LONG)        ║
       ║                                       ║
       ║  Working Orders: 1                    ║
       ║  - MNQ.U25: BUY 1 @ STOP 18500        ║
       ║                                       ║
       ║  Daily P&L:                           ║
       ║  - Realized:   +$150.00               ║
       ║  - Unrealized: -$75.00                ║
       ║  - Net:        +$75.00                ║
       ║                                       ║
       ║  Status: ✅ ACTIVE                    ║
       ║  Total Contracts: 3/4 (75% used)      ║
       ╚═══════════════════════════════════════╝
```

---

### Example 3: Order Submission (Allowed)

**Trigger:** Trader places order via TopstepX platform (within limits)

```
1. TopstepX Platform
   └─> Trader clicks "Buy 1 MNQ @ Market"
   └─> TopstepX API processes order
   └─> Emits: GatewayUserOrder event (status: PENDING → OPEN)

2. SignalR Client ❌ NOT IMPLEMENTED
   └─> Receives order event:
       {
         "id": 26975,
         "accountId": 465,
         "contractId": "CON.F.US.MNQ.U25",
         "status": 1,  // OPEN
         "side": 0,    // BID (buy)
         "size": 1,
         "type": 2,    // MARKET
         "creationTimestamp": "2025-10-23T10:35:00Z"
       }

3. Converter ✅ READY
   └─> api_to_internal_order(event)
   └─> Output (snake_case):
       {
         "order_id": 26975,
         "account_id": 465,
         "contract_id": "CON.F.US.MNQ.U25",
         "state": InternalOrderState.ACTIVE,
         "side": "buy",
         "quantity": 1,
         "order_type": 2,  // MARKET
         "creation_timestamp": datetime(...)
       }

4. StateManager ✅ IMPLEMENTED
   └─> update_order(event)
   └─> Stores: self.orders[465][26975] = {...}

5. Risk Rules Check (BEFORE FILL)
   └─> RULE-001: MaxContracts.check(465)
       - Current positions: 3 contracts
       - Pending order: 1 contract
       - Total if filled: 4 contracts
       - Limit: 4 contracts
       - Result: PASS (would be at limit)

   └─> RULE-002: MaxContractsPerInstrument.check(465)
       - Current MNQ: 2 contracts
       - Pending: 1 MNQ contract
       - Total if filled: 3 MNQ
       - Limit: 2 MNQ
       - Result: ❌ VIOLATION (would exceed per-instrument limit!)

6. Enforcement Action ❌ NOT IMPLEMENTED (MOD-001 stub)
   └─> enforcement_actions.cancel_order(465, 26975)
       - Converts to API format:
         internal_to_api_order_cancel_request({"order_id": 26975})
       - Sends: DELETE /api/Order/26975
       - TopstepX cancels order before fill

7. Lockout (if configured) 🟡 NOT IMPLEMENTED
   └─> lockout_manager.set_cooldown(465, duration=5)
       - Blocks new orders for 5 minutes
       - Logs enforcement action

8. Trader Notification
   └─> CLI monitor displays:
       "⚠️ Order cancelled: RULE-002 MaxContractsPerInstrument violated"
       "MNQ limit: 2, attempted: 3, cooldown: 5 minutes"
```

---

### Example 4: Rule Violation (Daily Loss Limit)

**Trigger:** Trade closes with realized loss, pushing daily total over limit

```
1. TopstepX SignalR Hub
   └─> Emits: GatewayUserTrade event
       {
         "id": 54321,
         "accountId": 465,
         "contractId": "CON.F.US.ES.H25",
         "orderId": 26900,
         "side": 1,  // ASK (sell/close)
         "size": 1,
         "price": 4895.00,
         "profitAndLoss": -125.00,  // Realized loss
         "creationTimestamp": "2025-10-23T14:30:00Z"
       }

2. Converter ✅ READY
   └─> api_to_internal_trade(event)
   └─> Output:
       {
         "trade_id": 54321,
         "order_id": 26900,
         "account_id": 465,
         "contract_id": "CON.F.US.ES.H25",
         "side": "sell",
         "quantity": 1,
         "price": 4895.00,
         "profit_and_loss": -125.00,
         "execution_time": datetime(...)
       }

3. PnLTracker (src/core/pnl_tracker.py) 🟡 STUB (would need implementation)
   └─> record_trade(trade)
   └─> Update daily totals:
       - Previous realized: +150.00
       - This trade: -125.00
       - New total: +25.00

4. RULE-003: DailyRealizedLoss ❌ NOT IMPLEMENTED (would check)
   └─> get_daily_realized_loss(465)
       - Check if any single loss > threshold
       - Check if cumulative loss > threshold
       - Single loss: -125.00 < -100.00 limit
       - Result: ❌ VIOLATION (single loss exceeded)

5. Enforcement Action ❌ NOT IMPLEMENTED
   └─> enforcement_actions.close_all_positions(465)
       - Gets all open positions from StateManager
       - For each position:
         · internal_to_api_position_close_request(position)
         · POST /api/Position/close
       - Closes: MNQ position (2 contracts)

6. Lockout ❌ NOT IMPLEMENTED
   └─> lockout_manager.set_lockout(465, duration_minutes=1440)  // 24 hours
       - Prevents any new orders for rest of trading day
       - Trader can only flatten/reduce (if configured)

7. Logging (src/risk_manager/logging/) ✅ IMPLEMENTED
   └─> enforcement_logger.log_violation({
         "rule": "RULE-003",
         "account_id": 465,
         "violation": "Daily realized loss exceeded",
         "loss_amount": -125.00,
         "threshold": -100.00,
         "action": "close_all_positions",
         "lockout_duration": 1440
       })

8. Trader Notification
   └─> CLI monitor displays:
       "🛑 RULE VIOLATION: Daily Realized Loss Exceeded"
       "Single loss: -$125.00 (limit: -$100.00)"
       "Action: All positions closed, account locked for 24 hours"
       "Contact admin to clear lockout if needed"
```

---

## Implementation Status

### ✅ Completed Components

| Component | File | Lines | Tests | Coverage | Status |
|-----------|------|-------|-------|----------|--------|
| **REST Client** | `src/api/rest_client.py` | 382 | 14/14 ✅ | 75% | Production-ready |
| **Converters** | `src/api/converters.py` | 476 | All passing | N/A | Production-ready |
| **Enums** | `src/api/enums.py` | 305 | Covered | N/A | Production-ready |
| **StateManager** | `src/core/state_manager.py` | 212 | 8 tests | Good | Production-ready |
| **RULE-001** | `src/rules/max_contracts.py` | 147 | 6/6 ✅ | 84% | Production-ready |
| **RULE-002** | `src/rules/max_contracts_per_instrument.py` | 194 | 6/6 ✅ | 83% | Production-ready |
| **RULE-006** | `src/rules/trade_frequency_limit.py` | 174 | 8/8 ✅ | 94% | Production-ready |
| **RULE-011** | `src/rules/symbol_blocks.py` | 210 | 4/6 🟡 | 88% | Functional (2 test bugs) |
| **Logging** | `src/risk_manager/logging/` | ~400 | Integrated | Good | Production-ready |
| **Exceptions** | `src/api/exceptions.py` | Small | Covered | Good | Production-ready |
| **Symbol Utils** | `src/utils/symbol_utils.py` | 38 | Covered | Good | Production-ready |

**Total Implemented:** ~2,538 lines of production code
**Test Pass Rate:** 92.3% (24/26 passing)
**Average Coverage:** 87.25% (implemented modules)

---

### ⏳ In Progress

| Component | Status | Notes |
|-----------|--------|-------|
| **Test Suite** | 270 tests written | TDD phase, most fail with `NotImplementedError` |
| **Core Modules** | 8/9 stubs | Need implementation (MOD-001 through MOD-008) |

---

### ❌ Not Started

| Component | Priority | Dependencies | Est. Lines |
|-----------|----------|--------------|------------|
| **SignalR Client** | HIGH | None | ~300 |
| **Event Router** | HIGH | SignalR, Converters | ~200 |
| **Enforcement Engine** | HIGH | StateManager, REST Client | ~150 |
| **RULE-003 to RULE-012** | MEDIUM | Core Modules | ~1,400 (8 rules × 175 avg) |
| **Daemon Process** | MEDIUM | All of above | ~400 |
| **Trader CLI** | LOW | Daemon IPC | ~300 |
| **Admin CLI** | LOW | Daemon IPC | ~400 |
| **Database Layer** | LOW | Schema defined | ~200 |
| **Configuration Loader** | LOW | YAML schemas exist | ~150 |

**Total Remaining:** ~3,500 lines estimated

---

## Implementation Roadmap

### Phase 1: Foundation (COMPLETE ✅)
- ✅ REST API client with auth, rate limiting, retry
- ✅ Data converters (API ↔ Internal format)
- ✅ StateManager for position/order tracking
- ✅ 4 basic risk rules (RULE-001, 002, 006, 011)
- ✅ Logging infrastructure
- ✅ Test suite (270 tests written)

**Duration:** ~3 weeks (complete)
**Lines Written:** ~2,538 lines

---

### Phase 2: Real-Time Events (NEXT)
**Goal:** Enable real-time monitoring of TopstepX account activity

**Components:**
1. **SignalR Client** (`src/api/signalr_client.py`)
   - WebSocket connection to TopstepX hub
   - Event subscription (GatewayUserPosition, GatewayUserOrder, GatewayUserTrade, GatewayUserQuote)
   - Auto-reconnection with exponential backoff
   - Event parsing and validation

2. **Event Router** (`src/daemon/event_router.py`)
   - Receives events from SignalR client
   - Passes through converters for normalization
   - Dispatches to StateManager for tracking
   - Dispatches to all active risk rules

**Validation:**
- 12 integration tests in `tests/integration/signalr/`
- Connect to TopstepX staging environment
- Verify real-time position/order updates flow to StateManager

**Est. Duration:** 1 week
**Est. Lines:** ~500 lines

---

### Phase 3: Core Modules (8 modules)
**Goal:** Implement remaining shared functionality for risk rules

**Implementation Order:**
1. **MOD-001: EnforcementActions** - Close positions, cancel orders via REST client
2. **MOD-005: PnLTracker** - Daily realized/unrealized P&L tracking (required by 5 rules)
3. **MOD-008: TradeCounter** - Trade frequency tracking (required by RULE-006)
4. **MOD-002: LockoutManager** - Trader lockout/cooldown management
5. **MOD-003: TimerManager** - Grace period and cooldown timers
6. **MOD-004: ResetScheduler** - Daily session reset logic (4:45 PM CT)
7. **MOD-007: ContractCache** - Contract metadata caching
8. **MOD-006: QuoteTracker** - Real-time quote tracking for unrealized P&L

**Validation:**
- 66 unit tests in `tests/unit/core/`
- Target: 90% coverage per module
- TDD: Run tests after each module implementation

**Est. Duration:** 2 weeks (1-2 days per module)
**Est. Lines:** ~1,200 lines (150 per module avg)

---

### Phase 4: Remaining Risk Rules (8 rules)
**Goal:** Complete all 12 risk rule implementations

**Phases:**
- **Phase 4a (Medium Complexity):** RULE-003, 004, 005, 007
- **Phase 4b (High Complexity):** RULE-008, 009, 010, 012

**Validation:**
- 78 unit tests in `tests/unit/rules/`
- 8 E2E tests in `tests/e2e/test_rule_violations.py`
- Target: 90% coverage per rule

**Est. Duration:** 2 weeks (parallel swarm execution recommended)
**Est. Lines:** ~1,400 lines (8 rules × 175 avg)

---

### Phase 5: Daemon & Integration
**Goal:** Build main daemon orchestrator and integrate all components

**Components:**
1. **Daemon** (`src/daemon/daemon.py`)
   - Process lifecycle (start, stop, restart)
   - Configuration loader (YAML → Python objects)
   - Initialize all modules and rules
   - State recovery from SQLite on startup
   - IPC listener for CLI commands
   - Main event loop

2. **Database Layer** (`src/database/sqlite_manager.py`)
   - Schema creation and migration
   - State persistence (positions, orders, lockouts, P&L)
   - Audit trail logging

**Validation:**
- 30 E2E tests in `tests/e2e/`
- Manual testing with TopstepX staging account
- Load testing (simulate high-frequency trading)

**Est. Duration:** 1 week
**Est. Lines:** ~600 lines

---

### Phase 6: CLI Tools
**Goal:** User interfaces for monitoring and administration

**Components:**
1. **Trader CLI** (`src/cli/trader_cli.py`)
   - Status, monitor, history commands
   - Real-time event streaming
   - Read-only access

2. **Admin CLI** (`src/cli/admin_cli.py`)
   - Configuration editing
   - Lockout management
   - Log viewing
   - Daemon control
   - Password authentication

**Validation:**
- Manual testing of all commands
- IPC communication tests
- Password authentication tests

**Est. Duration:** 1 week
**Est. Lines:** ~700 lines

---

### Phase 7: Production Hardening
**Goal:** Prepare for production deployment

**Tasks:**
1. Performance optimization (profiling, caching)
2. Error handling audit (fail-safe modes)
3. Documentation (user guide, API docs, deployment guide)
4. Security audit (credential storage, password hashing)
5. Production deployment scripts (systemd service, Docker)
6. Monitoring and alerting setup

**Validation:**
- Load testing (1000+ events/second)
- Failure scenario testing (API downtime, network issues)
- Security scan (static analysis, dependency audit)

**Est. Duration:** 1 week

---

### Total Estimated Timeline: 8-10 weeks from current point

**Breakdown:**
- Phase 2 (SignalR): 1 week
- Phase 3 (Core Modules): 2 weeks
- Phase 4 (Risk Rules): 2 weeks
- Phase 5 (Daemon): 1 week
- Phase 6 (CLI): 1 week
- Phase 7 (Hardening): 1 week
- Buffer: 2 weeks

**Total Remaining Code:** ~3,500 lines

---

## Next Steps

### Immediate (Today)
1. ✅ Review this system overview document
2. ⏳ **Decision:** Proceed to Phase 2 (SignalR) or finish remaining core modules?
3. ⏳ Update project roadmap based on priorities

### This Week (Recommended: Phase 2)
**Option A: SignalR Client (Recommended for momentum)**
- Enables real-time event flow (critical for daemon)
- Unblocks E2E testing
- 12 integration tests ready to validate

**Steps:**
1. Implement `src/api/signalr_client.py` (~300 lines)
2. Run integration tests: `pytest tests/integration/signalr/ -v`
3. Test with TopstepX staging environment
4. Verify events flow to StateManager via converters

**Option B: Complete Core Modules (Alternative path)**
- Finish MOD-001 through MOD-008 (8 modules)
- Enables implementation of remaining risk rules
- 66 unit tests ready to validate

**Steps:**
1. Implement modules in dependency order (MOD-001, 005, 008, 002, 003, 004, 007, 006)
2. TDD: Run tests after each module
3. Target 90% coverage per module

---

## Architecture Documents

Once individual architecture documents are created by other agents in the swarm, they will be linked here:

- **[01_DAEMON_ARCHITECTURE.md](01_DAEMON_ARCHITECTURE.md)** - Daemon process architecture
- **[02_CLI_ARCHITECTURE.md](02_CLI_ARCHITECTURE.md)** - Trader and Admin CLI design
- **[03_CORE_MODULES.md](03_CORE_MODULES.md)** - 9 core modules specifications
- **[04_RISK_RULES.md](04_RISK_RULES.md)** - 12 risk rules detailed specs
- **[05_API_INTEGRATION.md](05_API_INTEGRATION.md)** - REST + SignalR integration
- **[06_CONFIGURATION.md](06_CONFIGURATION.md)** - YAML configuration system

---

## Key Design Principles

1. **Test-Driven Development (TDD)**
   - Tests written before implementation
   - 270 tests ready, awaiting implementation
   - Target: 90% code coverage

2. **Single Source of Truth**
   - Converters centralize API ↔ Internal mapping
   - StateManager centralizes position/order tracking
   - Configuration files define all thresholds

3. **Fail-Safe Design**
   - Rules enforce protective actions (close, cancel, lockout)
   - Graceful degradation (missing data → defaults)
   - SQLite persistence for crash recovery

4. **Modular Architecture**
   - Each rule is independent (can enable/disable individually)
   - Core modules are reusable across rules
   - Clean separation: API layer → Core → Rules → Enforcement

5. **Real-Time Responsiveness**
   - SignalR WebSocket for instant event updates
   - In-memory state cache for fast rule evaluation
   - Asynchronous event processing

6. **Production Quality**
   - Comprehensive logging (execution, errors, enforcement)
   - Error handling at all layers
   - Rate limiting and retry logic
   - Type hints and docstrings throughout

---

## Technology Stack

- **Language:** Python 3.12+
- **API Client:** `requests` (REST), `signalr-client-threads` (WebSocket)
- **Database:** SQLite3 (local persistence)
- **Configuration:** YAML (`PyYAML`)
- **Logging:** Python `logging` module with rotating file handlers
- **Testing:** `pytest`, `pytest-cov`, `pytest-mock`
- **IPC:** Socket/pipe communication (daemon ↔ CLI)
- **Authentication:** JWT (API), bcrypt (admin CLI)
- **Deployment:** Systemd service (Linux) or Docker container

---

## Project Statistics

### Current State (as of 2025-10-23)
- **Total Files:** ~80 Python files
- **Production Code:** ~2,538 lines (completed components)
- **Test Code:** ~10,000+ lines (270 tests)
- **Documentation:** ~15 comprehensive specs
- **Test Pass Rate:** 92.3% (24/26 passing)
- **Coverage:** 87.25% (implemented modules), 33.79% overall
- **Overall Progress:** ~60% (specs + tests + partial implementation)

### Completion Metrics
| Category | Complete | In Progress | Not Started | Total |
|----------|----------|-------------|-------------|-------|
| **Specifications** | 100% | 0% | 0% | 100% |
| **Test Suite** | 100% | 0% | 0% | 270 tests |
| **Core Modules** | 11% (1/9) | 89% (8/9 stubs) | 0% | 9 modules |
| **Risk Rules** | 33% (4/12) | 0% | 67% (8/12) | 12 rules |
| **API Layer** | 60% | 0% | 40% (SignalR) | 5 files |
| **Daemon** | 0% | 0% | 100% | 1 component |
| **CLI Tools** | 0% | 0% | 100% | 2 tools |
| **Database** | 0% | 0% | 100% (schema ready) | 1 component |

**Overall Implementation:** ~40% complete

---

## References

### Specifications
- `/project-specs/SPECS/00-CORE-CONCEPT/system_architecture_v2.md` (v2.2)
- `/project-specs/SPECS/01-EXTERNAL-API/topstepx_integration.md`
- `/project-specs/SPECS/02-BACKEND-DAEMON/` (daemon specs)
- `/project-specs/SPECS/03-RISK-RULES/` (12 rule specs)
- `/project-specs/SPECS/04-CORE-MODULES/` (9 module specs)
- `/project-specs/SPECS/06-CLI-FRONTEND/` (CLI specs)

### Reports
- `/docs/PROJECT_STATUS_CURRENT.md` - Latest status
- `/docs/PHASE_1_SWARM_COMPLETE.md` - Phase 1 completion report
- `/docs/CONVERTER_IMPLEMENTATION.md` - Converter layer details
- `/reports/IMPLEMENTATION_ROADMAP.md` - Implementation plan
- `/reports/COMPLETENESS_REPORT.md` - Spec completeness

### Code Documentation
- `/src/api/converters.py` - API conversion layer
- `/src/core/state_manager.py` - State management
- `/src/rules/` - Implemented risk rules
- `/tests/` - Comprehensive test suite

---

**Document Created:** 2025-10-23
**Author:** System Overview Writer (Integration Architecture Swarm)
**Status:** Complete (synthesized from existing documentation)
**Next Update:** After Phase 2 completion (SignalR + Event Router)
