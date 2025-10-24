# Integration Contracts

This document defines EXACT function signatures for all integration points in the Risk Manager system.

**Last Updated:** 2025-10-23
**Status:** Complete
**Coverage:** All modules documented

---

## Table of Contents

1. [Converter Contracts](#converter-contracts) ✅
2. [State Manager Contracts](#state-manager-contracts) ✅
3. [Enforcement Actions Contracts](#enforcement-actions-contracts) ✅
4. [REST Client Contracts](#rest-client-contracts) ✅
5. [Risk Rule Contracts](#risk-rule-contracts) ⚠️
6. [Event Router Contracts](#event-router-contracts) ❌
7. [SignalR Client Contracts](#signalr-client-contracts) ❌
8. [CLI-Daemon IPC Contracts](#cli-daemon-ipc-contracts) ❌
9. [Configuration Loader Contracts](#configuration-loader-contracts) ❌
10. [Persistence Layer Contracts](#persistence-layer-contracts) ⚠️

---

## Converter Contracts ✅ (IMPLEMENTED)

**Module:** `src/api/converters.py`
**Purpose:** Convert between TopstepX API format (camelCase) and internal backend format (snake_case)

### API-to-Internal Converters

#### api_to_internal_account()

```python
def api_to_internal_account(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert TopstepX API account to internal format.

    Args:
        api_data: Account from API (camelCase fields)
            {
                "id": int,
                "name": str,
                "balance": float,
                "canTrade": bool,
                "isVisible": bool,
                "simulated": bool  # optional
            }

    Returns:
        Internal format (snake_case fields)
            {
                "account_id": int,
                "name": str,
                "balance": float,
                "can_trade": bool,
                "is_visible": bool,
                "simulated": bool
            }

    Used by: Account initialization, SignalR account updates
    """
```

#### api_to_internal_order()

```python
def api_to_internal_order(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert TopstepX API order to internal format.

    Args:
        api_data: Order from API (camelCase fields)
            {
                "id": int,  # or "orderId"
                "accountId": int,
                "contractId": str,
                "symbolId": str,
                "creationTimestamp": str,  # ISO 8601
                "updateTimestamp": str,  # ISO 8601
                "status": int,  # OrderStatus enum (0-6)
                "type": int,  # OrderType enum
                "side": int,  # 0=Buy, 1=Sell
                "size": int,
                "limitPrice": float | None,
                "stopPrice": float | None,
                "fillVolume": int,
                "filledPrice": float | None,
                "customTag": str | None
            }

    Returns:
        Internal format (snake_case fields)
            {
                "order_id": int,
                "account_id": int,
                "contract_id": str,
                "symbol_id": str,
                "creation_timestamp": datetime,
                "update_timestamp": datetime,
                "state": InternalOrderState,  # Converted enum
                "order_type": int,
                "side": str,  # "buy" or "sell"
                "quantity": int,
                "limit_price": float | None,
                "stop_price": float | None,
                "filled_quantity": int,
                "filled_price": float | None,
                "custom_tag": str | None
            }

    Side effects:
        - Converts ISO 8601 timestamps to datetime objects
        - Maps API OrderStatus (0-6) to InternalOrderState
        - Converts numeric side (0/1) to string ("buy"/"sell")

    Used by: Order updates, SignalR order events
    """
```

#### api_to_internal_position()

```python
def api_to_internal_position(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert TopstepX API position to internal format.

    Args:
        api_data: Position from API (camelCase fields)
            {
                "id": int,  # optional
                "accountId": int,
                "contractId": str,
                "creationTimestamp": str,  # ISO 8601
                "type": int,  # PositionType: 1=Long, 2=Short
                "size": int,
                "averagePrice": float,
                "unrealizedPnl": float  # optional
            }

    Returns:
        Internal format (snake_case fields)
            {
                "position_id": int | None,
                "account_id": int,
                "contract_id": str,
                "creation_timestamp": datetime | None,
                "position_type": str,  # "long" or "short"
                "quantity": int,
                "average_price": float,
                "unrealized_pnl": float
            }

    Side effects:
        - Converts position type (1/2) to string ("long"/"short")
        - Parses timestamp to datetime

    Used by: Position updates, GatewayUserPosition events
    """
```

#### api_to_internal_trade()

```python
def api_to_internal_trade(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert TopstepX API trade to internal format.

    Args:
        api_data: Trade from API
            {
                "id": int,
                "orderId": int,
                "accountId": int,
                "contractId": str,
                "creationTimestamp": str,
                "price": float,
                "profitAndLoss": float | None,  # null for half-turn
                "fees": float,
                "side": int,  # 0=Buy, 1=Sell
                "size": int,
                "voided": bool
            }

    Returns:
        Internal format
            {
                "trade_id": int,
                "order_id": int,
                "account_id": int,
                "contract_id": str,
                "quantity": int,
                "price": float,
                "execution_time": datetime,
                "side": str,  # "buy" or "sell"
                "fees": float,
                "profit_and_loss": float | None,
                "voided": bool
            }

    Used by: Trade history, PnL calculations
    """
```

#### api_to_internal_contract()

```python
def api_to_internal_contract(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert TopstepX API contract to internal format.

    Args:
        api_data: Contract metadata from API
            {
                "id": str,  # e.g., "CON.F.US.ENQ.H25"
                "name": str,
                "description": str,
                "tickSize": float,
                "tickValue": float,
                "activeContract": bool,
                "symbolId": str,
                "exchange": str,  # optional
                "contractSize": int  # optional
            }

    Returns:
        Internal format
            {
                "contract_id": str,
                "name": str,
                "symbol": str,
                "description": str,
                "exchange": str,
                "tick_size": float,
                "tick_value": float,
                "contract_size": int,
                "active_contract": bool
            }

    Used by: Contract cache, order validation
    """
```

#### api_to_internal_quote()

```python
def api_to_internal_quote(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert TopstepX API quote to internal format.

    Args:
        api_data: Market quote from API
            {
                "symbol": str,
                "symbolName": str,
                "lastPrice": float,
                "bestBid": float,
                "bestAsk": float,
                "change": float,
                "changePercent": float,
                "open": float,
                "high": float,
                "low": float,
                "volume": int,
                "lastUpdated": str,  # ISO 8601
                "timestamp": str  # ISO 8601
            }

    Returns:
        Internal format
            {
                "symbol": str,
                "symbol_name": str,
                "last_price": float,
                "best_bid": float,
                "best_ask": float,
                "change": float,
                "change_percent": float,
                "open": float,
                "high": float,
                "low": float,
                "volume": int,
                "last_updated": datetime,
                "timestamp": datetime
            }

    Used by: Quote tracker, market data processing
    """
```

### Internal-to-API Converters

#### internal_to_api_order_request()

```python
def internal_to_api_order_request(internal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert internal order format to TopstepX API request format.

    Args:
        internal_data: Order in internal format
            {
                "account_id": int,
                "contract_id": str,
                "order_type": str,  # "market", "limit", "stop", etc.
                "side": str,  # "buy" or "sell"
                "quantity": int,
                "limit_price": float | None,
                "stop_price": float | None,
                "trail_price": float | None,
                "custom_tag": str | None,
                "stop_loss_bracket": dict | None,  # optional
                "take_profit_bracket": dict | None  # optional
            }

    Returns:
        API request format (camelCase)
            {
                "accountId": int,
                "contractId": str,
                "type": int,  # OrderType enum
                "side": int,  # OrderSide enum (0=Buy, 1=Sell)
                "size": int,
                "limitPrice": float | None,
                "stopPrice": float | None,
                "trailPrice": float | None,
                "customTag": str | None,
                "stopLossBracket": dict | None,
                "takeProfitBracket": dict | None
            }

    Side effects:
        - Converts order_type string to OrderType enum int
        - Converts side string to OrderSide enum (0/1)

    Used by: Order placement, enforcement actions
    """
```

#### internal_to_api_order_modify_request()

```python
def internal_to_api_order_modify_request(internal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert internal order modify format to API request.

    Args:
        internal_data:
            {
                "account_id": int,
                "order_id": int,
                "quantity": int | None,
                "limit_price": float | None,
                "stop_price": float | None,
                "trail_price": float | None
            }

    Returns:
        API request format:
            {
                "accountId": int,
                "orderId": int,
                "size": int | None,
                "limitPrice": float | None,
                "stopPrice": float | None,
                "trailPrice": float | None
            }

    Used by: Order modification
    """
```

#### internal_to_api_order_cancel_request()

```python
def internal_to_api_order_cancel_request(internal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert internal order cancel format to API request.

    Args:
        internal_data:
            {
                "account_id": int,
                "order_id": int
            }

    Returns:
        API request format:
            {
                "accountId": int,
                "orderId": int
            }

    Used by: Order cancellation, enforcement actions
    """
```

#### internal_to_api_position_close_request()

```python
def internal_to_api_position_close_request(internal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert internal position close format to API request.

    Args:
        internal_data:
            {
                "account_id": int,
                "contract_id": str
            }

    Returns:
        API request format:
            {
                "accountId": int,
                "contractId": str
            }

    Used by: Position closing, enforcement actions
    """
```

---

## State Manager Contracts ✅ (IMPLEMENTED)

**Module:** `src/core/state_manager.py`
**Purpose:** Centralized position and order state tracking with persistence

### Position Management

#### update_position()

```python
def update_position(self, position_event: Dict[str, Any]) -> None:
    """
    Update single position from GatewayUserPosition event.

    Args:
        position_event: Position event in API format (camelCase)
            {
                "accountId": int,
                "id": int,
                "contractId": str,
                "type": int,  # PositionType enum
                "size": int,
                "averagePrice": float,
                "creationTimestamp": str
            }

    Side effects:
        - Updates in-memory position tracking
        - If size == 0, removes position from tracking
        - Persists to database if db connection exists
        - Does NOT trigger rule evaluation (handled by event router)

    Thread safety: Not thread-safe (use external locking if needed)

    Used by: Event router, position event handlers
    """
```

#### update_positions()

```python
def update_positions(self, account_id: int, positions: List[Dict[str, Any]]) -> None:
    """
    Update positions for an account (bulk update).

    Args:
        account_id: Account ID to update
        positions: List of position events (API format)

    Side effects:
        - Replaces all positions for account
        - Removes closed positions (size == 0)
        - Persists to database

    Used by: Initial position sync, bulk updates
    """
```

#### get_positions()

```python
def get_positions(self, account_id: int) -> List[Dict[str, Any]]:
    """
    Get all open positions for account.

    Args:
        account_id: Account ID

    Returns:
        List of position dicts (API format with camelCase)
            [
                {
                    "id": int,
                    "contractId": str,
                    "type": int,
                    "size": int,
                    "averagePrice": float,
                    "creationTimestamp": str
                },
                ...
            ]

    Used by: Risk rules, position queries
    """
```

#### get_position_count()

```python
def get_position_count(self, account_id: int) -> int:
    """
    Get total contract count across all positions.

    Args:
        account_id: Account ID

    Returns:
        Sum of all position sizes (net contract count)

    Used by: MaxContracts rule (RULE-001)
    """
```

#### get_positions_by_contract()

```python
def get_positions_by_contract(self, account_id: int, contract_id: str) -> List[Dict[str, Any]]:
    """
    Get positions for specific contract.

    Args:
        account_id: Account ID
        contract_id: Contract ID to filter by

    Returns:
        List of position dicts for the contract

    Used by: MaxContractsPerInstrument rule (RULE-002)
    """
```

#### get_contract_count()

```python
def get_contract_count(self, account_id: int, contract_id: str) -> int:
    """
    Get contract count for specific instrument.

    Args:
        account_id: Account ID
        contract_id: Contract ID

    Returns:
        Total position size for the contract

    Used by: MaxContractsPerInstrument rule
    """
```

### Order Management

#### update_order()

```python
def update_order(self, order_event: Dict[str, Any]) -> None:
    """
    Update single order from GatewayUserOrder event.

    Args:
        order_event: Order event in API format
            {
                "accountId": int,
                "id": int,
                "contractId": str,
                "type": int,
                "side": int,
                "size": int,
                "limitPrice": float | None,
                "stopPrice": float | None,
                "status": int,  # OrderStatus enum
                "creationTimestamp": str
            }

    Side effects:
        - Updates in-memory order tracking
        - Removes terminal orders (FILLED, CANCELLED, EXPIRED, REJECTED)
        - Persists to database

    Used by: Event router, order event handlers
    """
```

#### get_orders()

```python
def get_orders(self, account_id: int) -> List[Dict[str, Any]]:
    """
    Get all working orders for account.

    Args:
        account_id: Account ID

    Returns:
        List of order dicts (API format, excludes terminal orders)

    Used by: Risk rules, order queries
    """
```

#### get_orders_for_position()

```python
def get_orders_for_position(self, account_id: int, contract_id: str) -> List[Dict[str, Any]]:
    """
    Get orders for specific position/contract.

    Args:
        account_id: Account ID
        contract_id: Contract ID

    Returns:
        List of order dicts for the contract

    Used by: NoStopLossGrace rule (RULE-006)
    """
```

### Persistence

#### save_state_snapshot()

```python
def save_state_snapshot(self) -> None:
    """
    Persist current state to database.

    Side effects:
        - Clears existing positions and orders tables
        - Writes all in-memory state to database
        - Commits transaction

    Used by: Periodic snapshots, graceful shutdown
    """
```

#### load_state_snapshot()

```python
def load_state_snapshot(self) -> None:
    """
    Restore state from database.

    Side effects:
        - Loads all positions and orders from database
        - Replaces in-memory state

    Used by: Startup, state recovery
    """
```

#### clear_state()

```python
def clear_state(self, account_id: int) -> None:
    """
    Clear all state for an account.

    Args:
        account_id: Account ID to clear

    Side effects:
        - Removes all positions and orders for account
        - Deletes from database

    Used by: Account reset, testing
    """
```

---

## Enforcement Actions Contracts ✅ (IMPLEMENTED)

**Module:** `src/core/enforcement_actions.py`
**Purpose:** Unified enforcement API for all risk rules

### Constructor

```python
def __init__(self, rest_client, state_mgr=None, db=None):
    """
    Initialize enforcement actions.

    Args:
        rest_client: RestClient instance for API calls
        state_mgr: StateManager instance (optional, for lockout tracking)
        db: Database connection (optional, for logging)
    """
```

### Position Enforcement

#### close_all_positions()

```python
def close_all_positions(self, account_id: int) -> bool:
    """
    Close all open positions for an account.

    Args:
        account_id: TopstepX account ID

    Returns:
        True if successful, False otherwise

    Side effects:
        1. Calls rest_client.search_open_positions(account_id)
        2. For each position:
           - Calls rest_client.close_position(account_id, contract_id)
        3. Logs enforcement action to database
        4. Logs to application log

    Error handling:
        - Continues closing other positions if one fails
        - Returns False only if entire operation fails

    Thread safety: Thread-safe (uses internal lock)

    Used by: RULE-001 (MaxContracts), RULE-003 (DailyRealizedLoss),
             RULE-009 (AuthLossGuard)
    """
```

### Order Enforcement

#### cancel_all_orders()

```python
def cancel_all_orders(self, account_id: int) -> bool:
    """
    Cancel all open orders for an account.

    Args:
        account_id: TopstepX account ID

    Returns:
        True if successful, False otherwise

    Side effects:
        1. Calls rest_client._make_authenticated_request('/api/Order/searchOpen')
        2. For each order:
           - Calls rest_client.cancel_order(account_id, order_id)
        3. Logs enforcement action

    Error handling:
        - Continues canceling other orders if one fails

    Thread safety: Thread-safe

    Used by: Lockout enforcement, RULE-003, RULE-009
    """
```

### Lockout Management

#### apply_lockout()

```python
def apply_lockout(self, account_id: int, reason: str,
                  duration_hours: Optional[int] = None) -> bool:
    """
    Apply lockout to an account.

    Args:
        account_id: TopstepX account ID
        reason: Reason for lockout
        duration_hours: Lockout duration in hours (None = permanent)

    Returns:
        True if successful, False otherwise

    Side effects:
        - Calculates expiry timestamp
        - Updates state_manager lockout tracking
        - Logs enforcement action

    Thread safety: Thread-safe (uses internal lock)

    Used by: RULE-003, RULE-009 (lockout_on_breach)
    """
```

#### remove_lockout()

```python
def remove_lockout(self, account_id: int) -> bool:
    """
    Remove lockout from an account.

    Args:
        account_id: TopstepX account ID

    Returns:
        True if successful, False otherwise

    Side effects:
        - Clears lockout from state_manager
        - Logs enforcement action

    Thread safety: Thread-safe

    Used by: Manual lockout removal, CLI commands
    """
```

### Logging

#### log_enforcement()

```python
def log_enforcement(self, action_type: str, account_id: int,
                   reason: str, details: dict) -> None:
    """
    Log enforcement action to database and file log.

    Args:
        action_type: Type of action ("CLOSE_ALL_POSITIONS", "APPLY_LOCKOUT", etc.)
        account_id: Account ID
        reason: Human-readable reason
        details: Additional details as dict (JSON-serialized for DB)

    Side effects:
        - Inserts record into enforcement_log table
        - Writes to application log (INFO level)

    Error handling:
        - Logs error but does not raise exception

    Used by: All enforcement methods
    """
```

---

## REST Client Contracts ✅ (IMPLEMENTED)

**Module:** `src/api/rest_client.py`
**Purpose:** TopstepX REST API client with auth, rate limiting, retry logic

### Constructor

```python
def __init__(self, base_url: str, username: str, api_key: str):
    """
    Initialize REST client with credentials.

    Args:
        base_url: TopstepX API base URL
        username: Account username
        api_key: API key for authentication

    Side effects:
        - Creates requests.Session for connection pooling
        - Sets default headers (Content-Type, Accept)
        - Initializes rate limiting tracker
    """
```

### Authentication

#### authenticate()

```python
def authenticate(self) -> bool:
    """
    Authenticate with API and obtain JWT token.

    Returns:
        True if authentication successful

    Side effects:
        - Makes POST request to /api/Auth/loginKey
        - Stores JWT token in self._token
        - Sets token expiry to 1 hour from now

    Raises:
        AuthenticationError: If credentials invalid or request fails

    Used by: Client initialization, token refresh
    """
```

#### is_authenticated()

```python
def is_authenticated(self) -> bool:
    """
    Check if client is currently authenticated with valid token.

    Returns:
        True if token exists and not expired, False otherwise

    Used by: All authenticated requests (internal check)
    """
```

### Position Operations

#### search_open_positions()

```python
def search_open_positions(self, account_id: int) -> List[Position]:
    """
    Search for open positions.

    Args:
        account_id: Account ID to query

    Returns:
        List of Position objects
            Position attributes:
                - account_id: int
                - contract_id: str
                - side: int
                - quantity: int
                - avg_price: float
                - unrealized_pnl: float

    Raises:
        APIError: If request fails
        AuthenticationError: If not authenticated

    Used by: Enforcement actions, position sync
    """
```

#### close_position()

```python
def close_position(self, account_id: int, contract_id: str) -> bool:
    """
    Close position for contract.

    Args:
        account_id: Account ID
        contract_id: Contract ID to close

    Returns:
        True if successful

    Side effects:
        - Makes POST request to /api/Position/closeContract
        - Market order submitted to close position

    Raises:
        APIError: If close fails

    Used by: Enforcement actions
    """
```

### Order Operations

#### place_order()

```python
def place_order(self, account_id: int, contract_id: str, type: int,
               side: int, size: int, stop_price: float) -> int:
    """
    Place order and return order ID.

    Args:
        account_id: Account ID
        contract_id: Contract ID
        type: OrderType enum value
        side: OrderSide enum value (0=Buy, 1=Sell)
        size: Order quantity
        stop_price: Stop price (for stop orders)

    Returns:
        Order ID from API

    Side effects:
        - Makes POST request to /api/Order/place
        - Order submitted to exchange

    Raises:
        APIError: If order placement fails

    Used by: Stop-loss placement, manual orders
    """
```

#### modify_order()

```python
def modify_order(self, account_id: int, order_id: int,
                stop_price: float) -> bool:
    """
    Modify existing order.

    Args:
        account_id: Account ID
        order_id: Order ID to modify
        stop_price: New stop price

    Returns:
        True if successful

    Raises:
        APIError: If modification fails

    Used by: Trade management rules, trailing stops
    """
```

#### cancel_order()

```python
def cancel_order(self, account_id: int, order_id: int) -> bool:
    """
    Cancel working order.

    Args:
        account_id: Account ID
        order_id: Order ID to cancel

    Returns:
        True if successful

    Raises:
        APIError: If cancellation fails

    Used by: Enforcement actions, order management
    """
```

### Contract Operations

#### search_contract_by_id()

```python
def search_contract_by_id(self, contract_id: str) -> Contract:
    """
    Get contract metadata by ID.

    Args:
        contract_id: Contract ID (e.g., "CON.F.US.ENQ.H25")

    Returns:
        Contract object with attributes:
            - id: str
            - name: str
            - symbol: str
            - exchange: str
            - tick_size: float
            - tick_value: float
            - contract_size: int

    Raises:
        APIError: If contract not found

    Used by: Contract cache, order validation
    """
```

### Internal Methods

#### _enforce_rate_limit()

```python
def _enforce_rate_limit(self) -> None:
    """
    Enforce rate limiting by tracking requests in sliding window.

    Side effects:
        - Adds current timestamp to request tracker
        - Removes timestamps outside 60s window
        - Sleeps if rate limit exceeded (200 req/60s)

    Used by: _make_authenticated_request (internal)
    """
```

#### _make_authenticated_request()

```python
def _make_authenticated_request(self, method: str, endpoint: str,
                               payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make authenticated API request with retry logic.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        payload: Request body (JSON)

    Returns:
        Response data as dict

    Side effects:
        - Enforces rate limiting
        - Retries on 429, 500, 504 errors
        - Exponential backoff (up to 5 retries)

    Raises:
        AuthenticationError: If 401 received
        APIError: If request fails after retries
        NetworkError: If timeout or network error

    Used by: All API methods (internal)
    """
```

---

## Risk Rule Contracts ⚠️ (PARTIAL - 4/12 IMPLEMENTED)

**Purpose:** Standard interface for all risk rules

### Standard Rule Interface

Every risk rule MUST implement these methods:

#### check()

```python
def check(self, position_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Check if the rule is breached.

    Args:
        position_event: Position/order/trade event from TopstepX (API format)

    Returns:
        Breach info dict if breached, None otherwise
            {
                "rule_id": str,  # e.g., "RULE-001"
                "action": str,  # e.g., "CLOSE_ALL_POSITIONS"
                "reason": str,  # Human-readable reason
                "current_count": int | float,  # Current metric value
                "limit": int | float  # Configured limit
            }

    Side effects:
        - Queries state_manager for current state
        - Does NOT execute enforcement (that's enforce()'s job)

    Thread safety: Must be thread-safe (read-only state access)
    """
```

#### enforce()

```python
def enforce(self, account_id: int, breach: Dict[str, Any]) -> bool:
    """
    Execute enforcement action for a breach.

    Args:
        account_id: Account ID to enforce on
        breach: Breach information from check()

    Returns:
        True if enforcement succeeded, False otherwise

    Side effects:
        - Calls enforcement_actions methods
        - Logs enforcement action
        - May apply lockout if configured

    Thread safety: Must be thread-safe
    """
```

### Implemented Rules (4/12)

#### RULE-001: MaxContracts

```python
class MaxContractsRule:
    def __init__(self, config: Dict[str, Any], state_manager, actions, log_handler=None):
        """
        Args:
            config:
                - enabled: bool
                - limit: int (max net contracts)
                - count_type: "net" | "gross"
                - close_all: bool
                - reduce_to_limit: bool
                - lockout_on_breach: bool
        """

    def check(self, position_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Returns breach if net contracts > limit.
        Action: CLOSE_ALL_POSITIONS or REDUCE_TO_LIMIT
        """

    def enforce(self, account_id: int, breach: Dict[str, Any]) -> bool:
        """
        Calls actions.close_all_positions() or actions.reduce_positions_to_limit()
        """
```

#### RULE-002: MaxContractsPerInstrument

```python
class MaxContractsPerInstrumentRule:
    def __init__(self, config: Dict[str, Any], state_manager, actions, log_handler=None):
        """
        Args:
            config:
                - enabled: bool
                - limit: int (max contracts per instrument)
                - close_contract: bool
        """

    def check(self, position_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Returns breach if contract count > limit for specific instrument.
        Action: CLOSE_CONTRACT_POSITIONS
        """

    def enforce(self, account_id: int, breach: Dict[str, Any]) -> bool:
        """
        Calls actions.close_contract_positions(account_id, contract_id)
        """
```

#### RULE-003: DailyRealizedLoss

```python
class DailyRealizedLossRule:
    def __init__(self, config: Dict[str, Any], state_manager, actions, log_handler=None):
        """
        Args:
            config:
                - enabled: bool
                - limit: float (max daily realized loss)
                - lockout_on_breach: bool
        """

    def check(self, trade_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Returns breach if daily realized loss > limit.
        Action: CLOSE_ALL_POSITIONS + APPLY_LOCKOUT
        """

    def enforce(self, account_id: int, breach: Dict[str, Any]) -> bool:
        """
        Calls:
        1. actions.close_all_positions(account_id)
        2. actions.apply_lockout(account_id, reason, duration=None)
        """
```

#### RULE-011: SymbolBlocks

```python
class SymbolBlocksRule:
    def __init__(self, config: Dict[str, Any], state_manager, actions, log_handler=None):
        """
        Args:
            config:
                - enabled: bool
                - blocked_symbols: List[str]
        """

    def check(self, order_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Returns breach if order is for blocked symbol.
        Action: CANCEL_ORDER
        """

    def enforce(self, account_id: int, breach: Dict[str, Any]) -> bool:
        """
        Calls actions.cancel_order(account_id, order_id)
        """
```

### Unimplemented Rules (8/12) ❌

The following rules need implementation:

- **RULE-004:** DailyUnrealizedLoss
- **RULE-005:** MaxUnrealizedProfit
- **RULE-006:** NoStopLossGrace
- **RULE-007:** TradeFrequencyLimit
- **RULE-008:** CooldownAfterLoss
- **RULE-009:** AuthLossGuard
- **RULE-010:** SessionBlockOutsideHours
- **RULE-012:** TradeManagement

All unimplemented rules MUST follow the standard `check()` and `enforce()` interface.

---

## Event Router Contracts ❌ (NEEDS IMPLEMENTATION)

**Module:** `src/event_router.py` (NOT YET CREATED)
**Purpose:** Route SignalR events to appropriate handlers

### Constructor

```python
def __init__(self, state_manager: StateManager,
             enforcement_actions: EnforcementActions,
             risk_rules: List[RiskRule]):
    """
    Initialize event router.

    Args:
        state_manager: StateManager instance
        enforcement_actions: EnforcementActions instance
        risk_rules: List of instantiated risk rules
    """
```

### Event Handlers

#### handle_position_event()

```python
def handle_position_event(self, raw_event: Dict[str, Any]) -> None:
    """
    Process position update event from SignalR.

    Args:
        raw_event: Raw SignalR event (camelCase from API)
            {
                "accountId": int,
                "id": int,
                "contractId": str,
                "type": int,
                "size": int,
                "averagePrice": float,
                "creationTimestamp": str
            }

    Side effects:
        1. Converts event via api_to_internal_position()
        2. Updates StateManager via update_position()
        3. Evaluates all position-triggered rules
        4. If breach detected, calls rule.enforce()
        5. Persists state via state_manager.save_state_snapshot()

    Error handling:
        - Logs errors but does not raise
        - Continues processing other rules if one fails

    Thread safety: Must be thread-safe (called from SignalR thread)

    Raises:
        ValidationError: If event format is invalid
    """
```

#### handle_order_event()

```python
def handle_order_event(self, raw_event: Dict[str, Any]) -> None:
    """
    Process order update event from SignalR.

    Args:
        raw_event: Raw SignalR event (camelCase)

    Side effects:
        1. Converts event via api_to_internal_order()
        2. Updates StateManager via update_order()
        3. Evaluates order-triggered rules (e.g., SymbolBlocks)
        4. If breach, calls rule.enforce()

    Used by: SignalR client (GatewayUserOrder subscription)
    """
```

#### handle_trade_event()

```python
def handle_trade_event(self, raw_event: Dict[str, Any]) -> None:
    """
    Process trade event from SignalR.

    Args:
        raw_event: Raw SignalR trade event

    Side effects:
        1. Converts event via api_to_internal_trade()
        2. Updates PnL tracker
        3. Evaluates trade-triggered rules (e.g., DailyRealizedLoss)
        4. If breach, calls rule.enforce()

    Used by: SignalR client (GatewayUserTrade subscription)
    """
```

#### handle_account_event()

```python
def handle_account_event(self, raw_event: Dict[str, Any]) -> None:
    """
    Process account update event from SignalR.

    Args:
        raw_event: Raw account event

    Side effects:
        1. Converts event via api_to_internal_account()
        2. Updates account state
        3. Checks lockout status

    Used by: SignalR client (GatewayUserAccount subscription)
    """
```

#### handle_quote_event()

```python
def handle_quote_event(self, raw_event: Dict[str, Any]) -> None:
    """
    Process market quote event from SignalR.

    Args:
        raw_event: Raw quote event

    Side effects:
        1. Converts event via api_to_internal_quote()
        2. Updates quote tracker
        3. Recalculates unrealized PnL

    Used by: SignalR client (GatewayQuote subscription)
    """
```

---

## SignalR Client Contracts ❌ (NEEDS IMPLEMENTATION)

**Module:** `src/signalr_client.py` (NOT YET CREATED)
**Purpose:** SignalR real-time event streaming

### Constructor

```python
def __init__(self, hub_url: str, jwt_token: str):
    """
    Initialize SignalR client.

    Args:
        hub_url: SignalR hub URL (wss://...)
        jwt_token: JWT authentication token
    """
```

### Connection Management

#### connect()

```python
async def connect(self) -> None:
    """
    Connect to SignalR hub.

    Side effects:
        - Establishes WebSocket connection
        - Sends authentication token
        - Registers event handlers

    Raises:
        ConnectionError: If connection fails
        AuthenticationError: If authentication fails
    """
```

#### disconnect()

```python
async def disconnect(self) -> None:
    """
    Disconnect from SignalR hub.

    Side effects:
        - Closes WebSocket connection
        - Unsubscribes from all events
    """
```

### Subscription

#### subscribe()

```python
def subscribe(self, event_name: str, handler: Callable[[Dict], None]) -> None:
    """
    Subscribe to SignalR event.

    Args:
        event_name: Event type (e.g., "GatewayUserPosition")
        handler: Callback function to handle event
            Must accept Dict[str, Any] with camelCase fields

    Example:
        signalr.subscribe("GatewayUserPosition", event_router.handle_position_event)
        signalr.subscribe("GatewayUserOrder", event_router.handle_order_event)
        signalr.subscribe("GatewayUserTrade", event_router.handle_trade_event)

    Side effects:
        - Registers handler for event type
        - Sends subscription request to hub
    """
```

#### unsubscribe()

```python
def unsubscribe(self, event_name: str) -> None:
    """
    Unsubscribe from SignalR event.

    Args:
        event_name: Event type to unsubscribe from
    """
```

### Event Types

The following SignalR events are available:

- `GatewayUserPosition` - Position updates
- `GatewayUserOrder` - Order updates
- `GatewayUserTrade` - Trade executions
- `GatewayUserAccount` - Account balance updates
- `GatewayQuote` - Market quotes

---

## CLI-Daemon IPC Contracts ❌ (NEEDS IMPLEMENTATION)

**Purpose:** Communication between CLI tool and daemon process

### IPC Message Format

#### Request Format

```python
{
    "command": str,  # Command type
    "params": Dict[str, Any],  # Command-specific parameters
    "request_id": str  # Unique request ID (UUID)
}
```

#### Response Format

```python
{
    "status": "success" | "error",
    "data": Any,  # Response data (command-specific)
    "error": Optional[str],  # Error message if status == "error"
    "request_id": str  # Echo of request ID
}
```

### CLI Commands

#### status

```python
# Request
{
    "command": "status",
    "params": {
        "account_id": int  # optional, filter by account
    }
}

# Response
{
    "status": "success",
    "data": {
        "daemon_running": bool,
        "connected": bool,
        "accounts": [
            {
                "account_id": int,
                "position_count": int,
                "order_count": int,
                "locked_out": bool
            }
        ],
        "uptime_seconds": float
    }
}
```

#### config

```python
# Request
{
    "command": "config",
    "params": {
        "action": "get" | "reload" | "validate",
        "config_path": str  # optional, path to config file
    }
}

# Response (get)
{
    "status": "success",
    "data": {
        "config": Dict[str, Any],  # Current configuration
        "config_path": str,
        "last_loaded": str  # ISO 8601 timestamp
    }
}

# Response (reload)
{
    "status": "success",
    "data": {
        "reloaded": bool,
        "errors": List[str]  # Validation errors if any
    }
}
```

#### block

```python
# Request
{
    "command": "block",
    "params": {
        "account_id": int,
        "reason": str,
        "duration_hours": int | None  # None = permanent
    }
}

# Response
{
    "status": "success",
    "data": {
        "blocked": bool,
        "account_id": int,
        "expiry": str | None  # ISO 8601 or null
    }
}
```

#### unblock

```python
# Request
{
    "command": "unblock",
    "params": {
        "account_id": int
    }
}

# Response
{
    "status": "success",
    "data": {
        "unblocked": bool,
        "account_id": int
    }
}
```

#### logs

```python
# Request
{
    "command": "logs",
    "params": {
        "lines": int,  # default 100
        "filter": str,  # optional regex filter
        "level": str  # optional: "INFO", "WARNING", "ERROR"
    }
}

# Response
{
    "status": "success",
    "data": {
        "logs": List[str],  # Log lines
        "count": int
    }
}
```

#### enforce

```python
# Request (manual enforcement trigger)
{
    "command": "enforce",
    "params": {
        "account_id": int,
        "rule_id": str,  # e.g., "RULE-001"
        "dry_run": bool  # default False
    }
}

# Response
{
    "status": "success",
    "data": {
        "breach_detected": bool,
        "breach": Dict[str, Any] | None,
        "enforced": bool,
        "actions_taken": List[str]
    }
}
```

### IPC Transport

The IPC mechanism should support:

- **Unix Domain Sockets** (Linux/Mac): `/tmp/risk-manager.sock`
- **Named Pipes** (Windows): `\\.\pipe\risk-manager`
- **HTTP REST** (fallback): `http://localhost:5555`

---

## Configuration Loader Contracts ❌ (NEEDS IMPLEMENTATION)

**Module:** `src/config_loader.py` (NOT YET CREATED)
**Purpose:** Load and validate YAML configuration

### load_config()

```python
def load_config(config_path: str) -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config YAML file

    Returns:
        Config object with validated settings

    Raises:
        ConfigError: If config is invalid
        FileNotFoundError: If config file missing
        yaml.YAMLError: If YAML syntax error

    Validation:
        - All required fields present
        - Rule IDs are valid (RULE-001 to RULE-012)
        - Numeric limits are positive
        - Enum values are valid (count_type, order_type, etc.)
        - Time formats are valid (HH:MM)
    """
```

### Config Object Structure

```python
class Config:
    """Configuration data structure"""

    api: APIConfig
    rules: Dict[str, RuleConfig]
    logging: LoggingConfig
    persistence: PersistenceConfig

class APIConfig:
    base_url: str
    username: str
    api_key: str  # Should be loaded from env var

class RuleConfig:
    enabled: bool
    # Rule-specific fields vary by rule type

class LoggingConfig:
    level: str  # DEBUG, INFO, WARNING, ERROR
    file: str
    max_size_mb: int
    backup_count: int

class PersistenceConfig:
    database_path: str
    snapshot_interval_seconds: int
```

### validate_config()

```python
def validate_config(config: Config) -> List[str]:
    """
    Validate configuration object.

    Args:
        config: Config object to validate

    Returns:
        List of validation error messages (empty if valid)

    Checks:
        - API credentials not empty
        - At least one rule enabled
        - Rule limits are reasonable (not negative, not extreme)
        - Logging path is writable
        - Database path is writable
    """
```

### reload_config()

```python
def reload_config(config_path: str, current_config: Config) -> Config:
    """
    Reload configuration with hot-reload support.

    Args:
        config_path: Path to config file
        current_config: Current configuration

    Returns:
        New Config object

    Side effects:
        - Compares new vs old config
        - Logs changes detected
        - Validates before applying

    Raises:
        ConfigError: If new config is invalid
    """
```

---

## Persistence Layer Contracts ⚠️ (PARTIAL - StateManager has DB)

**Module:** `src/persistence.py` (PARTIALLY in StateManager)
**Purpose:** Database operations for state persistence

### Database Schema

```sql
-- Positions table
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    contract_id TEXT NOT NULL,
    type INTEGER NOT NULL,  -- PositionType enum
    size INTEGER NOT NULL,
    average_price REAL NOT NULL,
    created_at TEXT NOT NULL,  -- ISO 8601
    UNIQUE(account_id, contract_id)
);

-- Orders table
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    contract_id TEXT NOT NULL,
    type INTEGER NOT NULL,  -- OrderType enum
    side INTEGER NOT NULL,  -- OrderSide enum
    size INTEGER NOT NULL,
    limit_price REAL,
    stop_price REAL,
    status INTEGER NOT NULL,  -- OrderStatus enum
    created_at TEXT NOT NULL,
    UNIQUE(id, account_id)
);

-- Enforcement log table
CREATE TABLE enforcement_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    action_type TEXT NOT NULL,
    account_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    details TEXT  -- JSON
);

-- Lockouts table
CREATE TABLE lockouts (
    account_id INTEGER PRIMARY KEY,
    reason TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    expiry TEXT  -- NULL = permanent
);

-- PnL tracking table
CREATE TABLE pnl_tracker (
    account_id INTEGER NOT NULL,
    date TEXT NOT NULL,  -- YYYY-MM-DD
    realized_pnl REAL NOT NULL DEFAULT 0.0,
    unrealized_pnl REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY(account_id, date)
);

-- Trade counter table
CREATE TABLE trade_counter (
    account_id INTEGER NOT NULL,
    contract_id TEXT NOT NULL,
    window_start TEXT NOT NULL,  -- ISO 8601
    trade_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(account_id, contract_id, window_start)
);
```

### Position Persistence

#### save_position()

```python
def save_position(position: Dict[str, Any]) -> None:
    """
    Persist position to database.

    Args:
        position: Position in INTERNAL format (snake_case)
            Fields map directly to DB columns

    Side effects:
        - INSERT OR REPLACE into positions table
        - Commits transaction
    """
```

#### load_positions()

```python
def load_positions(account_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load positions from database.

    Args:
        account_id: Filter by account (None = all accounts)

    Returns:
        List of position dicts (API format)
    """
```

### Order Persistence

#### save_order()

```python
def save_order(order: Dict[str, Any]) -> None:
    """
    Persist order to database.

    Args:
        order: Order in INTERNAL format
    """
```

#### load_orders()

```python
def load_orders(account_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load orders from database.

    Args:
        account_id: Filter by account

    Returns:
        List of order dicts (API format)
    """
```

### Enforcement Log Persistence

#### save_enforcement_log()

```python
def save_enforcement_log(action_type: str, account_id: int,
                         reason: str, details: Dict[str, Any]) -> None:
    """
    Save enforcement action to log.

    Args:
        action_type: Action type
        account_id: Account ID
        reason: Reason string
        details: Additional details (JSON-serialized)
    """
```

#### query_enforcement_log()

```python
def query_enforcement_log(account_id: Optional[int] = None,
                          start_date: Optional[str] = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
    """
    Query enforcement log.

    Args:
        account_id: Filter by account
        start_date: Filter by date (ISO 8601)
        limit: Max records to return

    Returns:
        List of log entries
    """
```

---

## Summary

### Integration Point Count

| Component | Status | Methods | Notes |
|-----------|--------|---------|-------|
| **Converters** | ✅ IMPLEMENTED | 10 | All API<->internal conversions |
| **StateManager** | ✅ IMPLEMENTED | 15+ | Position/order tracking + persistence |
| **EnforcementActions** | ✅ IMPLEMENTED | 6 | Close, cancel, lockout operations |
| **REST Client** | ✅ IMPLEMENTED | 10+ | Auth, positions, orders, contracts |
| **Risk Rules** | ⚠️ PARTIAL | 4/12 | MaxContracts, MaxPerInstrument, DailyLoss, SymbolBlocks |
| **Event Router** | ❌ MISSING | ~6 | Position, order, trade, account handlers |
| **SignalR Client** | ❌ MISSING | ~8 | Connect, subscribe, event handling |
| **CLI IPC** | ❌ MISSING | ~10 | Status, config, block, logs commands |
| **Config Loader** | ❌ MISSING | ~4 | Load, validate, reload YAML config |
| **Persistence** | ⚠️ PARTIAL | ~12 | DB operations (partially in StateManager) |

### Critical Missing Integrations

1. **Event Router** - Routes SignalR events to state manager and rules
2. **SignalR Client** - Real-time event streaming from TopstepX
3. **CLI IPC** - Communication between CLI and daemon
4. **Config Loader** - YAML configuration loading and validation
5. **8 Risk Rules** - Need implementation (RULE-004 through RULE-010, RULE-012)

### Implementation Priority

**Phase 1 (Critical Path):**
1. Event Router (enables rule triggering)
2. SignalR Client (enables real-time operation)
3. Config Loader (enables configuration)

**Phase 2 (Essential):**
4. CLI IPC (enables user control)
5. Remaining 8 risk rules

**Phase 3 (Enhancement):**
6. Complete persistence layer
7. Advanced logging and monitoring

---

**Document Status:** Complete architecture documentation
**Next Steps:** Implement Event Router, SignalR Client, Config Loader
