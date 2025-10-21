---
doc_id: RULE-008
version: 3.0
last_updated: 2025-10-21
dependencies: [MOD-001, API-INT-001]
enforcement_type: Trade-by-Trade (No Lockout)
---

# RULE-008: NoStopLossGrace

**Purpose:** Enforce stop-loss placement within grace period after position opens.

---

## ⚙️ Configuration

```yaml
no_stop_loss_grace:
  enabled: true
  grace_period_seconds: 30  # Must place SL within 30 seconds of opening position
  enforcement: "close_position"
  lockout_on_breach: false
```

---

## 🎯 Trigger Condition

**Primary Event:** `GatewayUserPosition` (when position opens or updates)
**Secondary Event:** `GatewayUserOrder` (to detect stop-loss orders)

**Logic:**
```python
# Track positions pending stop-loss
positions_pending_stop = {}

def on_position_opened(position_event):
    """Called when GatewayUserPosition event received."""

    position_id = position_event['id']
    contract_id = position_event['contractId']
    account_id = position_event['accountId']
    entry_price = position_event['averagePrice']
    position_type = position_event['type']  # 1=Long, 2=Short

    # Start tracking this position
    positions_pending_stop[position_id] = {
        'contract_id': contract_id,
        'account_id': account_id,
        'entry_price': entry_price,
        'position_type': position_type,
        'opened_at': datetime.now(),
        'has_stop_loss': False
    }

    logger.info(f"Position {position_id} opened - grace period started")

def on_order_placed(order_event):
    """Called when GatewayUserOrder event received."""

    # Check if this order is a stop-loss for any pending position
    for position_id, pending in positions_pending_stop.items():
        if order_event['contractId'] == pending['contract_id']:
            if is_stop_loss_order(order_event, pending):
                pending['has_stop_loss'] = True
                logger.info(f"Stop-loss detected for position {position_id}")
                del positions_pending_stop[position_id]
                break

def is_stop_loss_order(order, position):
    """Detect if order is a stop-loss for the position."""

    # Stop-loss orders have type: Stop (4), StopLimit (3), or TrailingStop (5)
    if order['type'] not in [3, 4, 5]:
        return False

    # For LONG position: SL is SELL order with stop price BELOW entry
    if position['position_type'] == 1:  # Long
        if order['side'] == 1:  # Sell
            if order['stopPrice'] is not None and order['stopPrice'] < position['entry_price']:
                return True

    # For SHORT position: SL is BUY order with stop price ABOVE entry
    elif position['position_type'] == 2:  # Short
        if order['side'] == 0:  # Buy
            if order['stopPrice'] is not None and order['stopPrice'] > position['entry_price']:
                return True

    return False

def check_grace_periods():
    """Background task - runs every second in daemon loop."""

    now = datetime.now()
    grace_period = config['grace_period_seconds']

    for position_id, pending in list(positions_pending_stop.items()):
        elapsed = (now - pending['opened_at']).seconds

        # Grace period expired and no stop-loss?
        if elapsed >= grace_period and not pending['has_stop_loss']:
            # BREACH DETECTED
            logger.warning(f"RULE-008 BREACH: Position {position_id} has no stop-loss after {grace_period}s")

            # Enforce: Close position
            actions.close_position(pending['account_id'], pending['contract_id'])

            # Log enforcement
            logger.log_enforcement(
                f"NoStopLossGrace breach - Closed position {position_id} "
                f"(no SL within {grace_period}s)"
            )

            # Remove from tracking
            del positions_pending_stop[position_id]
```

---

## 🚨 Enforcement Action

**Type:** Trade-by-Trade (NO lockout)

**Action Sequence:**
1. ✅ **Close position** via `MOD-001.close_position()`
2. ✅ **Log enforcement** to `logs/enforcement.log`
3. ✅ **Update Trader CLI** with warning
4. ❌ **NO lockout** - trader can open next position immediately

**Enforcement Code:**
```python
def enforce(position_id, pending_position):
    """Execute enforcement for no stop-loss."""

    # Close the position
    success = actions.close_position(
        account_id=pending_position['account_id'],
        contract_id=pending_position['contract_id']
    )

    if success:
        logger.log_enforcement(
            f"RULE-008: Position {position_id} closed - "
            f"No stop-loss within {config['grace_period_seconds']}s"
        )

    # NO lockout - trader can trade again
```

---

## 📡 API Requirements

### **SignalR Events (Trigger):**

**GatewayUserPosition** (detects position open):
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

**GatewayUserOrder** (detects stop-loss placement):
```json
{
  "id": 789,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "type": 4,
  "side": 1,
  "stopPrice": 20950.00,
  "status": 1
}
```

**Key Fields:**
- `type`: OrderType (3=StopLimit, 4=Stop, 5=TrailingStop)
- `side`: OrderSide (0=Buy, 1=Sell)
- `stopPrice`: Trigger price for stop order

### **REST API Calls (Enforcement):**

```http
POST /api/Position/closeContract
Authorization: Bearer {jwt_token}
{
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25"
}
```

---

## 🧪 Test Scenarios

### **Scenario 1: Stop-Loss Placed in Time**
```
1. Position opens: Long 1 MNQ @ $21,000
2. Grace period: 30 seconds
3. At t=10s: Trader places Sell Stop @ $20,950
4. Rule detects stop-loss → NO BREACH
5. Position remains open
```

### **Scenario 2: No Stop-Loss - Breach**
```
1. Position opens: Long 1 MNQ @ $21,000
2. Grace period: 30 seconds
3. At t=30s: No stop-loss detected
4. Rule triggers → BREACH
5. Position closed immediately
6. Trader CLI shows: "⚠️ Position closed - No stop-loss within 30s"
```

### **Scenario 3: Take-Profit Only (Not a Stop-Loss)**
```
1. Position opens: Long 1 MNQ @ $21,000
2. At t=5s: Trader places Sell Limit @ $21,050 (take-profit)
3. At t=30s: No stop-loss detected (limit order doesn't count)
4. Rule triggers → BREACH
5. Position closed
```

### **Scenario 4: Wrong Direction Order**
```
1. Position opens: Short 1 MNQ @ $21,000
2. At t=10s: Trader places Sell Stop @ $20,950 (wrong direction)
3. At t=30s: No valid stop-loss for SHORT position
4. Rule triggers → BREACH
5. Position closed
```

---

## 📊 State Tracking

**In-Memory State:**
```python
positions_pending_stop = {
    456: {
        'contract_id': 'CON.F.US.MNQ.U25',
        'account_id': 123,
        'entry_price': 21000.25,
        'position_type': 1,  # Long
        'opened_at': datetime(2025, 1, 17, 14, 23, 0),
        'has_stop_loss': False
    }
}
```

**SQLite Persistence:**
```sql
CREATE TABLE pending_stop_loss (
    position_id INTEGER PRIMARY KEY,
    account_id INTEGER,
    contract_id TEXT,
    entry_price REAL,
    position_type INTEGER,
    opened_at DATETIME,
    has_stop_loss BOOLEAN DEFAULT 0
);
```

---

## ⚠️ Edge Cases

### **Position Closed Before Grace Period Expires**
- Remove from tracking when position closes
- No breach triggered

### **Stop-Loss Cancelled/Modified**
- If stop-loss order cancelled during grace period → BREACH
- Track order status updates

### **Multiple Positions Same Contract**
- Track each position independently by position ID
- Each has separate grace period

### **Position Scaled In/Out**
- Position size changes → keep existing stop-loss tracking
- Don't restart grace period on size updates

---

## 🔗 Dependencies

- **MOD-001:** `close_position()`
- **API-INT-001:** `GatewayUserPosition`, `GatewayUserOrder` events
- **src/utils/datetime_helpers.py:** Time calculations
- **src/state/persistence.py:** State save/restore

---

**This rule ensures traders always use stop-losses for risk management.**
