# Reverse Attachment Map

**Generated:** 2025-10-22
**Purpose:** Reverse lookup from implementation components to specifications
**Format:** Attachment → Specs (Which specs describe/use this component)

---

## How to Use This Document

For each implementation component (module, endpoint, table, test, config), this document lists which specifications reference it.

**Use Cases:**
- "I need to modify `src/state/lockout_manager.py` - which specs do I need to review?"
- "This database table needs a new column - which specs are affected?"
- "I'm working on endpoint `/api/Position/closeContract` - what rules use this?"

---

## Source Modules → Specifications

### Core Daemon

#### `src/core/daemon.py`
**Referenced by:**
- ARCH-V2.2 - System Architecture
- DAEMON-001 - Main daemon implementation (29-step startup, 6 threads)

#### `src/core/event_router.py`
**Referenced by:**
- ARCH-V2.2 - Event routing architecture
- DAEMON-001 - Event dispatch
- PIPE-001 - Event pipeline (<10ms processing)

#### `src/core/websocket_server.py`
**Referenced by:**
- ARCH-V2.2 - WebSocket architecture
- DAEMON-001 - Thread 6 (WebSocket server)
- ENDPOINT-001 - Server-side WebSocket implementation

#### `src/service/windows_service.py`
**Referenced by:**
- ARCH-V2.2 - Service architecture
- DAEMON-001 - Windows Service wrapper (SvcRun, SvcStop)

#### `src/service/installer.py`
**Referenced by:**
- ARCH-V2.2 - Installation logic
- DAEMON-001 - Service installation

---

### State Management

#### `src/state/lockout_manager.py`
**Referenced by:**
- MOD-002 - Lockout Manager specification
- STATE-001 - Critical state (must persist)
- RULE-003 - Daily Realized Loss (sets lockouts)
- RULE-006 - Trade Frequency (sets lockouts)
- RULE-010 - Auth Loss Guard (sets permanent lockouts)

#### `src/state/timer_manager.py`
**Referenced by:**
- MOD-003 - Timer Manager specification
- STATE-001 - Ephemeral state (no persistence)
- RULE-007 - Cooldown After Loss (cooldown timers)
- RULE-008 - No Stop-Loss Grace (grace period timers)

#### `src/state/reset_scheduler.py`
**Referenced by:**
- MOD-004 - Reset Scheduler specification
- DAEMON-001 - Thread 3 (daily reset checker)
- STATE-001 - Daily reset logic

#### `src/state/pnl_tracker.py`
**Referenced by:**
- MOD-005 - PNL Tracker specification
- STATE-001 - Critical state (must persist)
- RULE-003 - Daily Realized Loss (checks realized P&L)
- RULE-004 - Daily Unrealized Loss (calculates unrealized P&L)
- RULE-005 - Max Unrealized Profit (calculates unrealized P&L)
- RULE-007 - Cooldown After Loss (detects losing trades)

#### `src/state/quote_tracker.py`
**Referenced by:**
- MOD-006 - Quote Tracker specification
- STATE-001 - Ephemeral state (no persistence)
- RULE-004 - Daily Unrealized Loss (uses current quotes)
- RULE-005 - Max Unrealized Profit (uses current quotes)

#### `src/state/contract_cache.py`
**Referenced by:**
- MOD-007 - Contract Cache specification
- STATE-001 - Cached state (persist for performance)
- RULE-004 - Daily Unrealized Loss (uses tick size/value)
- RULE-005 - Max Unrealized Profit (uses tick size/value)
- RULE-012 - Trade Management (uses tick size for stop-loss calculation)

#### `src/state/trade_counter.py`
**Referenced by:**
- MOD-008 - Trade Counter specification
- STATE-001 - Recent history (rolling window)
- RULE-006 - Trade Frequency Limit (counts trades in window)

#### `src/state/state_manager.py`
**Referenced by:**
- MOD-009 - State Manager specification
- STATE-001 - Core state management
- RULE-001 - Max Contracts (queries position count)
- RULE-002 - Max Contracts Per Instrument (queries positions by symbol)
- RULE-004 - Daily Unrealized Loss (queries positions)
- RULE-005 - Max Unrealized Profit (queries positions)
- RULE-008 - No Stop-Loss Grace (queries positions and orders)
- RULE-009 - Session Block Outside Hours (queries orders)
- RULE-011 - Symbol Blocks (queries positions and orders)
- RULE-012 - Trade Management (queries positions and orders)

---

### Enforcement

#### `src/enforcement/actions.py`
**Referenced by:**
- MOD-001 - Enforcement Actions specification
- RULE-001 through RULE-012 - ALL rules (enforcement execution)

---

### Risk Rules

#### `src/rules/max_contracts.py`
**Referenced by:**
- RULE-001 - Max Contracts specification

#### `src/rules/max_contracts_per_instrument.py`
**Referenced by:**
- RULE-002 - Max Contracts Per Instrument specification

#### `src/rules/daily_realized_loss.py`
**Referenced by:**
- RULE-003 - Daily Realized Loss specification

#### `src/rules/daily_unrealized_loss.py`
**Referenced by:**
- RULE-004 - Daily Unrealized Loss specification

#### `src/rules/max_unrealized_profit.py`
**Referenced by:**
- RULE-005 - Max Unrealized Profit specification

#### `src/rules/trade_frequency_limit.py`
**Referenced by:**
- RULE-006 - Trade Frequency Limit specification

#### `src/rules/cooldown_after_loss.py`
**Referenced by:**
- RULE-007 - Cooldown After Loss specification

#### `src/rules/no_stop_loss_grace.py`
**Referenced by:**
- RULE-008 - No Stop-Loss Grace Period specification

#### `src/rules/session_block_outside.py`
**Referenced by:**
- RULE-009 - Session Block Outside Hours specification

#### `src/rules/auth_loss_guard.py`
**Referenced by:**
- RULE-010 - Auth Loss Guard specification

#### `src/rules/symbol_blocks.py`
**Referenced by:**
- RULE-011 - Symbol Blocks specification

#### `src/rules/trade_management.py`
**Referenced by:**
- RULE-012 - Trade Management specification

---

### API Integration

#### `src/api/auth.py`
**Referenced by:**
- API-INT-001 - Authentication implementation
- DAEMON-001 - Token refresh (Thread 5)
- CONFIG-001 - Uses accounts.yaml credentials

#### `src/api/rest_client.py`
**Referenced by:**
- API-INT-001 - REST API wrapper
- MOD-001 - Enforcement Actions (API calls)

#### `src/api/signalr_listener.py`
**Referenced by:**
- API-INT-001 - User Hub listener
- DAEMON-001 - Main event loop (Thread 1)
- PIPE-001 - SignalR event handlers

#### `src/api/market_hub.py`
**Referenced by:**
- API-INT-001 - Market Hub listener
- DAEMON-001 - Quote subscriptions (Thread 1)
- MOD-006 - Quote Tracker (receives MarketQuote events)

---

### CLI (Admin)

#### `src/cli/admin/admin_main.py`
**Referenced by:**
- CLI-ADMIN-001 - Main CLI specification
- CONFIG-004 - Admin password authentication

#### `src/cli/admin/ui_components.py`
**Referenced by:**
- CLI-ADMIN-001 - UI utilities (colors, boxes, animations)

#### `src/cli/admin/service_control.py`
**Referenced by:**
- CLI-ADMIN-001 - Service management (start/stop/restart)
- DAEMON-001 - Service control interface

---

### CLI (Trader)

#### `src/cli/trader/trader_main.py`
**Referenced by:**
- CLI-TRADER-001 - Main dashboard specification

#### `src/cli/trader/websocket_client.py`
**Referenced by:**
- CLI-TRADER-001 - WebSocket client
- ENDPOINT-001 - Client-side WebSocket implementation

#### `src/cli/trader/ui_components.py`
**Referenced by:**
- CLI-TRADER-001 - Dashboard rendering utilities

---

### Configuration

#### `src/config/loader.py`
**Referenced by:**
- CONFIG-001 - accounts.yaml loader
- CONFIG-002 - risk_config.yaml loader
- CONFIG-003 - logging.yaml loader
- DAEMON-001 - Configuration loading (startup Steps 1-3)

#### `src/config/logging_setup.py`
**Referenced by:**
- CONFIG-003 - LOGGING_CONFIG specification
- DAEMON-001 - Logging initialization

---

### Database

#### `src/database/init_schema.py`
**Referenced by:**
- DB-SCHEMA-001 - Schema creation
- DAEMON-001 - Database initialization (startup Steps 4-6)

#### `src/database/migrations.py`
**Referenced by:**
- DB-SCHEMA-001 - Schema versioning
- DAEMON-001 - Migration execution (startup Step 6)

---

### Data Models

#### `src/data_models/*.py` (all dataclasses)
**Referenced by:**
- STATE-OBJECTS-001 - State object definitions
- DB-SCHEMA-001 - Database row mapping
- ALL module specs (use dataclasses for type safety)

---

## API Endpoints → Specifications

### Authentication

#### `/api/Auth/apiKey`
**Used by:**
- API-INT-001 - Authentication endpoint
- CLI-ADMIN-001 - Account authentication
- CONFIG-001 - Credential validation
- DAEMON-001 - Startup authentication (Step 16)

#### `/api/Auth/validate`
**Used by:**
- API-INT-001 - Token validation endpoint
- CLI-ADMIN-001 - Connection test
- DAEMON-001 - Token refresh (Thread 5, Step 17)

---

### Position Management

#### `/api/Position/searchOpen`
**Used by:**
- API-INT-001 - Query open positions
- RULE-001 - Max Contracts (query all positions)
- RULE-002 - Max Contracts Per Instrument (query positions by symbol)
- RULE-003 - Daily Realized Loss (enforcement: query positions)
- RULE-006 - Trade Frequency (enforcement: query positions)
- RULE-010 - Auth Loss Guard (enforcement: query positions)

#### `/api/Position/closeContract`
**Used by:**
- API-INT-001 - Close position endpoint
- MOD-001 - Enforcement Actions (CLOSE_POSITION)
- RULE-001 - Max Contracts (close excess positions)
- RULE-002 - Max Contracts Per Instrument (close excess positions)
- RULE-003 - Daily Realized Loss (close all positions)
- RULE-004 - Daily Unrealized Loss (close losing positions)
- RULE-005 - Max Unrealized Profit (close profitable positions)
- RULE-006 - Trade Frequency (close all positions)
- RULE-007 - Cooldown After Loss (close all positions)
- RULE-008 - No Stop-Loss Grace (close positions without stop-loss)
- RULE-010 - Auth Loss Guard (close all positions)
- RULE-011 - Symbol Blocks (close positions in blocked symbols)

---

### Order Management

#### `/api/Order/cancel`
**Used by:**
- API-INT-001 - Cancel order endpoint
- MOD-001 - Enforcement Actions (CANCEL_ORDER)
- RULE-009 - Session Block Outside Hours (cancel orders outside hours)
- RULE-011 - Symbol Blocks (cancel orders in blocked symbols)

#### `/api/Order/place`
**Used by:**
- API-INT-001 - Place order endpoint
- MOD-001 - Enforcement Actions (place stop-loss)
- RULE-012 - Trade Management (auto-place stop-loss orders)

---

### Contract Metadata

#### `/api/Contract/searchById`
**Used by:**
- API-INT-001 - Contract lookup endpoint
- MOD-007 - Contract Cache (fetch missing contracts)

---

### SignalR Events

#### SignalR User Hub: `GatewayUserTrade`
**Used by:**
- API-INT-001 - Trade event
- PIPE-001 - Route to MOD-005 (PNL Tracker), MOD-008 (Trade Counter)
- MOD-005 - Update realized P&L
- MOD-008 - Increment trade count
- RULE-003 - Daily Realized Loss (trigger on P&L update)
- RULE-006 - Trade Frequency (trigger on trade count update)
- RULE-007 - Cooldown After Loss (trigger on losing trade)

#### SignalR User Hub: `GatewayUserPosition`
**Used by:**
- API-INT-001 - Position event
- PIPE-001 - Route to MOD-009 (State Manager)
- MOD-009 - Update position state
- RULE-001 - Max Contracts (trigger on position change)
- RULE-002 - Max Contracts Per Instrument (trigger on position change)
- RULE-004 - Daily Unrealized Loss (trigger on position change)
- RULE-005 - Max Unrealized Profit (trigger on position change)
- RULE-008 - No Stop-Loss Grace (trigger on new position)

#### SignalR User Hub: `GatewayUserOrder`
**Used by:**
- API-INT-001 - Order event
- PIPE-001 - Route to MOD-009 (State Manager)
- MOD-009 - Update order state
- RULE-008 - No Stop-Loss Grace (check for stop-loss orders)
- RULE-009 - Session Block Outside Hours (trigger on new order)
- RULE-011 - Symbol Blocks (trigger on new order)

#### SignalR User Hub: `GatewayUserAccount`
**Used by:**
- API-INT-001 - Account event
- PIPE-001 - Route to state updates (balance, account status)

#### SignalR Market Hub: `MarketQuote`
**Used by:**
- API-INT-001 - Quote event
- PIPE-001 - Route to MOD-006 (Quote Tracker)
- MOD-006 - Update current quotes
- RULE-004 - Daily Unrealized Loss (trigger on quote change)
- RULE-005 - Max Unrealized Profit (trigger on quote change)

---

### WebSocket (Internal)

#### `ws://localhost:8765`
**Used by:**
- ENDPOINT-001 - Daemon WebSocket server
- CLI-TRADER-001 - Trader CLI client
- DAEMON-001 - Thread 6 (WebSocket server)

---

## Database Tables → Specifications

### `lockouts`
**Used by:**
- DB-SCHEMA-001 - Table definition
- MOD-002 - Lockout Manager (reads/writes)
- STATE-001 - Critical state (must persist)
- RULE-003 - Daily Realized Loss (sets lockouts)
- RULE-006 - Trade Frequency (sets lockouts)
- RULE-010 - Auth Loss Guard (sets lockouts)
- CLI-ADMIN-001 - View lockouts
- CLI-TRADER-001 - Display lockout status

---

### `daily_pnl`
**Used by:**
- DB-SCHEMA-001 - Table definition
- MOD-005 - PNL Tracker (reads/writes)
- STATE-001 - Critical state (must persist)
- RULE-003 - Daily Realized Loss (reads realized P&L)
- RULE-007 - Cooldown After Loss (detects losing trades)
- MOD-004 - Reset Scheduler (resets daily P&L)
- CLI-ADMIN-001 - View P&L
- CLI-TRADER-001 - Display P&L

---

### `contract_cache`
**Used by:**
- DB-SCHEMA-001 - Table definition
- MOD-007 - Contract Cache (reads/writes)
- STATE-001 - Cached state (persist for performance)
- RULE-004 - Daily Unrealized Loss (uses tick size/value)
- RULE-005 - Max Unrealized Profit (uses tick size/value)
- RULE-012 - Trade Management (uses tick size)

---

### `trade_history`
**Used by:**
- DB-SCHEMA-001 - Table definition
- MOD-008 - Trade Counter (reads/writes)
- STATE-001 - Recent history (rolling window)
- RULE-006 - Trade Frequency (counts trades in window)
- MOD-004 - Reset Scheduler (resets trade counts)

---

### `session_state`
**Used by:**
- DB-SCHEMA-001 - Table definition
- MOD-008 - Trade Counter (session start time)
- STATE-001 - Session tracking

---

### `positions`
**Used by:**
- DB-SCHEMA-001 - Table definition
- MOD-009 - State Manager (reads/writes)
- STATE-001 - Core state (batched writes)
- RULE-001 - Max Contracts (reads position count)
- RULE-002 - Max Contracts Per Instrument (reads positions by symbol)
- RULE-004 - Daily Unrealized Loss (reads positions)
- RULE-005 - Max Unrealized Profit (reads positions)
- RULE-008 - No Stop-Loss Grace (reads positions)
- RULE-011 - Symbol Blocks (reads positions by symbol)
- RULE-012 - Trade Management (reads positions)
- CLI-ADMIN-001 - View positions
- CLI-TRADER-001 - Display positions

---

### `orders`
**Used by:**
- DB-SCHEMA-001 - Table definition
- MOD-009 - State Manager (reads/writes)
- STATE-001 - Core state (batched writes)
- RULE-008 - No Stop-Loss Grace (checks for stop-loss orders)
- RULE-009 - Session Block Outside Hours (reads orders)
- RULE-011 - Symbol Blocks (reads orders by symbol)
- RULE-012 - Trade Management (checks for existing stop-loss)
- CLI-ADMIN-001 - View orders
- CLI-TRADER-001 - Display orders

---

### `enforcement_log`
**Used by:**
- DB-SCHEMA-001 - Table definition
- MOD-001 - Enforcement Actions (writes audit trail)
- STATE-001 - Append-only log (batched writes)
- RULE-001 through RULE-012 - ALL rules (log enforcement actions)
- CLI-ADMIN-001 - View enforcement history
- CLI-TRADER-001 - Display recent enforcements

---

### `reset_schedule`
**Used by:**
- DB-SCHEMA-001 - Table definition
- MOD-004 - Reset Scheduler (reads/writes)
- STATE-001 - Reset tracking
- DAEMON-001 - Thread 3 (daily reset checker)

---

## Configuration Files → Specifications

### `config/accounts.yaml`
**Referenced by:**
- CONFIG-001 - accounts.yaml specification
- DAEMON-001 - Load accounts (Step 1)
- CLI-ADMIN-001 - Account management UI
- API-INT-001 - Authentication credentials

---

### `config/risk_config.yaml`
**Referenced by:**
- CONFIG-002 - risk_config.yaml specification
- DAEMON-001 - Load rule config (Step 2)
- RULE-001 through RULE-012 - ALL rules (read rule-specific config)
- CLI-ADMIN-001 - Rule configuration UI

---

### `config/logging.yaml`
**Referenced by:**
- CONFIG-003 - LOGGING_CONFIG specification
- DAEMON-001 - Logging setup
- ALL modules - Use configured loggers

---

### `config/admin_password.hash`
**Referenced by:**
- CONFIG-004 - ADMIN_PASSWORD specification
- CLI-ADMIN-001 - Admin authentication

---

## Test Files → Specifications

### Core Tests

#### `tests/core/test_daemon_startup.py`
**Tests:**
- ARCH-V2.2 - System startup
- DAEMON-001 - 29-step startup sequence

#### `tests/core/test_daemon_shutdown.py`
**Tests:**
- ARCH-V2.2 - System shutdown
- DAEMON-001 - Graceful shutdown sequence

#### `tests/core/test_threading_model.py`
**Tests:**
- DAEMON-001 - 6-thread model

#### `tests/core/test_event_router.py`
**Tests:**
- ARCH-V2.2 - Event routing
- PIPE-001 - Event pipeline

#### `tests/core/test_crash_recovery.py`
**Tests:**
- DAEMON-001 - Emergency shutdown and recovery
- STATE-001 - State persistence

---

### State Tests

#### `tests/state/test_lockout_*.py`
**Tests:**
- MOD-002 - Lockout Manager
- RULE-003 - Daily Realized Loss (lockout behavior)
- RULE-006 - Trade Frequency (lockout behavior)
- RULE-010 - Auth Loss Guard (lockout behavior)

#### `tests/state/test_pnl_*.py`
**Tests:**
- MOD-005 - PNL Tracker
- RULE-003 - Daily Realized Loss
- RULE-004 - Daily Unrealized Loss
- RULE-005 - Max Unrealized Profit

#### `tests/state/test_timer_*.py`
**Tests:**
- MOD-003 - Timer Manager
- RULE-007 - Cooldown After Loss
- RULE-008 - No Stop-Loss Grace

#### `tests/state/test_quote_*.py`
**Tests:**
- MOD-006 - Quote Tracker

#### `tests/state/test_contract_cache.py`
**Tests:**
- MOD-007 - Contract Cache

#### `tests/state/test_trade_counting.py`
**Tests:**
- MOD-008 - Trade Counter
- RULE-006 - Trade Frequency

#### `tests/state/test_position_*.py`
**Tests:**
- MOD-009 - State Manager (positions)

#### `tests/state/test_order_*.py`
**Tests:**
- MOD-009 - State Manager (orders)

---

### Rule Tests

#### `tests/rules/test_max_contracts.py`
**Tests:**
- RULE-001 - Max Contracts

#### `tests/rules/test_max_contracts_per_instrument.py`
**Tests:**
- RULE-002 - Max Contracts Per Instrument

#### `tests/rules/test_daily_realized_loss.py`
**Tests:**
- RULE-003 - Daily Realized Loss

#### `tests/rules/test_daily_unrealized_loss.py`
**Tests:**
- RULE-004 - Daily Unrealized Loss

#### `tests/rules/test_max_unrealized_profit.py`
**Tests:**
- RULE-005 - Max Unrealized Profit

#### `tests/rules/test_trade_frequency.py`
**Tests:**
- RULE-006 - Trade Frequency Limit

#### `tests/rules/test_cooldown.py`
**Tests:**
- RULE-007 - Cooldown After Loss

#### `tests/rules/test_stop_loss_grace.py`
**Tests:**
- RULE-008 - No Stop-Loss Grace

#### `tests/rules/test_session_hours.py`
**Tests:**
- RULE-009 - Session Block Outside Hours

#### `tests/rules/test_auth_bypass_detection.py`
**Tests:**
- RULE-010 - Auth Loss Guard

#### `tests/rules/test_symbol_blocks.py`
**Tests:**
- RULE-011 - Symbol Blocks

#### `tests/rules/test_auto_stop_loss.py`
**Tests:**
- RULE-012 - Trade Management

---

### API Tests

#### `tests/api/test_authentication.py`
**Tests:**
- API-INT-001 - Authentication flow

#### `tests/api/test_rest_client.py`
**Tests:**
- API-INT-001 - REST API wrapper

#### `tests/api/test_signalr_connection.py`
**Tests:**
- API-INT-001 - SignalR connections

---

### CLI Tests

#### `tests/cli/test_admin_*.py`
**Tests:**
- CLI-ADMIN-001 - Admin CLI

#### `tests/cli/test_trader_*.py`
**Tests:**
- CLI-TRADER-001 - Trader CLI

#### `tests/cli/test_websocket_client.py`
**Tests:**
- CLI-TRADER-001 - WebSocket client
- ENDPOINT-001 - Client-side WebSocket

---

### WebSocket Tests

#### `tests/websocket/test_server.py`
**Tests:**
- ENDPOINT-001 - WebSocket server

#### `tests/websocket/test_client.py`
**Tests:**
- ENDPOINT-001 - WebSocket client

#### `tests/websocket/test_event_broadcasting.py`
**Tests:**
- ENDPOINT-001 - Event broadcasting

---

### Database Tests

#### `tests/database/test_schema_creation.py`
**Tests:**
- DB-SCHEMA-001 - Schema creation

#### `tests/database/test_indexes.py`
**Tests:**
- DB-SCHEMA-001 - Index performance

#### `tests/database/test_cleanup_jobs.py`
**Tests:**
- DB-SCHEMA-001 - Maintenance jobs

---

### Configuration Tests

#### `tests/config/test_accounts_loading.py`
**Tests:**
- CONFIG-001 - accounts.yaml loading

#### `tests/config/test_risk_config_loading.py`
**Tests:**
- CONFIG-002 - risk_config.yaml loading

#### `tests/config/test_logging_setup.py`
**Tests:**
- CONFIG-003 - logging configuration

#### `tests/config/test_admin_auth.py`
**Tests:**
- CONFIG-004 - admin password authentication

---

## Summary Statistics

**Total Source Modules:** ~50 Python files
- Core: 5 files
- State: 8 files
- Rules: 12 files
- Enforcement: 1 file
- API: 4 files
- CLI: 6 files
- Config: 2 files
- Database: 2 files
- Data Models: 10+ files

**Total API Endpoints:** 28+
- REST: 24 endpoints
- SignalR: 4 event types (User Hub) + 1 event type (Market Hub)
- WebSocket: 1 internal endpoint

**Total Database Tables:** 9 tables
- Critical state: 2 tables (lockouts, daily_pnl)
- Cached state: 1 table (contract_cache)
- Recent history: 2 tables (trade_history, session_state)
- Core state: 2 tables (positions, orders)
- Audit: 1 table (enforcement_log)
- Scheduling: 1 table (reset_schedule)

**Total Configuration Files:** 4 YAML/hash files
- accounts.yaml
- risk_config.yaml
- logging.yaml
- admin_password.hash

**Total Test Files:** ~80 test files
- Core: 5 test files
- State: 15 test files
- Rules: 12 test files
- API: 3 test files
- CLI: 5 test files
- WebSocket: 3 test files
- Database: 3 test files
- Config: 4 test files
- Integration: 10+ test files
- Performance: 5+ test files
- End-to-End: 5+ test files

---

**Companion Document:** ATTACHMENT_MAP.md (Forward lookup: Spec → Attachments)
