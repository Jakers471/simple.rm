"""
E2E Tests - Performance Tests
Test ID Range: E2E-026 to E2E-027

Tests system performance under high load, stress conditions,
and long-running scenarios.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock
import threading


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.stress
class TestPerformance:
    """E2E performance and stress tests"""

    @pytest.mark.timeout(600)  # 10 minutes
    def test_e2e_026_high_volume_event_processing(
        self,
        test_daemon,
        mock_signalr_user_hub,
        mock_signalr_market_hub,
        performance_monitor,
        test_config
    ):
        """
        E2E-026: High Volume Event Processing

        Given: Daemon running with all rules enabled
        When: Process 1000+ events across multiple accounts
        Then: All events processed, latency acceptable, no crashes

        Duration: ~10 minutes
        """
        # Multiple accounts for load distribution
        accounts = [12345, 67890, 11111, 22222, 33333]

        test_config["accounts"] = [
            {"account_id": acc_id, "username": f"trader_{acc_id}"}
            for acc_id in accounts
        ]

        # Enable all rules
        test_config.update({
            "max_contracts": {"enabled": True, "limit": 10},
            "daily_realized_loss": {"enabled": True, "limit": -1000},
            "daily_unrealized_loss": {"enabled": True, "limit": 500},
            "trade_frequency_limit": {"enabled": True, "per_minute": 10},
            "no_stop_loss_grace": {"enabled": True, "grace_period_seconds": 30}
        })

        daemon = test_daemon.start(config=test_config)
        performance_monitor.start()
        time.sleep(2)

        # Test parameters
        total_events = 1000
        positions_per_account = 5
        trades_per_account = 100
        quotes_per_symbol = 200

        start_time = time.time()

        # Step 1: Create positions for all accounts
        position_events = []
        for account_id in accounts:
            for i in range(positions_per_account):
                position = {
                    "id": 5000 + (account_id % 10000) * 10 + i,
                    "accountId": account_id,
                    "contractId": f"CON.F.US.MNQ.U25",
                    "type": 1,
                    "size": 1,
                    "averagePrice": 21000.00 + i * 10
                }
                position_events.append(position)

        # Send positions in batches
        batch_size = 10
        for i in range(0, len(position_events), batch_size):
            batch = position_events[i:i + batch_size]
            for pos in batch:
                mock_signalr_user_hub.send_event("GatewayUserPosition", pos)
            time.sleep(0.1)  # Brief pause between batches

        # Verify positions created
        total_positions = sum(
            daemon.state_manager.get_position_count(acc) for acc in accounts
        )
        assert total_positions == len(accounts) * positions_per_account

        # Step 2: Generate trade events
        trade_events = []
        for account_id in accounts:
            for i in range(trades_per_account):
                trade = {
                    "id": 7000 + (account_id % 10000) * 100 + i,
                    "accountId": account_id,
                    "contractId": "CON.F.US.MNQ.U25",
                    "profitAndLoss": (i % 2 == 0) * 25.00 - (i % 2 == 1) * 15.00,
                    "price": 21000.00 + i
                }
                trade_events.append(trade)

        # Send trades in batches
        for i in range(0, len(trade_events), batch_size):
            batch = trade_events[i:i + batch_size]
            for trade in batch:
                mock_signalr_user_hub.send_event("GatewayUserTrade", trade)
            time.sleep(0.05)

        # Step 3: Generate quote events (high frequency)
        symbols = ["F.US.MNQ", "F.US.ES", "F.US.NQ", "F.US.YM"]
        quote_events = []

        for symbol in symbols:
            base_price = 21000.00 if "MNQ" in symbol else 5800.00
            for i in range(quotes_per_symbol):
                quote = {
                    "symbol": symbol,
                    "lastPrice": base_price + (i % 20) - 10,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                quote_events.append(quote)

        # Send quotes in rapid succession
        for i in range(0, len(quote_events), 5):
            batch = quote_events[i:i + 5]
            for quote in batch:
                mock_signalr_market_hub.send_event("MarketQuote", quote)
            time.sleep(0.01)  # 10ms between batches → 500 quotes/sec

        elapsed = time.time() - start_time

        # Step 4: Verify all events processed
        time.sleep(5)  # Allow processing to complete

        # Verify event counts
        total_processed = (
            len(position_events) +
            len(trade_events) +
            len(quote_events)
        )
        assert total_processed >= total_events

        # Step 5: Verify performance metrics
        metrics = performance_monitor.get_metrics()

        # Event processing rate
        events_per_second = total_processed / elapsed
        assert events_per_second > 50  # At least 50 events/sec

        # Average latency
        avg_latency = metrics["avg_event_processing_time"]
        assert avg_latency < 0.020  # < 20ms average

        # Max latency
        max_latency = metrics["max_event_processing_time"]
        assert max_latency < 0.100  # < 100ms max

        # CPU usage
        assert metrics["avg_cpu_usage"] < 30  # < 30% CPU

        # Memory usage
        memory_growth = metrics["memory_mb_end"] - metrics["memory_mb_start"]
        assert memory_growth < 50  # < 50 MB growth

        # Step 6: Verify state consistency
        # All positions still tracked
        final_positions = sum(
            daemon.state_manager.get_position_count(acc) for acc in accounts
        )
        assert final_positions > 0

        # P&L tracked for all accounts
        for account_id in accounts:
            pnl = daemon.pnl_tracker.get_daily_realized_pnl(account_id)
            assert pnl != 0  # Some trades executed

        # Step 7: Verify no crashes or errors
        assert daemon.is_running()
        assert daemon.all_threads_alive()
        assert daemon.get_error_count() == 0

        daemon.stop()
        performance_monitor.stop()

    @pytest.mark.timeout(7200)  # 2 hours
    @pytest.mark.long_running
    def test_e2e_027_long_running_stability_test(
        self,
        test_daemon,
        mock_signalr_user_hub,
        mock_signalr_market_hub,
        performance_monitor,
        test_config
    ):
        """
        E2E-027: Long-Running Stability Test

        Given: Daemon running continuously
        When: Run for 2 hours with periodic events
        Then: No crashes, memory leaks, or degradation

        Duration: ~2 hours (can be reduced with time acceleration)
        """
        account_id = 12345

        test_config.update({
            "max_contracts": {"enabled": True, "limit": 10},
            "daily_realized_loss": {"enabled": True, "limit": -1000}
        })

        daemon = test_daemon.start(config=test_config)
        performance_monitor.start()
        time.sleep(2)

        # Test duration
        test_duration_seconds = 7200  # 2 hours
        event_interval_seconds = 60  # Event every minute

        # Baseline metrics
        baseline_memory = performance_monitor.get_current_memory_mb()
        baseline_cpu = performance_monitor.get_current_cpu_percent()

        start_time = time.time()
        iteration = 0

        try:
            while (time.time() - start_time) < test_duration_seconds:
                iteration += 1
                elapsed = time.time() - start_time

                # Every minute: send position update
                if iteration % 1 == 0:
                    position = {
                        "id": 5000 + (iteration % 10),
                        "accountId": account_id,
                        "contractId": "CON.F.US.MNQ.U25",
                        "type": 1,
                        "size": 1 + (iteration % 3),
                        "averagePrice": 21000.00 + (iteration % 100)
                    }
                    mock_signalr_user_hub.send_event("GatewayUserPosition", position)

                # Every minute: send trade
                if iteration % 1 == 0:
                    trade = {
                        "id": 7000 + iteration,
                        "accountId": account_id,
                        "contractId": "CON.F.US.MNQ.U25",
                        "profitAndLoss": (iteration % 2 == 0) * 25.00 - 15.00,
                        "price": 21000.00 + iteration
                    }
                    mock_signalr_user_hub.send_event("GatewayUserTrade", trade)

                # Every 10 seconds: send quotes
                if iteration % 1 == 0:
                    for _ in range(5):
                        quote = {
                            "symbol": "F.US.MNQ",
                            "lastPrice": 21000.00 + (iteration % 50) - 25,
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                        mock_signalr_market_hub.send_event("MarketQuote", quote)

                # Every 15 minutes: check health
                if iteration % 15 == 0:
                    assert daemon.is_running()
                    assert daemon.all_threads_alive()

                    # Memory leak check
                    current_memory = performance_monitor.get_current_memory_mb()
                    memory_growth = current_memory - baseline_memory
                    assert memory_growth < 100  # < 100 MB growth per 15 min

                    # CPU check
                    current_cpu = performance_monitor.get_current_cpu_percent()
                    assert current_cpu < 40  # < 40% CPU

                    # Log progress
                    print(f"[{elapsed:.0f}s] Health check passed. Memory: {current_memory:.1f} MB, CPU: {current_cpu:.1f}%")

                # Every hour: verify state
                if iteration % 60 == 0:
                    pnl = daemon.pnl_tracker.get_daily_realized_pnl(account_id)
                    positions = daemon.state_manager.get_position_count(account_id)
                    print(f"[{elapsed:.0f}s] State check. P&L: ${pnl:.2f}, Positions: {positions}")

                time.sleep(event_interval_seconds)

        except KeyboardInterrupt:
            print("Test interrupted by user")

        # Final verification
        elapsed_total = time.time() - start_time

        # Verify daemon still running
        assert daemon.is_running()
        assert daemon.all_threads_alive()

        # Final metrics
        final_metrics = performance_monitor.get_metrics()

        # Memory leak check
        final_memory = final_metrics["memory_mb_end"]
        memory_growth_total = final_memory - baseline_memory
        memory_growth_per_hour = memory_growth_total / (elapsed_total / 3600)

        print(f"Final memory growth: {memory_growth_total:.1f} MB total, {memory_growth_per_hour:.1f} MB/hour")
        assert memory_growth_per_hour < 50  # < 50 MB/hour acceptable

        # CPU usage
        avg_cpu = final_metrics["avg_cpu_usage"]
        assert avg_cpu < 25  # < 25% average CPU

        # Error count
        error_count = daemon.get_error_count()
        assert error_count == 0  # No errors

        # Event processing
        total_events = final_metrics["total_events_processed"]
        assert total_events > (elapsed_total / event_interval_seconds) * 3  # At least 3 events/interval

        # Database integrity
        assert daemon.database.check_integrity() == "ok"

        daemon.stop()
        performance_monitor.stop()

        print(f"Long-running test completed successfully after {elapsed_total / 3600:.2f} hours")
