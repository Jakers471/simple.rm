"""
Integration Tests - REST API Authentication
Test IDs: IT-001-01, IT-001-02

Tests authentication flow including:
- Valid credential authentication
- Invalid credential rejection
- Token storage and validation
"""

import pytest
import responses
from datetime import datetime, timedelta
from src.api.rest_client import RestClient
from src.api.exceptions import AuthenticationError


class TestAuthentication:
    """Test suite for REST API authentication flows"""

    @responses.activate
    def test_authenticate_valid_credentials(self, caplog):
        """
        IT-001-01: Authentication with valid API key

        Verifies:
        - Successful authentication with valid credentials
        - JWT token storage
        - Token expiry calculation
        - Logging of success
        """
        # Mock successful authentication response
        responses.add(
            responses.POST,
            "https://api.topstepx.com/api/Auth/loginKey",
            json={
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjE3MzAwMDAwMDB9.signature",
                "success": True,
                "errorCode": 0,
                "errorMessage": None
            },
            status=200
        )

        # Create client and authenticate
        client = RestClient(
            base_url="https://api.topstepx.com",
            username="test_user_123",
            api_key="test_key_abc123xyz"
        )

        result = client.authenticate()

        # Assertions
        assert result is True, "Authentication should succeed"
        assert client.is_authenticated() is True, "Client should be in authenticated state"
        assert client._token is not None, "Token should be stored"
        assert client._token_expiry is not None, "Token expiry should be set"
        assert client._token_expiry > datetime.now(), "Token should not be expired"

        # Verify request was made correctly
        assert len(responses.calls) == 1, "Should make exactly one API call"
        request = responses.calls[0].request
        assert request.headers["Content-Type"] == "application/json"
        assert "userName" in request.body.decode()
        assert "apiKey" in request.body.decode()

        # Verify logging
        assert "authentication successful" in caplog.text.lower(), "Should log success message"

    @responses.activate
    def test_authenticate_invalid_credentials(self, caplog):
        """
        IT-001-02: Authentication with invalid credentials

        Verifies:
        - Authentication failure with invalid credentials
        - AuthenticationError exception raised
        - No token stored
        - Error logging
        """
        # Mock 401 Unauthorized response
        responses.add(
            responses.POST,
            "https://api.topstepx.com/api/Auth/loginKey",
            body="Error: response status is 401",
            status=401,
            content_type="text/plain"
        )

        # Create client with invalid credentials
        client = RestClient(
            base_url="https://api.topstepx.com",
            username="test_user_123",
            api_key="wrong_key_xyz"
        )

        # Attempt authentication and expect exception
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            client.authenticate()

        # Assertions
        assert client.is_authenticated() is False, "Client should not be authenticated"
        assert client._token is None, "Token should not be stored on failure"

        # Verify no retry attempted (401 is permanent failure)
        assert len(responses.calls) == 1, "Should not retry on 401 error"

        # Verify error logging
        assert "authentication failed" in caplog.text.lower(), "Should log authentication failure"
