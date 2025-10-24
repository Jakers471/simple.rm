# Implementation Roadmap

**Document ID:** ARCH-010
**Version:** 1.0
**Date:** 2025-10-23
**Agent:** Implementation Roadmap Writer
**Swarm:** Integration Architecture Swarm

---

## Executive Summary

This roadmap provides a **step-by-step implementation plan** to complete the Simple Risk Manager. The system is currently 33% complete (4 of 12 risk rules implemented). This document breaks down the remaining work into actionable phases that coders can execute.

**Current Status:**
- Foundation (9 Core Modules): 100% COMPLETE
- Risk Rules: 33% COMPLETE (4 of 12)
- API Integration: 50% COMPLETE (REST done, SignalR pending)
- Event Pipeline: 0% (not started)
- Daemon: 0% (not started)

**Target:** Complete production-ready risk manager daemon with all 12 rules, real-time event processing, and enforcement capabilities.

---

## Current Status Summary

### Phase 1: Foundation - COMPLETE

**Core Modules (9/9 - 100%):**
- MOD-001: Enforcement Actions
- MOD-002: Lockout Manager
- MOD-003: Timer Manager
- MOD-004: Reset Scheduler
- MOD-005: PNL Tracker
- MOD-006: Quote Tracker
- MOD-007: Contract Cache
- MOD-008: Trade Counter
- MOD-009: State Manager

**Risk Rules Implemented (4/12 - 33%):**
- RULE-001: MaxContracts (6/6 tests, 84% coverage)
- RULE-002: MaxContractsPerInstrument (6/6 tests, 83% coverage)
- RULE-006: TradeFrequencyLimit (8/8 tests, 94% coverage)
- RULE-011: SymbolBlocks (4/6 tests, 88% coverage)

**API Integration (50%):**
- REST Client: COMPLETE
- Converters (API to Internal): COMPLETE
- Enums: COMPLETE
- SignalR Client: NOT STARTED
- Event Router: NOT STARTED

---

## Phase 2: Complete Remaining Risk Rules

**Goal:** Implement 8 missing risk rules using TDD

**Estimated Time:** 16-20 hours (2-3 days with parallel agents)

**Missing Rules:**
1. RULE-003: DailyRealizedLoss
2. RULE-004: DailyUnrealizedLoss
3. RULE-005: MaxUnrealizedProfit
4. RULE-007: CooldownAfterLoss
5. RULE-008: NoStopLossGrace
6. RULE-009: SessionBlockOutside
7. RULE-010: AuthLossGuard
8. RULE-012: TradeManagement

### Step 1: Implement RULE-003 - DailyRealizedLoss (2-3 hours)

**Goal:** Enforce hard daily realized P&L limit

**Test File:** `tests/unit/rules/test_daily_realized_loss.py` (exists)

**Implementation File:** `src/rules/daily_realized_loss.py`

**TDD Process:**
```bash
# 1. Read spec
cat project-specs/SPECS/03-RISK-RULES/rules/03_daily_realized_loss.md

# 2. Run tests (see red)
pytest tests/unit/rules/test_daily_realized_loss.py -v

# 3. Implement rule class
# See template: project-specs/SPECS/03-RISK-RULES/HOW_TO_ADD_NEW_RULES.md

# 4. Verify tests pass
pytest tests/unit/rules/test_daily_realized_loss.py -v --cov=src/rules/daily_realized_loss
```

**Key Features:**
- Trigger: `GatewayUserTrade` events
- Condition: `daily_realized_pnl <= -500` (configurable)
- Action: Close all positions + lockout until daily reset (17:00)
- Dependencies: MOD-001, MOD-002, MOD-004, MOD-005

**Acceptance Criteria:**
- All tests passing (6-8 scenarios)
- Coverage >= 80%
- Proper use of PNL Tracker (MOD-005)
- Lockout set until reset time
- Enforcement logged

---

### Step 2: Implement RULE-004 - DailyUnrealizedLoss (2-3 hours)

**Goal:** Enforce unrealized floating loss limit

**Test File:** `tests/unit/rules/test_daily_unrealized_loss.py`

**Implementation File:** `src/rules/daily_unrealized_loss.py`

**Key Features:**
- Trigger: `GatewayUserPosition`, `GatewayQuote`
- Condition: `total_unrealized_pnl <= -300` (configurable)
- Action: Close position OR close all + lockout (mode-dependent)
- Dependencies: MOD-001, MOD-002, MOD-005, MOD-006, MOD-007

**Complexity:** Requires real-time P&L calculation from quotes

**Acceptance Criteria:**
- Supports both per_position and total modes
- Calculates unrealized P&L using quote tracker
- Uses contract cache for tick values

---

### Step 3: Implement RULE-005 - MaxUnrealizedProfit (2-3 hours)

**Goal:** Lock in profits at target

**Test File:** `tests/unit/rules/test_max_unrealized_profit.py`

**Implementation File:** `src/rules/max_unrealized_profit.py`

**Key Features:**
- Trigger: `GatewayUserPosition`, `GatewayQuote`
- Condition: `total_unrealized_pnl >= 1000` (profit target)
- Action: Close all + lockout until reset
- Dependencies: MOD-001, MOD-002, MOD-005, MOD-006, MOD-007

**Similar to RULE-004** but opposite direction (profit vs loss)

---

### Step 4: Implement RULE-007 - CooldownAfterLoss (2 hours)

**Goal:** Force break after losing trades

**Test File:** `tests/unit/rules/test_cooldown_after_loss.py`

**Implementation File:** `src/rules/cooldown_after_loss.py`

**Key Features:**
- Trigger: `GatewayUserTrade` (negative P&L only)
- Condition: Match loss to threshold tier
- Action: Set cooldown timer (no position close)
- Dependencies: MOD-002, MOD-003

**Tiered Cooldowns:**
```yaml
-100: 300s (5 min)
-200: 900s (15 min)
-300: 1800s (30 min)
```

---

### Step 5: Implement RULE-008 - NoStopLossGrace (2-3 hours)

**Goal:** Require stop-loss within grace period

**Test File:** `tests/unit/rules/test_no_stop_loss_grace.py`

**Implementation File:** `src/rules/no_stop_loss_grace.py`

**Key Features:**
- Trigger: `GatewayUserPosition` (open), `GatewayUserOrder` (stop detection), background timer
- Condition: `position_age > 30s AND no_stop_loss`
- Action: Close position (no lockout)
- Dependencies: MOD-001, MOD-009

**Stop-Loss Detection Logic:**
```python
# For LONG position: Sell order with stop price BELOW entry
# For SHORT position: Buy order with stop price ABOVE entry
# Order types: Stop (4), StopLimit (3), TrailingStop (5)
```

---

### Step 6: Implement RULE-009 - SessionBlockOutside (3-4 hours)

**Goal:** Block trading outside session hours and holidays

**Test File:** `tests/unit/rules/test_session_block_outside_hours.py`

**Implementation File:** `src/rules/session_block_outside_hours.py`

**Key Features:**
- Trigger: `GatewayUserPosition`, background timer, holiday check
- Condition: Outside session hours OR holiday
- Action: Close all + lockout until session start
- Dependencies: MOD-001, MOD-002, MOD-003, MOD-004

**Session Configuration:**
```yaml
global_session:
  start: "09:30"
  end: "16:00"
  timezone: "America/New_York"

per_instrument_sessions:
  ES:
    start: "18:00"  # Sunday 6pm
    end: "17:00"    # Friday 5pm
```

**Complexity:** Handles both global and per-instrument sessions, plus holiday calendar

---

### Step 7: Implement RULE-010 - AuthLossGuard (2 hours)

**Goal:** Enforce TopstepX canTrade status

**Test File:** `tests/unit/rules/test_auth_loss_guard.py`

**Implementation File:** `src/rules/auth_loss_guard.py`

**Key Features:**
- Trigger: `GatewayUserAccount`
- Condition: `account.canTrade == False`
- Action: Close all + indefinite lockout
- Dependencies: MOD-001, MOD-002

**Auto-unlock:** Only when `canTrade` returns to `True`

---

### Step 8: Implement RULE-012 - TradeManagement (3-4 hours)

**Goal:** Automated stop-loss management

**Test File:** `tests/unit/rules/test_trade_management.py`

**Implementation File:** `src/rules/trade_management.py`

**Key Features:**
- Trigger: `GatewayUserPosition`, `GatewayQuote`, `GatewayUserOrder`
- Auto Breakeven: Move stop to breakeven after X ticks profit
- Trailing Stop: Trail stop-loss as price moves favorably
- Action: Modify order (no close, no lockout)
- Dependencies: MOD-006, MOD-007

**Most Complex Rule:**
```python
# Auto Breakeven:
if profit_ticks >= 10:
    modify_stop_loss_to_breakeven()

# Trailing Stop:
if profit_ticks >= 20:
    update_trailing_stop(trail_distance=10)
```

---

## Phase 3: Event Processing Pipeline

**Goal:** Build real-time event pipeline from TopstepX SignalR to risk rules

**Estimated Time:** 12-16 hours (1.5-2 days)

### Step 9: Implement SignalR Client (6-8 hours)

**Goal:** Connect to TopstepX SignalR hubs and receive events

**Files to Create:**
- `src/api/signalr_client.py` (~200 lines)
- `src/api/signalr_user_hub.py` (~150 lines)
- `src/api/signalr_market_hub.py` (~150 lines)
- `tests/unit/api/test_signalr_client.py`

**External Dependencies:**
```bash
pip install signalrcore
```

**Implementation:**

```python
# src/api/signalr_client.py
from signalrcore.hub_connection_builder import HubConnectionBuilder

class SignalRClient:
    def __init__(self, hub_url: str, jwt_token: str, event_handler):
        self.hub_url = hub_url
        self.jwt_token = jwt_token
        self.event_handler = event_handler
        self.connection = None

    def connect(self):
        """Connect to SignalR hub with authentication"""
        self.connection = HubConnectionBuilder() \
            .with_url(
                f"{self.hub_url}?access_token={self.jwt_token}",
                options={
                    "skip_negotiation": True,
                    "transport": "WebSockets"
                }
            ) \
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 10,
                "reconnect_interval": 5,
                "max_attempts": 10
            }) \
            .build()

        # Register event handlers
        self.connection.on("GatewayUserPosition", self._on_position)
        self.connection.on("GatewayUserOrder", self._on_order)
        self.connection.on("GatewayUserTrade", self._on_trade)
        self.connection.on("GatewayUserAccount", self._on_account)

        # Start connection
        self.connection.start()

    def _on_position(self, data):
        """Handle position event"""
        self.event_handler.handle_position_event(data)

    def _on_trade(self, data):
        """Handle trade event"""
        self.event_handler.handle_trade_event(data)

    # Similar handlers for other events...
```

**Event Subscription:**
```python
# After connection established
connection.invoke("SubscribeAccounts")
connection.invoke("SubscribeOrders", account_id)
connection.invoke("SubscribePositions", account_id)
connection.invoke("SubscribeTrades", account_id)
```

**Reconnection Strategy:**
```python
connection.on_reconnecting(lambda: logger.warning("SignalR reconnecting..."))
connection.on_reconnected(lambda: self._reconcile_state())
connection.on_close(lambda: self._handle_disconnect())

def _reconcile_state(self):
    """Reconcile state after reconnection"""
    # Fetch current state via REST
    positions = rest_client.search_open_positions(account_id)
    orders = rest_client.search_open_orders(account_id)

    # Update StateManager
    state_manager.reconcile(positions, orders)
```

**Tests to Write:**
- test_connect_success()
- test_connect_with_auth()
- test_reconnect_on_failure()
- test_event_subscription()
- test_event_handler_routing()
- test_state_reconciliation()

**Acceptance Criteria:**
- Connects to TopstepX SignalR hubs
- Authenticates with JWT token
- Subscribes to all required events
- Routes events to event handler
- Handles reconnection automatically
- Reconciles state after reconnection
- All tests passing

---

### Step 10: Implement Event Router (6-8 hours)

**Goal:** Route SignalR events to state modules and risk rules

**Files to Create:**
- `src/core/event_router.py` (~250 lines)
- `tests/unit/core/test_event_router.py`

**Implementation:**

```python
# src/core/event_router.py
from src.api.converters import (
    api_to_internal_position,
    api_to_internal_order,
    api_to_internal_trade
)

class EventRouter:
    def __init__(
        self,
        state_manager,
        pnl_tracker,
        quote_tracker,
        trade_counter,
        lockout_manager,
        enforcement_engine,
        rules: List[RiskRule]
    ):
        self.state_manager = state_manager
        self.pnl_tracker = pnl_tracker
        self.quote_tracker = quote_tracker
        self.trade_counter = trade_counter
        self.lockout_manager = lockout_manager
        self.enforcement_engine = enforcement_engine
        self.rules = rules

    def handle_position_event(self, raw_event: dict):
        """Process GatewayUserPosition event"""
        # 1. Convert from API format to internal
        position = api_to_internal_position(raw_event)

        # 2. Update StateManager FIRST (before rules)
        self.state_manager.update_position(position)

        # 3. Check lockout (skip rules if locked)
        account_id = position['account_id']
        if self.lockout_manager.is_locked_out(account_id):
            logger.debug(f"Account {account_id} locked - skipping rules")
            return

        # 4. Evaluate rules
        self._evaluate_rules(account_id, "GatewayUserPosition", position)

    def handle_trade_event(self, raw_event: dict):
        """Process GatewayUserTrade event"""
        # 1. Convert
        trade = api_to_internal_trade(raw_event)

        # 2. Update state modules
        self.pnl_tracker.add_trade_pnl(
            trade['account_id'],
            trade['profit_and_loss']
        )
        self.trade_counter.record_trade(
            trade['account_id'],
            trade['execution_time']
        )

        # 3. Check lockout
        account_id = trade['account_id']
        if self.lockout_manager.is_locked_out(account_id):
            return

        # 4. Evaluate rules
        self._evaluate_rules(account_id, "GatewayUserTrade", trade)

    def handle_order_event(self, raw_event: dict):
        """Process GatewayUserOrder event"""
        order = api_to_internal_order(raw_event)
        self.state_manager.update_order(order)

        account_id = order['account_id']
        if not self.lockout_manager.is_locked_out(account_id):
            self._evaluate_rules(account_id, "GatewayUserOrder", order)

    def handle_quote_event(self, raw_event: dict):
        """Process GatewayQuote event"""
        # Update quote tracker (no conversion needed)
        self.quote_tracker.update_quote(
            raw_event['contractId'],
            raw_event
        )

        # Rules that depend on quotes will pull from tracker

    def _evaluate_rules(self, account_id: int, event_type: str, event_data: dict):
        """Evaluate all rules for this event"""
        for rule in self.rules:
            action = rule.check(account_id, event_type, event_data)
            if action:
                # First breach wins - execute and stop
                self.enforcement_engine.execute(action)
                logger.info(
                    f"Rule {action.rule_id} triggered for account {account_id}: "
                    f"{action.reason}"
                )
                break
```

**Event Flow:**
```
SignalR Event
    ↓
EventRouter.handle_*_event()
    ↓
1. Convert: api_to_internal_*()
2. Update State: state_manager.update_*()
3. Check Lockout: lockout_manager.is_locked_out()
4. Evaluate Rules: rule.check() for each rule
5. Enforce: enforcement_engine.execute()
```

**Tests to Write:**
- test_handle_position_event()
- test_handle_order_event()
- test_handle_trade_event()
- test_handle_quote_event()
- test_converter_integration()
- test_state_update_before_rules()
- test_lockout_skips_rules()
- test_first_breach_wins()
- test_enforcement_integration()

**Acceptance Criteria:**
- Receives raw API events
- Converts via converters
- Updates StateManager before rules
- Checks lockout before evaluating rules
- Evaluates all rules in order
- Triggers enforcement on first breach
- All tests passing (90%+ coverage)

---

## Phase 4: Daemon Main Process

**Goal:** Create daemon that initializes all components and runs event loop

**Estimated Time:** 8-12 hours (1-1.5 days)

### Step 11: Configuration Loader (3-4 hours)

**Goal:** Load and validate YAML configuration

**Files to Create:**
- `src/daemon/config_loader.py` (~150 lines)
- `config/risk_rules.yaml` (template)
- `config/daemon.yaml` (template)
- `tests/unit/daemon/test_config_loader.py`

**Implementation:**

```python
# src/daemon/config_loader.py
import yaml
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class DaemonConfig:
    """Daemon configuration"""
    api_url: str
    signalr_user_hub_url: str
    signalr_market_hub_url: str
    api_key: str
    account_id: int
    username: str

    # Risk rules config
    rules: Dict[str, Any]

    # Daily reset
    reset_time: str = "17:00"
    timezone: str = "America/New_York"

class ConfigLoader:
    def load(self, config_path: str) -> DaemonConfig:
        """Load configuration from YAML file"""
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        # Validate required fields
        self._validate_config(data)

        # Expand environment variables
        data = self._expand_env_vars(data)

        # Create config object
        return DaemonConfig(
            api_url=data['api']['url'],
            signalr_user_hub_url=data['api']['signalr_user_hub'],
            signalr_market_hub_url=data['api']['signalr_market_hub'],
            api_key=data['api']['api_key'],
            account_id=data['account']['id'],
            username=data['account']['username'],
            rules=data['risk_rules'],
            reset_time=data.get('reset_time', '17:00'),
            timezone=data.get('timezone', 'America/New_York')
        )

    def _validate_config(self, data: Dict) -> None:
        """Validate required fields"""
        required = ['api', 'account', 'risk_rules']
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate API config
        if 'url' not in data['api']:
            raise ValueError("Missing api.url")
        if 'api_key' not in data['api']:
            raise ValueError("Missing api.api_key")

    def _expand_env_vars(self, data: Dict) -> Dict:
        """Expand ${VAR} environment variables"""
        import os
        import re

        def expand(value):
            if isinstance(value, str):
                # Replace ${VAR} with os.environ['VAR']
                pattern = r'\$\{([^}]+)\}'
                matches = re.findall(pattern, value)
                for var in matches:
                    if var in os.environ:
                        value = value.replace(f'${{{var}}}', os.environ[var])
                return value
            elif isinstance(value, dict):
                return {k: expand(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [expand(item) for item in value]
            return value

        return expand(data)
```

**Config Template:**

```yaml
# config/daemon.yaml
api:
  url: "https://api.topstepx.com"
  signalr_user_hub: "https://rtc.topstepx.com/hubs/user"
  signalr_market_hub: "https://rtc.topstepx.com/hubs/market"
  api_key: "${TOPSTEPX_API_KEY}"  # From environment

account:
  id: 123
  username: "trader@example.com"

reset_time: "17:00"
timezone: "America/New_York"

# Risk rules configuration
risk_rules:
  max_contracts:
    enabled: true
    limit: 5
    count_type: "net"
    close_all: true
    reduce_to_limit: false

  max_contracts_per_instrument:
    enabled: true
    limits:
      MNQ: 2
      ES: 1
      NQ: 1
    enforcement: "reduce_to_limit"

  daily_realized_loss:
    enabled: true
    limit: -500
    enforcement: "close_all_and_lockout"

  # ... all 12 rules configured
```

**Tests to Write:**
- test_load_valid_config()
- test_load_missing_file()
- test_load_invalid_yaml()
- test_config_validation()
- test_environment_variable_expansion()
- test_missing_required_fields()

**Acceptance Criteria:**
- Loads YAML from file
- Validates all required fields
- Expands environment variables
- Returns typed DaemonConfig object
- All tests passing

---

### Step 12: Daemon Main Class (5-8 hours)

**Goal:** Main daemon class that orchestrates all components

**Files to Create:**
- `src/daemon/daemon.py` (~300 lines)
- `src/daemon/main.py` (~50 lines)
- `tests/integration/test_daemon.py`

**Implementation:**

```python
# src/daemon/daemon.py
import logging
from typing import List

from src.daemon.config_loader import ConfigLoader
from src.api.rest_client import RestClient
from src.api.signalr_client import SignalRClient
from src.core.event_router import EventRouter
from src.enforcement.enforcement_engine import EnforcementEngine

# All 9 core modules
from src.state.state_manager import StateManager
from src.state.pnl_tracker import PNLTracker
from src.api.quote_tracker import QuoteTracker
from src.api.contract_cache import ContractCache
from src.state.trade_counter import TradeCounter
from src.state.lockout_manager import LockoutManager
from src.state.timer_manager import TimerManager
from src.state.reset_scheduler import ResetScheduler

# All 12 risk rules
from src.rules.max_contracts import MaxContractsRule
from src.rules.max_contracts_per_instrument import MaxContractsPerInstrumentRule
from src.rules.daily_realized_loss import DailyRealizedLossRule
# ... import all 12

logger = logging.getLogger(__name__)

class RiskManagerDaemon:
    """Main daemon class - orchestrates all components"""

    def __init__(self):
        self.config = None
        self.running = False

        # API clients
        self.rest_client = None
        self.signalr_client = None

        # Core modules
        self.state_manager = None
        self.pnl_tracker = None
        self.quote_tracker = None
        self.contract_cache = None
        self.trade_counter = None
        self.lockout_manager = None
        self.timer_manager = None
        self.reset_scheduler = None

        # Event processing
        self.event_router = None
        self.enforcement_engine = None

        # Risk rules
        self.rules: List[RiskRule] = []

    def start(self, config_path: str):
        """Initialize and start daemon"""
        logger.info("=== Starting Risk Manager Daemon ===")

        # Phase 1: Load configuration
        logger.info("Phase 1: Loading configuration...")
        self.config = ConfigLoader().load(config_path)
        logger.info(f"Loaded config for account {self.config.account_id}")

        # Phase 2: Initialize core modules
        logger.info("Phase 2: Initializing core modules...")
        self._initialize_modules()

        # Phase 3: Authenticate with TopstepX
        logger.info("Phase 3: Authenticating with TopstepX...")
        self.rest_client = RestClient(
            self.config.api_url,
            self.config.username,
            self.config.api_key
        )
        self.rest_client.authenticate()
        logger.info("Authentication successful")

        # Phase 4: Initialize risk rules
        logger.info("Phase 4: Initializing risk rules...")
        self._initialize_rules()
        logger.info(f"Initialized {len(self.rules)} risk rules")

        # Phase 5: Initialize enforcement
        logger.info("Phase 5: Initializing enforcement...")
        self.enforcement_engine = EnforcementEngine(
            self.rest_client,
            self.lockout_manager
        )

        # Phase 6: Initialize event router
        logger.info("Phase 6: Initializing event router...")
        self.event_router = EventRouter(
            state_manager=self.state_manager,
            pnl_tracker=self.pnl_tracker,
            quote_tracker=self.quote_tracker,
            trade_counter=self.trade_counter,
            lockout_manager=self.lockout_manager,
            enforcement_engine=self.enforcement_engine,
            rules=self.rules
        )

        # Phase 7: Fetch initial state from API
        logger.info("Phase 7: Fetching initial state...")
        self._fetch_initial_state()

        # Phase 8: Connect SignalR
        logger.info("Phase 8: Connecting to SignalR hubs...")
        self.signalr_client = SignalRClient(
            self.config.signalr_user_hub_url,
            self.rest_client.token,
            self.event_router
        )
        self.signalr_client.connect()
        logger.info("SignalR connected")

        # Mark as running
        self.running = True
        logger.info("=== Daemon Started Successfully ===")

    def _initialize_modules(self):
        """Initialize all 9 core modules"""
        self.state_manager = StateManager()
        self.pnl_tracker = PNLTracker()
        self.quote_tracker = QuoteTracker()
        self.contract_cache = ContractCache(self.rest_client)
        self.trade_counter = TradeCounter()
        self.lockout_manager = LockoutManager()
        self.timer_manager = TimerManager()
        self.reset_scheduler = ResetScheduler(
            reset_time=self.config.reset_time,
            timezone=self.config.timezone
        )

    def _initialize_rules(self):
        """Initialize all 12 risk rules with configurations"""
        rule_configs = self.config.rules

        # RULE-001
        if rule_configs.get('max_contracts', {}).get('enabled', False):
            self.rules.append(MaxContractsRule(
                config=rule_configs['max_contracts'],
                state_manager=self.state_manager,
                enforcement_engine=self.enforcement_engine
            ))

        # RULE-002
        if rule_configs.get('max_contracts_per_instrument', {}).get('enabled', False):
            self.rules.append(MaxContractsPerInstrumentRule(
                config=rule_configs['max_contracts_per_instrument'],
                state_manager=self.state_manager,
                enforcement_engine=self.enforcement_engine
            ))

        # ... Initialize all 12 rules similarly

        logger.info(f"Enabled rules: {[type(r).__name__ for r in self.rules]}")

    def _fetch_initial_state(self):
        """Fetch current positions and orders from API"""
        # Fetch positions
        positions = self.rest_client.search_open_positions(self.config.account_id)
        for position in positions:
            self.state_manager.update_position(position)
        logger.info(f"Loaded {len(positions)} open positions")

        # Fetch orders
        orders = self.rest_client.search_open_orders(self.config.account_id)
        for order in orders:
            self.state_manager.update_order(order)
        logger.info(f"Loaded {len(orders)} working orders")

    def run(self):
        """Main event loop - blocks on SignalR connection"""
        logger.info("Entering main event loop...")
        try:
            # Block here - SignalR handles events
            while self.running:
                import time
                time.sleep(1)  # Keep daemon alive
        except KeyboardInterrupt:
            logger.info("Received shutdown signal (Ctrl+C)")
            self.shutdown()
        except Exception as e:
            logger.critical(f"Daemon crashed: {e}", exc_info=True)
            self.emergency_shutdown()

    def shutdown(self):
        """Graceful shutdown"""
        logger.info("=== Shutting Down Daemon ===")
        self.running = False

        # Disconnect SignalR
        if self.signalr_client:
            self.signalr_client.disconnect()

        logger.info("Daemon stopped")

    def emergency_shutdown(self):
        """Emergency shutdown - minimal cleanup"""
        logger.critical("EMERGENCY SHUTDOWN")
        self.running = False
        sys.exit(1)
```

```python
# src/daemon/main.py
import sys
import logging
from pathlib import Path
from src.daemon.daemon import RiskManagerDaemon

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python -m src.daemon.main <config_path>")
        print("Example: python -m src.daemon.main config/daemon.yaml")
        sys.exit(1)

    config_path = sys.argv[1]

    daemon = RiskManagerDaemon()
    daemon.start(config_path)
    daemon.run()

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Start daemon
python -m src.daemon.main config/daemon.yaml

# With environment variables
export TOPSTEPX_API_KEY="your_api_key_here"
python -m src.daemon.main config/daemon.yaml
```

**Tests to Write:**
- test_daemon_initialization()
- test_startup_sequence()
- test_module_initialization_order()
- test_rule_initialization()
- test_initial_state_fetch()
- test_shutdown_sequence()

**Acceptance Criteria:**
- Initializes all components in correct order
- Loads configuration successfully
- Authenticates with TopstepX
- Fetches initial state
- Connects to SignalR
- Runs main event loop
- Shuts down cleanly
- Integration test passes

---

## Phase 5: Production Readiness

**Goal:** Production features and polish

**Estimated Time:** 8-12 hours (1-1.5 days)

### Step 13: Enhanced Logging (3-4 hours)

**Files to Create:**
- `src/utils/logging_config.py`
- `logs/` directory structure
- Log rotation configuration

**Features:**
- Structured logging (JSON)
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)
- Separate log files: daemon.log, enforcement.log, api.log
- Log rotation (daily, max 7 days)

### Step 14: Monitoring & Metrics (3-4 hours)

**Files to Create:**
- `src/monitoring/metrics.py`
- `src/monitoring/health_check.py`

**Features:**
- Track rule breach counts
- Track enforcement actions
- Track API call rates
- Track event processing latency
- Health check endpoint (for admin CLI)

### Step 15: Error Handling & Recovery (2-4 hours)

**Enhancements:**
- Circuit breaker pattern for API calls
- Graceful degradation on SignalR disconnect
- Automatic state reconciliation
- Comprehensive error logging

---

## Implementation Timeline

**With Parallel Execution (Optimal):**

| Phase | Task | Hours | Days | Can Parallelize |
|-------|------|-------|------|-----------------|
| Phase 2 | Implement 8 rules | 16-20h | 2-3 days | YES (2 rules/agent, 4 agents) |
| Phase 3 | SignalR Client | 6-8h | 1 day | YES (can parallel with EventRouter) |
| Phase 3 | Event Router | 6-8h | 1 day | YES (can parallel with SignalR) |
| Phase 4 | Config Loader | 3-4h | 0.5 day | YES (can parallel with Daemon) |
| Phase 4 | Daemon Main | 5-8h | 1 day | YES (can parallel with Config) |
| Phase 5 | Production Features | 8-12h | 1-1.5 days | YES (3 tasks in parallel) |
| **Total** | | **44-60h** | **5.5-7.5 days** | **~3-4 days with parallelization** |

**Sequential Execution:**
- Total: 5.5-7.5 days

**Parallel Execution (4 agents):**
- Phase 2: 2-3 days (8 rules / 4 agents = 2 rules each)
- Phase 3: 1 day (2 tasks in parallel)
- Phase 4: 0.5-1 day (2 tasks in parallel)
- Phase 5: 0.5-1 day (3 tasks in parallel)
- **Total: 4-6 days**

---

## Success Criteria

### After Phase 2 (All Rules Complete):
- All 12 risk rules implemented
- All tests passing (150+ tests total)
- Coverage >= 80% per rule
- All rules use existing modules (no duplication)
- Documentation complete

### After Phase 3 (Event Pipeline Complete):
- SignalR client connects successfully
- Events received in real-time
- Event router processes events
- State updated correctly
- Rules evaluated on events
- Enforcement triggered

### After Phase 4 (Daemon Complete):
- Daemon starts successfully
- Loads configuration
- Connects to TopstepX API
- Subscribes to SignalR events
- Processes events in < 10ms
- System is FULLY FUNCTIONAL

### After Phase 5 (Production Ready):
- Comprehensive logging
- Monitoring and metrics
- Error recovery
- Production deployment ready

---

## Priority Levels

**P0 (Critical Path - Must Have):**
- Phase 2: All 8 missing rules
- Phase 3: SignalR Client + Event Router
- Phase 4: Daemon Main Process

**P1 (Core Functionality - Should Have):**
- Configuration Loader
- Initial state fetch
- Graceful shutdown

**P2 (Polish - Nice to Have):**
- Enhanced logging
- Monitoring & metrics
- Advanced error recovery

---

## Risk Mitigation

**Technical Risks:**

1. **SignalR Connection Issues**
   - Mitigation: Implement retry logic, fallback to REST polling
   - Testing: Mock SignalR server for tests

2. **State Synchronization**
   - Mitigation: Periodic reconciliation via REST
   - Testing: Inject events out-of-order

3. **Performance Bottlenecks**
   - Mitigation: Profile event processing, optimize hot paths
   - Target: < 10ms per event

4. **API Rate Limiting**
   - Mitigation: Client-side rate limiter (already implemented)
   - Monitoring: Track API call rates

**Dependency Risks:**

1. **External Library (signalrcore)**
   - Mitigation: Pin version, test thoroughly
   - Fallback: Could implement custom WebSocket client

2. **TopstepX API Changes**
   - Mitigation: Version API endpoints, monitor for deprecations
   - Testing: Mock API responses in tests

---

## Testing Strategy

**Unit Tests:**
- Each rule: 6-8 test scenarios
- Event router: 10+ test scenarios
- SignalR client: 8+ test scenarios
- Config loader: 6+ test scenarios
- Target coverage: 80%+

**Integration Tests:**
- Daemon startup sequence
- End-to-end event flow (mocked SignalR)
- Rule enforcement integration
- State reconciliation

**Manual Testing:**
- Connect to TopstepX demo account
- Verify real-time events received
- Trigger rule breaches manually
- Verify enforcement actions executed

---

## Next Steps

**Immediate Action:**
1. Review this roadmap
2. Approve architecture decisions
3. Decide: Sequential or parallel implementation?
4. Assign tasks to coders

**Recommended Approach:**
1. Start with Phase 2 (missing rules) - can be parallelized
2. Move to Phase 3 (event pipeline) - foundational
3. Complete Phase 4 (daemon) - integration
4. Polish with Phase 5 (production features)

**First Task:**
- Implement RULE-003 (DailyRealizedLoss) using TDD
- Estimated time: 2-3 hours
- Success metric: All tests passing, 80%+ coverage

---

## Conclusion

This roadmap provides **everything coders need** to implement the complete Simple Risk Manager:

- Detailed step-by-step instructions
- Code templates and examples
- Test scenarios for each component
- Clear acceptance criteria
- Realistic time estimates
- Parallelization opportunities

**The system is 33% complete.** With focused execution following this roadmap, the remaining 67% can be implemented in **4-6 days** with parallel agents, or **5.5-7.5 days** sequentially.

**All foundational work is done.** The core modules (MOD-001 through MOD-009) are complete and tested. The API integration is 50% complete (REST done). We just need to build the missing 8 rules, connect the event pipeline, and wrap it in a daemon.

**This is the final stretch to a production-ready trading risk manager.**

---

**End of Implementation Roadmap**
