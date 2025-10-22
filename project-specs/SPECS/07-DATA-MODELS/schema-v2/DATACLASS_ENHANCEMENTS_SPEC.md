# Dataclass Enhancements Specification

**doc_id:** DB-SCHEMA-003
**version:** 2.0
**status:** DRAFT
**addresses:** GAP-DM-002, GAP-DM-003 from ERRORS_AND_WARNINGS_CONSOLIDATED.md

---

## Overview

This specification defines enhancements to existing dataclasses to fix gaps identified in the error analysis. Specifically:
- **GAP-DM-002:** Add `TRAILING_STOP = 5` to `OrderType` enum
- **GAP-DM-003:** Add `execution_time_ms` field to `EnforcementLog` dataclass

**Purpose:** Ensure dataclasses match database schema and support future features (trailing stop orders, performance monitoring).

---

## Gap Analysis

### GAP-DM-002: Missing OrderType.TRAILING_STOP

**From ERRORS_AND_WARNINGS_CONSOLIDATED.md (line 58-63):**
> **GAP-DM-002: Missing Enum - `TrailingStop` in OrderType**
> - **Location:** State Objects `OrderType` enum
> - **Description:** Database schema mentions `OrderType=5 (TrailingStop)` on line 353, but State Objects only define 4 order types
> - **Impact:** Low - spec mentions it but not implemented yet
> - **Recommendation:** Add `TRAILING_STOP = 5` to OrderType enum

**Current State (v1):**
```python
class OrderType(IntEnum):
    """Order type"""
    MARKET = 1
    LIMIT = 2
    STOP = 3
    STOP_LIMIT = 4
```

**Issue:** Database schema (line 353) mentions `OrderType=5 (TrailingStop)` but enum doesn't define it.

### GAP-DM-003: Missing execution_time_ms Field

**From ERRORS_AND_WARNINGS_CONSOLIDATED.md (line 65-71):**
> **GAP-DM-003: Missing Field - `execution_time_ms` in EnforcementLog**
> - **Location:** EnforcementLog dataclass
> - **Description:** Database schema (line 404) defines `execution_time_ms` field, but EnforcementLog dataclass doesn't include it
> - **Impact:** Low - performance tracking, not critical for functionality
> - **Recommendation:** Add `execution_time_ms: Optional[int] = None` to dataclass

**Current State (v1):**
```python
@dataclass
class EnforcementLog:
    id: Optional[int] = None
    account_id: int = 0
    rule_id: str = ""
    action: str = ""
    reason: str = ""
    success: bool = False
    error_message: Optional[str] = None
    positions_closed: int = 0
    orders_canceled: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    # Missing: execution_time_ms
```

**Issue:** Database table has `execution_time_ms INTEGER` column (line 404) but dataclass doesn't.

---

## Schema Changes from v1

### Modified Enums

| Enum | Change | Reason |
|------|--------|--------|
| `OrderType` | Add `TRAILING_STOP = 5` | Match database schema, support future feature |

### Modified Dataclasses

| Dataclass | Change | Reason |
|-----------|--------|--------|
| `EnforcementLog` | Add `execution_time_ms` field | Match database schema, enable performance monitoring |

### Database Schema Changes

**No database changes required** - these are dataclass enhancements to match existing schema definitions.

---

## Enhancement 1: OrderType.TRAILING_STOP

### Updated OrderType Enum

**File:** `src/data_models/order.py`

**Before (v1):**
```python
class OrderType(IntEnum):
    """Order type"""
    MARKET = 1
    LIMIT = 2
    STOP = 3
    STOP_LIMIT = 4
```

**After (v2):**
```python
class OrderType(IntEnum):
    """Order type"""
    MARKET = 1
    LIMIT = 2
    STOP = 3
    STOP_LIMIT = 4
    TRAILING_STOP = 5  # NEW: Trailing stop-loss order
```

### Trailing Stop Order Behavior

**What is a Trailing Stop?**
- Stop-loss order that automatically adjusts as price moves favorably
- Trails price by fixed amount (e.g., $10 behind)
- Protects profits while allowing position to run

**Example:**
```python
# Buy MNQ at 21000, set trailing stop $10 behind
order = Order(
    id=123,
    account_id=456,
    contract_id="CON.F.US.MNQ.U25",
    type=OrderType.TRAILING_STOP,  # NEW
    side=OrderSide.SELL,
    size=1,
    stop_price=20990.00,  # Initial stop price ($10 below entry)
    state=OrderState.ACTIVE
)

# As MNQ rises to 21050, stop trails to 21040
# As MNQ rises to 21100, stop trails to 21090
# If MNQ drops to 21090, stop triggers (sell)
```

**TopstepX API Support:**
- Check if `/api/Order/placeOrder` supports `type=5` (TRAILING_STOP)
- May require additional field: `trailingAmount` or `trailingPercent`

**Database Storage:**
```sql
-- Trailing stop orders stored in orders table
INSERT INTO orders (id, account_id, contract_id, type, side, size, stop_price, state)
VALUES (123, 456, 'CON.F.US.MNQ.U25', 5, 1, 1, 20990.00, 2);
--                                      ↑
--                                   type=5 (TRAILING_STOP)
```

### Order Dataclass Updates

**Add validation for trailing stop orders:**

```python
@dataclass
class Order:
    # ... existing fields ...
    type: OrderType
    stop_price: Optional[float] = None
    trailing_amount: Optional[float] = None  # NEW: Trailing distance

    def __post_init__(self):
        """Validate order after initialization."""
        # Existing validations...

        # NEW: Validate trailing stop orders
        if self.type == OrderType.TRAILING_STOP:
            if self.stop_price is None:
                raise ValueError("Trailing stop order must have stop_price")
            if self.trailing_amount is None:
                raise ValueError("Trailing stop order must have trailing_amount")
```

### Impact on Risk Rules

**No immediate impact** - trailing stop orders are future feature, not currently used by any rules.

**Potential Future Use:**
- RULE-008 (No Stop Loss Grace): Could auto-place trailing stops
- RULE-012 (Trade Management): Could enforce trailing stop requirements

---

## Enhancement 2: EnforcementLog.execution_time_ms

### Updated EnforcementLog Dataclass

**File:** `src/data_models/enforcement_log.py`

**Before (v1):**
```python
@dataclass
class EnforcementLog:
    id: Optional[int] = None
    account_id: int = 0
    rule_id: str = ""
    action: str = ""
    reason: str = ""
    success: bool = False
    error_message: Optional[str] = None
    positions_closed: int = 0
    orders_canceled: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
```

**After (v2):**
```python
@dataclass
class EnforcementLog:
    id: Optional[int] = None
    account_id: int = 0
    rule_id: str = ""
    action: str = ""
    reason: str = ""
    success: bool = False
    error_message: Optional[str] = None
    positions_closed: int = 0
    orders_canceled: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time_ms: Optional[int] = None  # NEW: Performance tracking
```

### Purpose: Performance Monitoring

**What is tracked:**
- Time taken to execute enforcement action (in milliseconds)
- Includes time to:
  - Close positions via API
  - Cancel orders via API
  - Set lockout in database
  - Log action to database

**Example:**
```python
# Enforcement action execution
start_time = time.time()

# Close all positions
for position in positions:
    api.close_position(position.id)

# Cancel all orders
for order in orders:
    api.cancel_order(order.id)

# Set lockout
lockout_manager.set_lockout(account_id, reason)

# Log action with execution time
execution_time_ms = int((time.time() - start_time) * 1000)
log = EnforcementLog(
    account_id=account_id,
    rule_id="RULE-003",
    action="CLOSE_ALL_AND_LOCKOUT",
    reason="Daily loss limit hit: -$550",
    success=True,
    positions_closed=2,
    orders_canceled=1,
    execution_time_ms=execution_time_ms  # NEW: 145ms
)
```

### Database Storage

**Already defined in schema (line 404):**
```sql
CREATE TABLE enforcement_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    account_id INTEGER NOT NULL,
    rule_id TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL,
    success BOOLEAN NOT NULL DEFAULT 1,
    details TEXT,
    execution_time_ms INTEGER  -- Already exists in v1 schema
);
```

**Insert with execution time:**
```python
db.execute("""
    INSERT INTO enforcement_log
    (account_id, rule_id, action, reason, success, positions_closed,
     orders_canceled, execution_time_ms)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    log.account_id,
    log.rule_id,
    log.action,
    log.reason,
    log.success,
    log.positions_closed,
    log.orders_canceled,
    log.execution_time_ms  # NEW field
))
```

### Performance Analytics

**Queries enabled by this field:**

**1. Average enforcement time by rule:**
```sql
SELECT
    rule_id,
    AVG(execution_time_ms) as avg_time_ms,
    MIN(execution_time_ms) as min_time_ms,
    MAX(execution_time_ms) as max_time_ms,
    COUNT(*) as enforcement_count
FROM enforcement_log
WHERE success = 1
  AND execution_time_ms IS NOT NULL
GROUP BY rule_id
ORDER BY avg_time_ms DESC;
```

**2. Slow enforcements (>1 second):**
```sql
SELECT
    timestamp,
    account_id,
    rule_id,
    action,
    execution_time_ms,
    positions_closed,
    orders_canceled
FROM enforcement_log
WHERE execution_time_ms > 1000  -- >1 second
ORDER BY execution_time_ms DESC
LIMIT 10;
```

**3. Enforcement time trend (last 7 days):**
```sql
SELECT
    DATE(timestamp) as date,
    AVG(execution_time_ms) as avg_time_ms,
    COUNT(*) as enforcement_count
FROM enforcement_log
WHERE success = 1
  AND execution_time_ms IS NOT NULL
  AND timestamp >= datetime('now', '-7 days')
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

### Alerting Thresholds

**Performance alerts:**
- ⚠️ Warning: Enforcement takes >500ms
- 🚨 Critical: Enforcement takes >2000ms (2 seconds)
- 🚨 Failure: Enforcement times out (>5 seconds)

**Why this matters:**
- Fast enforcement = less slippage during breach
- Slow enforcement = potential for greater losses
- Timeout = enforcement failed, position still open

**Monitoring:**
```python
if log.execution_time_ms and log.execution_time_ms > 2000:
    logger.warning(
        f"Slow enforcement: {log.rule_id} took {log.execution_time_ms}ms "
        f"(account={log.account_id}, positions={log.positions_closed})"
    )
```

---

## Migration from v1 to v2

### No Database Migration Needed

**Why:**
- `OrderType.TRAILING_STOP` is enum change (code only)
- `execution_time_ms` already exists in database schema (line 404)

**What's changing:**
- Dataclass definitions updated to match existing schema
- No SQL changes required

### Code Migration

**1. Update OrderType Enum:**
```python
# Before
class OrderType(IntEnum):
    MARKET = 1
    LIMIT = 2
    STOP = 3
    STOP_LIMIT = 4

# After
class OrderType(IntEnum):
    MARKET = 1
    LIMIT = 2
    STOP = 3
    STOP_LIMIT = 4
    TRAILING_STOP = 5  # NEW
```

**2. Update EnforcementLog Dataclass:**
```python
# Before
@dataclass
class EnforcementLog:
    # ... fields ...
    timestamp: datetime = field(default_factory=datetime.now)

# After
@dataclass
class EnforcementLog:
    # ... fields ...
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time_ms: Optional[int] = None  # NEW
```

**3. Update Enforcement Action Execution:**
```python
# Before
def execute_enforcement(action: EnforcementAction):
    # ... execute action ...
    log = EnforcementLog(...)
    save_log(log)

# After
def execute_enforcement(action: EnforcementAction):
    start_time = time.time()

    # ... execute action ...

    execution_time_ms = int((time.time() - start_time) * 1000)
    log = EnforcementLog(..., execution_time_ms=execution_time_ms)
    save_log(log)
```

---

## Backward Compatibility

### OrderType.TRAILING_STOP

**Backward Compatible:** YES
- Existing code reads/writes OrderType 1-4 unchanged
- New OrderType.TRAILING_STOP (5) is additive
- No breaking changes to existing orders

**TopstepX API Compatibility:**
- Need to verify API supports `type=5` (TRAILING_STOP)
- If not supported, orders with `type=5` will be rejected
- Recommendation: Test in sandbox environment first

### EnforcementLog.execution_time_ms

**Backward Compatible:** YES
- Field is `Optional[int] = None` (nullable)
- Existing logs without `execution_time_ms` still load correctly
- New logs can optionally include `execution_time_ms`
- Database column already exists (no migration needed)

**Reading Old Logs:**
```python
# Old logs (created before v2)
log = EnforcementLog.from_db_row((1, 123, 'RULE-003', ..., None))
# execution_time_ms = None (acceptable)

# New logs (created in v2)
log = EnforcementLog.from_db_row((2, 123, 'RULE-003', ..., 145))
# execution_time_ms = 145 (ms)
```

---

## Configuration

### No Configuration Changes

These enhancements require no configuration:
- OrderType enum is code-only
- execution_time_ms is automatically tracked (opt-in)

**Optional:** Enable performance alerting in config:
```yaml
monitoring:
  enforcement:
    slow_threshold_ms: 500   # Warn if >500ms
    critical_threshold_ms: 2000  # Alert if >2s
    timeout_ms: 5000  # Fail if >5s
```

---

## Testing Requirements

### Unit Tests

**OrderType.TRAILING_STOP:**
1. ✅ Create order with `type=TRAILING_STOP`
2. ✅ Validate trailing stop requires `stop_price`
3. ✅ Validate trailing stop requires `trailing_amount`
4. ✅ Serialize/deserialize trailing stop order
5. ✅ Database stores `type=5` correctly

**EnforcementLog.execution_time_ms:**
1. ✅ Create log with `execution_time_ms=145`
2. ✅ Create log without `execution_time_ms` (None)
3. ✅ Read old logs (execution_time_ms=None)
4. ✅ Query average execution time per rule
5. ✅ Alert on slow enforcements (>2s)

### Integration Tests

**OrderType.TRAILING_STOP:**
1. ✅ Place trailing stop order via API (if supported)
2. ✅ Receive trailing stop order event from SignalR
3. ✅ Store trailing stop order in database
4. ✅ Reload trailing stop order on daemon restart

**EnforcementLog.execution_time_ms:**
1. ✅ Execute enforcement action
2. ✅ Verify `execution_time_ms` recorded accurately
3. ✅ Query slow enforcements (>500ms)
4. ✅ Alert triggers for critical slow enforcements (>2s)

---

## Performance Impact

### OrderType.TRAILING_STOP

**Storage:** No impact (enum value stored as INTEGER)

**Query Performance:** No impact (indexed on `type` already)

**API Impact:** Unknown - depends on TopstepX API support

### EnforcementLog.execution_time_ms

**Storage:** +4 bytes per enforcement log (INTEGER column)

**Query Performance:**
- No impact on writes (<1ms overhead to record time)
- New analytics queries possible (avg time, slow enforcements)

**Overhead:** Negligible (<1% of enforcement time)

---

## Implementation Checklist

### Phase 1: Enum Enhancement
- [ ] Add `TRAILING_STOP = 5` to OrderType enum
- [ ] Update Order dataclass validation for trailing stops
- [ ] Add `trailing_amount` field to Order dataclass
- [ ] Test trailing stop order creation

### Phase 2: Dataclass Enhancement
- [ ] Add `execution_time_ms` field to EnforcementLog
- [ ] Update enforcement execution to track time
- [ ] Update `to_dict()` method
- [ ] Update `from_db_row()` method

### Phase 3: Testing
- [ ] Write unit tests for OrderType.TRAILING_STOP
- [ ] Write unit tests for EnforcementLog.execution_time_ms
- [ ] Test backward compatibility (read old logs)
- [ ] Test performance analytics queries

### Phase 4: Monitoring
- [ ] Add performance alerting for slow enforcements
- [ ] Add analytics dashboard for execution times
- [ ] Document performance thresholds

---

## Validation Criteria

**Success Criteria:**
- ✅ OrderType.TRAILING_STOP defined and functional
- ✅ Order validation works for trailing stops
- ✅ EnforcementLog.execution_time_ms recorded accurately
- ✅ Backward compatibility maintained (old logs load)
- ✅ Performance analytics queries work
- ✅ No breaking changes to existing code

**Validation Queries:**
```python
# Test OrderType.TRAILING_STOP
assert OrderType.TRAILING_STOP == 5
assert OrderType.TRAILING_STOP in OrderType.__members__.values()

# Test EnforcementLog.execution_time_ms
log = EnforcementLog(
    account_id=123,
    rule_id="RULE-003",
    action="CLOSE_ALL",
    reason="Test",
    success=True,
    execution_time_ms=145
)
assert log.execution_time_ms == 145

# Test backward compatibility
old_log = EnforcementLog(
    account_id=123,
    rule_id="RULE-003",
    action="CLOSE_ALL",
    reason="Test",
    success=True
    # No execution_time_ms
)
assert old_log.execution_time_ms is None  # Default value
```

---

## References

**Source Documents:**
- `/docs/ERRORS_AND_WARNINGS_CONSOLIDATED.md` (GAP-DM-002, line 58-63; GAP-DM-003, line 65-71)
- `/project-specs/SPECS/07-DATA-MODELS/DATABASE_SCHEMA.md` (lines 353, 404)
- `/project-specs/SPECS/07-DATA-MODELS/STATE_OBJECTS.md` (OrderType, EnforcementLog)

**Related Specifications:**
- `SCHEMA_VERSION_TABLE_SPEC.md` (DB-SCHEMA-001)
- `FIELD_VALIDATION_SPEC.md` (DB-SCHEMA-004)

---

**Document Status:** DRAFT - Ready for Implementation
**Next Steps:** Implement enum and dataclass changes in Phase 1 (MVP)
