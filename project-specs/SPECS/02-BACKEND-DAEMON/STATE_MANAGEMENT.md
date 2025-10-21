# STATE_MANAGEMENT.md

**Status:** Complete
**Purpose:** In-memory state + SQLite persistence strategy for all 9 modules
**Last Updated:** 2025-10-21

---

## 🎯 Overview

The Risk Manager uses a **hybrid state management strategy**:
- **In-memory:** Fast lookups for real-time event processing
- **SQLite:** Persistence for crash recovery and audit trail
- **Sync strategy:** Critical writes are synchronous, bulk writes are batched

This document explains how each of the 9 modules manages state.

---

## 📊 State Management Strategy by Module

| Module | In-Memory | SQLite | Write Strategy | Recovery Needed |
|--------|-----------|--------|----------------|-----------------|
| **MOD-001** | No | Yes (log only) | Async insert | No |
| **MOD-002** | Yes (dict) | Yes (sync) | Immediate sync | Yes (critical) |
| **MOD-003** | Yes (dict) | No | N/A | No |
| **MOD-004** | Yes (datetime) | Yes (sync) | Daily update | Yes |
| **MOD-005** | Yes (dict) | Yes (sync) | Immediate sync | Yes (critical) |
| **MOD-006** | Yes (dict) | No | N/A | No |
| **MOD-007** | Yes (dict) | Yes (lazy) | Lazy write | Yes |
| **MOD-008** | Yes (list) | Yes (async) | Async insert | Yes |
| **MOD-009** | Yes (dict) | Yes (batched) | Batched writes | Yes |

**Legend:**
- **Sync:** Write immediately to SQLite (critical data)
- **Async:** Background thread writes (non-critical)
- **Batched:** Write every N seconds (performance)
- **Lazy:** Write only when new data added (cache)

---

## 🔧 MOD-001: Enforcement Actions

**Purpose:** Audit trail of enforcement actions

### **In-Memory State:**
```python
# NO in-memory state (stateless module)
# Just logs to database and files
```

### **SQLite Persistence:**
```python
# Table: enforcement_log
# Strategy: Async insert (don't block enforcement execution)

def log_enforcement(account_id, rule_id, action, reason, success, details):
    """Log enforcement action (non-blocking)."""

    # Add to async write queue
    enforcement_queue.put({
        'timestamp': datetime.now(),
        'account_id': account_id,
        'rule_id': rule_id,
        'action': action,
        'reason': reason,
        'success': success,
        'details': json.dumps(details)
    })

    # Background thread processes queue
```

### **Background Writer:**
```python
def enforcement_log_writer():
    """Background thread - writes enforcement logs to SQLite."""
    while daemon_running:
        batch = []

        # Collect up to 10 logs or wait 5 seconds
        try:
            batch.append(enforcement_queue.get(timeout=5))
            for _ in range(9):  # Get up to 9 more
                batch.append(enforcement_queue.get_nowait())
        except queue.Empty:
            pass

        if batch:
            with sqlite3.connect('data/state.db') as db:
                db.executemany(
                    """INSERT INTO enforcement_log
                       (timestamp, account_id, rule_id, action, reason, success, details)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    [(b['timestamp'], b['account_id'], b['rule_id'],
                      b['action'], b['reason'], b['success'], b['details'])
                     for b in batch]
                )
                db.commit()
```

### **Recovery:**
- **Not needed** - Historical data only, doesn't affect runtime state

---

## 🔧 MOD-002: Lockout Manager

**Purpose:** Manage account lockout state

### **In-Memory State:**
```python
# Dictionary: account_id -> lockout info
lockouts = {
    123: {
        'is_locked': True,
        'reason': 'Daily loss limit: -$550',
        'locked_at': datetime(2025, 10, 21, 10, 30, 0),
        'locked_until': datetime(2025, 10, 21, 17, 0, 0),
        'rule_id': 'RULE-003'
    }
}
```

### **SQLite Persistence:**
```python
# Table: lockouts
# Strategy: Immediate sync (critical - can't lose lockout state)

def set_lockout(account_id, reason, until, rule_id):
    """Set lockout - SYNC write."""

    # Update in-memory
    lockouts[account_id] = {
        'is_locked': True,
        'reason': reason,
        'locked_at': datetime.now(),
        'locked_until': until,
        'rule_id': rule_id
    }

    # Immediately sync to SQLite (critical!)
    with sqlite3.connect('data/state.db') as db:
        db.execute("""
            INSERT OR REPLACE INTO lockouts
            (account_id, is_locked, reason, locked_at, locked_until, rule_id, updated_at)
            VALUES (?, 1, ?, ?, ?, ?, ?)
        """, (account_id, reason, lockouts[account_id]['locked_at'], until, rule_id, datetime.now()))
        db.commit()

def clear_lockout(account_id):
    """Clear lockout - SYNC write."""

    # Update in-memory
    if account_id in lockouts:
        lockouts[account_id]['is_locked'] = False
        lockouts[account_id]['locked_until'] = None

    # Immediately sync to SQLite
    with sqlite3.connect('data/state.db') as db:
        db.execute("""
            UPDATE lockouts
            SET is_locked = 0, locked_until = NULL, updated_at = ?
            WHERE account_id = ?
        """, (datetime.now(), account_id))
        db.commit()

def is_locked_out(account_id):
    """Check lockout - in-memory lookup (FAST)."""
    if account_id not in lockouts:
        return False
    return lockouts[account_id]['is_locked']
```

### **Background Task:**
```python
def check_expired_lockouts():
    """Called every second - auto-unlock expired lockouts."""
    now = datetime.now()

    for account_id, lockout in list(lockouts.items()):
        if lockout['is_locked'] and lockout['locked_until']:
            if now >= lockout['locked_until']:
                clear_lockout(account_id)
                logger.info(f"Auto-unlocked account {account_id} (lockout expired)")
```

### **Recovery:**
```python
def load_lockouts():
    """Load lockouts from SQLite on daemon startup."""
    with sqlite3.connect('data/state.db') as db:
        cursor = db.execute("""
            SELECT account_id, is_locked, reason, locked_at, locked_until, rule_id
            FROM lockouts
            WHERE is_locked = 1
        """)

        for row in cursor:
            account_id, is_locked, reason, locked_at, locked_until, rule_id = row
            lockouts[account_id] = {
                'is_locked': bool(is_locked),
                'reason': reason,
                'locked_at': datetime.fromisoformat(locked_at),
                'locked_until': datetime.fromisoformat(locked_until) if locked_until else None,
                'rule_id': rule_id
            }

    logger.info(f"Loaded {len(lockouts)} lockouts from database")
```

---

## 🔧 MOD-003: Timer Manager

**Purpose:** Countdown timers for cooldowns

### **In-Memory State:**
```python
# Dictionary: timer_name -> timer info
timers = {
    'cooldown_123_RULE-006': {
        'account_id': 123,
        'started_at': datetime(2025, 10, 21, 10, 30, 0),
        'expires_at': datetime(2025, 10, 21, 10, 31, 0),
        'duration_seconds': 60,
        'callback': lambda: lockout_manager.clear_lockout(123),
        'is_active': True
    }
}
```

### **SQLite Persistence:**
```python
# NO persistence - timers reset on crash (SAFER)
# Reasoning: Don't want stale timer from yesterday firing today
```

### **Timer Operations:**
```python
def start_timer(name, duration_seconds, callback):
    """Start countdown timer."""
    now = datetime.now()
    timers[name] = {
        'started_at': now,
        'expires_at': now + timedelta(seconds=duration_seconds),
        'duration_seconds': duration_seconds,
        'callback': callback,
        'is_active': True
    }

def check_timers():
    """Called every second - fire expired timers."""
    now = datetime.now()

    for name, timer in list(timers.items()):
        if timer['is_active'] and now >= timer['expires_at']:
            # Fire callback
            try:
                timer['callback']()
            except Exception as e:
                logger.error(f"Timer callback failed: {e}")

            # Remove timer
            del timers[name]

def get_remaining_time(name):
    """Get seconds remaining on timer."""
    if name not in timers:
        return 0

    remaining = (timers[name]['expires_at'] - datetime.now()).total_seconds()
    return max(0, remaining)
```

### **Recovery:**
- **Not needed** - Timers intentionally reset on daemon restart

---

## 🔧 MOD-004: Reset Scheduler

**Purpose:** Track daily reset times

### **In-Memory State:**
```python
# Dictionary: account_id -> reset info
reset_schedule = {
    123: {
        'last_reset_date': date(2025, 10, 21),
        'next_reset_time': datetime(2025, 10, 21, 17, 0, 0),
        'reset_time_config': '17:00',
        'timezone': 'America/New_York'
    }
}
```

### **SQLite Persistence:**
```python
# Table: reset_schedule
# Strategy: Sync write after each reset

def perform_daily_reset(account_id):
    """Execute daily reset - SYNC write."""
    today = date.today()

    # Reset MOD-005 (daily PNL)
    pnl_tracker.reset_daily_pnl(account_id)

    # Reset MOD-008 (session state)
    trade_counter.reset_session(account_id)

    # Update in-memory
    reset_time_str = config['reset_time']  # "17:00"
    reset_time = datetime.strptime(reset_time_str, '%H:%M').time()
    next_reset = datetime.combine(today + timedelta(days=1), reset_time)

    reset_schedule[account_id] = {
        'last_reset_date': today,
        'next_reset_time': next_reset,
        'reset_time_config': reset_time_str,
        'timezone': config['timezone']
    }

    # Sync to SQLite
    with sqlite3.connect('data/state.db') as db:
        db.execute("""
            INSERT OR REPLACE INTO reset_schedule
            (account_id, last_reset_date, next_reset_time, reset_time_config, timezone)
            VALUES (?, ?, ?, ?, ?)
        """, (account_id, today, next_reset, reset_time_str, config['timezone']))
        db.commit()
```

### **Recovery:**
```python
def load_reset_schedule():
    """Load reset schedule on startup - check if reset needed."""
    with sqlite3.connect('data/state.db') as db:
        cursor = db.execute("""
            SELECT account_id, last_reset_date, next_reset_time, reset_time_config, timezone
            FROM reset_schedule
        """)

        for row in cursor:
            account_id, last_reset_date, next_reset_time, reset_time_config, timezone = row

            reset_schedule[account_id] = {
                'last_reset_date': date.fromisoformat(last_reset_date),
                'next_reset_time': datetime.fromisoformat(next_reset_time),
                'reset_time_config': reset_time_config,
                'timezone': timezone
            }

            # Check if reset needed (daemon was down during reset time)
            if reset_schedule[account_id]['last_reset_date'] < date.today():
                logger.info(f"Missed reset detected - performing reset now")
                perform_daily_reset(account_id)
```

---

## 🔧 MOD-005: PNL Tracker

**Purpose:** Track daily realized P&L

### **In-Memory State:**
```python
# Dictionary: account_id -> daily PNL
daily_pnl = {
    123: -150.50  # Current daily realized P&L
}
```

### **SQLite Persistence:**
```python
# Table: daily_pnl
# Strategy: Immediate sync on every trade (critical for RULE-003)

def add_trade_pnl(account_id, pnl):
    """Add trade P&L - SYNC write."""

    # Update in-memory
    if account_id not in daily_pnl:
        daily_pnl[account_id] = 0.0
    daily_pnl[account_id] += pnl

    # Immediately sync to SQLite
    today = date.today()
    with sqlite3.connect('data/state.db') as db:
        db.execute("""
            INSERT INTO daily_pnl (account_id, date, realized_pnl, last_updated)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(account_id, date) DO UPDATE SET
                realized_pnl = ?,
                last_updated = ?
        """, (account_id, today, daily_pnl[account_id], datetime.now(),
              daily_pnl[account_id], datetime.now()))
        db.commit()

    return daily_pnl[account_id]

def get_daily_realized_pnl(account_id):
    """Get daily P&L - in-memory lookup (FAST)."""
    return daily_pnl.get(account_id, 0.0)

def calculate_unrealized_pnl(account_id):
    """Calculate unrealized P&L - uses MOD-006, MOD-007, MOD-009."""
    positions = state_manager.get_all_positions(account_id)

    total_unrealized = 0.0
    for position in positions:
        contract_id = position['contractId']

        # Get current price (MOD-006)
        current_price = quote_tracker.get_last_price(contract_id)
        if not current_price:
            continue

        # Get contract metadata (MOD-007)
        contract = contract_cache.get_contract(contract_id)
        tick_value = contract['tickValue']
        tick_size = contract['tickSize']

        # Calculate P&L
        price_diff = current_price - position['averagePrice']
        ticks_moved = price_diff / tick_size

        if position['type'] == 1:  # Long
            position_pnl = ticks_moved * tick_value * position['size']
        else:  # Short
            position_pnl = -ticks_moved * tick_value * position['size']

        total_unrealized += position_pnl

    return total_unrealized
```

### **Recovery:**
```python
def load_daily_pnl():
    """Load today's P&L on startup."""
    today = date.today()

    with sqlite3.connect('data/state.db') as db:
        cursor = db.execute("""
            SELECT account_id, realized_pnl
            FROM daily_pnl
            WHERE date = ?
        """, (today,))

        for account_id, realized_pnl in cursor:
            daily_pnl[account_id] = realized_pnl

    logger.info(f"Loaded daily P&L for {len(daily_pnl)} accounts")
```

---

## 🔧 MOD-006: Quote Tracker

**Purpose:** Real-time price tracking

### **In-Memory State:**
```python
# Dictionary: contract_id -> quote data
quotes = {
    'CON.F.US.MNQ.U25': {
        'lastPrice': 20950.00,
        'bestBid': 20949.75,
        'bestAsk': 20950.25,
        'timestamp': datetime(2025, 10, 21, 14, 23, 0),
        'lastUpdated': datetime(2025, 10, 21, 14, 23, 1)
    }
}
```

### **SQLite Persistence:**
```python
# NO persistence - quotes are real-time only
# Reasoning: Quotes change every second, stale quotes are useless
```

### **Quote Operations:**
```python
def update_quote(contract_id, quote_data):
    """Update quote from GatewayQuote event."""
    quotes[contract_id] = {
        'lastPrice': quote_data['lastPrice'],
        'bestBid': quote_data['bestBid'],
        'bestAsk': quote_data['bestAsk'],
        'timestamp': datetime.fromisoformat(quote_data['timestamp'].replace('Z', '+00:00')),
        'lastUpdated': datetime.now()
    }

def get_last_price(contract_id):
    """Get last price - in-memory lookup (FAST)."""
    if contract_id not in quotes:
        return None
    return quotes[contract_id]['lastPrice']

def is_quote_stale(contract_id, max_age_seconds=10):
    """Check if quote is too old."""
    if contract_id not in quotes:
        return True

    age = (datetime.now() - quotes[contract_id]['lastUpdated']).total_seconds()
    return age > max_age_seconds
```

### **Recovery:**
- **Not needed** - Start fresh, quotes arrive within 0-5 seconds of SignalR connection

---

## 🔧 MOD-007: Contract Cache

**Purpose:** Cache contract metadata (tick values)

### **In-Memory State:**
```python
# Dictionary: contract_id -> contract metadata
contract_cache = {
    'CON.F.US.MNQ.U25': {
        'id': 'CON.F.US.MNQ.U25',
        'tickSize': 0.25,
        'tickValue': 0.5,
        'symbolId': 'F.US.MNQ',
        'name': 'MNQU5'
    }
}
```

### **SQLite Persistence:**
```python
# Table: contract_cache
# Strategy: Lazy write (write only when new contract cached)

def get_contract(contract_id):
    """Get contract metadata - cache miss triggers API call."""

    # Check in-memory cache first
    if contract_id in contract_cache:
        return contract_cache[contract_id]

    # Not in cache - fetch from API
    response = rest_client.post('/api/Contract/searchById', json={'contractId': contract_id})
    contract_data = response.json()['contract']

    # Cache in-memory
    contract_cache[contract_id] = {
        'id': contract_data['id'],
        'tickSize': contract_data['tickSize'],
        'tickValue': contract_data['tickValue'],
        'symbolId': contract_data['symbolId'],
        'name': contract_data.get('name', '')
    }

    # Lazy write to SQLite (don't block)
    cache_queue.put({
        'contract_id': contract_id,
        'tick_size': contract_data['tickSize'],
        'tick_value': contract_data['tickValue'],
        'symbol_id': contract_data['symbolId'],
        'name': contract_data.get('name', '')
    })

    return contract_cache[contract_id]
```

### **Background Writer:**
```python
def contract_cache_writer():
    """Background thread - writes contract cache to SQLite."""
    while daemon_running:
        try:
            contract = cache_queue.get(timeout=30)

            with sqlite3.connect('data/state.db') as db:
                db.execute("""
                    INSERT OR IGNORE INTO contract_cache
                    (contract_id, tick_size, tick_value, symbol_id, name, cached_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (contract['contract_id'], contract['tick_size'],
                      contract['tick_value'], contract['symbol_id'],
                      contract['name'], datetime.now()))
                db.commit()
        except queue.Empty:
            pass
```

### **Recovery:**
```python
def load_contract_cache():
    """Load contract cache on startup."""
    with sqlite3.connect('data/state.db') as db:
        cursor = db.execute("""
            SELECT contract_id, tick_size, tick_value, symbol_id, name
            FROM contract_cache
        """)

        for row in cursor:
            contract_id, tick_size, tick_value, symbol_id, name = row
            contract_cache[contract_id] = {
                'id': contract_id,
                'tickSize': tick_size,
                'tickValue': tick_value,
                'symbolId': symbol_id,
                'name': name
            }

    logger.info(f"Loaded {len(contract_cache)} contracts from cache")
```

---

## 🔧 MOD-008: Trade Counter

**Purpose:** Track trade frequency

### **In-Memory State:**
```python
# Dictionary: account_id -> list of trade timestamps (rolling 1-hour window)
trade_history = {
    123: [
        datetime(2025, 10, 21, 14, 0, 0),
        datetime(2025, 10, 21, 14, 5, 23),
        datetime(2025, 10, 21, 14, 12, 45)
    ]
}

# Dictionary: account_id -> session start time
session_starts = {
    123: datetime(2025, 10, 21, 17, 0, 0)
}
```

### **SQLite Persistence:**
```python
# Table: trade_history, session_state
# Strategy: Async insert (don't block trade processing)

def record_trade(account_id, timestamp):
    """Record trade - async write."""

    # Add to in-memory rolling window
    if account_id not in trade_history:
        trade_history[account_id] = []
    trade_history[account_id].append(timestamp)

    # Keep only last hour in memory
    cutoff = timestamp - timedelta(hours=1)
    trade_history[account_id] = [t for t in trade_history[account_id] if t > cutoff]

    # Async write to SQLite
    trade_queue.put({
        'account_id': account_id,
        'timestamp': timestamp,
        'contract_id': None,  # Optional, added by caller
        'pnl': None
    })

    # Return counts
    return get_trade_counts(account_id, timestamp)

def get_trade_counts(account_id, current_time):
    """Get trade counts - in-memory calculation (FAST)."""
    if account_id not in trade_history:
        return {'minute': 0, 'hour': 0, 'session': 0}

    trades = trade_history[account_id]

    minute_cutoff = current_time - timedelta(minutes=1)
    hour_cutoff = current_time - timedelta(hours=1)
    session_start = get_session_start(account_id)

    return {
        'minute': len([t for t in trades if t > minute_cutoff]),
        'hour': len([t for t in trades if t > hour_cutoff]),
        'session': len([t for t in trades if t > session_start])
    }
```

### **Background Writer:**
```python
def trade_history_writer():
    """Background thread - writes trades to SQLite."""
    while daemon_running:
        batch = []

        try:
            batch.append(trade_queue.get(timeout=5))
            for _ in range(99):  # Get up to 99 more
                batch.append(trade_queue.get_nowait())
        except queue.Empty:
            pass

        if batch:
            with sqlite3.connect('data/state.db') as db:
                db.executemany("""
                    INSERT INTO trade_history (account_id, timestamp, contract_id, pnl)
                    VALUES (?, ?, ?, ?)
                """, [(t['account_id'], t['timestamp'], t['contract_id'], t['pnl'])
                      for t in batch])
                db.commit()
```

### **Recovery:**
```python
def load_trade_history():
    """Load last hour of trades on startup."""
    cutoff = datetime.now() - timedelta(hours=1)

    with sqlite3.connect('data/state.db') as db:
        cursor = db.execute("""
            SELECT account_id, timestamp
            FROM trade_history
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        """, (cutoff,))

        for account_id, timestamp in cursor:
            if account_id not in trade_history:
                trade_history[account_id] = []
            trade_history[account_id].append(datetime.fromisoformat(timestamp))

    # Load session starts
    with sqlite3.connect('data/state.db') as db:
        cursor = db.execute("SELECT account_id, session_start FROM session_state")
        for account_id, session_start in cursor:
            session_starts[account_id] = datetime.fromisoformat(session_start)
```

---

## 🔧 MOD-009: State Manager

**Purpose:** Mirror TopstepX positions/orders

### **In-Memory State:**
```python
# Nested dictionaries: account_id -> position_id/order_id -> data
positions = {
    123: {  # account_id
        456: {  # position_id
            'id': 456,
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 1,  # Long
            'size': 2,
            'averagePrice': 21000.25,
            'createdAt': datetime(2025, 10, 21, 10, 0, 0)
        }
    }
}

orders = {
    123: {  # account_id
        789: {  # order_id
            'id': 789,
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 4,  # Stop
            'side': 1,  # Sell
            'size': 2,
            'limitPrice': None,
            'stopPrice': 20950.00,
            'state': 2  # Working
        }
    }
}
```

### **SQLite Persistence:**
```python
# Tables: positions, orders
# Strategy: Batched writes (every 5 seconds)

def update_position(position_event):
    """Update position - batched write."""
    account_id = position_event['accountId']
    position_id = position_event['id']

    if account_id not in positions:
        positions[account_id] = {}

    if position_event['size'] == 0:
        # Position closed
        if position_id in positions[account_id]:
            del positions[account_id][position_id]
            position_delete_queue.put(position_id)
    else:
        # Position opened/updated
        positions[account_id][position_id] = {
            'id': position_id,
            'contractId': position_event['contractId'],
            'type': position_event['type'],
            'size': position_event['size'],
            'averagePrice': position_event['averagePrice'],
            'createdAt': position_event['creationTimestamp']
        }
        position_update_queue.put(positions[account_id][position_id])

def update_order(order_event):
    """Update order - batched write."""
    account_id = order_event['accountId']
    order_id = order_event['id']

    if account_id not in orders:
        orders[account_id] = {}

    # Remove completed orders
    if order_event['state'] in [3, 4, 5]:  # Filled, Cancelled, Rejected
        if order_id in orders[account_id]:
            del orders[account_id][order_id]
            order_delete_queue.put(order_id)
    else:
        # Working order
        orders[account_id][order_id] = {
            'id': order_id,
            'contractId': order_event['contractId'],
            'type': order_event['type'],
            'side': order_event['side'],
            'size': order_event['size'],
            'limitPrice': order_event.get('limitPrice'),
            'stopPrice': order_event.get('stopPrice'),
            'state': order_event['state']
        }
        order_update_queue.put(orders[account_id][order_id])
```

### **Background Writer:**
```python
def state_writer():
    """Background thread - writes positions/orders every 5 seconds."""
    while daemon_running:
        time.sleep(5)

        with sqlite3.connect('data/state.db') as db:
            # Write position updates
            while not position_update_queue.empty():
                pos = position_update_queue.get_nowait()
                db.execute("""
                    INSERT OR REPLACE INTO positions
                    (id, account_id, contract_id, type, size, average_price, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (pos['id'], pos['accountId'], pos['contractId'],
                      pos['type'], pos['size'], pos['averagePrice'], pos['createdAt']))

            # Delete closed positions
            while not position_delete_queue.empty():
                pos_id = position_delete_queue.get_nowait()
                db.execute("DELETE FROM positions WHERE id = ?", (pos_id,))

            # Write order updates
            while not order_update_queue.empty():
                order = order_update_queue.get_nowait()
                db.execute("""
                    INSERT OR REPLACE INTO orders
                    (id, account_id, contract_id, type, side, size, limit_price, stop_price, state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (order['id'], order['accountId'], order['contractId'],
                      order['type'], order['side'], order['size'],
                      order['limitPrice'], order['stopPrice'], order['state']))

            # Delete completed orders
            while not order_delete_queue.empty():
                order_id = order_delete_queue.get_nowait()
                db.execute("DELETE FROM orders WHERE id = ?", (order_id,))

            db.commit()
```

### **Recovery:**
```python
def load_positions_and_orders():
    """Load positions and orders on startup."""
    with sqlite3.connect('data/state.db') as db:
        # Load positions
        cursor = db.execute("""
            SELECT id, account_id, contract_id, type, size, average_price, created_at
            FROM positions
        """)

        for row in cursor:
            pos_id, account_id, contract_id, pos_type, size, avg_price, created_at = row

            if account_id not in positions:
                positions[account_id] = {}

            positions[account_id][pos_id] = {
                'id': pos_id,
                'contractId': contract_id,
                'type': pos_type,
                'size': size,
                'averagePrice': avg_price,
                'createdAt': created_at
            }

        # Load orders
        cursor = db.execute("""
            SELECT id, account_id, contract_id, type, side, size, limit_price, stop_price, state
            FROM orders
        """)

        for row in cursor:
            order_id, account_id, contract_id, order_type, side, size, limit_price, stop_price, state = row

            if account_id not in orders:
                orders[account_id] = {}

            orders[account_id][order_id] = {
                'id': order_id,
                'contractId': contract_id,
                'type': order_type,
                'side': side,
                'size': size,
                'limitPrice': limit_price,
                'stopPrice': stop_price,
                'state': state
            }

    logger.info(f"Loaded {sum(len(p) for p in positions.values())} positions, "
                f"{sum(len(o) for o in orders.values())} orders")
```

---

## 🔄 Complete Startup Sequence

**When daemon starts, state is recovered in this order:**

```python
def initialize_state():
    """Initialize all module state on daemon startup."""

    logger.info("Initializing state from SQLite...")

    # 1. Load lockouts (MOD-002) - CRITICAL
    load_lockouts()

    # 2. Load daily PNL (MOD-005) - CRITICAL
    load_daily_pnl()

    # 3. Load contract cache (MOD-007) - Performance optimization
    load_contract_cache()

    # 4. Load reset schedule (MOD-004) - Check if reset needed
    load_reset_schedule()

    # 5. Load trade history (MOD-008) - Last hour of trades
    load_trade_history()

    # 6. Load positions and orders (MOD-009) - Mirror TopstepX state
    load_positions_and_orders()

    logger.info("State initialization complete")

    # Start background writers
    threading.Thread(target=enforcement_log_writer, daemon=True).start()
    threading.Thread(target=contract_cache_writer, daemon=True).start()
    threading.Thread(target=trade_history_writer, daemon=True).start()
    threading.Thread(target=state_writer, daemon=True).start()

    logger.info("Background writers started")
```

---

## 🧵 Threading Model

**Main Thread:**
- SignalR event loop (async)
- Event routing to rules

**Background Thread 1: State Writers**
- Enforcement log writer (batched, 5-10 seconds)
- Contract cache writer (lazy)
- Trade history writer (batched, 5 seconds)
- Position/order writer (batched, 5 seconds)

**Background Thread 2: Timers & Lockouts**
- Check expired lockouts (every 1 second)
- Check expired timers (every 1 second)

**Thread Safety:**
- In-memory dicts: Protected by GIL (Python single-threaded event processing)
- SQLite writes: Separate connections per thread
- Queues: `queue.Queue` (thread-safe)

---

## 📊 Performance Characteristics

**Memory Usage (1 account, typical):**
- Lockouts: ~1 KB
- Daily PNL: ~100 bytes
- Timers: ~1 KB (3-5 active timers)
- Contract cache: ~5 KB (50 contracts)
- Quotes: ~10 KB (50 active contracts)
- Trade history: ~5 KB (100 trades in last hour)
- Positions: ~2 KB (5 positions)
- Orders: ~2 KB (10 orders)

**Total: ~27 KB in-memory per account**

**SQLite Write Load:**
- Enforcement log: ~1 write/minute (batched)
- Lockouts: ~1 write/hour (sync, small)
- Daily PNL: ~10 writes/hour (sync, small)
- Contract cache: ~1 write/day (lazy)
- Trade history: ~100 writes/day (batched)
- Positions/orders: ~1000 writes/day (batched every 5 seconds)

**Total: ~1200 writes/day = ~1 write/minute average**

---

## ✅ State Integrity Guarantees

**Critical Data (MUST NOT LOSE):**
- Lockout state (MOD-002): **Synchronous writes**
- Daily PNL (MOD-005): **Synchronous writes**

**Important Data (Small loss acceptable):**
- Positions/orders (MOD-009): **Batched (5 seconds) - max 5 seconds of data lost**
- Trade history (MOD-008): **Batched (5 seconds) - recent trades may be missing**

**Non-Critical Data (Loss acceptable):**
- Quotes (MOD-006): **Not persisted - always start fresh**
- Timers (MOD-003): **Not persisted - safer to reset**
- Contract cache (MOD-007): **Lazy write - will refetch from API if missing**

**Crash Recovery:**
- Worst case: 5 seconds of position/order updates lost
- Positions/orders will resync from SignalR within 10 seconds of reconnect
- No financial impact (TopstepX is source of truth)

---

**This state management strategy balances performance, safety, and crash recovery for all 9 modules.**
