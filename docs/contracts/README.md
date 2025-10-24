# TopstepX API Contract Documentation

## Overview

This directory contains complete API contract analysis and field mappings extracted from the TopstepX Gateway API documentation.

## Files in This Directory

### 1. `api_contracts.json` (PRIMARY SOURCE - 1167 lines)
**Complete API contract specification** with every field, type, and structure from the TopstepX API.

**Contains:**
- Complete object definitions (Account, Order, Position, Trade, Contract)
- All request/response objects
- SignalR event payloads (GatewayUserAccount, GatewayUserOrder, etc.)
- All enum definitions with values
- Field naming conventions
- Timestamp formats
- Critical notes and warnings

**Use this file for:**
- Model generation
- Validation schemas
- Contract testing
- API client development

### 2. `API_CONTRACT_SUMMARY.md` (QUICK REFERENCE - 207 lines)
**Human-readable summary** of the most important findings.

**Contains:**
- Critical field naming rules (camelCase!)
- Complete object examples
- Enum value mappings
- Nullable field list
- Nested object structures
- SignalR event names
- What needs to be fixed in code

**Use this file for:**
- Quick reference during development
- Understanding API structure
- Code review checklist

### 3. `SNAKE_TO_CAMEL_MAPPING.json` (FIX GUIDE - 173 lines)
**Field name translation map** from snake_case to camelCase.

**Contains:**
- Direct mappings (account_id → accountId)
- Common patterns (*_timestamp → *Timestamp)
- Pydantic alias examples
- Search/replace regex patterns
- Critical reminders

**Use this file for:**
- Automated code fixes
- Find/replace operations
- Model field aliasing
- Validation rules

### 4. `backend_contracts.json` (EXISTING - 605 lines)
Backend system's internal contract definitions.

### 5. `enum_mapping.md` (EXISTING - 316 lines)
Enum value mappings between systems.

### 6. `files_to_update.md` (EXISTING - 291 lines)
List of files requiring updates.

## Critical Discovery: camelCase Field Names

**THE MOST IMPORTANT FINDING:**

The TopstepX API uses **camelCase** for ALL field names, NOT snake_case.

### Common Mistakes to Fix:

❌ WRONG (snake_case):
```python
{
    "account_id": 123,
    "contract_id": "CON.F.US.EP.U25",
    "creation_timestamp": "2025-07-18T21:00:01.268009+00:00",
    "limit_price": 2100.50,
    "stop_price": null
}
```

✅ CORRECT (camelCase):
```python
{
    "accountId": 123,
    "contractId": "CON.F.US.EP.U25",
    "creationTimestamp": "2025-07-18T21:00:01.268009+00:00",
    "limitPrice": 2100.50,
    "stopPrice": null
}
```

## Quick Start Guide for Agents

### For Model Mapper Agent:
1. Read `api_contracts.json`
2. Generate Python models with exact field names (camelCase)
3. Use Pydantic `Field(alias=...)` for internal snake_case if needed
4. Reference `SNAKE_TO_CAMEL_MAPPING.json` for aliases

### For Code Scanner Agent:
1. Use regex patterns from `SNAKE_TO_CAMEL_MAPPING.json`
2. Scan for snake_case field references
3. Flag all matches for replacement
4. Cross-reference with `API_CONTRACT_SUMMARY.md`

### For Test Writer Agent:
1. Use object examples from `API_CONTRACT_SUMMARY.md`
2. Test both serialization and deserialization
3. Validate camelCase in JSON output
4. Test nullable fields (limitPrice, profitAndLoss, etc.)

### For Code Fixer Agent:
1. Get field mappings from `SNAKE_TO_CAMEL_MAPPING.json`
2. Apply search/replace patterns
3. Update model field definitions
4. Add Pydantic aliases where needed

## Most Common Fields to Fix

Based on frequency in codebase:

1. `account_id` → `accountId` (used everywhere)
2. `contract_id` → `contractId` (orders, positions, trades)
3. `creation_timestamp` → `creationTimestamp` (all objects)
4. `update_timestamp` → `updateTimestamp` (orders)
5. `limit_price` → `limitPrice` (orders)
6. `stop_price` → `stopPrice` (orders)
7. `filled_price` → `filledPrice` (orders)
8. `fill_volume` → `fillVolume` (orders)
9. `average_price` → `averagePrice` (positions)
10. `profit_and_loss` → `profitAndLoss` (trades)

## Validation Checklist

Before considering the fix complete, verify:

- [ ] All model fields use camelCase in serialization
- [ ] Pydantic aliases configured for snake_case internal use
- [ ] Tests validate JSON output has camelCase fields
- [ ] SignalR event handlers use correct event names (GatewayUser*)
- [ ] Nullable fields handle None/null properly
- [ ] Nested objects (stopLossBracket, takeProfitBracket) structured correctly
- [ ] Enum values use integers, not strings
- [ ] Timestamps parsed as ISO 8601 with timezone

## Source Documentation

All information extracted from:
```
/project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/
├── account/search_account.md
├── orders/place_order.md
├── orders/search_orders.md
├── orders/modify_order.md
├── orders/cancel_order.md
├── positions/search_positions.md
├── trades/search_trades.md
├── market_data/search_contracts.md
└── realtime_updates/realtime_data_overview.md
```

## Contact

Created by: API Contract Analyzer Agent
Date: 2025-10-23
Swarm: Contract Fixing Swarm

---

**Next Step**: Other agents should now use these contracts to fix field name mismatches throughout the codebase.
