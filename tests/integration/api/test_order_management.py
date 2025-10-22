"""
Integration Tests - REST API Order Management
Test IDs: IT-001-04, IT-001-05

Tests order operations including:
- Cancel working orders
- Place stop-loss orders
- Order ID handling
"""

import pytest
import responses
from src.api.rest_client import RestClient


class TestOrderManagement:
    """Test suite for REST API order management operations"""

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
    def test_cancel_order_success(self, authenticated_client, caplog):
        """
        IT-001-04: Cancel working order successfully

        Verifies:
        - Order cancellation with valid orderId
        - Proper request format
        - Authorization header included
        - Success response handling
        """
        # Mock successful cancel order response
        responses.add(
            responses.POST,
            "https://api.topstepx.com/api/Order/cancel",
            json={
                "success": True,
                "errorCode": 0,
                "errorMessage": None
            },
            status=200
        )

        # Cancel order
        result = authenticated_client.cancel_order(
            account_id=12345,
            order_id=9056
        )

        # Assertions
        assert result is True, "Order cancellation should succeed"

        # Verify request format
        assert len(responses.calls) == 1, "Should make exactly one API call"
        request = responses.calls[0].request
        assert request.headers.get("Authorization", "").startswith("Bearer "), \
            "Should include Bearer token in Authorization header"
        assert request.headers["Content-Type"] == "application/json"

        # Verify request body
        body = request.body.decode()
        assert "12345" in body, "Should include accountId"
        assert "9056" in body, "Should include orderId"

        # Verify logging
        assert "order canceled successfully" in caplog.text.lower(), \
            "Should log successful cancellation"

    @responses.activate
    def test_place_stop_loss_order(self, authenticated_client, caplog):
        """
        IT-001-05: Place stop-loss order successfully

        Verifies:
        - Stop-loss order placement
        - All order parameters included
        - OrderId returned from response
        - Used by RULE-008 and RULE-012 enforcement
        """
        # Mock successful order placement response
        responses.add(
            responses.POST,
            "https://api.topstepx.com/api/Order/place",
            json={
                "orderId": 9056,
                "success": True,
                "errorCode": 0,
                "errorMessage": None
            },
            status=200
        )

        # Place stop-loss order
        order_id = authenticated_client.place_order(
            account_id=12345,
            contract_id="CON.F.US.MNQ.H25",
            type=4,  # Stop order
            side=1,  # Sell/Ask (to close long position)
            size=3,
            stop_price=20950.00
        )

        # Assertions
        assert order_id == 9056, "Should return orderId from response"

        # Verify request format
        assert len(responses.calls) == 1, "Should make exactly one API call"
        request = responses.calls[0].request
        assert request.headers.get("Authorization", "").startswith("Bearer "), \
            "Should include Bearer token"

        # Verify all order parameters in request body
        body = request.body.decode()
        assert "12345" in body, "Should include accountId"
        assert "CON.F.US.MNQ.H25" in body, "Should include contractId"
        assert '"type": 4' in body or '"type":4' in body, "Should include order type (Stop)"
        assert '"side": 1' in body or '"side":1' in body, "Should include side (Sell)"
        assert "3" in body, "Should include size"
        assert "20950" in body, "Should include stop price"

        # Verify logging
        assert "stop-loss order placed" in caplog.text.lower() or \
               "order placed" in caplog.text.lower(), \
            "Should log order placement"

    @responses.activate
    def test_modify_order_success(self, authenticated_client, caplog):
        """
        IT-001-05 (Extended): Modify existing order

        Verifies:
        - Order modification with new parameters
        - Proper request format
        - Success response handling
        """
        # Mock successful modify order response
        responses.add(
            responses.POST,
            "https://api.topstepx.com/api/Order/modify",
            json={
                "success": True,
                "errorCode": 0,
                "errorMessage": None
            },
            status=200
        )

        # Modify order
        result = authenticated_client.modify_order(
            account_id=12345,
            order_id=9056,
            stop_price=20975.00  # Move stop-loss
        )

        # Assertions
        assert result is True, "Order modification should succeed"

        # Verify request format
        assert len(responses.calls) == 1, "Should make exactly one API call"
        request = responses.calls[0].request

        # Verify request body
        body = request.body.decode()
        assert "12345" in body, "Should include accountId"
        assert "9056" in body, "Should include orderId"
        assert "20975" in body, "Should include new stop price"

        # Verify logging (if implemented)
        # Note: Logging verification is optional based on implementation
