"""
Unit Tests for API Data Converters

Tests the conversion layer between TopstepX API (camelCase) and internal backend (snake_case).
"""
import pytest
from datetime import datetime
from src.api.converters import (
    api_to_internal_account,
    api_to_internal_order,
    api_to_internal_position,
    api_to_internal_trade,
    api_to_internal_contract,
    api_to_internal_quote,
    internal_to_api_order_request,
    internal_to_api_order_modify_request,
    internal_to_api_order_cancel_request,
    internal_to_api_position_close_request,
    _parse_timestamp,
)
from src.api.enums import (
    APIOrderStatus,
    APIOrderSide,
    APIOrderType,
    APIPositionType,
    InternalOrderState,
)


class TestTimestampParsing:
    """Test timestamp parsing utilities"""

    def test_parse_iso8601_with_timezone(self):
        """Test parsing ISO 8601 timestamp with timezone offset"""
        ts = "2025-07-18T21:00:01.268009+00:00"
        result = _parse_timestamp(ts)

        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 7
        assert result.day == 18

    def test_parse_iso8601_with_z_suffix(self):
        """Test parsing ISO 8601 timestamp with Z suffix"""
        ts = "2025-01-20T15:47:39.882Z"
        result = _parse_timestamp(ts)

        assert result is not None
        assert isinstance(result, datetime)

    def test_parse_none_timestamp(self):
        """Test parsing None timestamp returns None"""
        result = _parse_timestamp(None)
        assert result is None

    def test_parse_invalid_timestamp(self):
        """Test parsing invalid timestamp returns None"""
        result = _parse_timestamp("invalid")
        assert result is None


class TestAccountConverter:
    """Test API to internal account conversion"""

    def test_convert_complete_account(self):
        """Test converting complete account data"""
        api_data = {
            "id": 465,
            "name": "Test Account",
            "balance": 50000.50,
            "canTrade": True,
            "isVisible": True,
            "simulated": False,
        }

        result = api_to_internal_account(api_data)

        assert result["account_id"] == 465
        assert result["name"] == "Test Account"
        assert result["balance"] == 50000.50
        assert result["can_trade"] is True
        assert result["is_visible"] is True
        assert result["simulated"] is False

    def test_convert_minimal_account(self):
        """Test converting account with minimal data"""
        api_data = {
            "id": 123,
            "name": "Minimal",
        }

        result = api_to_internal_account(api_data)

        assert result["account_id"] == 123
        assert result["name"] == "Minimal"
        assert result["balance"] == 0.0  # Default
        assert result["can_trade"] is False  # Default
        assert result["is_visible"] is True  # Default
        assert result["simulated"] is False  # Default


class TestOrderConverter:
    """Test API to internal order conversion"""

    def test_convert_complete_order(self):
        """Test converting complete order data"""
        api_data = {
            "id": 26974,
            "accountId": 465,
            "contractId": "CON.F.US.ENQ.H25",
            "symbolId": "ENQ.H25",
            "creationTimestamp": "2025-07-18T21:00:01.268009+00:00",
            "updateTimestamp": "2025-07-18T21:01:00.000000+00:00",
            "status": APIOrderStatus.OPEN,
            "type": APIOrderType.STOP,
            "side": APIOrderSide.BID,  # Buy
            "size": 2,
            "limitPrice": None,
            "stopPrice": 5000.00,
            "fillVolume": 0,
            "filledPrice": None,
            "customTag": "test-order",
        }

        result = api_to_internal_order(api_data)

        assert result["order_id"] == 26974
        assert result["account_id"] == 465
        assert result["contract_id"] == "CON.F.US.ENQ.H25"
        assert result["symbol_id"] == "ENQ.H25"
        assert result["state"] == InternalOrderState.ACTIVE  # OPEN maps to ACTIVE
        assert result["order_type"] == APIOrderType.STOP
        assert result["side"] == "buy"
        assert result["quantity"] == 2
        assert result["limit_price"] is None
        assert result["stop_price"] == 5000.00
        assert result["filled_quantity"] == 0
        assert result["filled_price"] is None
        assert result["custom_tag"] == "test-order"

    def test_convert_filled_order(self):
        """Test converting filled order"""
        api_data = {
            "id": 9056,
            "accountId": 465,
            "contractId": "CON.F.US.ENQ.H25",
            "symbolId": "ENQ.H25",
            "creationTimestamp": "2025-07-18T21:00:00.000000+00:00",
            "updateTimestamp": "2025-07-18T21:00:05.000000+00:00",
            "status": APIOrderStatus.FILLED,
            "type": APIOrderType.MARKET,
            "side": APIOrderSide.ASK,  # Sell
            "size": 1,
            "limitPrice": None,
            "stopPrice": None,
            "fillVolume": 1,
            "filledPrice": 5010.50,
            "customTag": None,
        }

        result = api_to_internal_order(api_data)

        assert result["state"] == InternalOrderState.FILLED
        assert result["side"] == "sell"
        assert result["filled_quantity"] == 1
        assert result["filled_price"] == 5010.50

    def test_convert_order_with_orderId_field(self):
        """Test converting order that uses 'orderId' instead of 'id'"""
        api_data = {
            "orderId": 12345,
            "accountId": 465,
            "contractId": "CON.F.US.ENQ.H25",
            "status": APIOrderStatus.PENDING,
            "type": APIOrderType.LIMIT,
            "side": APIOrderSide.BID,
            "size": 1,
        }

        result = api_to_internal_order(api_data)

        assert result["order_id"] == 12345


class TestPositionConverter:
    """Test API to internal position conversion"""

    def test_convert_long_position(self):
        """Test converting long position"""
        api_data = {
            "id": 1001,
            "accountId": 536,
            "contractId": "CON.F.US.GMET.J25",
            "creationTimestamp": "2025-07-18T20:00:00.000000+00:00",
            "type": APIPositionType.LONG,
            "size": 3,
            "averagePrice": 2500.75,
        }

        result = api_to_internal_position(api_data)

        assert result["position_id"] == 1001
        assert result["account_id"] == 536
        assert result["contract_id"] == "CON.F.US.GMET.J25"
        assert result["position_type"] == "long"
        assert result["quantity"] == 3
        assert result["average_price"] == 2500.75
        assert result["unrealized_pnl"] == 0.0  # Default

    def test_convert_short_position(self):
        """Test converting short position"""
        api_data = {
            "accountId": 536,
            "contractId": "CON.F.US.ENQ.H25",
            "type": APIPositionType.SHORT,
            "size": 1,
            "averagePrice": 5000.00,
        }

        result = api_to_internal_position(api_data)

        assert result["position_type"] == "short"
        assert result["quantity"] == 1

    def test_convert_position_old_api_format(self):
        """Test converting position from old API format with side/quantity"""
        api_data = {
            "accountId": 536,
            "contractId": "CON.F.US.ENQ.H25",
            "side": 0,  # 0=Buy=Long
            "quantity": 2,
            "avgPrice": 5010.25,
            "unrealizedPnl": 150.50,
        }

        result = api_to_internal_position(api_data)

        assert result["position_type"] == "long"
        assert result["quantity"] == 2
        assert result["average_price"] == 5010.25
        assert result["unrealized_pnl"] == 150.50

    def test_convert_position_old_api_short(self):
        """Test converting short position from old API format"""
        api_data = {
            "accountId": 536,
            "contractId": "CON.F.US.ENQ.H25",
            "side": 1,  # 1=Sell=Short
            "quantity": 1,
            "avgPrice": 5000.00,
        }

        result = api_to_internal_position(api_data)

        assert result["position_type"] == "short"


class TestTradeConverter:
    """Test API to internal trade conversion"""

    def test_convert_complete_trade(self):
        """Test converting complete trade data"""
        api_data = {
            "id": 5001,
            "accountId": 203,
            "contractId": "CON.F.US.ENQ.H25",
            "creationTimestamp": "2025-01-20T15:47:39.882Z",
            "price": 5010.50,
            "profitAndLoss": 125.75,
            "fees": 2.50,
            "side": APIOrderSide.BID,  # Buy
            "size": 1,
            "voided": False,
            "orderId": 26974,
        }

        result = api_to_internal_trade(api_data)

        assert result["trade_id"] == 5001
        assert result["order_id"] == 26974
        assert result["account_id"] == 203
        assert result["contract_id"] == "CON.F.US.ENQ.H25"
        assert result["quantity"] == 1
        assert result["price"] == 5010.50
        assert result["side"] == "buy"
        assert result["fees"] == 2.50
        assert result["profit_and_loss"] == 125.75
        assert result["voided"] is False

    def test_convert_half_turn_trade(self):
        """Test converting half-turn trade (null P&L)"""
        api_data = {
            "id": 5002,
            "accountId": 203,
            "contractId": "CON.F.US.ENQ.H25",
            "creationTimestamp": "2025-01-20T15:50:00.000Z",
            "price": 5020.00,
            "profitAndLoss": None,  # Half-turn trade
            "fees": 2.50,
            "side": APIOrderSide.ASK,  # Sell
            "size": 1,
            "voided": False,
            "orderId": 26975,
        }

        result = api_to_internal_trade(api_data)

        assert result["profit_and_loss"] is None
        assert result["side"] == "sell"


class TestContractConverter:
    """Test API to internal contract conversion"""

    def test_convert_complete_contract(self):
        """Test converting complete contract data"""
        api_data = {
            "id": "CON.F.US.ENQ.H25",
            "name": "E-mini NASDAQ-100",
            "description": "E-mini NASDAQ-100 March 2025",
            "tickSize": 0.25,
            "tickValue": 5.00,
            "activeContract": True,
            "symbolId": "ENQ.H25",
            "exchange": "CME",
            "contractSize": 1,
        }

        result = api_to_internal_contract(api_data)

        assert result["contract_id"] == "CON.F.US.ENQ.H25"
        assert result["name"] == "E-mini NASDAQ-100"
        assert result["symbol"] == "ENQ.H25"
        assert result["description"] == "E-mini NASDAQ-100 March 2025"
        assert result["exchange"] == "CME"
        assert result["tick_size"] == 0.25
        assert result["tick_value"] == 5.00
        assert result["contract_size"] == 1
        assert result["active_contract"] is True

    def test_convert_contract_old_api_format(self):
        """Test converting contract with old 'symbol' field"""
        api_data = {
            "id": "CON.F.US.GMET.J25",
            "name": "Gold",
            "symbol": "GMET.J25",  # Old API field
            "tickSize": 0.10,
            "tickValue": 1.00,
        }

        result = api_to_internal_contract(api_data)

        assert result["symbol"] == "GMET.J25"


class TestQuoteConverter:
    """Test API to internal quote conversion"""

    def test_convert_complete_quote(self):
        """Test converting complete quote data"""
        api_data = {
            "symbol": "ENQ.H25",
            "symbolName": "E-mini NASDAQ-100 Mar 25",
            "lastPrice": 5010.50,
            "bestBid": 5010.25,
            "bestAsk": 5010.75,
            "change": 15.50,
            "changePercent": 0.31,
            "open": 4995.00,
            "high": 5015.00,
            "low": 4990.00,
            "volume": 125000,
            "lastUpdated": "2025-07-18T21:05:00.000Z",
            "timestamp": "2025-07-18T21:05:00.100Z",
        }

        result = api_to_internal_quote(api_data)

        assert result["symbol"] == "ENQ.H25"
        assert result["symbol_name"] == "E-mini NASDAQ-100 Mar 25"
        assert result["last_price"] == 5010.50
        assert result["best_bid"] == 5010.25
        assert result["best_ask"] == 5010.75
        assert result["change"] == 15.50
        assert result["change_percent"] == 0.31
        assert result["open"] == 4995.00
        assert result["high"] == 5015.00
        assert result["low"] == 4990.00
        assert result["volume"] == 125000


class TestReverseConverters:
    """Test internal to API conversion (for sending requests)"""

    def test_internal_to_api_order_request(self):
        """Test converting internal order to API request format"""
        internal_data = {
            "account_id": 465,
            "contract_id": "CON.F.US.ENQ.H25",
            "order_type": "stop",
            "side": "buy",
            "quantity": 1,
            "stop_price": 5000.00,
            "custom_tag": "test",
        }

        result = internal_to_api_order_request(internal_data)

        assert result["accountId"] == 465
        assert result["contractId"] == "CON.F.US.ENQ.H25"
        assert result["type"] == APIOrderType.STOP
        assert result["side"] == APIOrderSide.BID
        assert result["size"] == 1
        assert result["stopPrice"] == 5000.00
        assert result["customTag"] == "test"

    def test_internal_to_api_order_modify_request(self):
        """Test converting internal order modify to API request"""
        internal_data = {
            "account_id": 465,
            "order_id": 26974,
            "stop_price": 5010.00,
        }

        result = internal_to_api_order_modify_request(internal_data)

        assert result["accountId"] == 465
        assert result["orderId"] == 26974
        assert result["stopPrice"] == 5010.00
        assert result["size"] is None

    def test_internal_to_api_order_cancel_request(self):
        """Test converting internal order cancel to API request"""
        internal_data = {
            "account_id": 465,
            "order_id": 26974,
        }

        result = internal_to_api_order_cancel_request(internal_data)

        assert result["accountId"] == 465
        assert result["orderId"] == 26974

    def test_internal_to_api_position_close_request(self):
        """Test converting internal position close to API request"""
        internal_data = {
            "account_id": 536,
            "contract_id": "CON.F.US.GMET.J25",
        }

        result = internal_to_api_position_close_request(internal_data)

        assert result["accountId"] == 536
        assert result["contractId"] == "CON.F.US.GMET.J25"


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_order_with_missing_optional_fields(self):
        """Test order conversion with missing optional fields"""
        api_data = {
            "id": 1,
            "accountId": 1,
            "contractId": "TEST",
            # Missing many optional fields
        }

        result = api_to_internal_order(api_data)

        # Should not raise, should use defaults
        assert result["order_id"] == 1
        assert result["filled_quantity"] == 0
        assert result["limit_price"] is None

    def test_position_with_no_type_or_side(self):
        """Test position conversion when both type and side are missing"""
        api_data = {
            "accountId": 1,
            "contractId": "TEST",
            "size": 1,
            "averagePrice": 100.0,
        }

        result = api_to_internal_position(api_data)

        assert result["position_type"] is None  # Cannot determine

    def test_quote_with_minimal_data(self):
        """Test quote conversion with minimal data"""
        api_data = {
            "symbol": "TEST",
        }

        result = api_to_internal_quote(api_data)

        # Should not raise, should use defaults
        assert result["symbol"] == "TEST"
        assert result["last_price"] == 0.0
        assert result["volume"] == 0
