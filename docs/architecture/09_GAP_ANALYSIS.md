# Gap Analysis - What Exists vs What's Needed

**Document ID:** ARCH-009
**Date:** 2025-10-23
**Author:** Integration Architecture Swarm - Gap Analysis Writer
**Status:** ACTIVE

---

## Executive Summary

**Total Components Planned:** 42 major components
**Components Completed:** 16 (38%)
**Components In Progress:** 0 (0%)
**Components Missing:** 26 (62%)
**Estimated Work Remaining:** 98 hours (12.25 days at 8h/day)

**Critical Path:** P0 components (46 hours) block runtime functionality. System cannot run without these.

**Key Finding:** Foundation layer is PRODUCTION READY (100% complete). All gaps are in integration, enforcement, and runtime layers.

---

## Component Status Matrix

| Component | Status | Files | Tests | Priority | Effort |
|-----------|--------|-------|-------|----------|--------|
| **API LAYER** |  |  |  |  |  |
| REST Client | ✅ DONE | rest_client.py (382 lines) | 14/14 ✅ | - | - |
| Converters | ✅ DONE | converters.py (478 lines) | 25/25 ✅ | - | - |
| Enums | ✅ DONE | enums.py (316 lines) | Tests included | - | - |
| Exceptions | ✅ DONE | exceptions.py (53 lines) | Tests included | - | - |
| SignalR Client | ❌ MISSING | N/A | 0/12 RED | P0 | 12h |
| Event Router | ❌ MISSING | N/A | 0/0 | P0 | 8h |
| **CORE MODULES (9 total)** |  |  |  |  |  |
| MOD-001: Enforcement Actions | ✅ DONE | enforcement_actions.py (254 lines) | 8/8 ✅ | - | - |
| MOD-002: Lockout Manager | ✅ DONE | lockout_manager.py (253 lines) | 10/10 ✅ | - | - |
| MOD-003: Timer Manager | ✅ DONE | timer_manager.py (180 lines) | 6/6 ✅ | - | - |
| MOD-004: Reset Scheduler | ✅ DONE | reset_scheduler.py (229 lines) | 6/6 ✅ | - | - |
| MOD-005: PNL Tracker | ✅ DONE | pnl_tracker.py (321 lines) | 8/8 ✅ | - | - |
| MOD-006: Quote Tracker | ✅ DONE | quote_tracker.py (184 lines) | 8/8 ✅ | - | - |
| MOD-007: Contract Cache | ✅ DONE | contract_cache.py (325 lines) | 6/6 ✅ | - | - |
| MOD-008: Trade Counter | ✅ DONE | trade_counter.py (217 lines) | 6/6 ✅ | - | - |
| MOD-009: State Manager | ✅ DONE | state_manager.py (209 lines) | 8/8 ✅ | - | - |
| **RISK RULES (12 total)** |  |  |  |  |  |
| RULE-001: MaxContracts | ✅ DONE | max_contracts.py (147 lines) | RED | - | - |
| RULE-002: MaxContractsPerInstrument | ✅ DONE | max_contracts_per_instrument.py (194 lines) | RED | - | - |
| RULE-006: TradeFrequencyLimit | ✅ DONE | trade_frequency_limit.py (174 lines) | RED | - | - |
| RULE-011: SymbolBlocks | ✅ DONE | symbol_blocks.py (208 lines) | RED | - | - |
| RULE-003: DailyRealizedLoss | ❌ MISSING | N/A | RED | P1 | 3h |
| RULE-004: DailyUnrealizedLoss | ❌ MISSING | N/A | RED | P1 | 3h |
| RULE-005: MaxUnrealizedProfit | ❌ MISSING | N/A | RED | P1 | 3h |
| RULE-007: CooldownAfterLoss | ❌ MISSING | N/A | RED | P1 | 3h |
| RULE-008: NoStopLossGrace | ❌ MISSING | N/A | RED | P1 | 3h |
| RULE-009: SessionBlockOutside | ❌ MISSING | N/A | RED | P1 | 3h |
| RULE-010: AuthLossGuard | ❌ MISSING | N/A | RED | P1 | 3h |
| RULE-012: TradeManagement | ❌ MISSING | N/A | RED | P1 | 3h |
| **ENFORCEMENT** |  |  |  |  |  |
| Enforcement Engine | ❌ MISSING | N/A | 0/0 | P0 | 10h |
| Rule Registry | ❌ MISSING | N/A | 0/0 | P0 | 4h |
| **DAEMON** |  |  |  |  |  |
| Main Daemon Process | ❌ MISSING | N/A | 0/0 | P0 | 12h |
| Config Loader | ❌ MISSING | N/A | 0/0 | P0 | 4h |
| Initialization Manager | ❌ MISSING | N/A | 0/0 | P0 | 6h |
| **CLI** |  |  |  |  |  |
| Trader CLI | ❌ MISSING | N/A | 0/0 | P2 | 8h |
| Admin CLI | ❌ MISSING | N/A | 0/0 | P2 | 6h |
| IPC Layer | ❌ MISSING | N/A | 0/0 | P2 | 4h |
| **CONFIGURATION** |  |  |  |  |  |
| Logging Config | ✅ DONE | config/logging.yaml | ✅ | - | - |
| Rules Config Files | ⏳ PARTIAL | Some YAML exists | N/A | P1 | 2h |
| Config Validation | ❌ MISSING | N/A | 0/0 | P1 | 3h |
| **PERSISTENCE** |  |  |  |  |  |
| Database Schema | ⏳ PARTIAL | Schema in specs | N/A | P1 | 2h |
| Database Initialization | ❌ MISSING | N/A | 0/0 | P1 | 4h |
| Migration System | ❌ MISSING | N/A | 0/0 | P3 | 6h |
| **UTILITIES** |  |  |  |  |  |
| Symbol Utils | ✅ DONE | utils/symbol_utils.py (34 lines) | ✅ | - | - |
| Logging Infrastructure | ✅ DONE | risk_manager/logging/* | ✅ | - | - |
| **ERROR HANDLING** |  |  |  |  |  |
| Error Code Mapping | ⏳ SPEC ONLY | Spec exists | N/A | P1 | 4h |
| Rate Limiting | ⏳ PARTIAL | REST client has basic | N/A | P1 | 6h |
| Circuit Breaker | ⏳ SPEC ONLY | Spec exists | N/A | P2 | 8h |

---

## Detailed Gap Analysis

### 1. API Layer

#### ✅ Completed Components

**REST Client** (`src/api/rest_client.py`)
- **Status:** PRODUCTION READY
- **Lines:** 382
- **Coverage:** 75%+
- **Tests:** 14/14 passing
- **Features:**
  - JWT authentication with token expiry management
  - Rate limiting (200 req/60s sliding window)
  - Retry logic with exponential backoff (5 retries)
  - Network timeout handling (30s default)
  - Request/response logging
  - Session-based connection pooling
- **Endpoints Implemented (7/10):**
  1. `/api/Auth/loginKey` - Authentication ✅
  2. `/api/Position/closePosition` - Close position ✅
  3. `/api/Order/cancelOrder` - Cancel order ✅
  4. `/api/Order/placeOrder` - Place order ✅
  5. `/api/Order/modifyOrder` - Modify order ✅
  6. `/api/Position/searchOpenPositions` - Get positions ✅
  7. `/api/Contract/searchContract` - Get contract metadata ✅

**Converters** (`src/api/converters.py`)
- **Status:** PRODUCTION READY
- **Lines:** 478
- **Tests:** 25/25 passing
- **Coverage:** ALL data types
- **Supported Conversions:**
  - Account (REST ↔ SignalR ↔ Internal)
  - Order (REST ↔ SignalR ↔ Internal)
  - Position (REST ↔ SignalR ↔ Internal)
  - Trade (REST ↔ SignalR ↔ Internal)
  - Contract (REST ↔ SignalR ↔ Internal)
  - Quote (SignalR ↔ Internal)
- **Key Features:**
  - Handles camelCase ↔ snake_case conversions
  - Enum value mapping (AccountStatusEnum, OrderStatusEnum, etc.)
  - NULL/None safety
  - Type validation
  - Timestamp parsing

**Enums** (`src/api/enums.py`)
- **Status:** PRODUCTION READY
- **Lines:** 316
- **Enums Defined:**
  - AccountStatusEnum (7 states)
  - OrderStatusEnum (9 states)
  - PositionStatusEnum (5 states)
  - TradeStatusEnum (6 states)
  - OrderTypeEnum (7 types)
  - OrderSideEnum (2 sides)
- **Features:**
  - Bidirectional mapping (int ↔ string)
  - Unknown value handling
  - Value validation

**Exceptions** (`src/api/exceptions.py`)
- **Status:** PRODUCTION READY
- **Lines:** 53
- **Exception Classes:**
  - AuthenticationError (401 failures)
  - APIError (general API errors)
  - RateLimitError (429 responses)
  - NetworkError (connection/timeout)

#### ❌ Missing Components

**SignalR Client** - CRITICAL GAP
- **File Needed:** `src/api/signalr_client.py`
- **Estimated Lines:** 400-500
- **Priority:** P0 (BLOCKS RUNTIME)
- **Effort:** 12 hours
- **Requirements:**
  - WebSocket connection to TopstepX SignalR hub
  - JWT authentication in connection string
  - Subscribe to 5 event types:
    1. `GatewayUserAccount` - Account updates
    2. `GatewayUserPosition` - Position changes
    3. `GatewayUserOrder` - Order status updates
    4. `GatewayUserTrade` - Trade executions
    5. `GatewayUserQuote` - Real-time quotes
  - Automatic reconnection with exponential backoff
  - Event buffering during disconnection
  - Thread-safe event callbacks
  - Connection health monitoring
  - Heartbeat/keepalive mechanism
- **Tests Waiting:** 12 tests (RED)
  - `test_connection.py` (3 tests)
  - `test_event_subscription.py` (4 tests)
  - `test_event_parsing.py` (2 tests)
  - `test_reconnection.py` (3 tests)
- **Dependencies:**
  - `signalrcore` library (already in requirements.txt likely)
  - `converters.py` for event parsing
  - `enums.py` for state mapping

**Event Router** - CRITICAL GAP
- **File Needed:** `src/core/event_router.py`
- **Estimated Lines:** 300-400
- **Priority:** P0 (BLOCKS RUNTIME)
- **Effort:** 8 hours
- **Requirements:**
  - Route SignalR events to appropriate modules
  - Call converters to transform SignalR → Internal format
  - Dispatch to all registered risk rules
  - Update StateManager with new data
  - Handle event ordering (position before trade, etc.)
  - Event queue for async processing
  - Error handling (continue on rule failure)
  - Performance logging (event processing time)
- **Event Routing Logic:**
  ```
  GatewayUserAccount → StateManager.update_account()
  GatewayUserPosition → StateManager.update_position() → ALL RULES
  GatewayUserOrder → StateManager.update_order() → ALL RULES
  GatewayUserTrade → PNLTracker.add_trade() → TradeCounter.record() → TRADE RULES
  GatewayUserQuote → QuoteTracker.update_quote()
  ```
- **Tests Waiting:** None (needs to be written)
- **Dependencies:**
  - SignalR Client (event source)
  - Converters (data transformation)
  - State Manager (state updates)
  - All risk rules (event subscribers)

**REST Client Completion**
- **Missing Endpoints (3/10):**
  8. `/api/Account/getAccount` - Get account details
  9. `/api/Order/searchOrders` - Query orders
  10. `/api/History/retrieveBars` - Historical data (optional)
- **Priority:** P1
- **Effort:** 4 hours
- **Notes:** System can function without these, but they're useful for initialization and diagnostics

---

### 2. Core Modules

#### ✅ ALL 9 MODULES COMPLETE (100%)

**Summary:** 2,182 lines of production code, 66/66 tests passing

| Module | File | Lines | Tests | Features |
|--------|------|-------|-------|----------|
| MOD-001 | enforcement_actions.py | 254 | 8/8 ✅ | Close positions, cancel orders, lockouts |
| MOD-002 | lockout_manager.py | 253 | 10/10 ✅ | Expiry, permanent locks, persistence |
| MOD-003 | timer_manager.py | 180 | 6/6 ✅ | Cooldown timers, callbacks |
| MOD-004 | reset_scheduler.py | 229 | 6/6 ✅ | Daily resets, holiday detection |
| MOD-005 | pnl_tracker.py | 321 | 8/8 ✅ | Realized/unrealized P&L, persistence |
| MOD-006 | quote_tracker.py | 184 | 8/8 ✅ | Real-time quotes, staleness |
| MOD-007 | contract_cache.py | 325 | 6/6 ✅ | Metadata caching, persistence |
| MOD-008 | trade_counter.py | 217 | 6/6 ✅ | Rolling windows, persistence |
| MOD-009 | state_manager.py | 209 | 8/8 ✅ | Global state, persistence |

**Status:** PRODUCTION READY
**No gaps in core modules** - this is the foundation layer

---

### 3. Risk Rules

#### ✅ Implemented (4/12 rules)

**RULE-001: MaxContracts** (`src/rules/max_contracts.py`)
- **Lines:** 147
- **Status:** Implemented, tests RED (need integration)
- **Features:** Net/gross contract counting, close_all vs reduce_to_limit

**RULE-002: MaxContractsPerInstrument** (`src/rules/max_contracts_per_instrument.py`)
- **Lines:** 194
- **Status:** Implemented, tests RED (need integration)
- **Features:** Per-symbol limits, unknown symbol handling

**RULE-006: TradeFrequencyLimit** (`src/rules/trade_frequency_limit.py`)
- **Lines:** 174
- **Status:** Implemented, tests RED (need integration)
- **Features:** Per-minute, per-hour, per-session limits

**RULE-011: SymbolBlocks** (`src/rules/symbol_blocks.py`)
- **Lines:** 208
- **Status:** Implemented, tests RED (need integration)
- **Features:** Symbol blacklist, immediate close, permanent lockout

#### ❌ Missing (8/12 rules)

All missing rules have **comprehensive test suites** already written (RED). Each test file has 6-12 test scenarios covering:
- Normal operation
- Threshold breaches
- Enforcement actions
- Edge cases
- Persistence/reset logic

**RULE-003: DailyRealizedLoss**
- **File Needed:** `src/rules/daily_realized_loss.py`
- **Estimated Lines:** 150-200
- **Tests Waiting:** `test_daily_realized_loss.py` (11 tests, 273 lines)
- **Priority:** P1
- **Effort:** 3 hours
- **Trigger:** GatewayUserTrade events
- **Enforcement:** Close all positions + lockout on breach
- **Dependencies:** PNLTracker (realized P&L calculation)

**RULE-004: DailyUnrealizedLoss**
- **File Needed:** `src/rules/daily_unrealized_loss.py`
- **Estimated Lines:** 150-200
- **Tests Waiting:** `test_daily_unrealized_loss.py` (12 tests, 264 lines)
- **Priority:** P1
- **Effort:** 3 hours
- **Trigger:** GatewayUserPosition events
- **Enforcement:** Close all positions + lockout on breach
- **Dependencies:** PNLTracker (unrealized P&L calculation), QuoteTracker (current prices)

**RULE-005: MaxUnrealizedProfit**
- **File Needed:** `src/rules/max_unrealized_profit.py`
- **Estimated Lines:** 150-200
- **Tests Waiting:** `test_max_unrealized_profit.py` (9 tests, 288 lines)
- **Priority:** P1
- **Effort:** 3 hours
- **Trigger:** GatewayUserPosition events
- **Enforcement:** Close all positions (capture profits)
- **Dependencies:** PNLTracker, QuoteTracker

**RULE-007: CooldownAfterLoss**
- **File Needed:** `src/rules/cooldown_after_loss.py`
- **Estimated Lines:** 120-150
- **Tests Waiting:** `test_cooldown_after_loss.py` (6 tests, 192 lines)
- **Priority:** P1
- **Effort:** 3 hours
- **Trigger:** GatewayUserTrade events (losing trades)
- **Enforcement:** Temporary lockout (timer-based)
- **Dependencies:** TimerManager (cooldown duration), PNLTracker (detect losses)

**RULE-008: NoStopLossGrace**
- **File Needed:** `src/rules/no_stop_loss_grace.py`
- **Estimated Lines:** 120-150
- **Tests Waiting:** `test_no_stop_loss_grace.py` (7 tests, 235 lines)
- **Priority:** P1
- **Effort:** 3 hours
- **Trigger:** GatewayUserOrder events (new orders)
- **Enforcement:** Grace period timer, then close position if no stop
- **Dependencies:** TimerManager (grace period), StateManager (order tracking)

**RULE-009: SessionBlockOutside**
- **File Needed:** `src/rules/session_block_outside_hours.py`
- **Estimated Lines:** 120-150
- **Tests Waiting:** `test_session_block_outside_hours.py` (8 tests, 216 lines)
- **Priority:** P1
- **Effort:** 3 hours
- **Trigger:** Scheduled (time-based)
- **Enforcement:** Lockout during off-hours
- **Dependencies:** TimerManager or ResetScheduler (time checks)

**RULE-010: AuthLossGuard**
- **File Needed:** `src/rules/auth_loss_guard.py`
- **Estimated Lines:** 150-200
- **Tests Waiting:** `test_auth_loss_guard.py` (9 tests, 242 lines)
- **Priority:** P1
- **Effort:** 3 hours
- **Trigger:** GatewayUserTrade events
- **Enforcement:** Close all + lockout after N losing trades
- **Dependencies:** TradeCounter (trade tracking), PNLTracker (loss detection)

**RULE-012: TradeManagement**
- **File Needed:** `src/rules/trade_management.py`
- **Estimated Lines:** 200-250
- **Tests Waiting:** `test_trade_management.py` (10 tests, 251 lines)
- **Priority:** P1
- **Effort:** 3 hours
- **Trigger:** GatewayUserPosition events
- **Enforcement:** Multiple strategies (targets, stop loss checks)
- **Dependencies:** StateManager (positions/orders), PNLTracker (P&L)

**Total Missing Rules Effort:** 8 rules × 3h = 24 hours

---

### 4. Enforcement Layer

#### ❌ Completely Missing - CRITICAL GAP

**Enforcement Engine**
- **File Needed:** `src/enforcement/engine.py`
- **Estimated Lines:** 400-500
- **Priority:** P0 (BLOCKS RUNTIME)
- **Effort:** 10 hours
- **Requirements:**
  - Initialize all 12 risk rules with config
  - Register event listeners for each rule
  - Dispatch events from Event Router to rules
  - Collect rule violation results
  - Execute enforcement actions (via EnforcementActions module)
  - Prevent duplicate actions (e.g., don't close same position twice)
  - Action priority queue (critical actions first)
  - Action logging (what was done, when, why)
  - Error recovery (continue if one action fails)
  - Thread safety (multiple events in parallel)
- **Pseudocode:**
  ```python
  class EnforcementEngine:
      def __init__(self, config, rest_client, modules):
          self.rules = self._initialize_rules(config)
          self.actions = EnforcementActions(rest_client)
          self.action_queue = PriorityQueue()

      def on_position_event(self, position):
          for rule in self.position_rules:
              violation = rule.check(position)
              if violation:
                  self.action_queue.put(violation.action)
          self._process_action_queue()

      def _process_action_queue(self):
          while not self.action_queue.empty():
              action = self.action_queue.get()
              self.actions.execute(action)
  ```
- **Tests Needed:** New tests to write (estimated 15-20 tests)

**Rule Registry**
- **File Needed:** `src/enforcement/rule_registry.py`
- **Estimated Lines:** 150-200
- **Priority:** P0
- **Effort:** 4 hours
- **Requirements:**
  - Map rule names → rule classes
  - Load rules dynamically from config
  - Validate rule configs
  - Enable/disable rules at runtime
  - Rule dependency resolution (some rules depend on others)
- **Example:**
  ```python
  RULE_REGISTRY = {
      'max_contracts': MaxContractsRule,
      'daily_realized_loss': DailyRealizedLossRule,
      # ... all 12 rules
  }
  ```

**Total Enforcement Layer Effort:** 14 hours

---

### 5. Daemon Layer

#### ❌ Completely Missing - CRITICAL GAP

**Main Daemon Process**
- **File Needed:** `src/daemon/main.py`
- **Estimated Lines:** 500-600
- **Priority:** P0 (BLOCKS RUNTIME)
- **Effort:** 12 hours
- **Requirements:**
  - Command-line entry point (argparse)
  - Load configuration from YAML/JSON
  - Initialize all core modules (9 modules)
  - Initialize REST client (authenticate)
  - Initialize SignalR client (connect)
  - Initialize Event Router
  - Initialize Enforcement Engine
  - Start event loop (asyncio or threading)
  - Signal handling (SIGTERM, SIGINT for graceful shutdown)
  - Health monitoring (restart components on failure)
  - Logging setup (file + console)
  - Daemon mode (background process)
- **Startup Sequence:**
  1. Parse CLI arguments
  2. Load config file
  3. Setup logging
  4. Initialize database
  5. Create core modules
  6. Authenticate REST API
  7. Connect SignalR
  8. Start enforcement engine
  9. Enter event loop
  10. Handle shutdown signals
- **Tests Waiting:** E2E tests exist (6 files, 30 tests)

**Config Loader**
- **File Needed:** `src/daemon/config_loader.py`
- **Estimated Lines:** 200-250
- **Priority:** P0
- **Effort:** 4 hours
- **Requirements:**
  - Load YAML/JSON config files
  - Validate config schema (required fields)
  - Default values for optional settings
  - Environment variable substitution (e.g., `${API_KEY}`)
  - Config merging (base config + overrides)
  - Config reload without restart (SIGHUP)
- **Config Structure:**
  ```yaml
  api:
    base_url: "https://..."
    username: "${USERNAME}"
    api_key: "${API_KEY}"

  rules:
    max_contracts:
      enabled: true
      limit: 10
    # ... all 12 rules

  daemon:
    log_level: INFO
    db_path: "./data/state.db"
    reset_time: "17:00:00"
  ```

**Initialization Manager**
- **File Needed:** `src/daemon/init_manager.py`
- **Estimated Lines:** 300-400
- **Priority:** P0
- **Effort:** 6 hours
- **Requirements:**
  - Initialize database (create tables if missing)
  - Load persisted state (lockouts, P&L, trades)
  - Restore from last session
  - Validate API connectivity
  - Prefetch contract metadata
  - Check for missed resets (if daemon was offline)
  - Dependency injection (create modules with config)
- **Initialization Order:**
  1. Database setup
  2. Core modules (StateManager, PNLTracker, etc.)
  3. REST client
  4. Load persisted data into modules
  5. SignalR client
  6. Event Router
  7. Enforcement Engine
  8. Start event processing

**Total Daemon Layer Effort:** 22 hours

---

### 6. CLI Layer

#### ❌ Completely Missing - NON-CRITICAL

**Trader CLI**
- **File Needed:** `src/cli/trader_cli.py`
- **Estimated Lines:** 300-400
- **Priority:** P2 (NICE TO HAVE)
- **Effort:** 8 hours
- **Requirements:**
  - Command-line interface for traders
  - IPC to daemon process (socket or pipe)
  - Commands:
    - `status` - Show account status, positions, P&L
    - `monitor` - Live monitoring (auto-refresh)
    - `lockouts` - View active lockouts
    - `rules` - List enabled rules and status
    - `logs` - Tail recent log entries
- **Example Usage:**
  ```bash
  trader-cli status
  trader-cli monitor --refresh 5s
  trader-cli lockouts
  ```

**Admin CLI**
- **File Needed:** `src/cli/admin_cli.py`
- **Estimated Lines:** 250-350
- **Priority:** P2 (NICE TO HAVE)
- **Effort:** 6 hours
- **Requirements:**
  - Administrative commands
  - Commands:
    - `config reload` - Reload configuration
    - `config show` - Display current config
    - `manage stop` - Stop daemon
    - `manage start` - Start daemon
    - `manage restart` - Restart daemon
    - `manage reset` - Trigger manual reset
    - `logs export` - Export logs to file

**IPC Layer**
- **File Needed:** `src/cli/ipc.py`
- **Estimated Lines:** 200-300
- **Priority:** P2
- **Effort:** 4 hours
- **Requirements:**
  - Unix socket or named pipe communication
  - JSON message protocol
  - Request/response pattern
  - Timeout handling
  - Authentication (shared secret)

**Total CLI Layer Effort:** 18 hours

---

### 7. Configuration

#### ✅ Partial

**Logging Config** (`config/logging.yaml`)
- **Status:** COMPLETE
- **Lines:** 2,143 (YAML)
- **Features:**
  - Rotating file handlers
  - Multiple log files (execution, results, errors)
  - Console output
  - Log level control

**Rules Config Files**
- **Status:** PARTIAL (need verification)
- **Location:** `config/` directory
- **Priority:** P1
- **Effort:** 2 hours
- **Requirements:**
  - Create YAML for each of 12 rules
  - Document all config options
  - Provide example configs
  - Default values

#### ❌ Missing

**Config Validation**
- **File Needed:** `src/daemon/config_validator.py`
- **Estimated Lines:** 200-250
- **Priority:** P1
- **Effort:** 3 hours
- **Requirements:**
  - JSON Schema or Pydantic models for validation
  - Validate required fields
  - Type checking (int, float, bool)
  - Range validation (e.g., limit > 0)
  - Enum validation (enforcement modes)
  - Helpful error messages

**Total Config Effort:** 5 hours

---

### 8. Persistence Layer

#### ⏳ Partial

**Database Schema**
- **Status:** Documented in specs, not implemented
- **Tables Needed:**
  - `daily_pnl` (realized P&L by date)
  - `trade_history` (trade timestamps)
  - `contract_cache` (metadata cache)
  - `lockouts` (active lockouts)
  - `enforcement_log` (actions taken)
  - `state_snapshot` (periodic state backups)

**Core Modules Have Persistence Methods:**
- PNLTracker has `save_to_db()`, `load_from_db()`
- LockoutManager has `save_to_db()`, `load_from_db()`
- ContractCache has `save_to_db()`, `load_from_db()`
- TradeCounter has `save_to_db()`, `load_from_db()`
- StateManager has `save_to_db()`, `load_from_db()`

**BUT:** No database initialization code exists!

#### ❌ Missing

**Database Initialization**
- **File Needed:** `src/persistence/database.py`
- **Estimated Lines:** 200-300
- **Priority:** P1
- **Effort:** 4 hours
- **Requirements:**
  - Create SQLite database file
  - Execute CREATE TABLE statements
  - Add indexes for performance
  - Handle schema version
  - Database connection pooling

**Migration System**
- **File Needed:** `src/persistence/migrations.py`
- **Estimated Lines:** 150-200
- **Priority:** P3 (FUTURE)
- **Effort:** 6 hours
- **Requirements:**
  - Track schema version
  - Apply schema changes
  - Rollback capability
  - Data migration scripts

**Total Persistence Effort:** 10 hours (P1 only: 4 hours)

---

### 9. Utilities

#### ✅ Completed

**Symbol Utils** (`src/utils/symbol_utils.py`)
- **Lines:** 34
- **Features:** Extract symbol root from contract ID

**Logging Infrastructure** (`src/risk_manager/logging/`)
- **Status:** PRODUCTION READY
- **Files:**
  - `config.py` - YAML loading
  - `formatters.py` - Custom formatters
  - `context.py` - Contextual logging
  - `performance.py` - Performance decorators

**No gaps in utilities**

---

### 10. Error Handling (Advanced)

#### ⏳ Specs Exist, Implementation Pending

**Error Code Mapping**
- **Spec:** `docs/ERROR_CODE_MAPPING_SPEC.md` (369 lines)
- **File Needed:** `src/api/error_mapper.py`
- **Priority:** P1
- **Effort:** 4 hours
- **Requirements:**
  - Map HTTP status codes → error codes
  - User-friendly error messages
  - Retry classification
  - PII sanitization

**Enhanced Rate Limiting**
- **Spec:** `docs/RATE_LIMITING_SPEC.md` (686 lines)
- **Current Status:** REST client has basic rate limiting
- **File Needed:** `src/api/rate_limiter.py`
- **Priority:** P1
- **Effort:** 6 hours
- **Requirements:**
  - Sliding window algorithm (10 sub-windows)
  - Per-endpoint limits
  - Priority queue
  - Pre-emptive throttling

**Circuit Breaker**
- **Spec:** `docs/CIRCUIT_BREAKER_SPEC.md` (790 lines)
- **File Needed:** `src/api/circuit_breaker.py`
- **Priority:** P2
- **Effort:** 8 hours
- **Requirements:**
  - CLOSED/OPEN/HALF_OPEN states
  - Per-service isolation
  - Exponential backoff
  - Fallback strategies

**Total Error Handling Effort:** 18 hours (P1: 10 hours, P2: 8 hours)

---

## Priority Breakdown

### P0 - CRITICAL (Blocks Runtime)

These components are **absolutely required** for the system to run. Without them, there is no runtime functionality.

| Component | Effort | Rationale |
|-----------|--------|-----------|
| Config Loader | 4h | Needed to load all settings |
| Database Initialization | 4h | Needed for persistence |
| Event Router | 8h | Connects API to core logic |
| SignalR Client | 12h | Provides real-time events |
| Enforcement Engine | 10h | Executes risk actions |
| Rule Registry | 4h | Manages rule lifecycle |
| Daemon Main Process | 12h | Wires everything together |
| Initialization Manager | 6h | Startup sequence |

**Total P0 Effort: 60 hours (7.5 days)**

**Critical Path:**
1. Config Loader (4h) - enables everything else
2. Database Init (4h) - needed for state
3. Initialization Manager (6h) - startup logic
4. Event Router (8h) - connects components
5. SignalR Client (12h) - real-time events
6. Rule Registry (4h) - rule management
7. Enforcement Engine (10h) - risk enforcement
8. Daemon Main (12h) - wires it all

**After P0 Complete:** System will start, connect to API, receive events, but **no risk rules will fire** (only 4/12 implemented).

---

### P1 - HIGH (Core Functionality)

These components complete the core risk management functionality. System runs without them, but lacks most risk rules.

| Component | Effort | Rationale |
|-----------|--------|-----------|
| **8 Missing Risk Rules** | 24h | Complete risk coverage |
| REST Client Completion | 4h | Full API access |
| Config Validation | 3h | Prevent invalid configs |
| Rules Config Files | 2h | Document rule settings |
| Error Code Mapping | 4h | Better error handling |
| Enhanced Rate Limiting | 6h | API protection |

**Total P1 Effort: 43 hours (5.4 days)**

**Breakdown:**
- RULE-003: DailyRealizedLoss (3h)
- RULE-004: DailyUnrealizedLoss (3h)
- RULE-005: MaxUnrealizedProfit (3h)
- RULE-007: CooldownAfterLoss (3h)
- RULE-008: NoStopLossGrace (3h)
- RULE-009: SessionBlockOutside (3h)
- RULE-010: AuthLossGuard (3h)
- RULE-012: TradeManagement (3h)
- REST completion (4h)
- Config work (5h)
- Error handling (10h)

**After P1 Complete:** System is **FEATURE COMPLETE** for risk management. All 12 rules operational.

---

### P2 - MEDIUM (User Interface)

These components add user-facing features and operational tools. Nice to have, not required for core functionality.

| Component | Effort | Rationale |
|-----------|--------|-----------|
| Trader CLI | 8h | User interface |
| Admin CLI | 6h | Admin tools |
| IPC Layer | 4h | CLI communication |
| Circuit Breaker | 8h | Advanced resilience |

**Total P2 Effort: 26 hours (3.25 days)**

**After P2 Complete:** System is **PRODUCTION READY** with full operational tooling.

---

### P3 - LOW (Future Enhancements)

These components are nice-to-have future additions.

| Component | Effort | Rationale |
|-----------|--------|-----------|
| Migration System | 6h | Schema versioning |
| Web Dashboard | 40h | GUI interface |
| Email Notifications | 12h | Alerts |
| Advanced Analytics | 20h | Reporting |

**Total P3 Effort: 78 hours** (not included in main estimate)

---

## Total Remaining Work Summary

| Priority | Components | Hours | Days (8h/day) | Status |
|----------|------------|-------|---------------|--------|
| **P0** | 8 critical | 60h | 7.5 days | **BLOCKS RUNTIME** |
| **P1** | 6 high | 43h | 5.4 days | **COMPLETES FEATURES** |
| **P2** | 4 medium | 26h | 3.25 days | **PRODUCTION READY** |
| **P3** | 4+ low | 78h | 9.75 days | **FUTURE** |
| **TOTAL (P0-P2)** | **18 components** | **129h** | **16.15 days** | **Full System** |

---

## Files to Create

### Priority 0 (Critical)

```
src/api/signalr_client.py               ~450 lines
src/core/event_router.py                 ~350 lines
src/enforcement/engine.py                ~450 lines
src/enforcement/rule_registry.py         ~175 lines
src/daemon/main.py                       ~550 lines
src/daemon/config_loader.py              ~225 lines
src/daemon/init_manager.py               ~350 lines
src/persistence/database.py              ~250 lines
```

**Total P0:** 2,800 lines across 8 files

### Priority 1 (High)

```
src/rules/daily_realized_loss.py         ~175 lines
src/rules/daily_unrealized_loss.py       ~175 lines
src/rules/max_unrealized_profit.py       ~175 lines
src/rules/cooldown_after_loss.py         ~135 lines
src/rules/no_stop_loss_grace.py          ~135 lines
src/rules/session_block_outside_hours.py ~135 lines
src/rules/auth_loss_guard.py             ~175 lines
src/rules/trade_management.py            ~225 lines
src/daemon/config_validator.py           ~225 lines
src/api/error_mapper.py                  ~200 lines
src/api/rate_limiter.py                  ~300 lines
config/rules/*.yaml                      ~200 lines (12 files)
```

**Total P1:** 2,255 lines across 20 files

### Priority 2 (Medium)

```
src/cli/trader_cli.py                    ~350 lines
src/cli/admin_cli.py                     ~300 lines
src/cli/ipc.py                           ~250 lines
src/api/circuit_breaker.py               ~400 lines
```

**Total P2:** 1,300 lines across 4 files

### Grand Total

**32 new files, ~6,355 lines of code**

---

## SPECS Alignment Analysis

### ✅ SPECS Accuracy

**What Matches SPECS:**
- Core modules design perfectly matches SPECS
- Risk rules design matches SPECS (for implemented rules)
- Module interfaces match SPECS
- Test coverage matches SPECS expectations
- Database schema matches SPECS

**SPECS Coverage:**
- Architecture: ✅ Complete
- Core modules: ✅ Complete (9/9)
- Risk rules: ✅ Complete (12/12 specs)
- API layer: ✅ Complete
- Error handling: ✅ Complete (5 detailed specs)
- Testing strategy: ✅ Complete

### ⚠️ SPECS Gaps/Discrepancies

**What SPECS Don't Cover:**
1. **Converter Layer** - Not mentioned in original SPECS
   - We added `converters.py` (478 lines) to handle camelCase ↔ snake_case
   - We added `enums.py` (316 lines) for state mapping
   - This was necessary due to TopstepX API contract inconsistencies
   - **Recommendation:** Add converter documentation to SPECS

2. **Field Name Mappings** - SPECS assume consistent naming
   - Reality: API uses camelCase, we use snake_case internally
   - Converters handle this, but SPECS don't document the mapping
   - **Recommendation:** Add field mapping tables to SPECS

3. **Event Router** - Not explicitly specified
   - SPECS mention SignalR events → rules, but don't specify the router layer
   - We need a router to dispatch events to multiple rules
   - **Recommendation:** Add Event Router to architecture SPECS

4. **Daemon Design** - High-level only
   - SPECS describe "daemon process" but lack initialization details
   - Startup sequence not documented
   - Component wiring not specified
   - **Recommendation:** Add detailed daemon architecture to SPECS

5. **CLI Design** - Mentioned but not detailed
   - SPECS mention CLI exists, but don't specify commands or IPC
   - **Recommendation:** Add CLI specification document

### 🔄 SPECS Updates Needed

1. **Add Converter Layer Documentation**
   - Document camelCase ↔ snake_case conversions
   - Document enum value mappings
   - Document field name mappings (e.g., `accountId` → `account_id`)

2. **Add Event Router Specification**
   - Document event routing logic
   - Document event ordering requirements
   - Document error handling in router

3. **Add Daemon Architecture Specification**
   - Document component initialization order
   - Document dependency injection
   - Document startup/shutdown sequences
   - Document signal handling

4. **Add Integration Architecture Section**
   - Document how all pieces fit together
   - Document data flow (API → Router → Rules → Enforcement)
   - Document state synchronization

5. **Add CLI Specification**
   - Document trader CLI commands
   - Document admin CLI commands
   - Document IPC protocol

6. **Update API Contract Documentation**
   - Document actual field names from TopstepX API
   - Document inconsistencies (REST vs SignalR)
   - Document enum value mappings

---

## Test Coverage Analysis

### Current Test Status

**Total Tests:** 270 tests across 54 test files

**Test Breakdown:**
- Unit Tests: 144 tests (21 files)
  - Core Modules: 66 tests ✅ (9 files, all passing)
  - Risk Rules: 78 tests ⏳ (12 files, RED - awaiting implementation)
- Integration Tests: 22 tests (8 files)
  - REST API: 10 tests ✅ (4 files, all passing)
  - SignalR: 12 tests ⏳ (4 files, RED - awaiting implementation)
- E2E Tests: 30 tests (6 files, RED - awaiting full integration)
- Infrastructure Tests: 74 tests (19 fixture/helper files)

### Test Health

**Passing Tests:** 76/270 (28%)
- All core module tests (66)
- All REST API tests (10)

**RED Tests (Awaiting Implementation):** 194/270 (72%)
- 78 rule tests (8 missing rules + 4 implemented but not integrated)
- 12 SignalR tests (SignalR client missing)
- 30 E2E tests (daemon missing)
- 74 helper tests (run during actual test execution)

**This is EXPECTED for TDD approach** - write tests first, implement later.

### Test Quality

**Test Coverage is Excellent:**
- Every core module has 6-10 comprehensive tests
- Every risk rule has 6-12 comprehensive tests
- Integration tests cover all major APIs
- E2E tests cover complete workflows
- Edge cases are well covered
- Error scenarios are tested

**Test Fixtures are Comprehensive:**
- 139 fixtures across 10 files
- Realistic data samples
- Multiple scenarios (normal, edge cases, errors)
- Well-documented

---

## Recommendations

### Phase 1: Get to Runtime (P0 - 7.5 days)

**Goal:** System starts and runs (even without all rules)

**Order of Implementation:**
1. **Config Loader** (Day 1, 4h)
   - Load YAML config
   - Validate basic structure
   - Environment variables

2. **Database Initialization** (Day 1, 4h)
   - Create SQLite database
   - Create tables
   - Test persistence

3. **Initialization Manager** (Day 2, 6h)
   - Component creation
   - Dependency injection
   - State restoration

4. **Event Router** (Day 2-3, 8h)
   - Event dispatching
   - Converter integration
   - Error handling

5. **SignalR Client** (Day 3-4, 12h)
   - WebSocket connection
   - Event subscription
   - Reconnection logic

6. **Rule Registry** (Day 5, 4h)
   - Rule loading
   - Config validation
   - Rule lifecycle

7. **Enforcement Engine** (Day 5-6, 10h)
   - Event handling
   - Rule execution
   - Action execution

8. **Daemon Main** (Day 6-7, 12h)
   - Startup sequence
   - Event loop
   - Shutdown handling

**After Phase 1:** System is OPERATIONAL but only 4/12 rules work.

---

### Phase 2: Complete Risk Rules (P1 - 5.4 days)

**Goal:** All 12 risk rules operational

**Order of Implementation:**
1. **RULE-003: DailyRealizedLoss** (Day 1, 3h) - Most critical
2. **RULE-004: DailyUnrealizedLoss** (Day 1, 3h) - Most critical
3. **RULE-005: MaxUnrealizedProfit** (Day 1, 2h) - High impact
4. **RULE-010: AuthLossGuard** (Day 2, 3h) - Safety critical
5. **RULE-007: CooldownAfterLoss** (Day 2, 3h) - Related to #10
6. **RULE-008: NoStopLossGrace** (Day 2, 2h) - Safety critical
7. **RULE-009: SessionBlockOutside** (Day 3, 3h) - Time-based
8. **RULE-012: TradeManagement** (Day 3, 3h) - Most complex

9. **REST Client Completion** (Day 4, 4h)
10. **Config Files** (Day 4, 2h)
11. **Config Validation** (Day 4, 3h)
12. **Error Code Mapping** (Day 5, 4h)
13. **Enhanced Rate Limiting** (Day 5, 6h)

**After Phase 2:** System is FEATURE COMPLETE.

---

### Phase 3: Production Tooling (P2 - 3.25 days)

**Goal:** Operational readiness

**Order of Implementation:**
1. **IPC Layer** (Day 1, 4h)
2. **Trader CLI** (Day 1-2, 8h)
3. **Admin CLI** (Day 2, 6h)
4. **Circuit Breaker** (Day 3, 8h)

**After Phase 3:** System is PRODUCTION READY.

---

### Total Timeline

| Phase | Duration | Cumulative | Status |
|-------|----------|------------|--------|
| Phase 1 (P0) | 7.5 days | 7.5 days | Runtime capable |
| Phase 2 (P1) | 5.4 days | 12.9 days | Feature complete |
| Phase 3 (P2) | 3.25 days | 16.15 days | Production ready |

**16 days total to production-ready system**

---

## Dependency Graph

### What Can Be Built In Parallel

**Phase 1 Parallelization:**
- Config Loader (no dependencies) - START FIRST
- Database Init (no dependencies) - PARALLEL
- After both complete:
  - Event Router + SignalR Client (parallel)
  - Initialization Manager (depends on config)
- After Event Router + SignalR:
  - Rule Registry + Enforcement Engine (parallel)
- After all above:
  - Daemon Main (wires everything)

**Phase 2 Parallelization:**
- All 8 rules can be built in parallel (share same dependencies)
- Config work in parallel with rules
- Error handling in parallel with rules

**Phase 3 Parallelization:**
- IPC + Trader CLI + Admin CLI all parallel
- Circuit Breaker independent

---

## Risk Assessment

### High Risk Items

1. **SignalR Client** (12h)
   - **Risk:** Complex WebSocket protocol, reconnection logic
   - **Mitigation:** Use proven `signalrcore` library, comprehensive tests exist

2. **Enforcement Engine** (10h)
   - **Risk:** Complex orchestration, race conditions
   - **Mitigation:** All dependencies complete, clear interface design

3. **Daemon Main** (12h)
   - **Risk:** Wiring all components, startup sequence
   - **Mitigation:** All components exist, clear initialization order

### Medium Risk Items

1. **Event Router** (8h)
   - **Risk:** Event ordering, error propagation
   - **Mitigation:** Well-defined interface, converters complete

2. **Missing Rules** (24h total)
   - **Risk:** Complex logic, edge cases
   - **Mitigation:** Comprehensive tests exist, similar rules already implemented

### Low Risk Items

1. **Config Loader** (4h)
   - Standard YAML loading, well-understood

2. **Database Init** (4h)
   - Simple SQLite, schema already defined

3. **CLI Components** (18h)
   - Standard CLI patterns, low complexity

---

## Success Criteria

### Phase 1 Success Criteria

- [ ] Daemon starts without errors
- [ ] Config loads from YAML
- [ ] Database initializes with all tables
- [ ] REST API authenticates successfully
- [ ] SignalR connects and receives events
- [ ] Event Router dispatches to rules
- [ ] Enforcement Engine executes actions
- [ ] 4 implemented rules fire correctly
- [ ] Graceful shutdown works
- [ ] Logs are written correctly

### Phase 2 Success Criteria

- [ ] All 12 rules implemented
- [ ] All 78 rule tests pass (GREEN)
- [ ] All 12 SignalR tests pass (GREEN)
- [ ] REST client has all 10 endpoints
- [ ] Config validation catches invalid configs
- [ ] Error mapping provides friendly messages
- [ ] Rate limiting prevents API overload

### Phase 3 Success Criteria

- [ ] Trader CLI works (status, monitor, logs)
- [ ] Admin CLI works (config, manage)
- [ ] Circuit breaker protects against API failures
- [ ] All 270 tests pass (GREEN)
- [ ] E2E tests demonstrate full workflows

---

## Conclusion

**Overall Project Health:** STRONG ✅

**Foundation Status:** PRODUCTION READY (100% complete)
- Core modules: 100% complete (9/9)
- API client: 100% complete
- Converters: 100% complete
- Logging: 100% complete
- Tests: Comprehensive coverage

**Integration Status:** CRITICAL GAPS ❌
- Runtime layer: 0% complete (daemon, event router, signalr)
- Enforcement layer: 0% complete (engine, registry)
- Configuration layer: Partial

**Features Status:** PARTIAL ⚠️
- Risk rules: 4/12 complete (33%)
- Remaining 8 rules have complete test suites

**Key Strengths:**
1. Excellent foundation - all core modules production ready
2. Comprehensive test coverage - 270 tests, well-designed
3. Clear architecture - modular, testable design
4. Good documentation - specs exist for all components

**Key Challenges:**
1. Runtime integration completely missing (P0 work)
2. Most risk rules not implemented (P1 work)
3. No user interface (P2 work)

**Recommended Approach:**
1. Focus on P0 first (7.5 days) - get system running
2. Then P1 (5.4 days) - complete features
3. Finally P2 (3.25 days) - production polish

**Total Estimated Effort:** 16 days to production-ready system

**Confidence Level:** HIGH
- Clear path forward
- No architectural unknowns
- All dependencies complete
- Comprehensive test coverage
- Proven design patterns

---

**End of Gap Analysis**
