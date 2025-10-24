# Core Modules Architecture

## Overview

The Simple Risk Manager daemon is built around **9 core modules** that provide centralized state management, enforcement, and coordination. All risk rules depend on these modules rather than implementing their own state tracking or API calls.

**Core Principle:** DRY (Don't Repeat Yourself) - each module provides a single source of truth for its domain.

---

## Module Catalog

### MOD-001: Enforcement Actions

**Purpose:** Centralized enforcement logic - all rules call these functions to execute actions.

**File:** `src/enforcement/actions.py`

**Methods:**
- `close_all_positions(account_id: int) -> bool`
  - Close all open positions via TopstepX API
  - Returns success/failure

- `close_position(account_id: int, contract_id: str) -> bool`
  - Close specific position

- `reduce_position_to_limit(account_id: int, contract_id: str, target_size: int) -> bool`
  - Partially close position to reach target size

- `cancel_all_orders(account_id: int) -> bool`
  - Cancel all pending orders

- `cancel_order(account_id: int, order_id: int) -> bool`
  - Cancel specific order

**Data Maintained:**
- None (stateless enforcement)
- Logs all actions to `enforcement_log` database table

**Dependencies:**
- `src/api/rest_client.py` - REST API wrapper
- `src/utils/logging.py` - Logging utilities

**Used By:** All enforcement rules (RULE-001, RULE-002, RULE-003, RULE-009, RULE-011, etc.)

**Status:** ✅ Implemented

---

### MOD-002: Lockout Manager

**Purpose:** Centralized lockout state management - all lockout rules call these functions.

**File:** `src/state/lockout_manager.py`

**Methods:**
- `set_lockout(account_id: int, reason: str, until: datetime) -> None`
  - Set hard lockout until specific datetime

- `set_cooldown(account_id: int, reason: str, duration_seconds: int) -> None`
  - Set lockout for specific duration
  - Uses MOD-003 (Timer Manager) for auto-expiry

- `is_locked_out(account_id: int) -> bool`
  - Check if account is currently locked out
  - Called by event_router before processing every event

- `get_lockout_info(account_id: int) -> dict | None`
  - Get lockout details for CLI display

- `clear_lockout(account_id: int) -> None`
  - Remove lockout (manual or auto-expiry)

- `check_expired_lockouts() -> None`
  - Background task to auto-clear expired lockouts
  - Called every second by daemon main loop

**Data Maintained:**
- In-memory: `lockout_state = {account_id: {reason, until, type, created_at}}`
- Persisted to: `lockouts` SQLite table

**Dependencies:**
- MOD-003 (Timer Manager) - For cooldown timers
- `src/state/persistence.py` - SQLite database
- `src/cli/trader/lockout_display.py` - CLI updates

**Used By:**
- RULE-003 (DailyRealizedLoss) - hard lockout
- RULE-006 (TradeFrequencyLimit) - cooldown
- RULE-007 (CooldownAfterLoss) - cooldown
- RULE-009 (SessionBlockOutside) - hard lockout
- RULE-011 (SymbolBlocks) - hard lockout
- `event_router.py` - checks lockout before processing events

**Status:** ✅ Implemented

---

### MOD-003: Timer Manager

**Purpose:** Countdown timers for cooldowns, session checks, and scheduled tasks.

**File:** `src/state/timer_manager.py`

**Methods:**
- `start_timer(name: str, duration: int, callback: callable) -> None`
  - Start countdown timer with callback
  - Example: `start_timer("lockout_123", 1800, lambda: clear_lockout(123))`

- `get_remaining_time(name: str) -> int`
  - Get seconds remaining on timer

- `check_timers() -> None`
  - Background task to check timers and fire callbacks
  - Called every second by daemon main loop

**Data Maintained:**
- In-memory only: `timers = {name: {expires_at, callback, duration}}`
- No persistence (timers recreated on restart)

**Dependencies:** None

**Used By:**
- MOD-002 (Lockout Manager) - for cooldown expiry
- RULE-009 (SessionBlockOutside) - for session timers

**Status:** ✅ Implemented

---

### MOD-004: Reset Scheduler

**Purpose:** Daily reset logic for P&L counters and holiday calendar integration.

**File:** `src/state/reset_scheduler.py`

**Methods:**
- `schedule_daily_reset(reset_time: str = "17:00", timezone: str = "America/New_York") -> None`
  - Schedule daily reset at specific time

- `reset_daily_counters(account_id: int) -> None`
  - Reset all daily counters (P&L, trade counts)
  - Clears daily lockouts

- `check_reset_time() -> None`
  - Background task to check if reset time reached
  - Called every minute

- `is_holiday(date: datetime) -> bool`
  - Check if date is a trading holiday
  - Reads from `config/holidays.yaml`

**Data Maintained:**
- In-memory: `reset_config = {time, timezone}`
- Persisted to: `reset_schedule` SQLite table

**Dependencies:**
- `config/holidays.yaml` - Holiday calendar

**Used By:**
- MOD-005 (PNL Tracker) - triggers `reset_daily_pnl()`
- MOD-008 (Trade Counter) - triggers `reset_session()`
- RULE-003, RULE-004, RULE-005 (daily P&L rules)
- RULE-009 (session/holiday checks)

**Status:** ✅ Implemented

---

### MOD-005: PNL Tracker

**Purpose:** Centralized P&L calculation and tracking - all rules call these functions.

**File:** `src/state/pnl_tracker.py`

**Methods:**
- `add_trade_pnl(account_id: int, pnl: float) -> float`
  - Add realized P&L from trade to daily total
  - Returns current daily realized P&L

- `get_daily_realized_pnl(account_id: int) -> float`
  - Get current daily realized P&L total

- `calculate_unrealized_pnl(account_id: int) -> float`
  - Calculate total unrealized P&L for all open positions
  - Uses state_manager for positions
  - Uses quote_tracker for current prices
  - Uses contract_cache for tick values

- `reset_daily_pnl(account_id: int) -> None`
  - Reset daily P&L counters
  - Called by MOD-004 at reset time

**Data Maintained:**
- In-memory: `daily_pnl = {account_id: realized_pnl}`
- Persisted to: `daily_pnl` SQLite table

**Dependencies:**
- MOD-009 (State Manager) - `get_all_positions()`
- MOD-006 (Quote Tracker) - `get_last_price()`
- MOD-007 (Contract Cache) - `get_contract()`
- `src/state/persistence.py` - SQLite operations

**Used By:**
- RULE-003 (DailyRealizedLoss)
- RULE-004 (DailyUnrealizedLoss)
- RULE-005 (MaxUnrealizedProfit)
- RULE-007 (CooldownAfterLoss)

**Status:** ✅ Implemented

---

### MOD-006: Quote Tracker

**Purpose:** Real-time price tracking from Market Hub - all rules call these functions.

**File:** `src/api/quote_tracker.py`

**Methods:**
- `get_last_price(contract_id: str) -> float | None`
  - Get most recent price for contract

- `update_quote(contract_id: str, quote_data: dict) -> None`
  - Update quote from GatewayQuote event
  - Called by `src/api/market_hub.py` on every event

- `is_quote_stale(contract_id: str, max_age_seconds: int = 10) -> bool`
  - Check if quote is too old

- `get_quote_age(contract_id: str) -> float | None`
  - Get seconds since last update

**Data Maintained:**
- In-memory only: `quotes = {contract_id: {lastPrice, bestBid, bestAsk, timestamp, lastUpdated}}`
- No persistence (real-time only)

**Dependencies:**
- API-INT-001: GatewayQuote event payload
- `src/api/market_hub.py` - Calls `update_quote()` on events

**Used By:**
- MOD-005 (PNL Tracker) - for unrealized P&L calculation
- RULE-004 (DailyUnrealizedLoss)
- RULE-005 (MaxUnrealizedProfit)
- RULE-012 (TradeManagement)

**Status:** ✅ Implemented

---

### MOD-007: Contract Cache

**Purpose:** Contract metadata caching (tick values, tick sizes) - all rules call these functions.

**File:** `src/api/contract_cache.py`

**Methods:**
- `get_contract(contract_id: str) -> dict`
  - Get contract metadata (fetches from API if not cached)
  - Returns: {id, tickSize, tickValue, symbolId, name}

- `cache_contract(contract_id: str, contract_data: dict) -> None`
  - Store contract in cache

- `get_tick_value(contract_id: str) -> float`
  - Get tick value for contract (shortcut)

- `get_tick_size(contract_id: str) -> float`
  - Get tick size for contract (shortcut)

**Data Maintained:**
- In-memory: `cache = {contract_id: {id, tickSize, tickValue, symbolId, name}}`
- Persisted to: `contract_cache` SQLite table (optional, for daemon restarts)

**Dependencies:**
- REST API: `POST /api/Contract/searchById`
- `src/api/rest_client.py` - API wrapper

**Used By:**
- MOD-005 (PNL Tracker) - for P&L calculations
- RULE-004 (DailyUnrealizedLoss)
- RULE-005 (MaxUnrealizedProfit)
- RULE-012 (TradeManagement)

**Status:** ✅ Implemented

---

### MOD-008: Trade Counter

**Purpose:** Track trade frequency across time windows (minute/hour/session) - RULE-006 calls these functions.

**File:** `src/state/trade_counter.py`

**Methods:**
- `record_trade(account_id: int, timestamp: datetime) -> dict`
  - Record a new trade and return current counts
  - Returns: {minute, hour, session} trade counts

- `get_trade_counts(account_id: int, current_time: datetime) -> dict`
  - Get trade counts for all time windows
  - Returns: {minute, hour, session}

- `reset_session(account_id: int) -> None`
  - Reset session trade count
  - Called by MOD-004 at reset time

- `get_session_start(account_id: int) -> datetime`
  - Get session start time

**Data Maintained:**
- In-memory:
  - `trade_history = {account_id: [timestamp, timestamp, ...]}`  (rolling 1-hour window)
  - `session_starts = {account_id: datetime}`
- Persisted to: `trade_history` and `session_state` SQLite tables

**Dependencies:**
- API-INT-001: GatewayUserTrade event
- `src/state/persistence.py` - SQLite operations
- MOD-004 (Reset Scheduler) - calls `reset_session()`

**Used By:**
- RULE-006 (TradeFrequencyLimit)

**Status:** ✅ Implemented

---

### MOD-009: State Manager

**Purpose:** Centralized position and order state tracking - all rules call these functions.

**File:** `src/state/state_manager.py`

**Methods:**

**Position Management:**
- `update_position(position_event: dict) -> None`
  - Update position from GatewayUserPosition event
  - Called by `src/api/user_hub.py` on every event

- `get_all_positions(account_id: int) -> list`
  - Get all open positions for account

- `get_position_count(account_id: int) -> int`
  - Get total contract count across all positions

- `get_positions_by_contract(account_id: int, contract_id: str) -> list`
  - Get positions for specific contract

- `get_contract_count(account_id: int, contract_id: str) -> int`
  - Get contract count for specific instrument

**Order Management:**
- `update_order(order_event: dict) -> None`
  - Update order from GatewayUserOrder event
  - Called by `src/api/user_hub.py` on every event

- `get_all_orders(account_id: int) -> list`
  - Get all working orders for account

- `get_orders_for_position(account_id: int, contract_id: str) -> list`
  - Get orders for specific position/contract

**Data Maintained:**
- In-memory:
  - `positions = {account_id: {position_id: {id, contractId, type, size, averagePrice, creationTimestamp}}}`
  - `orders = {account_id: {order_id: {id, accountId, contractId, type, side, size, limitPrice, stopPrice, state, creationTimestamp}}}`
- Persisted to: `positions` and `orders` SQLite tables

**Dependencies:**
- API-INT-001: GatewayUserPosition, GatewayUserOrder events
- `src/api/user_hub.py` - Calls `update_position()` and `update_order()` on events
- `src/state/persistence.py` - SQLite operations

**Used By:**
- MOD-005 (PNL Tracker) - for unrealized P&L calculation
- RULE-001 (MaxContracts)
- RULE-002 (MaxContractsPerInstrument)
- RULE-004 (DailyUnrealizedLoss)
- RULE-005 (MaxUnrealizedProfit)
- RULE-008 (NoStopLossGrace)
- RULE-009 (SessionBlockOutside)
- RULE-011 (SymbolBlocks)
- RULE-012 (TradeManagement)

**Status:** ✅ Implemented

---

## Module Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   TopstepX SignalR Events                    │
│         (GatewayUserPosition, GatewayUserOrder,              │
│          GatewayUserTrade, GatewayQuote)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     event_router.py                          │
│  1. Check lockout (MOD-002.is_locked_out)                   │
│  2. Update state (MOD-009.update_position/order)            │
│  3. Update quotes (MOD-006.update_quote)                    │
│  4. Record trades (MOD-008.record_trade)                    │
│  5. Add P&L (MOD-005.add_trade_pnl)                         │
│  6. Route to risk rules                                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Risk Rules Layer                        │
│  - RULE-001: MaxContracts                                   │
│  - RULE-002: MaxContractsPerInstrument                      │
│  - RULE-003: DailyRealizedLoss                              │
│  - RULE-004: DailyUnrealizedLoss                            │
│  - RULE-005: MaxUnrealizedProfit                            │
│  - RULE-006: TradeFrequencyLimit                            │
│  - RULE-007: CooldownAfterLoss                              │
│  - RULE-008: NoStopLossGrace                                │
│  - RULE-009: SessionBlockOutside                            │
│  - RULE-011: SymbolBlocks                                   │
│  - RULE-012: TradeManagement                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Module Dependencies (Rules Query)               │
│                                                              │
│  MOD-009 (State Manager)                                    │
│    ├─ get_all_positions(account_id)                         │
│    ├─ get_position_count(account_id)                        │
│    └─ get_all_orders(account_id)                            │
│                                                              │
│  MOD-005 (PNL Tracker)                                      │
│    ├─ get_daily_realized_pnl(account_id)                    │
│    ├─ calculate_unrealized_pnl(account_id)                  │
│    │    ├─ calls MOD-009.get_all_positions()                │
│    │    ├─ calls MOD-006.get_last_price()                   │
│    │    └─ calls MOD-007.get_contract()                     │
│    └─ add_trade_pnl(account_id, pnl)                        │
│                                                              │
│  MOD-008 (Trade Counter)                                    │
│    └─ get_trade_counts(account_id, current_time)            │
│                                                              │
│  MOD-002 (Lockout Manager)                                  │
│    └─ is_locked_out(account_id)                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          Enforcement Actions (Rule Violations)               │
│                                                              │
│  MOD-001 (Enforcement Actions)                              │
│    ├─ close_all_positions(account_id)                       │
│    ├─ close_position(account_id, contract_id)               │
│    ├─ cancel_all_orders(account_id)                         │
│    └─ reduce_position_to_limit(account_id, ...)             │
│                                                              │
│  MOD-002 (Lockout Manager)                                  │
│    ├─ set_lockout(account_id, reason, until)                │
│    ├─ set_cooldown(account_id, reason, duration)            │
│    │    └─ calls MOD-003.start_timer()                      │
│    └─ clear_lockout(account_id)                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                TopstepX REST API Calls                       │
│  - POST /api/Position/closeContract                         │
│  - POST /api/Order/cancel                                   │
│  - POST /api/Position/searchOpen                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Models

### Position Object Structure

**Source:** SPECS use **camelCase** (from TopstepX API payloads)

**In-Memory (Python):**
```python
{
    'id': 456,                              # position_id
    'contractId': 'CON.F.US.MNQ.U25',       # camelCase
    'type': 1,                              # 1=Long, 2=Short
    'size': 2,
    'averagePrice': 21000.25,               # camelCase
    'creationTimestamp': '2024-07-21T13:45:00Z'  # camelCase
}
```

**Database (SQLite):**
```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    account_id INTEGER,        -- snake_case
    contract_id TEXT,          -- snake_case
    type INTEGER,
    size INTEGER,
    average_price REAL,        -- snake_case
    created_at DATETIME        -- snake_case
);
```

**Conversion:**
- API events → camelCase → Python dict
- Python dict → converters → snake_case → SQLite
- SQLite → converters → camelCase → Python dict

---

### Order Object Structure

**In-Memory (Python):**
```python
{
    'id': 789,
    'accountId': 123,
    'contractId': 'CON.F.US.MNQ.U25',
    'type': 4,              # 1=Limit, 2=Market, 3=StopLimit, 4=Stop
    'side': 1,              # 0=Buy, 1=Sell
    'size': 2,
    'limitPrice': None,
    'stopPrice': 20950.00,
    'state': 2,             # 1=Pending, 2=Working, 3=Filled, 4=Cancelled
    'creationTimestamp': '2024-07-21T13:46:00Z'
}
```

**Database (SQLite):**
```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    account_id INTEGER,
    contract_id TEXT,
    type INTEGER,
    side INTEGER,
    size INTEGER,
    limit_price REAL,
    stop_price REAL,
    state INTEGER,
    created_at DATETIME
);
```

---

### Trade Object Structure

**In-Memory (Python):**
```python
{
    'id': 101112,
    'accountId': 123,
    'contractId': 'CON.F.US.MNQ.U25',
    'quantity': 2,
    'profitAndLoss': -45.50,        # camelCase
    'executionTime': '2024-07-21T14:45:15Z'
}
```

**Database (SQLite):**
```sql
CREATE TABLE trade_history (
    id INTEGER PRIMARY KEY,
    account_id INTEGER,
    timestamp DATETIME,
    contract_id TEXT,
    pnl REAL
);
```

---

### Quote Object Structure

**In-Memory (Python):**
```python
{
    'contractId': 'CON.F.US.MNQ.U25',
    'lastPrice': 21000.50,
    'bestBid': 21000.25,
    'bestAsk': 21000.75,
    'timestamp': '2024-07-21T13:45:00Z',
    'lastUpdated': datetime(2024, 7, 21, 13, 45, 1)
}
```

**No Database Persistence** (real-time only)

---

### ContractMetadata Object Structure

**In-Memory (Python):**
```python
{
    'id': 'CON.F.US.MNQ.U25',
    'tickSize': 0.25,
    'tickValue': 0.5,
    'symbolId': 'F.US.MNQ',
    'name': 'MNQU5'
}
```

**Database (SQLite):**
```sql
CREATE TABLE contract_cache (
    contract_id TEXT PRIMARY KEY,
    tick_size REAL,
    tick_value REAL,
    symbol_id TEXT,
    name TEXT,
    cached_at DATETIME
);
```

---

### Account Object Structure

**In-Memory (Python):**
```python
{
    'accountId': 123,
    'username': 'trader@example.com'
}
```

**No direct database storage** (loaded from config)

---

## Integration with Converters

**Converters Location:** `src/utils/converters.py`

**Conversion Flow:**

1. **API Event → Python Dict** (camelCase preserved)
   ```python
   position_event = {
       'accountId': 123,
       'contractId': 'CON.F.US.MNQ.U25',
       'averagePrice': 21000.25
   }
   ```

2. **Python Dict → Database** (snake_case conversion)
   ```python
   from src.utils.converters import camel_to_snake_dict

   db_data = camel_to_snake_dict(position_event)
   # Result: {'account_id': 123, 'contract_id': '...', 'average_price': 21000.25}
   ```

3. **Database → Python Dict** (camelCase conversion)
   ```python
   from src.utils.converters import snake_to_camel_dict

   position_dict = snake_to_camel_dict(db_row)
   # Result: {'accountId': 123, 'contractId': '...', 'averagePrice': 21000.25}
   ```

**Module Integration:**
- **MOD-009 (State Manager):** Receives camelCase from API, stores snake_case in DB
- **MOD-005 (PNL Tracker):** Works with camelCase in memory, stores snake_case in DB
- **MOD-007 (Contract Cache):** Receives camelCase from API, stores snake_case in DB

---

## Persistence Strategy

### In-Memory Only (No Database)

**MOD-003: Timer Manager**
- Timers are ephemeral (recreated on restart)
- No state to persist

**MOD-006: Quote Tracker**
- Quotes are real-time only
- Stale after daemon restart (re-subscribe to Market Hub)

---

### Hybrid (In-Memory + Database)

**MOD-002: Lockout Manager**
- In-memory: `lockout_state` dict
- Database: `lockouts` table
- On startup: Load active lockouts from DB

**MOD-005: PNL Tracker**
- In-memory: `daily_pnl` dict
- Database: `daily_pnl` table
- On startup: Load today's P&L from DB

**MOD-007: Contract Cache**
- In-memory: `cache` dict
- Database: `contract_cache` table (optional)
- On startup: Load cache from DB (avoids API calls)

**MOD-008: Trade Counter**
- In-memory: `trade_history` list (rolling 1-hour window)
- Database: `trade_history` table (last 7 days)
- On startup: Load last hour of trades from DB

**MOD-009: State Manager**
- In-memory: `positions` and `orders` dicts
- Database: `positions` and `orders` tables
- On startup: Load open positions and working orders from DB

---

### Database-Only (Audit Trail)

**MOD-001: Enforcement Actions**
- No in-memory state
- All actions logged to `enforcement_log` table
- Append-only (never deleted, except old records)

**MOD-004: Reset Scheduler**
- Minimal in-memory state (`reset_config`)
- Database: `reset_schedule` table
- Tracks last reset to prevent double-resets

---

## Initialization Order

When daemon starts:

1. **Database Connection** (`src/state/persistence.py`)
   - Connect to `data/state.db`
   - Validate schema exists

2. **MOD-004: Reset Scheduler**
   - Load reset config
   - Check if daily reset needed
   - If yes, reset P&L and trade counters

3. **MOD-007: Contract Cache**
   - Load contract metadata from DB
   - Populate in-memory cache

4. **MOD-002: Lockout Manager**
   - Load active lockouts from DB
   - Check for expired lockouts

5. **MOD-005: PNL Tracker**
   - Load today's daily P&L from DB
   - Initialize in-memory state

6. **MOD-008: Trade Counter**
   - Load last hour of trades from DB
   - Load session start time

7. **MOD-009: State Manager**
   - Load open positions from DB
   - Load working orders from DB
   - Populate in-memory dicts

8. **MOD-006: Quote Tracker**
   - Initialize empty quotes dict
   - (Quotes populated when Market Hub connects)

9. **MOD-003: Timer Manager**
   - Initialize empty timers dict
   - Start background timer check loop

10. **API Connections**
    - Connect to SignalR User Hub
    - Connect to SignalR Market Hub
    - Subscribe to position/order/trade events
    - Subscribe to quote events for open positions

11. **Background Tasks**
    - Start lockout expiry check (every second)
    - Start timer check (every second)
    - Start reset time check (every minute)

---

## Shutdown Sequence

1. **Disconnect SignalR** (User Hub, Market Hub)

2. **Stop Background Tasks**
   - Stop timer checks
   - Stop lockout checks
   - Stop reset checks

3. **Flush State to Database**
   - MOD-002: Save lockouts
   - MOD-005: Save daily P&L
   - MOD-008: Save trade history
   - MOD-009: Save positions and orders

4. **Close Database Connection**

---

## Thread Safety

### Thread-Safe Modules

**MOD-002: Lockout Manager**
- Uses `threading.Lock()` for `lockout_state` dict access
- Database writes are synchronous (SQLite handles locking)

**MOD-005: PNL Tracker**
- Uses `threading.Lock()` for `daily_pnl` dict access

**MOD-008: Trade Counter**
- Uses `threading.Lock()` for `trade_history` list access

**MOD-009: State Manager**
- Uses `threading.Lock()` for `positions` and `orders` dict access

---

### Single-Threaded (No Locking Needed)

**MOD-001: Enforcement Actions**
- Stateless (no shared state)

**MOD-003: Timer Manager**
- Accessed only from main event loop (single thread)

**MOD-004: Reset Scheduler**
- Minimal state, accessed from background thread only

**MOD-006: Quote Tracker**
- Write-only from Market Hub thread
- Read-only from rule evaluation thread
- No contention (quotes dict grows but never shrinks during runtime)

**MOD-007: Contract Cache**
- Write once, read many
- No contention after initial population

---

## SPECS Files Analyzed

### Core Modules SPECS
1. `/project-specs/SPECS/04-CORE-MODULES/modules/enforcement_actions.md` (MOD-001)
2. `/project-specs/SPECS/04-CORE-MODULES/modules/lockout_manager.md` (MOD-002)
3. `/project-specs/SPECS/04-CORE-MODULES/modules/timer_manager.md` (MOD-003)
4. `/project-specs/SPECS/04-CORE-MODULES/modules/reset_scheduler.md` (MOD-004)
5. `/project-specs/SPECS/04-CORE-MODULES/modules/pnl_tracker.md` (MOD-005)
6. `/project-specs/SPECS/04-CORE-MODULES/modules/quote_tracker.md` (MOD-006)
7. `/project-specs/SPECS/04-CORE-MODULES/modules/contract_cache.md` (MOD-007)
8. `/project-specs/SPECS/04-CORE-MODULES/modules/trade_counter.md` (MOD-008)
9. `/project-specs/SPECS/04-CORE-MODULES/modules/state_manager.md` (MOD-009)

### Data Models SPECS
10. `/project-specs/SPECS/07-DATA-MODELS/STATE_OBJECTS.md`
11. `/project-specs/SPECS/07-DATA-MODELS/DATABASE_SCHEMA.md`

---

## Summary

✅ **All 9 core modules documented**
✅ **Complete method signatures and data structures**
✅ **Module interaction patterns identified**
✅ **Persistence strategy defined**
✅ **Initialization and shutdown sequences specified**
✅ **Thread safety requirements documented**
✅ **Converter integration clarified (camelCase ↔ snake_case)**

**Next Steps for Implementation:**
1. Implement converters (`src/utils/converters.py`)
2. Implement persistence layer (`src/state/persistence.py`)
3. Implement modules in dependency order:
   - MOD-003 (no dependencies)
   - MOD-004 (no dependencies)
   - MOD-007 (no dependencies)
   - MOD-006 (no dependencies)
   - MOD-002 (depends on MOD-003)
   - MOD-009 (no dependencies)
   - MOD-008 (depends on MOD-004)
   - MOD-005 (depends on MOD-006, MOD-007, MOD-009)
   - MOD-001 (no dependencies, calls REST API)
