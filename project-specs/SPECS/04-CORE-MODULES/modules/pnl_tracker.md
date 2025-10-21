---
doc_id: MOD-005
version: 1.0
last_updated: 2025-10-21
dependencies: [API-INT-001]
---

# MOD-005: PNL Tracker

**Purpose:** Centralized P&L calculation and tracking - all rules call these functions.

**File:** `src/state/pnl_tracker.py`

---

## 🎯 Core Principle

**All P&L tracking logic in one place. Rules call MOD-005, never calculate P&L themselves.**

This ensures:
- **No duplication:** P&L calculation written once
- **Consistency:** All rules calculate P&L the same way
- **Accuracy:** Single source of truth for P&L data
- **Testability:** Easy to test P&L calculations in isolation

---

## 🔧 Public API

### **1. add_trade_pnl(account_id, pnl)**
**Purpose:** Add realized P&L from a trade, return daily total.

**Implementation:**
```python
def add_trade_pnl(account_id: int, pnl: float) -> float:
    """
    Add realized P&L from trade to daily total.

    Args:
        account_id: TopstepX account ID
        pnl: Realized P&L from trade (can be positive or negative)

    Returns:
        Current daily realized P&L total
    """
    # Get current daily total
    if account_id not in daily_pnl:
        daily_pnl[account_id] = 0.0

    # Add this trade's P&L
    daily_pnl[account_id] += pnl

    # Persist to SQLite
    db.execute(
        "UPDATE daily_pnl SET realized_pnl = ? WHERE account_id = ? AND date = CURRENT_DATE",
        (daily_pnl[account_id], account_id)
    )

    return daily_pnl[account_id]
```

**Used By:** RULE-003 (DailyRealizedLoss), RULE-007 (CooldownAfterLoss)

---

### **2. get_daily_realized_pnl(account_id)**
**Purpose:** Get current daily realized P&L.

**Implementation:**
```python
def get_daily_realized_pnl(account_id: int) -> float:
    """Get current daily realized P&L total."""
    return daily_pnl.get(account_id, 0.0)
```

**Used By:** RULE-003, RULE-007

---

### **3. calculate_unrealized_pnl(account_id)**
**Purpose:** Calculate total unrealized P&L for all open positions.

**Implementation:**
```python
def calculate_unrealized_pnl(account_id: int) -> float:
    """
    Calculate unrealized P&L for all open positions.

    Uses:
    - state_manager.get_all_positions() for positions
    - quote_tracker.get_last_price() for current prices
    - contract_cache.get_contract() for tick values

    Returns:
        Total unrealized P&L across all positions
    """
    from .state_manager import get_all_positions
    from ..api.quote_tracker import get_last_price
    from ..api.contract_cache import get_contract

    positions = get_all_positions(account_id)

    if not positions:
        return 0.0

    total_unrealized = 0.0

    for position in positions:
        contract_id = position['contractId']
        position_type = position['type']  # 1=Long, 2=Short
        size = position['size']
        entry_price = position['averagePrice']

        # Get current price
        current_price = get_last_price(contract_id)
        if current_price is None:
            continue

        # Get contract metadata
        contract = get_contract(contract_id)
        tick_value = contract['tickValue']
        tick_size = contract['tickSize']

        # Calculate P&L
        price_diff = current_price - entry_price
        ticks_moved = price_diff / tick_size

        if position_type == 1:  # Long
            position_pnl = ticks_moved * tick_value * size
        elif position_type == 2:  # Short
            position_pnl = -ticks_moved * tick_value * size
        else:
            continue

        total_unrealized += position_pnl

    return total_unrealized
```

**Used By:** RULE-004 (DailyUnrealizedLoss), RULE-005 (MaxUnrealizedProfit)

---

### **4. reset_daily_pnl(account_id)**
**Purpose:** Reset daily P&L counters (called at reset time).

**Implementation:**
```python
def reset_daily_pnl(account_id: int) -> None:
    """Reset daily P&L counters."""
    daily_pnl[account_id] = 0.0

    # Archive old data, start fresh
    db.execute(
        "INSERT INTO daily_pnl (account_id, realized_pnl, date) VALUES (?, 0.0, CURRENT_DATE)",
        (account_id,)
    )
```

**Used By:** MOD-004 (Reset Scheduler)

---

## 📊 State Management

**In-Memory State:**
```python
# Current daily P&L totals
daily_pnl = {
    123: -150.50,  # account_id: realized_pnl
    456: 200.00
}
```

**SQLite Persistence:**
```sql
CREATE TABLE daily_pnl (
    account_id INTEGER,
    realized_pnl REAL DEFAULT 0.0,
    unrealized_pnl REAL DEFAULT 0.0,
    date DATE DEFAULT CURRENT_DATE,
    PRIMARY KEY (account_id, date)
);
```

---

## 🔗 Dependencies

- **state_manager.py:** `get_all_positions()`
- **quote_tracker.py:** `get_last_price()`
- **contract_cache.py:** `get_contract()`
- **persistence.py:** SQLite operations

---

**Used By:** RULE-003, RULE-004, RULE-005, RULE-007, MOD-004
