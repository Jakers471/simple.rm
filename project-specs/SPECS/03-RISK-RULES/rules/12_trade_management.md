---
doc_id: RULE-012
version: 3.0
last_updated: 2025-10-21
dependencies: [API-INT-001]
enforcement_type: Trade-by-Trade (Automation)
---

# RULE-012: TradeManagement

**Purpose:** Automated trade management - auto breakeven stop-loss and trailing stops to protect profits without manual intervention.

---

## ⚙️ Configuration

```yaml
trade_management:
  enabled: true
  auto_breakeven:
    enabled: true
    profit_trigger_ticks: 10  # Move SL to breakeven after +10 ticks profit
    offset_ticks: 0           # Breakeven + offset (0 = exact breakeven)
  trailing_stop:
    enabled: true
    activation_ticks: 20      # Start trailing after +20 ticks profit
    trail_distance_ticks: 10  # Trail 10 ticks behind high water mark
    update_frequency: 1       # Update every 1 tick movement (or seconds)
```

---

## 🎯 Trigger Condition

**Primary Events:**
- `GatewayUserPosition` (when position opens or updates)
- `GatewayQuote` (when market prices update)
- `GatewayUserOrder` (to track stop-loss orders)

**Logic:**

```python
# Track positions and their stop-loss orders
position_tracking = {}

def on_position_opened(position_event):
    """Called when GatewayUserPosition event received."""

    position_id = position_event['id']
    account_id = position_event['accountId']
    contract_id = position_event['contractId']
    entry_price = position_event['averagePrice']
    position_type = position_event['type']  # 1=Long, 2=Short
    size = position_event['size']

    # Initialize tracking for this position
    position_tracking[position_id] = {
        'account_id': account_id,
        'contract_id': contract_id,
        'entry_price': entry_price,
        'position_type': position_type,
        'size': size,
        'stop_loss_order_id': None,
        'breakeven_applied': False,
        'trailing_active': False,
        'high_water_mark': entry_price if position_type == 1 else None,
        'low_water_mark': entry_price if position_type == 2 else None
    }

    logger.info(f"Tracking position {position_id} for auto-management")

def on_quote_update(quote_event, contract_id):
    """Called when GatewayQuote event received."""

    current_price = quote_event['lastPrice']

    # Check all positions for this contract
    for position_id, tracking in position_tracking.items():
        if tracking['contract_id'] != contract_id:
            continue

        # Get contract specs
        contract = contract_cache.get_contract(contract_id)
        tick_size = contract['tickSize']

        # Calculate profit in ticks
        profit_ticks = calculate_profit_ticks(
            tracking['entry_price'],
            current_price,
            tracking['position_type'],
            tick_size
        )

        # Auto Breakeven
        if config['auto_breakeven']['enabled']:
            if not tracking['breakeven_applied']:
                if profit_ticks >= config['auto_breakeven']['profit_trigger_ticks']:
                    apply_breakeven_stop(position_id, tracking)

        # Trailing Stop
        if config['trailing_stop']['enabled']:
            if profit_ticks >= config['trailing_stop']['activation_ticks']:
                update_trailing_stop(position_id, tracking, current_price, tick_size)

def calculate_profit_ticks(entry_price, current_price, position_type, tick_size):
    """Calculate profit in ticks."""

    price_diff = current_price - entry_price
    ticks_moved = price_diff / tick_size

    if position_type == 1:  # Long
        return ticks_moved
    elif position_type == 2:  # Short
        return -ticks_moved

    return 0

def apply_breakeven_stop(position_id, tracking):
    """Move stop-loss to breakeven."""

    contract = contract_cache.get_contract(tracking['contract_id'])
    tick_size = contract['tickSize']

    # Calculate breakeven price with offset
    offset = config['auto_breakeven']['offset_ticks'] * tick_size

    if tracking['position_type'] == 1:  # Long
        new_stop_price = tracking['entry_price'] + offset
    elif tracking['position_type'] == 2:  # Short
        new_stop_price = tracking['entry_price'] - offset

    # Modify or create stop-loss order
    if tracking['stop_loss_order_id']:
        # Modify existing stop
        modify_stop_loss_order(
            tracking['account_id'],
            tracking['stop_loss_order_id'],
            new_stop_price
        )
    else:
        # Create new stop at breakeven
        order_id = create_stop_loss_order(
            tracking['account_id'],
            tracking['contract_id'],
            tracking['position_type'],
            tracking['size'],
            new_stop_price
        )
        tracking['stop_loss_order_id'] = order_id

    tracking['breakeven_applied'] = True

    logger.log_enforcement(
        f"RULE-012: Auto-breakeven applied - "
        f"Position {position_id} stop moved to {new_stop_price:.2f}"
    )

def update_trailing_stop(position_id, tracking, current_price, tick_size):
    """Update trailing stop based on high/low water mark."""

    trail_distance = config['trailing_stop']['trail_distance_ticks'] * tick_size

    if tracking['position_type'] == 1:  # Long
        # Update high water mark
        if tracking['high_water_mark'] is None or current_price > tracking['high_water_mark']:
            tracking['high_water_mark'] = current_price

        # Calculate trailing stop price
        new_stop_price = tracking['high_water_mark'] - trail_distance

        # Don't move stop down, only up
        current_stop = get_current_stop_price(tracking['stop_loss_order_id'])
        if current_stop and new_stop_price <= current_stop:
            return  # Don't trail down

    elif tracking['position_type'] == 2:  # Short
        # Update low water mark
        if tracking['low_water_mark'] is None or current_price < tracking['low_water_mark']:
            tracking['low_water_mark'] = current_price

        # Calculate trailing stop price
        new_stop_price = tracking['low_water_mark'] + trail_distance

        # Don't move stop up, only down
        current_stop = get_current_stop_price(tracking['stop_loss_order_id'])
        if current_stop and new_stop_price >= current_stop:
            return  # Don't trail up

    # Modify stop-loss order
    if tracking['stop_loss_order_id']:
        modify_stop_loss_order(
            tracking['account_id'],
            tracking['stop_loss_order_id'],
            new_stop_price
        )
    else:
        # Create new trailing stop
        order_id = create_stop_loss_order(
            tracking['account_id'],
            tracking['contract_id'],
            tracking['position_type'],
            tracking['size'],
            new_stop_price
        )
        tracking['stop_loss_order_id'] = order_id

    tracking['trailing_active'] = True

    logger.info(
        f"Trailing stop updated - Position {position_id} stop at {new_stop_price:.2f}"
    )
```

---

## 🚨 Enforcement Action

**Type:** Trade-by-Trade Automation (NO position close, NO lockout)

**Action Sequence:**
1. ✅ **Modify existing stop-loss order** (via API)
2. ✅ **OR create new stop-loss order** if none exists
3. ✅ **Log modification**
4. ✅ **Update position tracking state**
5. ❌ **NO position close** (just modify stop)
6. ❌ **NO lockout**

**Enforcement Code:**
```python
def modify_stop_loss_order(account_id, order_id, new_stop_price):
    """Modify existing stop-loss order to new price."""

    response = api.modify_order(
        accountId=account_id,
        orderId=order_id,
        stopPrice=new_stop_price
    )

    if response['success']:
        logger.info(
            f"Stop-loss order {order_id} modified to {new_stop_price:.2f}"
        )
        return True

    logger.error(
        f"Failed to modify stop-loss order {order_id}: {response.get('errorMessage')}"
    )
    return False

def create_stop_loss_order(account_id, contract_id, position_type, size, stop_price):
    """Create new stop-loss order for position."""

    # Determine order side (opposite of position)
    if position_type == 1:  # Long position
        order_side = 1  # Sell to close
    elif position_type == 2:  # Short position
        order_side = 0  # Buy to close

    response = api.place_order(
        accountId=account_id,
        contractId=contract_id,
        type=4,  # Stop order
        side=order_side,
        size=size,
        stopPrice=stop_price
    )

    if response['success']:
        order_id = response['orderId']
        logger.info(
            f"Stop-loss order {order_id} created at {stop_price:.2f}"
        )
        return order_id

    logger.error(
        f"Failed to create stop-loss order: {response.get('errorMessage')}"
    )
    return None
```

---

## 📡 API Requirements

### **SignalR Events (Trigger):**

**GatewayUserPosition** (tracks positions):
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

**GatewayQuote** (monitors price movement):
```json
{
  "symbol": "F.US.MNQ",
  "symbolName": "/MNQ",
  "lastPrice": 21010.50,
  "bestBid": 21010.25,
  "bestAsk": 21010.75,
  "timestamp": "2024-07-21T13:45:30Z"
}
```

**GatewayUserOrder** (tracks stop-loss orders):
```json
{
  "id": 789,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "type": 4,
  "side": 1,
  "size": 2,
  "stopPrice": 21005.00,
  "status": 1
}
```

### **REST API Calls:**

**Modify Order** (update stop-loss):
```http
POST /api/Order/modify
Authorization: Bearer {jwt_token}
{
  "accountId": 123,
  "orderId": 789,
  "stopPrice": 21005.00
}

Response:
{
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

**Place Order** (create new stop-loss):
```http
POST /api/Order/place
Authorization: Bearer {jwt_token}
{
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "type": 4,
  "side": 1,
  "size": 2,
  "stopPrice": 21000.00
}

Response:
{
  "orderId": 789,
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

**Get Contract Info** (for tick size):
```http
POST /api/Contract/searchById
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

---

## 🧪 Test Scenarios

### **Scenario 1: Auto-Breakeven Applied**
```
Setup:
  - Long 2 MNQ @ 21000.00
  - Breakeven trigger: +10 ticks = +$2.50
  - Tick size: 0.25

Timeline:
  1. t=0: Position opens at 21000.00, no stop-loss
  2. t=30s: Price rises to 21002.00 → +8 ticks (not triggered)
  3. t=60s: Price rises to 21002.75 → +11 ticks (TRIGGERED!)
  4. Auto-breakeven: Create stop @ 21000.00 (entry price)
  5. Position now protected at breakeven
  6. If price drops to 21000.00, stop triggers (no loss)
```

### **Scenario 2: Trailing Stop Activation**
```
Setup:
  - Long 1 ES @ 5800.00
  - Trailing activation: +20 ticks
  - Trail distance: 10 ticks
  - Tick size: 0.25

Timeline:
  1. Position opens at 5800.00
  2. Price rises to 5805.00 → +20 ticks (trailing activates)
  3. High water mark: 5805.00
  4. Trailing stop set at: 5805.00 - (10 * 0.25) = 5802.50
  5. Price rises to 5810.00 → new high water mark
  6. Trailing stop updated to: 5810.00 - 2.50 = 5807.50
  7. Price pulls back to 5807.51 → stop still safe
  8. Price drops to 5807.50 → stop triggers (locked in +7.50 point profit)
```

### **Scenario 3: Breakeven Then Trailing**
```
Setup:
  - Long 2 MNQ @ 21000.00
  - Breakeven: +10 ticks
  - Trailing: +20 ticks, distance 10 ticks

Timeline:
  1. Position opens at 21000.00
  2. Price rises to 21002.50 → +10 ticks
  3. Breakeven applied: Stop @ 21000.00
  4. Price rises to 21005.00 → +20 ticks
  5. Trailing activates: Stop @ 20002.50 (21005.00 - 10 ticks)
  6. Breakeven stop replaced by trailing stop
  7. Position now has trailing protection
```

### **Scenario 4: Short Position (Trailing Down)**
```
Setup:
  - Short 1 ES @ 5800.00
  - Trailing activation: +20 ticks
  - Trail distance: 10 ticks

Timeline:
  1. Position opens Short @ 5800.00
  2. Price drops to 5795.00 → +20 ticks profit (SHORT!)
  3. Trailing activates
  4. Low water mark: 5795.00
  5. Trailing stop set at: 5795.00 + (10 * 0.25) = 5797.50
  6. Price drops to 5790.00 → new low water mark
  7. Trailing stop updated to: 5790.00 + 2.50 = 5792.50
  8. Price rallies to 5792.50 → stop triggers (locked in profit)
```

### **Scenario 5: Existing Stop-Loss Modified**
```
Setup:
  - Long 1 MNQ @ 21000.00
  - Trader placed manual stop @ 20990.00
  - Breakeven trigger: +10 ticks

Timeline:
  1. Position opens with manual stop @ 20990.00
  2. Price rises to 21002.50 → +10 ticks
  3. Auto-breakeven detects existing stop
  4. Modifies existing stop from 20990.00 → 21000.00
  5. Stop improved from -$10 risk to breakeven
```

---

## 📊 State Tracking

**In-Memory State:**
```python
# Position tracking for auto-management
position_tracking = {
    456: {  # position_id
        'account_id': 123,
        'contract_id': 'CON.F.US.MNQ.U25',
        'entry_price': 21000.25,
        'position_type': 1,  # Long
        'size': 2,
        'stop_loss_order_id': 789,
        'breakeven_applied': True,
        'trailing_active': True,
        'high_water_mark': 21010.50,
        'low_water_mark': None
    }
}

# Stop-loss order tracking
stop_loss_orders = {
    789: {  # order_id
        'position_id': 456,
        'current_stop_price': 21005.00,
        'last_modified': datetime(2025, 1, 17, 14, 25, 0)
    }
}
```

**SQLite Persistence:**
```sql
CREATE TABLE auto_trade_management (
    position_id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    contract_id TEXT NOT NULL,
    entry_price REAL NOT NULL,
    position_type INTEGER NOT NULL,
    stop_loss_order_id BIGINT,
    breakeven_applied BOOLEAN DEFAULT 0,
    trailing_active BOOLEAN DEFAULT 0,
    high_water_mark REAL,
    low_water_mark REAL,
    created_at DATETIME NOT NULL,
    last_updated DATETIME
);

-- Track stop-loss modifications
CREATE TABLE stop_modifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER NOT NULL,
    order_id BIGINT NOT NULL,
    old_stop_price REAL,
    new_stop_price REAL,
    modification_type TEXT,  -- 'breakeven', 'trailing'
    timestamp DATETIME NOT NULL
);
```

---

## ⚠️ Edge Cases

### **Position Closes Before Stop Modified**
- Position might close (manually or via another rule)
- Check position still exists before modifying stop
- Remove from tracking when position closes

### **Order Modification Fails**
- API might reject modification (invalid price, etc.)
- Retry with adjusted price
- Log error but don't stop monitoring
- Continue trying on next price update

### **Multiple Stop Orders**
- Position might have multiple stop orders
- Track primary stop-loss order ID
- Modify only the tracked stop
- Ignore other stops (target orders, etc.)

### **Rapid Price Movements**
- Price might move multiple ticks in one update
- Calculate based on current price vs high/low water mark
- Don't trail more frequently than configured
- Rate-limit stop modifications (max 1/second)

### **Position Scaled In/Out**
- Position size changes after entry
- Update stop order size to match position
- Keep same stop price
- Recalculate on size changes

### **No Stop-Loss Order**
- Trader never placed stop
- Auto-management creates stop when triggered
- Track newly created order ID
- Continue managing position

### **Manual Stop Modification**
- Trader manually modifies stop during auto-management
- Respect trader's manual change
- Resume auto-management from new stop price
- Update tracking with manual stop price

### **Tick Size Different Per Contract**
- Each contract has different tick size
- Always fetch from contract cache
- Calculate ticks based on contract-specific tick size
- Don't assume standard tick sizes

---

## 🔧 Background Processing

**Position Cleanup (on position close):**
```python
def on_position_closed(position_event):
    """Remove position from tracking when closed."""

    position_id = position_event['id']

    if position_id in position_tracking:
        tracking = position_tracking[position_id]

        logger.info(
            f"Position {position_id} closed - "
            f"Breakeven: {tracking['breakeven_applied']}, "
            f"Trailing: {tracking['trailing_active']}"
        )

        # Remove from tracking
        del position_tracking[position_id]

        # Cancel stop-loss order if position closed manually
        if tracking['stop_loss_order_id']:
            # Stop order might already be cancelled/filled
            pass
```

**Quote Subscription Management:**
```python
def on_position_opened_for_management(position_event):
    """Subscribe to quotes for positions under management."""

    contract_id = position_event['contractId']

    # Subscribe to market quotes for this contract
    market_hub.subscribe_to_contract_quotes(contract_id)

def on_position_closed_for_management(position_event):
    """Unsubscribe when position closed."""

    contract_id = position_event['contractId']

    # Check if any other positions for this contract
    other_positions = [
        p for p in position_tracking.values()
        if p['contract_id'] == contract_id
    ]

    if not other_positions:
        # No more positions, unsubscribe
        market_hub.unsubscribe_from_contract_quotes(contract_id)
```

**Stop Modification Rate Limiting:**
```python
# Prevent excessive API calls
last_modification_time = {}

def should_modify_stop(order_id):
    """Rate limit stop modifications to max 1/second."""

    now = datetime.now()
    last_mod = last_modification_time.get(order_id)

    if last_mod and (now - last_mod).seconds < 1:
        return False  # Too soon, skip

    last_modification_time[order_id] = now
    return True
```

---

## 🔗 Dependencies

- **API-INT-001:** `GatewayUserPosition`, `GatewayQuote`, `GatewayUserOrder` events
- **src/api/market_hub.py:** Market Hub connection for quotes
- **src/api/quote_tracker.py:** Real-time price tracking
- **src/api/contract_cache.py:** Contract metadata cache
- **src/state/position_manager.py:** Position tracking
- **POST /api/Order/modify:** Modify stop-loss orders
- **POST /api/Order/place:** Create stop-loss orders
- **POST /api/Contract/searchById:** Get contract tick size

---

**This rule automates protective stop management - moving stops to breakeven and trailing profits without requiring manual intervention.**
