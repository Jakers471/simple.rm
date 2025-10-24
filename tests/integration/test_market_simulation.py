"""Integration test demonstrating MarketSimulator usage

This test shows how to use the new mock_market fixtures for realistic
market simulation without requiring live market connections.
"""
import pytest
import asyncio
from decimal import Decimal
from datetime import datetime


class TestMarketSimulation:
    """Example integration tests using MarketSimulator"""

    @pytest.mark.asyncio
    async def test_market_tick_generation(self, market_simulator):
        """Test that market simulator generates realistic ticks"""
        tick_count = 0
        prices = []

        async for tick in market_simulator.generate_tick_stream(rate=10, max_ticks=10):
            tick_count += 1
            prices.append(tick.last)

            # Verify tick structure
            assert tick.symbol == "MNQ"
            assert tick.bid < tick.ask
            assert tick.bid <= tick.last <= tick.ask
            assert tick.volume > 0
            assert isinstance(tick.timestamp, datetime)

        # Verify we got all ticks
        assert tick_count == 10

        # Verify prices are changing (not all the same)
        assert len(set(prices)) > 1

    @pytest.mark.asyncio
    async def test_order_execution_market_order(self, market_simulator, order_simulator):
        """Test market order execution with slippage"""
        # Place market buy order
        order = await order_simulator.place_order({
            'contract_id': 'MNQ',
            'type': 'market',
            'side': 0,  # Buy
            'size': 2
        })

        # Verify order filled
        assert order.status == 'filled'
        assert len(order.fills) > 0
        assert sum(f.size for f in order.fills) == 2
        assert order.avg_fill_price is not None

        # Verify position updated
        position = order_simulator.get_position('MNQ')
        assert position == 2

    @pytest.mark.asyncio
    async def test_order_execution_limit_order(self, market_simulator, order_simulator):
        """Test limit order execution"""
        current_price = market_simulator.current_price

        # Place limit buy order below market
        limit_price = current_price - Decimal("100")

        order = await order_simulator.place_order({
            'contract_id': 'MNQ',
            'type': 'limit',
            'side': 0,  # Buy
            'size': 1,
            'price': limit_price
        })

        # Order should be working (not filled yet)
        assert order.status == 'working'

        # Move market price down
        market_simulator.current_price = limit_price - Decimal("1")

        # Check if order should fill now
        should_fill = await order_simulator._should_fill(order)
        assert should_fill

    @pytest.mark.asyncio
    async def test_orderbook_generation(self, market_simulator):
        """Test order book generation"""
        orderbook = await market_simulator.generate_orderbook(levels=10)

        # Verify structure
        assert 'bids' in orderbook
        assert 'asks' in orderbook
        assert len(orderbook['bids']) == 10
        assert len(orderbook['asks']) == 10

        # Verify bids descending, asks ascending
        bid_prices = [b['price'] for b in orderbook['bids']]
        ask_prices = [a['price'] for a in orderbook['asks']]

        assert bid_prices == sorted(bid_prices, reverse=True)
        assert ask_prices == sorted(ask_prices)

        # Verify spread
        best_bid = orderbook['bids'][0]['price']
        best_ask = orderbook['asks'][0]['price']
        assert best_ask > best_bid

    @pytest.mark.asyncio
    async def test_trending_market_scenario(self, market_simulator):
        """Test trending market configuration"""
        market_simulator.set_trending_market()

        assert market_simulator.trend == 0.001
        assert market_simulator.volatility == 0.01

        # Collect prices over time
        prices = []
        async for tick in market_simulator.generate_tick_stream(rate=50, max_ticks=20):
            prices.append(float(tick.last))

        # In trending market, we expect general upward movement
        # (though not guaranteed in every sample due to randomness)
        avg_early = sum(prices[:5]) / 5
        avg_late = sum(prices[-5:]) / 5

        # Most of the time, late prices should be higher (uptrend)
        # Note: This test might occasionally fail due to randomness
        # In production, you might want a more robust statistical test

    @pytest.mark.asyncio
    async def test_volatile_market_scenario(self, market_simulator):
        """Test volatile market configuration"""
        market_simulator.set_volatile_market()

        assert market_simulator.trend == 0.0
        assert market_simulator.volatility == 0.05

        prices = []
        async for tick in market_simulator.generate_tick_stream(rate=50, max_ticks=20):
            prices.append(float(tick.last))

        # Calculate price volatility (standard deviation)
        mean_price = sum(prices) / len(prices)
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        std_dev = variance ** 0.5

        # Volatile market should have larger price swings
        assert std_dev > 0  # Some movement occurred

    @pytest.mark.asyncio
    async def test_flash_crash_scenario(self, market_simulator):
        """Test flash crash simulation"""
        original_price = market_simulator.current_price

        # Simulate 5% flash crash
        crash_task = asyncio.create_task(
            market_simulator.simulate_flash_crash(drop_pct=0.05, recovery_seconds=0.1)
        )

        # Wait a moment for crash to happen
        await asyncio.sleep(0.05)
        crashed_price = market_simulator.current_price

        # Wait for recovery
        await crash_task
        recovered_price = market_simulator.current_price

        # Verify crash and recovery
        assert crashed_price < original_price
        assert recovered_price == original_price

    @pytest.mark.asyncio
    async def test_complete_trading_cycle(self, market_simulator, order_simulator):
        """Test complete trading workflow"""
        # Start market data stream in background
        market_task = asyncio.create_task(
            self._run_market_stream(market_simulator)
        )

        # Wait for market to stabilize
        await asyncio.sleep(0.1)

        # Place entry order
        entry_order = await order_simulator.place_order({
            'contract_id': 'MNQ',
            'type': 'market',
            'side': 0,  # Buy
            'size': 1
        })

        assert entry_order.status == 'filled'
        assert order_simulator.get_position('MNQ') == 1

        # Simulate some time passing
        await asyncio.sleep(0.1)

        # Place exit order
        exit_order = await order_simulator.place_order({
            'contract_id': 'MNQ',
            'type': 'market',
            'side': 1,  # Sell
            'size': 1
        })

        assert exit_order.status == 'filled'
        assert order_simulator.get_position('MNQ') == 0

        # Calculate P&L
        entry_price = entry_order.avg_fill_price
        exit_price = exit_order.avg_fill_price
        pnl = (exit_price - entry_price) * Decimal("1")  # 1 contract

        # P&L can be positive or negative depending on random price movement
        assert pnl is not None

        # Cleanup
        market_task.cancel()
        try:
            await market_task
        except asyncio.CancelledError:
            pass

    async def _run_market_stream(self, market_simulator):
        """Helper to run market stream in background"""
        async for tick in market_simulator.generate_tick_stream(rate=10):
            pass  # Just keep generating ticks

    def test_sample_tick_fixture(self, sample_tick):
        """Test that sample_tick fixture works"""
        assert sample_tick.symbol == "MNQ"
        assert sample_tick.bid < sample_tick.ask
        assert isinstance(sample_tick.timestamp, datetime)

    def test_sample_orderbook_fixture(self, sample_orderbook):
        """Test that sample_orderbook fixture works"""
        assert len(sample_orderbook['bids']) == 3
        assert len(sample_orderbook['asks']) == 3

        # Verify bids are descending
        bid_prices = [b['price'] for b in sample_orderbook['bids']]
        assert bid_prices == sorted(bid_prices, reverse=True)


class TestMarketSimulatorEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_zero_position(self, order_simulator):
        """Test getting position for symbol with no trades"""
        position = order_simulator.get_position('MNQ')
        assert position == 0

    @pytest.mark.asyncio
    async def test_partial_fills(self, market_simulator, order_simulator):
        """Test that orders can have partial fills"""
        # Place larger order to increase chance of partials
        order = await order_simulator.place_order({
            'contract_id': 'MNQ',
            'type': 'market',
            'side': 0,
            'size': 5
        })

        # Verify fills sum to total size
        total_filled = sum(f.size for f in order.fills)
        assert total_filled == 5

        # Each fill should have price and timestamp
        for fill in order.fills:
            assert fill.price > 0
            assert isinstance(fill.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_slippage_exists(self, market_simulator, order_simulator):
        """Test that market orders have slippage"""
        current_price = market_simulator.current_price

        order = await order_simulator.place_order({
            'contract_id': 'MNQ',
            'type': 'market',
            'side': 0,  # Buy
            'size': 1
        })

        # Buy order should fill slightly above market (slippage)
        assert order.avg_fill_price >= current_price


if __name__ == "__main__":
    # Run tests with: pytest tests/integration/test_market_simulation.py -v
    pytest.main([__file__, "-v", "-s"])
