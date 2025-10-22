"""
Unit tests for RULE-009: Session Block Outside Hours

Tests the rule that prevents trading outside configured session hours
(e.g., no trading before 9:30 AM ET).
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import pytz


@pytest.fixture
def mock_lockout_manager():
    """Mock lockout manager."""
    return Mock()


class TestSessionBlockOutsideHours:
    """Test suite for RULE-009: Session Block Outside Hours."""

    def test_check_position_during_valid_session(self, mock_lockout_manager):
        """
        GIVEN: Position at 10:00 AM ET (session 9:30-4:00 PM)
        WHEN: Position is checked
        THEN: No breach, trading allowed
        """
        # Given
        position_event = {
            "accountId": 123,
            "contractId": "CON.F.US.ES.U25",
            "creationTimestamp": "2024-07-21T14:00:00Z"  # 10 AM ET
        }

        config = {
            'session_hours': {
                'start': '09:30',
                'end': '16:00',
                'timezone': 'America/New_York'
            }
        }

        mock_tz = pytz.timezone('America/New_York')
        mock_now = datetime(2024, 7, 21, 10, 0, 0, tzinfo=mock_tz)

        # When
        from src.rules.session_block_outside_hours import SessionBlockOutsideHoursRule
        rule = SessionBlockOutsideHoursRule(config, mock_lockout_manager)

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            result = rule.check(position_event)

        # Then
        assert result is None
        assert mock_lockout_manager.is_locked_out(123) == False

    def test_check_position_before_session_start(self, mock_lockout_manager):
        """
        GIVEN: Position at 8:00 AM ET (before 9:30 AM start)
        WHEN: Position is checked
        THEN: Breach detected, close all and lockout
        """
        # Given
        position_event = {
            "accountId": 123,
            "contractId": "CON.F.US.ES.U25",
            "creationTimestamp": "2024-07-21T12:00:00Z"  # 8 AM ET
        }

        config = {
            'session_hours': {
                'start': '09:30',
                'end': '16:00',
                'timezone': 'America/New_York'
            },
            'action': 'CLOSE_ALL_AND_LOCKOUT'
        }

        mock_tz = pytz.timezone('America/New_York')
        mock_now = datetime(2024, 7, 21, 8, 0, 0, tzinfo=mock_tz)

        # When
        from src.rules.session_block_outside_hours import SessionBlockOutsideHoursRule
        rule = SessionBlockOutsideHoursRule(config, mock_lockout_manager)

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            result = rule.check(position_event)

        # Then
        assert result is not None
        assert result['breach'] == True
        assert result['reason'] == 'Trading outside session hours'
        assert result['current_time'] == '08:00:00'

        action = result['action']
        assert action['type'] == 'CLOSE_ALL_AND_LOCKOUT'

    def test_check_position_after_session_end(self, mock_lockout_manager):
        """
        GIVEN: Position at 5:00 PM ET (after 4:00 PM end)
        WHEN: Position is checked
        THEN: Breach detected
        """
        # Given
        position_event = {
            "accountId": 123,
            "contractId": "CON.F.US.MNQ.U25",
            "creationTimestamp": "2024-07-21T15:00:00Z"
        }

        config = {
            'session_hours': {
                'start': '09:30',
                'end': '16:00',
                'timezone': 'America/New_York'
            },
            'action': 'CLOSE_ALL_AND_LOCKOUT'
        }

        mock_tz = pytz.timezone('America/New_York')
        mock_now = datetime(2024, 7, 21, 17, 0, 0, tzinfo=mock_tz)

        # When
        from src.rules.session_block_outside_hours import SessionBlockOutsideHoursRule
        rule = SessionBlockOutsideHoursRule(config, mock_lockout_manager)

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            result = rule.check(position_event)

        # Then
        assert result is not None
        assert result['current_time'] == '17:00:00'
        assert result['session_end'] == '16:00:00'

    def test_check_holiday_detection(self, mock_lockout_manager):
        """
        GIVEN: Position on July 4th (market holiday)
        WHEN: Position is checked
        THEN: Breach detected for holiday trading
        """
        # Given
        position_event = {
            "accountId": 123,
            "contractId": "CON.F.US.ES.U25",
            "creationTimestamp": "2024-07-04T14:00:00Z"
        }

        config = {
            'session_hours': {
                'start': '09:30',
                'end': '16:00',
                'timezone': 'America/New_York'
            },
            'check_holidays': True,
            'holidays': [
                '2024-07-04',
                '2024-12-25'
            ]
        }

        mock_tz = pytz.timezone('America/New_York')
        mock_now = datetime(2024, 7, 4, 10, 0, 0, tzinfo=mock_tz)

        # When
        from src.rules.session_block_outside_hours import SessionBlockOutsideHoursRule
        rule = SessionBlockOutsideHoursRule(config, mock_lockout_manager)

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            result = rule.check(position_event)

        # Then
        assert result is not None
        assert result['reason'] == 'Trading on market holiday'
        assert result['date'] == '2024-07-04'

    def test_check_per_instrument_session_hours(self, mock_lockout_manager):
        """
        GIVEN: ES with extended hours (6 PM ET active)
        WHEN: ES position checked at 6 PM
        THEN: No breach (ES evening session active)
        """
        # Given
        position_event = {
            "accountId": 123,
            "contractId": "CON.F.US.ES.U25",
            "creationTimestamp": "2024-07-21T22:00:00Z"  # 6 PM ET
        }

        config = {
            'default_session': {
                'start': '09:30',
                'end': '16:00',
                'timezone': 'America/New_York'
            },
            'per_instrument_sessions': {
                'ES': {
                    'start': '18:00',
                    'end': '17:00',
                    'timezone': 'America/Chicago'
                }
            }
        }

        mock_tz = pytz.timezone('America/New_York')
        mock_now = datetime(2024, 7, 21, 18, 0, 0, tzinfo=mock_tz)

        # When
        from src.rules.session_block_outside_hours import SessionBlockOutsideHoursRule
        from src.utils.symbol_utils import extract_symbol_from_contract

        rule = SessionBlockOutsideHoursRule(config, mock_lockout_manager)
        symbol = extract_symbol_from_contract(position_event['contractId'])

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            result = rule.check(position_event, symbol=symbol)

        # Then
        assert result is None

    def test_check_session_end_auto_close(self, mock_lockout_manager):
        """
        GIVEN: Position still open at exactly 4:00 PM
        WHEN: Position is checked
        THEN: Auto-close triggered
        """
        # Given
        position_event = {
            "accountId": 123,
            "contractId": "CON.F.US.MNQ.U25",
            "creationTimestamp": "2024-07-21T15:30:00Z"
        }

        config = {
            'session_hours': {
                'start': '09:30',
                'end': '16:00',
                'timezone': 'America/New_York'
            },
            'auto_close_at_end': True
        }

        mock_tz = pytz.timezone('America/New_York')
        mock_now = datetime(2024, 7, 21, 16, 0, 0, tzinfo=mock_tz)

        # When
        from src.rules.session_block_outside_hours import SessionBlockOutsideHoursRule
        rule = SessionBlockOutsideHoursRule(config, mock_lockout_manager)

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            result = rule.check(position_event)

        # Then
        assert result is not None
        assert result['reason'] == 'Session end - auto-close'

        action = result['action']
        assert action['type'] == 'CLOSE_ALL_POSITIONS'
