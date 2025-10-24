# Phase 1: Make It Work (Console Mode)

**Status:** IN PROGRESS
**Goal:** Create runnable daemon that monitors TopstepX and enforces rules
**Estimated Time:** 3-5 days (32-42 hours)
**Started:** 2025-10-23
**Target Completion:** TBD

---

## 🎯 OBJECTIVE

Build a working daemon that:
- Starts in console mode
- Connects to TopstepX API (REST + SignalR)
- Processes real-time events
- Updates state (positions, P&L, etc.)
- Checks risk rules
- Enforces actions (close positions, lockouts)

**Deliverable:** `python -m src.core.daemon` runs and monitors accounts

---

## 📋 TASKS BREAKDOWN

### Task 1: Database Setup (~4 hours)

**Status:** ⏳ NOT STARTED

**Goal:** Create SQLite database with complete schema

**Steps:**

1. **Create data directory** (2 min)
   ```bash
   cd "/home/jakers/projects/simple-risk-manager/simple risk manager"
   mkdir -p data
   ```

2. **Write schema.sql** (30 min)
   - Read: `project-specs/SPECS/07-DATA-MODELS/DATABASE_SCHEMA.md`
   - Create: `data/schema.sql`
   - Include all 9 tables:
     - `lockouts` (MOD-002)
     - `daily_pnl` (MOD-005)
     - `contract_cache` (MOD-007)
     - `trade_history` (MOD-008)
     - `session_state` (MOD-008)
     - `positions` (MOD-009)
     - `orders` (MOD-009)
     - `enforcement_log` (MOD-001)
     - `reset_schedule` (MOD-004)

3. **Create init script** (30 min)
   - Create: `scripts/init_database.py`
   - Function: Create database from schema
   - Function: Verify all tables exist
   - Function: Insert test data (optional)

4. **Initialize database** (5 min)
   ```bash
   python scripts/init_database.py
   # Should create: data/state.db
   ```

5. **Test database** (30 min)
   - Create: `tests/integration/test_database.py`
   - Test: All tables exist
   - Test: Can insert/select/update/delete
   - Test: Foreign keys work
   - Test: Indexes exist

6. **Verify with modules** (2 hours)
   - Update each module to use real database instead of mocks
   - Test: `LockoutManager` can read/write lockouts table
   - Test: `PNLTracker` can read/write daily_pnl table
   - Test: `StateManager` can read/write positions/orders tables
   - Run: `python -m pytest tests/unit/test_lockout_manager.py -v`

**Files to Create:**
- `data/schema.sql`
- `scripts/init_database.py`
- `tests/integration/test_database.py`

**Files to Read:**
- `project-specs/SPECS/07-DATA-MODELS/DATABASE_SCHEMA.md`
- `src/core/lockout_manager.py` (see how it expects to use DB)
- `src/core/pnl_tracker.py` (see how it expects to use DB)

**Success Criteria:**
- ✅ `data/state.db` exists
- ✅ All 9 tables created
- ✅ Integration test passes
- ✅ At least 1 module verified with real DB

**Mark complete when:** Database exists and 1 module tested with it

---

### Task 2: Configuration Files (~3 hours)

**Status:** ⏳ NOT STARTED

**Goal:** Create all required configuration files

**Steps:**

1. **Create risk_config.yaml** (1.5 hours)
   - Read: `project-specs/SPECS/08-CONFIGURATION/RISK_CONFIG_YAML_SPEC.md`
   - Read: Each rule spec in `project-specs/SPECS/03-RISK-RULES/rules/`
   - Create: `config/risk_config.yaml`
   - Include: All 12 rules with default settings
   - Format:
     ```yaml
     rules:
       RULE-001:
         enabled: true
         limit: 5
         count_type: "net"
         # ... etc
     ```

2. **Create accounts.yaml template** (30 min)
   - Read: `project-specs/SPECS/08-CONFIGURATION/ACCOUNTS_YAML_SPEC.md` (if exists)
   - Create: `config/accounts.yaml.template`
   - Include: 1 example account with placeholders
   - Format:
     ```yaml
     accounts:
       - account_id: 12345
         api_key: "YOUR_API_KEY_HERE"
         api_secret: "YOUR_API_SECRET_HERE"
         enabled: true
     ```

3. **Create admin_password.hash** (15 min)
   - Create: `scripts/create_admin_password.py`
   - Function: Hash password with bcrypt/sha256
   - Run: Create initial admin password
   - Store: `config/admin_password.hash`

4. **Create config loader** (45 min)
   - Create: `src/config/config_loader.py`
   - Function: Load and validate YAML configs
   - Function: Merge defaults with user settings
   - Function: Validate all required fields
   - Error: Clear messages for missing/invalid config

5. **Test config loading** (15 min)
   - Create: `tests/unit/test_config_loader.py`
   - Test: Load valid config
   - Test: Detect missing required fields
   - Test: Detect invalid values
   - Test: Merge defaults

**Files to Create:**
- `config/risk_config.yaml`
- `config/accounts.yaml.template`
- `config/admin_password.hash`
- `scripts/create_admin_password.py`
- `src/config/config_loader.py`
- `tests/unit/test_config_loader.py`

**Files to Read:**
- `project-specs/SPECS/08-CONFIGURATION/RISK_CONFIG_YAML_SPEC.md`
- `project-specs/SPECS/03-RISK-RULES/rules/*.md` (all 12 rules)
- `config/logging.yaml` (existing, see format)

**Success Criteria:**
- ✅ `config/risk_config.yaml` has all 12 rules
- ✅ `config/accounts.yaml.template` exists
- ✅ Config loader validates correctly
- ✅ Tests pass

**Mark complete when:** All config files exist and loader works

---

### Task 3: Event Router (~8-12 hours)

**Status:** ⏳ NOT STARTED

**Goal:** Core event processing pipeline

**Steps:**

1. **Create event router skeleton** (1 hour)
   - Read: `project-specs/SPECS/02-BACKEND-DAEMON/EVENT_PIPELINE.md`
   - Create: `src/core/event_router.py`
   - Class: `EventRouter`
   - Methods:
     - `__init__(modules, rules, config)`
     - `route_event(event_type, payload)`
     - `_update_state(event_type, payload)`
     - `_check_lockout(account_id)`
     - `_check_rules(account_id, event_type)`
     - `_enforce_action(account_id, breach)`

2. **Implement state update logic** (2-3 hours)
   - Map event types to state updates:
     - `GatewayUserTrade` → PNLTracker, TradeCounter
     - `GatewayUserPosition` → StateManager (positions)
     - `GatewayUserOrder` → StateManager (orders)
     - `MarketQuote` → QuoteTracker
   - Update state BEFORE rule checks (critical!)
   - Log all state changes

3. **Implement lockout gating** (1 hour)
   - Check `LockoutManager.is_locked_out(account_id)` first
   - If locked, skip rule checks
   - Log lockout bypasses

4. **Implement rule routing** (2-3 hours)
   - Map event types to relevant rules:
     - Position events → RULE-001, RULE-002, etc.
     - Trade events → RULE-003, RULE-006, RULE-007
     - Order events → RULE-008, RULE-009
   - Call `rule.check(event)` for each relevant rule
   - Collect breach responses

5. **Implement enforcement** (2-3 hours)
   - Call `EnforcementActions` based on breach
   - Log enforcement actions
   - Update lockout state if needed
   - Handle enforcement failures

6. **Add error handling** (1 hour)
   - Try/catch around each step
   - Log errors with context
   - Continue processing other events on error
   - Alert on repeated failures

7. **Test event router** (1-2 hours)
   - Create: `tests/unit/test_event_router.py`
   - Test: State updates before rule checks
   - Test: Lockout gating works
   - Test: Rules receive correct events
   - Test: Enforcement executes
   - Test: Error handling

**Files to Create:**
- `src/core/event_router.py` (200-300 lines)
- `tests/unit/test_event_router.py`

**Files to Read:**
- `project-specs/SPECS/02-BACKEND-DAEMON/EVENT_PIPELINE.md` (critical!)
- `src/core/enforcement_actions.py` (see how to call it)
- `src/core/lockout_manager.py` (see how to check lockouts)
- `src/rules/*.py` (see how rules expose check() method)

**Dependencies:**
- All core modules in `src/core/`
- All rules in `src/rules/`
- Database must exist (Task 1)
- Config loader must work (Task 2)

**Success Criteria:**
- ✅ State updates happen first
- ✅ Lockout gating works
- ✅ Rules are routed correctly
- ✅ Enforcement executes
- ✅ Tests pass

**Mark complete when:** Event router processes mock events end-to-end

---

### Task 4: Main Daemon (~12-16 hours)

**Status:** ⏳ NOT STARTED

**Goal:** Daemon that connects to TopstepX and runs event loop

**Steps:**

1. **Create daemon skeleton** (1-2 hours)
   - Read: `project-specs/SPECS/02-BACKEND-DAEMON/DAEMON_ARCHITECTURE.md`
   - Create: `src/core/daemon.py`
   - Class: `RiskManagerDaemon`
   - Methods:
     - `__init__(config_path)`
     - `initialize()` - Load configs, connect DB, init modules
     - `start()` - Start event loop
     - `stop()` - Graceful shutdown
     - `_setup_signalr()` - SignalR connection setup
     - `_event_loop()` - Main event processing loop

2. **Implement initialization** (2-3 hours)
   - Load config files (risk_config.yaml, accounts.yaml)
   - Connect to database (create connection pool)
   - Initialize all core modules (pass DB connection)
   - Initialize all rules (pass modules, config)
   - Create event router (pass modules, rules)
   - Validate everything initialized

3. **Implement SignalR setup** (3-4 hours)
   - Read: `project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/REALTIME_DATA_OVERVIEW.md`
   - Use: `src/api/signalr_manager.py` (already exists!)
   - Connect to User Hub (positions, trades, orders)
   - Connect to Market Hub (quotes)
   - Register event callbacks:
     - `on_trade(event)` → `event_router.route_event('trade', event)`
     - `on_position(event)` → `event_router.route_event('position', event)`
     - `on_order(event)` → `event_router.route_event('order', event)`
     - `on_quote(event)` → `event_router.route_event('quote', event)`

4. **Implement event loop** (2-3 hours)
   - Start SignalR connections
   - Keep-alive loop (check connection health)
   - Background tasks:
     - Daily reset checks (every minute)
     - Connection health monitoring
   - Handle signals (SIGINT, SIGTERM for shutdown)

5. **Implement graceful shutdown** (1-2 hours)
   - Close SignalR connections
   - Flush any pending events
   - Close database connections
   - Save state
   - Log shutdown

6. **Add console mode entry point** (1 hour)
   - Create: `src/core/__main__.py`
   - Parse command line args
   - Setup logging
   - Start daemon
   - Handle Ctrl+C gracefully

7. **Test daemon** (2-3 hours)
   - Create: `tests/integration/test_daemon.py`
   - Test: Initialization works
   - Test: Config loading
   - Test: Module initialization
   - Test: Event routing (with mocks)
   - Test: Graceful shutdown

**Files to Create:**
- `src/core/daemon.py` (300-500 lines)
- `src/core/__main__.py` (50-100 lines)
- `tests/integration/test_daemon.py`

**Files to Read:**
- `project-specs/SPECS/02-BACKEND-DAEMON/DAEMON_ARCHITECTURE.md` (critical!)
- `src/api/signalr_manager.py` (already exists, use this!)
- `src/api/rest_client.py` (for API calls)
- `src/core/event_router.py` (from Task 3)

**Dependencies:**
- Database (Task 1)
- Config files (Task 2)
- Event router (Task 3)

**Success Criteria:**
- ✅ Daemon starts without errors
- ✅ Connects to database
- ✅ Loads configs
- ✅ Initializes all modules
- ✅ SignalR connections work (mocked for now)
- ✅ Event loop runs
- ✅ Graceful shutdown works

**Mark complete when:** Daemon runs in console mode with mocked SignalR

---

### Task 5: Integration Testing (~4-6 hours)

**Status:** ⏳ NOT STARTED

**Goal:** Connect to real TopstepX API and verify everything works

**Steps:**

1. **Get TopstepX sandbox credentials** (30 min)
   - Sign up for sandbox account
   - Get API key/secret
   - Add to `config/accounts.yaml`

2. **Test REST API connection** (1-2 hours)
   - Update: `src/api/rest_client.py` with real credentials
   - Test: Authentication
   - Test: Fetch contracts
   - Test: Fetch positions
   - Test: Fetch orders
   - Verify: All endpoints work

3. **Test SignalR connection** (2-3 hours)
   - Connect to real SignalR User Hub
   - Connect to real SignalR Market Hub
   - Subscribe to events
   - Verify: Events received
   - Verify: Event format matches specs
   - Log: All events for inspection

4. **End-to-end test** (1-2 hours)
   - Start daemon with real API
   - Place a test trade (manually via TopstepX UI)
   - Verify: Event received
   - Verify: State updated
   - Verify: Rule checked
   - Verify: Logged correctly

5. **Test enforcement** (30 min)
   - Configure a rule to trigger easily
   - Trigger the rule (e.g., exceed max contracts)
   - Verify: Enforcement action executes
   - Verify: Position closed (or lockout applied)
   - Verify: Logged in database

**Files to Update:**
- `config/accounts.yaml` (add real credentials)
- `tests/integration/test_real_api.py` (create)
- `tests/integration/test_e2e.py` (create)

**Files to Read:**
- `project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/` (all API docs)
- `src/api/rest_client.py`
- `src/api/signalr_manager.py`

**Dependencies:**
- Daemon working (Task 4)
- Event router working (Task 3)
- TopstepX sandbox account

**Success Criteria:**
- ✅ Connected to real TopstepX API
- ✅ REST API calls work
- ✅ SignalR events received
- ✅ Full event → state → rule → enforce pipeline works
- ✅ At least 1 rule enforcement verified

**Mark complete when:** Daemon processes real events and enforces 1 rule

---

## 📊 PHASE 1 COMPLETION CHECKLIST

- [ ] Task 1: Database Setup (4 hours)
- [ ] Task 2: Configuration Files (3 hours)
- [ ] Task 3: Event Router (8-12 hours)
- [ ] Task 4: Main Daemon (12-16 hours)
- [ ] Task 5: Integration Testing (4-6 hours)

**Total Time:** 32-42 hours (3-5 days)

---

## ✅ PHASE 1 COMPLETE WHEN:

- ✅ Database exists with all 9 tables
- ✅ Config files created and loaded
- ✅ Event router processes events correctly
- ✅ Daemon runs in console mode
- ✅ Connects to real TopstepX API
- ✅ Processes real events
- ✅ Enforces at least 1 rule on real data
- ✅ All integration tests pass

---

## 🚦 HOW TO RUN WHEN COMPLETE

```bash
cd "/home/jakers/projects/simple-risk-manager/simple risk manager"
source venv/bin/activate

# Initialize database (first time only)
python scripts/init_database.py

# Start daemon in console mode
python -m src.core.daemon --config config/risk_config.yaml

# Should see:
# [2025-10-23 14:00:00] INFO - Risk Manager Daemon starting...
# [2025-10-23 14:00:01] INFO - Database connected: data/state.db
# [2025-10-23 14:00:01] INFO - Loaded 12 risk rules
# [2025-10-23 14:00:02] INFO - Connected to TopstepX API
# [2025-10-23 14:00:03] INFO - SignalR User Hub connected
# [2025-10-23 14:00:03] INFO - Monitoring 1 account(s)...
# [2025-10-23 14:00:03] INFO - Daemon running. Press Ctrl+C to stop.
```

---

## 📁 FILES CREATED IN PHASE 1

**Database:**
- `data/state.db` - SQLite database
- `data/schema.sql` - Schema definition
- `scripts/init_database.py` - Database initialization

**Configuration:**
- `config/risk_config.yaml` - Risk rules settings
- `config/accounts.yaml.template` - Account template
- `config/admin_password.hash` - Admin auth
- `src/config/config_loader.py` - Config loading logic

**Core Application:**
- `src/core/event_router.py` - Event pipeline
- `src/core/daemon.py` - Main daemon
- `src/core/__main__.py` - Entry point

**Tests:**
- `tests/integration/test_database.py`
- `tests/integration/test_daemon.py`
- `tests/integration/test_real_api.py`
- `tests/integration/test_e2e.py`
- `tests/unit/test_config_loader.py`
- `tests/unit/test_event_router.py`

---

## 🔄 UPDATING THIS FILE

**After completing each task:**

1. Change status from ⏳ NOT STARTED to ✅ COMPLETE
2. Add actual time taken
3. Note any deviations from plan
4. Update completion checklist
5. Mark any blockers or issues

**When Phase 1 complete:**

1. Update `START_HERE.md` to point to Phase 2
2. Change this file's status to ✅ COMPLETE
3. Document lessons learned
4. Note any technical debt

---

**Phase 1 Status:** IN PROGRESS
**Last Updated:** 2025-10-23
**Next Task:** Task 1 - Database Setup
