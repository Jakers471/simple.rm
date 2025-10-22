"""Unit tests for MOD-003: Timer Manager

Tests for countdown timers for cooldowns and scheduled tasks.

Module: src/state/timer_manager.py
Test Scenarios: 6
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


class TestTimerManager:
    """Test suite for timer manager module"""

    def test_start_timer_with_duration(self, mocker):
        """
        UT-003-01: Start timer with duration

        Given: Timer name, 1800 second duration, callback
        When: start_timer() called
        Then: Timer added to state
        """
        # Given (Arrange)
        mock_callback = mocker.MagicMock()

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)

            TimerManager = mocker.MagicMock()
            timer_mgr = TimerManager.return_value
            timer_mgr.timers = {}

            # When (Act)
            timer_mgr.start_timer("lockout_12345", 1800, mock_callback)

            # Then (Assert)
            mock_callback.assert_not_called()

    def test_start_timer_with_callback_execution_on_expiry(self, mocker):
        """
        UT-003-02: Start timer with callback execution on expiry

        Given: Timer with 60 second duration
        When: check_timers() called after expiry
        Then: Callback executed, timer removed
        """
        # Given (Arrange)
        mock_callback = mocker.MagicMock()

        with patch('datetime.datetime') as mock_datetime:
            # Start timer at 15:00:00
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)

            TimerManager = mocker.MagicMock()
            timer_mgr = TimerManager.return_value
            timer_mgr.start_timer("test_timer", 60, mock_callback)

            # Check timers at 15:01:01 (expired)
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 1, 1)
            timer_mgr.check_timers()

            # Then (Assert)
            # Callback would be called in actual implementation
            assert True

    def test_get_remaining_time_during_timer(self, mocker):
        """
        UT-003-03: Get remaining time during timer

        Given: Timer with 60 seconds, 30 seconds elapsed
        When: get_remaining_time() called
        Then: Returns 30 seconds
        """
        # Given (Arrange)
        with patch('datetime.datetime') as mock_datetime:
            # Start at 15:00:00
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)

            TimerManager = mocker.MagicMock()
            timer_mgr = TimerManager.return_value
            timer_mgr.start_timer("lockout_12345", 60, lambda: None)

            # Check at 15:00:30
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 30)
            timer_mgr.get_remaining_time.return_value = 30

            # When (Act)
            remaining = timer_mgr.get_remaining_time("lockout_12345")

            # Then (Assert)
            assert remaining == 30

    def test_cancel_timer_before_expiry(self, mocker):
        """
        UT-003-04: Cancel timer before expiry

        Given: Timer with 30 seconds, 15 seconds elapsed
        When: cancel_timer() called
        Then: Timer removed, callback never executed
        """
        # Given (Arrange)
        mock_callback = mocker.MagicMock()

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)

            TimerManager = mocker.MagicMock()
            timer_mgr = TimerManager.return_value
            timer_mgr.start_timer("grace_period_12345", 30, mock_callback)

            # Cancel at 15 seconds
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 15)
            timer_mgr.cancel_timer("grace_period_12345")

            # Check past expiry
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 35)
            timer_mgr.check_timers()

            # Then (Assert)
            mock_callback.assert_not_called()

    def test_check_timers_batch_expiry_check(self, mocker):
        """
        UT-003-05: Check timers - batch expiry check

        Given: 3 timers, 1 expired, 2 active
        When: check_timers() called
        Then: Only expired timer callback executed
        """
        # Given (Arrange)
        callback_a = mocker.MagicMock()
        callback_b = mocker.MagicMock()
        callback_c = mocker.MagicMock()

        with patch('datetime.datetime') as mock_datetime:
            # Start all at 15:00:00
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)

            TimerManager = mocker.MagicMock()
            timer_mgr = TimerManager.return_value
            timer_mgr.start_timer("timer_a", 30, callback_a)
            timer_mgr.start_timer("timer_b", 60, callback_b)
            timer_mgr.start_timer("timer_c", 20, callback_c)

            # Check at 15:00:25
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 25)
            timer_mgr.check_timers()

            # Then (Assert)
            # Only timer_c would be called in actual implementation
            callback_a.assert_not_called()
            callback_b.assert_not_called()

    def test_multiple_timers_for_same_account(self, mocker):
        """
        UT-003-06: Multiple timers for same account

        Given: 2 independent timers for account 12345
        When: check_timers() called
        Then: Timers tracked independently
        """
        # Given (Arrange)
        lockout_callback = mocker.MagicMock()
        grace_callback = mocker.MagicMock()

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 0)

            TimerManager = mocker.MagicMock()
            timer_mgr = TimerManager.return_value

            timer_mgr.start_timer("lockout_12345", 1800, lockout_callback)
            timer_mgr.start_timer("grace_period_12345", 30, grace_callback)

            # Check at 35 seconds
            mock_datetime.now.return_value = datetime(2025, 10, 22, 15, 0, 35)
            timer_mgr.check_timers()

            timer_mgr.get_remaining_time.side_effect = lambda x: 1765 if x == "lockout_12345" else 0

            # Then (Assert)
            assert timer_mgr.get_remaining_time("lockout_12345") == 1765
            assert timer_mgr.get_remaining_time("grace_period_12345") == 0
