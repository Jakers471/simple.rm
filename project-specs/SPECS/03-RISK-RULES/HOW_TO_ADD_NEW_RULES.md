---
doc_id: RULE-GUIDE-001
title: How to Add New Risk Rules
version: 1.0
last_updated: 2025-10-21
---

# How to Add New Risk Rules

**Purpose:** Step-by-step guide for adding new risk rules to the system

**Difficulty:** Easy - The system is designed to make adding new rules trivial

---

## 🎯 Overview

The Risk Manager system is built with **extreme modularity** in mind. Adding a new rule requires:

1. **Writing the rule specification** (~1 hour)
2. **Implementing the rule class** (~30 minutes)
3. **Updating the event router** (~5 minutes)
4. **Adding configuration** (~5 minutes)
5. **Testing** (~30 minutes)

**Total Time:** ~2-3 hours per rule

**No other changes needed** - The architecture handles everything else automatically.

---

## 📋 Step-by-Step Guide

### Step 1: Create Rule Specification

**Location:** `project-specs/SPECS/03-RISK-RULES/rules/`

**Filename:** `13_your_rule_name.md` (increment number from last rule)

**Template:**
```markdown
---
doc_id: RULE-013
title: Your Rule Name
version: 1.0
last_updated: 2025-10-21
dependencies: [MOD-001, MOD-002, ...list any modules you need]
---

# RULE-013: Your Rule Name

**Purpose:** Brief description of what this rule prevents

**Category:** Position Limits / Loss Limits / Trading Behavior / Time-Based / Symbol Restrictions

---

## 🎯 Rule Overview

**What it does:**
- Clear explanation of the rule

**When it triggers:**
- Specific event types that trigger this rule

**What it enforces:**
- Enforcement action taken when breached

---

## ⚙️ Configuration

### YAML Configuration
\`\`\`yaml
rules:
  rule_013_your_rule_name:
    enabled: true
    # Your parameters here
    param1: value1
    param2: value2
\`\`\`

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | bool | Yes | Enable/disable rule |
| `param1` | type | Yes | Description |
| `param2` | type | No | Description |

---

## 🔍 Detection Logic

### Trigger Events
- **Event Type:** Which SignalR events trigger this rule
- **Frequency:** How often to check

### Breach Condition
\`\`\`python
# Pseudocode for breach detection
if condition_met:
    return EnforcementAction(...)
else:
    return None  # No breach
\`\`\`

### State Dependencies
List which modules this rule reads from:
- MOD-XXX: What data you need from it

---

## 🛡️ Enforcement

### Enforcement Action
- **Type:** CLOSE_ALL_POSITIONS | CLOSE_ALL_AND_LOCKOUT | COOLDOWN | REJECT_ORDER | AUTO_STOP_LOSS
- **Reason:** "Human-readable reason"
- **Lockout Duration:** If applicable (e.g., "until 5 PM" or "permanent")

---

## 📊 Examples

### Example 1: Breach Scenario
[Provide detailed example with numbers]

### Example 2: No Breach Scenario
[Provide example where rule doesn't trigger]

---

## 🧪 Testing

### Test Cases
1. Test breach detection
2. Test enforcement action
3. Test configuration validation
4. Test edge cases

---
```

**Example:** See `03-RISK-RULES/rules/01_max_contracts.md` for reference

---

### Step 2: Implement Rule Class

**Location:** `src/rules/your_rule_name.py`

**Template:**
```python
"""
RULE-013: Your Rule Name
Purpose: Brief description
"""

from typing import Optional
from dataclasses import dataclass
from src.data_models.enforcement_action import EnforcementAction, EnforcementActionType
from src.data_models.rule_config import RuleConfig

# Import any modules you need
from src.state.state_manager import StateManager
from src.state.pnl_tracker import PnlTracker
# etc.

class YourRuleNameRule:
    """
    RULE-013: Your Rule Name

    Trigger Events: List events
    Enforcement: Action type
    """

    def __init__(self, config: RuleConfig, state_manager: StateManager,
                 # Add any other module dependencies as parameters
                 ):
        """
        Initialize rule.

        Args:
            config: Rule configuration from risk_config.yaml
            state_manager: State manager for position/order data
            # Document other dependencies
        """
        self.config = config
        self.state_manager = state_manager
        # Store other dependencies

        # Parse configuration
        self.enabled = config.enabled
        self.param1 = config.get_param('param1')
        self.param2 = config.get_param('param2', default_value)

    def check(self, account_id: int, event_type: str, event_data: dict) -> Optional[EnforcementAction]:
        """
        Check if rule is breached.

        Args:
            account_id: Account to check
            event_type: Type of event (e.g., "GatewayUserPosition")
            event_data: Event payload from TopstepX

        Returns:
            EnforcementAction if breached, None otherwise
        """
        # Return early if rule disabled
        if not self.enabled:
            return None

        # Return early if this event doesn't trigger this rule
        if event_type not in ["GatewayUserPosition", "GatewayUserTrade"]:  # Your event types
            return None

        # Get required state from modules
        # Example: current_positions = self.state_manager.get_positions(account_id)

        # Implement your breach detection logic
        if self._is_breached(account_id, event_data):
            return EnforcementAction(
                type=EnforcementActionType.CLOSE_ALL_POSITIONS,  # Your enforcement type
                reason=self._get_breach_reason(account_id, event_data),
                rule_id="RULE-013",
                account_id=account_id,
                # Add any other enforcement details
            )

        return None  # No breach

    def _is_breached(self, account_id: int, event_data: dict) -> bool:
        """
        Check if breach condition is met.

        Args:
            account_id: Account to check
            event_data: Event payload

        Returns:
            True if breached, False otherwise
        """
        # Your breach detection logic here
        # Return True if rule is violated
        pass

    def _get_breach_reason(self, account_id: int, event_data: dict) -> str:
        """
        Generate human-readable breach reason.

        Args:
            account_id: Account that breached
            event_data: Event payload

        Returns:
            Breach reason string
        """
        # Return descriptive reason
        return f"Your rule breached: details here"
```

**Key Points:**
- All rules follow the same pattern: `check(account_id, event_type, event_data) -> Optional[EnforcementAction]`
- Return `None` if no breach, `EnforcementAction` if breached
- Use helper methods to keep `check()` clean
- Document all parameters and return values

---

### Step 3: Update Event Router

**Location:** `src/core/event_router.py`

**Changes Required:**

**3a. Import your rule:**
```python
# Add to imports at top of file
from src.rules.your_rule_name import YourRuleNameRule
```

**3b. Initialize rule in `__init__`:**
```python
class EventRouter:
    def __init__(self, config, state_manager, lockout_manager, pnl_tracker, ...):
        # ... existing code ...

        # Initialize all rules
        self.rules = [
            MaxContractsRule(rule_configs['rule_001'], state_manager),
            # ... existing rules ...
            YourRuleNameRule(rule_configs['rule_013'], state_manager, pnl_tracker),  # Add your rule
        ]
```

**3c. Add event type routing (if needed):**
```python
def route_event(self, event_type: str, event_data: dict):
    """Route event to relevant rules"""
    account_id = event_data['accountId']

    # Check lockout FIRST (don't process if locked)
    if self.lockout_manager.is_locked_out(account_id):
        return

    # Update state FIRST (before rule checks)
    self._update_state(event_type, event_data)

    # Route to rules based on event type
    if event_type == "GatewayUserPosition":
        relevant_rules = [r for r in self.rules if hasattr(r, 'handles_positions')]
    elif event_type == "GatewayUserTrade":
        relevant_rules = [r for r in self.rules if hasattr(r, 'handles_trades')]
    # ... etc.

    # Check each relevant rule
    for rule in relevant_rules:
        action = rule.check(account_id, event_type, event_data)
        if action:
            self.enforcement_engine.execute(action)
            break  # Stop after first breach
```

**OR** (simpler approach - check all rules for all events):
```python
# The router already does this - no changes needed!
for rule in self.rules:
    action = rule.check(account_id, event_type, event_data)
    if action:
        self.enforcement_engine.execute(action)
        break
```

**That's it!** The event router automatically calls your rule's `check()` method.

---

### Step 4: Add Configuration

**Location:** `config/risk_config.yaml`

**Add your rule:**
```yaml
rules:
  # ... existing rules ...

  rule_013_your_rule_name:
    enabled: true
    param1: value1
    param2: value2
    # Add your parameters
```

**That's all!** The config loader automatically loads this.

---

### Step 5: Test Your Rule

**Location:** `tests/rules/test_your_rule_name.py`

**Test Template:**
```python
import pytest
from src.rules.your_rule_name import YourRuleNameRule
from src.data_models.rule_config import RuleConfig

def test_breach_detection():
    """Test rule detects breach correctly"""
    # Create mock config
    config = RuleConfig(
        rule_id="RULE-013",
        name="YourRuleName",
        enabled=True,
        params={'param1': value1, 'param2': value2}
    )

    # Create mock dependencies
    state_manager = MockStateManager()

    # Initialize rule
    rule = YourRuleNameRule(config, state_manager)

    # Create breach scenario
    event_data = {
        'accountId': 123,
        # ... event data that should trigger breach
    }

    # Check rule
    action = rule.check(123, "GatewayUserPosition", event_data)

    # Assert breach detected
    assert action is not None
    assert action.type == EnforcementActionType.CLOSE_ALL_POSITIONS
    assert "Your rule breached" in action.reason

def test_no_breach():
    """Test rule doesn't trigger when no breach"""
    # ... similar setup ...

    # Create non-breach scenario
    event_data = {
        'accountId': 123,
        # ... event data that should NOT trigger breach
    }

    # Check rule
    action = rule.check(123, "GatewayUserPosition", event_data)

    # Assert no breach
    assert action is None

def test_rule_disabled():
    """Test rule doesn't trigger when disabled"""
    config = RuleConfig(
        rule_id="RULE-013",
        name="YourRuleName",
        enabled=False,  # Disabled
        params={}
    )

    rule = YourRuleNameRule(config, state_manager)

    # Even with breach scenario
    action = rule.check(123, "GatewayUserPosition", breach_event_data)

    # Should return None (disabled)
    assert action is None
```

**Run tests:**
```bash
pytest tests/rules/test_your_rule_name.py -v
```

---

## 📝 Complete Checklist

Before considering your rule complete:

- [ ] Rule specification created (`03-RISK-RULES/rules/13_your_rule.md`)
- [ ] Rule class implemented (`src/rules/your_rule_name.py`)
- [ ] Rule imported in event router (`src/core/event_router.py`)
- [ ] Rule initialized in router's `__init__`
- [ ] Configuration added (`config/risk_config.yaml`)
- [ ] Unit tests written (`tests/rules/test_your_rule_name.py`)
- [ ] Tests pass (`pytest tests/rules/test_your_rule_name.py`)
- [ ] Integration test with event router
- [ ] Manual test with real TopstepX events (if possible)
- [ ] Documentation updated (`COMPLETE_SPECIFICATION.md` if major rule)

---

## 🔧 What You DON'T Need to Change

The following components automatically adapt to new rules:

✅ **Event Router** - Already loops through all rules
✅ **Enforcement Engine** - Already handles all enforcement action types
✅ **State Manager** - Already provides all state data
✅ **WebSocket Server** - Already broadcasts all events
✅ **Database** - Already logs all enforcement actions
✅ **Trader CLI** - Already displays all enforcement alerts
✅ **Admin CLI** - Already shows all rule configs

**You only touch:**
1. Rule specification (documentation)
2. Rule class (implementation)
3. Event router (1-2 lines to import and initialize)
4. Config file (add your parameters)
5. Tests

---

## 💡 Rule Implementation Tips

### Tip 1: Keep Rules Simple
Each rule should do ONE thing:
- ✅ Good: "Check if total contracts > 5"
- ❌ Bad: "Check contracts AND check P&L AND check time"

If you have complex logic, split into multiple rules.

---

### Tip 2: Use Existing Modules
Don't reimplement state tracking:
```python
# ❌ Bad - reimplementing state
current_positions = []
for event in all_events:
    if event['type'] == 'position':
        current_positions.append(event)

# ✅ Good - use state manager
current_positions = self.state_manager.get_positions(account_id)
```

---

### Tip 3: Return Early for Non-Relevant Events
```python
def check(self, account_id, event_type, event_data):
    # Fast path - ignore irrelevant events
    if event_type not in ["GatewayUserPosition", "GatewayUserTrade"]:
        return None  # Not my event type

    # Now do expensive checks
    # ...
```

---

### Tip 4: Make Breach Reasons Descriptive
```python
# ❌ Bad
return "Rule breached"

# ✅ Good
return f"Max contracts exceeded: {current} > {limit} (instrument: {symbol})"
```

Trader needs to understand WHY they were stopped.

---

### Tip 5: Use Type Hints
```python
def check(self, account_id: int, event_type: str, event_data: dict) -> Optional[EnforcementAction]:
    """Always include type hints for clarity"""
```

---

## 🎯 Example: Adding a "Max Daily Trades" Rule

Let's walk through a complete example:

### 1. Specification (`03-RISK-RULES/rules/13_max_daily_trades.md`)

```markdown
# RULE-013: Max Daily Trades

**Purpose:** Prevent overtrading by limiting trades per day

**Category:** Trading Behavior

## Configuration
\`\`\`yaml
rule_013_max_daily_trades:
  enabled: true
  max_trades: 20
  action: CLOSE_ALL_AND_LOCKOUT
\`\`\`

## Detection Logic
- **Trigger:** GatewayUserTrade event
- **Condition:** Trade count today >= max_trades
- **Enforcement:** Close all + lockout until daily reset

## Example
If max_trades = 20:
- Trades 1-19: Allowed
- Trade 20: Allowed (but warning)
- Trade 21: **BREACH** - Close all + lockout
```

---

### 2. Implementation (`src/rules/max_daily_trades.py`)

```python
from typing import Optional
from src.data_models.enforcement_action import EnforcementAction, EnforcementActionType
from src.state.trade_counter import TradeCounter

class MaxDailyTradesRule:
    """RULE-013: Max Daily Trades"""

    def __init__(self, config, trade_counter: TradeCounter):
        self.enabled = config.enabled
        self.max_trades = config.get_param('max_trades')
        self.trade_counter = trade_counter

    def check(self, account_id: int, event_type: str, event_data: dict) -> Optional[EnforcementAction]:
        if not self.enabled:
            return None

        if event_type != "GatewayUserTrade":
            return None  # Only check on trade events

        # Get trade count (already updated by state manager)
        trade_count = self.trade_counter.get_daily_count(account_id)

        # Check breach
        if trade_count > self.max_trades:
            return EnforcementAction(
                type=EnforcementActionType.CLOSE_ALL_AND_LOCKOUT,
                reason=f"Max daily trades exceeded: {trade_count} > {self.max_trades}",
                rule_id="RULE-013",
                account_id=account_id,
                lockout_until=None  # Lockout until daily reset
            )

        return None
```

---

### 3. Event Router Update (`src/core/event_router.py`)

```python
from src.rules.max_daily_trades import MaxDailyTradesRule

class EventRouter:
    def __init__(self, ...):
        # ... existing code ...

        self.rules = [
            # ... existing rules ...
            MaxDailyTradesRule(rule_configs['rule_013'], self.trade_counter),
        ]
```

---

### 4. Configuration (`config/risk_config.yaml`)

```yaml
rules:
  rule_013_max_daily_trades:
    enabled: true
    max_trades: 20
```

---

### 5. Test (`tests/rules/test_max_daily_trades.py`)

```python
def test_breach_on_21st_trade():
    config = RuleConfig("RULE-013", "MaxDailyTrades", True, {'max_trades': 20})
    trade_counter = MockTradeCounter()
    trade_counter.set_count(123, 21)  # 21 trades today

    rule = MaxDailyTradesRule(config, trade_counter)
    action = rule.check(123, "GatewayUserTrade", {})

    assert action is not None
    assert action.type == EnforcementActionType.CLOSE_ALL_AND_LOCKOUT
```

---

**Done!** You've added a new risk rule in ~2 hours.

---

## 🚀 Advanced: Cross-Rule Dependencies

If your rule needs data from another rule:

```python
class YourRule:
    def __init__(self, config, state_manager, other_rule: OtherRule):
        self.other_rule = other_rule

    def check(self, ...):
        # You can call other rule's methods
        if self.other_rule.is_condition_met():
            # ...
```

**Note:** Be careful with circular dependencies.

---

## 📊 Performance Considerations

Each rule's `check()` method is called on EVERY event:

- **Fast path:** Return early if event not relevant (~1 microsecond)
- **Breach check:** Should complete in < 1ms
- **Total latency budget:** < 10ms from event → enforcement

**Profile your rule:**
```python
import time

def check(self, ...):
    start = time.perf_counter()

    # Your logic here

    elapsed = time.perf_counter() - start
    if elapsed > 0.001:  # Slower than 1ms
        logger.warning(f"Rule {self.rule_id} slow: {elapsed*1000:.2f}ms")
```

---

## 🎓 Summary

**Adding a new risk rule is easy:**

1. Write spec (copy template)
2. Implement rule class (copy template)
3. Import and initialize in event router (2 lines)
4. Add config (YAML)
5. Write tests

**The system handles:**
- Event routing
- State management
- Enforcement execution
- CLI updates
- Database logging
- Everything else!

**Total effort:** ~2-3 hours per rule

---

**Ready to add your first rule?** Start with the specification template above!
