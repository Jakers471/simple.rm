# Quick Start - Market Simulator Fixtures

## New Test Fixtures Available

### MarketSimulator - Realistic Market Data

```python
import pytest

@pytest.mark.asyncio
async def test_example(market_simulator):
    # Generate 10 ticks at 10 ticks/second
    async for tick in market_simulator.generate_tick_stream(rate=10, max_ticks=10):
        print(f"{tick.symbol}: ${tick.last}")
```

### OrderSimulator - Order Execution

```python
@pytest.mark.asyncio
async def test_order(order_simulator):
    # Place market order
    order = await order_simulator.place_order({
        'contract_id': 'MNQ',
        'type': 'market',
        'side': 0,  # Buy
        'size': 1
    })

    assert order.status == 'filled'
    assert order_simulator.get_position('MNQ') == 1
```

## Market Scenarios

```python
from tests.fixtures.mock_market import MarketScenarios

# Trending market (uptrend, low vol)
MarketScenarios.apply_trending(market_simulator)

# Volatile market (no trend, high vol)
MarketScenarios.apply_volatile(market_simulator)

# Flash crash
await MarketScenarios.apply_flash_crash(market_simulator)

# Wide spreads
MarketScenarios.apply_low_liquidity(market_simulator)
```

## Complete Example

```python
@pytest.mark.asyncio
async def test_trading_flow(market_simulator, order_simulator):
    # Setup trending market
    market_simulator.set_trending_market()

    # Buy
    buy_order = await order_simulator.place_order({
        'contract_id': 'MNQ',
        'type': 'market',
        'side': 0,
        'size': 1
    })

    # Sell
    sell_order = await order_simulator.place_order({
        'contract_id': 'MNQ',
        'type': 'market',
        'side': 1,
        'size': 1
    })

    # Calculate P&L
    pnl = (sell_order.avg_fill_price - buy_order.avg_fill_price)

    assert order_simulator.get_position('MNQ') == 0
```

## Available Fixtures

- `market_simulator` - Full market simulator
- `order_simulator` - Order execution engine
- `sample_tick` - Single tick data
- `sample_orderbook` - Sample order book
- `trading_suite_mock` - Mock trading suite

## Run Tests

```bash
# Run all tests
pytest

# Run market simulation examples
pytest tests/integration/test_market_simulation.py -v

# List fixtures
pytest --fixtures | grep market
```

## Documentation

- **Full Guide**: `tests/FIXTURE_USAGE_GUIDE.md`
- **Structure**: `tests/.structure_plan.txt`
- **Examples**: `tests/integration/test_market_simulation.py`
- **Source**: `tests/fixtures/mock_market.py`

---

**Status**: ✅ Ready to use - No setup required!
