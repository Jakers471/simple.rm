# Test Scenario Matrix - Simple Risk Manager

**Generated:** 2025-10-22
**Purpose:** Comprehensive test plan covering unit, integration, and end-to-end testing
**Version:** 1.0
**Status:** Implementation Ready

---

## Executive Summary

This document defines **156 test scenarios** across 3 categories:
- **Unit Tests (84 scenarios):** Module-level component testing
- **Integration Tests (42 scenarios):** API and system integration testing
- **End-to-End Tests (30 scenarios):** Complete workflow validation

**Test Coverage Target:** 90%+ code coverage
**Frameworks:** pytest (unit/integration), Playwright (E2E if UI added)

---

## Table of Contents

1. [Unit Tests](#unit-tests)
2. [Integration Tests](#integration-tests)
3. [End-to-End Tests](#end-to-end-tests)
4. [Test Data Requirements](#test-data-requirements)
5. [Testing Infrastructure](#testing-infrastructure)
6. [Coverage Metrics](#coverage-metrics)

---

# Unit Tests

## 1. Core Modules (MOD-001 through MOD-009)

### 1.1 MOD-001: Enforcement Actions (`src/enforcement/actions.py`)

**Spec-ID:** MOD-001
**Test File:** `tests/unit/test_enforcement_actions.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-001-01 | close_all_positions() with 2 open positions | Mock REST API, 2 positions in state | All positions closed via API | High |
| UT-001-02 | close_all_positions() with API failure | Mock REST API returning 500 error | Returns False, logs error | High |
| UT-001-03 | close_all_positions() with network timeout | Mock REST API with timeout | Retries 3 times, then returns False | High |
| UT-001-04 | cancel_all_orders() with 3 working orders | Mock REST API, 3 orders in state | All orders canceled via API | High |
| UT-001-05 | reduce_position_to_limit() from 5 to 3 contracts | Mock REST API, position size 5 | Position reduced to 3 via partialClose | Medium |
| UT-001-06 | place_stop_loss_order() for new position | Mock REST API, position without SL | Stop-loss order placed at calculated price | Medium |
| UT-001-07 | Enforcement log written after action | Mock SQLite | Log entry created with correct details | High |
| UT-001-08 | Concurrent enforcement actions | 2 threads calling enforcement | Both actions execute without conflict | Medium |

**Total MOD-001 Tests:** 8

---

### 1.2 MOD-002: Lockout Manager (`src/state/lockout_manager.py`)

**Spec-ID:** MOD-002
**Test File:** `tests/unit/test_lockout_manager.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-002-01 | set_lockout() with expiry time | Clean lockout state | Lockout set, is_locked_out() returns True | High |
| UT-002-02 | set_lockout() with permanent lockout | Clean state | Lockout set with NULL expiry | High |
| UT-002-03 | is_locked_out() when locked | Lockout set for account | Returns True | High |
| UT-002-04 | is_locked_out() when not locked | No lockout | Returns False | High |
| UT-002-05 | is_locked_out() after expiry | Lockout expired 5 minutes ago | Returns False (auto-cleared) | High |
| UT-002-06 | clear_lockout() manual unlock | Lockout active | Lockout cleared, is_locked_out() returns False | Medium |
| UT-002-07 | check_expired_lockouts() batch check | 3 accounts, 1 expired | Expired lockout cleared, others remain | High |
| UT-002-08 | get_lockout_info() details | Active lockout | Returns reason, expiry, rule_id | Medium |
| UT-002-09 | Lockout persistence to SQLite | Lockout set | SQLite row created/updated | High |
| UT-002-10 | Load lockouts from SQLite on init | Existing lockout in DB | Lockout restored to memory | High |

**Total MOD-002 Tests:** 10

---

### 1.3 MOD-003: Timer Manager (`src/state/timer_manager.py`)

**Spec-ID:** MOD-003
**Test File:** `tests/unit/test_timer_manager.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-003-01 | start_timer() with duration | Clean timer state | Timer started, get_remaining_time() returns duration | High |
| UT-003-02 | start_timer() callback on expiry | Timer with callback | Callback executed when timer expires | High |
| UT-003-03 | get_remaining_time() during timer | Timer running 30s of 60s | Returns ~30 seconds | Medium |
| UT-003-04 | cancel_timer() before expiry | Active timer | Timer stopped, callback not executed | Medium |
| UT-003-05 | check_timers() batch check | 3 timers, 1 expired | Expired timer callback executed | High |
| UT-003-06 | Multiple timers for same account | 2 timers with different names | Both timers tracked independently | Medium |

**Total MOD-003 Tests:** 6

---

### 1.4 MOD-004: Reset Scheduler (`src/state/reset_scheduler.py`)

**Spec-ID:** MOD-004
**Test File:** `tests/unit/test_reset_scheduler.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-004-01 | schedule_daily_reset() config | Config: 17:00 ET | Reset scheduled for next 5 PM ET | High |
| UT-004-02 | reset_daily_counters() execution | Daily P&L = -$500 | P&L reset to 0, lockouts cleared | High |
| UT-004-03 | check_reset_times() before reset time | Current time 4:00 PM | Returns empty list (no reset yet) | Medium |
| UT-004-04 | check_reset_times() at reset time | Current time 5:00 PM | Returns account_id for reset | High |
| UT-004-05 | is_holiday() check | Date is July 4th | Returns True | Medium |
| UT-004-06 | Double-reset prevention | Reset already run today | check_reset_times() returns empty | High |

**Total MOD-004 Tests:** 6

---

### 1.5 MOD-005: PNL Tracker (`src/state/pnl_tracker.py`)

**Spec-ID:** MOD-005
**Test File:** `tests/unit/test_pnl_tracker.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-005-01 | add_trade_pnl() positive P&L | Daily P&L = 0 | Daily P&L increases by trade amount | High |
| UT-005-02 | add_trade_pnl() negative P&L | Daily P&L = 0 | Daily P&L decreases by trade amount | High |
| UT-005-03 | get_daily_realized_pnl() query | Multiple trades logged | Returns sum of all trades today | High |
| UT-005-04 | reset_daily_pnl() reset | Daily P&L = -$350 | P&L reset to 0 | High |
| UT-005-05 | calculate_unrealized_pnl() long position | Long 3 MNQ @ 21000, current 21002 | Returns positive P&L | High |
| UT-005-06 | calculate_unrealized_pnl() short position | Short 2 ES @ 5000, current 4995 | Returns positive P&L | High |
| UT-005-07 | PNL persistence to SQLite | Trades added | SQLite daily_pnl table updated | High |
| UT-005-08 | Load PNL from SQLite on init | Existing PNL in DB | PNL restored to memory | High |

**Total MOD-005 Tests:** 8

---

### 1.6 MOD-006: Quote Tracker (`src/api/quote_tracker.py`)

**Spec-ID:** MOD-006
**Test File:** `tests/unit/test_quote_tracker.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-006-01 | update_quote() new contract | No existing quote | Quote stored in memory | High |
| UT-006-02 | update_quote() existing contract | Quote already exists | Quote updated with new prices | High |
| UT-006-03 | get_quote() existing contract | Quote stored | Returns Quote object | High |
| UT-006-04 | get_quote() non-existent contract | No quote stored | Returns None | Medium |
| UT-006-05 | Quote age calculation | Quote received 5 seconds ago | age_seconds() returns ~5 | Medium |
| UT-006-06 | is_stale() check | Quote received 10 seconds ago | Returns True (stale after 5s) | Medium |

**Total MOD-006 Tests:** 6

---

### 1.7 MOD-007: Contract Cache (`src/api/contract_cache.py`)

**Spec-ID:** MOD-007
**Test File:** `tests/unit/test_contract_cache.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-007-01 | fetch_and_cache() new contract | Mock REST API | Contract metadata fetched and cached | High |
| UT-007-02 | get_contract() cached contract | Contract already cached | Returns metadata without API call | High |
| UT-007-03 | get_contract() uncached contract | Contract not cached | Returns None (does not auto-fetch) | Medium |
| UT-007-04 | calculate_pnl() using metadata | MNQ metadata, entry/exit prices | Returns correct P&L | High |
| UT-007-05 | Cache persistence to SQLite | Contracts cached | SQLite contract_cache table updated | High |
| UT-007-06 | Load cache from SQLite on init | Existing cache in DB | Cache restored to memory | High |

**Total MOD-007 Tests:** 6

---

### 1.8 MOD-008: Trade Counter (`src/state/trade_counter.py`)

**Spec-ID:** MOD-008
**Test File:** `tests/unit/test_trade_counter.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-008-01 | record_trade() new trade | Trade history empty | Trade added with timestamp | High |
| UT-008-02 | get_trades_in_window() last 60s | 5 trades recorded | Returns trades within 60s window | High |
| UT-008-03 | get_trades_since_session_start() | Session start 2 hours ago | Returns all trades since session start | High |
| UT-008-04 | clear_old_trades() cleanup | Trades older than 7 days | Old trades deleted from SQLite | Medium |
| UT-008-05 | Trade persistence to SQLite | Trades recorded | SQLite trade_history table updated | High |
| UT-008-06 | Load trades from SQLite on init | Existing trades in DB | Trades restored to memory | High |

**Total MOD-008 Tests:** 6

---

### 1.9 MOD-009: State Manager (`src/state/state_manager.py`)

**Spec-ID:** MOD-009
**Test File:** `tests/unit/test_state_manager.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-009-01 | update_position() new position | No existing position | Position added to state | High |
| UT-009-02 | update_position() existing position | Position already exists | Position updated | High |
| UT-009-03 | remove_position() closed position | Position size = 0 | Position removed from state | High |
| UT-009-04 | get_position_count() net contracts | Long 3 MNQ, Short 2 ES | Returns net = 1 | High |
| UT-009-05 | get_positions_by_contract() filter | Multiple positions | Returns positions for specific contract | Medium |
| UT-009-06 | update_order() new order | No existing order | Order added to state | High |
| UT-009-07 | update_order() existing order | Order already exists | Order updated | High |
| UT-009-08 | remove_order() filled/canceled | Order state = FILLED | Order removed from state | High |
| UT-009-09 | get_open_orders() query | Multiple orders | Returns only ACTIVE/PARTIAL orders | Medium |
| UT-009-10 | State persistence to SQLite | Positions/orders updated | SQLite tables updated | High |
| UT-009-11 | Load state from SQLite on init | Existing state in DB | State restored to memory | High |

**Total MOD-009 Tests:** 11

---

## 2. Risk Rules (RULE-001 through RULE-012)

### 2.1 RULE-001: Max Contracts

**Spec-ID:** RULE-001
**Test File:** `tests/unit/test_rules/test_max_contracts.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-101-01 | check() under limit | Net 4 contracts, limit 5 | Returns None (no breach) | High |
| UT-101-02 | check() at limit | Net 5 contracts, limit 5 | Returns None (at limit OK) | High |
| UT-101-03 | check() breach by 1 | Net 6 contracts, limit 5 | Returns CLOSE_ALL_POSITIONS action | High |
| UT-101-04 | check() net calculation | Long 7, Short 2 = net 5 | Returns None if limit 5 | High |
| UT-101-05 | check() reduce_to_limit mode | Net 6, limit 5, reduce mode | Returns reduce_position action | Medium |
| UT-101-06 | check() ignores closed positions | Closed position in state | Not counted toward limit | Medium |

**Total RULE-001 Tests:** 6

---

### 2.2 RULE-002: Max Contracts Per Instrument

**Spec-ID:** RULE-002
**Test File:** `tests/unit/test_rules/test_max_contracts_per_instrument.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-102-01 | check() under limit | MNQ=2, limit=3 | Returns None | High |
| UT-102-02 | check() breach for instrument | MNQ=4, limit=3 | Returns reduce_position action | High |
| UT-102-03 | check() unknown symbol block | Symbol not in config | Returns cancel_order action | Medium |
| UT-102-04 | check() multiple instruments | MNQ=2, ES=1, both within limits | Returns None | High |
| UT-102-05 | check() net per instrument | Long 4 MNQ, Short 2 MNQ = net 2 | Returns None if limit 3 | Medium |

**Total RULE-002 Tests:** 5

---

### 2.3 RULE-003: Daily Realized Loss

**Spec-ID:** RULE-003
**Test File:** `tests/unit/test_rules/test_daily_realized_loss.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-103-01 | check() under limit | Daily P&L = -$400, limit -$500 | Returns None | High |
| UT-103-02 | check() at limit | Daily P&L = -$500, limit -$500 | Returns None | High |
| UT-103-03 | check() breach by $1 | Daily P&L = -$501, limit -$500 | Returns CLOSE_ALL_AND_LOCKOUT action | High |
| UT-103-04 | check() lockout until next reset | Breach detected | Lockout set until configured reset time | High |
| UT-103-05 | check() after daily reset | P&L reset to 0 | Returns None | High |

**Total RULE-003 Tests:** 5

---

### 2.4 RULE-004: Daily Unrealized Loss

**Spec-ID:** RULE-004
**Test File:** `tests/unit/test_rules/test_daily_unrealized_loss.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-104-01 | check() under limit | Unrealized P&L = -$400, limit -$500 | Returns None | High |
| UT-104-02 | check() breach | Unrealized P&L = -$550, limit -$500 | Returns CLOSE_ALL_AND_LOCKOUT action | High |
| UT-104-03 | check() with multiple positions | 3 positions, sum = -$520 | Returns breach action | High |
| UT-104-04 | check() triggered by quote update | Position unchanged, quote moved | Recalculates unrealized P&L | High |
| UT-104-05 | check() long position losing | Long @ 21000, current 20950 | Calculates correct negative P&L | High |
| UT-104-06 | check() short position losing | Short @ 21000, current 21050 | Calculates correct negative P&L | High |

**Total RULE-004 Tests:** 6

---

### 2.5 RULE-005: Max Unrealized Profit

**Spec-ID:** RULE-005
**Test File:** `tests/unit/test_rules/test_max_unrealized_profit.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-105-01 | check() under limit | Unrealized P&L = $1800, limit $2000 | Returns None | High |
| UT-105-02 | check() breach | Unrealized P&L = $2100, limit $2000 | Returns CLOSE_ALL_AND_LOCKOUT action | High |
| UT-105-03 | check() long position winning | Long @ 21000, current 21100 | Calculates correct positive P&L | High |
| UT-105-04 | check() short position winning | Short @ 21000, current 20900 | Calculates correct positive P&L | High |

**Total RULE-005 Tests:** 4

---

### 2.6 RULE-006: Trade Frequency Limit

**Spec-ID:** RULE-006
**Test File:** `tests/unit/test_rules/test_trade_frequency_limit.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-106-01 | check() under per_minute limit | 2 trades in last 60s, limit 3 | Returns None | High |
| UT-106-02 | check() breach per_minute | 4 trades in last 60s, limit 3 | Returns COOLDOWN action | High |
| UT-106-03 | check() breach per_hour | 11 trades in last hour, limit 10 | Returns COOLDOWN action | High |
| UT-106-04 | check() breach per_session | 51 trades since session start, limit 50 | Returns COOLDOWN action | High |
| UT-106-05 | check() cooldown duration | Breach detected | Cooldown matches config duration | Medium |

**Total RULE-006 Tests:** 5

---

### 2.7 RULE-007: Cooldown After Loss

**Spec-ID:** RULE-007
**Test File:** `tests/unit/test_rules/test_cooldown_after_loss.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-107-01 | check() profit trade | Trade P&L = +$50 | Returns None | High |
| UT-107-02 | check() loss trade under threshold | Trade P&L = -$20, threshold -$50 | Returns None | High |
| UT-107-03 | check() loss trade breach | Trade P&L = -$75, threshold -$50 | Returns COOLDOWN action | High |
| UT-107-04 | check() cooldown duration | Breach detected | Cooldown set for configured duration | Medium |

**Total RULE-007 Tests:** 4

---

### 2.8 RULE-008: No Stop-Loss Grace Period

**Spec-ID:** RULE-008
**Test File:** `tests/unit/test_rules/test_no_stop_loss_grace.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-108-01 | check() position with stop-loss | Position + SL order exists | Returns None | High |
| UT-108-02 | check() position without SL | Position opened, no SL order | Starts 30s grace timer | High |
| UT-108-03 | check() SL added within grace | Position + SL placed in 15s | Cancels grace timer, returns None | High |
| UT-108-04 | check() grace period expired | 30s elapsed, no SL | Returns CLOSE_ALL_AND_LOCKOUT action | High |
| UT-108-05 | check() SL detection by order type | Stop order on opposite side of position | Detects as valid SL | Medium |

**Total RULE-008 Tests:** 5

---

### 2.9 RULE-009: Session Block Outside Hours

**Spec-ID:** RULE-009
**Test File:** `tests/unit/test_rules/test_session_block_outside.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-109-01 | check() position during session | Time 10:00 AM, session 9:30-4:00 | Returns None | High |
| UT-109-02 | check() position outside session | Time 8:00 AM, session 9:30-4:00 | Returns CLOSE_ALL_AND_LOCKOUT action | High |
| UT-109-03 | check() holiday detection | Date is July 4th | Returns lockout action | Medium |
| UT-109-04 | check() per-instrument session | ES position @ 6PM CT (ES session active) | Returns None | High |
| UT-109-05 | check() session end auto-close | Time = session end | Closes all positions | High |

**Total RULE-009 Tests:** 5

---

### 2.10 RULE-010: Auth Loss Guard

**Spec-ID:** RULE-010
**Test File:** `tests/unit/test_rules/test_auth_loss_guard.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-110-01 | check() normal trading event | GatewayUserTrade event | Returns None | High |
| UT-110-02 | check() auth event detected | GatewayUserAccount + auth signature | Returns CLOSE_ALL_AND_LOCKOUT action | High |
| UT-110-03 | check() auth bypass pattern | Suspicious account state change | Logs warning, returns action | Medium |

**Total RULE-010 Tests:** 3

---

### 2.11 RULE-011: Symbol Blocks

**Spec-ID:** RULE-011
**Test File:** `tests/unit/test_rules/test_symbol_blocks.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-111-01 | check() allowed symbol | Position in MNQ, MNQ allowed | Returns None | High |
| UT-111-02 | check() blocked symbol position | Position in BTC, BTC blocked | Returns CLOSE_ALL_AND_LOCKOUT action | High |
| UT-111-03 | check() blocked symbol order | Order in blocked symbol | Returns cancel_order action | Medium |

**Total RULE-011 Tests:** 3

---

### 2.12 RULE-012: Trade Management (Auto Stop-Loss)

**Spec-ID:** RULE-012
**Test File:** `tests/unit/test_rules/test_trade_management.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-112-01 | check() position without auto-SL | Position, auto_stop disabled | Returns None | Medium |
| UT-112-02 | check() position needs auto-SL | Position profitable, no SL | Returns AUTO_STOP_LOSS action | High |
| UT-112-03 | check() auto-SL price calculation | Long @ 21000, profit $100 | Calculates breakeven SL price | High |
| UT-112-04 | check() trailing stop update | Position profit increases | Updates SL price higher | Medium |
| UT-112-05 | check() position already has SL | Manual SL exists | Returns None (don't override) | Medium |

**Total RULE-012 Tests:** 5

---

## 3. Event Router & Pipeline

**Test File:** `tests/unit/test_event_router.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| UT-201-01 | route_event() updates state first | GatewayUserTrade event | State updated before rule checks | Critical |
| UT-201-02 | route_event() lockout gating | Account locked, event arrives | Rules not executed (skipped) | High |
| UT-201-03 | route_event() routes to correct rules | GatewayUserPosition event | Routes to RULE-001, 002, 004, 005, etc. | High |
| UT-201-04 | route_event() stops after first breach | 2 rules breach | Only first breach action executed | High |
| UT-201-05 | route_event() handles invalid event | Missing accountId | Logs error, does not crash | High |
| UT-201-06 | route_event() MarketQuote triggers | Quote event | Routes to RULE-004, 005 only | High |

**Total Event Router Tests:** 6

---

## Unit Test Summary

| Module/Component | Test Scenarios | Priority Distribution |
|------------------|----------------|----------------------|
| MOD-001 to MOD-009 | 67 | High: 50, Medium: 17 |
| RULE-001 to RULE-012 | 56 | High: 48, Medium: 8 |
| Event Router | 6 | Critical: 1, High: 5 |
| **Total Unit Tests** | **129** | **High: 104, Medium: 25** |

---

# Integration Tests

## 4. API Integration Tests

### 4.1 TopstepX REST API Integration

**Test File:** `tests/integration/test_api_integration.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| IT-001-01 | authenticate() valid credentials | Valid API key | Returns JWT token | High |
| IT-001-02 | authenticate() invalid credentials | Invalid API key | Raises AuthenticationError | High |
| IT-001-03 | POST /api/Position/closeContract | Open position | Position closed successfully | High |
| IT-001-04 | POST /api/Order/cancel | Working order | Order canceled successfully | High |
| IT-001-05 | POST /api/Order/placeOrder stop-loss | Valid order params | Stop-loss order placed | High |
| IT-001-06 | GET /api/Position/searchOpen | API available | Returns open positions | High |
| IT-001-07 | GET /api/Contract/searchById | Valid contract ID | Returns contract metadata | High |
| IT-001-08 | API rate limiting handling | 20 requests/second | Respects rate limits, no 429 errors | High |
| IT-001-09 | API retry on 500 error | Mock 500 response | Retries 3 times with backoff | High |
| IT-001-10 | API timeout handling | Mock slow response | Times out after 30s, retries | High |

**Total REST API Tests:** 10

---

### 4.2 SignalR WebSocket Integration

**Test File:** `tests/integration/test_signalr_integration.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| IT-002-01 | Connect to User Hub | Valid JWT token | Connection established | High |
| IT-002-02 | Connect to Market Hub | Valid JWT token | Connection established | High |
| IT-002-03 | Receive GatewayUserTrade event | Account trading | Event received and parsed | High |
| IT-002-04 | Receive GatewayUserPosition event | Position opened | Event received and parsed | High |
| IT-002-05 | Receive GatewayUserOrder event | Order placed | Event received and parsed | High |
| IT-002-06 | Receive MarketQuote event | Subscribed to contract | Quote received and parsed | High |
| IT-002-07 | Auto-reconnect on disconnect | Connection dropped | Reconnects within 5 seconds | High |
| IT-002-08 | Multiple simultaneous events | High trading activity | All events processed | Medium |
| IT-002-09 | Subscribe to contract quotes | New position opened | Quote subscription activated | High |
| IT-002-10 | Unsubscribe from contract | Position closed | Quote subscription removed | Medium |

**Total SignalR Tests:** 10

---

## 5. Database Integration Tests

**Test File:** `tests/integration/test_persistence.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| IT-003-01 | Save lockout to SQLite | Lockout set in memory | Row created in lockouts table | High |
| IT-003-02 | Load lockout from SQLite | Existing lockout row | Lockout restored to memory | High |
| IT-003-03 | Save daily P&L to SQLite | Trades recorded | daily_pnl table updated | High |
| IT-003-04 | Load daily P&L from SQLite | Existing P&L row | P&L restored to memory | High |
| IT-003-05 | Save positions to SQLite (batched) | 5 positions updated | Batch write every 5 seconds | High |
| IT-003-06 | Load positions from SQLite | Existing positions | All positions restored | High |
| IT-003-07 | Enforcement log write | Enforcement executed | Log row created | High |
| IT-003-08 | SQLite WAL mode enabled | Database initialized | journal_mode = WAL | High |
| IT-003-09 | Concurrent read/write | Multiple threads | No locking errors | Medium |
| IT-003-10 | Database corruption recovery | Corrupted state.db | Backup created, DB rebuilt | Low |

**Total Database Tests:** 10

---

## 6. Full Workflow Integration Tests

**Test File:** `tests/integration/test_full_workflow.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| IT-004-01 | Trade → P&L update → Daily loss breach | Simulated trade event | Lockout set, positions closed | High |
| IT-004-02 | Position open → No SL → Grace → Close | Simulated position event | Position closed after 30s | High |
| IT-004-03 | Quote update → Unrealized breach | Position + quote change | Lockout set | High |
| IT-004-04 | Multiple trades → Frequency breach | 4 trades in 60s, limit 3 | Cooldown set | High |
| IT-004-05 | Session end → Auto-close | Time reaches session end | All positions closed | High |
| IT-004-06 | Daily reset → P&L cleared | 5:00 PM ET | P&L reset, lockouts cleared | High |
| IT-004-07 | Max contracts breach → Reduce | 6 contracts, limit 5 | Position reduced to 5 | High |
| IT-004-08 | Blocked symbol position → Close | Position in blocked symbol | Position closed, locked out | High |
| IT-004-09 | Auto stop-loss placement | Position profitable | SL order placed at breakeven | Medium |
| IT-004-10 | Concurrent enforcement actions | Multiple breaches | All actions execute correctly | Medium |
| IT-004-11 | Crash recovery - positions | Daemon restart | Positions restored from SQLite | High |
| IT-004-12 | Crash recovery - lockouts | Daemon restart | Lockouts restored from SQLite | High |

**Total Workflow Tests:** 12

---

## Integration Test Summary

| Test Category | Test Scenarios | Priority Distribution |
|---------------|----------------|----------------------|
| REST API | 10 | High: 10 |
| SignalR WebSocket | 10 | High: 8, Medium: 2 |
| Database Persistence | 10 | High: 8, Medium: 1, Low: 1 |
| Full Workflow | 12 | High: 10, Medium: 2 |
| **Total Integration Tests** | **42** | **High: 36, Medium: 5, Low: 1** |

---

# End-to-End Tests

## 7. Complete System Workflows

**Test File:** `tests/e2e/test_complete_workflows.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| E2E-001 | Daemon startup → Trading → Enforcement → Shutdown | Clean system | Complete lifecycle executed | Critical |
| E2E-002 | Multiple accounts monitored | 2 accounts configured | Both accounts monitored independently | High |
| E2E-003 | Admin CLI configuration change | Daemon running | Config updated, daemon reloaded | High |
| E2E-004 | Trader CLI real-time updates | Daemon + Trader CLI running | CLI shows live P&L, lockouts | High |
| E2E-005 | Windows Service install/start/stop | Admin privileges | Service lifecycle managed | High |
| E2E-006 | Daily reset at 5 PM | Wait until reset time | P&L reset, lockouts cleared | High |
| E2E-007 | Full trading day simulation | 8 hours simulated time | All rules tested in realistic flow | High |
| E2E-008 | Network outage recovery | Disconnect SignalR | Reconnects, resumes monitoring | High |
| E2E-009 | Database backup and restore | Backup created | State restored from backup | Medium |
| E2E-010 | Token refresh at 20 hours | Token near expiry | Token refreshed automatically | Medium |

**Total E2E Tests:** 10

---

## 8. Performance & Load Tests

**Test File:** `tests/e2e/test_performance.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| E2E-101 | Event processing latency | 1000 events/second | All events processed < 10ms | High |
| E2E-102 | Memory usage under load | 8 hours runtime | Memory < 200 MB | High |
| E2E-103 | CPU usage under load | High event rate | CPU < 20% average | Medium |
| E2E-104 | SQLite write performance | 10,000 writes | No locking errors, < 5s total | Medium |
| E2E-105 | Concurrent rule checks | 12 rules checking simultaneously | No race conditions | High |

**Total Performance Tests:** 5

---

## 9. Error Handling & Edge Cases

**Test File:** `tests/e2e/test_error_handling.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| E2E-201 | Enforcement API failure | TopstepX API returns 500 | Logs error, retries, continues monitoring | High |
| E2E-202 | Invalid SignalR event payload | Malformed JSON | Logs error, skips event, continues | High |
| E2E-203 | SQLite database locked | Concurrent write conflict | Waits, retries, succeeds | Medium |
| E2E-204 | Configuration file missing | accounts.yaml deleted | Logs error, exits gracefully | High |
| E2E-205 | Configuration file invalid | Malformed YAML | Logs validation errors, exits | High |
| E2E-206 | Disk full during write | Disk space exhausted | Logs error, continues with in-memory state | Low |
| E2E-207 | TopstepX API key revoked | Auth fails after startup | Logs error, attempts to continue | Medium |
| E2E-208 | SignalR connection timeout | Network delay | Times out, reconnects | Medium |
| E2E-209 | Memory leak detection | 24 hour run | Memory stable, no leaks | Medium |
| E2E-210 | Rule configuration hot reload | Config changed while running | Rules updated without restart | Low |

**Total Error Handling Tests:** 10

---

## 10. Security & Access Control Tests

**Test File:** `tests/e2e/test_security.py`

| Test ID | Scenario Description | Prerequisites | Expected Outcome | Priority |
|---------|---------------------|---------------|------------------|----------|
| E2E-301 | Admin CLI password authentication | Correct password | Access granted | High |
| E2E-302 | Admin CLI password authentication | Incorrect password | Access denied | High |
| E2E-303 | Trader CLI read-only access | Trader CLI running | Cannot modify config | High |
| E2E-304 | Windows Service stop (trader) | Non-admin user | Operation denied | High |
| E2E-305 | API key storage security | Check config files | API keys not logged in plaintext | High |

**Total Security Tests:** 5

---

## End-to-End Test Summary

| Test Category | Test Scenarios | Priority Distribution |
|---------------|----------------|----------------------|
| Complete Workflows | 10 | Critical: 1, High: 8, Medium: 1 |
| Performance & Load | 5 | High: 3, Medium: 2 |
| Error Handling | 10 | High: 5, Medium: 4, Low: 1 |
| Security | 5 | High: 5 |
| **Total E2E Tests** | **30** | **Critical: 1, High: 21, Medium: 7, Low: 1** |

---

# Test Data Requirements

See separate document: `TEST_FIXTURES_PLAN.md`

---

# Testing Infrastructure

See separate document: `TESTING_READINESS.md`

---

# Coverage Metrics

## Overall Test Count

- **Unit Tests:** 129 scenarios
- **Integration Tests:** 42 scenarios
- **End-to-End Tests:** 30 scenarios
- **Total:** **201 test scenarios**

## Priority Breakdown

| Priority | Count | Percentage |
|----------|-------|------------|
| Critical | 2 | 1% |
| High | 161 | 80% |
| Medium | 34 | 17% |
| Low | 4 | 2% |

## Test Execution Estimates

- **Unit Tests:** ~15 minutes (parallel execution)
- **Integration Tests:** ~30 minutes (requires external services)
- **End-to-End Tests:** ~2 hours (full system workflows)
- **Total CI/CD Time:** ~2.75 hours

## Code Coverage Targets

| Component | Target Coverage | Measurement |
|-----------|-----------------|-------------|
| Core Modules | 95% | Line coverage |
| Risk Rules | 90% | Line + branch coverage |
| API Integration | 85% | Line coverage |
| Event Router | 95% | Branch coverage |
| **Overall** | **90%** | Line coverage |

---

## Next Steps

1. Review `TEST_FIXTURES_PLAN.md` for mock data requirements
2. Review `TESTING_READINESS.md` for framework setup
3. Prioritize High/Critical tests for initial implementation
4. Set up CI/CD pipeline for automated testing
5. Begin Phase 1 implementation (MVP rules)

---

**Document Complete** ✓
**Ready for Implementation** ✓
**Spec Coverage:** 100% of modules and rules covered
