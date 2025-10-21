---
doc_id: MOD-006
version: 1.0
last_updated: 2025-10-21
dependencies: [API-INT-001]
---

# MOD-006: Quote Tracker

**Purpose:** Real-time price tracking from Market Hub - all rules call these functions.

**File:** `src/api/quote_tracker.py`

---

## 🎯 Core Principle

**All quote data managed in one place. Rules never directly handle GatewayQuote events.**

This ensures:
- **Single source of truth:** One place for current prices
- **Consistency:** All rules use same price data
- **Stale data handling:** Centralized quote age checking
- **Performance:** In-memory cache for fast lookups

---

## 🔧 Public API

### **1. get_last_price(contract_id)**
**Purpose:** Get most recent price for contract.

**Implementation:**
```python
def get_last_price(contract_id: str) -> float | None:
    """
    Get most recent price for contract.

    Args:
        contract_id: Contract ID (e.g., "CON.F.US.MNQ.U25")

    Returns:
        Last price, or None if no quote available
    """
    if contract_id not in quotes:
        return None

    return quotes[contract_id]['lastPrice']
```

**Used By:** MOD-005 (PNL Tracker), RULE-004, RULE-005, RULE-012

---

### **2. update_quote(contract_id, quote_data)**
**Purpose:** Update quote from GatewayQuote event.

**Implementation:**
```python
def update_quote(contract_id: str, quote_data: dict) -> None:
    """
    Update quote from GatewayQuote event.

    Args:
        contract_id: Contract ID
        quote_data: GatewayQuote event payload

    Example quote_data:
    {
      "symbol": "F.US.MNQ",
      "lastPrice": 20950.00,
      "bestBid": 20949.75,
      "bestAsk": 20950.25,
      "timestamp": "2024-07-21T13:45:00Z"
    }
    """
    quotes[contract_id] = {
        'lastPrice': quote_data['lastPrice'],
        'bestBid': quote_data['bestBid'],
        'bestAsk': quote_data['bestAsk'],
        'timestamp': datetime.fromisoformat(quote_data['timestamp'].replace('Z', '+00:00')),
        'lastUpdated': datetime.now()
    }
```

**Used By:** `src/api/market_hub.py` (calls this on every GatewayQuote event)

---

### **3. is_quote_stale(contract_id, max_age_seconds)**
**Purpose:** Check if quote is too old.

**Implementation:**
```python
def is_quote_stale(contract_id: str, max_age_seconds: int = 10) -> bool:
    """
    Check if quote is stale (too old).

    Args:
        contract_id: Contract ID
        max_age_seconds: Maximum acceptable age (default 10s)

    Returns:
        True if quote is stale or missing
    """
    if contract_id not in quotes:
        return True

    age = (datetime.now() - quotes[contract_id]['lastUpdated']).total_seconds()
    return age > max_age_seconds
```

**Used By:** RULE-004, RULE-005 (to warn about stale data)

---

### **4. get_quote_age(contract_id)**
**Purpose:** Get seconds since last update.

**Implementation:**
```python
def get_quote_age(contract_id: str) -> float | None:
    """Get age of quote in seconds."""
    if contract_id not in quotes:
        return None

    return (datetime.now() - quotes[contract_id]['lastUpdated']).total_seconds()
```

---

## 📊 State Management

**In-Memory State:**
```python
quotes = {
    'CON.F.US.MNQ.U25': {
        'lastPrice': 20950.00,
        'bestBid': 20949.75,
        'bestAsk': 20950.25,
        'timestamp': datetime(2024, 7, 21, 13, 45, 0),
        'lastUpdated': datetime(2024, 7, 21, 13, 45, 1)
    }
}
```

**No SQLite persistence** - quotes are real-time only, not persisted.

---

## 🔗 Dependencies

- **API-INT-001:** GatewayQuote event payload
- **market_hub.py:** Calls `update_quote()` on events

---

**Used By:** MOD-005, RULE-004, RULE-005, RULE-012
