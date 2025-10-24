# Risk Rules Architecture

**Last Updated:** 2025-10-23
**Status:** Complete Analysis
**Agent:** RISK RULES ANALYZER

---

## Overview

The Risk Manager implements **12 specialized risk rules** that protect trading accounts from various failure modes. Each rule monitors specific events, detects violations, and triggers appropriate enforcement actions. The system is designed for **extreme modularity** - adding new rules requires only 2-3 hours.

**Design Philosophy:**
- Each rule does ONE thing
- All rules share a common interface
- Rules are independent (no cross-dependencies)
- Enforcement is centralized in MOD-001
- State tracking is delegated to core modules

---

## Rule Catalog

### RULE-001: MaxContracts
**Purpose:** Cap net contract exposure across all instruments to prevent over-leveraging

**Trigger:** `GatewayUserPosition` (on every position update)

**Condition:**
```python
total_net_contracts > configured_limit
```

**Action:** Trade-by-Trade (No Lockout)
- Close all positions (if `close_all: true`)
- OR reduce to limit (if `reduce_to_limit: true`)
- Log enforcement
- NO lockout - can trade again immediately

**Config:**
```yaml
max_contracts:
  enabled: true
  limit: 5
  count_type: "net"  # or "gross"
  close_all: true
  reduce_to_limit: false
  lockout_on_breach: false
```

**Status:** ✅ Implemented
**Dependencies:** MOD-001 (enforcement/actions)
**Specs File:** `03-RISK-RULES/rules/01_max_contracts.md`

---

### RULE-002: MaxContractsPerInstrument
**Purpose:** Enforce per-symbol contract limits to prevent concentration risk

**Trigger:** `GatewayUserPosition`

**Condition:**
```python
contracts_in_symbol > limit_for_symbol[symbol]
```

**Action:** Trade-by-Trade (No Lockout)
- Reduce position to symbol limit
- OR close entire position in that symbol
- NO lockout

**Config:**
```yaml
max_contracts_per_instrument:
  enabled: true
  limits:
    MNQ: 2
    ES: 1
    NQ: 1
  enforcement: "reduce_to_limit"
  unknown_symbol_action: "block"
  lockout_on_breach: false
```

**Status:** ✅ Implemented
**Dependencies:** MOD-001
**Specs File:** `03-RISK-RULES/rules/02_max_contracts_per_instrument.md`

---

### RULE-003: DailyRealizedLoss
**Purpose:** Enforce hard daily realized P&L limit - stops trading when daily loss threshold is hit

**Trigger:** `GatewayUserTrade` (only trades with P&L, not half-turns)

**Condition:**
```python
daily_realized_pnl <= loss_limit  # e.g., -500
```

**Action:** Hard Lockout (Until Reset at 17:00)
1. Close all positions
2. Cancel all orders
3. Set lockout until 17:00 (configurable reset time)
4. Log enforcement
5. Auto-unlock at reset time

**Config:**
```yaml
daily_realized_loss:
  enabled: true
  limit: -500
  reset_time: "17:00"
  timezone: "America/New_York"
  enforcement: "close_all_and_lockout"
  lockout_until_reset: true
```

**Status:** ✅ Implemented
**Dependencies:** MOD-001, MOD-002 (lockout), MOD-004 (reset scheduler), PnL tracker
**Specs File:** `03-RISK-RULES/rules/03_daily_realized_loss.md`

---

### RULE-004: DailyUnrealizedLoss
**Purpose:** Enforce hard daily floating loss limit - stops trading when unrealized P&L drops below threshold

**Trigger:** `GatewayUserPosition`, `GatewayQuote` (continuous monitoring)

**Condition:**
```python
total_unrealized_pnl <= loss_limit  # e.g., -300
# Calculated from: (current_price - entry_price) * tick_value * size
```

**Action:** Hard Lockout (Until Reset) OR Per-Position Close
- **Mode 1 (per_position):** Close only losing position, no lockout
- **Mode 2 (total):** Close all + lockout until reset

**Config:**
```yaml
daily_unrealized_loss:
  enabled: true
  loss_limit: 300.00
  scope: "per_position"  # or "total"
  action: "CLOSE_POSITION"  # or "CLOSE_ALL_AND_LOCKOUT"
  lockout: false
```

**Status:** ✅ Implemented
**Dependencies:** MOD-001, MOD-002, MOD-004, MOD-005 (unrealized PnL calc), MOD-006 (quote tracker), MOD-007 (contract cache)
**Specs File:** `03-RISK-RULES/rules/04_daily_unrealized_loss.md`

---

### RULE-005: MaxUnrealizedProfit
**Purpose:** Enforce profit target - close positions when unrealized profit hits target to lock in gains

**Trigger:** `GatewayUserPosition`, `GatewayQuote`

**Condition:**
```python
total_unrealized_pnl >= profit_target  # e.g., +1000
```

**Action:** Hard Lockout (Until Reset)
1. Close all positions (locks in profit)
2. Cancel all orders
3. Set lockout until reset time
4. Prevents "giving back profits"

**Config:**
```yaml
max_unrealized_profit:
  enabled: true
  mode: "profit_target"  # or "breakeven"
  profit_target: 1000.00
  scope: "per_position"
  action: "CLOSE_POSITION"
```

**Status:** ✅ Implemented
**Dependencies:** MOD-001, MOD-002, MOD-004, MOD-005, MOD-006, MOD-007
**Specs File:** `03-RISK-RULES/rules/05_max_unrealized_profit.md`

---

### RULE-006: TradeFrequencyLimit
**Purpose:** Prevent overtrading by limiting trades per time window

**Trigger:** `GatewayUserTrade`

**Condition:**
```python
trades_in_minute > limit_per_minute
OR trades_in_hour > limit_per_hour
OR trades_in_session > limit_per_session
```

**Action:** Configurable Timer Lockout (No Position Close)
- Trade already executed, can't reverse
- Set cooldown timer (duration depends on breach type)
- Auto-unlock when timer expires
- Different cooldowns for different windows

**Config:**
```yaml
trade_frequency_limit:
  enabled: true
  limits:
    per_minute: 3
    per_hour: 10
    per_session: 50
  cooldown_on_breach:
    per_minute_breach: 60      # 1 min
    per_hour_breach: 1800      # 30 min
    per_session_breach: 3600   # 1 hour
  reset_time: "17:00"
```

**Status:** ✅ Implemented
**Dependencies:** MOD-002 (cooldown), MOD-003 (timer), MOD-004 (session reset), MOD-008 (trade counter)
**Specs File:** `03-RISK-RULES/rules/06_trade_frequency_limit.md`

---

### RULE-007: CooldownAfterLoss
**Purpose:** Force break after losing trades to prevent revenge trading and emotional decision-making

**Trigger:** `GatewayUserTrade` (only trades with negative P&L)

**Condition:**
```python
trade_pnl <= loss_threshold  # e.g., -100, -200, -300
```

**Action:** Configurable Timer Lockout
- Match loss amount to cooldown tier
- Larger losses = longer cooldowns
- Auto-unlock when timer expires
- NO position close (trade already happened)

**Config:**
```yaml
cooldown_after_loss:
  enabled: true
  loss_thresholds:
    - loss_amount: -100
      cooldown_duration: 300    # 5 min
    - loss_amount: -200
      cooldown_duration: 900    # 15 min
    - loss_amount: -300
      cooldown_duration: 1800   # 30 min
  allow_trading_during_cooldown: false
```

**Status:** ✅ Implemented
**Dependencies:** MOD-002, MOD-003
**Specs File:** `03-RISK-RULES/rules/07_cooldown_after_loss.md`

---

### RULE-008: NoStopLossGrace
**Purpose:** Enforce stop-loss placement within grace period after position opens

**Trigger:**
- `GatewayUserPosition` (position opens)
- `GatewayUserOrder` (stop-loss detection)
- Background timer check

**Condition:**
```python
position_age > grace_period_seconds
AND no_stop_loss_detected
```

**Action:** Trade-by-Trade (No Lockout)
- Close position immediately
- Log enforcement
- NO lockout - can open next trade immediately

**Config:**
```yaml
no_stop_loss_grace:
  enabled: true
  grace_period_seconds: 30
  action: "CLOSE_POSITION"
```

**Detection Logic:**
```python
# Detects stop-loss orders:
# - Type: Stop (4), StopLimit (3), or TrailingStop (5)
# - For LONG: Sell order with stop price BELOW entry
# - For SHORT: Buy order with stop price ABOVE entry
```

**Status:** ✅ Implemented
**Dependencies:** MOD-001
**Specs File:** `03-RISK-RULES/rules/08_no_stop_loss_grace.md`

---

### RULE-009: SessionBlockOutside
**Purpose:** Block trading outside configured session hours and on holidays

**Trigger:**
- `GatewayUserPosition` (position opens outside session)
- Background timer (session end reached)
- Holiday check

**Condition:**
```python
current_time < session_start OR current_time > session_end
OR is_holiday(current_date)
```

**Action:** Hard Lockout (Session-Based)
1. Close position if opened outside session
2. OR close all positions at session end
3. Cancel all orders
4. Set lockout until next session start
5. Auto-unlock at session start

**Config:**
```yaml
session_block_outside:
  enabled: true
  global_session:
    enabled: true
    start: "09:30"
    end: "16:00"
    timezone: "America/New_York"
  per_instrument_sessions:
    enabled: true
    sessions:
      ES:
        start: "18:00"  # Sunday 6pm
        end: "17:00"    # Friday 5pm
  close_positions_at_session_end: true
  lockout_outside_session: true
  respect_holidays: true
```

**Status:** ✅ Implemented
**Dependencies:** MOD-001, MOD-002, MOD-003 (timer), MOD-004 (holiday calendar)
**Specs File:** `03-RISK-RULES/rules/09_session_block_outside.md`

---

### RULE-010: AuthLossGuard
**Purpose:** Monitor TopstepX `canTrade` status and enforce lockout when API signals account restriction

**Trigger:** `GatewayUserAccount` (account status updates)

**Condition:**
```python
account.canTrade == False
```

**Action:** Hard Lockout (API-Driven, Indefinite)
1. Close all positions immediately
2. Cancel all orders
3. Set indefinite lockout (no expiry time)
4. Auto-unlock ONLY when `canTrade` returns to `True`
5. Ensures compliance with platform restrictions

**Config:**
```yaml
auth_loss_guard:
  enabled: true
  enforcement: "close_all_and_lockout"
  auto_unlock_on_restore: true
  check_on_startup: true
```

**Status:** ✅ Implemented
**Dependencies:** MOD-001, MOD-002
**Specs File:** `03-RISK-RULES/rules/10_auth_loss_guard.md`

---

### RULE-011: SymbolBlocks
**Purpose:** Blacklist specific symbols - immediately close any position and permanently prevent trading in blocked instruments

**Trigger:** `GatewayUserPosition`, background monitor

**Condition:**
```python
symbol_root in blocked_symbols
# Extract from: "CON.F.US.RTY.H25" → "RTY"
```

**Action:** Hard Lockout (Symbol-Specific, Permanent)
1. Close position in blocked symbol immediately
2. Cancel all orders for symbol
3. Set permanent symbol-level lockout
4. Monitor for any future fills in blocked symbols

**Config:**
```yaml
symbol_blocks:
  enabled: true
  blocked_symbols:
    - "RTY"
    - "BTC"
  action: "CANCEL_ORDER"
  close_existing: true
```

**Status:** ✅ Implemented
**Dependencies:** MOD-001, MOD-002 (symbol-specific lockout)
**Specs File:** `03-RISK-RULES/rules/11_symbol_blocks.md`

---

### RULE-012: TradeManagement
**Purpose:** Automated trade management - auto breakeven stop-loss and trailing stops

**Trigger:** `GatewayUserPosition`, `GatewayQuote`, `GatewayUserOrder`

**Condition:**
```python
# Auto Breakeven:
profit_ticks >= breakeven_trigger_ticks

# Trailing Stop:
profit_ticks >= trailing_activation_ticks
```

**Action:** Trade-by-Trade Automation (No Close, No Lockout)
1. Modify existing stop-loss order to breakeven price
2. OR create new stop-loss if none exists
3. Update trailing stop as price moves favorably
4. NO position close
5. NO lockout

**Config:**
```yaml
trade_management:
  enabled: true
  auto_breakeven:
    enabled: true
    profit_trigger_ticks: 10
    offset_ticks: 0
  trailing_stop:
    enabled: true
    activation_ticks: 20
    trail_distance_ticks: 10
    update_frequency: 1
```

**Status:** ✅ Implemented
**Dependencies:** MOD-006 (quote tracker), MOD-007 (contract cache)
**Specs File:** `03-RISK-RULES/rules/12_trade_management.md`

---

## Rule Evaluation Flow

### When Are Rules Checked?

**Event-Driven Architecture:**

1. **SignalR Event Received** → Event Router receives event
2. **State Updated FIRST** → StateManager updates positions/trades/orders
3. **Lockout Check** → If account locked, skip rule processing
4. **Rule Evaluation** → Each rule's `check()` method called with event
5. **Enforcement** → If breach detected, EnforcementEngine executes action

**Order of Operations:**
```
SignalR Event → Update State → Check Lockout → Evaluate Rules → Enforce Action
```

### Rule Evaluation Order

Rules are evaluated **in order of initialization** in EventRouter:

```python
self.rules = [
    MaxContractsRule(...),                    # RULE-001
    MaxContractsPerInstrumentRule(...),       # RULE-002
    DailyRealizedLossRule(...),               # RULE-003
    DailyUnrealizedLossRule(...),             # RULE-004
    MaxUnrealizedProfitRule(...),             # RULE-005
    TradeFrequencyLimitRule(...),             # RULE-006
    CooldownAfterLossRule(...),               # RULE-007
    NoStopLossGraceRule(...),                 # RULE-008
    SessionBlockOutsideRule(...),             # RULE-009
    AuthLossGuardRule(...),                   # RULE-010
    SymbolBlocksRule(...),                    # RULE-011
    TradeManagementRule(...),                 # RULE-012
]

# Router checks each rule for each event:
for rule in self.rules:
    action = rule.check(account_id, event_type, event_data)
    if action:
        enforcement_engine.execute(action)
        break  # Stop after first breach
```

**Important:** First breach wins - if RULE-001 breaches, later rules don't execute.

---

## Rule Architecture

### Standard Rule Interface

**Every rule implements this interface:**

```python
class RiskRule:
    """Base interface for all risk rules."""

    def __init__(self, config: RuleConfig, state_manager: StateManager, ...):
        """
        Initialize rule with configuration and dependencies.

        Args:
            config: Rule configuration from risk_config.yaml
            state_manager: Access to positions, trades, orders
            ...: Other module dependencies as needed
        """
        self.config = config
        self.enabled = config.enabled
        # Parse rule-specific parameters

    def check(self, account_id: int, event_type: str, event_data: dict) -> Optional[EnforcementAction]:
        """
        Check if rule is breached.

        Args:
            account_id: Account to check
            event_type: Event type (e.g., "GatewayUserPosition")
            event_data: Event payload from TopstepX

        Returns:
            EnforcementAction if breached, None otherwise
        """
        # Return early if disabled
        if not self.enabled:
            return None

        # Return early if event not relevant
        if event_type not in self.trigger_events:
            return None

        # Check breach condition
        if self._is_breached(account_id, event_data):
            return EnforcementAction(
                type=EnforcementActionType.CLOSE_ALL_POSITIONS,
                reason=self._get_breach_reason(...),
                rule_id="RULE-XXX",
                account_id=account_id
            )

        return None

    def _is_breached(self, account_id: int, event_data: dict) -> bool:
        """Detect if breach condition is met."""
        # Rule-specific logic
        pass

    def _get_breach_reason(self, account_id: int, event_data: dict) -> str:
        """Generate human-readable breach reason."""
        # Return descriptive message
        pass
```

### EnforcementAction Data Model

```python
@dataclass
class EnforcementAction:
    """Enforcement action to be executed."""

    type: EnforcementActionType  # What action to take
    reason: str                   # Human-readable reason
    rule_id: str                  # Which rule triggered (e.g., "RULE-003")
    account_id: int               # Account to enforce on

    # Optional fields:
    contract_id: Optional[str] = None      # For symbol-specific actions
    lockout_until: Optional[datetime] = None  # For lockout actions
    metadata: Optional[dict] = None        # Additional context

class EnforcementActionType(Enum):
    """Types of enforcement actions."""
    CLOSE_ALL_POSITIONS = "close_all_positions"
    CLOSE_POSITION = "close_position"
    CLOSE_ALL_AND_LOCKOUT = "close_all_and_lockout"
    COOLDOWN = "cooldown"
    REJECT_ORDER = "reject_order"
    AUTO_STOP_LOSS = "auto_stop_loss"
    SYMBOL_LOCKOUT = "symbol_lockout"
```

---

## Enforcement Actions

**All enforcement is centralized in MOD-001** (`src/enforcement/actions.py`)

### Available Actions

| Action | Purpose | API Calls | Used By |
|--------|---------|-----------|---------|
| `close_all_positions(account_id)` | Close all open positions | 1 search + n closes | RULE-001, 003, 004, 005, 009, 010 |
| `close_position(account_id, contract_id)` | Close specific position | 1 close | RULE-002, 008, 009, 011 |
| `reduce_position_to_limit(account_id, contract_id, target_size)` | Partially close position | 1 search + 1 partial | RULE-001, 002 |
| `cancel_all_orders(account_id)` | Cancel all pending orders | 1 search + n cancels | RULE-003, 004, 005, 009, 010 |
| `cancel_order(account_id, order_id)` | Cancel specific order | 1 cancel | Individual rules |

### Enforcement Sequence

```
1. Rule detects breach
2. Rule creates EnforcementAction object
3. Rule returns action to EventRouter
4. EventRouter passes action to EnforcementEngine
5. EnforcementEngine executes via MOD-001:
   a. Call API (close positions/cancel orders)
   b. Update lockout state (MOD-002)
   c. Log enforcement (logs/enforcement.log)
   d. Notify Trader CLI (WebSocket)
6. Return control to EventRouter
```

**Performance:** Typically < 500ms from breach detection to enforcement completion

---

## Configuration

### YAML Configuration Structure

**Location:** `config/risk_config.yaml`

```yaml
# Global settings
risk_manager:
  enabled: true
  timezone: "America/New_York"
  daily_reset_time: "17:00"

# Rule-specific configurations
rules:
  rule_001_max_contracts:
    enabled: true
    limit: 5
    count_type: "net"
    close_all: true
    reduce_to_limit: false
    lockout_on_breach: false

  rule_002_max_contracts_per_instrument:
    enabled: true
    limits:
      MNQ: 2
      ES: 1
      NQ: 1
    enforcement: "reduce_to_limit"
    unknown_symbol_action: "block"

  rule_003_daily_realized_loss:
    enabled: true
    limit: -500
    reset_time: "17:00"
    timezone: "America/New_York"
    enforcement: "close_all_and_lockout"

  # ... all 12 rules configured here
```

### Configuration Loading

```python
# In EventRouter.__init__():
config = load_config("config/risk_config.yaml")
rule_configs = parse_rule_configs(config['rules'])

# Initialize each rule with its config:
self.rules = [
    MaxContractsRule(rule_configs['rule_001'], state_manager),
    MaxContractsPerInstrumentRule(rule_configs['rule_002'], state_manager),
    # ... etc.
]
```

### Runtime Configuration Changes

- Config file can be reloaded without daemon restart
- Use `SIGHUP` signal or admin CLI command
- Rules re-initialize with new config
- Active lockouts/cooldowns preserved

---

## Rule Dependencies

### Core Module Dependencies

**Rules depend on these core modules for state access:**

| Module | Purpose | Used By Rules |
|--------|---------|---------------|
| **MOD-001** (enforcement/actions) | Execute enforcement actions | ALL rules |
| **MOD-002** (lockout_manager) | Manage lockouts/cooldowns | 003, 004, 005, 006, 007, 009, 010, 011 |
| **MOD-003** (timer_manager) | Timer-based auto-unlock | 006, 007, 009 |
| **MOD-004** (reset_scheduler) | Daily reset scheduling | 003, 004, 005, 006, 009 |
| **MOD-005** (pnl_tracker) | Calculate P&L | 003, 004, 005 |
| **MOD-006** (quote_tracker) | Real-time quotes | 004, 005, 012 |
| **MOD-007** (contract_cache) | Contract metadata | 004, 005, 012 |
| **MOD-008** (trade_counter) | Track trade counts | 006 |
| **MOD-009** (state_manager) | Positions/orders/trades | ALL rules |

### Dependency Graph

```
All Rules
    ↓
StateManager (MOD-009) - provides current state
    ↓
Enforcement Actions (MOD-001) - executes API calls
    ↓
TopstepX REST API
```

**Additional dependencies:**
```
RULE-003, 004, 005 → PnL Tracker (MOD-005) → Quote Tracker (MOD-006) + Contract Cache (MOD-007)
RULE-006 → Trade Counter (MOD-008)
RULE-003, 004, 005, 006, 007, 009, 010, 011 → Lockout Manager (MOD-002)
RULE-006, 007, 009 → Timer Manager (MOD-003)
RULE-003, 004, 005, 006, 009 → Reset Scheduler (MOD-004)
```

### StateManager Interface

**All rules access state via StateManager:**

```python
# Get current positions
positions = state_manager.get_positions(account_id)
position = state_manager.get_position_by_contract(account_id, contract_id)

# Get position counts
total_contracts = state_manager.get_position_count(account_id)
symbol_contracts = state_manager.get_contract_count(account_id, contract_id)

# Get orders
orders = state_manager.get_orders(account_id)

# Get trades
trades = state_manager.get_trades(account_id, start_time, end_time)

# Get account status
can_trade = state_manager.get_can_trade_status(account_id)
```

---

## Rule Interaction

### No Cross-Rule Dependencies

**Design principle:** Rules are independent. No rule depends on another rule.

**Benefits:**
- Rules can be added/removed independently
- Rules can be enabled/disabled in any combination
- Rules don't need to know about each other
- Testing is simpler (test each rule in isolation)

### Indirect Interaction via State

**Rules CAN affect each other indirectly:**

1. **RULE-001** closes all positions → **RULE-004** sees no positions → no unrealized loss
2. **RULE-003** locks out account → EventRouter skips all other rules
3. **RULE-010** (canTrade=false) locks out → All other rules skipped

**However, this is NOT rule-to-rule communication. It's:**
- Rule A affects shared state
- EventRouter checks lockout before evaluating rules
- Rule B sees different state as a result

### First Breach Wins

**EventRouter stops processing after first breach:**

```python
for rule in self.rules:
    action = rule.check(account_id, event_type, event_data)
    if action:
        self.enforcement_engine.execute(action)
        break  # Stop - don't check other rules
```

**Implication:** Rule order matters. Earlier rules have priority.

**Example:**
- RULE-001 (MaxContracts) triggers first
- Closes all positions
- RULE-004 (DailyUnrealizedLoss) never sees the breach
- Only one enforcement action per event

---

## Integration with Core Modules

### Event Flow

```
TopstepX SignalR → EventRouter → Update State → Check Rules → Enforce
```

**Detailed sequence:**

1. **SignalR event received** (e.g., `GatewayUserPosition`)
2. **EventRouter.route_event()** called
3. **Update state FIRST:**
   ```python
   state_manager.update_position(event_data)  # Update before checking rules
   ```
4. **Check lockout:**
   ```python
   if lockout_manager.is_locked_out(account_id):
       return  # Don't process events if locked
   ```
5. **Evaluate each rule:**
   ```python
   for rule in self.rules:
       action = rule.check(account_id, event_type, event_data)
       if action:
           break
   ```
6. **Execute enforcement:**
   ```python
   if action:
       enforcement_engine.execute(action)
   ```

### StateManager Integration

**Rules read from StateManager, never write:**

```python
class MaxContractsRule:
    def check(self, account_id, event_type, event_data):
        # READ current state
        positions = self.state_manager.get_positions(account_id)

        # Calculate total contracts
        total = sum(p['size'] for p in positions)

        # Check breach
        if total > self.limit:
            return EnforcementAction(...)

        return None
```

**StateManager updates come from EventRouter, not rules:**

```python
class EventRouter:
    def route_event(self, event_type, event_data):
        # Update state BEFORE checking rules
        if event_type == "GatewayUserPosition":
            self.state_manager.update_position(event_data)
        elif event_type == "GatewayUserTrade":
            self.state_manager.update_trade(event_data)

        # NOW check rules
        for rule in self.rules:
            action = rule.check(...)
```

### Enforcement Integration

**Rules create EnforcementAction objects, EnforcementEngine executes them:**

```python
# Rule creates action:
action = EnforcementAction(
    type=EnforcementActionType.CLOSE_ALL_POSITIONS,
    reason="MaxContracts breach: 6 > 5",
    rule_id="RULE-001",
    account_id=123
)

# EnforcementEngine executes:
class EnforcementEngine:
    def execute(self, action: EnforcementAction):
        if action.type == EnforcementActionType.CLOSE_ALL_POSITIONS:
            actions.close_all_positions(action.account_id)
            lockout_manager.set_lockout(...)  # If needed
            logger.log_enforcement(...)
        # etc.
```

---

## SPECS Files Analyzed

**Complete specification coverage from:**

### Rule Specifications (12 files)
1. `/project-specs/SPECS/03-RISK-RULES/rules/01_max_contracts.md` - RULE-001
2. `/project-specs/SPECS/03-RISK-RULES/rules/02_max_contracts_per_instrument.md` - RULE-002
3. `/project-specs/SPECS/03-RISK-RULES/rules/03_daily_realized_loss.md` - RULE-003
4. `/project-specs/SPECS/03-RISK-RULES/rules/04_daily_unrealized_loss.md` - RULE-004
5. `/project-specs/SPECS/03-RISK-RULES/rules/05_max_unrealized_profit.md` - RULE-005
6. `/project-specs/SPECS/03-RISK-RULES/rules/06_trade_frequency_limit.md` - RULE-006
7. `/project-specs/SPECS/03-RISK-RULES/rules/07_cooldown_after_loss.md` - RULE-007
8. `/project-specs/SPECS/03-RISK-RULES/rules/08_no_stop_loss_grace.md` - RULE-008
9. `/project-specs/SPECS/03-RISK-RULES/rules/09_session_block_outside.md` - RULE-009
10. `/project-specs/SPECS/03-RISK-RULES/rules/10_auth_loss_guard.md` - RULE-010
11. `/project-specs/SPECS/03-RISK-RULES/rules/11_symbol_blocks.md` - RULE-011
12. `/project-specs/SPECS/03-RISK-RULES/rules/12_trade_management.md` - RULE-012

### Implementation Guide
- `/project-specs/SPECS/03-RISK-RULES/HOW_TO_ADD_NEW_RULES.md` - Rule development guide

### Core Module Specifications
- `/project-specs/SPECS/04-CORE-MODULES/modules/enforcement_actions.md` - MOD-001

**Total:** 14 specification files analyzed for complete rule system architecture.

---

## Summary

**12 Risk Rules** protect trading accounts from:
- Over-leveraging (RULE-001, 002)
- Daily losses - realized (RULE-003) and unrealized (RULE-004)
- Giving back profits (RULE-005)
- Overtrading (RULE-006, 007)
- Trading without protection (RULE-008)
- Trading outside hours (RULE-009)
- Platform restrictions (RULE-010)
- Blacklisted symbols (RULE-011)
- Unmanaged trades (RULE-012)

**Architecture highlights:**
- Event-driven evaluation
- Centralized enforcement (MOD-001)
- Independent rules (no cross-dependencies)
- Modular design (2-3 hours to add new rule)
- Shared state access (StateManager)
- First breach wins (no multiple enforcement per event)

**Enforcement types:**
- Trade-by-Trade (no lockout): RULE-001, 002, 008, 012
- Timer Lockout: RULE-006, 007
- Hard Lockout (until reset): RULE-003, 004, 005, 009
- API-Driven Lockout (indefinite): RULE-010
- Symbol-Specific Lockout (permanent): RULE-011
