# Specification Attachment Map

**Generated:** 2025-10-22
**Purpose:** Forward mapping from specifications to implementation components
**Format:** Spec → Attachments (Modules, Endpoints, Database, Tests, Configs)

---

## How to Use This Document

For each specification, this document lists:
- **Modules:** Which source code files implement this spec
- **API Endpoints:** Which TopstepX API endpoints this spec uses
- **Database:** Which database tables this spec affects
- **Tests:** Which test files should validate this spec
- **Config:** Which configuration files this spec depends on
- **Dependencies:** Other specs this spec requires

---

## Core Architecture Specifications

### ARCH-V2.2: System Architecture v2
**File:** `00-CORE-CONCEPT/system_architecture_v2.md`

**Modules:**
- `src/core/daemon.py` - Main daemon entry point
- `src/core/event_router.py` - Event routing logic
- `src/core/websocket_server.py` - WebSocket broadcast server
- `src/service/windows_service.py` - Windows Service wrapper
- `src/service/installer.py` - Service installation

**API Endpoints:**
- ALL TopstepX endpoints (system-wide integration)
- SignalR User Hub (`wss://rtc.topstepx.com/hubs/user`)
- SignalR Market Hub (`wss://rtc.topstepx.com/hubs/market`)

**Database:**
- ALL 9 tables (system-wide state management)

**Tests:**
- `tests/core/test_daemon_startup.py`
- `tests/core/test_daemon_shutdown.py`
- `tests/core/test_event_router.py`
- `tests/integration/test_full_system.py`

**Config:**
- `config/accounts.yaml` - Account credentials
- `config/risk_config.yaml` - Rule configurations

**Dependencies:** ALL specs (master architecture)

---

### DAEMON-001: Daemon Architecture
**File:** `02-BACKEND-DAEMON/DAEMON_ARCHITECTURE.md`

**Modules:**
- `src/core/daemon.py` - 29-step startup, 6-thread model, shutdown
- `src/core/event_router.py` - Event dispatch
- `src/core/websocket_server.py` - Real-time CLI broadcasting
- `src/service/windows_service.py` - Service lifecycle
- `src/cli/admin/service_control.py` - Service management

**API Endpoints:**
- `/api/Auth/apiKey` - Authentication
- `/api/Auth/validate` - Token validation

**Database:**
- ALL 9 tables (state recovery on restart)

**Tests:**
- `tests/core/test_daemon_startup.py` - 29-step startup
- `tests/core/test_threading_model.py` - 6 threads
- `tests/core/test_daemon_shutdown.py` - Graceful shutdown
- `tests/core/test_crash_recovery.py` - Emergency shutdown

**Config:**
- `config/accounts.yaml` - Authentication
- `config/risk_config.yaml` - Rules to load

**Dependencies:** MOD-001 through MOD-009, STATE-001, DB-SCHEMA-001

---

### PIPE-001: Event Pipeline
**File:** `02-BACKEND-DAEMON/EVENT_PIPELINE.md`

**Modules:**
- `src/core/event_router.py` - Event routing (<10ms processing)
- `src/api/signalr_listener.py` - SignalR event handlers

**API Endpoints:**
- SignalR User Hub events (GatewayUserTrade, GatewayUserPosition, GatewayUserOrder, GatewayUserAccount)
- SignalR Market Hub events (MarketQuote)

**Database:**
- No direct DB access (calls modules for state updates)

**Tests:**
- `tests/core/test_event_pipeline.py`
- `tests/performance/test_event_latency.py`

**Config:**
- None (event routing logic is hardcoded)

**Dependencies:** MOD-001 through MOD-009, all 12 RULE specs

---

### STATE-001: State Management Strategy
**File:** `02-BACKEND-DAEMON/STATE_MANAGEMENT.md`

**Modules:**
- `src/state/state_manager.py` (MOD-009) - Position/order state
- `src/state/pnl_tracker.py` (MOD-005) - P&L tracking
- `src/state/lockout_manager.py` (MOD-002) - Lockouts
- ALL 9 module files

**API Endpoints:**
- None (internal state management)

**Database:**
- ALL 9 tables (hybrid in-memory + SQLite persistence)

**Tests:**
- `tests/state/test_memory_footprint.py`
- `tests/state/test_batched_writes.py`
- `tests/state/test_crash_recovery.py`

**Config:**
- None (state strategy is architecture-level)

**Dependencies:** DB-SCHEMA-001, MOD-002, MOD-005, MOD-009

---

## Module Specifications

### MOD-001: Enforcement Actions
**File:** `04-CORE-MODULES/modules/enforcement_actions.md`

**Modules:**
- `src/enforcement/actions.py` - Enforcement executor

**API Endpoints:**
- `/api/Position/closeContract` - Close positions
- `/api/Position/searchOpen` - Query positions
- `/api/Order/cancel` - Cancel orders
- `/api/Order/place` - Place stop-loss orders

**Database:**
- `enforcement_log` - Audit trail of actions

**Tests:**
- `tests/enforcement/test_close_positions.py`
- `tests/enforcement/test_cancel_orders.py`
- `tests/enforcement/test_enforcement_logging.py`

**Config:**
- None (enforcement logic driven by rules)

**Dependencies:** API-INT-001 (TopstepX integration)

---

### MOD-002: Lockout Manager
**File:** `04-CORE-MODULES/modules/lockout_manager.py`

**Modules:**
- `src/state/lockout_manager.py`

**API Endpoints:**
- None (internal state management)

**Database:**
- `lockouts` - Current lockout state

**Tests:**
- `tests/state/test_lockout_set_clear.py`
- `tests/state/test_lockout_expiry.py`
- `tests/state/test_timer_lockout.py`

**Config:**
- `config/risk_config.yaml` - Lockout durations per rule

**Dependencies:** MOD-003 (Timer Manager for expiry checks)

---

### MOD-003: Timer Manager
**File:** `04-CORE-MODULES/modules/timer_manager.md`

**Modules:**
- `src/state/timer_manager.py`

**API Endpoints:**
- None (internal timer management)

**Database:**
- None (in-memory only, no persistence)

**Tests:**
- `tests/state/test_timer_start_stop.py`
- `tests/state/test_timer_expiry.py`

**Config:**
- None (timers configured per-rule in risk_config.yaml)

**Dependencies:** None (standalone utility module)

---

### MOD-004: Reset Scheduler
**File:** `04-CORE-MODULES/modules/reset_scheduler.md`

**Modules:**
- `src/state/reset_scheduler.py`

**API Endpoints:**
- None (internal scheduling logic)

**Database:**
- `reset_schedule` - Last reset tracking
- `daily_pnl` - Reset daily P&L
- `trade_history` - Reset trade counts

**Tests:**
- `tests/state/test_daily_reset.py`
- `tests/state/test_reset_scheduler.py`

**Config:**
- `config/accounts.yaml` - Per-account reset times
- `config/risk_config.yaml` - Reset-related rule configs

**Dependencies:** MOD-005 (PNL Tracker), MOD-008 (Trade Counter)

---

### MOD-005: PNL Tracker
**File:** `04-CORE-MODULES/modules/pnl_tracker.md`

**Modules:**
- `src/state/pnl_tracker.py`

**API Endpoints:**
- None (calculates from events and contract metadata)

**Database:**
- `daily_pnl` - Daily realized P&L

**Tests:**
- `tests/state/test_pnl_tracking.py`
- `tests/state/test_unrealized_pnl_calc.py`

**Config:**
- None (P&L tracking is automatic)

**Dependencies:** MOD-006 (Quote Tracker), MOD-007 (Contract Cache), MOD-009 (State Manager)

---

### MOD-006: Quote Tracker
**File:** `04-CORE-MODULES/modules/quote_tracker.md`

**Modules:**
- `src/state/quote_tracker.py`

**API Endpoints:**
- SignalR Market Hub (MarketQuote events, 1-4/sec per instrument)

**Database:**
- None (in-memory only, start fresh on restart)

**Tests:**
- `tests/state/test_quote_updates.py`
- `tests/state/test_quote_staleness.py`

**Config:**
- None (quote tracking is automatic)

**Dependencies:** None (standalone real-time data module)

---

### MOD-007: Contract Cache
**File:** `04-CORE-MODULES/modules/contract_cache.md`

**Modules:**
- `src/state/contract_cache.py`

**API Endpoints:**
- `/api/Contract/searchById` - Fetch contract metadata

**Database:**
- `contract_cache` - Cached contract metadata

**Tests:**
- `tests/state/test_contract_cache.py`
- `tests/state/test_pnl_calculation.py`

**Config:**
- None (contract caching is automatic)

**Dependencies:** None (standalone metadata cache)

---

### MOD-008: Trade Counter
**File:** `04-CORE-MODULES/modules/trade_counter.md`

**Modules:**
- `src/state/trade_counter.py`

**API Endpoints:**
- None (counts from GatewayUserTrade events)

**Database:**
- `trade_history` - Trade timestamps
- `session_state` - Session start time

**Tests:**
- `tests/state/test_trade_counting.py`
- `tests/state/test_rolling_windows.py`

**Config:**
- None (trade counting is automatic)

**Dependencies:** None (standalone counter module)

---

### MOD-009: State Manager
**File:** `04-CORE-MODULES/modules/state_manager.md`

**Modules:**
- `src/state/state_manager.py`

**API Endpoints:**
- None (updates from GatewayUserPosition and GatewayUserOrder events)

**Database:**
- `positions` - Current positions
- `orders` - Current orders

**Tests:**
- `tests/state/test_position_updates.py`
- `tests/state/test_order_updates.py`
- `tests/state/test_state_queries.py`

**Config:**
- None (state tracking is automatic)

**Dependencies:** API-INT-001 (event structures)

---

## Risk Rule Specifications

### RULE-001: Max Contracts
**File:** `03-RISK-RULES/rules/01_max_contracts.md`

**Modules:**
- `src/rules/max_contracts.py`

**API Endpoints:**
- `/api/Position/searchOpen` - Query all positions (enforcement)
- `/api/Position/closeContract` - Close positions (enforcement)

**Database:**
- `positions` (via MOD-009) - Query position count
- `enforcement_log` - Log enforcement actions

**Tests:**
- `tests/rules/test_max_contracts.py`
- `tests/rules/test_net_vs_gross.py`

**Config:**
- `config/risk_config.yaml` - `rules.max_contracts.*`

**Dependencies:** MOD-001 (Enforcement), MOD-009 (State Manager)

---

### RULE-002: Max Contracts Per Instrument
**File:** `03-RISK-RULES/rules/02_max_contracts_per_instrument.md`

**Modules:**
- `src/rules/max_contracts_per_instrument.py`

**API Endpoints:**
- `/api/Position/searchOpen` - Query positions by instrument
- `/api/Position/closeContract` - Close specific positions

**Database:**
- `positions` (via MOD-009) - Query per-instrument counts
- `enforcement_log` - Log actions

**Tests:**
- `tests/rules/test_max_contracts_per_instrument.py`
- `tests/rules/test_reduce_to_limit.py`

**Config:**
- `config/risk_config.yaml` - `rules.max_contracts_per_instrument.*`

**Dependencies:** MOD-001, MOD-009

---

### RULE-003: Daily Realized Loss
**File:** `03-RISK-RULES/rules/03_daily_realized_loss.md`

**Modules:**
- `src/rules/daily_realized_loss.py`

**API Endpoints:**
- `/api/Position/searchOpen` - Query positions (enforcement)
- `/api/Position/closeContract` - Close positions (enforcement)

**Database:**
- `daily_pnl` (via MOD-005) - Query realized P&L
- `lockouts` (via MOD-002) - Set lockout
- `enforcement_log` - Log actions

**Tests:**
- `tests/rules/test_daily_realized_loss.py`
- `tests/rules/test_lockout_until_reset.py`

**Config:**
- `config/risk_config.yaml` - `rules.daily_realized_loss.*`

**Dependencies:** MOD-001, MOD-002, MOD-005

---

### RULE-004: Daily Unrealized Loss
**File:** `03-RISK-RULES/rules/04_daily_unrealized_loss.md`

**Modules:**
- `src/rules/daily_unrealized_loss.py`

**API Endpoints:**
- `/api/Position/closeContract` - Close losing positions

**Database:**
- `positions` (via MOD-009) - Query positions
- `contract_cache` (via MOD-007) - Contract metadata for P&L calc
- `enforcement_log` - Log actions

**Tests:**
- `tests/rules/test_daily_unrealized_loss.py`
- `tests/rules/test_per_position_unrealized.py`

**Config:**
- `config/risk_config.yaml` - `rules.daily_unrealized_loss.*`

**Dependencies:** MOD-001, MOD-005, MOD-006, MOD-007, MOD-009

---

### RULE-005: Max Unrealized Profit
**File:** `03-RISK-RULES/rules/05_max_unrealized_profit.md`

**Modules:**
- `src/rules/max_unrealized_profit.py`

**API Endpoints:**
- `/api/Position/closeContract` - Close profitable positions

**Database:**
- `positions` (via MOD-009) - Query positions
- `contract_cache` (via MOD-007) - Contract metadata for P&L calc
- `enforcement_log` - Log actions

**Tests:**
- `tests/rules/test_max_unrealized_profit.py`
- `tests/rules/test_profit_target_mode.py`
- `tests/rules/test_breakeven_mode.py`

**Config:**
- `config/risk_config.yaml` - `rules.max_unrealized_profit.*`

**Dependencies:** MOD-001, MOD-005, MOD-006, MOD-007, MOD-009

---

### RULE-006: Trade Frequency Limit
**File:** `03-RISK-RULES/rules/06_trade_frequency_limit.md`

**Modules:**
- `src/rules/trade_frequency_limit.py`

**API Endpoints:**
- `/api/Position/searchOpen` - Query positions (enforcement)
- `/api/Position/closeContract` - Close positions (enforcement)

**Database:**
- `trade_history` (via MOD-008) - Query trade count in window
- `lockouts` (via MOD-002) - Set lockout
- `enforcement_log` - Log actions

**Tests:**
- `tests/rules/test_trade_frequency.py`
- `tests/rules/test_rolling_windows.py`

**Config:**
- `config/risk_config.yaml` - `rules.trade_frequency_limit.*`

**Dependencies:** MOD-001, MOD-002, MOD-008

---

### RULE-007: Cooldown After Loss
**File:** `03-RISK-RULES/rules/07_cooldown_after_loss.md`

**Modules:**
- `src/rules/cooldown_after_loss.py`

**API Endpoints:**
- `/api/Position/searchOpen` - Query positions (enforcement)
- `/api/Position/closeContract` - Close positions (enforcement)

**Database:**
- `daily_pnl` (via MOD-005) - Detect losing trades
- `enforcement_log` - Log actions

**Tests:**
- `tests/rules/test_cooldown.py`
- `tests/rules/test_cooldown_expiry.py`

**Config:**
- `config/risk_config.yaml` - `rules.cooldown_after_loss.*`

**Dependencies:** MOD-001, MOD-003, MOD-005

---

### RULE-008: No Stop-Loss Grace Period
**File:** `03-RISK-RULES/rules/08_no_stop_loss_grace.md`

**Modules:**
- `src/rules/no_stop_loss_grace.py`

**API Endpoints:**
- `/api/Position/closeContract` - Close positions without stop-loss

**Database:**
- `positions` (via MOD-009) - Query positions
- `orders` (via MOD-009) - Check for stop-loss orders
- `enforcement_log` - Log actions

**Tests:**
- `tests/rules/test_stop_loss_grace.py`
- `tests/rules/test_grace_period_expiry.py`

**Config:**
- `config/risk_config.yaml` - `rules.no_stop_loss_grace.*`

**Dependencies:** MOD-001, MOD-003, MOD-009

---

### RULE-009: Session Block Outside Hours
**File:** `03-RISK-RULES/rules/09_session_block_outside.md`

**Modules:**
- `src/rules/session_block_outside.py`

**API Endpoints:**
- `/api/Order/cancel` - Cancel orders outside session

**Database:**
- `orders` (via MOD-009) - Query active orders
- `enforcement_log` - Log actions

**Tests:**
- `tests/rules/test_session_hours.py`
- `tests/rules/test_timezone_handling.py`

**Config:**
- `config/risk_config.yaml` - `rules.session_block_outside.*`

**Dependencies:** MOD-001, MOD-009

---

### RULE-010: Auth Loss Guard
**File:** `03-RISK-RULES/rules/10_auth_loss_guard.md`

**Modules:**
- `src/rules/auth_loss_guard.py`

**API Endpoints:**
- `/api/Position/searchOpen` - Query positions (enforcement)
- `/api/Position/closeContract` - Close positions (enforcement)

**Database:**
- `lockouts` (via MOD-002) - Set permanent lockout
- `enforcement_log` - Log critical auth bypass

**Tests:**
- `tests/rules/test_auth_bypass_detection.py`

**Config:**
- `config/risk_config.yaml` - `rules.auth_loss_guard.*`

**Dependencies:** MOD-001, MOD-002

---

### RULE-011: Symbol Blocks
**File:** `03-RISK-RULES/rules/11_symbol_blocks.md`

**Modules:**
- `src/rules/symbol_blocks.py`

**API Endpoints:**
- `/api/Order/cancel` - Cancel orders in blocked symbols
- `/api/Position/closeContract` - Close positions in blocked symbols

**Database:**
- `orders` (via MOD-009) - Query orders by symbol
- `positions` (via MOD-009) - Query positions by symbol
- `enforcement_log` - Log actions

**Tests:**
- `tests/rules/test_symbol_blocks.py`
- `tests/rules/test_block_existing_positions.py`

**Config:**
- `config/risk_config.yaml` - `rules.symbol_blocks.*`

**Dependencies:** MOD-001, MOD-009

---

### RULE-012: Trade Management
**File:** `03-RISK-RULES/rules/12_trade_management.md`

**Modules:**
- `src/rules/trade_management.py`

**API Endpoints:**
- `/api/Order/place` - Place automatic stop-loss orders

**Database:**
- `positions` (via MOD-009) - Query positions
- `orders` (via MOD-009) - Check for existing stop-loss
- `contract_cache` (via MOD-007) - Contract metadata for tick calculations
- `enforcement_log` - Log auto stop-loss placements

**Tests:**
- `tests/rules/test_auto_stop_loss.py`
- `tests/rules/test_tick_calculations.py`

**Config:**
- `config/risk_config.yaml` - `rules.trade_management.*`

**Dependencies:** MOD-001, MOD-007, MOD-009

---

## Data Model Specifications

### DB-SCHEMA-001: Database Schema
**File:** `07-DATA-MODELS/DATABASE_SCHEMA.md`

**Modules:**
- `src/database/init_schema.py` - Schema creation
- `src/database/migrations.py` - Schema versioning
- ALL module persistence code

**API Endpoints:**
- None (internal database schema)

**Database:**
- ALL 9 tables:
  - `lockouts`
  - `daily_pnl`
  - `contract_cache`
  - `trade_history`
  - `session_state`
  - `positions`
  - `orders`
  - `enforcement_log`
  - `reset_schedule`

**Tests:**
- `tests/database/test_schema_creation.py`
- `tests/database/test_indexes.py`
- `tests/database/test_cleanup_jobs.py`

**Config:**
- None (schema is code-defined)

**Dependencies:** All MOD-* specs (each module has persistence requirements)

---

### STATE-OBJECTS-001: State Objects
**File:** `07-DATA-MODELS/STATE_OBJECTS.md`

**Modules:**
- `src/data_models/position.py`
- `src/data_models/order.py`
- `src/data_models/trade.py`
- `src/data_models/quote.py`
- `src/data_models/contract_metadata.py`
- `src/data_models/lockout.py`
- `src/data_models/enforcement.py`
- `src/data_models/timer.py`
- `src/data_models/daily_pnl.py`
- `src/data_models/config.py`

**API Endpoints:**
- None (internal data structures)

**Database:**
- ALL 9 tables (dataclasses map to database rows)

**Tests:**
- `tests/data_models/test_dataclasses.py`
- `tests/data_models/test_serialization.py`

**Config:**
- None (data model definitions)

**Dependencies:** None (foundational data structures)

---

## API Integration Specifications

### API-INT-001: TopstepX Integration
**File:** `01-EXTERNAL-API/api/topstepx_integration.md`

**Modules:**
- `src/api/auth.py` - Authentication
- `src/api/rest_client.py` - REST API wrapper
- `src/api/signalr_listener.py` - User Hub listener
- `src/api/market_hub.py` - Market Hub listener

**API Endpoints:**
- ALL TopstepX REST endpoints (24 documented)
- SignalR User Hub (4 event types)
- SignalR Market Hub (MarketQuote)

**Database:**
- None (API integration layer)

**Tests:**
- `tests/api/test_authentication.py`
- `tests/api/test_rest_client.py`
- `tests/api/test_signalr_connection.py`

**Config:**
- `config/accounts.yaml` - API keys and credentials

**Dependencies:** None (external integration layer)

---

## Frontend Specifications

### CLI-ADMIN-001: Admin CLI
**File:** `06-CLI-FRONTEND/ADMIN_CLI_SPEC.md`

**Modules:**
- `src/cli/admin/admin_main.py` - Main CLI
- `src/cli/admin/ui_components.py` - UI utilities
- `src/cli/admin/service_control.py` - Service management

**API Endpoints:**
- `/api/Auth/validate` - Test connection
- `/api/Auth/apiKey` - Authenticate accounts

**Database:**
- `data/state.db` - Read-only queries for status display
- `enforcement_log` - View recent enforcements
- `lockouts` - View lockouts

**Tests:**
- `tests/cli/test_admin_authentication.py`
- `tests/cli/test_service_control.py`

**Config:**
- `config/admin_password.hash` - Admin authentication
- `config/accounts.yaml` - Account management
- `config/risk_config.yaml` - Rule configuration

**Dependencies:** DAEMON-001 (service control), all CONFIG specs

---

### CLI-TRADER-001: Trader CLI
**File:** `06-CLI-FRONTEND/TRADER_CLI_SPEC.md`

**Modules:**
- `src/cli/trader/trader_main.py` - Main dashboard
- `src/cli/trader/websocket_client.py` - WebSocket client
- `src/cli/trader/ui_components.py` - UI rendering

**API Endpoints:**
- WebSocket `ws://localhost:8765` - Real-time events from daemon

**Database:**
- `data/state.db` - Read-only queries for initial state
- `positions` - Position display
- `orders` - Order display
- `daily_pnl` - P&L display
- `lockouts` - Lockout status
- `enforcement_log` - Recent actions

**Tests:**
- `tests/cli/test_websocket_client.py`
- `tests/cli/test_trader_ui.py`

**Config:**
- None (read-only dashboard, no configuration)

**Dependencies:** ENDPOINT-001 (WebSocket protocol), DB-SCHEMA-001

---

### ENDPOINT-001: Daemon WebSocket API
**File:** `05-INTERNAL-API/DAEMON_ENDPOINTS.md`

**Modules:**
- `src/core/websocket_server.py` - Server implementation
- `src/cli/trader/websocket_client.py` - Client implementation

**API Endpoints:**
- WebSocket `ws://localhost:8765` - Broadcast endpoint

**Database:**
- None (real-time broadcasting only)

**Tests:**
- `tests/websocket/test_server.py`
- `tests/websocket/test_client.py`
- `tests/websocket/test_event_broadcasting.py`

**Config:**
- None (localhost-only WebSocket)

**Dependencies:** PIPE-001 (event types), CLI-TRADER-001 (client)

---

## Configuration Specifications

### CONFIG-001: accounts.yaml
**File:** `08-CONFIGURATION/ACCOUNTS_YAML_SPEC.md`

**Modules:**
- `src/config/loader.py` - Configuration loader
- `src/api/auth.py` - Uses credentials for authentication

**API Endpoints:**
- `/api/Auth/apiKey` - Authentication endpoint

**Database:**
- None (configuration file)

**Tests:**
- `tests/config/test_accounts_loading.py`
- `tests/config/test_account_validation.py`

**Config:**
- `config/accounts.yaml` - THE configuration file

**Dependencies:** None (foundational configuration)

---

### CONFIG-002: risk_config.yaml
**File:** `08-CONFIGURATION/RISK_CONFIG_YAML_SPEC.md`

**Modules:**
- `src/config/loader.py` - Configuration loader
- ALL 12 rule files (use rule-specific configs)

**API Endpoints:**
- None (configuration file)

**Database:**
- None (configuration file)

**Tests:**
- `tests/config/test_risk_config_loading.py`
- `tests/config/test_rule_validation.py`

**Config:**
- `config/risk_config.yaml` - THE configuration file

**Dependencies:** RULE-001 through RULE-012 (each rule reads its section)

---

### CONFIG-003: LOGGING_CONFIG
**File:** `08-CONFIGURATION/LOGGING_CONFIG_SPEC.md`

**Modules:**
- `src/config/logging_setup.py` - Logging configuration
- ALL modules (use configured loggers)

**API Endpoints:**
- None (logging configuration)

**Database:**
- None (writes to log files)

**Tests:**
- `tests/config/test_logging_setup.py`
- `tests/config/test_log_rotation.py`

**Config:**
- `config/logging.yaml` - Logging configuration

**Dependencies:** None (cross-cutting concern)

---

### CONFIG-004: ADMIN_PASSWORD
**File:** `08-CONFIGURATION/ADMIN_PASSWORD_SPEC.md`

**Modules:**
- `src/cli/admin/admin_main.py` - Password authentication
- `src/cli/admin/setup_password.py` - Initial password setup

**API Endpoints:**
- None (local authentication)

**Database:**
- None (password hash file)

**Tests:**
- `tests/cli/test_admin_auth.py`
- `tests/cli/test_password_hashing.py`

**Config:**
- `config/admin_password.hash` - Bcrypt hash file

**Dependencies:** None (admin authentication)

---

## Summary Statistics

**Total Specifications:** 57 files
- **Core Architecture:** 4 specs
- **Modules:** 9 specs
- **Risk Rules:** 12 specs
- **Data Models:** 2 specs
- **API Integration:** 25 specs (1 main + 24 endpoint refs)
- **Frontend:** 3 specs
- **Configuration:** 4 specs

**Total Modules:** ~50 source files
**Total Tests:** ~80 test files
**Total Config Files:** 4 YAML files
**Total Database Tables:** 9 tables
**Total API Endpoints:** 28+ (REST + SignalR)

---

**Next Document:** REVERSE_ATTACHMENT_MAP.md (Attachment → Specs reverse lookup)
