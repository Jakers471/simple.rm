---
doc_id: MOD-008
version: 1.0
last_updated: 2025-10-21
dependencies: [API-INT-001]
---

# MOD-008: Trade Counter

**Purpose:** Track trade frequency across time windows (minute/hour/session) - RULE-006 calls these functions.

**File:** `src/state/trade_counter.py`

---

## 🎯 Core Principle

**All trade frequency tracking in one place. RULE-006 never directly tracks trades.**

This ensures:
- **Single source of truth:** One place for trade counts
- **Consistency:** All time windows tracked uniformly
- **Automatic cleanup:** Old trades removed from rolling windows
- **Performance:** Efficient in-memory tracking

---

## 🔧 Public API

### **1. record_trade(account_id, timestamp)**
**Purpose:** Record a new trade and return current counts.

**Implementation:**
```python
def record_trade(account_id: int, timestamp: datetime) -> dict:
    """
    Record a new trade and return counts across all time windows.

    Args:
        account_id: TopstepX account ID
        timestamp: Trade timestamp from GatewayUserTrade event

    Returns:
        {
            'minute': 5,   # Trades in last 60 seconds
            'hour': 42,    # Trades in last 60 minutes
            'session': 150 # Trades since session start
        }
    """
    # Initialize if needed
    if account_id not in trade_history:
        trade_history[account_id] = []

    # Add this trade
    trade_history[account_id].append(timestamp)

    # Clean old trades (older than 1 hour)
    cutoff = timestamp - timedelta(hours=1)
    trade_history[account_id] = [
        t for t in trade_history[account_id] if t > cutoff
    ]

    # Persist to SQLite
    db.execute(
        "INSERT INTO trade_history (account_id, timestamp) VALUES (?, ?)",
        (account_id, timestamp)
    )

    # Return current counts
    return get_trade_counts(account_id, timestamp)
```

**Used By:** RULE-006

---

### **2. get_trade_counts(account_id, current_time)**
**Purpose:** Get trade counts for all time windows.

**Implementation:**
```python
def get_trade_counts(account_id: int, current_time: datetime) -> dict:
    """
    Get trade counts across all time windows.

    Args:
        account_id: TopstepX account ID
        current_time: Current timestamp (usually datetime.now())

    Returns:
        {
            'minute': 5,   # Trades in last 60 seconds
            'hour': 42,    # Trades in last 60 minutes
            'session': 150 # Trades since session start
        }
    """
    if account_id not in trade_history:
        return {'minute': 0, 'hour': 0, 'session': 0}

    trades = trade_history[account_id]

    # Count trades in each window
    minute_cutoff = current_time - timedelta(minutes=1)
    hour_cutoff = current_time - timedelta(hours=1)
    session_start = get_session_start(account_id)

    return {
        'minute': len([t for t in trades if t > minute_cutoff]),
        'hour': len([t for t in trades if t > hour_cutoff]),
        'session': len([t for t in trades if t > session_start])
    }
```

**Used By:** RULE-006

---

### **3. reset_session(account_id)**
**Purpose:** Reset session trade count (called at reset time).

**Implementation:**
```python
def reset_session(account_id: int) -> None:
    """
    Reset session trade count.

    Called by MOD-004 (Reset Scheduler) at reset_time.
    """
    # Clear in-memory history
    trade_history[account_id] = []

    # Update session start time
    session_starts[account_id] = datetime.now()

    # Archive to SQLite
    db.execute(
        "UPDATE session_state SET session_start = ? WHERE account_id = ?",
        (session_starts[account_id], account_id)
    )
```

**Used By:** MOD-004 (Reset Scheduler)

---

### **4. get_session_start(account_id)**
**Purpose:** Get session start time.

**Implementation:**
```python
def get_session_start(account_id: int) -> datetime:
    """Get session start time."""
    if account_id not in session_starts:
        # Default to today's reset time if not set
        reset_time = time(17, 0)  # 5:00 PM from config
        session_starts[account_id] = datetime.combine(
            datetime.now().date(),
            reset_time
        )
        if datetime.now() < session_starts[account_id]:
            # Before reset time, use yesterday's reset
            session_starts[account_id] -= timedelta(days=1)

    return session_starts[account_id]
```

---

## 📊 State Management

**In-Memory State:**
```python
# Trade history (rolling 1-hour window)
trade_history = {
    123: [
        datetime(2024, 7, 21, 14, 0, 0),
        datetime(2024, 7, 21, 14, 5, 23),
        datetime(2024, 7, 21, 14, 12, 45),
        # ... last hour of trades
    ]
}

# Session start times
session_starts = {
    123: datetime(2024, 7, 21, 17, 0, 0)  # Today's reset time
}
```

**SQLite Persistence:**
```sql
CREATE TABLE trade_history (
    account_id INTEGER,
    timestamp DATETIME,
    PRIMARY KEY (account_id, timestamp)
);

CREATE INDEX idx_trade_timestamp ON trade_history(timestamp);

CREATE TABLE session_state (
    account_id INTEGER PRIMARY KEY,
    session_start DATETIME
);
```

---

## 🔗 Dependencies

- **API-INT-001:** GatewayUserTrade event
- **persistence.py:** SQLite operations
- **MOD-004:** Reset Scheduler calls `reset_session()`

---

**Used By:** RULE-006 (TradeFrequencyLimit), MOD-004 (Reset Scheduler)
