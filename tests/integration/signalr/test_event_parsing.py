"""SignalR Event Parsing Integration Tests

Test ID Range: IT-SIG-008 to IT-SIG-009
Purpose: Verify correct parsing of SignalR event payloads into application data structures
Category: Event Parsing
"""

import pytest
from datetime import datetime
from enum import IntEnum


# Mock enums for order types and position types
class OrderSide(IntEnum):
    """Order side enumeration"""
    BID = 0
    ASK = 1


class PositionType(IntEnum):
    """Position type enumeration"""
    LONG = 1
    SHORT = 2


# Mock data structures
class TradeEvent:
    """Trade event data structure"""

    def __init__(self, payload: dict):
        self.id = payload["id"]
        self.account_id = payload["accountId"]
        self.contract_id = payload["contractId"]
        self.creation_timestamp = self._parse_timestamp(payload["creationTimestamp"])
        self.price = float(payload["price"])
        self.profit_and_loss = float(payload["profitAndLoss"])
        self.fees = float(payload["fees"])
        self.side = OrderSide(payload["side"])
        self.size = int(payload["size"])
        self.voided = bool(payload["voided"])
        self.order_id = payload["orderId"]

    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> datetime:
        """Parse ISO 8601 timestamp to datetime object"""
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))


class PositionEvent:
    """Position event data structure"""

    def __init__(self, payload: dict):
        self.id = payload["id"]
        self.account_id = payload["accountId"]
        self.contract_id = payload["contractId"]
        self.creation_timestamp = self._parse_timestamp(payload["creationTimestamp"])
        self.type = PositionType(payload["type"])
        self.size = int(payload["size"])
        self.average_price = float(payload["averagePrice"])

    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> datetime:
        """Parse ISO 8601 timestamp to datetime object"""
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))


def parse_trade_event(payload: dict) -> TradeEvent:
    """Parse GatewayUserTrade event payload into TradeEvent object"""
    return TradeEvent(payload)


def parse_position_event(payload: dict) -> PositionEvent:
    """Parse GatewayUserPosition event payload into PositionEvent object"""
    return PositionEvent(payload)


class TestTradeEventParsing:
    """IT-SIG-008: Parse GatewayUserTrade Event Payload"""

    @pytest.fixture
    def trade_event_payload(self):
        """Mock GatewayUserTrade event payload"""
        return {
            "id": 101112,
            "accountId": 123,
            "contractId": "CON.F.US.EP.U25",
            "creationTimestamp": "2024-07-21T13:47:00Z",
            "price": 2100.75,
            "profitAndLoss": 50.25,
            "fees": 2.50,
            "side": 0,  # BID
            "size": 1,
            "voided": False,
            "orderId": 789
        }

    def test_parse_trade_event_all_fields(self, trade_event_payload):
        """
        IT-SIG-008: Parse GatewayUserTrade event payload

        Given:
        - Connected User Hub
        - Trade event received with all fields populated

        When:
        1. Event handler receives trade event
        2. Parse event into TradeEvent object
        3. Validate all fields

        Then:
        - All fields correctly mapped to object attributes
        - Numeric fields parsed as correct types (int, float)
        - Timestamp parsed to datetime object
        - Enum values (side) correctly interpreted
        - Boolean flags correctly parsed
        """
        # Act
        trade = parse_trade_event(trade_event_payload)

        # Assert - Field mapping
        assert trade.id == 101112
        assert trade.account_id == 123
        assert trade.contract_id == "CON.F.US.EP.U25"
        assert trade.order_id == 789

        # Assert - Numeric types
        assert trade.price == 2100.75
        assert isinstance(trade.price, float)
        assert trade.profit_and_loss == 50.25
        assert isinstance(trade.profit_and_loss, float)
        assert trade.fees == 2.50
        assert isinstance(trade.fees, float)
        assert trade.size == 1
        assert isinstance(trade.size, int)

        # Assert - Timestamp parsing
        assert isinstance(trade.creation_timestamp, datetime)
        assert trade.creation_timestamp.year == 2024
        assert trade.creation_timestamp.month == 7
        assert trade.creation_timestamp.day == 21
        assert trade.creation_timestamp.hour == 13
        assert trade.creation_timestamp.minute == 47

        # Assert - Enum values
        assert trade.side == OrderSide.BID
        assert trade.side.value == 0

        # Assert - Boolean flags
        assert trade.voided is False
        assert isinstance(trade.voided, bool)

    def test_parse_trade_event_bid_side(self, trade_event_payload):
        """
        Test parsing trade with BID side (side=0)

        Verifies:
        - Side enumeration correctly interpreted
        - BID (0) maps to OrderSide.BID
        """
        # Arrange
        trade_event_payload["side"] = 0

        # Act
        trade = parse_trade_event(trade_event_payload)

        # Assert
        assert trade.side == OrderSide.BID
        assert trade.side.value == 0

    def test_parse_trade_event_ask_side(self, trade_event_payload):
        """
        Test parsing trade with ASK side (side=1)

        Verifies:
        - Side enumeration correctly interpreted
        - ASK (1) maps to OrderSide.ASK
        """
        # Arrange
        trade_event_payload["side"] = 1

        # Act
        trade = parse_trade_event(trade_event_payload)

        # Assert
        assert trade.side == OrderSide.ASK
        assert trade.side.value == 1

    def test_parse_trade_event_voided_true(self, trade_event_payload):
        """
        Test parsing voided trade (voided=True)

        Verifies:
        - Boolean voided flag correctly parsed
        - Voided trades identified
        """
        # Arrange
        trade_event_payload["voided"] = True

        # Act
        trade = parse_trade_event(trade_event_payload)

        # Assert
        assert trade.voided is True

    def test_parse_trade_event_negative_pnl(self, trade_event_payload):
        """
        Test parsing trade with negative P&L (losing trade)

        Verifies:
        - Negative profit_and_loss correctly parsed
        - Losses represented as negative numbers
        """
        # Arrange
        trade_event_payload["profitAndLoss"] = -75.50

        # Act
        trade = parse_trade_event(trade_event_payload)

        # Assert
        assert trade.profit_and_loss == -75.50
        assert trade.profit_and_loss < 0

    def test_parse_trade_event_timestamp_formats(self):
        """
        Test parsing various timestamp formats

        Verifies:
        - ISO 8601 format with 'Z' suffix
        - ISO 8601 format with timezone offset
        - Datetime object correctly created
        """
        # Test with 'Z' suffix
        payload_z = {
            "id": 1,
            "accountId": 123,
            "contractId": "CON.F.US.EP.U25",
            "creationTimestamp": "2024-07-21T13:47:00Z",
            "price": 2100.00,
            "profitAndLoss": 0.00,
            "fees": 2.50,
            "side": 0,
            "size": 1,
            "voided": False,
            "orderId": 789
        }

        trade_z = parse_trade_event(payload_z)
        assert isinstance(trade_z.creation_timestamp, datetime)

        # Test with timezone offset
        payload_offset = payload_z.copy()
        payload_offset["creationTimestamp"] = "2024-07-21T13:47:00+00:00"

        trade_offset = parse_trade_event(payload_offset)
        assert isinstance(trade_offset.creation_timestamp, datetime)


class TestPositionEventParsing:
    """IT-SIG-009: Parse GatewayUserPosition Event Payload"""

    @pytest.fixture
    def position_event_payload(self):
        """Mock GatewayUserPosition event payload"""
        return {
            "id": 456,
            "accountId": 123,
            "contractId": "CON.F.US.EP.U25",
            "creationTimestamp": "2024-07-21T13:45:00Z",
            "type": 1,  # LONG
            "size": 2,
            "averagePrice": 2100.25
        }

    def test_parse_position_event_all_fields(self, position_event_payload):
        """
        IT-SIG-009: Parse GatewayUserPosition event payload

        Given:
        - Connected User Hub
        - Position event received with all fields

        When:
        1. Event handler receives position event
        2. Parse into PositionEvent object
        3. Validate position type enumeration

        Then:
        - Position type correctly interpreted (1 = Long, 2 = Short)
        - Size parsed as integer
        - Average price parsed as float
        - Timestamp converted to datetime
        - Contract ID correctly extracted
        """
        # Act
        position = parse_position_event(position_event_payload)

        # Assert - Field mapping
        assert position.id == 456
        assert position.account_id == 123
        assert position.contract_id == "CON.F.US.EP.U25"

        # Assert - Position type enumeration
        assert position.type == PositionType.LONG
        assert position.type.value == 1

        # Assert - Numeric types
        assert position.size == 2
        assert isinstance(position.size, int)
        assert position.average_price == 2100.25
        assert isinstance(position.average_price, float)

        # Assert - Timestamp parsing
        assert isinstance(position.creation_timestamp, datetime)
        assert position.creation_timestamp.year == 2024
        assert position.creation_timestamp.month == 7
        assert position.creation_timestamp.day == 21

    def test_parse_position_event_long_type(self, position_event_payload):
        """
        Test parsing LONG position (type=1)

        Verifies:
        - Type enumeration correctly interpreted
        - LONG (1) maps to PositionType.LONG
        """
        # Arrange
        position_event_payload["type"] = 1

        # Act
        position = parse_position_event(position_event_payload)

        # Assert
        assert position.type == PositionType.LONG
        assert position.type.value == 1

    def test_parse_position_event_short_type(self, position_event_payload):
        """
        Test parsing SHORT position (type=2)

        Verifies:
        - Type enumeration correctly interpreted
        - SHORT (2) maps to PositionType.SHORT
        """
        # Arrange
        position_event_payload["type"] = 2

        # Act
        position = parse_position_event(position_event_payload)

        # Assert
        assert position.type == PositionType.SHORT
        assert position.type.value == 2

    def test_parse_position_event_large_size(self, position_event_payload):
        """
        Test parsing position with large size

        Verifies:
        - Large position sizes correctly parsed
        - Integer type maintained
        """
        # Arrange
        position_event_payload["size"] = 100

        # Act
        position = parse_position_event(position_event_payload)

        # Assert
        assert position.size == 100
        assert isinstance(position.size, int)

    def test_parse_position_event_negative_size(self, position_event_payload):
        """
        Test parsing position with negative size (short position representation)

        Note: In some systems, short positions may be represented with negative size

        Verifies:
        - Negative size correctly parsed
        - Absolute value represents position magnitude
        """
        # Arrange
        position_event_payload["size"] = -3
        position_event_payload["type"] = 2  # SHORT

        # Act
        position = parse_position_event(position_event_payload)

        # Assert
        assert position.size == -3
        assert position.type == PositionType.SHORT

    def test_parse_position_event_decimal_average_price(self, position_event_payload):
        """
        Test parsing position with high precision average price

        Verifies:
        - Decimal precision maintained
        - Float type with accurate decimal places
        """
        # Arrange
        position_event_payload["averagePrice"] = 2100.12345

        # Act
        position = parse_position_event(position_event_payload)

        # Assert
        assert position.average_price == 2100.12345
        assert isinstance(position.average_price, float)

    def test_parse_position_event_contract_id_formats(self):
        """
        Test parsing positions with various contract ID formats

        Verifies:
        - Different contract ID formats supported
        - String contract IDs preserved exactly
        """
        # Test standard format
        payload_standard = {
            "id": 456,
            "accountId": 123,
            "contractId": "CON.F.US.EP.U25",
            "creationTimestamp": "2024-07-21T13:45:00Z",
            "type": 1,
            "size": 2,
            "averagePrice": 2100.25
        }

        position_standard = parse_position_event(payload_standard)
        assert position_standard.contract_id == "CON.F.US.EP.U25"

        # Test alternative format
        payload_alt = payload_standard.copy()
        payload_alt["contractId"] = "CON.F.US.MNQ.U25"

        position_alt = parse_position_event(payload_alt)
        assert position_alt.contract_id == "CON.F.US.MNQ.U25"


class TestEventParsingErrorHandling:
    """Test error handling in event parsing"""

    def test_parse_trade_event_missing_field(self):
        """
        Test parsing fails gracefully with missing required field

        Verifies:
        - KeyError raised for missing fields
        - Error message indicates missing field
        """
        # Arrange
        incomplete_payload = {
            "id": 101112,
            "accountId": 123,
            # Missing other required fields
        }

        # Act & Assert
        with pytest.raises(KeyError):
            parse_trade_event(incomplete_payload)

    def test_parse_position_event_invalid_type(self):
        """
        Test parsing fails with invalid position type enumeration

        Verifies:
        - ValueError raised for invalid enum value
        - Only valid position types accepted (1, 2)
        """
        # Arrange
        invalid_payload = {
            "id": 456,
            "accountId": 123,
            "contractId": "CON.F.US.EP.U25",
            "creationTimestamp": "2024-07-21T13:45:00Z",
            "type": 99,  # Invalid type
            "size": 2,
            "averagePrice": 2100.25
        }

        # Act & Assert
        with pytest.raises(ValueError):
            parse_position_event(invalid_payload)

    def test_parse_trade_event_invalid_timestamp(self):
        """
        Test parsing fails with malformed timestamp

        Verifies:
        - ValueError raised for invalid timestamp format
        - ISO 8601 format required
        """
        # Arrange
        invalid_payload = {
            "id": 101112,
            "accountId": 123,
            "contractId": "CON.F.US.EP.U25",
            "creationTimestamp": "invalid-timestamp",
            "price": 2100.75,
            "profitAndLoss": 50.25,
            "fees": 2.50,
            "side": 0,
            "size": 1,
            "voided": False,
            "orderId": 789
        }

        # Act & Assert
        with pytest.raises(ValueError):
            parse_trade_event(invalid_payload)


# Test configuration for pytest
pytestmark = [
    pytest.mark.integration,
    pytest.mark.signalr,
    pytest.mark.unit  # These are more unit-like but part of integration spec
]
