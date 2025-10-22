"""
E2E Tests - SignalR Event-Triggered Workflows
Test ID Range: E2E-014 to E2E-018

Tests SignalR event routing and rule triggering from real-time events,
including quote updates, order events, account events, and high-frequency scenarios.
"""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock


@pytest.mark.e2e
@pytest.mark.slow
class TestSignalRTriggers:
    """E2E tests for SignalR event-triggered workflows"""

    def test_e2e_014_quote_update_triggers_unrealized_loss_rule(
        self,
        test_daemon,
        mock_signalr_market_hub,
        mock_api,
        test_config
    ):
        """
        E2E-014: Quote Update Triggers Unrealized Loss Rule

        Given: Position Long 3 MNQ @ 21000.00, loss_limit=300, scope=total
        When: Market drops gradually: 21000 → 20950 → 20900 → 20850
        Then: RULE-004 triggered at 20850, all positions closed

        Duration: ~2 minutes
        """
        account_id = 12345
        test_config["daily_unrealized_loss"] = {
            "enabled": True,
            "loss_limit": 300.00,
            "scope": "total",
            "action": "close_all_and_lockout"
        }

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Open position
        position = {
            "id": 5010,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,
            "size": 3,
            "averagePrice": 21000.00
        }
        daemon.state_manager.add_position(position)

        # Step 1: Initial quote (at entry, no unrealized P&L)
        quote_1 = {
            "symbol": "F.US.MNQ",
            "lastPrice": 21000.00,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_market_hub.send_event("MarketQuote", quote_1)
        time.sleep(0.5)

        unrealized = daemon.pnl_tracker.get_unrealized_pnl(account_id)
        assert unrealized == pytest.approx(0.0, abs=1.0)

        # Step 2: Price drops to 20950 (-$150)
        quote_2 = {
            "symbol": "F.US.MNQ",
            "lastPrice": 20950.00,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_market_hub.send_event("MarketQuote", quote_2)
        time.sleep(0.5)

        unrealized = daemon.pnl_tracker.get_unrealized_pnl(account_id)
        assert unrealized == pytest.approx(-150.0, abs=10.0)
        assert not daemon.enforcement_executed()  # -150 > -300 (no breach)

        # Step 3: Price drops to 20900 (-$300, at limit)
        quote_3 = {
            "symbol": "F.US.MNQ",
            "lastPrice": 20900.00,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_market_hub.send_event("MarketQuote", quote_3)
        time.sleep(0.5)

        unrealized = daemon.pnl_tracker.get_unrealized_pnl(account_id)
        assert unrealized == pytest.approx(-300.0, abs=10.0)
        assert not daemon.enforcement_executed()  # At limit OK

        # Step 4: Price drops to 20850 (-$450, BREACH)
        quote_4 = {
            "symbol": "F.US.MNQ",
            "lastPrice": 20850.00,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_market_hub.send_event("MarketQuote", quote_4)
        time.sleep(0.5)

        # Verify breach detection
        unrealized = daemon.pnl_tracker.get_unrealized_pnl(account_id)
        assert unrealized < -300.0

        # Verify enforcement
        assert daemon.enforcement_executed()
        assert mock_api.was_called("POST", "/api/Position/closeContract")
        assert mock_api.was_called("POST", "/api/Order/cancel")

        # Lockout set
        assert daemon.lockout_manager.is_locked_out(account_id)

        # Position closed
        assert daemon.state_manager.get_position_count(account_id) == 0

        daemon.stop()

    def test_e2e_015_multiple_positions_different_quote_updates(
        self,
        test_daemon,
        mock_signalr_market_hub,
        mock_api,
        test_config
    ):
        """
        E2E-015: Multiple Positions, Different Quote Updates

        Given: Long 2 MNQ @ 21000, Long 1 ES @ 5800, loss_limit=300 (total)
        When: MNQ drops to 20900 (-$200), then ES drops to 5792 (-$200)
        Then: Combined unrealized=-$400, breach triggers enforcement

        Duration: ~2 minutes
        """
        account_id = 12345
        test_config["daily_unrealized_loss"] = {
            "enabled": True,
            "loss_limit": 300.00,
            "scope": "total"  # Combined loss across all positions
        }

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Open two positions
        position_mnq = {
            "id": 5011,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,
            "size": 2,
            "averagePrice": 21000.00
        }
        position_es = {
            "id": 5012,
            "accountId": account_id,
            "contractId": "CON.F.US.ES.U25",
            "type": 1,
            "size": 1,
            "averagePrice": 5800.00
        }
        daemon.state_manager.add_position(position_mnq)
        daemon.state_manager.add_position(position_es)

        # Subscribe to both symbols
        assert daemon.market_hub.is_subscribed("F.US.MNQ")
        assert daemon.market_hub.is_subscribed("F.US.ES")

        # Step 1: MNQ drops (-$200)
        quote_mnq = {
            "symbol": "F.US.MNQ",
            "lastPrice": 20900.00,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_market_hub.send_event("MarketQuote", quote_mnq)
        time.sleep(0.5)

        # Only MNQ loss so far
        unrealized = daemon.pnl_tracker.get_unrealized_pnl(account_id)
        assert unrealized == pytest.approx(-200.0, abs=10.0)
        assert not daemon.enforcement_executed()  # -200 > -300

        # Step 2: ES drops (-$200)
        quote_es = {
            "symbol": "F.US.ES",
            "lastPrice": 5792.00,  # -8 points = -$200
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_market_hub.send_event("MarketQuote", quote_es)
        time.sleep(0.5)

        # Combined loss: -$400
        unrealized = daemon.pnl_tracker.get_unrealized_pnl(account_id)
        assert unrealized == pytest.approx(-400.0, abs=20.0)

        # Breach: -400 < -300
        assert daemon.enforcement_executed()

        # Step 3: Verify both positions closed
        assert mock_api.call_count("POST", "/api/Position/closeContract") == 2
        assert daemon.state_manager.get_position_count(account_id) == 0

        # Step 4: Verify Market Hub unsubscribes
        assert not daemon.market_hub.is_subscribed("F.US.MNQ")
        assert not daemon.market_hub.is_subscribed("F.US.ES")

        daemon.stop()

    def test_e2e_016_order_event_triggers_stop_loss_detection(
        self,
        test_daemon,
        mock_signalr_user_hub,
        test_config
    ):
        """
        E2E-016: Order Event Triggers Stop-Loss Detection

        Given: Position Long 2 MNQ, grace timer active (25s remaining)
        When: Stop-loss order event arrives
        Then: RULE-008 validates order, grace timer cancelled

        Duration: ~1 minute
        """
        account_id = 12345
        test_config["no_stop_loss_grace"] = {
            "enabled": True,
            "grace_period_seconds": 30
        }

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Open position (starts grace timer)
        position = {
            "id": 5013,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,  # Long
            "size": 2,
            "averagePrice": 21000.00
        }
        mock_signalr_user_hub.send_event("GatewayUserPosition", position)
        time.sleep(0.5)

        timer_key = f"no_sl_grace_{account_id}_5013"
        assert daemon.timer_manager.has_active_timer(timer_key)

        # Wait 5 seconds
        time.sleep(5)

        # Grace timer still active
        remaining = daemon.timer_manager.get_remaining_time(timer_key)
        assert 23 < remaining <= 26

        # Step 1: Place stop-loss order
        stop_loss = {
            "id": 1003,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 3,  # Stop
            "side": 2,  # Sell (opposite of Long)
            "size": 2,
            "stopPrice": 20980.00,
            "state": 1  # Working
        }
        mock_signalr_user_hub.send_event("GatewayUserOrder", stop_loss)
        time.sleep(0.5)

        # Step 2: Verify RULE-008 validation
        order = daemon.state_manager.get_order(1003)
        assert order is not None
        assert order["type"] == 3  # Stop
        assert order["side"] == 2  # Sell

        # Step 3: Verify grace timer cancelled
        assert not daemon.timer_manager.has_active_timer(timer_key)

        # Step 4: Verify no enforcement
        assert not daemon.enforcement_executed()
        assert not daemon.lockout_manager.is_locked_out(account_id)
        assert daemon.state_manager.get_position_count(account_id) == 2

        daemon.stop()

    def test_e2e_017_account_event_triggers_auth_loss_guard(
        self,
        test_daemon,
        mock_signalr_user_hub,
        mock_api,
        test_config
    ):
        """
        E2E-017: Account Event Triggers Auth Loss Guard

        Given: Position open, auth_loss_guard enabled
        When: GatewayUserAccount event with "AuthorizationLost"
        Then: RULE-010 triggers defensive close, permanent lockout

        Duration: ~1 minute
        """
        account_id = 12345
        test_config["auth_loss_guard"] = {
            "enabled": True,
            "action": "close_all_and_lockout"
        }

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Open position
        position = {
            "id": 5014,
            "accountId": account_id,
            "contractId": "CON.F.US.ES.U25",
            "type": 1,
            "size": 1,
            "averagePrice": 5800.00
        }
        mock_signalr_user_hub.send_event("GatewayUserPosition", position)
        time.sleep(0.5)

        assert daemon.state_manager.get_position_count(account_id) == 1

        # Step 1: Suspicious account event arrives
        account_event = {
            "accountId": account_id,
            "eventType": "AuthorizationLost",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_user_hub.send_event("GatewayUserAccount", account_event)
        time.sleep(0.5)

        # Step 2: Verify RULE-010 detection
        assert daemon.enforcement_executed()

        # Step 3: Verify defensive close
        assert mock_api.was_called("POST", "/api/Position/closeContract")
        assert daemon.state_manager.get_position_count(account_id) == 0

        # Step 4: Verify permanent lockout
        assert daemon.lockout_manager.is_locked_out(account_id)

        lockout = daemon.lockout_manager.get_lockout(account_id)
        assert lockout is not None
        assert lockout["until"] is None  # Permanent (no expiry)
        assert "authorization" in lockout["reason"].lower()

        daemon.stop()

    @pytest.mark.stress
    def test_e2e_018_high_frequency_quote_updates_stress_test(
        self,
        test_daemon,
        mock_signalr_market_hub,
        test_config,
        performance_monitor
    ):
        """
        E2E-018: High-Frequency Quote Updates (Stress Test)

        Given: Position Long 5 MNQ, all rules enabled
        When: 100 quote updates in 10 seconds (10 quotes/second)
        Then: All quotes processed, latency < 10ms per quote, no missed events

        Duration: ~30 seconds
        """
        account_id = 12345

        # Enable all rules for comprehensive stress test
        test_config.update({
            "max_contracts": {"enabled": True, "limit": 10},
            "daily_unrealized_loss": {"enabled": True, "limit": 1000.00},
            "max_unrealized_profit": {"enabled": True, "limit": 5000.00}
        })

        daemon = test_daemon.start(config=test_config)
        performance_monitor.start()
        time.sleep(1)

        # Open position
        position = {
            "id": 5015,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,
            "size": 5,
            "averagePrice": 21000.00
        }
        daemon.state_manager.add_position(position)

        # Step 1: Simulate 100 quotes in 10 seconds
        quote_count = 100
        duration_seconds = 10
        prices = [20995, 21005, 20998, 21003, 20997, 21001, 20999, 21002, 21000, 21004]

        start_time = time.time()
        for i in range(quote_count):
            quote = {
                "symbol": "F.US.MNQ",
                "lastPrice": prices[i % len(prices)],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            mock_signalr_market_hub.send_event("MarketQuote", quote)
            time.sleep(duration_seconds / quote_count)  # 0.1s between quotes

        elapsed = time.time() - start_time

        # Step 2: Verify all quotes processed
        quote_tracker_count = daemon.quote_tracker.get_update_count("F.US.MNQ")
        assert quote_tracker_count == quote_count

        # Step 3: Verify no quotes dropped
        assert daemon.market_hub.get_dropped_events() == 0

        # Step 4: Verify performance metrics
        metrics = performance_monitor.get_metrics()

        # Average latency per quote should be < 5ms
        avg_latency = metrics["avg_quote_processing_time"]
        assert avg_latency < 0.005  # 5ms

        # Max latency should be < 10ms
        max_latency = metrics["max_quote_processing_time"]
        assert max_latency < 0.010  # 10ms

        # CPU usage should be reasonable
        assert metrics["cpu_usage_percent"] < 20

        # Memory should be stable (no leak)
        memory_start = metrics["memory_mb_start"]
        memory_end = metrics["memory_mb_end"]
        memory_growth = memory_end - memory_start
        assert memory_growth < 10  # Less than 10 MB growth

        # Step 5: Verify state consistency
        final_price = daemon.quote_tracker.get_last_price("F.US.MNQ")
        assert final_price in prices  # Last quote received

        # Position unchanged (no breaches)
        assert daemon.state_manager.get_position_count(account_id) == 5
        assert not daemon.enforcement_executed()

        # All background threads still running
        assert daemon.all_threads_alive()

        daemon.stop()
        performance_monitor.stop()
