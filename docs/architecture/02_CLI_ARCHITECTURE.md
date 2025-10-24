# CLI Architecture

## Overview

The Risk Manager system provides two distinct command-line interfaces (CLIs) for different user roles:

1. **Trader CLI**: Real-time monitoring dashboard for traders (read-only)
2. **Admin CLI**: Setup wizard and configuration tool for administrators (full control)

Both CLIs communicate with the daemon but serve fundamentally different purposes and have different access levels.

---

## CLI Types

### Trader CLI

**Purpose**: Real-time terminal-based dashboard for traders to monitor their account status, P&L, positions, lockouts, and enforcement actions.

**Who Uses It**: Traders who want to monitor their trading activity and risk status in real-time.

**Key Characteristics**:
- Real-time updates via WebSocket (< 10ms latency from daemon events)
- Beautiful ANSI-colored UI with boxes, tables, and status indicators
- Tab-based interface for different views (Overview, P&L, Positions, Rules, Connections, Holidays, Lockouts, Enforcement History)
- Clock in/out tracking for trading sessions
- Connection status monitoring (daemon, TopstepX API, WebSocket)
- Lockout alerts with countdown timers
- Enforcement action history with reasons

**Access Level**:
- ✅ **CAN** view all account data (P&L, positions, quotes, lockouts, enforcement)
- ✅ **CAN** see real-time updates (same data that rules see)
- ✅ **CAN** clock in/out for sessions
- ❌ **CANNOT** modify risk rules
- ❌ **CANNOT** stop daemon
- ❌ **CANNOT** bypass enforcement

**File Location**: `src/cli/trader/`

---

### Admin CLI

**Purpose**: Setup wizard and configuration tool for administrators to manage the entire risk management system.

**Who Uses It**: System administrators responsible for configuring accounts, risk rules, and controlling the daemon service.

**Key Characteristics**:
- Beautiful ANSI UI with centered menus, colors, and animations
- Number-based selection (type 1, 2, 3 - no external dependencies)
- Password authentication (admin-only access)
- Windows Service control (requires admin privileges)
- YAML configuration editing (accounts.yaml, risk_config.yaml)
- Connection testing (TopstepX API, SignalR, database)

**Access Level**:
- ✅ **REQUIRES** admin password authentication
- ✅ **REQUIRES** Windows admin privileges (for service control)
- ✅ **CAN** modify all configuration files
- ✅ **CAN** install/start/stop/restart daemon service
- ✅ **CAN** authenticate trader accounts
- ❌ **NO real-time dashboard** (use Trader CLI for that)

**File Location**: `src/cli/admin/`

---

## Complete Command Reference

### Trader CLI Commands

The Trader CLI is **not** command-based. Instead, it's an interactive dashboard with tab-based navigation:

**Launch Command**:
```bash
python src/cli/trader/trader_main.py --account-id 123
```

**Interactive Navigation** (once running):
- Press `1` - Overview tab (P&L summary, positions, lockouts)
- Press `2` - P&L Details tab (daily summary, recent trades)
- Press `3` - Positions tab (open positions, orders, quote status)
- Press `4` - Rules tab (active risk rules and their status)
- Press `5` - Connections tab (daemon, WebSocket, API status)
- Press `6` - Holidays tab (upcoming holidays, trading hours)
- Press `7` - Lockouts tab (active lockouts, lockout history)
- Press `8` - Enforcement History tab (recent enforcement actions)
- Press `I` - Clock In (start trading session)
- Press `O` - Clock Out (end trading session)
- Press `Q` - Quit (exit dashboard)

**Data Display**:
- Real-time P&L (realized and unrealized)
- Open positions with current prices
- Active lockouts with countdown timers
- Enforcement actions with timestamps and reasons
- Connection status indicators
- Quote age monitoring

---

### Admin CLI Commands

The Admin CLI is menu-driven with the following main options:

**Launch Command**:
```bash
python src/cli/admin/admin_main.py
# Requires admin password on startup
# Requires Windows admin privileges
```

**Main Menu Options**:

1. **Configure Authentication**
   - Enter TopstepX username and API key
   - Validate credentials with TopstepX API
   - Obtain JWT token (valid 24 hours)
   - Save credentials to `config/accounts.yaml`

2. **Manage Accounts**
   - `A` - Add new trader account
   - `E` - Edit existing account (username, API key)
   - `D` - Delete account (requires confirmation)
   - View all configured accounts with status

3. **Configure Risk Rules**
   - `E [rule_number]` - Edit specific rule parameters
   - `T [rule_number]` - Toggle rule enable/disable
   - `R` - Reset all rules to defaults
   - View all 12 risk rules with current limits and status

4. **Service Control**
   - `1` - Start daemon service
   - `2` - Stop daemon service
   - `3` - Restart daemon service
   - `4` - View service logs (last 20 lines)
   - `5` - Install Windows Service (one-time setup)
   - `6` - Uninstall Windows Service

5. **Test Connection**
   - Runs diagnostic tests:
     - TopstepX API connectivity
     - SignalR WebSocket connections
     - Account authentication
     - Database access
     - WebSocket server availability

6. **View Daemon Status**
   - Service status (running/stopped)
   - Uptime and resource usage
   - Connection status
   - Monitored accounts summary
   - Recent events log

---

## CLI-Daemon Communication

### Communication Mechanism: Dual-Pattern Architecture

The CLIs use **two different communication patterns** depending on their purpose:

#### 1. Trader CLI → Daemon: Real-Time WebSocket

**Protocol**: WebSocket (RFC 6455)

**Endpoint**: `ws://localhost:8765`

**Direction**: One-way broadcast (Daemon → Trader CLI)

**Characteristics**:
- True real-time: < 10ms latency from daemon event to UI update
- Event-driven: Trader receives same events that daemon processes
- No authentication: Localhost-only connection (trusted)
- Multiple clients: Daemon can broadcast to multiple Trader CLIs simultaneously
- Client-side filtering: Each Trader CLI filters events by account_id

**Event Types Broadcasted**:

1. **GatewayUserTrade** - Trade executed (P&L updated)
   ```json
   {
     "type": "GatewayUserTrade",
     "account_id": 123,
     "data": {
       "id": 101112,
       "contractId": "CON.F.US.MNQ.U25",
       "profitAndLoss": -45.50,
       "timestamp": "2025-01-17T14:45:15Z"
     }
   }
   ```

2. **GatewayUserPosition** - Position changed
   ```json
   {
     "type": "GatewayUserPosition",
     "account_id": 123,
     "data": {
       "id": 456,
       "contractId": "CON.F.US.MNQ.U25",
       "type": 1,
       "size": 3,
       "averagePrice": 21000.5
     }
   }
   ```

3. **GatewayUserOrder** - Order placed/canceled/filled
   ```json
   {
     "type": "GatewayUserOrder",
     "account_id": 123,
     "data": {
       "id": 789,
       "contractId": "CON.F.US.MNQ.U25",
       "state": 1,
       "size": 2
     }
   }
   ```

4. **MarketQuote** - Real-time price update (~10-20 times/second)
   ```json
   {
     "type": "MarketQuote",
     "account_id": 123,
     "data": {
       "contractId": "CON.F.US.MNQ.U25",
       "bid": 21000.25,
       "ask": 21000.50,
       "last": 21000.50
     }
   }
   ```

5. **lockout_set** - Lockout applied
   ```json
   {
     "type": "lockout_set",
     "account_id": 123,
     "data": {
       "reason": "Daily loss limit hit: -$550",
       "locked_until": "2025-01-17T17:00:00Z",
       "rule_id": "RULE-003"
     }
   }
   ```

6. **lockout_cleared** - Lockout removed
   ```json
   {
     "type": "lockout_cleared",
     "account_id": 123,
     "data": {
       "cleared_at": "2025-01-17T17:00:00Z",
       "cleared_by": "TIMER_EXPIRY"
     }
   }
   ```

7. **enforcement_action** - Enforcement executed
   ```json
   {
     "type": "enforcement_action",
     "account_id": 123,
     "data": {
       "action": "CLOSE_ALL_POSITIONS",
       "reason": "MaxContracts breach: 6 > 5",
       "rule_id": "RULE-001",
       "timestamp": "2025-01-17T14:45:15Z"
     }
   }
   ```

8. **daily_reset** - Daily reset executed
   ```json
   {
     "type": "daily_reset",
     "account_id": 123,
     "data": {
       "reset_time": "2025-01-17T17:00:00Z",
       "previous_pnl": -150.50,
       "lockouts_cleared": true
     }
   }
   ```

9. **daemon_status** - Daemon status change
   ```json
   {
     "type": "daemon_status",
     "account_id": null,
     "data": {
       "status": "RUNNING",
       "message": "Daemon started successfully"
     }
   }
   ```

**Fallback**: If WebSocket disconnected, Trader CLI falls back to polling SQLite database every 1 second for state updates.

---

#### 2. Admin CLI → Daemon: Windows Service API + Config Files

**Protocol**: Windows Service Manager API + Direct file I/O

**Direction**: Bidirectional (Admin CLI ↔ Daemon via service control and config files)

**Service Control** (via `win32serviceutil`):
```python
# Start daemon
win32serviceutil.StartService("RiskManagerDaemon")

# Stop daemon
win32serviceutil.StopService("RiskManagerDaemon")

# Restart daemon
win32serviceutil.RestartService("RiskManagerDaemon")

# Get status
status = win32serviceutil.QueryServiceStatus("RiskManagerDaemon")
```

**Configuration Management** (via YAML file editing):
```python
# Edit config/risk_config.yaml
config = yaml.safe_load(open("config/risk_config.yaml"))
config['max_contracts']['limit'] = 10
yaml.dump(config, open("config/risk_config.yaml", 'w'))

# Restart daemon to apply changes
win32serviceutil.RestartService("RiskManagerDaemon")
```

**Data Access** (read-only SQLite queries):
```python
# Query daemon status from database
db = sqlite3.connect('data/state.db')
status = db.execute("SELECT * FROM session_state").fetchone()
```

---

#### 3. Both CLIs → Logs: Direct File Reads

**Protocol**: Direct filesystem access (read-only)

**Log Files**:
```
logs/
├── daemon.log          # General daemon events
├── enforcement.log     # All enforcement actions
├── api.log            # SignalR/REST API events
└── error.log          # Errors only
```

**Read Pattern** (tail last N lines):
```python
with open('logs/enforcement.log', 'r') as f:
    lines = f.readlines()
    last_50 = lines[-50:]
    for line in last_50:
        print(line)
```

---

## CLI Architecture

### Trader CLI Process Model

**Architecture**: Single process with background thread for WebSocket

**Main Components**:
1. **Main Thread**: UI rendering and user input handling
2. **WebSocket Thread**: Receives real-time events from daemon
3. **UI Update Callback**: Triggered by WebSocket events to update display

**Connection Lifecycle**:
```
1. Trader launches CLI with account ID
2. Load initial state from SQLite (current P&L, positions, lockouts)
3. Connect to daemon WebSocket (ws://localhost:8765)
4. Subscribe to all events (filter by account_id on client side)
5. Render initial UI with loaded state
6. Enter UI loop:
   - Handle user input (tab switching, clock in/out)
   - Receive WebSocket events → Update in-memory state → Re-render UI
   - Refresh every 1 second (update timers, check connection)
7. On quit: Disconnect WebSocket, close UI
```

**Reconnection Logic**:
- If WebSocket disconnects:
  1. Show warning: "⚠️ Lost connection to daemon"
  2. Fall back to polling SQLite every 1 second
  3. Retry WebSocket connection with exponential backoff:
     - 1st retry: 1 second
     - 2nd retry: 2 seconds
     - 3rd retry: 4 seconds
     - 4th retry: 8 seconds
     - 5th+ retry: 10 seconds (max)
  4. When reconnected: Resume real-time updates

---

### Admin CLI Process Model

**Architecture**: Single process, synchronous menu navigation

**Main Components**:
1. **Main Thread**: Menu rendering, user input, synchronous operations
2. **No background threads**: All operations are synchronous (blocking)

**Execution Flow**:
```
1. Admin launches CLI
2. Check Windows admin privileges (exit if not admin)
3. Prompt for admin password authentication (3 attempts)
4. Show main menu
5. User selects option → Execute synchronously → Return to menu
6. Repeat until user quits
```

**Service Control Flow**:
```
Admin selects "Start Service"
  ↓
Check admin privileges
  ↓
Call win32serviceutil.StartService("RiskManagerDaemon")
  ↓
Wait 2 seconds for service to start
  ↓
Query service status to verify
  ↓
Show success/failure message
  ↓
Return to menu
```

**Config Edit Flow**:
```
Admin selects "Edit Rule"
  ↓
Load config/risk_config.yaml
  ↓
Show current rule settings
  ↓
Prompt for field to edit
  ↓
Prompt for new value
  ↓
Validate input
  ↓
Update YAML file
  ↓
Show success message
  ↓
Prompt: "Restart daemon to apply changes? (y/n)"
  ↓
If yes: Restart daemon service
  ↓
Return to menu
```

---

## Command Syntax

### Trader CLI Syntax

**Basic Usage**:
```bash
# Launch with account ID
python src/cli/trader/trader_main.py --account-id 123

# Optional: Specify database path
python src/cli/trader/trader_main.py --account-id 123 --db-path data/state.db
```

**Interactive Controls** (no command-line arguments, all keyboard-driven):
- Number keys (1-8): Switch tabs
- `I` key: Clock in
- `O` key: Clock out
- `Q` key: Quit
- `R` key: Force refresh

---

### Admin CLI Syntax

**Basic Usage**:
```bash
# Launch (requires admin privileges)
python src/cli/admin/admin_main.py

# Must be run as Administrator on Windows
# Right-click → "Run as Administrator"
```

**No command-line arguments** - all configuration is menu-driven.

---

## Response Format

### Trader CLI Display Format

**Output**: ANSI-colored terminal UI with box-drawing characters

**Layout Structure**:
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         RISK MANAGER - TRADER DASHBOARD                      ║
║                    Account: John Trader (#123) | 2025-01-17 14:32:45        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  [1] Overview    [2] P&L    [3] Positions    [4] Rules    [5] Connections  ║
║  [6] Holidays    [7] Lockouts    [8] Enforcement History    [Q] Quit        ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║                        [ TAB CONTENT AREA ]                                  ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Status: 🟢 Connected | WebSocket: 🟢 ws://localhost:8765 | Daemon: 🟢 Running ║
║ Session: 🟢 Clocked In at 09:30:00 (5h 2m trading)                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**Color Coding**:
- 🟢 Green: Profit, success, OK status, connected
- 🔴 Red: Loss, error, lockout, disconnected
- 🟡 Yellow: Warning, approaching limits
- 🔵 Blue/Cyan: Info, neutral status
- ⚪ White: Neutral values

**Data Formatting**:
- P&L: `+$1,250.00` (green) or `-$150.00` (red)
- Percentages: `75% 🟡` (color-coded by proximity to limit)
- Timestamps: `14:32:15` (HH:MM:SS)
- Durations: `5h 32m 15s`
- Quote age: `0.2s 🟢` (fresh), `5.5s 🟡` (stale), `30s+ 🔴` (no data)

---

### Admin CLI Display Format

**Output**: ANSI-colored terminal UI with centered menus

**Layout Structure**:
```
                    ██████╗ ██╗███████╗██╗  ██╗
                    ██╔══██╗██║██╔════╝██║ ██╔╝
                    ██████╔╝██║███████╗█████╔╝
                    ██╔══██╗██║╚════██║██╔═██╗
                    ██║  ██║██║███████║██║  ██╗
                    ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝

              Risk Manager - Admin Configuration v1.0.0


              ╔══════════════════════════════════════════════════════╗
              ║ Quick Actions                                        ║
              ╠══════════════════════════════════════════════════════╣
              ║                                                      ║
              ║ 1. 🔐 Configure Authentication                      ║
              ║ 2. 👤 Manage Accounts                               ║
              ║ 3. ⚙️  Configure Risk Rules                          ║
              ║ 4. 🚀 Service Control                               ║
              ║ 5. 🔍 Test Connection                               ║
              ║ 6. 📊 View Daemon Status                            ║
              ║                                                      ║
              ║ 0. Exit                                              ║
              ║                                                      ║
              ╚══════════════════════════════════════════════════════╝

              Enter choice [0-6]: _
```

**Color Scheme**:
- Blue: Authentication
- Cyan: Account management
- Yellow: Rules/warnings
- Green: Service/success
- Magenta: Testing
- Red: Danger/errors

**Loading Animations**:
```
⠋ Validating credentials...
⠙ Starting service...
⠹ Testing connection...
```

**Status Messages**:
```
✓ Success: "Service started successfully"
✗ Error: "Failed to authenticate account"
⚠️  Warning: "High memory usage detected"
ℹ  Info: "JWT token obtained (valid 24h)"
```

---

## Authentication/Security

### Trader CLI Security

**Authentication**: None (read-only access to local data)

**Authorization**:
- Can read SQLite database (read-only mode)
- Can connect to WebSocket (localhost-only, no auth)
- Can read log files (filesystem permissions)
- **Cannot** write to any files
- **Cannot** control daemon
- **Cannot** modify configuration

**Network Security**:
- WebSocket: Localhost-only (`ws://127.0.0.1:8765`)
- No network exposure (no external connections)
- No TLS needed (local machine trust)

---

### Admin CLI Security

**Authentication**: Two-factor security

1. **Password Authentication**:
   ```python
   # Stored as bcrypt hash in config/admin_password.hash
   import bcrypt

   # Verify password on CLI startup
   if bcrypt.checkpw(entered_password.encode(), stored_hash):
       # Access granted
   else:
       # Access denied (3 attempts max)
   ```

2. **Windows Admin Privileges**:
   ```python
   import ctypes

   # Check if running as Administrator
   if not ctypes.windll.shell32.IsUserAnAdmin():
       print("❌ Please run as Administrator")
       sys.exit(1)
   ```

**Authorization**:
- Can read/write all configuration files
- Can control Windows Service (start/stop/restart)
- Can install/uninstall Windows Service
- Can read SQLite database
- Can read all log files

**Network Security**:
- No network connections (local file and service API only)
- Service control API: Windows system-level security

---

## SPECS Files Analyzed

The following specification files were analyzed to create this architecture document:

1. **`/project-specs/SPECS/06-CLI-FRONTEND/TRADER_CLI_SPEC.md`**
   - Complete Trader CLI specification
   - Real-time WebSocket client implementation
   - UI components (colors, boxes, tables)
   - 8 tab layouts (Overview, P&L, Positions, Rules, Connections, Holidays, Lockouts, Enforcement)
   - Clock in/out feature
   - File: `src/cli/trader/trader_main.py` (~400 lines)
   - File: `src/cli/trader/realtime_client.py` (~200 lines)
   - File: `src/cli/trader/ui_components.py` (~300 lines)

2. **`/project-specs/SPECS/06-CLI-FRONTEND/ADMIN_CLI_SPEC.md`**
   - Complete Admin CLI specification
   - Beautiful ANSI UI with centered menus
   - 6 main screens (Authentication, Accounts, Rules, Service, Testing, Status)
   - Windows Service control implementation
   - Password authentication with bcrypt
   - File: `src/cli/admin/admin_main.py` (~500 lines)
   - File: `src/cli/admin/ui_components.py` (~300 lines)
   - File: `src/cli/admin/service_control.py` (~200 lines)

3. **`/project-specs/SPECS/05-INTERNAL-API/DAEMON_ENDPOINTS.md`**
   - WebSocket API specification (9 event types)
   - Message format (JSON with type, account_id, data)
   - Event broadcasting protocol
   - Error handling and reconnection logic
   - File: `src/core/websocket_server.py` (~150 lines)

4. **`/project-specs/SPECS/05-INTERNAL-API/FRONTEND_BACKEND_ARCHITECTURE.md`**
   - Communication patterns (WebSocket, Service API, File I/O)
   - Data access patterns (Trader and Admin data layers)
   - Real-time update strategy (polling + WebSocket)
   - Security model (authentication, authorization)
   - File: `src/cli/trader/data_access.py` (~150 lines)
   - File: `src/cli/admin/data_access.py` (~200 lines)

5. **`/project-specs/SPECS/02-BACKEND-DAEMON/DAEMON_ARCHITECTURE.md`**
   - Daemon threading model (6 threads including WebSocket server)
   - Startup sequence (29 steps)
   - WebSocket server implementation (Thread 6)
   - Shutdown and crash recovery
   - File: `src/core/websocket_server.py` (~150 lines)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DAEMON (Windows Service)                           │
│  - Monitors all accounts 24/7                                           │
│  - Enforces risk rules in real-time                                     │
│  - Writes state to SQLite (data/state.db)                               │
│  - Broadcasts events via WebSocket (Thread 6)                           │
│  - Listens on ws://localhost:8765                                       │
└─────────────┬────────────────────┬──────────────────────────────────────┘
              │                    │
              │ Writes state       │ Broadcasts events
              ▼                    ▼
       ┌──────────────┐     ┌──────────────────┐
       │ SQLite DB    │     │ WebSocket Server │
       │ state.db     │     │ localhost:8765   │
       └──────┬───────┘     └────────┬─────────┘
              │                      │
              │                      │
              ▼                      ▼
       ┌────────────────────────────────────┐
       │        TRADER CLI                  │
       │  - WebSocket client (real-time)    │
       │  - SQLite reader (initial state)   │
       │  - 8 tab interface                 │
       │  - Clock in/out tracking           │
       │  - READ-ONLY access                │
       └────────────────────────────────────┘

       ┌────────────────────────────────────┐
       │         ADMIN CLI                  │
       │  - Service control (win32service)  │
       │  - Config editing (YAML files)     │
       │  - Password authentication         │
       │  - FULL CONTROL access             │
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

## Implementation Summary

### Trader CLI Files
- **src/cli/trader/trader_main.py** (~400 lines): Main dashboard, UI loop, event handling
- **src/cli/trader/realtime_client.py** (~200 lines): WebSocket client for real-time updates
- **src/cli/trader/ui_components.py** (~300 lines): UI helpers (colors, boxes, formatting)
- **src/cli/trader/data_access.py** (~150 lines): SQLite query functions
- **Total**: ~1050 lines

### Admin CLI Files
- **src/cli/admin/admin_main.py** (~500 lines): Main menu, screens, authentication
- **src/cli/admin/ui_components.py** (~300 lines): Centered menus, colors, animations
- **src/cli/admin/service_control.py** (~200 lines): Windows Service management
- **src/cli/admin/data_access.py** (~200 lines): Service API, config YAML editing
- **Total**: ~1200 lines

### Daemon WebSocket Server
- **src/core/websocket_server.py** (~150 lines): WebSocket broadcast server
- **Integration**: Event router, enforcement engine, lockout manager all broadcast events

### Total Implementation
- **Trader CLI**: ~1050 lines
- **Admin CLI**: ~1200 lines
- **WebSocket Server**: ~150 lines
- **Grand Total**: ~2400 lines of Python code

---

## Dependencies

### Trader CLI Dependencies
- `websocket-client`: WebSocket client library
- `sqlite3`: Built-in Python (no install needed)
- Terminal: ANSI color support (Windows Terminal, iTerm2, etc.)

### Admin CLI Dependencies
- `bcrypt`: Password hashing
- `pywin32`: Windows Service control
- `pyyaml`: YAML configuration editing
- `ctypes`: Built-in Python (for admin privilege check)
- `getpass`: Built-in Python (for password input)

### Daemon Dependencies
- `websockets`: WebSocket server library (asyncio-based)
- `asyncio`: Built-in Python (for WebSocket event loop)

---

## Performance Characteristics

### Trader CLI Performance
- **WebSocket latency**: < 10ms (daemon event → UI update)
- **SQLite query**: ~1ms per query
- **UI render**: ~10ms per full screen refresh
- **CPU usage**: < 1% (idle), < 5% (active trading)
- **Memory usage**: ~20-30 MB

### Admin CLI Performance
- **Service start/stop**: ~2-5 seconds
- **Config save**: ~10ms (YAML write)
- **Connection test**: ~2-3 seconds (network round-trip)
- **CPU usage**: < 1% (menu navigation)
- **Memory usage**: ~10-15 MB

### WebSocket Server Performance
- **Broadcast latency**: < 1ms (localhost)
- **Max clients**: 100+ (tested limit)
- **Memory per client**: ~50 KB
- **CPU usage**: < 1%
- **Network bandwidth**: ~10 KB/sec (JSON messages)

---

## Coordination Integration

After creating this document, notify the swarm:

```bash
npx claude-flow@alpha hooks post-edit --file "docs/architecture/02_CLI_ARCHITECTURE.md" --memory-key "swarm/architecture/cli-complete"
```

This signals to other agents that CLI architecture analysis is complete and the document is ready for review.
