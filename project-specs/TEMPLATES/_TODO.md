# 📋 TODO - Code Templates

**Status:** Future Work
**Priority:** LOW (Create During Implementation)
**For AI:** Reusable code templates to speed up development

---

## 🎯 What This Section Will Contain

**Purpose:** Provide code templates that AI can use when implementing components

These templates will be created during implementation as patterns emerge.

---

## 📋 Planned Templates

### 1. rule_implementation_template.py
**Purpose:** Template for implementing a new risk rule

**Will Include:**
```python
"""
Template for RULE-XXX: [Rule Name]

Specification: See SPECS/03-RISK-RULES/RULE-XXX_*.md
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from ..base_rule import BaseRule
from ..enforcement.actions import EnforcementActions
from ..state.lockout_manager import LockoutManager

class RuleNameHere(BaseRule):
    """
    [Rule description]

    Triggers: [Event types that trigger this rule]
    Enforcement: [What happens on breach]
    """

    def __init__(self, config: dict):
        super().__init__(config)
        # Load rule-specific config
        self.limit = config.get("limit")
        # ...

    def check(self, event: dict) -> bool:
        """
        Check if rule is breached

        Returns: True if breach detected, False otherwise
        """
        # TODO: Implement breach detection logic
        pass

    def enforce(self, event: dict) -> None:
        """
        Execute enforcement action
        """
        # TODO: Implement enforcement logic
        pass
```

---

### 2. module_implementation_template.py
**Purpose:** Template for implementing a core module

**Will Include:**
```python
"""
Template for MOD-XXX: [Module Name]

Specification: See SPECS/04-CORE-MODULES/MOD-XXX_*.md
"""

from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

class ModuleNameHere:
    """
    [Module description]

    Used By: [Which rules/components use this]
    """

    def __init__(self, state_manager):
        self.state_manager = state_manager
        # Initialize module state

    # Template methods based on module type
```

---

### 3. test_template.py
**Purpose:** Template for writing tests

**Will Include:**
```python
"""
Test template for [component name]

Tests: [What's being tested]
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.rules.rule_name import RuleName

class TestRuleName:
    """Test suite for RuleName rule"""

    @pytest.fixture
    def rule_config(self):
        """Standard rule configuration"""
        return {
            "enabled": True,
            "limit": -500,
            # ...
        }

    @pytest.fixture
    def rule(self, rule_config):
        """Instantiate rule with test config"""
        return RuleName(rule_config)

    def test_breach_detected(self, rule):
        """Test that breach is detected when limit exceeded"""
        # Arrange
        event = {...}

        # Act
        result = rule.check(event)

        # Assert
        assert result == True

    def test_no_breach_within_limit(self, rule):
        """Test that no breach when within limit"""
        # ...
```

---

### 4. cli_screen_template.py
**Purpose:** Template for CLI screen components

**Will Include:**
```python
"""
Template for CLI screen: [Screen Name]

Displays: [What this screen shows]
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def render_screen_name(state: dict) -> None:
    """
    Render [screen name]

    Args:
        state: Current system state
    """

    # Clear screen
    console.clear()

    # Render header
    console.print(Panel("[bold]Screen Title[/bold]"))

    # Render main content
    table = Table(title="Content Title")
    table.add_column("Column 1")
    table.add_column("Column 2")
    # ...

    console.print(table)

    # Render footer
    console.print("\n[dim]Press 'q' to quit[/dim]")
```

---

### 5. config_template.yaml
**Purpose:** Complete example configuration file

**Will Include:**
```yaml
# Risk Manager Configuration Template
# See: SPECS/08-CONFIGURATION/ for complete specification

# TopstepX API Configuration
topstepx:
  username: "your_username"
  api_key: "your_api_key_here"

monitored_account:
  account_id: 123
  account_name: "Main Trading Account"

# Risk Rules Configuration
# Enable/disable and configure each rule below

# RULE-001: Max Contracts
max_contracts:
  enabled: true
  limit: 5
  # ... all options with comments
```

---

### 6. event_handler_template.py
**Purpose:** Template for handling TopstepX events

**Will Include:**
```python
"""
Template for event handler: [Event Type]

Handles: [TopstepX event name]
"""

from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)

def handle_event_name(event_data: dict, rule_engine) -> None:
    """
    Handle [event type] from TopstepX

    Args:
        event_data: Raw event payload from SignalR
        rule_engine: Risk engine instance
    """

    # Validate event
    if not validate_event(event_data):
        logger.error("Invalid event data")
        return

    # Parse event
    parsed_event = parse_event(event_data)

    # Route to appropriate rules
    rule_engine.process_event(parsed_event)

def validate_event(event_data: dict) -> bool:
    """Validate event has required fields"""
    # TODO: Implement validation
    pass

def parse_event(event_data: dict) -> dict:
    """Parse event into standardized format"""
    # TODO: Implement parsing
    pass
```

---

## 🚫 Do Not Create These Yet!

**Why Wait:**
1. Templates are based on actual implementation patterns
2. Specs must be complete first
3. Templates emerge naturally during coding
4. Premature templates might not match final implementation

---

## 🚀 When to Create These

**Trigger:** After implementing first few components, patterns will emerge

**Creation Approach:**
1. Implement 2-3 rules manually
2. Notice common patterns
3. Extract patterns into templates
4. Use templates for remaining rules

**Example Flow:**
```
1. Manually implement RULE-001 (MaxContracts)
2. Manually implement RULE-002 (MaxContractsPerInstrument)
3. Notice both have same structure
4. Extract into rule_implementation_template.py
5. Use template for RULE-003 through RULE-012
```

---

## 💡 For Now

**Current Focus:**
- Complete all specs
- Don't worry about templates yet
- Templates are optimization, not requirement

**When Ready:**
- Create templates based on real implementations
- Keep templates simple and well-commented
- Update templates as patterns evolve

---

**Status:** 🚫 DO NOT CREATE YET - WAIT FOR IMPLEMENTATION PHASE
