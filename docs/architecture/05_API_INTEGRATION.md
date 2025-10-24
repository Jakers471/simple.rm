# API Integration Architecture

**Document ID:** ARCH-005
**Version:** 1.0
**Last Updated:** 2025-10-23
**Status:** Final
**Agent:** API Integration Analyzer
**Swarm:** Integration Architecture Swarm

---

## Overview

This document describes how the Simple Risk Manager integrates with the TopstepX Gateway API to receive real-time trading events and execute enforcement actions. The system uses a dual-channel approach: **REST API** for commands (close positions, cancel orders) and **SignalR WebSockets** for real-time event streaming (trades, positions, orders, account updates).

**Integration Goals:**
1. **Real-time monitoring** - Receive trading events within milliseconds
2. **Reliable enforcement** - Execute risk actions (close positions, cancel orders) with retry logic
3. **Resilient connection** - Automatic reconnection with state reconciliation
4. **Rate-limited** - Client-side throttling to prevent API quota exhaustion
5. **Authenticated** - JWT token management with proactive refresh

---

## API Connection Details

### **Base URLs**
```yaml
REST API:        https://api.topstepx.com
SignalR User Hub:   https://rtc.topstepx.com/hubs/user
SignalR Market Hub: https://rtc.topstepx.com/hubs/market
```

### **Authentication**
- **Method:** JWT Bearer Token
- **Endpoint:** `POST /api/Auth/loginKey`
- **Token Lifetime:** 24 hours
- **Refresh Strategy:** Proactive refresh 2 hours before expiry (see TOKEN_REFRESH_STRATEGY_SPEC.md)

**Authentication Flow:**
```python
# Step 1: Authenticate with API key
payload = {"userName": username, "apiKey": api_key}
response = requests.post(f"{base_url}/api/Auth/loginKey", json=payload)
token = response.json()["token"]

# Step 2: Use token in all subsequent requests
headers = {"Authorization": f"Bearer {token}"}
```

---

## REST API Client

The REST client (`src/api/rest_client.py`) handles all outbound commands to TopstepX.

### **Endpoints Used**

| Endpoint | Method | Purpose | Retry on Failure |
|----------|--------|---------|------------------|
| `/api/Auth/loginKey` | POST | Authenticate, obtain JWT | Yes (3 attempts) |
| `/api/Position/closeContract` | POST | Close position | Yes (5 attempts) |
| `/api/Position/searchOpen` | POST | Get all open positions | Yes (3 attempts) |
| `/api/Order/place` | POST | Place stop-loss order | Yes (5 attempts) |
| `/api/Order/cancel` | POST | Cancel order | Yes (5 attempts) |
| `/api/Order/modify` | POST | Modify order (e.g., trailing stop) | Yes (3 attempts) |
| `/api/Order/searchOpen` | POST | Get all open orders | Yes (3 attempts) |
| `/api/Contract/searchById` | POST | Get contract metadata | Yes (3 attempts) |

### **REST Client Features**

**1. JWT Token Management**
```python
class RestClient:
    def __init__(self, base_url, username, api_key):
        self._token = None
        self._token_expiry = None  # Set to now + 1 hour after auth

    def is_authenticated(self):
        """Check if token is valid and not expired"""
        return self._token and self._token_expiry > datetime.now()
```

**2. Rate Limiting**
- **Limit:** 200 requests per 60 seconds (sliding window)
- **Implementation:** Client-side enforcement before sending requests
- **Strategy:** If limit reached, wait until oldest request expires

```python
def _enforce_rate_limit(self):
    """Sliding window rate limiter"""
    now = datetime.now()
    cutoff = now - timedelta(seconds=60)

    # Remove timestamps outside 60-second window
    self._request_timestamps = [ts for ts in self._request_timestamps if ts > cutoff]

    # If at limit, wait
    if len(self._request_timestamps) >= 200:
        wait_time = (oldest_timestamp + 60s - now).total_seconds()
        time.sleep(wait_time)
```

**3. Retry Logic with Exponential Backoff**
- **Max Retries:** 5 attempts for critical operations, 3 for queries
- **Backoff Formula:** `delay = 1 * (2 ^ attempt_number)` seconds
- **Retryable Errors:** 429 (Rate Limit), 500 (Server Error), 502/503/504 (Gateway Errors), Timeout
- **Non-Retryable Errors:** 400 (Bad Request), 401 (Unauthorized), 404 (Not Found)

```python
for attempt in range(MAX_RETRIES):
    try:
        response = self.session.post(url, json=payload, timeout=30)

        if response.status_code == 429:
            # Rate limit - wait and retry
            retry_after = int(response.headers.get('Retry-After', backoff))
            time.sleep(retry_after)
            continue

        if response.status_code >= 500:
            # Server error - exponential backoff
            backoff = INITIAL_BACKOFF * (2 ** attempt)
            time.sleep(backoff)
            continue

        return response.json()
    except Timeout:
        continue  # Retry on timeout
```

**4. Error Handling**
```python
# Custom exceptions defined in src/api/exceptions.py
AuthenticationError  # Token invalid/expired
APIError            # General API failure
RateLimitError      # Rate limit exceeded
NetworkError        # Timeout/connection failure
```

### **REST Client Usage Example**

```python
# Initialize
client = RestClient(
    base_url="https://api.topstepx.com",
    username="trader@example.com",
    api_key="YOUR_API_KEY"
)

# Authenticate
client.authenticate()

# Close position (with automatic retry)
try:
    success = client.close_position(
        account_id=123,
        contract_id="CON.F.US.MNQ.U25"
    )
except APIError as e:
    logger.error(f"Failed to close position: {e}")
```

---

## SignalR WebSocket Client

**SPECIFICATION GAP:** SignalR client not yet implemented.

The SignalR client will connect to TopstepX real-time hubs to receive trading events.

### **User Hub Events**

The User Hub provides account-specific events:

| Event Name | Description | Fields | Used By Rules |
|------------|-------------|--------|---------------|
| `GatewayUserTrade` | Trade execution | `id`, `accountId`, `contractId`, `price`, `profitAndLoss`, `fees`, `side`, `size`, `orderId` | RULE-003 (DailyRealizedLoss), RULE-006 (TradeFrequency), RULE-007 (CooldownAfterLoss) |
| `GatewayUserPosition` | Position update | `id`, `accountId`, `contractId`, `type` (1=Long, 2=Short), `size`, `averagePrice` | RULE-001 (MaxContracts), RULE-002 (MaxContractsPerInstrument), RULE-004 (DailyUnrealizedLoss), RULE-009 (SessionBlock), RULE-011 (SymbolBlocks) |
| `GatewayUserOrder` | Order update | `id`, `accountId`, `contractId`, `status`, `type`, `side`, `size`, `stopPrice`, `fillVolume` | RULE-008 (NoStopLossGrace) |
| `GatewayUserAccount` | Account update | `id`, `name`, `balance`, `canTrade`, `simulated` | RULE-010 (AuthLossGuard) |

**Event Payload Example (GatewayUserTrade):**
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

### **Market Hub Events**

The Market Hub provides real-time quotes:

| Event Name | Description | Fields | Used By Rules |
|------------|-------------|--------|---------------|
| `GatewayQuote` | Real-time price quote | `symbol`, `lastPrice`, `bestBid`, `bestAsk`, `change`, `volume`, `timestamp` | RULE-004 (DailyUnrealizedLoss), RULE-005 (MaxUnrealizedProfit), RULE-012 (TradeManagement) |

### **SignalR Connection Configuration**

```python
# PLANNED IMPLEMENTATION (not yet coded)
from signalrcore.hub_connection_builder import HubConnectionBuilder

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
```

### **SignalR Subscription Management**

After connecting, the client must subscribe to specific event streams:

```python
# Subscribe to account-specific events
connection.invoke("SubscribeAccounts")
connection.invoke("SubscribeOrders", account_id)
connection.invoke("SubscribePositions", account_id)
connection.invoke("SubscribeTrades", account_id)

# Register event handlers
connection.on("GatewayUserTrade", handle_trade_event)
connection.on("GatewayUserPosition", handle_position_event)
connection.on("GatewayUserOrder", handle_order_event)
connection.on("GatewayUserAccount", handle_account_event)

# Start connection
connection.start()
```

### **SignalR Reconnection Strategy**

**See:** `SIGNALR_RECONNECTION_SPEC.md`, `EXPONENTIAL_BACKOFF_SPEC.md`

**Reconnection Flow:**
1. **onreconnecting** - Mark connection as unstable, queue events
2. **onreconnected** - Re-subscribe to all events, reconcile state
3. **onclose** - If reconnection fails after 10 attempts, fall back to REST polling

```python
connection.onreconnected(async (connectionId) => {
    logger.info('SignalR reconnected, re-subscribing...')

    # Re-subscribe to events
    await resubscribe_to_all_events()

    # Reconcile state via REST API
    positions = await rest_client.search_open_positions(account_id)
    orders = await rest_client.search_open_orders(account_id)

    # Update local state
    state_manager.reconcile(positions, orders)
})
```

**State Reconciliation After Reconnection:**
- Fetch current positions via REST
- Fetch current orders via REST
- Update local state to match server truth
- Re-run risk checks on all positions

---

## Data Transformation with Converters

The TopstepX API sends **camelCase** responses. Our internal backend uses **snake_case**. Converters (`src/api/converters.py`) transform between these formats.

### **API Response Flow**

```
TopstepX API (camelCase)
  ↓
REST Client receives response
  ↓
Converter: api_to_internal_*()
  ↓
Internal format (snake_case)
  ↓
StateManager/Rules
```

### **SignalR Event Flow**

```
TopstepX SignalR Event (camelCase)
  ↓
SignalR Client receives event
  ↓
Converter: api_to_internal_*()
  ↓
Event Router
  ↓
StateManager/Rules
```

### **Converter Functions**

| Function | Input | Output |
|----------|-------|--------|
| `api_to_internal_account()` | API account JSON | Internal account dict |
| `api_to_internal_order()` | API order JSON | Internal order dict |
| `api_to_internal_position()` | API position JSON | Internal position dict |
| `api_to_internal_trade()` | API trade JSON | Internal trade dict |
| `api_to_internal_contract()` | API contract JSON | Internal contract dict |
| `api_to_internal_quote()` | API quote JSON | Internal quote dict |
| `internal_to_api_order_request()` | Internal order dict | API request JSON |
| `internal_to_api_position_close_request()` | Internal close dict | API request JSON |

**Example:**

```python
# API response (camelCase)
api_position = {
    "id": 456,
    "accountId": 123,
    "contractId": "CON.F.US.MNQ.U25",
    "type": 1,  # 1=Long
    "size": 2,
    "averagePrice": 21000.25
}

# Convert to internal format (snake_case)
from src.api.converters import api_to_internal_position

internal_position = api_to_internal_position(api_position)
# {
#     "position_id": 456,
#     "account_id": 123,
#     "contract_id": "CON.F.US.MNQ.U25",
#     "position_type": "long",
#     "quantity": 2,
#     "average_price": 21000.25,
#     "unrealized_pnl": 0.0
# }
```

### **Enum Conversions**

The converters also handle enum transformations (`src/api/enums.py`):

**Order Side:**
- API: `0` = Buy, `1` = Sell
- Internal: `"buy"`, `"sell"`

**Position Type:**
- API: `1` = Long, `2` = Short
- Internal: `"long"`, `"short"`

**Order State:**
- API: `0` = None, `1` = Open, `2` = Filled, `3` = Cancelled, `4` = Expired, `5` = Rejected, `6` = Pending
- Internal: `InternalOrderState.PENDING`, `ACTIVE`, `FILLED`, `CANCELLED`, `REJECTED`, `EXPIRED`

```python
from src.api.enums import api_to_internal_order_side, api_to_internal_position_type

side = api_to_internal_order_side(0)  # Returns "buy"
position_type = api_to_internal_position_type(1)  # Returns "long"
```

---

## Error Handling & Resilience

### **Authentication Errors**
- **Scenario:** Token expires during operation
- **Response:**
  1. Attempt token refresh via `/api/Auth/validate`
  2. If refresh fails, re-authenticate with API key
  3. Retry original request with new token
  4. If re-auth fails after 3 attempts, alert and halt

**See:** `TOKEN_REFRESH_STRATEGY_SPEC.md`

### **Rate Limiting**
- **Limit:** 200 requests / 60 seconds (general), 50 requests / 30 seconds (retrieveBars)
- **Client-side enforcement:** Wait before sending if limit reached
- **Server-side response:** 429 status code with `Retry-After` header
- **Action:** Exponential backoff with jitter

**See:** `RATE_LIMITING_SPEC.md`

### **Network Failures**
- **Scenarios:** Timeout, connection refused, DNS failure
- **Response:**
  1. Retry with exponential backoff (1s, 2s, 4s, 8s, 16s)
  2. After 5 retries, log error and fail request
  3. For critical operations (close position), alert trader

**See:** `RETRY_STRATEGY_SPEC.md`, `CIRCUIT_BREAKER_SPEC.md`

### **SignalR Disconnection**
- **Auto-reconnect:** Built-in exponential backoff (0s, 2s, 10s, 30s, 60s)
- **After reconnection:** Re-subscribe to events, reconcile state
- **If reconnection fails after 10 attempts:** Fall back to REST polling every 5 seconds

**See:** `SIGNALR_RECONNECTION_SPEC.md`, `STATE_RECONCILIATION_SPEC.md`

### **Partial Failures**
- **Scenario:** Close 3 positions, 1 fails
- **Response:**
  1. Continue closing remaining positions
  2. Log failed position
  3. Return partial success with failed IDs
  4. Alert trader to manually close failed position

---

## Integration Points

### **Where API Clients Connect to System**

```
REST Client (src/api/rest_client.py)
  ↓
Called by Enforcement Engine (src/enforcement/enforcement_engine.py)
  ↓
Which is triggered by Rules (src/rules/*)
  ↓
Which are fed by Event Router (src/core/event_router.py)
  ↓
Which receives events from SignalR Client (NOT YET IMPLEMENTED)
```

**Enforcement Actions → REST Client:**
```python
# In src/enforcement/enforcement_engine.py
from src.api.rest_client import RestClient

def close_all_positions(account_id):
    positions = rest_client.search_open_positions(account_id)

    for position in positions:
        try:
            rest_client.close_position(account_id, position.contract_id)
        except APIError as e:
            logger.error(f"Failed to close {position.contract_id}: {e}")
```

**SignalR Events → Event Router:**
```python
# PLANNED: In src/api/signalr_client.py (not yet implemented)
def handle_trade_event(trade_data):
    # Convert from API format to internal format
    internal_trade = api_to_internal_trade(trade_data)

    # Route to event router
    event_router.route_event("trade", internal_trade)
```

**Event Router → State Manager + Rules:**
```python
# In src/core/event_router.py (PLANNED)
def route_event(event_type, event_data):
    # Update state
    if event_type == "trade":
        state_manager.record_trade(event_data)

    # Check rules
    for rule in active_rules:
        if rule.applies_to(event_type):
            action = rule.check(event_data)
            if action:
                enforcement_engine.execute(action)
```

---

## Connection Lifecycle

### **Startup Sequence**

```
1. Load configuration (config.yaml)
   ↓
2. Create REST client with credentials
   ↓
3. Authenticate and obtain JWT token
   ↓
4. Create SignalR client with JWT token
   ↓
5. Connect to User Hub and Market Hub
   ↓
6. Subscribe to account events (SubscribeOrders, SubscribePositions, etc.)
   ↓
7. Fetch initial state via REST (positions, orders, account)
   ↓
8. Start event loop (process SignalR events, run risk checks)
```

**Implementation (PLANNED):**
```python
# In src/core/daemon.py
def startup():
    # REST authentication
    rest_client = RestClient(config.api_base_url, config.username, config.api_key)
    rest_client.authenticate()

    # SignalR connection
    signalr_client = SignalRClient(config.signalr_base_url, rest_client.token)
    signalr_client.connect()
    signalr_client.subscribe_to_account(config.account_id)

    # Initial state sync
    positions = rest_client.search_open_positions(config.account_id)
    orders = rest_client.search_open_orders(config.account_id)
    state_manager.initialize(positions, orders)

    # Start event loop
    run_event_loop()
```

### **Maintaining Connection**

- **JWT Token:** Refresh 2 hours before expiry (proactive)
- **SignalR Connection:** Keep-alive ping every 10 seconds
- **State Sync:** Reconcile every 60 seconds via REST (fallback)

### **Reconnection After Disruption**

```
SignalR Disconnection Detected
  ↓
Attempt Auto-Reconnect (exponential backoff)
  ↓
If reconnect succeeds:
  - Re-subscribe to events
  - Reconcile state via REST
  - Resume normal operation
  ↓
If reconnect fails after 10 attempts:
  - Fall back to REST polling (every 5 seconds)
  - Alert trader of degraded mode
```

---

## SPECS Files Analyzed

This document is based on analysis of the following specification files:

### **API Integration Specs**
- `/project-specs/SPECS/01-EXTERNAL-API/api/topstepx_integration.md` - Complete event pipeline
- `/project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/getting_started/authenticate_api_key.md` - Authentication flow
- `/project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/getting_started/connection_urls.md` - Endpoints
- `/project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/realtime_updates/realtime_data_overview.md` - SignalR events
- `/project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/orders/place_order.md` - Order placement
- `/project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/positions/close_positions.md` - Position closing

### **Error Handling & Resilience Specs**
- `/project-specs/SPECS/01-EXTERNAL-API/error-handling/RETRY_STRATEGY_SPEC.md` - Retry logic, exponential backoff
- `/project-specs/SPECS/01-EXTERNAL-API/error-handling/RATE_LIMITING_SPEC.md` - Rate limit handling
- `/project-specs/SPECS/01-EXTERNAL-API/security/TOKEN_REFRESH_STRATEGY_SPEC.md` - JWT token management
- `/project-specs/SPECS/01-EXTERNAL-API/signalr/SIGNALR_RECONNECTION_SPEC.md` - SignalR reconnection
- `/project-specs/SPECS/01-EXTERNAL-API/signalr/SIGNALR_EVENT_SUBSCRIPTION_SPEC.md` - Event subscription management
- `/project-specs/SPECS/01-EXTERNAL-API/signalr/STATE_RECONCILIATION_SPEC.md` - State reconciliation after reconnection

### **Implementation Files**
- `/src/api/rest_client.py` - REST client implementation (COMPLETED)
- `/src/api/converters.py` - API ↔ Internal data conversion (COMPLETED)
- `/src/api/enums.py` - Enum mappings (COMPLETED)
- `/src/api/exceptions.py` - API exception hierarchy (PARTIAL)

---

## Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| **REST Client** | ✅ COMPLETE | `src/api/rest_client.py` |
| **Converters** | ✅ COMPLETE | `src/api/converters.py` |
| **Enums** | ✅ COMPLETE | `src/api/enums.py` |
| **Exceptions** | ⚠️ PARTIAL | `src/api/exceptions.py` |
| **SignalR Client** | ❌ NOT STARTED | N/A |
| **Event Router** | ❌ NOT STARTED | N/A |
| **Token Refresh** | ⚠️ BASIC | `rest_client.py` (1-hour expiry, no proactive refresh) |
| **Rate Limiter** | ✅ COMPLETE | `rest_client.py` (sliding window) |
| **Retry Logic** | ✅ COMPLETE | `rest_client.py` (exponential backoff) |
| **State Reconciliation** | ❌ NOT STARTED | N/A |

---

## Next Steps for Implementation

### **High Priority**
1. Implement SignalR Client (`src/api/signalr_client.py`)
2. Implement Event Router (`src/core/event_router.py`)
3. Implement State Reconciliation logic
4. Upgrade Token Refresh to proactive 2-hour strategy

### **Medium Priority**
5. Implement Circuit Breaker pattern
6. Expand Exception hierarchy with error codes
7. Add telemetry/metrics for API calls

### **Low Priority**
8. Implement REST polling fallback mode
9. Add API response caching for quotes
10. Optimize rate limiter with request prioritization

---

**End of Document**
