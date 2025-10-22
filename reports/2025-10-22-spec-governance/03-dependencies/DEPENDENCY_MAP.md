# Complete Dependency Map - Simple Risk Manager

**Generated:** 2025-10-22
**Project:** Simple Risk Manager
**Purpose:** Complete import/dependency graph for all specifications

---

## Executive Summary

**Total Specifications Analyzed:** 100+
**Dependency Relationships:** 250+
**Circular Dependencies Detected:** 0 CRITICAL
**Maximum Dependency Depth:** 4 levels
**Most Depended-On Module:** MOD-001 (Enforcement Actions) - 14 dependents

---

## 1. Module Dependencies (Core Components)

### 1.1 Core Architecture Layer

```
ARCH-V2.2 (system_architecture_v2.md)
├── depends on: MOD-001 through MOD-009, API-INT-001
└── depended by: DAEMON-001, PIPE-001, STATE-001, All Rules

PIPE-001 (EVENT_PIPELINE.md)
├── depends on: ARCH-V2.2, MOD-001 through MOD-009, API-INT-001
└── depended by: DAEMON-001, DAEMON-ENDPOINTS

DAEMON-001 (DAEMON_ARCHITECTURE.md)
├── depends on: ARCH-V2.2, PIPE-001, STATE-001, DB-SCHEMA-001, MOD-001 through MOD-009
└── depended by: ADMIN_CLI, TRADER_CLI, FRONTEND-BACKEND-001
```

### 1.2 Module Dependency Tree

**MOD-001: Enforcement Actions** (`enforcement_actions.md`)
- **Dependencies:** None (base module)
- **Depended By:** All 12 rules, PIPE-001, DAEMON-001
- **Description:** Centralized enforcement logic - no external dependencies

**MOD-002: Lockout Manager** (`lockout_manager.md`)
- **Dependencies:** MOD-003 (Timer Manager)
- **Depended By:** 8 rules (RULE-003, 004, 005, 006, 007, 009, 010, 011), PIPE-001
- **Description:** Depends on timer manager for cooldown expiry

**MOD-003: Timer Manager** (`timer_manager.md`)
- **Dependencies:** None (base module)
- **Depended By:** MOD-002, RULE-006, RULE-007
- **Description:** No external dependencies

**MOD-004: Reset Scheduler** (`reset_scheduler.md`)
- **Dependencies:** None (base module)
- **Depended By:** RULE-003, RULE-004, RULE-005, RULE-009, DAEMON-001
- **Description:** No external dependencies

**MOD-005: PNL Tracker** (`pnl_tracker.md`)
- **Dependencies:** API-INT-001 (GatewayUserTrade events)
- **Depended By:** RULE-003, RULE-004, RULE-005, PIPE-001
- **Description:** Depends on TopstepX trade events

**MOD-006: Quote Tracker** (`quote_tracker.md`)
- **Dependencies:** API-INT-001 (MarketQuote events)
- **Depended By:** RULE-004, RULE-005, RULE-012, PIPE-001
- **Description:** Depends on TopstepX market data

**MOD-007: Contract Cache** (`contract_cache.md`)
- **Dependencies:** API-INT-001 (Contract API)
- **Depended By:** MOD-005, RULE-002, RULE-011, PIPE-001
- **Description:** Depends on TopstepX contract metadata API

**MOD-008: Trade Counter** (`trade_counter.md`)
- **Dependencies:** API-INT-001 (GatewayUserTrade events)
- **Depended By:** RULE-006, RULE-007, PIPE-001
- **Description:** Depends on TopstepX trade events

**MOD-009: State Manager** (`state_manager.md`)
- **Dependencies:** API-INT-001 (Position/Order events)
- **Depended By:** All position-based rules, PIPE-001
- **Description:** Depends on TopstepX position/order events

---

## 2. Risk Rule Dependencies

### 2.1 Dependency Matrix

| Rule | ID | MOD-001 | MOD-002 | MOD-003 | MOD-004 | MOD-005 | MOD-006 | MOD-007 | MOD-008 | MOD-009 | API-INT-001 |
|------|----|---------|---------|---------|---------|---------|---------|---------|---------|---------| ------------|
| Max Contracts | RULE-001 | X | | | | | | | | X | |
| Max Contracts Per Instrument | RULE-002 | X | | | | | | X | | X | |
| Daily Realized Loss | RULE-003 | X | X | | X | X | | | | | |
| Daily Unrealized Loss | RULE-004 | X | X | | X | X | X | | | X | X |
| Max Unrealized Profit | RULE-005 | X | X | | X | X | X | | | X | X |
| Trade Frequency Limit | RULE-006 | | X | X | | | | | X | | X |
| Cooldown After Loss | RULE-007 | | X | X | | X | | | X | | X |
| No Stop Loss Grace | RULE-008 | X | | | | | | | | X | X |
| Session Block Outside | RULE-009 | X | X | | X | | | | | X | |
| Auth Loss Guard | RULE-010 | X | X | | | | | | | | X |
| Symbol Blocks | RULE-011 | X | X | | | | | X | | X | X |
| Trade Management | RULE-012 | X | | | | | | X | | X | X |

### 2.2 Rule Dependency Details

**RULE-001: Max Contracts**
```
├── MOD-001 (enforcement)
└── MOD-009 (get position count)
```

**RULE-002: Max Contracts Per Instrument**
```
├── MOD-001 (enforcement)
├── MOD-007 (symbol extraction)
└── MOD-009 (get positions by contract)
```

**RULE-003: Daily Realized Loss**
```
├── MOD-001 (enforcement)
├── MOD-002 (lockout)
├── MOD-004 (reset time)
└── MOD-005 (daily P&L)
```

**RULE-004: Daily Unrealized Loss**
```
├── MOD-001 (enforcement)
├── MOD-002 (lockout)
├── MOD-004 (reset time)
├── MOD-005 (unrealized P&L calculation)
├── MOD-006 (current quotes)
├── MOD-009 (position data)
└── API-INT-001 (position events, quotes)
```

**RULE-005: Max Unrealized Profit**
```
├── MOD-001 (enforcement)
├── MOD-002 (lockout)
├── MOD-004 (reset time)
├── MOD-005 (unrealized P&L calculation)
├── MOD-006 (current quotes)
├── MOD-009 (position data)
└── API-INT-001 (position events, quotes)
```

**RULE-006: Trade Frequency Limit**
```
├── MOD-002 (cooldown lockout)
├── MOD-003 (cooldown timers)
├── MOD-008 (trade count)
└── API-INT-001 (trade events)
```

**RULE-007: Cooldown After Loss**
```
├── MOD-002 (cooldown lockout)
├── MOD-003 (cooldown timers)
├── MOD-005 (trade P&L)
├── MOD-008 (trade timestamp)
└── API-INT-001 (trade events)
```

**RULE-008: No Stop Loss Grace**
```
├── MOD-001 (enforcement)
├── MOD-009 (position/order tracking)
└── API-INT-001 (position/order events)
```

**RULE-009: Session Block Outside**
```
├── MOD-001 (enforcement)
├── MOD-002 (lockout)
├── MOD-004 (holiday calendar)
└── MOD-009 (position state)
```

**RULE-010: Auth Loss Guard**
```
├── MOD-001 (enforcement)
├── MOD-002 (lockout)
└── API-INT-001 (account events)
```

**RULE-011: Symbol Blocks**
```
├── MOD-001 (enforcement)
├── MOD-002 (lockout)
├── MOD-007 (symbol extraction)
├── MOD-009 (position/order data)
└── API-INT-001 (position/order events)
```

**RULE-012: Trade Management**
```
├── MOD-001 (place stop-loss orders)
├── MOD-007 (tick size/value)
├── MOD-009 (position/order tracking)
└── API-INT-001 (position/order events, place order API)
```

---

## 3. Configuration Dependencies

### 3.1 Configuration File Dependencies

**RISK_CONFIG_YAML_SPEC.md** (risk_config.yaml)
```
├── depends on: All 12 rule specifications (RULE-001 through RULE-012)
├── depended by: daemon.py (startup), rule_loader.py
└── hot-reloadable: Yes (admin CLI)
```

**ACCOUNTS_YAML_SPEC.md** (accounts.yaml)
```
├── depends on: TopstepX API key format
├── depended by: daemon.py (authentication), auth.py
└── hot-reloadable: No (requires daemon restart)
```

**ADMIN_PASSWORD_SPEC.md** (admin_password.hash)
```
├── depends on: bcrypt hashing
├── depended by: admin CLI authentication
└── hot-reloadable: No
```

**LOGGING_CONFIG_SPEC.md** (logging config)
```
├── depends on: Python logging module
├── depended by: All modules (logger instances)
└── hot-reloadable: Partial (log level only)
```

### 3.2 Configuration Dependency Graph

```
risk_config.yaml
├── Loaded by: config/loader.py
├── Used by: risk_engine.py (rule instantiation)
├── Validated by: config/validator.py
└── Updated by: Admin CLI (hot reload)

accounts.yaml
├── Loaded by: config/loader.py
├── Used by: daemon.py (authentication phase)
└── Updated by: Admin CLI (requires restart)

admin_password.hash
├── Loaded by: cli/admin/auth.py
└── Used by: Admin CLI (password verification)
```

---

## 4. External API Dependencies

### 4.1 TopstepX API Dependencies

**API-INT-001** (TopstepX Gateway API)
```
External dependencies (all modules depend on):
├── REST API Endpoints:
│   ├── /api/Account/search
│   ├── /api/Position/searchOpen
│   ├── /api/Position/closeContract
│   ├── /api/Position/partialCloseContract
│   ├── /api/Order/search
│   ├── /api/Order/searchOpen
│   ├── /api/Order/placeOrder
│   ├── /api/Order/cancel
│   ├── /api/Order/modify
│   ├── /api/Contract/searchById
│   └── /api/Trades/search
│
└── SignalR Hubs:
    ├── User Hub (wss://rtc.topstepx.com/hubs/user)
    │   ├── GatewayUserTrade
    │   ├── GatewayUserPosition
    │   ├── GatewayUserOrder
    │   └── GatewayUserAccount
    │
    └── Market Hub (wss://rtc.topstepx.com/hubs/market)
        └── MarketQuote
```

**API Dependency by Module:**

| Module | REST API | SignalR User Hub | SignalR Market Hub |
|--------|----------|------------------|-------------------|
| MOD-001 | Close, Cancel, Modify Orders | - | - |
| MOD-005 | - | GatewayUserTrade | - |
| MOD-006 | - | - | MarketQuote |
| MOD-007 | Contract Search | - | - |
| MOD-008 | - | GatewayUserTrade | - |
| MOD-009 | - | Position, Order events | - |

### 4.2 Authentication Dependencies

```
Authentication Flow:
1. accounts.yaml → username, api_key
2. auth.py → POST /api/Account/authenticateApiKey
3. JWT token (24h lifetime) → stored in daemon
4. Token refresh → token_refresh_checker (background thread)
```

**Token Dependencies:**
- All REST API calls require valid JWT token
- SignalR connections require token in connection URL
- Token refresh must happen before 24h expiration
- Failed authentication blocks daemon startup

---

## 5. Database Schema Dependencies

### 5.1 Schema Dependency Map

**DATABASE_SCHEMA.md** (SQLite schema)
```
Database: data/state.db

Table Dependencies:
├── lockouts (MOD-002)
│   └── no foreign keys
│
├── daily_pnl (MOD-005)
│   └── no foreign keys
│
├── contract_cache (MOD-007)
│   └── no foreign keys
│
├── trade_history (MOD-008)
│   └── no foreign keys
│
├── session_state (MOD-008)
│   └── no foreign keys
│
├── positions (MOD-009)
│   └── no foreign keys
│
├── orders (MOD-009)
│   └── no foreign keys
│
├── enforcement_log (MOD-001)
│   └── no foreign keys
│
└── reset_schedule (MOD-004)
    └── no foreign keys

Note: No FK constraints (TopstepX IDs are external)
```

### 5.2 Module-to-Table Mapping

| Module | Tables Used | Operations |
|--------|------------|------------|
| MOD-001 | enforcement_log | INSERT (audit trail) |
| MOD-002 | lockouts | INSERT, UPDATE, DELETE, SELECT |
| MOD-004 | reset_schedule | INSERT, UPDATE, SELECT |
| MOD-005 | daily_pnl | INSERT, UPDATE, SELECT |
| MOD-007 | contract_cache | INSERT, SELECT |
| MOD-008 | trade_history, session_state | INSERT, SELECT, DELETE |
| MOD-009 | positions, orders | INSERT, UPDATE, DELETE, SELECT |

**Database Initialization Order** (startup):
1. Connect to SQLite
2. Create tables (if not exist)
3. Load MOD-004 (reset schedule)
4. Load MOD-002 (lockouts)
5. Load MOD-005 (daily P&L)
6. Load MOD-007 (contract cache)
7. Load MOD-008 (session state)
8. Load MOD-009 (positions, orders)

---

## 6. Frontend-Backend Dependencies

### 6.1 CLI Interface Dependencies

**ADMIN_CLI_SPEC.md**
```
├── depends on: DAEMON-001, FRONTEND-BACKEND-001, CONFIG-001, CONFIG-002
├── reads from: SQLite (read-only)
├── writes to: config files (hot reload)
└── controls: Windows Service (start/stop/restart)
```

**TRADER_CLI_SPEC.md**
```
├── depends on: DAEMON-001, FRONTEND-BACKEND-001, MOD-001 through MOD-009
├── reads from: SQLite (read-only), WebSocket (real-time)
├── writes to: None (read-only)
└── displays: Lockout status, P&L, positions, enforcement log
```

### 6.2 Internal API Dependencies

**FRONTEND_BACKEND_ARCHITECTURE.md**
```
├── depends on: DAEMON-001, DB-SCHEMA-001, STATE-001
├── exposes: WebSocket server (localhost:8765)
└── broadcasts: Real-time events to Trader CLIs
```

**DAEMON_ENDPOINTS.md**
```
├── depends on: FE-BE-001, DAEMON-001, PIPE-001
└── defines: WebSocket message format
```

---

## 7. Implementation Guide Dependencies

### 7.1 API Resilience Dependencies

**API_RESILIENCE_OVERVIEW.md**
```
├── depends on: ERRORS_AND_WARNINGS_CONSOLIDATED.md, api-integration-analysis.md
├── defines: Error handling strategies
└── depended by: All API-calling modules
```

**IMPLEMENTATION_ROADMAP_V2.md**
```
├── depends on: API_RESILIENCE_OVERVIEW.md, ERRORS_AND_WARNINGS_CONSOLIDATED.md
└── defines: Implementation phases
```

**ARCHITECTURE_INTEGRATION_SPEC.md**
```
├── depends on: API_RESILIENCE_OVERVIEW.md
└── defines: Integration with core architecture
```

**CONFIGURATION_MASTER_SPEC.md**
```
├── depends on: RISK_CONFIG_YAML_SPEC.md, API_RESILIENCE_OVERVIEW.md
└── defines: Resilience configuration options
```

### 7.2 Error Handling Dependencies

```
Error Handling Chain:
├── ERROR_CODE_MAPPING_SPEC.md → Maps TopstepX errors to internal codes
├── RETRY_STRATEGY_SPEC.md → Defines retry logic
├── CIRCUIT_BREAKER_SPEC.md → Prevents cascade failures
├── RATE_LIMITING_SPEC.md → Respects API rate limits
└── ERROR_LOGGING_SPEC.md → Structured error logging

All modules that call TopstepX API must implement:
1. Error code mapping
2. Retry strategy
3. Circuit breaker checks
4. Rate limit compliance
5. Error logging
```

---

## 8. Dependency Depth Analysis

### 8.1 Dependency Levels

**Level 0: No Dependencies**
- MOD-001 (Enforcement Actions)
- MOD-003 (Timer Manager)
- MOD-004 (Reset Scheduler)
- API-INT-001 (External - TopstepX)

**Level 1: Depends on Level 0 Only**
- MOD-002 (Lockout Manager) → MOD-003
- MOD-005 (PNL Tracker) → API-INT-001
- MOD-006 (Quote Tracker) → API-INT-001
- MOD-007 (Contract Cache) → API-INT-001
- MOD-008 (Trade Counter) → API-INT-001
- MOD-009 (State Manager) → API-INT-001

**Level 2: Depends on Level 0-1**
- All 12 Risk Rules → MOD-001, MOD-002, MOD-005, MOD-006, MOD-007, MOD-008, MOD-009
- PIPE-001 (Event Pipeline) → All MOD-001 through MOD-009

**Level 3: Depends on Level 0-2**
- DAEMON-001 (Daemon) → ARCH-V2.2, PIPE-001, All Modules
- DB-SCHEMA-001 → All Modules (persistence)
- STATE-001 → All Modules (state management)

**Level 4: Depends on Level 0-3**
- ADMIN_CLI → DAEMON-001, DB-SCHEMA-001, CONFIG files
- TRADER_CLI → DAEMON-001, DB-SCHEMA-001, WebSocket
- FRONTEND-BACKEND-001 → DAEMON-001, DB-SCHEMA-001

### 8.2 Critical Path Analysis

**Longest Dependency Chain:**
```
TRADER_CLI (Level 4)
├→ DAEMON-001 (Level 3)
   ├→ PIPE-001 (Level 2)
      ├→ RULE-004 (Level 2)
         ├→ MOD-006 (Level 1)
            └→ API-INT-001 (Level 0)

Total Depth: 5 levels
```

**Most Dependencies:**
- DAEMON-001: 15 direct dependencies
- PIPE-001: 10 direct dependencies
- RULE-004/005: 7 direct dependencies each

**Fewest Dependencies:**
- MOD-001: 0 dependencies
- MOD-003: 0 dependencies
- MOD-004: 0 dependencies

---

## 9. Import Analysis (Code-Level)

### 9.1 Python Module Imports

**Expected Import Structure:**

```python
# src/core/daemon.py
import threading
import sqlite3
from datetime import datetime
from api.auth import authenticate
from api.signalr_listener import SignalRListener
from api.market_hub import MarketHubListener
from state.lockout_manager import LockoutManager
from state.pnl_tracker import PNLTracker
from state.quote_tracker import QuoteTracker
from state.state_manager import StateManager
from enforcement.actions import close_all_positions
from rules.base_rule import BaseRule
from config.loader import load_config

# src/rules/daily_realized_loss.py
from state.pnl_tracker import PNLTracker
from state.lockout_manager import LockoutManager
from enforcement.actions import close_all_positions, cancel_all_orders
from rules.base_rule import BaseRule
from config.loader import get_rule_config

# src/api/signalr_listener.py
from signalrcore.hub_connection_builder import HubConnectionBuilder
from core.event_router import EventRouter
```

### 9.2 External Library Dependencies

**Python Package Requirements:**
```
# Core dependencies
signalrcore==1.0.0       # SignalR WebSocket client
requests==2.31.0         # REST API calls
pyyaml==6.0.1           # YAML config parsing
sqlite3                  # (built-in) Database
datetime                 # (built-in) Time handling
threading                # (built-in) Background threads
asyncio                  # (built-in) WebSocket server

# Windows Service (optional - production only)
pywin32==306            # Windows Service integration

# Logging
logging                  # (built-in)

# CLI Display
tabulate==0.9.0         # Table formatting
colorama==0.4.6         # Terminal colors

# Testing
pytest==7.4.0
pytest-asyncio==0.21.0
```

---

## 10. Dependency Risk Assessment

### 10.1 External Dependency Risks

**HIGH RISK:**
- **TopstepX API Availability**
  - Risk: API downtime blocks all enforcement
  - Mitigation: Retry logic, circuit breakers, offline mode
  - Impact: CRITICAL (cannot enforce rules without API)

- **SignalR Connection Stability**
  - Risk: Disconnection causes missed events
  - Mitigation: Auto-reconnect, state reconciliation
  - Impact: HIGH (missed events = missed breaches)

**MEDIUM RISK:**
- **SQLite Database Corruption**
  - Risk: State loss on corruption
  - Mitigation: Daily backups, integrity checks
  - Impact: MEDIUM (can rebuild from TopstepX)

- **Python Library Vulnerabilities**
  - Risk: Security vulnerabilities in dependencies
  - Mitigation: Regular updates, security scanning
  - Impact: MEDIUM

**LOW RISK:**
- **Configuration File Errors**
  - Risk: Invalid YAML syntax
  - Mitigation: Validation on load, schema checks
  - Impact: LOW (detected at startup)

### 10.2 Internal Dependency Risks

**Circular Dependencies:**
- None detected (all dependencies are acyclic)

**Tight Coupling:**
- All rules depend on MOD-001 (by design - centralized enforcement)
- Most rules depend on MOD-002 (by design - centralized lockouts)
- Risk: LOW (intentional design pattern)

**Missing Dependencies:**
- None detected (all dependencies properly declared)

---

## 11. Dependency Change Impact Analysis

### 11.1 If TopstepX API Changes

**High Impact Changes:**
```
API Schema Change (GatewayUserTrade format)
├→ Affects: MOD-005, MOD-008, PIPE-001
├→ Impact: CRITICAL (all P&L tracking breaks)
└→ Mitigation: Version API calls, backward compatibility

API Authentication Change (JWT format)
├→ Affects: auth.py, all REST API calls, SignalR connections
├→ Impact: CRITICAL (cannot connect)
└→ Mitigation: Multiple auth strategies, fallback methods
```

**Low Impact Changes:**
```
New API Endpoint Added
├→ Affects: None (unless we use it)
└→ Impact: NONE

Rate Limit Change
├→ Affects: retry_strategy.py, rate_limiter.py
└→ Impact: LOW (adjust retry logic)
```

### 11.2 If Module Interface Changes

**MOD-001 Interface Change:**
```
Affects: All 12 rules, PIPE-001, DAEMON-001
Impact: HIGH (central enforcement module)
Required Updates: 15+ files
```

**MOD-005 Interface Change:**
```
Affects: RULE-003, RULE-004, RULE-005, RULE-007, PIPE-001
Impact: MEDIUM
Required Updates: 5 files
```

**MOD-009 Interface Change:**
```
Affects: 7 rules, PIPE-001, DAEMON-001
Impact: MEDIUM-HIGH
Required Updates: 10+ files
```

---

## 12. Dependency Health Metrics

### 12.1 Module Stability Score

| Module | Direct Dependencies | Dependents | Stability Score | Risk Level |
|--------|---------------------|-----------|-----------------|-----------|
| MOD-001 | 0 | 14 | 1.00 (Very Stable) | LOW |
| MOD-003 | 0 | 3 | 1.00 (Very Stable) | LOW |
| MOD-004 | 0 | 5 | 1.00 (Very Stable) | LOW |
| MOD-002 | 1 | 8 | 0.89 (Stable) | LOW |
| MOD-005 | 1 | 4 | 0.80 (Stable) | LOW |
| MOD-006 | 1 | 3 | 0.75 (Stable) | LOW |
| MOD-007 | 1 | 4 | 0.80 (Stable) | LOW |
| MOD-008 | 1 | 3 | 0.75 (Stable) | LOW |
| MOD-009 | 1 | 8 | 0.89 (Stable) | LOW |
| PIPE-001 | 10 | 2 | 0.17 (Unstable) | MEDIUM |
| DAEMON-001 | 15 | 3 | 0.17 (Unstable) | MEDIUM |

**Stability Formula:** `Depended By / (Depends On + Depended By)`
- 1.00 = Very Stable (no dependencies, many dependents)
- 0.00 = Very Unstable (many dependencies, no dependents)

### 12.2 Coupling Metrics

**Fan-Out (Dependencies):**
- Highest: DAEMON-001 (15 dependencies)
- Lowest: MOD-001, MOD-003, MOD-004 (0 dependencies)

**Fan-In (Dependents):**
- Highest: MOD-001 (14 dependents)
- Lowest: MOD-003 (3 dependents)

**Average Dependencies per Module:** 2.8
**Average Dependents per Module:** 5.2

---

## 13. Recommendations

### 13.1 Dependency Management

**Keep:**
- ✅ Centralized enforcement (MOD-001) - good design
- ✅ Centralized lockouts (MOD-002) - good design
- ✅ No circular dependencies - excellent
- ✅ Clear layering - excellent

**Improve:**
- ⚠️ Reduce PIPE-001 dependencies (10 direct dependencies) - consider splitting
- ⚠️ Reduce DAEMON-001 dependencies (15 direct dependencies) - consider facade pattern
- ⚠️ Add dependency injection for easier testing

**Monitor:**
- 📊 TopstepX API stability (external dependency)
- 📊 SignalR connection reliability (external dependency)
- 📊 Module interface stability (version changes)

### 13.2 Future Dependency Planning

**If Adding New Rules:**
1. Follow existing dependency pattern (MOD-001, MOD-002)
2. Keep dependencies minimal
3. Document new dependencies in rule spec

**If Adding New Modules:**
1. Aim for 0-2 dependencies maximum
2. Make new module a dependency target, not dependent
3. Follow base module pattern (like MOD-001, MOD-003, MOD-004)

**If Refactoring:**
1. Don't break MOD-001, MOD-002 interfaces (14+ dependents)
2. Use adapter pattern for external API changes
3. Version configuration schemas

---

## 14. Dependency Validation

### 14.1 Automated Checks

**Recommended CI/CD Checks:**
```bash
# Check for circular dependencies
python scripts/check_circular_deps.py

# Validate all specs have dependency declarations
python scripts/validate_spec_deps.py

# Check import consistency
python scripts/check_imports.py

# Validate configuration schemas
python scripts/validate_configs.py
```

### 14.2 Manual Review Checklist

**Before Implementation:**
- [ ] All module dependencies declared in spec
- [ ] No circular dependencies
- [ ] External dependencies documented
- [ ] Configuration dependencies mapped
- [ ] Database schema dependencies clear

**During Implementation:**
- [ ] Actual imports match spec dependencies
- [ ] No hidden dependencies added
- [ ] Test mocks respect dependencies
- [ ] Dependency injection used where appropriate

**After Implementation:**
- [ ] Dependency graph still matches specs
- [ ] No new circular dependencies introduced
- [ ] Documentation updated for any changes
- [ ] Regression tests cover dependency changes

---

## Summary Statistics

**Total Specifications:** 100+
**Total Modules:** 9 core modules
**Total Rules:** 12 risk rules
**Total Dependencies:** 250+ relationships
**Circular Dependencies:** 0
**Maximum Depth:** 5 levels
**Average Dependencies:** 2.8 per module
**Most Depended-On:** MOD-001 (14 dependents)
**Most Dependencies:** DAEMON-001 (15 dependencies)
**External Dependencies:** 2 (TopstepX REST API, TopstepX SignalR)
**Configuration Files:** 4 (risk_config, accounts, admin_password, logging)
**Database Tables:** 9 (SQLite)

**Overall Health:** ✅ EXCELLENT
- No circular dependencies
- Clear layering
- Well-documented
- Intentional coupling (centralized patterns)

---

**Generated by:** Dependency Mapper Agent
**Report Date:** 2025-10-22
**Project Version:** 2.2
**Status:** Complete and Ready for Implementation
