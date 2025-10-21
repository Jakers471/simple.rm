---
doc_id: STATE-OBJ-001
version: 1.0
last_updated: 2025-10-21
dependencies: [ARCH-V2.2, DB-SCHEMA-001, STATE-001, API-INT-001]
---

# State Objects (Python Dataclasses)

**Purpose:** Complete Python dataclass definitions for all in-memory state objects

**File Coverage:** Data structures used throughout daemon, CLIs, and modules

---

## 🎯 Design Principles

### **Dataclass Benefits**
- **Type safety**: Python type hints for all fields
- **Auto-generated methods**: `__init__`, `__repr__`, `__eq__` automatically created
- **Immutability option**: Use `frozen=True` for immutable objects
- **Default values**: Easy to specify field defaults
- **JSON serialization**: Easy conversion to/from dict/JSON

### **Naming Conventions**
- **Classes**: PascalCase (e.g., `Position`, `EnforcementAction`)
- **Fields**: snake_case (e.g., `account_id`, `contract_id`)
- **Enums**: UPPER_SNAKE_CASE (e.g., `OrderState.FILLED`)

---

## 📦 Import Statement

All dataclasses require these imports:
```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum, IntEnum
```

---

## 🔢 Enumerations

### **PositionType**
```python
class PositionType(IntEnum):
    """Position direction"""
    LONG = 1
    SHORT = 2
```

---

### **OrderType**
```python
class OrderType(IntEnum):
    """Order type"""
    MARKET = 1
    LIMIT = 2
    STOP = 3
    STOP_LIMIT = 4
```

---

### **OrderSide**
```python
class OrderSide(IntEnum):
    """Order side (buy/sell)"""
    BUY = 1
    SELL = 2
```

---

### **OrderState**
```python
class OrderState(IntEnum):
    """Order state"""
    ACTIVE = 1       # Order placed, not filled
    FILLED = 2       # Order completely filled
    CANCELED = 3     # Order canceled
    REJECTED = 4     # Order rejected by exchange
    PARTIAL = 5      # Partially filled
```

---

### **EnforcementActionType**
```python
class EnforcementActionType(Enum):
    """Type of enforcement action"""
    CLOSE_ALL_POSITIONS = "CLOSE_ALL_POSITIONS"
    CLOSE_ALL_AND_LOCKOUT = "CLOSE_ALL_AND_LOCKOUT"
    COOLDOWN = "COOLDOWN"
    REJECT_ORDER = "REJECT_ORDER"
    AUTO_STOP_LOSS = "AUTO_STOP_LOSS"
```

---

### **LockoutReason**
```python
class LockoutReason(Enum):
    """Reason for lockout"""
    DAILY_LOSS = "DAILY_LOSS"
    DAILY_UNREALIZED_LOSS = "DAILY_UNREALIZED_LOSS"
    MAX_CONTRACTS = "MAX_CONTRACTS"
    TRADE_FREQUENCY = "TRADE_FREQUENCY"
    COOLDOWN = "COOLDOWN"
    NO_STOP_LOSS = "NO_STOP_LOSS"
    SESSION_BLOCK = "SESSION_BLOCK"
    SYMBOL_BLOCK = "SYMBOL_BLOCK"
    ADMIN_OVERRIDE = "ADMIN_OVERRIDE"
```

---

## 📊 Core State Objects

### **Position**

**Purpose:** Represents an open trading position

**File:** `src/data_models/position.py`

```python
@dataclass
class Position:
    """
    An open trading position (long or short).
    Updated via GatewayUserPosition events from TopstepX.
    """

    # Identity
    id: int                          # Position ID from TopstepX
    account_id: int                  # Account that owns this position
    contract_id: str                 # Contract identifier (e.g., "CON.F.US.MNQ.U25")

    # Position details
    type: PositionType               # LONG or SHORT
    size: int                        # Current position size (number of contracts)
    average_price: float             # Average entry price

    # Timestamps
    created_at: datetime             # When position was opened
    updated_at: datetime             # When position was last updated

    # Optional fields
    unrealized_pnl: Optional[float] = None  # Calculated unrealized P&L

    def __post_init__(self):
        """Validate position after initialization"""
        if self.size < 0:
            raise ValueError(f"Position size cannot be negative: {self.size}")
        if self.average_price <= 0:
            raise ValueError(f"Average price must be positive: {self.average_price}")

    def is_closed(self) -> bool:
        """Check if position is closed (size = 0)"""
        return self.size == 0

    def is_long(self) -> bool:
        """Check if position is long"""
        return self.type == PositionType.LONG

    def is_short(self) -> bool:
        """Check if position is short"""
        return self.type == PositionType.SHORT

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'account_id': self.account_id,
            'contract_id': self.contract_id,
            'type': self.type.value,
            'size': self.size,
            'average_price': self.average_price,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'unrealized_pnl': self.unrealized_pnl
        }

    @classmethod
    def from_api_payload(cls, payload: dict) -> 'Position':
        """Create Position from TopstepX API payload"""
        return cls(
            id=payload['id'],
            account_id=payload['accountId'],
            contract_id=payload['contractId'],
            type=PositionType(payload['type']),
            size=payload['size'],
            average_price=payload['averagePrice'],
            created_at=datetime.fromisoformat(payload['createdAt'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(payload['updatedAt'].replace('Z', '+00:00'))
        )
```

**Example:**
```python
position = Position(
    id=456,
    account_id=123,
    contract_id="CON.F.US.MNQ.U25",
    type=PositionType.LONG,
    size=3,
    average_price=21000.50,
    created_at=datetime(2025, 1, 17, 14, 30, 0),
    updated_at=datetime(2025, 1, 17, 14, 45, 15),
    unrealized_pnl=150.00
)
```

---

### **Order**

**Purpose:** Represents a pending or filled order

**File:** `src/data_models/order.py`

```python
@dataclass
class Order:
    """
    A trading order (market, limit, stop, etc.).
    Updated via GatewayUserOrder events from TopstepX.
    """

    # Identity
    id: int                          # Order ID from TopstepX
    account_id: int                  # Account that placed this order
    contract_id: str                 # Contract identifier

    # Order details
    type: OrderType                  # MARKET, LIMIT, STOP, STOP_LIMIT
    side: OrderSide                  # BUY or SELL
    size: int                        # Order quantity (number of contracts)
    state: OrderState                # ACTIVE, FILLED, CANCELED, REJECTED, PARTIAL

    # Prices (may be None depending on order type)
    limit_price: Optional[float] = None    # Limit price (for LIMIT, STOP_LIMIT orders)
    stop_price: Optional[float] = None     # Stop price (for STOP, STOP_LIMIT orders)
    fill_price: Optional[float] = None     # Actual fill price (when filled)

    # Quantities
    filled_size: int = 0             # How many contracts filled (for partial fills)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Optional metadata
    is_stop_loss: bool = False       # True if this is a stop-loss order (for RULE-008)

    def is_active(self) -> bool:
        """Check if order is still active"""
        return self.state == OrderState.ACTIVE or self.state == OrderState.PARTIAL

    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.state == OrderState.FILLED

    def is_canceled(self) -> bool:
        """Check if order was canceled"""
        return self.state == OrderState.CANCELED

    def is_buy(self) -> bool:
        """Check if order is a buy order"""
        return self.side == OrderSide.BUY

    def is_sell(self) -> bool:
        """Check if order is a sell order"""
        return self.side == OrderSide.SELL

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'account_id': self.account_id,
            'contract_id': self.contract_id,
            'type': self.type.value,
            'side': self.side.value,
            'size': self.size,
            'state': self.state.value,
            'limit_price': self.limit_price,
            'stop_price': self.stop_price,
            'fill_price': self.fill_price,
            'filled_size': self.filled_size,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_stop_loss': self.is_stop_loss
        }

    @classmethod
    def from_api_payload(cls, payload: dict) -> 'Order':
        """Create Order from TopstepX API payload"""
        return cls(
            id=payload['id'],
            account_id=payload['accountId'],
            contract_id=payload['contractId'],
            type=OrderType(payload['type']),
            side=OrderSide(payload['side']),
            size=payload['size'],
            state=OrderState(payload['state']),
            limit_price=payload.get('limitPrice'),
            stop_price=payload.get('stopPrice'),
            fill_price=payload.get('fillPrice'),
            filled_size=payload.get('filledSize', 0),
            created_at=datetime.fromisoformat(payload['createdAt'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(payload['updatedAt'].replace('Z', '+00:00'))
        )
```

**Example:**
```python
order = Order(
    id=789,
    account_id=123,
    contract_id="CON.F.US.MNQ.U25",
    type=OrderType.LIMIT,
    side=OrderSide.BUY,
    size=2,
    state=OrderState.ACTIVE,
    limit_price=21000.00,
    created_at=datetime(2025, 1, 17, 14, 45, 0),
    updated_at=datetime(2025, 1, 17, 14, 45, 0)
)
```

---

### **Trade**

**Purpose:** Represents a completed full-turn trade (with P&L)

**File:** `src/data_models/trade.py`

```python
@dataclass
class Trade:
    """
    A completed full-turn trade (position closed with realized P&L).
    Created from GatewayUserTrade events from TopstepX.
    """

    # Identity
    id: int                          # Trade ID from TopstepX
    account_id: int                  # Account that executed this trade
    contract_id: str                 # Contract identifier

    # Trade details
    quantity: int                    # Number of contracts traded
    profit_and_loss: float           # Realized P&L (negative = loss)
    execution_time: datetime         # When trade executed (TopstepX time)

    # Optional metadata
    entry_price: Optional[float] = None    # Entry price (if available)
    exit_price: Optional[float] = None     # Exit price (if available)

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)  # When daemon received event

    def is_profit(self) -> bool:
        """Check if trade was profitable"""
        return self.profit_and_loss > 0

    def is_loss(self) -> bool:
        """Check if trade was a loss"""
        return self.profit_and_loss < 0

    def is_breakeven(self) -> bool:
        """Check if trade was breakeven"""
        return self.profit_and_loss == 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'account_id': self.account_id,
            'contract_id': self.contract_id,
            'quantity': self.quantity,
            'profit_and_loss': self.profit_and_loss,
            'execution_time': self.execution_time.isoformat(),
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_api_payload(cls, payload: dict) -> 'Trade':
        """Create Trade from TopstepX API payload"""
        return cls(
            id=payload['id'],
            account_id=payload['accountId'],
            contract_id=payload['contractId'],
            quantity=payload['quantity'],
            profit_and_loss=payload['profitAndLoss'],
            execution_time=datetime.fromisoformat(payload['executionTime'].replace('Z', '+00:00')),
            entry_price=payload.get('entryPrice'),
            exit_price=payload.get('exitPrice'),
            timestamp=datetime.now()
        )
```

**Example:**
```python
trade = Trade(
    id=101112,
    account_id=123,
    contract_id="CON.F.US.MNQ.U25",
    quantity=2,
    profit_and_loss=-45.50,
    execution_time=datetime(2025, 1, 17, 14, 45, 15),
    entry_price=21000.50,
    exit_price=20999.25,
    timestamp=datetime(2025, 1, 17, 14, 45, 15)
)
```

---

### **Quote**

**Purpose:** Represents a real-time market quote

**File:** `src/data_models/quote.py`

```python
@dataclass
class Quote:
    """
    Real-time market quote (bid/ask/last prices).
    Updated via MarketQuote events from TopstepX Market Hub.
    """

    # Identity
    contract_id: str                 # Contract identifier

    # Prices
    bid: float                       # Current bid price
    ask: float                       # Current ask price
    last: float                      # Last traded price

    # Timestamp
    timestamp: datetime              # When quote was received

    def mid_price(self) -> float:
        """Calculate mid price (average of bid/ask)"""
        return (self.bid + self.ask) / 2.0

    def spread(self) -> float:
        """Calculate bid/ask spread"""
        return self.ask - self.bid

    def age_seconds(self) -> float:
        """Calculate how old this quote is (in seconds)"""
        return (datetime.now() - self.timestamp).total_seconds()

    def is_stale(self, max_age_seconds: float = 5.0) -> bool:
        """Check if quote is stale (older than max_age_seconds)"""
        return self.age_seconds() > max_age_seconds

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'contract_id': self.contract_id,
            'bid': self.bid,
            'ask': self.ask,
            'last': self.last,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_api_payload(cls, payload: dict) -> 'Quote':
        """Create Quote from TopstepX API payload"""
        return cls(
            contract_id=payload['contractId'],
            bid=payload['bid'],
            ask=payload['ask'],
            last=payload['last'],
            timestamp=datetime.fromisoformat(payload['timestamp'].replace('Z', '+00:00'))
        )
```

**Example:**
```python
quote = Quote(
    contract_id="CON.F.US.MNQ.U25",
    bid=21000.25,
    ask=21000.50,
    last=21000.50,
    timestamp=datetime(2025, 1, 17, 14, 45, 15)
)
```

---

### **ContractMetadata**

**Purpose:** Cached contract metadata (tick size, tick value, etc.)

**File:** `src/data_models/contract_metadata.py`

```python
@dataclass
class ContractMetadata:
    """
    Contract metadata cached from TopstepX API.
    Used for P&L calculations and display.
    """

    # Identity
    contract_id: str                 # Contract identifier (e.g., "CON.F.US.MNQ.U25")
    symbol_id: str                   # Symbol identifier (e.g., "MNQ")

    # Contract details
    name: str                        # Human-readable name (e.g., "Micro E-mini Nasdaq-100")
    tick_size: float                 # Minimum price increment (e.g., 0.25)
    tick_value: float                # Dollar value per tick (e.g., 0.50)

    # Multiplier for P&L calculation
    point_value: float               # Dollar value per full point (e.g., 2.00 for MNQ)

    # Optional metadata
    exchange: Optional[str] = None   # Exchange (e.g., "CME")
    expiration: Optional[str] = None # Contract expiration (e.g., "2025-06-20")

    # Timestamp
    cached_at: datetime = field(default_factory=datetime.now)

    def calculate_pnl(self, entry_price: float, exit_price: float, size: int,
                      position_type: PositionType) -> float:
        """
        Calculate P&L for a trade.

        Args:
            entry_price: Entry price
            exit_price: Exit price
            size: Position size (number of contracts)
            position_type: LONG or SHORT

        Returns:
            Realized P&L (positive = profit, negative = loss)
        """
        price_diff = exit_price - entry_price

        # For short positions, invert the price difference
        if position_type == PositionType.SHORT:
            price_diff = -price_diff

        # Calculate P&L: (price_diff / tick_size) * tick_value * size
        ticks = price_diff / self.tick_size
        pnl = ticks * self.tick_value * size

        return pnl

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'contract_id': self.contract_id,
            'symbol_id': self.symbol_id,
            'name': self.name,
            'tick_size': self.tick_size,
            'tick_value': self.tick_value,
            'point_value': self.point_value,
            'exchange': self.exchange,
            'expiration': self.expiration,
            'cached_at': self.cached_at.isoformat()
        }

    @classmethod
    def from_api_response(cls, response: dict) -> 'ContractMetadata':
        """Create ContractMetadata from TopstepX API response"""
        return cls(
            contract_id=response['id'],
            symbol_id=response['symbolId'],
            name=response['name'],
            tick_size=response['tickSize'],
            tick_value=response['tickValue'],
            point_value=response['pointValue'],
            exchange=response.get('exchange'),
            expiration=response.get('expiration'),
            cached_at=datetime.now()
        )
```

**Example:**
```python
contract = ContractMetadata(
    contract_id="CON.F.US.MNQ.U25",
    symbol_id="MNQ",
    name="Micro E-mini Nasdaq-100 Jun 2025",
    tick_size=0.25,
    tick_value=0.50,
    point_value=2.00,
    exchange="CME",
    expiration="2025-06-20",
    cached_at=datetime(2025, 1, 17, 8, 0, 0)
)
```

---

## 🔒 Enforcement & Lockout Objects

### **Lockout**

**Purpose:** Represents an active lockout on an account

**File:** `src/data_models/lockout.py`

```python
@dataclass
class Lockout:
    """
    An active lockout preventing trading on an account.
    Managed by MOD-002 (Lockout Manager).
    """

    # Identity
    account_id: int                  # Account that is locked

    # Lockout details
    is_locked: bool                  # True if currently locked
    reason: str                      # Human-readable reason
    rule_id: str                     # Rule that triggered lockout (e.g., "RULE-003")

    # Timestamps
    locked_at: datetime              # When lockout was set
    locked_until: Optional[datetime] = None  # When lockout expires (None = permanent)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """Check if lockout has expired"""
        if self.locked_until is None:
            return False  # Permanent lockout never expires
        return datetime.now() >= self.locked_until

    def is_permanent(self) -> bool:
        """Check if lockout is permanent"""
        return self.locked_until is None

    def time_remaining_seconds(self) -> Optional[float]:
        """Get time remaining until lockout expires (in seconds)"""
        if self.locked_until is None:
            return None  # Permanent lockout

        remaining = (self.locked_until - datetime.now()).total_seconds()
        return max(0.0, remaining)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'account_id': self.account_id,
            'is_locked': self.is_locked,
            'reason': self.reason,
            'rule_id': self.rule_id,
            'locked_at': self.locked_at.isoformat(),
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
```

**Example:**
```python
lockout = Lockout(
    account_id=123,
    is_locked=True,
    reason="Daily loss limit hit: -$550",
    rule_id="RULE-003",
    locked_at=datetime(2025, 1, 17, 14, 45, 15),
    locked_until=datetime(2025, 1, 17, 17, 0, 0)  # Expires at 5 PM
)
```

---

### **EnforcementAction**

**Purpose:** Represents an enforcement action to execute

**File:** `src/data_models/enforcement_action.py`

```python
@dataclass
class EnforcementAction:
    """
    An enforcement action to be executed by MOD-001.
    Returned by rules when breach detected.
    """

    # Action details
    type: EnforcementActionType      # Type of action (CLOSE_ALL_POSITIONS, etc.)
    reason: str                      # Human-readable reason
    rule_id: str                     # Rule that triggered action (e.g., "RULE-001")
    account_id: int                  # Account to enforce on

    # Lockout details (if applicable)
    lockout_until: Optional[datetime] = None     # When lockout expires
    lockout_duration_seconds: Optional[int] = None  # Duration in seconds (for cooldowns)

    # Order details (for REJECT_ORDER, AUTO_STOP_LOSS)
    order_id: Optional[int] = None               # Order to cancel/modify
    position_id: Optional[int] = None            # Position to add stop-loss to
    stop_price: Optional[float] = None           # Stop price (for AUTO_STOP_LOSS)

    # Execution details
    executed: bool = False           # True if action was executed
    success: bool = False            # True if action succeeded
    error_message: Optional[str] = None  # Error message (if failed)

    # Timestamp
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'type': self.type.value,
            'reason': self.reason,
            'rule_id': self.rule_id,
            'account_id': self.account_id,
            'lockout_until': self.lockout_until.isoformat() if self.lockout_until else None,
            'lockout_duration_seconds': self.lockout_duration_seconds,
            'order_id': self.order_id,
            'position_id': self.position_id,
            'stop_price': self.stop_price,
            'executed': self.executed,
            'success': self.success,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'executed_at': self.executed_at.isoformat() if self.executed_at else None
        }
```

**Example:**
```python
action = EnforcementAction(
    type=EnforcementActionType.CLOSE_ALL_AND_LOCKOUT,
    reason="Daily loss limit hit: -$550",
    rule_id="RULE-003",
    account_id=123,
    lockout_until=datetime(2025, 1, 17, 17, 0, 0),
    executed=True,
    success=True,
    executed_at=datetime(2025, 1, 17, 14, 45, 15)
)
```

---

### **EnforcementLog**

**Purpose:** Represents a logged enforcement action (for audit trail)

**File:** `src/data_models/enforcement_log.py`

```python
@dataclass
class EnforcementLog:
    """
    A logged enforcement action (for audit trail).
    Stored in enforcement_log SQLite table.
    """

    # Identity (auto-generated by SQLite)
    id: Optional[int] = None         # Auto-increment ID

    # Enforcement details
    account_id: int = 0              # Account that was enforced
    rule_id: str = ""                # Rule that triggered enforcement
    action: str = ""                 # Action type (e.g., "CLOSE_ALL_POSITIONS")
    reason: str = ""                 # Human-readable reason

    # Execution details
    success: bool = False            # True if action succeeded
    error_message: Optional[str] = None  # Error message (if failed)

    # Metadata
    positions_closed: int = 0        # Number of positions closed
    orders_canceled: int = 0         # Number of orders canceled

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'account_id': self.account_id,
            'rule_id': self.rule_id,
            'action': self.action,
            'reason': self.reason,
            'success': self.success,
            'error_message': self.error_message,
            'positions_closed': self.positions_closed,
            'orders_canceled': self.orders_canceled,
            'timestamp': self.timestamp.isoformat()
        }
```

**Example:**
```python
log = EnforcementLog(
    id=1,
    account_id=123,
    rule_id="RULE-003",
    action="CLOSE_ALL_AND_LOCKOUT",
    reason="Daily loss limit hit: -$550",
    success=True,
    positions_closed=2,
    orders_canceled=1,
    timestamp=datetime(2025, 1, 17, 14, 45, 15)
)
```

---

## ⏱️ Timer & State Objects

### **Timer**

**Purpose:** Represents a timer (cooldown, grace period, etc.)

**File:** `src/data_models/timer.py`

```python
@dataclass
class Timer:
    """
    A timer for cooldowns, grace periods, etc.
    Managed by MOD-003 (Timer Manager).
    """

    # Identity
    account_id: int                  # Account this timer belongs to
    timer_type: str                  # Timer type (e.g., "COOLDOWN", "GRACE_PERIOD")
    rule_id: str                     # Rule that set this timer

    # Timer details
    started_at: datetime             # When timer started
    expires_at: datetime             # When timer expires
    duration_seconds: int            # Duration in seconds

    # State
    is_active: bool = True           # True if timer is still running

    def is_expired(self) -> bool:
        """Check if timer has expired"""
        return datetime.now() >= self.expires_at

    def time_remaining_seconds(self) -> float:
        """Get time remaining until expiry (in seconds)"""
        remaining = (self.expires_at - datetime.now()).total_seconds()
        return max(0.0, remaining)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'account_id': self.account_id,
            'timer_type': self.timer_type,
            'rule_id': self.rule_id,
            'started_at': self.started_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'duration_seconds': self.duration_seconds,
            'is_active': self.is_active
        }
```

**Example:**
```python
timer = Timer(
    account_id=123,
    timer_type="COOLDOWN",
    rule_id="RULE-007",
    started_at=datetime(2025, 1, 17, 14, 45, 15),
    expires_at=datetime(2025, 1, 17, 14, 50, 15),  # 5 minutes later
    duration_seconds=300,
    is_active=True
)
```

---

### **DailyPnl**

**Purpose:** Represents daily P&L for an account

**File:** `src/data_models/daily_pnl.py`

```python
@dataclass
class DailyPnl:
    """
    Daily realized P&L for an account.
    Managed by MOD-005 (PNL Tracker).
    """

    # Identity
    account_id: int                  # Account ID
    date: str                        # Date (YYYY-MM-DD format)

    # P&L
    realized_pnl: float = 0.0        # Realized P&L for the day

    # Metadata
    trade_count: int = 0             # Number of trades today
    last_updated: datetime = field(default_factory=datetime.now)

    def add_trade_pnl(self, pnl: float):
        """Add trade P&L to daily total"""
        self.realized_pnl += pnl
        self.trade_count += 1
        self.last_updated = datetime.now()

    def reset(self):
        """Reset daily P&L (for daily reset)"""
        self.realized_pnl = 0.0
        self.trade_count = 0
        self.last_updated = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'account_id': self.account_id,
            'date': self.date,
            'realized_pnl': self.realized_pnl,
            'trade_count': self.trade_count,
            'last_updated': self.last_updated.isoformat()
        }
```

**Example:**
```python
daily_pnl = DailyPnl(
    account_id=123,
    date="2025-01-17",
    realized_pnl=-150.50,
    trade_count=5,
    last_updated=datetime(2025, 1, 17, 14, 45, 15)
)
```

---

## ⚙️ Configuration Objects

### **RuleConfig**

**Purpose:** Configuration for a single risk rule

**File:** `src/data_models/rule_config.py`

```python
@dataclass
class RuleConfig:
    """
    Configuration for a risk rule.
    Loaded from config/risk_config.yaml.
    """

    # Identity
    rule_id: str                     # Rule ID (e.g., "RULE-001")
    name: str                        # Rule name (e.g., "MaxContracts")

    # State
    enabled: bool = True             # True if rule is enabled

    # Rule-specific parameters (varies by rule)
    params: Dict = field(default_factory=dict)

    def get_param(self, key: str, default=None):
        """Get rule parameter with default"""
        return self.params.get(key, default)

    def set_param(self, key: str, value):
        """Set rule parameter"""
        self.params[key] = value

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'enabled': self.enabled,
            'params': self.params
        }

    @classmethod
    def from_yaml(cls, rule_id: str, config: dict) -> 'RuleConfig':
        """Create RuleConfig from YAML config"""
        return cls(
            rule_id=rule_id,
            name=config.get('name', rule_id),
            enabled=config.get('enabled', True),
            params=config
        )
```

**Example:**
```python
rule_config = RuleConfig(
    rule_id="RULE-001",
    name="MaxContracts",
    enabled=True,
    params={
        'limit': 5,
        'action': 'CLOSE_ALL_POSITIONS'
    }
)
```

---

### **AccountConfig**

**Purpose:** Configuration for a trading account

**File:** `src/data_models/account_config.py`

```python
@dataclass
class AccountConfig:
    """
    Configuration for a trading account.
    Loaded from config/accounts.yaml.
    """

    # Identity
    account_id: int                  # Account ID from TopstepX
    username: str                    # TopstepX username

    # Authentication
    api_key: str                     # TopstepX API key

    # Optional settings
    enabled: bool = True             # True if monitoring enabled for this account
    nickname: Optional[str] = None   # Optional nickname for UI

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'account_id': self.account_id,
            'username': self.username,
            'api_key': '***REDACTED***',  # Don't log API key
            'enabled': self.enabled,
            'nickname': self.nickname
        }

    @classmethod
    def from_yaml(cls, config: dict) -> 'AccountConfig':
        """Create AccountConfig from YAML config"""
        return cls(
            account_id=config['account_id'],
            username=config['username'],
            api_key=config['api_key'],
            enabled=config.get('enabled', True),
            nickname=config.get('nickname')
        )
```

**Example:**
```python
account = AccountConfig(
    account_id=123,
    username="trader@example.com",
    api_key="sk_live_abc123...",
    enabled=True,
    nickname="John's Account"
)
```

---

## 📝 Summary

**Total Dataclasses Defined:** 15

**Core Objects:**
- Position
- Order
- Trade
- Quote
- ContractMetadata

**Enforcement Objects:**
- Lockout
- EnforcementAction
- EnforcementLog

**State Objects:**
- Timer
- DailyPnl

**Configuration Objects:**
- RuleConfig
- AccountConfig

**Enumerations:**
- PositionType
- OrderType
- OrderSide
- OrderState
- EnforcementActionType

**Key Features:**
- ✅ Type safety with Python type hints
- ✅ Automatic `__init__`, `__repr__`, `__eq__` methods
- ✅ `to_dict()` methods for JSON serialization
- ✅ `from_api_payload()` / `from_yaml()` factory methods
- ✅ Helper methods for common operations
- ✅ Validation in `__post_init__` where needed

**Files to Implement:**
- `src/data_models/*.py` (~15 files, ~1500 lines total)

---

**Complete!** All state objects now fully specified with Python dataclasses.
