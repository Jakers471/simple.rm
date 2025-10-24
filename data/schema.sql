-- Simple Risk Manager Database Schema
-- Created: 2025-10-23
-- SQLite Database for State Persistence and Crash Recovery
-- Total Tables: 9

-- ============================================================
-- Table 1: lockouts (MOD-002: Lockout Manager)
-- ============================================================
CREATE TABLE IF NOT EXISTS lockouts (
    account_id INTEGER PRIMARY KEY,
    is_locked BOOLEAN NOT NULL DEFAULT 0,
    reason TEXT,
    locked_at DATETIME,
    locked_until DATETIME,
    rule_id TEXT,  -- Which rule caused lockout (e.g., "RULE-003")
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lockouts_until ON lockouts(locked_until);

-- ============================================================
-- Table 2: daily_pnl (MOD-005: PNL Tracker)
-- ============================================================
CREATE TABLE IF NOT EXISTS daily_pnl (
    account_id INTEGER NOT NULL,
    date DATE NOT NULL,
    realized_pnl REAL NOT NULL DEFAULT 0.0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (account_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_pnl_date ON daily_pnl(date);

-- ============================================================
-- Table 3: contract_cache (MOD-007: Contract Cache)
-- ============================================================
CREATE TABLE IF NOT EXISTS contract_cache (
    contract_id TEXT PRIMARY KEY,
    tick_size REAL NOT NULL,
    tick_value REAL NOT NULL,
    symbol_id TEXT NOT NULL,
    name TEXT,
    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contract_cache_symbol ON contract_cache(symbol_id);

-- ============================================================
-- Table 4: trade_history (MOD-008: Trade Counter)
-- ============================================================
CREATE TABLE IF NOT EXISTS trade_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    contract_id TEXT NOT NULL,
    pnl REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trade_history_account_time ON trade_history(account_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trade_history_timestamp ON trade_history(timestamp);

-- ============================================================
-- Table 5: session_state (MOD-008: Trade Counter)
-- ============================================================
CREATE TABLE IF NOT EXISTS session_state (
    account_id INTEGER PRIMARY KEY,
    session_start DATETIME NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Table 6: positions (MOD-009: State Manager)
-- ============================================================
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY,  -- TopstepX position ID
    account_id INTEGER NOT NULL,
    contract_id TEXT NOT NULL,
    type INTEGER NOT NULL,  -- 1=Long, 2=Short
    size INTEGER NOT NULL,
    average_price REAL NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_positions_account ON positions(account_id);
CREATE INDEX IF NOT EXISTS idx_positions_contract ON positions(contract_id);

-- ============================================================
-- Table 7: orders (MOD-009: State Manager)
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,  -- TopstepX order ID
    account_id INTEGER NOT NULL,
    contract_id TEXT NOT NULL,
    type INTEGER NOT NULL,  -- OrderType enum (1=Limit, 2=Market, 3=StopLimit, 4=Stop, 5=TrailingStop)
    side INTEGER NOT NULL,  -- 0=Buy, 1=Sell
    size INTEGER NOT NULL,
    limit_price REAL,
    stop_price REAL,
    state INTEGER NOT NULL,  -- OrderState enum (1=Pending, 2=Working, 3=Filled, 4=Cancelled, 5=Rejected)
    created_at DATETIME NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orders_account ON orders(account_id);
CREATE INDEX IF NOT EXISTS idx_orders_contract ON orders(contract_id);
CREATE INDEX IF NOT EXISTS idx_orders_state ON orders(state);

-- ============================================================
-- Table 8: enforcement_log (MOD-001: Enforcement Actions)
-- ============================================================
CREATE TABLE IF NOT EXISTS enforcement_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    account_id INTEGER NOT NULL,
    rule_id TEXT NOT NULL,  -- e.g., "RULE-003"
    action TEXT NOT NULL,   -- e.g., "close_all_positions", "set_lockout"
    reason TEXT NOT NULL,   -- e.g., "Daily loss limit: -$550"
    success BOOLEAN NOT NULL DEFAULT 1,
    details TEXT,           -- JSON details (positions closed, orders cancelled, etc.)
    execution_time_ms INTEGER  -- How long enforcement took
);

CREATE INDEX IF NOT EXISTS idx_enforcement_account ON enforcement_log(account_id);
CREATE INDEX IF NOT EXISTS idx_enforcement_timestamp ON enforcement_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_enforcement_rule ON enforcement_log(rule_id);

-- ============================================================
-- Table 9: reset_schedule (MOD-004: Reset Scheduler)
-- ============================================================
CREATE TABLE IF NOT EXISTS reset_schedule (
    account_id INTEGER PRIMARY KEY,
    last_reset_date DATE NOT NULL,
    next_reset_time DATETIME NOT NULL,
    reset_time_config TEXT NOT NULL,  -- "17:00" from config
    timezone TEXT NOT NULL  -- "America/New_York"
);

-- ============================================================
-- Schema Version
-- ============================================================
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_version (version) VALUES (1);
