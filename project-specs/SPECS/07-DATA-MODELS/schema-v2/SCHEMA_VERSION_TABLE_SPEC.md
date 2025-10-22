# Schema Version Table Specification

**doc_id:** DB-SCHEMA-001
**version:** 2.0
**status:** DRAFT
**addresses:** REC-DM-001 from ERRORS_AND_WARNINGS_CONSOLIDATED.md

---

## Overview

This specification defines the `schema_version` table for tracking database schema evolution and migrations. This addresses **REC-DM-001** (MEDIUM priority) which identified the lack of schema versioning for future migrations.

**Purpose:** Enable safe, tracked migrations as the risk manager evolves, preventing schema drift and providing migration history.

---

## Schema Changes from v1

### New Tables

| Table | Purpose | Priority |
|-------|---------|----------|
| schema_version | Track database migrations and schema evolution | **Required** |

### Rationale

Without schema versioning:
- No way to detect schema version mismatches between code and database
- Migration scripts must manually check for existing tables
- No audit trail of when/why schema changed
- Rollback becomes complex and error-prone
- Multi-instance deployments risk schema conflicts

---

## Table Specification

### schema_version

**Purpose:** Track all schema migrations applied to the database.

**Table Structure:**
```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,  -- ISO8601 timestamp
    description TEXT NOT NULL,
    migration_script TEXT,
    rollback_script TEXT,
    execution_time_ms INTEGER,
    success BOOLEAN NOT NULL DEFAULT 1,
    error_message TEXT
);
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `version` | INTEGER | NO | Schema version number (1, 2, 3, ...) |
| `applied_at` | TEXT | NO | ISO8601 timestamp when migration applied |
| `description` | TEXT | NO | Human-readable description of migration |
| `migration_script` | TEXT | YES | SQL script that was executed (for audit) |
| `rollback_script` | TEXT | YES | SQL script to reverse migration (if applicable) |
| `execution_time_ms` | INTEGER | YES | How long migration took (milliseconds) |
| `success` | BOOLEAN | NO | Whether migration succeeded (default: 1) |
| `error_message` | TEXT | YES | Error message if migration failed |

**Indexes:**
```sql
CREATE INDEX idx_schema_version_applied ON schema_version(applied_at DESC);
```

**Constraints:**
- `version` is PRIMARY KEY (ensures no duplicate versions)
- `applied_at` must be valid ISO8601 timestamp
- `success` defaults to 1 (true)

---

## Migration Version Tracking

### Version Numbering

**Format:** Integer incrementing from 1

| Version | Description | Date Applied |
|---------|-------------|--------------|
| 1 | Initial schema (9 tables from DATABASE_SCHEMA.md) | Baseline |
| 2 | Schema v2 enhancements (schema_version, analytics indexes, new fields) | TBD |
| 3+ | Future migrations | TBD |

### Version Resolution

**On daemon startup:**

1. Check if `schema_version` table exists
   - If not: Database is v1 (baseline schema)
   - If exists: Read `MAX(version)` to get current schema version

2. Compare current schema version to required schema version (hardcoded in daemon)
   - If current < required: Run migration scripts
   - If current = required: Continue startup
   - If current > required: **FATAL ERROR** - daemon code is older than database

3. If migration needed, execute in transaction with full rollback support

**Example Check:**
```python
def get_current_schema_version(db: sqlite3.Connection) -> int:
    """Get current schema version from database."""
    cursor = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    if not cursor.fetchone():
        return 1  # Baseline schema (no schema_version table)

    cursor = db.execute("SELECT MAX(version) FROM schema_version WHERE success = 1")
    version = cursor.fetchone()[0]
    return version if version else 1
```

---

## Migration Record Format

### Example Records

**Version 1 (Baseline):**
```sql
INSERT INTO schema_version (version, applied_at, description, success)
VALUES (
    1,
    '2025-10-22T00:00:00Z',
    'Baseline schema - 9 tables (lockouts, daily_pnl, contract_cache, trade_history, session_state, positions, orders, enforcement_log, reset_schedule)',
    1
);
```

**Version 2 (Schema v2 Enhancements):**
```sql
INSERT INTO schema_version (version, applied_at, description, migration_script, execution_time_ms, success)
VALUES (
    2,
    '2025-10-22T14:30:00Z',
    'Schema v2: Add schema_version table, daily_unrealized_pnl table, execution_time_ms column, analytics indexes (GAP-DM-001, GAP-DM-003, REC-DM-004)',
    'CREATE TABLE schema_version (...); CREATE TABLE daily_unrealized_pnl (...); ALTER TABLE enforcement_log ADD COLUMN execution_time_ms INTEGER; CREATE INDEX ...',
    145,  -- took 145ms to execute
    1
);
```

**Failed Migration Example:**
```sql
INSERT INTO schema_version (version, applied_at, description, success, error_message)
VALUES (
    3,
    '2025-10-23T09:15:00Z',
    'Add foreign key constraints',
    0,  -- failed
    'FOREIGN KEY constraint failed: no such table: accounts'
);
```

---

## Migration Workflow

### Pre-Migration Checks

**Before applying any migration:**

1. **Backup Database**
   ```bash
   cp data/state.db data/backups/state_pre_v2_$(date +%Y%m%d_%H%M%S).db
   ```

2. **Verify Integrity**
   ```sql
   PRAGMA integrity_check;
   -- Result should be: ok
   ```

3. **Check Current Version**
   ```python
   current_version = get_current_schema_version(db)
   if current_version >= target_version:
       raise MigrationError(f"Database already at version {current_version}")
   ```

4. **Verify No Active Connections**
   - Ensure daemon is stopped
   - Ensure no admin CLI sessions active
   - Check for SQLite lock files

### Migration Execution

**Transactional Migration Pattern:**

```python
def apply_migration(db: sqlite3.Connection, version: int, description: str,
                    migration_sql: str, rollback_sql: Optional[str] = None):
    """Apply a schema migration in a transaction."""

    start_time = time.time()

    try:
        db.execute("BEGIN TRANSACTION")

        # Check version not already applied
        cursor = db.execute(
            "SELECT 1 FROM schema_version WHERE version = ? AND success = 1",
            (version,)
        )
        if cursor.fetchone():
            raise MigrationError(f"Version {version} already applied")

        # Execute migration SQL
        db.executescript(migration_sql)

        # Record successful migration
        execution_time_ms = int((time.time() - start_time) * 1000)
        db.execute("""
            INSERT INTO schema_version
            (version, applied_at, description, migration_script, rollback_script,
             execution_time_ms, success)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (
            version,
            datetime.utcnow().isoformat() + 'Z',
            description,
            migration_sql,
            rollback_sql,
            execution_time_ms
        ))

        db.commit()
        print(f"✓ Migration to version {version} successful ({execution_time_ms}ms)")

    except Exception as e:
        db.rollback()

        # Record failed migration
        db.execute("""
            INSERT INTO schema_version
            (version, applied_at, description, success, error_message)
            VALUES (?, ?, ?, 0, ?)
        """, (
            version,
            datetime.utcnow().isoformat() + 'Z',
            description,
            str(e)
        ))
        db.commit()

        raise MigrationError(f"Migration to version {version} failed: {e}")
```

### Post-Migration Verification

**After migration completes:**

1. **Verify Version Updated**
   ```sql
   SELECT MAX(version) FROM schema_version WHERE success = 1;
   -- Should return new version number
   ```

2. **Verify Tables Exist**
   ```python
   expected_tables = ['lockouts', 'daily_pnl', 'contract_cache', 'trade_history',
                      'session_state', 'positions', 'orders', 'enforcement_log',
                      'reset_schedule', 'schema_version']

   if version >= 2:
       expected_tables.append('daily_unrealized_pnl')

   cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table'")
   existing_tables = {row[0] for row in cursor.fetchall()}

   missing = set(expected_tables) - existing_tables
   if missing:
       raise MigrationError(f"Migration incomplete - missing tables: {missing}")
   ```

3. **Verify Indexes Exist**
   ```python
   cursor = db.execute("SELECT name FROM sqlite_master WHERE type='index'")
   indexes = {row[0] for row in cursor.fetchall()}

   # Check for expected indexes (version-dependent)
   ```

4. **Run Test Queries**
   ```python
   # Test that schema changes work
   db.execute("SELECT version, applied_at FROM schema_version ORDER BY version")

   # If version 2+, test new columns/tables
   if version >= 2:
       db.execute("SELECT execution_time_ms FROM enforcement_log LIMIT 1")
       db.execute("SELECT * FROM daily_unrealized_pnl LIMIT 1")
   ```

---

## Rollback Strategy

### Automatic Rollback

**If migration fails mid-execution:**
- Transaction automatically rolls back (atomicity guaranteed)
- Database remains at previous version
- Failed migration recorded in `schema_version` with `success = 0`
- Daemon startup will retry migration on next start

### Manual Rollback

**If migration succeeds but causes runtime issues:**

1. **Stop Daemon**
   ```bash
   ./scripts/stop_daemon.sh
   ```

2. **Restore from Backup**
   ```bash
   mv data/state.db data/state.db.failed_v2
   cp data/backups/state_pre_v2_YYYYMMDD_HHMMSS.db data/state.db
   ```

3. **Verify Restore**
   ```sql
   SELECT MAX(version) FROM schema_version WHERE success = 1;
   -- Should return previous version (or error if v1)
   ```

4. **Restart Daemon**
   ```bash
   ./scripts/start_daemon.sh
   ```

### Rollback Scripts (Optional)

**For reversible migrations, store rollback SQL:**

```python
# Example: Version 2 rollback
rollback_v2 = """
DROP INDEX IF EXISTS idx_enforcement_log_success;
DROP INDEX IF EXISTS idx_positions_updated;
DROP INDEX IF EXISTS idx_orders_state_account;

-- Cannot easily remove column (SQLite limitation)
-- Would require table recreation, so backup restore preferred

DROP TABLE IF EXISTS daily_unrealized_pnl;
DROP TABLE IF EXISTS schema_version;
"""
```

**Note:** SQLite does not support `ALTER TABLE DROP COLUMN`, so column additions are **not reversible** without full table recreation. This is why backup restore is the recommended rollback method.

---

## Version Compatibility

### Daemon Code Versions

**Each daemon version requires a specific schema version:**

| Daemon Version | Required Schema | Notes |
|----------------|-----------------|-------|
| v1.0.0 - v1.9.9 | 1 | Baseline schema |
| v2.0.0+ | 2 | Adds schema_version table, analytics indexes |
| v3.0.0+ | 3+ | Future enhancements |

**Startup Check:**
```python
REQUIRED_SCHEMA_VERSION = 2  # Hardcoded in daemon

current_version = get_current_schema_version(db)

if current_version < REQUIRED_SCHEMA_VERSION:
    print(f"Database schema v{current_version} < required v{REQUIRED_SCHEMA_VERSION}")
    print("Running automatic migration...")
    run_migrations(db, current_version, REQUIRED_SCHEMA_VERSION)

elif current_version > REQUIRED_SCHEMA_VERSION:
    raise FatalError(
        f"Database schema v{current_version} > daemon supports v{REQUIRED_SCHEMA_VERSION}\n"
        f"Upgrade daemon to latest version or restore database backup"
    )

else:
    print(f"✓ Database schema v{current_version} (current)")
```

---

## Initial Population

### Marking Existing Databases as v1

**For databases created before schema_version table existed:**

```python
def initialize_schema_versioning(db: sqlite3.Connection):
    """Add schema_version table to existing v1 database."""

    # Create schema_version table
    db.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL,
            description TEXT NOT NULL,
            migration_script TEXT,
            rollback_script TEXT,
            execution_time_ms INTEGER,
            success BOOLEAN NOT NULL DEFAULT 1,
            error_message TEXT
        )
    """)

    # Mark as version 1 (baseline)
    db.execute("""
        INSERT OR IGNORE INTO schema_version (version, applied_at, description, success)
        VALUES (1, ?, 'Baseline schema - 9 tables', 1)
    """, (datetime.utcnow().isoformat() + 'Z',))

    db.commit()
```

---

## Configuration

### Migration Settings

**In `config/database.yaml`:**

```yaml
database:
  path: "data/state.db"

  # Schema versioning
  schema:
    current_version: 2  # Expected schema version
    auto_migrate: true  # Automatically run migrations on startup
    backup_before_migrate: true  # Create backup before migration

  # Backup settings
  backup:
    directory: "data/backups"
    retention_days: 30  # Keep backups for 30 days
    max_backups: 10     # Keep at most 10 backups
```

---

## Monitoring & Alerts

### Schema Version Monitoring

**Metrics to track:**
- Current schema version
- Last migration date
- Failed migration count
- Schema version mismatches (if multi-instance)

**Alerts:**
- Alert if migration fails
- Alert if schema version mismatch detected
- Alert if database backup fails before migration

**Logging:**
```python
logger.info(f"Database schema version: {current_version}")
logger.info(f"Last migration: {last_migration_date}")

if current_version < REQUIRED_SCHEMA_VERSION:
    logger.warning(f"Schema upgrade required: v{current_version} -> v{REQUIRED_SCHEMA_VERSION}")
```

---

## Testing Requirements

### Unit Tests

**Test Cases:**
1. ✅ Create schema_version table successfully
2. ✅ Insert version 1 record correctly
3. ✅ Get current schema version (v1 and v2+)
4. ✅ Detect schema version mismatches
5. ✅ Record failed migrations correctly
6. ✅ Transaction rollback on migration failure

### Integration Tests

**Test Scenarios:**
1. ✅ Fresh database initialization (no schema_version table)
2. ✅ Migrate v1 -> v2 successfully
3. ✅ Migrate v1 -> v2 with simulated failure (rollback)
4. ✅ Attempt duplicate migration (should fail)
5. ✅ Daemon startup with older schema (auto-migrate)
6. ✅ Daemon startup with newer schema (fatal error)

### Migration Testing Checklist

Before deploying any migration:
- [ ] Backup created successfully
- [ ] Migration runs without errors on test database
- [ ] Rollback script tested (if applicable)
- [ ] Daemon starts successfully after migration
- [ ] All existing functionality works after migration
- [ ] New functionality works as expected
- [ ] Performance impact measured (should be negligible)
- [ ] Documentation updated

---

## Performance Impact

### Storage Impact

**schema_version table:**
- ~1 record per migration
- ~200 bytes per record
- Expected: <10 KB for 50 migrations

**Total Overhead:** Negligible (<0.001% of database)

### Query Performance

**Schema version check on startup:**
- 1 query: `SELECT MAX(version) FROM schema_version WHERE success = 1`
- Expected: <1ms (table will be tiny)
- **Impact:** None

---

## Security Considerations

### Migration Script Storage

**Risks:**
- Migration scripts stored in database contain schema details
- Could reveal internal structure to attackers

**Mitigations:**
- Database file permissions: `chmod 600 data/state.db`
- No network access to database (local SQLite only)
- Encryption at rest recommended for production

### Rollback Script Storage

**Risks:**
- Rollback scripts could be abused to intentionally corrupt database

**Mitigations:**
- Only admin users can access database file
- Daemon runs as non-root user with limited permissions
- Audit trail of all migrations (success and failure)

---

## Implementation Checklist

### Phase 1: Schema Creation
- [ ] Create `schema_version` table in migration script
- [ ] Add indexes (`idx_schema_version_applied`)
- [ ] Write table creation SQL

### Phase 2: Migration Logic
- [ ] Implement `get_current_schema_version()`
- [ ] Implement `apply_migration()`
- [ ] Implement backup creation before migration
- [ ] Implement transaction-based migration
- [ ] Implement rollback on failure

### Phase 3: Daemon Integration
- [ ] Add schema version check to daemon startup
- [ ] Add auto-migration support
- [ ] Add version mismatch error handling
- [ ] Add logging for schema operations

### Phase 4: Testing
- [ ] Write unit tests for migration functions
- [ ] Write integration tests for v1 -> v2 migration
- [ ] Test rollback scenarios
- [ ] Test version mismatch handling

### Phase 5: Documentation
- [ ] Document migration process
- [ ] Document rollback procedures
- [ ] Update DATABASE_SCHEMA.md with schema_version table
- [ ] Create migration guide for developers

---

## Validation Criteria

**Success Criteria:**
- ✅ schema_version table created successfully
- ✅ Baseline schema (v1) can be marked retroactively
- ✅ Migrations execute in transactions (atomic)
- ✅ Failed migrations recorded with error messages
- ✅ Daemon detects schema version mismatches
- ✅ Auto-migration works on daemon startup
- ✅ Rollback restores database to previous state
- ✅ No performance degradation from version checks

**Validation Queries:**
```sql
-- Verify schema_version table exists
SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version';

-- Verify current version
SELECT version, applied_at, description, success
FROM schema_version
ORDER BY version DESC
LIMIT 1;

-- Check for failed migrations
SELECT version, applied_at, error_message
FROM schema_version
WHERE success = 0;
```

---

## References

**Source Documents:**
- `/docs/ERRORS_AND_WARNINGS_CONSOLIDATED.md` (REC-DM-001, line 77-80)
- `/project-specs/SPECS/07-DATA-MODELS/DATABASE_SCHEMA.md` (v1 schema)

**Related Specifications:**
- `ANALYTICS_INDEXES_SPEC.md` (REC-DM-004)
- `DATACLASS_ENHANCEMENTS_SPEC.md` (GAP-DM-002, GAP-DM-003)
- `SCHEMA_MIGRATION_STRATEGY_SPEC.md` (overall migration strategy)

**External References:**
- SQLite Schema Versioning: https://www.sqlite.org/pragma.html#pragma_user_version
- Database Migration Best Practices: https://martinfowler.com/articles/evodb.html

---

**Document Status:** DRAFT - Ready for Implementation
**Next Steps:** Review by tech lead, then implement in Phase 1 (MVP)
