# TopstepX API Contract Analysis - Complete

## Location
**Complete Contract Mapping**: `/docs/contracts/api_contracts.json`

## Critical Findings for Code Fixes

### 1. FIELD NAMING: ALL camelCase (NOT snake_case!)

**CRITICAL**: The TopstepX API uses **camelCase** for ALL fields, not snake_case.

#### Examples of Correct Field Names:
- `accountId` (NOT `account_id`)
- `contractId` (NOT `contract_id`)
- `creationTimestamp` (NOT `creation_timestamp`)
- `updateTimestamp` (NOT `update_timestamp`)
- `limitPrice` (NOT `limit_price`)
- `stopPrice` (NOT `stop_price`)
- `fillVolume` (NOT `fill_volume`)
- `filledPrice` (NOT `filled_price`)
- `customTag` (NOT `custom_tag`)
- `averagePrice` (NOT `average_price`)
- `profitAndLoss` (NOT `profit_and_loss`)
- `orderId` (NOT `order_id`)
- `symbolId` (NOT `symbol_id`)
- `tickSize` (NOT `tick_size`)
- `tickValue` (NOT `tick_value`)
- `activeContract` (NOT `active_contract`)
- `stopLossBracket` (NOT `stop_loss_bracket`)
- `takeProfitBracket` (NOT `take_profit_bracket`)
- `errorCode` (NOT `error_code`)
- `errorMessage` (NOT `error_message`)

### 2. Complete Object Structures

#### Account Object
```json
{
  "id": 123,
  "name": "TEST_ACCOUNT_1",
  "balance": 50000,
  "canTrade": true,
  "isVisible": true,
  "simulated": false
}
```

#### Order Object
```json
{
  "id": 36598,
  "accountId": 704,
  "contractId": "CON.F.US.EP.U25",
  "symbolId": "F.US.EP",
  "creationTimestamp": "2025-07-18T21:00:01.268009+00:00",
  "updateTimestamp": "2025-07-18T21:00:01.268009+00:00",
  "status": 2,
  "type": 2,
  "side": 0,
  "size": 1,
  "limitPrice": null,
  "stopPrice": null,
  "fillVolume": 1,
  "filledPrice": 6335.250000000,
  "customTag": null
}
```

#### Position Object
```json
{
  "id": 6124,
  "accountId": 536,
  "contractId": "CON.F.US.GMET.J25",
  "creationTimestamp": "2025-04-21T19:52:32.175721+00:00",
  "type": 1,
  "size": 2,
  "averagePrice": 1575.750000000
}
```

#### Trade Object
```json
{
  "id": 8604,
  "accountId": 203,
  "contractId": "CON.F.US.EP.H25",
  "creationTimestamp": "2025-01-21T16:13:52.523293+00:00",
  "price": 6065.250000000,
  "profitAndLoss": 50.000000000,
  "fees": 1.4000,
  "side": 1,
  "size": 1,
  "voided": false,
  "orderId": 14328
}
```

### 3. Enum Values (All Integers)

#### OrderStatus
- `0` = None
- `1` = Open
- `2` = Filled
- `3` = Cancelled
- `4` = Expired
- `5` = Rejected
- `6` = Pending

#### OrderType
- `0` = Unknown
- `1` = Limit
- `2` = Market
- `3` = StopLimit
- `4` = Stop
- `5` = TrailingStop
- `6` = JoinBid
- `7` = JoinAsk

#### OrderSide
- `0` = Bid (Buy)
- `1` = Ask (Sell)

#### PositionType
- `0` = Undefined
- `1` = Long
- `2` = Short

### 4. Nullable Fields

Many fields can be `null`:
- `limitPrice` (null for market orders)
- `stopPrice` (null for non-stop orders)
- `trailPrice` (null for non-trailing orders)
- `filledPrice` (null until filled)
- `customTag` (null if not provided)
- `profitAndLoss` (null for half-turn/opening trades)
- `errorMessage` (null on success)

### 5. Nested Objects

#### Bracket Orders (in Place Order requests)
```json
{
  "stopLossBracket": {
    "ticks": 10,
    "type": 1
  },
  "takeProfitBracket": {
    "ticks": 20,
    "type": 1
  }
}
```

### 6. SignalR Event Names

#### User Hub Events:
- `GatewayUserAccount` - Account updates
- `GatewayUserOrder` - Order updates
- `GatewayUserPosition` - Position updates
- `GatewayUserTrade` - Trade updates

#### Market Hub Events:
- `GatewayQuote` - Quote/price updates
- `GatewayDepth` - Market depth (DOM) updates
- `GatewayTrade` - Market trade events

### 7. Timestamp Format

All timestamps use ISO 8601 format with timezone:
- `"2025-07-18T21:00:01.268009+00:00"`
- `"2024-07-21T13:45:00Z"`

### 8. Standard API Response Structure

Every API response includes:
```json
{
  "success": true,
  "errorCode": 0,
  "errorMessage": null,
  "...": "additional response fields"
}
```

## What Code Needs to Fix

1. **Change all field references from snake_case to camelCase**
2. **Update data models to match exact API field names**
3. **Ensure enum handling uses integers, not strings**
4. **Handle nullable fields properly (limitPrice, stopPrice, profitAndLoss, etc.)**
5. **Use correct nested object structures for brackets**
6. **Parse timestamps as ISO 8601 with timezone**
7. **Handle SignalR event names correctly (GatewayUser* prefix)**

## Next Steps for Other Agents

1. **Model Mapper Agent**: Create exact Python models matching these camelCase fields
2. **Code Scanner Agent**: Find all snake_case field references and flag for replacement
3. **Test Writer Agent**: Create tests validating camelCase serialization/deserialization
4. **Documentation Agent**: Update all code comments to reference correct field names

---

**Generated**: 2025-10-23
**Source**: Complete analysis of /project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/
