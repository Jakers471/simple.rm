---
doc_id: API-INT-001
version: 1.0
last_updated: 2025-01-17
dependencies: [ARCH-V2, MOD-001]
---

# TopstepX API Integration & Event Pipeline

**Purpose:** Complete data flow from TopstepX API → Risk Engine → Enforcement → CLI

---

## 🔄 Complete Event Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TOPSTEPX GATEWAY API                             │
│  REST: https://api.topstepx.com                                        │
│  SignalR User Hub: https://rtc.topstepx.com/hubs/user                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  │ SignalR WebSocket Events
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  src/api/signalr_listener.py                                           │
│  - Subscribes to: GatewayUserTrade, GatewayUserPosition,               │
│                   GatewayUserOrder, GatewayUserAccount                 │
│  - Validates event payloads                                            │
│  - Logs all events to logs/api.log                                     │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  │ Parsed Event Dict
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  src/core/event_router.py                                              │
│  - Checks if account is locked (MOD-002.is_locked_out())               │
│  - Routes event to relevant rules based on event type                  │
│  - Maintains event processing queue                                    │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
                ┌─────────────────┴─────────────────┐
                │                                   │
                ▼                                   ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│  src/rules/                  │   │  src/state/                  │
│  - Each rule.check(event)    │   │  - Update state:             │
│  - Calculate breach          │   │    * positions               │
│  - Return action if needed   │   │    * P&L                     │
└────────────┬─────────────────┘   │    * trade counts            │
              │                     │    * timers                  │
              │ Breach Detected     └──────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  src/enforcement/enforcement_engine.py                                 │
│  - Receives enforcement action from rule                               │
│  - Calls MOD-001 (enforcement/actions.py)                              │
│  - Calls MOD-002 (lockout_manager.py) if lockout needed                │
│  - Logs enforcement to logs/enforcement.log                            │
└────────────────────────────────┬────────────────────────────────────────┘
                                  │
                ┌─────────────────┴─────────────────┐
                │                                   │
                ▼                                   ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│  MOD-001: actions.py         │   │  MOD-002: lockout_manager.py │
│  - close_all_positions()     │   │  - set_lockout()             │
│  - close_position()          │   │  - set_cooldown()            │
│  - cancel_all_orders()       │   │  - persist to SQLite         │
│  (REST API calls to TopstepX)│   └──────────────────────────────┘
└──────────────────────────────┘
                │
                │ REST API Calls
                │
                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  TOPSTEPX REST API                                                     │
│  - POST /api/Position/closeContract                                    │
│  - POST /api/Position/partialCloseContract                             │
│  - POST /api/Order/cancel                                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📡 TopstepX API Integration Details

### **1. Authentication Flow**

```python
# src/api/auth.py

def authenticate():
    """Get JWT token from TopstepX."""
    payload = {
        "userName": config.username,
        "apiKey": config.api_key
    }

    response = requests.post(
        "https://api.topstepx.com/api/Auth/loginKey",
        json=payload
    )

    token = response.json()["token"]
    # Token valid for 24 hours
    return token

def validate_token(token):
    """Check if token is still valid, refresh if needed."""
    response = requests.post(
        "https://api.topstepx.com/api/Auth/validate",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.json()["success"]:
        return response.json()["newToken"]
    else:
        return authenticate()  # Re-authenticate
```

**Called By:**
- `src/core/daemon.py` on startup
- Background task every 20 hours to refresh token

---

### **2. SignalR WebSocket Connection**

```python
# src/api/signalr_listener.py

from signalrcore.hub_connection_builder import HubConnectionBuilder

def setup_user_hub(jwt_token, account_id):
    """Connect to TopstepX SignalR User Hub."""

    connection = HubConnectionBuilder() \
        .with_url(
            f"https://rtc.topstepx.com/hubs/user?access_token={jwt_token}",
            options={
                "skip_negotiation": True,
                "transport": "WebSockets",
                "access_token_factory": lambda: jwt_token
            }
        ) \
        .with_automatic_reconnect({
            "type": "raw",
            "keep_alive_interval": 10,
            "reconnect_interval": 5,
            "max_attempts": 10
        }) \
        .build()

    # Subscribe to events
    connection.on_open(lambda: subscribe_to_user_events(account_id))
    connection.on_close(lambda: handle_disconnect())
    connection.on_error(lambda error: log_error(error))

    # Register event handlers
    connection.on("GatewayUserTrade", handle_trade_event)
    connection.on("GatewayUserPosition", handle_position_event)
    connection.on("GatewayUserOrder", handle_order_event)
    connection.on("GatewayUserAccount", handle_account_event)

    connection.start()
    return connection

def subscribe_to_user_events(account_id):
    """Subscribe to account-specific events."""
    connection.invoke("SubscribeAccounts")
    connection.invoke("SubscribeOrders", account_id)
    connection.invoke("SubscribePositions", account_id)
    connection.invoke("SubscribeTrades", account_id)

def setup_market_hub(jwt_token):
    """Connect to TopstepX SignalR Market Hub for real-time quotes."""

    market_connection = HubConnectionBuilder() \
        .with_url(
            f"https://rtc.topstepx.com/hubs/market?access_token={jwt_token}",
            options={
                "skip_negotiation": True,
                "transport": "WebSockets",
                "access_token_factory": lambda: jwt_token
            }
        ) \
        .with_automatic_reconnect({
            "type": "raw",
            "keep_alive_interval": 10,
            "reconnect_interval": 5,
            "max_attempts": 10
        }) \
        .build()

    # Register quote handler
    market_connection.on("GatewayQuote", handle_quote_event)

    market_connection.start()
    return market_connection

def subscribe_to_contract_quotes(contract_ids):
    """Subscribe to real-time quotes for specific contracts."""
    for contract_id in contract_ids:
        market_connection.invoke("SubscribeContractQuotes", contract_id)

def unsubscribe_from_contract_quotes(contract_ids):
    """Unsubscribe from quotes when positions close."""
    for contract_id in contract_ids:
        market_connection.invoke("UnsubscribeContractQuotes", contract_id)
```

**User Hub Event Payloads (Complete):**

#### GatewayUserTrade
```json
{
  "id": 101112,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "creationTimestamp": "2024-07-21T13:47:00Z",
  "price": 21000.75,
  "profitAndLoss": -50.25,
  "fees": 2.50,
  "side": 0,
  "size": 1,
  "voided": false,
  "orderId": 789
}
```
**Fields:** `id`, `accountId`, `contractId`, `creationTimestamp`, `price`, `profitAndLoss`, `fees`, `side` (0=Buy, 1=Sell), `size`, `voided`, `orderId`

**Used By:** RULE-003 (DailyRealizedLoss), RULE-006 (TradeFrequencyLimit), RULE-007 (CooldownAfterLoss)

---

#### GatewayUserPosition
```json
{
  "id": 456,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "creationTimestamp": "2024-07-21T13:45:00Z",
  "type": 1,
  "size": 2,
  "averagePrice": 21000.25
}
```
**Fields:** `id`, `accountId`, `contractId`, `creationTimestamp`, `type` (1=Long, 2=Short), `size`, `averagePrice`

**Used By:** RULE-001 (MaxContracts), RULE-002 (MaxContractsPerInstrument), RULE-004 (DailyUnrealizedLoss), RULE-005 (MaxUnrealizedProfit), RULE-009 (SessionBlockOutside), RULE-011 (SymbolBlocks), RULE-012 (TradeManagement)

---

#### GatewayUserOrder
```json
{
  "id": 789,
  "accountId": 123,
  "contractId": "CON.F.US.MNQ.U25",
  "symbolId": "F.US.MNQ",
  "creationTimestamp": "2024-07-21T13:45:00Z",
  "updateTimestamp": "2024-07-21T13:46:00Z",
  "status": 1,
  "type": 4,
  "side": 1,
  "size": 1,
  "limitPrice": null,
  "stopPrice": 20950.00,
  "fillVolume": 0,
  "filledPrice": null,
  "customTag": "strategy-1"
}
```
**Fields:** `id`, `accountId`, `contractId`, `symbolId`, `creationTimestamp`, `updateTimestamp`, `status` (1=Open, 2=Filled, 3=Cancelled), `type` (1=Limit, 2=Market, 3=StopLimit, 4=Stop, 5=TrailingStop), `side` (0=Buy, 1=Sell), `size`, `limitPrice`, `stopPrice`, `fillVolume`, `filledPrice`, `customTag`

**Used By:** RULE-008 (NoStopLossGrace)

---

#### GatewayUserAccount
```json
{
  "id": 123,
  "name": "Main Trading Account",
  "balance": 10000.50,
  "canTrade": true,
  "isVisible": true,
  "simulated": false
}
```
**Fields:** `id`, `name`, `balance`, `canTrade`, `isVisible`, `simulated`

**Used By:** RULE-010 (AuthLossGuard)

---

**Market Hub Event Payloads:**

#### GatewayQuote
```json
{
  "symbol": "F.US.MNQ",
  "symbolName": "/MNQ",
  "lastPrice": 21000.25,
  "bestBid": 21000.00,
  "bestAsk": 21000.50,
  "change": 25.50,
  "changePercent": 0.14,
  "open": 20990.00,
  "high": 21010.00,
  "low": 20980.00,
  "volume": 12000,
  "lastUpdated": "2024-07-21T13:45:00Z",
  "timestamp": "2024-07-21T13:45:00Z"
}
```
**Fields:** `symbol`, `symbolName`, `lastPrice`, `bestBid`, `bestAsk`, `change`, `changePercent`, `open`, `high`, `low`, `volume`, `lastUpdated`, `timestamp`

**Used By:** RULE-004 (DailyUnrealizedLoss), RULE-005 (MaxUnrealizedProfit), RULE-012 (TradeManagement)

---

### **3. REST API Enforcement Actions**

```python
# src/enforcement/actions.py

def close_all_positions(account_id, jwt_token):
    """Close all open positions for account."""

    # Step 1: Get all open positions
    response = requests.post(
        "https://api.topstepx.com/api/Position/searchOpen",
        headers={"Authorization": f"Bearer {jwt_token}"},
        json={"accountId": account_id}
    )

    positions = response.json()["positions"]

    # Step 2: Close each position
    for position in positions:
        requests.post(
            "https://api.topstepx.com/api/Position/closeContract",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={
                "accountId": account_id,
                "contractId": position["contractId"]
            }
        )

    logger.info(f"Closed {len(positions)} positions for account {account_id}")
    return True

def cancel_all_orders(account_id, jwt_token):
    """Cancel all open orders for account."""

    # Step 1: Get all open orders
    response = requests.post(
        "https://api.topstepx.com/api/Order/searchOpen",
        headers={"Authorization": f"Bearer {jwt_token}"},
        json={"accountId": account_id}
    )

    orders = response.json()["orders"]

    # Step 2: Cancel each order
    for order in orders:
        requests.post(
            "https://api.topstepx.com/api/Order/cancel",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={
                "accountId": account_id,
                "orderId": order["id"]
            }
        )

    logger.info(f"Cancelled {len(orders)} orders for account {account_id}")
    return True

def modify_order(account_id, order_id, jwt_token, **params):
    """Modify an existing order (for auto-breakeven, trailing stops)."""

    payload = {
        "accountId": account_id,
        "orderId": order_id
    }

    # Add optional parameters
    if 'size' in params:
        payload['size'] = params['size']
    if 'limitPrice' in params:
        payload['limitPrice'] = params['limitPrice']
    if 'stopPrice' in params:
        payload['stopPrice'] = params['stopPrice']
    if 'trailPrice' in params:
        payload['trailPrice'] = params['trailPrice']

    response = requests.post(
        "https://api.topstepx.com/api/Order/modify",
        headers={"Authorization": f"Bearer {jwt_token}"},
        json=payload
    )

    if response.json()["success"]:
        logger.info(f"Modified order {order_id} for account {account_id}")
        return True
    else:
        logger.error(f"Failed to modify order {order_id}: {response.json()}")
        return False
```

**Used By:** RULE-012 (TradeManagement) for auto-breakeven and trailing stops

---

## 📊 API Enum Definitions

```python
# src/api/enums.py

class OrderType:
    UNKNOWN = 0
    LIMIT = 1
    MARKET = 2
    STOP_LIMIT = 3
    STOP = 4
    TRAILING_STOP = 5
    JOIN_BID = 6
    JOIN_ASK = 7

class OrderSide:
    BUY = 0   # Bid
    SELL = 1  # Ask

class OrderStatus:
    NONE = 0
    OPEN = 1
    FILLED = 2
    CANCELLED = 3
    EXPIRED = 4
    REJECTED = 5
    PENDING = 6

class PositionType:
    UNDEFINED = 0
    LONG = 1
    SHORT = 2
```

---

## 🔀 Event Routing Logic

```python
# src/core/event_router.py

def route_event(event_type, event_data):
    """Route events to relevant rules."""

    account_id = event_data.get("accountId")

    # Check lockout FIRST
    if lockout_manager.is_locked_out(account_id):
        # If locked out and new position/order detected, close/cancel immediately
        if event_type == "GatewayUserPosition":
            enforcement.close_position(account_id, event_data["contractId"])
        elif event_type == "GatewayUserOrder" and event_data["status"] == 1:  # Open order
            enforcement.cancel_order(account_id, event_data["id"])
        return

    # Route to rules based on event type
    if event_type == "GatewayUserTrade":
        # Trade events → P&L and frequency rules
        for rule in [
            daily_realized_loss,      # RULE-003
            trade_frequency_limit,    # RULE-006
            cooldown_after_loss       # RULE-007
        ]:
            if rule.enabled:
                action = rule.check(event_data)
                if action:
                    enforcement_engine.execute(action)

    elif event_type == "GatewayUserPosition":
        # Position events → ALL position-based rules
        for rule in [
            max_contracts,                  # RULE-001
            max_contracts_per_instrument,   # RULE-002
            daily_unrealized_loss,          # RULE-004
            max_unrealized_profit,          # RULE-005
            session_block_outside,          # RULE-009
            symbol_blocks,                  # RULE-011
            trade_management                # RULE-012
        ]:
            if rule.enabled:
                action = rule.check(event_data)
                if action:
                    enforcement_engine.execute(action)

    elif event_type == "GatewayUserOrder":
        # Order events → stop-loss grace rule
        if no_stop_loss_grace.enabled:  # RULE-008
            action = no_stop_loss_grace.check(event_data)
            if action:
                enforcement_engine.execute(action)

    elif event_type == "GatewayUserAccount":
        # Account events → auth guard rule
        if auth_loss_guard.enabled:  # RULE-010
            action = auth_loss_guard.check(event_data)
            if action:
                enforcement_engine.execute(action)

    elif event_type == "GatewayQuote":
        # Quote events → unrealized P&L tracking
        quote_tracker.update_quote(event_data)

        # Trigger unrealized P&L rules to recalculate
        for rule in [
            daily_unrealized_loss,    # RULE-004
            max_unrealized_profit,    # RULE-005
            trade_management          # RULE-012
        ]:
            if rule.enabled:
                action = rule.check_with_current_prices()
                if action:
                    enforcement_engine.execute(action)
```

---

## 🗄️ State Persistence (SQLite)

### **Database Schema:**

```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    account_id INTEGER,
    contract_id TEXT,
    position_type INTEGER,  -- 1=Long, 2=Short
    size INTEGER,
    average_price REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    account_id INTEGER,
    contract_id TEXT,
    price REAL,
    profit_and_loss REAL,
    fees REAL,
    side INTEGER,  -- 0=Buy, 1=Sell
    size INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lockouts (
    account_id INTEGER PRIMARY KEY,
    reason TEXT,
    expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE daily_pnl (
    account_id INTEGER PRIMARY KEY,
    realized_pnl REAL DEFAULT 0,
    unrealized_pnl REAL DEFAULT 0,
    date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE trade_counts (
    account_id INTEGER,
    window_type TEXT,  -- 'minute', 'hour', 'session'
    window_start DATETIME,
    count INTEGER,
    PRIMARY KEY (account_id, window_type, window_start)
);
```

**Persistence Flow:**
```python
# src/state/persistence.py

def save_state():
    """Save current state to SQLite (called after every event)."""
    # Auto-commit on every state change
    # Ensures crash recovery

def load_state_on_startup():
    """Load state from SQLite when daemon starts."""
    # Restore lockouts, P&L, trade counts
```

---

## ⏱️ Background Tasks (Daemon Loop)

```python
# src/core/daemon.py

def main_loop():
    """Main event loop - runs continuously."""

    while running:
        # Check timers every second
        timer_manager.check_timers()

        # Check for expired lockouts
        lockout_manager.check_expired_lockouts()

        # Check daily reset
        reset_scheduler.check_reset_time()

        # Validate token every 20 hours
        if time_since_auth > 72000:  # 20 hours in seconds
            jwt_token = auth.validate_token(jwt_token)

        time.sleep(1)
```

---

## 📊 CLI Real-Time Updates

```python
# src/cli/trader/status_screen.py

def display_status(refresh_interval=1):
    """Real-time status display (refreshes every second)."""

    while True:
        os.system('cls')  # Clear screen

        # Get current state
        lockout_info = lockout_manager.get_lockout_info(account_id)
        positions = state_manager.get_current_positions(account_id)
        daily_pnl = pnl_tracker.get_daily_pnl(account_id)

        # Display header
        print("="*60)
        print(f"  RISK MANAGER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        # Display lockout status
        if lockout_info:
            time_remaining = lockout_info['expires_at'] - datetime.now()
            print(f"\n🔴 LOCKED OUT - {lockout_info['reason']}")
            print(f"   Unlocks in: {time_remaining}")
        else:
            print("\n🟢 OK TO TRADE")

        # Display P&L
        print(f"\nDaily P&L: ${daily_pnl['realized']:.2f} (Realized)")
        print(f"           ${daily_pnl['unrealized']:.2f} (Unrealized)")

        # Display positions
        print(f"\nOpen Positions: {len(positions)}")
        for pos in positions:
            print(f"  {pos['contract_id']}: {pos['size']} @ {pos['average_price']}")

        time.sleep(refresh_interval)
```

---

## 🚨 Error Handling & Reconnection

```python
# src/api/connection_manager.py

def handle_signalr_disconnect():
    """Reconnect to SignalR on disconnect."""
    logger.warning("SignalR connection lost - attempting reconnect")

    max_retries = 10
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            connection.start()
            logger.info("SignalR reconnected successfully")
            return
        except Exception as e:
            logger.error(f"Reconnect attempt {attempt+1} failed: {e}")
            time.sleep(retry_delay)

    # If all retries fail, send critical alert
    logger.critical("SignalR reconnection failed - RISK ENFORCEMENT OFFLINE")
    # Email/SMS alert here

def handle_rest_api_error(response):
    """Handle REST API errors gracefully."""
    if response.status_code == 429:  # Rate limit
        logger.warning("Rate limit hit - backing off")
        time.sleep(30)
    elif response.status_code == 401:  # Auth failed
        logger.warning("Auth failed - refreshing token")
        jwt_token = auth.authenticate()
    else:
        logger.error(f"API error: {response.status_code} - {response.text}")
```

---

## 📋 Complete Integration Checklist

| Component | Purpose | API Dependencies |
|-----------|---------|------------------|
| `auth.py` | JWT authentication | POST /api/Auth/loginKey, POST /api/Auth/validate |
| `signalr_listener.py` | Real-time events | SignalR User Hub (4 event types) |
| `rest_client.py` | Position/order actions | POST /api/Position/closeContract, POST /api/Order/cancel |
| `event_router.py` | Route events to rules | None (internal) |
| `enforcement_engine.py` | Execute enforcement | Calls MOD-001, MOD-002 |
| `persistence.py` | State save/load | SQLite (no API) |

---

**This pipeline ensures zero event loss, crash recovery, and sub-second enforcement.**
