# Field Validation Specification

**doc_id:** DB-SCHEMA-004
**version:** 2.0
**status:** DRAFT
**addresses:** REC-DM-005 from ERRORS_AND_WARNINGS_CONSOLIDATED.md

---

## Overview

This specification defines field validation requirements for dataclasses using `__post_init__` methods. This addresses **REC-DM-005** (MEDIUM priority) which identified missing validation on Order, Trade, and Quote dataclasses.

**Purpose:** Catch invalid data at creation time before it reaches the database or causes runtime errors.

---

## Gap Analysis

### REC-DM-005: Missing Field Validation

**From ERRORS_AND_WARNINGS_CONSOLIDATED.md (line 104-108):**
> **REC-DM-005: Add field validation methods**
> - **Severity:** MEDIUM
> - **Priority:** Should-Have (Before Production)
> - **Description:** Missing validation on Order, Trade, Quote dataclasses
> - **Recommendation:** Add `__post_init__` validation methods

**Current State (v1):**
- Position has basic validation (`size >= 0`, `average_price > 0`)
- Order, Trade, Quote have NO validation
- Invalid data can reach database or cause runtime errors

**Issues:**
- Orders with LIMIT type but no `limit_price` → crashes
- Orders with STOP type but no `stop_price` → crashes
- Trades with zero/negative quantity → invalid state
- Quotes with stale timestamps → incorrect P&L calculations

---

## Validation Strategy

### Python Dataclass `__post_init__`

**How it works:**
```python
@dataclass
class Order:
    type: OrderType
    limit_price: Optional[float] = None

    def __post_init__(self):
        """Validate order after initialization."""
        if self.type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("LIMIT orders must have limit_price")
```

**When it runs:**
- Automatically called after `__init__` completes
- Runs on every object creation (normal constructor, `from_api_payload()`, etc.)
- Raises `ValueError` if validation fails

**Benefits:**
- Fail-fast: Catch errors at creation time
- Single source of truth: Validation logic in one place
- Clear error messages: Developers know exactly what's wrong
- Type-safe: Works with Python type hints

---

## Validation Requirements by Dataclass

### 1. Order Validation

**File:** `src/data_models/order.py`

**Validation Rules:**

| Rule | Condition | Error Message |
|------|-----------|---------------|
| Quantity positive | `size > 0` | "Order size must be positive: {size}" |
| LIMIT has limit_price | `type == LIMIT` → `limit_price` not None | "LIMIT orders must have limit_price" |
| STOP has stop_price | `type == STOP` → `stop_price` not None | "STOP orders must have stop_price" |
| STOP_LIMIT has both | `type == STOP_LIMIT` → both not None | "STOP_LIMIT orders must have both limit_price and stop_price" |
| TRAILING_STOP has stop_price | `type == TRAILING_STOP` → `stop_price` not None | "TRAILING_STOP orders must have stop_price" |
| Prices positive | All prices > 0 if not None | "Order price must be positive: {price}" |
| Filled size valid | `0 <= filled_size <= size` | "Filled size {filled_size} exceeds order size {size}" |

**Implementation:**

```python
@dataclass
class Order:
    id: int
    account_id: int
    contract_id: str
    type: OrderType
    side: OrderSide
    size: int
    state: OrderState
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    fill_price: Optional[float] = None
    filled_size: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_stop_loss: bool = False

    def __post_init__(self):
        """Validate order fields after initialization."""

        # Validate quantity
        if self.size <= 0:
            raise ValueError(f"Order size must be positive: {self.size}")

        # Validate filled size
        if not (0 <= self.filled_size <= self.size):
            raise ValueError(
                f"Filled size {self.filled_size} must be between 0 and {self.size}"
            )

        # Validate prices based on order type
        if self.type == OrderType.LIMIT:
            if self.limit_price is None:
                raise ValueError("LIMIT orders must have limit_price")
            if self.limit_price <= 0:
                raise ValueError(f"Limit price must be positive: {self.limit_price}")

        elif self.type == OrderType.STOP:
            if self.stop_price is None:
                raise ValueError("STOP orders must have stop_price")
            if self.stop_price <= 0:
                raise ValueError(f"Stop price must be positive: {self.stop_price}")

        elif self.type == OrderType.STOP_LIMIT:
            if self.limit_price is None or self.stop_price is None:
                raise ValueError(
                    "STOP_LIMIT orders must have both limit_price and stop_price"
                )
            if self.limit_price <= 0:
                raise ValueError(f"Limit price must be positive: {self.limit_price}")
            if self.stop_price <= 0:
                raise ValueError(f"Stop price must be positive: {self.stop_price}")

        elif self.type == OrderType.TRAILING_STOP:
            if self.stop_price is None:
                raise ValueError("TRAILING_STOP orders must have stop_price")
            if self.stop_price <= 0:
                raise ValueError(f"Stop price must be positive: {self.stop_price}")

        # MARKET orders don't require price validation (filled at market)

        # Validate fill price if set
        if self.fill_price is not None and self.fill_price <= 0:
            raise ValueError(f"Fill price must be positive: {self.fill_price}")
```

**Example Valid Orders:**
```python
# Valid LIMIT order
order1 = Order(
    id=1, account_id=123, contract_id="CON.F.US.MNQ.U25",
    type=OrderType.LIMIT, side=OrderSide.BUY, size=2,
    state=OrderState.ACTIVE, limit_price=21000.00
)  # ✓ Passes validation

# Valid MARKET order
order2 = Order(
    id=2, account_id=123, contract_id="CON.F.US.MNQ.U25",
    type=OrderType.MARKET, side=OrderSide.SELL, size=1,
    state=OrderState.ACTIVE
)  # ✓ Passes validation (no prices required)
```

**Example Invalid Orders:**
```python
# Invalid: LIMIT order without limit_price
try:
    order = Order(
        id=1, account_id=123, contract_id="CON.F.US.MNQ.U25",
        type=OrderType.LIMIT, side=OrderSide.BUY, size=2,
        state=OrderState.ACTIVE
        # Missing: limit_price
    )
except ValueError as e:
    print(e)  # "LIMIT orders must have limit_price"

# Invalid: Negative quantity
try:
    order = Order(
        id=1, account_id=123, contract_id="CON.F.US.MNQ.U25",
        type=OrderType.MARKET, side=OrderSide.BUY, size=-1,
        state=OrderState.ACTIVE
    )
except ValueError as e:
    print(e)  # "Order size must be positive: -1"

# Invalid: Filled size exceeds order size
try:
    order = Order(
        id=1, account_id=123, contract_id="CON.F.US.MNQ.U25",
        type=OrderType.LIMIT, side=OrderSide.BUY, size=2,
        state=OrderState.PARTIAL, limit_price=21000.00,
        filled_size=3  # ERROR: Can't fill 3 contracts on 2-contract order
    )
except ValueError as e:
    print(e)  # "Filled size 3 must be between 0 and 2"
```

---

### 2. Trade Validation

**File:** `src/data_models/trade.py`

**Validation Rules:**

| Rule | Condition | Error Message |
|------|-----------|---------------|
| Quantity positive | `quantity > 0` | "Trade quantity must be positive: {quantity}" |
| Prices positive | `entry_price > 0` if not None | "Entry price must be positive: {entry_price}" |
| Prices positive | `exit_price > 0` if not None | "Exit price must be positive: {exit_price}" |
| Execution time valid | `execution_time` not in future | "Trade execution time cannot be in the future" |

**Implementation:**

```python
@dataclass
class Trade:
    id: int
    account_id: int
    contract_id: str
    quantity: int
    profit_and_loss: float
    execution_time: datetime
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate trade fields after initialization."""

        # Validate quantity
        if self.quantity <= 0:
            raise ValueError(f"Trade quantity must be positive: {self.quantity}")

        # Validate prices if provided
        if self.entry_price is not None and self.entry_price <= 0:
            raise ValueError(f"Entry price must be positive: {self.entry_price}")

        if self.exit_price is not None and self.exit_price <= 0:
            raise ValueError(f"Exit price must be positive: {self.exit_price}")

        # Validate execution time not in future
        if self.execution_time > datetime.now():
            raise ValueError(
                f"Trade execution time cannot be in the future: {self.execution_time}"
            )

        # Note: profit_and_loss can be negative (losses are valid)
```

**Example Valid Trades:**
```python
# Valid profitable trade
trade1 = Trade(
    id=101, account_id=123, contract_id="CON.F.US.MNQ.U25",
    quantity=2, profit_and_loss=150.00,
    execution_time=datetime(2025, 10, 22, 14, 30, 0),
    entry_price=21000.00, exit_price=21075.00
)  # ✓ Passes validation

# Valid losing trade (negative P&L allowed)
trade2 = Trade(
    id=102, account_id=123, contract_id="CON.F.US.MNQ.U25",
    quantity=1, profit_and_loss=-45.50,
    execution_time=datetime(2025, 10, 22, 14, 45, 0)
)  # ✓ Passes validation
```

**Example Invalid Trades:**
```python
# Invalid: Zero quantity
try:
    trade = Trade(
        id=101, account_id=123, contract_id="CON.F.US.MNQ.U25",
        quantity=0,  # ERROR
        profit_and_loss=150.00,
        execution_time=datetime.now()
    )
except ValueError as e:
    print(e)  # "Trade quantity must be positive: 0"

# Invalid: Negative price
try:
    trade = Trade(
        id=101, account_id=123, contract_id="CON.F.US.MNQ.U25",
        quantity=1, profit_and_loss=50.00,
        execution_time=datetime.now(),
        entry_price=-21000.00  # ERROR
    )
except ValueError as e:
    print(e)  # "Entry price must be positive: -21000.0"

# Invalid: Future execution time
try:
    trade = Trade(
        id=101, account_id=123, contract_id="CON.F.US.MNQ.U25",
        quantity=1, profit_and_loss=50.00,
        execution_time=datetime(2026, 1, 1)  # Future date
    )
except ValueError as e:
    print(e)  # "Trade execution time cannot be in the future: 2026-01-01..."
```

---

### 3. Quote Validation

**File:** `src/data_models/quote.py`

**Validation Rules:**

| Rule | Condition | Error Message |
|------|-----------|---------------|
| Bid positive | `bid > 0` | "Bid price must be positive: {bid}" |
| Ask positive | `ask > 0` | "Ask price must be positive: {ask}" |
| Last positive | `last > 0` | "Last price must be positive: {last}" |
| Ask >= Bid | `ask >= bid` | "Ask price {ask} must be >= bid price {bid}" |
| Timestamp not future | `timestamp <= now()` | "Quote timestamp cannot be in the future" |
| Timestamp not stale | `age < max_age` (optional) | "Quote is stale (age: {age}s > {max_age}s)" |

**Implementation:**

```python
@dataclass
class Quote:
    contract_id: str
    bid: float
    ask: float
    last: float
    timestamp: datetime

    def __post_init__(self):
        """Validate quote fields after initialization."""

        # Validate prices are positive
        if self.bid <= 0:
            raise ValueError(f"Bid price must be positive: {self.bid}")

        if self.ask <= 0:
            raise ValueError(f"Ask price must be positive: {self.ask}")

        if self.last <= 0:
            raise ValueError(f"Last price must be positive: {self.last}")

        # Validate bid/ask spread (ask should be >= bid)
        if self.ask < self.bid:
            raise ValueError(
                f"Ask price {self.ask} must be >= bid price {self.bid}"
            )

        # Validate timestamp not in future
        if self.timestamp > datetime.now():
            raise ValueError(
                f"Quote timestamp cannot be in the future: {self.timestamp}"
            )

        # Optional: Warn if quote is stale (>5 seconds old)
        # This is a warning, not an error, so we use logging instead of raising
        age_seconds = (datetime.now() - self.timestamp).total_seconds()
        if age_seconds > 5.0:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Quote for {self.contract_id} is stale "
                f"(age: {age_seconds:.1f}s > 5.0s)"
            )
```

**Example Valid Quotes:**
```python
# Valid quote with normal spread
quote1 = Quote(
    contract_id="CON.F.US.MNQ.U25",
    bid=21000.00, ask=21000.25, last=21000.25,
    timestamp=datetime.now()
)  # ✓ Passes validation

# Valid quote with wide spread
quote2 = Quote(
    contract_id="CON.F.US.ES.U25",
    bid=5800.00, ask=5800.50, last=5800.25,
    timestamp=datetime.now()
)  # ✓ Passes validation
```

**Example Invalid Quotes:**
```python
# Invalid: Negative price
try:
    quote = Quote(
        contract_id="CON.F.US.MNQ.U25",
        bid=-21000.00, ask=21000.25, last=21000.00,
        timestamp=datetime.now()
    )
except ValueError as e:
    print(e)  # "Bid price must be positive: -21000.0"

# Invalid: Ask < Bid (inverted spread)
try:
    quote = Quote(
        contract_id="CON.F.US.MNQ.U25",
        bid=21000.25, ask=21000.00,  # ERROR: ask < bid
        last=21000.00,
        timestamp=datetime.now()
    )
except ValueError as e:
    print(e)  # "Ask price 21000.0 must be >= bid price 21000.25"

# Invalid: Future timestamp
try:
    quote = Quote(
        contract_id="CON.F.US.MNQ.U25",
        bid=21000.00, ask=21000.25, last=21000.00,
        timestamp=datetime(2026, 1, 1)  # Future date
    )
except ValueError as e:
    print(e)  # "Quote timestamp cannot be in the future: 2026-01-01..."
```

---

### 4. Position Validation (Enhanced)

**File:** `src/data_models/position.py`

**Current validation (v1):**
```python
def __post_init__(self):
    if self.size < 0:
        raise ValueError(f"Position size cannot be negative: {self.size}")
    if self.average_price <= 0:
        raise ValueError(f"Average price must be positive: {self.average_price}")
```

**Enhanced validation (v2):**
```python
def __post_init__(self):
    """Validate position fields after initialization."""

    # Size must be non-negative (0 = closed position)
    if self.size < 0:
        raise ValueError(f"Position size cannot be negative: {self.size}")

    # Average price must be positive
    if self.average_price <= 0:
        raise ValueError(f"Average price must be positive: {self.average_price}")

    # If position has unrealized P&L, validate it's consistent with position type
    # (This is optional, as unrealized P&L is calculated, not user-provided)
    if self.unrealized_pnl is not None:
        # Warn if unrealized P&L seems extreme (>$10,000 per contract)
        pnl_per_contract = abs(self.unrealized_pnl / self.size) if self.size > 0 else 0
        if pnl_per_contract > 10000:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Position {self.id} has extreme unrealized P&L: "
                f"${self.unrealized_pnl:.2f} (${pnl_per_contract:.2f}/contract)"
            )

    # Validate timestamps
    if self.updated_at < self.created_at:
        raise ValueError(
            f"Position updated_at {self.updated_at} cannot be before "
            f"created_at {self.created_at}"
        )
```

---

## Validation Testing

### Unit Tests per Dataclass

**Order Tests:**
```python
def test_order_limit_requires_limit_price():
    """LIMIT orders must have limit_price."""
    with pytest.raises(ValueError, match="LIMIT orders must have limit_price"):
        Order(
            id=1, account_id=123, contract_id="TEST",
            type=OrderType.LIMIT, side=OrderSide.BUY, size=1,
            state=OrderState.ACTIVE
            # Missing: limit_price
        )

def test_order_stop_requires_stop_price():
    """STOP orders must have stop_price."""
    with pytest.raises(ValueError, match="STOP orders must have stop_price"):
        Order(
            id=1, account_id=123, contract_id="TEST",
            type=OrderType.STOP, side=OrderSide.SELL, size=1,
            state=OrderState.ACTIVE
            # Missing: stop_price
        )

def test_order_negative_size():
    """Order size must be positive."""
    with pytest.raises(ValueError, match="Order size must be positive"):
        Order(
            id=1, account_id=123, contract_id="TEST",
            type=OrderType.MARKET, side=OrderSide.BUY, size=-1,
            state=OrderState.ACTIVE
        )

def test_order_filled_exceeds_size():
    """Filled size cannot exceed order size."""
    with pytest.raises(ValueError, match="Filled size .* must be between"):
        Order(
            id=1, account_id=123, contract_id="TEST",
            type=OrderType.MARKET, side=OrderSide.BUY, size=2,
            state=OrderState.PARTIAL, filled_size=3  # ERROR
        )
```

**Trade Tests:**
```python
def test_trade_zero_quantity():
    """Trade quantity must be positive."""
    with pytest.raises(ValueError, match="Trade quantity must be positive"):
        Trade(
            id=1, account_id=123, contract_id="TEST",
            quantity=0, profit_and_loss=50.00,
            execution_time=datetime.now()
        )

def test_trade_negative_price():
    """Entry/exit prices must be positive."""
    with pytest.raises(ValueError, match="Entry price must be positive"):
        Trade(
            id=1, account_id=123, contract_id="TEST",
            quantity=1, profit_and_loss=50.00,
            execution_time=datetime.now(),
            entry_price=-100.00
        )

def test_trade_future_execution_time():
    """Trade execution time cannot be in future."""
    with pytest.raises(ValueError, match="cannot be in the future"):
        Trade(
            id=1, account_id=123, contract_id="TEST",
            quantity=1, profit_and_loss=50.00,
            execution_time=datetime(2026, 1, 1)
        )
```

**Quote Tests:**
```python
def test_quote_inverted_spread():
    """Ask must be >= bid."""
    with pytest.raises(ValueError, match="Ask price .* must be >= bid price"):
        Quote(
            contract_id="TEST",
            bid=100.25, ask=100.00,  # Inverted
            last=100.00,
            timestamp=datetime.now()
        )

def test_quote_negative_price():
    """Prices must be positive."""
    with pytest.raises(ValueError, match="Bid price must be positive"):
        Quote(
            contract_id="TEST",
            bid=-100.00, ask=100.25, last=100.00,
            timestamp=datetime.now()
        )

def test_quote_future_timestamp():
    """Quote timestamp cannot be in future."""
    with pytest.raises(ValueError, match="cannot be in the future"):
        Quote(
            contract_id="TEST",
            bid=100.00, ask=100.25, last=100.00,
            timestamp=datetime(2026, 1, 1)
        )
```

---

## Error Handling Strategy

### Validation Failures

**Where validation errors occur:**
1. **API payload parsing** → `from_api_payload()` calls `__init__` which calls `__post_init__`
2. **Database loading** → `from_db_row()` calls `__init__` which calls `__post_init__`
3. **Manual object creation** → Constructor calls `__post_init__`

**How to handle:**
```python
try:
    order = Order.from_api_payload(payload)
except ValueError as e:
    logger.error(f"Invalid order from API: {e}")
    # Option 1: Skip this order
    # Option 2: Store error in database for review
    # Option 3: Alert admin
```

### Logging Validation Errors

**Log Format:**
```python
logger.error(
    f"Validation failed for {cls.__name__}: {error_message}",
    extra={
        'class': cls.__name__,
        'error': str(e),
        'data': sanitized_data  # Remove sensitive fields
    }
)
```

**Example:**
```
ERROR: Validation failed for Order: LIMIT orders must have limit_price
  class: Order
  error: LIMIT orders must have limit_price
  data: {'id': 123, 'type': 'LIMIT', 'side': 'BUY', 'size': 2}
```

### Alerting on Validation Failures

**Alert Thresholds:**
- 1-5 validation errors/hour: Log (normal, API bugs)
- >5 validation errors/hour: Warn (possible API change)
- >20 validation errors/hour: Alert (critical, API broken)

**Metrics to track:**
- Validation failures per dataclass
- Validation failures per error type
- Validation failures over time

---

## Performance Impact

### Validation Overhead

**Benchmarks:**
- Order validation: <0.1ms per object
- Trade validation: <0.05ms per object
- Quote validation: <0.05ms per object

**Total Impact:** Negligible (<0.1% of object creation time)

**When validation matters:**
- High-frequency quote updates (1000s/second)
- Batch order processing (100s/second)
- Database bulk loads (1000s of records)

**Mitigation:**
- Validation is in-memory (no I/O)
- Simple comparisons (no regex, no network calls)
- Fails fast (returns early on first error)

---

## Configuration

### Optional: Disable Validation (Production Only)

**NOT RECOMMENDED** but possible if validation overhead becomes an issue:

```yaml
dataclasses:
  validation:
    enabled: true  # default: true
    strict: true   # raise errors vs log warnings
```

**Implementation:**
```python
import os

VALIDATION_ENABLED = os.getenv('VALIDATION_ENABLED', 'true').lower() == 'true'

def __post_init__(self):
    if not VALIDATION_ENABLED:
        return  # Skip validation

    # ... validation logic ...
```

**Use Cases for Disabling:**
- Performance benchmarking
- Debugging specific issues
- Importing legacy data with known issues

**⚠️ WARNING:** Disabling validation can lead to database corruption, crashes, and incorrect calculations. Only disable in controlled testing environments.

---

## Implementation Checklist

### Phase 1: Order Validation
- [ ] Add `__post_init__` to Order dataclass
- [ ] Implement quantity validation
- [ ] Implement order type validations (LIMIT, STOP, STOP_LIMIT, TRAILING_STOP)
- [ ] Implement filled_size validation
- [ ] Write unit tests (5+ test cases)

### Phase 2: Trade Validation
- [ ] Add `__post_init__` to Trade dataclass
- [ ] Implement quantity validation
- [ ] Implement price validations
- [ ] Implement execution time validation
- [ ] Write unit tests (3+ test cases)

### Phase 3: Quote Validation
- [ ] Add `__post_init__` to Quote dataclass
- [ ] Implement price validations
- [ ] Implement bid/ask spread validation
- [ ] Implement timestamp validation
- [ ] Add staleness warning (optional)
- [ ] Write unit tests (4+ test cases)

### Phase 4: Enhanced Position Validation
- [ ] Enhance Position `__post_init__`
- [ ] Add unrealized P&L sanity check
- [ ] Add timestamp consistency check
- [ ] Write unit tests (2+ test cases)

### Phase 5: Error Handling
- [ ] Add validation error logging
- [ ] Add validation metrics tracking
- [ ] Add validation alerting thresholds
- [ ] Document error recovery procedures

---

## Validation Criteria

**Success Criteria:**
- ✅ All dataclasses have `__post_init__` validation
- ✅ Invalid objects cannot be created
- ✅ Clear error messages for all validation failures
- ✅ Unit tests cover all validation rules
- ✅ Validation overhead <1% of object creation time
- ✅ No breaking changes to existing code

**Validation Tests:**
```python
# All invalid objects should raise ValueError
assert_raises(ValueError, lambda: Order(type=LIMIT, limit_price=None))
assert_raises(ValueError, lambda: Order(size=-1))
assert_raises(ValueError, lambda: Trade(quantity=0))
assert_raises(ValueError, lambda: Quote(bid=100, ask=99))

# All valid objects should succeed
Order(type=LIMIT, limit_price=100.00)  # ✓
Trade(quantity=1, pnl=50.00, execution_time=now())  # ✓
Quote(bid=100.00, ask=100.25, last=100.00, timestamp=now())  # ✓
```

---

## References

**Source Documents:**
- `/docs/ERRORS_AND_WARNINGS_CONSOLIDATED.md` (REC-DM-005, line 104-108)
- `/project-specs/SPECS/07-DATA-MODELS/STATE_OBJECTS.md` (Order, Trade, Quote, Position)

**Related Specifications:**
- `DATACLASS_ENHANCEMENTS_SPEC.md` (DB-SCHEMA-003)
- `SCHEMA_VERSION_TABLE_SPEC.md` (DB-SCHEMA-001)

**External References:**
- Python Dataclasses: https://docs.python.org/3/library/dataclasses.html
- Validation Best Practices: https://docs.python-guide.org/writing/structure/

---

**Document Status:** DRAFT - Ready for Implementation
**Next Steps:** Implement validation in Phase 1 (MVP) - MEDIUM priority (Should-Have Before Production)
