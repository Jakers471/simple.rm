# Test Fixture Usage Guide

## Overview

This guide explains how to use the test fixtures available in the Simple Risk Manager test suite. All fixtures are automatically registered via `conftest.py` and available to any test.

## Quick Start

```python
import pytest

def test_example(sample_position, market_simulator):
    # Fixtures are automatically injected by pytest
    assert sample_position.size > 0
    # Use market_simulator for realistic market testing
```

## Available Fixture Modules

### 1. Market Simulation (`fixtures/mock_market.py`) **NEW**

Realistic market simulation without live connections.

#### Fixtures:

**`market_simulator`** - Full market simulator with price movements
```python
@pytest.mark.asyncio
async def test_market_data(market_simulator):
    # Configure market conditions
    market_simulator.set_trending_market()
    market_simulator.volatility = 0.03

    # Generate tick stream
    async for tick in market_simulator.generate_tick_stream(rate=10, max_ticks=5):
        print(f"{tick.symbol}: {tick.last} (bid: {tick.bid}, ask: {tick.ask})")
```

**`order_simulator`** - Order execution with slippage and fills
```python
@pytest.mark.asyncio
async def test_order_execution(order_simulator):
    # Place market order
    order = await order_simulator.place_order({
        'contract_id': 'MNQ',
        'type': 'market',
        'side': 0,  # Buy
        'size': 2
    })

    assert order.status == 'filled'
    assert order.avg_fill_price is not None

    # Check position
    position = order_simulator.get_position('MNQ')
    assert position == 2
```

**`sample_tick`** - Single market tick
```python
def test_tick_processing(sample_tick):
    assert sample_tick.symbol == "MNQ"
    assert sample_tick.bid < sample_tick.ask
```

**`sample_orderbook`** - Sample order book data
```python
def test_orderbook_parsing(sample_orderbook):
    best_bid = sample_orderbook['bids'][0]
    best_ask = sample_orderbook['asks'][0]
    spread = best_ask['price'] - best_bid['price']
```

**`trading_suite_mock`** - Mock trading suite
```python
@pytest.mark.asyncio
async def test_trading_suite(trading_suite_mock):
    market = trading_suite_mock['market']
    orders = trading_suite_mock['orders']
```

#### Market Scenarios:

```python
from tests.fixtures.mock_market import MarketScenarios

@pytest.mark.asyncio
async def test_trending_market(market_simulator):
    # Apply trending market
    MarketScenarios.apply_trending(market_simulator)
    # market_simulator.trend = 0.001
    # market_simulator.volatility = 0.01

@pytest.mark.asyncio
async def test_volatile_market(market_simulator):
    # Apply volatile conditions
    MarketScenarios.apply_volatile(market_simulator)
    # market_simulator.trend = 0.0
    # market_simulator.volatility = 0.05

@pytest.mark.asyncio
async def test_flash_crash(market_simulator):
    # Simulate flash crash
    await MarketScenarios.apply_flash_crash(market_simulator)

def test_low_liquidity(market_simulator):
    # Wide spreads
    MarketScenarios.apply_low_liquidity(market_simulator)
    # market_simulator.spread_pct = Decimal("0.005")
```

---

### 2. Positions (`fixtures/positions.py`)

Position-related test data.

```python
def test_position_validation(sample_long_position):
    assert sample_long_position.size > 0
    assert sample_long_position.symbol == "MNQ"

def test_short_position(sample_short_position):
    assert sample_short_position.size < 0

def test_flat_position(sample_flat_position):
    assert sample_flat_position.size == 0
```

Available position fixtures:
- `sample_long_position`
- `sample_short_position`
- `sample_flat_position`
- `multiple_positions`
- `position_with_pnl`

---

### 3. Orders (`fixtures/orders.py`)

Order-related test data.

```python
def test_buy_order(sample_buy_order):
    assert sample_buy_order.side == 0  # Buy
    assert sample_buy_order.size > 0

def test_bracket_order(sample_bracket_order):
    assert 'stop_loss' in sample_bracket_order
    assert 'take_profit' in sample_bracket_order
```

Available order fixtures:
- `sample_buy_order`
- `sample_sell_order`
- `sample_market_order`
- `sample_limit_order`
- `sample_stop_order`
- `sample_bracket_order`
- `multiple_orders`

---

### 4. Trades (`fixtures/trades.py`)

Trade execution data.

```python
def test_winning_trade(sample_win_trade):
    assert sample_win_trade.pnl > 0

def test_losing_trade(sample_loss_trade):
    assert sample_loss_trade.pnl < 0
```

Available trade fixtures:
- `sample_trade`
- `sample_win_trade`
- `sample_loss_trade`
- `multiple_trades`
- `trade_sequence`

---

### 5. Accounts (`fixtures/accounts.py`)

Account and configuration data.

```python
def test_account_balance(sample_account):
    assert sample_account.balance > 0
    assert sample_account.account_id is not None

def test_multiple_accounts(multiple_accounts):
    assert len(multiple_accounts) > 1
```

Available account fixtures:
- `sample_account`
- `sample_account_dict`
- `multiple_accounts`
- `funded_account`
- `margin_account`

---

### 6. Contracts (`fixtures/contracts.py`)

Contract definitions.

```python
def test_contract(sample_contract):
    assert sample_contract.symbol == "MNQ"
    assert sample_contract.multiplier > 0
```

Available contract fixtures:
- `sample_contract`
- `mnq_contract`
- `mes_contract`
- `multiple_contracts`

---

### 7. Quotes (`fixtures/quotes.py`)

Quote and price data.

```python
def test_quote(sample_quote):
    assert sample_quote.bid < sample_quote.ask
    assert sample_quote.symbol is not None
```

Available quote fixtures:
- `sample_quote`
- `realtime_quote`
- `delayed_quote`

---

### 8. SignalR Events (`fixtures/signalr_events.py`)

SignalR event data for testing event handling.

```python
def test_signalr_event(sample_signalr_event):
    assert 'event_type' in sample_signalr_event
    assert 'data' in sample_signalr_event
```

Available SignalR fixtures:
- `sample_signalr_event`
- `order_update_event`
- `position_update_event`
- `quote_update_event`

---

### 9. Configs (`fixtures/configs.py`)

Configuration objects for testing.

```python
def test_risk_config(sample_risk_config):
    assert sample_risk_config.max_daily_loss > 0
    assert sample_risk_config.max_position_size > 0
```

Available config fixtures:
- `sample_risk_config`
- `sample_account_config`
- `sample_rule_config`

---

### 10. API Responses (`fixtures/api_responses.py`)

Mock API response data.

```python
def test_api_response(sample_api_response):
    assert sample_api_response.status_code == 200
    assert 'data' in sample_api_response.json()
```

Available API fixtures:
- `sample_api_response`
- `error_response`
- `authentication_response`

---

## Global Fixtures (from `conftest.py`)

### `mock_lockout_manager`
```python
def test_lockout_check(mock_lockout_manager):
    # Mock returns False by default
    assert not mock_lockout_manager.is_symbol_locked("MNQ")
```

### `mock_actions`
```python
def test_enforcement(mock_actions):
    # Mock enforcement actions
    mock_actions.block_symbol("MNQ")
    mock_actions.block_symbol.assert_called_once()
```

### `mock_logger`
```python
def test_logging(mock_logger):
    # Mock logger for testing
    mock_logger.info("Test message")
    mock_logger.info.assert_called()
```

### `logger`
```python
def test_with_logging(logger):
    # Real logger instance
    logger.info("This will be logged")
```

### `test_data_dir`
```python
def test_data_path(test_data_dir):
    # Path to tests/fixtures/
    assert test_data_dir.exists()
```

---

## Combining Fixtures

You can use multiple fixtures in one test:

```python
@pytest.mark.asyncio
async def test_complete_workflow(
    market_simulator,
    order_simulator,
    sample_account,
    mock_lockout_manager
):
    # Setup market
    market_simulator.set_trending_market()

    # Check account
    assert sample_account.balance > 0

    # Verify no lockout
    assert not mock_lockout_manager.is_symbol_locked("MNQ")

    # Place order
    order = await order_simulator.place_order({
        'contract_id': 'MNQ',
        'type': 'market',
        'side': 0,
        'size': 1
    })

    assert order.status == 'filled'
```

---

## Creating Custom Fixtures

Add to `conftest.py`:

```python
@pytest.fixture
def my_custom_fixture():
    """Description of fixture"""
    # Setup
    data = {'key': 'value'}
    yield data
    # Teardown (optional)
```

Or create a new file in `tests/fixtures/`:

```python
# tests/fixtures/my_fixtures.py
import pytest

@pytest.fixture
def my_fixture():
    return "my data"
```

Then register in `conftest.py`:
```python
pytest_plugins = [
    # ... existing plugins ...
    'fixtures.my_fixtures'
]
```

---

## Fixture Scopes

- `scope='function'` (default) - New instance per test
- `scope='class'` - One instance per test class
- `scope='module'` - One instance per test module
- `scope='session'` - One instance per test session

```python
@pytest.fixture(scope='session')
def expensive_setup():
    # Only runs once for all tests
    return setup_data()
```

---

## Async Fixtures

For async fixtures (like market_simulator):

```python
@pytest.fixture
async def my_async_fixture():
    client = await create_client()
    yield client
    await client.close()
```

Use with `@pytest.mark.asyncio`:
```python
@pytest.mark.asyncio
async def test_async(my_async_fixture):
    result = await my_async_fixture.do_something()
```

---

## Parameterized Fixtures

Test multiple scenarios:

```python
@pytest.fixture(params=['MNQ', 'MES', 'RTY'])
def symbol(request):
    return request.param

def test_symbols(symbol):
    # Runs 3 times, once for each symbol
    assert len(symbol) > 0
```

---

## Best Practices

1. **Use descriptive names**: `sample_long_position` not `pos1`
2. **Document fixtures**: Add docstrings
3. **Keep fixtures simple**: One responsibility per fixture
4. **Avoid fixture interdependencies**: Unless necessary
5. **Use appropriate scopes**: Session for expensive setup
6. **Clean up resources**: Use `yield` for teardown
7. **Test fixtures independently**: Ensure they work alone

---

## Finding Available Fixtures

List all fixtures:
```bash
pytest --fixtures
```

List fixtures from specific file:
```bash
pytest --fixtures tests/fixtures/positions.py
```

---

## Example Test Patterns

### Unit Test Pattern
```python
def test_risk_rule(sample_position, mock_actions, mock_logger):
    # Test isolated rule logic
    rule = MyRiskRule(mock_actions, mock_logger)
    result = rule.evaluate(sample_position)
    assert result.is_valid
```

### Integration Test Pattern
```python
@pytest.mark.asyncio
async def test_order_flow(market_simulator, order_simulator, sample_account):
    # Test multiple components together
    # ... test implementation
```

### E2E Test Pattern
```python
@pytest.mark.asyncio
async def test_complete_trading_cycle(
    market_simulator,
    order_simulator,
    sample_account,
    sample_risk_config
):
    # Test full system workflow
    # ... test implementation
```

---

## Troubleshooting

### Fixture not found
```
ERROR: fixture 'my_fixture' not found
```
- Check fixture is registered in `conftest.py`
- Verify fixture file is in `tests/fixtures/`
- Check spelling

### Async fixture issues
```
ERROR: coroutine never awaited
```
- Add `@pytest.mark.asyncio` decorator
- Make test function `async def`

### Import errors
```
ModuleNotFoundError: No module named 'fixtures'
```
- Check `sys.path` setup in `conftest.py`
- Verify fixture files have `__init__.py`

---

## See Also

- `tests/fixtures/README.md` - Fixture catalog
- `tests/.structure_plan.txt` - Test organization
- `tests/integration/test_market_simulation.py` - Example usage
- [Pytest Fixtures Documentation](https://docs.pytest.org/en/stable/fixture.html)
