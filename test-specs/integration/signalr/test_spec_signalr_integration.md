# SignalR WebSocket Integration Test Specification

**Generated:** 2025-10-22
**Purpose:** Integration test specifications for SignalR real-time WebSocket connections
**Test File:** `tests/integration/test_signalr_integration.py`
**Priority:** High (Critical for real-time event processing)

---

## Overview

This document specifies integration tests for the SignalR WebSocket implementation that connects to TopstepX Gateway API real-time hubs. These tests verify connection establishment, event subscription, payload parsing, reconnection logic, and authentication.

**SignalR Hubs:**
- **User Hub:** `wss://rtc.topstepx.com/hubs/user` (account, order, position, trade events)
- **Market Hub:** `wss://rtc.topstepx.com/hubs/market` (quote, depth, trade events)

**Technology:** Microsoft SignalR WebSocket protocol with JWT authentication

---

## Test Scenario Index

| Test ID | Scenario | Priority |
|---------|----------|----------|
| IT-SIG-001 | Connect to User Hub with valid JWT | High |
| IT-SIG-002 | Connect to Market Hub with valid JWT | High |
| IT-SIG-003 | Connection fails with invalid JWT | High |
| IT-SIG-004 | Subscribe to GatewayUserTrade events | High |
| IT-SIG-005 | Subscribe to GatewayUserPosition events | High |
| IT-SIG-006 | Subscribe to GatewayUserOrder events | High |
| IT-SIG-007 | Subscribe to GatewayQuote events | High |
| IT-SIG-008 | Parse GatewayUserTrade event payload | High |
| IT-SIG-009 | Parse GatewayUserPosition event payload | High |
| IT-SIG-010 | Auto-reconnect after connection drop | Critical |
| IT-SIG-011 | Exponential backoff on connection failure | High |
| IT-SIG-012 | Resubscribe to events after reconnection | Critical |

**Total Scenarios:** 12

---

## IT-SIG-001: Connect to User Hub with Valid JWT

**Test ID:** IT-SIG-001
**Priority:** High
**Category:** Connection Establishment

### Description
Verify that the SignalR client successfully connects to the User Hub using a valid JWT token obtained from the authentication endpoint.

### Given
- Valid API key and username credentials
- JWT token obtained via `POST /api/Auth/loginKey`
- User Hub URL: `wss://rtc.topstepx.com/hubs/user`
- WebSocket transport type configured
- Connection timeout set to 10 seconds

### When
1. Initialize HubConnectionBuilder with User Hub URL
2. Configure connection with:
   - `skipNegotiation: true`
   - `transport: HttpTransportType.WebSockets`
   - `accessTokenFactory: () => JWT_TOKEN`
   - `timeout: 10000`
3. Enable `withAutomaticReconnect()`
4. Call `rtcConnection.start()`

### Then
- Connection state transitions to `CONNECTED`
- No exceptions thrown during connection
- Connection ID is assigned
- Connection is ready to invoke hub methods
- Connection logged in application logs

### Test Data
```python
# Mock JWT token structure
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
USER_HUB_URL = "wss://rtc.topstepx.com/hubs/user"
ACCOUNT_ID = 123
```

### Assertions
```python
assert connection.state == HubConnectionState.CONNECTED
assert connection.connection_id is not None
assert connection.transport == "WebSockets"
```

---

## IT-SIG-002: Connect to Market Hub with Valid JWT

**Test ID:** IT-SIG-002
**Priority:** High
**Category:** Connection Establishment

### Description
Verify that the SignalR client successfully connects to the Market Hub for real-time quote data.

### Given
- Valid JWT token
- Market Hub URL: `wss://rtc.topstepx.com/hubs/market`
- Contract ID for subscription: `CON.F.US.EP.U25`
- WebSocket configuration identical to User Hub

### When
1. Initialize HubConnectionBuilder with Market Hub URL
2. Configure connection with same parameters as User Hub
3. Call `rtcConnection.start()`

### Then
- Connection state transitions to `CONNECTED`
- Connection ID assigned
- Ready to subscribe to market data streams
- Independent connection from User Hub

### Test Data
```python
MARKET_HUB_URL = "wss://rtc.topstepx.com/hubs/market"
CONTRACT_ID = "CON.F.US.EP.U25"
```

### Assertions
```python
assert connection.state == HubConnectionState.CONNECTED
assert connection.connection_id is not None
assert connection != user_hub_connection  # Independent connection
```

---

## IT-SIG-003: Connection Fails with Invalid JWT

**Test ID:** IT-SIG-003
**Priority:** High
**Category:** Authentication

### Description
Verify that connection fails gracefully when an invalid or expired JWT token is provided.

### Given
- Invalid JWT token (expired, malformed, or revoked)
- User Hub URL
- Connection timeout: 10 seconds

### When
1. Initialize HubConnectionBuilder with invalid JWT
2. Attempt to call `rtcConnection.start()`

### Then
- Connection fails with authentication error
- Exception raised: `HubConnectionError` or `AuthenticationException`
- Error message indicates authentication failure
- Connection state remains `DISCONNECTED`
- Application logs error with token validation failure

### Test Data
```python
INVALID_JWT = "invalid.token.here"
EXPIRED_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired..."
```

### Assertions
```python
with pytest.raises((HubConnectionError, AuthenticationException)):
    await connection.start()
assert connection.state == HubConnectionState.DISCONNECTED
```

---

## IT-SIG-004: Subscribe to GatewayUserTrade Events

**Test ID:** IT-SIG-004
**Priority:** High
**Category:** Event Subscription

### Description
Verify that the client successfully subscribes to trade events and receives them in real-time.

### Given
- Connected User Hub
- Account ID: 123
- Event handler registered for `GatewayUserTrade`

### When
1. Call `rtcConnection.invoke('SubscribeTrades', ACCOUNT_ID)`
2. Register event handler:
   ```python
   rtcConnection.on('GatewayUserTrade', handle_trade_event)
   ```
3. Trigger a trade event (via API or manual trade)

### Then
- Subscription confirmed (no error returned)
- Event handler receives `GatewayUserTrade` event
- Event payload contains expected fields
- Event is received within 500ms of occurrence

### Test Data
```python
ACCOUNT_ID = 123
EXPECTED_TRADE_FIELDS = [
    'id', 'accountId', 'contractId', 'creationTimestamp',
    'price', 'profitAndLoss', 'fees', 'side', 'size',
    'voided', 'orderId'
]
```

### Assertions
```python
assert subscription_result is None  # Success returns None
assert trade_event_received is True
assert all(field in trade_event for field in EXPECTED_TRADE_FIELDS)
assert trade_event['accountId'] == ACCOUNT_ID
```

---

## IT-SIG-005: Subscribe to GatewayUserPosition Events

**Test ID:** IT-SIG-005
**Priority:** High
**Category:** Event Subscription

### Description
Verify subscription to position updates for real-time position tracking.

### Given
- Connected User Hub
- Account ID: 123
- Event handler for `GatewayUserPosition`

### When
1. Call `rtcConnection.invoke('SubscribePositions', ACCOUNT_ID)`
2. Register event handler:
   ```python
   rtcConnection.on('GatewayUserPosition', handle_position_event)
   ```
3. Open a new position or update existing position

### Then
- Subscription successful
- Position event received with correct structure
- Event payload matches specification
- Multiple position updates received for active positions

### Test Data
```python
EXPECTED_POSITION_FIELDS = [
    'id', 'accountId', 'contractId', 'creationTimestamp',
    'type', 'size', 'averagePrice'
]
```

### Assertions
```python
assert position_event_received is True
assert all(field in position_event for field in EXPECTED_POSITION_FIELDS)
assert position_event['accountId'] == ACCOUNT_ID
assert position_event['type'] in [1, 2]  # Long or Short
```

---

## IT-SIG-006: Subscribe to GatewayUserOrder Events

**Test ID:** IT-SIG-006
**Priority:** High
**Category:** Event Subscription

### Description
Verify subscription to order updates for real-time order state tracking.

### Given
- Connected User Hub
- Account ID: 123
- Event handler for `GatewayUserOrder`

### When
1. Call `rtcConnection.invoke('SubscribeOrders', ACCOUNT_ID)`
2. Register event handler:
   ```python
   rtcConnection.on('GatewayUserOrder', handle_order_event)
   ```
3. Place a new order via REST API

### Then
- Subscription confirmed
- Order event received when order is placed
- Event contains all order details
- Order status updates received (OPEN -> FILLED/CANCELLED)

### Test Data
```python
EXPECTED_ORDER_FIELDS = [
    'id', 'accountId', 'contractId', 'symbolId',
    'creationTimestamp', 'updateTimestamp', 'status',
    'type', 'side', 'size', 'limitPrice', 'stopPrice',
    'fillVolume', 'filledPrice', 'customTag'
]
```

### Assertions
```python
assert order_event_received is True
assert all(field in order_event for field in EXPECTED_ORDER_FIELDS)
assert order_event['status'] in [0, 1, 2, 3, 4, 5, 6]  # Valid OrderStatus
```

---

## IT-SIG-007: Subscribe to GatewayQuote Events

**Test ID:** IT-SIG-007
**Priority:** High
**Category:** Event Subscription

### Description
Verify subscription to market quotes for real-time price tracking.

### Given
- Connected Market Hub
- Contract ID: `CON.F.US.EP.U25`
- Event handler for `GatewayQuote`

### When
1. Call `rtcConnection.invoke('SubscribeContractQuotes', CONTRACT_ID)`
2. Register event handler:
   ```python
   rtcConnection.on('GatewayQuote', handle_quote_event)
   ```
3. Wait for market quote updates

### Then
- Subscription successful
- Quote events received continuously
- Event payload contains bid/ask/last prices
- Quotes received at market data frequency (10-100ms)

### Test Data
```python
CONTRACT_ID = "CON.F.US.EP.U25"
EXPECTED_QUOTE_FIELDS = [
    'symbol', 'symbolName', 'lastPrice', 'bestBid',
    'bestAsk', 'change', 'changePercent', 'open',
    'high', 'low', 'volume', 'lastUpdated', 'timestamp'
]
```

### Assertions
```python
assert quote_event_received is True
assert all(field in quote_event for field in EXPECTED_QUOTE_FIELDS)
assert quote_event['bestBid'] <= quote_event['lastPrice'] <= quote_event['bestAsk']
```

---

## IT-SIG-008: Parse GatewayUserTrade Event Payload

**Test ID:** IT-SIG-008
**Priority:** High
**Category:** Event Parsing

### Description
Verify that GatewayUserTrade events are correctly parsed into application data structures.

### Given
- Connected User Hub
- Trade event received:
```json
{
  "id": 101112,
  "accountId": 123,
  "contractId": "CON.F.US.EP.U25",
  "creationTimestamp": "2024-07-21T13:47:00Z",
  "price": 2100.75,
  "profitAndLoss": 50.25,
  "fees": 2.50,
  "side": 0,
  "size": 1,
  "voided": false,
  "orderId": 789
}
```

### When
1. Event handler receives trade event
2. Parse event into `TradeEvent` object
3. Validate all fields

### Then
- All fields correctly mapped to object attributes
- Numeric fields parsed as correct types (int, float)
- Timestamp parsed to datetime object
- Enum values (side) correctly interpreted
- Boolean flags correctly parsed

### Test Data
```python
TRADE_EVENT_PAYLOAD = {
    "id": 101112,
    "accountId": 123,
    "contractId": "CON.F.US.EP.U25",
    "creationTimestamp": "2024-07-21T13:47:00Z",
    "price": 2100.75,
    "profitAndLoss": 50.25,
    "fees": 2.50,
    "side": 0,
    "size": 1,
    "voided": False,
    "orderId": 789
}
```

### Assertions
```python
trade = parse_trade_event(TRADE_EVENT_PAYLOAD)
assert trade.id == 101112
assert trade.account_id == 123
assert trade.price == 2100.75
assert isinstance(trade.creation_timestamp, datetime)
assert trade.side == OrderSide.BID
assert trade.voided is False
```

---

## IT-SIG-009: Parse GatewayUserPosition Event Payload

**Test ID:** IT-SIG-009
**Priority:** High
**Category:** Event Parsing

### Description
Verify correct parsing of position events including position type (long/short) enumeration.

### Given
- Connected User Hub
- Position event received:
```json
{
  "id": 456,
  "accountId": 123,
  "contractId": "CON.F.US.EP.U25",
  "creationTimestamp": "2024-07-21T13:45:00Z",
  "type": 1,
  "size": 2,
  "averagePrice": 2100.25
}
```

### When
1. Event handler receives position event
2. Parse into `PositionEvent` object
3. Validate position type enumeration

### Then
- Position type correctly interpreted (1 = Long, 2 = Short)
- Size parsed as integer
- Average price parsed as float
- Timestamp converted to datetime
- Contract ID correctly extracted

### Test Data
```python
POSITION_EVENT_PAYLOAD = {
    "id": 456,
    "accountId": 123,
    "contractId": "CON.F.US.EP.U25",
    "creationTimestamp": "2024-07-21T13:45:00Z",
    "type": 1,
    "size": 2,
    "averagePrice": 2100.25
}
```

### Assertions
```python
position = parse_position_event(POSITION_EVENT_PAYLOAD)
assert position.id == 456
assert position.type == PositionType.LONG
assert position.size == 2
assert position.average_price == 2100.25
assert isinstance(position.creation_timestamp, datetime)
```

---

## IT-SIG-010: Auto-Reconnect After Connection Drop

**Test ID:** IT-SIG-010
**Priority:** Critical
**Category:** Reconnection Logic

### Description
Verify that SignalR automatically reconnects after a connection drop and resumes monitoring.

### Given
- Established User Hub connection
- Active event subscriptions
- Connection configured with `.withAutomaticReconnect()`

### When
1. Connection established and subscriptions active
2. Simulate connection drop (network disconnect, server restart)
3. Wait for automatic reconnection

### Then
- `onreconnecting` event handler triggered
- Connection attempts reconnection automatically
- `onreconnected` event handler triggered with new connection ID
- Connection state returns to `CONNECTED`
- Reconnection occurs within 5 seconds
- Application logs reconnection events

### Test Data
```python
RECONNECT_TIMEOUT = 5  # seconds
```

### Assertions
```python
assert reconnecting_triggered is True
assert reconnected_triggered is True
assert connection.state == HubConnectionState.CONNECTED
assert reconnection_time < RECONNECT_TIMEOUT
assert new_connection_id != old_connection_id
```

---

## IT-SIG-011: Exponential Backoff on Connection Failure

**Test ID:** IT-SIG-011
**Priority:** High
**Category:** Reconnection Logic

### Description
Verify that reconnection attempts use exponential backoff to avoid overwhelming the server.

### Given
- Disconnected SignalR connection
- Server unavailable or rejecting connections
- `.withAutomaticReconnect([0, 2000, 5000, 10000])` configured

### When
1. Initial connection fails
2. Automatic reconnection attempts triggered

### Then
- First retry attempted immediately (0ms delay)
- Second retry after 2 seconds
- Third retry after 5 seconds
- Fourth retry after 10 seconds
- Delays increase exponentially
- Application logs retry attempts with timing

### Test Data
```python
RETRY_DELAYS = [0, 2000, 5000, 10000]  # milliseconds
```

### Assertions
```python
assert retry_attempts == len(RETRY_DELAYS)
assert retry_delays[0] < 100  # Immediate
assert 1800 <= retry_delays[1] <= 2200  # ~2 seconds
assert 4800 <= retry_delays[2] <= 5200  # ~5 seconds
assert 9800 <= retry_delays[3] <= 10200  # ~10 seconds
```

---

## IT-SIG-012: Resubscribe to Events After Reconnection

**Test ID:** IT-SIG-012
**Priority:** Critical
**Category:** Reconnection Logic

### Description
Verify that all event subscriptions are automatically restored after reconnection.

### Given
- Connected User Hub and Market Hub
- Active subscriptions:
  - SubscribeTrades(123)
  - SubscribePositions(123)
  - SubscribeOrders(123)
  - SubscribeContractQuotes("CON.F.US.EP.U25")
- Connection dropped and reconnected

### When
1. Establish connection and subscriptions
2. Store subscription state
3. Simulate connection drop
4. Wait for automatic reconnection
5. `onreconnected` handler invokes resubscription logic

### Then
- All subscriptions automatically re-invoked
- Subscription methods called in correct order
- Events resume flowing after reconnection
- No events missed (or gap detected and logged)
- Application logs resubscription actions

### Test Data
```python
SUBSCRIPTIONS = [
    ('SubscribeTrades', 123),
    ('SubscribePositions', 123),
    ('SubscribeOrders', 123),
    ('SubscribeContractQuotes', 'CON.F.US.EP.U25')
]
```

### Assertions
```python
assert reconnected is True
for method, arg in SUBSCRIPTIONS:
    assert subscription_invoked(method, arg) is True
assert trade_events_resumed is True
assert position_events_resumed is True
assert order_events_resumed is True
assert quote_events_resumed is True
```

---

## Test Execution Requirements

### Test Infrastructure

**Required Services:**
- TopstepX Gateway API (staging or production)
- Valid test account credentials
- Network connectivity to `rtc.topstepx.com`

**Required Libraries:**
```python
pytest
pytest-asyncio
signalrcore  # Python SignalR client
websockets
aiohttp
```

**Mock/Stub Requirements:**
- JWT token generator for testing
- Mock SignalR server for connection failure tests
- Network simulation tools for reconnection tests

### Test Data Setup

**Authentication:**
```python
# Obtain JWT token before tests
response = requests.post(
    "https://api.topstepx.com/api/Auth/loginKey",
    json={"userName": TEST_USERNAME, "apiKey": TEST_API_KEY}
)
JWT_TOKEN = response.json()['token']
```

**Test Accounts:**
- Account ID: 123 (or from test environment)
- Valid contract IDs: CON.F.US.EP.U25, CON.F.US.MNQ.U25

### Expected Test Durations

| Test ID | Estimated Duration |
|---------|-------------------|
| IT-SIG-001 | 5 seconds |
| IT-SIG-002 | 5 seconds |
| IT-SIG-003 | 3 seconds |
| IT-SIG-004 | 10 seconds |
| IT-SIG-005 | 10 seconds |
| IT-SIG-006 | 10 seconds |
| IT-SIG-007 | 15 seconds |
| IT-SIG-008 | 2 seconds |
| IT-SIG-009 | 2 seconds |
| IT-SIG-010 | 30 seconds |
| IT-SIG-011 | 60 seconds |
| IT-SIG-012 | 45 seconds |

**Total Suite Duration:** ~3-5 minutes

---

## Integration with System Components

### State Manager Integration
- Position events update `StateManager` position cache
- Order events update `StateManager` order cache
- Trade events trigger P&L calculations

### Quote Tracker Integration
- GatewayQuote events update `QuoteTracker`
- Quote age tracking for staleness detection
- Quote subscription management per contract

### Event Router Integration
- All events routed to `EventRouter.route_event()`
- Events trigger risk rule checks
- Enforcement actions taken on rule breaches

---

## Error Scenarios

### Connection Errors
- Network timeout during connection
- Server unavailable (503)
- Invalid WebSocket upgrade
- SSL/TLS certificate errors

### Subscription Errors
- Subscribe to non-existent account
- Subscribe without authentication
- Subscribe to invalid contract ID
- Subscription after connection closed

### Event Processing Errors
- Malformed JSON payload
- Missing required fields
- Invalid enum values
- Timestamp parsing errors

---

## Success Criteria

### Definition of Success
- All 12 test scenarios pass consistently
- Connection established within 5 seconds
- Events received within 500ms of occurrence
- Reconnection successful within 5 seconds
- Zero event loss during reconnection
- All payloads correctly parsed

### Performance Targets
- Connection latency: < 2 seconds
- Event processing latency: < 10ms
- Reconnection time: < 5 seconds
- Memory usage: < 50 MB per connection
- CPU usage: < 5% during normal operation

---

## Related Specifications

- `/project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/realtime_updates/realtime_data_overview.md`
- `/project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/getting_started/authenticate_api_key.md`
- `/project-specs/SPECS/06-EVENT-ROUTER/event_router_spec.md`
- `/reports/2025-10-22-spec-governance/04-testing/TEST_SCENARIO_MATRIX.md`

---

## Document Status

- **Completeness:** 100%
- **Implementation Ready:** Yes
- **Review Status:** Pending
- **Last Updated:** 2025-10-22

---

**End of SignalR Integration Test Specification**
