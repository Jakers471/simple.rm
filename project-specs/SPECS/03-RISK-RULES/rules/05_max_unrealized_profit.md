---
doc_id: RULE-005
version: 3.0
last_updated: 2025-10-21
dependencies: [MOD-001, MOD-002, MOD-004, API-INT-001]
enforcement_type: Hard Lockout (Until Reset)
---

# RULE-005: MaxUnrealizedProfit

**Purpose:** Enforce profit target - close positions when daily unrealized profit limit is hit to lock in gains and prevent giving back profits.

---

## ⚙️ Configuration

```yaml
max_unrealized_profit:
  enabled: true
  limit: 1000               # Take profit at +$1000 unrealized profit
  reset_time: "17:00"       # Daily reset time (5:00 PM)
  timezone: "America/New_York"
  enforcement: "close_all_and_lockout"
  lockout_until_reset: true
  check_interval_seconds: 1  # How often to recalculate (every second)
```

---

## 🎯 Trigger Condition

**Primary Events:**
- `GatewayUserPosition` (when positions open/close/change)
- `GatewayQuote` (when market prices update)

**Logic:**
```python
def check_with_current_prices():
    """Check if profit target hit."""

    # Calculate total unrealized P&L (via MOD-005)
    total_unrealized_pnl = pnl_tracker.calculate_unrealized_pnl(account_id)

    # Check if profit target hit (positive value)
    if total_unrealized_pnl >= config['limit']:
        return BREACH
```

**Example Calculation:**

```
Position 1: Long 2 MNQ @ 21000.00
  - Current price: 21050.00
  - Tick size: 0.25
  - Tick value: $0.50
  - Price diff: +50.00
  - Ticks moved: +50.00 / 0.25 = +200 ticks
  - P&L: +200 * $0.50 * 2 = +$200

Position 2: Long 1 ES @ 5800.00
  - Current price: 5864.00
  - Tick size: 0.25
  - Tick value: $12.50
  - Price diff: +64.00
  - Ticks moved: +64.00 / 0.25 = +256 ticks
  - P&L: +256 * $12.50 * 1 = +$3,200

Total Unrealized P&L: +$200 + $3,200 = +$3,400
Limit: +$1,000
PROFIT TARGET HIT!
```

---

## 🚨 Enforcement Action

**Type:** Hard Lockout (trader CANNOT trade until reset time)

**Action Sequence:**
1. ✅ **Close all positions** (via MOD-001) - locks in current profit
2. ✅ **Cancel all orders** (via MOD-001)
3. ✅ **Set lockout** (via MOD-002) → Until `reset_time`
4. ✅ **Log enforcement**
5. ✅ **Update Trader CLI** → Show countdown timer

**Enforcement Code:**
```python
def enforce(account_id, total_unrealized_pnl):
    # Close everything immediately to lock in profits
    actions.close_all_positions(account_id)
    actions.cancel_all_orders(account_id)

    # Calculate next reset time
    reset_time = datetime.combine(
        datetime.now().date(),
        time(17, 0)  # 5:00 PM
    )
    if datetime.now() > reset_time:
        reset_time += timedelta(days=1)  # Next day if past 5pm

    # Set lockout
    lockout_manager.set_lockout(
        account_id=account_id,
        reason=f"Daily profit target hit (${total_unrealized_pnl:.2f})",
        until=reset_time
    )

    # Log enforcement
    logger.log_enforcement(
        f"RULE-005: Daily profit target hit - "
        f"Unrealized P&L: ${total_unrealized_pnl:.2f}, Target: ${config['limit']:.2f} - "
        f"Positions closed, locked until {reset_time.strftime('%I:%M %p')}"
    )
```

---

## 📡 API Requirements

### **SignalR Events (Trigger):**

**GatewayUserPosition** (tracks open positions):
```json
{
  "id": 456,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "creationTimestamp": "2024-07-21T13:45:00Z",
  "type": 1,
  "size": 2,
  "averagePrice": 21000.25
}
```

**GatewayQuote** (real-time price updates):
```json
{
  "symbol": "F.US.MNQ",
  "symbolName": "/MNQ",
  "lastPrice": 21050.00,
  "bestBid": 21049.75,
  "bestAsk": 21050.25,
  "timestamp": "2024-07-21T13:45:00Z"
}
```

### **REST API Calls (Setup & Enforcement):**

**Get Contract Info** (for tick value):
```http
POST /api/Contract/searchById
Authorization: Bearer {jwt_token}
{
  "contractId": "CON.F.US.MNQ.U25"
}

Response:
{
  "contract": {
    "id": "CON.F.US.MNQ.U25",
    "tickSize": 0.25,
    "tickValue": 0.5
  }
}
```

**Close All Positions** (enforcement):
```http
POST /api/Position/searchOpen
POST /api/Position/closeContract (for each position)
POST /api/Order/searchOpen
POST /api/Order/cancel (for each order)
```

---

## 🧪 Test Scenarios

### **Scenario 1: Profit Target Hit**
```
Setup:
  - Long 2 MNQ @ 21000.00
  - Limit: +$1,000

Timeline:
  1. t=0: Position opens at 21000.00
  2. t=10s: Price rises to 21050.00 → Unrealized P&L = +$200 (no breach)
  3. t=30s: Price rises to 21500.00 → Unrealized P&L = +$1,000 (at limit, no breach)
  4. t=45s: Price rises to 21510.00 → Unrealized P&L = +$1,020 (PROFIT TARGET HIT!)
  5. Rule triggers → Close positions, lock in profit, lockout until 5pm
```

### **Scenario 2: Multiple Positions, Combined Profit**
```
Positions:
  - Long 1 MNQ @ 21000 → current 21200 → +$400
  - Long 1 ES @ 5800 → current 5848 → +$1,200
  - Total: +$1,600
  - Limit: +$1,000
  - PROFIT TARGET HIT!
```

### **Scenario 3: One Position Profit, One Loss (Net Profit)**
```
Positions:
  - Long 2 MNQ @ 21000 → current 21400 → +$1,600
  - Long 1 ES @ 5800 → current 5752 → -$600
  - Total: +$1,000
  - Limit: +$1,000
  - AT LIMIT - NO BREACH (must be >= to breach)
  - At 21410: +$1,620 - $600 = +$1,020 → BREACH!
```

### **Scenario 4: Price Pullback Before Target**
```
Timeline:
  1. Long 2 MNQ @ 21000
  2. Price rises to 21500 → +$1,000 (at limit, no breach)
  3. Price pulls back to 21400 → +$800 (safe)
  4. Never breaches, trader can manually exit or ride it
```

---

## 📊 State Tracking

**Contract Cache (In-Memory):**
```python
contract_cache = {
    'CON.F.US.MNQ.U25': {
        'tickSize': 0.25,
        'tickValue': 0.5,
        'symbolId': 'F.US.MNQ'
    },
    'CON.F.US.ES.U25': {
        'tickSize': 0.25,
        'tickValue': 12.5,
        'symbolId': 'F.US.ES'
    }
}
```

**Quote Tracker (In-Memory):**
```python
quote_tracker = {
    'CON.F.US.MNQ.U25': {
        'lastPrice': 21050.00,
        'lastUpdated': datetime(2025, 1, 17, 14, 23, 0)
    }
}
```

**SQLite Persistence:**
```sql
CREATE TABLE daily_unrealized_profit (
    account_id INTEGER,
    timestamp DATETIME,
    unrealized_pnl REAL,
    PRIMARY KEY (account_id, timestamp)
);

-- Track historical unrealized P&L for analysis and reporting
```

---

## ⚠️ Edge Cases

### **No Quote Data Available**
- If no recent quote for contract → skip that position from calculation
- Log warning: "Missing quote data for {contract_id}"
- Don't breach based on incomplete data

### **Position Closes During Calculation**
- Position closes → unrealized P&L becomes realized
- Remove from unrealized P&L calculation
- Realized profit handled by RULE-003 (if implemented)

### **Stale Quote Data**
- If quote older than 10 seconds → consider stale
- Log warning, but still use (better than no data)
- Configuration: `max_quote_age_seconds: 10`

### **Multiple Positions Same Contract**
- Aggregate all positions for same contract
- Net out longs vs shorts
- Calculate combined P&L

### **Contract Cache Miss**
- If contract not in cache → fetch via `/api/Contract/searchById`
- Cache result for future use
- Retry on API failure

### **Profit Target Hit Multiple Times**
- First breach closes all positions and locks out
- Subsequent position opens after reset are independent
- Each day has its own profit target

---

## 🔧 Background Processing

**Continuous Monitoring:**
```python
# In daemon main loop - runs every second
def check_unrealized_profit_rules():
    """Called every second in background."""

    if max_unrealized_profit.enabled:
        # Recalculate with current quotes
        breach = max_unrealized_profit.check_with_current_prices()

        if breach:
            enforcement_engine.execute(breach)
```

**Quote Subscription Management:**
```python
def on_position_opened(position_event):
    """Subscribe to quotes when position opens."""
    contract_id = position_event['contractId']

    # Subscribe to Market Hub for this contract
    market_hub.subscribe_to_contract_quotes(contract_id)

def on_position_closed(position_event):
    """Unsubscribe when all positions for contract are closed."""
    contract_id = position_event['contractId']

    # Check if any other positions for this contract
    other_positions = state_manager.get_positions_by_contract(contract_id)

    if not other_positions:
        # No more positions, unsubscribe to save bandwidth
        market_hub.unsubscribe_from_contract_quotes(contract_id)
```

---

## 🔗 Dependencies

- **MOD-001:** `close_all_positions()`, `cancel_all_orders()`
- **MOD-002:** `set_lockout()`
- **MOD-004:** Daily reset scheduler
- **MOD-005:** `calculate_unrealized_pnl()` (uses MOD-006, MOD-007, MOD-009 internally)
- **API-INT-001:** `GatewayUserPosition`, `GatewayQuote` events

---

**This rule enforces "take profit and stop for the day" - protecting against giving back hard-earned gains.**
