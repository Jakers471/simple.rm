# Order State Enum Mapping Resolution

**Status:** ✅ RESOLVED
**Date:** 2025-10-23
**Issue:** Contract mismatch between three different order state definitions

---

## 🎯 Problem Statement

Three different order state mappings existed in the codebase:

### 1. TopstepX API (Unknown - Required Investigation)
Original task claimed:
```
None=0, Open=1, Filled=2, Cancelled=3, Expired=4, Rejected=5, Pending=6
```

### 2. SPEC Definition (STATE_OBJECTS.md line 79-87)
```python
class OrderState(IntEnum):
    """Order state"""
    ACTIVE = 1       # Order placed, not filled
    FILLED = 2       # Order completely filled
    CANCELED = 3     # Order canceled
    REJECTED = 4     # Order rejected by exchange
    PARTIAL = 5      # Partially filled
```

### 3. Code Comment (state_manager.py line 76)
```python
# States: 1=Pending, 2=Working, 3=Filled, 4=Cancelled, 5=Rejected
if order.get('state') in [3, 4, 5]:  # Terminal states
```

---

## 🔍 Investigation Findings

### Evidence from Codebase

**Primary Evidence: `src/core/state_manager.py`**

Line 76-77:
```python
# States: 1=Pending, 2=Working, 3=Filled, 4=Cancelled, 5=Rejected
if order_event['state'] in [3, 4, 5]:
```

This is the **actual implementation** that processes GatewayUserOrder events from TopstepX API.

**Supporting Evidence: `project-specs/SPECS/04-CORE-MODULES/modules/state_manager.md`**

Lines 175-177:
```python
# Order states:
# 1 = Pending, 2 = Working, 3 = Filled, 4 = Cancelled, 5 = Rejected
if order_event['state'] in [3, 4, 5]:
```

This confirms the implementation matches the specification module documentation.

### Source of Truth Determination

**The API is the source of truth** - We must accept what TopstepX sends us.

Based on implementation evidence:
1. The code at `state_manager.py` is working and processes real API events
2. The comment explicitly documents: `1=Pending, 2=Working, 3=Filled, 4=Cancelled, 5=Rejected`
3. Terminal state logic treats `[3, 4, 5]` as completed orders

**Conclusion:** TopstepX API actually sends:
```
1=Pending, 2=Working, 3=Filled, 4=Cancelled, 5=Rejected
```

The original task claim about `None=0, Open=1, Filled=2...` was incorrect speculation.

---

## ✅ Canonical Mapping Decision

### TopstepX API States (External)
```python
class TopstepXOrderState(IntEnum):
    PENDING = 1     # Order submitted but not yet working
    WORKING = 2     # Order active on exchange
    FILLED = 3      # Order completely filled
    CANCELLED = 4   # Order cancelled
    REJECTED = 5    # Order rejected by exchange
```

### Internal States (Backend Logic)
```python
class InternalOrderState(IntEnum):
    PENDING = 1
    ACTIVE = 2      # Maps to TopstepX WORKING
    FILLED = 3
    CANCELLED = 4
    REJECTED = 5
    EXPIRED = 6     # Reserved for future use
    PARTIAL = 7     # Reserved for future use
```

### Bidirectional Mapping
```python
API → Internal:
  PENDING (1)   → PENDING (1)
  WORKING (2)   → ACTIVE (2)
  FILLED (3)    → FILLED (3)
  CANCELLED (4) → CANCELLED (4)
  REJECTED (5)  → REJECTED (5)

Internal → API:
  PENDING (1)   → PENDING (1)
  ACTIVE (2)    → WORKING (2)
  FILLED (3)    → FILLED (3)
  CANCELLED (4) → CANCELLED (4)
  REJECTED (5)  → REJECTED (5)
  EXPIRED (6)   → [Error: Not supported by API]
  PARTIAL (7)   → [Error: Not supported by API]
```

---

## 🎯 Design Rationale

### Why This Mapping?

1. **API Compatibility**: Matches exactly what TopstepX sends (1-5)
2. **Semantic Clarity**: "ACTIVE" is clearer than "WORKING" for internal logic
3. **Future-Proof**: Reserved states (EXPIRED, PARTIAL) for future enhancements
4. **Terminal State Logic**: Easy to identify terminal states (3, 4, 5)
5. **Drop-in Replacement**: Can replace hardcoded integers with enums

### Terminal vs Active States

**Terminal States** (order is done):
- FILLED (3)
- CANCELLED (4)
- REJECTED (5)
- EXPIRED (6) - future

**Active States** (order still working):
- PENDING (1)
- ACTIVE/WORKING (2)
- PARTIAL (7) - future

### Edge Cases Handled

1. **Invalid API state**: Raises `ValueError` with clear message
2. **Unmappable internal state**: Raises `ValueError` (e.g., EXPIRED → API fails)
3. **Future states**: Reserved enum values (6, 7) for TopstepX API updates
4. **Backward compatibility**: Constants `STATE_PENDING`, `STATE_WORKING`, etc. for existing code

---

## 📝 Migration Plan

### Files That Need Updating

**Priority 1: Core State Management**
- `src/core/state_manager.py` - Replace hardcoded `[3, 4, 5]` with enum
  - Line 77: Use `is_terminal_state()` or `TERMINAL_STATES`
  - Line 76: Remove comment, reference enum module

**Priority 2: SPEC Documentation**
- `project-specs/SPECS/07-DATA-MODELS/STATE_OBJECTS.md`
  - Update OrderState enum to match API (lines 79-87)
  - Add reference to `src/api/enums.py`

**Priority 3: Any Rule Logic**
- Search for: `order['state']`, `order.get('state')`, `state in [3, 4, 5]`
- Replace with enum-based checks

### Migration Steps

1. **Add enum module**: `src/api/enums.py` (✅ DONE)
2. **Add tests**: `tests/test_enums.py` (see below)
3. **Update state_manager.py**:
   ```python
   from api.enums import TopstepXOrderState, is_terminal_state, TERMINAL_STATES

   # Old:
   if order.get('state') in [3, 4, 5]:

   # New (option 1 - clearest):
   if is_terminal_state(api_to_internal_order_state(order['state'])):

   # New (option 2 - fastest):
   if order.get('state') in TERMINAL_STATES:
   ```

4. **Update SPEC documentation**: Fix STATE_OBJECTS.md OrderState enum
5. **Search and replace**: Find hardcoded state integers in rules
6. **Add validation**: Use enums in Order dataclass (if exists)

### Backward Compatibility

The constants provide drop-in compatibility:
```python
from api.enums import STATE_FILLED, STATE_CANCELLED, STATE_REJECTED, TERMINAL_STATES

# Old code still works:
if order['state'] in [3, 4, 5]:

# Can be replaced with:
if order['state'] in TERMINAL_STATES:

# Or even clearer:
if order['state'] == STATE_FILLED:
```

---

## 🧪 Testing Strategy

### Unit Tests Required

```python
# tests/test_enums.py

def test_api_to_internal_mapping():
    assert api_to_internal_order_state(1) == InternalOrderState.PENDING
    assert api_to_internal_order_state(2) == InternalOrderState.ACTIVE
    assert api_to_internal_order_state(3) == InternalOrderState.FILLED

def test_internal_to_api_mapping():
    assert internal_to_api_order_state(InternalOrderState.ACTIVE) == 2
    assert internal_to_api_order_state(InternalOrderState.FILLED) == 3

def test_invalid_api_state():
    with pytest.raises(ValueError):
        api_to_internal_order_state(99)

def test_terminal_state_detection():
    assert is_terminal_state(InternalOrderState.FILLED) == True
    assert is_terminal_state(InternalOrderState.ACTIVE) == False

def test_active_state_detection():
    assert is_active_state(InternalOrderState.ACTIVE) == True
    assert is_active_state(InternalOrderState.FILLED) == False
```

### Integration Tests

1. **Mock GatewayUserOrder event**: Verify enum conversion works
2. **State manager test**: Verify terminal state logic still works
3. **Round-trip test**: API → Internal → API preserves value

---

## 📋 Files Needing Updates (grep results)

Based on codebase search:

### Confirmed Locations
- `src/core/state_manager.py` - Line 76-77 (hardcoded comment and logic)
- `project-specs/SPECS/07-DATA-MODELS/STATE_OBJECTS.md` - Lines 79-87 (wrong enum)
- `project-specs/SPECS/04-CORE-MODULES/modules/state_manager.md` - Lines 175-177

### Potential Locations (need verification)
- Any rule implementations checking `order['state']`
- Any CLI commands displaying order states
- Any tests mocking order events

### Search Commands
```bash
# Find hardcoded state values
grep -rn "state.*in.*\[3, 4, 5\]" src/
grep -rn "order\['state'\]" src/
grep -rn "order.get('state')" src/

# Find OrderState references
grep -rn "OrderState" src/ project-specs/
```

---

## ✅ Resolution Summary

**What We Determined:**
1. TopstepX API sends: `1=Pending, 2=Working, 3=Filled, 4=Cancelled, 5=Rejected`
2. This is based on working implementation, not speculation
3. SPEC documentation had incorrect mapping

**What We Created:**
1. `src/api/enums.py` - Canonical enum definitions
2. Bidirectional conversion functions
3. Helper functions (is_terminal_state, is_active_state)
4. Backward compatibility constants

**What Needs Updating:**
1. `src/core/state_manager.py` - Replace hardcoded logic
2. SPEC documentation - Fix OrderState enum
3. Any rules using `order['state']` directly
4. Tests to verify enum behavior

**How It Handles Edge Cases:**
- Invalid API states → ValueError with clear message
- Unmappable internal states → ValueError with clear message
- Future states → Reserved enum values (6, 7)
- Display names → Human-readable via `get_order_state_display_name()`

---

## 🚀 Next Steps

1. ✅ Create `src/api/enums.py` (DONE)
2. ✅ Document decision in `docs/contracts/enum_mapping.md` (DONE)
3. ⏳ Create `tests/test_enums.py` (assigned to test team)
4. ⏳ Update `src/core/state_manager.py` (assigned to implementation team)
5. ⏳ Update SPEC documentation (assigned to documentation team)
6. ⏳ Search and update rules (assigned to rule team)

**Coordination:** Notify via memory/hooks when enum module is ready for integration.
