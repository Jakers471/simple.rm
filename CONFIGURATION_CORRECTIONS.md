# Configuration Corrections & Clarifications

**Date:** 2025-10-21
**Purpose:** Address user feedback on risk_config.yaml specification

---

## 🔍 Issues Identified

### **Issue 1: RULE-002 - Per-Symbol Limits**

**User Feedback:**
> "i need to be able to add multiple symbols - like mnq, nq, es, also makesure this is what we should be calling them "symbols" check docs on external api. but i should be able to set limit per symbol as well."

**✅ CORRECT TERMINOLOGY:**
- **Symbol Root:** `MNQ`, `ES`, `NQ`, `RTY` (extracted from contract ID)
- **Contract ID:** `CON.F.US.MNQ.U25` (full contract identifier)
- **Symbol ID:** `F.US.MNQ` (from TopstepX API)

From external API docs (`search_contracts.md`):
```json
{
  "id": "CON.F.US.MNQ.U25",
  "name": "MNQU5",
  "symbolId": "F.US.MNQ"  ← This is what TopstepX calls it
}
```

**✅ CURRENT SPEC IS ALREADY CORRECT!**

The individual rule spec (`02_max_contracts_per_instrument.md`) **already supports per-symbol limits**:

```yaml
max_contracts_per_instrument:
  enabled: true
  limits:
    MNQ: 2      # Max 2 contracts in MNQ
    ES: 1       # Max 1 contract in ES
    NQ: 1       # Max 1 contract in NQ
```

**❌ ISSUE:** The simplified YAML config spec (`RISK_CONFIG_YAML_SPEC.md`) shows:
```yaml
max_contracts_per_instrument:
  enabled: true
  limit: 3           # ← WRONG! This is simplified/incomplete
  per_symbol: true
```

**✅ FIX:** Update `RISK_CONFIG_YAML_SPEC.md` to match the actual rule spec with per-symbol limits.

---

### **Issue 2: RULE-004 - Daily Unrealized Loss (Trade-by-Trade)**

**User Feedback:**
> "this is on a trade by trade basis, does not lockout, just closes the trade."

**❌ CURRENT SPEC IS WRONG!**

The YAML config spec shows:
```yaml
daily_unrealized_loss:
  action: "CLOSE_ALL_AND_LOCKOUT"  # ← WRONG!
```

But user wants:
- Trade-by-trade basis (not total unrealized P&L)
- Close only the losing position (not all positions)
- **No lockout**

**🤔 CLARIFICATION NEEDED:**

**Current Spec (RULE-004):**
- Monitors **TOTAL unrealized P&L across all positions**
- If total unrealized P&L hits -$300, close ALL positions + lockout

**User's Intent:**
- Monitor **individual position unrealized P&L**
- If **one position** hits -$300, close **that position only**
- No lockout, trader can continue

**✅ SOLUTION:**

This is actually a **DIFFERENT RULE** than what's currently spec'd. We need:

**Option A:** Modify RULE-004 to support both modes:
```yaml
daily_unrealized_loss:
  enabled: true
  loss_limit: 300.00
  scope: "per_position"     # "total" or "per_position"
  action: "CLOSE_POSITION"  # Close only losing position
  lockout: false            # No lockout
```

**Option B:** Create a new rule (RULE-013: Per-Position Stop Loss):
```yaml
per_position_unrealized_loss:  # New rule
  enabled: true
  loss_limit: 300.00           # Max loss per position
  action: "CLOSE_POSITION"     # Close only that position
```

**👉 RECOMMENDATION:** Use **Option A** - modify RULE-004 to support both modes, as it's semantically the same rule (unrealized loss limit) with different scope.

---

### **Issue 3: RULE-005 - Max Unrealized Profit (Position-Specific + Breakeven)**

**User Feedback:**
> "closes only that trade"
> "add $ amount to breakeven rule as well, i can eneable whichever one, only one enabled ata time"

**✅ CORRECT!**

The current spec already supports closing individual positions, but needs enhancement for breakeven mode.

**❌ CURRENT SPEC:**
```yaml
max_unrealized_profit:
  action: "CLOSE_ALL_POSITIONS"  # ← Misleading name
  profit_target: 1000.00
```

**✅ ENHANCED SPEC:**
```yaml
max_unrealized_profit:
  enabled: true
  mode: "profit_target"      # "profit_target" or "breakeven"
  profit_target: 1000.00     # Used when mode = "profit_target"
  scope: "per_position"      # Close each position individually
  action: "CLOSE_POSITION"   # Close only the profitable position
```

**How It Works:**

**Mode 1: Profit Target** (`mode: "profit_target"`)
- Close position when unrealized P&L reaches `profit_target` (e.g., +$1000)
- Example: Long 2 MNQ @ 21000, price moves to 21200
  - Unrealized P&L = +$1,000
  - Position closed automatically (take profit)

**Mode 2: Breakeven** (`mode: "breakeven"`)
- Close position when unrealized P&L reaches $0 (breakeven)
- Example: Long 1 ES @ 5800, price drops to 5750, then recovers to 5800
  - Unrealized P&L = $0 (back to entry price)
  - Position closed automatically (protect from giving back gains)

**Use Cases:**
- **Profit Target:** Lock in profits at predetermined level
- **Breakeven:** Protect against giving back gains after position moves in your favor

**Validation:**
- Only one mode can be active at a time
- If `mode = "profit_target"`, must provide `profit_target` value
- If `mode = "breakeven"`, `profit_target` is ignored

**✅ FIX:**
1. Update action to `CLOSE_POSITION`
2. Add `mode` parameter with "profit_target" and "breakeven" options
3. Add `scope: per_position` to clarify individual position handling

---

### **Issue 4: RULE-008 - No Stop-Loss Grace (Position-Specific)**

**User Feedback:**
> "for that trade only"

**✅ CORRECT!**

Same as RULE-005 - should close only the position without a stop-loss, not all positions.

**❌ CURRENT SPEC:**
```yaml
no_stop_loss_grace:
  action: "CLOSE_ALL_POSITIONS"  # ← Wrong
```

**✅ CORRECT:**
```yaml
no_stop_loss_grace:
  action: "CLOSE_POSITION"  # Close only position without stop-loss
```

---

### **Issue 5: RULE-010 - Auth Loss Guard (Connection Issue)**

**User Feedback:**
> "just realised, if we disconnected, we wouldnt even be bale to lockout in the firts place. either get rid of the rule or..."

**🤔 EXCELLENT POINT!**

**The Problem:**
- If SignalR connection drops, we can't receive events
- If we can't receive events, we can't detect `canTrade=false`
- If connection is fully lost, we can't call REST API to close positions

**✅ RULE IS STILL USEFUL - Here's Why:**

**Scenario 1: Daemon is connected, TopstepX disables account**
- `GatewayUserAccount` event fires with `canTrade=false`
- Daemon receives event (connection still active)
- Daemon closes positions + locks out
- ✅ **Rule works perfectly**

**Scenario 2: SignalR connection drops**
- Daemon detects connection loss (SignalR library fires `onDisconnected` event)
- Daemon attempts reconnection
- **During disconnection:** Daemon cannot process events, but also cannot enforce anything
- **After reconnection:** Daemon re-syncs state via REST API
- Daemon checks `canTrade` status on reconnect
- If `canTrade=false`, apply lockout
- ✅ **Rule works after reconnection**

**Scenario 3: Daemon crashes/stops**
- Daemon is offline - cannot enforce anything
- This is **expected behavior** - daemon must be running to enforce
- When daemon restarts: Check `canTrade` on startup (already in spec)
- ✅ **Rule catches up on restart**

**✅ RECOMMENDATION:** **KEEP THE RULE** - it's valuable for detecting when TopstepX disables the account. Add connection monitoring (separate feature).

**✅ ENHANCEMENT:** Add connection monitoring in DAEMON_ARCHITECTURE:
```python
def on_signalr_disconnected():
    """Called when SignalR connection drops."""
    logger.error("SignalR connection lost - cannot enforce rules until reconnected")
    # Attempt reconnection
    # On successful reconnection, re-sync state
```

---

### **Issue 6: RULE-011 - Symbol Blocks (REJECT_ORDER API Call)**

**User Feedback:**
> "reject order, is htat an api call?"

**✅ GREAT QUESTION!**

**Answer:** **NO, it's NOT an API call** - it's event-based prevention.

**How it works:**

**Method 1: Intercept at Event Level (RECOMMENDED)**
```python
def on_order_submitted(order_event):
    """Called when GatewayUserOrder event received."""

    symbol = extract_symbol(order_event['contractId'])

    if symbol in config['blocked_symbols']:
        # DON'T call TopstepX API - order already submitted
        # Instead: Immediately cancel the order
        api.cancel_order(account_id, order_event['orderId'])
        logger.warning(f"BLOCKED ORDER: Symbol {symbol} is blacklisted")
```

**Method 2: Pre-Submission Prevention (REQUIRES INTERMEDIARY)**
```python
# This would require daemon to act as trading proxy (NOT in current design)
def submit_order(order):
    symbol = order['symbol']

    if symbol in blocked_symbols:
        return {"error": "Symbol blocked"}  # Reject before API call

    # Forward to TopstepX
    api.submit_order(order)
```

**Current Design:**
- Daemon monitors events via SignalR (passive monitoring)
- Daemon does NOT intercept orders before submission
- Orders go directly from trading platform → TopstepX

**✅ SOLUTION:**
```yaml
symbol_blocks:
  action: "CANCEL_ORDER"  # Cancel immediately after detection
  # OR
  action: "CLOSE_POSITION"  # Close any existing positions
```

**❌ "REJECT_ORDER" is misleading** - it implies prevention, but we're reactive (cancel after detection).

**✅ FIX:** Rename action to `CANCEL_ORDER` or `CLOSE_POSITION`.

---

## 📝 Summary of Required Changes

| Rule | Current Spec | Issue | Corrected Spec |
|------|-------------|-------|----------------|
| **RULE-002** | `limit: 3` (single value) | Missing per-symbol limits | `limits: { MNQ: 2, ES: 1 }` |
| **RULE-004** | `CLOSE_ALL_AND_LOCKOUT` | Should close per-position | Add `scope: per_position`, `action: CLOSE_POSITION` |
| **RULE-005** | `CLOSE_ALL_POSITIONS` | Missing breakeven mode | Add `mode: profit_target/breakeven`, `action: CLOSE_POSITION` |
| **RULE-008** | `CLOSE_ALL_POSITIONS` | Should close per-position | Change to `CLOSE_POSITION` |
| **RULE-010** | (No issue) | Connection concern | **Keep rule**, add connection monitoring |
| **RULE-011** | `REJECT_ORDER` | Misleading - reactive, not preventive | Change to `CANCEL_ORDER` or `CLOSE_POSITION` |

---

## ✅ Updated YAML Configuration (Corrected)

```yaml
# risk_config.yaml - Risk rule configurations (CORRECTED)

global:
  strict_mode: false
  logging_level: "INFO"

rules:
  # RULE-001: Max Contracts
  max_contracts:
    enabled: true
    limit: 5
    count_type: "net"

  # RULE-002: Max Contracts Per Instrument (CORRECTED)
  max_contracts_per_instrument:
    enabled: true
    limits:
      MNQ: 2    # Max 2 micro NQ contracts
      NQ: 1     # Max 1 full NQ contract
      ES: 1     # Max 1 ES contract
      MES: 3    # Max 3 micro ES contracts
    enforcement: "reduce_to_limit"  # or "close_all"
    unknown_symbol_action: "allow_with_limit:1"  # Default 1 contract for unlisted symbols

  # RULE-003: Daily Realized Loss
  daily_realized_loss:
    enabled: true
    loss_limit: 500.00
    action: "CLOSE_ALL_AND_LOCKOUT"
    lockout_until: "daily_reset"

  # RULE-004: Daily Unrealized Loss (CORRECTED)
  daily_unrealized_loss:
    enabled: true
    loss_limit: 300.00
    scope: "per_position"         # NEW: "total" or "per_position"
    action: "CLOSE_POSITION"      # CHANGED: Close only losing position
    lockout: false                # NEW: No lockout

  # RULE-005: Max Unrealized Profit (CORRECTED)
  # OPTION 1: Profit Target Mode
  max_unrealized_profit:
    enabled: true
    mode: "profit_target"         # NEW: "profit_target" or "breakeven"
    profit_target: 1000.00        # Used when mode = "profit_target"
    scope: "per_position"         # NEW: Close each position at profit target
    action: "CLOSE_POSITION"      # CHANGED: Close only profitable position

  # OPTION 2: Breakeven Mode (Alternative - only enable ONE mode)
  # max_unrealized_profit:
  #   enabled: true
  #   mode: "breakeven"           # Close at $0 P&L (breakeven)
  #   scope: "per_position"
  #   action: "CLOSE_POSITION"

  # RULE-006: Trade Frequency Limit
  trade_frequency_limit:
    enabled: true
    max_trades: 30
    time_window_minutes: 60

  # RULE-007: Cooldown After Loss
  cooldown_after_loss:
    enabled: true
    loss_threshold: 100.00
    cooldown_seconds: 300

  # RULE-008: No Stop-Loss Grace Period (CORRECTED)
  no_stop_loss_grace:
    enabled: true
    grace_period_seconds: 30
    action: "CLOSE_POSITION"      # CHANGED: Close only position without stop-loss

  # RULE-009: Session Block Outside Hours
  session_block_outside:
    enabled: true
    allowed_hours:
      start: "08:30"
      end: "15:00"
    timezone: "America/Chicago"
    action: "CANCEL_ORDER"        # Cancel orders outside hours

  # RULE-010: Auth Loss Guard (KEEP - see notes above)
  auth_loss_guard:
    enabled: true
    action: "CLOSE_ALL_AND_LOCKOUT"
    auto_unlock_on_restore: true  # Auto-unlock when canTrade=true again

  # RULE-011: Symbol Blocks (CORRECTED)
  symbol_blocks:
    enabled: true
    blocked_symbols:
      - "RTY"   # Russell 2000
      - "BTC"   # Bitcoin futures
    action: "CANCEL_ORDER"        # CHANGED: Cancel orders in blocked symbols
    close_existing: true          # NEW: Also close any existing positions

  # RULE-012: Trade Management
  trade_management:
    enabled: false
    auto_stop_loss: true
    stop_loss_ticks: 10
```

---

## 🛠️ Next Steps

1. ✅ **Update RISK_CONFIG_YAML_SPEC.md** with corrected schema
2. ✅ **Update individual rule specs** to align with user requirements
3. ✅ **Add `scope` parameter** to RULE-004, RULE-005, RULE-008
4. ✅ **Update enforcement actions** in MOD-001 to support per-position actions
5. ✅ **Keep RULE-010** but document connection monitoring requirements
6. ✅ **Clarify RULE-011** action terminology

---

**Status:** Ready for implementation with corrections applied
