# Test Fixtures Reference Guide

## Overview

This document describes all test fixtures used in the Simple Risk Manager project. Understanding the difference between API response fixtures and internal format fixtures is crucial for writing correct tests.

## Fixture Types

### 1. API Response Fixtures (camelCase)
**Purpose**: Mock actual TopstepX Gateway API responses
**Naming Convention**: `<entity>_<scenario>_api`
**Field Format**: camelCase (e.g., `accountId`, `contractId`, `createdAt`)
**Use When**: Testing API clients, parsers, or data converters

### 2. Internal Format Fixtures (snake_case)
**Purpose**: Mock internal data structures after conversion
**Naming Convention**: `<entity>_<scenario>` (no suffix)
**Field Format**: snake_case (e.g., `account_id`, `contract_id`, `created_at`)
**Use When**: Testing core business logic, risk rules, or internal components

---

## Positions Fixtures

### API Response Format (camelCase)

Located in: `/tests/fixtures/positions.py`

#### `single_es_long_position_api()`
```python
{
    "id": 12345,
    "accountId": 123,
    "contractId": "CON.F.US.ES.H25",
    "type": 1,  # LONG
    "size": 1,
    "averagePrice": 4500.00,
    "createdAt": "2025-01-17T14:30:00Z",
    "updatedAt": "2025-01-17T14:30:00Z"
}
```

#### `single_nq_short_position_api()`
```python
{
    "id": 12346,
    "accountId": 123,
    "contractId": "CON.F.US.NQ.H25",
    "type": 2,  # SHORT
    "size": 1,
    "averagePrice": 16000.00,
    "createdAt": "2025-01-17T14:35:00Z",
    "updatedAt": "2025-01-17T14:35:00Z"
}
```

#### `two_open_positions_mixed_api()`
Returns list of two positions (ES long, NQ short) in API format.

### Internal Format (snake_case)

#### `single_es_long_position()`
Same data as API version, but with snake_case field names:
- `accountId` → `account_id`
- `contractId` → `contract_id`
- `averagePrice` → `average_price`
- `createdAt` → `created_at`
- `updatedAt` → `updated_at`

#### Other Position Fixtures (Internal Format)
- `single_nq_short_position()` - Single NQ short position
- `two_open_positions_mixed()` - Two positions mixed
- `three_mnq_long_positions()` - Three MNQ positions
- `max_contracts_breach_positions()` - 6 contracts (breaches limit)
- `position_with_unrealized_loss()` - Position with loss
- `position_with_unrealized_profit()` - Position with profit
- `position_at_breakeven()` - Position at breakeven
- `position_without_stop_loss()` - No stop-loss protection
- `position_in_blocked_symbol()` - RTY position (blocked)
- `empty_positions_list()` - Empty list
- `large_position_size()` - 10 contracts
- `hedged_positions()` - Offsetting positions

---

## Orders Fixtures

### API Response Format (camelCase)

Located in: `/tests/fixtures/orders.py`

#### `order_stop_loss_working_api()`
```python
{
    "id": 78901,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "type": 4,  # STOP
    "side": 1,  # BUY
    "size": 3,
    "stopPrice": 20950.00,
    "state": 2,  # ACTIVE
    "createdAt": "2025-01-17T14:30:05Z",
    "updatedAt": "2025-01-17T14:30:05Z"
}
```

#### `order_limit_working_api()`
```python
{
    "id": 78902,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "type": 2,  # LIMIT
    "side": 1,  # BUY
    "size": 2,
    "limitPrice": 21000.00,
    "state": 2,  # ACTIVE
    "createdAt": "2025-01-17T14:30:00Z",
    "updatedAt": "2025-01-17T14:30:00Z"
}
```

### Internal Format (snake_case)

#### `order_stop_loss_working()`
Stop-loss order in internal format (snake_case fields)

#### Other Order Fixtures (Internal Format)
- `order_limit_working()` - Working limit order
- `order_market_pending()` - Pending market order
- `order_filled()` - Filled order
- `order_canceled()` - Canceled order
- `order_partial_fill()` - Partially filled
- `order_rejected()` - Rejected order
- `order_stop_loss_for_position()` - Stop-loss with position link
- `orders_multiple_working()` - Multiple working orders
- `order_blocked_symbol()` - Order in blocked symbol
- `empty_orders_list()` - Empty list

---

## Trades Fixtures

### API Response Format (camelCase)

Located in: `/tests/fixtures/trades.py`

#### `trade_single_profit_api()`
```python
{
    "id": 10001,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "quantity": 2,
    "profitAndLoss": 45.50,
    "executionTime": "2025-01-17T14:45:15Z",
    "entryPrice": 21000.50,
    "exitPrice": 21023.00
}
```

#### `trade_single_loss_api()`
```python
{
    "id": 10002,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "quantity": 3,
    "profitAndLoss": -120.00,
    "executionTime": "2025-01-17T15:00:00Z",
    "entryPrice": 21000.00,
    "exitPrice": 20980.00
}
```

### Internal Format (snake_case)

#### Other Trade Fixtures (Internal Format)
- `trade_single_profit()` - Single profit (+$45.50)
- `trade_single_loss()` - Single loss (-$120.00)
- `trade_large_loss_breach()` - Large loss (-$550.00)
- `trade_cooldown_trigger()` - Loss triggering cooldown
- `trades_sequence_losses()` - 3 losing trades
- `trades_high_frequency()` - 35 trades (breach limit)
- `trades_within_frequency_limit()` - 25 trades (within limit)
- `trades_mixed_pnl()` - Mixed profitable/losing trades
- `trade_breakeven()` - $0 P&L
- `empty_trades_list()` - Empty list

---

## Account Fixtures

### API Response Format (camelCase)

Located in: `/tests/fixtures/accounts.py`

#### `account_details_api()`
```python
{
    "id": 123,
    "username": "test_trader@example.com",
    "status": "Active",
    "balance": 50000.00,
    "equity": 50150.50,
    "marginUsed": 5000.00,
    "marginAvailable": 45150.50,
    "buyingPower": 50000.00,
    "unrealizedProfitLoss": 150.50
}
```

#### `account_suspended_api()`
```python
{
    "id": 123,
    "username": "suspended@example.com",
    "status": "Suspended",
    "balance": 48500.00,
    "equity": 48500.00,
    "marginUsed": 0.00,
    "marginAvailable": 0.00,
    "suspensionReason": "Exceeded daily loss limit",
    "suspendedAt": "2025-01-17T14:50:00Z",
    "suspendedUntil": "2025-01-17T17:00:00Z"
}
```

### Internal Config Format (snake_case)

These represent local configuration, not API responses:

- `account_test_primary()` - Primary test account config
- `account_test_secondary()` - Secondary test account config
- `account_disabled()` - Disabled account
- `account_without_api_key()` - Missing API key
- `accounts_multiple()` - Multiple accounts
- `account_config_minimal()` - Minimal config
- `account_config_full()` - Full config with all fields
- `account_suspended_status()` - Suspended status
- `account_active_status()` - Active status

---

## API Response Fixtures (HTTP Responses)

Located in: `/tests/fixtures/api_responses.py`

These fixtures mock complete HTTP responses from TopstepX API, including success and error responses.

### Authentication
- `auth_success_response()` - JWT token response
- `auth_failure_response()` - Invalid credentials
- `auth_expired_token_response()` - Expired token

### Positions
- `positions_open_response()` - GET /api/positions (2 positions)
- `positions_empty_response()` - Empty positions list
- `position_close_success_response()` - Close position success
- `position_partial_close_response()` - Partial close
- `position_not_found_response()` - 404 error

### Orders
- `orders_open_response()` - GET /api/orders (1 order)
- `orders_empty_response()` - Empty orders list
- `order_cancel_success_response()` - Cancel success
- `order_place_success_response()` - Place order success
- `order_rejected_response()` - Order rejected
- `order_not_found_response()` - 404 error

### Contracts
- `contract_mnq_response()` - MNQ contract details
- `contract_es_response()` - ES contract details
- `contract_nq_response()` - NQ contract details
- `contracts_list_response()` - List of contracts
- `contract_not_found_response()` - 404 error

### Accounts
- `account_details_response()` - Account details
- `account_suspended_response()` - Suspended account

### Error Responses
- `rate_limit_error_response()` - HTTP 429
- `server_error_response()` - HTTP 500
- `bad_request_response()` - HTTP 400
- `timeout_error_response()` - Request timeout
- `network_error_response()` - Network error

---

## Usage Examples

### Testing API Client (Use API Format)

```python
def test_parse_position_response(positions_open_response):
    """Test parsing API response"""
    from src.api.rest_client import parse_positions

    positions = parse_positions(positions_open_response)

    # After parsing, should be in internal format
    assert positions[0]["account_id"] == 123
    assert positions[0]["contract_id"] == "CON.F.US.MNQ.U25"
```

### Testing Data Converter (Use Both Formats)

```python
def test_api_to_internal_conversion(single_es_long_position_api):
    """Test converting API format to internal format"""
    from src.api.converters import api_to_internal_position

    internal = api_to_internal_position(single_es_long_position_api)

    # Verify conversion
    assert internal["account_id"] == single_es_long_position_api["accountId"]
    assert internal["average_price"] == single_es_long_position_api["averagePrice"]
```

### Testing Core Logic (Use Internal Format)

```python
def test_max_contracts_rule(two_open_positions_mixed):
    """Test max contracts rule with internal format"""
    from src.rules.max_contracts import MaxContractsRule

    rule = MaxContractsRule(max_contracts=5)
    result = rule.evaluate(positions=two_open_positions_mixed)

    assert result.compliant is True
    assert result.total_contracts == 3
```

---

## Field Name Mapping Reference

### Common Field Mappings

| API Format (camelCase) | Internal Format (snake_case) |
|------------------------|------------------------------|
| `accountId` | `account_id` |
| `contractId` | `contract_id` |
| `averagePrice` | `average_price` |
| `stopPrice` | `stop_price` |
| `limitPrice` | `limit_price` |
| `createdAt` | `created_at` |
| `updatedAt` | `updated_at` |
| `profitAndLoss` | `profit_and_loss` |
| `executionTime` | `execution_time` |
| `entryPrice` | `entry_price` |
| `exitPrice` | `exit_price` |
| `marginUsed` | `margin_used` |
| `marginAvailable` | `margin_available` |
| `buyingPower` | `buying_power` |
| `unrealizedProfitLoss` | `unrealized_pnl` |
| `suspendedAt` | `suspended_at` |
| `suspendedUntil` | `suspended_until` |
| `suspensionReason` | `suspension_reason` |

---

## Best Practices

1. **Always use API fixtures when testing API integration**
   - Use fixtures ending with `_api`
   - These should match actual TopstepX API responses exactly

2. **Use internal fixtures for business logic tests**
   - Use fixtures without `_api` suffix
   - These are already in the format your core logic expects

3. **Test converters with both formats**
   - Input: API format fixture (`*_api`)
   - Output: Validate against internal format

4. **Maintain consistency**
   - When adding new fixtures, create both API and internal versions
   - Follow naming conventions: `<entity>_<scenario>_api` and `<entity>_<scenario>`

5. **Document field mapping**
   - If you add new fields, update the mapping table above
   - Ensure converters handle all fields correctly

---

## Related Files

- `/tests/fixtures/positions.py` - Position fixtures
- `/tests/fixtures/orders.py` - Order fixtures
- `/tests/fixtures/trades.py` - Trade fixtures
- `/tests/fixtures/accounts.py` - Account fixtures
- `/tests/fixtures/api_responses.py` - Complete HTTP response fixtures
- `/tests/conftest.py` - Shared test configuration
- `/src/api/converters.py` - API to internal format converters (if exists)

---

**Last Updated**: 2025-10-23
**Maintained By**: Contract Fixing Swarm - Test Fixture Updater Agent
