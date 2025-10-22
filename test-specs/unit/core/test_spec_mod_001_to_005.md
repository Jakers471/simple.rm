# Unit Test Specifications: Core Modules (MOD-001 to MOD-005)

**Generated:** 2025-10-22
**Purpose:** Detailed test specifications for core modules using Given/When/Then format
**Total Test Scenarios:** 38
**Coverage:** MOD-001 through MOD-005

---

## Table of Contents

1. [MOD-001: Enforcement Actions (8 tests)](#mod-001-enforcement-actions)
2. [MOD-002: Lockout Manager (10 tests)](#mod-002-lockout-manager)
3. [MOD-003: Timer Manager (6 tests)](#mod-003-timer-manager)
4. [MOD-004: Reset Scheduler (6 tests)](#mod-004-reset-scheduler)
5. [MOD-005: P&L Tracker (8 tests)](#mod-005-pnl-tracker)

---

# MOD-001: Enforcement Actions

**Module:** `src/enforcement/actions.py`
**Test File:** `tests/unit/test_enforcement_actions.py`
**Purpose:** Centralized enforcement logic - all rules call these functions to execute actions

---

## UT-001-01: Close All Positions - Happy Path

**Spec-ID:** MOD-001
**Test ID:** UT-001-01
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Mock REST client configured to return success responses
- State manager has 2 open positions:
  - Position 1:
    - contractId: "CON.F.US.ES.U25"
    - symbol: ES
    - side: LONG
    - size: 2 contracts
    - averagePrice: 4500.00
    - positionId: "pos-123"
  - Position 2:
    - contractId: "CON.F.US.NQ.U25"
    - symbol: NQ
    - side: SHORT
    - size: 1 contract
    - averagePrice: 16000.00
    - positionId: "pos-456"
- Mock SQLite database with enforcement_log table empty

### When (Act)
```python
enforcement = EnforcementActions(
    rest_client=mock_rest_client,
    state_mgr=mock_state_manager,
    db=mock_db
)
result = enforcement.close_all_positions(account_id=12345)
```

### Then (Assert)
- Function returns: `True`
- REST API POST called exactly 3 times:
  - Call 1: `POST /api/Position/searchOpen` with `{"accountId": 12345}`
  - Call 2: `POST /api/Position/closeContract` with `{"accountId": 12345, "contractId": "CON.F.US.ES.U25"}`
  - Call 3: `POST /api/Position/closeContract` with `{"accountId": 12345, "contractId": "CON.F.US.NQ.U25"}`
- Enforcement log written with:
  - action_type = "CLOSE_ALL_POSITIONS"
  - account_id = 12345
  - count = 2
- Logger info message: "Closed 2 positions for account 12345"

### Mock Setup (Python Pseudocode)
```python
from unittest.mock import MagicMock, call

# Mock REST client
mock_rest_client = MagicMock()
mock_rest_client.post.side_effect = [
    # Response for searchOpen
    MagicMock(json=lambda: {
        "positions": [
            {"contractId": "CON.F.US.ES.U25", "size": 2},
            {"contractId": "CON.F.US.NQ.U25", "size": 1}
        ]
    }),
    # Response for first closeContract
    MagicMock(json=lambda: {"success": True, "positionId": "pos-123"}),
    # Response for second closeContract
    MagicMock(json=lambda: {"success": True, "positionId": "pos-456"})
]

# Mock state manager
mock_state_manager = MagicMock()

# Mock database
mock_db = MagicMock()

# Verify calls
expected_calls = [
    call("/api/Position/searchOpen", json={"accountId": 12345}),
    call("/api/Position/closeContract", json={"accountId": 12345, "contractId": "CON.F.US.ES.U25"}),
    call("/api/Position/closeContract", json={"accountId": 12345, "contractId": "CON.F.US.NQ.U25"})
]
assert mock_rest_client.post.call_args_list == expected_calls
```

### Test Data Fixtures
- Fixture: `tests/fixtures/positions.py::two_open_positions_mixed()`
- Fixture: `tests/fixtures/api_responses.py::search_open_positions_success()`

---

## UT-001-02: Close All Positions - API Failure

**Spec-ID:** MOD-001
**Test ID:** UT-001-02
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Mock REST client configured to return HTTP 500 error
- Error response: `{"error": "Internal Server Error", "status": 500}`
- Logger configured to capture error messages

### When (Act)
```python
enforcement = EnforcementActions(rest_client=mock_rest_client, state_mgr=mock_state_manager)
result = enforcement.close_all_positions(account_id=12345)
```

### Then (Assert)
- Function returns: `False`
- Logger error message contains: "Error closing positions"
- No enforcement log entry written
- No positions are removed from state

### Mock Setup (Python Pseudocode)
```python
import requests

mock_rest_client = MagicMock()
mock_rest_client.post.side_effect = requests.exceptions.HTTPError("500 Server Error")

# Capture logger errors
with pytest.raises(Exception):
    pass  # Exception should be caught and logged, not raised
```

### Test Data Fixtures
- Fixture: `tests/fixtures/api_responses.py::api_error_500()`

---

## UT-001-03: Close All Positions - Network Timeout with Retry

**Spec-ID:** MOD-001
**Test ID:** UT-001-03
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Mock REST client configured to timeout on first 2 attempts
- Third attempt succeeds with 2 positions
- Retry configuration: max_retries = 3, exponential backoff (2s, 4s)

### When (Act)
```python
enforcement = EnforcementActions(rest_client=mock_rest_client)
result = enforcement.close_all_positions(account_id=12345)
```

### Then (Assert)
- Function returns: `True` (succeeds on 3rd attempt)
- REST API POST called exactly 3 times for searchOpen
- Time delays between retries: ~2 seconds, then ~4 seconds
- Logger warning messages for first 2 attempts
- Enforcement log shows successful closure

### Mock Setup (Python Pseudocode)
```python
import requests
from time import time

mock_rest_client = MagicMock()
call_count = 0

def side_effect(*args, **kwargs):
    nonlocal call_count
    call_count += 1
    if call_count <= 2:
        raise requests.exceptions.Timeout("Request timed out")
    return MagicMock(json=lambda: {"positions": []})

mock_rest_client.post.side_effect = side_effect
```

### Test Data Fixtures
- Fixture: `tests/fixtures/api_responses.py::timeout_then_success()`

---

## UT-001-04: Cancel All Orders - Happy Path

**Spec-ID:** MOD-001
**Test ID:** UT-001-04
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Mock REST client configured to return 3 working orders:
  - Order 1: id=789, type="Limit", symbol="ES", side="Buy", quantity=2
  - Order 2: id=790, type="Stop", symbol="NQ", side="Sell", quantity=1
  - Order 3: id=791, type="Limit", symbol="MNQ", side="Buy", quantity=3
- All orders have status="Working"

### When (Act)
```python
enforcement = EnforcementActions(rest_client=mock_rest_client)
result = enforcement.cancel_all_orders(account_id=12345)
```

### Then (Assert)
- Function returns: `True`
- REST API POST called exactly 4 times:
  - Call 1: `POST /api/Order/searchOpen` with `{"accountId": 12345}`
  - Call 2: `POST /api/Order/cancel` with `{"accountId": 12345, "orderId": 789}`
  - Call 3: `POST /api/Order/cancel` with `{"accountId": 12345, "orderId": 790}`
  - Call 4: `POST /api/Order/cancel` with `{"accountId": 12345, "orderId": 791}`
- Logger info message: "Cancelled 3 orders for account 12345"
- Enforcement log entry: "CANCEL_ALL_ORDERS: account=12345, count=3"

### Mock Setup (Python Pseudocode)
```python
mock_rest_client = MagicMock()
mock_rest_client.post.side_effect = [
    # searchOpen response
    MagicMock(json=lambda: {
        "orders": [
            {"id": 789, "type": "Limit", "status": "Working"},
            {"id": 790, "type": "Stop", "status": "Working"},
            {"id": 791, "type": "Limit", "status": "Working"}
        ]
    }),
    # cancel responses
    MagicMock(json=lambda: {"success": True}),
    MagicMock(json=lambda: {"success": True}),
    MagicMock(json=lambda: {"success": True})
]
```

### Test Data Fixtures
- Fixture: `tests/fixtures/orders.py::three_working_orders()`

---

## UT-001-05: Reduce Position to Limit - Partial Close

**Spec-ID:** MOD-001
**Test ID:** UT-001-05
**Priority:** Medium
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Contract ID: "CON.F.US.MNQ.U25"
- Current position size: 5 contracts
- Target size: 3 contracts
- Mock REST client configured to return current position and accept partial close

### When (Act)
```python
enforcement = EnforcementActions(rest_client=mock_rest_client)
result = enforcement.reduce_position_to_limit(
    account_id=12345,
    contract_id="CON.F.US.MNQ.U25",
    target_size=3
)
```

### Then (Assert)
- Function returns: `True`
- REST API POST called exactly 2 times:
  - Call 1: `POST /api/Position/searchOpen` to get current size
  - Call 2: `POST /api/Position/partialCloseContract` with:
    - accountId: 12345
    - contractId: "CON.F.US.MNQ.U25"
    - size: 2 (contracts to close: 5 - 3 = 2)
- Logger info message: "Reduced CON.F.US.MNQ.U25 from 5 to 3"
- Enforcement log: "REDUCE_POSITION: account=12345, contract=CON.F.US.MNQ.U25, from=5, to=3"

### Mock Setup (Python Pseudocode)
```python
mock_rest_client = MagicMock()
mock_rest_client.post.side_effect = [
    # searchOpen response
    MagicMock(json=lambda: {
        "positions": [
            {"contractId": "CON.F.US.MNQ.U25", "size": 5, "averagePrice": 21000.00}
        ]
    }),
    # partialCloseContract response
    MagicMock(json=lambda: {"success": True, "newSize": 3})
]
```

### Test Data Fixtures
- Fixture: `tests/fixtures/positions.py::position_at_size(symbol="MNQ", size=5)`

---

## UT-001-06: Place Stop-Loss Order - Calculate Price

**Spec-ID:** MOD-001
**Test ID:** UT-001-06
**Priority:** Medium
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Position: Long 2 MNQ @ 21000.00
- Contract metadata: MNQ tick size = 0.25, tick value = $0.50
- Stop-loss offset: 10 ticks below entry = 20997.50
- Mock REST client accepts order placement

### When (Act)
```python
enforcement = EnforcementActions(rest_client=mock_rest_client, contract_cache=mock_cache)
result = enforcement.place_stop_loss_order(
    account_id=12345,
    contract_id="CON.F.US.MNQ.U25",
    position_side="LONG",
    entry_price=21000.00,
    quantity=2,
    offset_ticks=10
)
```

### Then (Assert)
- Function returns: `True`
- REST API POST called once: `POST /api/Order/placeOrder`
- Order parameters:
  - accountId: 12345
  - contractId: "CON.F.US.MNQ.U25"
  - orderType: "Stop"
  - side: "Sell" (opposite of LONG position)
  - quantity: 2
  - stopPrice: 20997.50 (21000.00 - 10 * 0.25)
- Logger info message includes calculated stop price
- Enforcement log: "PLACE_STOP_LOSS: account=12345, contract=CON.F.US.MNQ.U25, stopPrice=20997.50"

### Mock Setup (Python Pseudocode)
```python
mock_rest_client = MagicMock()
mock_rest_client.post.return_value = MagicMock(
    json=lambda: {"success": True, "orderId": 999}
)

mock_cache = MagicMock()
mock_cache.get_contract.return_value = {
    "tickSize": 0.25,
    "tickValue": 0.50
}
```

### Test Data Fixtures
- Fixture: `tests/fixtures/contracts.py::mnq_contract_metadata()`
- Fixture: `tests/fixtures/positions.py::long_mnq_position()`

---

## UT-001-07: Enforcement Logging - Verify Log Entry

**Spec-ID:** MOD-001
**Test ID:** UT-001-07
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Mock file system for logs/enforcement.log
- Account ID: 12345
- Enforcement action: CLOSE_ALL_POSITIONS
- Position count: 2
- Timestamp: 2025-10-22 14:23:15

### When (Act)
```python
enforcement = EnforcementActions()
enforcement.log_enforcement("CLOSE_ALL_POSITIONS: account=12345, count=2")
```

### Then (Assert)
- File `logs/enforcement.log` contains new line:
  - Format: `[2025-10-22 14:23:15] CLOSE_ALL_POSITIONS: account=12345, count=2`
- File is appended (not overwritten)
- Line ends with newline character
- Timestamp format matches: YYYY-MM-DD HH:MM:SS

### Mock Setup (Python Pseudocode)
```python
from unittest.mock import mock_open, patch
from datetime import datetime

mock_file = mock_open()

with patch('builtins.open', mock_file):
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2025, 10, 22, 14, 23, 15)
        enforcement.log_enforcement("CLOSE_ALL_POSITIONS: account=12345, count=2")

mock_file.assert_called_with("logs/enforcement.log", "a")
handle = mock_file()
handle.write.assert_called_with("[2025-10-22 14:23:15] CLOSE_ALL_POSITIONS: account=12345, count=2\n")
```

### Test Data Fixtures
- Fixture: `tests/fixtures/filesystem.py::mock_log_file()`

---

## UT-001-08: Concurrent Enforcement Actions - Thread Safety

**Spec-ID:** MOD-001
**Test ID:** UT-001-08
**Priority:** Medium
**Type:** Unit Test

### Given (Arrange)
- Account IDs: 12345 and 67890
- Mock REST client handles concurrent requests
- Thread 1: closes positions for account 12345
- Thread 2: cancels orders for account 67890
- Both threads execute simultaneously

### When (Act)
```python
import threading

enforcement = EnforcementActions(rest_client=mock_rest_client)

thread1 = threading.Thread(
    target=enforcement.close_all_positions,
    args=(12345,)
)
thread2 = threading.Thread(
    target=enforcement.cancel_all_orders,
    args=(67890,)
)

thread1.start()
thread2.start()
thread1.join()
thread2.join()
```

### Then (Assert)
- Both threads complete successfully without errors
- Thread 1 result: `True`
- Thread 2 result: `True`
- No race conditions in logger
- No race conditions in enforcement log
- API calls for each account kept separate
- No data corruption in shared state

### Mock Setup (Python Pseudocode)
```python
from threading import Lock

mock_rest_client = MagicMock()
lock = Lock()

def thread_safe_post(endpoint, json):
    with lock:
        # Simulate API call
        return MagicMock(json=lambda: {"success": True})

mock_rest_client.post.side_effect = thread_safe_post
```

### Test Data Fixtures
- Fixture: `tests/fixtures/threading.py::concurrent_accounts()`

---

# MOD-002: Lockout Manager

**Module:** `src/state/lockout_manager.py`
**Test File:** `tests/unit/test_lockout_manager.py`
**Purpose:** Centralized lockout state management

---

## UT-002-01: Set Lockout with Expiry Time

**Spec-ID:** MOD-002
**Test ID:** UT-002-01
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Clean lockout state (no existing lockouts)
- Reason: "Daily loss limit hit"
- Expiry time: 2025-10-22 17:00:00 (5 PM ET)
- Current time: 2025-10-22 14:23:00
- Mock SQLite database

### When (Act)
```python
from datetime import datetime

lockout_mgr = LockoutManager(db=mock_db)
lockout_mgr.set_lockout(
    account_id=12345,
    reason="Daily loss limit hit",
    until=datetime(2025, 10, 22, 17, 0, 0)
)
```

### Then (Assert)
- Lockout state contains account 12345:
  ```python
  {
      "reason": "Daily loss limit hit",
      "until": datetime(2025, 10, 22, 17, 0, 0),
      "type": "hard_lockout",
      "created_at": datetime(2025, 10, 22, 14, 23, 0)
  }
  ```
- `is_locked_out(12345)` returns `True`
- SQLite INSERT OR REPLACE executed with:
  - account_id: 12345
  - reason: "Daily loss limit hit"
  - expires_at: 2025-10-22 17:00:00
  - created_at: 2025-10-22 14:23:00
- Logger info message: "Lockout set for account 12345: Daily loss limit hit until 2025-10-22 17:00:00"

### Mock Setup (Python Pseudocode)
```python
from unittest.mock import MagicMock

mock_db = MagicMock()
mock_cli = MagicMock()

lockout_mgr = LockoutManager(db=mock_db, cli=mock_cli)

# Verify database call
mock_db.execute.assert_called_once_with(
    "INSERT OR REPLACE INTO lockouts (account_id, reason, expires_at, created_at) VALUES (?, ?, ?, ?)",
    (12345, "Daily loss limit hit", datetime(2025, 10, 22, 17, 0, 0), datetime(2025, 10, 22, 14, 23, 0))
)

# Verify CLI notification
mock_cli.update_lockout_display.assert_called_once_with(
    12345, "Daily loss limit hit", datetime(2025, 10, 22, 17, 0, 0)
)
```

### Test Data Fixtures
- Fixture: `tests/fixtures/lockouts.py::daily_loss_lockout()`

---

## UT-002-02: Set Lockout with Permanent Lockout (NULL Expiry)

**Spec-ID:** MOD-002
**Test ID:** UT-002-02
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Clean lockout state
- Reason: "Manual lockout by administrator"
- Expiry time: None (permanent lockout)

### When (Act)
```python
lockout_mgr = LockoutManager(db=mock_db)
lockout_mgr.set_lockout(
    account_id=12345,
    reason="Manual lockout by administrator",
    until=None  # Permanent
)
```

### Then (Assert)
- Lockout state contains account 12345 with `until: None`
- `is_locked_out(12345)` returns `True` indefinitely
- SQLite INSERT with expires_at = NULL
- Lockout persists across daemon restarts
- Can only be cleared with `clear_lockout(12345)` call

### Mock Setup (Python Pseudocode)
```python
mock_db = MagicMock()

lockout_mgr = LockoutManager(db=mock_db)
lockout_mgr.set_lockout(12345, "Manual lockout", None)

# Verify NULL stored for permanent lockout
mock_db.execute.assert_called_with(
    "INSERT OR REPLACE INTO lockouts (account_id, reason, expires_at, created_at) VALUES (?, ?, ?, ?)",
    (12345, "Manual lockout", None, ANY)
)
```

### Test Data Fixtures
- Fixture: `tests/fixtures/lockouts.py::permanent_lockout()`

---

## UT-002-03: Is Locked Out - Account Currently Locked

**Spec-ID:** MOD-002
**Test ID:** UT-002-03
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Lockout set at 14:00:00, expires at 17:00:00
- Current time: 15:00:00 (1 hour into lockout)
- Reason: "Daily loss limit"

### When (Act)
```python
lockout_mgr = LockoutManager()
lockout_mgr.set_lockout(12345, "Daily loss limit", datetime(2025, 10, 22, 17, 0, 0))

is_locked = lockout_mgr.is_locked_out(12345)
```

### Then (Assert)
- Function returns: `True`
- Lockout state unchanged
- No database queries (in-memory check)

### Mock Setup (Python Pseudocode)
```python
from datetime import datetime
from unittest.mock import patch

with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)

    lockout_mgr = LockoutManager()
    lockout_mgr.set_lockout(12345, "Daily loss limit", datetime(2025, 10, 22, 17, 0, 0))

    assert lockout_mgr.is_locked_out(12345) == True
```

### Test Data Fixtures
- Fixture: `tests/fixtures/lockouts.py::active_lockout()`

---

## UT-002-04: Is Locked Out - Account Not Locked

**Spec-ID:** MOD-002
**Test ID:** UT-002-04
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- No lockout state for this account
- Lockout state is empty or only contains other accounts

### When (Act)
```python
lockout_mgr = LockoutManager()
is_locked = lockout_mgr.is_locked_out(12345)
```

### Then (Assert)
- Function returns: `False`
- No errors or exceptions
- No database queries

### Mock Setup (Python Pseudocode)
```python
lockout_mgr = LockoutManager()
# Empty state
assert lockout_mgr.is_locked_out(12345) == False

# State with other account
lockout_mgr.set_lockout(67890, "Other account", datetime(2025, 10, 22, 17, 0, 0))
assert lockout_mgr.is_locked_out(12345) == False
```

### Test Data Fixtures
- Fixture: `tests/fixtures/lockouts.py::empty_lockout_state()`

---

## UT-002-05: Is Locked Out - Lockout Expired (Auto-Clear)

**Spec-ID:** MOD-002
**Test ID:** UT-002-05
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Lockout set with expiry: 2025-10-22 17:00:00
- Current time: 2025-10-22 17:05:00 (5 minutes after expiry)

### When (Act)
```python
from datetime import datetime
from unittest.mock import patch

lockout_mgr = LockoutManager()
lockout_mgr.set_lockout(12345, "Daily loss", datetime(2025, 10, 22, 17, 0, 0))

# Fast-forward time
with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2025, 10, 22, 17, 5, 0)
    is_locked = lockout_mgr.is_locked_out(12345)
```

### Then (Assert)
- Function returns: `False`
- Lockout automatically cleared from memory
- `clear_lockout(12345)` called internally
- SQLite DELETE executed
- Logger message: "Lockout cleared for account 12345"

### Mock Setup (Python Pseudocode)
```python
mock_db = MagicMock()

with patch('datetime.datetime') as mock_datetime:
    # Set lockout at 14:00
    mock_datetime.now.return_value = datetime(2025, 10, 22, 14, 0, 0)
    lockout_mgr = LockoutManager(db=mock_db)
    lockout_mgr.set_lockout(12345, "Daily loss", datetime(2025, 10, 22, 17, 0, 0))

    # Check at 17:05 (expired)
    mock_datetime.now.return_value = datetime(2025, 10, 22, 17, 5, 0)
    assert lockout_mgr.is_locked_out(12345) == False

    # Verify cleared from DB
    mock_db.execute.assert_any_call(
        "DELETE FROM lockouts WHERE account_id=?", (12345,)
    )
```

### Test Data Fixtures
- Fixture: `tests/fixtures/lockouts.py::expired_lockout()`

---

## UT-002-06: Clear Lockout - Manual Unlock

**Spec-ID:** MOD-002
**Test ID:** UT-002-06
**Priority:** Medium
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Active lockout:
  - reason: "Daily loss limit"
  - until: 2025-10-22 17:00:00
  - type: "hard_lockout"
- Current time: 15:00:00 (before expiry)

### When (Act)
```python
lockout_mgr = LockoutManager(db=mock_db)
lockout_mgr.clear_lockout(account_id=12345)
```

### Then (Assert)
- Lockout removed from memory state
- `is_locked_out(12345)` returns `False`
- SQLite DELETE executed:
  ```sql
  DELETE FROM lockouts WHERE account_id=12345
  ```
- Logger message: "Lockout cleared for account 12345: Daily loss limit"
- CLI notification sent to clear display

### Mock Setup (Python Pseudocode)
```python
mock_db = MagicMock()
mock_cli = MagicMock()

lockout_mgr = LockoutManager(db=mock_db, cli=mock_cli)
lockout_mgr.set_lockout(12345, "Daily loss limit", datetime(2025, 10, 22, 17, 0, 0))

lockout_mgr.clear_lockout(12345)

# Verify state cleared
assert lockout_mgr.is_locked_out(12345) == False

# Verify database deletion
mock_db.execute.assert_any_call(
    "DELETE FROM lockouts WHERE account_id=?", (12345,)
)

# Verify CLI notified
mock_cli.clear_lockout_display.assert_called_once_with(12345)
```

### Test Data Fixtures
- Fixture: `tests/fixtures/lockouts.py::active_lockout_to_clear()`

---

## UT-002-07: Check Expired Lockouts - Batch Cleanup

**Spec-ID:** MOD-002
**Test ID:** UT-002-07
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Three accounts with lockouts:
  - Account 12345: expires at 17:00:00 (EXPIRED)
  - Account 67890: expires at 18:00:00 (still active)
  - Account 11111: expires at 16:00:00 (EXPIRED)
- Current time: 17:05:00

### When (Act)
```python
lockout_mgr = LockoutManager()
lockout_mgr.check_expired_lockouts()
```

### Then (Assert)
- Expired lockouts cleared: 12345 and 11111
- Active lockout remains: 67890
- `is_locked_out(12345)` returns `False`
- `is_locked_out(67890)` returns `True`
- `is_locked_out(11111)` returns `False`
- Logger messages for each cleared lockout:
  - "Auto-cleared expired lockout for account 12345"
  - "Auto-cleared expired lockout for account 11111"

### Mock Setup (Python Pseudocode)
```python
from datetime import datetime
from unittest.mock import patch

with patch('datetime.datetime') as mock_datetime:
    lockout_mgr = LockoutManager()

    # Set lockouts
    lockout_mgr.set_lockout(12345, "Loss 1", datetime(2025, 10, 22, 17, 0, 0))
    lockout_mgr.set_lockout(67890, "Loss 2", datetime(2025, 10, 22, 18, 0, 0))
    lockout_mgr.set_lockout(11111, "Loss 3", datetime(2025, 10, 22, 16, 0, 0))

    # Check at 17:05
    mock_datetime.now.return_value = datetime(2025, 10, 22, 17, 5, 0)
    lockout_mgr.check_expired_lockouts()

    # Verify results
    assert lockout_mgr.is_locked_out(12345) == False
    assert lockout_mgr.is_locked_out(67890) == True
    assert lockout_mgr.is_locked_out(11111) == False
```

### Test Data Fixtures
- Fixture: `tests/fixtures/lockouts.py::mixed_expiry_lockouts()`

---

## UT-002-08: Get Lockout Info - Details for Display

**Spec-ID:** MOD-002
**Test ID:** UT-002-08
**Priority:** Medium
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Active lockout:
  - reason: "Daily loss limit hit"
  - until: 2025-10-22 17:00:00
  - type: "hard_lockout"
  - created_at: 2025-10-22 14:00:00
- Current time: 2025-10-22 15:30:00

### When (Act)
```python
lockout_mgr = LockoutManager()
info = lockout_mgr.get_lockout_info(account_id=12345)
```

### Then (Assert)
- Function returns dictionary:
  ```python
  {
      "reason": "Daily loss limit hit",
      "until": datetime(2025, 10, 22, 17, 0, 0),
      "remaining_seconds": 5400,  # 1.5 hours = 90 minutes
      "type": "hard_lockout"
  }
  ```
- Remaining time calculated correctly: (17:00 - 15:30) = 90 minutes = 5400 seconds
- For non-locked account, returns `None`

### Mock Setup (Python Pseudocode)
```python
from datetime import datetime
from unittest.mock import patch

with patch('datetime.datetime') as mock_datetime:
    lockout_mgr = LockoutManager()

    # Set lockout at 14:00
    mock_datetime.now.return_value = datetime(2025, 10, 22, 14, 0, 0)
    lockout_mgr.set_lockout(12345, "Daily loss limit hit", datetime(2025, 10, 22, 17, 0, 0))

    # Get info at 15:30
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 30, 0)
    info = lockout_mgr.get_lockout_info(12345)

    assert info["remaining_seconds"] == 5400
    assert info["reason"] == "Daily loss limit hit"
```

### Test Data Fixtures
- Fixture: `tests/fixtures/lockouts.py::lockout_with_remaining_time()`

---

## UT-002-09: Lockout Persistence - Save to SQLite

**Spec-ID:** MOD-002
**Test ID:** UT-002-09
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Mock SQLite database with lockouts table
- Lockout details to save:
  - reason: "Daily loss limit"
  - expires_at: 2025-10-22 17:00:00
  - created_at: 2025-10-22 14:00:00

### When (Act)
```python
lockout_mgr = LockoutManager(db=mock_db)
lockout_mgr.set_lockout(
    account_id=12345,
    reason="Daily loss limit",
    until=datetime(2025, 10, 22, 17, 0, 0)
)
```

### Then (Assert)
- SQLite INSERT OR REPLACE executed with correct parameters
- Database row created/updated:
  ```sql
  account_id | reason            | expires_at          | created_at
  -----------+-------------------+---------------------+--------------------
  12345      | Daily loss limit  | 2025-10-22 17:00:00 | 2025-10-22 14:00:00
  ```
- Transaction committed
- No database errors

### Mock Setup (Python Pseudocode)
```python
import sqlite3
from unittest.mock import MagicMock

mock_db = MagicMock()
lockout_mgr = LockoutManager(db=mock_db)

lockout_mgr.set_lockout(12345, "Daily loss limit", datetime(2025, 10, 22, 17, 0, 0))

# Verify database call
mock_db.execute.assert_called_with(
    "INSERT OR REPLACE INTO lockouts (account_id, reason, expires_at, created_at) VALUES (?, ?, ?, ?)",
    (12345, "Daily loss limit", datetime(2025, 10, 22, 17, 0, 0), ANY)
)
```

### Test Data Fixtures
- Fixture: `tests/fixtures/database.py::mock_sqlite_db()`

---

## UT-002-10: Load Lockouts from SQLite on Init

**Spec-ID:** MOD-002
**Test ID:** UT-002-10
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- SQLite database contains 2 lockout rows:
  - Account 12345: expires at 2025-10-22 17:00:00, reason "Daily loss"
  - Account 67890: expires at 2025-10-22 18:00:00, reason "Trade frequency"
- One expired lockout (should not be loaded):
  - Account 11111: expires at 2025-10-22 14:00:00 (already expired)
- Current time: 2025-10-22 15:00:00

### When (Act)
```python
lockout_mgr = LockoutManager(db=mock_db)
lockout_mgr.load_lockouts_from_db()
```

### Then (Assert)
- Lockout state contains 2 accounts: 12345 and 67890
- Expired lockout (11111) not loaded
- `is_locked_out(12345)` returns `True`
- `is_locked_out(67890)` returns `True`
- `is_locked_out(11111)` returns `False`
- Logger message: "Loaded 2 lockouts from database"

### Mock Setup (Python Pseudocode)
```python
from datetime import datetime

mock_db = MagicMock()
mock_db.execute.return_value = [
    (12345, "Daily loss", datetime(2025, 10, 22, 17, 0, 0)),
    (67890, "Trade frequency", datetime(2025, 10, 22, 18, 0, 0))
    # Expired lockout filtered by SQL query
]

with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)

    lockout_mgr = LockoutManager(db=mock_db)
    lockout_mgr.load_lockouts_from_db()

    assert lockout_mgr.is_locked_out(12345) == True
    assert lockout_mgr.is_locked_out(67890) == True

# Verify SQL query filters expired
mock_db.execute.assert_called_with(
    "SELECT account_id, reason, expires_at FROM lockouts WHERE expires_at > ?",
    (datetime(2025, 10, 22, 15, 0, 0),)
)
```

### Test Data Fixtures
- Fixture: `tests/fixtures/database.py::lockouts_in_db()`

---

# MOD-003: Timer Manager

**Module:** `src/state/timer_manager.py`
**Test File:** `tests/unit/test_timer_manager.py`
**Purpose:** Countdown timers for cooldowns and scheduled tasks

---

## UT-003-01: Start Timer with Duration

**Spec-ID:** MOD-003
**Test ID:** UT-003-01
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Timer name: "lockout_12345"
- Duration: 1800 seconds (30 minutes)
- Callback function: `lambda: clear_lockout(12345)`
- Current time: 2025-10-22 15:00:00
- Empty timer state

### When (Act)
```python
timer_mgr = TimerManager()
timer_mgr.start_timer(
    name="lockout_12345",
    duration=1800,
    callback=lambda: clear_lockout(12345)
)
```

### Then (Assert)
- Timer added to state:
  ```python
  {
      "lockout_12345": {
          "expires_at": datetime(2025, 10, 22, 15, 30, 0),
          "callback": <function>,
          "duration": 1800
      }
  }
  ```
- `get_remaining_time("lockout_12345")` returns 1800
- Timer not yet executed (callback not called)

### Mock Setup (Python Pseudocode)
```python
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

mock_callback = MagicMock()

with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)

    timer_mgr = TimerManager()
    timer_mgr.start_timer("lockout_12345", 1800, mock_callback)

    # Verify timer state
    assert "lockout_12345" in timer_mgr.timers
    assert timer_mgr.timers["lockout_12345"]["duration"] == 1800
    assert timer_mgr.timers["lockout_12345"]["expires_at"] == datetime(2025, 10, 22, 15, 30, 0)

    # Callback not yet called
    mock_callback.assert_not_called()
```

### Test Data Fixtures
- Fixture: `tests/fixtures/timers.py::thirty_minute_timer()`

---

## UT-003-02: Start Timer with Callback Execution on Expiry

**Spec-ID:** MOD-003
**Test ID:** UT-003-02
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Timer name: "test_timer"
- Duration: 60 seconds
- Callback function: Mock function that sets a flag
- Current time: 15:00:00

### When (Act)
```python
callback_executed = False

def callback():
    global callback_executed
    callback_executed = True

timer_mgr = TimerManager()
timer_mgr.start_timer("test_timer", 60, callback)

# Fast-forward 61 seconds
with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 1, 1)
    timer_mgr.check_timers()
```

### Then (Assert)
- Callback function executed once
- `callback_executed` flag is `True`
- Timer removed from state
- `get_remaining_time("test_timer")` returns 0

### Mock Setup (Python Pseudocode)
```python
from datetime import datetime
from unittest.mock import MagicMock, patch

mock_callback = MagicMock()

with patch('datetime.datetime') as mock_datetime:
    # Start timer at 15:00:00
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)
    timer_mgr = TimerManager()
    timer_mgr.start_timer("test_timer", 60, mock_callback)

    # Check timers at 15:01:01 (expired)
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 1, 1)
    timer_mgr.check_timers()

    # Verify callback called once
    mock_callback.assert_called_once()

    # Verify timer removed
    assert "test_timer" not in timer_mgr.timers
```

### Test Data Fixtures
- Fixture: `tests/fixtures/timers.py::one_minute_timer_expired()`

---

## UT-003-03: Get Remaining Time During Timer

**Spec-ID:** MOD-003
**Test ID:** UT-003-03
**Priority:** Medium
**Type:** Unit Test

### Given (Arrange)
- Timer name: "lockout_12345"
- Duration: 60 seconds
- Started at: 15:00:00
- Current time: 15:00:30 (30 seconds elapsed)

### When (Act)
```python
with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)
    timer_mgr = TimerManager()
    timer_mgr.start_timer("lockout_12345", 60, lambda: None)

    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 30)
    remaining = timer_mgr.get_remaining_time("lockout_12345")
```

### Then (Assert)
- Function returns: 30 seconds
- Timer still active in state
- Value updates as time progresses

### Mock Setup (Python Pseudocode)
```python
from datetime import datetime
from unittest.mock import patch

with patch('datetime.datetime') as mock_datetime:
    # Start at 15:00:00
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)
    timer_mgr = TimerManager()
    timer_mgr.start_timer("lockout_12345", 60, lambda: None)

    # Check at 15:00:30
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 30)
    assert timer_mgr.get_remaining_time("lockout_12345") == 30

    # Check at 15:00:45
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 45)
    assert timer_mgr.get_remaining_time("lockout_12345") == 15
```

### Test Data Fixtures
- Fixture: `tests/fixtures/timers.py::timer_in_progress()`

---

## UT-003-04: Cancel Timer Before Expiry

**Spec-ID:** MOD-003
**Test ID:** UT-003-04
**Priority:** Medium
**Type:** Unit Test

### Given (Arrange)
- Timer name: "grace_period_12345"
- Duration: 30 seconds
- Started at: 15:00:00
- Current time: 15:00:15 (15 seconds elapsed)
- Callback: Mock function

### When (Act)
```python
mock_callback = MagicMock()

timer_mgr = TimerManager()
timer_mgr.start_timer("grace_period_12345", 30, mock_callback)

# Cancel after 15 seconds
timer_mgr.cancel_timer("grace_period_12345")

# Fast-forward past original expiry
with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 35)
    timer_mgr.check_timers()
```

### Then (Assert)
- Timer removed from state immediately on cancel
- Callback never executed
- `get_remaining_time("grace_period_12345")` returns 0
- No errors when checking expired timers

### Mock Setup (Python Pseudocode)
```python
from datetime import datetime
from unittest.mock import MagicMock, patch

mock_callback = MagicMock()

with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)
    timer_mgr = TimerManager()
    timer_mgr.start_timer("grace_period_12345", 30, mock_callback)

    # Cancel at 15 seconds
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 15)
    timer_mgr.cancel_timer("grace_period_12345")

    # Check past expiry
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 35)
    timer_mgr.check_timers()

    # Callback never called
    mock_callback.assert_not_called()
```

### Test Data Fixtures
- Fixture: `tests/fixtures/timers.py::cancelable_timer()`

---

## UT-003-05: Check Timers - Batch Expiry Check

**Spec-ID:** MOD-003
**Test ID:** UT-003-05
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Three timers started:
  - Timer 1: "timer_a", 30 seconds, expires at 15:00:30
  - Timer 2: "timer_b", 60 seconds, expires at 15:01:00
  - Timer 3: "timer_c", 20 seconds, expires at 15:00:20
- Current time: 15:00:25 (timer_c expired, others still active)

### When (Act)
```python
timer_mgr = TimerManager()

callback_a = MagicMock()
callback_b = MagicMock()
callback_c = MagicMock()

# Start all timers at 15:00:00
timer_mgr.start_timer("timer_a", 30, callback_a)
timer_mgr.start_timer("timer_b", 60, callback_b)
timer_mgr.start_timer("timer_c", 20, callback_c)

# Check at 15:00:25
with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 25)
    timer_mgr.check_timers()
```

### Then (Assert)
- Timer C callback executed (expired)
- Timer A callback not executed (5 seconds remaining)
- Timer B callback not executed (35 seconds remaining)
- Timer C removed from state
- Timers A and B remain active

### Mock Setup (Python Pseudocode)
```python
from datetime import datetime
from unittest.mock import MagicMock, patch

callback_a = MagicMock()
callback_b = MagicMock()
callback_c = MagicMock()

with patch('datetime.datetime') as mock_datetime:
    # Start all at 15:00:00
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)
    timer_mgr = TimerManager()
    timer_mgr.start_timer("timer_a", 30, callback_a)
    timer_mgr.start_timer("timer_b", 60, callback_b)
    timer_mgr.start_timer("timer_c", 20, callback_c)

    # Check at 15:00:25
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 25)
    timer_mgr.check_timers()

    # Verify only timer_c callback called
    callback_c.assert_called_once()
    callback_a.assert_not_called()
    callback_b.assert_not_called()

    # Verify timer_c removed
    assert "timer_c" not in timer_mgr.timers
    assert "timer_a" in timer_mgr.timers
    assert "timer_b" in timer_mgr.timers
```

### Test Data Fixtures
- Fixture: `tests/fixtures/timers.py::three_timers_mixed_expiry()`

---

## UT-003-06: Multiple Timers for Same Account

**Spec-ID:** MOD-003
**Test ID:** UT-003-06
**Priority:** Medium
**Type:** Unit Test

### Given (Arrange)
- Account 12345 has two independent timers:
  - Timer 1: "lockout_12345" - 1800 seconds cooldown
  - Timer 2: "grace_period_12345" - 30 seconds grace period
- Both timers started at 15:00:00
- Current time: 15:00:35

### When (Act)
```python
timer_mgr = TimerManager()

lockout_callback = MagicMock()
grace_callback = MagicMock()

timer_mgr.start_timer("lockout_12345", 1800, lockout_callback)
timer_mgr.start_timer("grace_period_12345", 30, grace_callback)

# Check at 15:00:35
with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 35)
    timer_mgr.check_timers()
```

### Then (Assert)
- Grace period timer expired and callback executed
- Lockout timer still active
- `get_remaining_time("grace_period_12345")` returns 0
- `get_remaining_time("lockout_12345")` returns 1765 (1800 - 35)
- Both timers tracked independently with no interference

### Mock Setup (Python Pseudocode)
```python
from datetime import datetime
from unittest.mock import MagicMock, patch

lockout_callback = MagicMock()
grace_callback = MagicMock()

with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)
    timer_mgr = TimerManager()

    timer_mgr.start_timer("lockout_12345", 1800, lockout_callback)
    timer_mgr.start_timer("grace_period_12345", 30, grace_callback)

    # Check at 35 seconds
    mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 35)
    timer_mgr.check_timers()

    # Grace callback executed
    grace_callback.assert_called_once()

    # Lockout callback not executed
    lockout_callback.assert_not_called()

    # Verify remaining time
    assert timer_mgr.get_remaining_time("lockout_12345") == 1765
    assert timer_mgr.get_remaining_time("grace_period_12345") == 0
```

### Test Data Fixtures
- Fixture: `tests/fixtures/timers.py::multiple_timers_per_account()`

---

# MOD-004: Reset Scheduler

**Module:** `src/state/reset_scheduler.py`
**Test File:** `tests/unit/test_reset_scheduler.py`
**Purpose:** Daily reset logic for P&L counters and holiday calendar

---

## UT-004-01: Schedule Daily Reset - Configuration

**Spec-ID:** MOD-004
**Test ID:** UT-004-01
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Reset time: "17:00" (5:00 PM)
- Timezone: "America/New_York" (ET)
- Empty reset configuration

### When (Act)
```python
reset_scheduler = ResetScheduler()
reset_scheduler.schedule_daily_reset(
    reset_time="17:00",
    timezone="America/New_York"
)
```

### Then (Assert)
- Reset configuration stored:
  ```python
  {
      "time": "17:00",
      "timezone": "America/New_York"
  }
  ```
- Logger message: "Daily reset scheduled for 17:00 America/New_York"
- No immediate reset triggered
- Configuration persisted for daemon restarts

### Mock Setup (Python Pseudocode)
```python
from unittest.mock import MagicMock

mock_logger = MagicMock()

reset_scheduler = ResetScheduler(logger=mock_logger)
reset_scheduler.schedule_daily_reset("17:00", "America/New_York")

# Verify config stored
assert reset_scheduler.reset_config["time"] == "17:00"
assert reset_scheduler.reset_config["timezone"] == "America/New_York"

# Verify logger called
mock_logger.info.assert_called_with("Daily reset scheduled for 17:00 America/New_York")
```

### Test Data Fixtures
- Fixture: `tests/fixtures/config.py::reset_time_config()`

---

## UT-004-02: Reset Daily Counters - Execution

**Spec-ID:** MOD-004
**Test ID:** UT-004-02
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Current state:
  - Daily realized P&L: -$500
  - Daily unrealized P&L: -$200
  - Active lockout: "Daily loss limit"
- Mock database with daily_pnl table
- Mock lockout manager

### When (Act)
```python
reset_scheduler = ResetScheduler(db=mock_db, lockout_mgr=mock_lockout_mgr)
reset_scheduler.reset_daily_counters(account_id=12345)
```

### Then (Assert)
- Daily realized P&L reset to $0
- Daily unrealized P&L reset to $0
- SQLite UPDATE executed:
  ```sql
  UPDATE daily_pnl
  SET realized_pnl=0, unrealized_pnl=0
  WHERE account_id=12345
  ```
- Lockout cleared: `lockout_mgr.clear_lockout(12345)` called
- Logger message: "Daily counters reset for account 12345"

### Mock Setup (Python Pseudocode)
```python
from unittest.mock import MagicMock

mock_db = MagicMock()
mock_lockout_mgr = MagicMock()

reset_scheduler = ResetScheduler(db=mock_db, lockout_mgr=mock_lockout_mgr)
reset_scheduler.reset_daily_counters(12345)

# Verify database update
mock_db.execute.assert_called_with(
    "UPDATE daily_pnl SET realized_pnl=0, unrealized_pnl=0 WHERE account_id=?",
    (12345,)
)

# Verify lockout cleared
mock_lockout_mgr.clear_lockout.assert_called_once_with(12345)
```

### Test Data Fixtures
- Fixture: `tests/fixtures/pnl.py::daily_pnl_negative_balance()`

---

## UT-004-03: Check Reset Times - Before Reset Time

**Spec-ID:** MOD-004
**Test ID:** UT-004-03
**Priority:** Medium
**Type:** Unit Test

### Given (Arrange)
- Reset scheduled for: 17:00 ET
- Current time: 16:00 ET (1 hour before reset)
- Account ID: 12345

### When (Act)
```python
from datetime import datetime
from unittest.mock import patch

reset_scheduler = ResetScheduler()
reset_scheduler.schedule_daily_reset("17:00", "America/New_York")

with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2025, 10, 22, 16, 0, 0)
    accounts_to_reset = reset_scheduler.check_reset_times()
```

### Then (Assert)
- Function returns: empty list `[]`
- No resets triggered
- No database updates
- No lockouts cleared

### Mock Setup (Python Pseudocode)
```python
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

mock_db = MagicMock()

with patch('datetime.datetime') as mock_datetime:
    # Current time is 16:00 ET
    tz = ZoneInfo("America/New_York")
    mock_datetime.now.return_value = datetime(2025, 10, 22, 16, 0, 0, tzinfo=tz)

    reset_scheduler = ResetScheduler(db=mock_db)
    reset_scheduler.schedule_daily_reset("17:00", "America/New_York")

    accounts = reset_scheduler.check_reset_times()

    assert accounts == []
    mock_db.execute.assert_not_called()
```

### Test Data Fixtures
- Fixture: `tests/fixtures/time.py::before_reset_time()`

---

## UT-004-04: Check Reset Times - At Reset Time

**Spec-ID:** MOD-004
**Test ID:** UT-004-04
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Reset scheduled for: 17:00 ET
- Current time: 17:00 ET (exact reset time)
- Account ID: 12345
- Reset not yet triggered today

### When (Act)
```python
reset_scheduler = ResetScheduler(db=mock_db)
reset_scheduler.schedule_daily_reset("17:00", "America/New_York")

with patch('datetime.datetime') as mock_datetime:
    tz = ZoneInfo("America/New_York")
    mock_datetime.now.return_value = datetime(2025, 10, 22, 17, 0, 0, tzinfo=tz)
    accounts = reset_scheduler.check_reset_times()
```

### Then (Assert)
- Function returns: `[12345]` (account ID to reset)
- Reset triggered flag set to prevent duplicate resets
- `reset_daily_counters(12345)` called
- Logger message: "Executing daily reset for account 12345"

### Mock Setup (Python Pseudocode)
```python
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

mock_db = MagicMock()

with patch('datetime.datetime') as mock_datetime:
    tz = ZoneInfo("America/New_York")
    mock_datetime.now.return_value = datetime(2025, 10, 22, 17, 0, 0, tzinfo=tz)

    reset_scheduler = ResetScheduler(db=mock_db)
    reset_scheduler.schedule_daily_reset("17:00", "America/New_York")

    # First check at 17:00 - should trigger
    accounts = reset_scheduler.check_reset_times()
    assert 12345 in accounts

    # Second check at 17:00 - should NOT trigger again
    accounts2 = reset_scheduler.check_reset_times()
    assert accounts2 == []  # Already reset today
```

### Test Data Fixtures
- Fixture: `tests/fixtures/time.py::at_reset_time()`

---

## UT-004-05: Is Holiday Check - Holiday Detection

**Spec-ID:** MOD-004
**Test ID:** UT-004-05
**Priority:** Medium
**Type:** Unit Test

### Given (Arrange)
- Holiday calendar loaded from `config/holidays.yaml`:
  ```yaml
  holidays:
    - "2025-01-01"  # New Year's Day
    - "2025-07-04"  # Independence Day
    - "2025-12-25"  # Christmas
  ```
- Test date: July 4, 2025

### When (Act)
```python
from datetime import datetime

reset_scheduler = ResetScheduler()
reset_scheduler.load_holiday_calendar("config/holidays.yaml")

is_holiday = reset_scheduler.is_holiday(datetime(2025, 7, 4))
```

### Then (Assert)
- Function returns: `True`
- For non-holiday date (e.g., July 5), returns `False`
- Holiday detection case-insensitive and format-tolerant

### Mock Setup (Python Pseudocode)
```python
from datetime import datetime
from unittest.mock import MagicMock, patch

mock_yaml = {
    "holidays": [
        "2025-01-01",
        "2025-07-04",
        "2025-12-25"
    ]
}

with patch('yaml.safe_load', return_value=mock_yaml):
    reset_scheduler = ResetScheduler()
    reset_scheduler.load_holiday_calendar("config/holidays.yaml")

    # Test holiday
    assert reset_scheduler.is_holiday(datetime(2025, 7, 4)) == True

    # Test non-holiday
    assert reset_scheduler.is_holiday(datetime(2025, 7, 5)) == False
```

### Test Data Fixtures
- Fixture: `tests/fixtures/config.py::holiday_calendar()`

---

## UT-004-06: Double-Reset Prevention - Already Reset Today

**Spec-ID:** MOD-004
**Test ID:** UT-004-06
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Reset scheduled for: 17:00 ET
- Current time: 17:05 ET
- Reset already executed at 17:00
- `reset_triggered_today` flag is `True`

### When (Act)
```python
reset_scheduler = ResetScheduler()
reset_scheduler.schedule_daily_reset("17:00", "America/New_York")

# First check at 17:00
with patch('datetime.datetime') as mock_datetime:
    tz = ZoneInfo("America/New_York")
    mock_datetime.now.return_value = datetime(2025, 10, 22, 17, 0, 0, tzinfo=tz)
    accounts1 = reset_scheduler.check_reset_times()

    # Second check at 17:05
    mock_datetime.now.return_value = datetime(2025, 10, 22, 17, 5, 0, tzinfo=tz)
    accounts2 = reset_scheduler.check_reset_times()
```

### Then (Assert)
- First check returns: `[12345]` (reset triggered)
- Second check returns: `[]` (no reset, already done)
- Database UPDATE called only once
- Logger message only once
- Flag resets at midnight for next day

### Mock Setup (Python Pseudocode)
```python
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

mock_db = MagicMock()

with patch('datetime.datetime') as mock_datetime:
    tz = ZoneInfo("America/New_York")
    reset_scheduler = ResetScheduler(db=mock_db)
    reset_scheduler.schedule_daily_reset("17:00", "America/New_York")

    # First check at 17:00
    mock_datetime.now.return_value = datetime(2025, 10, 22, 17, 0, 0, tzinfo=tz)
    accounts1 = reset_scheduler.check_reset_times()
    assert 12345 in accounts1

    # Database called once
    call_count_1 = mock_db.execute.call_count

    # Second check at 17:05
    mock_datetime.now.return_value = datetime(2025, 10, 22, 17, 5, 0, tzinfo=tz)
    accounts2 = reset_scheduler.check_reset_times()
    assert accounts2 == []

    # Database NOT called again
    call_count_2 = mock_db.execute.call_count
    assert call_count_2 == call_count_1
```

### Test Data Fixtures
- Fixture: `tests/fixtures/time.py::after_reset_time_same_day()`

---

# MOD-005: P&L Tracker

**Module:** `src/state/pnl_tracker.py`
**Test File:** `tests/unit/test_pnl_tracker.py`
**Purpose:** Centralized P&L calculation and tracking

---

## UT-005-01: Add Trade P&L - Positive P&L

**Spec-ID:** MOD-005
**Test ID:** UT-005-01
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Current daily P&L: $0
- Trade P&L to add: +$150.50
- Mock SQLite database

### When (Act)
```python
pnl_tracker = PNLTracker(db=mock_db)
new_total = pnl_tracker.add_trade_pnl(account_id=12345, pnl=150.50)
```

### Then (Assert)
- Function returns: 150.50
- Daily P&L updated to: $150.50
- SQLite UPDATE executed:
  ```sql
  UPDATE daily_pnl
  SET realized_pnl = 150.50
  WHERE account_id = 12345 AND date = CURRENT_DATE
  ```
- In-memory state updated:
  ```python
  daily_pnl[12345] = 150.50
  ```

### Mock Setup (Python Pseudocode)
```python
from unittest.mock import MagicMock

mock_db = MagicMock()

pnl_tracker = PNLTracker(db=mock_db)
result = pnl_tracker.add_trade_pnl(12345, 150.50)

assert result == 150.50
assert pnl_tracker.daily_pnl[12345] == 150.50

# Verify database update
mock_db.execute.assert_called_with(
    "UPDATE daily_pnl SET realized_pnl = ? WHERE account_id = ? AND date = CURRENT_DATE",
    (150.50, 12345)
)
```

### Test Data Fixtures
- Fixture: `tests/fixtures/pnl.py::positive_trade_pnl()`

---

## UT-005-02: Add Trade P&L - Negative P&L

**Spec-ID:** MOD-005
**Test ID:** UT-005-02
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Current daily P&L: $0
- Trade P&L to add: -$275.25
- Mock SQLite database

### When (Act)
```python
pnl_tracker = PNLTracker(db=mock_db)
new_total = pnl_tracker.add_trade_pnl(account_id=12345, pnl=-275.25)
```

### Then (Assert)
- Function returns: -275.25
- Daily P&L updated to: -$275.25
- SQLite UPDATE executed with negative value
- Subsequent trade adds correctly:
  ```python
  pnl_tracker.add_trade_pnl(12345, 50.00)
  # New total: -225.25
  ```

### Mock Setup (Python Pseudocode)
```python
mock_db = MagicMock()

pnl_tracker = PNLTracker(db=mock_db)

# First trade: -$275.25
result1 = pnl_tracker.add_trade_pnl(12345, -275.25)
assert result1 == -275.25

# Second trade: +$50.00
result2 = pnl_tracker.add_trade_pnl(12345, 50.00)
assert result2 == -225.25

# Verify final state
assert pnl_tracker.daily_pnl[12345] == -225.25
```

### Test Data Fixtures
- Fixture: `tests/fixtures/pnl.py::negative_trade_pnl()`

---

## UT-005-03: Get Daily Realized P&L - Query Current Total

**Spec-ID:** MOD-005
**Test ID:** UT-005-03
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Multiple trades recorded today:
  - Trade 1: +$100.00
  - Trade 2: -$50.00
  - Trade 3: +$75.50
- Current daily P&L: $125.50

### When (Act)
```python
pnl_tracker = PNLTracker()
pnl_tracker.add_trade_pnl(12345, 100.00)
pnl_tracker.add_trade_pnl(12345, -50.00)
pnl_tracker.add_trade_pnl(12345, 75.50)

total = pnl_tracker.get_daily_realized_pnl(account_id=12345)
```

### Then (Assert)
- Function returns: 125.50
- No database queries (in-memory read)
- For account with no trades, returns: 0.0

### Mock Setup (Python Pseudocode)
```python
pnl_tracker = PNLTracker()

# Add multiple trades
pnl_tracker.add_trade_pnl(12345, 100.00)
pnl_tracker.add_trade_pnl(12345, -50.00)
pnl_tracker.add_trade_pnl(12345, 75.50)

# Get total
total = pnl_tracker.get_daily_realized_pnl(12345)
assert total == 125.50

# Account with no trades
total_empty = pnl_tracker.get_daily_realized_pnl(67890)
assert total_empty == 0.0
```

### Test Data Fixtures
- Fixture: `tests/fixtures/pnl.py::multiple_trades_today()`

---

## UT-005-04: Reset Daily P&L - Reset Counters

**Spec-ID:** MOD-005
**Test ID:** UT-005-04
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Current daily P&L: -$350.75
- Mock SQLite database

### When (Act)
```python
pnl_tracker = PNLTracker(db=mock_db)
pnl_tracker.add_trade_pnl(12345, -350.75)

# Reset
pnl_tracker.reset_daily_pnl(account_id=12345)
```

### Then (Assert)
- Daily P&L reset to: $0.00
- In-memory state:
  ```python
  daily_pnl[12345] = 0.0
  ```
- SQLite INSERT for new day:
  ```sql
  INSERT INTO daily_pnl (account_id, realized_pnl, date)
  VALUES (12345, 0.0, CURRENT_DATE)
  ```
- `get_daily_realized_pnl(12345)` returns 0.0

### Mock Setup (Python Pseudocode)
```python
mock_db = MagicMock()

pnl_tracker = PNLTracker(db=mock_db)
pnl_tracker.add_trade_pnl(12345, -350.75)

# Reset
pnl_tracker.reset_daily_pnl(12345)

# Verify state
assert pnl_tracker.daily_pnl[12345] == 0.0
assert pnl_tracker.get_daily_realized_pnl(12345) == 0.0

# Verify database insert
mock_db.execute.assert_any_call(
    "INSERT INTO daily_pnl (account_id, realized_pnl, date) VALUES (?, 0.0, CURRENT_DATE)",
    (12345,)
)
```

### Test Data Fixtures
- Fixture: `tests/fixtures/pnl.py::pnl_ready_for_reset()`

---

## UT-005-05: Calculate Unrealized P&L - Long Position

**Spec-ID:** MOD-005
**Test ID:** UT-005-05
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Long position: 3 contracts MNQ
  - Entry price: 21000.00
  - Current price: 21002.00 (2 points profit)
  - Contract metadata:
    - Tick size: 0.25
    - Tick value: $0.50
    - Point value: $2.00
- Mock state manager, quote tracker, contract cache

### When (Act)
```python
# Position data
position = {
    "contractId": "CON.F.US.MNQ.U25",
    "type": 1,  # Long
    "size": 3,
    "averagePrice": 21000.00
}

# Current quote
current_price = 21002.00

# Contract metadata
contract = {
    "tickSize": 0.25,
    "tickValue": 0.50
}

pnl_tracker = PNLTracker(
    state_mgr=mock_state_mgr,
    quote_tracker=mock_quote_tracker,
    contract_cache=mock_cache
)

unrealized = pnl_tracker.calculate_unrealized_pnl(account_id=12345)
```

### Then (Assert)
- Calculation:
  - Price diff: 21002.00 - 21000.00 = 2.00 points
  - Ticks moved: 2.00 / 0.25 = 8 ticks
  - P&L per contract: 8 ticks * $0.50 = $4.00
  - Total P&L: $4.00 * 3 contracts = $12.00
- Function returns: 12.00

### Mock Setup (Python Pseudocode)
```python
from unittest.mock import MagicMock

mock_state_mgr = MagicMock()
mock_state_mgr.get_all_positions.return_value = [
    {
        "contractId": "CON.F.US.MNQ.U25",
        "type": 1,  # Long
        "size": 3,
        "averagePrice": 21000.00
    }
]

mock_quote_tracker = MagicMock()
mock_quote_tracker.get_last_price.return_value = 21002.00

mock_cache = MagicMock()
mock_cache.get_contract.return_value = {
    "tickSize": 0.25,
    "tickValue": 0.50
}

pnl_tracker = PNLTracker(
    state_mgr=mock_state_mgr,
    quote_tracker=mock_quote_tracker,
    contract_cache=mock_cache
)

unrealized = pnl_tracker.calculate_unrealized_pnl(12345)
assert unrealized == 12.00
```

### Test Data Fixtures
- Fixture: `tests/fixtures/positions.py::long_mnq_profitable()`
- Fixture: `tests/fixtures/contracts.py::mnq_metadata()`

---

## UT-005-06: Calculate Unrealized P&L - Short Position

**Spec-ID:** MOD-005
**Test ID:** UT-005-06
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Short position: 2 contracts ES
  - Entry price: 5000.00
  - Current price: 4995.00 (5 points profit for short)
  - Contract metadata:
    - Tick size: 0.25
    - Tick value: $12.50
    - Point value: $50.00

### When (Act)
```python
position = {
    "contractId": "CON.F.US.ES.U25",
    "type": 2,  # Short
    "size": 2,
    "averagePrice": 5000.00
}

current_price = 4995.00

contract = {
    "tickSize": 0.25,
    "tickValue": 12.50
}

pnl_tracker = PNLTracker(
    state_mgr=mock_state_mgr,
    quote_tracker=mock_quote_tracker,
    contract_cache=mock_cache
)

unrealized = pnl_tracker.calculate_unrealized_pnl(account_id=12345)
```

### Then (Assert)
- Calculation:
  - Price diff: 4995.00 - 5000.00 = -5.00 points
  - Ticks moved: -5.00 / 0.25 = -20 ticks
  - For SHORT: P&L = -(-20 ticks) * $12.50 = +$250.00 per contract
  - Total P&L: $250.00 * 2 contracts = $500.00
- Function returns: 500.00

### Mock Setup (Python Pseudocode)
```python
mock_state_mgr = MagicMock()
mock_state_mgr.get_all_positions.return_value = [
    {
        "contractId": "CON.F.US.ES.U25",
        "type": 2,  # Short
        "size": 2,
        "averagePrice": 5000.00
    }
]

mock_quote_tracker = MagicMock()
mock_quote_tracker.get_last_price.return_value = 4995.00

mock_cache = MagicMock()
mock_cache.get_contract.return_value = {
    "tickSize": 0.25,
    "tickValue": 12.50
}

pnl_tracker = PNLTracker(
    state_mgr=mock_state_mgr,
    quote_tracker=mock_quote_tracker,
    contract_cache=mock_cache
)

unrealized = pnl_tracker.calculate_unrealized_pnl(12345)
assert unrealized == 500.00
```

### Test Data Fixtures
- Fixture: `tests/fixtures/positions.py::short_es_profitable()`
- Fixture: `tests/fixtures/contracts.py::es_metadata()`

---

## UT-005-07: P&L Persistence to SQLite

**Spec-ID:** MOD-005
**Test ID:** UT-005-07
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- Account ID: 12345
- Multiple trades to add
- Mock SQLite database with daily_pnl table

### When (Act)
```python
pnl_tracker = PNLTracker(db=mock_db)

pnl_tracker.add_trade_pnl(12345, 100.00)
pnl_tracker.add_trade_pnl(12345, -50.00)
pnl_tracker.add_trade_pnl(12345, 75.50)
```

### Then (Assert)
- SQLite UPDATE called 3 times (once per trade)
- Final database row:
  ```sql
  account_id | realized_pnl | date
  -----------+--------------+------------
  12345      | 125.50       | 2025-10-22
  ```
- Transaction committed after each update
- No data loss if daemon crashes

### Mock Setup (Python Pseudocode)
```python
from unittest.mock import MagicMock, call

mock_db = MagicMock()

pnl_tracker = PNLTracker(db=mock_db)

pnl_tracker.add_trade_pnl(12345, 100.00)
pnl_tracker.add_trade_pnl(12345, -50.00)
pnl_tracker.add_trade_pnl(12345, 75.50)

# Verify 3 database updates
assert mock_db.execute.call_count == 3

# Verify final update
expected_calls = [
    call("UPDATE daily_pnl SET realized_pnl = ? WHERE account_id = ? AND date = CURRENT_DATE", (100.00, 12345)),
    call("UPDATE daily_pnl SET realized_pnl = ? WHERE account_id = ? AND date = CURRENT_DATE", (50.00, 12345)),
    call("UPDATE daily_pnl SET realized_pnl = ? WHERE account_id = ? AND date = CURRENT_DATE", (125.50, 12345))
]

mock_db.execute.assert_has_calls(expected_calls)
```

### Test Data Fixtures
- Fixture: `tests/fixtures/database.py::pnl_table_schema()`

---

## UT-005-08: Load P&L from SQLite on Init

**Spec-ID:** MOD-005
**Test ID:** UT-005-08
**Priority:** High
**Type:** Unit Test

### Given (Arrange)
- SQLite database contains existing P&L data:
  - Account 12345: realized_pnl = -$350.00, date = 2025-10-22
  - Account 67890: realized_pnl = $200.00, date = 2025-10-22
- Daemon startup / initialization

### When (Act)
```python
pnl_tracker = PNLTracker(db=mock_db)
pnl_tracker.load_pnl_from_db()
```

### Then (Assert)
- In-memory state loaded:
  ```python
  daily_pnl = {
      12345: -350.00,
      67890: 200.00
  }
  ```
- `get_daily_realized_pnl(12345)` returns -350.00
- `get_daily_realized_pnl(67890)` returns 200.00
- Logger message: "Loaded P&L for 2 accounts from database"

### Mock Setup (Python Pseudocode)
```python
from unittest.mock import MagicMock

mock_db = MagicMock()
mock_db.execute.return_value = [
    (12345, -350.00, "2025-10-22"),
    (67890, 200.00, "2025-10-22")
]

pnl_tracker = PNLTracker(db=mock_db)
pnl_tracker.load_pnl_from_db()

# Verify state loaded
assert pnl_tracker.daily_pnl[12345] == -350.00
assert pnl_tracker.daily_pnl[67890] == 200.00

# Verify getter works
assert pnl_tracker.get_daily_realized_pnl(12345) == -350.00
assert pnl_tracker.get_daily_realized_pnl(67890) == 200.00

# Verify SQL query
mock_db.execute.assert_called_with(
    "SELECT account_id, realized_pnl, date FROM daily_pnl WHERE date = CURRENT_DATE"
)
```

### Test Data Fixtures
- Fixture: `tests/fixtures/database.py::pnl_data_in_db()`

---

## Summary

**Total Test Specifications Created:** 38

### Breakdown by Module:
- **MOD-001 (Enforcement Actions):** 8 tests
- **MOD-002 (Lockout Manager):** 10 tests
- **MOD-003 (Timer Manager):** 6 tests
- **MOD-004 (Reset Scheduler):** 6 tests
- **MOD-005 (P&L Tracker):** 8 tests

### Priority Distribution:
- **High Priority:** 30 tests (79%)
- **Medium Priority:** 8 tests (21%)

### Test Coverage:
- All public API functions covered
- Happy path and error scenarios
- Edge cases (timeouts, expiry, concurrency)
- Data persistence and recovery
- Integration points between modules

---

**Next Steps:**
1. Implement test fixtures referenced in specifications
2. Create mock helpers for REST API, SQLite, and state managers
3. Set up pytest configuration with coverage tracking
4. Implement tests following these specifications
5. Achieve 90%+ code coverage for core modules

---

**Document Complete** ✓
**Ready for Test Implementation** ✓
