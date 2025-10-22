# Daily Unrealized PNL Table Specification

**doc_id:** DB-SCHEMA-002
**version:** 2.0
**status:** DRAFT
**addresses:** GAP-DM-001 from ERRORS_AND_WARNINGS_CONSOLIDATED.md

---

## Overview

This specification defines the **optional** `daily_unrealized_pnl` table for tracking historical unrealized P&L. This addresses **GAP-DM-001** (LOW priority) which identified a table mentioned in RULE-004 specification but not defined in the database schema.

**Purpose:** Enable historical tracking of daily unrealized P&L for reporting and analytics.

**Priority:** OPTIONAL - RULE-004 can calculate unrealized P&L on-the-fly from current positions and quotes without persistent storage.

---

## Gap Analysis

### Current State (v1)

RULE-004 (Daily Unrealized Loss Limit) specification mentions:
> "Track daily unrealized P&L per account in `daily_unrealized_pnl` table"

However:
- `daily_unrealized_pnl` table does NOT exist in DATABASE_SCHEMA.md
- RULE-004 can function without persistent unrealized P&L history
- Unrealized P&L is calculated on-demand from positions + quotes

### Issue Identified

**From ERRORS_AND_WARNINGS_CONSOLIDATED.md (line 49-55):**
> **GAP-DM-001: Missing Table - `daily_unrealized_pnl`**
> - **Location:** RULE-004 spec (line 254)
> - **Description:** Table mentioned in RULE-004 specification but not defined in database schema
> - **Impact:** Low - RULE-004 can work without persistent unrealized P&L history
> - **Recommendation:** Either add table to schema (for historical tracking) OR remove from spec (calculate on-the-fly from positions + quotes)

---

## Decision

### OPTIONAL TABLE - Historical Tracking Only

**Recommendation:** Implement as optional feature for analytics, but NOT required for RULE-004 functionality.

**Rationale:**
1. **Real-time calculation is sufficient** for rule enforcement
2. **Historical data is nice-to-have** for reporting/analytics
3. **Storage overhead is minimal** (~22 KB/year per account)
4. **Query performance unaffected** by real-time calculation
5. **Simplifies MVP** - can add post-launch if needed

**Decision:** Include table in schema v2, but make it optional with configuration flag.

---

## Schema Changes from v1

### New Tables

| Table | Purpose | Priority |
|-------|---------|----------|
| daily_unrealized_pnl | Track historical unrealized P&L snapshots | **Optional** |

### When to Use This Table

**Use Cases:**
- ✅ Historical reporting (P&L charts over time)
- ✅ Daily P&L analytics (max drawdown, peak unrealized)
- ✅ Performance monitoring (compare days)
- ✅ Debugging (when did unrealized P&L breach occur?)

**NOT Needed For:**
- ❌ Real-time rule enforcement (calculate from current state)
- ❌ RULE-004 breach detection (uses live positions + quotes)
- ❌ Current account status (stored in memory)

---

## Table Specification

### daily_unrealized_pnl

**Purpose:** Historical snapshot of daily unrealized P&L for each account.

**Table Structure:**
```sql
CREATE TABLE daily_unrealized_pnl (
    account_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,  -- ISO8601 date (YYYY-MM-DD)
    unrealized_pnl REAL NOT NULL,
    positions_count INTEGER NOT NULL,
    total_exposure REAL,  -- Sum of position sizes * prices
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (account_id, timestamp)
);

-- Index for date range queries
CREATE INDEX idx_daily_unrealized_pnl_date
ON daily_unrealized_pnl(timestamp DESC);

-- Index for account history queries
CREATE INDEX idx_daily_unrealized_pnl_account_date
ON daily_unrealized_pnl(account_id, timestamp DESC);
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `account_id` | INTEGER | NO | Account ID (foreign key reference) |
| `timestamp` | TEXT | NO | Date of snapshot (YYYY-MM-DD format) |
| `unrealized_pnl` | REAL | NO | Total unrealized P&L at end of day (can be negative) |
| `positions_count` | INTEGER | NO | Number of open positions |
| `total_exposure` | REAL | YES | Total exposure (sum of position notional values) |
| `created_at` | TEXT | NO | When record was created (ISO8601 timestamp) |

**Primary Key:** `(account_id, timestamp)` - ensures one snapshot per account per day

**Constraints:**
- `timestamp` must be date-only (no time component): `YYYY-MM-DD`
- `unrealized_pnl` can be negative (losses)
- `positions_count` must be >= 0

---

## Data Collection Strategy

### Option 1: End-of-Day Snapshot (Recommended)

**When:** Daily at reset time (5:00 PM configured time)

**How:**
1. Daily reset task calculates current unrealized P&L
2. Inserts snapshot into `daily_unrealized_pnl` table
3. Uses current positions + latest quotes

**Pros:**
- Simple implementation (single daily query)
- Consistent snapshot time
- Minimal storage (1 record/account/day)

**Cons:**
- Misses intraday peaks/troughs
- May not capture exact moment of breach

**Implementation:**
```python
def take_daily_unrealized_snapshot(account_id: int, db: sqlite3.Connection):
    """Take end-of-day snapshot of unrealized P&L."""

    # Calculate current unrealized P&L
    positions = state_manager.get_positions(account_id)
    total_unrealized = 0.0
    total_exposure = 0.0

    for position in positions:
        quote = quote_tracker.get_latest_quote(position.contract_id)
        if quote:
            unrealized = calculate_unrealized_pnl(position, quote)
            total_unrealized += unrealized
            total_exposure += abs(position.size * position.average_price)

    # Insert snapshot
    today = datetime.now().date().isoformat()  # YYYY-MM-DD
    db.execute("""
        INSERT OR REPLACE INTO daily_unrealized_pnl
        (account_id, timestamp, unrealized_pnl, positions_count, total_exposure)
        VALUES (?, ?, ?, ?, ?)
    """, (
        account_id,
        today,
        total_unrealized,
        len(positions),
        total_exposure
    ))
    db.commit()
```

### Option 2: Continuous Sampling (Advanced)

**When:** Every 5 minutes during trading hours

**How:**
1. Background task samples unrealized P&L every 5 minutes
2. Stores high-water mark (peak) and low-water mark (trough) per day
3. More granular history for precise breach detection

**Pros:**
- Captures intraday peaks/troughs
- More accurate breach timestamps
- Better for analytics

**Cons:**
- More complex implementation
- Higher storage overhead (~288 records/account/day)
- May require separate table (`unrealized_pnl_samples`)

**Not Recommended for MVP** - use Option 1 (end-of-day snapshot)

---

## Retention Policy

### 7-Day Retention (Default)

**Rationale:**
- Most rules have 1-day scope (daily limits)
- 7 days sufficient for debugging recent breaches
- Keeps storage minimal

**Cleanup Query:**
```sql
DELETE FROM daily_unrealized_pnl
WHERE timestamp < date('now', '-7 days');
```

**Scheduled Cleanup:**
- Run daily at midnight
- Part of existing database cleanup job

### Extended Retention (Optional)

**For analytics/reporting, configure longer retention:**

| Retention | Storage Estimate | Use Case |
|-----------|------------------|----------|
| 7 days | ~22 KB/account | Default (debugging) |
| 30 days | ~95 KB/account | Monthly reporting |
| 90 days | ~280 KB/account | Quarterly analytics |
| 365 days | ~1.1 MB/account | Annual reporting |

**Configuration:**
```yaml
database:
  retention:
    daily_unrealized_pnl: 7  # days (default)
```

---

## Query Patterns

### Recent History

**Get last 7 days of unrealized P&L:**
```sql
SELECT
    timestamp,
    unrealized_pnl,
    positions_count,
    total_exposure
FROM daily_unrealized_pnl
WHERE account_id = ?
  AND timestamp >= date('now', '-7 days')
ORDER BY timestamp DESC;
```

**Expected Performance:** <1ms (indexed on `account_id, timestamp`)

### Peak/Trough Detection

**Find maximum unrealized loss in last 7 days:**
```sql
SELECT
    timestamp,
    MIN(unrealized_pnl) as max_loss,
    positions_count
FROM daily_unrealized_pnl
WHERE account_id = ?
  AND timestamp >= date('now', '-7 days')
GROUP BY account_id;
```

### Date Range Analytics

**Average daily unrealized P&L (last 30 days):**
```sql
SELECT
    AVG(unrealized_pnl) as avg_unrealized,
    MIN(unrealized_pnl) as worst_day,
    MAX(unrealized_pnl) as best_day,
    COUNT(*) as days_tracked
FROM daily_unrealized_pnl
WHERE account_id = ?
  AND timestamp >= date('now', '-30 days');
```

---

## RULE-004 Integration

### RULE-004: Daily Unrealized Loss Limit

**Rule Logic:**
```yaml
RULE-004:
  enabled: true
  loss_limit: -$500
  action: CLOSE_ALL_AND_LOCKOUT
```

**Implementation Options:**

#### Option A: Real-Time Calculation (No Table Needed)
```python
def check_daily_unrealized_loss(account_id: int) -> bool:
    """Check if account breached daily unrealized loss limit."""

    # Calculate current unrealized P&L from live positions + quotes
    positions = state_manager.get_positions(account_id)
    total_unrealized = 0.0

    for position in positions:
        quote = quote_tracker.get_latest_quote(position.contract_id)
        if quote:
            unrealized = calculate_unrealized_pnl(position, quote)
            total_unrealized += unrealized

    # Check breach
    loss_limit = rule_config.get_param('loss_limit')  # -500
    if total_unrealized <= loss_limit:
        return True  # BREACH

    return False
```

**Pros:**
- No database dependency
- Always current (real-time)
- Simplest implementation

**Cons:**
- No historical data
- Cannot debug "when did breach occur?"

#### Option B: Historical Tracking (With Table)
```python
def check_daily_unrealized_loss(account_id: int) -> bool:
    """Check if account breached daily unrealized loss limit."""

    # Calculate current unrealized P&L
    total_unrealized = calculate_current_unrealized_pnl(account_id)

    # Store snapshot for historical tracking (optional)
    store_unrealized_snapshot(account_id, total_unrealized)

    # Check breach
    loss_limit = rule_config.get_param('loss_limit')  # -500
    if total_unrealized <= loss_limit:
        return True  # BREACH

    return False

def store_unrealized_snapshot(account_id: int, unrealized_pnl: float):
    """Store unrealized P&L snapshot (if table enabled)."""
    if not config.get('database.track_unrealized_pnl', False):
        return  # Table disabled

    today = datetime.now().date().isoformat()
    db.execute("""
        INSERT OR REPLACE INTO daily_unrealized_pnl
        (account_id, timestamp, unrealized_pnl, positions_count)
        VALUES (?, ?, ?, ?)
    """, (account_id, today, unrealized_pnl, get_positions_count(account_id)))
    db.commit()
```

**Pros:**
- Historical data for debugging
- Can analyze patterns
- Audit trail of breaches

**Cons:**
- Extra database writes
- More complex

**Recommendation:** Start with Option A (real-time), add Option B post-MVP if needed.

---

## Configuration

### Enable/Disable Historical Tracking

**In `config/database.yaml`:**
```yaml
database:
  # Historical tracking (optional)
  track_unrealized_pnl: false  # default: false (disabled)

  retention:
    daily_unrealized_pnl: 7  # days (if enabled)

  cleanup:
    schedule: "0 2 * * *"  # 2 AM daily
```

**When to Enable:**
- Analytics/reporting dashboard desired
- Historical P&L charts needed
- Debugging frequent breaches
- Performance monitoring over time

**When to Disable (Default):**
- Minimize storage overhead
- Simplify MVP implementation
- RULE-004 works without it

---

## Migration from v1 to v2

### Migration Script

```sql
-- Add daily_unrealized_pnl table (optional)
CREATE TABLE IF NOT EXISTS daily_unrealized_pnl (
    account_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    unrealized_pnl REAL NOT NULL,
    positions_count INTEGER NOT NULL,
    total_exposure REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (account_id, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_daily_unrealized_pnl_date
ON daily_unrealized_pnl(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_daily_unrealized_pnl_account_date
ON daily_unrealized_pnl(account_id, timestamp DESC);
```

**Backfill:** Not required - table starts empty, snapshots begin accumulating from migration date forward.

---

## Performance Impact

### Storage Overhead

**Per Account:**
- 1 record/day × 32 bytes/record = ~11.7 KB/year (365 days)
- With 7-day retention: ~220 bytes per account

**For 10 Accounts:**
- 7-day retention: ~2.2 KB
- 90-day retention: ~28 KB
- 1-year retention: ~117 KB

**Negligible impact** on database size.

### Query Performance

**Snapshot Insert:**
- 1 INSERT per account per day
- Expected: <1ms
- **Impact:** None (happens once daily)

**Historical Query:**
- Indexed on `(account_id, timestamp)`
- 7-day range: <1ms
- 90-day range: <5ms
- **Impact:** None (rare queries)

**RULE-004 Enforcement:**
- No impact (calculates from memory)
- Table is optional for historical tracking only

---

## Dataclass Specification

### DailyUnrealizedPnl (New)

**Purpose:** In-memory representation of daily unrealized P&L snapshot.

**File:** `src/data_models/daily_unrealized_pnl.py`

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class DailyUnrealizedPnl:
    """
    Daily snapshot of unrealized P&L for an account.
    Stored in daily_unrealized_pnl table (optional).
    """

    # Identity
    account_id: int              # Account ID
    timestamp: str               # Date (YYYY-MM-DD)

    # P&L Details
    unrealized_pnl: float        # Total unrealized P&L (can be negative)
    positions_count: int         # Number of open positions
    total_exposure: Optional[float] = None  # Total notional exposure

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'account_id': self.account_id,
            'timestamp': self.timestamp,
            'unrealized_pnl': self.unrealized_pnl,
            'positions_count': self.positions_count,
            'total_exposure': self.total_exposure,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_db_row(cls, row: tuple) -> 'DailyUnrealizedPnl':
        """Create from database row."""
        return cls(
            account_id=row[0],
            timestamp=row[1],
            unrealized_pnl=row[2],
            positions_count=row[3],
            total_exposure=row[4],
            created_at=datetime.fromisoformat(row[5])
        )
```

**Validation:**
- `timestamp` must be date-only (YYYY-MM-DD)
- `unrealized_pnl` can be negative
- `positions_count` must be >= 0

---

## Testing Requirements

### Unit Tests

**Test Cases:**
1. ✅ Create daily_unrealized_pnl table successfully
2. ✅ Insert snapshot with valid data
3. ✅ Prevent duplicate snapshots (same account + date)
4. ✅ Query last 7 days of snapshots
5. ✅ Calculate peak/trough correctly
6. ✅ Cleanup old snapshots (>7 days)

### Integration Tests

**Test Scenarios:**
1. ✅ End-of-day snapshot task runs successfully
2. ✅ Snapshot reflects current positions + quotes
3. ✅ RULE-004 works without table (real-time calculation)
4. ✅ RULE-004 works with table (historical tracking)
5. ✅ Disabled table doesn't block daemon startup

---

## Implementation Checklist

### Phase 1: Table Creation (Optional)
- [ ] Add `daily_unrealized_pnl` table to migration script
- [ ] Add indexes (`idx_daily_unrealized_pnl_date`, `idx_daily_unrealized_pnl_account_date`)
- [ ] Add configuration flag (`track_unrealized_pnl`)

### Phase 2: Snapshot Logic
- [ ] Implement `take_daily_unrealized_snapshot()`
- [ ] Integrate with daily reset task (MOD-004)
- [ ] Add retention cleanup to nightly job

### Phase 3: RULE-004 Integration
- [ ] Implement real-time calculation (Option A)
- [ ] Optionally add historical tracking (Option B)
- [ ] Ensure rule works with table disabled

### Phase 4: Dataclass
- [ ] Implement `DailyUnrealizedPnl` dataclass
- [ ] Add `to_dict()` and `from_db_row()` methods

### Phase 5: Testing
- [ ] Write unit tests for snapshot logic
- [ ] Write integration tests for daily task
- [ ] Test with table disabled (default)
- [ ] Test with table enabled (optional)

---

## Validation Criteria

**Success Criteria:**
- ✅ Table creation succeeds in migration
- ✅ Snapshots inserted correctly at daily reset
- ✅ Retention cleanup removes old snapshots
- ✅ RULE-004 functions correctly (with or without table)
- ✅ Historical queries return accurate data
- ✅ No performance degradation from table

**Validation Queries:**
```sql
-- Verify table exists
SELECT name FROM sqlite_master WHERE type='table' AND name='daily_unrealized_pnl';

-- Check recent snapshots
SELECT account_id, timestamp, unrealized_pnl, positions_count
FROM daily_unrealized_pnl
ORDER BY timestamp DESC
LIMIT 7;

-- Verify retention (no records older than 7 days)
SELECT COUNT(*) FROM daily_unrealized_pnl WHERE timestamp < date('now', '-7 days');
-- Should return 0
```

---

## References

**Source Documents:**
- `/docs/ERRORS_AND_WARNINGS_CONSOLIDATED.md` (GAP-DM-001, line 49-55)
- `/project-specs/SPECS/03-RISK-RULES/rules/04_daily_unrealized_loss.md` (RULE-004)
- `/project-specs/SPECS/07-DATA-MODELS/DATABASE_SCHEMA.md` (v1 schema)

**Related Specifications:**
- `SCHEMA_VERSION_TABLE_SPEC.md` (DB-SCHEMA-001)
- `DATACLASS_ENHANCEMENTS_SPEC.md` (DB-SCHEMA-003)

---

**Document Status:** DRAFT - Optional Feature
**Next Steps:** Review and decide if needed for MVP (recommendation: defer to post-launch)
