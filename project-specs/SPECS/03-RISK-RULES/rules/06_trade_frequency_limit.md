---
doc_id: RULE-006
version: 3.0
last_updated: 2025-10-21
dependencies: [MOD-002, MOD-003, API-INT-001]
enforcement_type: Configurable Timer Lockout
---

# RULE-006: TradeFrequencyLimit

**Purpose:** Prevent overtrading by limiting trades per time window - protects against impulsive trading behavior.

---

## ⚙️ Configuration

```yaml
trade_frequency_limit:
  enabled: true
  limits:
    per_minute: 3     # Max 3 trades in any 60-second window
    per_hour: 10      # Max 10 trades in any 60-minute window
    per_session: 50   # Max 50 trades from session start to reset
  cooldown_on_breach:
    enabled: true
    per_minute_breach: 60      # 1 min cooldown if minute limit hit
    per_hour_breach: 1800      # 30 min cooldown if hour limit hit
    per_session_breach: 3600   # 1 hour cooldown if session limit hit
  reset_time: "17:00"          # Daily session reset
  timezone: "America/New_York"
```

---

## 🎯 Trigger Condition

**Primary Event:** `GatewayUserTrade`

**Logic:**
```python
def on_trade_executed(trade_event):
    """Called when GatewayUserTrade event received."""

    account_id = trade_event['accountId']
    trade_timestamp = datetime.fromisoformat(trade_event['creationTimestamp'])

    # Record trade and get counts (via MOD-008)
    counts = trade_counter.record_trade(account_id, trade_timestamp)

    # Check minute window
    if counts['minute'] > config['limits']['per_minute']:
        return BREACH, "per_minute", counts['minute']

    # Check hour window
    if counts['hour'] > config['limits']['per_hour']:
        return BREACH, "per_hour", counts['hour']

    # Check session window
    if counts['session'] > config['limits']['per_session']:
        return BREACH, "per_session", counts['session']

    return NO_BREACH
```

---

## 🚨 Enforcement Action

**Type:** Configurable Timer Lockout (NO position close - trade already happened)

**Action Sequence:**
1. ❌ **NO position close** (trade has already executed)
2. ✅ **Set cooldown** (via MOD-002, MOD-003)
3. ✅ **Log enforcement**
4. ✅ **Update Trader CLI** → Show countdown timer
5. ✅ **Auto-unlock** when timer expires

**Enforcement Code:**
```python
def enforce(account_id, breach_type, trade_count):
    # Determine cooldown duration based on breach type
    cooldown_durations = {
        'per_minute': config['cooldown_on_breach']['per_minute_breach'],
        'per_hour': config['cooldown_on_breach']['per_hour_breach'],
        'per_session': config['cooldown_on_breach']['per_session_breach']
    }

    cooldown_seconds = cooldown_durations[breach_type]

    # Set cooldown (NOT lockout - softer restriction)
    lockout_manager.set_cooldown(
        account_id=account_id,
        reason=f"Trade frequency limit: {trade_count}/{config['limits'][breach_type]} trades",
        duration_seconds=cooldown_seconds
    )

    # Log enforcement
    logger.log_enforcement(
        f"RULE-006: Trade frequency limit breach - "
        f"{breach_type}: {trade_count} trades - "
        f"Cooldown for {cooldown_seconds}s"
    )

    # CLI will show: "🟡 COOLDOWN - 4/3 trades this minute - Unlocks in 47s"
```

---

## 📡 API Requirements

### **SignalR Events (Trigger):**

**GatewayUserTrade** (executes on every trade):
```json
{
  "id": 101112,
  "accountId": 123,
  "contractId": "CON.F.US.EP.U25",
  "creationTimestamp": "2024-07-21T13:47:00Z",
  "price": 2100.75,
  "profitAndLoss": 50.25,
  "fees": 2.50,
  "side": 0,
  "size": 1,
  "voided": false,
  "orderId": 789
}
```

**Key Fields:**
- `id`: Unique trade ID
- `accountId`: Account that executed trade
- `creationTimestamp`: When trade was executed (ISO 8601)
- `side`: 0=Buy, 1=Sell (OrderSide enum)
- `size`: Number of contracts traded
- `voided`: If true, ignore this trade (cancelled/reversed)

### **REST API Calls (Optional - Historical Data):**

**Get Historical Trades** (for initial state on startup):
```http
POST /api/Trade/search
Authorization: Bearer {jwt_token}
{
  "accountId": 123,
  "startTimestamp": "2024-07-21T00:00:00Z",
  "endTimestamp": "2024-07-21T23:59:59Z"
}

Response:
{
  "trades": [
    {
      "id": 8604,
      "accountId": 123,
      "contractId": "CON.F.US.EP.H25",
      "creationTimestamp": "2024-07-21T16:13:52Z",
      "price": 6065.25,
      "profitAndLoss": 50.00,
      "fees": 1.40,
      "side": 1,
      "size": 1,
      "voided": false,
      "orderId": 14328
    }
  ],
  "success": true
}
```

---

## 🧪 Test Scenarios

### **Scenario 1: Minute Limit Breach**
```
Setup:
  - Limit: 3 trades/minute
  - Cooldown: 60 seconds

Timeline:
  1. t=0s: Trade 1 executes → 1/3 trades (OK)
  2. t=10s: Trade 2 executes → 2/3 trades (OK)
  3. t=20s: Trade 3 executes → 3/3 trades (OK, at limit)
  4. t=30s: Trade 4 executes → 4/3 trades (BREACH!)
  5. Cooldown set for 60 seconds
  6. At t=90s (60s after breach): Cooldown expires, can trade again
```

### **Scenario 2: Hour Limit Breach**
```
Setup:
  - Limit: 10 trades/hour
  - Cooldown: 30 minutes

Timeline:
  1. Trader executes 10 trades over 45 minutes → OK
  2. Trade 11 executes at t=47min → BREACH!
  3. Cooldown set for 30 minutes
  4. Old trades from 60+ minutes ago fall out of window
  5. After cooldown expires, trader has fresh hour window
```

### **Scenario 3: Session Limit Breach**
```
Setup:
  - Limit: 50 trades/session
  - Session: 17:00 yesterday to 17:00 today
  - Cooldown: 1 hour

Timeline:
  1. Trader executes 50 trades throughout the day → OK
  2. Trade 51 executes → BREACH!
  3. Cooldown set for 1 hour
  4. After cooldown, still can't trade (session limit is hard until reset)
  5. At 17:00 (reset time): Session counter resets to 0
```

### **Scenario 4: Rolling Window (No Breach)**
```
Setup:
  - Limit: 3 trades/minute

Timeline:
  1. t=0s: Trade 1
  2. t=10s: Trade 2
  3. t=20s: Trade 3 → 3/3 trades (at limit)
  4. t=70s: Trade 4 → Only 2 trades in last 60s (Trade 1 aged out)
  5. NO BREACH - rolling window allows continued trading
```

---

## 📊 State Tracking

**In-Memory State (for fast lookups):**
```python
# Recent trades cache (last 1 hour)
recent_trades = {
    123: [  # account_id
        {
            'trade_id': 101112,
            'timestamp': datetime(2025, 1, 17, 14, 23, 0),
            'voided': False
        },
        {
            'trade_id': 101113,
            'timestamp': datetime(2025, 1, 17, 14, 23, 15),
            'voided': False
        }
    ]
}

# Session counters (reset daily)
session_trade_counts = {
    123: 12  # 12 trades so far today
}
```

**SQLite Persistence:**
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    trade_id BIGINT NOT NULL,
    contract_id TEXT,
    timestamp DATETIME NOT NULL,
    side INTEGER,
    size INTEGER,
    voided BOOLEAN DEFAULT 0,
    INDEX idx_account_timestamp (account_id, timestamp)
);

-- Index for fast rolling window queries
CREATE INDEX idx_trades_window
ON trades(account_id, timestamp DESC);

-- Track session counts separately for performance
CREATE TABLE session_trade_counts (
    account_id INTEGER PRIMARY KEY,
    session_date DATE,
    trade_count INTEGER DEFAULT 0,
    last_updated DATETIME
);
```

---

## ⚠️ Edge Cases

### **Voided Trades**
- If `voided: true` in trade event → don't count toward limits
- Remove from tracking if already counted
- Voided trades are cancelled/reversed trades

### **Multiple Breaches Simultaneously**
- Possible to breach minute AND hour limits on same trade
- Apply most severe cooldown (hour > minute > session)
- Log all breaches that occurred

### **Trade Executed During Cooldown**
- Shouldn't happen (trading disabled during cooldown)
- If it does: extend cooldown duration
- Log warning about enforcement bypass

### **Session Reset During Cooldown**
- Session counter resets at 17:00
- Cooldown timer continues independently
- After cooldown expires, trader has fresh session count

### **Daemon Restart**
- Load recent trades from database on startup
- Rebuild in-memory cache from last 1 hour of trades
- Recalculate session counts from last reset time

### **Clock Skew / Timestamp Issues**
- Trade timestamp from API may differ from local time
- Always use trade's `creationTimestamp` field
- Don't rely on local receipt time

---

## 🔧 Background Processing

**Trade Cleanup (runs every 5 minutes):**
```python
def cleanup_old_trades():
    """Remove trades older than 1 hour from in-memory cache."""

    cutoff_time = datetime.now() - timedelta(hours=1)

    for account_id, trades in recent_trades.items():
        # Keep only trades from last hour
        recent_trades[account_id] = [
            t for t in trades
            if t['timestamp'] > cutoff_time
        ]
```

**Session Reset (runs at configured reset_time):**
```python
def reset_session_counts():
    """Reset all session trade counts at 17:00."""

    logger.info("Resetting session trade counts")

    # Clear session counters
    session_trade_counts.clear()

    # Update database
    db.execute("""
        UPDATE session_trade_counts
        SET trade_count = 0,
            session_date = CURRENT_DATE,
            last_updated = CURRENT_TIMESTAMP
    """)
```

**No Active Position Monitoring Required:**
- This rule only tracks completed trades
- No need to monitor positions or quotes
- Purely event-driven on `GatewayUserTrade`

---

## 🔗 Dependencies

- **MOD-002:** `set_lockout()` (for cooldown management)
- **MOD-003:** Timer-based auto-unlock
- **MOD-004:** Daily reset scheduler (for session counter reset)
- **API-INT-001:** `GatewayUserTrade` event
- **src/state/trade_tracker.py:** Trade tracking and counting
- **src/state/persistence.py:** SQLite trade history
- **POST /api/Trade/search:** Historical trade data (startup only)

---

**This rule prevents overtrading - a common cause of account blowups and emotional decision-making.**
