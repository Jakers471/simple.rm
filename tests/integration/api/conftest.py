"""
Pytest Configuration and Fixtures for REST API Integration Tests

Provides common fixtures and configuration for all API integration tests.
"""

import pytest
import responses
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path so we can import from src
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.rest_client import RestClient


@pytest.fixture
def mock_client():
    """
    Fixture providing REST client for testing

    Returns:
        RestClient: Client instance with test credentials
    """
    client = RestClient(
        base_url="https://api.topstepx.com",
        username="test_user_123",
        api_key="test_key_abc123xyz"
    )
    return client


@pytest.fixture
def authenticated_client(mock_client):
    """
    Fixture providing authenticated REST client

    Returns:
        RestClient: Client instance with simulated authentication
    """
    # Simulate authenticated state
    mock_client._token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjE3MzAwMDAwMDB9.signature"
    mock_client._token_expiry = datetime.now() + timedelta(hours=24)
    return mock_client


@pytest.fixture
def mock_auth_response():
    """
    Fixture for mocking authentication endpoint

    Usage:
        @responses.activate
        def test_something(mock_auth_response):
            mock_auth_response()
            # ... test code
    """
    def _mock_auth():
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
    return _mock_auth


# Test data constants
TEST_USER = "test_user_123"
TEST_API_KEY = "test_key_abc123xyz"
TEST_ACCOUNT_ID = 12345
TEST_CONTRACT_MNQ = "CON.F.US.MNQ.H25"
TEST_CONTRACT_ES = "CON.F.US.ES.H25"
TEST_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjE3MzAwMDAwMDB9.signature"


@pytest.fixture
def test_constants():
    """
    Fixture providing test constants

    Returns:
        dict: Dictionary of test constants
    """
    return {
        "username": TEST_USER,
        "api_key": TEST_API_KEY,
        "account_id": TEST_ACCOUNT_ID,
        "contract_mnq": TEST_CONTRACT_MNQ,
        "contract_es": TEST_CONTRACT_ES,
        "jwt_token": TEST_JWT_TOKEN,
        "base_url": "https://api.topstepx.com"
    }
