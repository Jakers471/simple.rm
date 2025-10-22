# Schema Migration Strategy Specification

**doc_id:** DB-SCHEMA-006
**version:** 2.0
**status:** DRAFT
**addresses:** Overall migration strategy from v1 to v2

---

## Overview

This specification defines the complete migration strategy from database schema v1 (baseline) to v2 (enhancements). It consolidates migration requirements from all schema v2 specifications.

**Purpose:** Provide a comprehensive, step-by-step migration plan with backup, verification, and rollback procedures.

---

## Migration Scope

### Schema v1 → v2 Changes

**New Tables:**
| Table | Purpose | Priority | Spec Reference |
|-------|---------|----------|----------------|
| `schema_version` | Track database migrations | **Required** | DB-SCHEMA-001 |
| `daily_unrealized_pnl` | Historical unrealized P&L snapshots | **Optional** | DB-SCHEMA-002 |

**New Columns:**
| Table | Column | Type | Purpose | Spec Reference |
|-------|--------|------|---------|----------------|
| `enforcement_log` | `execution_time_ms` | INTEGER | Performance tracking | DB-SCHEMA-003 |

**New Indexes:**
| Index | Table | Columns | Purpose | Spec Reference |
|-------|-------|---------|---------|----------------|
| `idx_enforcement_log_success` | `enforcement_log` | `(success, timestamp DESC)` | Failure analysis | DB-SCHEMA-005 |
| `idx_positions_updated` | `positions` | `(updated_at DESC)` | Recent updates | DB-SCHEMA-005 |
| `idx_orders_state_account` | `orders` | `(state, account_id)` | Account orders by state | DB-SCHEMA-005 |
| `idx_daily_unrealized_pnl_date` | `daily_unrealized_pnl` | `(timestamp DESC)` | Date range queries | DB-SCHEMA-002 |
| `idx_daily_unrealized_pnl_account_date` | `daily_unrealized_pnl` | `(account_id, timestamp DESC)` | Account history | DB-SCHEMA-002 |

**Dataclass Enhancements:**
| Dataclass | Change | Purpose | Spec Reference |
|-----------|--------|---------|----------------|
| `OrderType` | Add `TRAILING_STOP = 5` | Future feature support | DB-SCHEMA-003 |
| `EnforcementLog` | Add `execution_time_ms` field | Match database schema | DB-SCHEMA-003 |
| `Order`, `Trade`, `Quote` | Add `__post_init__` validation | Data integrity | DB-SCHEMA-004 |

---

## Migration Phases

### Phase 0: Pre-Migration (Required)

**Duration:** 5-10 minutes

**Steps:**

1. **Stop Daemon**
   ```bash
   ./scripts/stop_daemon.sh
   # Verify daemon stopped:
   ps aux | grep risk_manager_daemon
   # Should return no results
   ```

2. **Verify No Active Connections**
   ```bash
   # Check for SQLite lock files
   ls -la data/state.db-wal data/state.db-shm
   # Should not exist (or be empty)
   ```

3. **Create Backup**
   ```bash
   BACKUP_NAME="state_pre_v2_$(date +%Y%m%d_%H%M%S).db"
   cp data/state.db "data/backups/$BACKUP_NAME"
   echo "Backup created: $BACKUP_NAME"
   ```

4. **Verify Backup Integrity**
   ```bash
   sqlite3 "data/backups/$BACKUP_NAME" "PRAGMA integrity_check;"
   # Expected output: ok
   ```

5. **Verify Backup Size**
   ```bash
   ls -lh data/state.db "data/backups/$BACKUP_NAME"
   # Sizes should match (within a few KB)
   ```

6. **Record Current Schema Version**
   ```bash
   sqlite3 data/state.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;" > /tmp/v1_tables.txt
   cat /tmp/v1_tables.txt
   ```

**Expected v1 Tables:**
```
contract_cache
daily_pnl
enforcement_log
lockouts
orders
positions
reset_schedule
session_state
trade_history
```

---

### Phase 1: Core Migration (Required)

**Duration:** 1-2 seconds

**Purpose:** Add schema_version table and mark v1 baseline.

**Migration SQL:**
```sql
-- migration_v1_to_v2_core.sql
BEGIN TRANSACTION;

-- 1. Create schema_version table
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT NOT NULL,
    migration_script TEXT,
    rollback_script TEXT,
    execution_time_ms INTEGER,
    success BOOLEAN NOT NULL DEFAULT 1,
    error_message TEXT
);

-- 2. Create index
CREATE INDEX IF NOT EXISTS idx_schema_version_applied
ON schema_version(applied_at DESC);

-- 3. Mark v1 as baseline (retroactive)
INSERT INTO schema_version (version, applied_at, description, success)
VALUES (
    1,
    datetime('now'),
    'Baseline schema - 9 tables (lockouts, daily_pnl, contract_cache, trade_history, session_state, positions, orders, enforcement_log, reset_schedule)',
    1
);

-- 4. Mark v2 as in-progress
INSERT INTO schema_version (version, applied_at, description, success)
VALUES (
    2,
    datetime('now'),
    'Schema v2: Add schema_version table, analytics indexes, optional daily_unrealized_pnl table',
    1
);

COMMIT;
```

**Execute:**
```python
def migrate_v1_to_v2_core(db_path: str):
    """Add schema_version table and mark baseline."""
    import sqlite3
    import time

    start_time = time.time()

    with sqlite3.connect(db_path) as db:
        with open('migrations/migration_v1_to_v2_core.sql', 'r') as f:
            migration_sql = f.read()

        try:
            db.executescript(migration_sql)
            elapsed_ms = int((time.time() - start_time) * 1000)
            print(f"✓ Core migration successful ({elapsed_ms}ms)")
            return True

        except Exception as e:
            print(f"✗ Core migration failed: {e}")
            return False
```

**Verification:**
```sql
-- Verify schema_version table created
SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version';
-- Expected: schema_version

-- Verify version records
SELECT version, description, success FROM schema_version ORDER BY version;
-- Expected: 2 rows (v1 baseline, v2 current)
```

---

### Phase 2: Analytics Indexes (Required)

**Duration:** <100ms (for 1000 rows)

**Purpose:** Add performance-optimized indexes.

**Migration SQL:**
```sql
-- migration_v1_to_v2_indexes.sql
BEGIN TRANSACTION;

-- 1. Enforcement log success index (for failure analysis)
CREATE INDEX IF NOT EXISTS idx_enforcement_log_success
ON enforcement_log(success, timestamp DESC);

-- 2. Positions updated_at index (for recent updates)
CREATE INDEX IF NOT EXISTS idx_positions_updated
ON positions(updated_at DESC);

-- 3. Orders state+account composite index (for account queries)
CREATE INDEX IF NOT EXISTS idx_orders_state_account
ON orders(state, account_id);

COMMIT;
```

**Execute:**
```python
def migrate_v1_to_v2_indexes(db_path: str):
    """Add analytics indexes."""
    import sqlite3
    import time

    start_time = time.time()

    with sqlite3.connect(db_path) as db:
        with open('migrations/migration_v1_to_v2_indexes.sql', 'r') as f:
            migration_sql = f.read()

        try:
            db.executescript(migration_sql)
            elapsed_ms = int((time.time() - start_time) * 1000)
            print(f"✓ Analytics indexes created ({elapsed_ms}ms)")
            return True

        except Exception as e:
            print(f"✗ Index creation failed: {e}")
            return False
```

**Verification:**
```sql
-- Verify indexes created
SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY name;

-- Expected indexes (13 total):
-- idx_contract_cache_symbol
-- idx_daily_pnl_date
-- idx_enforcement_account
-- idx_enforcement_log_success       ← NEW
-- idx_enforcement_rule
-- idx_enforcement_timestamp
-- idx_lockouts_until
-- idx_orders_account
-- idx_orders_contract
-- idx_orders_state
-- idx_orders_state_account          ← NEW
-- idx_positions_account
-- idx_positions_contract
-- idx_positions_updated             ← NEW
-- idx_schema_version_applied        ← NEW
-- idx_trade_history_account_time
-- idx_trade_history_timestamp
```

---

### Phase 3: Optional Tables (Optional)

**Duration:** <10ms

**Purpose:** Add daily_unrealized_pnl table for historical tracking.

**Migration SQL:**
```sql
-- migration_v1_to_v2_optional.sql
BEGIN TRANSACTION;

-- 1. Create daily_unrealized_pnl table (optional)
CREATE TABLE IF NOT EXISTS daily_unrealized_pnl (
    account_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,  -- YYYY-MM-DD
    unrealized_pnl REAL NOT NULL,
    positions_count INTEGER NOT NULL,
    total_exposure REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (account_id, timestamp)
);

-- 2. Create indexes
CREATE INDEX IF NOT EXISTS idx_daily_unrealized_pnl_date
ON daily_unrealized_pnl(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_daily_unrealized_pnl_account_date
ON daily_unrealized_pnl(account_id, timestamp DESC);

COMMIT;
```

**Execute:**
```python
def migrate_v1_to_v2_optional(db_path: str, enable_unrealized_pnl: bool = False):
    """Add optional daily_unrealized_pnl table."""
    if not enable_unrealized_pnl:
        print("⊘ Optional daily_unrealized_pnl table skipped (disabled in config)")
        return True

    import sqlite3
    import time

    start_time = time.time()

    with sqlite3.connect(db_path) as db:
        with open('migrations/migration_v1_to_v2_optional.sql', 'r') as f:
            migration_sql = f.read()

        try:
            db.executescript(migration_sql)
            elapsed_ms = int((time.time() - start_time) * 1000)
            print(f"✓ Optional table created ({elapsed_ms}ms)")
            return True

        except Exception as e:
            print(f"✗ Optional table creation failed: {e}")
            return False
```

**Note:** This table is NOT required for RULE-004 (Daily Unrealized Loss) to function. It only provides historical tracking.

---

### Phase 4: Post-Migration Verification (Required)

**Duration:** 1-2 seconds

**Purpose:** Verify migration completed successfully.

**Verification Checks:**

```python
def verify_v2_migration(db_path: str, enable_unrealized_pnl: bool = False):
    """Verify schema v2 migration successful."""
    import sqlite3

    with sqlite3.connect(db_path) as db:
        errors = []

        # 1. Verify schema version = 2
        cursor = db.execute(
            "SELECT MAX(version) FROM schema_version WHERE success = 1"
        )
        version = cursor.fetchone()[0]
        if version != 2:
            errors.append(f"Schema version {version} != 2")

        # 2. Verify all v1 tables still exist
        v1_tables = [
            'lockouts', 'daily_pnl', 'contract_cache', 'trade_history',
            'session_state', 'positions', 'orders', 'enforcement_log',
            'reset_schedule'
        ]
        cursor = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        existing_tables = {row[0] for row in cursor.fetchall()}

        for table in v1_tables:
            if table not in existing_tables:
                errors.append(f"Missing v1 table: {table}")

        # 3. Verify schema_version table exists
        if 'schema_version' not in existing_tables:
            errors.append("Missing schema_version table")

        # 4. Verify optional table (if enabled)
        if enable_unrealized_pnl and 'daily_unrealized_pnl' not in existing_tables:
            errors.append("Missing daily_unrealized_pnl table (enabled in config)")

        # 5. Verify new indexes exist
        required_indexes = [
            'idx_enforcement_log_success',
            'idx_positions_updated',
            'idx_orders_state_account',
            'idx_schema_version_applied'
        ]
        cursor = db.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        existing_indexes = {row[0] for row in cursor.fetchall()}

        for index in required_indexes:
            if index not in existing_indexes:
                errors.append(f"Missing index: {index}")

        # 6. Run integrity check
        cursor = db.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        if integrity != 'ok':
            errors.append(f"Integrity check failed: {integrity}")

        # 7. Verify data integrity (sample queries)
        try:
            db.execute("SELECT COUNT(*) FROM enforcement_log").fetchone()
            db.execute("SELECT COUNT(*) FROM positions").fetchone()
            db.execute("SELECT COUNT(*) FROM orders").fetchone()
        except Exception as e:
            errors.append(f"Sample query failed: {e}")

        if errors:
            print("✗ Migration verification failed:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("✓ Migration verification successful")
            return True
```

**Run Verification:**
```bash
python scripts/verify_v2_migration.py data/state.db
```

---

### Phase 5: Update Code (Required)

**Duration:** N/A (development task)

**Dataclass Updates:**

1. **Update OrderType enum:**
   ```python
   # src/data_models/order.py
   class OrderType(IntEnum):
       MARKET = 1
       LIMIT = 2
       STOP = 3
       STOP_LIMIT = 4
       TRAILING_STOP = 5  # NEW
   ```

2. **Update EnforcementLog dataclass:**
   ```python
   # src/data_models/enforcement_log.py
   @dataclass
   class EnforcementLog:
       # ... existing fields ...
       execution_time_ms: Optional[int] = None  # NEW
   ```

3. **Add validation to Order, Trade, Quote:**
   ```python
   # See DB-SCHEMA-004 for complete validation specs
   def __post_init__(self):
       """Validate fields after initialization."""
       # ... validation logic ...
   ```

**Enforcement Execution Update:**
```python
# src/modules/enforcement_actions.py
def execute_enforcement(action: EnforcementAction):
    start_time = time.time()

    # ... execute action ...

    # NEW: Track execution time
    execution_time_ms = int((time.time() - start_time) * 1000)

    log = EnforcementLog(
        # ... fields ...
        execution_time_ms=execution_time_ms  # NEW
    )
    save_log(log)
```

---

### Phase 6: Restart Daemon (Required)

**Duration:** <5 seconds

**Steps:**

1. **Start Daemon**
   ```bash
   ./scripts/start_daemon.sh
   ```

2. **Verify Startup Logs**
   ```bash
   tail -f logs/daemon.log
   # Expected:
   # INFO: Database schema version: 2
   # INFO: Loaded 10 positions
   # INFO: Loaded 5 orders
   # INFO: Daemon started successfully
   ```

3. **Verify Schema Version Check**
   ```python
   # Daemon startup should log:
   current_version = get_current_schema_version(db)
   print(f"✓ Database schema v{current_version} (current)")
   ```

4. **Run Smoke Tests**
   ```bash
   # Test basic daemon operations
   python scripts/smoke_tests.py
   ```

---

## Rollback Procedures

### Scenario 1: Migration Failed Mid-Execution

**Symptom:** Migration script returned error.

**Action:** Transaction automatically rolled back (no changes applied).

**Steps:**
1. Verify no changes:
   ```sql
   SELECT name FROM sqlite_master WHERE name='schema_version';
   -- Should return no rows (or empty)
   ```

2. Fix migration script error

3. Re-run migration

### Scenario 2: Migration Succeeded but Daemon Won't Start

**Symptom:** Daemon crashes on startup after migration.

**Action:** Restore from backup.

**Steps:**

1. **Stop Daemon** (if running)
   ```bash
   ./scripts/stop_daemon.sh
   ```

2. **Rename Failed Database**
   ```bash
   mv data/state.db data/state.db.failed_v2_$(date +%Y%m%d_%H%M%S)
   ```

3. **Restore Backup**
   ```bash
   BACKUP_NAME="state_pre_v2_YYYYMMDD_HHMMSS.db"  # Use actual backup name
   cp "data/backups/$BACKUP_NAME" data/state.db
   ```

4. **Verify Restore**
   ```sql
   sqlite3 data/state.db "PRAGMA integrity_check;"
   # Expected: ok

   sqlite3 data/state.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
   # Should NOT include schema_version (v1 schema)
   ```

5. **Restart Daemon (v1)**
   ```bash
   ./scripts/start_daemon.sh
   # Should start successfully with v1 schema
   ```

6. **Investigate Issue**
   - Review daemon crash logs
   - Check for code/schema mismatch
   - Fix code, then retry migration

### Scenario 3: Migration Succeeded but Runtime Errors

**Symptom:** Daemon runs but errors occur during normal operation.

**Action:** Rollback if errors critical, otherwise fix forward.

**Decision Tree:**

```
Are errors blocking critical functionality? (position tracking, enforcement)
  YES → Rollback to v1 (follow Scenario 2)
  NO → Fix forward (patch code, deploy update)

Are errors related to new v2 features?
  YES → Disable feature, continue with v1 functionality
  NO → Investigate root cause
```

**Example: Optional Table Causing Errors**
```python
# Disable daily_unrealized_pnl tracking
config['database']['track_unrealized_pnl'] = False
# Daemon continues working, table just not used
```

---

## Testing Strategy

### Unit Tests

**Test Migration Scripts:**
```python
def test_migration_v1_to_v2_idempotent():
    """Migration should be idempotent (can run multiple times)."""
    db = create_test_db_v1()

    # Run migration twice
    assert migrate_v1_to_v2(db) == True
    assert migrate_v1_to_v2(db) == True  # Should not error

    # Verify schema still v2
    assert get_current_schema_version(db) == 2
```

### Integration Tests

**Test Full Migration:**
```python
def test_full_migration_v1_to_v2():
    """Test complete v1 → v2 migration."""
    # 1. Create v1 database with sample data
    db = create_test_db_v1()
    insert_sample_data_v1(db)

    # 2. Backup
    backup_path = backup_database(db)

    # 3. Migrate
    assert migrate_v1_to_v2_core(db) == True
    assert migrate_v1_to_v2_indexes(db) == True

    # 4. Verify
    assert verify_v2_migration(db) == True

    # 5. Verify data integrity
    assert verify_data_preserved(db, backup_path) == True
```

**Test Rollback:**
```python
def test_rollback_from_v2_to_v1():
    """Test rollback from v2 to v1."""
    # 1. Create v2 database
    db = create_test_db_v2()

    # 2. Backup v1 snapshot
    v1_backup = create_test_db_v1()

    # 3. Restore from v1 backup
    restore_database(db, v1_backup)

    # 4. Verify v1 schema
    assert get_current_schema_version(db) == 1
```

---

## Production Deployment

### Deployment Checklist

**Pre-Deployment:**
- [ ] All migration scripts tested in dev/staging
- [ ] Rollback procedure tested
- [ ] Backup retention verified (30 days minimum)
- [ ] Downtime window scheduled (5-10 minutes)
- [ ] Team on-call for migration window

**During Migration:**
- [ ] Stop daemon
- [ ] Create backup
- [ ] Verify backup integrity
- [ ] Run migration scripts (Phase 1, 2, 3)
- [ ] Run verification (Phase 4)
- [ ] Update daemon code (Phase 5)
- [ ] Restart daemon (Phase 6)
- [ ] Monitor logs for 10 minutes

**Post-Migration:**
- [ ] Verify all risk rules functional
- [ ] Run smoke tests
- [ ] Monitor performance (query times)
- [ ] Check enforcement actions execute correctly
- [ ] Verify no data loss

**Rollback Conditions:**
- Migration fails verification
- Daemon won't start after migration
- Critical errors within 10 minutes of restart
- Data integrity check fails

---

## Configuration

### Migration Settings

**In `config/database.yaml`:**
```yaml
database:
  path: "data/state.db"

  # Schema versioning
  schema:
    current_version: 2
    auto_migrate: true  # Auto-migrate on daemon startup

  # Optional features (v2)
  track_unrealized_pnl: false  # daily_unrealized_pnl table

  # Backup
  backup:
    directory: "data/backups"
    retention_days: 30
    max_backups: 10

  # Migration behavior
  migration:
    require_confirmation: true  # Prompt before migration
    create_backup: true         # Always backup before migration
    verify_after: true          # Run verification after migration
```

---

## References

**Source Documents:**
- `SCHEMA_VERSION_TABLE_SPEC.md` (DB-SCHEMA-001)
- `DAILY_UNREALIZED_PNL_TABLE_SPEC.md` (DB-SCHEMA-002)
- `DATACLASS_ENHANCEMENTS_SPEC.md` (DB-SCHEMA-003)
- `FIELD_VALIDATION_SPEC.md` (DB-SCHEMA-004)
- `ANALYTICS_INDEXES_SPEC.md` (DB-SCHEMA-005)
- `/docs/ERRORS_AND_WARNINGS_CONSOLIDATED.md` (all REC-DM and GAP-DM issues)

**Related Documentation:**
- `/project-specs/SPECS/07-DATA-MODELS/DATABASE_SCHEMA.md` (v1 schema)
- `/project-specs/SPECS/07-DATA-MODELS/STATE_OBJECTS.md` (dataclasses)

---

**Document Status:** DRAFT - Complete Migration Guide
**Next Steps:** Review by tech lead, test in dev/staging, deploy to production
