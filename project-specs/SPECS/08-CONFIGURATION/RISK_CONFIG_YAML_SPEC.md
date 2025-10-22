---
doc_id: CONFIG-002
title: risk_config.yaml Specification
version: 1.0
last_updated: 2025-10-21
dependencies: [RULE-001 through RULE-012]
---

# risk_config.yaml Configuration Specification

**Purpose:** Complete specification for the risk rules configuration file

**File Location:** `config/risk_config.yaml`

**Format:** YAML

---

## 🎯 Overview

The `risk_config.yaml` file defines configuration for all 12 risk rules. Each rule can be independently enabled/disabled and has rule-specific parameters.

**Key Features:**
- Per-rule enable/disable
- Rule-specific parameters
- Comments for documentation
- Hot-reloadable (Admin CLI can reload without daemon restart)

---

## 📋 Complete Schema

```yaml
# risk_config.yaml - Risk rule configurations

# Global settings (optional)
global:
  strict_mode: false        # If true, any breach causes immediate lockout
  logging_level: "INFO"     # DEBUG, INFO, WARNING, ERROR

# Rule configurations
rules:
  # RULE-001: Max Contracts
  max_contracts:
    enabled: true
    limit: 5
    count_type: "net"       # "net" or "gross"

  # RULE-002: Max Contracts Per Instrument
  max_contracts_per_instrument:
    enabled: true
    limits:
      MNQ: 2    # Max 2 micro NQ contracts
      NQ: 1     # Max 1 full NQ contract
      ES: 1     # Max 1 ES contract
      MES: 3    # Max 3 micro ES contracts
    enforcement: "reduce_to_limit"  # "reduce_to_limit" or "close_all"
    unknown_symbol_action: "allow_with_limit:1"  # Default limit for unlisted symbols

  # RULE-003: Daily Realized Loss
  daily_realized_loss:
    enabled: true
    loss_limit: 500.00
    action: "CLOSE_ALL_AND_LOCKOUT"
    lockout_until: "daily_reset"  # or "permanent"

  # RULE-004: Daily Unrealized Loss
  daily_unrealized_loss:
    enabled: true
    loss_limit: 300.00
    scope: "per_position"         # "total" or "per_position"
    action: "CLOSE_POSITION"      # Close only losing position
    lockout: false                # No lockout on per-position mode

  # RULE-005: Max Unrealized Profit
  max_unrealized_profit:
    enabled: true
    mode: "profit_target"         # "profit_target" or "breakeven"
    profit_target: 1000.00        # Used when mode = "profit_target"
    scope: "per_position"         # Close each position individually
    action: "CLOSE_POSITION"      # Close only profitable position

  # RULE-006: Trade Frequency Limit
  trade_frequency_limit:
    enabled: true
    max_trades: 30
    time_window_minutes: 60

  # RULE-007: Cooldown After Loss
  cooldown_after_loss:
    enabled: true
    loss_threshold: 100.00
    cooldown_seconds: 300

  # RULE-008: No Stop-Loss Grace Period
  no_stop_loss_grace:
    enabled: true
    grace_period_seconds: 30
    action: "CLOSE_POSITION"      # Close only position without stop-loss

  # RULE-009: Session Block Outside Hours
  session_block_outside:
    enabled: true
    allowed_hours:
      start: "08:30"
      end: "15:00"
    timezone: "America/Chicago"
    action: "CANCEL_ORDER"        # Cancel orders outside allowed hours

  # RULE-010: Auth Loss Guard
  auth_loss_guard:
    enabled: true
    action: "CLOSE_ALL_AND_LOCKOUT"

  # RULE-011: Symbol Blocks
  symbol_blocks:
    enabled: true
    blocked_symbols:
      - "RTY"   # Russell 2000
      - "BTC"   # Bitcoin futures
    action: "CANCEL_ORDER"        # Cancel orders in blocked symbols
    close_existing: true          # Also close any existing positions

  # RULE-012: Trade Management
  trade_management:
    enabled: false            # Disabled by default
    auto_stop_loss: true
    stop_loss_ticks: 10
```

---

## 🔧 Global Settings

### **global** (object, optional)

Global configuration applying to all rules.

---

#### **strict_mode** (boolean, optional)

If `true`, ANY rule breach causes immediate permanent lockout.

**Default:** `false`
**Use Case:** Maximum safety - one strike and you're out

**Behavior:**
- `false`: Each rule has its own enforcement action
- `true`: All breaches → CLOSE_ALL_AND_LOCKOUT (permanent)

---

#### **logging_level** (string, optional)

Logging verbosity level.

**Default:** `"INFO"`
**Options:** `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`

**Levels:**
- `DEBUG`: Everything (very verbose)
- `INFO`: General info + warnings + errors
- `WARNING`: Warnings + errors only
- `ERROR`: Errors only

---

## 🚨 Rule Configurations

Each rule has its own configuration block under `rules:`.

---

### **RULE-001: max_contracts**

**Purpose:** Limit total net contracts across all instruments

```yaml
max_contracts:
  enabled: true           # Enable this rule
  limit: 5                # Max net contracts (default: 5)
  count_type: "net"       # "net" or "gross" (default: "net")
```

**Fields:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable rule |
| `limit` | int | `5` | Max contracts allowed |
| `count_type` | string | `"net"` | Count method: "net" (long-short) or "gross" (absolute) |

**Example:**
```yaml
max_contracts:
  enabled: true
  limit: 10
  count_type: "gross"  # Count all contracts regardless of direction
```

**Validation:**
- `limit` must be > 0
- `count_type` must be "net" or "gross"

**Reference:** `03-RISK-RULES/rules/01_max_contracts.md`

---

### **RULE-002: max_contracts_per_instrument**

**Purpose:** Limit contracts per individual instrument (per-symbol limits)

```yaml
max_contracts_per_instrument:
  enabled: true
  limits:
    MNQ: 2              # Max 2 micro NQ contracts
    NQ: 1               # Max 1 full NQ contract
    ES: 1               # Max 1 ES contract
    MES: 3              # Max 3 micro ES contracts
  enforcement: "reduce_to_limit"  # "reduce_to_limit" or "close_all"
  unknown_symbol_action: "allow_with_limit:1"  # Default limit for unlisted symbols
```

**Fields:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable rule |
| `limits` | dict | `{}` | Per-symbol contract limits (symbol: limit) |
| `enforcement` | string | `"reduce_to_limit"` | "reduce_to_limit" or "close_all" |
| `unknown_symbol_action` | string | `"block"` | "block", "allow_with_limit:N", or "allow_unlimited" |

**Validation:**
- `limits` must be dict with string keys (symbols) and int values (limits)
- All limit values must be > 0
- `enforcement` must be "reduce_to_limit" or "close_all"

**Reference:** `03-RISK-RULES/rules/02_max_contracts_per_instrument.md`

---

### **RULE-003: daily_realized_loss**

**Purpose:** Limit daily realized loss (P&L from closed trades)

```yaml
daily_realized_loss:
  enabled: true
  loss_limit: 500.00              # Max loss in dollars (default: 500)
  action: "CLOSE_ALL_AND_LOCKOUT" # Enforcement action
  lockout_until: "daily_reset"    # "daily_reset" or "permanent"
```

**Fields:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable rule |
| `loss_limit` | float | `500.00` | Max daily loss (negative P&L) |
| `action` | string | `"CLOSE_ALL_AND_LOCKOUT"` | Enforcement action |
| `lockout_until` | string | `"daily_reset"` | When lockout expires |

**Actions:**
- `"CLOSE_ALL_POSITIONS"` - Close positions only
- `"CLOSE_ALL_AND_LOCKOUT"` - Close + lockout

**Lockout Duration:**
- `"daily_reset"` - Lock until 5 PM (daily reset time)
- `"permanent"` - Never unlock (admin must clear)

**Validation:**
- `loss_limit` must be > 0
- `action` must be valid enforcement action
- `lockout_until` must be "daily_reset" or "permanent"

**Reference:** `03-RISK-RULES/rules/03_daily_realized_loss.md`

---

### **RULE-004: daily_unrealized_loss**

**Purpose:** Limit unrealized loss per position (per-trade stop-loss)

```yaml
daily_unrealized_loss:
  enabled: true
  loss_limit: 300.00              # Max unrealized loss per position (default: 300)
  scope: "per_position"           # "total" or "per_position" (default: per_position)
  action: "CLOSE_POSITION"        # Close only losing position
  lockout: false                  # No lockout (default: false)
```

**Fields:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable rule |
| `loss_limit` | float | `300.00` | Max unrealized loss (per position or total) |
| `scope` | string | `"per_position"` | "total" (all positions) or "per_position" (each position) |
| `action` | string | `"CLOSE_POSITION"` | Enforcement action |
| `lockout` | bool | `false` | Whether to lockout account |

**Validation:**
- `loss_limit` must be > 0
- `scope` must be "total" or "per_position"

**Reference:** `03-RISK-RULES/rules/04_daily_unrealized_loss.md`

---

### **RULE-005: max_unrealized_profit**

**Purpose:** Auto-close positions at profit target or breakeven

```yaml
max_unrealized_profit:
  enabled: true
  mode: "profit_target"           # "profit_target" or "breakeven"
  profit_target: 1000.00          # Used when mode = "profit_target" (default: 1000)
  scope: "per_position"           # Close each position individually
  action: "CLOSE_POSITION"        # Close only profitable position
```

**Fields:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable rule |
| `mode` | string | `"profit_target"` | "profit_target" (close at $ amount) or "breakeven" (close at $0 P&L) |
| `profit_target` | float | `1000.00` | Auto-close profit level (only for profit_target mode) |
| `scope` | string | `"per_position"` | Close each position individually |
| `action` | string | `"CLOSE_POSITION"` | Enforcement action |

**Modes:**
- `"profit_target"`: Close position when unrealized P&L reaches `profit_target` (e.g., +$1000)
- `"breakeven"`: Close position when unrealized P&L reaches $0 (back to entry price)

**Validation:**
- `mode` must be "profit_target" or "breakeven"
- `profit_target` must be > 0 (when mode = "profit_target")

**Reference:** `03-RISK-RULES/rules/05_max_unrealized_profit.md`

---

### **RULE-006: trade_frequency_limit**

**Purpose:** Limit number of trades in time window

```yaml
trade_frequency_limit:
  enabled: true
  max_trades: 30              # Max trades in window (default: 30)
  time_window_minutes: 60     # Time window (default: 60)
```

**Fields:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable rule |
| `max_trades` | int | `30` | Max trades allowed |
| `time_window_minutes` | int | `60` | Time window in minutes |

**Validation:**
- `max_trades` must be > 0
- `time_window_minutes` must be > 0

**Reference:** `03-RISK-RULES/rules/06_trade_frequency_limit.md`

---

### **RULE-007: cooldown_after_loss**

**Purpose:** Enforce cooldown period after losing trade

```yaml
cooldown_after_loss:
  enabled: true
  loss_threshold: 100.00      # Loss that triggers cooldown (default: 100)
  cooldown_seconds: 300       # Cooldown duration (default: 300 = 5 min)
```

**Fields:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable rule |
| `loss_threshold` | float | `100.00` | Loss amount that triggers cooldown |
| `cooldown_seconds` | int | `300` | Cooldown duration in seconds |

**Validation:**
- `loss_threshold` must be > 0
- `cooldown_seconds` must be > 0

**Reference:** `03-RISK-RULES/rules/07_cooldown_after_loss.md`

---

### **RULE-008: no_stop_loss_grace**

**Purpose:** Require stop-loss on all positions within grace period

```yaml
no_stop_loss_grace:
  enabled: true
  grace_period_seconds: 30    # Grace period (default: 30)
  action: "CLOSE_POSITION"    # Close only position without stop-loss
```

**Fields:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable rule |
| `grace_period_seconds` | int | `30` | Time allowed without stop-loss |
| `action` | string | `"CLOSE_POSITION"` | Enforcement action (closes specific position) |

**Validation:**
- `grace_period_seconds` must be > 0

**Reference:** `03-RISK-RULES/rules/08_no_stop_loss_grace.md`

---

### **RULE-009: session_block_outside**

**Purpose:** Block trading outside allowed hours

```yaml
session_block_outside:
  enabled: true
  allowed_hours:
    start: "08:30"            # Session start time (default: 08:30)
    end: "15:00"              # Session end time (default: 15:00)
  timezone: "America/Chicago" # Timezone (default: America/Chicago)
  action: "CANCEL_ORDER"      # Cancel orders outside hours
```

**Fields:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable rule |
| `allowed_hours.start` | string | `"08:30"` | Session start time (HH:MM) |
| `allowed_hours.end` | string | `"15:00"` | Session end time (HH:MM) |
| `timezone` | string | `"America/Chicago"` | Timezone for times |
| `action` | string | `"CANCEL_ORDER"` | Enforcement action (cancels orders reactively) |

**Time Format:** `"HH:MM"` (24-hour format)

**Timezone:** IANA timezone name (e.g., "America/New_York", "UTC")

**Validation:**
- `start` must be valid time format
- `end` must be valid time format
- `end` must be after `start`
- `timezone` must be valid IANA timezone

**Reference:** `03-RISK-RULES/rules/09_session_block_outside.md`

---

### **RULE-010: auth_loss_guard**

**Purpose:** Detect and prevent authentication bypass attempts

```yaml
auth_loss_guard:
  enabled: true
  action: "CLOSE_ALL_AND_LOCKOUT"  # Permanent lockout on auth bypass
```

**Fields:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable rule |
| `action` | string | `"CLOSE_ALL_AND_LOCKOUT"` | Enforcement action |

**Note:** This rule has no configurable thresholds - any auth bypass is immediate breach.

**Reference:** `03-RISK-RULES/rules/10_auth_loss_guard.md`

---

### **RULE-011: symbol_blocks**

**Purpose:** Block trading specific instruments

```yaml
symbol_blocks:
  enabled: true
  blocked_symbols:            # List of blocked symbols
    - "RTY"     # Russell 2000
    - "BTC"     # Bitcoin futures
  action: "CANCEL_ORDER"      # Cancel orders in blocked symbols
  close_existing: true        # Also close any existing positions
```

**Fields:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable rule |
| `blocked_symbols` | array | `[]` | List of blocked symbol IDs |
| `action` | string | `"CANCEL_ORDER"` | Enforcement action (reactively cancels orders) |
| `close_existing` | bool | `true` | Whether to close existing positions in blocked symbols |

**Symbol Format:** Symbol root (e.g., "RTY", "MNQ", "BTC" - extracted from contract ID)

**Validation:**
- `blocked_symbols` must be array of strings
- Can be empty array (no symbols blocked)

**Reference:** `03-RISK-RULES/rules/11_symbol_blocks.md`

---

### **RULE-012: trade_management**

**Purpose:** Automatically place stop-loss orders

```yaml
trade_management:
  enabled: false              # Disabled by default (requires testing)
  auto_stop_loss: true        # Auto-place stop-loss on positions
  stop_loss_ticks: 10         # Stop-loss distance in ticks
```

**Fields:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable/disable rule |
| `auto_stop_loss` | bool | `true` | Auto-place stop-loss orders |
| `stop_loss_ticks` | int | `10` | Stop-loss distance in ticks |

**Validation:**
- `stop_loss_ticks` must be > 0

**Note:** Disabled by default - requires careful testing before enabling.

**Reference:** `03-RISK-RULES/rules/12_trade_management.md`

---

## ✅ Complete Example

```yaml
# risk_config.yaml
# Risk rule configurations for trading account monitoring

global:
  strict_mode: false        # Normal mode - use per-rule enforcement
  logging_level: "INFO"     # Standard logging

rules:
  max_contracts:
    enabled: true
    limit: 5
    count_type: "net"

  max_contracts_per_instrument:
    enabled: true
    limits:
      MNQ: 2
      NQ: 1
      ES: 1
      MES: 3
    enforcement: "reduce_to_limit"
    unknown_symbol_action: "allow_with_limit:1"

  daily_realized_loss:
    enabled: true
    loss_limit: 500.00
    action: "CLOSE_ALL_AND_LOCKOUT"
    lockout_until: "daily_reset"

  daily_unrealized_loss:
    enabled: true
    loss_limit: 300.00
    scope: "per_position"
    action: "CLOSE_POSITION"
    lockout: false

  max_unrealized_profit:
    enabled: true
    mode: "profit_target"
    profit_target: 1000.00
    scope: "per_position"
    action: "CLOSE_POSITION"

  trade_frequency_limit:
    enabled: true
    max_trades: 30
    time_window_minutes: 60

  cooldown_after_loss:
    enabled: true
    loss_threshold: 100.00
    cooldown_seconds: 300

  no_stop_loss_grace:
    enabled: true
    grace_period_seconds: 30
    action: "CLOSE_POSITION"

  session_block_outside:
    enabled: true
    allowed_hours:
      start: "08:30"
      end: "15:00"
    timezone: "America/Chicago"
    action: "CANCEL_ORDER"

  auth_loss_guard:
    enabled: true
    action: "CLOSE_ALL_AND_LOCKOUT"

  symbol_blocks:
    enabled: true
    blocked_symbols:
      - "RTY"
      - "BTC"
    action: "CANCEL_ORDER"
    close_existing: true

  trade_management:
    enabled: false            # Test carefully before enabling!
    auto_stop_loss: true
    stop_loss_ticks: 10
```

---

## 🔧 Configuration Loader

**Location:** `src/config/loader.py`

**Function:** `load_risk_config()`

**Pseudocode:**
```python
def load_risk_config(file_path='config/risk_config.yaml'):
    """
    Load and validate risk configuration.

    Returns:
        Dict[str, RuleConfig]: Rule configs by rule name

    Raises:
        ValidationError: If validation fails
    """
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)

    # Validate top-level structure
    if 'rules' not in config:
        raise ValidationError("Missing 'rules' key")

    # Parse global settings (optional)
    global_config = config.get('global', {})
    strict_mode = global_config.get('strict_mode', False)
    logging_level = global_config.get('logging_level', 'INFO')

    # Load each rule config
    rule_configs = {}
    for rule_name, rule_data in config['rules'].items():
        # Create RuleConfig object
        rule_config = RuleConfig(
            rule_id=f"RULE-{rule_name}",
            name=rule_name,
            enabled=rule_data.get('enabled', True),
            params=rule_data
        )

        # Validate rule-specific parameters
        validate_rule_config(rule_name, rule_data)

        rule_configs[rule_name] = rule_config

    return rule_configs, strict_mode, logging_level
```

---

## 🔄 Hot Reloading

The Admin CLI can reload configuration without restarting the daemon.

**Process:**
1. Admin edits `risk_config.yaml`
2. Admin runs "Reload Config" in Admin CLI
3. Daemon reloads YAML file
4. Daemon validates new configuration
5. If valid: Apply new config
6. If invalid: Keep old config, show error

**What Can Be Hot-Reloaded:**
- ✅ Enable/disable individual rules
- ✅ Change rule parameters (limits, thresholds, etc.)
- ✅ Change global settings

**What Requires Restart:**
- Account changes (accounts.yaml)
- Module changes (code changes)

---

## 🧪 Validation

### **Validation Rules**

1. **File exists:** `config/risk_config.yaml` must be present
2. **Valid YAML:** Must parse without syntax errors
3. **Top-level 'rules' key:** Required
4. **Per-rule validation:** Each rule's parameters validated

### **Per-Rule Validation**

Each rule validates its own parameters:
- Numeric fields: Must be correct type (int/float)
- Numeric limits: Must be > 0
- Time formats: Must be valid HH:MM
- Timezone: Must be valid IANA timezone
- Actions: Must be valid enforcement action type
- Symbol lists: Must be array of strings

---

## 📝 Summary

**Configuration File:** `config/risk_config.yaml`

**Sections:**
- `global`: Global settings (optional)
- `rules`: 12 rule configurations

**Common Fields per Rule:**
- `enabled` (bool) - Enable/disable rule
- Rule-specific parameters

**Hot Reloadable:** Yes (via Admin CLI)

**Validation:** On daemon startup + on hot reload

---

**Related Files:**
- `src/config/loader.py` - Configuration loader
- `src/data_models/rule_config.py` - RuleConfig dataclass
- `03-RISK-RULES/rules/*.md` - Individual rule specifications

---

**Status:** Complete and ready for implementation
