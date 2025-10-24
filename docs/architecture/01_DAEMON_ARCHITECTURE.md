# Daemon Architecture Analysis

**Document ID:** ARCH-ANALYSIS-001
**Version:** 1.0
**Date:** 2025-10-23
**Agent:** DAEMON ARCHITECTURE ANALYZER

---

## Overview

The Risk Manager Daemon is a **Windows Service** that runs continuously (24/7) to monitor all configured trading accounts and enforce risk rules in real-time. It is a Python-based application with a hybrid architecture supporting both Windows Service mode (production) and console mode (development).

### Key Characteristics

- **Multi-Account Monitoring:** One daemon monitors ALL accounts (not one per account)
- **Windows Service:** Auto-start on boot, admin-only control
- **Event-Driven:** Processes TopstepX SignalR events in real-time (< 10ms latency)
- **Fault-Tolerant:** Crash recovery via SQLite state persistence
- **Real-Time Broadcasting:** WebSocket server for live updates to Trader CLIs
- **Admin-Controlled:** Traders cannot stop daemon or bypass rules

---

## Entry Point

### Main Entry Point
**File:** `src/core/daemon.py`
**Class:** `RiskManagerDaemon`

**Primary Functions:**
```python
def __init__(self):
    # Initialize all module references

def start(self):
    # Execute 29-step startup sequence

def run(self):
    # Main event loop - blocks on SignalR

def shutdown(self):
    # Graceful shutdown sequence

def emergency_shutdown(self):
    # Crash recovery - save critical state
```

### Development Mode Entry
```bash
python src/core/daemon.py --dev-mode
```
- Runs as console application (foreground)
- Logs to console instead of file
- No admin privileges required
- Ideal for testing and development

### Production Mode Entry
**File:** `src/service/windows_service.py`
**Class:** `RiskManagerService(win32serviceutil.ServiceFramework)`

**Installation:**
```bash
# Install as Windows Service (requires admin)
python src/service/windows_service.py install

# Start service
net start RiskManagerDaemon
```

---

## Components Inside Daemon

The daemon consists of **13 core components** organized into distinct layers:

### Layer 1: API Communication

#### 1. SignalR User Hub (`src/api/signalr_listener.py`)
**Purpose:** Receive real-time trading events from TopstepX
- **Connection:** `wss://rtc.topstepx.com/hubs/user`
- **Events Handled:**
  - `GatewayUserTrade` - Trade executions (P&L updates)
  - `GatewayUserPosition` - Position changes
  - `GatewayUserOrder` - Order updates
  - `GatewayUserAccount` - Account state changes
- **Auto-Reconnect:** 5 attempts with exponential backoff
- **Thread:** Main thread (blocks on event loop)

#### 2. SignalR Market Hub (`src/api/market_hub.py`)
**Purpose:** Receive real-time market quotes
- **Connection:** `wss://rtc.topstepx.com/hubs/market`
- **Events Handled:**
  - `MarketQuote` - Real-time price updates (1-4/sec per instrument)
- **Subscription Management:** Subscribe to contracts with open positions
- **Thread:** Shares main thread with User Hub

#### 3. REST Client (`src/api/rest_client.py`)
**Purpose:** Execute enforcement actions via TopstepX REST API
- **Endpoints Used:**
  - `POST /api/Position/closeContract` - Close positions
  - `POST /api/Position/partialCloseContract` - Reduce position size
  - `POST /api/Order/cancel` - Cancel orders
  - `POST /api/Order/placeOrder` - Place stop-loss orders
- **Authentication:** JWT token-based (24-hour expiry)
- **Retry Logic:** 3 attempts with exponential backoff

### Layer 2: Event Processing

#### 4. Event Router (`src/core/event_router.py`)
**Purpose:** Central event processing pipeline
- **Responsibilities:**
  1. Update state modules (BEFORE rule checks)
  2. Check account lockout status (gate for rules)
  3. Route events to relevant risk rules
  4. Execute enforcement actions on rule breaches
  5. Broadcast events to WebSocket server
- **Processing Order (CRITICAL):**
  ```
  Event Arrives → Update State → Check Lockout → Route to Rules → Enforce
  ```
- **Performance:** < 10ms per event

### Layer 3: State Management Modules

#### 5. State Manager (MOD-009: `src/state/state_manager.py`)
**Purpose:** Mirror TopstepX positions and orders
- **In-Memory State:**
  - Positions by account (nested dict)
  - Orders by account (nested dict)
- **Key Operations:**
  - `update_position()` - From GatewayUserPosition events
  - `update_order()` - From GatewayUserOrder events
  - `get_all_positions()` - For rule checks
  - `get_position_count()` - Total contract count
- **Persistence:** Batched writes every 5 seconds
- **Recovery:** Load from SQLite on startup

#### 6. PNL Tracker (MOD-005: `src/state/pnl_tracker.py`)
**Purpose:** Calculate and track realized/unrealized P&L
- **Daily Realized P&L:**
  - `add_trade_pnl()` - Accumulate from trades
  - `get_daily_realized_pnl()` - Current total
  - Synced to SQLite immediately (critical data)
- **Unrealized P&L:**
  - `calculate_unrealized_pnl()` - Real-time calculation
  - Uses: positions (MOD-009) + quotes (MOD-006) + contract metadata (MOD-007)
  - Triggered by: GatewayUserPosition, MarketQuote events
- **Daily Reset:** Reset counters at configured time

#### 7. Quote Tracker (MOD-006: `src/api/quote_tracker.py`)
**Purpose:** Real-time price tracking
- **In-Memory Only:** No persistence (always fresh)
- **Data Stored:**
  - Last price, bid, ask per contract
  - Timestamp of last update
- **Stale Check:** Quote > 10 seconds old considered stale
- **Used By:** PNL Tracker (MOD-005) for unrealized P&L

#### 8. Contract Cache (MOD-007: `src/api/contract_cache.py`)
**Purpose:** Cache contract metadata (tick values)
- **Lazy Loading:** Fetch from API on cache miss
- **Data Stored:**
  - Tick size (e.g., 0.25)
  - Tick value (e.g., $5)
  - Symbol ID
  - Contract name
- **Persistence:** Lazy write to SQLite (background thread)
- **Recovery:** Load from SQLite on startup

#### 9. Trade Counter (MOD-008: `src/state/trade_counter.py`)
**Purpose:** Track trade frequency
- **In-Memory State:**
  - Rolling 1-hour window of trade timestamps
  - Session start times
- **Counts Provided:**
  - Trades in last minute
  - Trades in last hour
  - Trades in current session
- **Persistence:** Async insert to SQLite
- **Recovery:** Load last hour on startup

#### 10. Lockout Manager (MOD-002: `src/state/lockout_manager.py`)
**Purpose:** Manage account lockout state
- **Lockout Types:**
  - **Hard Lockout:** Until specific datetime (e.g., daily reset at 5 PM)
  - **Cooldown Timer:** Duration-based (e.g., 30 minutes)
- **Key Operations:**
  - `set_lockout()` - Set hard lockout
  - `set_cooldown()` - Set duration-based lockout
  - `is_locked_out()` - Check if account locked (called before every rule check)
  - `clear_lockout()` - Manual or auto-clear
- **Persistence:** Immediate sync to SQLite (critical data)
- **Auto-Expiry:** Background thread checks every 1 second

#### 11. Timer Manager (MOD-003: `src/state/timer_manager.py`)
**Purpose:** Countdown timers for cooldowns
- **In-Memory Only:** No persistence (safer to reset on restart)
- **Operations:**
  - `start_timer()` - Start countdown
  - `check_timers()` - Fire expired callbacks
  - `get_remaining_time()` - Query time left
- **Background Task:** Checks every 1 second
- **Used By:** Lockout Manager (MOD-002) for cooldowns

#### 12. Reset Scheduler (MOD-004: `src/state/reset_scheduler.py`)
**Purpose:** Manage daily reset schedule
- **Configuration:**
  - Reset time (e.g., "17:00")
  - Timezone (e.g., "America/New_York")
- **Reset Actions:**
  - Clear daily P&L (MOD-005)
  - Clear trade counters (MOD-008)
  - Clear daily lockouts (MOD-002)
- **Persistence:** Sync to SQLite after each reset
- **Background Task:** Checks every 10 seconds

### Layer 4: Enforcement

#### 13. Enforcement Engine (MOD-001: `src/enforcement/actions.py`)
**Purpose:** Execute enforcement actions via REST API
- **Actions Supported:**
  - `close_all_positions()` - Close all positions
  - `close_position()` - Close specific position
  - `reduce_position_to_limit()` - Partial close
  - `cancel_all_orders()` - Cancel all orders
  - `cancel_order()` - Cancel specific order
  - `place_stop_loss_order()` - Auto-place stop-loss
- **Retry Logic:** 3 attempts with exponential backoff
- **Logging:** All actions logged to `logs/enforcement.log`
- **Used By:** ALL 12 risk rules

### Layer 5: Real-Time Broadcasting

#### 14. WebSocket Server (`src/core/websocket_server.py`)
**Purpose:** Broadcast real-time events to Trader CLIs
- **Server Address:** `ws://localhost:8765`
- **Protocol:** Raw WebSocket (no Socket.IO wrapper)
- **Events Broadcasted:**
  - All SignalR events (GatewayUserTrade, GatewayUserPosition, etc.)
  - Enforcement actions
  - Lockout changes
  - Daily reset notifications
- **Client Filtering:** Clients filter by account_id (server broadcasts all)
- **Thread:** Dedicated thread (Thread 6) with asyncio event loop
- **Performance:** < 1ms broadcast latency

---

## Component Initialization Order

The daemon follows a strict **29-step startup sequence** to ensure proper dependency initialization:

### Phase 1: Configuration Loading (Steps 1-3)
1. **Load Account Configuration** (`config/accounts.yaml`)
   - Account IDs, usernames, API keys
2. **Load Risk Rule Configuration** (`config/risk_config.yaml`)
   - All 12 rule configs (enabled/disabled, limits)
3. **Validate Configuration**
   - Check required fields present
   - Validate reset times, timezones
   - No duplicate account IDs

### Phase 2: Database Initialization (Steps 4-6)
4. **Connect to SQLite Database** (`data/state.db`)
   - Enable WAL mode for concurrent reads
   - Set busy timeout (5 seconds)
5. **Create Tables** (If not exist)
   - 9 tables: lockouts, daily_pnl, contract_cache, trade_history, session_state, positions, orders, enforcement_log, reset_schedule
6. **Run Database Migrations** (If needed)
   - Check schema version
   - Run upgrade scripts if outdated

### Phase 3: Module Initialization - Load State from SQLite (Steps 7-15)

**CRITICAL ORDER: Load in dependency order**

7. **MOD-004: Reset Scheduler**
   - Load last reset date and next reset time
   - Check if reset needed (daemon was down during reset time)

8. **MOD-002: Lockout Manager**
   - Load active lockouts
   - Restore lockout state (critical for enforcement)

9. **MOD-005: PNL Tracker**
   - Load today's daily P&L for each account
   - Initialize daily totals

10. **MOD-007: Contract Cache**
    - Load cached contract metadata
    - Avoid API calls for known contracts

11. **MOD-008: Trade Counter**
    - Load last hour of trade timestamps
    - Load session start times

12. **MOD-009: State Manager (Positions)**
    - Load all open positions from database
    - Mirror TopstepX state

13. **MOD-009: State Manager (Orders)**
    - Load all working orders from database
    - Mirror TopstepX state

14. **MOD-006: Quote Tracker**
    - NO database load - starts fresh
    - Quotes arrive within seconds of SignalR connection

15. **MOD-003: Timer Manager**
    - NO database load - timers start fresh
    - Safer to reset (avoid stale timers from yesterday)

### Phase 4: TopstepX Authentication (Steps 16-18)
16. **Authenticate with TopstepX API**
    - For EACH account in `accounts.yaml`
    - Get JWT token (valid 24 hours)
17. **Validate Tokens**
    - Verify all tokens are valid
18. **Store Tokens for API Calls**
    - REST client uses these for enforcement

### Phase 5: SignalR Hub Connections (Steps 19-23)
19. **Connect SignalR User Hub**
    - `wss://rtc.topstepx.com/hubs/user`
    - Register handlers: GatewayUserTrade, GatewayUserPosition, etc.
20. **Connect SignalR Market Hub**
    - `wss://rtc.topstepx.com/hubs/market`
    - Register handler: MarketQuote
21. **Subscribe to Quotes for Open Positions**
    - For each open position, subscribe to real-time quotes
22. **Wait for SignalR Connections to Stabilize**
    - Give 2 seconds to establish connections
    - Verify connections succeeded
23. **Verify Initial Events Received**
    - Optional check to verify data flow

### Phase 6: Start Background Threads (Steps 24-29)
24. **Start Timer/Lockout Checker Thread**
    - Runs every 1 second
    - Checks expired lockouts and timers
25. **Start Daily Reset Checker Thread**
    - Runs every 10 seconds
    - Checks if reset time reached
26. **Start State Writer Thread**
    - Runs every 5 seconds
    - Batches position/order writes to SQLite
27. **Start Token Refresh Thread**
    - Runs every hour
    - Refreshes JWT token if < 4 hours remaining
28. **Start WebSocket Server Thread**
    - Runs asyncio event loop
    - Listens on `localhost:8765` for Trader CLI connections
29. **Log Startup Complete**
    - Display summary (account count, active rules, etc.)

**Total Startup Time:** ~5-10 seconds (mostly network authentication and SignalR connection)

---

## Inter-Component Communication

### Communication Pattern: Direct Function Calls (Python)

All components run in the **same Python process** and communicate via direct function calls:

```python
# Example: Event Router calling modules
def route_event(self, event_type, payload):
    # 1. Update state (direct call to MOD-009)
    self.state_manager.update_position(payload)

    # 2. Check lockout (direct call to MOD-002)
    if self.lockout_manager.is_locked_out(account_id):
        return

    # 3. Route to rules (direct call to rule instances)
    for rule in self.active_rules:
        action = rule.check(payload)
        if action:
            # 4. Execute enforcement (direct call to MOD-001)
            self.enforcement_engine.execute(action)
```

### Thread-Safe Communication

**Main Thread:** Event processing (SignalR event loop)
**Background Threads:** State persistence, timers, reset checks, WebSocket server

**Synchronization Mechanisms:**
- **Python GIL:** Protects in-memory dict access (single-threaded event processing)
- **Thread-Safe Queues:** For batched writes to SQLite
  - `queue.Queue` for enforcement logs, contract cache, trade history, positions/orders
- **SQLite WAL Mode:** Allows concurrent reads from Trader CLIs
- **asyncio.run_coroutine_threadsafe():** For WebSocket broadcasts from main thread

### Data Flow Diagram

```
SignalR Event → Event Router → State Modules → Lockout Check → Rules → Enforcement
                      ↓
                WebSocket Server (broadcast to Trader CLIs)
                      ↓
            Background Writers → SQLite (persistence)
```

---

## Configuration

### Configuration Files

1. **`config/accounts.yaml`**
   - Account credentials (account_id, username, api_key)
   - Loaded once at startup
   - Requires daemon restart to apply changes

2. **`config/risk_config.yaml`**
   - All 12 risk rule configurations
   - Enabled/disabled flags
   - Rule-specific parameters (limits, timeouts, etc.)
   - Loaded once at startup
   - Requires daemon restart to apply changes

### Configuration Loading

```python
# Load YAML files
accounts = load_config('config/accounts.yaml')
risk_config = load_config('config/risk_config.yaml')

# Validate
validate_config(accounts, risk_config)

# Initialize modules with config
for rule_config in risk_config:
    if rule_config['enabled']:
        rule = RuleFactory.create(rule_config)
        self.active_rules.append(rule)
```

### Runtime Configuration Changes

**No hot-reload support.** Configuration changes require:
1. Edit YAML file
2. Restart daemon (via Admin CLI)
3. Daemon reloads config on startup

---

## Main Event Loop

### Event Loop Structure

The daemon's **main thread** is the SignalR event loop:

```python
def run(self):
    """
    Main event loop - blocks on SignalR waiting for events.
    Background threads run independently.
    """
    try:
        # Block here waiting for events (runs forever)
        self.user_hub.connection.start()

        # Never reaches here (blocks until error or shutdown)

    except KeyboardInterrupt:
        logger.info("Received shutdown signal (Ctrl+C)")
        self.shutdown()

    except Exception as e:
        logger.critical(f"Daemon crashed: {e}", exc_info=True)
        self.emergency_shutdown()
```

### Event Processing Flow

**Main Thread (Event-Driven):**
```
1. SignalR event arrives (e.g., GatewayUserTrade)
   ↓
2. SignalR calls registered handler: _on_trade(payload)
   ↓
3. Handler calls: event_router.route_event("GatewayUserTrade", payload)
   ↓
4. EventRouter processes event:
   - Update state (MOD-005, MOD-008, etc.)
   - Broadcast to WebSocket server
   - Check lockout
   - Route to rules
   - Execute enforcement if breach
   ↓
5. Return to waiting (main thread blocks again)
```

**Processing Time:** < 10ms per event

**Background Threads (Time-Driven):**
- **Thread 2:** Timer/Lockout checker (every 1 second)
- **Thread 3:** Daily reset checker (every 10 seconds)
- **Thread 4:** State writer (every 5 seconds)
- **Thread 5:** Token refresh (every 1 hour)
- **Thread 6:** WebSocket server (asyncio event loop)

---

## Shutdown Procedure

### Graceful Shutdown Sequence

**Triggered By:**
- Admin CLI: "Stop Service"
- Windows Service Manager: Stop command
- Development mode: Ctrl+C

**Shutdown Steps:**

1. **Set Shutdown Flag**
   ```python
   self.daemon_running = False
   logger.info("Shutdown initiated...")
   ```

2. **Stop Accepting New Events**
   ```python
   user_hub.connection.stop()
   market_hub.connection.stop()
   logger.info("SignalR connections closed")
   ```

3. **Stop WebSocket Server**
   ```python
   websocket_server.stop()
   logger.info("WebSocket server stopped")
   ```

4. **Wait for Background Threads to Finish**
   ```python
   threads = [timer_thread, reset_thread, writer_thread, token_thread, websocket_thread]
   for thread in threads:
       thread.join(timeout=10)
       if thread.is_alive():
           logger.warning(f"Thread {thread.name} did not stop cleanly")
   ```

5. **Flush All State to SQLite**
   ```python
   with sqlite3.connect('data/state.db') as db:
       state_manager.flush_positions_to_db(db)
       state_manager.flush_orders_to_db(db)
       contract_cache.flush_to_db(db)
       lockout_manager.flush_to_db(db)
       pnl_tracker.flush_to_db(db)
       db.commit()
   logger.info("State flushed to database")
   ```

6. **Close Database Connection**
   ```python
   db_connection.close()
   logger.info("Database connection closed")
   ```

7. **Log Shutdown Complete**
   ```python
   logger.info("Risk Manager Daemon Stopped")
   ```

**Total Shutdown Time:** < 15 seconds

### Emergency Shutdown (Crash Recovery)

**When Daemon Crashes:**
```python
def emergency_shutdown(self):
    """Emergency shutdown - save critical state before exit"""
    logger.critical("EMERGENCY SHUTDOWN - Attempting to save state")

    try:
        # Try to flush critical state only
        with sqlite3.connect('data/state.db') as db:
            # Save lockouts (CRITICAL)
            lockout_manager.flush_to_db(db)

            # Save daily P&L (CRITICAL)
            pnl_tracker.flush_to_db(db)

            db.commit()
        logger.info("Critical state saved")

    except Exception as e:
        logger.critical(f"Failed to save state during crash: {e}")

    finally:
        sys.exit(1)
```

**On Restart After Crash:**
1. Daemon restarts (Windows Service auto-restart)
2. Startup sequence runs (29 steps)
3. Load persisted state from SQLite:
   - ✅ Lockouts restored (MOD-002)
   - ✅ Daily P&L restored (MOD-005)
   - ✅ Positions restored (MOD-009) - may be slightly stale (< 5 seconds)
   - ✅ Orders restored (MOD-009) - may be slightly stale (< 5 seconds)
   - ❌ Quotes lost (start fresh - no issue, quotes arrive within seconds)
   - ❌ Timers lost (recalculated on events)
4. Resume monitoring

**Data Loss on Crash:** < 5 seconds of position/order updates (acceptable)

---

## Key Classes and Methods

### Class: RiskManagerDaemon

**File:** `src/core/daemon.py`

```python
class RiskManagerDaemon:
    """Main daemon class - manages startup, event loop, shutdown"""

    def __init__(self):
        """Initialize module references"""
        self.daemon_running = False
        self.state_manager = None
        self.pnl_tracker = None
        self.quote_tracker = None
        self.contract_cache = None
        self.trade_counter = None
        self.lockout_manager = None
        self.timer_manager = None
        self.reset_scheduler = None
        self.user_hub = None
        self.market_hub = None
        self.rest_client = None
        self.websocket_server = None
        self.db_connection = None
        self.accounts = None
        self.risk_config = None

    def start(self):
        """Execute 29-step startup sequence"""
        # Phase 1: Configuration (Steps 1-3)
        self._load_configuration()

        # Phase 2: Database (Steps 4-6)
        self._initialize_database()

        # Phase 3: Modules (Steps 7-15)
        self._initialize_modules()

        # Phase 4: Authentication (Steps 16-18)
        self._authenticate_accounts()

        # Phase 5: SignalR (Steps 19-23)
        self._connect_signalr()

        # Phase 6: Background Threads (Steps 24-29)
        self._start_background_threads()

        self.daemon_running = True

    def run(self):
        """Main event loop - blocks on SignalR"""
        try:
            self.user_hub.connection.start()
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            logger.critical(f"Daemon crashed: {e}", exc_info=True)
            self.emergency_shutdown()

    def shutdown(self):
        """Graceful shutdown sequence"""
        self.daemon_running = False
        self.user_hub.connection.stop()
        self.market_hub.connection.stop()
        self.websocket_server.stop()
        # ... (see Shutdown Procedure section)

    def emergency_shutdown(self):
        """Emergency shutdown - save critical state"""
        # ... (see Emergency Shutdown section)
```

### Class: EventRouter

**File:** `src/core/event_router.py`

```python
class EventRouter:
    """Routes SignalR events to state updates and risk rules"""

    def __init__(self, state_manager, pnl_tracker, quote_tracker,
                 contract_cache, trade_counter, lockout_manager,
                 rule_engine, websocket_server):
        self.state_manager = state_manager
        self.pnl_tracker = pnl_tracker
        self.quote_tracker = quote_tracker
        self.contract_cache = contract_cache
        self.trade_counter = trade_counter
        self.lockout_manager = lockout_manager
        self.rule_engine = rule_engine
        self.websocket_server = websocket_server

    def route_event(self, event_type: str, payload: dict):
        """Main event routing entry point"""
        # STEP 1: Update state FIRST (before rule checks)
        self._update_state(event_type, payload)

        # STEP 2: Broadcast to Trader CLIs
        self.websocket_server.broadcast({
            'type': event_type,
            'account_id': payload.get('accountId'),
            'data': payload
        })

        # STEP 3: Check if account is locked
        account_id = payload.get('accountId')
        if account_id and self.lockout_manager.is_locked_out(account_id):
            logger.debug(f"Account {account_id} locked - skipping rules")
            return

        # STEP 4: Route to relevant rules
        self._route_to_rules(event_type, payload)

    def _update_state(self, event_type: str, payload: dict):
        """Update state based on event type"""
        if event_type == "GatewayUserTrade":
            self.pnl_tracker.add_trade_pnl(...)
            self.trade_counter.record_trade(...)
        elif event_type == "GatewayUserPosition":
            self.state_manager.update_position(...)
        elif event_type == "GatewayUserOrder":
            self.state_manager.update_order(...)
        elif event_type == "MarketQuote":
            self.quote_tracker.update_quote(...)

    def _route_to_rules(self, event_type: str, payload: dict):
        """Route event to relevant rules"""
        rule_map = {
            "GatewayUserTrade": ["RULE-003", "RULE-006", "RULE-007", "RULE-012"],
            "GatewayUserPosition": ["RULE-001", "RULE-002", "RULE-004", ...],
            # ...
        }

        for rule_id in rule_map.get(event_type, []):
            action = self.rule_engine.check_rule(rule_id, payload)
            if action is not None:
                self._execute_enforcement(action, payload['accountId'])
                break  # Only execute first breach
```

### Class: DaemonWebSocketServer

**File:** `src/core/websocket_server.py`

```python
class DaemonWebSocketServer:
    """WebSocket server for broadcasting events to Trader CLIs"""

    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.loop = None
        self.server = None

    def start(self, loop: asyncio.AbstractEventLoop):
        """Start WebSocket server in asyncio event loop"""
        self.loop = loop
        start_server = websockets.serve(self._handler, self.host, self.port)
        self.server = loop.run_until_complete(start_server)
        logger.info(f"WebSocket server started on {self.host}:{self.port}")

    async def _handler(self, websocket, path):
        """Handle new Trader CLI connection"""
        self.clients.add(websocket)
        logger.info(f"Trader CLI connected: {websocket.remote_address}")
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            logger.info(f"Trader CLI disconnected")

    def broadcast(self, event: Dict[str, Any]):
        """Broadcast event to all connected Trader CLIs (thread-safe)"""
        if not self.clients:
            return

        message = json.dumps(event)
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self._broadcast_async(message),
                self.loop
            )

    async def _broadcast_async(self, message: str):
        """Actually broadcast to clients (runs in event loop)"""
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )

    def stop(self):
        """Stop WebSocket server"""
        if self.server:
            self.server.close()
            self.loop.run_until_complete(self.server.wait_closed())
```

---

## SPECS Files Analyzed

### Primary Specs (Backend/Daemon)
1. `/project-specs/SPECS/02-BACKEND-DAEMON/DAEMON_ARCHITECTURE.md`
2. `/project-specs/SPECS/02-BACKEND-DAEMON/EVENT_PIPELINE.md`
3. `/project-specs/SPECS/02-BACKEND-DAEMON/STATE_MANAGEMENT.md`

### API Specs
4. `/project-specs/SPECS/05-INTERNAL-API/DAEMON_ENDPOINTS.md`
5. `/project-specs/SPECS/05-INTERNAL-API/FRONTEND_BACKEND_ARCHITECTURE.md`

### Module Specs
6. `/project-specs/SPECS/04-CORE-MODULES/modules/state_manager.md` (MOD-009)
7. `/project-specs/SPECS/04-CORE-MODULES/modules/pnl_tracker.md` (MOD-005)
8. `/project-specs/SPECS/04-CORE-MODULES/modules/enforcement_actions.md` (MOD-001)
9. `/project-specs/SPECS/04-CORE-MODULES/modules/lockout_manager.md` (MOD-002)

---

## Summary

The Risk Manager Daemon is a **sophisticated event-driven system** that:

1. **Monitors ALL accounts** from a single Windows Service instance
2. **Processes events in < 10ms** with strict ordering (state → lockout → rules → enforcement)
3. **Broadcasts real-time updates** to Trader CLIs via WebSocket
4. **Persists critical state** to SQLite for crash recovery
5. **Runs 6 threads** (1 main + 5 background) for concurrent operations
6. **Enforces 12 risk rules** via centralized enforcement module
7. **Manages 13 core components** across 5 architectural layers

**Key Implementation Files:**
- `src/core/daemon.py` (~250 lines) - Main daemon logic
- `src/core/event_router.py` (~150 lines) - Event processing
- `src/core/websocket_server.py` (~150 lines) - Real-time broadcasting
- `src/service/windows_service.py` (~150 lines) - Windows Service wrapper
- `src/cli/admin/service_control.py` (~200 lines) - Admin controls

**Total Core:** ~900 lines for daemon architecture

**Next Steps:**
- Analyze API integration layer (SignalR/REST clients)
- Analyze risk rules implementation
- Analyze CLI architecture (Admin and Trader)
