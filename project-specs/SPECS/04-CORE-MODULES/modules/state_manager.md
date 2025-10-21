---
doc_id: MOD-009
version: 1.0
last_updated: 2025-10-21
dependencies: [API-INT-001]
---

# MOD-009: State Manager

**Purpose:** Centralized position and order state tracking - all rules call these functions.

**File:** `src/state/state_manager.py`

---

## 🎯 Core Principle

**All position and order state in one place. Rules never directly handle state events.**

This ensures:
- **Single source of truth:** One place for current positions/orders
- **Consistency:** All rules see same state data
- **Automatic updates:** SignalR events update state automatically
- **Query efficiency:** Fast in-memory lookups

---

## 🔧 Public API

### **Position Management**

#### **1. update_position(position_event)**
**Purpose:** Update position from GatewayUserPosition event.

**Implementation:**
```python
def update_position(position_event: dict) -> None:
    """
    Update position from GatewayUserPosition event.

    Args:
        position_event: GatewayUserPosition payload from SignalR
    """
    account_id = position_event['accountId']
    position_id = position_event['id']

    if account_id not in positions:
        positions[account_id] = {}

    if position_event['size'] == 0:
        # Position closed
        if position_id in positions[account_id]:
            del positions[account_id][position_id]
    else:
        # Position opened or updated
        positions[account_id][position_id] = {
            'id': position_id,
            'contractId': position_event['contractId'],
            'type': position_event['type'],  # 1=Long, 2=Short
            'size': position_event['size'],
            'averagePrice': position_event['averagePrice'],
            'creationTimestamp': position_event['creationTimestamp']
        }

    # Persist to SQLite
    if position_event['size'] == 0:
        db.execute("DELETE FROM positions WHERE id = ?", (position_id,))
    else:
        db.execute("""
            INSERT OR REPLACE INTO positions
            (id, account_id, contract_id, type, size, average_price, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            position_id,
            account_id,
            position_event['contractId'],
            position_event['type'],
            position_event['size'],
            position_event['averagePrice'],
            position_event['creationTimestamp']
        ))
```

**Used By:** `src/api/user_hub.py` (calls on every GatewayUserPosition event)

---

#### **2. get_all_positions(account_id)**
**Purpose:** Get all open positions for account.

**Implementation:**
```python
def get_all_positions(account_id: int) -> list:
    """
    Get all open positions for account.

    Args:
        account_id: TopstepX account ID

    Returns:
        List of position dicts
    """
    return list(positions.get(account_id, {}).values())
```

**Used By:** MOD-005, RULE-001, RULE-002, RULE-004, RULE-005, RULE-009, RULE-011

---

#### **3. get_position_count(account_id)**
**Purpose:** Get total contract count across all positions.

**Implementation:**
```python
def get_position_count(account_id: int) -> int:
    """Get total contract count (sum of position sizes)."""
    positions_list = get_all_positions(account_id)
    return sum(p['size'] for p in positions_list)
```

**Used By:** RULE-001 (MaxContracts)

---

#### **4. get_positions_by_contract(account_id, contract_id)**
**Purpose:** Get positions for specific contract.

**Implementation:**
```python
def get_positions_by_contract(account_id: int, contract_id: str) -> list:
    """Get positions for specific contract."""
    all_positions = get_all_positions(account_id)
    return [p for p in all_positions if p['contractId'] == contract_id]
```

**Used By:** RULE-002 (MaxContractsPerInstrument)

---

#### **5. get_contract_count(account_id, contract_id)**
**Purpose:** Get contract count for specific instrument.

**Implementation:**
```python
def get_contract_count(account_id: int, contract_id: str) -> int:
    """Get total contracts for specific instrument."""
    instrument_positions = get_positions_by_contract(account_id, contract_id)
    return sum(p['size'] for p in instrument_positions)
```

**Used By:** RULE-002

---

### **Order Management**

#### **6. update_order(order_event)**
**Purpose:** Update order from GatewayUserOrder event.

**Implementation:**
```python
def update_order(order_event: dict) -> None:
    """
    Update order from GatewayUserOrder event.

    Args:
        order_event: GatewayUserOrder payload from SignalR
    """
    account_id = order_event['accountId']
    order_id = order_event['id']

    if account_id not in orders:
        orders[account_id] = {}

    # Order states:
    # 1 = Pending, 2 = Working, 3 = Filled, 4 = Cancelled, 5 = Rejected
    if order_event['state'] in [3, 4, 5]:
        # Order completed/cancelled/rejected - remove
        if order_id in orders[account_id]:
            del orders[account_id][order_id]
    else:
        # Order pending or working
        orders[account_id][order_id] = {
            'id': order_id,
            'accountId': account_id,
            'contractId': order_event['contractId'],
            'type': order_event['type'],
            'side': order_event['side'],
            'size': order_event['size'],
            'limitPrice': order_event.get('limitPrice'),
            'stopPrice': order_event.get('stopPrice'),
            'state': order_event['state'],
            'creationTimestamp': order_event['creationTimestamp']
        }

    # Persist to SQLite
    if order_event['state'] in [3, 4, 5]:
        db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    else:
        db.execute("""
            INSERT OR REPLACE INTO orders
            (id, account_id, contract_id, type, side, size, limit_price, stop_price, state, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            account_id,
            order_event['contractId'],
            order_event['type'],
            order_event['side'],
            order_event['size'],
            order_event.get('limitPrice'),
            order_event.get('stopPrice'),
            order_event['state'],
            order_event['creationTimestamp']
        ))
```

**Used By:** `src/api/user_hub.py` (calls on every GatewayUserOrder event)

---

#### **7. get_all_orders(account_id)**
**Purpose:** Get all working orders for account.

**Implementation:**
```python
def get_all_orders(account_id: int) -> list:
    """Get all working orders for account."""
    return list(orders.get(account_id, {}).values())
```

**Used By:** RULE-008, RULE-012

---

#### **8. get_orders_for_position(account_id, contract_id)**
**Purpose:** Get orders for specific position/contract.

**Implementation:**
```python
def get_orders_for_position(account_id: int, contract_id: str) -> list:
    """Get orders for specific contract."""
    all_orders = get_all_orders(account_id)
    return [o for o in all_orders if o['contractId'] == contract_id]
```

**Used By:** RULE-008 (NoStopLossGrace), RULE-012 (TradeManagement)

---

## 📊 State Management

**In-Memory State:**
```python
# Positions by account
positions = {
    123: {  # account_id
        456: {  # position_id
            'id': 456,
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 1,  # Long
            'size': 2,
            'averagePrice': 21000.25,
            'creationTimestamp': '2024-07-21T13:45:00Z'
        }
    }
}

# Orders by account
orders = {
    123: {  # account_id
        789: {  # order_id
            'id': 789,
            'accountId': 123,
            'contractId': 'CON.F.US.MNQ.U25',
            'type': 4,  # Stop
            'side': 1,  # Sell
            'size': 2,
            'limitPrice': None,
            'stopPrice': 20950.00,
            'state': 2,  # Working
            'creationTimestamp': '2024-07-21T13:46:00Z'
        }
    }
}
```

**SQLite Persistence:**
```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    account_id INTEGER,
    contract_id TEXT,
    type INTEGER,
    size INTEGER,
    average_price REAL,
    created_at DATETIME
);

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

## 🔗 Dependencies

- **API-INT-001:** GatewayUserPosition, GatewayUserOrder events
- **user_hub.py:** Calls `update_position()` and `update_order()` on events
- **persistence.py:** SQLite operations

---

**Used By:** MOD-005, RULE-001, RULE-002, RULE-004, RULE-005, RULE-008, RULE-009, RULE-011, RULE-012
