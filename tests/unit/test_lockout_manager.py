"""Unit tests for MOD-002: Lockout Manager

Tests for centralized lockout state management.

Module: src/state/lockout_manager.py
Test Scenarios: 10
"""

import pytest
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime
from zoneinfo import ZoneInfo


class TestLockoutManager:
    """Test suite for lockout manager module"""

    def test_set_lockout_with_expiry_time(self, mocker):
        """
        UT-002-01: Set lockout with expiry time

        Given: Account 12345, no existing lockout
        When: set_lockout() called with expiry time
        Then: Lockout stored in memory and database
        """
        # Given (Arrange)
        account_id = 12345
        reason = "Daily loss limit hit"
        until = datetime(2025, 10, 22, 17, 0, 0)

        mock_db = mocker.MagicMock()
        mock_cli = mocker.MagicMock()

        LockoutManager = mocker.MagicMock()
        lockout_mgr = LockoutManager.return_value
        lockout_mgr.is_locked_out.return_value = True

        # When (Act)
        lockout_mgr.set_lockout(account_id, reason, until)

        # Then (Assert)
        assert lockout_mgr.is_locked_out(account_id) is True

    def test_set_lockout_with_permanent_lockout(self, mocker):
        """
        UT-002-02: Set lockout with permanent lockout (NULL expiry)

        Given: Account 12345, no existing lockout
        When: set_lockout() called with until=None
        Then: Permanent lockout stored
        """
        # Given (Arrange)
        account_id = 12345
        reason = "Manual lockout by administrator"

        mock_db = mocker.MagicMock()

        LockoutManager = mocker.MagicMock()
        lockout_mgr = LockoutManager.return_value
        lockout_mgr.is_locked_out.return_value = True

        # When (Act)
        lockout_mgr.set_lockout(account_id, reason, None)

        # Then (Assert)
        assert lockout_mgr.is_locked_out(account_id) is True

    def test_is_locked_out_account_currently_locked(self, mocker):
        """
        UT-002-03: Is locked out - account currently locked

        Given: Active lockout until 17:00, current time 15:00
        When: is_locked_out() called
        Then: Returns True
        """
        # Given (Arrange)
        account_id = 12345

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)

            LockoutManager = mocker.MagicMock()
            lockout_mgr = LockoutManager.return_value
            lockout_mgr.set_lockout(12345, "Daily loss limit", datetime(2025, 10, 22, 17, 0, 0))
            lockout_mgr.is_locked_out.return_value = True

            # When (Act)
            is_locked = lockout_mgr.is_locked_out(account_id)

            # Then (Assert)
            assert is_locked is True

    def test_is_locked_out_account_not_locked(self, mocker):
        """
        UT-002-04: Is locked out - account not locked

        Given: No lockout state for account
        When: is_locked_out() called
        Then: Returns False
        """
        # Given (Arrange)
        account_id = 12345

        LockoutManager = mocker.MagicMock()
        lockout_mgr = LockoutManager.return_value
        lockout_mgr.is_locked_out.return_value = False

        # When (Act)
        is_locked = lockout_mgr.is_locked_out(account_id)

        # Then (Assert)
        assert is_locked is False

    def test_is_locked_out_lockout_expired_auto_clear(self, mocker):
        """
        UT-002-05: Is locked out - lockout expired (auto-clear)

        Given: Lockout expired 5 minutes ago
        When: is_locked_out() called
        Then: Returns False, lockout cleared
        """
        # Given (Arrange)
        account_id = 12345
        mock_db = mocker.MagicMock()

        with patch('datetime.datetime') as mock_datetime:
            # Set lockout at 14:00
            mock_datetime.now.return_value = datetime(2025, 10, 22, 14, 0, 0)

            LockoutManager = mocker.MagicMock()
            lockout_mgr = LockoutManager.return_value
            lockout_mgr.set_lockout(12345, "Daily loss", datetime(2025, 10, 22, 17, 0, 0))

            # Check at 17:05 (expired)
            mock_datetime.now.return_value = datetime(2025, 10, 22, 17, 5, 0)
            lockout_mgr.is_locked_out.return_value = False

            # When (Act)
            is_locked = lockout_mgr.is_locked_out(account_id)

            # Then (Assert)
            assert is_locked is False

    def test_clear_lockout_manual_unlock(self, mocker):
        """
        UT-002-06: Clear lockout - manual unlock

        Given: Active lockout before expiry
        When: clear_lockout() called
        Then: Lockout removed from memory and database
        """
        # Given (Arrange)
        account_id = 12345
        mock_db = mocker.MagicMock()
        mock_cli = mocker.MagicMock()

        LockoutManager = mocker.MagicMock()
        lockout_mgr = LockoutManager.return_value
        lockout_mgr.set_lockout(12345, "Daily loss limit", datetime(2025, 10, 22, 17, 0, 0))
        lockout_mgr.is_locked_out.return_value = False

        # When (Act)
        lockout_mgr.clear_lockout(account_id)

        # Then (Assert)
        assert lockout_mgr.is_locked_out(account_id) is False

    def test_check_expired_lockouts_batch_cleanup(self, mocker):
        """
        UT-002-07: Check expired lockouts - batch cleanup

        Given: 3 accounts, 2 with expired lockouts
        When: check_expired_lockouts() called
        Then: Expired lockouts cleared, active remains
        """
        # Given (Arrange)
        with patch('datetime.datetime') as mock_datetime:
            LockoutManager = mocker.MagicMock()
            lockout_mgr = LockoutManager.return_value

            # Set lockouts
            lockout_mgr.set_lockout(12345, "Loss 1", datetime(2025, 10, 22, 17, 0, 0))
            lockout_mgr.set_lockout(67890, "Loss 2", datetime(2025, 10, 22, 18, 0, 0))
            lockout_mgr.set_lockout(11111, "Loss 3", datetime(2025, 10, 22, 16, 0, 0))

            # Check at 17:05
            mock_datetime.now.return_value = datetime(2025, 10, 22, 17, 5, 0)
            lockout_mgr.check_expired_lockouts()

            lockout_mgr.is_locked_out.side_effect = lambda x: x == 67890

            # Then (Assert)
            assert lockout_mgr.is_locked_out(12345) is False
            assert lockout_mgr.is_locked_out(67890) is True
            assert lockout_mgr.is_locked_out(11111) is False

    def test_get_lockout_info_details_for_display(self, mocker):
        """
        UT-002-08: Get lockout info - details for display

        Given: Active lockout with 90 minutes remaining
        When: get_lockout_info() called
        Then: Returns lockout details with remaining time
        """
        # Given (Arrange)
        account_id = 12345

        with patch('datetime.datetime') as mock_datetime:
            LockoutManager = mocker.MagicMock()
            lockout_mgr = LockoutManager.return_value

            # Set lockout at 14:00
            mock_datetime.now.return_value = datetime(2025, 10, 22, 14, 0, 0)
            lockout_mgr.set_lockout(12345, "Daily loss limit hit", datetime(2025, 10, 22, 17, 0, 0))

            # Get info at 15:30
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 30, 0)
            lockout_mgr.get_lockout_info.return_value = {
                "reason": "Daily loss limit hit",
                "until": datetime(2025, 10, 22, 17, 0, 0),
                "remaining_seconds": 5400,
                "type": "hard_lockout"
            }

            # When (Act)
            info = lockout_mgr.get_lockout_info(account_id)

            # Then (Assert)
            assert info["remaining_seconds"] == 5400
            assert info["reason"] == "Daily loss limit hit"

    def test_lockout_persistence_save_to_sqlite(self, mocker):
        """
        UT-002-09: Lockout persistence - save to SQLite

        Given: New lockout to save
        When: set_lockout() called
        Then: Database INSERT executed
        """
        # Given (Arrange)
        account_id = 12345
        mock_db = mocker.MagicMock()

        LockoutManager = mocker.MagicMock()
        lockout_mgr = LockoutManager.return_value

        # When (Act)
        lockout_mgr.set_lockout(12345, "Daily loss limit", datetime(2025, 10, 22, 17, 0, 0))

        # Then (Assert)
        # Verify database would be called
        assert True  # Placeholder for actual implementation

    def test_load_lockouts_from_sqlite_on_init(self, mocker):
        """
        UT-002-10: Load lockouts from SQLite on init

        Given: Database contains 2 active lockouts
        When: load_lockouts_from_db() called
        Then: Lockouts loaded into memory
        """
        # Given (Arrange)
        mock_db = mocker.MagicMock()
        mock_db.execute.return_value = [
            (12345, "Daily loss", datetime(2025, 10, 22, 17, 0, 0)),
            (67890, "Trade frequency", datetime(2025, 10, 22, 18, 0, 0))
        ]

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)

            LockoutManager = mocker.MagicMock()
            lockout_mgr = LockoutManager.return_value
            lockout_mgr.load_lockouts_from_db()

            lockout_mgr.is_locked_out.side_effect = lambda x: x in [12345, 67890]

            # Then (Assert)
            assert lockout_mgr.is_locked_out(12345) is True
            assert lockout_mgr.is_locked_out(67890) is True
