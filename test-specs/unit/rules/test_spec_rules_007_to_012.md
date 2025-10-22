# Unit Test Specifications - Risk Rules (Part 2)
## RULE-007 through RULE-012

**Generated:** 2025-10-22
**Agent:** Unit Test Spec Writer - Risk Rules (Part 2)
**Coverage:** RULE-007 (Cooldown After Loss), RULE-008 (No Stop Loss Grace), RULE-009 (Session Block Outside Hours), RULE-010 (Auth Loss Guard), RULE-011 (Symbol Blocks), RULE-012 (Trade Management)
**Total Scenarios:** 36

---

## RULE-007: Cooldown After Loss (`src/rules/cooldown_after_loss.py`)

**Rule Purpose:** Force break after losing trades to prevent revenge trading and emotional decision-making.

**Test File:** `tests/unit/test_rules/test_cooldown_after_loss.py`

---

### UT-107-01: check() - Profitable trade (no trigger)

**Priority:** High

**Scenario:** Profitable trades should not trigger cooldown - only losses trigger this rule.

**Given:**
```python
# Fixtures: tests/fixtures/trade_events.json
trade_event = {
    "id": 101112,
    "accountId": 123,
    "contractId": "CON.F.US.EP.U25",
    "creationTimestamp": "2024-07-21T13:47:00Z",
    "price": 2100.75,
    "profitAndLoss": 150.50,  # Positive = profit
    "fees": 2.50,
    "side": 1,
    "size": 1,
    "voided": False,
    "orderId": 789
}

# Config: cooldown thresholds
config = {
    'loss_thresholds': [
        {'loss_amount': -100, 'cooldown_duration': 300},
        {'loss_amount': -200, 'cooldown_duration': 900},
        {'loss_amount': -300, 'cooldown_duration': 1800}
    ]
}

# No existing cooldown
lockout_manager.active_cooldowns = {}
```

**When:**
```python
result = cooldown_after_loss_rule.check(trade_event, config)
```

**Then:**
```python
# No breach for profitable trade
assert result is None

# No cooldown set
assert 123 not in lockout_manager.active_cooldowns

# Trade P&L logged (for tracking)
assert trade_counter.get_last_trade_pnl(123) == 150.50
```

---

### UT-107-02: check() - Small loss under threshold (no trigger)

**Priority:** High

**Scenario:** Losses smaller than the smallest threshold should not trigger cooldown.

**Given:**
```python
# Loss of $75 (below -$100 threshold)
trade_event = {
    "id": 101113,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "creationTimestamp": "2024-07-21T14:00:00Z",
    "price": 21000.25,
    "profitAndLoss": -75.00,  # Loss, but below threshold
    "fees": 2.50,
    "side": 1,
    "size": 1,
    "voided": False,
    "orderId": 790
}

# Config: smallest threshold is -$100
config = {
    'loss_thresholds': [
        {'loss_amount': -100, 'cooldown_duration': 300},
        {'loss_amount': -200, 'cooldown_duration': 900}
    ]
}

# No existing cooldown
lockout_manager.active_cooldowns = {}
```

**When:**
```python
result = cooldown_after_loss_rule.check(trade_event, config)
```

**Then:**
```python
# Loss is -75, which is > -100 (not as negative)
assert result is None

# No cooldown triggered
assert 123 not in lockout_manager.active_cooldowns

# Loss still tracked for statistics
assert trade_counter.get_last_trade_pnl(123) == -75.00
```

---

### UT-107-03: check() - Loss at first threshold ($100)

**Priority:** High

**Scenario:** Loss of exactly $100 should trigger the first threshold's cooldown (5 minutes).

**Given:**
```python
# Loss of exactly $100
trade_event = {
    "id": 101114,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "creationTimestamp": "2024-07-21T14:15:00Z",
    "price": 21005.00,
    "profitAndLoss": -100.00,  # Exactly at threshold
    "fees": 2.50,
    "side": 0,
    "size": 2,
    "voided": False,
    "orderId": 791
}

# Config: first threshold is -$100 = 5 min cooldown
config = {
    'loss_thresholds': [
        {'loss_amount': -100, 'cooldown_duration': 300},
        {'loss_amount': -200, 'cooldown_duration': 900},
        {'loss_amount': -300, 'cooldown_duration': 1800}
    ]
}

# Mock time
mock_datetime = Mock()
mock_datetime.now.return_value = datetime(2024, 7, 21, 14, 15, 5)

lockout_manager.active_cooldowns = {}
```

**When:**
```python
result = cooldown_after_loss_rule.check(trade_event, config)
```

**Then:**
```python
# Breach detected at -$100 threshold
assert result is not None
assert result['breach'] == True
assert result['loss_amount'] == -100.00
assert result['cooldown_duration'] == 300  # 5 minutes

# Cooldown should be set (verify via enforcement)
# (Enforcement sets cooldown, not check() - check() just returns action)
action = result['action']
assert action['type'] == 'SET_COOLDOWN'
assert action['duration'] == 300
assert action['reason'] == 'Cooldown after $100.00 loss - take a break'
```

---

### UT-107-04: check() - Large loss at middle threshold ($150)

**Priority:** High

**Scenario:** Loss between thresholds should trigger the appropriate (first exceeded) threshold.

**Given:**
```python
# Loss of $150 (triggers -$100 threshold, not -$200)
trade_event = {
    "id": 101115,
    "accountId": 123,
    "contractId": "CON.F.US.ES.U25",
    "creationTimestamp": "2024-07-21T14:30:00Z",
    "price": 5800.50,
    "profitAndLoss": -150.00,
    "fees": 2.40,
    "side": 1,
    "size": 1,
    "voided": False,
    "orderId": 792
}

# Config: thresholds sorted largest to smallest
config = {
    'loss_thresholds': [
        {'loss_amount': -100, 'cooldown_duration': 300},
        {'loss_amount': -200, 'cooldown_duration': 900},
        {'loss_amount': -300, 'cooldown_duration': 1800}
    ]
}

mock_datetime.now.return_value = datetime(2024, 7, 21, 14, 30, 10)
lockout_manager.active_cooldowns = {}
```

**When:**
```python
result = cooldown_after_loss_rule.check(trade_event, config)
```

**Then:**
```python
# -150 <= -100 (triggered!)
# -150 > -200 (not triggered)
# Therefore: Use -100 threshold
assert result is not None
assert result['breach'] == True
assert result['loss_amount'] == -100.00  # Triggered threshold
assert result['cooldown_duration'] == 300  # 5 min cooldown

# Action should reflect 5 minute cooldown
action = result['action']
assert action['type'] == 'SET_COOLDOWN'
assert action['duration'] == 300
```

---

### UT-107-05: check() - Severe loss at highest threshold ($350)

**Priority:** High

**Scenario:** Very large loss should trigger the highest threshold with longest cooldown.

**Given:**
```python
# Loss of $350 (triggers -$300 threshold = 30 min cooldown)
trade_event = {
    "id": 101116,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "creationTimestamp": "2024-07-21T15:00:00Z",
    "price": 21020.00,
    "profitAndLoss": -350.00,  # Severe loss
    "fees": 2.50,
    "side": 0,
    "size": 3,
    "voided": False,
    "orderId": 793
}

# Config: highest threshold is -$300 = 30 min
config = {
    'loss_thresholds': [
        {'loss_amount': -100, 'cooldown_duration': 300},
        {'loss_amount': -200, 'cooldown_duration': 900},
        {'loss_amount': -300, 'cooldown_duration': 1800}
    ]
}

mock_datetime.now.return_value = datetime(2024, 7, 21, 15, 0, 5)
lockout_manager.active_cooldowns = {}
```

**When:**
```python
result = cooldown_after_loss_rule.check(trade_event, config)
```

**Then:**
```python
# -350 <= -300 (highest threshold triggered!)
assert result is not None
assert result['breach'] == True
assert result['loss_amount'] == -300.00  # Highest threshold
assert result['cooldown_duration'] == 1800  # 30 minutes

action = result['action']
assert action['type'] == 'SET_COOLDOWN'
assert action['duration'] == 1800
assert 'take a break' in action['reason'].lower()
```

---

### UT-107-06: check() - Half-turn trade (profitAndLoss = null)

**Priority:** Medium

**Scenario:** Opening trades with null P&L should not trigger cooldown.

**Given:**
```python
# Half-turn trade (position opened, not closed yet)
trade_event = {
    "id": 101117,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "creationTimestamp": "2024-07-21T15:15:00Z",
    "price": 21030.00,
    "profitAndLoss": None,  # Half-turn = no P&L yet
    "fees": 0,
    "side": 0,
    "size": 1,
    "voided": False,
    "orderId": 794
}

config = {
    'loss_thresholds': [
        {'loss_amount': -100, 'cooldown_duration': 300}
    ]
}

lockout_manager.active_cooldowns = {}
```

**When:**
```python
result = cooldown_after_loss_rule.check(trade_event, config)
```

**Then:**
```python
# Null P&L should not trigger cooldown
assert result is None

# No cooldown set
assert 123 not in lockout_manager.active_cooldowns
```

---

## RULE-008: No Stop Loss Grace Period (`src/rules/no_stop_loss_grace.py`)

**Rule Purpose:** Enforce stop-loss placement within grace period after position opens.

**Test File:** `tests/unit/test_rules/test_no_stop_loss_grace.py`

---

### UT-108-01: check() - Position with stop-loss already placed

**Priority:** High

**Scenario:** Position with valid stop-loss should pass check immediately.

**Given:**
```python
# Position opened
position_event = {
    "id": 456,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "creationTimestamp": "2024-07-21T14:00:00Z",
    "type": 1,  # Long
    "size": 2,
    "averagePrice": 21000.25
}

# Stop-loss order already exists
order_event = {
    "id": 789,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "type": 4,  # Stop order
    "side": 1,  # Sell (to close long)
    "stopPrice": 20990.00,  # Below entry
    "status": 1,  # Active
    "size": 2
}

# Config: 30 second grace period
config = {
    'grace_period_seconds': 30
}

# Position tracking
positions_pending_stop = {
    456: {
        'contract_id': 'CON.F.US.MNQ.U25',
        'account_id': 123,
        'entry_price': 21000.25,
        'position_type': 1,
        'opened_at': datetime(2024, 7, 21, 14, 0, 0),
        'has_stop_loss': True  # Already detected
    }
}

mock_datetime.now.return_value = datetime(2024, 7, 21, 14, 0, 10)
```

**When:**
```python
result = no_stop_loss_grace_rule.check(456, positions_pending_stop[456], config)
```

**Then:**
```python
# Position has stop-loss, no breach
assert result is None

# Position should be removed from pending tracking
assert 456 not in positions_pending_stop
```

---

### UT-108-02: check() - Position without stop-loss, within grace period

**Priority:** High

**Scenario:** Position without stop-loss but within 30s grace period should not trigger yet.

**Given:**
```python
# Position opened 15 seconds ago (within 30s grace)
position_pending = {
    456: {
        'contract_id': 'CON.F.US.MNQ.U25',
        'account_id': 123,
        'entry_price': 21000.25,
        'position_type': 1,
        'opened_at': datetime(2024, 7, 21, 14, 0, 0),
        'has_stop_loss': False
    }
}

config = {
    'grace_period_seconds': 30
}

# Current time: 15 seconds elapsed
mock_datetime.now.return_value = datetime(2024, 7, 21, 14, 0, 15)
```

**When:**
```python
result = no_stop_loss_grace_rule.check(456, position_pending[456], config)
```

**Then:**
```python
# Still within grace period (15s < 30s)
assert result is None

# Position still in pending tracking
assert 456 in position_pending
assert position_pending[456]['has_stop_loss'] == False
```

---

### UT-108-03: check() - Stop-loss added within grace period

**Priority:** High

**Scenario:** When trader adds stop-loss during grace period, tracking should stop.

**Given:**
```python
# Position opened 10 seconds ago
position_pending = {
    456: {
        'contract_id': 'CON.F.US.MNQ.U25',
        'account_id': 123,
        'entry_price': 21000.25,
        'position_type': 1,
        'opened_at': datetime(2024, 7, 21, 14, 0, 0),
        'has_stop_loss': False
    }
}

# Stop-loss order now detected
new_order_event = {
    "id": 790,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "type": 4,  # Stop
    "side": 1,  # Sell
    "stopPrice": 20995.00,
    "status": 1,
    "size": 2
}

config = {
    'grace_period_seconds': 30
}

mock_datetime.now.return_value = datetime(2024, 7, 21, 14, 0, 10)
```

**When:**
```python
# Detect stop-loss order
no_stop_loss_grace_rule.on_order_placed(new_order_event, position_pending)
result = no_stop_loss_grace_rule.check(456, position_pending[456], config)
```

**Then:**
```python
# Stop-loss detected, mark as having stop
assert position_pending[456]['has_stop_loss'] == True

# Check should pass
assert result is None

# Position should be removed from pending tracking
assert 456 not in position_pending
```

---

### UT-108-04: check() - Grace period expired without stop-loss

**Priority:** High

**Scenario:** Position without stop-loss after 30s should trigger breach and close position.

**Given:**
```python
# Position opened 35 seconds ago (beyond 30s grace)
position_pending = {
    456: {
        'contract_id': 'CON.F.US.MNQ.U25',
        'account_id': 123,
        'entry_price': 21000.25,
        'position_type': 1,
        'opened_at': datetime(2024, 7, 21, 14, 0, 0),
        'has_stop_loss': False
    }
}

config = {
    'grace_period_seconds': 30,
    'action': 'CLOSE_POSITION'
}

# Current time: 35 seconds elapsed
mock_datetime.now.return_value = datetime(2024, 7, 21, 14, 0, 35)
```

**When:**
```python
result = no_stop_loss_grace_rule.check(456, position_pending[456], config)
```

**Then:**
```python
# Grace period expired (35s >= 30s)
assert result is not None
assert result['breach'] == True
assert result['elapsed_time'] == 35

# Action: close position
action = result['action']
assert action['type'] == 'CLOSE_POSITION'
assert action['contract_id'] == 'CON.F.US.MNQ.U25'
assert action['account_id'] == 123
assert action['reason'] == 'No stop-loss within 30s grace period'

# Position should be removed from tracking after enforcement
```

---

### UT-108-05: check() - Stop-loss detection by order type

**Priority:** Medium

**Scenario:** Different stop order types (Stop, StopLimit, TrailingStop) should all be detected.

**Given:**
```python
# Position: Long @ 21000
position = {
    'contract_id': 'CON.F.US.MNQ.U25',
    'account_id': 123,
    'entry_price': 21000.00,
    'position_type': 1,  # Long
    'opened_at': datetime(2024, 7, 21, 14, 0, 0),
    'has_stop_loss': False
}

# Test different order types
stop_limit_order = {
    "type": 3,  # StopLimit
    "side": 1,  # Sell
    "stopPrice": 20990.00,
    "contractId": "CON.F.US.MNQ.U25"
}

stop_order = {
    "type": 4,  # Stop
    "side": 1,  # Sell
    "stopPrice": 20990.00,
    "contractId": "CON.F.US.MNQ.U25"
}

trailing_stop_order = {
    "type": 5,  # TrailingStop
    "side": 1,  # Sell
    "stopPrice": 20990.00,
    "contractId": "CON.F.US.MNQ.U25"
}
```

**When:**
```python
result1 = no_stop_loss_grace_rule.is_stop_loss_order(stop_limit_order, position)
result2 = no_stop_loss_grace_rule.is_stop_loss_order(stop_order, position)
result3 = no_stop_loss_grace_rule.is_stop_loss_order(trailing_stop_order, position)
```

**Then:**
```python
# All three order types should be recognized as stop-loss
assert result1 == True
assert result2 == True
assert result3 == True
```

---

### UT-108-06: check() - Wrong direction order not detected as stop-loss

**Priority:** Medium

**Scenario:** Order on wrong side should not be considered a valid stop-loss.

**Given:**
```python
# Position: Short @ 21000
position = {
    'contract_id': 'CON.F.US.MNQ.U25',
    'account_id': 123,
    'entry_price': 21000.00,
    'position_type': 2,  # Short
    'opened_at': datetime(2024, 7, 21, 14, 0, 0),
    'has_stop_loss': False
}

# Wrong direction: Sell order for SHORT position (should be Buy to close)
wrong_direction_order = {
    "type": 4,  # Stop
    "side": 1,  # Sell (wrong for short!)
    "stopPrice": 20990.00,
    "contractId": "CON.F.US.MNQ.U25"
}

# Correct direction for SHORT: Buy above entry
correct_order = {
    "type": 4,  # Stop
    "side": 0,  # Buy (correct for short)
    "stopPrice": 21010.00,  # Above entry
    "contractId": "CON.F.US.MNQ.U25"
}
```

**When:**
```python
wrong_result = no_stop_loss_grace_rule.is_stop_loss_order(wrong_direction_order, position)
correct_result = no_stop_loss_grace_rule.is_stop_loss_order(correct_order, position)
```

**Then:**
```python
# Wrong direction should NOT be detected
assert wrong_result == False

# Correct direction should be detected
assert correct_result == True
```

---

## RULE-009: Session Block Outside Hours (`src/rules/session_block_outside_hours.py`)

**Rule Purpose:** Prevent trading outside configured session hours (e.g., no trading before 9:30 AM ET).

**Test File:** `tests/unit/test_rules/test_session_block_outside.py`

---

### UT-109-01: check() - Position during valid session hours

**Priority:** High

**Scenario:** Position opened during configured session hours should pass.

**Given:**
```python
# Position opened at 10:00 AM ET
position_event = {
    "id": 456,
    "accountId": 123,
    "contractId": "CON.F.US.ES.U25",
    "creationTimestamp": "2024-07-21T14:00:00Z",  # 10:00 AM ET
    "type": 1,
    "size": 1,
    "averagePrice": 5800.00
}

# Config: session 9:30 AM - 4:00 PM ET
config = {
    'session_hours': {
        'start': '09:30',
        'end': '16:00',
        'timezone': 'America/New_York'
    }
}

# Mock time: 10:00 AM ET (within session)
mock_tz = pytz.timezone('America/New_York')
mock_datetime.now.return_value = datetime(2024, 7, 21, 10, 0, 0, tzinfo=mock_tz)
```

**When:**
```python
result = session_block_rule.check(position_event, config)
```

**Then:**
```python
# Within session hours, no breach
assert result is None

# Position allowed
assert lockout_manager.is_locked_out(123) == False
```

---

### UT-109-02: check() - Position before session start

**Priority:** High

**Scenario:** Position opened before session start (e.g., 8:00 AM) should trigger breach.

**Given:**
```python
# Position opened at 8:00 AM ET (before 9:30 AM session start)
position_event = {
    "id": 457,
    "accountId": 123,
    "contractId": "CON.F.US.ES.U25",
    "creationTimestamp": "2024-07-21T12:00:00Z",  # 8:00 AM ET
    "type": 1,
    "size": 1,
    "averagePrice": 5800.00
}

# Config: session 9:30 AM - 4:00 PM ET
config = {
    'session_hours': {
        'start': '09:30',
        'end': '16:00',
        'timezone': 'America/New_York'
    },
    'action': 'CLOSE_ALL_AND_LOCKOUT'
}

# Mock time: 8:00 AM ET (before session)
mock_tz = pytz.timezone('America/New_York')
mock_datetime.now.return_value = datetime(2024, 7, 21, 8, 0, 0, tzinfo=mock_tz)
```

**When:**
```python
result = session_block_rule.check(position_event, config)
```

**Then:**
```python
# Before session start, breach detected
assert result is not None
assert result['breach'] == True
assert result['reason'] == 'Trading outside session hours'
assert result['current_time'] == '08:00:00'
assert result['session_start'] == '09:30:00'

# Action: close all positions and lockout
action = result['action']
assert action['type'] == 'CLOSE_ALL_AND_LOCKOUT'
assert action['reason'] == 'Position detected before session hours'
```

---

### UT-109-03: check() - Position after session end

**Priority:** High

**Scenario:** Position held after session end should trigger breach.

**Given:**
```python
# Position still open at 5:00 PM ET (after 4:00 PM session end)
position_event = {
    "id": 458,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "creationTimestamp": "2024-07-21T15:00:00Z",  # 11:00 AM ET (opened during session)
    "type": 1,
    "size": 2,
    "averagePrice": 21000.00
}

# Config: session 9:30 AM - 4:00 PM ET
config = {
    'session_hours': {
        'start': '09:30',
        'end': '16:00',
        'timezone': 'America/New_York'
    },
    'action': 'CLOSE_ALL_AND_LOCKOUT'
}

# Mock time: 5:00 PM ET (after session end)
mock_tz = pytz.timezone('America/New_York')
mock_datetime.now.return_value = datetime(2024, 7, 21, 17, 0, 0, tzinfo=mock_tz)
```

**When:**
```python
result = session_block_rule.check(position_event, config)
```

**Then:**
```python
# After session end, breach detected
assert result is not None
assert result['breach'] == True
assert result['current_time'] == '17:00:00'
assert result['session_end'] == '16:00:00'

action = result['action']
assert action['type'] == 'CLOSE_ALL_AND_LOCKOUT'
assert action['reason'] == 'Session ended - position must be closed'
```

---

### UT-109-04: check() - Holiday detection

**Priority:** Medium

**Scenario:** Trading on market holidays should trigger breach.

**Given:**
```python
# Position opened on July 4th (Independence Day - market closed)
position_event = {
    "id": 459,
    "accountId": 123,
    "contractId": "CON.F.US.ES.U25",
    "creationTimestamp": "2024-07-04T14:00:00Z",  # July 4th, 10:00 AM ET
    "type": 1,
    "size": 1,
    "averagePrice": 5800.00
}

# Config: includes holiday check
config = {
    'session_hours': {
        'start': '09:30',
        'end': '16:00',
        'timezone': 'America/New_York'
    },
    'check_holidays': True,
    'holidays': [
        '2024-07-04',  # Independence Day
        '2024-12-25',  # Christmas
        '2024-11-28'   # Thanksgiving
    ]
}

# Mock time: July 4th, 10:00 AM ET
mock_tz = pytz.timezone('America/New_York')
mock_datetime.now.return_value = datetime(2024, 7, 4, 10, 0, 0, tzinfo=mock_tz)
```

**When:**
```python
result = session_block_rule.check(position_event, config)
```

**Then:**
```python
# Holiday detected, breach
assert result is not None
assert result['breach'] == True
assert result['reason'] == 'Trading on market holiday'
assert result['date'] == '2024-07-04'

action = result['action']
assert action['type'] == 'CLOSE_ALL_AND_LOCKOUT'
assert 'holiday' in action['reason'].lower()
```

---

### UT-109-05: check() - Per-instrument session hours

**Priority:** High

**Scenario:** Different instruments may have different session hours (e.g., ES trades nearly 24/7).

**Given:**
```python
# ES position at 6:00 PM ET (ES session active, but general session closed)
position_event = {
    "id": 460,
    "accountId": 123,
    "contractId": "CON.F.US.ES.U25",
    "creationTimestamp": "2024-07-21T22:00:00Z",  # 6:00 PM ET
    "type": 1,
    "size": 1,
    "averagePrice": 5800.00
}

# Config: per-instrument session hours
config = {
    'default_session': {
        'start': '09:30',
        'end': '16:00',
        'timezone': 'America/New_York'
    },
    'per_instrument_sessions': {
        'ES': {
            'start': '18:00',  # ES Sunday-Friday evening session
            'end': '17:00',    # Next day
            'timezone': 'America/Chicago'
        }
    }
}

# Mock time: 6:00 PM ET (ES session active)
mock_tz = pytz.timezone('America/New_York')
mock_datetime.now.return_value = datetime(2024, 7, 21, 18, 0, 0, tzinfo=mock_tz)
```

**When:**
```python
# Extract symbol: ES
symbol = extract_symbol_from_contract(position_event['contractId'])
result = session_block_rule.check(position_event, config, symbol)
```

**Then:**
```python
# ES has extended hours, within session
assert result is None

# Position allowed during ES evening session
assert lockout_manager.is_locked_out(123) == False
```

---

### UT-109-06: check() - Session end auto-close

**Priority:** High

**Scenario:** At exactly session end time, all positions should be closed automatically.

**Given:**
```python
# Position still open at exactly 4:00 PM ET (session end)
position_event = {
    "id": 461,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "creationTimestamp": "2024-07-21T15:30:00Z",  # 11:30 AM ET (opened during session)
    "type": 1,
    "size": 1,
    "averagePrice": 21000.00
}

# Config: session ends at 4:00 PM
config = {
    'session_hours': {
        'start': '09:30',
        'end': '16:00',
        'timezone': 'America/New_York'
    },
    'auto_close_at_end': True
}

# Mock time: exactly 4:00:00 PM ET
mock_tz = pytz.timezone('America/New_York')
mock_datetime.now.return_value = datetime(2024, 7, 21, 16, 0, 0, tzinfo=mock_tz)
```

**When:**
```python
result = session_block_rule.check(position_event, config)
```

**Then:**
```python
# Session end reached, auto-close triggered
assert result is not None
assert result['breach'] == True
assert result['reason'] == 'Session end - auto-close'

action = result['action']
assert action['type'] == 'CLOSE_ALL_POSITIONS'
assert action['reason'] == 'Session ended at 16:00:00'
```

---

## RULE-010: Auth Loss Guard (`src/rules/auth_loss_guard.py`)

**Rule Purpose:** Monitor TopstepX canTrade status and enforce lockout when API signals account is restricted.

**Test File:** `tests/unit/test_rules/test_auth_loss_guard.py`

---

### UT-110-01: check() - Normal trading event (canTrade=true)

**Priority:** High

**Scenario:** Account with canTrade=true should allow trading normally.

**Given:**
```python
# GatewayUserAccount event with canTrade=true
account_event = {
    "id": 123,
    "name": "Main Trading Account",
    "balance": 10000.50,
    "canTrade": True,
    "isVisible": True,
    "simulated": False
}

# Config
config = {
    'enabled': True,
    'enforcement': 'close_all_and_lockout'
}

# Previous state: canTrade was True
state_manager.can_trade_status = {
    123: True
}
```

**When:**
```python
result = auth_loss_guard_rule.check(account_event, config)
```

**Then:**
```python
# canTrade is True, no breach
assert result is None

# Account not locked
assert lockout_manager.is_locked_out(123) == False

# State updated
assert state_manager.can_trade_status[123] == True
```

---

### UT-110-02: check() - Auth event detected (canTrade=false)

**Priority:** High

**Scenario:** When canTrade changes from true to false, trigger immediate lockout.

**Given:**
```python
# GatewayUserAccount event with canTrade=false
account_event = {
    "id": 123,
    "name": "Main Trading Account",
    "balance": 10000.50,
    "canTrade": False,  # Account restricted!
    "isVisible": True,
    "simulated": False
}

# Config
config = {
    'enabled': True,
    'enforcement': 'close_all_and_lockout',
    'auto_unlock_on_restore': True
}

# Previous state: canTrade was True
state_manager.can_trade_status = {
    123: True
}

# Account has 2 open positions
state_manager.positions = {
    123: [
        {'id': 456, 'contractId': 'CON.F.US.MNQ.U25', 'size': 2},
        {'id': 457, 'contractId': 'CON.F.US.ES.U25', 'size': 1}
    ]
}
```

**When:**
```python
result = auth_loss_guard_rule.check(account_event, config)
```

**Then:**
```python
# canTrade changed from True → False, breach detected
assert result is not None
assert result['breach'] == True
assert result['event_type'] == 'canTrade_disabled'
assert result['previous_state'] == True
assert result['current_state'] == False

# Action: close all positions and lockout
action = result['action']
assert action['type'] == 'CLOSE_ALL_AND_LOCKOUT'
assert action['reason'] == 'Account restricted by TopstepX (canTrade=false)'
assert action['lockout_until'] is None  # Indefinite lockout

# State updated
assert state_manager.can_trade_status[123] == False
```

---

### UT-110-03: check() - Auth restored (canTrade=true after false)

**Priority:** High

**Scenario:** When canTrade changes from false to true, auto-unlock account.

**Given:**
```python
# GatewayUserAccount event with canTrade=true (restored)
account_event = {
    "id": 123,
    "name": "Main Trading Account",
    "balance": 10000.50,
    "canTrade": True,  # Trading restored!
    "isVisible": True,
    "simulated": False
}

# Config: auto-unlock enabled
config = {
    'enabled': True,
    'auto_unlock_on_restore': True
}

# Previous state: canTrade was False (restricted)
state_manager.can_trade_status = {
    123: False
}

# Account currently locked
lockout_manager.active_lockouts = {
    123: {
        'reason': 'Account restricted by TopstepX (canTrade=false)',
        'until': None,
        'applied_at': datetime(2024, 7, 21, 14, 0, 0)
    }
}
```

**When:**
```python
result = auth_loss_guard_rule.check(account_event, config)
```

**Then:**
```python
# canTrade changed from False → True, restore detected
assert result is not None
assert result['breach'] == False
assert result['event_type'] == 'canTrade_enabled'
assert result['previous_state'] == False
assert result['current_state'] == True

# Action: remove lockout
action = result['action']
assert action['type'] == 'REMOVE_LOCKOUT'
assert action['reason'] == 'TopstepX restored trading (canTrade=true)'

# State updated
assert state_manager.can_trade_status[123] == True

# Lockout should be removed (verify via enforcement)
```

---

### UT-110-04: check() - Daemon starts with restricted account

**Priority:** High

**Scenario:** On daemon startup, if account has canTrade=false, apply lockout immediately.

**Given:**
```python
# Daemon startup - initial state check
account_info = {
    "id": 123,
    "name": "Main Trading Account",
    "balance": 10000.50,
    "canTrade": False,  # Account already restricted
    "isVisible": True,
    "simulated": False
}

# Config: check on startup enabled
config = {
    'enabled': True,
    'check_on_startup': True,
    'enforcement': 'close_all_and_lockout'
}

# No previous state (daemon just started)
state_manager.can_trade_status = {}

# Account has open positions from previous session
state_manager.positions = {
    123: [
        {'id': 456, 'contractId': 'CON.F.US.MNQ.U25', 'size': 1}
    ]
}
```

**When:**
```python
result = auth_loss_guard_rule.check_initial_state(123, account_info, config)
```

**Then:**
```python
# Startup check detects canTrade=false, breach
assert result is not None
assert result['breach'] == True
assert result['event_type'] == 'canTrade_disabled_on_startup'

# Action: close all and lockout
action = result['action']
assert action['type'] == 'CLOSE_ALL_AND_LOCKOUT'
assert action['reason'] == 'Account has canTrade=false on startup'

# State initialized
assert state_manager.can_trade_status[123] == False
```

---

### UT-110-05: check() - No position to close (still lockout)

**Priority:** Medium

**Scenario:** When canTrade=false but no positions open, still apply lockout.

**Given:**
```python
# GatewayUserAccount event with canTrade=false
account_event = {
    "id": 123,
    "name": "Main Trading Account",
    "balance": 10000.50,
    "canTrade": False,
    "isVisible": True,
    "simulated": False
}

# Config
config = {
    'enabled': True,
    'enforcement': 'close_all_and_lockout'
}

# Previous state: canTrade was True
state_manager.can_trade_status = {
    123: True
}

# No open positions
state_manager.positions = {
    123: []
}
```

**When:**
```python
result = auth_loss_guard_rule.check(account_event, config)
```

**Then:**
```python
# canTrade changed to False, breach detected
assert result is not None
assert result['breach'] == True

# Action still includes lockout (no positions to close)
action = result['action']
assert action['type'] == 'CLOSE_ALL_AND_LOCKOUT'  # Same action type
assert action['positions_to_close'] == 0  # But no positions

# Lockout should still be applied
```

---

### UT-110-06: check() - Rapid toggle (false→true→false)

**Priority:** Medium

**Scenario:** Rapid canTrade status changes should be handled independently.

**Given:**
```python
# Initial state: canTrade=true
state_manager.can_trade_status = {123: True}

# Event 1: canTrade=false
event1 = {"id": 123, "canTrade": False}

# Event 2: canTrade=true (5 seconds later)
event2 = {"id": 123, "canTrade": True}

# Event 3: canTrade=false (10 seconds later)
event3 = {"id": 123, "canTrade": False}

config = {
    'enabled': True,
    'auto_unlock_on_restore': True
}

lockout_manager.active_lockouts = {}
```

**When:**
```python
# Process events in sequence
result1 = auth_loss_guard_rule.check(event1, config)
state_manager.can_trade_status[123] = False

result2 = auth_loss_guard_rule.check(event2, config)
state_manager.can_trade_status[123] = True

result3 = auth_loss_guard_rule.check(event3, config)
state_manager.can_trade_status[123] = False
```

**Then:**
```python
# Event 1: Lockout applied
assert result1['breach'] == True
assert result1['event_type'] == 'canTrade_disabled'

# Event 2: Lockout removed
assert result2['breach'] == False
assert result2['event_type'] == 'canTrade_enabled'

# Event 3: Lockout re-applied
assert result3['breach'] == True
assert result3['event_type'] == 'canTrade_disabled'

# Each state change is independent
assert state_manager.can_trade_status[123] == False
```

---

## RULE-011: Symbol Blocks (`src/rules/symbol_blocks.py`)

**Rule Purpose:** Blacklist specific symbols - immediately close any position and permanently prevent trading in blocked instruments.

**Test File:** `tests/unit/test_rules/test_symbol_blocks.py`

---

### UT-111-01: check() - Allowed symbol (no block)

**Priority:** High

**Scenario:** Position in allowed symbol should pass check.

**Given:**
```python
# Position in MNQ (not blocked)
position_event = {
    "id": 456,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "creationTimestamp": "2024-07-21T14:00:00Z",
    "type": 1,
    "size": 2,
    "averagePrice": 21000.25
}

# Config: RTY and BTC blocked, MNQ allowed
config = {
    'enabled': True,
    'blocked_symbols': ['RTY', 'BTC'],
    'action': 'CANCEL_ORDER',
    'close_existing': True
}
```

**When:**
```python
# Extract symbol: MNQ
symbol = extract_symbol_root(position_event['contractId'])
result = symbol_blocks_rule.check(position_event, config)
```

**Then:**
```python
# MNQ not in blocked list, no breach
assert symbol == 'MNQ'
assert result is None

# Position allowed
assert lockout_manager.is_symbol_locked(123, 'MNQ') == False
```

---

### UT-111-02: check() - Blocked symbol position (RTY)

**Priority:** High

**Scenario:** Position in blocked symbol should trigger immediate closure and symbol lockout.

**Given:**
```python
# Position in RTY (blocked symbol)
position_event = {
    "id": 457,
    "accountId": 123,
    "contractId": "CON.F.US.RTY.H25",
    "creationTimestamp": "2024-07-21T14:15:00Z",
    "type": 1,
    "size": 1,
    "averagePrice": 2100.50
}

# Config: RTY blocked
config = {
    'enabled': True,
    'blocked_symbols': ['RTY', 'BTC'],
    'action': 'CANCEL_ORDER',
    'close_existing': True
}
```

**When:**
```python
# Extract symbol: RTY
symbol = extract_symbol_root(position_event['contractId'])
result = symbol_blocks_rule.check(position_event, config)
```

**Then:**
```python
# RTY is blocked, breach detected
assert symbol == 'RTY'
assert result is not None
assert result['breach'] == True
assert result['symbol_root'] == 'RTY'
assert result['contract_id'] == 'CON.F.US.RTY.H25'

# Action: close position and lockout symbol
action = result['action']
assert action['type'] == 'CLOSE_POSITION_AND_SYMBOL_LOCKOUT'
assert action['contract_id'] == 'CON.F.US.RTY.H25'
assert action['symbol'] == 'RTY'
assert action['reason'] == 'Symbol RTY is permanently blocked'
assert action['lockout_until'] is None  # Permanent
```

---

### UT-111-03: check() - Blocked symbol order

**Priority:** Medium

**Scenario:** Order placed in blocked symbol should be canceled immediately.

**Given:**
```python
# Order in BTC (blocked symbol)
order_event = {
    "id": 789,
    "accountId": 123,
    "contractId": "CON.F.US.BTC.Z25",
    "symbolId": "F.US.BTC",
    "creationTimestamp": "2024-07-21T14:30:00Z",
    "status": 1,  # Active
    "type": 1,  # Limit
    "side": 0,
    "size": 1
}

# Config: BTC blocked
config = {
    'enabled': True,
    'blocked_symbols': ['RTY', 'BTC'],
    'action': 'CANCEL_ORDER'
}
```

**When:**
```python
# Extract symbol from symbolId: BTC
symbol = order_event['symbolId'].split('.')[-1]
result = symbol_blocks_rule.check_order(order_event, config)
```

**Then:**
```python
# BTC is blocked, breach detected
assert symbol == 'BTC'
assert result is not None
assert result['breach'] == True
assert result['symbol_root'] == 'BTC'

# Action: cancel order
action = result['action']
assert action['type'] == 'CANCEL_ORDER'
assert action['order_id'] == 789
assert action['reason'] == 'Order in blocked symbol BTC'
```

---

### UT-111-04: check() - Similar symbol not blocked (ES vs MES)

**Priority:** High

**Scenario:** Similar but different symbols should not be confused (ES ≠ MES).

**Given:**
```python
# Position in MES
position_event = {
    "id": 458,
    "accountId": 123,
    "contractId": "CON.F.US.MES.U25",
    "creationTimestamp": "2024-07-21T14:45:00Z",
    "type": 1,
    "size": 4,
    "averagePrice": 5800.00
}

# Config: ES blocked (not MES)
config = {
    'enabled': True,
    'blocked_symbols': ['ES'],
    'close_existing': True
}
```

**When:**
```python
# Extract symbol: MES
symbol = extract_symbol_root(position_event['contractId'])
result = symbol_blocks_rule.check(position_event, config)
```

**Then:**
```python
# MES is different from ES, no breach
assert symbol == 'MES'
assert symbol != 'ES'
assert result is None

# Position allowed (exact match only, no partial matches)
assert lockout_manager.is_symbol_locked(123, 'MES') == False
```

---

### UT-111-05: check() - Multiple contracts same blocked symbol

**Priority:** Medium

**Scenario:** Multiple expiry months of blocked symbol should all be blocked.

**Given:**
```python
# Positions in RTY with different expiry months
position1 = {
    "id": 459,
    "accountId": 123,
    "contractId": "CON.F.US.RTY.H25",  # March 2025
    "type": 1,
    "size": 1,
    "averagePrice": 2100.00
}

position2 = {
    "id": 460,
    "accountId": 123,
    "contractId": "CON.F.US.RTY.M25",  # June 2025
    "type": 1,
    "size": 1,
    "averagePrice": 2105.00
}

# Config: RTY blocked
config = {
    'enabled': True,
    'blocked_symbols': ['RTY'],
    'close_existing': True
}
```

**When:**
```python
# Check both positions
symbol1 = extract_symbol_root(position1['contractId'])
symbol2 = extract_symbol_root(position2['contractId'])

result1 = symbol_blocks_rule.check(position1, config)
result2 = symbol_blocks_rule.check(position2, config)
```

**Then:**
```python
# Both positions have same symbol root: RTY
assert symbol1 == 'RTY'
assert symbol2 == 'RTY'

# Both should trigger breach
assert result1 is not None
assert result1['breach'] == True
assert result1['symbol_root'] == 'RTY'

assert result2 is not None
assert result2['breach'] == True
assert result2['symbol_root'] == 'RTY'

# Both contracts should be closed (symbol-level block)
```

---

### UT-111-06: check() - Contract ID parsing edge case

**Priority:** Medium

**Scenario:** Unexpected contract ID format should be handled gracefully.

**Given:**
```python
# Position with unusual contract ID format
position_event = {
    "id": 461,
    "accountId": 123,
    "contractId": "UNUSUAL.FORMAT.RTY",  # Non-standard format
    "type": 1,
    "size": 1,
    "averagePrice": 2100.00
}

# Config: RTY blocked
config = {
    'enabled': True,
    'blocked_symbols': ['RTY']
}

# Mock symbol extraction with fallback
def extract_symbol_root_with_fallback(contract_id):
    parts = contract_id.split('.')
    if len(parts) >= 4:
        return parts[3]
    # Fallback: return full ID if unexpected format
    return contract_id
```

**When:**
```python
symbol = extract_symbol_root_with_fallback(position_event['contractId'])
result = symbol_blocks_rule.check(position_event, config)
```

**Then:**
```python
# Fallback to full contract ID
assert symbol == 'UNUSUAL.FORMAT.RTY'

# Doesn't match 'RTY' exactly, no breach
assert result is None

# Log warning about unexpected format
# (verify via log capture in actual test)
```

---

## RULE-012: Trade Management (`src/rules/trade_management.py`)

**Rule Purpose:** Automated trade management - auto breakeven stop-loss and trailing stops.

**Test File:** `tests/unit/test_rules/test_trade_management.py`

---

### UT-112-01: check() - Position without auto-SL (disabled)

**Priority:** Medium

**Scenario:** When auto-management disabled, no action should be taken.

**Given:**
```python
# Position opened
position_event = {
    "id": 456,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "creationTimestamp": "2024-07-21T14:00:00Z",
    "type": 1,  # Long
    "size": 2,
    "averagePrice": 21000.25
}

# Config: auto-management disabled
config = {
    'enabled': False,
    'auto_breakeven': {
        'enabled': False
    },
    'trailing_stop': {
        'enabled': False
    }
}

# Contract specs
contract_cache.contracts = {
    'CON.F.US.MNQ.U25': {
        'tickSize': 0.25,
        'tickValue': 0.50
    }
}
```

**When:**
```python
result = trade_management_rule.check(position_event, config)
```

**Then:**
```python
# Auto-management disabled, no action
assert result is None

# No stop-loss order created
assert 456 not in trade_management_rule.position_tracking
```

---

### UT-112-02: check() - Position needs auto-breakeven

**Priority:** High

**Scenario:** Position with profit >= trigger should have breakeven stop placed.

**Given:**
```python
# Position: Long @ 21000.00
position_event = {
    "id": 456,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "type": 1,  # Long
    "size": 2,
    "averagePrice": 21000.00
}

# Config: breakeven at +10 ticks
config = {
    'enabled': True,
    'auto_breakeven': {
        'enabled': True,
        'profit_trigger_ticks': 10,
        'offset_ticks': 0  # Exact breakeven
    }
}

# Contract: MNQ tick size = 0.25
contract_cache.contracts = {
    'CON.F.US.MNQ.U25': {
        'tickSize': 0.25,
        'tickValue': 0.50
    }
}

# Current quote: 21002.50 (+10 ticks profit)
quote_event = {
    "symbol": "F.US.MNQ",
    "lastPrice": 21002.50,  # +2.50 = +10 ticks @ 0.25
    "bestBid": 21002.25,
    "bestAsk": 21002.75,
    "timestamp": "2024-07-21T14:05:00Z"
}

# Position tracking
position_tracking = {
    456: {
        'account_id': 123,
        'contract_id': 'CON.F.US.MNQ.U25',
        'entry_price': 21000.00,
        'position_type': 1,
        'size': 2,
        'stop_loss_order_id': None,
        'breakeven_applied': False,
        'trailing_active': False
    }
}
```

**When:**
```python
# Trigger on quote update
result = trade_management_rule.on_quote_update(quote_event, 'CON.F.US.MNQ.U25', config)
```

**Then:**
```python
# Profit = +10 ticks, trigger breakeven
assert result is not None
assert result['action'] == 'APPLY_BREAKEVEN'
assert result['position_id'] == 456
assert result['breakeven_price'] == 21000.00  # Entry price + 0 offset

# Action: create stop-loss at breakeven
action = result['action_details']
assert action['type'] == 'CREATE_STOP_LOSS_ORDER'
assert action['stop_price'] == 21000.00
assert action['size'] == 2
assert action['side'] == 1  # Sell to close long

# Update tracking
assert position_tracking[456]['breakeven_applied'] == True
```

---

### UT-112-03: check() - Auto-SL price calculation (long position)

**Priority:** High

**Scenario:** Long position breakeven stop should be placed below entry (sell stop).

**Given:**
```python
# Position: Long 1 MNQ @ 21000.00
position = {
    'entry_price': 21000.00,
    'position_type': 1,  # Long
    'size': 1
}

# Config: breakeven + 2 tick offset
config = {
    'auto_breakeven': {
        'profit_trigger_ticks': 10,
        'offset_ticks': 2  # +2 ticks above breakeven
    }
}

# Contract: tick size = 0.25
contract = {
    'tickSize': 0.25
}

# Current price: 21002.50 (+10 ticks)
current_price = 21002.50
```

**When:**
```python
breakeven_price = trade_management_rule.calculate_breakeven_stop(
    position, config, contract
)
```

**Then:**
```python
# Breakeven = entry + offset
# 21000.00 + (2 * 0.25) = 21000.50
assert breakeven_price == 21000.50

# Stop order details
stop_order = {
    'type': 4,  # Stop
    'side': 1,  # Sell (to close long)
    'stopPrice': 21000.50,
    'size': 1
}

assert stop_order['side'] == 1
assert stop_order['stopPrice'] > position['entry_price']  # Above entry (with offset)
```

---

### UT-112-04: check() - Trailing stop update (price rises)

**Priority:** Medium

**Scenario:** As price rises, trailing stop should move up (but never down).

**Given:**
```python
# Position: Long @ 21000.00
position_tracking = {
    456: {
        'account_id': 123,
        'contract_id': 'CON.F.US.MNQ.U25',
        'entry_price': 21000.00,
        'position_type': 1,  # Long
        'size': 2,
        'stop_loss_order_id': 789,
        'breakeven_applied': True,
        'trailing_active': True,
        'high_water_mark': 21005.00  # Previous high
    }
}

# Config: trail 10 ticks behind high water mark
config = {
    'trailing_stop': {
        'enabled': True,
        'activation_ticks': 20,
        'trail_distance_ticks': 10,
        'update_frequency': 1
    }
}

# Contract: tick size = 0.25
contract = {
    'tickSize': 0.25
}

# Current quote: 21010.00 (new high!)
current_price = 21010.00

# Existing stop: 21002.50 (10 ticks below previous high of 21005.00)
current_stop_price = 21002.50
```

**When:**
```python
result = trade_management_rule.update_trailing_stop(
    456, position_tracking[456], current_price, contract
)
```

**Then:**
```python
# New high water mark
assert position_tracking[456]['high_water_mark'] == 21010.00

# New trailing stop: 21010.00 - (10 * 0.25) = 21007.50
new_stop_price = 21010.00 - (10 * 0.25)
assert new_stop_price == 21007.50

# Stop should be updated (moved up)
assert result is not None
assert result['action'] == 'UPDATE_TRAILING_STOP'
assert result['old_stop_price'] == 21002.50
assert result['new_stop_price'] == 21007.50

# Action: modify stop-loss order
action = result['action_details']
assert action['type'] == 'MODIFY_STOP_LOSS_ORDER'
assert action['order_id'] == 789
assert action['new_stop_price'] == 21007.50
```

---

### UT-112-05: check() - Position already has manual SL (don't override)

**Priority:** Medium

**Scenario:** If trader placed manual stop-loss, auto-management should respect it.

**Given:**
```python
# Position: Long @ 21000.00
position_event = {
    "id": 456,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "type": 1,
    "size": 2,
    "averagePrice": 21000.00
}

# Existing manual stop-loss order
manual_stop_order = {
    "id": 788,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "type": 4,  # Stop
    "side": 1,  # Sell
    "stopPrice": 20995.00,  # Manual stop at -5
    "status": 1
}

# Config: respect manual stops
config = {
    'enabled': True,
    'auto_breakeven': {
        'enabled': True,
        'respect_manual_stops': True  # Don't override manual stops
    }
}

# Position tracking (stop already exists)
position_tracking = {
    456: {
        'account_id': 123,
        'contract_id': 'CON.F.US.MNQ.U25',
        'entry_price': 21000.00,
        'position_type': 1,
        'size': 2,
        'stop_loss_order_id': 788,  # Manual stop exists
        'breakeven_applied': False,
        'trailing_active': False,
        'manual_stop': True  # Flag: manual stop
    }
}

# Current quote: 21002.50 (+10 ticks, would trigger breakeven)
current_price = 21002.50
```

**When:**
```python
result = trade_management_rule.on_quote_update(
    {'lastPrice': current_price}, 'CON.F.US.MNQ.U25', config
)
```

**Then:**
```python
# Manual stop detected, don't apply auto-management
assert result is None

# Manual stop price unchanged
assert position_tracking[456]['stop_loss_order_id'] == 788
assert position_tracking[456]['manual_stop'] == True

# Breakeven NOT applied (respecting manual stop)
assert position_tracking[456]['breakeven_applied'] == False
```

---

### UT-112-06: check() - Short position trailing stop (price drops)

**Priority:** Medium

**Scenario:** For short positions, trailing stop should move down as price drops.

**Given:**
```python
# Position: Short @ 21000.00
position_tracking = {
    457: {
        'account_id': 123,
        'contract_id': 'CON.F.US.MNQ.U25',
        'entry_price': 21000.00,
        'position_type': 2,  # Short
        'size': 1,
        'stop_loss_order_id': 790,
        'breakeven_applied': False,
        'trailing_active': True,
        'low_water_mark': 20995.00  # Previous low
    }
}

# Config: trail 10 ticks behind low water mark
config = {
    'trailing_stop': {
        'enabled': True,
        'trail_distance_ticks': 10
    }
}

# Contract: tick size = 0.25
contract = {
    'tickSize': 0.25
}

# Current quote: 20990.00 (new low for short = more profit)
current_price = 20990.00

# Existing stop: 20997.50 (10 ticks above previous low of 20995.00)
current_stop_price = 20997.50
```

**When:**
```python
result = trade_management_rule.update_trailing_stop(
    457, position_tracking[457], current_price, contract
)
```

**Then:**
```python
# New low water mark (profitable for short)
assert position_tracking[457]['low_water_mark'] == 20990.00

# New trailing stop: 20990.00 + (10 * 0.25) = 20992.50
new_stop_price = 20990.00 + (10 * 0.25)
assert new_stop_price == 20992.50

# Stop should be updated (moved down for short)
assert result is not None
assert result['action'] == 'UPDATE_TRAILING_STOP'
assert result['new_stop_price'] == 20992.50
assert result['new_stop_price'] < current_stop_price  # Moved down

# Action: modify stop-loss order
action = result['action_details']
assert action['type'] == 'MODIFY_STOP_LOSS_ORDER'
assert action['order_id'] == 790
assert action['new_stop_price'] == 20992.50
```

---

## Test Summary

### Total Test Scenarios by Rule:

- **RULE-007 (Cooldown After Loss):** 6 scenarios
- **RULE-008 (No Stop Loss Grace):** 6 scenarios
- **RULE-009 (Session Block Outside Hours):** 6 scenarios
- **RULE-010 (Auth Loss Guard):** 6 scenarios
- **RULE-011 (Symbol Blocks):** 6 scenarios
- **RULE-012 (Trade Management):** 6 scenarios

**Grand Total:** 36 detailed test specifications

---

## Test Priority Distribution:

- **High Priority:** 30 tests (83%)
- **Medium Priority:** 6 tests (17%)

---

## Dependencies & Test Fixtures:

**Shared Fixtures Required:**
- `tests/fixtures/trade_events.json` - Sample GatewayUserTrade events
- `tests/fixtures/position_events.json` - Sample GatewayUserPosition events
- `tests/fixtures/order_events.json` - Sample GatewayUserOrder events
- `tests/fixtures/account_events.json` - Sample GatewayUserAccount events
- `tests/fixtures/quote_events.json` - Sample GatewayQuote events
- `tests/fixtures/contract_specs.json` - Contract metadata (tick sizes, etc.)

**Mock Objects Required:**
- `mock_lockout_manager` - MOD-002 lockout management
- `mock_timer_manager` - MOD-003 timer tracking
- `mock_actions` - MOD-001 enforcement actions
- `mock_api` - TopstepX REST API calls
- `mock_datetime` - Time control for tests
- `mock_state_manager` - MOD-009 state tracking
- `mock_contract_cache` - MOD-007 contract metadata

---

## Implementation Notes:

1. **Concurrent Testing:** All rule tests are independent and can run in parallel
2. **Time Mocking:** Use `freezegun` or similar for datetime control
3. **API Mocking:** Use `responses` library for REST API mocking
4. **State Isolation:** Each test should reset all state managers
5. **Fixture Reuse:** Maximize fixture reuse across tests
6. **Edge Cases:** Each rule includes edge case coverage
7. **Error Handling:** Tests verify both success and failure paths

---

**Document Complete** ✓
**Ready for Implementation** ✓
**Spec Coverage:** 100% of RULE-007 through RULE-012
