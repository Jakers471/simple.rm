---
doc_id: DAEMON-001
version: 1.0
last_updated: 2025-10-21
dependencies: [ARCH-V2.2, PIPE-001, STATE-001, DB-SCHEMA-001, MOD-001 through MOD-009]
---

# Daemon Architecture

**Purpose:** Complete daemon implementation - startup, threading, event loop, Windows Service, shutdown

**File Coverage:** `src/core/daemon.py`, `src/service/windows_service.py`, `src/service/installer.py`

---

## 🎯 Core Architecture Overview

### **What is the Daemon?**
A Windows Service that runs continuously (24/7), monitoring all configured trading accounts and enforcing risk rules in real-time.

### **Key Characteristics:**
- **One daemon monitors ALL accounts** (not one per account)
- **Runs as Windows Service** (auto-start on boot, requires admin to control)
- **Cannot be stopped by traders** (admin-only control)
- **Survives reboots** (auto-starts with Windows)
- **Hybrid mode** (Windows Service for production, console mode for development)

---

## 🔐 Security & Access Control

### **Admin Privileges Required For:**
```
✅ Install Windows Service
✅ Start/Stop/Restart Service
✅ Configure risk rules (config/risk_config.yaml)
✅ Manage accounts (config/accounts.yaml)
✅ Add/remove API keys
✅ Modify daemon settings
```

### **Trader Access (Read-Only):**
```
❌ CANNOT stop daemon
❌ CANNOT modify config
❌ CANNOT bypass rules
✅ CAN view status (via Trader CLI reading SQLite)
✅ CAN view lockouts (read-only)
✅ CAN view P&L (read-only)
✅ CAN view logs (read-only)
```

### **Implementation:**
```python
# Admin CLI requires password authentication
def admin_main():
    if not authenticate_admin():
        print("❌ Access denied - admin privileges required")
        sys.exit(1)

    # Show admin menu (service control, config, etc.)
    admin_menu()

# Trader CLI has no authentication (read-only SQLite access)
def trader_main():
    # No authentication needed
    # Just reads from data/state.db
    trader_menu()
```

---

## 🧵 Threading Model

### **Thread 1: Main Thread (SignalR Event Loop)**
```python
# Main daemon thread - runs SignalR WebSocket listeners
def main_event_loop():
    # Connect SignalR User Hub
    user_hub.connection.start()  # Blocks here waiting for events

    # When event arrives:
    #   → SignalR calls event handler
    #   → event_router.route_event(type, payload)
    #   → Process event (update state, check rules, enforce)
    #   → Return to waiting
```

**Characteristics:**
- Blocks on SignalR WebSocket connection
- Event-driven (idle until event arrives)
- Processes events synchronously (one at a time)
- Latency: < 10ms per event

**Why main thread:**
- SignalR WebSocket requires main thread
- Python GIL makes single-threaded simple
- Events are fast enough (< 10ms processing)

---

### **Thread 2: Background - Timers & Lockouts**
```python
def timer_and_lockout_checker():
    """Check for expired timers and lockouts every 1 second."""
    while daemon_running:
        time.sleep(1)

        # Check expired lockouts
        expired = lockout_manager.check_expired_lockouts()
        for account_id in expired:
            logger.info(f"Lockout expired for account {account_id}")

        # Check expired timers
        expired = timer_manager.check_expired_timers()
        for account_id in expired:
            logger.info(f"Timer expired for account {account_id}")
```

**Characteristics:**
- Runs every 1 second
- Time-based (not event-driven)
- Independent of main event thread

**Why separate thread:**
- Lockouts expire at specific times (need to check continuously)
- Can't rely on events to trigger expiry checks
- Can't block main SignalR thread

---

### **Thread 3: Background - Daily Reset Scheduler**
```python
def daily_reset_checker():
    """Check for daily reset time every 10 seconds."""
    while daemon_running:
        time.sleep(10)

        # Check if reset time reached for any account
        accounts_to_reset = reset_scheduler.check_reset_times()

        for account_id in accounts_to_reset:
            logger.info(f"Daily reset triggered for account {account_id}")

            # Reset daily P&L
            pnl_tracker.reset_daily_pnl(account_id)

            # Clear daily lockouts
            lockout_manager.clear_daily_lockouts(account_id)

            # Reset trade counter
            trade_counter.reset_daily_count(account_id)
```

**Characteristics:**
- Runs every 10 seconds
- Checks if current time >= reset time
- Executes reset actions (clear P&L, lockouts, counters)

**Why separate thread:**
- Time-based (not event-driven)
- Independent of events
- Can't block main thread

---

### **Thread 4: Background - State Writer (Batched Persistence)**
```python
def state_writer():
    """Write batched state to SQLite every 5 seconds."""
    while daemon_running:
        time.sleep(5)

        with sqlite3.connect('data/state.db') as db:
            # Write batched positions
            while not position_update_queue.empty():
                position = position_update_queue.get_nowait()
                db.execute("INSERT OR REPLACE INTO positions (...)", position)

            # Write batched orders
            while not order_update_queue.empty():
                order = order_update_queue.get_nowait()
                db.execute("INSERT OR REPLACE INTO orders (...)", order)

            # Write batched enforcement logs
            while not enforcement_log_queue.empty():
                log = enforcement_log_queue.get_nowait()
                db.execute("INSERT INTO enforcement_log (...)", log)

            # Commit all at once
            db.commit()
```

**Characteristics:**
- Runs every 5 seconds
- Batches writes for performance
- Uses thread-safe queues

**Why separate thread:**
- Can't block main event thread with disk I/O
- Batching reduces SQLite contention
- Asynchronous persistence

---

### **Thread 5: Background - Token Refresh**
```python
def token_refresh_checker():
    """Refresh TopstepX JWT token every 20 hours."""
    while daemon_running:
        time.sleep(3600)  # Check every hour

        # Check if token expires in < 4 hours
        if token_expires_in() < 14400:  # 4 hours = 14400 seconds
            logger.info("Refreshing TopstepX token")

            try:
                new_token = auth.validate_and_refresh_token(current_token)
                current_token = new_token

                # Update SignalR connections with new token
                user_hub.update_token(new_token)
                market_hub.update_token(new_token)

            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                # Will retry in 1 hour
```

**Characteristics:**
- Runs every hour (checks token expiry)
- Refreshes token if < 4 hours remaining
- Handles token refresh failures

**Why separate thread:**
- Time-based (not event-driven)
- Independent of events
- Can't block main thread

---

### **Thread 6: Background - WebSocket Server**
```python
def websocket_server_thread():
    """
    Run WebSocket server for broadcasting real-time events to Trader CLIs.
    Uses asyncio event loop for handling WebSocket connections.
    """
    import asyncio

    # Create asyncio event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Start WebSocket server
    websocket_server = DaemonWebSocketServer(host='localhost', port=8765)
    websocket_server.start(loop)

    # Run event loop (blocks here)
    try:
        loop.run_forever()
    except Exception as e:
        logger.error(f"WebSocket server error: {e}")
    finally:
        loop.close()
```

**Characteristics:**
- Runs asyncio event loop (separate from main thread)
- Listens on `localhost:8765` for Trader CLI connections
- Broadcasts events to all connected clients
- Thread-safe broadcasting using `asyncio.run_coroutine_threadsafe()`

**Why separate thread:**
- asyncio requires its own event loop
- Can't block main SignalR thread
- Independent of event processing (broadcasting only)
- Trader CLIs connect/disconnect independently

**Integration with Event Router:**
```python
# In EventRouter.route_event() - called from main thread
def route_event(self, event_type: str, payload: dict):
    # STEP 1: Update state
    self._update_state(event_type, payload)

    # STEP 2: Broadcast to Trader CLIs (Thread 6)
    self.websocket_server.broadcast({
        'type': event_type,
        'account_id': payload.get('accountId'),
        'data': payload
    })

    # STEP 3: Check lockout
    if self.lockout_manager.is_locked_out(account_id):
        return

    # STEP 4: Route to rules
    self._route_to_rules(event_type, payload)
```

---

### **Total: 6 Threads**
1. Main (SignalR event loop)
2. Timer/lockout checker (every 1 second)
3. Daily reset checker (every 10 seconds)
4. State writer (every 5 seconds)
5. Token refresh (every 1 hour)
6. WebSocket server (asyncio event loop for Trader CLI connections)

---

## 🚀 Startup Sequence (29 Steps)

### **Phase 1: Configuration Loading (Steps 1-3)**

**Step 1: Load Account Configuration**
```python
# Load config/accounts.yaml
accounts = load_config('config/accounts.yaml')

# Example accounts.yaml:
# accounts:
#   - account_id: 123
#     username: "trader1"
#     api_key: "xyz123..."
#   - account_id: 456
#     username: "trader2"
#     api_key: "abc456..."
```

**Step 2: Load Risk Rule Configuration**
```python
# Load config/risk_config.yaml
risk_config = load_config('config/risk_config.yaml')

# Contains all 12 rule configs (enabled/disabled, limits, etc.)
```

**Step 3: Validate Configuration**
```python
# Validate all required fields present
validate_config(accounts, risk_config)

# Check:
# - All accounts have username, api_key
# - All enabled rules have required parameters
# - No duplicate account IDs
# - Valid reset times, timezones, etc.
```

---

### **Phase 2: Database Initialization (Steps 4-6)**

**Step 4: Connect to SQLite Database**
```python
# Open data/state.db
db_connection = sqlite3.connect('data/state.db')

# Enable WAL mode (Write-Ahead Logging) for concurrent reads
db_connection.execute("PRAGMA journal_mode=WAL")

# Set busy timeout (wait 5 seconds if database locked)
db_connection.execute("PRAGMA busy_timeout=5000")
```

**Step 5: Create Tables (If Not Exist)**
```python
# Run CREATE TABLE IF NOT EXISTS for all 9 tables
# (See DATABASE_SCHEMA.md for complete schema)

create_tables(db_connection)

# Tables created:
# - lockouts (MOD-002)
# - daily_pnl (MOD-005)
# - contract_cache (MOD-007)
# - trade_history (MOD-008)
# - session_state (MOD-008)
# - positions (MOD-009)
# - orders (MOD-009)
# - enforcement_log (MOD-001)
# - reset_schedule (MOD-004)
```

**Step 6: Run Database Migrations (If Needed)**
```python
# Check schema version
current_version = get_schema_version(db_connection)

# Run migrations if schema outdated
if current_version < LATEST_SCHEMA_VERSION:
    run_migrations(db_connection, current_version, LATEST_SCHEMA_VERSION)
```

---

### **Phase 3: Module Initialization - Load State from SQLite (Steps 7-15)**

**CRITICAL ORDER: Load in dependency order**

**Step 7: MOD-004 - Reset Scheduler**
```python
reset_scheduler = ResetScheduler()
reset_scheduler.load_from_database(db_connection)

# Loads reset schedule for each account:
# - last_reset_date
# - next_reset_time
# - reset_time_config (e.g., "17:00")
# - timezone (e.g., "America/New_York")
```

**Step 8: MOD-002 - Lockout Manager**
```python
lockout_manager = LockoutManager()
lockout_manager.load_from_database(db_connection)

# Loads active lockouts:
# - account_id
# - is_locked
# - reason
# - locked_until
# - rule_id

# Example: Account 123 locked until 5:00 PM (daily loss limit)
```

**Step 9: MOD-005 - PNL Tracker**
```python
pnl_tracker = PNLTracker()
pnl_tracker.load_from_database(db_connection)

# Loads daily P&L for each account:
# - account_id
# - date (today's date)
# - realized_pnl (current total)

# Example: Account 123 → -$350 realized P&L today
```

**Step 10: MOD-007 - Contract Cache**
```python
contract_cache = ContractCache()
contract_cache.load_from_database(db_connection)

# Loads contract metadata:
# - contract_id (e.g., "CON.F.US.MNQ.U25")
# - tick_size (0.25)
# - tick_value ($5)
# - symbol_id ("MNQ")
# - name ("Micro E-mini NASDAQ-100")

# Used for P&L calculations
```

**Step 11: MOD-008 - Trade Counter**
```python
trade_counter = TradeCounter()
trade_counter.load_from_database(db_connection)

# Loads recent trade history (last 24 hours):
# - account_id
# - timestamp
# - contract_id
# - pnl

# Used for trade frequency limits
```

**Step 12: MOD-009 - State Manager (Positions)**
```python
state_manager = StateManager()
state_manager.load_positions_from_database(db_connection)

# Loads open positions:
# - id (position ID)
# - account_id
# - contract_id
# - type (1=Long, 2=Short)
# - size (number of contracts)
# - average_price

# Example: Account 123 → Long 3 MNQ @ 21000.5
```

**Step 13: MOD-009 - State Manager (Orders)**
```python
state_manager.load_orders_from_database(db_connection)

# Loads open orders:
# - id (order ID)
# - account_id
# - contract_id
# - type (1=Market, 2=Limit, 3=Stop)
# - side (1=Buy, 2=Sell)
# - size
# - limit_price / stop_price
# - state (1=Working, 2=Filled, etc.)

# Example: Account 123 → Stop-loss sell order @ 20950
```

**Step 14: MOD-006 - Quote Tracker (No Persistence)**
```python
quote_tracker = QuoteTracker()
# NO database load - quotes start fresh (real-time data)

# Will populate when Market Hub sends first quote events
```

**Step 15: MOD-003 - Timer Manager (No Persistence)**
```python
timer_manager = TimerManager()
# NO database load - timers start fresh

# Timers calculated on-the-fly based on events
```

---

### **Phase 4: TopstepX Authentication (Steps 16-18)**

**Step 16: Authenticate with TopstepX API**
```python
# For EACH account in accounts.yaml
for account in accounts:
    try:
        token = auth.authenticate(
            username=account['username'],
            api_key=account['api_key']
        )

        # Store token (valid 24 hours)
        account_tokens[account['account_id']] = token

        logger.info(f"Authenticated account {account['account_id']}")

    except Exception as e:
        logger.error(f"Failed to authenticate account {account['account_id']}: {e}")
        # Continue with other accounts (don't fail entire startup)
```

**Step 17: Validate Tokens**
```python
# Verify all tokens are valid
for account_id, token in account_tokens.items():
    if not auth.validate_token(token):
        logger.error(f"Token invalid for account {account_id}")
```

**Step 18: Store Tokens for API Calls**
```python
# REST client uses these tokens for enforcement
rest_client.set_tokens(account_tokens)
```

---

### **Phase 5: SignalR Hub Connections (Steps 19-23)**

**Step 19: Connect SignalR User Hub**
```python
user_hub = SignalRListener(
    jwt_token=account_tokens[primary_account_id],  # Use first account token
    event_router=event_router
)

user_hub.setup_user_hub()
# Connects to wss://rtc.topstepx.com/hubs/user
# Registers handlers: GatewayUserTrade, GatewayUserPosition, etc.
```

**Step 20: Connect SignalR Market Hub**
```python
market_hub = MarketHubListener(
    jwt_token=account_tokens[primary_account_id],
    event_router=event_router
)

market_hub.setup_market_hub()
# Connects to wss://rtc.topstepx.com/hubs/market
# Registers handler: MarketQuote
```

**Step 21: Subscribe to Quotes for Open Positions**
```python
# For each open position, subscribe to real-time quotes
for position in state_manager.get_all_positions():
    market_hub.subscribe_to_contract(position['contract_id'])
    logger.debug(f"Subscribed to quotes for {position['contract_id']}")

# Example: If account has MNQ position, subscribe to MNQ quotes
```

**Step 22: Wait for SignalR Connections to Stabilize**
```python
# Give SignalR 2 seconds to establish connections
time.sleep(2)

# Verify connections established
if not user_hub.is_connected():
    raise Exception("User Hub connection failed")

if not market_hub.is_connected():
    raise Exception("Market Hub connection failed")

logger.info("SignalR connections established")
```

**Step 23: Verify Initial Events Received**
```python
# Optional: Wait for first position/quote events to verify data flow
# (Helps catch connection issues early)
```

---

### **Phase 6: Start Background Threads (Steps 24-29)**

**Step 24: Start Timer/Lockout Checker Thread**
```python
timer_thread = threading.Thread(
    target=timer_and_lockout_checker,
    daemon=True,
    name="TimerLockoutChecker"
)
timer_thread.start()

logger.info("Started timer/lockout checker thread")
```

**Step 25: Start Daily Reset Checker Thread**
```python
reset_thread = threading.Thread(
    target=daily_reset_checker,
    daemon=True,
    name="DailyResetChecker"
)
reset_thread.start()

logger.info("Started daily reset checker thread")
```

**Step 26: Start State Writer Thread**
```python
writer_thread = threading.Thread(
    target=state_writer,
    daemon=True,
    name="StateWriter"
)
writer_thread.start()

logger.info("Started state writer thread")
```

**Step 27: Start Token Refresh Thread**
```python
token_thread = threading.Thread(
    target=token_refresh_checker,
    daemon=True,
    name="TokenRefresh"
)
token_thread.start()

logger.info("Started token refresh thread")
```

**Step 28: Start WebSocket Server Thread**
```python
websocket_thread = threading.Thread(
    target=websocket_server_thread,
    daemon=True,
    name="WebSocketServer"
)
websocket_thread.start()

logger.info("Started WebSocket server thread (listening on localhost:8765)")
```

**Step 29: Log Startup Complete**
```python
logger.info("=" * 60)
logger.info("Risk Manager Daemon Started Successfully")
logger.info(f"Monitoring {len(accounts)} accounts")
logger.info(f"Active rules: {len([r for r in risk_config if r['enabled']])}")
logger.info(f"WebSocket server: ws://localhost:8765 (for Trader CLIs)")
logger.info("=" * 60)
```

---

## 🔄 Main Event Loop

### **Main Loop Structure**
```python
def run(self):
    """
    Main event loop - blocks on SignalR waiting for events.

    This is the main daemon thread - it just waits for SignalR events.
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

### **Event Processing Flow (Main Thread)**
```
1. SignalR event arrives (e.g., GatewayUserTrade)
   ↓
2. SignalR calls registered handler: _on_trade(payload)
   ↓
3. Handler calls: event_router.route_event("GatewayUserTrade", payload)
   ↓
4. EventRouter processes event:
   - Update state (MOD-005, MOD-008, etc.)
   - Check lockout
   - Route to rules
   - Execute enforcement if breach
   ↓
5. Return to waiting (main thread blocks again)
```

**Processing time:** < 10ms per event

---

## 🛑 Shutdown Sequence (Graceful)

### **Triggered By:**
- Admin CLI: "Stop Service"
- Windows Service Manager: Stop command
- Development mode: Ctrl+C

### **Shutdown Steps:**

**Step 1: Set Shutdown Flag**
```python
self.daemon_running = False
logger.info("Shutdown initiated...")
```

**Step 2: Stop Accepting New Events**
```python
# Close SignalR connections
user_hub.connection.stop()
market_hub.connection.stop()

logger.info("SignalR connections closed")
```

**Step 3: Stop WebSocket Server**
```python
# Stop WebSocket server (stop accepting new connections)
websocket_server.stop()

logger.info("WebSocket server stopped")
```

**Step 4: Wait for Background Threads to Finish**
```python
# daemon_running = False will stop all while loops
# Wait up to 10 seconds for threads to exit cleanly

threads = [timer_thread, reset_thread, writer_thread, token_thread, websocket_thread]
for thread in threads:
    thread.join(timeout=10)

    if thread.is_alive():
        logger.warning(f"Thread {thread.name} did not stop cleanly")

logger.info("Background threads stopped")
```

**Step 5: Flush All State to SQLite**
```python
# Force immediate write of all in-memory state
logger.info("Flushing state to database...")

with sqlite3.connect('data/state.db') as db:
    # Write positions
    state_manager.flush_positions_to_db(db)

    # Write orders
    state_manager.flush_orders_to_db(db)

    # Write contract cache
    contract_cache.flush_to_db(db)

    # Write enforcement logs
    flush_enforcement_logs(db)

    # Write lockouts (should already be synced, but double-check)
    lockout_manager.flush_to_db(db)

    # Write daily P&L (should already be synced, but double-check)
    pnl_tracker.flush_to_db(db)

    db.commit()

logger.info("State flushed to database")
```

**Step 6: Close Database Connection**
```python
db_connection.close()
logger.info("Database connection closed")
```

**Step 7: Log Shutdown Complete**
```python
logger.info("=" * 60)
logger.info("Risk Manager Daemon Stopped")
logger.info("=" * 60)
```

---

## 💥 Emergency Shutdown (Crash Recovery)

### **When Daemon Crashes:**
```python
def emergency_shutdown(self):
    """
    Emergency shutdown - daemon crashed.
    Try to save as much state as possible before exiting.
    """
    logger.critical("EMERGENCY SHUTDOWN - Attempting to save state")

    try:
        # Try to flush critical state
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
        # Exit with error code
        sys.exit(1)
```

### **On Restart After Crash:**
```
1. Daemon restarts (Windows Service auto-restart)
2. Startup sequence runs (28 steps)
3. Load persisted state from SQLite:
   ✅ Lockouts restored (MOD-002)
   ✅ Daily P&L restored (MOD-005)
   ✅ Positions restored (MOD-009) - may be slightly stale (< 5 seconds)
   ✅ Orders restored (MOD-009) - may be slightly stale (< 5 seconds)
   ❌ Quotes lost (start fresh - no big deal, quotes arrive every second)
   ❌ Timers lost (recalculated on events)
4. Resume monitoring
```

**Data loss on crash:** < 5 seconds of position/order updates (acceptable)

---

## 🏗️ Implementation Files

### **src/core/websocket_server.py** (~150 lines)

```python
"""
WebSocket server for broadcasting real-time events to Trader CLIs.
Runs in separate thread with asyncio event loop.
"""

import asyncio
import json
import logging
import websockets
from typing import Set, Dict, Any

logger = logging.getLogger(__name__)

class DaemonWebSocketServer:
    """
    WebSocket server that broadcasts daemon events to connected Trader CLIs.
    Runs on localhost:8765 (only accepts local connections).
    """

    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.loop = None
        self.server = None

    def start(self, loop: asyncio.AbstractEventLoop):
        """
        Start WebSocket server in the given asyncio event loop.
        Called from background thread.
        """
        self.loop = loop

        # Start WebSocket server
        start_server = websockets.serve(
            self._handler,
            self.host,
            self.port
        )

        self.server = loop.run_until_complete(start_server)

        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")

    async def _handler(self, websocket, path):
        """
        Handle new WebSocket connection from Trader CLI.
        """
        # Add client to set
        self.clients.add(websocket)
        client_addr = websocket.remote_address
        logger.info(f"Trader CLI connected: {client_addr}")

        try:
            # Keep connection alive (just wait for disconnect)
            await websocket.wait_closed()
        finally:
            # Remove client on disconnect
            self.clients.remove(websocket)
            logger.info(f"Trader CLI disconnected: {client_addr}")

    def broadcast(self, event: Dict[str, Any]):
        """
        Broadcast event to all connected Trader CLIs.
        Thread-safe - can be called from main daemon thread.

        Args:
            event: Event dictionary to broadcast
                   {'type': 'GatewayUserTrade', 'account_id': 123, 'data': {...}}
        """
        if not self.clients:
            return  # No clients connected

        message = json.dumps(event)

        if self.loop:
            # Schedule broadcast on asyncio event loop (thread-safe)
            asyncio.run_coroutine_threadsafe(
                self._broadcast_async(message),
                self.loop
            )

    async def _broadcast_async(self, message: str):
        """
        Async broadcast to all connected clients.
        Runs in asyncio event loop.
        """
        if not self.clients:
            return

        # Send to all clients concurrently
        await asyncio.gather(
            *[client.send(message) for client in self.clients],
            return_exceptions=True  # Don't fail if one client disconnected
        )

    def stop(self):
        """
        Stop WebSocket server (close all connections).
        Called during daemon shutdown.
        """
        if self.server:
            self.server.close()

            if self.loop:
                # Wait for server to close
                self.loop.run_until_complete(self.server.wait_closed())

        # Close all client connections
        if self.clients:
            close_tasks = [client.close() for client in self.clients]
            if self.loop:
                self.loop.run_until_complete(asyncio.gather(*close_tasks))

        logger.info("WebSocket server stopped")
```

---

### **src/core/daemon.py** (~250 lines)

```python
"""
Main daemon implementation.
Can run standalone (development) or via Windows Service (production).
"""

import sys
import time
import threading
import sqlite3
import logging
from datetime import datetime

class RiskManagerDaemon:
    """
    Main daemon class - manages startup, event loop, shutdown.
    """

    def __init__(self):
        self.daemon_running = False

        # Modules (initialized in start())
        self.state_manager = None
        self.pnl_tracker = None
        self.quote_tracker = None
        self.contract_cache = None
        self.trade_counter = None
        self.lockout_manager = None
        self.timer_manager = None
        self.reset_scheduler = None

        # API connections
        self.user_hub = None
        self.market_hub = None
        self.rest_client = None

        # Background threads
        self.timer_thread = None
        self.reset_thread = None
        self.writer_thread = None
        self.token_thread = None
        self.websocket_thread = None

        # WebSocket server
        self.websocket_server = None

        # Database
        self.db_connection = None

        # Configuration
        self.accounts = None
        self.risk_config = None
        self.account_tokens = {}

    def start(self):
        """
        Execute 28-step startup sequence.
        Raises exception if startup fails.
        """
        logger.info("Starting Risk Manager Daemon...")

        # PHASE 1: Configuration (Steps 1-3)
        self._load_configuration()

        # PHASE 2: Database (Steps 4-6)
        self._initialize_database()

        # PHASE 3: Modules (Steps 7-15)
        self._initialize_modules()

        # PHASE 4: Authentication (Steps 16-18)
        self._authenticate_accounts()

        # PHASE 5: SignalR (Steps 19-23)
        self._connect_signalr()

        # PHASE 6: Background Threads (Steps 24-28)
        self._start_background_threads()

        self.daemon_running = True

        logger.info("Daemon started successfully")

    def run(self):
        """
        Main event loop - blocks on SignalR.
        """
        try:
            # Block here waiting for events
            self.user_hub.connection.start()

        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
            self.shutdown()

        except Exception as e:
            logger.critical(f"Daemon crashed: {e}", exc_info=True)
            self.emergency_shutdown()

    def shutdown(self):
        """
        Graceful shutdown sequence.
        """
        logger.info("Shutting down daemon...")

        # Stop accepting events
        self.daemon_running = False

        # Close SignalR
        self.user_hub.connection.stop()
        self.market_hub.connection.stop()

        # Stop WebSocket server
        self.websocket_server.stop()

        # Wait for background threads
        for thread in [self.timer_thread, self.reset_thread,
                       self.writer_thread, self.token_thread, self.websocket_thread]:
            thread.join(timeout=10)

        # Flush state to SQLite
        self._flush_all_state()

        # Close database
        self.db_connection.close()

        logger.info("Daemon stopped")

    def emergency_shutdown(self):
        """
        Emergency shutdown - save critical state.
        """
        logger.critical("EMERGENCY SHUTDOWN")

        try:
            with sqlite3.connect('data/state.db') as db:
                self.lockout_manager.flush_to_db(db)
                self.pnl_tracker.flush_to_db(db)
                db.commit()
        except:
            pass

        sys.exit(1)

    # Internal methods (implementation details)
    def _load_configuration(self):
        """Steps 1-3: Load and validate config"""
        # ... implementation ...

    def _initialize_database(self):
        """Steps 4-6: Connect to SQLite, create tables"""
        # ... implementation ...

    def _initialize_modules(self):
        """Steps 7-15: Initialize all 9 modules, load state"""
        # ... implementation ...

    def _authenticate_accounts(self):
        """Steps 16-18: Get JWT tokens for all accounts"""
        # ... implementation ...

    def _connect_signalr(self):
        """Steps 19-23: Connect SignalR hubs, subscribe to quotes"""
        # ... implementation ...

    def _start_background_threads(self):
        """Steps 24-29: Start 5 background threads + WebSocket server"""
        # ... implementation ...

    def _flush_all_state(self):
        """Flush all in-memory state to SQLite"""
        # ... implementation ...


# Development mode entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--dev-mode', action='store_true',
                        help='Run in development mode (console)')
    args = parser.parse_args()

    # Setup logging to console
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    # Create and start daemon
    daemon = RiskManagerDaemon()
    daemon.start()
    daemon.run()
```

---

### **src/service/windows_service.py** (~150 lines)

```python
"""
Windows Service wrapper for daemon.
Allows daemon to run as Windows Service (auto-start, admin-only control).
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.daemon import RiskManagerDaemon

class RiskManagerService(win32serviceutil.ServiceFramework):
    """
    Windows Service wrapper for Risk Manager Daemon.
    """

    # Service configuration
    _svc_name_ = "RiskManagerDaemon"
    _svc_display_name_ = "Risk Manager Daemon"
    _svc_description_ = "Trading risk management daemon - monitors accounts and enforces risk rules"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)

        # Create stop event (used to signal shutdown)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

        # Create daemon instance
        self.daemon = RiskManagerDaemon()

        # Setup logging to file (not console)
        logging.basicConfig(
            filename='logs/daemon.log',
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s'
        )

    def SvcStop(self):
        """
        Called when Windows Service Manager stops the service.
        (Admin runs: net stop RiskManagerDaemon)
        """
        # Report status
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        # Signal stop event
        win32event.SetEvent(self.stop_event)

        # Shutdown daemon
        self.daemon.shutdown()

        # Report stopped
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )

    def SvcDoRun(self):
        """
        Called when Windows Service Manager starts the service.
        (Admin runs: net start RiskManagerDaemon)
        """
        # Report status
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)

        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )

        # Report running
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)

        try:
            # Start daemon
            self.daemon.start()

            # Run daemon (blocks here until stopped)
            self.daemon.run()

        except Exception as e:
            # Log error
            servicemanager.LogErrorMsg(f"Daemon crashed: {e}")

            # Emergency shutdown
            self.daemon.emergency_shutdown()


# Command-line interface for installing/removing service
if __name__ == '__main__':
    """
    Usage:
        python windows_service.py install   # Install service
        python windows_service.py start     # Start service
        python windows_service.py stop      # Stop service
        python windows_service.py remove    # Uninstall service
    """
    win32serviceutil.HandleCommandLine(RiskManagerService)
```

---

### **src/cli/admin/service_control.py** (~200 lines)

```python
"""
Admin CLI service control functions.
Called by admin menu to manage Windows Service.
"""

import win32serviceutil
import win32service
import win32api
import subprocess
import sys
import time

def check_admin_privileges():
    """
    Check if running with admin privileges.
    Returns True if admin, False otherwise.
    """
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def install_service():
    """
    Install Risk Manager as Windows Service.
    Requires admin privileges.
    """
    if not check_admin_privileges():
        print("❌ Admin privileges required to install service")
        print("   Right-click and 'Run as Administrator'")
        return False

    try:
        print("Installing Risk Manager Windows Service...")

        # Get Python executable and service script path
        python_exe = sys.executable
        service_script = "src/service/windows_service.py"

        # Install service
        subprocess.run(
            [python_exe, service_script, "install"],
            check=True
        )

        # Configure service to auto-start on boot
        win32serviceutil.ChangeServiceConfig(
            None,  # local machine
            "RiskManagerDaemon",
            startType=win32service.SERVICE_AUTO_START,
            description="Trading risk management daemon - monitors accounts and enforces risk rules"
        )

        print("✅ Service installed successfully")
        print("   Service will auto-start on boot")
        return True

    except Exception as e:
        print(f"❌ Failed to install service: {e}")
        return False

def start_service():
    """
    Start Risk Manager Windows Service.
    Requires admin privileges.
    """
    if not check_admin_privileges():
        print("❌ Admin privileges required to start service")
        return False

    try:
        print("Starting Risk Manager service...")

        win32serviceutil.StartService("RiskManagerDaemon")

        # Wait for service to start
        time.sleep(2)

        # Check status
        status = get_service_status()
        if status == "RUNNING":
            print("✅ Service started successfully")
            return True
        else:
            print(f"⚠️ Service status: {status}")
            return False

    except Exception as e:
        print(f"❌ Failed to start service: {e}")
        return False

def stop_service():
    """
    Stop Risk Manager Windows Service.
    Requires admin privileges.
    """
    if not check_admin_privileges():
        print("❌ Admin privileges required to stop service")
        return False

    try:
        print("Stopping Risk Manager service...")

        win32serviceutil.StopService("RiskManagerDaemon")

        # Wait for service to stop
        time.sleep(2)

        # Check status
        status = get_service_status()
        if status == "STOPPED":
            print("✅ Service stopped successfully")
            return True
        else:
            print(f"⚠️ Service status: {status}")
            return False

    except Exception as e:
        print(f"❌ Failed to stop service: {e}")
        return False

def restart_service():
    """
    Restart Risk Manager Windows Service.
    Requires admin privileges.
    """
    if not check_admin_privileges():
        print("❌ Admin privileges required to restart service")
        return False

    print("Restarting Risk Manager service...")

    if stop_service():
        time.sleep(2)
        return start_service()
    else:
        return False

def uninstall_service():
    """
    Uninstall Risk Manager Windows Service.
    Requires admin privileges.
    """
    if not check_admin_privileges():
        print("❌ Admin privileges required to uninstall service")
        return False

    try:
        # Stop service first
        print("Stopping service before uninstall...")
        try:
            win32serviceutil.StopService("RiskManagerDaemon")
            time.sleep(2)
        except:
            pass  # Service might not be running

        print("Uninstalling Risk Manager Windows Service...")

        # Get Python executable and service script path
        python_exe = sys.executable
        service_script = "src/service/windows_service.py"

        # Uninstall service
        subprocess.run(
            [python_exe, service_script, "remove"],
            check=True
        )

        print("✅ Service uninstalled successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to uninstall service: {e}")
        return False

def get_service_status():
    """
    Get current status of Risk Manager Windows Service.

    Returns:
        str: "RUNNING", "STOPPED", "START_PENDING", "STOP_PENDING",
             "PAUSED", "NOT_INSTALLED"
    """
    try:
        status = win32serviceutil.QueryServiceStatus("RiskManagerDaemon")

        status_map = {
            win32service.SERVICE_STOPPED: "STOPPED",
            win32service.SERVICE_START_PENDING: "START_PENDING",
            win32service.SERVICE_STOP_PENDING: "STOP_PENDING",
            win32service.SERVICE_RUNNING: "RUNNING",
            win32service.SERVICE_CONTINUE_PENDING: "CONTINUE_PENDING",
            win32service.SERVICE_PAUSE_PENDING: "PAUSE_PENDING",
            win32service.SERVICE_PAUSED: "PAUSED"
        }

        return status_map.get(status[1], "UNKNOWN")

    except Exception:
        return "NOT_INSTALLED"

def show_service_menu():
    """
    Show service control menu (called from admin CLI).
    """
    while True:
        print("\n" + "=" * 60)
        print("Risk Manager - Service Control")
        print("=" * 60)

        # Show current status
        status = get_service_status()
        status_color = {
            "RUNNING": "🟢",
            "STOPPED": "🔴",
            "NOT_INSTALLED": "⚪",
        }.get(status, "🟡")

        print(f"\nService Status: {status_color} {status}")

        print("\n1) Install Service (one-time setup)")
        print("2) Start Service")
        print("3) Stop Service")
        print("4) Restart Service")
        print("5) Uninstall Service")
        print("6) Back to Main Menu")

        choice = input("\nSelect option: ")

        if choice == "1":
            install_service()
        elif choice == "2":
            start_service()
        elif choice == "3":
            stop_service()
        elif choice == "4":
            restart_service()
        elif choice == "5":
            if input("Are you sure? (yes/no): ").lower() == "yes":
                uninstall_service()
        elif choice == "6":
            break

        input("\nPress Enter to continue...")
```

---

## 📊 Performance Characteristics

### **Startup Time:**
- **Cold start (first time):** ~5-10 seconds
  - Load config: ~100ms
  - Initialize SQLite: ~200ms
  - Load state from database: ~500ms
  - Authenticate with TopstepX: ~2-3 seconds (network)
  - Connect SignalR hubs: ~2-3 seconds (network)
  - Start threads: ~100ms

- **Warm start (after crash):** ~5-10 seconds (same as cold start)

### **Memory Usage:**
- Daemon process: ~50-100 MB RAM
- SQLite database: ~100-500 KB on disk
- In-memory state: ~27 KB (see STATE_MANAGEMENT.md)

### **CPU Usage:**
- **Idle (waiting for events):** < 1% CPU
- **Processing events:** < 5% CPU (spikes during events)
- **Background threads:** < 1% CPU each

### **Disk I/O:**
- SQLite writes: Every 5 seconds (batched)
- Log files: ~1 MB per day

---

## 🚨 Error Handling & Recovery

### **1. SignalR Disconnection**
```python
# Auto-reconnect policy (in SignalR setup)
reconnect_policy = {
    "type": "raw",
    "keep_alive_interval": 10,
    "reconnect_interval": 5,
    "max_reconnect_attempts": 5
}

# If all reconnect attempts fail:
logger.critical("SignalR connection lost - restarting daemon")
emergency_shutdown()
# Windows Service will auto-restart daemon
```

### **2. TopstepX API Down**
```python
# Retry logic in enforcement actions
def close_all_positions(account_id):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # REST API call
            return True
        except:
            if attempt < max_retries - 1:
                time.sleep(2)

    # All retries failed
    logger.critical("ENFORCEMENT FAILED - API unavailable")
    # Continue monitoring (don't crash daemon)
    return False
```

### **3. Database Corruption**
```python
# SQLite corruption detection
try:
    db.execute("PRAGMA integrity_check")
except:
    logger.critical("Database corrupted - creating backup and rebuilding")

    # Backup corrupted DB
    shutil.copy('data/state.db', 'data/state.db.corrupted')

    # Rebuild database
    create_tables(db)

    # Re-fetch state from TopstepX
    sync_state_from_topstepx()
```

### **4. Configuration Error**
```python
# Validate config on startup
try:
    validate_config(accounts, risk_config)
except ConfigError as e:
    logger.critical(f"Invalid configuration: {e}")
    print(f"❌ Configuration error: {e}")
    print("   Fix config/accounts.yaml or config/risk_config.yaml")
    sys.exit(1)
```

### **5. Out of Memory**
```python
# Monitor memory usage
import psutil

def check_memory():
    process = psutil.Process()
    mem_mb = process.memory_info().rss / 1024 / 1024

    if mem_mb > 500:  # More than 500 MB
        logger.warning(f"High memory usage: {mem_mb:.0f} MB")

        # Clear caches
        contract_cache.clear_old_entries()
        trade_counter.clear_old_trades()
```

---

## 📝 Logging Strategy

### **Log Files:**
```
logs/
├── daemon.log          # Main daemon events (startup, shutdown, errors)
├── enforcement.log     # All enforcement actions (positions closed, lockouts set)
├── api.log            # SignalR events, REST API calls
└── error.log          # Errors only (extracted from daemon.log)
```

### **Log Levels:**
```python
# daemon.log
logger.info("Daemon started successfully")           # INFO
logger.warning("High memory usage: 450 MB")          # WARNING
logger.error("Failed to authenticate account 123")   # ERROR
logger.critical("Database corrupted - rebuilding")   # CRITICAL

# enforcement.log (INFO level only)
logger.info("CLOSE_ALL_POSITIONS: account=123, reason=MaxContracts breach")
logger.info("SET_LOCKOUT: account=123, until=2025-01-17 17:00, reason=Daily loss limit")

# api.log (DEBUG level)
logger.debug("SignalR event: GatewayUserTrade - account=123, pnl=-50")
logger.debug("REST API call: POST /api/Position/closeContract")
```

### **Log Rotation:**
```python
# Rotate logs daily, keep 30 days
from logging.handlers import TimedRotatingFileHandler

handler = TimedRotatingFileHandler(
    filename='logs/daemon.log',
    when='midnight',
    interval=1,
    backupCount=30
)
```

---

## 🧪 Testing Daemon

### **1. Unit Tests (Startup/Shutdown)**
```python
def test_daemon_startup():
    """Test 28-step startup sequence."""
    daemon = RiskManagerDaemon()
    daemon.start()

    # Verify all modules initialized
    assert daemon.state_manager is not None
    assert daemon.lockout_manager is not None
    # ... etc ...

    daemon.shutdown()

def test_daemon_shutdown():
    """Test graceful shutdown."""
    daemon = RiskManagerDaemon()
    daemon.start()

    # Shutdown
    daemon.shutdown()

    # Verify all threads stopped
    assert not daemon.timer_thread.is_alive()
    # ... etc ...
```

### **2. Integration Tests (End-to-End)**
```python
def test_daemon_processes_trade_event():
    """Test complete flow: Event → State → Rule → Enforcement."""
    daemon = RiskManagerDaemon()
    daemon.start()

    # Simulate trade event
    daemon.event_router.route_event("GatewayUserTrade", {
        'accountId': 123,
        'profitAndLoss': -600
    })

    # Verify lockout set
    assert daemon.lockout_manager.is_locked_out(123)

    daemon.shutdown()
```

### **3. Crash Recovery Tests**
```python
def test_daemon_recovers_from_crash():
    """Test state recovery after crash."""
    daemon = RiskManagerDaemon()
    daemon.start()

    # Set lockout
    daemon.lockout_manager.set_lockout(123, "Test", datetime.now())

    # Simulate crash (kill daemon)
    daemon.emergency_shutdown()

    # Restart daemon
    daemon2 = RiskManagerDaemon()
    daemon2.start()

    # Verify lockout restored
    assert daemon2.lockout_manager.is_locked_out(123)

    daemon2.shutdown()
```

---

## 📝 Summary

**Key Points:**

1. **One daemon monitors all accounts** (from accounts.yaml)
2. **Runs as Windows Service** (auto-start, admin-only control)
3. **29-step startup sequence** (config → database → modules → auth → SignalR → threads)
4. **6 threads total** (1 main event loop + 5 background)
   - Thread 1: SignalR event loop (main)
   - Thread 2: Timer/lockout checker (every 1 second)
   - Thread 3: Daily reset checker (every 10 seconds)
   - Thread 4: State writer (every 5 seconds)
   - Thread 5: Token refresh (every 1 hour)
   - Thread 6: WebSocket server (asyncio event loop for Trader CLIs)
5. **Real-time broadcasting** (WebSocket server broadcasts events to Trader CLIs)
6. **Graceful shutdown** (flush state, stop threads, close connections, stop WebSocket server)
7. **Crash recovery** (load state from SQLite, resume monitoring)
8. **Hybrid mode** (Windows Service for production, console for development)
9. **Admin CLI controls service** (install, start, stop, restart, uninstall)

**Files to Implement:**
- `src/core/websocket_server.py` (~150 lines)
- `src/core/daemon.py` (~250 lines)
- `src/service/windows_service.py` (~150 lines)
- `src/cli/admin/service_control.py` (~200 lines)

**Total: ~750 lines** (WebSocket server + daemon core + Windows Service wrapper + Admin controls)

---

**Next Step:** Update TRADER_CLI_SPEC.md, DAEMON_ENDPOINTS.md, STATE_OBJECTS.md for new modules (MOD-005 through MOD-009)
