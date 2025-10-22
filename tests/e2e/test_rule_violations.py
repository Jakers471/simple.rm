"""
E2E Tests - Rule Violation Workflows
Test ID Range: E2E-006 to E2E-013

Tests all major rule breach scenarios with enforcement actions,
including max contracts, loss limits, stop-loss violations, and symbol blocks.
"""

import pytest
import time
from datetime import datetime, timedelta


@pytest.mark.e2e
@pytest.mark.slow
class TestRuleViolations:
    """E2E tests for rule violation workflows"""

    def test_e2e_006_rule_001_max_contracts_exceeded(
        self,
        test_daemon,
        mock_signalr_user_hub,
        mock_api,
        test_config
    ):
        """
        E2E-006: RULE-001 Violation - Max Contracts Exceeded

        Given: max_contracts limit=5, current positions: Long 4 MNQ
        When: Trader opens additional Long 2 ES (total=6)
        Then: All positions closed via REST API, NO lockout

        Duration: ~1 minute
        """
        account_id = 12345
        test_config["max_contracts"] = {
            "enabled": True,
            "limit": 5,
            "count_type": "net",
            "close_all": True,
            "lockout_on_breach": False
        }

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Step 1: Open 4 MNQ contracts
        position_1 = {
            "id": 5001,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,  # Long
            "size": 4,
            "averagePrice": 21000.00
        }
        mock_signalr_user_hub.send_event("GatewayUserPosition", position_1)
        time.sleep(0.5)

        assert daemon.state_manager.get_position_count(account_id) == 4

        # Step 2: Open 2 ES contracts (breach: 4+2=6 > 5)
        position_2 = {
            "id": 5003,
            "accountId": account_id,
            "contractId": "CON.F.US.ES.U25",
            "type": 1,  # Long
            "size": 2,
            "averagePrice": 5800.00
        }
        mock_signalr_user_hub.send_event("GatewayUserPosition", position_2)
        time.sleep(0.5)

        # Step 3: Verify breach detection
        # Position count should momentarily be 6 before enforcement
        assert daemon.enforcement_executed()

        # Step 4: Verify enforcement action
        # All positions should be closed via REST API
        assert mock_api.was_called("POST", "/api/Position/closeContract")
        assert mock_api.call_count("POST", "/api/Position/closeContract") == 2  # Both positions

        # Positions removed from state
        assert daemon.state_manager.get_position_count(account_id) == 0

        # Step 5: Verify NO lockout
        assert not daemon.lockout_manager.is_locked_out(account_id)

        # Verify enforcement log
        logs = daemon.get_enforcement_logs(account_id)
        assert len(logs) == 1
        assert logs[0]["rule_id"] == "RULE-001"
        assert logs[0]["action"] == "CLOSE_ALL_POSITIONS"
        assert "6 > 5" in logs[0]["reason"]

        daemon.stop()

    def test_e2e_007_rule_003_daily_realized_loss_limit(
        self,
        test_daemon,
        mock_signalr_user_hub,
        mock_api,
        test_config
    ):
        """
        E2E-007: RULE-003 Violation - Daily Realized Loss Limit

        Given: Daily P&L=-$450, limit=-$500, open positions
        When: Trade executes with P&L=-$75.50 (total=-$525.50)
        Then: All positions closed, lockout until 5:00 PM

        Duration: ~2 minutes
        """
        account_id = 12345
        test_config["daily_realized_loss"] = {
            "enabled": True,
            "limit": -500,
            "reset_time": "17:00",
            "timezone": "America/New_York",
            "enforcement": "close_all_and_lockout"
        }

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Set current time to 2:00 PM (5 hours before reset)
        current_time = datetime.now().replace(hour=14, minute=0, second=0)

        # Establish previous P&L state
        daemon.pnl_tracker.set_daily_pnl(account_id, -450.00)

        # Open position
        position = {
            "id": 5002,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,
            "size": 2,
            "averagePrice": 21000.00
        }
        mock_signalr_user_hub.send_event("GatewayUserPosition", position)
        time.sleep(0.5)

        # Step 1: Large losing trade (breach)
        trade = {
            "id": 7002,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "profitAndLoss": -75.50,
            "price": 20950.00
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade)
        time.sleep(0.5)

        # Step 2: Verify P&L breach
        daily_pnl = daemon.pnl_tracker.get_daily_realized_pnl(account_id)
        assert daily_pnl == -525.50

        # Step 3: Verify enforcement (close all + cancel all)
        assert mock_api.was_called("POST", "/api/Position/closeContract")
        assert mock_api.was_called("POST", "/api/Order/cancel")

        # Step 4: Verify lockout set
        assert daemon.lockout_manager.is_locked_out(account_id)

        lockout = daemon.lockout_manager.get_lockout(account_id)
        assert lockout is not None
        assert lockout["until"].hour == 17  # 5:00 PM
        assert lockout["until"].minute == 0

        # Duration should be ~3 hours
        duration = (lockout["until"] - current_time).total_seconds()
        assert 10700 < duration < 10900  # ~3 hours

        # Step 5: Attempt to place order (should be blocked)
        order_event = {
            "id": 1005,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 2,
            "side": 1,
            "size": 1,
            "limitPrice": 21000.00,
            "state": 1
        }
        mock_signalr_user_hub.send_event("GatewayUserOrder", order_event)
        time.sleep(0.5)

        # Order should NOT be tracked (event skipped)
        assert daemon.state_manager.get_order(1005) is None

        daemon.stop()

    def test_e2e_008_rule_004_unrealized_loss_per_position(
        self,
        test_daemon,
        mock_signalr_market_hub,
        mock_api,
        test_config
    ):
        """
        E2E-008: RULE-004 Violation - Daily Unrealized Loss (Per Position)

        Given: Position Long 2 MNQ @ 21000.00, loss_limit=300, scope=per_position
        When: Price drops to 20700.00 (unrealized=-$1200)
        Then: Only losing position closed, NO lockout

        Duration: ~2 minutes
        """
        account_id = 12345
        test_config["daily_unrealized_loss"] = {
            "enabled": True,
            "loss_limit": 300.00,
            "scope": "per_position",
            "action": "CLOSE_POSITION",
            "lockout": False
        }

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Open position
        position = {
            "id": 5004,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,
            "size": 2,
            "averagePrice": 21000.00
        }
        daemon.state_manager.add_position(position)

        # Initial quote (at entry)
        quote_1 = {
            "symbol": "F.US.MNQ",
            "lastPrice": 21000.00,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_market_hub.send_event("MarketQuote", quote_1)
        time.sleep(0.5)

        # Step 1: Price drops significantly
        quote_2 = {
            "symbol": "F.US.MNQ",
            "lastPrice": 20700.00,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_market_hub.send_event("MarketQuote", quote_2)
        time.sleep(0.5)

        # Step 2: Verify unrealized P&L calculation
        # -300 points = -1200 ticks (0.25 tick size)
        # -1200 ticks * $0.50 per tick * 2 contracts = -$1200
        unrealized = daemon.pnl_tracker.get_position_unrealized_pnl(account_id, 5004)
        assert unrealized == pytest.approx(-1200.00, abs=1.0)

        # Step 3: Verify breach detection
        # -1200 > 300 limit → BREACH
        assert daemon.enforcement_executed()

        # Step 4: Verify enforcement (close specific position only)
        assert mock_api.was_called("POST", "/api/Position/closeContract")
        call_args = mock_api.get_last_call("POST", "/api/Position/closeContract")
        assert call_args["contractId"] == "CON.F.US.MNQ.U25"

        # Position removed
        assert daemon.state_manager.get_position(5004) is None

        # Step 5: Verify NO lockout
        assert not daemon.lockout_manager.is_locked_out(account_id)

        # Can open new position immediately
        new_position = {
            "id": 5005,
            "accountId": account_id,
            "contractId": "CON.F.US.ES.U25",
            "type": 1,
            "size": 1,
            "averagePrice": 5800.00
        }
        daemon.state_manager.add_position(new_position)
        assert daemon.state_manager.get_position_count(account_id) == 1

        daemon.stop()

    def test_e2e_009_rule_008_no_stop_loss_grace_expired(
        self,
        test_daemon,
        mock_signalr_user_hub,
        mock_api,
        test_config
    ):
        """
        E2E-009: RULE-008 Violation - No Stop-Loss Grace Period Expired

        Given: Position opens without SL, grace_period=30s
        When: 30 seconds elapse without SL placement
        Then: All positions closed, 1-hour lockout

        Duration: ~45 seconds
        """
        account_id = 12345
        test_config["no_stop_loss_grace"] = {
            "enabled": True,
            "grace_period_seconds": 30,
            "action": "close_all_and_lockout",
            "lockout_duration": 3600  # 1 hour
        }

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Step 1: Open position without stop-loss
        position = {
            "id": 5005,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,
            "size": 2,
            "averagePrice": 21000.00,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_user_hub.send_event("GatewayUserPosition", position)
        time.sleep(0.5)

        # Step 2: Verify grace timer started
        timer_key = f"no_sl_grace_{account_id}_5005"
        assert daemon.timer_manager.has_active_timer(timer_key)

        remaining = daemon.timer_manager.get_remaining_time(timer_key)
        assert 28 < remaining <= 30

        # Step 3: Wait for grace period to expire
        time.sleep(31)

        # Step 4: Verify grace expired, enforcement executed
        assert not daemon.timer_manager.has_active_timer(timer_key)
        assert daemon.enforcement_executed()

        # Positions closed
        assert mock_api.was_called("POST", "/api/Position/closeContract")
        assert daemon.state_manager.get_position_count(account_id) == 0

        # Step 5: Verify lockout (1 hour)
        assert daemon.lockout_manager.is_locked_out(account_id)

        lockout = daemon.lockout_manager.get_lockout(account_id)
        assert lockout is not None

        duration = (lockout["until"] - datetime.now()).total_seconds()
        assert 3550 < duration < 3610  # ~1 hour (3600s)

        daemon.stop()

    def test_e2e_010_rule_011_blocked_symbol_position(
        self,
        test_daemon,
        mock_signalr_user_hub,
        mock_api,
        test_config
    ):
        """
        E2E-010: RULE-011 Violation - Blocked Symbol Position

        Given: Blocked symbols: [BTC, ETH, GC]
        When: Position opens in BTC
        Then: All positions closed, 24-hour lockout

        Duration: ~1 minute
        """
        account_id = 12345
        test_config["symbol_blocks"] = {
            "enabled": True,
            "blocked_symbols": ["BTC", "ETH", "GC"],
            "action": "close_all_and_lockout",
            "lockout_duration": 86400  # 24 hours
        }

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Step 1: Open position in blocked symbol (Bitcoin)
        position = {
            "id": 5006,
            "accountId": account_id,
            "contractId": "CON.F.US.BTC.U25",
            "type": 1,
            "size": 1,
            "averagePrice": 95000.00
        }
        mock_signalr_user_hub.send_event("GatewayUserPosition", position)
        time.sleep(0.5)

        # Step 2: Verify breach detection
        # Extract "BTC" from contract ID → match blocked list
        assert daemon.enforcement_executed()

        # Step 3: Verify enforcement (close all)
        assert mock_api.was_called("POST", "/api/Position/closeContract")
        assert daemon.state_manager.get_position_count(account_id) == 0

        # Step 4: Verify 24-hour lockout
        assert daemon.lockout_manager.is_locked_out(account_id)

        lockout = daemon.lockout_manager.get_lockout(account_id)
        duration = (lockout["until"] - datetime.now()).total_seconds()
        assert 86300 < duration < 86500  # ~24 hours

        assert "BTC" in lockout["reason"]

        daemon.stop()

    def test_e2e_011_rule_006_trade_frequency_breach(
        self,
        test_daemon,
        mock_signalr_user_hub,
        test_config
    ):
        """
        E2E-011: RULE-006 Violation - Trade Frequency Limit (Per Minute)

        Given: Trade frequency limit: 3 per minute
        When: 4 trades executed within 60 seconds
        Then: 60-second cooldown triggered, expires after 60s

        Duration: ~2 minutes
        """
        account_id = 12345
        test_config["trade_frequency_limit"] = {
            "enabled": True,
            "limits": {
                "per_minute": 3,
                "per_hour": 10,
                "per_session": 50
            },
            "cooldown_on_breach": {
                "enabled": True,
                "per_minute_breach": 60  # 60 second cooldown
            }
        }

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Step 1: Execute 3 trades (within limit)
        for i in range(3):
            trade = {
                "id": 7001 + i,
                "accountId": account_id,
                "contractId": "CON.F.US.MNQ.U25",
                "profitAndLoss": 25.00,
                "price": 21000.00
            }
            mock_signalr_user_hub.send_event("GatewayUserTrade", trade)
            time.sleep(0.2)

        # Verify no breach yet
        assert not daemon.lockout_manager.is_locked_out(account_id)
        trade_count = daemon.trade_counter.get_trades_in_window(account_id, 60)
        assert trade_count == 3

        # Step 2: Execute 4th trade (BREACH)
        trade_4 = {
            "id": 7004,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "profitAndLoss": 25.00,
            "price": 21000.00
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade_4)
        time.sleep(0.5)

        # Step 3: Verify cooldown set
        assert daemon.lockout_manager.is_locked_out(account_id)

        lockout = daemon.lockout_manager.get_lockout(account_id)
        assert "frequency" in lockout["reason"].lower()

        duration = (lockout["until"] - datetime.now()).total_seconds()
        assert 55 < duration <= 60

        # Step 4: Wait for cooldown to expire
        time.sleep(61)

        # Step 5: Verify cooldown expired
        assert not daemon.lockout_manager.is_locked_out(account_id)

        # Can trade again
        trade_5 = {
            "id": 7005,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "profitAndLoss": 25.00,
            "price": 21000.00
        }
        mock_signalr_user_hub.send_event("GatewayUserTrade", trade_5)
        time.sleep(0.5)

        # Only 1 trade in last 60 seconds (old trades expired)
        trade_count = daemon.trade_counter.get_trades_in_window(account_id, 60)
        assert trade_count == 1

        daemon.stop()

    def test_e2e_012_rule_009_session_block_outside_hours(
        self,
        test_daemon,
        mock_signalr_user_hub,
        mock_api,
        test_config,
        time_simulator
    ):
        """
        E2E-012: RULE-009 Violation - Session Block Outside Hours

        Given: Session hours: 9:30 AM - 4:00 PM, open position
        When: Clock hits 4:00 PM (session end)
        Then: All positions closed, lockout until 9:30 AM next day

        Duration: ~1 minute
        """
        account_id = 12345
        test_config["session_block_outside"] = {
            "enabled": True,
            "global_session": {
                "enabled": True,
                "start": "09:30",
                "end": "16:00",
                "timezone": "America/New_York"
            },
            "close_positions_at_session_end": True,
            "lockout_outside_session": True
        }

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Set time to 3:59 PM (just before session end)
        time_simulator.set_time("15:59")

        # Open position
        position = {
            "id": 5007,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 1,
            "size": 2,
            "averagePrice": 21000.00
        }
        mock_signalr_user_hub.send_event("GatewayUserPosition", position)
        time.sleep(0.5)

        assert daemon.state_manager.get_position_count(account_id) == 2

        # Step 1: Clock hits 4:00 PM
        time_simulator.set_time("16:00")
        time.sleep(1)  # Allow reset scheduler to trigger

        # Step 2: Verify auto-close enforcement
        assert mock_api.was_called("POST", "/api/Position/closeContract")
        assert daemon.state_manager.get_position_count(account_id) == 0

        # Step 3: Verify lockout until next session
        assert daemon.lockout_manager.is_locked_out(account_id)

        lockout = daemon.lockout_manager.get_lockout(account_id)
        assert lockout["until"].hour == 9
        assert lockout["until"].minute == 30
        assert lockout["until"].date() > datetime.now().date()  # Tomorrow

        # Step 4: Try to place order (blocked)
        order = {
            "id": 1010,
            "accountId": account_id,
            "contractId": "CON.F.US.MNQ.U25",
            "type": 2,
            "side": 1,
            "size": 1,
            "limitPrice": 21000.00,
            "state": 1
        }
        mock_signalr_user_hub.send_event("GatewayUserOrder", order)
        time.sleep(0.5)

        # Event skipped
        assert daemon.state_manager.get_order(1010) is None

        daemon.stop()

    def test_e2e_013_rule_005_max_unrealized_profit(
        self,
        test_daemon,
        mock_signalr_market_hub,
        mock_api,
        test_config
    ):
        """
        E2E-013: RULE-005 Violation - Max Unrealized Profit

        Given: Position Long 10 ES @ 5800.00, profit_limit=2000
        When: Price rises to 5804.25 (unrealized=+$2012.50)
        Then: Position closed (lock in profit), 1-hour lockout

        Duration: ~1 minute
        """
        account_id = 12345
        test_config["max_unrealized_profit"] = {
            "enabled": True,
            "profit_limit": 2000.00,
            "action": "close_all_and_lockout",
            "lockout_duration": 3600
        }

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Open position
        position = {
            "id": 5008,
            "accountId": account_id,
            "contractId": "CON.F.US.ES.U25",
            "type": 1,
            "size": 10,
            "averagePrice": 5800.00
        }
        daemon.state_manager.add_position(position)

        # Step 1: Price at limit (no breach)
        quote_1 = {
            "symbol": "F.US.ES",
            "lastPrice": 5804.00,  # +4 points = +$2000
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_market_hub.send_event("MarketQuote", quote_1)
        time.sleep(0.5)

        unrealized = daemon.pnl_tracker.get_position_unrealized_pnl(account_id, 5008)
        assert unrealized == pytest.approx(2000.00, abs=1.0)

        # No breach yet (at limit is OK)
        assert not daemon.enforcement_executed()

        # Step 2: Price exceeds limit (breach)
        quote_2 = {
            "symbol": "F.US.ES",
            "lastPrice": 5804.25,  # +4.25 points = +$2012.50
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        mock_signalr_market_hub.send_event("MarketQuote", quote_2)
        time.sleep(0.5)

        unrealized = daemon.pnl_tracker.get_position_unrealized_pnl(account_id, 5008)
        assert unrealized > 2000.00

        # Step 3: Verify enforcement
        assert daemon.enforcement_executed()
        assert mock_api.was_called("POST", "/api/Position/closeContract")
        assert daemon.state_manager.get_position_count(account_id) == 0

        # Step 4: Verify lockout (1 hour)
        assert daemon.lockout_manager.is_locked_out(account_id)

        lockout = daemon.lockout_manager.get_lockout(account_id)
        duration = (lockout["until"] - datetime.now()).total_seconds()
        assert 3550 < duration < 3610

        daemon.stop()
