# API Call Matrix - Module to Endpoint Mapping

**Generated:** 2025-10-22
**Purpose:** Map which application modules call which TopstepX API endpoints

---

## Module Architecture

```
Simple Risk Manager Application
│
├── Authentication Module
│   └── Handles JWT token lifecycle
│
├── Risk Manager Module
│   └── Core risk management logic
│
├── Order Execution Module
│   └── Order placement and management
│
├── Market Data Module
│   └── Real-time and historical data
│
└── Position Monitoring Module
    └── Track and manage positions
```

---

## 1. Authentication Module

### Endpoints Used

| Endpoint | Method | Purpose | Frequency | Critical |
|----------|--------|---------|-----------|----------|
| `/api/Auth/loginKey` | POST | Initial authentication | Once per session | YES |
| `/api/Auth/validate` | POST | Token refresh | Every ~22 hours | YES |

### Calling Sequence

```javascript
// On Application Startup
1. POST /api/Auth/loginKey
   Input: { userName, apiKey }
   Output: { token, success, errorCode }

// Before Token Expiry (24h)
2. POST /api/Auth/validate
   Input: { } (token in headers)
   Output: { newToken, success }
```

### Data Flow

```
[API Key Storage]
      │
      ▼
┌─────────────────┐
│  loginKey()     │──────▶ JWT Token (24h TTL)
└─────────────────┘          │
                             ▼
                      [Token Storage]
                             │
                             ├──────▶ [All REST Calls]
                             └──────▶ [SignalR Connections]

      ⏰ Before 24h Expiry
                             │
                             ▼
                      ┌──────────────┐
                      │ validate()   │──────▶ New JWT Token
                      └──────────────┘
```

### Dependencies
- Required for: ALL other modules
- Depends on: None (entry point)

---

## 2. Risk Manager Module

### Endpoints Used

| Endpoint | Method | Purpose | Frequency | Critical |
|----------|--------|---------|-----------|----------|
| `/api/Account/search` | POST | Get account list | Startup, Account change | YES |
| `/api/Position/searchOpen` | POST | Get current positions | On-demand, Startup | YES |
| `/api/Order/searchOpen` | POST | Get active orders | On-demand, Startup | YES |
| `/api/Position/closeContract` | POST | Emergency position close | On risk breach | YES |
| `/api/Position/partialCloseContract` | POST | Reduce position size | On risk adjustment | YES |
| `/api/Order/cancel` | POST | Cancel pending orders | On risk breach | YES |
| **SignalR User Hub** | WebSocket | Real-time updates | Continuous | YES |

### SignalR Subscriptions

```javascript
// User Hub Connection
const userHub = new HubConnection('wss://rtc.topstepx.com/hubs/user');

// Subscribe to Events
userHub.invoke('SubscribeAccounts');
userHub.invoke('SubscribePositions', accountId);
userHub.invoke('SubscribeOrders', accountId);
userHub.invoke('SubscribeTrades', accountId);

// Event Handlers
userHub.on('GatewayUserAccount', handleAccountUpdate);
userHub.on('GatewayUserPosition', handlePositionUpdate);
userHub.on('GatewayUserOrder', handleOrderUpdate);
userHub.on('GatewayUserTrade', handleTradeUpdate);
```

### Calling Sequence

```javascript
// Startup Sequence
1. POST /api/Account/search
   → Get list of trading accounts
   → Select active account

2. Connect SignalR User Hub
   → Subscribe to account updates
   → Subscribe to position updates
   → Subscribe to order updates

3. POST /api/Position/searchOpen
   → Load current positions (snapshot)

4. POST /api/Order/searchOpen
   → Load active orders (snapshot)

// Runtime Monitoring (via SignalR)
- GatewayUserPosition → Update position tracking
- GatewayUserOrder    → Update order status
- GatewayUserTrade    → Calculate P&L
- GatewayUserAccount  → Monitor balance

// Risk Breach Response
IF (risk_limit_breached):
  1. POST /api/Position/closeContract
     OR
     POST /api/Position/partialCloseContract
  2. POST /api/Order/cancel (for pending orders)
```

### Data Flow

```
┌─────────────────────┐
│ Account Selection   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐         ┌──────────────────┐
│ Load Initial State  │◀────────│ SignalR Updates  │
│ - Positions         │         │ - Continuous     │
│ - Orders            │         │ - Real-time      │
└──────────┬──────────┘         └────────┬─────────┘
           │                             │
           ▼                             ▼
┌─────────────────────────────────────────────────┐
│           Risk Calculation Engine               │
│  - Current Positions × Live Prices              │
│  - Open Order Exposure                          │
│  - Account Balance                              │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │ Risk Breach?   │
              └────────┬───────┘
                       │
         ┌─────────────┴─────────────┐
         │ YES                       │ NO
         ▼                           ▼
┌─────────────────┐         ┌──────────────┐
│ Execute:        │         │ Continue     │
│ - Close Pos     │         │ Monitoring   │
│ - Cancel Orders │         └──────────────┘
└─────────────────┘
```

### Dependencies
- Requires: Authentication Module (JWT token)
- Used by: Position Monitoring Module

---

## 3. Order Execution Module

### Endpoints Used

| Endpoint | Method | Purpose | Frequency | Critical |
|----------|--------|---------|-----------|----------|
| `/api/Order/place` | POST | Place new order | Per trade signal | YES |
| `/api/Order/modify` | POST | Modify existing order | Order adjustment | MEDIUM |
| `/api/Order/cancel` | POST | Cancel order | Cancel request | HIGH |
| `/api/Order/searchOpen` | POST | Verify order status | Post-placement | MEDIUM |
| **SignalR User Hub** | WebSocket | Monitor order fills | Continuous | YES |

### Calling Sequence

```javascript
// Order Placement Flow
1. Validate order parameters
   - contractId exists
   - size within limits
   - price valid

2. POST /api/Order/place
   Input: {
     accountId: int,
     contractId: string,
     type: OrderType,
     side: OrderSide,
     size: int,
     limitPrice?: number,
     stopPrice?: number,
     stopLossBracket?: { ticks, type },
     takeProfitBracket?: { ticks, type }
   }
   Output: {
     orderId: long,
     success: bool,
     errorCode: int
   }

3. Monitor via SignalR
   - GatewayUserOrder (status updates)
   - GatewayUserTrade (fill notifications)

4. IF order needs modification:
   POST /api/Order/modify
   Input: {
     accountId: int,
     orderId: long,
     size?: int,
     limitPrice?: number,
     stopPrice?: number
   }

5. IF order needs cancellation:
   POST /api/Order/cancel
   Input: {
     accountId: int,
     orderId: long
   }
```

### Order Lifecycle Tracking

```
┌──────────────────┐
│  Place Order     │
│  POST /place     │
└────────┬─────────┘
         │
         ▼
  ┌──────────────┐
  │ orderId: 123 │
  └──────┬───────┘
         │
         ▼
┌─────────────────────────────┐
│ SignalR: GatewayUserOrder   │
│ status: 1 (Open)            │
└──────────┬──────────────────┘
           │
    ┌──────┴────────┐
    │ Order Active  │
    │ Status: Open  │
    └──────┬────────┘
           │
    ┌──────┴────────────────┐
    │ Modify?    Cancel?    │
    │ POST       POST       │
    │ /modify    /cancel    │
    └──────┬────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ SignalR: GatewayUserOrder   │
│ status: 2 (Filled) or       │
│ status: 3 (Cancelled)       │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ SignalR: GatewayUserTrade   │
│ (if filled)                 │
│ - price, size, fees         │
│ - profitAndLoss             │
└─────────────────────────────┘
```

### Bracket Order Handling

```javascript
// OCO (One-Cancels-Other) Orders
const orderRequest = {
  accountId: 123,
  contractId: "CON.F.US.EP.U25",
  type: 2, // Market
  side: 0, // Buy
  size: 1,
  stopLossBracket: {
    ticks: 10,  // 10 ticks below entry
    type: 1     // Limit order
  },
  takeProfitBracket: {
    ticks: 20,  // 20 ticks above entry
    type: 1     // Limit order
  }
};

// Results in 3 orders:
// 1. Main entry order (executed immediately if market)
// 2. Stop loss order (placed automatically)
// 3. Take profit order (placed automatically)
// When one bracket fills, the other cancels automatically
```

### Dependencies
- Requires: Authentication Module, Market Data Module (contract info)
- Used by: Risk Manager Module

---

## 4. Market Data Module

### Endpoints Used

| Endpoint | Method | Purpose | Frequency | Critical |
|----------|--------|---------|-----------|----------|
| `/api/Contract/available` | POST | Load contract universe | Startup, Daily | MEDIUM |
| `/api/Contract/search` | POST | Search contracts | User search | LOW |
| `/api/Contract/searchById` | POST | Get contract details | On-demand | MEDIUM |
| `/api/History/retrieveBars` | POST | Historical data | Chart load, Backtest | HIGH |
| **SignalR Market Hub** | WebSocket | Real-time quotes | Continuous | HIGH |

### SignalR Subscriptions

```javascript
// Market Hub Connection
const marketHub = new HubConnection('wss://rtc.topstepx.com/hubs/market');

// Subscribe to Contract Data
marketHub.invoke('SubscribeContractQuotes', contractId);
marketHub.invoke('SubscribeContractTrades', contractId);
marketHub.invoke('SubscribeContractMarketDepth', contractId);

// Event Handlers
marketHub.on('GatewayQuote', handleQuoteUpdate);
  // → lastPrice, bestBid, bestAsk, volume

marketHub.on('GatewayTrade', handleTradeUpdate);
  // → price, volume, type (buy/sell), timestamp

marketHub.on('GatewayDepth', handleDepthUpdate);
  // → DOM updates (price levels, volume)
```

### Calling Sequence

```javascript
// Startup Sequence
1. POST /api/Contract/available
   Input: { live: true }
   Output: { contracts: [...] }
   → Cache contract details (tickSize, tickValue, etc.)

2. Connect SignalR Market Hub
   → Subscribe to active contracts

// User Requests Historical Data
3. POST /api/History/retrieveBars
   Input: {
     contractId: string,
     live: bool,
     startTime: datetime,
     endTime: datetime,
     unit: int (1-6),
     unitNumber: int,
     limit: int (max 20,000),
     includePartialBar: bool
   }
   Output: {
     bars: [{ t, o, h, l, c, v }]
   }

   ⚠️ RATE LIMITED: 50 requests / 30 seconds
```

### Data Flow

```
┌──────────────────────┐
│ Contract Universe    │
│ POST /available      │
│ (~26 contracts)      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ Contract Cache                       │
│ - contractId → tickSize, tickValue   │
│ - Active contracts                   │
└──────────┬───────────────────────────┘
           │
           ├─────────────────────┐
           │                     │
           ▼                     ▼
┌─────────────────────┐   ┌──────────────────┐
│ SignalR Market Hub  │   │ Historical Data  │
│ - Real-time quotes  │   │ POST /retrieve   │
│ - Trade feed        │   │ - OHLCV bars     │
│ - DOM updates       │   │ - Max 20k bars   │
└─────────┬───────────┘   └────────┬─────────┘
          │                        │
          └────────────┬───────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ Price Data Store    │
            │ - Current prices    │
            │ - Historical bars   │
            │ - Volume data       │
            └─────────┬───────────┘
                      │
                      ▼
            ┌─────────────────────┐
            │ Risk Calculations   │
            │ Position Valuations │
            └─────────────────────┘
```

### Rate Limit Management

```javascript
class HistoricalDataRateLimiter {
  maxRequests = 50;
  windowMs = 30000; // 30 seconds
  requests = [];

  async fetchBars(params) {
    await this.throttle();
    return await fetch('/api/History/retrieveBars', params);
  }

  async throttle() {
    const now = Date.now();
    this.requests = this.requests.filter(t => now - t < this.windowMs);

    if (this.requests.length >= this.maxRequests) {
      const waitTime = this.windowMs - (now - this.requests[0]);
      await sleep(waitTime);
    }

    this.requests.push(now);
  }
}
```

### Dependencies
- Requires: Authentication Module
- Used by: Order Execution Module, Risk Manager Module

---

## 5. Position Monitoring Module

### Endpoints Used

| Endpoint | Method | Purpose | Frequency | Critical |
|----------|--------|---------|-----------|----------|
| `/api/Position/searchOpen` | POST | Load positions | Startup, Refresh | YES |
| `/api/Trade/search` | POST | Historical trades | Report generation | MEDIUM |
| **SignalR User Hub** | WebSocket | Real-time position updates | Continuous | YES |

### Calling Sequence

```javascript
// Startup Sequence
1. POST /api/Position/searchOpen
   Input: { accountId: int }
   Output: {
     positions: [{
       id: int,
       accountId: int,
       contractId: string,
       creationTimestamp: datetime,
       type: PositionType (1=Long, 2=Short),
       size: int,
       averagePrice: number
     }]
   }

2. SignalR Subscription
   userHub.invoke('SubscribePositions', accountId);
   userHub.on('GatewayUserPosition', handlePositionUpdate);

// Trade History
3. POST /api/Trade/search
   Input: {
     accountId: int,
     startTimestamp: datetime,
     endTimestamp: datetime
   }
   Output: {
     trades: [{
       id: long,
       contractId: string,
       price: number,
       profitAndLoss: number,
       fees: number,
       side: OrderSide,
       size: int,
       orderId: long
     }]
   }
```

### Position Tracking Flow

```
┌──────────────────────┐
│ Load Open Positions  │
│ POST /searchOpen     │
└──────────┬───────────┘
           │
           ▼
┌─────────────────────────────┐
│ Position Snapshot           │
│ - Contract: EP.U25          │
│ - Type: Long (1)            │
│ - Size: 2 contracts         │
│ - Avg Price: 5100.00        │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ SignalR: GatewayUserPosition        │
│ Real-time Updates:                  │
│ - Position size changes             │
│ - Average price updates             │
│ - Position open/close               │
└──────────┬──────────────────────────┘
           │
           ├─────────────────────┐
           │                     │
           ▼                     ▼
┌────────────────────┐  ┌──────────────────┐
│ Market Data Feed   │  │ Trade Events     │
│ (Live Prices)      │  │ GatewayUserTrade │
└────────┬───────────┘  └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │ P&L Calculation      │
          │ - Unrealized P&L     │
          │ - Realized P&L       │
          │ - Risk Exposure      │
          └──────────────────────┘
```

### P&L Calculation

```javascript
// Unrealized P&L for Open Positions
function calculateUnrealizedPnL(position, currentPrice, contract) {
  const priceDiff = position.type === PositionType.Long
    ? currentPrice - position.averagePrice
    : position.averagePrice - currentPrice;

  const ticks = priceDiff / contract.tickSize;
  const pnl = ticks * contract.tickValue * position.size;

  return pnl;
}

// Realized P&L from Trades
function calculateRealizedPnL(trades) {
  return trades
    .filter(t => t.profitAndLoss !== null)
    .reduce((sum, t) => sum + t.profitAndLoss - t.fees, 0);
}
```

### Dependencies
- Requires: Authentication Module, Market Data Module (for P&L)
- Used by: Risk Manager Module

---

## 6. Cross-Module Integration Map

```
┌──────────────────────┐
│ Authentication       │
│ Module               │
└─────────┬────────────┘
          │ (JWT Token)
          │
          ├─────────────────┬─────────────────┬─────────────────┐
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Risk Manager    │  │ Order Exec   │  │ Market Data  │  │ Position     │
│ Module          │  │ Module       │  │ Module       │  │ Monitor      │
└────────┬────────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
         │                  │                 │                 │
         │                  │◀────────────────┤                 │
         │                  │   (contract     │                 │
         │                  │    details)     │                 │
         │                  │                 │                 │
         │◀─────────────────┴─────────────────┴─────────────────┘
         │           (position & order data)
         │
         ▼
┌──────────────────────────┐
│ Risk Calculation Engine  │
│ - Position risk          │
│ - Order exposure         │
│ - Account balance        │
└──────────────────────────┘
```

---

## 7. API Call Frequency Analysis

### High Frequency (Continuous)
- SignalR User Hub events: ~10-100 events/second (market dependent)
- SignalR Market Hub events: ~100-1000 events/second per contract

### Medium Frequency (Per User Action)
- POST /api/Order/place: Variable (per trade)
- POST /api/Order/cancel: Variable (per cancellation)
- POST /api/Order/modify: Variable (per modification)
- POST /api/Position/closeContract: Rare (emergency)

### Low Frequency (Startup/Periodic)
- POST /api/Auth/loginKey: Once per session
- POST /api/Auth/validate: Every ~22 hours
- POST /api/Account/search: Startup, account change
- POST /api/Contract/available: Daily or on-demand
- POST /api/Position/searchOpen: Startup, refresh
- POST /api/Order/searchOpen: Startup, refresh

### Rate Limited
- POST /api/History/retrieveBars: 50 req/30s
- All other endpoints: 200 req/60s

---

## 8. Critical Path Analysis

### Order Placement Critical Path
```
1. Market Data → Get current price
2. Risk Check → Verify limits
3. POST /api/Order/place → Submit order
4. SignalR GatewayUserOrder → Confirm submission
5. SignalR GatewayUserTrade → Confirm fill
6. SignalR GatewayUserPosition → Update position
7. Risk Recalculation → Update exposure
```

**Total Latency:** 50-200ms (network dependent)
**Failure Points:** 3 (API call, order rejection, fill failure)

### Position Close Critical Path
```
1. POST /api/Position/closeContract → Close request
2. SignalR GatewayUserOrder → Market order created
3. SignalR GatewayUserTrade → Fill notification
4. SignalR GatewayUserPosition → Position closed
5. Risk Recalculation → Update exposure
```

**Total Latency:** 50-150ms
**Failure Points:** 2 (API call, market liquidity)

---

## 9. Error Handling Requirements by Module

### Authentication Module
- Invalid API key → Retry with correct key
- Token expired → Refresh token
- Network failure → Retry with exponential backoff
- Validate failure → Re-authenticate

### Risk Manager Module
- Position close failure → Alert user, retry
- Order cancel failure → Escalate, manual intervention
- SignalR disconnect → Fallback to polling
- Account balance mismatch → Reconcile

### Order Execution Module
- Order rejected → Parse error, notify user
- Network timeout → Verify order status
- Duplicate order → Check idempotency
- Modification failure → Attempt cancel+replace

### Market Data Module
- Rate limit exceeded → Queue and throttle
- Historical data unavailable → Use cached data
- SignalR disconnect → Reconnect with backoff
- Invalid contract → Validate contract list

### Position Monitoring Module
- P&L calculation error → Use last known good
- Trade history incomplete → Fetch multiple pages
- Position mismatch → Reconcile with API

---

## 10. Recommended Module Communication

### Event Bus Architecture
```javascript
// Central event bus for inter-module communication
class EventBus {
  subscribers = new Map();

  subscribe(event, callback) {
    if (!this.subscribers.has(event)) {
      this.subscribers.set(event, []);
    }
    this.subscribers.get(event).push(callback);
  }

  publish(event, data) {
    if (this.subscribers.has(event)) {
      this.subscribers.get(event).forEach(cb => cb(data));
    }
  }
}

// Module interactions
eventBus.subscribe('auth:token-refreshed', (newToken) => {
  marketDataModule.updateToken(newToken);
  orderModule.updateToken(newToken);
});

eventBus.subscribe('position:updated', (position) => {
  riskManager.recalculateExposure(position);
});

eventBus.subscribe('order:filled', (trade) => {
  positionMonitor.updatePosition(trade);
  riskManager.recalculateExposure();
});
```

---

**Document Version:** 1.0
**Last Updated:** 2025-10-22
**Maintained By:** API Integration Specialist
