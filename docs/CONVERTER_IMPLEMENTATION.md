# API Data Converter Implementation

**Status:** ✅ COMPLETE
**Created:** 2025-10-23
**Agent:** Converter Builder (Contract Fixing Swarm)

## Overview

This document describes the complete conversion layer that transforms TopstepX API data (camelCase) into internal backend format (snake_case).

## Files Created

### Core Implementation

1. **`/src/api/enums.py`** (305 lines)
   - Extended existing file with additional API enum definitions
   - Contains all enum mappings between API and internal formats
   - Includes conversion functions for order side, position type, and order type

2. **`/src/api/converters.py`** (476 lines)
   - Complete conversion layer for all API data types
   - Handles bidirectional conversion (API ↔ Internal)
   - Includes timestamp parsing and field mapping

3. **`/tests/unit/api/test_converters.py`** (500 lines)
   - Comprehensive unit tests for all converter functions
   - Tests edge cases and error handling
   - Validates both API→Internal and Internal→API conversions

## API Enums Defined

### Order Type (APIOrderType)
```python
UNKNOWN = 0
LIMIT = 1
MARKET = 2
STOP_LIMIT = 3
STOP = 4
TRAILING_STOP = 5
JOIN_BID = 6
JOIN_ASK = 7
```

### Order Side (APIOrderSide)
```python
BID = 0  # Buy
ASK = 1  # Sell
```

### Order Status (APIOrderStatus)
```python
NONE = 0
OPEN = 1
FILLED = 2
CANCELLED = 3
EXPIRED = 4
REJECTED = 5
PENDING = 6
```

### Position Type (APIPositionType)
```python
UNDEFINED = 0
LONG = 1
SHORT = 2
```

## Converter Functions

### API → Internal Converters

#### 1. `api_to_internal_account(api_data)`
Converts TopstepX account data to internal format.

**API Fields (camelCase):**
- `id`, `name`, `balance`, `canTrade`, `isVisible`, `simulated`

**Internal Fields (snake_case):**
- `account_id`, `name`, `balance`, `can_trade`, `is_visible`, `simulated`

#### 2. `api_to_internal_order(api_data)`
Converts TopstepX order data to internal format.

**API Fields:**
- `id/orderId`, `accountId`, `contractId`, `symbolId`
- `creationTimestamp`, `updateTimestamp`
- `status`, `type`, `side`, `size`
- `limitPrice`, `stopPrice`, `fillVolume`, `filledPrice`, `customTag`

**Internal Fields:**
- `order_id`, `account_id`, `contract_id`, `symbol_id`
- `creation_timestamp`, `update_timestamp`
- `state` (InternalOrderState enum), `order_type`, `side` (buy/sell), `quantity`
- `limit_price`, `stop_price`, `filled_quantity`, `filled_price`, `custom_tag`

**Special Handling:**
- Handles both `status` (0-6) and `state` (1-5) fields from different API endpoints
- Converts OrderStatus to InternalOrderState enum
- Maps order side: 0=Buy, 1=Sell → "buy"/"sell"

#### 3. `api_to_internal_position(api_data)`
Converts TopstepX position data to internal format.

**API Fields:**
- `id`, `accountId`, `contractId`, `creationTimestamp`
- `type`, `size`, `averagePrice`
- Legacy: `side`, `quantity`, `avgPrice`, `unrealizedPnl`

**Internal Fields:**
- `position_id`, `account_id`, `contract_id`, `creation_timestamp`
- `position_type` (long/short), `quantity`, `average_price`, `unrealized_pnl`

**Special Handling:**
- Supports both new API format (`type`/`size`) and old format (`side`/`quantity`)
- Maps position type: 1=Long, 2=Short → "long"/"short"

#### 4. `api_to_internal_trade(api_data)`
Converts TopstepX trade data to internal format.

**API Fields:**
- `id`, `accountId`, `contractId`, `creationTimestamp`
- `price`, `profitAndLoss`, `fees`, `side`, `size`, `voided`, `orderId`

**Internal Fields:**
- `trade_id`, `order_id`, `account_id`, `contract_id`
- `quantity`, `price`, `execution_time`, `side`, `fees`, `profit_and_loss`, `voided`

**Special Handling:**
- `profitAndLoss` is `null` for half-turn trades (opening position)

#### 5. `api_to_internal_contract(api_data)`
Converts TopstepX contract metadata to internal format.

**API Fields:**
- `id`, `name`, `description`, `tickSize`, `tickValue`
- `activeContract`, `symbolId`, `exchange`, `contractSize`

**Internal Fields:**
- `contract_id`, `name`, `symbol`, `description`, `tick_size`, `tick_value`
- `active_contract`, `exchange`, `contract_size`

#### 6. `api_to_internal_quote(api_data)`
Converts TopstepX market quote data to internal format.

**API Fields:**
- `symbol`, `symbolName`, `lastPrice`, `bestBid`, `bestAsk`
- `change`, `changePercent`, `open`, `high`, `low`, `volume`
- `lastUpdated`, `timestamp`

**Internal Fields:**
- All fields converted to snake_case equivalents

### Internal → API Converters

#### 1. `internal_to_api_order_request(internal_data)`
Converts internal order format to TopstepX API request format for placing orders.

**Maps:**
- `account_id` → `accountId`
- `contract_id` → `contractId`
- `order_type` → `type` (int enum)
- `side` → `side` (0/1)
- `quantity` → `size`
- `limit_price` → `limitPrice`
- `stop_price` → `stopPrice`
- `trail_price` → `trailPrice`
- `custom_tag` → `customTag`

#### 2. `internal_to_api_order_modify_request(internal_data)`
Converts internal order modify format to API request.

#### 3. `internal_to_api_order_cancel_request(internal_data)`
Converts internal order cancel format to API request.

#### 4. `internal_to_api_position_close_request(internal_data)`
Converts internal position close format to API request.

## Timestamp Handling

The `_parse_timestamp()` function handles multiple timestamp formats:

- ISO 8601 with timezone: `"2025-07-18T21:00:01.268009+00:00"`
- ISO 8601 with Z suffix: `"2025-01-20T15:47:39.882Z"`
- Returns `None` for invalid/missing timestamps (graceful degradation)

## Enum Conversion Functions

### `api_to_internal_order_side(api_side: int) -> str`
- `0` (BID) → `"buy"`
- `1` (ASK) → `"sell"`

### `api_to_internal_order_state(api_state: int) -> InternalOrderState`
- Uses existing TopstepX state conversion (1-5 → PENDING/ACTIVE/FILLED/CANCELLED/REJECTED)

### `api_to_internal_position_type(api_type: int) -> str`
- `1` (LONG) → `"long"`
- `2` (SHORT) → `"short"`

### `internal_to_api_order_side(internal_side: str) -> int`
- `"buy"` → `0` (BID)
- `"sell"` → `1` (ASK)

### `internal_to_api_order_type(order_type_str: str) -> int`
- `"market"` → `2` (MARKET)
- `"limit"` → `1` (LIMIT)
- `"stop"` → `4` (STOP)
- `"stop_limit"` → `3` (STOP_LIMIT)
- `"trailing_stop"` → `5` (TRAILING_STOP)

## Field Mapping Reference

### Common Patterns

| API Field (camelCase) | Internal Field (snake_case) |
|----------------------|----------------------------|
| `accountId` | `account_id` |
| `contractId` | `contract_id` |
| `orderId` | `order_id` |
| `symbolId` | `symbol_id` |
| `creationTimestamp` | `creation_timestamp` |
| `updateTimestamp` | `update_timestamp` |
| `limitPrice` | `limit_price` |
| `stopPrice` | `stop_price` |
| `trailPrice` | `trail_price` |
| `fillVolume` | `filled_quantity` |
| `filledPrice` | `filled_price` |
| `averagePrice` | `average_price` |
| `unrealizedProfitLoss` | `unrealized_pnl` |
| `realizedProfitLoss` | `realized_pnl` |
| `profitAndLoss` | `profit_and_loss` |
| `customTag` | `custom_tag` |
| `canTrade` | `can_trade` |
| `isVisible` | `is_visible` |
| `activeContract` | `active_contract` |
| `tickSize` | `tick_size` |
| `tickValue` | `tick_value` |
| `contractSize` | `contract_size` |
| `bestBid` | `best_bid` |
| `bestAsk` | `best_ask` |
| `lastPrice` | `last_price` |
| `lastUpdated` | `last_updated` |

### Special Cases

| API Field | Internal Field | Notes |
|-----------|----------------|-------|
| `size` | `quantity` | Position/order quantity |
| `status` | `state` | Order status (0-6) → InternalOrderState enum |
| `side` | `side` | 0/1 → "buy"/"sell" |
| `type` | `position_type` | Position: 1/2 → "long"/"short" |
| `type` | `order_type` | Order: kept as int enum |
| `id` | `{entity}_id` | Different entities use different suffixes |

## Usage Examples

### Converting API Order to Internal Format

```python
from src.api.converters import api_to_internal_order

# API response from TopstepX
api_order = {
    "id": 26974,
    "accountId": 465,
    "contractId": "CON.F.US.ENQ.H25",
    "status": 1,  # OPEN
    "side": 0,    # BID (Buy)
    "size": 2,
    "stopPrice": 5000.00,
}

# Convert to internal format
internal_order = api_to_internal_order(api_order)

# Result:
# {
#     "order_id": 26974,
#     "account_id": 465,
#     "contract_id": "CON.F.US.ENQ.H25",
#     "state": <InternalOrderState.ACTIVE: 2>,
#     "side": "buy",
#     "quantity": 2,
#     "stop_price": 5000.00,
#     ...
# }
```

### Placing an Order via API

```python
from src.api.converters import internal_to_api_order_request

# Internal order representation
internal_order = {
    "account_id": 465,
    "contract_id": "CON.F.US.ENQ.H25",
    "order_type": "stop",
    "side": "buy",
    "quantity": 1,
    "stop_price": 5000.00,
}

# Convert to API request format
api_request = internal_to_api_order_request(internal_order)

# Result:
# {
#     "accountId": 465,
#     "contractId": "CON.F.US.ENQ.H25",
#     "type": 4,  # STOP
#     "side": 0,  # BID
#     "size": 1,
#     "stopPrice": 5000.00,
#     ...
# }

# Send to API
response = rest_client._make_authenticated_request('POST', '/api/Order/place', api_request)
```

## Testing

All converter functions have comprehensive unit tests covering:

1. **Complete data conversion** - All fields mapped correctly
2. **Minimal data conversion** - Defaults applied appropriately
3. **Edge cases** - Missing fields, null values, invalid data
4. **Timestamp parsing** - Multiple formats, invalid timestamps
5. **Enum conversions** - All enum values mapped correctly
6. **Backward compatibility** - Old and new API formats supported

Run tests with:
```bash
python3 -m pytest tests/unit/api/test_converters.py -v
```

## Integration Points

The converter layer integrates with:

1. **REST Client** (`src/api/rest_client.py`)
   - Wraps API responses with converters
   - Sends requests using reverse converters

2. **SignalR Client** (when implemented)
   - Converts real-time event payloads
   - Normalizes GatewayUser* events

3. **State Manager** (`src/core/state_manager.py`)
   - Receives normalized internal format
   - No longer needs to handle camelCase

4. **Risk Rules** (`src/rules/`)
   - Works with consistent snake_case format
   - Type-safe with enum values

## Design Decisions

1. **Single Source of Truth:** All field mappings in one file
2. **Type Safety:** Use enums for states, not magic strings/numbers
3. **Graceful Degradation:** Return None/defaults instead of raising on missing fields
4. **Backward Compatibility:** Support both old and new API field names
5. **Bidirectional:** Convert both directions (API ↔ Internal)
6. **Comprehensive:** Cover all API data types, not just positions/orders

## References

- TopstepX Gateway API Documentation
- `/project-specs/SPECS/01-API-INTEGRATION/topstepx_integration.md`
- `/reports/2025-10-22-spec-governance/02-analysis/API_ALIGNMENT_REPORT.md`
- `/src/api/rest_client.py` (existing implementation patterns)

## Status

✅ **COMPLETE AND TESTED**

All converter functions implemented, documented, and ready for integration.
