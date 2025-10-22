"""
Integration Tests - REST API Position Management
Test IDs: IT-001-03, IT-001-06, IT-001-07

Tests position operations including:
- Close positions
- Search open positions
- Retrieve contract metadata
"""

import pytest
import responses
from src.api.rest_client import RestClient


class TestPositionManagement:
    """Test suite for REST API position management operations"""

    @pytest.fixture
    def authenticated_client(self):
        """Fixture providing authenticated REST client"""
        client = RestClient(
            base_url="https://api.topstepx.com",
            username="test_user_123",
            api_key="test_key_abc123xyz"
        )
        # Simulate authenticated state
        client._token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"
        client._token_expiry = None  # Set appropriately in real implementation
        return client

    @responses.activate
    def test_close_position_success(self, authenticated_client, caplog):
        """
        IT-001-03: Close position successfully

        Verifies:
        - Position closure with valid accountId and contractId
        - Proper request format with Authorization header
        - Success response handling
        - Used by enforcement actions
        """
        # Mock successful close position response
        responses.add(
            responses.POST,
            "https://api.topstepx.com/api/Position/closeContract",
            json={
                "success": True,
                "errorCode": 0,
                "errorMessage": None
            },
            status=200
        )

        # Close position
        result = authenticated_client.close_position(
            account_id=12345,
            contract_id="CON.F.US.MNQ.H25"
        )

        # Assertions
        assert result is True, "Position closure should succeed"

        # Verify request format
        assert len(responses.calls) == 1, "Should make exactly one API call"
        request = responses.calls[0].request
        assert request.headers.get("Authorization", "").startswith("Bearer "), \
            "Should include Bearer token in Authorization header"
        assert request.headers["Content-Type"] == "application/json"

        # Verify request body
        body = request.body.decode()
        assert "12345" in body, "Should include accountId"
        assert "CON.F.US.MNQ.H25" in body, "Should include contractId"

        # Verify logging
        assert "position closed successfully" in caplog.text.lower() or \
               "mnq" in caplog.text.lower(), \
            "Should log successful position closure"

    @responses.activate
    def test_search_open_positions(self, authenticated_client):
        """
        IT-001-06: Retrieve open positions

        Verifies:
        - Position search by accountId
        - Response parsed into Position objects
        - Multiple positions returned correctly
        - Used by enforcement actions to determine positions to close
        """
        # Mock successful positions search response
        responses.add(
            responses.POST,
            "https://api.topstepx.com/api/Position/searchOpen",
            json={
                "positions": [
                    {
                        "accountId": 12345,
                        "contractId": "CON.F.US.MNQ.H25",
                        "side": 0,  # Long
                        "quantity": 3,
                        "avgPrice": 21000.50,
                        "unrealizedPnl": 150.00
                    },
                    {
                        "accountId": 12345,
                        "contractId": "CON.F.US.ES.H25",
                        "side": 1,  # Short
                        "quantity": 2,
                        "avgPrice": 5000.25,
                        "unrealizedPnl": -75.50
                    }
                ],
                "success": True,
                "errorCode": 0,
                "errorMessage": None
            },
            status=200
        )

        # Search open positions
        positions = authenticated_client.search_open_positions(account_id=12345)

        # Assertions
        assert positions is not None, "Should return positions list"
        assert len(positions) == 2, "Should return 2 positions"

        # Verify first position (MNQ long)
        assert positions[0].contract_id == "CON.F.US.MNQ.H25", \
            "First position should be MNQ"
        assert positions[0].side == 0, "Should be long position"
        assert positions[0].quantity == 3, "Should have 3 contracts"
        assert positions[0].avg_price == 21000.50, "Should have correct avg price"
        assert positions[0].unrealized_pnl == 150.00, "Should have correct unrealized P&L"

        # Verify second position (ES short)
        assert positions[1].contract_id == "CON.F.US.ES.H25", \
            "Second position should be ES"
        assert positions[1].side == 1, "Should be short position"
        assert positions[1].quantity == 2, "Should have 2 contracts"
        assert positions[1].unrealized_pnl == -75.50, "Should have correct unrealized P&L"

        # Verify request format
        assert len(responses.calls) == 1, "Should make exactly one API call"
        request = responses.calls[0].request
        body = request.body.decode()
        assert "12345" in body, "Should include accountId in request"

    @responses.activate
    def test_search_contract_by_id(self, authenticated_client, caplog):
        """
        IT-001-07: Retrieve contract metadata

        Verifies:
        - Contract search by contractId
        - Contract metadata parsed correctly
        - Tick size and tick value extracted
        - Used by ContractCache for P&L calculations
        """
        # Mock successful contract search response
        responses.add(
            responses.POST,
            "https://api.topstepx.com/api/Contract/searchById",
            json={
                "contract": {
                    "id": "CON.F.US.MNQ.H25",
                    "name": "Micro E-Mini NASDAQ-100 Mar 2025",
                    "symbol": "MNQ",
                    "exchange": "CME",
                    "tickSize": 0.25,
                    "tickValue": 0.50,
                    "contractSize": 1
                },
                "success": True,
                "errorCode": 0,
                "errorMessage": None
            },
            status=200
        )

        # Search contract by ID
        contract = authenticated_client.search_contract_by_id(
            contract_id="CON.F.US.MNQ.H25"
        )

        # Assertions
        assert contract is not None, "Should return contract object"
        assert contract.id == "CON.F.US.MNQ.H25", "Should have correct contract ID"
        assert contract.symbol == "MNQ", "Should have correct symbol"
        assert contract.name == "Micro E-Mini NASDAQ-100 Mar 2025", \
            "Should have correct name"
        assert contract.exchange == "CME", "Should have correct exchange"
        assert contract.tick_size == 0.25, "Should have correct tick size"
        assert contract.tick_value == 0.50, "Should have correct tick value"
        assert contract.contract_size == 1, "Should have correct contract size"

        # Verify request format
        assert len(responses.calls) == 1, "Should make exactly one API call"
        request = responses.calls[0].request
        body = request.body.decode()
        assert "CON.F.US.MNQ.H25" in body, "Should include contractId in request"

        # Verify logging (if implemented at DEBUG level)
        # Note: Debug logging verification is optional
