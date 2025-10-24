#!/usr/bin/env python3
"""
Database Initialization Script
Creates state.db with complete schema from schema.sql

Usage:
    python scripts/init_database.py
    python scripts/init_database.py --db-path custom/path/state.db
"""

import argparse
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get project root directory."""
    # This script is in scripts/, so parent is project root
    return Path(__file__).parent.parent


def read_schema_sql(schema_path: Path) -> str:
    """Read schema.sql file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        return f.read()


def init_database(db_path: Path, schema_sql: str) -> None:
    """
    Initialize database with schema.

    Args:
        db_path: Path to database file
        schema_sql: SQL schema content
    """
    # Create parent directory if needed
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if database already exists
    db_exists = db_path.exists()

    if db_exists:
        logger.warning(f"Database already exists: {db_path}")
        response = input("Overwrite existing database? (yes/no): ").strip().lower()
        if response != 'yes':
            logger.info("Database initialization cancelled.")
            return

        # Backup existing database
        backup_path = db_path.parent / f"state_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        import shutil
        shutil.copy2(db_path, backup_path)
        logger.info(f"Backed up existing database to: {backup_path}")

        # Remove old database
        db_path.unlink()

    # Create new database and execute schema
    logger.info(f"Creating database: {db_path}")

    try:
        with sqlite3.connect(db_path) as conn:
            # Enable foreign keys (though we don't use them)
            conn.execute("PRAGMA foreign_keys = ON")

            # Execute schema
            conn.executescript(schema_sql)

            # Verify tables created
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]

            logger.info(f"Created {len(tables)} tables:")
            for table in tables:
                logger.info(f"  - {table}")

            # Verify indexes created
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
            )
            indexes = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]

            logger.info(f"Created {len(indexes)} indexes:")
            for index in indexes:
                logger.info(f"  - {index}")

            conn.commit()

        logger.info("✅ Database initialization complete!")
        logger.info(f"Database location: {db_path.resolve()}")

        # Show database size
        size_bytes = db_path.stat().st_size
        size_kb = size_bytes / 1024
        logger.info(f"Database size: {size_kb:.2f} KB")

    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


def validate_schema(db_path: Path) -> bool:
    """
    Validate that database has all required tables.

    Args:
        db_path: Path to database file

    Returns:
        True if valid, False otherwise
    """
    required_tables = {
        'lockouts', 'daily_pnl', 'contract_cache', 'trade_history',
        'session_state', 'positions', 'orders', 'enforcement_log',
        'reset_schedule', 'schema_version'
    }

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            existing_tables = {row[0] for row in cursor.fetchall()}

            missing = required_tables - existing_tables

            if missing:
                logger.error(f"Missing tables: {missing}")
                return False

            logger.info("✅ Schema validation passed!")
            return True

    except sqlite3.Error as e:
        logger.error(f"Schema validation failed: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Initialize Simple Risk Manager database'
    )
    parser.add_argument(
        '--db-path',
        type=Path,
        help='Path to database file (default: data/state.db)'
    )
    parser.add_argument(
        '--schema-path',
        type=Path,
        help='Path to schema.sql file (default: data/schema.sql)'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate existing database'
    )

    args = parser.parse_args()

    # Determine paths
    project_root = get_project_root()
    db_path = args.db_path or (project_root / 'data' / 'state.db')
    schema_path = args.schema_path or (project_root / 'data' / 'schema.sql')

    logger.info("=== Simple Risk Manager Database Initialization ===")
    logger.info(f"Project root: {project_root}")
    logger.info(f"Database path: {db_path}")
    logger.info(f"Schema path: {schema_path}")

    if args.validate_only:
        if not db_path.exists():
            logger.error(f"Database does not exist: {db_path}")
            sys.exit(1)

        if validate_schema(db_path):
            logger.info("Database is valid!")
            sys.exit(0)
        else:
            logger.error("Database validation failed!")
            sys.exit(1)

    # Read schema
    schema_sql = read_schema_sql(schema_path)

    # Initialize database
    init_database(db_path, schema_sql)

    # Validate
    if validate_schema(db_path):
        logger.info("Database ready for use!")
    else:
        logger.error("Database validation failed after creation!")
        sys.exit(1)


if __name__ == '__main__':
    main()
