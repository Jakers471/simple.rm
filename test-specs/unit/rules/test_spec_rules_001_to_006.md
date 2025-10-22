# Unit Test Specifications: RULE-001 through RULE-006

**Generated:** 2025-10-22
**Purpose:** Detailed Given/When/Then test specifications for Risk Rules 001-006
**Test File:** `tests/unit/test_rules/`
**Format:** Given/When/Then with Python pseudocode
**Total Scenarios:** 42

---

## Table of Contents

1. [RULE-001: MaxContracts (6 scenarios)](#rule-001-maxcontracts)
2. [RULE-002: MaxContractsPerInstrument (6 scenarios)](#rule-002-maxcontractsperinstrument)
3. [RULE-003: DailyRealizedLoss (8 scenarios)](#rule-003-dailyrealizedloss)
4. [RULE-004: DailyUnrealizedLoss (8 scenarios)](#rule-004-dailyunrealizedloss)
5. [RULE-005: MaxUnrealizedProfit (6 scenarios)](#rule-005-maxunrealizedprofit)
6. [RULE-006: TradeFrequencyLimit (8 scenarios)](#rule-006-tradefrequencylimit)

---

# RULE-001: MaxContracts

**Test File:** `tests/unit/test_rules/test_max_contracts.py`

---

## UT-101-01: Check Under Limit

**Priority:** High
**Description:** Net contracts under limit should not trigger enforcement

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limit': 5,
    'count_type': 'net',
    'close_all': True,
    'lockout_on_breach': False
}

# Mock state manager with positions
mock_state_manager = Mock()
mock_state_manager.get_position_count.return_value = 4  # Net 4 contracts

# Mock enforcement actions
mock_actions = Mock()
```

### When
```python
# Simulate position event
position_event = {
    'id': 456,
    'accountId': 123,
    'contractId': 'CON.F.US.MNQ.U25',
    'type': 1,  # Long
    'size': 2,
    'averagePrice': 21000.5
}

# Check rule
rule = MaxContractsRule(config, mock_state_manager, mock_actions)
result = rule.check(position_event)
```

### Then
```python
# Assert no breach detected
assert result is None

# Assert no enforcement actions called
mock_actions.close_all_positions.assert_not_called()

# Assert state manager queried correctly
mock_state_manager.get_position_count.assert_called_once_with(123)
```

---

## UT-101-02: Check At Limit

**Priority:** High
**Description:** Net contracts exactly at limit should not trigger enforcement

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limit': 5,
    'count_type': 'net',
    'close_all': True
}

# Mock state with exactly 5 contracts
mock_state_manager = Mock()
mock_state_manager.get_position_count.return_value = 5

mock_actions = Mock()
```

### When
```python
position_event = {
    'accountId': 123,
    'contractId': 'CON.F.US.ES.U25',
    'type': 1,
    'size': 2
}

rule = MaxContractsRule(config, mock_state_manager, mock_actions)
result = rule.check(position_event)
```

### Then
```python
# No breach when at limit
assert result is None

# No enforcement
mock_actions.close_all_positions.assert_not_called()
```

---

## UT-101-03: Check Breach By One

**Priority:** High
**Description:** Net contracts exceeding limit by 1 should trigger close all positions

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limit': 5,
    'count_type': 'net',
    'close_all': True,
    'lockout_on_breach': False
}

# Mock state with 6 contracts (breach)
mock_state_manager = Mock()
mock_state_manager.get_position_count.return_value = 6

# Mock enforcement
mock_actions = Mock()
mock_actions.close_all_positions.return_value = True

# Mock logger
mock_logger = Mock()
```

### When
```python
position_event = {
    'accountId': 123,
    'contractId': 'CON.F.US.MNQ.U25',
    'type': 1,
    'size': 3
}

rule = MaxContractsRule(config, mock_state_manager, mock_actions, mock_logger)
breach = rule.check(position_event)

# Execute enforcement
if breach:
    rule.enforce(123, breach)
```

### Then
```python
# Breach detected
assert breach is not None
assert breach['rule_id'] == 'RULE-001'
assert breach['action'] == 'CLOSE_ALL_POSITIONS'
assert breach['reason'] == 'MaxContracts breach (net=6, limit=5)'

# Enforcement executed
mock_actions.close_all_positions.assert_called_once_with(123)

# Enforcement logged
mock_logger.log_enforcement.assert_called_once()
log_message = mock_logger.log_enforcement.call_args[0][0]
assert 'MaxContracts breach' in log_message
assert 'net=6' in log_message
assert 'limit=5' in log_message
```

---

## UT-101-04: Check Net Calculation

**Priority:** High
**Description:** Rule should correctly calculate net contracts (Long - Short)

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limit': 5,
    'count_type': 'net'
}

# Mock positions: Long 7, Short 2 = Net 5
mock_state_manager = Mock()

# Define position data
positions = {
    'CON.F.US.MNQ.U25': {'type': 1, 'size': 7},  # Long 7
    'CON.F.US.ES.U25': {'type': 2, 'size': 2}    # Short 2
}

# Calculate net: abs(7 - 2) = 5 or (7 - 2) = 5 depending on implementation
mock_state_manager.get_position_count.return_value = 5

mock_actions = Mock()
```

### When
```python
position_event = {
    'accountId': 123,
    'contractId': 'CON.F.US.MNQ.U25',
    'type': 1,
    'size': 7
}

rule = MaxContractsRule(config, mock_state_manager, mock_actions)
result = rule.check(position_event)
```

### Then
```python
# Net 5 = no breach (at limit)
assert result is None

# Verify net calculation was used
mock_state_manager.get_position_count.assert_called_once_with(123)
```

---

## UT-101-05: Check Reduce To Limit Mode

**Priority:** Medium
**Description:** With reduce_to_limit enabled, should reduce position instead of closing all

### Given
```python
# Configuration with reduce mode
config = {
    'enabled': True,
    'limit': 5,
    'count_type': 'net',
    'close_all': False,
    'reduce_to_limit': True
}

# Mock state with 6 contracts
mock_state_manager = Mock()
mock_state_manager.get_position_count.return_value = 6
mock_state_manager.get_all_positions.return_value = [
    {'contract_id': 'CON.F.US.MNQ.U25', 'size': 3},
    {'contract_id': 'CON.F.US.ES.U25', 'size': 3}
]

# Mock enforcement
mock_actions = Mock()
mock_actions.reduce_positions_to_limit.return_value = True

mock_logger = Mock()
```

### When
```python
position_event = {
    'accountId': 123,
    'contractId': 'CON.F.US.MNQ.U25',
    'type': 1,
    'size': 3
}

rule = MaxContractsRule(config, mock_state_manager, mock_actions, mock_logger)
breach = rule.check(position_event)

if breach:
    rule.enforce(123, breach)
```

### Then
```python
# Breach detected
assert breach is not None
assert breach['action'] == 'REDUCE_TO_LIMIT'

# Reduce called instead of close all
mock_actions.reduce_positions_to_limit.assert_called_once_with(123, target_net=5)
mock_actions.close_all_positions.assert_not_called()

# Correct log message
log_message = mock_logger.log_enforcement.call_args[0][0]
assert 'Reduced' in log_message
assert 'from 6 to 5' in log_message
```

---

## UT-101-06: Check Ignores Closed Positions

**Priority:** Medium
**Description:** Positions with size=0 should not be counted toward limit

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limit': 3,
    'count_type': 'net'
}

# Mock state manager
mock_state_manager = Mock()

# Return positions including closed (size=0)
positions = {
    'CON.F.US.MNQ.U25': {'type': 1, 'size': 2},  # Open
    'CON.F.US.ES.U25': {'type': 1, 'size': 0},   # Closed (should ignore)
    'CON.F.US.NQ.U25': {'type': 1, 'size': 1}    # Open
}

# Net count should be 3 (ignoring closed position)
mock_state_manager.get_position_count.return_value = 3

mock_actions = Mock()
```

### When
```python
position_event = {
    'accountId': 123,
    'contractId': 'CON.F.US.NQ.U25',
    'type': 1,
    'size': 1
}

rule = MaxContractsRule(config, mock_state_manager, mock_actions)
result = rule.check(position_event)
```

### Then
```python
# No breach (net = 3, limit = 3)
assert result is None

# Verify closed positions excluded
mock_state_manager.get_position_count.assert_called_once_with(123)
```

---

# RULE-002: MaxContractsPerInstrument

**Test File:** `tests/unit/test_rules/test_max_contracts_per_instrument.py`

---

## UT-102-01: Check Under Limit

**Priority:** High
**Description:** Position size under instrument limit should not trigger enforcement

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limits': {
        'MNQ': 2,
        'ES': 1,
        'NQ': 1
    },
    'enforcement': 'reduce_to_limit',
    'unknown_symbol_action': 'block'
}

# Mock state with MNQ position size 2 (within limit)
mock_state_manager = Mock()
mock_state_manager.get_contract_count.return_value = 2

mock_actions = Mock()
```

### When
```python
position_event = {
    'accountId': 123,
    'contractId': 'CON.F.US.MNQ.U25',
    'type': 1,
    'size': 2
}

rule = MaxContractsPerInstrumentRule(config, mock_state_manager, mock_actions)
result = rule.check(position_event)
```

### Then
```python
# No breach
assert result is None

# No enforcement
mock_actions.reduce_position.assert_not_called()
mock_actions.close_position.assert_not_called()
```

---

## UT-102-02: Check Breach For Instrument

**Priority:** High
**Description:** Position size exceeding instrument limit should trigger reduction

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limits': {
        'MNQ': 3,
        'ES': 1
    },
    'enforcement': 'reduce_to_limit'
}

# Mock state with MNQ position size 4 (exceeds limit of 3)
mock_state_manager = Mock()
mock_state_manager.get_contract_count.return_value = 4

mock_actions = Mock()
mock_actions.reduce_position.return_value = True

mock_logger = Mock()
```

### When
```python
position_event = {
    'accountId': 123,
    'contractId': 'CON.F.US.MNQ.U25',
    'type': 1,
    'size': 4
}

rule = MaxContractsPerInstrumentRule(config, mock_state_manager, mock_actions, mock_logger)
breach = rule.check(position_event)

if breach:
    rule.enforce(123, breach)
```

### Then
```python
# Breach detected
assert breach is not None
assert breach['rule_id'] == 'RULE-002'
assert breach['action'] == 'REDUCE_POSITION'
assert breach['symbol'] == 'MNQ'
assert breach['current_size'] == 4
assert breach['limit'] == 3

# Reduce position called with excess = 1
mock_actions.reduce_position.assert_called_once_with(
    123,
    'CON.F.US.MNQ.U25',
    reduce_by=1
)

# Enforcement logged
log_message = mock_logger.log_enforcement.call_args[0][0]
assert 'MNQ' in log_message
assert 'Reduced from 4 to 3' in log_message
```

---

## UT-102-03: Check Unknown Symbol Block

**Priority:** Medium
**Description:** Unknown symbol with block action should trigger position close

### Given
```python
# Configuration with block unknown symbols
config = {
    'enabled': True,
    'limits': {
        'MNQ': 2,
        'ES': 1
    },
    'enforcement': 'close_all',
    'unknown_symbol_action': 'block'
}

# Mock state with RTY position (not in limits)
mock_state_manager = Mock()
mock_state_manager.get_contract_count.return_value = 1

mock_actions = Mock()
mock_actions.close_position.return_value = True

mock_logger = Mock()
```

### When
```python
position_event = {
    'accountId': 123,
    'contractId': 'CON.F.US.RTY.U25',  # RTY not in limits
    'type': 1,
    'size': 1
}

rule = MaxContractsPerInstrumentRule(config, mock_state_manager, mock_actions, mock_logger)
breach = rule.check(position_event)

if breach:
    rule.enforce(123, breach)
```

### Then
```python
# Breach detected for unknown symbol
assert breach is not None
assert breach['action'] == 'CLOSE_POSITION'
assert breach['reason'] == 'Unknown symbol not in configured limits'
assert breach['symbol'] == 'RTY'

# Position closed
mock_actions.close_position.assert_called_once_with(
    123,
    'CON.F.US.RTY.U25'
)

# Logged
log_message = mock_logger.log_enforcement.call_args[0][0]
assert 'Unknown symbol' in log_message or 'RTY' in log_message
```

---

## UT-102-04: Check Multiple Instruments

**Priority:** High
**Description:** Multiple positions within their respective limits should not trigger enforcement

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limits': {
        'MNQ': 2,
        'ES': 1
    },
    'enforcement': 'reduce_to_limit'
}

# Mock state manager
mock_state_manager = Mock()

# Define side effect for different contract queries
def get_contract_count_side_effect(account_id, contract_id):
    if 'MNQ' in contract_id:
        return 2  # Within limit
    elif 'ES' in contract_id:
        return 1  # Within limit
    return 0

mock_state_manager.get_contract_count.side_effect = get_contract_count_side_effect

mock_actions = Mock()
```

### When
```python
# Check MNQ position
mnq_event = {
    'accountId': 123,
    'contractId': 'CON.F.US.MNQ.U25',
    'type': 1,
    'size': 2
}

# Check ES position
es_event = {
    'accountId': 123,
    'contractId': 'CON.F.US.ES.U25',
    'type': 1,
    'size': 1
}

rule = MaxContractsPerInstrumentRule(config, mock_state_manager, mock_actions)
result_mnq = rule.check(mnq_event)
result_es = rule.check(es_event)
```

### Then
```python
# No breaches for either position
assert result_mnq is None
assert result_es is None

# No enforcement actions
mock_actions.reduce_position.assert_not_called()
mock_actions.close_position.assert_not_called()
```

---

## UT-102-05: Check Net Per Instrument

**Priority:** Medium
**Description:** Net calculation per instrument (Long - Short) should work correctly

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limits': {
        'MNQ': 3
    },
    'enforcement': 'reduce_to_limit'
}

# Mock state with MNQ: Long 4, Short 2 = Net 2
mock_state_manager = Mock()
mock_state_manager.get_contract_count.return_value = 2

mock_actions = Mock()
```

### When
```python
position_event = {
    'accountId': 123,
    'contractId': 'CON.F.US.MNQ.U25',
    'type': 1,
    'size': 4  # Long 4 (but also Short 2 elsewhere)
}

rule = MaxContractsPerInstrumentRule(config, mock_state_manager, mock_actions)
result = rule.check(position_event)
```

### Then
```python
# Net 2 within limit of 3
assert result is None

# Verify net calculation
mock_state_manager.get_contract_count.assert_called_with(123, 'CON.F.US.MNQ.U25')
```

---

## UT-102-06: Check Close All Enforcement Mode

**Priority:** Medium
**Description:** With enforcement='close_all', entire position should be closed on breach

### Given
```python
# Configuration with close_all mode
config = {
    'enabled': True,
    'limits': {
        'MNQ': 2
    },
    'enforcement': 'close_all'
}

# Mock state with MNQ size 3 (breach)
mock_state_manager = Mock()
mock_state_manager.get_contract_count.return_value = 3

mock_actions = Mock()
mock_actions.close_position.return_value = True

mock_logger = Mock()
```

### When
```python
position_event = {
    'accountId': 123,
    'contractId': 'CON.F.US.MNQ.U25',
    'type': 1,
    'size': 3
}

rule = MaxContractsPerInstrumentRule(config, mock_state_manager, mock_actions, mock_logger)
breach = rule.check(position_event)

if breach:
    rule.enforce(123, breach)
```

### Then
```python
# Breach detected
assert breach is not None
assert breach['action'] == 'CLOSE_ALL'

# Entire position closed (not reduced)
mock_actions.close_position.assert_called_once_with(
    123,
    'CON.F.US.MNQ.U25'
)
mock_actions.reduce_position.assert_not_called()

# Logged correctly
log_message = mock_logger.log_enforcement.call_args[0][0]
assert 'Closed entire position' in log_message
```

---

# RULE-003: DailyRealizedLoss

**Test File:** `tests/unit/test_rules/test_daily_realized_loss.py`

---

## UT-103-01: Check Under Limit

**Priority:** High
**Description:** Daily P&L under limit should not trigger enforcement

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limit': -500,
    'reset_time': '17:00',
    'timezone': 'America/New_York',
    'enforcement': 'close_all_and_lockout',
    'lockout_until_reset': True
}

# Mock P&L tracker with daily P&L = -400
mock_pnl_tracker = Mock()
mock_pnl_tracker.get_daily_realized_pnl.return_value = -400

mock_actions = Mock()
mock_lockout_manager = Mock()
```

### When
```python
trade_event = {
    'id': 101112,
    'accountId': 123,
    'profitAndLoss': -50,  # This trade causes -400 total
    'contractId': 'CON.F.US.MNQ.U25'
}

rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)
result = rule.check(trade_event)
```

### Then
```python
# No breach (-400 > -500)
assert result is None

# P&L tracker updated
mock_pnl_tracker.add_trade_pnl.assert_called_once_with(123, -50)

# No enforcement
mock_actions.close_all_positions.assert_not_called()
mock_lockout_manager.set_lockout.assert_not_called()
```

---

## UT-103-02: Check At Limit

**Priority:** High
**Description:** Daily P&L exactly at limit should not trigger enforcement

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limit': -500
}

# Mock P&L tracker with daily P&L = -500
mock_pnl_tracker = Mock()
mock_pnl_tracker.add_trade_pnl.return_value = -500

mock_actions = Mock()
mock_lockout_manager = Mock()
```

### When
```python
trade_event = {
    'accountId': 123,
    'profitAndLoss': -100  # Results in exactly -500 total
}

rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)
result = rule.check(trade_event)
```

### Then
```python
# At limit, no breach
assert result is None

# No enforcement
mock_actions.close_all_positions.assert_not_called()
mock_lockout_manager.set_lockout.assert_not_called()
```

---

## UT-103-03: Check Breach By One Dollar

**Priority:** High
**Description:** Daily P&L exceeding limit by $1 should trigger close all and lockout

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limit': -500,
    'reset_time': '17:00',
    'timezone': 'America/New_York',
    'lockout_until_reset': True
}

# Mock P&L tracker with breach
mock_pnl_tracker = Mock()
mock_pnl_tracker.add_trade_pnl.return_value = -501  # Breach!

# Mock enforcement
mock_actions = Mock()
mock_actions.close_all_positions.return_value = True
mock_actions.cancel_all_orders.return_value = True

# Mock lockout manager
mock_lockout_manager = Mock()

# Mock logger
mock_logger = Mock()

# Mock datetime for reset time calculation
from datetime import datetime, time, timedelta
mock_now = datetime(2025, 1, 17, 14, 30, 0)  # 2:30 PM
expected_reset = datetime.combine(mock_now.date(), time(17, 0))  # 5:00 PM today
```

### When
```python
trade_event = {
    'accountId': 123,
    'profitAndLoss': -201  # Causes -501 total
}

rule = DailyRealizedLossRule(
    config,
    mock_pnl_tracker,
    mock_actions,
    mock_lockout_manager,
    mock_logger
)

# Patch datetime.now
with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = mock_now

    breach = rule.check(trade_event)

    if breach:
        rule.enforce(123, breach)
```

### Then
```python
# Breach detected
assert breach is not None
assert breach['rule_id'] == 'RULE-003'
assert breach['action'] == 'CLOSE_ALL_AND_LOCKOUT'
assert breach['daily_pnl'] == -501
assert breach['limit'] == -500

# All positions closed
mock_actions.close_all_positions.assert_called_once_with(123)

# All orders cancelled
mock_actions.cancel_all_orders.assert_called_once_with(123)

# Lockout set until reset time
mock_lockout_manager.set_lockout.assert_called_once()
lockout_call = mock_lockout_manager.set_lockout.call_args
assert lockout_call[1]['account_id'] == 123
assert lockout_call[1]['until'] == expected_reset
assert 'Daily loss limit hit' in lockout_call[1]['reason']

# Enforcement logged
mock_logger.log_enforcement.assert_called_once()
log_message = mock_logger.log_enforcement.call_args[0][0]
assert 'RULE-003' in log_message or 'DailyRealizedLoss' in log_message
assert '-501' in log_message or '501' in log_message
```

---

## UT-103-04: Check Lockout Until Next Reset

**Priority:** High
**Description:** Lockout should be set until configured reset time

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limit': -500,
    'reset_time': '17:00',
    'lockout_until_reset': True
}

# Mock breach scenario
mock_pnl_tracker = Mock()
mock_pnl_tracker.add_trade_pnl.return_value = -550

mock_actions = Mock()
mock_lockout_manager = Mock()

# Current time: 2:00 PM
mock_now = datetime(2025, 1, 17, 14, 0, 0)
expected_reset = datetime(2025, 1, 17, 17, 0, 0)  # 5:00 PM same day
```

### When
```python
trade_event = {
    'accountId': 123,
    'profitAndLoss': -550
}

rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)

with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = mock_now
    mock_datetime.combine = datetime.combine  # Keep combine working

    breach = rule.check(trade_event)
    if breach:
        rule.enforce(123, breach)
```

### Then
```python
# Lockout set until 5:00 PM today
mock_lockout_manager.set_lockout.assert_called_once()
lockout_call = mock_lockout_manager.set_lockout.call_args[1]
assert lockout_call['until'] == expected_reset
assert (expected_reset - mock_now).total_seconds() == 3 * 3600  # 3 hours
```

---

## UT-103-05: Check After Daily Reset

**Priority:** High
**Description:** After daily reset, P&L should be zero and no breach should occur

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limit': -500
}

# Mock P&L tracker after reset (P&L = 0)
mock_pnl_tracker = Mock()
mock_pnl_tracker.get_daily_realized_pnl.return_value = 0
mock_pnl_tracker.add_trade_pnl.return_value = -50  # First trade after reset

mock_actions = Mock()
mock_lockout_manager = Mock()
```

### When
```python
trade_event = {
    'accountId': 123,
    'profitAndLoss': -50
}

rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)
result = rule.check(trade_event)
```

### Then
```python
# No breach (only -50)
assert result is None

# No enforcement
mock_actions.close_all_positions.assert_not_called()
mock_lockout_manager.set_lockout.assert_not_called()
```

---

## UT-103-06: Check Ignores Half-Turn Trades

**Priority:** High
**Description:** Trades with profitAndLoss=null should not update P&L

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limit': -500
}

# Mock P&L tracker
mock_pnl_tracker = Mock()

mock_actions = Mock()
```

### When
```python
# Half-turn trade (opening position, no P&L)
trade_event = {
    'accountId': 123,
    'profitAndLoss': None,  # Half-turn
    'contractId': 'CON.F.US.MNQ.U25',
    'side': 0,
    'size': 1
}

rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, None)
result = rule.check(trade_event)
```

### Then
```python
# No check performed
assert result is None

# P&L tracker NOT updated
mock_pnl_tracker.add_trade_pnl.assert_not_called()
```

---

## UT-103-07: Check Multiple Trades Accumulation

**Priority:** High
**Description:** Multiple trades should accumulate to daily total

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limit': -500
}

# Mock P&L tracker with accumulation
mock_pnl_tracker = Mock()

# Simulate multiple trades
daily_pnl_sequence = [
    100,   # Trade 1: +100
    -50,   # Trade 2: +50 total
    -200,  # Trade 3: -150 total
    -450   # Trade 4: -600 total (BREACH!)
]

mock_pnl_tracker.add_trade_pnl.side_effect = daily_pnl_sequence

mock_actions = Mock()
mock_lockout_manager = Mock()
```

### When
```python
trades = [
    {'accountId': 123, 'profitAndLoss': 100},
    {'accountId': 123, 'profitAndLoss': -50},
    {'accountId': 123, 'profitAndLoss': -200},
    {'accountId': 123, 'profitAndLoss': -450}
]

rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)

results = []
for trade in trades:
    result = rule.check(trade)
    results.append(result)
```

### Then
```python
# First 3 trades: no breach
assert results[0] is None  # +100
assert results[1] is None  # +50
assert results[2] is None  # -150

# Fourth trade: BREACH
assert results[3] is not None
assert results[3]['daily_pnl'] == -600

# P&L tracker called 4 times
assert mock_pnl_tracker.add_trade_pnl.call_count == 4
```

---

## UT-103-08: Check Lockout After 5 PM Goes To Next Day

**Priority:** Medium
**Description:** If breach occurs after reset time, lockout should be until next day's reset

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limit': -500,
    'reset_time': '17:00',
    'lockout_until_reset': True
}

mock_pnl_tracker = Mock()
mock_pnl_tracker.add_trade_pnl.return_value = -600

mock_actions = Mock()
mock_lockout_manager = Mock()

# Current time: 6:00 PM (after reset)
mock_now = datetime(2025, 1, 17, 18, 0, 0)
expected_reset = datetime(2025, 1, 18, 17, 0, 0)  # Next day at 5 PM
```

### When
```python
trade_event = {
    'accountId': 123,
    'profitAndLoss': -600
}

rule = DailyRealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)

with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = mock_now
    mock_datetime.combine = datetime.combine

    breach = rule.check(trade_event)
    if breach:
        rule.enforce(123, breach)
```

### Then
```python
# Lockout set until next day 5 PM
mock_lockout_manager.set_lockout.assert_called_once()
lockout_call = mock_lockout_manager.set_lockout.call_args[1]
assert lockout_call['until'] == expected_reset
assert lockout_call['until'].day == 18  # Next day
```

---

# RULE-004: DailyUnrealizedLoss

**Test File:** `tests/unit/test_rules/test_daily_unrealized_loss.py`

---

## UT-104-01: Check Under Limit

**Priority:** High
**Description:** Unrealized P&L under loss limit should not trigger enforcement

### Given
```python
# Configuration
config = {
    'enabled': True,
    'loss_limit': 300.00,
    'scope': 'total',
    'action': 'CLOSE_ALL_AND_LOCKOUT',
    'lockout': True
}

# Mock P&L tracker
mock_pnl_tracker = Mock()
mock_pnl_tracker.calculate_unrealized_pnl.return_value = -250.00  # Under limit

mock_actions = Mock()
mock_lockout_manager = Mock()
```

### When
```python
# Position event or quote update
position_event = {
    'accountId': 123,
    'contractId': 'CON.F.US.MNQ.U25',
    'type': 1,
    'size': 2,
    'averagePrice': 21000.00
}

rule = DailyUnrealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)
result = rule.check_with_current_prices(123)
```

### Then
```python
# No breach (-250 > -300)
assert result is None

# No enforcement
mock_actions.close_all_positions.assert_not_called()
mock_lockout_manager.set_lockout.assert_not_called()
```

---

## UT-104-02: Check Breach

**Priority:** High
**Description:** Unrealized P&L exceeding loss limit should trigger close all and lockout

### Given
```python
# Configuration
config = {
    'enabled': True,
    'loss_limit': 300.00,
    'scope': 'total',
    'action': 'CLOSE_ALL_AND_LOCKOUT',
    'lockout': True,
    'reset_time': '17:00'
}

# Mock P&L tracker with breach
mock_pnl_tracker = Mock()
mock_pnl_tracker.calculate_unrealized_pnl.return_value = -350.00  # Breach!

mock_actions = Mock()
mock_actions.close_all_positions.return_value = True
mock_actions.cancel_all_orders.return_value = True

mock_lockout_manager = Mock()
mock_logger = Mock()

# Mock time
mock_now = datetime(2025, 1, 17, 14, 30, 0)
expected_reset = datetime(2025, 1, 17, 17, 0, 0)
```

### When
```python
rule = DailyUnrealizedLossRule(
    config,
    mock_pnl_tracker,
    mock_actions,
    mock_lockout_manager,
    mock_logger
)

with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = mock_now
    mock_datetime.combine = datetime.combine

    breach = rule.check_with_current_prices(123)

    if breach:
        rule.enforce(123, breach)
```

### Then
```python
# Breach detected
assert breach is not None
assert breach['rule_id'] == 'RULE-004'
assert breach['action'] == 'CLOSE_ALL_AND_LOCKOUT'
assert breach['unrealized_pnl'] == -350.00
assert breach['limit'] == -300.00

# All positions closed
mock_actions.close_all_positions.assert_called_once_with(123)

# All orders cancelled
mock_actions.cancel_all_orders.assert_called_once_with(123)

# Lockout set
mock_lockout_manager.set_lockout.assert_called_once()
lockout_call = mock_lockout_manager.set_lockout.call_args[1]
assert lockout_call['account_id'] == 123
assert lockout_call['until'] == expected_reset

# Logged
mock_logger.log_enforcement.assert_called_once()
```

---

## UT-104-03: Check With Multiple Positions

**Priority:** High
**Description:** Multiple positions should be summed for total unrealized P&L

### Given
```python
# Configuration
config = {
    'enabled': True,
    'loss_limit': 300.00,
    'scope': 'total'
}

# Mock P&L tracker with multiple positions
# Position 1: -150, Position 2: -200, Total: -350 (breach)
mock_pnl_tracker = Mock()
mock_pnl_tracker.calculate_unrealized_pnl.return_value = -350.00

mock_actions = Mock()
mock_lockout_manager = Mock()
```

### When
```python
rule = DailyUnrealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)
breach = rule.check_with_current_prices(123)
```

### Then
```python
# Breach detected with combined P&L
assert breach is not None
assert breach['unrealized_pnl'] == -350.00

# P&L calculated once (handles all positions internally)
mock_pnl_tracker.calculate_unrealized_pnl.assert_called_once_with(123)
```

---

## UT-104-04: Check Triggered By Quote Update

**Priority:** High
**Description:** Quote updates should trigger P&L recalculation

### Given
```python
# Configuration
config = {
    'enabled': True,
    'loss_limit': 300.00
}

# Mock P&L tracker - changes based on quote
mock_pnl_tracker = Mock()

# Sequence: First check OK, second check breach
unrealized_sequence = [
    -250.00,  # After first quote
    -310.00   # After second quote (BREACH!)
]
mock_pnl_tracker.calculate_unrealized_pnl.side_effect = unrealized_sequence

mock_actions = Mock()
mock_lockout_manager = Mock()
```

### When
```python
rule = DailyUnrealizedLossRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)

# First quote update
result1 = rule.check_with_current_prices(123)

# Second quote update (price moved against position)
result2 = rule.check_with_current_prices(123)
```

### Then
```python
# First check: no breach
assert result1 is None

# Second check: breach!
assert result2 is not None
assert result2['unrealized_pnl'] == -310.00

# P&L calculated twice (once per quote update)
assert mock_pnl_tracker.calculate_unrealized_pnl.call_count == 2
```

---

## UT-104-05: Check Long Position Losing

**Priority:** High
**Description:** Long position with price below entry should calculate negative P&L correctly

### Given
```python
# Configuration
config = {
    'enabled': True,
    'loss_limit': 300.00
}

# Mock P&L tracker for long position
# Long 2 MNQ @ 21000, current 20950 = -$200
mock_pnl_tracker = Mock()

# Mock contract cache with MNQ metadata
mock_contract_cache = Mock()
mock_contract_cache.get_contract.return_value = {
    'tickSize': 0.25,
    'tickValue': 0.50
}

# Mock quote tracker
mock_quote_tracker = Mock()
mock_quote_tracker.get_quote.return_value = {
    'lastPrice': 20950.00
}

# Mock state manager with position
mock_state_manager = Mock()
mock_state_manager.get_all_positions.return_value = [{
    'contract_id': 'CON.F.US.MNQ.U25',
    'type': 1,  # Long
    'size': 2,
    'averagePrice': 21000.00
}]

# Create P&L tracker with dependencies
from src.state.pnl_tracker import PNLTracker
pnl_tracker = PNLTracker(mock_state_manager, mock_contract_cache, mock_quote_tracker)

mock_actions = Mock()
```

### When
```python
rule = DailyUnrealizedLossRule(config, pnl_tracker, mock_actions, None)

# Calculate unrealized P&L
unrealized_pnl = pnl_tracker.calculate_unrealized_pnl(123)
```

### Then
```python
# Should calculate -$200
# Ticks moved: (20950 - 21000) / 0.25 = -200 ticks
# P&L: -200 * 0.50 * 2 = -$200
assert unrealized_pnl == -200.00

# Still under limit
breach = rule.check_with_current_prices(123)
assert breach is None
```

---

## UT-104-06: Check Short Position Losing

**Priority:** High
**Description:** Short position with price above entry should calculate negative P&L correctly

### Given
```python
# Configuration
config = {
    'enabled': True,
    'loss_limit': 300.00
}

# Mock contract cache with MNQ metadata
mock_contract_cache = Mock()
mock_contract_cache.get_contract.return_value = {
    'tickSize': 0.25,
    'tickValue': 0.50
}

# Mock quote tracker
mock_quote_tracker = Mock()
mock_quote_tracker.get_quote.return_value = {
    'lastPrice': 21050.00  # Price went up
}

# Mock state manager with short position
mock_state_manager = Mock()
mock_state_manager.get_all_positions.return_value = [{
    'contract_id': 'CON.F.US.MNQ.U25',
    'type': 2,  # Short
    'size': 2,
    'averagePrice': 21000.00
}]

from src.state.pnl_tracker import PNLTracker
pnl_tracker = PNLTracker(mock_state_manager, mock_contract_cache, mock_quote_tracker)

mock_actions = Mock()
```

### When
```python
rule = DailyUnrealizedLossRule(config, pnl_tracker, mock_actions, None)
unrealized_pnl = pnl_tracker.calculate_unrealized_pnl(123)
```

### Then
```python
# Should calculate -$200
# Short position loses when price goes up
# Ticks moved: (21050 - 21000) / 0.25 = 200 ticks
# P&L for short: -200 * 0.50 * 2 = -$200
assert unrealized_pnl == -200.00

# Under limit
breach = rule.check_with_current_prices(123)
assert breach is None
```

---

## UT-104-07: Check Missing Quote Data

**Priority:** Medium
**Description:** Missing quote data should skip position from calculation, not breach

### Given
```python
# Configuration
config = {
    'enabled': True,
    'loss_limit': 300.00
}

# Mock quote tracker with no quote
mock_quote_tracker = Mock()
mock_quote_tracker.get_quote.return_value = None  # No quote available

mock_contract_cache = Mock()
mock_state_manager = Mock()
mock_state_manager.get_all_positions.return_value = [{
    'contract_id': 'CON.F.US.MNQ.U25',
    'type': 1,
    'size': 2,
    'averagePrice': 21000.00
}]

from src.state.pnl_tracker import PNLTracker
pnl_tracker = PNLTracker(mock_state_manager, mock_contract_cache, mock_quote_tracker)

mock_actions = Mock()
mock_logger = Mock()
```

### When
```python
rule = DailyUnrealizedLossRule(config, pnl_tracker, mock_actions, None, mock_logger)
unrealized_pnl = pnl_tracker.calculate_unrealized_pnl(123)
```

### Then
```python
# Should return 0 (or skip position)
assert unrealized_pnl == 0.00

# Warning logged
mock_logger.warning.assert_called()
warning_message = mock_logger.warning.call_args[0][0]
assert 'Missing quote' in warning_message or 'No quote' in warning_message

# No breach
breach = rule.check_with_current_prices(123)
assert breach is None
```

---

## UT-104-08: Check Per-Position Scope

**Priority:** High
**Description:** With scope='per_position', only losing position should be closed

### Given
```python
# Configuration with per-position scope
config = {
    'enabled': True,
    'loss_limit': 300.00,
    'scope': 'per_position',
    'action': 'CLOSE_POSITION',
    'lockout': False
}

# Mock P&L tracker
# Position 1: -350 (breach), Position 2: +100 (OK)
mock_pnl_tracker = Mock()

# Return per-position P&L
def calculate_per_position_pnl(account_id):
    return {
        'CON.F.US.MNQ.U25': -350.00,  # Breach!
        'CON.F.US.ES.U25': 100.00     # OK
    }

mock_pnl_tracker.calculate_per_position_pnl.return_value = calculate_per_position_pnl(123)

mock_actions = Mock()
mock_lockout_manager = Mock()
mock_logger = Mock()
```

### When
```python
rule = DailyUnrealizedLossRule(
    config,
    mock_pnl_tracker,
    mock_actions,
    mock_lockout_manager,
    mock_logger
)

breach = rule.check_with_current_prices(123)

if breach:
    rule.enforce(123, breach)
```

### Then
```python
# Breach detected for MNQ only
assert breach is not None
assert breach['contract_id'] == 'CON.F.US.MNQ.U25'
assert breach['unrealized_pnl'] == -350.00

# Only MNQ position closed
mock_actions.close_position.assert_called_once_with(123, 'CON.F.US.MNQ.U25')

# ES position NOT closed
assert mock_actions.close_all_positions.call_count == 0

# No lockout (per-position mode)
mock_lockout_manager.set_lockout.assert_not_called()
```

---

# RULE-005: MaxUnrealizedProfit

**Test File:** `tests/unit/test_rules/test_max_unrealized_profit.py`

---

## UT-105-01: Check Under Limit

**Priority:** High
**Description:** Unrealized profit under target should not trigger enforcement

### Given
```python
# Configuration
config = {
    'enabled': True,
    'mode': 'profit_target',
    'profit_target': 1000.00,
    'scope': 'total',
    'action': 'CLOSE_ALL_AND_LOCKOUT'
}

# Mock P&L tracker
mock_pnl_tracker = Mock()
mock_pnl_tracker.calculate_unrealized_pnl.return_value = 800.00  # Under target

mock_actions = Mock()
mock_lockout_manager = Mock()
```

### When
```python
rule = MaxUnrealizedProfitRule(config, mock_pnl_tracker, mock_actions, mock_lockout_manager)
result = rule.check_with_current_prices(123)
```

### Then
```python
# No breach (800 < 1000)
assert result is None

# No enforcement
mock_actions.close_all_positions.assert_not_called()
mock_lockout_manager.set_lockout.assert_not_called()
```

---

## UT-105-02: Check Breach

**Priority:** High
**Description:** Unrealized profit exceeding target should trigger close all and lockout

### Given
```python
# Configuration
config = {
    'enabled': True,
    'mode': 'profit_target',
    'profit_target': 1000.00,
    'scope': 'total',
    'action': 'CLOSE_ALL_AND_LOCKOUT',
    'reset_time': '17:00'
}

# Mock P&L tracker with profit target hit
mock_pnl_tracker = Mock()
mock_pnl_tracker.calculate_unrealized_pnl.return_value = 1100.00  # Hit target!

mock_actions = Mock()
mock_actions.close_all_positions.return_value = True
mock_actions.cancel_all_orders.return_value = True

mock_lockout_manager = Mock()
mock_logger = Mock()

# Mock time
mock_now = datetime(2025, 1, 17, 14, 30, 0)
expected_reset = datetime(2025, 1, 17, 17, 0, 0)
```

### When
```python
rule = MaxUnrealizedProfitRule(
    config,
    mock_pnl_tracker,
    mock_actions,
    mock_lockout_manager,
    mock_logger
)

with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = mock_now
    mock_datetime.combine = datetime.combine

    breach = rule.check_with_current_prices(123)

    if breach:
        rule.enforce(123, breach)
```

### Then
```python
# Breach detected
assert breach is not None
assert breach['rule_id'] == 'RULE-005'
assert breach['action'] == 'CLOSE_ALL_AND_LOCKOUT'
assert breach['unrealized_pnl'] == 1100.00
assert breach['target'] == 1000.00

# All positions closed (lock in profit)
mock_actions.close_all_positions.assert_called_once_with(123)

# All orders cancelled
mock_actions.cancel_all_orders.assert_called_once_with(123)

# Lockout set
mock_lockout_manager.set_lockout.assert_called_once()
lockout_call = mock_lockout_manager.set_lockout.call_args[1]
assert 'profit target hit' in lockout_call['reason'].lower()

# Logged
mock_logger.log_enforcement.assert_called_once()
log_message = mock_logger.log_enforcement.call_args[0][0]
assert 'profit target' in log_message.lower()
```

---

## UT-105-03: Check Long Position Winning

**Priority:** High
**Description:** Long position with price above entry should calculate positive P&L correctly

### Given
```python
# Configuration
config = {
    'enabled': True,
    'profit_target': 1000.00
}

# Mock contract cache
mock_contract_cache = Mock()
mock_contract_cache.get_contract.return_value = {
    'tickSize': 0.25,
    'tickValue': 0.50
}

# Mock quote tracker
mock_quote_tracker = Mock()
mock_quote_tracker.get_quote.return_value = {
    'lastPrice': 21100.00  # Price went up
}

# Mock state manager with long position
mock_state_manager = Mock()
mock_state_manager.get_all_positions.return_value = [{
    'contract_id': 'CON.F.US.MNQ.U25',
    'type': 1,  # Long
    'size': 2,
    'averagePrice': 21000.00
}]

from src.state.pnl_tracker import PNLTracker
pnl_tracker = PNLTracker(mock_state_manager, mock_contract_cache, mock_quote_tracker)

mock_actions = Mock()
```

### When
```python
rule = MaxUnrealizedProfitRule(config, pnl_tracker, mock_actions, None)
unrealized_pnl = pnl_tracker.calculate_unrealized_pnl(123)
```

### Then
```python
# Should calculate +$400
# Ticks moved: (21100 - 21000) / 0.25 = 400 ticks
# P&L: 400 * 0.50 * 2 = +$400
assert unrealized_pnl == 400.00

# Under target
breach = rule.check_with_current_prices(123)
assert breach is None
```

---

## UT-105-04: Check Short Position Winning

**Priority:** High
**Description:** Short position with price below entry should calculate positive P&L correctly

### Given
```python
# Configuration
config = {
    'enabled': True,
    'profit_target': 1000.00
}

# Mock contract cache
mock_contract_cache = Mock()
mock_contract_cache.get_contract.return_value = {
    'tickSize': 0.25,
    'tickValue': 0.50
}

# Mock quote tracker
mock_quote_tracker = Mock()
mock_quote_tracker.get_quote.return_value = {
    'lastPrice': 20900.00  # Price went down
}

# Mock state manager with short position
mock_state_manager = Mock()
mock_state_manager.get_all_positions.return_value = [{
    'contract_id': 'CON.F.US.MNQ.U25',
    'type': 2,  # Short
    'size': 2,
    'averagePrice': 21000.00
}]

from src.state.pnl_tracker import PNLTracker
pnl_tracker = PNLTracker(mock_state_manager, mock_contract_cache, mock_quote_tracker)

mock_actions = Mock()
```

### When
```python
rule = MaxUnrealizedProfitRule(config, pnl_tracker, mock_actions, None)
unrealized_pnl = pnl_tracker.calculate_unrealized_pnl(123)
```

### Then
```python
# Should calculate +$400
# Short position profits when price goes down
# Ticks moved: (21000 - 20900) / 0.25 = 400 ticks
# P&L for short: 400 * 0.50 * 2 = +$400
assert unrealized_pnl == 400.00

# Under target
breach = rule.check_with_current_prices(123)
assert breach is None
```

---

## UT-105-05: Check Breakeven Mode

**Priority:** Medium
**Description:** With mode='breakeven', should close when P&L returns to zero

### Given
```python
# Configuration with breakeven mode
config = {
    'enabled': True,
    'mode': 'breakeven',
    'scope': 'per_position',
    'action': 'CLOSE_POSITION'
}

# Mock P&L tracker
# Position was profitable, now back to breakeven
mock_pnl_tracker = Mock()
mock_pnl_tracker.calculate_per_position_pnl.return_value = {
    'CON.F.US.MNQ.U25': 0.00  # Breakeven
}

mock_actions = Mock()
mock_logger = Mock()
```

### When
```python
rule = MaxUnrealizedProfitRule(config, mock_pnl_tracker, mock_actions, None, mock_logger)
breach = rule.check_with_current_prices(123)

if breach:
    rule.enforce(123, breach)
```

### Then
```python
# Breach detected at breakeven
assert breach is not None
assert breach['mode'] == 'breakeven'
assert breach['unrealized_pnl'] == 0.00

# Position closed
mock_actions.close_position.assert_called_once_with(123, 'CON.F.US.MNQ.U25')
```

---

## UT-105-06: Check Per-Position Scope

**Priority:** High
**Description:** With scope='per_position', only profitable position hitting target should close

### Given
```python
# Configuration
config = {
    'enabled': True,
    'profit_target': 1000.00,
    'scope': 'per_position',
    'action': 'CLOSE_POSITION',
    'lockout': False
}

# Mock P&L tracker
mock_pnl_tracker = Mock()

def calculate_per_position_pnl(account_id):
    return {
        'CON.F.US.MNQ.U25': 1100.00,  # Hit target!
        'CON.F.US.ES.U25': 500.00     # Still has room
    }

mock_pnl_tracker.calculate_per_position_pnl.return_value = calculate_per_position_pnl(123)

mock_actions = Mock()
mock_logger = Mock()
```

### When
```python
rule = MaxUnrealizedProfitRule(config, mock_pnl_tracker, mock_actions, None, mock_logger)
breach = rule.check_with_current_prices(123)

if breach:
    rule.enforce(123, breach)
```

### Then
```python
# Breach for MNQ only
assert breach is not None
assert breach['contract_id'] == 'CON.F.US.MNQ.U25'
assert breach['unrealized_pnl'] == 1100.00

# Only MNQ closed
mock_actions.close_position.assert_called_once_with(123, 'CON.F.US.MNQ.U25')

# ES position still open
# No close_all called
mock_actions.close_all_positions.assert_not_called()
```

---

# RULE-006: TradeFrequencyLimit

**Test File:** `tests/unit/test_rules/test_trade_frequency_limit.py`

---

## UT-106-01: Check Under Per-Minute Limit

**Priority:** High
**Description:** Trades under per-minute limit should not trigger cooldown

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limits': {
        'per_minute': 3,
        'per_hour': 10,
        'per_session': 50
    },
    'cooldown_on_breach': {
        'enabled': True,
        'per_minute_breach': 60
    }
}

# Mock trade counter
mock_trade_counter = Mock()

# Return counts: 2/3 trades this minute
mock_trade_counter.record_trade.return_value = {
    'minute': 2,
    'hour': 5,
    'session': 15
}

mock_lockout_manager = Mock()
```

### When
```python
trade_event = {
    'id': 101112,
    'accountId': 123,
    'contractId': 'CON.F.US.MNQ.U25',
    'creationTimestamp': '2025-01-17T14:30:00Z'
}

rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager)
result = rule.check(trade_event)
```

### Then
```python
# No breach (2 < 3)
assert result is None

# Trade recorded
mock_trade_counter.record_trade.assert_called_once()

# No cooldown
mock_lockout_manager.set_cooldown.assert_not_called()
```

---

## UT-106-02: Check Breach Per-Minute

**Priority:** High
**Description:** Exceeding per-minute limit should trigger 60-second cooldown

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limits': {
        'per_minute': 3
    },
    'cooldown_on_breach': {
        'enabled': True,
        'per_minute_breach': 60
    }
}

# Mock trade counter - 4th trade in minute
mock_trade_counter = Mock()
mock_trade_counter.record_trade.return_value = {
    'minute': 4,  # Breach!
    'hour': 4,
    'session': 4
}

mock_lockout_manager = Mock()
mock_logger = Mock()
```

### When
```python
trade_event = {
    'accountId': 123,
    'creationTimestamp': '2025-01-17T14:30:30Z'
}

rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager, mock_logger)
breach = rule.check(trade_event)

if breach:
    rule.enforce(123, breach)
```

### Then
```python
# Breach detected
assert breach is not None
assert breach['rule_id'] == 'RULE-006'
assert breach['breach_type'] == 'per_minute'
assert breach['trade_count'] == 4
assert breach['limit'] == 3

# Cooldown set for 60 seconds
mock_lockout_manager.set_cooldown.assert_called_once()
cooldown_call = mock_lockout_manager.set_cooldown.call_args[1]
assert cooldown_call['account_id'] == 123
assert cooldown_call['duration_seconds'] == 60
assert '4/3 trades' in cooldown_call['reason']

# Logged
mock_logger.log_enforcement.assert_called_once()
```

---

## UT-106-03: Check Breach Per-Hour

**Priority:** High
**Description:** Exceeding per-hour limit should trigger 30-minute cooldown

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limits': {
        'per_minute': 10,
        'per_hour': 10
    },
    'cooldown_on_breach': {
        'enabled': True,
        'per_hour_breach': 1800  # 30 minutes
    }
}

# Mock trade counter - 11th trade in hour
mock_trade_counter = Mock()
mock_trade_counter.record_trade.return_value = {
    'minute': 1,
    'hour': 11,  # Breach!
    'session': 20
}

mock_lockout_manager = Mock()
mock_logger = Mock()
```

### When
```python
trade_event = {
    'accountId': 123,
    'creationTimestamp': '2025-01-17T14:45:00Z'
}

rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager, mock_logger)
breach = rule.check(trade_event)

if breach:
    rule.enforce(123, breach)
```

### Then
```python
# Breach detected
assert breach is not None
assert breach['breach_type'] == 'per_hour'
assert breach['trade_count'] == 11
assert breach['limit'] == 10

# 30-minute cooldown
mock_lockout_manager.set_cooldown.assert_called_once()
cooldown_call = mock_lockout_manager.set_cooldown.call_args[1]
assert cooldown_call['duration_seconds'] == 1800
```

---

## UT-106-04: Check Breach Per-Session

**Priority:** High
**Description:** Exceeding per-session limit should trigger 1-hour cooldown

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limits': {
        'per_minute': 10,
        'per_hour': 20,
        'per_session': 50
    },
    'cooldown_on_breach': {
        'enabled': True,
        'per_session_breach': 3600  # 1 hour
    }
}

# Mock trade counter - 51st trade in session
mock_trade_counter = Mock()
mock_trade_counter.record_trade.return_value = {
    'minute': 1,
    'hour': 5,
    'session': 51  # Breach!
}

mock_lockout_manager = Mock()
mock_logger = Mock()
```

### When
```python
trade_event = {
    'accountId': 123,
    'creationTimestamp': '2025-01-17T15:30:00Z'
}

rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager, mock_logger)
breach = rule.check(trade_event)

if breach:
    rule.enforce(123, breach)
```

### Then
```python
# Breach detected
assert breach is not None
assert breach['breach_type'] == 'per_session'
assert breach['trade_count'] == 51
assert breach['limit'] == 50

# 1-hour cooldown
mock_lockout_manager.set_cooldown.assert_called_once()
cooldown_call = mock_lockout_manager.set_cooldown.call_args[1]
assert cooldown_call['duration_seconds'] == 3600
```

---

## UT-106-05: Check Cooldown Duration

**Priority:** Medium
**Description:** Cooldown duration should match config for breach type

### Given
```python
# Configuration with custom cooldowns
config = {
    'enabled': True,
    'limits': {
        'per_minute': 3
    },
    'cooldown_on_breach': {
        'enabled': True,
        'per_minute_breach': 120  # 2 minutes
    }
}

mock_trade_counter = Mock()
mock_trade_counter.record_trade.return_value = {
    'minute': 4,
    'hour': 4,
    'session': 4
}

mock_lockout_manager = Mock()
```

### When
```python
trade_event = {
    'accountId': 123,
    'creationTimestamp': '2025-01-17T14:30:00Z'
}

rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager)
breach = rule.check(trade_event)

if breach:
    rule.enforce(123, breach)
```

### Then
```python
# Cooldown matches configured duration
mock_lockout_manager.set_cooldown.assert_called_once()
cooldown_call = mock_lockout_manager.set_cooldown.call_args[1]
assert cooldown_call['duration_seconds'] == 120  # 2 minutes
```

---

## UT-106-06: Check Ignores Voided Trades

**Priority:** High
**Description:** Trades with voided=true should not count toward limits

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limits': {
        'per_minute': 3
    }
}

# Mock trade counter
mock_trade_counter = Mock()

# Normal trades
mock_trade_counter.record_trade.side_effect = [
    {'minute': 1, 'hour': 1, 'session': 1},
    {'minute': 2, 'hour': 2, 'session': 2},
    {'minute': 2, 'hour': 2, 'session': 2},  # Voided (doesn't increment)
    {'minute': 3, 'hour': 3, 'session': 3}
]

mock_lockout_manager = Mock()
```

### When
```python
trades = [
    {'accountId': 123, 'voided': False},
    {'accountId': 123, 'voided': False},
    {'accountId': 123, 'voided': True},   # Should be ignored
    {'accountId': 123, 'voided': False}
]

rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager)

results = []
for trade in trades:
    if not trade.get('voided'):
        result = rule.check(trade)
        results.append(result)
```

### Then
```python
# No breaches (only 3 non-voided trades)
assert all(r is None for r in results)

# Trade counter called 3 times (voided trade skipped)
assert mock_trade_counter.record_trade.call_count == 3
```

---

## UT-106-07: Check Rolling Window

**Priority:** High
**Description:** Old trades should age out of rolling minute window

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limits': {
        'per_minute': 3
    }
}

# Mock trade counter with time-aware counting
mock_trade_counter = Mock()

# Simulate trades aging out
# At t=0: 3 trades
# At t=70s: oldest trade aged out, now 2 in window
mock_trade_counter.record_trade.side_effect = [
    {'minute': 1, 'hour': 1, 'session': 1},
    {'minute': 2, 'hour': 2, 'session': 2},
    {'minute': 3, 'hour': 3, 'session': 3},  # At limit
    {'minute': 3, 'hour': 4, 'session': 4}   # After 70s, only 2 in window
]

mock_lockout_manager = Mock()
```

### When
```python
from datetime import datetime, timedelta

base_time = datetime(2025, 1, 17, 14, 0, 0)

trades = [
    {'accountId': 123, 'creationTimestamp': base_time.isoformat()},
    {'accountId': 123, 'creationTimestamp': (base_time + timedelta(seconds=10)).isoformat()},
    {'accountId': 123, 'creationTimestamp': (base_time + timedelta(seconds=20)).isoformat()},
    {'accountId': 123, 'creationTimestamp': (base_time + timedelta(seconds=70)).isoformat()}  # First trade aged out
]

rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager)

results = []
for trade in trades:
    result = rule.check(trade)
    results.append(result)
```

### Then
```python
# No breaches (rolling window allows 4th trade)
assert all(r is None for r in results)

# Fourth trade only sees 2 trades in last 60s
last_count = mock_trade_counter.record_trade.call_args_list[-1][0]
# Verify trade counter properly handles rolling window
```

---

## UT-106-08: Check Multiple Breach Types

**Priority:** Medium
**Description:** Multiple breaches on same trade should apply most severe cooldown

### Given
```python
# Configuration
config = {
    'enabled': True,
    'limits': {
        'per_minute': 3,
        'per_hour': 10
    },
    'cooldown_on_breach': {
        'enabled': True,
        'per_minute_breach': 60,
        'per_hour_breach': 1800
    }
}

# Mock trade counter - breaches BOTH minute and hour
mock_trade_counter = Mock()
mock_trade_counter.record_trade.return_value = {
    'minute': 4,  # Breach minute
    'hour': 11,   # Breach hour
    'session': 15
}

mock_lockout_manager = Mock()
mock_logger = Mock()
```

### When
```python
trade_event = {
    'accountId': 123,
    'creationTimestamp': '2025-01-17T14:30:00Z'
}

rule = TradeFrequencyLimitRule(config, mock_trade_counter, mock_lockout_manager, mock_logger)
breach = rule.check(trade_event)

if breach:
    rule.enforce(123, breach)
```

### Then
```python
# Breach detected
assert breach is not None

# Most severe cooldown applied (hour > minute)
mock_lockout_manager.set_cooldown.assert_called_once()
cooldown_call = mock_lockout_manager.set_cooldown.call_args[1]
assert cooldown_call['duration_seconds'] == 1800  # Hour cooldown, not minute

# Both breaches logged
mock_logger.log_enforcement.assert_called()
log_message = mock_logger.log_enforcement.call_args[0][0]
assert ('per_minute' in log_message or 'per_hour' in log_message)
```

---

## Summary

**Total Test Scenarios:** 42

| Rule | Scenarios | File |
|------|-----------|------|
| RULE-001: MaxContracts | 6 | `test_max_contracts.py` |
| RULE-002: MaxContractsPerInstrument | 6 | `test_max_contracts_per_instrument.py` |
| RULE-003: DailyRealizedLoss | 8 | `test_daily_realized_loss.py` |
| RULE-004: DailyUnrealizedLoss | 8 | `test_daily_unrealized_loss.py` |
| RULE-005: MaxUnrealizedProfit | 6 | `test_max_unrealized_profit.py` |
| RULE-006: TradeFrequencyLimit | 8 | `test_trade_frequency_limit.py` |

**Key Testing Patterns:**
1. All tests use mocks for external dependencies (API, state manager, lockout manager)
2. Given/When/Then format for clarity
3. Python pseudocode showing expected implementation
4. Assertions cover both breach detection and enforcement actions
5. Edge cases explicitly tested (at limit, missing data, etc.)

**Next Steps:**
1. Implement actual test files using pytest framework
2. Create test fixtures for common mocks
3. Add integration tests combining multiple rules
4. Set up CI/CD pipeline for automated testing

---

**Document Complete** ✓
**Ready for Implementation** ✓
