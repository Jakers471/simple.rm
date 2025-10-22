# TopstepX API Quick Reference

**For:** Developers implementing the Simple Risk Manager
**Version:** 1.0
**Last Updated:** 2025-10-22

---

## Base URLs

```
REST API:    https://api.topstepx.com
User Hub:    wss://rtc.topstepx.com/hubs/user
Market Hub:  wss://rtc.topstepx.com/hubs/market
```

---

## Authentication

### Get JWT Token
```bash
curl -X POST https://api.topstepx.com/api/Auth/loginKey \
  -H 'Content-Type: application/json' \
  -d '{
    "userName": "your_username",
    "apiKey": "your_api_key"
  }'
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1...",
  "success": true,
  "errorCode": 0
}
```

**Token Expiry:** 24 hours

### Refresh Token
```bash
curl -X POST https://api.topstepx.com/api/Auth/validate \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

---

## REST API Endpoints

### Accounts
```javascript
// Get all active accounts
POST /api/Account/search
Body: { "onlyActiveAccounts": true }
```

### Orders
```javascript
// Place order
POST /api/Order/place
Body: {
  "accountId": 123,
  "contractId": "CON.F.US.EP.U25",
  "type": 2,        // 1=Limit, 2=Market, 4=Stop, 5=Trail
  "side": 0,        // 0=Buy, 1=Sell
  "size": 1,
  "limitPrice": 5100.00,  // Optional
  "stopLossBracket": {    // Optional
    "ticks": 10,
    "type": 1
  }
}

// Modify order
POST /api/Order/modify
Body: {
  "accountId": 123,
  "orderId": 456,
  "size": 2,
  "limitPrice": 5105.00
}

// Cancel order
POST /api/Order/cancel
Body: { "accountId": 123, "orderId": 456 }

// Get open orders
POST /api/Order/searchOpen
Body: { "accountId": 123 }

// Search orders by date
POST /api/Order/search
Body: {
  "accountId": 123,
  "startTimestamp": "2025-01-01T00:00:00Z",
  "endTimestamp": "2025-01-31T23:59:59Z"
}
```

### Positions
```javascript
// Get open positions
POST /api/Position/searchOpen
Body: { "accountId": 123 }

// Close entire position
POST /api/Position/closeContract
Body: {
  "accountId": 123,
  "contractId": "CON.F.US.EP.U25"
}

// Partially close position
POST /api/Position/partialCloseContract
Body: {
  "accountId": 123,
  "contractId": "CON.F.US.EP.U25",
  "size": 1
}
```

### Trades
```javascript
// Search trades
POST /api/Trade/search
Body: {
  "accountId": 123,
  "startTimestamp": "2025-01-01T00:00:00Z",
  "endTimestamp": "2025-01-31T23:59:59Z"
}
```

### Contracts
```javascript
// Get all available contracts
POST /api/Contract/available
Body: { "live": true }

// Search contracts
POST /api/Contract/search
Body: {
  "searchText": "ES",
  "live": true
}

// Get contract by ID
POST /api/Contract/searchById
Body: { "contractId": "CON.F.US.EP.U25" }
```

### Historical Data
```javascript
// Get OHLCV bars
POST /api/History/retrieveBars
Body: {
  "contractId": "CON.F.US.EP.U25",
  "live": true,
  "startTime": "2025-01-01T00:00:00Z",
  "endTime": "2025-01-31T23:59:59Z",
  "unit": 2,              // 1=Second, 2=Minute, 3=Hour, 4=Day
  "unitNumber": 5,        // 5-minute bars
  "limit": 1000,          // Max 20,000
  "includePartialBar": false
}
```

**Rate Limit:** 50 requests / 30 seconds

---

## SignalR Real-Time Events

### User Hub (Account/Order/Position Updates)

```javascript
const { HubConnectionBuilder, HttpTransportType } = require('@microsoft/signalr');

const connection = new HubConnectionBuilder()
  .withUrl('https://rtc.topstepx.com/hubs/user', {
    skipNegotiation: true,
    transport: HttpTransportType.WebSockets,
    accessTokenFactory: () => JWT_TOKEN
  })
  .withAutomaticReconnect([0, 2000, 10000, 30000])
  .build();

await connection.start();

// Subscribe to events
connection.invoke('SubscribeAccounts');
connection.invoke('SubscribeOrders', accountId);
connection.invoke('SubscribePositions', accountId);
connection.invoke('SubscribeTrades', accountId);

// Event handlers
connection.on('GatewayUserAccount', (account) => {
  console.log('Account update:', account);
  // { id, name, balance, canTrade, isVisible, simulated }
});

connection.on('GatewayUserOrder', (order) => {
  console.log('Order update:', order);
  // { id, accountId, contractId, status, type, side, size,
  //   limitPrice, fillVolume, filledPrice }
});

connection.on('GatewayUserPosition', (position) => {
  console.log('Position update:', position);
  // { id, accountId, contractId, type, size, averagePrice }
});

connection.on('GatewayUserTrade', (trade) => {
  console.log('Trade executed:', trade);
  // { id, accountId, contractId, price, profitAndLoss,
  //   fees, side, size, orderId }
});
```

### Market Hub (Market Data Updates)

```javascript
const marketConnection = new HubConnectionBuilder()
  .withUrl('https://rtc.topstepx.com/hubs/market', {
    skipNegotiation: true,
    transport: HttpTransportType.WebSockets,
    accessTokenFactory: () => JWT_TOKEN
  })
  .withAutomaticReconnect([0, 2000, 10000, 30000])
  .build();

await marketConnection.start();

// Subscribe to market data
marketConnection.invoke('SubscribeContractQuotes', contractId);
marketConnection.invoke('SubscribeContractTrades', contractId);
marketConnection.invoke('SubscribeContractMarketDepth', contractId);

// Event handlers
marketConnection.on('GatewayQuote', (contractId, quote) => {
  console.log('Quote update:', quote);
  // { symbol, lastPrice, bestBid, bestAsk, change,
  //   volume, high, low, open }
});

marketConnection.on('GatewayTrade', (contractId, trade) => {
  console.log('Trade:', trade);
  // { symbolId, price, volume, type, timestamp }
});

marketConnection.on('GatewayDepth', (contractId, depth) => {
  console.log('DOM update:', depth);
  // { timestamp, type, price, volume, currentVolume }
});
```

---

## Enums

```typescript
enum OrderType {
  Limit = 1,
  Market = 2,
  StopLimit = 3,
  Stop = 4,
  TrailingStop = 5,
  JoinBid = 6,
  JoinAsk = 7
}

enum OrderSide {
  Bid = 0,   // Buy
  Ask = 1    // Sell
}

enum OrderStatus {
  None = 0,
  Open = 1,
  Filled = 2,
  Cancelled = 3,
  Expired = 4,
  Rejected = 5,
  Pending = 6
}

enum PositionType {
  Undefined = 0,
  Long = 1,
  Short = 2
}

enum DomType {
  Unknown = 0,
  Ask = 1,
  Bid = 2,
  BestAsk = 3,
  BestBid = 4,
  Trade = 5
}
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/api/History/retrieveBars` | 50 requests / 30 seconds |
| All other endpoints | 200 requests / 60 seconds |

**Error Response:** HTTP 429 Too Many Requests

---

## Common Workflows

### Startup Sequence
```javascript
// 1. Authenticate
const { token } = await authenticate(userName, apiKey);

// 2. Get accounts
const { accounts } = await searchAccounts(true);
const accountId = accounts[0].id;

// 3. Connect SignalR
await userHub.start();
await marketHub.start();

// 4. Subscribe to user events
userHub.invoke('SubscribeAccounts');
userHub.invoke('SubscribeOrders', accountId);
userHub.invoke('SubscribePositions', accountId);

// 5. Load initial state
const positions = await searchOpenPositions(accountId);
const orders = await searchOpenOrders(accountId);

// 6. Subscribe to market data
for (const position of positions) {
  marketHub.invoke('SubscribeContractQuotes', position.contractId);
}
```

### Place Order with Brackets
```javascript
const order = {
  accountId: 123,
  contractId: "CON.F.US.EP.U25",
  type: 2,      // Market
  side: 0,      // Buy
  size: 1,
  stopLossBracket: {
    ticks: 10,  // 10 ticks stop loss
    type: 1     // Limit
  },
  takeProfitBracket: {
    ticks: 20,  // 20 ticks take profit
    type: 1     // Limit
  }
};

const result = await placeOrder(order);
console.log('Order ID:', result.orderId);

// Monitor via SignalR
userHub.on('GatewayUserOrder', handleOrderUpdate);
userHub.on('GatewayUserTrade', handleFill);
```

### Emergency Position Close
```javascript
// Close all positions for account
const positions = await searchOpenPositions(accountId);

for (const position of positions) {
  try {
    await closePosition(accountId, position.contractId);
    console.log(`Closed ${position.contractId}`);
  } catch (error) {
    console.error(`Failed to close ${position.contractId}:`, error);
  }
}

// Cancel all open orders
const orders = await searchOpenOrders(accountId);

for (const order of orders) {
  try {
    await cancelOrder(accountId, order.id);
    console.log(`Cancelled order ${order.id}`);
  } catch (error) {
    console.error(`Failed to cancel order ${order.id}:`, error);
  }
}
```

---

## Error Handling

### Standard Response Format
```json
{
  "success": true,
  "errorCode": 0,
  "errorMessage": null,
  "data": { ... }
}
```

### Common Errors
- **401 Unauthorized** - Invalid or expired token
- **429 Too Many Requests** - Rate limit exceeded
- **400 Bad Request** - Invalid parameters

### Recommended Retry Logic
```javascript
async function apiCallWithRetry(fn, maxRetries = 3) {
  const delays = [1000, 2000, 5000];

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429) {
        // Rate limited - wait longer
        await sleep(delays[i] || 5000);
      } else if (error.status === 401) {
        // Token expired - refresh
        await refreshToken();
        return await fn();
      } else if (i === maxRetries - 1) {
        // Last attempt failed
        throw error;
      }
      await sleep(delays[i] || 2000);
    }
  }
}
```

---

## Contract ID Format

Format: `CON.F.US.{SYMBOL}.{MONTH}{YEAR}`

Examples:
- `CON.F.US.EP.U25` - E-Mini S&P 500, September 2025
- `CON.F.US.ENQ.H25` - E-Mini NASDAQ, March 2025

**Month Codes:**
- F=Jan, G=Feb, H=Mar, J=Apr, K=May, M=Jun
- N=Jul, Q=Aug, U=Sep, V=Oct, X=Nov, Z=Dec

---

## Important Notes

1. **Token Security**: Never log tokens or include in URLs if possible
2. **Token Refresh**: Refresh proactively before 24h expiry
3. **SignalR Reconnection**: Implement all reconnection handlers
4. **Rate Limiting**: Implement client-side throttling
5. **Order Verification**: Always verify order status after placement
6. **Network Failures**: Implement idempotency checks
7. **Position Reconciliation**: Regularly reconcile local state with API

---

## Resources

- **Full Analysis**: `/reports/api-integration-analysis.md`
- **Module Integration**: `/reports/api-call-matrix.md`
- **API Specs**: `/project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/`

---

**Quick Reference Version:** 1.0
**For Questions:** Contact API Integration Specialist
