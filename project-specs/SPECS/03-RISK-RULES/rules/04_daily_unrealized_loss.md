---
doc_id: RULE-004
version: 3.0
last_updated: 2025-10-21
dependencies: [MOD-001, MOD-002, MOD-004, API-INT-001]
enforcement_type: Hard Lockout (Until Reset)
---

# RULE-004: DailyUnrealizedLoss

**Purpose:** Enforce hard daily floating loss limit - stops trading when unrealized P&L drops below threshold.

---

## ⚙️ Configuration

```yaml
daily_unrealized_loss:
  enabled: true
  loss_limit: 300.00        # Max unrealized loss (positive value in $)
  scope: "per_position"     # "total" or "per_position"
  action: "CLOSE_POSITION"  # "CLOSE_POSITION" or "CLOSE_ALL_AND_LOCKOUT"
  lockout: false            # Whether to lock account (only with scope="total")
```

**Configuration Modes:**

**Mode 1: Per-Position Stop-Loss** (Recommended)
```yaml
daily_unrealized_loss:
  enabled: true
  loss_limit: 300.00
  scope: "per_position"     # Monitor each position individually
  action: "CLOSE_POSITION"  # Close only the losing position
  lockout: false            # No lockout
```

**Mode 2: Total Account Unrealized Loss** (Legacy)
```yaml
daily_unrealized_loss:
  enabled: true
  loss_limit: 300.00
  scope: "total"            # Monitor total unrealized P&L
  action: "CLOSE_ALL_AND_LOCKOUT"  # Close all + lockout
  lockout: true
  lockout_until: "daily_reset"  # or "permanent"
```

---

## 🎯 Trigger Condition

**Primary Events:**
- `GatewayUserPosition` (when positions open/close/change)
- `GatewayQuote` (when market prices update)

**Logic:**
```python
def check_with_current_prices():
    """Check if unrealized loss limit breached."""

    # Calculate total unrealized P&L (via MOD-005)
    total_unrealized_pnl = pnl_tracker.calculate_unrealized_pnl(account_id)

    # Check if breach (negative value, below limit)
    if total_unrealized_pnl <= config['limit']:
        return BREACH
```

**Example Calculation:**

```
Position 1: Long 2 MNQ @ 21000.00
  - Current price: 20950.00
  - Tick size: 0.25
  - Tick value: $0.50
  - Price diff: -50.00
  - Ticks moved: -50.00 / 0.25 = -200 ticks
  - P&L: -200 * $0.50 * 2 = -$200

Position 2: Long 1 ES @ 5800.00
  - Current price: 5775.00
  - Tick size: 0.25
  - Tick value: $12.50
  - Price diff: -25.00
  - Ticks moved: -25.00 / 0.25 = -100 ticks
  - P&L: -100 * $12.50 * 1 = -$1,250

Total Unrealized P&L: -$200 + (-$1,250) = -$1,450
Limit: -$300
BREACH DETECTED!
```

---

## 🚨 Enforcement Action

**Type:** Hard Lockout (trader CANNOT trade until reset time)

**Action Sequence:**
1. ✅ **Close all positions** (via MOD-001) - locks in current loss
2. ✅ **Cancel all orders** (via MOD-001)
3. ✅ **Set lockout** (via MOD-002) → Until `reset_time`
4. ✅ **Log enforcement**
5. ✅ **Update Trader CLI** → Show countdown timer

**Enforcement Code:**
```python
def enforce(account_id, total_unrealized_pnl):
    # Close everything immediately
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
        reason=f"Daily unrealized loss limit hit (${total_unrealized_pnl:.2f})",
        until=reset_time
    )

    # Log enforcement
    logger.log_enforcement(
        f"RULE-004: Daily unrealized loss breach - "
        f"Unrealized P&L: ${total_unrealized_pnl:.2f}, Limit: ${config['limit']:.2f} - "
        f"Locked until {reset_time.strftime('%I:%M %p')}"
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
  "lastPrice": 20950.00,
  "bestBid": 20949.75,
  "bestAsk": 20950.25,
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

### **Scenario 1: Floating Loss Breach**
```
Setup:
  - Long 2 MNQ @ 21000.00
  - Limit: -$300

Timeline:
  1. t=0: Position opens at 21000.00
  2. t=10s: Price drops to 20950.00 → Unrealized P&L = -$200 (no breach)
  3. t=30s: Price drops to 20700.00 → Unrealized P&L = -$300 (no breach, at limit)
  4. t=45s: Price drops to 20690.00 → Unrealized P&L = -$310 (BREACH!)
  5. Rule triggers → Close positions, lockout until 5pm
```

### **Scenario 2: Multiple Positions, Combined Loss**
```
Positions:
  - Long 1 MNQ @ 21000 → current 20900 → -$200
  - Long 1 ES @ 5800 → current 5792 → -$200
  - Total: -$400
  - Limit: -$300
  - BREACH!
```

### **Scenario 3: Hedged Positions (No Breach)**
```
Positions:
  - Long 2 MNQ @ 21000 → current 20900 → -$200
  - Short 2 MNQ @ 20900 → current 20900 → $0
  - Total: -$200
  - Limit: -$300
  - NO BREACH
```

### **Scenario 4: Price Recovers Before Breach**
```
Timeline:
  1. Long 2 MNQ @ 21000
  2. Price drops to 20700 → -$300 (at limit, no breach)
  3. Price recovers to 20800 → -$200 (safe)
  4. Never breaches
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
        'lastPrice': 20950.00,
        'lastUpdated': datetime(2025, 1, 17, 14, 23, 0)
    }
}
```

**SQLite Persistence:**
```sql
CREATE TABLE daily_unrealized_pnl (
    account_id INTEGER,
    timestamp DATETIME,
    unrealized_pnl REAL,
    PRIMARY KEY (account_id, timestamp)
);

-- Track historical unrealized P&L for analysis
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
- Realized loss handled by RULE-003

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

---

## 🔧 Background Processing

**Continuous Monitoring:**
```python
# In daemon main loop - runs every second
def check_unrealized_pnl_rules():
    """Called every second in background."""

    if daily_unrealized_loss.enabled:
        # Recalculate with current quotes
        breach = daily_unrealized_loss.check_with_current_prices()

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

**This rule protects against floating losses before they become realized losses.**
