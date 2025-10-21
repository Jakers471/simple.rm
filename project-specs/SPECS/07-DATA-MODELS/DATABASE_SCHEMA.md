# DATABASE_SCHEMA.md

**Status:** Complete
**Purpose:** SQLite database schema for all 9 modules
**Database File:** `data/state.db`
**Last Updated:** 2025-10-21

---

## 🎯 Schema Overview

This database stores state for all 9 core modules, enabling:
- Crash recovery (reload state on daemon restart)
- Audit trail (enforcement actions, trade history)
- Persistence (lockouts, PNL, contract cache)

**Modules Covered:**
- MOD-001: Enforcement Actions (audit log)
- MOD-002: Lockout Manager (lockout state)
- MOD-003: Timer Manager (no persistence - in-memory only)
- MOD-004: Reset Scheduler (last reset tracking)
- MOD-005: PNL Tracker (daily realized P&L)
- MOD-006: Quote Tracker (no persistence - real-time only)
- MOD-007: Contract Cache (contract metadata)
- MOD-008: Trade Counter (trade history)
- MOD-009: State Manager (positions, orders)

---

## 📊 Schema Diagram

```
┌─────────────────┐
│   lockouts      │  ← MOD-002: Current lockout state
├─────────────────┤
│ account_id (PK) │
│ is_locked       │
│ reason          │
│ locked_at       │
│ locked_until    │
│ rule_id         │
└─────────────────┘

┌──────────────────┐
│  daily_pnl       │  ← MOD-005: Daily realized P&L
├──────────────────┤
│ account_id       │
│ date (PK)        │
│ realized_pnl     │
│ last_updated     │
└──────────────────┘

┌──────────────────┐
│ contract_cache   │  ← MOD-007: Contract metadata
├──────────────────┤
│ contract_id (PK) │
│ tick_size        │
│ tick_value       │
│ symbol_id        │
│ name             │
│ cached_at        │
└──────────────────┘

┌──────────────────┐
│ trade_history    │  ← MOD-008: Trade timestamps
├──────────────────┤
│ id (PK)          │
│ account_id       │
│ timestamp        │
│ contract_id      │
│ pnl              │
└──────────────────┘

┌──────────────────┐
│ session_state    │  ← MOD-008: Session start time
├──────────────────┤
│ account_id (PK)  │
│ session_start    │
└──────────────────┘

┌──────────────────┐
│  positions       │  ← MOD-009: Current positions
├──────────────────┤
│ id (PK)          │
│ account_id       │
│ contract_id      │
│ type             │
│ size             │
│ average_price    │
│ created_at       │
│ updated_at       │
└──────────────────┘

┌──────────────────┐
│    orders        │  ← MOD-009: Current orders
├──────────────────┤
│ id (PK)          │
│ account_id       │
│ contract_id      │
│ type             │
│ side             │
│ size             │
│ limit_price      │
│ stop_price       │
│ state            │
│ created_at       │
│ updated_at       │
└──────────────────┘

┌──────────────────┐
│ enforcement_log  │  ← MOD-001: Enforcement audit trail
├──────────────────┤
│ id (PK)          │
│ timestamp        │
│ account_id       │
│ rule_id          │
│ action           │
│ reason           │
│ success          │
│ details          │
└──────────────────┘

┌──────────────────┐
│  reset_schedule  │  ← MOD-004: Daily reset tracking
├──────────────────┤
│ account_id (PK)  │
│ last_reset_date  │
│ next_reset_time  │
│ reset_time_config│
└──────────────────┘
```

---

## 📝 Table Definitions

### **1. lockouts** (MOD-002: Lockout Manager)

**Purpose:** Store current lockout state for each account.

```sql
CREATE TABLE lockouts (
    account_id INTEGER PRIMARY KEY,
    is_locked BOOLEAN NOT NULL DEFAULT 0,
    reason TEXT,
    locked_at DATETIME,
    locked_until DATETIME,
    rule_id TEXT,  -- Which rule caused lockout (e.g., "RULE-003")
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lockouts_until ON lockouts(locked_until);
```

**Columns:**
- `account_id`: TopstepX account ID
- `is_locked`: Boolean - true if currently locked out
- `reason`: Human-readable lockout reason (e.g., "Daily loss limit: -$550")
- `locked_at`: When lockout started
- `locked_until`: When lockout expires (NULL for indefinite locks)
- `rule_id`: Which rule triggered lockout (RULE-003, RULE-004, etc.)

**Usage:**
- Background task checks `locked_until` every second to auto-unlock expired lockouts
- `lockout_manager.is_locked_out(account_id)` queries this table
- Updated on every lockout set/clear

---

### **2. daily_pnl** (MOD-005: PNL Tracker)

**Purpose:** Track daily realized P&L per account.

```sql
CREATE TABLE daily_pnl (
    account_id INTEGER NOT NULL,
    date DATE NOT NULL,
    realized_pnl REAL NOT NULL DEFAULT 0.0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (account_id, date)
);

CREATE INDEX idx_daily_pnl_date ON daily_pnl(date);
```

**Columns:**
- `account_id`: TopstepX account ID
- `date`: Trading date (YYYY-MM-DD)
- `realized_pnl`: Cumulative realized P&L for the day
- `last_updated`: Last trade timestamp

**Usage:**
- Updated on every `GatewayUserTrade` event with P&L
- Reset at `reset_time` (5:00 PM) by MOD-004
- RULE-003 (DailyRealizedLoss) queries this for breach detection

**Cleanup:**
- Keep last 90 days for reporting
- Delete older rows: `DELETE FROM daily_pnl WHERE date < date('now', '-90 days')`

---

### **3. contract_cache** (MOD-007: Contract Cache)

**Purpose:** Cache contract metadata (tick size, tick value) to avoid repeated API calls.

```sql
CREATE TABLE contract_cache (
    contract_id TEXT PRIMARY KEY,
    tick_size REAL NOT NULL,
    tick_value REAL NOT NULL,
    symbol_id TEXT NOT NULL,
    name TEXT,
    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contract_cache_symbol ON contract_cache(symbol_id);
```

**Columns:**
- `contract_id`: TopstepX contract ID (e.g., "CON.F.US.MNQ.U25")
- `tick_size`: Minimum price increment (e.g., 0.25)
- `tick_value`: Dollar value per tick (e.g., $0.50 for MNQ)
- `symbol_id`: Root symbol (e.g., "F.US.MNQ")
- `name`: Contract name (e.g., "MNQU5")
- `cached_at`: When metadata was cached

**Usage:**
- First time we see a contract, fetch from `/api/Contract/searchById` and cache
- MOD-005 (PNL Tracker) uses this for unrealized P&L calculations
- RULE-004, RULE-005, RULE-012 use this

**Cleanup:**
- No cleanup needed (contract specs don't change)
- Optionally clear cache older than 1 year

---

### **4. trade_history** (MOD-008: Trade Counter)

**Purpose:** Track trade timestamps for frequency limits.

```sql
CREATE TABLE trade_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    contract_id TEXT NOT NULL,
    pnl REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trade_history_account_time ON trade_history(account_id, timestamp DESC);
CREATE INDEX idx_trade_history_timestamp ON trade_history(timestamp);
```

**Columns:**
- `id`: Auto-incrementing primary key
- `account_id`: TopstepX account ID
- `timestamp`: Trade execution time (from `GatewayUserTrade.creationTimestamp`)
- `contract_id`: Which contract was traded
- `pnl`: Realized P&L (can be NULL for half-turn trades)

**Usage:**
- Inserted on every `GatewayUserTrade` event
- RULE-006 (TradeFrequencyLimit) queries this for rolling windows:
  - Last 60 seconds (per_minute limit)
  - Last 60 minutes (per_hour limit)
  - Since session start (per_session limit)

**Cleanup:**
- Keep last 7 days for audit trail
- Delete older rows: `DELETE FROM trade_history WHERE timestamp < datetime('now', '-7 days')`
- Run cleanup daily at midnight

---

### **5. session_state** (MOD-008: Trade Counter)

**Purpose:** Track when current trading session started.

```sql
CREATE TABLE session_state (
    account_id INTEGER PRIMARY KEY,
    session_start DATETIME NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Columns:**
- `account_id`: TopstepX account ID
- `session_start`: When current session started (typically last reset time)

**Usage:**
- Updated at daily reset time by MOD-004
- RULE-006 uses this to count trades since session start
- On daemon restart, if no row exists, use today's reset time

---

### **6. positions** (MOD-009: State Manager)

**Purpose:** Mirror TopstepX open positions for crash recovery.

```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,  -- TopstepX position ID
    account_id INTEGER NOT NULL,
    contract_id TEXT NOT NULL,
    type INTEGER NOT NULL,  -- 1=Long, 2=Short
    size INTEGER NOT NULL,
    average_price REAL NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_positions_account ON positions(account_id);
CREATE INDEX idx_positions_contract ON positions(contract_id);
```

**Columns:**
- `id`: TopstepX position ID (from `GatewayUserPosition.id`)
- `account_id`: TopstepX account ID
- `contract_id`: Contract ID (e.g., "CON.F.US.MNQ.U25")
- `type`: Position type (1=Long, 2=Short)
- `size`: Contract count
- `average_price`: Entry price
- `created_at`: Position open time

**Usage:**
- Updated on every `GatewayUserPosition` event
- Deleted when position size = 0 (position closed)
- On daemon restart, reload all positions into memory
- RULE-001, RULE-002, RULE-004, RULE-005, RULE-009, RULE-011 query this

**Cleanup:**
- Closed positions automatically deleted (size=0 triggers delete)
- No manual cleanup needed

---

### **7. orders** (MOD-009: State Manager)

**Purpose:** Mirror TopstepX working orders for crash recovery.

```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,  -- TopstepX order ID
    account_id INTEGER NOT NULL,
    contract_id TEXT NOT NULL,
    type INTEGER NOT NULL,  -- OrderType enum (1=Limit, 2=Market, 3=StopLimit, 4=Stop, 5=TrailingStop)
    side INTEGER NOT NULL,  -- 0=Buy, 1=Sell
    size INTEGER NOT NULL,
    limit_price REAL,
    stop_price REAL,
    state INTEGER NOT NULL,  -- OrderState enum (1=Pending, 2=Working, 3=Filled, 4=Cancelled, 5=Rejected)
    created_at DATETIME NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_account ON orders(account_id);
CREATE INDEX idx_orders_contract ON orders(contract_id);
CREATE INDEX idx_orders_state ON orders(state);
```

**Columns:**
- `id`: TopstepX order ID (from `GatewayUserOrder.id`)
- `account_id`: TopstepX account ID
- `contract_id`: Contract ID
- `type`: OrderType (1=Limit, 2=Market, 3=StopLimit, 4=Stop, 5=TrailingStop)
- `side`: OrderSide (0=Buy, 1=Sell)
- `size`: Order quantity
- `limit_price`: Limit price (NULL for market/stop orders)
- `stop_price`: Stop price (NULL for market/limit orders)
- `state`: OrderState (1=Pending, 2=Working, 3=Filled, 4=Cancelled, 5=Rejected)

**Usage:**
- Updated on every `GatewayUserOrder` event
- Deleted when state = 3, 4, or 5 (filled, cancelled, rejected)
- On daemon restart, reload all working orders into memory
- RULE-008 (NoStopLossGrace) and RULE-012 (TradeManagement) query this

**Cleanup:**
- Completed orders automatically deleted (state 3, 4, 5 triggers delete)
- No manual cleanup needed

---

### **8. enforcement_log** (MOD-001: Enforcement Actions)

**Purpose:** Audit trail of all enforcement actions.

```sql
CREATE TABLE enforcement_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    account_id INTEGER NOT NULL,
    rule_id TEXT NOT NULL,  -- e.g., "RULE-003"
    action TEXT NOT NULL,   -- e.g., "close_all_positions", "set_lockout"
    reason TEXT NOT NULL,   -- e.g., "Daily loss limit: -$550"
    success BOOLEAN NOT NULL DEFAULT 1,
    details TEXT,           -- JSON details (positions closed, orders cancelled, etc.)
    execution_time_ms INTEGER  -- How long enforcement took
);

CREATE INDEX idx_enforcement_account ON enforcement_log(account_id);
CREATE INDEX idx_enforcement_timestamp ON enforcement_log(timestamp DESC);
CREATE INDEX idx_enforcement_rule ON enforcement_log(rule_id);
```

**Columns:**
- `id`: Auto-incrementing primary key
- `timestamp`: When enforcement action executed
- `account_id`: TopstepX account ID
- `rule_id`: Which rule triggered enforcement
- `action`: Action taken (close_all_positions, cancel_all_orders, set_lockout, etc.)
- `reason`: Why enforcement was triggered
- `success`: Whether enforcement succeeded
- `details`: JSON string with details (positions closed, errors, etc.)
- `execution_time_ms`: Performance tracking

**Usage:**
- Inserted on every enforcement action by MOD-001
- Used for reporting, analytics, debugging
- Admin CLI can query this for enforcement history

**Example details JSON:**
```json
{
  "positions_closed": 2,
  "orders_cancelled": 1,
  "lockout_until": "2025-10-21T17:00:00",
  "pnl_at_enforcement": -550.25
}
```

**Cleanup:**
- Keep 1 year for audit compliance
- Delete older rows: `DELETE FROM enforcement_log WHERE timestamp < datetime('now', '-1 year')`

---

### **9. reset_schedule** (MOD-004: Reset Scheduler)

**Purpose:** Track daily reset times to prevent double-resets.

```sql
CREATE TABLE reset_schedule (
    account_id INTEGER PRIMARY KEY,
    last_reset_date DATE NOT NULL,
    next_reset_time DATETIME NOT NULL,
    reset_time_config TEXT NOT NULL,  -- "17:00" from config
    timezone TEXT NOT NULL  -- "America/New_York"
);
```

**Columns:**
- `account_id`: TopstepX account ID
- `last_reset_date`: Date of last reset (to prevent double-reset)
- `next_reset_time`: Calculated next reset datetime
- `reset_time_config`: Configured reset time (e.g., "17:00")
- `timezone`: Configured timezone

**Usage:**
- Updated after each daily reset
- Checked at startup to see if reset needed
- Prevents resetting twice if daemon restarts near reset time

---

## 🔄 State Recovery on Daemon Restart

**When daemon restarts, it loads state in this order:**

1. **Load lockouts** → Restore lockout state from `lockouts` table
2. **Load daily PNL** → Restore today's P&L from `daily_pnl` table
3. **Load contract cache** → Restore contract metadata from `contract_cache` table
4. **Load session state** → Restore session start from `session_state` table
5. **Load positions** → Restore open positions from `positions` table
6. **Load orders** → Restore working orders from `orders` table
7. **Load reset schedule** → Check if daily reset needed from `reset_schedule` table

**Then:**
- Re-connect to SignalR (User Hub + Market Hub)
- Subscribe to quotes for open positions
- Resume event processing

---

## 🧹 Cleanup & Maintenance

**Daily Cleanup Job (runs at midnight):**
```sql
-- Delete old trade history (keep 7 days)
DELETE FROM trade_history WHERE timestamp < datetime('now', '-7 days');

-- Delete old enforcement logs (keep 1 year)
DELETE FROM enforcement_log WHERE timestamp < datetime('now', '-1 year');

-- Delete old daily PNL (keep 90 days)
DELETE FROM daily_pnl WHERE date < date('now', '-90 days');

-- Vacuum database to reclaim space
VACUUM;
```

**Weekly Backup:**
- Copy `state.db` to `data/backups/state_YYYY-MM-DD.db`
- Keep last 4 weeks of backups
- Delete backups older than 30 days

---

## 📊 Database Statistics

**Expected Sizes (for 1 account, 1 year):**

| Table | Rows/Year | Size Estimate |
|-------|-----------|---------------|
| `lockouts` | 1 | < 1 KB |
| `daily_pnl` | 365 | < 50 KB |
| `contract_cache` | ~50 | < 10 KB |
| `trade_history` | ~10,000 | ~500 KB |
| `session_state` | 1 | < 1 KB |
| `positions` | 0-10 | < 5 KB |
| `orders` | 0-20 | < 10 KB |
| `enforcement_log` | ~1,000 | ~200 KB |
| `reset_schedule` | 1 | < 1 KB |
| **TOTAL** | | **~800 KB** |

**After cleanup (7-day trade history, 90-day PNL):**
- Expected size: ~100 KB
- SQLite performs well up to 100 MB
- No performance concerns

---

## 🔒 Database Integrity

**Foreign Key Constraints:**
- None (TopstepX IDs are external, can't enforce FK)
- Orphaned records cleaned by event processing (position closes, order fills)

**Transaction Strategy:**
- Critical updates (lockouts, PNL): Synchronous, single transaction
- Bulk updates (positions, orders): Batched transactions
- Read-heavy tables (contract_cache): No transactions needed

**Backup on Schema Change:**
```bash
# Before applying schema changes
cp data/state.db data/backups/state_pre_migration_$(date +%Y%m%d).db
```

---

## 🚀 Initial Schema Creation

**File:** `scripts/init_database.sql`

```sql
-- Create all tables in order
CREATE TABLE IF NOT EXISTS lockouts (...);
CREATE TABLE IF NOT EXISTS daily_pnl (...);
CREATE TABLE IF NOT EXISTS contract_cache (...);
CREATE TABLE IF NOT EXISTS trade_history (...);
CREATE TABLE IF NOT EXISTS session_state (...);
CREATE TABLE IF NOT EXISTS positions (...);
CREATE TABLE IF NOT EXISTS orders (...);
CREATE TABLE IF NOT EXISTS enforcement_log (...);
CREATE TABLE IF NOT EXISTS reset_schedule (...);

-- Create all indexes
CREATE INDEX IF NOT EXISTS idx_lockouts_until ON lockouts(locked_until);
-- ... (all other indexes)

-- Initial data
INSERT OR IGNORE INTO session_state (account_id, session_start)
VALUES (?, datetime('now', 'start of day', '+17 hours'));
```

**Run on first startup:**
```python
def init_database(account_id):
    with sqlite3.connect('data/state.db') as db:
        db.executescript(open('scripts/init_database.sql').read())
        db.execute("INSERT OR IGNORE INTO session_state (account_id, session_start) VALUES (?, datetime('now'))", (account_id,))
        db.commit()
```

---

## ✅ Schema Validation

**On daemon startup, verify schema exists:**

```python
def validate_schema():
    required_tables = [
        'lockouts', 'daily_pnl', 'contract_cache', 'trade_history',
        'session_state', 'positions', 'orders', 'enforcement_log', 'reset_schedule'
    ]

    with sqlite3.connect('data/state.db') as db:
        cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        missing = set(required_tables) - existing_tables
        if missing:
            raise Exception(f"Missing database tables: {missing}. Run init_database.sql")
```

---

**This schema supports all 9 modules and provides complete crash recovery, audit trail, and performance optimization.**
