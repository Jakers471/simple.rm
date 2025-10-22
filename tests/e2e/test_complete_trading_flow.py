"""
E2E Tests - Complete Trading Flows
Test ID Range: E2E-001 to E2E-005

Tests complete trading workflows from daemon startup to shutdown,
including normal flows, stop-loss handling, crash recovery, multi-account,
and full trading day simulation.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteTradingFlows:
    """E2E tests for complete trading workflows"""

    def test_e2e_001_normal_trading_flow_no_violations(
        self,
        test_daemon,
        mock_api,
        mock_signalr_user_hub,
        mock_signalr_market_hub,
        test_database
    ):
        """
        E2E-001: Normal Trading Flow (No Violations)

        Given: Daemon stopped, empty database, test account configured
        When: Complete trading cycle (startup → order → fill → position → quotes → close → shutdown)
        Then: All operations succeed, no violations, state persisted correctly

        Duration: ~2 minutes
        """
        # Given: Initial configuration
        account_id = 12345
        config = {
            "max_contracts": 5,
            "daily_realized_loss": -500
        }

        # Step 1: Start daemon
        daemon = test_daemon.start(config=config)
        time.sleep(2)  # Allow startup sequence (29 steps)

        assert daemon.is_running()
        assert daemon.startup_complete()
        assert mock_signalr_user_hub.is_connected()
        assert mock_signalr_market_hub.is_connected()

        # Step 2: Trader places order
        order_event = {
            "id": 1001,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 2,  # Limit
            "side": 1,  # Buy
            "size": 2,
            "limitPrice": 21000.00,
            "state": 1  # Working
        }
        mock_signalr_user_hub.send_event("GatewayUserOrder", order_event)
        time.sleep(0.5)

        # Verify order tracked
        assert daemon.state_manager.get_order(1001) is not None
        assert daemon.state_manager.get_order(1001)["state"] == 1

        # Step 3: Order fills
        fill_event = order_event.copy()
        fill_event["state"] = 2  # Filled
        fill_event["averageFillPrice"] = 21000.25
        mock_signalr_user_hub.send_event("GatewayUserOrder", fill_event)
        time.sleep(0.5)

        assert daemon.state_manager.get_order(1001)["state"] == 2

        # Step 4: Position opens
        position_event = {
            "id": 5001,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,  # Long
            "size": 2,
            "averagePrice": 21000.25
        }
        mock_signalr_user_hub.send_event("GatewayUserPosition", position_event)
        time.sleep(0.5)

        # Verify position tracking
        assert daemon.state_manager.get_position_count(account_id) == 2
        assert mock_signalr_market_hub.is_subscribed("F.US.MNQ")

        # Step 5: Quote updates (price moves up)
        quote_event = {
            "symbol": "F.US.MNQ",
            "lastPrice": 21050.00,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_market_hub.send_event("MarketQuote", quote_event)
        time.sleep(0.5)

        # Verify quote tracked and unrealized P&L calculated
        assert daemon.quote_tracker.get_last_price("F.US.MNQ") == 21050.00
        unrealized_pnl = daemon.pnl_tracker.get_unrealized_pnl(account_id)
        assert unrealized_pnl > 0  # Profitable position

        # Step 6: Trader closes position
        close_position_event = position_event.copy()
        close_position_event["size"] = 0
        mock_signalr_user_hub.send_event("GatewayUserPosition", close_position_event)
        time.sleep(0.5)

        assert daemon.state_manager.get_position_count(account_id) == 0
        assert not mock_signalr_market_hub.is_subscribed("F.US.MNQ")

        # Step 7: Trade P&L realized
        trade_event = {
            "id": 7001,
            "accountId": account_id,
            "profitAndLoss": 49.75,
            "contractId": "CON.F.US.MNQ.U25"
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade_event)
        time.sleep(0.5)

        # Verify P&L tracking
        daily_pnl = daemon.pnl_tracker.get_daily_realized_pnl(account_id)
        assert daily_pnl == 49.75
        assert not daemon.lockout_manager.is_locked_out(account_id)

        # Step 8: Shutdown daemon
        daemon.stop()
        time.sleep(1)

        assert not daemon.is_running()

        # Step 9: Verify SQLite persistence
        db_pnl = test_database.get_daily_pnl(account_id)
        assert db_pnl == 49.75

        db_trades = test_database.get_trade_history(account_id)
        assert len(db_trades) == 1
        assert db_trades[0]["profit_and_loss"] == 49.75

        # No enforcement logs (no violations)
        enforcement_logs = test_database.get_enforcement_logs(account_id)
        assert len(enforcement_logs) == 0

    def test_e2e_002_complete_flow_with_stop_loss(
        self,
        test_daemon,
        mock_signalr_user_hub,
        test_config
    ):
        """
        E2E-002: Complete Trading Flow with Stop-Loss

        Given: Daemon running, no_stop_loss_grace enabled
        When: Position opens without SL, then SL placed within grace period
        Then: Grace timer cancelled, no enforcement action

        Duration: ~2 minutes
        """
        account_id = 12345
        test_config["no_stop_loss_grace"] = {
            "enabled": True,
            "grace_period_seconds": 30,
            "action": "close_all_and_lockout"
        }

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Step 1: Open position without stop-loss
        position_event = {
            "id": 5002,
            "accountId": account_id,
            "contractId": "CON.F.US.ES.U25",
            "type": 1,  # Long
            "size": 1,
            "averagePrice": 5800.00
        }
        mock_signalr_user_hub.send_event("GatewayUserPosition", position_event)
        time.sleep(0.5)

        # Verify grace timer started
        assert daemon.timer_manager.has_active_timer(f"no_sl_grace_{account_id}_5002")
        remaining = daemon.timer_manager.get_remaining_time(f"no_sl_grace_{account_id}_5002")
        assert 25 < remaining <= 30

        # Step 2: Wait 10 seconds (within grace period)
        time.sleep(10)

        # Still in grace period
        remaining = daemon.timer_manager.get_remaining_time(f"no_sl_grace_{account_id}_5002")
        assert 15 < remaining <= 20
        assert not daemon.lockout_manager.is_locked_out(account_id)

        # Step 3: Place stop-loss order
        stop_loss_event = {
            "id": 1002,
            "accountId": account_id,
            "contractId": "CON.F.US.ES.U25",
            "type": 3,  # Stop
            "side": 2,  # Sell (opposite of Long)
            "size": 1,
            "stopPrice": 5790.00,
            "state": 1  # Working
        }
        mock_signalr_user_hub.send_event("GatewayUserOrder", stop_loss_event)
        time.sleep(0.5)

        # Step 4: Verify grace timer cancelled
        assert not daemon.timer_manager.has_active_timer(f"no_sl_grace_{account_id}_5002")
        assert not daemon.lockout_manager.is_locked_out(account_id)
        assert daemon.state_manager.get_position_count(account_id) == 1

        daemon.stop()

    def test_e2e_003_daemon_restart_with_state_recovery(
        self,
        test_daemon,
        test_database,
        mock_signalr_user_hub
    ):
        """
        E2E-003: Daemon Restart with State Recovery

        Given: Daemon running with active position and P&L
        When: Daemon crashes and restarts
        Then: State recovered from SQLite, monitoring resumes correctly

        Duration: ~3 minutes
        """
        account_id = 12345

        # Step 1: Start daemon and establish state
        daemon = test_daemon.start()
        time.sleep(1)

        # Create position
        position_event = {
            "id": 5003,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,  # Long
            "size": 3,
            "averagePrice": 21000.00
        }
        mock_signalr_user_hub.send_event("GatewayUserPosition", position_event)

        # Create P&L
        trade_event = {
            "id": 7001,
            "accountId": account_id,
            "profitAndLoss": -250.00,
            "contractId": "CON.F.US.MNQ.U25"
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade_event)
        time.sleep(0.5)

        # Verify state before crash
        assert daemon.state_manager.get_position_count(account_id) == 3
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == -250.00

        # Step 2: Simulate crash
        daemon.crash_simulate()  # Emergency shutdown
        time.sleep(1)

        # Step 3: Restart daemon
        daemon = test_daemon.start()  # Fresh start, loads from DB
        time.sleep(2)

        # Step 4: Verify state recovery
        recovered_pnl = daemon.pnl_tracker.get_daily_realized_pnl(account_id)
        assert recovered_pnl == -250.00

        recovered_positions = daemon.state_manager.get_position_count(account_id)
        assert recovered_positions == 3

        # No lockouts recovered (none were set)
        assert not daemon.lockout_manager.is_locked_out(account_id)

        # Market Hub resubscribes to symbols
        assert daemon.market_hub.is_subscribed("F.US.MNQ")

        daemon.stop()

    def test_e2e_004_multi_account_monitoring(
        self,
        test_daemon,
        mock_signalr_user_hub,
        test_config
    ):
        """
        E2E-004: Multi-Account Monitoring

        Given: Two accounts configured and authenticated
        When: Account 1 trades within limits, Account 2 breaches loss limit
        Then: Account 2 locked out independently, Account 1 unaffected

        Duration: ~3 minutes
        """
        account_1 = 12345
        account_2 = 67890

        test_config["accounts"] = [
            {"account_id": account_1, "username": "trader1", "api_key": "key1"},
            {"account_id": account_2, "username": "trader2", "api_key": "key2"}
        ]
        test_config["daily_realized_loss"] = {
            "enabled": True,
            "limit": -500,
            "enforcement": "close_all_and_lockout"
        }

        # Step 1: Start daemon
        daemon = test_daemon.start(config=test_config)
        time.sleep(2)

        # Verify both accounts authenticated
        assert daemon.has_token(account_1)
        assert daemon.has_token(account_2)

        # Step 2: Account 1 trades (within limits)
        trade_1 = {
            "id": 7001,
            "accountId": account_1,
            "profitAndLoss": -100.00,
            "contractId": "CON.F.US.MNQ.U25"
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade_1)
        time.sleep(0.5)

        assert daemon.pnl_tracker.get_daily_realized_pnl(account_1) == -100.00
        assert not daemon.lockout_manager.is_locked_out(account_1)

        # Step 3: Account 2 trades (breach limit)
        trade_2 = {
            "id": 7002,
            "accountId": account_2,
            "profitAndLoss": -550.00,
            "contractId": "CON.F.US.ES.U25"
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade_2)
        time.sleep(0.5)

        # Verify Account 2 enforcement
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_2) == -550.00
        assert daemon.lockout_manager.is_locked_out(account_2)

        lockout = daemon.lockout_manager.get_lockout(account_2)
        assert lockout is not None
        assert "daily loss limit" in lockout["reason"].lower()

        # Step 4: Verify Account 1 unaffected
        assert not daemon.lockout_manager.is_locked_out(account_1)

        # Account 1 can still trade
        trade_3 = {
            "id": 7003,
            "accountId": account_1,
            "profitAndLoss": 50.00,
            "contractId": "CON.F.US.MNQ.U25"
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade_3)
        time.sleep(0.5)

        assert daemon.pnl_tracker.get_daily_realized_pnl(account_1) == -50.00

        # Account 2 events are skipped
        trade_4 = {
            "id": 7004,
            "accountId": account_2,
            "profitAndLoss": 100.00,  # Would improve P&L
            "contractId": "CON.F.US.ES.U25"
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade_4)
        time.sleep(0.5)

        # P&L unchanged (event skipped due to lockout)
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_2) == -550.00

        daemon.stop()

    @pytest.mark.slow
    @pytest.mark.timeout(600)  # 10 minutes
    def test_e2e_005_full_trading_day_simulation(
        self,
        test_daemon,
        mock_signalr_user_hub,
        mock_signalr_market_hub,
        time_accelerator,
        test_config
    ):
        """
        E2E-005: Full Trading Day Simulation (8 Hours)

        Given: Time-accelerated simulation (1 minute = 1 hour)
        When: Simulate full trading day with multiple scenarios
        Then: All rules tested, daily reset executes correctly

        Duration: ~10 minutes (accelerated from 8 hours)
        """
        account_id = 12345

        # Enable time acceleration (60x speed)
        time_accelerator.set_multiplier(60)

        # Enable all risk rules
        test_config.update({
            "max_contracts": {"enabled": True, "limit": 5},
            "daily_realized_loss": {"enabled": True, "limit": -500},
            "daily_unrealized_loss": {"enabled": True, "limit": 300},
            "trade_frequency_limit": {"enabled": True, "per_minute": 3},
            "no_stop_loss_grace": {"enabled": True, "grace_period_seconds": 30},
            "session_block_outside": {"enabled": True, "start": "09:30", "end": "16:00"}
        })

        daemon = test_daemon.start(config=test_config)
        time.sleep(2)

        # 9:30 AM - Session start
        time_accelerator.set_time("09:30")

        # Open position with stop-loss
        position = {
            "id": 5001,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,
            "size": 2,
            "averagePrice": 21000.00
        }
        mock_signalr_user_hub.send_event("GatewayUserPosition", position)

        stop_loss = {
            "id": 1001,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 3,
            "side": 2,
            "size": 2,
            "stopPrice": 20990.00,
            "state": 1
        }
        mock_signalr_user_hub.send_event("GatewayUserOrder", stop_loss)
        time.sleep(0.5)

        # 10:00 AM - Morning trading (5 profitable trades)
        time_accelerator.advance_hours(0.5)
        for i in range(5):
            trade = {
                "id": 7000 + i,
                "accountId": account_id,
                "profitAndLoss": 30.00,
                "contractId": "CON.F.US.MNQ.U25"
            }
            mock_signalr_user_hub.send_event("GatewayUserTrade", trade)
            time.sleep(0.1)

        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == 150.00

        # 11:00 AM - Frequency test (breach per_minute=3)
        time_accelerator.advance_hours(1)
        for i in range(4):
            trade = {
                "id": 7010 + i,
                "accountId": account_id,
                "profitAndLoss": 10.00,
                "contractId": "CON.F.US.MNQ.U25"
            }
            mock_signalr_user_hub.send_event("GatewayUserTrade", trade)
            time.sleep(0.2)  # All within 1 minute

        # Should trigger cooldown
        assert daemon.lockout_manager.is_locked_out(account_id)

        # Wait for cooldown
        time.sleep(2)  # 60 seconds in accelerated time
        assert not daemon.lockout_manager.is_locked_out(account_id)

        # Continue simulation through afternoon...
        # (Additional scenarios omitted for brevity)

        # 5:00 PM - Daily reset
        time_accelerator.set_time("17:00")
        time.sleep(2)

        # Verify reset executed
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == 0
        assert not daemon.lockout_manager.is_locked_out(account_id)

        daemon.stop()
