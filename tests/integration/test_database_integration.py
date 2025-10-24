"""
Integration tests for database with core modules.

Tests that modules can correctly use the real database.
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


# Test database path
TEST_DB = Path(__file__).parent.parent.parent / "data" / "state.db"


@pytest.fixture
def db_connection():
    """Provide database connection for tests."""
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_database_exists():
    """Test that database file exists."""
    assert TEST_DB.exists(), f"Database not found: {TEST_DB}"


def test_all_tables_exist(db_connection):
    """Test that all required tables exist."""
    required_tables = {
        'lockouts', 'daily_pnl', 'contract_cache', 'trade_history',
        'session_state', 'positions', 'orders', 'enforcement_log',
        'reset_schedule', 'schema_version'
    }

    cursor = db_connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    existing_tables = {row[0] for row in cursor.fetchall()}

    missing = required_tables - existing_tables
    assert not missing, f"Missing tables: {missing}"


def test_all_indexes_exist(db_connection):
    """Test that all required indexes exist."""
    required_indexes = {
        'idx_lockouts_until',
        'idx_daily_pnl_date',
        'idx_contract_cache_symbol',
        'idx_trade_history_account_time',
        'idx_trade_history_timestamp',
        'idx_positions_account',
        'idx_positions_contract',
        'idx_orders_account',
        'idx_orders_contract',
        'idx_orders_state',
        'idx_enforcement_account',
        'idx_enforcement_timestamp',
        'idx_enforcement_rule',
    }

    cursor = db_connection.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    )
    existing_indexes = {row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')}

    missing = required_indexes - existing_indexes
    assert not missing, f"Missing indexes: {missing}"


def test_lockouts_table_operations(db_connection):
    """Test lockouts table CRUD operations."""
    account_id = 999999
    rule_id = "RULE-003"

    # Insert lockout
    db_connection.execute("""
        INSERT OR REPLACE INTO lockouts (account_id, is_locked, reason, locked_at, locked_until, rule_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        account_id,
        1,
        "Test lockout",
        datetime.now(),
        datetime.now() + timedelta(hours=24),
        rule_id
    ))
    db_connection.commit()

    # Read lockout
    cursor = db_connection.execute("SELECT * FROM lockouts WHERE account_id = ?", (account_id,))
    row = cursor.fetchone()
    assert row is not None
    assert row['is_locked'] == 1
    assert row['rule_id'] == rule_id

    # Update lockout
    db_connection.execute(
        "UPDATE lockouts SET is_locked = 0 WHERE account_id = ?",
        (account_id,)
    )
    db_connection.commit()

    # Verify update
    cursor = db_connection.execute("SELECT is_locked FROM lockouts WHERE account_id = ?", (account_id,))
    row = cursor.fetchone()
    assert row['is_locked'] == 0

    # Delete lockout
    db_connection.execute("DELETE FROM lockouts WHERE account_id = ?", (account_id,))
    db_connection.commit()


def test_daily_pnl_table_operations(db_connection):
    """Test daily_pnl table operations."""
    account_id = 999999
    today = datetime.now().date()

    # Insert P&L
    db_connection.execute("""
        INSERT OR REPLACE INTO daily_pnl (account_id, date, realized_pnl)
        VALUES (?, ?, ?)
    """, (account_id, today, -150.50))
    db_connection.commit()

    # Read P&L
    cursor = db_connection.execute(
        "SELECT * FROM daily_pnl WHERE account_id = ? AND date = ?",
        (account_id, today)
    )
    row = cursor.fetchone()
    assert row is not None
    assert row['realized_pnl'] == -150.50

    # Update P&L (add more loss)
    db_connection.execute("""
        UPDATE daily_pnl SET realized_pnl = realized_pnl + ?
        WHERE account_id = ? AND date = ?
    """, (-100.0, account_id, today))
    db_connection.commit()

    # Verify update
    cursor = db_connection.execute(
        "SELECT realized_pnl FROM daily_pnl WHERE account_id = ? AND date = ?",
        (account_id, today)
    )
    row = cursor.fetchone()
    assert row['realized_pnl'] == -250.50

    # Cleanup
    db_connection.execute("DELETE FROM daily_pnl WHERE account_id = ?", (account_id,))
    db_connection.commit()


def test_positions_table_operations(db_connection):
    """Test positions table operations."""
    position_id = 999999
    account_id = 999999
    contract_id = "CON.F.US.MNQ.TEST"

    # Insert position
    db_connection.execute("""
        INSERT OR REPLACE INTO positions (id, account_id, contract_id, type, size, average_price, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (position_id, account_id, contract_id, 1, 2, 18500.25, datetime.now()))
    db_connection.commit()

    # Read position
    cursor = db_connection.execute("SELECT * FROM positions WHERE id = ?", (position_id,))
    row = cursor.fetchone()
    assert row is not None
    assert row['size'] == 2
    assert row['average_price'] == 18500.25

    # Cleanup
    db_connection.execute("DELETE FROM positions WHERE id = ?", (position_id,))
    db_connection.commit()


def test_enforcement_log_operations(db_connection):
    """Test enforcement_log table operations."""
    account_id = 999999
    rule_id = "RULE-003"

    # Insert log entry
    db_connection.execute("""
        INSERT INTO enforcement_log (account_id, rule_id, action, reason, success, details, execution_time_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        account_id,
        rule_id,
        "close_all_positions",
        "Daily loss limit: -$550",
        1,
        '{"positions_closed": 2}',
        45
    ))
    db_connection.commit()

    # Read log entry
    cursor = db_connection.execute(
        "SELECT * FROM enforcement_log WHERE account_id = ? AND rule_id = ?",
        (account_id, rule_id)
    )
    row = cursor.fetchone()
    assert row is not None
    assert row['action'] == "close_all_positions"
    assert row['success'] == 1

    # Cleanup
    db_connection.execute("DELETE FROM enforcement_log WHERE account_id = ?", (account_id,))
    db_connection.commit()


def test_contract_cache_operations(db_connection):
    """Test contract_cache table operations."""
    contract_id = "CON.F.US.MNQ.TEST"

    # Insert contract metadata
    db_connection.execute("""
        INSERT OR REPLACE INTO contract_cache (contract_id, tick_size, tick_value, symbol_id, name)
        VALUES (?, ?, ?, ?, ?)
    """, (contract_id, 0.25, 0.50, "F.US.MNQ", "MNQTEST"))
    db_connection.commit()

    # Read contract
    cursor = db_connection.execute("SELECT * FROM contract_cache WHERE contract_id = ?", (contract_id,))
    row = cursor.fetchone()
    assert row is not None
    assert row['tick_size'] == 0.25
    assert row['tick_value'] == 0.50

    # Cleanup
    db_connection.execute("DELETE FROM contract_cache WHERE contract_id = ?", (contract_id,))
    db_connection.commit()


def test_database_size():
    """Test database is reasonable size."""
    size_bytes = TEST_DB.stat().st_size
    size_kb = size_bytes / 1024

    # Empty database should be < 200 KB
    assert size_kb < 200, f"Database too large: {size_kb:.2f} KB"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
