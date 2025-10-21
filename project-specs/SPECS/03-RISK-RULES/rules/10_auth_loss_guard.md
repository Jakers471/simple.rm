---
doc_id: RULE-010
version: 3.0
last_updated: 2025-10-21
dependencies: [MOD-001, MOD-002, API-INT-001]
enforcement_type: Hard Lockout (API-Driven)
---

# RULE-010: AuthLossGuard

**Purpose:** Monitor TopstepX `canTrade` status and enforce lockout when API signals account is restricted - ensures compliance with platform-level restrictions.

---

## ⚙️ Configuration

```yaml
auth_loss_guard:
  enabled: true
  enforcement: "close_all_and_lockout"
  auto_unlock_on_restore: true  # Auto-unlock when canTrade becomes true again
  check_on_startup: true         # Verify canTrade status on daemon startup
```

---

## 🎯 Trigger Condition

**Primary Event:** `GatewayUserAccount`

**Logic:**
```python
def on_account_update(account_event):
    """Called when GatewayUserAccount event received."""

    account_id = account_event['id']
    can_trade = account_event['canTrade']
    previous_state = state_manager.get_can_trade_status(account_id)

    # Store current state
    state_manager.set_can_trade_status(account_id, can_trade)

    # Check for canTrade status change
    if previous_state is True and can_trade is False:
        # Account was tradeable, now restricted
        logger.warning(
            f"Account {account_id} canTrade changed: True → False - "
            f"TopstepX has restricted trading"
        )
        return BREACH, "canTrade_disabled"

    elif previous_state is False and can_trade is True:
        # Account was restricted, now restored
        logger.info(
            f"Account {account_id} canTrade changed: False → True - "
            f"TopstepX has restored trading privileges"
        )
        return RESTORE, "canTrade_enabled"

    elif can_trade is False:
        # Account remains restricted (no change, but still locked)
        return BREACH, "canTrade_disabled"

    # can_trade is True - all good
    return NO_BREACH

# Initial state check (on startup)
def check_initial_state(account_id):
    """Verify canTrade status on daemon startup."""

    account = api.get_account_info(account_id)
    can_trade = account['canTrade']

    if not can_trade:
        logger.warning(
            f"Account {account_id} has canTrade=false on startup - "
            f"Applying lockout"
        )
        return BREACH, "canTrade_disabled"

    return NO_BREACH
```

---

## 🚨 Enforcement Action

**Type:** Hard Lockout (trader CANNOT trade - no expiry time)

**Action Sequence (on canTrade = false):**
1. ✅ **Close all positions** (via MOD-001)
2. ✅ **Cancel all orders** (via MOD-001)
3. ✅ **Set lockout** (via MOD-002) - no expiry time (indefinite)
4. ✅ **Log enforcement**
5. ✅ **Update Trader CLI** → Show lockout message

**Auto-Unlock (on canTrade = true):**
1. ✅ **Remove lockout** (via MOD-002)
2. ✅ **Log restoration**
3. ✅ **Update Trader CLI** → "Trading enabled"

**Enforcement Code:**
```python
def enforce(account_id, event_type):
    if event_type == "canTrade_disabled":
        # Close all open positions and orders
        actions.close_all_positions(account_id)
        actions.cancel_all_orders(account_id)

        # Set indefinite lockout (no until time)
        lockout_manager.set_lockout(
            account_id=account_id,
            reason="Account restricted by TopstepX (canTrade=false)",
            until=None  # Indefinite - only unlocks when canTrade=true
        )

        # Log enforcement
        logger.log_enforcement(
            f"RULE-010: Account {account_id} restricted - "
            f"canTrade=false detected - All positions closed, indefinite lockout"
        )

        # CLI shows: "🔴 ACCOUNT RESTRICTED - Contact TopstepX support"

    elif event_type == "canTrade_enabled":
        # Remove lockout automatically
        lockout_manager.remove_lockout(
            account_id=account_id,
            reason="TopstepX restored trading (canTrade=true)"
        )

        # Log restoration
        logger.log_enforcement(
            f"RULE-010: Account {account_id} restored - "
            f"canTrade=true detected - Lockout removed"
        )

        # CLI shows: "🟢 TRADING ENABLED - Account restrictions lifted"
```

---

## 📡 API Requirements

### **SignalR Events (Trigger):**

**GatewayUserAccount** (monitors account status):
```json
{
  "id": 123,
  "name": "Main Trading Account",
  "balance": 10000.50,
  "canTrade": false,
  "isVisible": true,
  "simulated": false
}
```

**Key Fields:**
- `canTrade`: Boolean - Whether account is eligible for trading
- `id`: Account ID
- `balance`: Current account balance (informational)
- `simulated`: Whether account is simulated or live

**Typical Trigger Events:**

Account Restricted:
```json
{
  "id": 123,
  "canTrade": false  // Trading disabled by TopstepX
}
```

Account Restored:
```json
{
  "id": 123,
  "canTrade": true   // Trading re-enabled by TopstepX
}
```

### **REST API Calls:**

**Get Account Info** (initial state check on startup):
```http
POST /api/Account/search
Authorization: Bearer {jwt_token}
{
  "onlyActiveAccounts": true
}

Response:
{
  "accounts": [
    {
      "id": 123,
      "name": "TEST_ACCOUNT_1",
      "balance": 50000,
      "canTrade": true,
      "isVisible": true
    }
  ],
  "success": true
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

### **Scenario 1: Account Restricted (Basic Flow)**
```
Setup:
  - Account starts with canTrade=true
  - Trader has 2 open positions

Timeline:
  1. t=0: Account operating normally, canTrade=true
  2. t=60s: TopstepX restricts account (rule violation, margin call, etc.)
  3. GatewayUserAccount event: canTrade=false
  4. Rule triggers → BREACH
  5. All positions closed immediately
  6. All orders cancelled
  7. Lockout set (indefinite)
  8. CLI shows: "🔴 ACCOUNT RESTRICTED - Contact TopstepX support"
  9. Trader cannot place orders until canTrade=true
```

### **Scenario 2: Account Restored**
```
Setup:
  - Account locked due to canTrade=false
  - Trader resolved issue with TopstepX support

Timeline:
  1. Account locked, canTrade=false
  2. Trader contacts TopstepX support
  3. TopstepX restores account
  4. GatewayUserAccount event: canTrade=true
  5. Rule triggers → RESTORE
  6. Lockout removed automatically
  7. CLI shows: "🟢 TRADING ENABLED - Account restrictions lifted"
  8. Trader can resume trading
```

### **Scenario 3: Daemon Starts with Restricted Account**
```
Setup:
  - Daemon starts
  - Account has canTrade=false from previous session

Timeline:
  1. Daemon startup
  2. Initial state check via POST /api/Account/search
  3. Account has canTrade=false
  4. Rule triggers → BREACH
  5. Lockout applied on startup
  6. CLI shows restriction message immediately
  7. Trader sees lockout before attempting any trades
```

### **Scenario 4: No Position to Close**
```
Setup:
  - Account has canTrade=true, no open positions
  - TopstepX restricts account

Timeline:
  1. GatewayUserAccount event: canTrade=false
  2. Rule triggers → BREACH
  3. No positions to close (skip position closing)
  4. No orders to cancel (skip order cancelling)
  5. Lockout still applied
  6. Same enforcement, just no cleanup needed
```

### **Scenario 5: Rapid Toggle (Edge Case)**
```
Timeline:
  1. canTrade=false → Lockout applied
  2. 5 seconds later: canTrade=true → Lockout removed
  3. 10 seconds later: canTrade=false → Lockout re-applied
  4. Each state change is independent
  5. Always reflects current canTrade status
```

---

## 📊 State Tracking

**In-Memory State:**
```python
# Current canTrade status per account
can_trade_status = {
    123: True,   # Account can trade
    124: False   # Account restricted
}

# Active lockouts
active_lockouts = {
    124: {
        'reason': 'Account restricted by TopstepX (canTrade=false)',
        'until': None,  # Indefinite
        'applied_at': datetime(2025, 1, 17, 14, 30, 0)
    }
}
```

**SQLite Persistence:**
```sql
CREATE TABLE account_restrictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    can_trade BOOLEAN NOT NULL,
    changed_at DATETIME NOT NULL,
    previous_state BOOLEAN,
    lockout_applied BOOLEAN DEFAULT 0,
    lockout_removed_at DATETIME
);

-- Track all canTrade state changes for audit trail
CREATE INDEX idx_account_restrictions
ON account_restrictions(account_id, changed_at DESC);

-- Track current state (single row per account)
CREATE TABLE account_current_state (
    account_id INTEGER PRIMARY KEY,
    can_trade BOOLEAN NOT NULL,
    last_updated DATETIME NOT NULL,
    locked_out BOOLEAN DEFAULT 0
);
```

---

## ⚠️ Edge Cases

### **Missing canTrade Field**
- If account event doesn't have `canTrade` field
- Assume `canTrade=true` (fail-open, not fail-closed)
- Log warning about missing field

### **Null or Undefined canTrade**
- Treat as `canTrade=true` (permissive)
- Log warning
- Don't lock out on missing data

### **Multiple Accounts**
- Each account has independent canTrade status
- Track state separately per account_id
- One account locked doesn't affect others

### **Daemon Restart During Lockout**
- Load lockout state from database on startup
- Re-check canTrade via REST API
- If still false, maintain lockout
- If now true, remove lockout

### **Position Close Fails**
- If position close API call fails
- Still apply lockout (rule takes precedence)
- Log error about failed position close
- Retry position close in background

### **API Response Delay**
- GatewayUserAccount event might lag
- Use latest received status
- Don't cache stale data
- Real-time enforcement based on events

### **Manual Override**
- Admin can manually remove lockout
- But will re-apply if canTrade still false
- Next GatewayUserAccount event re-enforces
- Can't override API-level restriction

---

## 🔧 Background Processing

**Periodic State Verification (runs every 5 minutes):**
```python
def verify_can_trade_status():
    """Verify canTrade status matches current lockout state."""

    for account_id in monitored_accounts:
        # Get current in-memory state
        current_state = can_trade_status.get(account_id)
        is_locked = lockout_manager.is_locked(account_id)

        # Verify consistency
        if current_state is False and not is_locked:
            # Should be locked but isn't
            logger.warning(
                f"Inconsistent state detected: account {account_id} "
                f"has canTrade=false but no lockout - Applying lockout"
            )
            enforce(account_id, "canTrade_disabled")

        elif current_state is True and is_locked:
            # Should be unlocked but isn't (manual lockout might exist)
            # Don't auto-remove - might be from another rule
            pass
```

**Startup State Sync:**
```python
def sync_account_states_on_startup():
    """Load and sync all account states on daemon startup."""

    # Get all accounts from API
    accounts = api.get_all_accounts()

    for account in accounts:
        account_id = account['id']
        can_trade = account['canTrade']

        # Update in-memory state
        can_trade_status[account_id] = can_trade

        # Apply lockout if needed
        if not can_trade:
            enforce(account_id, "canTrade_disabled")

    logger.info(f"Synced {len(accounts)} account states on startup")
```

**No Active Monitoring Required:**
- This rule is purely event-driven
- No need to poll API continuously
- Relies on SignalR events for real-time updates
- Periodic verification is just a safety check

---

## 🔗 Dependencies

- **MOD-001:** `close_all_positions()`, `cancel_all_orders()`
- **MOD-002:** `set_lockout()`, `remove_lockout()`
- **API-INT-001:** `GatewayUserAccount` event
- **src/state/account_state.py:** Account state tracking
- **src/state/persistence.py:** SQLite state storage
- **POST /api/Account/search:** Get account info (startup/verification)
- **POST /api/Position/closeContract:** Close positions (enforcement)
- **POST /api/Order/cancel:** Cancel orders (enforcement)

---

**This rule ensures compliance with TopstepX platform restrictions - when they say "no trading", we enforce it immediately.**
