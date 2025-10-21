---
doc_id: RULE-011
version: 3.0
last_updated: 2025-10-21
dependencies: [MOD-001, MOD-002, API-INT-001]
enforcement_type: Hard Lockout (Symbol-Specific)
---

# RULE-011: SymbolBlocks

**Purpose:** Blacklist specific symbols - immediately close any position and permanently prevent trading in blocked instruments.

---

## ⚙️ Configuration

```yaml
symbol_blocks:
  enabled: true
  blocked_symbols:
    - "RTY"     # Russell 2000 - never trade
    - "BTC"     # Bitcoin futures - never trade
    - "CL"      # Crude Oil - too volatile
  enforcement: "close_and_lockout_symbol"
  allow_override: false  # Cannot be manually overridden
  match_mode: "symbol_root"  # Match by symbol root (RTY matches all RTY contracts)
```

---

## 🎯 Trigger Condition

**Primary Event:** `GatewayUserPosition` (when position opens or updates)

**Logic:**
```python
def on_position_opened(position_event):
    """Called when GatewayUserPosition event received."""

    account_id = position_event['accountId']
    contract_id = position_event['contractId']
    position_id = position_event['id']

    # Extract symbol root from contract ID
    # Example: "CON.F.US.RTY.H25" → "RTY"
    symbol_root = extract_symbol_root(contract_id)

    # Check if symbol is blocked
    if symbol_root in config['blocked_symbols']:
        logger.warning(
            f"RULE-011 BREACH: Position {position_id} opened in blocked symbol {symbol_root} - "
            f"Contract: {contract_id}"
        )
        return BREACH, symbol_root, contract_id

    return NO_BREACH

def extract_symbol_root(contract_id):
    """Extract symbol root from contract ID.

    Examples:
    - "CON.F.US.RTY.H25" → "RTY"
    - "CON.F.US.ES.U25" → "ES"
    - "CON.F.US.MNQ.M25" → "MNQ"
    - "CON.F.US.BTC.Z25" → "BTC"
    """

    # Contract ID format: CON.F.{region}.{symbol}.{expiry}
    parts = contract_id.split('.')

    if len(parts) >= 4:
        return parts[3]  # Symbol is 4th part (0-indexed: parts[3])

    # Fallback: return full contract ID if format unexpected
    logger.warning(f"Unexpected contract ID format: {contract_id}")
    return contract_id

# Alternative: Match by symbolId from GatewayUserOrder
def check_order_symbol(order_event):
    """Check if order is for blocked symbol."""

    symbol_id = order_event.get('symbolId')  # e.g., "F.US.RTY"

    if symbol_id:
        # Extract symbol root from symbolId
        # "F.US.RTY" → "RTY"
        symbol_root = symbol_id.split('.')[-1]

        if symbol_root in config['blocked_symbols']:
            return BREACH, symbol_root

    return NO_BREACH
```

---

## 🚨 Enforcement Action

**Type:** Hard Lockout (symbol-specific, permanent until configuration changed)

**Action Sequence:**
1. ✅ **Close position immediately** (via MOD-001)
2. ✅ **Cancel all orders for symbol** (via MOD-001)
3. ✅ **Set permanent symbol lockout** (via MOD-002)
4. ✅ **Log enforcement**
5. ✅ **Update Trader CLI** → Show blocked symbol message
6. ✅ **Monitor future fills** → Auto-close any new positions in blocked symbol

**Enforcement Code:**
```python
def enforce(account_id, symbol_root, contract_id):
    # Close the position immediately
    success = actions.close_position_by_contract(account_id, contract_id)

    if success:
        logger.log_enforcement(
            f"RULE-011: Closed position in blocked symbol {symbol_root} - "
            f"Contract: {contract_id}"
        )

    # Cancel any open orders for this symbol
    actions.cancel_orders_by_symbol(account_id, symbol_root)

    # Set permanent symbol-specific lockout
    lockout_manager.set_symbol_lockout(
        account_id=account_id,
        symbol=symbol_root,
        reason=f"Symbol {symbol_root} is permanently blocked",
        until=datetime.max  # Permanent lockout
    )

    # Log permanent block
    logger.log_enforcement(
        f"RULE-011: Permanent lockout for symbol {symbol_root} - "
        f"Account {account_id} cannot trade this instrument"
    )

    # CLI shows:
    # "🔴 BLOCKED SYMBOL - {symbol_root} is blacklisted - Position closed"

# Ongoing monitoring: Auto-close any new fills in blocked symbols
def monitor_for_blocked_symbols():
    """Background task - checks for new positions in blocked symbols."""

    for account_id in monitored_accounts:
        positions = state_manager.get_all_positions(account_id)

        for position in positions:
            contract_id = position['contractId']
            symbol_root = extract_symbol_root(contract_id)

            if symbol_root in config['blocked_symbols']:
                # Shouldn't happen (locked out), but enforce anyway
                logger.warning(
                    f"Detected position in blocked symbol {symbol_root} - "
                    f"Closing immediately"
                )
                enforce(account_id, symbol_root, contract_id)
```

---

## 📡 API Requirements

### **SignalR Events (Trigger):**

**GatewayUserPosition** (detects positions in blocked symbols):
```json
{
  "id": 456,
  "accountId": 123,
  "contractId": "CON.F.US.RTY.H25",
  "creationTimestamp": "2024-07-21T13:45:00Z",
  "type": 1,
  "size": 2,
  "averagePrice": 2100.25
}
```

**GatewayUserOrder** (detects orders in blocked symbols):
```json
{
  "id": 789,
  "accountId": 123,
  "contractId": "CON.F.US.RTY.H25",
  "symbolId": "F.US.RTY",
  "creationTimestamp": "2024-07-21T13:45:00Z",
  "status": 1,
  "type": 1,
  "side": 0,
  "size": 1
}
```

**Key Fields:**
- `contractId`: Full contract identifier (parse to extract symbol)
- `symbolId`: Symbol ID (easier to parse for symbol matching)

### **REST API Calls:**

**Close Position** (enforcement):
```http
POST /api/Position/closeContract
Authorization: Bearer {jwt_token}
{
  "accountId": 123,
  "contractId": "CON.F.US.RTY.H25"
}

Response:
{
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

**Cancel Orders by Symbol** (enforcement):
```http
POST /api/Order/searchOpen
{
  "accountId": 123
}

Response:
{
  "orders": [
    {
      "id": 789,
      "contractId": "CON.F.US.RTY.H25",
      "symbolId": "F.US.RTY",
      ...
    }
  ]
}

// For each matching order:
POST /api/Order/cancel
{
  "accountId": 123,
  "orderId": 789
}
```

**Search Positions** (verification):
```http
POST /api/Position/searchOpen
{
  "accountId": 123
}

Response:
{
  "positions": [
    {
      "id": 456,
      "accountId": 123,
      "contractId": "CON.F.US.RTY.H25",
      ...
    }
  ]
}
```

---

## 🧪 Test Scenarios

### **Scenario 1: Position Opens in Blocked Symbol**
```
Setup:
  - Blocked symbols: ["RTY", "BTC"]
  - Trader attempts to trade RTY

Timeline:
  1. Order placed: Buy 1 RTY @ market
  2. Order fills
  3. GatewayUserPosition event: contractId="CON.F.US.RTY.H25"
  4. Rule extracts symbol: "RTY"
  5. Matches blocked list → BREACH
  6. Position closed immediately
  7. Symbol lockout set (permanent)
  8. CLI shows: "🔴 BLOCKED SYMBOL - RTY is blacklisted - Position closed"
  9. Future RTY orders rejected by lockout system
```

### **Scenario 2: Multiple Contracts, Same Symbol**
```
Setup:
  - Blocked symbols: ["RTY"]
  - Trader has RTY positions in different expiry months

Positions:
  - CON.F.US.RTY.H25 (March 2025)
  - CON.F.US.RTY.M25 (June 2025)

Result:
  - Both positions closed (same symbol root)
  - Both contracts match "RTY" block
  - Symbol-level lockout prevents all RTY contracts
```

### **Scenario 3: Similar But Different Symbols**
```
Setup:
  - Blocked symbols: ["ES"]
  - Trader opens MES (Micro ES) position

Timeline:
  1. Position opens: CON.F.US.MES.H25
  2. Symbol extracted: "MES"
  3. "MES" ≠ "ES" → NO BREACH
  4. Position allowed (different symbol)
  5. Must explicitly block "MES" if unwanted
```

### **Scenario 4: Symbol Added to Block List Mid-Session**
```
Timeline:
  1. Trader has open ES position
  2. Admin adds "ES" to blocked_symbols config
  3. Config reloaded
  4. Background monitor detects ES position
  5. Rule triggers → BREACH
  6. ES position closed
  7. Symbol lockout applied
```

### **Scenario 5: Prevented Order (Lockout Working)**
```
Setup:
  - RTY already locked out from previous breach

Timeline:
  1. Trader attempts to place RTY order via API
  2. Pre-order check detects RTY lockout
  3. Order rejected before placement
  4. CLI shows: "🔴 Cannot trade RTY - Symbol is blocked"
  5. Order never reaches exchange
```

---

## 📊 State Tracking

**In-Memory State:**
```python
# Symbol-specific lockouts
symbol_lockouts = {
    123: {  # account_id
        'RTY': {
            'reason': 'Symbol RTY is permanently blocked',
            'locked_at': datetime(2025, 1, 17, 14, 30, 0),
            'until': datetime.max  # Permanent
        },
        'BTC': {
            'reason': 'Symbol BTC is permanently blocked',
            'locked_at': datetime(2025, 1, 17, 15, 0, 0),
            'until': datetime.max
        }
    }
}

# Blocked symbols list (from config)
blocked_symbols = ['RTY', 'BTC', 'CL']
```

**SQLite Persistence:**
```sql
CREATE TABLE symbol_lockouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    contract_id TEXT,
    reason TEXT,
    locked_at DATETIME NOT NULL,
    until DATETIME,
    removed_at DATETIME,
    UNIQUE(account_id, symbol)
);

-- Track all symbol blocks
CREATE INDEX idx_symbol_lockouts_account
ON symbol_lockouts(account_id, locked_at DESC);

-- Track blocked position closures
CREATE TABLE blocked_position_closures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    position_id INTEGER,
    contract_id TEXT,
    symbol TEXT,
    closed_at DATETIME NOT NULL,
    reason TEXT
);
```

---

## ⚠️ Edge Cases

### **Contract ID Parsing Failure**
- If contract ID format is unexpected
- Fallback: use full contract ID as symbol
- Log warning about unexpected format
- Still attempt to match against blocked list

### **Null/Missing symbolId**
- GatewayUserOrder might not have `symbolId`
- Use `contractId` parsing as backup
- Extract symbol from contract ID

### **Case Sensitivity**
- Symbol matching is case-insensitive
- "RTY" == "rty" == "Rty"
- Normalize to uppercase for comparison

### **Partial Symbol Matches**
- Don't use partial matches (e.g., "ES" shouldn't match "MES")
- Exact symbol root match only
- Avoid false positives

### **Position Already Closed**
- Position might close before enforcement executes
- Check if position still exists before closing
- Don't error if already closed

### **Multiple Positions Same Symbol**
- Close all positions for blocked symbol
- Iterate through all open positions
- Apply lockout once per symbol (not per position)

### **Symbol Removed from Block List**
- When symbol removed from config
- Remove corresponding symbol lockouts
- Allow trading in that symbol again
- Log configuration change

### **Different Exchanges**
- "RTY" on CME vs "RTY" on different exchange
- Contract ID includes region: CON.F.US.RTY vs CON.F.EU.RTY
- Current logic blocks all RTY regardless of region
- Can extend to region-specific blocks if needed

---

## 🔧 Background Processing

**Position Monitor (runs every 10 seconds):**
```python
def monitor_blocked_symbol_positions():
    """Check for any positions in blocked symbols."""

    for account_id in monitored_accounts:
        positions = state_manager.get_all_positions(account_id)

        for position in positions:
            contract_id = position['contractId']
            symbol_root = extract_symbol_root(contract_id)

            if symbol_root in config['blocked_symbols']:
                # Position exists in blocked symbol - enforce
                logger.warning(
                    f"Detected position in blocked symbol {symbol_root} - "
                    f"Account: {account_id}, Contract: {contract_id}"
                )
                enforce(account_id, symbol_root, contract_id)
```

**Pre-Order Validation (before order placement):**
```python
def validate_order_symbol(account_id, contract_id):
    """Validate symbol before allowing order placement."""

    symbol_root = extract_symbol_root(contract_id)

    # Check symbol lockouts
    if lockout_manager.is_symbol_locked(account_id, symbol_root):
        raise BlockedSymbolError(
            f"Symbol {symbol_root} is blocked for account {account_id}"
        )

    # Check global blocked symbols
    if symbol_root in config['blocked_symbols']:
        raise BlockedSymbolError(
            f"Symbol {symbol_root} is globally blocked"
        )

    return True  # Order can proceed
```

**Config Change Sync:**
```python
def on_config_reload():
    """Handle changes to blocked_symbols configuration."""

    new_blocked = set(config['blocked_symbols'])
    old_blocked = set(previous_config['blocked_symbols'])

    # Symbols newly added to block list
    newly_blocked = new_blocked - old_blocked

    # Symbols removed from block list
    newly_unblocked = old_blocked - new_blocked

    # Enforce lockouts for newly blocked symbols
    for symbol in newly_blocked:
        logger.info(f"Symbol {symbol} added to block list - checking positions")

        for account_id in monitored_accounts:
            positions = state_manager.get_positions_by_symbol(account_id, symbol)

            for position in positions:
                enforce(account_id, symbol, position['contractId'])

    # Remove lockouts for newly unblocked symbols
    for symbol in newly_unblocked:
        logger.info(f"Symbol {symbol} removed from block list - removing lockouts")

        for account_id in monitored_accounts:
            lockout_manager.remove_symbol_lockout(account_id, symbol)
```

---

## 🔗 Dependencies

- **MOD-001:** `close_position_by_contract()`, `cancel_orders_by_symbol()`
- **MOD-002:** `set_symbol_lockout()`, `remove_symbol_lockout()`, `is_symbol_locked()`
- **API-INT-001:** `GatewayUserPosition`, `GatewayUserOrder` events
- **src/state/position_manager.py:** Position tracking
- **src/state/lockout_manager.py:** Symbol-specific lockout management
- **src/utils/symbol_parser.py:** Contract ID parsing utilities
- **POST /api/Position/closeContract:** Close position (enforcement)
- **POST /api/Order/cancel:** Cancel orders (enforcement)
- **POST /api/Position/searchOpen:** Get positions (monitoring)
- **POST /api/Order/searchOpen:** Get orders (monitoring)

---

**This rule prevents trading in instruments where the trader historically loses or wants to avoid - "never let me trade RTY again."**
