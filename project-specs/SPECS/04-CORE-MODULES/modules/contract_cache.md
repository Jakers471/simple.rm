---
doc_id: MOD-007
version: 1.0
last_updated: 2025-10-21
dependencies: [API-INT-001]
---

# MOD-007: Contract Cache

**Purpose:** Contract metadata caching (tick values, tick sizes) - all rules call these functions.

**File:** `src/api/contract_cache.py`

---

## 🎯 Core Principle

**All contract metadata cached in one place. Rules never directly call `/api/Contract/searchById`.**

This ensures:
- **Performance:** Fetch once, use many times
- **Consistency:** All rules use same contract metadata
- **Reduced API calls:** Cache prevents repeated requests
- **Offline capability:** Cached data survives API outages

---

## 🔧 Public API

### **1. get_contract(contract_id)**
**Purpose:** Get contract metadata (fetches from API if not cached).

**Implementation:**
```python
def get_contract(contract_id: str) -> dict:
    """
    Get contract metadata.

    Fetches from cache, or calls API if not cached.

    Args:
        contract_id: Contract ID (e.g., "CON.F.US.MNQ.U25")

    Returns:
        {
            'id': 'CON.F.US.MNQ.U25',
            'tickSize': 0.25,
            'tickValue': 0.5,
            'symbolId': 'F.US.MNQ',
            'name': 'MNQU5'
        }
    """
    if contract_id in cache:
        return cache[contract_id]

    # Not in cache - fetch from API
    response = rest_client.post(
        "/api/Contract/searchById",
        json={"contractId": contract_id}
    )

    contract_data = response.json()['contract']

    # Cache it
    cache_contract(contract_id, contract_data)

    return contract_data
```

**Used By:** MOD-005 (PNL Tracker), RULE-004, RULE-005, RULE-012

---

### **2. cache_contract(contract_id, contract_data)**
**Purpose:** Store contract in cache.

**Implementation:**
```python
def cache_contract(contract_id: str, contract_data: dict) -> None:
    """Store contract metadata in cache."""
    cache[contract_id] = {
        'id': contract_data['id'],
        'tickSize': contract_data['tickSize'],
        'tickValue': contract_data['tickValue'],
        'symbolId': contract_data['symbolId'],
        'name': contract_data.get('name', '')
    }
```

---

### **3. get_tick_value(contract_id)**
**Purpose:** Get tick value for contract.

**Implementation:**
```python
def get_tick_value(contract_id: str) -> float:
    """Get tick value (shortcut for get_contract()['tickValue'])."""
    return get_contract(contract_id)['tickValue']
```

---

### **4. get_tick_size(contract_id)**
**Purpose:** Get tick size for contract.

**Implementation:**
```python
def get_tick_size(contract_id: str) -> float:
    """Get tick size (shortcut for get_contract()['tickSize'])."""
    return get_contract(contract_id)['tickSize']
```

---

## 📊 State Management

**In-Memory Cache:**
```python
cache = {
    'CON.F.US.MNQ.U25': {
        'id': 'CON.F.US.MNQ.U25',
        'tickSize': 0.25,
        'tickValue': 0.5,
        'symbolId': 'F.US.MNQ',
        'name': 'MNQU5'
    },
    'CON.F.US.ES.U25': {
        'id': 'CON.F.US.ES.U25',
        'tickSize': 0.25,
        'tickValue': 12.5,
        'symbolId': 'F.US.ES',
        'name': 'ESU5'
    }
}
```

**Optional SQLite persistence** (to survive daemon restarts):
```sql
CREATE TABLE contract_cache (
    contract_id TEXT PRIMARY KEY,
    tick_size REAL,
    tick_value REAL,
    symbol_id TEXT,
    name TEXT,
    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔗 Dependencies

- **REST API:** `POST /api/Contract/searchById`
- **rest_client.py:** API wrapper

---

**Used By:** MOD-005, RULE-004, RULE-005, RULE-012
