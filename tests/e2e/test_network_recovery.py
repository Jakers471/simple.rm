"""
E2E Tests - Network & Recovery Workflows
Test ID Range: E2E-022 to E2E-025

Tests network disconnection, reconnection, crash recovery,
and resilience scenarios.
"""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch


@pytest.mark.e2e
@pytest.mark.slow
class TestNetworkRecovery:
    """E2E tests for network and recovery workflows"""

    def test_e2e_022_signalr_disconnection_and_reconnection(
        self,
        test_daemon,
        mock_signalr_user_hub,
        mock_signalr_market_hub,
        test_config
    ):
        """
        E2E-022: SignalR Disconnection and Reconnection

        Given: Daemon running with active connections
        When: SignalR User Hub disconnects, then reconnects
        Then: Connection restored, event processing resumes, no data loss

        Duration: ~2 minutes
        """
        account_id = 12345

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Verify initial connection
        assert mock_signalr_user_hub.is_connected()
        assert mock_signalr_market_hub.is_connected()

        # Open position before disconnection
        position = {
            "id": 5020,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,
            "size": 2,
            "averagePrice": 21000.00
        }
        mock_signalr_user_hub.send_event("GatewayUserPosition", position)
        time.sleep(0.5)

        assert daemon.state_manager.get_position_count(account_id) == 2

        # Step 1: Simulate User Hub disconnection
        mock_signalr_user_hub.disconnect()
        time.sleep(0.5)

        assert not mock_signalr_user_hub.is_connected()
        assert daemon.is_connection_lost()

        # Step 2: Attempt to send event while disconnected (should queue)
        trade = {
            "id": 7020,
            "accountId": account_id,
            "profitAndLoss": 50.00,
            "contractId": "CON.F.US.MNQ.U25"
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade)  # Queued
        time.sleep(0.5)

        # Event not processed yet
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == 0.00

        # Step 3: Reconnect User Hub
        mock_signalr_user_hub.reconnect()
        time.sleep(2)  # Allow reconnection and queue processing

        # Step 4: Verify reconnection
        assert mock_signalr_user_hub.is_connected()
        assert not daemon.is_connection_lost()

        # Step 5: Verify queued events processed
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == 50.00

        # Step 6: Verify new events processed normally
        trade_2 = {
            "id": 7021,
            "accountId": account_id,
            "profitAndLoss": 25.00,
            "contractId": "CON.F.US.MNQ.U25"
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade_2)
        time.sleep(0.5)

        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == 75.00

        daemon.stop()

    def test_e2e_023_market_hub_disconnection_quote_recovery(
        self,
        test_daemon,
        mock_signalr_market_hub,
        test_config
    ):
        """
        E2E-023: Market Hub Disconnection - Quote Recovery

        Given: Position open, receiving quote updates
        When: Market Hub disconnects, then reconnects
        Then: Quote stream restored, no missed prices, unrealized P&L accurate

        Duration: ~2 minutes
        """
        account_id = 12345

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Open position
        position = {
            "id": 5021,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,
            "size": 3,
            "averagePrice": 21000.00
        }
        daemon.state_manager.add_position(position)

        assert mock_signalr_market_hub.is_subscribed("F.US.MNQ")

        # Send initial quote
        quote_1 = {
            "symbol": "F.US.MNQ",
            "lastPrice": 21000.00,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_market_hub.send_event("MarketQuote", quote_1)
        time.sleep(0.5)

        assert daemon.quote_tracker.get_last_price("F.US.MNQ") == 21000.00

        # Step 1: Market Hub disconnects
        mock_signalr_market_hub.disconnect()
        time.sleep(0.5)

        assert not mock_signalr_market_hub.is_connected()

        # Step 2: Attempt to send quote while disconnected (lost)
        quote_2 = {
            "symbol": "F.US.MNQ",
            "lastPrice": 21050.00,  # This quote will be missed
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_market_hub.send_event("MarketQuote", quote_2)  # Not received
        time.sleep(0.5)

        # Quote not updated (still old price)
        assert daemon.quote_tracker.get_last_price("F.US.MNQ") == 21000.00

        # Step 3: Reconnect Market Hub
        mock_signalr_market_hub.reconnect()
        time.sleep(2)

        # Step 4: Verify resubscription
        assert mock_signalr_market_hub.is_subscribed("F.US.MNQ")
        assert mock_signalr_market_hub.is_connected()

        # Step 5: Send quote after reconnection
        quote_3 = {
            "symbol": "F.US.MNQ",
            "lastPrice": 21100.00,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_market_hub.send_event("MarketQuote", quote_3)
        time.sleep(0.5)

        # Quote updated
        assert daemon.quote_tracker.get_last_price("F.US.MNQ") == 21100.00

        # Unrealized P&L calculated correctly
        unrealized = daemon.pnl_tracker.get_unrealized_pnl(account_id)
        assert unrealized > 0  # Profitable

        daemon.stop()

    def test_e2e_024_daemon_crash_recovery_state_preservation(
        self,
        test_daemon,
        test_database,
        mock_signalr_user_hub,
        test_config
    ):
        """
        E2E-024: Daemon Crash Recovery - State Preservation

        Given: Daemon running with active positions, P&L, lockouts
        When: Daemon crashes unexpectedly
        Then: State saved to SQLite, daemon restarts, all state recovered

        Duration: ~3 minutes
        """
        account_id = 12345

        # Step 1: Start daemon and establish complex state
        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Multiple positions
        position_1 = {
            "id": 5022,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,
            "size": 2,
            "averagePrice": 21000.00
        }
        position_2 = {
            "id": 5023,
            "accountId": account_id,
            "contractId": "CON.F.US.ES.U25",
            "type": 1,
            "size": 1,
            "averagePrice": 5800.00
        }
        mock_signalr_user_hub.send_event("GatewayUserPosition", position_1)
        mock_signalr_user_hub.send_event("GatewayUserPosition", position_2)

        # Trades (P&L)
        trade_1 = {
            "id": 7022,
            "accountId": account_id,
            "profitAndLoss": -150.00,
            "contractId": "CON.F.US.MNQ.U25"
        }
        trade_2 = {
            "id": 7023,
            "accountId": account_id,
            "profitAndLoss": -100.00,
            "contractId": "CON.F.US.ES.U25"
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade_1)
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade_2)

        # Active order
        order = {
            "id": 1020,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 3,
            "side": 2,
            "size": 2,
            "stopPrice": 20990.00,
            "state": 1
        }
        mock_signalr_user_hub.send_event("GatewayUserOrder", order)

        time.sleep(1)

        # Verify state before crash
        assert daemon.state_manager.get_position_count(account_id) == 3
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == -250.00
        assert daemon.state_manager.get_order(1020) is not None

        # Step 2: Simulate crash
        daemon.crash_simulate()  # Emergency shutdown, saves state
        time.sleep(2)

        # Verify state persisted to database
        db_pnl = test_database.get_daily_pnl(account_id)
        assert db_pnl == -250.00

        db_positions = test_database.get_active_positions(account_id)
        assert len(db_positions) == 2  # 2 positions

        db_trades = test_database.get_trade_history(account_id)
        assert len(db_trades) == 2

        # Step 3: Restart daemon
        daemon = test_daemon.start(config=test_config)
        time.sleep(3)  # Allow full startup and state recovery

        # Step 4: Verify state recovery
        recovered_pnl = daemon.pnl_tracker.get_daily_realized_pnl(account_id)
        assert recovered_pnl == -250.00

        recovered_positions = daemon.state_manager.get_position_count(account_id)
        assert recovered_positions == 3

        recovered_order = daemon.state_manager.get_order(1020)
        assert recovered_order is not None
        assert recovered_order["stopPrice"] == 20990.00

        # Step 5: Verify monitoring resumes
        # New events processed normally
        trade_3 = {
            "id": 7024,
            "accountId": account_id,
            "profitAndLoss": 50.00,
            "contractId": "CON.F.US.MNQ.U25"
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade_3)
        time.sleep(0.5)

        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == -200.00

        daemon.stop()

    @pytest.mark.timeout(300)  # 5 minutes
    def test_e2e_025_multiple_crash_recovery_cycles(
        self,
        test_daemon,
        test_database,
        mock_signalr_user_hub,
        test_config
    ):
        """
        E2E-025: Multiple Crash-Recovery Cycles

        Given: Daemon running
        When: Daemon crashes and restarts 3 times
        Then: State preserved across all cycles, no corruption

        Duration: ~5 minutes
        """
        account_id = 12345

        # Initial state
        initial_pnl = -100.00

        # Cycle 1: Start → crash
        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        daemon.pnl_tracker.set_daily_pnl(account_id, initial_pnl)
        daemon.crash_simulate()
        time.sleep(1)

        # Verify persistence
        db_pnl = test_database.get_daily_pnl(account_id)
        assert db_pnl == initial_pnl

        # Cycle 2: Restart → modify → crash
        daemon = test_daemon.start(config=test_config)
        time.sleep(2)

        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == initial_pnl

        # Add more P&L
        trade = {
            "id": 7030,
            "accountId": account_id,
            "profitAndLoss": -50.00,
            "contractId": "CON.F.US.MNQ.U25"
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade)
        time.sleep(0.5)

        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == -150.00

        daemon.crash_simulate()
        time.sleep(1)

        # Cycle 3: Restart → verify cumulative state
        daemon = test_daemon.start(config=test_config)
        time.sleep(2)

        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == -150.00

        # Add more P&L
        trade_2 = {
            "id": 7031,
            "accountId": account_id,
            "profitAndLoss": 100.00,
            "contractId": "CON.F.US.MNQ.U25"
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade_2)
        time.sleep(0.5)

        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == -50.00

        daemon.crash_simulate()
        time.sleep(1)

        # Final cycle: Restart → verify final state
        daemon = test_daemon.start(config=test_config)
        time.sleep(2)

        final_pnl = daemon.pnl_tracker.get_daily_realized_pnl(account_id)
        assert final_pnl == -50.00

        # Verify database integrity
        db_pnl = test_database.get_daily_pnl(account_id)
        assert db_pnl == -50.00

        # No data corruption
        assert daemon.database.check_integrity() == "ok"

        daemon.stop()
