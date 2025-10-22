"""
E2E Tests - Daily Reset Workflows
Test ID Range: E2E-019 to E2E-021

Tests daily reset scheduler functionality, including P&L reset,
lockout clearing, and timezone handling.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch


@pytest.mark.e2e
@pytest.mark.slow
class TestDailyReset:
    """E2E tests for daily reset workflows"""

    def test_e2e_019_daily_reset_at_scheduled_time(
        self,
        test_daemon,
        test_database,
        time_simulator,
        test_config
    ):
        """
        E2E-019: Daily Reset at Scheduled Time

        Given: Daily P&L=-$350, active lockout, trades recorded
        When: Clock hits 5:00 PM (reset time)
        Then: P&L reset to 0, lockouts cleared, trade counter reset

        Duration: ~2 minutes
        """
        account_id = 12345
        test_config["daily_reset_time"] = "17:00"
        test_config["timezone"] = "America/New_York"

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Establish state before reset
        daemon.pnl_tracker.set_daily_pnl(account_id, -350.00)
        daemon.trade_counter.record_trade(account_id)
        daemon.trade_counter.record_trade(account_id)
        daemon.trade_counter.record_trade(account_id)

        daemon.lockout_manager.set_lockout(
            account_id,
            reason="Test lockout",
            until=datetime.now().replace(hour=17, minute=0, second=0)
        )

        # Verify state before reset
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == -350.00
        assert daemon.trade_counter.get_daily_count(account_id) == 3
        assert daemon.lockout_manager.is_locked_out(account_id)

        # Step 1: Advance time to 4:59 PM (before reset)
        time_simulator.set_time("16:59")
        time.sleep(1)

        # State unchanged
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == -350.00

        # Step 2: Advance time to 5:00 PM (reset time)
        time_simulator.set_time("17:00")
        time.sleep(2)  # Allow reset scheduler to execute

        # Step 3: Verify P&L reset
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == 0.00

        # Step 4: Verify lockout cleared
        assert not daemon.lockout_manager.is_locked_out(account_id)

        # Step 5: Verify trade counter reset
        assert daemon.trade_counter.get_daily_count(account_id) == 0

        # Step 6: Verify database persistence
        db_pnl = test_database.get_daily_pnl(account_id)
        assert db_pnl == 0.00

        db_lockouts = test_database.get_active_lockouts(account_id)
        assert len(db_lockouts) == 0

        daemon.stop()

    def test_e2e_020_reset_with_multiple_accounts(
        self,
        test_daemon,
        time_simulator,
        test_config
    ):
        """
        E2E-020: Reset with Multiple Accounts

        Given: 3 accounts with different P&L and lockout states
        When: Daily reset triggers at 5:00 PM
        Then: All accounts reset independently, state correct for each

        Duration: ~2 minutes
        """
        account_1 = 12345
        account_2 = 67890
        account_3 = 11111

        test_config["accounts"] = [
            {"account_id": account_1, "username": "trader1"},
            {"account_id": account_2, "username": "trader2"},
            {"account_id": account_3, "username": "trader3"}
        ]
        test_config["daily_reset_time"] = "17:00"

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        # Establish different states for each account
        # Account 1: Negative P&L, locked out
        daemon.pnl_tracker.set_daily_pnl(account_1, -450.00)
        daemon.lockout_manager.set_lockout(
            account_1,
            reason="Daily loss",
            until=datetime.now().replace(hour=17, minute=0)
        )

        # Account 2: Positive P&L, not locked out
        daemon.pnl_tracker.set_daily_pnl(account_2, 250.00)

        # Account 3: Zero P&L, locked out (cooldown)
        daemon.pnl_tracker.set_daily_pnl(account_3, 0.00)
        daemon.lockout_manager.set_lockout(
            account_3,
            reason="Cooldown",
            until=datetime.now().replace(hour=17, minute=0)
        )

        # Verify pre-reset state
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_1) == -450.00
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_2) == 250.00
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_3) == 0.00
        assert daemon.lockout_manager.is_locked_out(account_1)
        assert not daemon.lockout_manager.is_locked_out(account_2)
        assert daemon.lockout_manager.is_locked_out(account_3)

        # Step 1: Trigger daily reset
        time_simulator.set_time("17:00")
        time.sleep(2)

        # Step 2: Verify all accounts reset
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_1) == 0.00
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_2) == 0.00
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_3) == 0.00

        # Step 3: Verify all lockouts cleared
        assert not daemon.lockout_manager.is_locked_out(account_1)
        assert not daemon.lockout_manager.is_locked_out(account_2)
        assert not daemon.lockout_manager.is_locked_out(account_3)

        daemon.stop()

    def test_e2e_021_timezone_handling_for_reset(
        self,
        test_daemon,
        time_simulator,
        test_config
    ):
        """
        E2E-021: Timezone Handling for Reset

        Given: Reset time 5:00 PM in America/New_York (ET)
        When: Test different timezone scenarios
        Then: Reset triggers at correct local time

        Duration: ~3 minutes
        """
        account_id = 12345

        # Scenario 1: Eastern Time (ET)
        test_config["daily_reset_time"] = "17:00"
        test_config["timezone"] = "America/New_York"

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        daemon.pnl_tracker.set_daily_pnl(account_id, -100.00)

        # Set time to 5:00 PM ET
        time_simulator.set_timezone("America/New_York")
        time_simulator.set_time("17:00")
        time.sleep(2)

        # Verify reset executed
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == 0.00

        daemon.stop()

        # Scenario 2: Central Time (CT) - 1 hour behind ET
        test_config["timezone"] = "America/Chicago"

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        daemon.pnl_tracker.set_daily_pnl(account_id, -100.00)

        # Set time to 5:00 PM CT (which is 6:00 PM ET)
        time_simulator.set_timezone("America/Chicago")
        time_simulator.set_time("17:00")
        time.sleep(2)

        # Verify reset executed at 5:00 PM CT
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == 0.00

        daemon.stop()

        # Scenario 3: Pacific Time (PT) - 3 hours behind ET
        test_config["timezone"] = "America/Los_Angeles"

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        daemon.pnl_tracker.set_daily_pnl(account_id, -100.00)

        # Set time to 5:00 PM PT (which is 8:00 PM ET)
        time_simulator.set_timezone("America/Los_Angeles")
        time_simulator.set_time("17:00")
        time.sleep(2)

        # Verify reset executed at 5:00 PM PT
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == 0.00

        daemon.stop()

        # Scenario 4: UTC
        test_config["timezone"] = "UTC"
        test_config["daily_reset_time"] = "22:00"  # 5:00 PM ET = 22:00 UTC

        daemon = test_daemon.start(config=test_config)
        time.sleep(1)

        daemon.pnl_tracker.set_daily_pnl(account_id, -100.00)

        time_simulator.set_timezone("UTC")
        time_simulator.set_time("22:00")
        time.sleep(2)

        # Verify reset executed at 22:00 UTC
        assert daemon.pnl_tracker.get_daily_realized_pnl(account_id) == 0.00

        daemon.stop()
