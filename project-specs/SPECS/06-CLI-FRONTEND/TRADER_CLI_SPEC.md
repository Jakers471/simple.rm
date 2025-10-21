---
doc_id: CLI-TRADER-001
version: 1.0
last_updated: 2025-10-21
dependencies: [DAEMON-001, FRONTEND-BACKEND-001, MOD-001 through MOD-009]
---

# Trader CLI Specification

**Purpose:** Complete specification for trader CLI - real-time monitoring dashboard with WebSocket updates

**File Coverage:** `src/cli/trader/trader_main.py`, `src/cli/trader/realtime_client.py`, `src/cli/trader/ui_components.py`

---

## 🎯 Overview

### **What is the Trader CLI?**
A real-time terminal-based dashboard for traders to monitor their account status, P&L, positions, lockouts, and enforcement actions. The trader CANNOT modify rules or bypass enforcement - this is read-only monitoring.

### **Key Features:**
- **Real-time updates** via WebSocket (< 10ms latency from daemon events)
- **Beautiful ANSI-colored UI** with boxes, tables, and status indicators
- **Tab-based interface** for different views (Overview, P&L, Positions, Rules, etc.)
- **Clock in/out tracking** for trading sessions
- **Connection status monitoring** (daemon, TopstepX API, WebSocket)
- **Lockout alerts** with countdown timers
- **Enforcement action history** with reasons

### **Access Level:**
- ✅ **CAN** view all account data (P&L, positions, quotes, lockouts, enforcement)
- ✅ **CAN** see real-time updates (same data that rules see)
- ✅ **CAN** clock in/out for sessions
- ❌ **CANNOT** modify risk rules
- ❌ **CANNOT** stop daemon
- ❌ **CANNOT** bypass enforcement

---

## 🔌 Architecture

### **Data Sources:**
1. **WebSocket (Real-Time)** - Connects to daemon's WebSocket server (`ws://localhost:8765`)
   - Receives same events that daemon processes (quotes, trades, positions, enforcement)
   - Updates UI in real-time (< 10ms latency)
   - Automatically reconnects on disconnect

2. **SQLite (Initial State)** - Reads from `data/state.db` on startup
   - Loads current lockouts, P&L, positions, orders, contract cache
   - Used when WebSocket disconnected (fallback to polling every 1 second)

### **Threading Model:**
1. **Main Thread** - UI rendering and user input
2. **WebSocket Thread** - Receives real-time events from daemon
3. **UI Update Thread** - Processes events and updates display (triggered by WebSocket)

### **Update Flow:**
```
Daemon Event Router
    ↓ (broadcasts to WebSocket)
WebSocket Server (Thread 6)
    ↓ (sends message)
Trader CLI WebSocket Client
    ↓ (parses event)
UI Update Callback
    ↓ (updates in-memory state)
Main UI Thread (refreshes display)
```

---

## 🎨 UI Design

### **Color Scheme:**
```python
class Colors:
    """ANSI color codes for beautiful terminal UI"""
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Text colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Status colors
    SUCCESS = GREEN
    WARNING = YELLOW
    ERROR = RED
    INFO = CYAN

    # P&L colors
    PROFIT = GREEN
    LOSS = RED
    NEUTRAL = WHITE
```

### **Box Drawing Characters:**
```python
class BoxChars:
    """Unicode box drawing characters"""
    # Corners
    TOP_LEFT = "╔"
    TOP_RIGHT = "╗"
    BOTTOM_LEFT = "╚"
    BOTTOM_RIGHT = "╝"

    # Lines
    HORIZONTAL = "═"
    VERTICAL = "║"

    # T-junctions
    T_DOWN = "╦"
    T_UP = "╩"
    T_RIGHT = "╠"
    T_LEFT = "╣"

    # Cross
    CROSS = "╬"
```

---

## 📱 Main Screen Layout

### **Full Screen Layout:**
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
║                        (see sections below)                                  ║
║                                                                              ║
║                                                                              ║
║                                                                              ║
║                                                                              ║
║                                                                              ║
║                                                                              ║
║                                                                              ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Status: 🟢 Connected | WebSocket: 🟢 ws://localhost:8765 | Daemon: 🟢 Running ║
║ Session: 🟢 Clocked In at 09:30:00 (5h 2m trading)                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### **Header Section:**
- **Line 1:** Title - "RISK MANAGER - TRADER DASHBOARD"
- **Line 2:** Account name, account ID, current date/time (updates every second)
- **Line 3:** Horizontal separator

### **Navigation Menu:**
- **Line 4-5:** Tab buttons (number-based selection, no mouse needed)
- Pressing `1-8` switches tabs, `Q` quits

### **Content Area:**
- **Lines 6-14:** Main content (changes based on selected tab)
- This is where tab-specific data is displayed

### **Status Bar:**
- **Line 15:** Connection status indicators (daemon, WebSocket, TopstepX API)
- **Line 16:** Session status (clocked in/out, duration)

---

## 📊 Tab 1: Overview

### **Layout:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                  OVERVIEW                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Today's P&L                                                        │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  Realized:    +$1,250.00  🟢                                        │    ║
║  │  Unrealized:   -$150.00   🔴                                        │    ║
║  │  Total:       +$1,100.00  🟢                                        │    ║
║  │                                                                      │    ║
║  │  Daily Loss Limit: $2,000  |  Remaining: $900 (45%)                │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Positions (3 open)                                                 │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  MNQ   Long 2 @ 21050.00   Current: 21025.00   P&L: -$100.00  🔴   │    ║
║  │  ES    Long 1 @ 5825.00    Current: 5827.50    P&L: +$62.50   🟢   │    ║
║  │  CL    Short 1 @ 77.50     Current: 77.45      P&L: +$50.00   🟢   │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Active Lockouts                                                    │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  🔴 NONE - All rules clear                                          │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### **Data Sources:**
- **Today's P&L:** `MOD-005` (PNL Tracker)
  - Real-time updates on `GatewayUserTrade` and `MarketQuote` events
  - Unrealized P&L calculated from current positions + latest quotes
  - Daily loss limit from `config/risk_config.yaml` (RULE-003)

- **Positions:** `MOD-009` (State Manager)
  - Real-time updates on `GatewayUserPosition` events
  - Current price from `MOD-006` (Quote Tracker) via `MarketQuote` events
  - Unrealized P&L color-coded (green = profit, red = loss)

- **Active Lockouts:** `MOD-002` (Lockout Manager)
  - Real-time updates when lockout set/cleared
  - Shows lockout reason, expires time, countdown timer

### **Update Frequency:**
- **Realized P&L:** Updates on `GatewayUserTrade` events (when trade closes)
- **Unrealized P&L:** Updates on `MarketQuote` events (~10-20 times/second for active contracts)
- **Positions:** Updates on `GatewayUserPosition` events (when position changes)
- **Lockouts:** Updates immediately when lockout set/cleared

---

## 💰 Tab 2: P&L Details

### **Layout:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                P&L DETAILS                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Daily Summary (2025-01-17)                                         │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  Starting Balance:      $25,000.00                                  │    ║
║  │  Realized P&L:          +$1,250.00  🟢                              │    ║
║  │  Unrealized P&L:          -$150.00  🔴                              │    ║
║  │  Current Balance:       $26,100.00  (+4.4%)                         │    ║
║  │                                                                      │    ║
║  │  Daily Loss Limit:      -$2,000.00                                  │    ║
║  │  Remaining Buffer:        +$900.00  (45% of limit used)             │    ║
║  │                                                                      │    ║
║  │  Max Unrealized Loss:      -$350.00  (at 13:45:22)                  │    ║
║  │  Max Unrealized Profit:   +$1,800.00  (at 11:23:15)                 │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Recent Trades (Last 10)                                            │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  Time      Contract   Side   Qty   Price      P&L      Total        │    ║
║  │  ───────   ────────   ────   ───   ──────   ──────    ──────        │    ║
║  │  14:32:15  MNQ        Sell   1     21025.00  +$50.00  +$1,250.00    │    ║
║  │  14:15:42  ES         Sell   1     5827.50   +$125.00 +$1,200.00    │    ║
║  │  13:58:30  CL         Buy    1     77.45     -$50.00  +$1,075.00    │    ║
║  │  13:45:22  MNQ        Buy    2     21050.00  -$100.00 +$1,125.00    │    ║
║  │  ... (6 more trades)                                                │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### **Data Sources:**
- **Daily Summary:** `MOD-005` (PNL Tracker)
  - `daily_pnl` table (realized P&L)
  - Calculated unrealized P&L (positions × current quotes)
  - Max unrealized loss/profit tracked in memory (MOD-005)

- **Recent Trades:** `MOD-008` (Trade Counter)
  - `trade_history` table (last 24 hours)
  - Real-time updates on `GatewayUserTrade` events
  - Shows running total P&L after each trade

### **Update Frequency:**
- **Unrealized P&L:** Updates on `MarketQuote` events (~10-20/second)
- **Realized P&L:** Updates on `GatewayUserTrade` events (when trade closes)
- **Recent Trades:** Updates on `GatewayUserTrade` events (new row added)

---

## 📍 Tab 3: Positions

### **Layout:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                 POSITIONS                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Open Positions (3)                                                 │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  Contract   Side   Qty   Avg Price   Current   P&L      Age         │    ║
║  │  ────────   ────   ───   ─────────   ───────   ──────   ──────      │    ║
║  │  MNQ        Long   2     21050.00    21025.00  -$100.00  2h 15m     │    ║
║  │  ES         Long   1     5825.00     5827.50   +$62.50   45m        │    ║
║  │  CL         Short  1     77.50       77.45     +$50.00   12m        │    ║
║  │                                                                      │    ║
║  │  Total Contracts: 4 / 10 (Max: 10)                                  │    ║
║  │  Total Unrealized P&L: +$12.50  🟢                                  │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Open Orders (2)                                                    │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  Contract   Type        Side   Qty   Price    Status   Age          │    ║
║  │  ────────   ────────    ────   ───   ──────   ──────   ──────       │    ║
║  │  MNQ        Stop Loss   Sell   2     20950.00 Working  2h 15m       │    ║
║  │  ES         Limit       Sell   1     5830.00  Working  45m          │    ║
║  │                                                                      │    ║
║  │  Total Orders: 2 Working                                            │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Quote Status                                                       │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  MNQ:  Bid 21024.75 / Ask 21025.25  (Age: 0.2s)  🟢 FRESH          │    ║
║  │  ES:   Bid 5827.25  / Ask 5827.75   (Age: 0.5s)  🟢 FRESH          │    ║
║  │  CL:   Bid 77.44    / Ask 77.45     (Age: 1.2s)  🟢 FRESH          │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### **Data Sources:**
- **Open Positions:** `MOD-009` (State Manager)
  - `positions` table
  - Real-time updates on `GatewayUserPosition` events
  - Current price from `MOD-006` (Quote Tracker)
  - P&L calculated using contract tick size/value from `MOD-007` (Contract Cache)

- **Open Orders:** `MOD-009` (State Manager)
  - `orders` table
  - Real-time updates on `GatewayUserOrder` events
  - Age calculated from `created_at` timestamp

- **Quote Status:** `MOD-006` (Quote Tracker)
  - In-memory quote storage
  - Real-time updates on `MarketQuote` events
  - Age = time since last quote received
  - **Warning:** If age > 5 seconds → 🟡 STALE
  - **Error:** If age > 30 seconds → 🔴 NO DATA

### **Update Frequency:**
- **Positions:** Updates on `GatewayUserPosition` events (when position changes)
- **Orders:** Updates on `GatewayUserOrder` events (when order state changes)
- **Quotes:** Updates on `MarketQuote` events (~10-20/second for active contracts)
- **Quote Age:** Calculated every 1 second (shows age of last quote)

---

## 📏 Tab 4: Rules

### **Layout:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                   RULES                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Active Risk Rules (12 configured)                                  │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  🟢 01 - Max Contracts              Limit: 10    Current: 4 (40%)   │    ║
║  │  🟢 02 - Max Contracts Per Instr.   Limit: 5     Current: 2 (40%)   │    ║
║  │  🟢 03 - Daily Realized Loss        Limit: $2000  Used: $0 (0%)     │    ║
║  │  🟢 04 - Daily Unrealized Loss      Limit: $1500  Current: $150     │    ║
║  │  🟢 05 - Max Unrealized Profit      Limit: $2500  Current: $1100    │    ║
║  │  🟢 06 - Trade Frequency Limit      Limit: 10/hr  Current: 3/hr     │    ║
║  │  🔴 07 - Cooldown After Loss        Status: ACTIVE (2m 15s left)    │    ║
║  │  🟢 08 - No Stop Loss Grace         Status: OK (all positions safe) │    ║
║  │  🟢 09 - Session Block Outside      Status: INSIDE trading hours    │    ║
║  │  🟢 10 - Auth Loss Guard            Status: OK (authenticated)      │    ║
║  │  🟢 11 - Symbol Blocks              Blocked: None                   │    ║
║  │  🟢 12 - Trade Management           Status: OK                      │    ║
║  │                                                                      │    ║
║  │  Note: 🟢 = OK, 🟡 = Warning, 🔴 = Active/Breached                  │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  ⚠️  Trader cannot edit rules - configured by Admin CLI                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### **Data Sources:**
- **Rule Configuration:** `config/risk_config.yaml` (loaded from SQLite on startup)
  - Each rule shows: enabled/disabled, limit, current value, percentage used
  - Color-coded based on proximity to limit:
    - 🟢 Green: < 70% of limit
    - 🟡 Yellow: 70-90% of limit
    - 🔴 Red: > 90% of limit or breached

- **Current Values:** Calculated from modules
  - Max Contracts: `MOD-009` (count open positions)
  - Daily Realized Loss: `MOD-005` (daily P&L)
  - Daily Unrealized Loss: `MOD-005` (unrealized P&L)
  - Trade Frequency: `MOD-008` (count trades in last hour)
  - Cooldown Timer: `MOD-003` (Timer Manager)

### **Update Frequency:**
- **Rule Status:** Updates on every event (rules checked on each event)
- **Current Values:** Real-time (recalculated from module state)
- **Cooldown Timer:** Updates every 1 second (countdown display)

---

## 🔗 Tab 5: Connections

### **Layout:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                CONNECTIONS                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Connection Status                                                  │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │                                                                      │    ║
║  │  🟢 Risk Manager Daemon                                             │    ║
║  │     Status: Running                                                 │    ║
║  │     Uptime: 5h 32m 15s                                              │    ║
║  │     Last Heartbeat: 0.5s ago                                        │    ║
║  │                                                                      │    ║
║  │  🟢 WebSocket Server                                                │    ║
║  │     URL: ws://localhost:8765                                        │    ║
║  │     Status: Connected                                               │    ║
║  │     Last Event: 0.2s ago (MarketQuote for MNQ)                      │    ║
║  │     Events Received: 15,342 (since startup)                         │    ║
║  │                                                                      │    ║
║  │  🟢 TopstepX API                                                    │    ║
║  │     SignalR User Hub: Connected                                     │    ║
║  │     SignalR Market Hub: Connected                                   │    ║
║  │     JWT Token: Valid (expires in 18h 23m)                           │    ║
║  │     Last Trade Event: 2m 15s ago                                    │    ║
║  │     Last Quote Event: 0.2s ago                                      │    ║
║  │                                                                      │    ║
║  │  🟢 Database                                                        │    ║
║  │     SQLite: data/state.db                                           │    ║
║  │     Size: 245 KB                                                    │    ║
║  │     Last Write: 3s ago                                              │    ║
║  │                                                                      │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  ⚠️  If WebSocket disconnected, CLI falls back to polling SQLite (1s)       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### **Data Sources:**
- **Daemon Status:** Check if Windows Service running (via SQLite last_update timestamp)
  - If `last_update` in `session_state` table > 5 seconds ago → daemon may be down
  - Uptime calculated from daemon start time

- **WebSocket Status:** Client connection state
  - 🟢 Connected: Receiving events
  - 🔴 Disconnected: Attempting reconnect
  - Shows time since last event received
  - Shows total events received since startup

- **TopstepX API:** Read from daemon logs or SQLite metadata
  - SignalR connection status (from daemon logs)
  - JWT token expiry (from daemon state)
  - Last event timestamps

- **Database:** File system check
  - SQLite file size
  - Last write timestamp (from file modification time)

### **Update Frequency:**
- **Connection Status:** Updates every 1 second
- **WebSocket Events:** Real-time (counts every event received)
- **Last Event Times:** Real-time (updated on every event)

---

## 📅 Tab 6: Holidays

### **Layout:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                  HOLIDAYS                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Upcoming Holidays (Next 7 Days)                                    │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  🔴 TODAY (2025-01-17):  Normal Trading Day                         │    ║
║  │                                                                      │    ║
║  │  2025-01-18 (Sat):       Weekend - Market Closed                    │    ║
║  │  2025-01-19 (Sun):       Weekend - Market Closed                    │    ║
║  │  2025-01-20 (Mon):       MLK Day - Market Closed 🏛️                 │    ║
║  │  2025-01-21 (Tue):       Normal Trading Day                         │    ║
║  │  2025-01-22 (Wed):       Normal Trading Day                         │    ║
║  │  2025-01-23 (Thu):       Normal Trading Day                         │    ║
║  │  2025-01-24 (Fri):       Normal Trading Day                         │    ║
║  │                                                                      │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Trading Hours (Today)                                              │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  Session Start:  09:30 AM EST                                       │    ║
║  │  Session End:    04:00 PM EST                                       │    ║
║  │                                                                      │    ║
║  │  Current Time:   02:32 PM EST  ✅ INSIDE trading hours              │    ║
║  │  Time Until End: 1h 28m                                             │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### **Data Sources:**
- **Holidays:** `config/holidays.yaml`
  - Loaded on CLI startup
  - Shows next 7 days
  - Highlights today and upcoming holidays

- **Trading Hours:** `MOD-004` (Reset Scheduler)
  - Session start/end times from account config
  - Current time in account timezone
  - Time until session end

### **Update Frequency:**
- **Holiday List:** Static (loaded on startup)
- **Current Time:** Updates every 1 second
- **Time Until End:** Updates every 1 second

---

## 🔒 Tab 7: Lockouts

### **Layout:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                  LOCKOUTS                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Active Lockouts (1)                                                │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  🔴 RULE-007: Cooldown After Loss                                   │    ║
║  │     Locked At:    14:30:00                                          │    ║
║  │     Locked Until: 14:35:00 (5 minutes)                              │    ║
║  │     Time Left:    ⏱️  2m 15s                                         │    ║
║  │     Reason:       Trade lost $200 - mandatory 5min cooldown         │    ║
║  │                                                                      │    ║
║  │     ⚠️  Trading BLOCKED until lockout expires                        │    ║
║  │                                                                      │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Lockout History (Last 5)                                           │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  Time      Rule                        Duration  Reason              │    ║
║  │  ───────   ────────────────────────    ────────  ──────────────      │    ║
║  │  14:30:00  Cooldown After Loss         5m        Lost $200 trade    │    ║
║  │  13:45:22  Daily Unrealized Loss       25m       Hit -$1500 limit   │    ║
║  │  12:15:30  Max Unrealized Profit       10m       Hit $2500 limit    │    ║
║  │  11:30:45  Trade Frequency Limit       15m       10 trades in 1hr   │    ║
║  │  10:00:00  Session Block Outside       Until 9:30 AM                │    ║
║  │                                                                      │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### **Data Sources:**
- **Active Lockouts:** `MOD-002` (Lockout Manager)
  - `lockouts` table (where `locked_until > now()`)
  - Real-time updates when lockout set/cleared
  - Countdown timer updates every 1 second

- **Lockout History:** `MOD-002` (Lockout Manager)
  - `lockouts` table (recent lockouts, sorted by `locked_at` DESC)
  - Shows last 5 lockouts (both active and expired)

### **Update Frequency:**
- **Active Lockouts:** Real-time (updates on lockout set/cleared events)
- **Countdown Timer:** Updates every 1 second
- **Lockout History:** Updates on new lockout events

---

## 🚨 Tab 8: Enforcement History

### **Layout:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                            ENFORCEMENT HISTORY                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Recent Enforcement Actions (Last 20)                               │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  Time      Rule             Action                Reason             │    ║
║  │  ───────   ──────────────   ──────────────────    ──────────────     │    ║
║  │  14:30:15  RULE-007         SET_LOCKOUT (5m)     Lost $200 trade    │    ║
║  │  14:30:15  RULE-007         CANCEL_ALL_ORDERS    Cooldown triggered │    ║
║  │  13:45:22  RULE-004         CLOSE_ALL_POSITIONS  -$1500 unrealized  │    ║
║  │  13:45:22  RULE-004         SET_LOCKOUT (25m)    Daily loss limit   │    ║
║  │  12:15:30  RULE-005         CLOSE_ALL_POSITIONS  +$2500 profit lock │    ║
║  │  12:15:30  RULE-005         SET_LOCKOUT (10m)    Max profit reached │    ║
║  │  11:30:45  RULE-006         REJECT_ORDER          10 trades in 1hr   │    ║
║  │  11:30:45  RULE-006         SET_LOCKOUT (15m)    Frequency limit    │    ║
║  │  10:05:22  RULE-001         REJECT_ORDER          Max 10 contracts   │    ║
║  │  09:58:15  RULE-008         CLOSE_POSITION (MNQ) No stop loss set   │    ║
║  │  ... (10 more actions)                                              │    ║
║  │                                                                      │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  Summary                                                            │    ║
║  │  ───────────────────────────────────────────────────────────────    │    ║
║  │  Total Actions Today: 23                                            │    ║
║  │  Positions Closed: 5                                                │    ║
║  │  Orders Rejected: 8                                                 │    ║
║  │  Lockouts Set: 10                                                   │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### **Data Sources:**
- **Enforcement Actions:** `MOD-001` (Enforcement Engine)
  - `enforcement_log` table
  - Real-time updates on enforcement actions
  - Shows action type, rule that triggered it, reason

- **Summary:** Calculated from `enforcement_log` table
  - Count actions by type (today only)

### **Update Frequency:**
- **Enforcement History:** Real-time (updates when new action taken)
- **Summary:** Real-time (recalculated when new action added)

---

## ⏰ Clock In/Out Feature

### **Location:** Bottom status bar

### **States:**
1. **Clocked Out:**
   ```
   Session: 🔴 Clocked Out | Press [I] to Clock In
   ```

2. **Clocked In:**
   ```
   Session: 🟢 Clocked In at 09:30:00 (5h 2m trading) | Press [O] to Clock Out
   ```

### **Functionality:**
- **Clock In:** Press `I` key
  - Records start time in `session_state` table
  - Starts session timer (updates every second)
  - Daemon is not affected (continues monitoring regardless)

- **Clock Out:** Press `O` key
  - Records end time in `session_state` table
  - Stops session timer
  - Calculates total session duration
  - Daemon is not affected (continues monitoring regardless)

### **Data Storage:**
```sql
-- session_state table (MOD-008)
CREATE TABLE session_state (
    account_id INTEGER PRIMARY KEY,
    clocked_in BOOLEAN NOT NULL DEFAULT 0,
    clock_in_time TIMESTAMP,
    clock_out_time TIMESTAMP,
    total_duration_seconds INTEGER DEFAULT 0
);
```

### **Purpose:**
- Track trader's active trading time
- For personal records (not enforced by daemon)
- Optional feature (trader can ignore)

---

## 🔌 WebSocket Client Implementation

### **src/cli/trader/realtime_client.py** (~200 lines)

```python
"""
WebSocket client for receiving real-time events from daemon.
Connects to daemon's WebSocket server on localhost:8765.
"""

import websocket
import json
import threading
import logging
from typing import Callable, Dict, Any

logger = logging.getLogger(__name__)

class TraderRealtimeClient:
    """
    WebSocket client that receives real-time events from daemon.
    Runs in background thread, calls UI callback on events.
    """

    def __init__(self, account_id: int, event_callback: Callable):
        """
        Args:
            account_id: Account ID to filter events for
            event_callback: Function to call on event: callback(event_type, data)
        """
        self.account_id = account_id
        self.event_callback = event_callback
        self.ws = None
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5

    def connect(self):
        """Connect to daemon WebSocket server (ws://localhost:8765)"""
        logger.info("Connecting to daemon WebSocket server...")

        self.ws = websocket.WebSocketApp(
            "ws://localhost:8765",
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )

        # Run in background thread
        self.thread = threading.Thread(
            target=self.ws.run_forever,
            daemon=True,
            name="WebSocketClient"
        )
        self.thread.start()

    def _on_open(self, ws):
        """Called when WebSocket connection established"""
        self.connected = True
        self.reconnect_attempts = 0
        logger.info("WebSocket connected to daemon")

    def _on_message(self, ws, message):
        """
        Called when event received from daemon.

        Message format:
        {
            'type': 'GatewayUserTrade',
            'account_id': 123,
            'data': {...}
        }
        """
        try:
            event = json.loads(message)

            # Filter by account_id
            if event.get('account_id') != self.account_id:
                return  # Ignore events for other accounts

            # Forward to UI callback
            event_type = event['type']
            data = event['data']

            self.event_callback(event_type, data)

        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")

    def _on_error(self, ws, error):
        """Called when WebSocket error occurs"""
        logger.error(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        """Called when WebSocket connection closed"""
        self.connected = False
        logger.warning(f"WebSocket disconnected (code: {close_status_code})")

        # Attempt reconnect
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"Reconnecting... (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")

            import time
            time.sleep(2)  # Wait 2 seconds before reconnect

            self.connect()
        else:
            logger.error("Max reconnect attempts reached - falling back to SQLite polling")

    def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.ws:
            self.ws.close()

        self.connected = False
        logger.info("WebSocket disconnected")

    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.connected
```

---

## 🎨 UI Components Implementation

### **src/cli/trader/ui_components.py** (~300 lines)

```python
"""
UI components for Trader CLI - boxes, tables, status indicators.
"""

import os
import sys
from datetime import datetime

class Colors:
    """ANSI color codes"""
    RESET = "\033[0m"
    BOLD = "\033[1m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"

class BoxChars:
    """Unicode box drawing characters"""
    TOP_LEFT = "╔"
    TOP_RIGHT = "╗"
    BOTTOM_LEFT = "╚"
    BOTTOM_RIGHT = "╝"
    HORIZONTAL = "═"
    VERTICAL = "║"
    T_DOWN = "╦"
    T_UP = "╩"
    T_RIGHT = "╠"
    T_LEFT = "╣"

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_box(title: str, content: list[str], width: int = 76):
    """
    Print a box with title and content.

    Args:
        title: Box title
        content: List of strings (one per line)
        width: Box width (default 76)
    """
    # Top border with title
    title_str = f" {title} "
    title_len = len(title_str)
    left_padding = (width - title_len - 2) // 2
    right_padding = width - title_len - left_padding - 2

    print(f"{BoxChars.TOP_LEFT}{BoxChars.HORIZONTAL * left_padding}{title_str}{BoxChars.HORIZONTAL * right_padding}{BoxChars.TOP_RIGHT}")

    # Content lines
    for line in content:
        # Pad line to width
        padding = width - len(line) - 2
        print(f"{BoxChars.VERTICAL} {line}{' ' * padding} {BoxChars.VERTICAL}")

    # Bottom border
    print(f"{BoxChars.BOTTOM_LEFT}{BoxChars.HORIZONTAL * width}{BoxChars.BOTTOM_RIGHT}")

def format_pnl(value: float) -> str:
    """
    Format P&L value with color.

    Args:
        value: P&L value

    Returns:
        Colored string (e.g., "+$1,250.00  🟢")
    """
    if value > 0:
        return f"{Colors.GREEN}+${value:,.2f}  🟢{Colors.RESET}"
    elif value < 0:
        return f"{Colors.RED}-${abs(value):,.2f}  🔴{Colors.RESET}"
    else:
        return f" ${value:,.2f}  ⚪"

def format_percentage(value: float, limit: float) -> str:
    """
    Format percentage with color based on limit proximity.

    Args:
        value: Current value
        limit: Limit value

    Returns:
        Colored percentage string
    """
    pct = (abs(value) / abs(limit)) * 100 if limit != 0 else 0

    if pct < 70:
        color = Colors.GREEN
        icon = "🟢"
    elif pct < 90:
        color = Colors.YELLOW
        icon = "🟡"
    else:
        color = Colors.RED
        icon = "🔴"

    return f"{color}{pct:.0f}% {icon}{Colors.RESET}"

def format_timestamp(ts: datetime) -> str:
    """Format timestamp as HH:MM:SS"""
    return ts.strftime("%H:%M:%S")

def format_duration(seconds: int) -> str:
    """
    Format duration as "5h 32m 15s".

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def print_header(account_name: str, account_id: int):
    """Print CLI header"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"{BoxChars.TOP_LEFT}{BoxChars.HORIZONTAL * 76}{BoxChars.TOP_RIGHT}")
    print(f"{BoxChars.VERTICAL}{' ' * 20}RISK MANAGER - TRADER DASHBOARD{' ' * 24}{BoxChars.VERTICAL}")
    print(f"{BoxChars.VERTICAL}{' ' * 10}Account: {account_name} (#{account_id}) | {now}{' ' * 10}{BoxChars.VERTICAL}")
    print(f"{BoxChars.T_RIGHT}{BoxChars.HORIZONTAL * 76}{BoxChars.T_LEFT}")

def print_nav_menu(current_tab: int):
    """Print navigation menu"""
    tabs = [
        "[1] Overview",
        "[2] P&L",
        "[3] Positions",
        "[4] Rules",
        "[5] Connections",
        "[6] Holidays",
        "[7] Lockouts",
        "[8] Enforcement",
        "[Q] Quit"
    ]

    # Highlight current tab
    tabs_str = "  ".join(tabs)
    print(f"{BoxChars.VERTICAL}{' ' * 2}{tabs_str}{' ' * 2}{BoxChars.VERTICAL}")
    print(f"{BoxChars.T_RIGHT}{BoxChars.HORIZONTAL * 76}{BoxChars.T_LEFT}")

def print_status_bar(daemon_status: str, websocket_status: str, session_status: str):
    """Print bottom status bar"""
    print(f"{BoxChars.T_RIGHT}{BoxChars.HORIZONTAL * 76}{BoxChars.T_LEFT}")

    # Connection status
    daemon_icon = "🟢" if daemon_status == "RUNNING" else "🔴"
    ws_icon = "🟢" if websocket_status == "CONNECTED" else "🔴"

    line1 = f"Status: {daemon_icon} Daemon {daemon_status} | WebSocket: {ws_icon} {websocket_status}"
    print(f"{BoxChars.VERTICAL} {line1}{' ' * (75 - len(line1))}{BoxChars.VERTICAL}")

    # Session status
    print(f"{BoxChars.VERTICAL} {session_status}{' ' * (75 - len(session_status))}{BoxChars.VERTICAL}")

    print(f"{BoxChars.BOTTOM_LEFT}{BoxChars.HORIZONTAL * 76}{BoxChars.BOTTOM_RIGHT}")
```

---

## 🚀 Main CLI Implementation

### **src/cli/trader/trader_main.py** (~400 lines)

```python
"""
Main Trader CLI entry point.
Connects to daemon via WebSocket, displays real-time dashboard.
"""

import sys
import time
import sqlite3
import threading
from datetime import datetime
from realtime_client import TraderRealtimeClient
from ui_components import *

class TraderDashboard:
    """
    Main Trader CLI dashboard.
    """

    def __init__(self, account_id: int):
        self.account_id = account_id

        # UI state
        self.current_tab = 1  # Start on Overview tab
        self.running = True

        # Data state (loaded from SQLite + updated via WebSocket)
        self.pnl_data = {}
        self.positions = []
        self.orders = []
        self.lockouts = []
        self.enforcement_log = []
        self.quotes = {}

        # WebSocket client
        self.ws_client = TraderRealtimeClient(
            account_id=account_id,
            event_callback=self._on_event
        )

        # Database connection (for initial state + fallback)
        self.db = sqlite3.connect('data/state.db')

    def start(self):
        """Start dashboard - load initial state and connect WebSocket"""
        # Load initial state from SQLite
        self._load_initial_state()

        # Connect to WebSocket server
        self.ws_client.connect()

        # Wait for connection
        time.sleep(1)

        # Start UI loop
        self._ui_loop()

    def _load_initial_state(self):
        """Load initial state from SQLite database"""
        # Load P&L
        cursor = self.db.execute(
            "SELECT * FROM daily_pnl WHERE account_id = ? AND date = ?",
            (self.account_id, datetime.now().date())
        )
        row = cursor.fetchone()
        if row:
            self.pnl_data = {
                'realized': row[2],
                'unrealized': 0  # Will be calculated from positions + quotes
            }

        # Load positions
        cursor = self.db.execute(
            "SELECT * FROM positions WHERE account_id = ?",
            (self.account_id,)
        )
        self.positions = cursor.fetchall()

        # Load orders
        cursor = self.db.execute(
            "SELECT * FROM orders WHERE account_id = ?",
            (self.account_id,)
        )
        self.orders = cursor.fetchall()

        # Load lockouts
        cursor = self.db.execute(
            "SELECT * FROM lockouts WHERE account_id = ? AND locked_until > ?",
            (self.account_id, datetime.now())
        )
        self.lockouts = cursor.fetchall()

        # Load enforcement log (last 20)
        cursor = self.db.execute(
            "SELECT * FROM enforcement_log WHERE account_id = ? ORDER BY timestamp DESC LIMIT 20",
            (self.account_id,)
        )
        self.enforcement_log = cursor.fetchall()

    def _on_event(self, event_type: str, data: dict):
        """
        Called when WebSocket event received from daemon.
        Updates in-memory state and triggers UI refresh.
        """
        # Update state based on event type
        if event_type == "GatewayUserTrade":
            self._update_pnl_from_trade(data)

        elif event_type == "GatewayUserPosition":
            self._update_positions(data)

        elif event_type == "GatewayUserOrder":
            self._update_orders(data)

        elif event_type == "MarketQuote":
            self._update_quotes(data)

        elif event_type == "LockoutSet":
            self._update_lockouts(data)

        elif event_type == "EnforcementAction":
            self._update_enforcement_log(data)

        # Trigger UI refresh (next loop iteration will redraw)

    def _ui_loop(self):
        """Main UI loop - render dashboard and handle input"""
        while self.running:
            # Clear screen
            clear_screen()

            # Print header
            print_header("John Trader", self.account_id)

            # Print navigation menu
            print_nav_menu(self.current_tab)

            # Print current tab content
            if self.current_tab == 1:
                self._render_overview_tab()
            elif self.current_tab == 2:
                self._render_pnl_tab()
            elif self.current_tab == 3:
                self._render_positions_tab()
            # ... (other tabs)

            # Print status bar
            daemon_status = "RUNNING" if self.ws_client.is_connected() else "DISCONNECTED"
            ws_status = "CONNECTED" if self.ws_client.is_connected() else "DISCONNECTED"
            session_status = "🟢 Clocked In at 09:30:00 (5h 2m trading)"

            print_status_bar(daemon_status, ws_status, session_status)

            # Handle user input (non-blocking)
            # ... (tab switching, clock in/out, quit)

            # Refresh every 1 second
            time.sleep(1)

    def _render_overview_tab(self):
        """Render Overview tab (Tab 1)"""
        # P&L box
        pnl_content = [
            "Today's P&L",
            "─" * 70,
            f"Realized:    {format_pnl(self.pnl_data.get('realized', 0))}",
            f"Unrealized:  {format_pnl(self.pnl_data.get('unrealized', 0))}",
            f"Total:       {format_pnl(self.pnl_data.get('realized', 0) + self.pnl_data.get('unrealized', 0))}",
            "",
            f"Daily Loss Limit: $2,000  |  Remaining: $900 (45%)",
        ]
        print_box("", pnl_content)

        # Positions box
        # ... (render positions)

        # Lockouts box
        # ... (render lockouts)

    # ... (other tab rendering methods)

    def shutdown(self):
        """Shutdown dashboard"""
        self.running = False
        self.ws_client.disconnect()
        self.db.close()


# Entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Trader CLI Dashboard")
    parser.add_argument("--account-id", type=int, required=True, help="Account ID")
    args = parser.parse_args()

    dashboard = TraderDashboard(account_id=args.account_id)

    try:
        dashboard.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        dashboard.shutdown()
```

---

## 📝 Summary

**Key Points:**

1. **Real-time updates** via WebSocket (< 10ms latency from daemon events)
2. **Beautiful ANSI UI** with colors, boxes, and tables
3. **8 tabs** for different views (Overview, P&L, Positions, Rules, Connections, Holidays, Lockouts, Enforcement)
4. **Number-based navigation** (press 1-8 to switch tabs, Q to quit)
5. **Connection status monitoring** (daemon, WebSocket, TopstepX API)
6. **Clock in/out tracking** for trading sessions
7. **Read-only access** - trader cannot modify rules or bypass enforcement
8. **Hybrid data access** - WebSocket for real-time + SQLite for initial state/fallback

**Files to Implement:**
- `src/cli/trader/realtime_client.py` (~200 lines) - WebSocket client
- `src/cli/trader/ui_components.py` (~300 lines) - UI helpers (boxes, colors, formatting)
- `src/cli/trader/trader_main.py` (~400 lines) - Main dashboard loop

**Total: ~900 lines** (WebSocket client + UI components + main dashboard)

**Dependencies:**
- `websocket-client` library (for WebSocket client)
- `sqlite3` (built-in Python)
- ANSI terminal support (Windows Terminal, iTerm2, etc.)

---

**Next Step:** Create ADMIN_CLI_SPEC.md with clickable UI (based on examples/cli/admin/cli-clickable.py)
