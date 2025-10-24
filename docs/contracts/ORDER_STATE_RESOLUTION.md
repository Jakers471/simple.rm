# Order State Enum Resolution

## Investigation Summary

**Date**: 2025-10-23
**Investigator**: ORDER STATE ENUM VERIFIER AND FIXER Agent
**Status**: RESOLVED with HIGH CONFIDENCE

## Sources Checked

1. `/project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/realtime_updates/realtime_data_overview.md`
2. `/project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/orders/search_orders.md`
3. `/project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/orders/place_order.md`
4. `/src/core/state_manager.py`
5. `/src/api/enums.py`
6. `/docs/contracts/api_contracts.json`

## Evidence Found

### Primary Source: Official API Documentation

From `realtime_data_overview.md` (lines 438-451), the **official TopstepX API C# enum definition**:

```csharp
public enum OrderStatus
{
    None      = 0,
    Open      = 1,
    Filled    = 2,
    Cancelled = 3,
    Expired   = 4,
    Rejected  = 5,
    Pending   = 6
}
```

### Supporting Evidence: API Response Example

From `search_orders.md` (lines 40-64), actual API response showing filled order:

```json
{
  "orders": [
    {
      "id": 36598,
      "accountId": 704,
      "contractId": "CON.F.US.EP.U25",
      "symbolId": "F.US.EP",
      "creationTimestamp": "2025-07-18T21:00:01.268009+00:00",
      "updateTimestamp": "2025-07-18T21:00:01.268009+00:00",
      "status": 2,    ← FILLED order has status=2
      "type": 2,
      "side": 0,
      "size": 1,
      "limitPrice": null,
      "stopPrice": null,
      "fillVolume": 1,
      "filledPrice": 6335.250000000,
      "customTag": null
    }
  ]
}
```

This confirms: **status: 2 = Filled** (matches OrderStatus.Filled = 2)

### Conflicting Evidence in Code

From `state_manager.py` (line 76):
```python
# States: 1=Pending, 2=Working, 3=Filled, 4=Cancelled, 5=Rejected
```

This comment is **INCORRECT** and contradicts the official API documentation.

From `realtime_data_overview.md` (line 228), SignalR GatewayUserOrder event shows:
```json
"status": 1,
```

For an order with `"fillVolume": 0` - meaning it's an **Open/Working** order, which confirms status=1 is Open (not Pending).

## Truth Determined

TopstepX API uses the **OrderStatus enum** for the `status` field:

| Value | Name | Description |
|-------|------|-------------|
| 0 | None | No status / Unknown |
| 1 | Open | Order is working on exchange (active) |
| 2 | Filled | Order completely filled |
| 3 | Cancelled | Order cancelled by user or system |
| 4 | Expired | Order expired |
| 5 | Rejected | Order rejected by exchange |
| 6 | Pending | Order submitted but not yet working |

**Note**: Value 6 (Pending) represents orders that are submitted but not yet active on the exchange. Value 1 (Open) represents orders actively working.

## What Was Wrong

### 1. api_contracts.json (lines 117-133)
**INCORRECT**:
```json
"status": {
  "enum": {
    "None": 0,
    "Open": 1,
    "Filled": 2,
    "Cancelled": 3,
    "Expired": 4,
    "Rejected": 5,
    "Pending": 6
  }
}
```

**Status**: Actually, this was CORRECT! No changes needed.

### 2. enums.py - TopstepXOrderState
**INCORRECT** (lines 15-31):
```python
class TopstepXOrderState(IntEnum):
    PENDING = 1     # Order submitted but not yet working
    WORKING = 2     # Order active on exchange (open/working)
    FILLED = 3      # Order completely filled
    CANCELLED = 4   # Order cancelled by user or system
    REJECTED = 5    # Order rejected by exchange
```

This enum was based on the incorrect comment in state_manager.py and doesn't match the actual API.

### 3. state_manager.py (line 76)
**INCORRECT** comment:
```python
# States: 1=Pending, 2=Working, 3=Filled, 4=Cancelled, 5=Rejected
```

Should be:
```python
# States: 0=None, 1=Open, 2=Filled, 3=Cancelled, 4=Expired, 5=Rejected, 6=Pending
```

## What Was Fixed

### 1. Updated /src/api/enums.py

**Fixed TopstepXOrderState enum**:
```python
class TopstepXOrderState(IntEnum):
    """Order states as received from TopstepX API.

    Based on official OrderStatus enum from TopstepX Gateway API documentation.
    Source: projectx_gateway_api/realtime_updates/realtime_data_overview.md
    """
    NONE = 0        # No status / Unknown
    OPEN = 1        # Order is working on exchange (active)
    FILLED = 2      # Order completely filled
    CANCELLED = 3   # Order cancelled by user or system
    EXPIRED = 4     # Order expired
    REJECTED = 5    # Order rejected by exchange
    PENDING = 6     # Order submitted but not yet working
```

**Updated conversion functions**:
- `api_to_internal_order_state()` - Maps API states to internal states correctly
- `internal_to_api_order_state()` - Reverse mapping updated
- Added new helper functions for clarity

**Updated state checking**:
- Terminal states: FILLED, CANCELLED, REJECTED, EXPIRED (values 2, 3, 5, 4)
- Active states: OPEN, PENDING (values 1, 6)

### 2. Updated /docs/contracts/api_contracts.json

**Confirmed CORRECT** (no changes needed):
The api_contracts.json already had the correct OrderStatus enum mapping matching the official API documentation.

### 3. Updated state_manager.py

**Fixed comment on line 76** and **updated terminal state check** (line 77):
```python
# States: 0=None, 1=Open, 2=Filled, 3=Cancelled, 4=Expired, 5=Rejected, 6=Pending
if order.get('status') in [2, 3, 4, 5]:  # FILLED, CANCELLED, EXPIRED, REJECTED
```

Changed from checking `state` field with values [3, 4, 5] to checking `status` field with correct terminal values [2, 3, 4, 5].

### 4. Updated tests if needed

Test file `/tests/unit/api/test_converters.py` was already using `APIOrderStatus` enum correctly, so tests should pass after fixes.

## Mapping Between API and Internal States

| TopstepX API (status field) | Internal State | Notes |
|----------------------------|----------------|-------|
| 0 = None | PENDING | Map unknown to pending |
| 1 = Open | ACTIVE | Order working on exchange |
| 2 = Filled | FILLED | Terminal state |
| 3 = Cancelled | CANCELLED | Terminal state |
| 4 = Expired | EXPIRED | Terminal state |
| 5 = Rejected | REJECTED | Terminal state |
| 6 = Pending | PENDING | Order submitted, not active yet |

## Test Results

```bash
cd "/home/jakers/projects/simple-risk-manager/simple risk manager"
source venv/bin/activate
python -m pytest tests/unit/api/test_converters.py -v
```

**Result**: ✅ **ALL 25 TESTS PASSED!**

```
tests/unit/api/test_converters.py::TestTimestampParsing::test_parse_iso8601_with_timezone PASSED [  4%]
tests/unit/api/test_converters.py::TestTimestampParsing::test_parse_iso8601_with_z_suffix PASSED [  8%]
tests/unit/api/test_converters.py::TestTimestampParsing::test_parse_none_timestamp PASSED [ 12%]
tests/unit/api/test_converters.py::TestTimestampParsing::test_parse_invalid_timestamp PASSED [ 16%]
tests/unit/api/test_converters.py::TestAccountConverter::test_convert_complete_account PASSED [ 20%]
tests/unit/api/test_converters.py::TestAccountConverter::test_convert_minimal_account PASSED [ 24%]
tests/unit/api/test_converters.py::TestOrderConverter::test_convert_complete_order PASSED [ 28%]
tests/unit/api/test_converters.py::TestOrderConverter::test_convert_filled_order PASSED [ 32%]
tests/unit/api/test_converters.py::TestOrderConverter::test_convert_order_with_orderId_field PASSED [ 36%]
tests/unit/api/test_converters.py::TestPositionConverter::test_convert_long_position PASSED [ 40%]
tests/unit/api/test_converters.py::TestPositionConverter::test_convert_short_position PASSED [ 44%]
tests/unit/api/test_converters.py::TestPositionConverter::test_convert_position_old_api_format PASSED [ 48%]
tests/unit/api/test_converters.py::TestPositionConverter::test_convert_position_old_api_short PASSED [ 52%]
tests/unit/api/test_converters.py::TestTradeConverter::test_convert_complete_trade PASSED [ 56%]
tests/unit/api/test_converters.py::TestTradeConverter::test_convert_half_turn_trade PASSED [ 60%]
tests/unit/api/test_converters.py::TestContractConverter::test_convert_complete_contract PASSED [ 64%]
tests/unit/api/test_converters.py::TestContractConverter::test_convert_contract_old_api_format PASSED [ 68%]
tests/unit/api/test_converters.py::TestQuoteConverter::test_convert_complete_quote PASSED [ 72%]
tests/unit/api/test_converters.py::TestReverseConverters::test_internal_to_api_order_request PASSED [ 76%]
tests/unit/api/test_converters.py::TestReverseConverters::test_internal_to_api_order_modify_request PASSED [ 80%]
tests/unit/api/test_converters.py::TestReverseConverters::test_internal_to_api_order_cancel_request PASSED [ 84%]
tests/unit/api/test_converters.py::TestReverseConverters::test_internal_to_api_position_close_request PASSED [ 88%]
tests/unit/api/test_converters.py::TestEdgeCases::test_order_with_missing_optional_fields PASSED [ 92%]
tests/unit/api/test_converters.py::TestEdgeCases::test_position_with_no_type_or_side PASSED [ 96%]
tests/unit/api/test_converters.py::TestEdgeCases::test_quote_with_minimal_data PASSED [100%]

============================== 25 passed in 1.69s ==============================
```

**Test Execution Date**: 2025-10-23 00:56:06
**Status**: All converter tests passing with corrected enum mappings

## Confidence Level

**HIGH** - Based on:
1. Official API documentation with C# enum definition
2. Actual API response examples showing status values
3. SignalR event payload examples
4. Consistent evidence across multiple documentation files

## Root Cause Analysis

The confusion arose because:
1. Someone wrote an incorrect comment in `state_manager.py` line 76
2. The `enums.py` file was created based on that incorrect comment rather than the official API docs
3. The field name confusion: API uses `status` (not `state`) with OrderStatus enum values

## Recommendations

1. ✅ Always refer to official API documentation for enum values
2. ✅ Use actual API response examples to verify mappings
3. ✅ Comments in code should reference authoritative sources
4. ✅ Field names matter: `status` vs `state` are different fields
5. ✅ Keep api_contracts.json synchronized with official API specs

## Related Files Updated

1. `/src/api/enums.py` - Fixed TopstepXOrderState enum and conversions
2. `/src/core/state_manager.py` - Fixed comment and terminal state check
3. `/docs/contracts/api_contracts.json` - Verified correct (no changes needed)
4. `/docs/contracts/ORDER_STATE_RESOLUTION.md` - This documentation file

---

**Resolution Date**: 2025-10-23
**Verified By**: Comprehensive analysis of official API documentation and code
