# Data Flow Diagrams - Simple Risk Manager

**Project:** Simple Risk Manager v2.2
**Date:** 2025-10-23
**Purpose:** Comprehensive data flow documentation showing how data moves through the system

---

## Table of Contents

1. [Complete System Tree](#1-complete-system-tree)
2. [Daemon Startup Flow](#2-daemon-startup-flow)
3. [SignalR Event Flow](#3-signalr-event-flow)
4. [CLI Command Flow](#4-cli-command-flow)
5. [Order Submission Flow](#5-order-submission-flow)
6. [Configuration Change Flow](#6-configuration-change-flow)
7. [Risk Rule Evaluation Flow](#7-risk-rule-evaluation-flow)
8. [State Persistence Flow](#8-state-persistence-flow)

---

## 1. Complete System Tree

```
simple-risk-manager/
├── daemon/                           ❌ (Not yet implemented)
│   ├── main.py                       ❌ (entry point)
│   ├── config_loader.py              ❌
│   ├── event_router.py               ❌
│   └── enforcement_engine.py         ❌
│
├── api/                              ✅ (Complete)
│   ├── rest_client.py                ✅ (HTTP client for TopstepX)
│   ├── signalr_client.py             ❌ (WebSocket client)
│   ├── converters.py                 ✅ (camelCase ↔ snake_case)
│   ├── enums.py                      ✅ (API enum mappings)
│   └── exceptions.py                 ✅ (API error handling)
│
├── core/                             ✅ (Complete - 9 modules)
│   ├── state_manager.py              ✅ (MOD-009: Position/order tracking)
│   ├── pnl_tracker.py                ✅ (MOD-010: PnL calculations)
│   ├── enforcement_actions.py        ✅ (MOD-001: Enforcement logic)
│   ├── lockout_manager.py            ✅ (MOD-002: Account lockouts)
│   ├── reset_scheduler.py            ✅ (MOD-003: Daily resets)
│   ├── trade_counter.py              ✅ (MOD-004: Trade frequency)
│   ├── timer_manager.py              ✅ (MOD-005: Time-based rules)
│   ├── quote_tracker.py              ✅ (MOD-006: Market data)
│   └── contract_cache.py             ✅ (MOD-007: Contract metadata)
│
├── rules/                            ⚠️  (4 of 12 implemented)
│   ├── max_contracts.py              ✅ (RULE-001)
│   ├── max_contracts_per_instrument.py ✅ (RULE-002)
│   ├── symbol_blocks.py              ✅ (RULE-008)
│   ├── trade_frequency_limit.py      ✅ (RULE-009)
│   ├── daily_loss_limit.py           ❌ (RULE-003)
│   ├── daily_profit_target.py        ❌ (RULE-004)
│   ├── trailing_drawdown.py          ❌ (RULE-005)
│   ├── time_based_restrictions.py    ❌ (RULE-006)
│   ├── max_order_size.py             ❌ (RULE-007)
│   ├── position_duration.py          ❌ (RULE-010)
│   ├── consecutive_losses.py         ❌ (RULE-011)
│   └── volatility_circuit_breaker.py ❌ (RULE-012)
│
├── cli/                              ❌ (Not yet implemented)
│   ├── trader_cli.py                 ❌ (User commands)
│   └── admin_cli.py                  ❌ (Config management)
│
├── utils/                            ✅ (Complete)
│   └── symbol_utils.py               ✅ (Symbol parsing)
│
├── risk_manager/                     ✅ (Complete)
│   └── logging/                      ✅ (Logging system)
│       ├── config.py                 ✅
│       ├── context.py                ✅
│       ├── formatters.py             ✅
│       └── performance.py            ✅
│
└── config/                           ⚠️  (Partial)
    ├── risk_rules.yaml               ✅ (Rule configurations)
    └── daemon.yaml                   ❌ (Daemon settings)

Tests:
├── tests/e2e/                        ✅ (5 end-to-end tests)
├── tests/integration/                ✅ (Module integration tests)
└── tests/unit/                       ✅ (Unit tests for all modules)

Documentation:
├── docs/                             ✅ (Comprehensive docs)
├── project-specs/                    ✅ (Specifications)
└── reports/                          ✅ (Status reports)
```

**Status Summary:**
- ✅ **Complete:** api/, core/, utils/, logging/, tests/
- ⚠️  **Partial:** rules/ (4/12), config/ (1/2)
- ❌ **Missing:** daemon/, cli/

---

## 2. Daemon Startup Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: INITIALIZATION                                         │
└─────────────────────────────────────────────────────────────────┘

1. Load Configuration
   ┌──────────────────────────────────────────────┐
   │ config_loader.load('config/risk_rules.yaml') │
   │ config_loader.load('config/daemon.yaml')     │
   └──────────────────────────────────────────────┘
   ↓
   Parse YAML → Dict[str, Any]
   {
     "max_contracts": {"enabled": True, "limit": 5, ...},
     "daily_loss_limit": {"enabled": True, "limit": -500, ...},
     ...
   }

2. Initialize Database
   ┌────────────────────────────────────┐
   │ persistence.initialize()           │
   │   ├─ Create SQLite connection      │
   │   ├─ Create tables (if not exist): │
   │   │   - positions                  │
   │   │   - orders                     │
   │   │   - trades                     │
   │   │   - pnl_history                │
   │   └─ Migrate schema (if needed)    │
   └────────────────────────────────────┘

3. Initialize Core Modules
   ┌──────────────────────────────────────────────────────┐
   │ state_manager = StateManager(db_connection)          │
   │   ↓                                                  │
   │ state_manager.load_state_snapshot()  ← Restore state │
   ├──────────────────────────────────────────────────────┤
   │ pnl_tracker = PNLTracker(state_manager)              │
   ├──────────────────────────────────────────────────────┤
   │ lockout_manager = LockoutManager()                   │
   ├──────────────────────────────────────────────────────┤
   │ reset_scheduler = ResetScheduler(lockout_manager)    │
   ├──────────────────────────────────────────────────────┤
   │ trade_counter = TradeCounter()                       │
   ├──────────────────────────────────────────────────────┤
   │ timer_manager = TimerManager()                       │
   ├──────────────────────────────────────────────────────┤
   │ quote_tracker = QuoteTracker()                       │
   ├──────────────────────────────────────────────────────┤
   │ contract_cache = ContractCache(rest_client)          │
   ├──────────────────────────────────────────────────────┤
   │ enforcement_actions = EnforcementActions(            │
   │     rest_client, state_manager, lockout_manager)     │
   └──────────────────────────────────────────────────────┘

4. Initialize Risk Rules
   ┌────────────────────────────────────────────────────────┐
   │ rules = [                                              │
   │     MaxContractsRule(config, state_manager, actions),  │
   │     MaxContractsPerInstrumentRule(...),                │
   │     SymbolBlocksRule(...),                             │
   │     TradeFrequencyLimitRule(...),                      │
   │     # ... load all 12 rules                            │
   │ ]                                                      │
   └────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: API CONNECTION                                         │
└─────────────────────────────────────────────────────────────────┘

5. Initialize API Clients
   ┌────────────────────────────────────────────┐
   │ rest_client = RESTClient(                  │
   │     base_url="https://gateway.topstepx.com",│
   │     converters=converters                  │
   │ )                                          │
   ├────────────────────────────────────────────┤
   │ signalr_client = SignalRClient(            │
   │     hub_url=".../realtimeHub",             │
   │     converters=converters                  │
   │ )                                          │
   └────────────────────────────────────────────┘

6. Connect to TopstepX
   ┌────────────────────────────────────────────┐
   │ rest_client.authenticate(                  │
   │     username=ENV['TOPSTEPX_USERNAME'],     │
   │     password=ENV['TOPSTEPX_PASSWORD']      │
   │ )                                          │
   │ ↓                                          │
   │ POST /auth/login                           │
   │ ← Response: {"token": "...", ...}          │
   │ ↓                                          │
   │ rest_client.set_auth_token(token)          │
   ├────────────────────────────────────────────┤
   │ signalr_client.connect()                   │
   │ ↓                                          │
   │ WebSocket handshake                        │
   │ ← Connected: SignalR Hub                   │
   └────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: STATE SYNCHRONIZATION                                  │
└─────────────────────────────────────────────────────────────────┘

7. Fetch Initial State
   ┌──────────────────────────────────────────────────────┐
   │ GET /accounts                                        │
   │ ← API Response (camelCase):                          │
   │   [{"id": 12345, "name": "SIM-Account", ...}]        │
   │ ↓                                                    │
   │ converters.api_to_internal_account(response)         │
   │ ← Internal Format (snake_case):                      │
   │   [{"account_id": 12345, "name": "SIM-Account", ...}]│
   ├──────────────────────────────────────────────────────┤
   │ GET /positions?accountId=12345                       │
   │ ← API Response:                                      │
   │   [{"accountId": 12345, "contractId": "MNQ",         │
   │     "type": 1, "size": 3, ...}]                      │
   │ ↓                                                    │
   │ converters.api_to_internal_position(pos)             │
   │ ← [{"account_id": 12345, "contract_id": "MNQ",       │
   │     "position_type": "long", "quantity": 3, ...}]    │
   │ ↓                                                    │
   │ state_manager.update_positions(12345, positions)     │
   ├──────────────────────────────────────────────────────┤
   │ GET /orders?accountId=12345&status=Open              │
   │ ← API Response:                                      │
   │   [{"id": 999, "accountId": 12345, ...}]             │
   │ ↓                                                    │
   │ converters.api_to_internal_order(order)              │
   │ ↓                                                    │
   │ state_manager.update_orders(12345, orders)           │
   ├──────────────────────────────────────────────────────┤
   │ contract_cache.load_contracts()                      │
   │ ↓                                                    │
   │ GET /contracts?activeContract=true                   │
   │ ← Cache all active contracts for metadata lookups    │
   └──────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: REAL-TIME SUBSCRIPTION                                 │
└─────────────────────────────────────────────────────────────────┘

8. Subscribe to Events
   ┌──────────────────────────────────────────────────────────┐
   │ signalr_client.subscribe(                                │
   │     event='GatewayUserPosition',                         │
   │     handler=event_router.handle_position_update          │
   │ )                                                        │
   ├──────────────────────────────────────────────────────────┤
   │ signalr_client.subscribe(                                │
   │     event='GatewayUserOrder',                            │
   │     handler=event_router.handle_order_update             │
   │ )                                                        │
   ├──────────────────────────────────────────────────────────┤
   │ signalr_client.subscribe(                                │
   │     event='GatewayUserTrade',                            │
   │     handler=event_router.handle_trade_execution          │
   │ )                                                        │
   ├──────────────────────────────────────────────────────────┤
   │ signalr_client.subscribe(                                │
   │     event='GatewayQuote',                                │
   │     handler=event_router.handle_quote_update             │
   │ )                                                        │
   └──────────────────────────────────────────────────────────┘

9. Start Event Loop
   ┌──────────────────────────────────────┐
   │ daemon.run()                         │
   │   ↓                                  │
   │ while running:                       │
   │     event = signalr_client.poll()    │
   │     event_router.dispatch(event)     │
   │     reset_scheduler.check_reset()    │
   │     timer_manager.check_timeouts()   │
   │     state_manager.save_snapshot()    │
   └──────────────────────────────────────┘

✅ DAEMON READY - Listening for TopstepX events
```

---

## 3. SignalR Event Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ REAL-TIME EVENT PROCESSING PIPELINE                             │
└─────────────────────────────────────────────────────────────────┘

TopstepX API emits: GatewayUserPosition
  ↓
┌──────────────────────────────────────────────────────────────┐
│ RAW API EVENT (camelCase)                                    │
├──────────────────────────────────────────────────────────────┤
│ {                                                            │
│   "accountId": 12345,                                        │
│   "contractId": "CON.F.US.MNQ.H25",                          │
│   "type": 1,              ← PositionType enum (1=Long)       │
│   "size": 3,              ← API uses "size" not "quantity"   │
│   "averagePrice": 21000.50,                                  │
│   "creationTimestamp": "2025-01-20T15:47:39.882Z"            │
│ }                                                            │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ SIGNALR CLIENT RECEIVES (WebSocket)                          │
├──────────────────────────────────────────────────────────────┤
│ signalr_client.on_message(event_data)                        │
│   ↓                                                          │
│ event_type = "GatewayUserPosition"                           │
│ raw_payload = event_data                                     │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ CONVERTER: API → INTERNAL                                    │
├──────────────────────────────────────────────────────────────┤
│ converters.api_to_internal_position(raw_payload)             │
│                                                              │
│ Transformations:                                             │
│   - "accountId" → "account_id"                               │
│   - "contractId" → "contract_id"                             │
│   - "type" (1) → "position_type" ("long")                    │
│   - "size" → "quantity"                                      │
│   - "averagePrice" → "average_price"                         │
│   - "creationTimestamp" → datetime object                    │
│                                                              │
│ Output (snake_case):                                         │
│ {                                                            │
│   "account_id": 12345,                                       │
│   "contract_id": "CON.F.US.MNQ.H25",                         │
│   "position_type": "long",                                   │
│   "quantity": 3,                                             │
│   "average_price": 21000.50,                                 │
│   "creation_timestamp": datetime(2025, 1, 20, 15, 47, 39)    │
│ }                                                            │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ EVENT ROUTER DISPATCHES                                      │
├──────────────────────────────────────────────────────────────┤
│ event_router.handle_position_update(converted_position)      │
│   ↓                                                          │
│ Routes to appropriate handlers based on event type           │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ STATE MANAGER UPDATES                                        │
├──────────────────────────────────────────────────────────────┤
│ state_manager.update_position(converted_position)            │
│   ↓                                                          │
│ In-Memory Update:                                            │
│   positions[12345][101] = {                                  │
│       "position_id": 101,                                    │
│       "contract_id": "CON.F.US.MNQ.H25",                     │
│       "quantity": 3,                                         │
│       ...                                                    │
│   }                                                          │
│   ↓                                                          │
│ Database Persistence:                                        │
│   INSERT OR REPLACE INTO positions                           │
│   (id, account_id, contract_id, quantity, ...)               │
│   VALUES (101, 12345, 'CON.F.US.MNQ.H25', 3, ...)            │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ RISK RULES EVALUATION (All 12 rules)                         │
├──────────────────────────────────────────────────────────────┤
│ for rule in rules:                                           │
│     breach = rule.check(converted_position)                  │
│     if breach:                                               │
│         enforcement_engine.handle(breach)                    │
│                                                              │
│ Example: MaxContractsRule                                    │
│   ↓                                                          │
│ current_count = state_manager.get_position_count(12345)      │
│ ↓                                                            │
│ current_count = 3                                            │
│ limit = 5                                                    │
│ ↓                                                            │
│ 3 > 5? NO → No breach, continue monitoring                   │
│                                                              │
│ Example: SymbolBlocksRule                                    │
│   ↓                                                          │
│ is_blocked = "MNQ" in blocked_symbols                        │
│ ↓                                                            │
│ False → No breach                                            │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ IF VIOLATION DETECTED                                        │
├──────────────────────────────────────────────────────────────┤
│ Example: User adds 3 more contracts, total = 6 > limit (5)   │
│   ↓                                                          │
│ breach = {                                                   │
│     "rule_id": "RULE-001",                                   │
│     "action": "CLOSE_ALL_POSITIONS",                         │
│     "reason": "MaxContracts breach (net=6, limit=5)",        │
│     "current_count": 6,                                      │
│     "limit": 5                                               │
│ }                                                            │
│   ↓                                                          │
│ enforcement_engine.handle(breach)                            │
│   ↓                                                          │
│ enforcement_actions.close_all_positions(12345)               │
│   ↓                                                          │
│ [See Order Submission Flow below]                            │
│   ↓                                                          │
│ lockout_manager.block_account(12345)  ← If configured        │
│   ↓                                                          │
│ logging.log_enforcement(breach)                              │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ STATE PERSISTED                                              │
├──────────────────────────────────────────────────────────────┤
│ state_manager.save_state_snapshot()                          │
│   ↓                                                          │
│ SQLite database updated with current state                   │
│ Survives daemon restarts                                     │
└──────────────────────────────────────────────────────────────┘

✅ EVENT PROCESSED - System ready for next event
```

---

## 4. CLI Command Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ TRADER CLI: STATUS COMMAND                                      │
└─────────────────────────────────────────────────────────────────┘

User terminal:
  $ risk-manager-trader status
  ↓
┌──────────────────────────────────────────────────────────────┐
│ TRADER CLI PROCESS STARTS                                    │
├──────────────────────────────────────────────────────────────┤
│ trader_cli.py main()                                         │
│   ↓                                                          │
│ args = parse_args()  ← command="status"                      │
│   ↓                                                          │
│ cli.handle_command(args)                                     │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ IPC CLIENT CONNECTS TO DAEMON                                │
├──────────────────────────────────────────────────────────────┤
│ ipc_client = IPCClient()                                     │
│ ipc_client.connect("/var/run/risk-manager.sock")             │
│   ↓                                                          │
│ Unix socket connection established                           │
│ ← Connected to daemon IPC server                             │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ CLI SENDS REQUEST                                            │
├──────────────────────────────────────────────────────────────┤
│ request = {                                                  │
│     "command": "status",                                     │
│     "account_id": None,  ← None = all accounts               │
│     "timestamp": "2025-10-23T10:30:00Z"                      │
│ }                                                            │
│   ↓                                                          │
│ ipc_client.send(request)                                     │
│ ← Request sent over Unix socket                              │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ DAEMON IPC HANDLER RECEIVES                                  │
├──────────────────────────────────────────────────────────────┤
│ ipc_handler.on_message(request)                              │
│   ↓                                                          │
│ command = request["command"]  ← "status"                     │
│   ↓                                                          │
│ ipc_handler.handle_status_request(request)                   │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ DAEMON QUERIES STATE MANAGER                                 │
├──────────────────────────────────────────────────────────────┤
│ state = state_manager.get_current_state()                    │
│   ↓                                                          │
│ For each account:                                            │
│   - positions = state_manager.get_positions(account_id)      │
│   - orders = state_manager.get_orders(account_id)            │
│   - pnl = pnl_tracker.get_daily_pnl(account_id)              │
│   - locked = lockout_manager.is_locked(account_id)           │
│   - trade_count = trade_counter.get_count(account_id)        │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ DAEMON FORMATS RESPONSE                                      │
├──────────────────────────────────────────────────────────────┤
│ response = {                                                 │
│     "accounts": [                                            │
│         {                                                    │
│             "account_id": 12345,                             │
│             "name": "SIM-Account",                           │
│             "positions": [                                   │
│                 {                                            │
│                     "contract_id": "MNQ",                    │
│                     "position_type": "long",                 │
│                     "quantity": 3,                           │
│                     "average_price": 21000.50,               │
│                     "unrealized_pnl": 150.00                 │
│                 }                                            │
│             ],                                               │
│             "orders": [                                      │
│                 {                                            │
│                     "order_id": 999,                         │
│                     "contract_id": "ES",                     │
│                     "side": "buy",                           │
│                     "quantity": 1,                           │
│                     "state": "PENDING"                       │
│                 }                                            │
│             ],                                               │
│             "pnl": {                                         │
│                 "daily_pnl": 150.00,                         │
│                 "realized_pnl": 0.00,                        │
│                 "unrealized_pnl": 150.00                     │
│             },                                               │
│             "status": "active",                              │
│             "locked": False,                                 │
│             "trade_count": 5                                 │
│         }                                                    │
│     ],                                                       │
│     "timestamp": "2025-10-23T10:30:01Z"                      │
│ }                                                            │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ DAEMON SENDS RESPONSE                                        │
├──────────────────────────────────────────────────────────────┤
│ ipc_handler.send_response(response)                          │
│   ↓                                                          │
│ Response sent over Unix socket                               │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ CLI RECEIVES AND DISPLAYS                                    │
├──────────────────────────────────────────────────────────────┤
│ response = ipc_client.receive()                              │
│   ↓                                                          │
│ cli.display_status(response)                                 │
│   ↓                                                          │
│ Format as table using rich library                           │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ OUTPUT TO TERMINAL                                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ ╔═══════════════════════════════════════════════════════╗    │
│ ║ Risk Manager Status - Account: SIM-Account (12345)   ║    │
│ ╠═══════════════════════════════════════════════════════╣    │
│ ║ Status:         🟢 ACTIVE                             ║    │
│ ║ Locked:         No                                    ║    │
│ ║ Trade Count:    5                                     ║    │
│ ╠═══════════════════════════════════════════════════════╣    │
│ ║ Positions                                             ║    │
│ ╟───────────────────────────────────────────────────────╢    │
│ ║ MNQ   │ LONG │ 3 @ 21000.50 │ PnL: +$150.00         ║    │
│ ╠═══════════════════════════════════════════════════════╣    │
│ ║ Working Orders                                        ║    │
│ ╟───────────────────────────────────────────────────────╢    │
│ ║ ES    │ BUY  │ 1             │ Status: PENDING       ║    │
│ ╠═══════════════════════════════════════════════════════╣    │
│ ║ Daily PnL Summary                                     ║    │
│ ╟───────────────────────────────────────────────────────╢    │
│ ║ Realized:       $0.00                                 ║    │
│ ║ Unrealized:     $150.00                               ║    │
│ ║ Total:          $150.00                               ║    │
│ ╚═══════════════════════════════════════════════════════╝    │
│                                                              │
│ Last updated: 2025-10-23 10:30:01                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
  ↓
CLI process exits
```

---

## 5. Order Submission Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ ENFORCEMENT ACTION TRIGGERS ORDER                                │
└─────────────────────────────────────────────────────────────────┘

Risk rule breach detected
  ↓
┌──────────────────────────────────────────────────────────────┐
│ ENFORCEMENT ENGINE DECIDES ACTION                            │
├──────────────────────────────────────────────────────────────┤
│ breach = {                                                   │
│     "rule_id": "RULE-001",                                   │
│     "action": "CLOSE_ALL_POSITIONS"                          │
│ }                                                            │
│   ↓                                                          │
│ enforcement_engine.handle(breach)                            │
│   ↓                                                          │
│ enforcement_actions.close_all_positions(12345)               │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ ENFORCEMENT ACTIONS BUILDS ORDER                             │
├──────────────────────────────────────────────────────────────┤
│ positions = state_manager.get_positions(12345)               │
│   ↓                                                          │
│ For position in positions:                                   │
│     contract_id = position["contract_id"]  ← "MNQ"           │
│     quantity = position["quantity"]        ← 3               │
│     position_type = position["position_type"] ← "long"       │
│       ↓                                                      │
│     Create closing order:                                    │
│     internal_order = {                                       │
│         "account_id": 12345,                                 │
│         "contract_id": "MNQ",                                │
│         "order_type": "market",                              │
│         "side": "sell",  ← Opposite of position_type         │
│         "quantity": 3,                                       │
│         "custom_tag": "RULE-001-AUTO-CLOSE"                  │
│     }                                                        │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ ENFORCEMENT VALIDATES (Not Locked)                           │
├──────────────────────────────────────────────────────────────┤
│ if lockout_manager.is_locked(12345):                         │
│     log_error("Cannot submit order - account locked")        │
│     return False                                             │
│   ↓                                                          │
│ Account not locked → Proceed                                 │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ CONVERTER: INTERNAL → API                                    │
├──────────────────────────────────────────────────────────────┤
│ converters.internal_to_api_order_request(internal_order)     │
│                                                              │
│ Transformations:                                             │
│   - "account_id" → "accountId"                               │
│   - "contract_id" → "contractId"                             │
│   - "order_type" ("market") → "type" (0)                     │
│   - "side" ("sell") → "side" (1)                             │
│   - "quantity" → "size"                                      │
│   - "custom_tag" → "customTag"                               │
│                                                              │
│ Output (camelCase):                                          │
│ api_order = {                                                │
│     "accountId": 12345,                                      │
│     "contractId": "MNQ",                                     │
│     "type": 0,          ← OrderType.Market                   │
│     "side": 1,          ← OrderSide.Sell                     │
│     "size": 3,                                               │
│     "customTag": "RULE-001-AUTO-CLOSE",                      │
│     "limitPrice": None,                                      │
│     "stopPrice": None                                        │
│ }                                                            │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ REST CLIENT SENDS                                            │
├──────────────────────────────────────────────────────────────┤
│ rest_client.place_order(api_order)                           │
│   ↓                                                          │
│ POST https://gateway.topstepx.com/orders                     │
│ Headers: {                                                   │
│     "Authorization": "Bearer {token}",                       │
│     "Content-Type": "application/json"                       │
│ }                                                            │
│ Body: {                                                      │
│     "accountId": 12345,                                      │
│     "contractId": "MNQ",                                     │
│     "type": 0,                                               │
│     "side": 1,                                               │
│     "size": 3,                                               │
│     "customTag": "RULE-001-AUTO-CLOSE"                       │
│ }                                                            │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ TOPSTEPX API RECEIVES (camelCase)                            │
├──────────────────────────────────────────────────────────────┤
│ Order validation:                                            │
│   ✓ Account exists and active                                │
│   ✓ Contract is valid and trading                            │
│   ✓ Sufficient margin                                        │
│   ✓ No exchange restrictions                                 │
│   ↓                                                          │
│ Order submitted to exchange                                  │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ API RESPONDS                                                 │
├──────────────────────────────────────────────────────────────┤
│ HTTP 200 OK                                                  │
│ Response (camelCase):                                        │
│ {                                                            │
│     "id": 12345,         ← orderId                           │
│     "accountId": 12345,                                      │
│     "contractId": "MNQ",                                     │
│     "status": 6,         ← OrderStatus.Pending               │
│     "type": 0,                                               │
│     "side": 1,                                               │
│     "size": 3,                                               │
│     "creationTimestamp": "2025-10-23T10:30:05.123Z",         │
│     "customTag": "RULE-001-AUTO-CLOSE"                       │
│ }                                                            │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ CONVERTER: API → INTERNAL                                    │
├──────────────────────────────────────────────────────────────┤
│ converters.api_to_internal_order(response)                   │
│   ↓                                                          │
│ internal_order_response = {                                  │
│     "order_id": 12345,                                       │
│     "account_id": 12345,                                     │
│     "contract_id": "MNQ",                                    │
│     "state": InternalOrderState.PENDING,                     │
│     "side": "sell",                                          │
│     "quantity": 3,                                           │
│     "creation_timestamp": datetime(2025, 10, 23, 10, 30, 5), │
│     "custom_tag": "RULE-001-AUTO-CLOSE"                      │
│ }                                                            │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ STATE MANAGER UPDATES                                        │
├──────────────────────────────────────────────────────────────┤
│ state_manager.add_order(internal_order_response)             │
│   ↓                                                          │
│ orders[12345][12345] = {                                     │
│     "order_id": 12345,                                       │
│     "state": "PENDING",                                      │
│     ...                                                      │
│ }                                                            │
│   ↓                                                          │
│ Database: INSERT INTO orders (...)                           │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ SIGNALR EVENTS FOLLOW                                        │
├──────────────────────────────────────────────────────────────┤
│ ~100ms later: GatewayUserOrder (status: Open)                │
│ ~200ms later: GatewayUserOrder (status: Filled)              │
│ ~200ms later: GatewayUserTrade (execution details)           │
│ ~200ms later: GatewayUserPosition (size: 0, closed)          │
│   ↓                                                          │
│ Each event updates state_manager via SignalR flow            │
└──────────────────────────────────────────────────────────────┘

✅ ORDER SUBMITTED - Position closure in progress
```

---

## 6. Configuration Change Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ ADMIN CLI: UPDATE CONFIGURATION                                 │
└─────────────────────────────────────────────────────────────────┘

Admin terminal:
  $ risk-manager-admin config set max_contracts.limit 10
  ↓
┌──────────────────────────────────────────────────────────────┐
│ ADMIN CLI PROCESS                                            │
├──────────────────────────────────────────────────────────────┤
│ admin_cli.py main()                                          │
│   ↓                                                          │
│ command = "config"                                           │
│ subcommand = "set"                                           │
│ key = "max_contracts.limit"                                  │
│ value = 10                                                   │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ CLI → DAEMON IPC                                             │
├──────────────────────────────────────────────────────────────┤
│ ipc_client.connect("/var/run/risk-manager.sock")             │
│   ↓                                                          │
│ request = {                                                  │
│     "command": "config_update",                              │
│     "key": "max_contracts.limit",                            │
│     "value": 10                                              │
│ }                                                            │
│   ↓                                                          │
│ ipc_client.send(request)                                     │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ DAEMON RECEIVES REQUEST                                      │
├──────────────────────────────────────────────────────────────┤
│ ipc_handler.handle_config_update(request)                    │
│   ↓                                                          │
│ key = "max_contracts.limit"                                  │
│ value = 10                                                   │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ DAEMON VALIDATES                                             │
├──────────────────────────────────────────────────────────────┤
│ config_validator.validate(key, value)                        │
│   ↓                                                          │
│ Checks:                                                      │
│   ✓ Key exists in schema                                     │
│   ✓ Value type matches (int expected)                        │
│   ✓ Value in valid range (1-100)                             │
│   ✓ No dependencies broken                                   │
│   ↓                                                          │
│ Validation passed                                            │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ DAEMON UPDATES CONFIG                                        │
├──────────────────────────────────────────────────────────────┤
│ config_manager.set("max_contracts.limit", 10)                │
│   ↓                                                          │
│ In-memory config update:                                     │
│ config["max_contracts"]["limit"] = 10                        │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ DAEMON SAVES TO FILE                                         │
├──────────────────────────────────────────────────────────────┤
│ config_manager.save("config/risk_rules.yaml")                │
│   ↓                                                          │
│ Write YAML:                                                  │
│ ---                                                          │
│ max_contracts:                                               │
│   enabled: true                                              │
│   limit: 10          ← Updated                               │
│   count_type: net                                            │
│   ...                                                        │
│   ↓                                                          │
│ File written to disk                                         │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ DAEMON RELOADS RULES                                         │
├──────────────────────────────────────────────────────────────┤
│ For rule in rules:                                           │
│     if isinstance(rule, MaxContractsRule):                   │
│         rule.reload_config(config["max_contracts"])          │
│           ↓                                                  │
│         rule.limit = 10  ← Hot reload, no restart needed     │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ DAEMON LOGS CHANGE                                           │
├──────────────────────────────────────────────────────────────┤
│ audit_log.record({                                           │
│     "event": "config_update",                                │
│     "key": "max_contracts.limit",                            │
│     "old_value": 5,                                          │
│     "new_value": 10,                                         │
│     "user": "admin",                                         │
│     "timestamp": "2025-10-23T10:35:00Z"                      │
│ })                                                           │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ DAEMON RESPONDS                                              │
├──────────────────────────────────────────────────────────────┤
│ response = {                                                 │
│     "status": "success",                                     │
│     "message": "max_contracts.limit updated to 10",          │
│     "old_value": 5,                                          │
│     "new_value": 10                                          │
│ }                                                            │
│   ↓                                                          │
│ ipc_handler.send_response(response)                          │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ CLI DISPLAYS                                                 │
├──────────────────────────────────────────────────────────────┤
│ admin_cli.display_success(response)                          │
│   ↓                                                          │
│ Output:                                                      │
│ ✅ Configuration updated successfully                         │
│                                                              │
│ max_contracts.limit                                          │
│   Old value: 5                                               │
│   New value: 10                                              │
│                                                              │
│ Change effective immediately (no restart required)           │
└──────────────────────────────────────────────────────────────┘

✅ CONFIG UPDATED - Rule now enforces new limit
```

---

## 7. Risk Rule Evaluation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ MULTI-RULE EVALUATION PIPELINE                                  │
└─────────────────────────────────────────────────────────────────┘

Event arrives (e.g., GatewayUserPosition)
  ↓
┌──────────────────────────────────────────────────────────────┐
│ EVENT CONVERTED AND ROUTED                                   │
├──────────────────────────────────────────────────────────────┤
│ [See SignalR Event Flow above]                               │
│   ↓                                                          │
│ State updated in StateManager                                │
│   ↓                                                          │
│ Ready for rule evaluation                                    │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ RULE EVALUATION LOOP                                         │
├──────────────────────────────────────────────────────────────┤
│ for rule in rules:  ← All 12 rules                           │
│     breach = rule.check(event, state_manager)                │
│     if breach:                                               │
│         enforcement_engine.handle(breach)                    │
└──────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ RULE-001: MAX CONTRACTS                                         │
└─────────────────────────────────────────────────────────────────┘
  ↓
max_contracts_rule.check(event)
  ↓
account_id = event["account_id"]  ← 12345
current_count = state_manager.get_position_count(12345)
  ↓
Sum all positions: MNQ (3) + ES (2) = 5
  ↓
if current_count > limit (5 > 5):  ← False
    return None  ← No breach
  ↓
Continue to next rule

┌─────────────────────────────────────────────────────────────────┐
│ RULE-002: MAX CONTRACTS PER INSTRUMENT                          │
└─────────────────────────────────────────────────────────────────┘
  ↓
max_contracts_per_instrument_rule.check(event)
  ↓
contract_id = event["contract_id"]  ← "MNQ"
contract_count = state_manager.get_contract_count(12345, "MNQ")
  ↓
contract_count = 3
limit = config["limits"]["MNQ"]  ← 5
  ↓
if contract_count > limit (3 > 5):  ← False
    return None  ← No breach
  ↓
Continue to next rule

┌─────────────────────────────────────────────────────────────────┐
│ RULE-003: DAILY LOSS LIMIT                                      │
└─────────────────────────────────────────────────────────────────┘
  ↓
daily_loss_limit_rule.check(event)
  ↓
daily_pnl = pnl_tracker.get_daily_pnl(12345)
  ↓
daily_pnl = -350.00  ← Losing day
limit = -500.00      ← Max loss allowed
  ↓
if daily_pnl < limit (-350 < -500):  ← False
    return None  ← No breach (still above limit)
  ↓
Continue to next rule

┌─────────────────────────────────────────────────────────────────┐
│ RULE-008: SYMBOL BLOCKS                                         │
└─────────────────────────────────────────────────────────────────┘
  ↓
symbol_blocks_rule.check(event)
  ↓
contract_id = event["contract_id"]  ← "MNQ"
blocked_symbols = config["blocked_symbols"]  ← ["GC", "CL"]
  ↓
if contract_id in blocked_symbols:  ← False
    return breach
  ↓
Continue to next rule

┌─────────────────────────────────────────────────────────────────┐
│ RULE-009: TRADE FREQUENCY LIMIT                                 │
└─────────────────────────────────────────────────────────────────┘
  ↓
trade_frequency_limit_rule.check(event)
  ↓
trade_count = trade_counter.get_count_in_window(
    12345,
    window_minutes=60
)
  ↓
trade_count = 8
limit = 10
  ↓
if trade_count > limit (8 > 10):  ← False
    return None  ← No breach
  ↓
Continue to next rule

... [Other 8 rules evaluate similarly]

┌─────────────────────────────────────────────────────────────────┐
│ ALL RULES PASSED - NO BREACH                                    │
└─────────────────────────────────────────────────────────────────┘

✅ Event processing complete - System continues monitoring

┌─────────────────────────────────────────────────────────────────┐
│ EXAMPLE: BREACH DETECTED                                        │
└─────────────────────────────────────────────────────────────────┘

User adds 2 more MNQ contracts → Total = 7
  ↓
RULE-001: MaxContracts
  ↓
current_count = 7
limit = 5
  ↓
if current_count > limit (7 > 5):  ← TRUE
    return {
        "rule_id": "RULE-001",
        "action": "CLOSE_ALL_POSITIONS",
        "reason": "MaxContracts breach (net=7, limit=5)",
        "current_count": 7,
        "limit": 5
    }
  ↓
┌──────────────────────────────────────────────────────────────┐
│ ENFORCEMENT ENGINE HANDLES BREACH                            │
├──────────────────────────────────────────────────────────────┤
│ enforcement_engine.handle(breach)                            │
│   ↓                                                          │
│ 1. Log breach to audit log                                   │
│ 2. Execute enforcement action:                               │
│    enforcement_actions.close_all_positions(12345)            │
│    [See Order Submission Flow above]                         │
│ 3. Apply lockout (if configured):                            │
│    lockout_manager.block_account(12345)                      │
│ 4. Send notifications (email, SMS, webhook)                  │
│ 5. Update metrics/dashboards                                 │
└──────────────────────────────────────────────────────────────┘

❌ BREACH ENFORCED - Positions closed, account locked
```

---

## 8. State Persistence Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ CONTINUOUS STATE PERSISTENCE                                    │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ IN-MEMORY STATE (Fast Access)                                │
├──────────────────────────────────────────────────────────────┤
│ StateManager:                                                │
│   positions = {                                              │
│       12345: {  ← account_id                                 │
│           101: {position_data},  ← position_id               │
│           102: {position_data}                               │
│       }                                                      │
│   }                                                          │
│                                                              │
│   orders = {                                                 │
│       12345: {  ← account_id                                 │
│           999: {order_data},  ← order_id                     │
│           1000: {order_data}                                 │
│       }                                                      │
│   }                                                          │
└──────────────────────────────────────────────────────────────┘
  │
  │ (Every state change triggers persistence)
  ↓
┌──────────────────────────────────────────────────────────────┐
│ AUTOMATIC PERSISTENCE TRIGGERS                               │
├──────────────────────────────────────────────────────────────┤
│ 1. On position update:                                       │
│    state_manager.update_position() → Auto-save to DB         │
│                                                              │
│ 2. On order update:                                          │
│    state_manager.update_order() → Auto-save to DB            │
│                                                              │
│ 3. Periodic snapshot (every 60 seconds):                     │
│    state_manager.save_state_snapshot()                       │
│                                                              │
│ 4. On graceful shutdown:                                     │
│    daemon.on_shutdown() → state_manager.save_state_snapshot()│
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ SQLITE DATABASE (Persistent Storage)                        │
├──────────────────────────────────────────────────────────────┤
│ File: ~/.risk-manager/state.db                               │
│                                                              │
│ Table: positions                                             │
│ ┌─────┬────────────┬─────────────┬──────┬──────┬───────────┐│
│ │ id  │ account_id │ contract_id │ type │ size │ avg_price ││
│ ├─────┼────────────┼─────────────┼──────┼──────┼───────────┤│
│ │ 101 │ 12345      │ MNQ         │ 1    │ 3    │ 21000.50  ││
│ │ 102 │ 12345      │ ES          │ 1    │ 2    │ 5800.00   ││
│ └─────┴────────────┴─────────────┴──────┴──────┴───────────┘│
│                                                              │
│ Table: orders                                                │
│ ┌─────┬────────────┬─────────────┬──────┬──────┬──────────┐ │
│ │ id  │ account_id │ contract_id │ side │ size │ status   │ │
│ ├─────┼────────────┼─────────────┼──────┼──────┼──────────┤ │
│ │ 999 │ 12345      │ ES          │ 0    │ 1    │ 6        │ │
│ └─────┴────────────┴─────────────┴──────┴──────┴──────────┘ │
│                                                              │
│ Table: trades (historical)                                   │
│ Table: pnl_history (daily snapshots)                         │
│ Table: audit_log (enforcement actions)                       │
└──────────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────────┐
│ DAEMON RESTART SCENARIO                                      │
├──────────────────────────────────────────────────────────────┤
│ 1. Daemon crashes or stops                                   │
│    ↓                                                         │
│ 2. Daemon restarts                                           │
│    ↓                                                         │
│ 3. state_manager.load_state_snapshot()                       │
│    ↓                                                         │
│ 4. Read from SQLite:                                         │
│    SELECT * FROM positions                                   │
│    SELECT * FROM orders                                      │
│    ↓                                                         │
│ 5. Restore in-memory state:                                  │
│    positions[12345][101] = {restored_data}                   │
│    orders[12345][999] = {restored_data}                      │
│    ↓                                                         │
│ 6. Reconnect to TopstepX API                                 │
│    ↓                                                         │
│ 7. Fetch current state from API                              │
│    ↓                                                         │
│ 8. Merge API state with persisted state:                     │
│    - If API has newer data → Update DB                       │
│    - If DB has orphaned data → Mark as stale                 │
│    ↓                                                         │
│ 9. Resume monitoring                                         │
└──────────────────────────────────────────────────────────────┘

✅ STATE PERSISTENCE - Survives crashes, no data loss

┌──────────────────────────────────────────────────────────────┐
│ TRANSACTION GUARANTEES                                       │
├──────────────────────────────────────────────────────────────┤
│ - Atomic writes: Position + Order updates are transactional  │
│ - Write-ahead logging: SQLite WAL mode enabled               │
│ - Crash recovery: SQLite auto-recovery on restart            │
│ - Backup strategy: Daily snapshots to separate file          │
└──────────────────────────────────────────────────────────────┘
```

---

## Summary

This document provides comprehensive data flow diagrams for the Simple Risk Manager system. Key flows include:

1. **System Structure**: Complete file tree showing implemented vs. missing components
2. **Daemon Startup**: 9-phase initialization from config to event loop
3. **SignalR Events**: Real-time event processing with camelCase ↔ snake_case conversion
4. **CLI Commands**: IPC-based communication between CLI and daemon
5. **Order Submission**: Enforcement action → converter → API → state update
6. **Configuration**: Hot-reload configuration changes without restart
7. **Risk Rules**: Multi-rule evaluation pipeline with breach handling
8. **State Persistence**: Continuous SQLite persistence with crash recovery

**Next Steps:**
- Implement missing daemon components (`daemon/`, `cli/`)
- Complete remaining 8 risk rules
- Build SignalR client for real-time events
- Add IPC layer for CLI communication

**Related Documents:**
- `/docs/COORDINATION_FLOW_DIAGRAMS.md` - Agent coordination patterns
- `/docs/PROJECT_STATUS_CURRENT.md` - Implementation status
- `/docs/contracts/API_CONTRACT_SUMMARY.md` - API contract details
- `/project-specs/SPECS/` - Complete specifications

---

**Document Version:** 1.0
**Last Updated:** 2025-10-23
**Maintained By:** Integration Architecture Swarm
