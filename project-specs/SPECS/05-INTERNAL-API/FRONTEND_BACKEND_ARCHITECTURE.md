---
doc_id: FE-BE-001
version: 1.0
last_updated: 2025-10-21
dependencies: [DAEMON-001, DB-SCHEMA-001, STATE-001]
---

# Frontend-Backend Communication Architecture

**Purpose:** Complete design of how Admin CLI and Trader CLI communicate with the daemon

**File Coverage:** Communication patterns, data access, UI architecture

---

## 🎯 Architecture Overview

### **Communication Model: Real-Time WebSocket + Direct Access**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DAEMON (Windows Service)                           │
│  - Runs 24/7 monitoring accounts                                        │
│  - Enforces risk rules in real-time                                     │
│  - Writes state to SQLite (data/state.db)                               │
│  - Writes logs to logs/ directory                                       │
│  - Runs WebSocket server (localhost:8765) ⭐ NEW                        │
│  - Broadcasts events to connected Trader CLIs ⭐ NEW                    │
└─────────────┬────────────────────┬──────────────────────────────────────┘
              │                    │
              │ Writes             │ Broadcasts events
              ▼                    ▼
       ┌──────────────┐     ┌──────────────────┐
       │ data/        │     │ WebSocket Server │
       │   state.db   │     │ localhost:8765   │
       │ (SQLite)     │     │ (Real-time push) │
       └──────┬───────┘     └────────┬─────────┘
              │                      │
              │ Reads                │ Subscribes (real-time)
              │                      │
              ▼                      ▼
       ┌────────────────────────────────────┐
       │        TRADER CLI                  │
       │  - WebSocket client (real-time)    │
       │  - SQLite queries (initial state)  │
       │  - Log viewer                      │
       └────────────────────────────────────┘


       ┌────────────────────────────────────┐
       │         ADMIN CLI                  │
       │  - Service control (win32service)  │
       │  - Config editing (YAML files)     │
       │  - No real-time dashboard          │
       └──────────┬─────────────────────────┘
                  │
                  │ Controls
                  ▼
           ┌──────────────────┐
           │ Windows Service  │
           │ Manager API      │
           └──────┬───────────┘
                  │
                  │ Start/Stop/Restart
                  ▼
           ┌──────────────────┐
           │ Config Files     │
           │ accounts.yaml    │
           │ risk_config.yaml │
           └──────────────────┘
```

---

## 📊 Communication Patterns

### **Pattern 1: Trader CLI → Daemon (Real-Time WebSocket)**

**Method:** WebSocket subscription for real-time event push

**Connection:** `ws://localhost:8765`

**Event Types Broadcasted:**
```python
# Trade executed - P&L updated
{
  'type': 'GatewayUserTrade',
  'account_id': 123,
  'data': {
    'id': 101112,
    'contractId': 'CON.F.US.MNQ.U25',
    'profitAndLoss': -45.50,
    'timestamp': '2025-01-17T14:45:15Z'
  }
}

# Position changed
{
  'type': 'GatewayUserPosition',
  'account_id': 123,
  'data': {
    'id': 456,
    'contractId': 'CON.F.US.MNQ.U25',
    'type': 1,  # Long
    'size': 3,
    'averagePrice': 21000.5
  }
}

# Quote updated (real-time price)
{
  'type': 'MarketQuote',
  'account_id': 123,
  'data': {
    'contractId': 'CON.F.US.MNQ.U25',
    'bid': 21000.25,
    'ask': 21000.50,
    'last': 21000.50
  }
}

# Lockout set
{
  'type': 'lockout_set',
  'account_id': 123,
  'data': {
    'reason': 'Daily loss limit hit',
    'locked_until': '2025-01-17T17:00:00Z',
    'rule_id': 'RULE-003'
  }
}

# Enforcement action executed
{
  'type': 'enforcement_action',
  'account_id': 123,
  'data': {
    'action': 'CLOSE_ALL_POSITIONS',
    'reason': 'MaxContracts breach (6 > 5)',
    'rule_id': 'RULE-001',
    'timestamp': '2025-01-17T14:45:15Z'
  }
}
```

**Why this pattern:**
- ✅ **True real-time**: < 10ms latency from daemon event to trader UI
- ✅ **Event-driven**: Trader receives same events that PNL Tracker module sees
- ✅ **Efficient**: Only pushes when state changes (no polling)
- ✅ **Scalable**: Can support multiple Trader CLIs connected simultaneously
- ✅ **Secure**: Read-only broadcast (Trader CLI can't send commands)

---

### **Pattern 2: Admin CLI → Daemon (Control)**

**Method:** Windows Service API + Config file editing

**Actions:**

**Service Control:**
```python
import win32serviceutil

# Start daemon
win32serviceutil.StartService("RiskManagerDaemon")

# Stop daemon
win32serviceutil.StopService("RiskManagerDaemon")

# Restart daemon
win32serviceutil.RestartService("RiskManagerDaemon")

# Get status
status = win32serviceutil.QueryServiceStatus("RiskManagerDaemon")
```

**Config Management:**
```python
# Edit config/risk_config.yaml
config = load_yaml("config/risk_config.yaml")
config['max_contracts']['limit'] = 10
save_yaml("config/risk_config.yaml", config)

# Restart daemon to apply changes
win32serviceutil.RestartService("RiskManagerDaemon")
```

**Why this pattern:**
- ✅ Standard: Windows Service Manager is the standard way
- ✅ Secure: Requires admin privileges
- ✅ Simple: No custom IPC protocol needed
- ✅ Reliable: Windows handles service lifecycle

---

### **Pattern 3: Both CLIs → Logs (Read-Only)**

**Method:** Direct file reads (tail -f pattern)

**Log Files:**
```
logs/
├── daemon.log          # General daemon events
├── enforcement.log     # All enforcement actions
├── api.log            # SignalR/REST API events
└── error.log          # Errors only
```

**Read Pattern:**
```python
# Tail last 50 lines of enforcement.log
with open('logs/enforcement.log', 'r') as f:
    lines = f.readlines()
    last_50 = lines[-50:]
    for line in last_50:
        print(line)
```

**Why this pattern:**
- ✅ Simple: Just file reads
- ✅ Fast: Text file reads are instant
- ✅ Standard: Every CLI has log viewer
- ✅ No daemon dependency: Can view logs even if daemon stopped

---

## 🔐 Security Model

### **Trader CLI (No Privileges)**
```
Trader can:
✅ Read SQLite database (read-only)
✅ Read log files (read-only)
✅ View current state
✅ See enforcement actions

Trader CANNOT:
❌ Modify config files
❌ Start/stop daemon
❌ Bypass lockouts
❌ Change rules
❌ Write to database
```

### **Admin CLI (Requires Admin Privileges)**
```
Admin can:
✅ All trader capabilities
✅ Start/stop/restart daemon
✅ Modify config files (accounts.yaml, risk_config.yaml)
✅ Install/uninstall Windows Service
✅ Add/remove accounts
✅ Enable/disable rules
✅ Change rule parameters

Admin requires:
🔒 Password authentication (on CLI startup)
🔒 Windows admin privileges (for service control)
```

**Implementation:**
```python
# Admin CLI entry point
def admin_main():
    # Check Windows admin privileges
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("❌ Please run as Administrator")
        sys.exit(1)

    # Password authentication
    if not authenticate_admin():
        print("❌ Invalid password")
        sys.exit(1)

    # Show admin menu
    admin_menu()
```

---

## 🔌 WebSocket Implementation

### **Daemon: WebSocket Server**

**File:** `src/core/websocket_server.py` (~150 lines)

```python
"""
WebSocket server for broadcasting events to Trader CLIs.
Runs as Thread 6 in daemon.
"""

import asyncio
import websockets
import json
import threading
from typing import Set
import logging

logger = logging.getLogger(__name__)

class DaemonWebSocketServer:
    """Broadcasts real-time events to connected Trader CLIs"""

    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.loop = None
        self.server = None

    async def handler(self, websocket, path):
        """Handle new Trader CLI connection"""
        self.clients.add(websocket)
        client_addr = websocket.remote_address
        logger.info(f"Trader CLI connected: {client_addr}")

        try:
            # Keep connection alive, wait for client to disconnect
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            logger.info(f"Trader CLI disconnected: {client_addr}")

    def broadcast(self, event: dict):
        """
        Broadcast event to all connected Trader CLIs.
        Called from daemon's event router (main thread).
        Thread-safe - queues event to event loop.
        """
        if not self.clients:
            return  # No clients connected

        message = json.dumps(event)

        # Schedule broadcast in event loop (thread-safe)
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self._broadcast_async(message),
                self.loop
            )

    async def _broadcast_async(self, message: str):
        """Actually broadcast to clients (runs in event loop)"""
        if self.clients:
            # Send to all clients concurrently
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True  # Don't fail if one client errors
            )

    def start(self):
        """
        Start WebSocket server in background thread.
        Called during daemon startup (Thread 6).
        """
        # Create new event loop for this thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Start WebSocket server
        start_server = websockets.serve(
            self.handler,
            self.host,
            self.port
        )

        self.server = self.loop.run_until_complete(start_server)
        logger.info(f"WebSocket server started on {self.host}:{self.port}")

        # Run event loop (blocks until stopped)
        self.loop.run_forever()

    def stop(self):
        """Stop WebSocket server (called during daemon shutdown)"""
        if self.server:
            self.server.close()
            self.loop.run_until_complete(self.server.wait_closed())

        if self.loop:
            self.loop.stop()
```

**Integration with Event Router:**

```python
# In src/core/event_router.py

class EventRouter:
    def __init__(self, ..., websocket_server):
        # ... existing init ...
        self.websocket_server = websocket_server

    def route_event(self, event_type: str, payload: dict):
        """Route event AND broadcast to Trader CLIs"""

        # STEP 1: Update state (existing)
        self._update_state(event_type, payload)

        # STEP 2: Broadcast to Trader CLIs ⭐ NEW
        self.websocket_server.broadcast({
            'type': event_type,
            'account_id': payload.get('accountId'),
            'data': payload
        })

        # STEP 3: Check lockout (existing)
        if self.lockout_manager.is_locked_out(account_id):
            return

        # STEP 4: Route to rules (existing)
        self._route_to_rules(event_type, payload)
```

**Broadcasting Enforcement Actions:**

```python
# In src/enforcement/enforcement_engine.py

def execute_enforcement(action, account_id):
    """Execute enforcement and broadcast to Trader CLIs"""

    # Execute enforcement (existing)
    if action.type == "CLOSE_ALL_POSITIONS":
        actions.close_all_positions(account_id)

    # Broadcast to Trader CLIs ⭐ NEW
    websocket_server.broadcast({
        'type': 'enforcement_action',
        'account_id': account_id,
        'data': {
            'action': action.type,
            'reason': action.reason,
            'rule_id': action.rule_id,
            'timestamp': datetime.now().isoformat()
        }
    })
```

**Broadcasting Lockouts:**

```python
# In src/state/lockout_manager.py

def set_lockout(self, account_id, reason, until, rule_id):
    """Set lockout and broadcast to Trader CLIs"""

    # Set lockout (existing)
    self.lockouts[account_id] = {
        'is_locked': True,
        'reason': reason,
        'locked_until': until,
        'rule_id': rule_id
    }

    # Persist to SQLite (existing)
    self._persist_to_db(account_id)

    # Broadcast to Trader CLIs ⭐ NEW
    self.websocket_server.broadcast({
        'type': 'lockout_set',
        'account_id': account_id,
        'data': {
            'reason': reason,
            'locked_until': until.isoformat(),
            'rule_id': rule_id
        }
    })
```

---

### **Trader CLI: WebSocket Client**

**File:** `src/cli/trader/realtime_client.py` (~200 lines)

```python
"""
WebSocket client for receiving real-time updates from daemon.
Runs as Thread 1 in Trader CLI.
"""

import websocket
import json
import threading
import logging
from typing import Callable

logger = logging.getLogger(__name__)

class TraderRealtimeClient:
    """Receives real-time events from daemon via WebSocket"""

    def __init__(self, account_id: int, event_callback: Callable):
        """
        Args:
            account_id: Account to filter events for
            event_callback: Function called when event received
                            event_callback(event_type, data)
        """
        self.account_id = account_id
        self.event_callback = event_callback
        self.ws = None
        self.connected = False

    def connect(self):
        """Connect to daemon WebSocket server"""
        self.ws = websocket.WebSocketApp(
            "ws://localhost:8765",
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )

        # Run in background thread
        thread = threading.Thread(
            target=self.ws.run_forever,
            daemon=True,
            name="WebSocketClient"
        )
        thread.start()

        logger.info("Connecting to daemon WebSocket...")

    def _on_open(self, ws):
        """Called when connection established"""
        self.connected = True
        logger.info("Connected to daemon WebSocket")

        # Notify UI (connection status changed)
        self.event_callback('connection_status', {'connected': True})

    def _on_message(self, ws, message):
        """Called when event received from daemon"""
        try:
            event = json.loads(message)

            # Filter by account_id
            if event.get('account_id') == self.account_id:
                # Forward to UI callback
                self.event_callback(event['type'], event['data'])

        except Exception as e:
            logger.error(f"Error processing event: {e}")

    def _on_error(self, ws, error):
        """Called on error"""
        logger.error(f"WebSocket error: {error}")
        self.connected = False

    def _on_close(self, ws, close_status_code, close_msg):
        """Called when connection closed"""
        self.connected = False
        logger.warning("Disconnected from daemon WebSocket")

        # Notify UI (connection status changed)
        self.event_callback('connection_status', {'connected': False})

    def disconnect(self):
        """Disconnect from daemon"""
        if self.ws:
            self.ws.close()
```

**Trader CLI Integration:**

```python
# In src/cli/trader/trader_main.py

class TraderUI:
    """Trader CLI with real-time updates"""

    def __init__(self, account_id):
        self.account_id = account_id
        self.data_access = TraderDataAccess()

        # Initialize WebSocket client
        self.realtime_client = TraderRealtimeClient(
            account_id=account_id,
            event_callback=self.on_realtime_event
        )

        # Current state (updated in real-time)
        self.current_pnl = 0.0
        self.positions = []
        self.lockout = None
        self.connection_status = False

    def start(self):
        """Start Trader CLI"""
        # Load initial state from SQLite
        self.current_pnl = self.data_access.get_daily_pnl(self.account_id)
        self.positions = self.data_access.get_positions(self.account_id)
        self.lockout = self.data_access.get_lockout_status(self.account_id)

        # Connect to daemon WebSocket for real-time updates
        self.realtime_client.connect()

        # Render initial UI
        self.render_ui()

        # Enter UI loop (handles user input)
        self.ui_loop()

    def on_realtime_event(self, event_type, data):
        """Handle real-time event from daemon"""

        if event_type == 'GatewayUserTrade':
            # Trade executed - update P&L
            self.current_pnl = data.get('realized_pnl_total', self.current_pnl)
            self.flash_message(f"Trade executed: P&L {data['profitAndLoss']:+.2f}")
            self.render_ui()

        elif event_type == 'GatewayUserPosition':
            # Position changed - update positions list
            self._update_position_in_list(data)
            self.render_ui()

        elif event_type == 'MarketQuote':
            # Quote updated - update quote display
            self._update_quote_display(data)
            # Note: Don't re-render entire UI on every quote (too frequent)
            # Just update quote section

        elif event_type == 'lockout_set':
            # Lockout set - flash alert
            self.lockout = data
            self.flash_alert(f"⚠️ LOCKOUT: {data['reason']}")
            self.render_ui()

        elif event_type == 'enforcement_action':
            # Enforcement action - flash alert
            self.flash_alert(f"⚠️ {data['action']}: {data['reason']}")
            self.render_ui()

        elif event_type == 'connection_status':
            # Connection status changed
            self.connection_status = data['connected']
            if not data['connected']:
                self.flash_warning("⚠️ Disconnected from daemon")
            self.render_ui()
```

---

## 📁 Data Access Patterns

### **Trader CLI Data Layer**

**File:** `src/cli/trader/data_access.py`

**Purpose:** Reusable functions for querying SQLite

```python
import sqlite3
from typing import List, Dict, Optional
from datetime import date

class TraderDataAccess:
    """Data access layer for Trader CLI (read-only)"""

    def __init__(self, db_path: str = "data/state.db"):
        self.db_path = db_path

    def _query(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute SELECT query and return results as list of dicts"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_lockout_status(self, account_id: int) -> Optional[Dict]:
        """Get current lockout status for account"""
        sql = """
            SELECT is_locked, reason, locked_until, rule_id
            FROM lockouts
            WHERE account_id = ? AND is_locked = 1
        """
        results = self._query(sql, (account_id,))
        return results[0] if results else None

    def get_daily_pnl(self, account_id: int) -> float:
        """Get today's realized P&L"""
        sql = """
            SELECT realized_pnl
            FROM daily_pnl
            WHERE account_id = ? AND date = ?
        """
        results = self._query(sql, (account_id, date.today()))
        return results[0]['realized_pnl'] if results else 0.0

    def get_positions(self, account_id: int) -> List[Dict]:
        """Get all open positions"""
        sql = """
            SELECT id, contract_id, type, size, average_price
            FROM positions
            WHERE account_id = ?
            ORDER BY created_at DESC
        """
        return self._query(sql, (account_id,))

    def get_orders(self, account_id: int) -> List[Dict]:
        """Get all open orders"""
        sql = """
            SELECT id, contract_id, type, side, size, limit_price, stop_price, state
            FROM orders
            WHERE account_id = ?
            ORDER BY created_at DESC
        """
        return self._query(sql, (account_id,))

    def get_enforcement_actions(self, account_id: int, limit: int = 20) -> List[Dict]:
        """Get recent enforcement actions"""
        sql = """
            SELECT timestamp, rule_id, action, reason, success
            FROM enforcement_log
            WHERE account_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        return self._query(sql, (account_id, limit))

    def get_trade_count(self, account_id: int) -> int:
        """Get today's trade count"""
        sql = """
            SELECT COUNT(*) as count
            FROM trade_history
            WHERE account_id = ? AND timestamp >= date('now')
        """
        result = self._query(sql, (account_id,))
        return result[0]['count'] if result else 0

    def get_daemon_status(self) -> Dict:
        """Get daemon status from last heartbeat"""
        # Check if database is accessible (daemon is writing to it)
        try:
            sql = "SELECT MAX(updated_at) as last_update FROM lockouts"
            result = self._query(sql)
            if result and result[0]['last_update']:
                return {
                    'status': 'RUNNING',
                    'last_update': result[0]['last_update']
                }
            else:
                return {'status': 'STOPPED', 'last_update': None}
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}

    def get_contract_info(self, contract_id: str) -> Optional[Dict]:
        """Get contract metadata from cache"""
        sql = """
            SELECT tick_size, tick_value, symbol_id, name
            FROM contract_cache
            WHERE contract_id = ?
        """
        results = self._query(sql, (contract_id,))
        return results[0] if results else None
```

---

### **Admin CLI Data Layer**

**File:** `src/cli/admin/data_access.py`

**Purpose:** Service control + config management

```python
import win32serviceutil
import win32service
import yaml
from typing import Dict, List

class AdminDataAccess:
    """Data access layer for Admin CLI (read/write)"""

    def __init__(self):
        self.service_name = "RiskManagerDaemon"
        self.accounts_path = "config/accounts.yaml"
        self.risk_config_path = "config/risk_config.yaml"

    # ===== Service Control =====

    def start_service(self) -> bool:
        """Start daemon service"""
        try:
            win32serviceutil.StartService(self.service_name)
            return True
        except Exception as e:
            print(f"Error starting service: {e}")
            return False

    def stop_service(self) -> bool:
        """Stop daemon service"""
        try:
            win32serviceutil.StopService(self.service_name)
            return True
        except Exception as e:
            print(f"Error stopping service: {e}")
            return False

    def restart_service(self) -> bool:
        """Restart daemon service"""
        try:
            win32serviceutil.RestartService(self.service_name)
            return True
        except Exception as e:
            print(f"Error restarting service: {e}")
            return False

    def get_service_status(self) -> str:
        """Get service status"""
        try:
            status = win32serviceutil.QueryServiceStatus(self.service_name)
            status_map = {
                win32service.SERVICE_STOPPED: "STOPPED",
                win32service.SERVICE_RUNNING: "RUNNING",
                win32service.SERVICE_START_PENDING: "STARTING",
                win32service.SERVICE_STOP_PENDING: "STOPPING",
            }
            return status_map.get(status[1], "UNKNOWN")
        except:
            return "NOT_INSTALLED"

    # ===== Config Management =====

    def load_accounts(self) -> List[Dict]:
        """Load accounts from YAML"""
        with open(self.accounts_path, 'r') as f:
            config = yaml.safe_load(f)
            return config.get('accounts', [])

    def save_accounts(self, accounts: List[Dict]) -> bool:
        """Save accounts to YAML"""
        try:
            with open(self.accounts_path, 'w') as f:
                yaml.dump({'accounts': accounts}, f, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error saving accounts: {e}")
            return False

    def add_account(self, username: str, api_key: str, account_id: int) -> bool:
        """Add new account"""
        accounts = self.load_accounts()
        accounts.append({
            'account_id': account_id,
            'username': username,
            'api_key': api_key
        })
        return self.save_accounts(accounts)

    def remove_account(self, account_id: int) -> bool:
        """Remove account"""
        accounts = self.load_accounts()
        accounts = [a for a in accounts if a['account_id'] != account_id]
        return self.save_accounts(accounts)

    def load_risk_config(self) -> Dict:
        """Load risk config from YAML"""
        with open(self.risk_config_path, 'r') as f:
            return yaml.safe_load(f)

    def save_risk_config(self, config: Dict) -> bool:
        """Save risk config to YAML"""
        try:
            with open(self.risk_config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error saving risk config: {e}")
            return False

    def update_rule(self, rule_name: str, params: Dict) -> bool:
        """Update single rule configuration"""
        config = self.load_risk_config()
        if rule_name in config:
            config[rule_name].update(params)
            return self.save_risk_config(config)
        return False

    def toggle_rule(self, rule_name: str) -> bool:
        """Enable/disable a rule"""
        config = self.load_risk_config()
        if rule_name in config:
            config[rule_name]['enabled'] = not config[rule_name].get('enabled', False)
            return self.save_risk_config(config)
        return False
```

---

## 🔄 Real-Time Updates (Trader CLI)

### **Polling Strategy**

**Pattern:** Poll SQLite every 1 second, update UI only if data changed

```python
import time
import hashlib

class TraderUI:
    """Trader CLI with real-time updates"""

    def __init__(self):
        self.data_access = TraderDataAccess()
        self.last_state_hash = None
        self.account_id = None

    def run(self):
        """Main UI loop with real-time updates"""
        while True:
            # Query current state
            state = self._get_current_state()

            # Hash state to detect changes
            state_hash = hashlib.md5(str(state).encode()).hexdigest()

            # Only update UI if state changed
            if state_hash != self.last_state_hash:
                self._render_ui(state)
                self.last_state_hash = state_hash

            # Poll every 1 second
            time.sleep(1)

    def _get_current_state(self) -> Dict:
        """Query all data from SQLite"""
        return {
            'lockout': self.data_access.get_lockout_status(self.account_id),
            'pnl': self.data_access.get_daily_pnl(self.account_id),
            'positions': self.data_access.get_positions(self.account_id),
            'orders': self.data_access.get_orders(self.account_id),
            'enforcement_actions': self.data_access.get_enforcement_actions(self.account_id, 10),
            'trade_count': self.data_access.get_trade_count(self.account_id),
            'daemon_status': self.data_access.get_daemon_status(),
        }

    def _render_ui(self, state: Dict):
        """Render UI with current state"""
        # Clear screen and redraw
        # (Implementation in TRADER_CLI_SPEC.md)
        pass
```

**Performance:**
- SQLite query: ~1ms
- Hash calculation: ~0.1ms
- UI render: ~10ms
- Total: ~12ms per cycle
- CPU usage: < 1%

---

## 📊 Data Flow Diagrams

### **Trader CLI Startup Flow**

```
1. Trader launches CLI
   ↓
2. Select account (from list in SQLite or config)
   ↓
3. Initialize data access layer
   ↓
4. Start polling loop (every 1 second)
   ↓
5. Query SQLite → Get state
   ↓
6. Render UI with current state
   ↓
7. Wait 1 second, repeat from step 5
```

### **Admin CLI Config Change Flow**

```
1. Admin launches CLI (requires admin privileges)
   ↓
2. Authenticate with password
   ↓
3. Navigate to "Configure Rules"
   ↓
4. Select rule to edit
   ↓
5. Modify rule parameters (in-memory)
   ↓
6. Save to config/risk_config.yaml
   ↓
7. Prompt: "Restart daemon to apply changes?"
   ↓
8. If yes → win32serviceutil.RestartService()
   ↓
9. Wait for service to restart (~5 seconds)
   ↓
10. Show success message
```

### **Enforcement Action Flow (Real-Time)**

```
DAEMON:
1. Rule breach detected
   ↓
2. Execute enforcement (close positions)
   ↓
3. Write to enforcement_log table (SQLite)
   ↓

TRADER CLI (running in parallel):
4. Poll SQLite (every 1 second)
   ↓
5. Query enforcement_log table
   ↓
6. Detect new enforcement action
   ↓
7. Flash alert on UI: "⚠️ Rule breach - Positions closed"
   ↓
8. Show reason: "Daily loss limit exceeded"
```

**Latency:** < 1 second from enforcement to trader seeing alert

---

## 🧪 Testing Communication

### **Test 1: Trader CLI Reads While Daemon Writes**
```python
def test_concurrent_access():
    """Test SQLite read while daemon is writing"""
    # Daemon writes to positions table
    daemon.state_manager.update_position(position)

    # Trader CLI reads at same time
    positions = trader_data_access.get_positions(account_id)

    # Should work (SQLite WAL mode allows concurrent read/write)
    assert len(positions) > 0
```

### **Test 2: Admin CLI Config Change**
```python
def test_config_change():
    """Test config change + daemon restart"""
    # Admin changes max_contracts limit
    admin.update_rule('max_contracts', {'limit': 10})

    # Restart daemon
    admin.restart_service()

    # Wait for restart
    time.sleep(5)

    # Verify daemon loaded new config
    # (Check via enforcement - try to breach old limit, should not trigger)
```

### **Test 3: Trader CLI Graceful Degradation**
```python
def test_daemon_stopped():
    """Test Trader CLI behavior when daemon stopped"""
    # Stop daemon
    admin.stop_service()

    # Trader CLI should still work (reading last known state)
    state = trader_data_access.get_current_state()

    # Should show warning: "⚠️ Daemon stopped - showing last known state"
    assert state['daemon_status']['status'] == 'STOPPED'
```

---

## 📝 Summary

**Key Decisions:**

1. **Trader CLI:** Direct SQLite reads, polling every 1 second
2. **Admin CLI:** Windows Service API + YAML config editing
3. **No IPC needed:** Simple, proven pattern
4. **Security:** Admin requires password + Windows admin privileges
5. **Real-time:** < 1 second latency for trader to see enforcement actions
6. **Graceful degradation:** Trader CLI works even if daemon stopped

**Files to Implement:**
- `src/cli/trader/data_access.py` (~150 lines)
- `src/cli/admin/data_access.py` (~200 lines)
- `src/cli/trader/ui_loop.py` (~100 lines)
- `src/cli/admin/service_control.py` (~200 lines, already spec'd in DAEMON_ARCHITECTURE.md)

**Total: ~650 lines** (data access + UI loop)

---

**Next:** TRADER_CLI_SPEC.md (complete UI screens with tabs, real-time data)
