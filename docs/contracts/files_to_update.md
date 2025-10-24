# Files Requiring Enum Migration Updates

**Generated:** 2025-10-23
**Related:** enum_mapping.md

This document lists all files that need to be updated to use the new canonical enum mapping from `src/api/enums.py`.

---

## 🎯 Critical Updates (Must Do)

### 1. `src/core/state_manager.py`

**Lines:** 76-77, 92, 102

**Current Code:**
```python
# States: 1=Pending, 2=Working, 3=Filled, 4=Cancelled, 5=Rejected
if order.get('state') in [3, 4, 5]:
```

**Updated Code:**
```python
from api.enums import TERMINAL_STATES, is_terminal_state, api_to_internal_order_state

# Use the enum constant set
if order.get('state') in TERMINAL_STATES:
```

**Or more explicitly:**
```python
from api.enums import TopstepXOrderState, InternalOrderState, api_to_internal_order_state

# Convert to internal state and check
internal_state = api_to_internal_order_state(order['state'])
if is_terminal_state(internal_state):
    # Order is done (filled/cancelled/rejected)
```

**Impact:** HIGH - This is the core state management logic

---

### 2. `project-specs/SPECS/07-DATA-MODELS/STATE_OBJECTS.md`

**Lines:** 79-87

**Current Code:**
```python
class OrderState(IntEnum):
    """Order state"""
    ACTIVE = 1       # Order placed, not filled
    FILLED = 2       # Order completely filled
    CANCELED = 3     # Order canceled
    REJECTED = 4     # Order rejected by exchange
    PARTIAL = 5      # Partially filled
```

**Updated Code:**
```python
class OrderState(IntEnum):
    """Order state - matches TopstepX API values.

    See src/api/enums.py for canonical definitions.
    Use InternalOrderState from that module instead.
    """
    PENDING = 1      # Order submitted but not yet working
    ACTIVE = 2       # Order active on exchange (was: WORKING in API)
    FILLED = 3       # Order completely filled
    CANCELLED = 4    # Order cancelled
    REJECTED = 5     # Order rejected by exchange
    EXPIRED = 6      # Order expired (reserved)
    PARTIAL = 7      # Partially filled (reserved)
```

**Or better - reference the canonical module:**
```markdown
### **OrderState**

**Canonical Definition:** See `src/api/enums.InternalOrderState`

Order states are now centrally defined in `src/api/enums.py` to resolve
contract mismatches between API, SPEC, and implementation.

Use:
- `InternalOrderState` for backend logic
- `TopstepXOrderState` for API payloads
- Helper functions: `is_terminal_state()`, `is_active_state()`
```

**Impact:** MEDIUM - Documentation only, but critical for future development

---

### 3. `project-specs/SPECS/04-CORE-MODULES/modules/state_manager.md`

**Lines:** 175-177

**Current Code:**
```python
# Order states:
# 1 = Pending, 2 = Working, 3 = Filled, 4 = Cancelled, 5 = Rejected
if order_event['state'] in [3, 4, 5]:
```

**Updated Code:**
```python
from api.enums import TERMINAL_STATES

# Terminal states (order is done)
if order_event['state'] in TERMINAL_STATES:
```

**Or update comment to reference enum:**
```python
# Order states: see src/api/enums.TopstepXOrderState for definitions
if order_event['state'] in TERMINAL_STATES:
```

**Impact:** MEDIUM - Documentation/spec file

---

## 🔍 Potential Updates (Search Required)

### Files That May Use Order States

**Search Command:**
```bash
cd "/home/jakers/projects/simple-risk-manager/simple risk manager"
grep -rn "order\['state'\]" src/ tests/
grep -rn "order.get('state')" src/ tests/
grep -rn "OrderState" src/ tests/
```

**Common Patterns to Look For:**

1. **Direct state checks:**
   ```python
   if order['state'] == 3:  # BAD: hardcoded
   if order['state'] == STATE_FILLED:  # GOOD: using constant
   ```

2. **State filtering:**
   ```python
   active_orders = [o for o in orders if o['state'] in [1, 2]]  # BAD
   active_orders = [o for o in orders if is_active_state(o['state'])]  # GOOD
   ```

3. **State comparison:**
   ```python
   if order_state > 2:  # BAD: assumes numeric ordering
   if is_terminal_state(order_state):  # GOOD: semantic check
   ```

### Likely Locations

Based on project structure:

- `src/rules/*.py` - Any rule checking order states
- `src/api/user_hub.py` - Event handling for GatewayUserOrder
- `tests/test_state_manager.py` - Unit tests for state manager
- `tests/rules/test_*.py` - Rule tests that mock orders
- Any CLI commands showing order status

---

## 📝 SPEC Documentation Updates

### Files to Update

1. **STATE_OBJECTS.md** (listed above)
2. **COMPLETE_SPECIFICATION.md** - References to OrderState
3. **DATABASE_SCHEMA.md** - Orders table `state` column description

### Documentation Pattern

Add this notice to relevant SPEC files:
```markdown
> **Note:** Order state enums are centrally defined in `src/api/enums.py`
> to resolve contract mismatches. Always use `InternalOrderState` for
> backend logic and `TopstepXOrderState` when processing API events.
```

---

## 🧪 Testing Updates

### New Test File Required

**File:** `tests/test_enums.py`

**Test Coverage:**
- Enum value correctness (TopstepX: 1-5)
- Bidirectional mapping (API ↔ Internal)
- Invalid state handling (ValueError)
- Terminal state detection
- Active state detection
- Display name generation
- Backward compatibility constants

### Existing Tests to Update

Search for tests that:
1. Mock GatewayUserOrder events with hardcoded `state` values
2. Assert on specific state values (e.g., `assert order['state'] == 3`)
3. Test state_manager.py order handling

**Update Pattern:**
```python
# Old test:
mock_order = {'state': 3, ...}  # Hardcoded

# New test:
from api.enums import TopstepXOrderState
mock_order = {'state': TopstepXOrderState.FILLED.value, ...}
# Or even better:
mock_order = {'state': TopstepXOrderState.FILLED, ...}
```

---

## 🔄 Migration Checklist

- [ ] Create `src/api/enums.py` (✅ DONE)
- [ ] Create `tests/test_enums.py` (TODO)
- [ ] Update `src/core/state_manager.py` line 76-77 (TODO)
- [ ] Update `src/core/state_manager.py` line 92, 102 (TODO)
- [ ] Update `project-specs/SPECS/07-DATA-MODELS/STATE_OBJECTS.md` (TODO)
- [ ] Update `project-specs/SPECS/04-CORE-MODULES/modules/state_manager.md` (TODO)
- [ ] Search for hardcoded state values in rules (TODO)
- [ ] Search for hardcoded state values in tests (TODO)
- [ ] Update any CLI commands displaying order states (TODO)
- [ ] Run full test suite to verify no regressions (TODO)
- [ ] Update API integration code if needed (TODO)

---

## 🚨 Breaking Changes

**None** - This is backward compatible if done correctly.

The constants (`STATE_FILLED`, `STATE_CANCELLED`, etc.) allow gradual migration:
```python
# Old code still works:
if order['state'] in [3, 4, 5]:

# Can migrate to:
if order['state'] in TERMINAL_STATES:

# Eventually to:
if is_terminal_state(api_to_internal_order_state(order['state'])):
```

**However**, if you change the numeric values (e.g., FILLED from 3 to 2), that would break everything. **DO NOT** change the numeric values - they must match the API.

---

## 📊 Impact Summary

| File/Area | Priority | Impact | Effort |
|-----------|----------|--------|--------|
| `src/core/state_manager.py` | HIGH | HIGH | LOW (3 lines) |
| `STATE_OBJECTS.md` | HIGH | MEDIUM | LOW (documentation) |
| `state_manager.md` spec | MEDIUM | LOW | LOW (documentation) |
| Rules (if any use states) | MEDIUM | MEDIUM | MEDIUM (search required) |
| Tests | MEDIUM | MEDIUM | MEDIUM (new + updates) |
| CLI commands | LOW | LOW | LOW (display only) |

**Total Estimated Effort:** 2-4 hours for complete migration

**Risk Level:** LOW (backward compatible)

---

## ✅ Verification Steps

After migration:

1. **Run tests:** `python -m pytest tests/test_enums.py -v`
2. **Run state manager tests:** `python -m pytest tests/test_state_manager.py -v`
3. **Search for hardcoded values:** `grep -rn "\b[3-5]\b.*state\|state.*\b[3-5]\b" src/`
4. **Verify no magic numbers:** Should only find enum definitions
5. **Integration test:** Mock GatewayUserOrder event, verify state handling
6. **Code review:** Ensure all order state checks use enums

---

**Status:** Ready for implementation team
**Owner:** Contract Fixing Swarm → Implementation Team
**Coordination:** Via memory key `swarm/contract-fix/enums-complete`
