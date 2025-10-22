# Test Fixtures Plan - Simple Risk Manager

**Generated:** 2025-10-22
**Purpose:** Mock data requirements for all test scenarios
**Version:** 1.0
**Status:** Implementation Ready

---

## Table of Contents

1. [Fixture Categories](#fixture-categories)
2. [API Response Mocks](#api-response-mocks)
3. [SignalR Event Mocks](#signalr-event-mocks)
4. [Database Fixtures](#database-fixtures)
5. [Configuration Fixtures](#configuration-fixtures)
6. [Fixture Management](#fixture-management)

---

# Fixture Categories

## Overview

All test fixtures are organized into 5 categories:

1. **API Response Mocks** - TopstepX REST API responses
2. **SignalR Event Mocks** - WebSocket event payloads
3. **Database Fixtures** - Sample SQLite data
4. **Configuration Fixtures** - Test configurations (YAML)
5. **State Object Fixtures** - Python dataclass instances

---

# API Response Mocks

## 1. Authentication Responses

### 1.1 Successful Authentication

**File:** `tests/fixtures/api/auth_success.json`

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE3MDYzMzkwMjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
  "expiresIn": 86400,
  "tokenType": "Bearer"
}
```

### 1.2 Failed Authentication

**File:** `tests/fixtures/api/auth_failure.json`

```json
{
  "error": "Unauthorized",
  "message": "Invalid API key or username",
  "statusCode": 401
}
```

---

## 2. Position API Responses

### 2.1 Search Open Positions

**File:** `tests/fixtures/api/positions_open.json`

```json
[
  {
    "id": 12345,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "type": 1,
    "size": 3,
    "averagePrice": 21000.50,
    "createdAt": "2025-01-17T14:30:00Z",
    "updatedAt": "2025-01-17T14:45:15Z"
  },
  {
    "id": 12346,
    "accountId": 123,
    "contractId": "CON.F.US.ES.H25",
    "type": 2,
    "size": 1,
    "averagePrice": 5000.25,
    "createdAt": "2025-01-17T14:35:00Z",
    "updatedAt": "2025-01-17T14:35:00Z"
  }
]
```

### 2.2 Close Position Success

**File:** `tests/fixtures/api/position_close_success.json`

```json
{
  "success": true,
  "message": "Position closed successfully",
  "positionId": 12345,
  "closedAt": "2025-01-17T14:50:00Z",
  "exitPrice": 21002.25
}
```

### 2.3 Partial Close Position

**File:** `tests/fixtures/api/position_partial_close.json`

```json
{
  "success": true,
  "message": "Position partially closed",
  "positionId": 12345,
  "originalSize": 5,
  "closedSize": 2,
  "remainingSize": 3,
  "exitPrice": 21002.00
}
```

---

## 3. Order API Responses

### 3.1 Search Open Orders

**File:** `tests/fixtures/api/orders_open.json`

```json
[
  {
    "id": 78901,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "type": 4,
    "side": 1,
    "size": 3,
    "stopPrice": 20950.00,
    "state": 2,
    "createdAt": "2025-01-17T14:30:05Z",
    "updatedAt": "2025-01-17T14:30:05Z"
  }
]
```

### 3.2 Cancel Order Success

**File:** `tests/fixtures/api/order_cancel_success.json`

```json
{
  "success": true,
  "message": "Order canceled successfully",
  "orderId": 78901,
  "canceledAt": "2025-01-17T14:50:00Z"
}
```

### 3.3 Place Order Success

**File:** `tests/fixtures/api/order_place_success.json`

```json
{
  "success": true,
  "message": "Order placed successfully",
  "orderId": 78902,
  "contractId": "CON.F.US.MNQ.U25",
  "type": 4,
  "side": 1,
  "size": 3,
  "stopPrice": 20990.00,
  "state": 2,
  "createdAt": "2025-01-17T14:55:00Z"
}
```

---

## 4. Contract API Responses

### 4.1 Search Contract by ID

**File:** `tests/fixtures/api/contract_mnq.json`

```json
{
  "id": "CON.F.US.MNQ.U25",
  "symbolId": "MNQ",
  "name": "Micro E-mini Nasdaq-100 Jun 2025",
  "exchange": "CME",
  "tickSize": 0.25,
  "tickValue": 0.50,
  "pointValue": 2.00,
  "expiration": "2025-06-20",
  "currency": "USD"
}
```

### 4.2 List Available Contracts

**File:** `tests/fixtures/api/contracts_list.json`

```json
[
  {
    "id": "CON.F.US.MNQ.U25",
    "symbolId": "MNQ",
    "name": "Micro E-mini Nasdaq-100 Jun 2025",
    "tickSize": 0.25,
    "tickValue": 0.50
  },
  {
    "id": "CON.F.US.ES.H25",
    "symbolId": "ES",
    "name": "E-mini S&P 500 Mar 2025",
    "tickSize": 0.25,
    "tickValue": 12.50
  },
  {
    "id": "CON.F.US.NQ.H25",
    "symbolId": "NQ",
    "name": "E-mini Nasdaq-100 Mar 2025",
    "tickSize": 0.25,
    "tickValue": 5.00
  }
]
```

---

## 5. Account API Responses

### 5.1 Search Account

**File:** `tests/fixtures/api/account_details.json`

```json
{
  "id": 123,
  "username": "trader@example.com",
  "status": "Active",
  "balance": 50000.00,
  "equity": 50150.50,
  "marginUsed": 5000.00,
  "marginAvailable": 45150.50
}
```

---

## 6. API Error Responses

### 6.1 Rate Limit Error

**File:** `tests/fixtures/api/error_rate_limit.json`

```json
{
  "error": "TooManyRequests",
  "message": "Rate limit exceeded. Maximum 20 requests per second.",
  "statusCode": 429,
  "retryAfter": 1
}
```

### 6.2 Server Error

**File:** `tests/fixtures/api/error_server.json`

```json
{
  "error": "InternalServerError",
  "message": "An unexpected error occurred",
  "statusCode": 500
}
```

### 6.3 Not Found Error

**File:** `tests/fixtures/api/error_not_found.json`

```json
{
  "error": "NotFound",
  "message": "Position not found",
  "statusCode": 404
}
```

---

# SignalR Event Mocks

## 1. GatewayUserTrade Events

### 1.1 Profitable Trade

**File:** `tests/fixtures/signalr/trade_profit.json`

```json
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

### 1.2 Loss Trade

**File:** `tests/fixtures/signalr/trade_loss.json`

```json
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

### 1.3 Breakeven Trade

**File:** `tests/fixtures/signalr/trade_breakeven.json`

```json
{
  "id": 10003,
  "accountId": 123,
  "contractId": "CON.F.US.ES.H25",
  "quantity": 1,
  "profitAndLoss": 0.00,
  "executionTime": "2025-01-17T15:10:00Z",
  "entryPrice": 5000.00,
  "exitPrice": 5000.00
}
```

---

## 2. GatewayUserPosition Events

### 2.1 Position Opened

**File:** `tests/fixtures/signalr/position_opened.json`

```json
{
  "id": 12347,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "type": 1,
  "size": 3,
  "averagePrice": 21000.50,
  "createdAt": "2025-01-17T14:30:00Z",
  "updatedAt": "2025-01-17T14:30:00Z"
}
```

### 2.2 Position Updated (Scaled In)

**File:** `tests/fixtures/signalr/position_scaled.json`

```json
{
  "id": 12347,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "type": 1,
  "size": 5,
  "averagePrice": 21001.00,
  "createdAt": "2025-01-17T14:30:00Z",
  "updatedAt": "2025-01-17T14:35:00Z"
}
```

### 2.3 Position Closed

**File:** `tests/fixtures/signalr/position_closed.json`

```json
{
  "id": 12347,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "type": 1,
  "size": 0,
  "averagePrice": 21000.50,
  "createdAt": "2025-01-17T14:30:00Z",
  "updatedAt": "2025-01-17T14:50:00Z"
}
```

---

## 3. GatewayUserOrder Events

### 3.1 Order Placed

**File:** `tests/fixtures/signalr/order_placed.json`

```json
{
  "id": 78903,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "type": 2,
  "side": 1,
  "size": 3,
  "limitPrice": 21000.00,
  "state": 2,
  "createdAt": "2025-01-17T14:30:00Z",
  "updatedAt": "2025-01-17T14:30:00Z"
}
```

### 3.2 Order Filled

**File:** `tests/fixtures/signalr/order_filled.json`

```json
{
  "id": 78903,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "type": 2,
  "side": 1,
  "size": 3,
  "limitPrice": 21000.00,
  "fillPrice": 21000.25,
  "filledSize": 3,
  "state": 3,
  "createdAt": "2025-01-17T14:30:00Z",
  "updatedAt": "2025-01-17T14:31:00Z"
}
```

### 3.3 Order Canceled

**File:** `tests/fixtures/signalr/order_canceled.json`

```json
{
  "id": 78903,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "type": 2,
  "side": 1,
  "size": 3,
  "limitPrice": 21000.00,
  "state": 4,
  "createdAt": "2025-01-17T14:30:00Z",
  "updatedAt": "2025-01-17T14:35:00Z"
}
```

### 3.4 Stop-Loss Order Placed

**File:** `tests/fixtures/signalr/order_stop_loss.json`

```json
{
  "id": 78904,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "type": 4,
  "side": 1,
  "size": 3,
  "stopPrice": 20950.00,
  "state": 2,
  "createdAt": "2025-01-17T14:30:05Z",
  "updatedAt": "2025-01-17T14:30:05Z"
}
```

---

## 4. MarketQuote Events

### 4.1 Real-Time Quote

**File:** `tests/fixtures/signalr/quote_mnq.json`

```json
{
  "contractId": "CON.F.US.MNQ.U25",
  "bid": 21000.25,
  "ask": 21000.50,
  "last": 21000.50,
  "timestamp": "2025-01-17T14:45:15.123Z"
}
```

### 4.2 Quote Price Movement

**File:** `tests/fixtures/signalr/quote_mnq_moved.json`

```json
{
  "contractId": "CON.F.US.MNQ.U25",
  "bid": 20950.00,
  "ask": 20950.25,
  "last": 20950.25,
  "timestamp": "2025-01-17T14:46:00.456Z"
}
```

---

## 5. GatewayUserAccount Events

### 5.1 Account Status Update

**File:** `tests/fixtures/signalr/account_update.json`

```json
{
  "accountId": 123,
  "status": "Active",
  "balance": 50150.50,
  "equity": 50200.25,
  "timestamp": "2025-01-17T14:45:00Z"
}
```

### 5.2 Auth Event (Suspicious)

**File:** `tests/fixtures/signalr/account_auth_event.json`

```json
{
  "accountId": 123,
  "eventType": "Authentication",
  "status": "Successful",
  "ipAddress": "192.168.1.100",
  "timestamp": "2025-01-17T14:30:00Z"
}
```

---

# Database Fixtures

## 1. Lockouts Table

**File:** `tests/fixtures/database/lockouts.sql`

```sql
INSERT INTO lockouts (account_id, is_locked, reason, locked_at, locked_until, rule_id)
VALUES
  (123, 1, 'Daily loss limit: -$550', '2025-01-17 14:45:00', '2025-01-17 17:00:00', 'RULE-003'),
  (456, 0, NULL, NULL, NULL, NULL);
```

---

## 2. Daily PNL Table

**File:** `tests/fixtures/database/daily_pnl.sql`

```sql
INSERT INTO daily_pnl (account_id, date, realized_pnl, last_updated)
VALUES
  (123, '2025-01-17', -350.50, '2025-01-17 14:45:00'),
  (456, '2025-01-17', 120.00, '2025-01-17 14:30:00');
```

---

## 3. Contract Cache Table

**File:** `tests/fixtures/database/contract_cache.sql`

```sql
INSERT INTO contract_cache (contract_id, tick_size, tick_value, symbol_id, name, cached_at)
VALUES
  ('CON.F.US.MNQ.U25', 0.25, 0.50, 'MNQ', 'Micro E-mini Nasdaq-100 Jun 2025', '2025-01-17 08:00:00'),
  ('CON.F.US.ES.H25', 0.25, 12.50, 'ES', 'E-mini S&P 500 Mar 2025', '2025-01-17 08:00:00'),
  ('CON.F.US.NQ.H25', 0.25, 5.00, 'NQ', 'E-mini Nasdaq-100 Mar 2025', '2025-01-17 08:00:00');
```

---

## 4. Trade History Table

**File:** `tests/fixtures/database/trade_history.sql`

```sql
INSERT INTO trade_history (account_id, timestamp, contract_id, pnl)
VALUES
  (123, '2025-01-17 14:00:00', 'CON.F.US.MNQ.U25', -45.50),
  (123, '2025-01-17 14:15:00', 'CON.F.US.MNQ.U25', -60.00),
  (123, '2025-01-17 14:30:00', 'CON.F.US.ES.H25', 30.00),
  (123, '2025-01-17 14:45:00', 'CON.F.US.MNQ.U25', -120.00);
```

---

## 5. Positions Table

**File:** `tests/fixtures/database/positions.sql`

```sql
INSERT INTO positions (id, account_id, contract_id, type, size, average_price, created_at, updated_at)
VALUES
  (12345, 123, 'CON.F.US.MNQ.U25', 1, 3, 21000.50, '2025-01-17 14:30:00', '2025-01-17 14:45:15'),
  (12346, 123, 'CON.F.US.ES.H25', 2, 1, 5000.25, '2025-01-17 14:35:00', '2025-01-17 14:35:00');
```

---

## 6. Orders Table

**File:** `tests/fixtures/database/orders.sql`

```sql
INSERT INTO orders (id, account_id, contract_id, type, side, size, stop_price, state, created_at, updated_at)
VALUES
  (78901, 123, 'CON.F.US.MNQ.U25', 4, 1, 3, 20950.00, 2, '2025-01-17 14:30:05', '2025-01-17 14:30:05');
```

---

## 7. Enforcement Log Table

**File:** `tests/fixtures/database/enforcement_log.sql`

```sql
INSERT INTO enforcement_log (account_id, rule_id, action, reason, success, details, timestamp)
VALUES
  (123, 'RULE-003', 'CLOSE_ALL_AND_LOCKOUT', 'Daily loss limit: -$550', 1, '{"positions_closed": 2, "orders_canceled": 1}', '2025-01-17 14:45:15');
```

---

# Configuration Fixtures

## 1. Test Risk Configuration

**File:** `tests/fixtures/config/risk_config_test.yaml`

```yaml
# Test configuration with all rules enabled
max_contracts:
  enabled: true
  limit: 5
  count_type: "net"
  close_all: true

max_contracts_per_instrument:
  enabled: true
  limits:
    MNQ: 3
    ES: 2
    NQ: 1
  enforcement: "reduce_to_limit"

daily_realized_loss:
  enabled: true
  limit: -500
  reset_time: "17:00"
  timezone: "America/New_York"
  enforcement: "close_all_and_lockout"

daily_unrealized_loss:
  enabled: true
  limit: -500
  enforcement: "close_all_and_lockout"

max_unrealized_profit:
  enabled: true
  limit: 2000
  enforcement: "close_all_and_lockout"

trade_frequency_limit:
  enabled: true
  limits:
    per_minute: 3
    per_hour: 10
    per_session: 50
  cooldown_on_breach:
    enabled: true
    per_minute_breach: 60
    per_hour_breach: 1800
    per_session_breach: 3600

cooldown_after_loss:
  enabled: true
  loss_threshold: -50
  cooldown_duration: 300

no_stop_loss_grace:
  enabled: true
  grace_period: 30
  enforcement: "close_all_and_lockout"

session_block_outside:
  enabled: true
  global_session:
    enabled: true
    start: "09:30"
    end: "16:00"
    timezone: "America/New_York"
  close_positions_at_session_end: true
  lockout_outside_session: true

auth_loss_guard:
  enabled: true
  enforcement: "close_all_and_lockout"

symbol_blocks:
  enabled: true
  blocked_symbols:
    - "BTC"
    - "ETH"
  enforcement: "close_all_and_lockout"

trade_management:
  enabled: true
  auto_stop_loss:
    enabled: true
    breakeven_after_profit: 100
```

---

## 2. Test Accounts Configuration

**File:** `tests/fixtures/config/accounts_test.yaml`

```yaml
accounts:
  - account_id: 123
    username: "test_trader@example.com"
    api_key: "test_api_key_123"
    enabled: true
    nickname: "Test Account 1"

  - account_id: 456
    username: "test_trader2@example.com"
    api_key: "test_api_key_456"
    enabled: true
    nickname: "Test Account 2"
```

---

## 3. Minimal Risk Configuration (MVP)

**File:** `tests/fixtures/config/risk_config_minimal.yaml`

```yaml
# Minimal config for MVP testing (only 3 rules)
max_contracts:
  enabled: true
  limit: 5

max_contracts_per_instrument:
  enabled: true
  limits:
    MNQ: 3

session_block_outside:
  enabled: true
  global_session:
    enabled: true
    start: "09:30"
    end: "16:00"
```

---

# Fixture Management

## Fixture Loading Utilities

**File:** `tests/conftest.py`

```python
import pytest
import json
import yaml
from pathlib import Path

# Base fixture directory
FIXTURE_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture
def api_response(request):
    """Load API response fixture by name"""
    fixture_name = request.param
    fixture_path = FIXTURE_DIR / "api" / f"{fixture_name}.json"
    with open(fixture_path) as f:
        return json.load(f)

@pytest.fixture
def signalr_event(request):
    """Load SignalR event fixture by name"""
    fixture_name = request.param
    fixture_path = FIXTURE_DIR / "signalr" / f"{fixture_name}.json"
    with open(fixture_path) as f:
        return json.load(f)

@pytest.fixture
def test_config(request):
    """Load test configuration by name"""
    fixture_name = request.param
    fixture_path = FIXTURE_DIR / "config" / f"{fixture_name}.yaml"
    with open(fixture_path) as f:
        return yaml.safe_load(f)

@pytest.fixture
def mock_database(tmp_path):
    """Create temporary SQLite database with test data"""
    import sqlite3
    db_path = tmp_path / "test_state.db"
    conn = sqlite3.connect(db_path)

    # Load and execute all database fixture SQL files
    for sql_file in (FIXTURE_DIR / "database").glob("*.sql"):
        with open(sql_file) as f:
            conn.executescript(f.read())

    conn.commit()
    return str(db_path)
```

---

## Fixture Usage Examples

### Example 1: Using API Response Fixture

```python
@pytest.mark.parametrize("api_response", ["positions_open"], indirect=True)
def test_load_positions(api_response):
    """Test loading positions from API response"""
    assert len(api_response) == 2
    assert api_response[0]['contractId'] == "CON.F.US.MNQ.U25"
```

### Example 2: Using SignalR Event Fixture

```python
@pytest.mark.parametrize("signalr_event", ["trade_loss"], indirect=True)
def test_daily_loss_rule(signalr_event):
    """Test daily loss rule with loss trade event"""
    rule = DailyRealizedLossRule(config)
    action = rule.check(signalr_event)
    assert action is not None
    assert action.type == EnforcementActionType.CLOSE_ALL_AND_LOCKOUT
```

### Example 3: Using Test Configuration

```python
@pytest.mark.parametrize("test_config", ["risk_config_minimal"], indirect=True)
def test_rule_loader(test_config):
    """Test loading rules from minimal config"""
    loader = RuleLoader(test_config)
    rules = loader.load_rules()
    assert len(rules) == 3  # Only 3 rules enabled in minimal config
```

---

## Fixture Maintenance

### Updating Fixtures

1. Add new fixtures to appropriate subdirectory (`api/`, `signalr/`, etc.)
2. Follow naming convention: `{category}_{description}.json`
3. Include docstring comment in fixture explaining usage
4. Update this document with fixture description

### Fixture Validation

**File:** `tests/validate_fixtures.py`

```python
"""Validate all test fixtures are valid JSON/YAML"""

import json
import yaml
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"

def test_all_json_fixtures_valid():
    """Validate all JSON fixtures parse correctly"""
    for json_file in FIXTURE_DIR.rglob("*.json"):
        with open(json_file) as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {json_file}: {e}")

def test_all_yaml_fixtures_valid():
    """Validate all YAML fixtures parse correctly"""
    for yaml_file in FIXTURE_DIR.rglob("*.yaml"):
        with open(yaml_file) as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {yaml_file}: {e}")
```

---

## Summary

- **Total API Response Fixtures:** 16
- **Total SignalR Event Fixtures:** 14
- **Total Database Fixtures:** 7 tables
- **Total Configuration Fixtures:** 3
- **Total Fixtures:** 40+

All fixtures are version-controlled and maintained alongside test code.

---

**Document Complete** ✓
**Ready for Use in Testing** ✓
