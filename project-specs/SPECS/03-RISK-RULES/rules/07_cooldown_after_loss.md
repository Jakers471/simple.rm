---
doc_id: RULE-007
version: 3.0
last_updated: 2025-10-21
dependencies: [MOD-002, MOD-003, API-INT-001]
enforcement_type: Configurable Timer Lockout
---

# RULE-007: CooldownAfterLoss

**Purpose:** Force break after losing trades to prevent revenge trading and emotional decision-making.

---

## ⚙️ Configuration

```yaml
cooldown_after_loss:
  enabled: true
  loss_thresholds:
    - loss_amount: -100
      cooldown_duration: 300    # 5 min cooldown after -$100 loss on a single trade
    - loss_amount: -200
      cooldown_duration: 900    # 15 min cooldown after -$200 loss on a single trade
    - loss_amount: -300
      cooldown_duration: 1800   # 30 min cooldown after -$300 loss on a single trade
  allow_trading_during_cooldown: false  # Hard lockout during cooldown
```

---

## 🎯 Trigger Condition

**Primary Event:** `GatewayUserTrade`

**Logic:**
```python
def on_trade_executed(trade_event):
    """Called when GatewayUserTrade event received."""

    account_id = trade_event['accountId']
    trade_pnl = trade_event['profitAndLoss']

    # Only trigger on losing trades
    if trade_pnl is None or trade_pnl >= 0:
        return NO_BREACH  # Not a losing trade

    # Check against each threshold (largest to smallest)
    thresholds = sorted(
        config['loss_thresholds'],
        key=lambda x: x['loss_amount']  # Sort by loss amount (most negative first)
    )

    for threshold in thresholds:
        if trade_pnl <= threshold['loss_amount']:
            # Loss is at or below this threshold
            return BREACH, threshold['loss_amount'], threshold['cooldown_duration']

    return NO_BREACH

# Example: If trade_pnl = -250
# - Checks against -300: -250 > -300 (not triggered)
# - Checks against -200: -250 <= -200 (TRIGGERED!)
# - Returns: cooldown_duration = 900 seconds (15 minutes)
```

**Trade P&L Calculation:**
- P&L is provided directly in `GatewayUserTrade.profitAndLoss` field
- Positive = profit, Negative = loss
- `null` value = "half-turn" trade (opened position, not closed)

---

## 🚨 Enforcement Action

**Type:** Configurable Timer Lockout (NO position close - trade already happened)

**Action Sequence:**
1. ❌ **NO position close** (trade has already executed and closed)
2. ✅ **Set cooldown** (via MOD-002, MOD-003)
3. ✅ **Log enforcement**
4. ✅ **Update Trader CLI** → Show countdown timer
5. ✅ **Auto-unlock** when timer expires

**Enforcement Code:**
```python
def enforce(account_id, loss_amount, cooldown_duration):
    # Set cooldown timer
    lockout_manager.set_cooldown(
        account_id=account_id,
        reason=f"Cooldown after ${abs(loss_amount):.2f} loss - take a break",
        duration_seconds=cooldown_duration
    )

    # Log enforcement
    logger.log_enforcement(
        f"RULE-007: Cooldown after loss - "
        f"Trade P&L: ${loss_amount:.2f} - "
        f"Cooldown for {cooldown_duration}s ({cooldown_duration/60:.0f} minutes)"
    )

    # CLI will show:
    # "🟡 COOLDOWN - $250 loss - Take a break - Unlocks in 14:23"
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
  "profitAndLoss": -150.50,
  "fees": 2.50,
  "side": 1,
  "size": 1,
  "voided": false,
  "orderId": 789
}
```

**Key Fields:**
- `profitAndLoss`: Total P&L for this trade (negative = loss, positive = profit, null = half-turn)
- `voided`: If true, ignore this trade (cancelled/reversed)
- `creationTimestamp`: When trade executed (for logging)
- `side`: 0=Buy, 1=Sell (OrderSide enum)

**Half-Turn Trades (profitAndLoss = null):**
```json
{
  "id": 101113,
  "accountId": 123,
  "contractId": "CON.F.US.EP.U25",
  "profitAndLoss": null,    // Opening trade - no P&L yet
  "side": 0,
  "size": 1
}
```

### **REST API Calls (Optional - Historical Data):**

**Get Historical Trades** (for analysis, not required for rule):
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
      "profitAndLoss": -125.00,
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

### **Scenario 1: Small Loss (No Cooldown)**
```
Setup:
  - Thresholds: -$100, -$200, -$300
  - Trade closes: P&L = -$75

Result:
  - -$75 > -$100 (not at any threshold)
  - NO BREACH
  - Trader can continue trading immediately
```

### **Scenario 2: Moderate Loss (5 Min Cooldown)**
```
Setup:
  - Thresholds: [-$100 = 5min, -$200 = 15min, -$300 = 30min]
  - Trade closes: P&L = -$150

Timeline:
  1. Trade executes with -$150 loss
  2. Checks: -$150 <= -$100 (triggered!)
  3. Applies: 5 minute cooldown
  4. CLI shows: "🟡 COOLDOWN - $150 loss - Unlocks in 4:58"
  5. After 5 minutes: Auto-unlock, can trade again
```

### **Scenario 3: Large Loss (30 Min Cooldown)**
```
Setup:
  - Thresholds: [-$100 = 5min, -$200 = 15min, -$300 = 30min]
  - Trade closes: P&L = -$350

Timeline:
  1. Trade executes with -$350 loss
  2. Checks: -$350 <= -$300 (triggered at highest threshold!)
  3. Applies: 30 minute cooldown
  4. CLI shows: "🟡 COOLDOWN - $350 loss - Take a break - Unlocks in 29:42"
  5. After 30 minutes: Auto-unlock
```

### **Scenario 4: Multiple Losses in Series**
```
Timeline:
  1. t=0: Trade 1 closes at -$120 → 5 min cooldown
  2. t=5min: Cooldown expires
  3. t=6min: Trade 2 closes at -$95 → No cooldown (< $100)
  4. t=7min: Trade 3 closes at -$250 → 15 min cooldown
  5. t=22min: Cooldown expires
  6. Each loss is independent - cooldowns don't stack
```

### **Scenario 5: Profitable Trade (No Trigger)**
```
Setup:
  - Trade closes: P&L = +$200

Result:
  - Profitable trade → NO BREACH
  - Rule only triggers on losses
```

---

## 📊 State Tracking

**In-Memory State:**
```python
# Active cooldowns (managed by lockout_manager)
active_cooldowns = {
    123: {  # account_id
        'reason': 'Cooldown after $150 loss',
        'expires_at': datetime(2025, 1, 17, 14, 35, 0),
        'duration_seconds': 300
    }
}
```

**SQLite Persistence:**
```sql
CREATE TABLE loss_cooldowns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    trade_id BIGINT NOT NULL,
    loss_amount REAL NOT NULL,
    cooldown_duration INTEGER NOT NULL,
    triggered_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    completed BOOLEAN DEFAULT 0
);

-- Track all loss-triggered cooldowns for analysis
CREATE INDEX idx_loss_cooldowns_account
ON loss_cooldowns(account_id, triggered_at DESC);

-- Track losing trades separately for reporting
CREATE TABLE losing_trades (
    trade_id BIGINT PRIMARY KEY,
    account_id INTEGER NOT NULL,
    contract_id TEXT,
    timestamp DATETIME NOT NULL,
    pnl REAL NOT NULL,
    cooldown_triggered BOOLEAN DEFAULT 0,
    cooldown_duration INTEGER
);
```

---

## ⚠️ Edge Cases

### **Half-Turn Trades (profitAndLoss = null)**
- Opening trades have `profitAndLoss = null`
- Don't trigger cooldown on null P&L
- Only closing trades (with actual P&L) trigger rule

### **Voided Trades**
- If `voided: true` → ignore trade completely
- Don't trigger cooldown on voided trades
- Voided = cancelled or reversed trade

### **Exactly at Threshold**
- If loss is EXACTLY at threshold (e.g., -$100.00)
- Still triggers cooldown (uses `<=` comparison)
- Edge case: -$100.00 triggers -$100 threshold

### **Multiple Cooldowns**
- New cooldown during active cooldown
- Replace existing cooldown with new one (if longer)
- Or extend existing cooldown by new duration (configurable)

### **Daemon Restart During Cooldown**
- Load active cooldowns from database on startup
- Recalculate remaining time based on `expires_at`
- If already expired, don't re-apply cooldown

### **Fees Included in P&L**
- `profitAndLoss` field already includes fees
- Don't need to subtract fees separately
- Use P&L value as-is from API

### **Positive P&L After Fees**
- Trade might show profit after fees are factored in
- If final P&L >= 0, don't trigger cooldown
- Only negative P&L triggers rule

---

## 🔧 Background Processing

**Cooldown Expiration Monitor (runs every second):**
```python
def check_cooldown_expirations():
    """Auto-unlock accounts when cooldowns expire."""

    now = datetime.now()

    for account_id, cooldown in active_cooldowns.items():
        if now >= cooldown['expires_at']:
            # Cooldown has expired
            lockout_manager.remove_cooldown(account_id)

            logger.info(
                f"Cooldown expired for account {account_id} - "
                f"Reason: {cooldown['reason']}"
            )

            # Mark as completed in database
            db.execute("""
                UPDATE loss_cooldowns
                SET completed = 1
                WHERE account_id = ?
                AND expires_at = ?
            """, (account_id, cooldown['expires_at']))
```

**Loss Tracking (for analytics):**
```python
def on_losing_trade(trade_event):
    """Track losing trades for pattern analysis."""

    db.execute("""
        INSERT INTO losing_trades
        (trade_id, account_id, contract_id, timestamp, pnl, cooldown_triggered, cooldown_duration)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        trade_event['id'],
        trade_event['accountId'],
        trade_event['contractId'],
        trade_event['creationTimestamp'],
        trade_event['profitAndLoss'],
        True if cooldown_applied else False,
        cooldown_duration if cooldown_applied else None
    ))
```

**No Active Position Monitoring Required:**
- This rule only triggers on completed trades
- No need to monitor positions or quotes
- Purely event-driven on `GatewayUserTrade`

---

## 🔗 Dependencies

- **MOD-002:** `set_cooldown()`, `remove_cooldown()`
- **MOD-003:** Timer-based auto-unlock
- **API-INT-001:** `GatewayUserTrade` event
- **src/state/cooldown_manager.py:** Cooldown state management
- **src/state/persistence.py:** SQLite cooldown tracking
- **POST /api/Trade/search:** Historical trade data (optional, for analysis)

---

**This rule prevents revenge trading - forcing traders to take a break after significant losses to reset emotionally.**
