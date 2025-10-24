# Contract Mismatch Audit Report

**Date:** 2025-10-23
**Scope:** API → Backend → Tests
**Ground Truth:** `/project-specs/SPECS/01-EXTERNAL-API/` and `/project-specs/SPECS/07-DATA-MODELS/`

---

## Executive Summary

**Critical Mismatches Found:** 6
**Severity:** HIGH - Silent failures likely in production

The codebase has **systematic camelCase/snake_case mismatches** between:
1. TopstepX API (uses camelCase)
2. SPECS documentation (uses camelCase)
3. Implementation code (uses snake_case)
4. Test fixtures (mix of both - INCONSISTENT)

**Impact:** Data will be silently dropped at runtime. No errors thrown, just missing fields.

---

## 1. API → Backend Mismatches

### Critical: Position Event Field Names

| Layer | Field Name | Type | Notes |
|-------|-----------|------|-------|
| **API Spec** | `accountId` | int | GatewayUserPosition event |
| **API Spec** | `contractId` | string | GatewayUserPosition event |
| **API Spec** | `averagePrice` | number | GatewayUserPosition event |
| **API Spec** | `creationTimestamp` | string | GatewayUserPosition event |
| **STATE OBJECTS SPEC** | `account_id` | int | Position dataclass |
| **STATE OBJECTS SPEC** | `contract_id` | str | Position dataclass |
| **STATE OBJECTS SPEC** | `average_price` | float | Position dataclass |
| **STATE OBJECTS SPEC** | `created_at` | datetime | Position dataclass |
| **IMPLEMENTATION** | `contractId` | str | state_manager.py line 30 |
| **IMPLEMENTATION** | `averagePrice` | float | state_manager.py line 33 |
| **IMPLEMENTATION** | `creationTimestamp` | str | state_manager.py line 34 |

**Problem:** Implementation uses camelCase (matches API), but SPEC says to use snake_case. **No conversion layer exists.**

**Evidence:**
- `src/core/state_manager.py` line 30: `'contractId': position['contractId']`
- `project-specs/SPECS/07-DATA-MODELS/STATE_OBJECTS.md` line 189-198: Shows `from_api_payload()` method that converts camelCase → snake_case
- **BUT**: This method is NOT implemented in actual code

**Impact:** If code follows SPEC and uses snake_case, API data will be lost.

---

### Critical: Order Event Field Names

| Layer | Field Name | Type | Notes |
|-------|-----------|------|-------|
| **API Spec** | `limitPrice` | number | GatewayUserOrder |
| **API Spec** | `stopPrice` | number | GatewayUserOrder |
| **API Spec** | `fillVolume` | int | GatewayUserOrder |
| **API Spec** | `filledPrice` | number | GatewayUserOrder |
| **API Spec** | `customTag` | string | GatewayUserOrder |
| **STATE OBJECTS SPEC** | `limit_price` | Optional[float] | Order dataclass |
| **STATE OBJECTS SPEC** | `stop_price` | Optional[float] | Order dataclass |
| **STATE OBJECTS SPEC** | `filled_size` | int | Order dataclass |
| **STATE OBJECTS SPEC** | `fill_price` | Optional[float] | Order dataclass |
| **IMPLEMENTATION** | `limitPrice` | number | state_manager.py line 90 |
| **IMPLEMENTATION** | `stopPrice` | number | state_manager.py line 91 |

**Problem:**
1. API uses `filledPrice`, SPEC uses `fill_price`, implementation stores `limitPrice`
2. API uses `fillVolume`, SPEC uses `filled_size`
3. API has `customTag`, completely missing from implementation

**Impact:** Order fill prices and volumes will be incorrect or missing.

---

### Critical: Trade Event Field Names

| Layer | Field Name | Type | Notes |
|-------|-----------|------|-------|
| **API Spec** | `profitAndLoss` | number | GatewayUserTrade |
| **API Spec** | `creationTimestamp` | string | GatewayUserTrade |
| **STATE OBJECTS SPEC** | `profit_and_loss` | float | Trade dataclass |
| **STATE OBJECTS SPEC** | `execution_time` | datetime | Trade dataclass |
| **TEST FIXTURE** | `profitAndLoss` | float | signalr_events.py line 21 |
| **TEST FIXTURE** | `executionTime` | string | signalr_events.py line 22 |

**Problem:**
- API: `creationTimestamp`
- SPEC: `execution_time`
- Test: `executionTime`
- **Three different names for the same field!**

**Impact:** Trades won't be recorded with correct timestamps.

---

### Critical: Account Response Field Names

| Layer | Field Name | Type | Notes |
|-------|-----------|------|-------|
| **API Spec** | `canTrade` | bool | Account search response |
| **API Spec** | `isVisible` | bool | Account search response |
| **API Spec** | `simulated` | bool | Account search response (SignalR only) |
| **Implementation** | ❌ MISSING | - | Not tracked anywhere |

**Problem:** Important account flags not tracked.

**Impact:** Cannot detect if account is suspended or simulated.

---

## 2. Backend → Tests Mismatches

### Critical: Test Fixtures Use Wrong Field Names

**File:** `tests/fixtures/signalr_events.py`

| Fixture | Uses API Format? | Uses SPEC Format? | Consistent? |
|---------|------------------|-------------------|-------------|
| `trade_profit_event` | ✅ YES (camelCase) | ❌ NO | Partial |
| `position_opened_event` | ❌ NO (uses `createdAt`) | ❌ NO | **WRONG** |
| `order_placed_event` | ❌ NO (uses `createdAt`) | ❌ NO | **WRONG** |

**Evidence:**
```python
# Line 117: Position event uses createdAt instead of creationTimestamp
"createdAt": "2025-01-17T14:30:00Z",  # ❌ WRONG - API uses creationTimestamp

# Line 22: Trade event uses executionTime instead of creationTimestamp
"executionTime": "2025-01-17T14:45:15Z",  # ⚠️ Inconsistent with API spec
```

**API Spec Says:**
- Positions: `creationTimestamp` (line 197 of realtime_data_overview.md)
- Orders: `creationTimestamp` (line 226)
- Trades: `creationTimestamp` (line 269)

**Test Fixtures Say:**
- Positions: `createdAt` ❌
- Orders: `createdAt` ❌
- Trades: `executionTime` ❌

**Impact:** Tests pass with wrong data shapes. Production will fail.

---

### Critical: Function Signature Mismatch

**File:** `src/core/pnl_tracker.py`

```python
# Line 64: Method signature
def record_realized_pnl(self, account_id: int, contract_id: str, realized_pnl: float) -> float:
```

**File:** `tests/fixtures/signalr_events.py`

```python
# Line 21: Trade event payload
{
    "id": 10001,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "quantity": 2,           # ⚠️ SPEC calls this 'size'
    "profitAndLoss": 45.50,
    ...
}
```

**API Spec Says:**
- Field name is `size` (line 292 of realtime_data_overview.md)

**Test Fixture Says:**
- Field name is `quantity` ❌

**Impact:** PnL calculations will fail to find `quantity` field.

---

## 3. SPECS → Implementation Mismatches

### Critical: Missing from_api_payload() Methods

**SPEC Says (STATE_OBJECTS.md lines 188-199):**
```python
@classmethod
def from_api_payload(cls, payload: dict) -> 'Position':
    """Create Position from TopstepX API payload"""
    return cls(
        id=payload['id'],
        account_id=payload['accountId'],      # ← Converts camelCase
        contract_id=payload['contractId'],    # ← to snake_case
        type=PositionType(payload['type']),
        size=payload['size'],
        average_price=payload['averagePrice'],
        ...
    )
```

**Implementation Reality:**
- ❌ This method does NOT exist in `src/core/state_manager.py`
- ❌ No conversion layer exists anywhere
- ❌ Code directly stores camelCase from API

**Impact:** Breaking change if someone implements the SPEC.

---

### Critical: Missing State Object Dataclasses

**SPEC Defines (STATE_OBJECTS.md):**
- ✅ Position (lines 123-200)
- ✅ Order (lines 219-316)
- ✅ Trade (lines 336-407)
- ✅ Quote (lines 426-487)
- ✅ ContractMetadata (lines 502-589)
- ✅ Lockout (lines 610-682)
- ✅ EnforcementAction (lines 686-756)

**Implementation Has:**
- ❌ NONE of these as Python dataclasses
- ❌ All data stored as raw dicts
- ❌ No type safety
- ❌ No validation

**Impact:**
- No compile-time type checking
- Silent failures on bad data
- Cannot use IDE autocomplete

---

### Critical: Order State Enum Mismatch

**API Spec Says (realtime_data_overview.md lines 440-450):**
```csharp
public enum OrderStatus {
    None      = 0,
    Open      = 1,
    Filled    = 2,
    Cancelled = 3,
    Expired   = 4,
    Rejected  = 5,
    Pending   = 6
}
```

**STATE OBJECTS SPEC Says (STATE_OBJECTS.md lines 79-87):**
```python
class OrderState(IntEnum):
    ACTIVE = 1       # Order placed, not filled
    FILLED = 2       # Order completely filled
    CANCELED = 3     # Order canceled
    REJECTED = 4     # Order rejected by exchange
    PARTIAL = 5      # Partially filled
```

**Implementation Says (state_manager.py line 76):**
```python
# States: 1=Pending, 2=Working, 3=Filled, 4=Cancelled, 5=Rejected
```

**Three Different Mappings:**

| Value | API Name | SPEC Name | Implementation Name |
|-------|----------|-----------|---------------------|
| 0 | None | - | - |
| 1 | Open | ACTIVE | Pending |
| 2 | Filled | FILLED | Working |
| 3 | Cancelled | CANCELED | Filled |
| 4 | Expired | REJECTED | Cancelled |
| 5 | Rejected | PARTIAL | Rejected |
| 6 | Pending | - | - |

**Impact:** Order states will be completely wrong.

---

## 4. Critical Fixes Needed (Priority Order)

### 🔥 P0 - Immediate Failures

1. **Create conversion layer for API → Backend**
   - Implement `from_api_payload()` methods from SPEC
   - Convert camelCase → snake_case at API boundary
   - **Files:** All data models

2. **Fix order state enum**
   - Match API OrderStatus enum exactly
   - Remove conflicting comments
   - **File:** `src/core/state_manager.py` line 76

3. **Fix test fixtures**
   - Change `createdAt` → `creationTimestamp` in positions/orders
   - Change `executionTime` → `creationTimestamp` in trades
   - Change `quantity` → `size` in trades
   - **File:** `tests/fixtures/signalr_events.py`

### 🔥 P1 - Data Loss

4. **Add missing API fields**
   - `customTag` on orders
   - `canTrade`, `isVisible`, `simulated` on accounts
   - `fees`, `voided` on trades
   - **Files:** All state tracking

5. **Implement dataclasses from SPEC**
   - Replace raw dicts with typed dataclasses
   - Add validation in `__post_init__`
   - **Files:** Create `src/data_models/*.py`

### 🔥 P2 - Silent Errors

6. **Add field name validation**
   - Log warnings when API returns unexpected fields
   - Fail fast on missing required fields
   - **Files:** All API event handlers

---

## Appendix: Field Name Cross-Reference

### Position Fields
```
API            | SPEC          | Implementation
---------------|---------------|----------------
id             | id            | id
accountId      | account_id    | accountId ❌
contractId     | contract_id   | contractId ❌
type           | type          | type
size           | size          | size
averagePrice   | average_price | averagePrice ❌
creationTimestamp | created_at | creationTimestamp ❌
updateTimestamp   | updated_at | (not stored) ❌
```

### Order Fields
```
API            | SPEC          | Implementation
---------------|---------------|----------------
id             | id            | id
accountId      | account_id    | accountId ❌
contractId     | contract_id   | contractId ❌
type           | type          | type
side           | side          | side
size           | size          | size
limitPrice     | limit_price   | limitPrice ❌
stopPrice      | stop_price    | stopPrice ❌
status         | state         | state ⚠️
fillVolume     | filled_size   | (not stored) ❌
filledPrice    | fill_price    | (not stored) ❌
customTag      | -             | (not stored) ❌
creationTimestamp | created_at | creationTimestamp ❌
```

### Trade Fields
```
API            | SPEC              | Test Fixture
---------------|-------------------|----------------
id             | id                | id
accountId      | account_id        | accountId ❌
contractId     | contract_id       | contractId ❌
profitAndLoss  | profit_and_loss   | profitAndLoss ❌
creationTimestamp | execution_time | executionTime ❌
price          | (multiple)        | (split into entry/exit) ⚠️
size           | quantity          | quantity ❌
side           | -                 | side
fees           | -                 | fees
voided         | -                 | voided
orderId        | -                 | orderId
```

---

**End of Report**
