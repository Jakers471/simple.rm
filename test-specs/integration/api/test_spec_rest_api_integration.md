# Integration Test Specifications - REST API

**Generated:** 2025-10-22
**Purpose:** Integration testing for TopstepX Gateway REST API client implementation
**Test Type:** Integration (API Client Layer with Mocked HTTP Responses)
**Framework:** pytest with responses/httpx mock
**Priority:** High - Critical for all enforcement actions
**Spec Version:** 2.0 - Aligned with TEST_SCENARIO_MATRIX

---

## Overview

These integration tests verify the **REST API client layer** including:
- Authentication flow (login, token refresh, validation)
- Order placement (place, modify, cancel)
- Position management (search, close, partial close)
- Error handling (401, 429, 500, network timeout)
- Retry logic with exponential backoff
- Rate limiting enforcement

**Test Philosophy:**
- Mock HTTP responses using `responses` library or `httpx.mock`
- Test REAL client logic including retries, error handling, and state management
- Verify authentication state transitions
- Ensure thread-safe concurrent operations

**Coverage Target:** 90%+ of API client code
**Total Test Scenarios:** 10 (matching TEST_SCENARIO_MATRIX IT-001-01 through IT-001-10)

---

## Test Data & Fixtures

### Mock Credentials
```python
TEST_USER = "test_user_123"
TEST_API_KEY = "test_key_abc123xyz"
TEST_ACCOUNT_ID = 12345
TEST_CONTRACT_MNQ = "CON.F.US.MNQ.H25"
TEST_CONTRACT_ES = "CON.F.US.ES.H25"
```

### Mock JWT Token
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjE3MzAwMDAwMDB9.signature
```

---

## Test Suite: REST API Integration

### Test ID: IT-001-01
**Test Scenario:** `authenticate()` with valid credentials
**Priority:** High
**Module:** `src/api/rest_client.py`
**Test File:** `tests/integration/test_api_integration.py::test_authenticate_valid_credentials`

**Given:**
- Valid API credentials (userName, apiKey) from test config
- Mock HTTP response for `POST /api/Auth/loginKey`
- Clean authentication state (no cached token)
- Base URL: `https://api.topstepx.com`

**When:**
- `RestClient.authenticate()` is called with valid credentials

**Then:**
- HTTP POST request sent to `https://api.topstepx.com/api/Auth/loginKey`
- Request headers include: `Content-Type: application/json`
- Request body contains: `{"userName": "test_user_123", "apiKey": "test_key_abc123xyz"}`
- Response status: 200 OK
- Response body parsed successfully
- JWT token extracted and stored in `self._token`
- Token expiry time calculated as `now + 24 hours`
- `is_authenticated()` method returns `True`
- No exceptions raised
- Logs: "Authentication successful for user: test_user_123" (INFO level)

**Mock HTTP Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

**Assertions:**
```python
assert client.is_authenticated() == True
assert client._token is not None
assert client._token_expiry > datetime.now()
assert "authentication successful" in caplog.text.lower()
```

---

### Test ID: IT-001-02
**Test Scenario:** `authenticate()` with invalid credentials
**Priority:** High
**Module:** `src/api/rest_client.py`
**Test File:** `tests/integration/test_api_integration.py::test_authenticate_invalid_credentials`

**Given:**
- Invalid API credentials (wrong apiKey)
- Mock HTTP 401 Unauthorized response
- Clean authentication state

**When:**
- `RestClient.authenticate()` is called with invalid credentials

**Then:**
- HTTP POST request sent to authentication endpoint
- Server returns 401 Unauthorized status
- `AuthenticationError` exception raised with message: "Authentication failed: Invalid credentials"
- Token NOT stored in `self._token`
- `is_authenticated()` returns `False`
- Error logged with WARNING level: "Authentication failed for user test_user_123"
- No retry attempted (401 is permanent failure)

**Mock HTTP Response:**
```
HTTP/1.1 401 Unauthorized
Content-Type: text/plain

Error: response status is 401
```

**Assertions:**
```python
with pytest.raises(AuthenticationError, match="Invalid credentials"):
    client.authenticate()

assert client.is_authenticated() == False
assert client._token is None
assert "authentication failed" in caplog.text.lower()
```

---

### Test ID: IT-001-03
**Test Scenario:** `POST /api/Position/closeContract` - Close position successfully
**Priority:** High
**Module:** `src/api/rest_client.py`
**Test File:** `tests/integration/test_api_integration.py::test_close_position_success`

**Given:**
- Authenticated client with valid JWT token
- Open position for accountId=12345, contractId="CON.F.US.MNQ.H25"
- Mock HTTP response for `POST /api/Position/closeContract`

**When:**
- `RestClient.close_position(account_id=12345, contract_id="CON.F.US.MNQ.H25")` called

**Then:**
- HTTP POST request sent to `https://api.topstepx.com/api/Position/closeContract`
- Authorization header includes: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
- Content-Type header: `application/json`
- Request body contains: `{"accountId": 12345, "contractId": "CON.F.US.MNQ.H25"}`
- Response status: 200 OK
- Response indicates `success: true`
- Method returns `True`
- Logs: "Position closed successfully: MNQ for account 12345" (INFO level)
- No exceptions raised

**Mock HTTP Response:**
```json
{
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

**Assertions:**
```python
result = client.close_position(12345, "CON.F.US.MNQ.H25")
assert result == True
assert len(responses.calls) == 1
assert responses.calls[0].request.headers["Authorization"] == "Bearer ..."
```

---

### Test ID: IT-001-04
**Test Scenario:** `POST /api/Order/cancel` - Cancel working order successfully
**Priority:** High
**Module:** `src/api/rest_client.py`
**Test File:** `tests/integration/test_api_integration.py::test_cancel_order_success`

**Given:**
- Authenticated client
- Working order with orderId=9056 for accountId=12345
- Mock HTTP response for `POST /api/Order/cancel`

**When:**
- `RestClient.cancel_order(account_id=12345, order_id=9056)` called

**Then:**
- HTTP POST request sent to `https://api.topstepx.com/api/Order/cancel`
- Authorization header includes Bearer token
- Request body contains: `{"accountId": 12345, "orderId": 9056}`
- Response status: 200 OK
- Response indicates success
- Method returns `True`
- Logs: "Order canceled successfully: 9056 for account 12345" (INFO level)
- Used by enforcement actions to cancel all orders

**Mock HTTP Response:**
```json
{
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

**Assertions:**
```python
result = client.cancel_order(12345, 9056)
assert result == True
assert "order canceled successfully" in caplog.text.lower()
```

---

### Test ID: IT-001-05
**Test Scenario:** `POST /api/Order/place` - Place stop-loss order successfully
**Priority:** High
**Module:** `src/api/rest_client.py`
**Test File:** `tests/integration/test_api_integration.py::test_place_stop_loss_order`

**Given:**
- Authenticated client
- Open long position requiring stop-loss protection
- Mock HTTP response for `POST /api/Order/place`

**When:**
- `RestClient.place_order(account_id=12345, contract_id="CON.F.US.MNQ.H25", type=4, side=1, size=3, stop_price=20950.00)` called
- OrderType=4 (Stop order)
- Side=1 (Sell/Ask - to close long position)

**Then:**
- HTTP POST request sent to order placement endpoint
- Request body contains all order parameters:
  ```json
  {
    "accountId": 12345,
    "contractId": "CON.F.US.MNQ.H25",
    "type": 4,
    "side": 1,
    "size": 3,
    "stopPrice": 20950.00
  }
  ```
- Response includes orderId
- Method returns orderId (9056)
- Logs: "Stop-loss order placed: 9056 for MNQ @ 20950.00" (INFO level)
- Used by RULE-008 (No Stop-Loss Grace) and RULE-012 (Trade Management) enforcement

**Mock HTTP Response:**
```json
{
  "orderId": 9056,
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

**Assertions:**
```python
order_id = client.place_order(
    account_id=12345,
    contract_id="CON.F.US.MNQ.H25",
    type=4,  # Stop
    side=1,  # Sell
    size=3,
    stop_price=20950.00
)
assert order_id == 9056
assert "stop-loss order placed" in caplog.text.lower()
```

---

### Test ID: IT-001-06
**Test Scenario:** `POST /api/Position/searchOpen` - Retrieve open positions
**Priority:** High
**Module:** `src/api/rest_client.py`
**Test File:** `tests/integration/test_api_integration.py::test_search_open_positions`

**Given:**
- Authenticated client
- Account with 2 open positions (MNQ and ES)
- Mock HTTP response for `POST /api/Position/searchOpen`

**When:**
- `RestClient.search_open_positions(account_id=12345)` called

**Then:**
- HTTP POST request sent to search endpoint
- Request body contains: `{"accountId": 12345}`
- Response parsed into list of Position objects
- Method returns list with 2 positions
- Each position has: contractId, side, quantity, avgPrice, unrealizedPnl
- Position 1: MNQ long 3 contracts @ 21000.50, unrealized +$150.00
- Position 2: ES short 2 contracts @ 5000.25, unrealized -$75.50
- Used by enforcement actions to determine positions to close

**Mock HTTP Response:**
```json
{
  "positions": [
    {
      "accountId": 12345,
      "contractId": "CON.F.US.MNQ.H25",
      "side": 0,
      "quantity": 3,
      "avgPrice": 21000.50,
      "unrealizedPnl": 150.00
    },
    {
      "accountId": 12345,
      "contractId": "CON.F.US.ES.H25",
      "side": 1,
      "quantity": 2,
      "avgPrice": 5000.25,
      "unrealizedPnl": -75.50
    }
  ],
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

**Assertions:**
```python
positions = client.search_open_positions(12345)
assert len(positions) == 2
assert positions[0].contract_id == "CON.F.US.MNQ.H25"
assert positions[0].quantity == 3
assert positions[1].contract_id == "CON.F.US.ES.H25"
assert positions[1].quantity == 2
```

---

### Test ID: IT-001-07
**Test Scenario:** `GET /api/Contract/searchById` - Retrieve contract metadata
**Priority:** High
**Module:** `src/api/rest_client.py`
**Test File:** `tests/integration/test_api_integration.py::test_search_contract_by_id`

**Given:**
- Authenticated client
- Valid contractId for MNQ March 2025: "CON.F.US.MNQ.H25"
- Mock HTTP response for `POST /api/Contract/searchById`

**When:**
- `RestClient.search_contract_by_id(contract_id="CON.F.US.MNQ.H25")` called

**Then:**
- HTTP POST request sent to contract search endpoint
- Request body contains: `{"contractId": "CON.F.US.MNQ.H25"}`
- Response includes contract metadata
- Method returns Contract object with:
  - id: "CON.F.US.MNQ.H25"
  - name: "Micro E-Mini NASDAQ-100 Mar 2025"
  - symbol: "MNQ"
  - tickSize: 0.25
  - tickValue: 0.50
  - contractSize: 1
- Used by ContractCache for P&L calculations
- Logs: "Contract metadata retrieved: MNQ" (DEBUG level)

**Mock HTTP Response:**
```json
{
  "contract": {
    "id": "CON.F.US.MNQ.H25",
    "name": "Micro E-Mini NASDAQ-100 Mar 2025",
    "symbol": "MNQ",
    "exchange": "CME",
    "tickSize": 0.25,
    "tickValue": 0.50,
    "contractSize": 1
  },
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

**Assertions:**
```python
contract = client.search_contract_by_id("CON.F.US.MNQ.H25")
assert contract.symbol == "MNQ"
assert contract.tick_size == 0.25
assert contract.tick_value == 0.50
```

---

### Test ID: IT-001-08
**Test Scenario:** API rate limiting handling (client-side prevention)
**Priority:** High
**Module:** `src/api/rest_client.py`
**Test File:** `tests/integration/test_api_integration.py::test_rate_limiting_enforcement`

**Given:**
- Authenticated client with rate limit tracking enabled
- Rate limit: 200 requests / 60 seconds for standard endpoints
- 190 requests already sent in last 60 seconds (tracked in sliding window)

**When:**
- Rapid burst of 20 additional requests attempted via `close_position()` calls
- Total would exceed 200/60s limit without client-side prevention

**Then:**
- Client tracks request timestamps in sliding window
- Requests 1-10 sent immediately (total 200 in window)
- Requests 11-20 blocked/delayed by client-side rate limiter
- Client waits until oldest requests exit 60s window
- Delayed requests then sent once slots available
- No 429 errors from server (prevented by client-side limiting)
- Logs: "Rate limit approaching: delaying request" (WARNING level)
- Total execution time: ~60 seconds (due to rate limit delays)

**Rate Limit Implementation:**
- Use sliding window algorithm with deque of timestamps
- Before each request, count requests in last 60 seconds
- If count >= 200, calculate wait time until next slot
- Sleep for wait time, then proceed with request

**Assertions:**
```python
# Send 210 requests total (190 + 20)
for i in range(20):
    result = client.close_position(12345, f"CON.F.US.TEST.{i}")
    # Verify no 429 errors occurred

assert "rate limit" in caplog.text.lower()
# Verify no 429 status codes in responses
assert all(call.response.status_code != 429 for call in responses.calls)
```

---

### Test ID: IT-001-09
**Test Scenario:** API retry on 500 Internal Server Error with exponential backoff
**Priority:** High
**Module:** `src/api/rest_client.py`
**Test File:** `tests/integration/test_api_integration.py::test_retry_on_500_error`

**Given:**
- Authenticated client
- Mock HTTP 500 response on first 2 attempts
- Mock successful 200 response on 3rd attempt

**When:**
- `RestClient.close_position(account_id=12345, contract_id="CON.F.US.MNQ.H25")` called
- First two attempts return 500 Internal Server Error

**Then:**
- Client detects 500 status code (server error - retriable)
- Logs WARNING: "API server error 500, retrying... (attempt 1/5)"
- Waits 1 second (exponential backoff: 2^0 = 1s)
- Retry attempt 2 → also returns 500
- Logs WARNING: "API server error 500, retrying... (attempt 2/5)"
- Waits 2 seconds (exponential backoff: 2^1 = 2s)
- Retry attempt 3 → returns 200 Success
- Logs INFO: "Request succeeded after 3 attempts"
- Method returns `True` to caller
- Caller unaware of retries (transparent retry logic)
- Total requests made: 3

**Mock Sequence:**
```python
responses.add(responses.POST, url, status=500, json={"errorMessage": "Internal error"})  # Attempt 1
responses.add(responses.POST, url, status=500, json={"errorMessage": "Internal error"})  # Attempt 2
responses.add(responses.POST, url, status=200, json={"success": True, "errorCode": 0})  # Attempt 3
```

**Backoff Strategy:**
- Attempt 1: immediate
- Attempt 2: wait 1 second (2^0)
- Attempt 3: wait 2 seconds (2^1)
- Attempt 4: wait 4 seconds (2^2)
- Attempt 5: wait 8 seconds (2^3)
- Max retries: 5 attempts total

**Assertions:**
```python
result = client.close_position(12345, "CON.F.US.MNQ.H25")
assert result == True
assert len(responses.calls) == 3  # Verify 3 attempts made
assert "retrying" in caplog.text.lower()
assert "succeeded after" in caplog.text.lower()
```

---

### Test ID: IT-001-10
**Test Scenario:** API timeout handling with retry
**Priority:** High
**Module:** `src/api/rest_client.py`
**Test File:** `tests/integration/test_api_integration.py::test_network_timeout_retry`

**Given:**
- Authenticated client
- Mock network timeout on first attempt (simulated delay > 30s timeout)
- Mock successful response on retry (within timeout)
- Timeout configuration: connect=10s, read=30s, total=45s

**When:**
- `RestClient.search_open_positions(account_id=12345)` called
- First attempt times out after 30 seconds (no response)

**Then:**
- Client waits for configured read timeout (30 seconds)
- `TimeoutError` exception caught by retry logic
- Logs ERROR: "Request timeout after 30s, retrying... (attempt 1/5)"
- Retry request immediately (no backoff for timeout - network issue)
- Second attempt succeeds within timeout (2 seconds)
- Logs INFO: "Request succeeded after timeout retry"
- Method returns position list
- Timeout exception NOT propagated to caller (handled by retry logic)
- Total execution time: ~32 seconds (30s timeout + 2s success)

**Mock Sequence:**
```python
# First call - simulate timeout
responses.add_callback(
    responses.POST,
    url,
    callback=lambda req: time.sleep(35),  # Exceeds 30s timeout
    content_type="application/json"
)
# Second call - success
responses.add(responses.POST, url, status=200, json={"positions": [...]})
```

**Timeout Configuration:**
```python
timeout = httpx.Timeout(
    connect=10.0,  # Connection timeout
    read=30.0,     # Read timeout
    write=10.0,    # Write timeout
    pool=10.0      # Pool timeout
)
```

**Assertions:**
```python
start_time = time.time()
positions = client.search_open_positions(12345)
elapsed = time.time() - start_time

assert positions is not None
assert elapsed > 30  # Confirms timeout occurred
assert len(responses.calls) == 2  # Confirms retry
assert "timeout" in caplog.text.lower()
assert "retry" in caplog.text.lower()
```

---

## Test Execution Guidelines

### Setup Requirements

**Required Libraries:**
```bash
pip install pytest pytest-cov responses httpx freezegun
```

**Test Configuration:**
```python
# conftest.py
import pytest
import responses
from src.api.rest_client import RestClient

@pytest.fixture
def mock_client():
    """Fixture providing authenticated REST client with mocked responses"""
    client = RestClient(
        base_url="https://api.topstepx.com",
        username="test_user_123",
        api_key="test_key_abc123xyz"
    )
    return client

@pytest.fixture
def mock_auth():
    """Fixture for mocking authentication endpoint"""
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "https://api.topstepx.com/api/Auth/loginKey",
            json={
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "success": True,
                "errorCode": 0
            },
            status=200
        )
        yield rsps
```

### Common Test Patterns

**Pattern 1: Mock successful API response**
```python
@responses.activate
def test_close_position_success(mock_client):
    responses.add(
        responses.POST,
        "https://api.topstepx.com/api/Position/closeContract",
        json={"success": True, "errorCode": 0},
        status=200
    )

    result = mock_client.close_position(12345, "CON.F.US.MNQ.H25")
    assert result is True
    assert len(responses.calls) == 1
```

**Pattern 2: Mock retry sequence**
```python
@responses.activate
def test_retry_on_500():
    url = "https://api.topstepx.com/api/Position/closeContract"
    responses.add(responses.POST, url, status=500)  # Attempt 1 fails
    responses.add(responses.POST, url, status=500)  # Attempt 2 fails
    responses.add(responses.POST, url, json={"success": True}, status=200)  # Attempt 3 succeeds

    result = client.close_position(12345, "CON.F.US.MNQ.H25")
    assert result is True
    assert len(responses.calls) == 3  # Verify 3 attempts made
```

**Pattern 3: Mock authentication failure**
```python
@responses.activate
def test_auth_failure():
    responses.add(
        responses.POST,
        "https://api.topstepx.com/api/Auth/loginKey",
        body="Error: response status is 401",
        status=401
    )

    with pytest.raises(AuthenticationError, match="Invalid credentials"):
        client.authenticate()
```

### Test Data Files

**Location:** `tests/fixtures/`

**Files:**
- `api_responses.json` - Mock response templates
- `test_credentials.yaml` - Test API keys (invalid/fake for safety)
- `test_contracts.json` - Sample contract metadata
- `test_positions.json` - Sample position data

**Example: api_responses.json**
```json
{
  "auth_success": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "success": true,
    "errorCode": 0,
    "errorMessage": null
  },
  "close_position_success": {
    "success": true,
    "errorCode": 0,
    "errorMessage": null
  },
  "positions_list": {
    "positions": [
      {
        "accountId": 12345,
        "contractId": "CON.F.US.MNQ.H25",
        "side": 0,
        "quantity": 3,
        "avgPrice": 21000.50,
        "unrealizedPnl": 150.00
      }
    ],
    "success": true
  }
}
```

---

## Running the Tests

### Run All Integration Tests
```bash
cd /home/jakers/projects/simple-risk-manager/simple\ risk\ manager
pytest tests/integration/test_api_integration.py -v
```

### Run Specific Test
```bash
pytest tests/integration/test_api_integration.py::test_authenticate_valid_credentials -v
```

### Run with Coverage Report
```bash
pytest tests/integration/test_api_integration.py --cov=src/api/rest_client --cov-report=html
```

### Run with Detailed Logging
```bash
pytest tests/integration/test_api_integration.py -v -s --log-cli-level=DEBUG
```

---

## Coverage Metrics

**Expected Coverage for API Client:**
- Authentication logic: 95%+
- Position/order endpoints: 90%+
- Error handling: 90%+
- Retry logic: 100% (critical path)
- Rate limiting: 95%+
- Timeout handling: 90%+

**Overall Target:** 90%+ line coverage for `src/api/rest_client.py`

---

## Success Criteria

**All tests must:**
1. ✅ Use mocked HTTP responses (no real API calls)
2. ✅ Test REAL client logic (authentication state, retries, rate limits)
3. ✅ Execute in < 10 seconds total (fast with mocks)
4. ✅ Be deterministic (no flaky tests)
5. ✅ Verify both success and failure paths
6. ✅ Check logging output for debugging
7. ✅ Validate request/response formats
8. ✅ Test error propagation correctly

---

## Dependencies & Prerequisites

**Requires Implementation:**
- `src/api/rest_client.py` - Main REST client class
- `src/api/exceptions.py` - Custom exceptions (AuthenticationError, APIError, etc.)
- `src/api/models.py` - Data models (Position, Order, Contract, etc.)
- `src/api/rate_limiter.py` - Client-side rate limiting logic

**Configuration:**
- Base URL: `https://api.topstepx.com`
- Rate limits: 200 req/60s (standard), 50 req/30s (history)
- Timeouts: connect=10s, read=30s, total=45s
- Max retries: 5 attempts
- Backoff: exponential (2^n seconds)

---

## Related Specifications

- **API Specs:** `/project-specs/SPECS/01-EXTERNAL-API/projectx_gateway_api/`
- **Test Matrix:** `/reports/2025-10-22-spec-governance/04-testing/TEST_SCENARIO_MATRIX.md`
- **Unit Tests:** `/test-specs/unit/core/` (for individual module testing)
- **E2E Tests:** `/test-specs/e2e/` (for full workflow testing)

---

**Document Status:** ✅ Complete - Ready for Implementation
**Version:** 2.0 - Aligned with TEST_SCENARIO_MATRIX IT-001-01 through IT-001-10
**Total Test Scenarios:** 10 integration tests
**Estimated Implementation Time:** 8-12 hours
**Estimated Execution Time:** 5-10 minutes (with mocked HTTP)
