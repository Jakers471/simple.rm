"""
REST API Client for TopstepX API

Implements:
- JWT authentication with token expiry management
- Rate limiting (200 requests per 60s sliding window)
- Retry logic with exponential backoff for transient errors
- Network timeout handling
- Request/response logging

Test coverage:
- tests/integration/api/test_authentication.py
- tests/integration/api/test_order_management.py
- tests/integration/api/test_position_management.py
- tests/integration/api/test_error_handling.py
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from src.api.exceptions import AuthenticationError, APIError, RateLimitError, NetworkError

# Configure logging
logger = logging.getLogger(__name__)


class Position:
    """Position data object"""
    def __init__(self, account_id: int, contract_id: str, side: int,
                 quantity: int, avg_price: float, unrealized_pnl: float):
        self.account_id = account_id
        self.contract_id = contract_id
        self.side = side
        self.quantity = quantity
        self.avg_price = avg_price
        self.unrealized_pnl = unrealized_pnl


class Contract:
    """Contract metadata object"""
    def __init__(self, id: str, name: str, symbol: str, exchange: str,
                 tick_size: float, tick_value: float, contract_size: int):
        self.id = id
        self.name = name
        self.symbol = symbol
        self.exchange = exchange
        self.tick_size = tick_size
        self.tick_value = tick_value
        self.contract_size = contract_size


class RestClient:
    """REST API Client for TopstepX API with JWT auth, rate limiting, and retry logic"""

    RATE_LIMIT_REQUESTS = 200  # Max requests per window
    RATE_LIMIT_WINDOW = 60  # seconds
    MAX_RETRIES = 5
    INITIAL_BACKOFF = 1  # seconds
    REQUEST_TIMEOUT = 30  # seconds

    def __init__(self, base_url: str, username: str, api_key: str):
        """Initialize REST client with credentials"""
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_key = api_key
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._request_timestamps: List[datetime] = []

        # Create requests session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'text/plain, application/json'
        })

    def authenticate(self) -> bool:
        """Authenticate with API and obtain JWT token"""
        url = f"{self.base_url}/api/Auth/loginKey"
        payload = {
            "userName": self.username,
            "apiKey": self.api_key
        }

        try:
            logger.info("Attempting authentication...")
            response = self.session.post(
                url,
                json=payload,
                timeout=self.REQUEST_TIMEOUT
            )

            if response.status_code == 401:
                logger.error("Authentication failed: Invalid credentials")
                raise AuthenticationError("Invalid credentials")

            response.raise_for_status()
            data = response.json()

            if not data.get('success', False):
                error_msg = data.get('errorMessage', 'Authentication failed')
                logger.error(f"Authentication failed: {error_msg}")
                raise AuthenticationError(error_msg)

            # Store JWT token
            self._token = data.get('token')
            if not self._token:
                raise AuthenticationError("No token received in response")

            # Parse JWT to get expiry (simplified - just set to 1 hour)
            # In production, would decode JWT to get actual expiry
            self._token_expiry = datetime.now() + timedelta(hours=1)

            logger.info("Authentication successful")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication request failed: {e}")
            raise AuthenticationError(f"Authentication request failed: {e}")

    def is_authenticated(self) -> bool:
        """Check if client is currently authenticated with valid token"""
        if self._token is None:
            return False
        if self._token_expiry and self._token_expiry < datetime.now():
            return False
        return True

    def _enforce_rate_limit(self):
        """Enforce rate limiting by tracking requests in sliding window"""
        now = datetime.now()

        # Remove timestamps outside the sliding window
        cutoff = now - timedelta(seconds=self.RATE_LIMIT_WINDOW)
        self._request_timestamps = [
            ts for ts in self._request_timestamps if ts > cutoff
        ]

        # Check if we're at the rate limit
        if len(self._request_timestamps) >= self.RATE_LIMIT_REQUESTS:
            # Calculate how long to wait
            oldest_timestamp = self._request_timestamps[0]
            wait_time = (oldest_timestamp + timedelta(seconds=self.RATE_LIMIT_WINDOW) - now).total_seconds()

            if wait_time > 0:
                logger.warning(f"Rate limit approaching, delaying request by {wait_time:.2f}s")
                time.sleep(wait_time)
                # Recursively check again after waiting
                return self._enforce_rate_limit()

        # Add current timestamp
        self._request_timestamps.append(now)

    def _make_authenticated_request(self, method: str, endpoint: str,
                                   payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make authenticated API request with retry logic"""
        if not self.is_authenticated():
            raise AuthenticationError("Client is not authenticated")

        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self._token}'
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                # Enforce rate limiting before making request
                self._enforce_rate_limit()

                # Make request
                response = self.session.request(
                    method=method,
                    url=url,
                    json=payload,
                    headers=headers,
                    timeout=self.REQUEST_TIMEOUT
                )

                # Handle different status codes
                if response.status_code == 401:
                    logger.error("Authentication error: 401 Unauthorized")
                    raise AuthenticationError("Invalid or expired token")

                if response.status_code == 429:
                    # Rate limit exceeded
                    retry_after = int(response.headers.get('Retry-After', self.INITIAL_BACKOFF * (2 ** attempt)))
                    logger.warning(f"Rate limit exceeded (429), retrying after {retry_after}s")
                    time.sleep(retry_after)
                    continue

                if response.status_code == 504:
                    # Gateway timeout - retry immediately
                    logger.warning(f"Gateway timeout (504), attempt {attempt + 1}/{self.MAX_RETRIES}")
                    if attempt < self.MAX_RETRIES - 1:
                        continue
                    raise NetworkError("Gateway timeout after retries")

                if response.status_code >= 500:
                    # Server error - retry with exponential backoff
                    if attempt < self.MAX_RETRIES - 1:
                        backoff = self.INITIAL_BACKOFF * (2 ** attempt)
                        logger.warning(f"Server error {response.status_code}, retrying in {backoff}s (attempt {attempt + 1}/{self.MAX_RETRIES})")
                        time.sleep(backoff)
                        continue
                    else:
                        logger.error(f"Request failed after {self.MAX_RETRIES} attempts")
                        raise APIError(f"Server error {response.status_code} after {self.MAX_RETRIES} retries")

                # Success or client error (4xx other than 401, 429)
                response.raise_for_status()

                # Try to parse JSON response
                try:
                    return response.json()
                except json.JSONDecodeError:
                    # Some endpoints return plain text on error
                    logger.warning(f"Could not parse JSON response: {response.text}")
                    return {'success': True} if response.status_code == 200 else {'error': response.text}

            except requests.exceptions.Timeout:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"Request timeout, retrying (attempt {attempt + 1}/{self.MAX_RETRIES})")
                    continue
                raise NetworkError(f"Request timeout after {self.MAX_RETRIES} attempts")

            except requests.exceptions.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    backoff = self.INITIAL_BACKOFF * (2 ** attempt)
                    logger.warning(f"Request error: {e}, retrying in {backoff}s")
                    time.sleep(backoff)
                    continue
                raise APIError(f"Request failed: {e}")

        raise APIError(f"Request failed after {self.MAX_RETRIES} attempts")

    def close_position(self, account_id: int, contract_id: str) -> bool:
        """Close position for contract"""
        payload = {
            'accountId': account_id,
            'contractId': contract_id
        }

        data = self._make_authenticated_request('POST', '/api/Position/closeContract', payload)

        if data.get('success', False):
            logger.info(f"Position closed successfully for contract {contract_id}")
            return True

        error_msg = data.get('errorMessage', 'Unknown error')
        logger.error(f"Failed to close position: {error_msg}")
        raise APIError(f"Failed to close position: {error_msg}")

    def cancel_order(self, account_id: int, order_id: int) -> bool:
        """Cancel working order"""
        payload = {
            'accountId': account_id,
            'orderId': order_id
        }

        data = self._make_authenticated_request('POST', '/api/Order/cancel', payload)

        if data.get('success', False):
            logger.info(f"Order canceled successfully: order_id={order_id}")
            return True

        error_msg = data.get('errorMessage', 'Unknown error')
        logger.error(f"Failed to cancel order: {error_msg}")
        raise APIError(f"Failed to cancel order: {error_msg}")

    def place_order(self, account_id: int, contract_id: str, type: int,
                   side: int, size: int, stop_price: float) -> int:
        """Place order and return order ID"""
        payload = {
            'accountId': account_id,
            'contractId': contract_id,
            'type': type,
            'side': side,
            'size': size,
            'stopPrice': stop_price,
            'limitPrice': None,
            'trailPrice': None,
            'customTag': None
        }

        data = self._make_authenticated_request('POST', '/api/Order/place', payload)

        if data.get('success', False):
            order_id = data.get('orderId')
            if order_id:
                logger.info(f"Stop-loss order placed successfully: order_id={order_id}")
                return order_id
            else:
                raise APIError("Order placed but no orderId returned")

        error_msg = data.get('errorMessage', 'Unknown error')
        logger.error(f"Failed to place order: {error_msg}")
        raise APIError(f"Failed to place order: {error_msg}")

    def modify_order(self, account_id: int, order_id: int,
                    stop_price: float) -> bool:
        """Modify existing order"""
        payload = {
            'accountId': account_id,
            'orderId': order_id,
            'stopPrice': stop_price,
            'size': None,
            'limitPrice': None,
            'trailPrice': None
        }

        data = self._make_authenticated_request('POST', '/api/Order/modify', payload)

        if data.get('success', False):
            logger.info(f"Order modified successfully: order_id={order_id}, new_stop_price={stop_price}")
            return True

        error_msg = data.get('errorMessage', 'Unknown error')
        logger.error(f"Failed to modify order: {error_msg}")
        raise APIError(f"Failed to modify order: {error_msg}")

    def search_open_positions(self, account_id: int) -> List[Position]:
        """Search for open positions"""
        payload = {
            'accountId': account_id
        }

        data = self._make_authenticated_request('POST', '/api/Position/searchOpen', payload)

        if not data.get('success', False):
            error_msg = data.get('errorMessage', 'Unknown error')
            logger.error(f"Failed to search positions: {error_msg}")
            raise APIError(f"Failed to search positions: {error_msg}")

        positions_data = data.get('positions', [])
        positions = []

        for pos_data in positions_data:
            position = Position(
                account_id=pos_data.get('accountId'),
                contract_id=pos_data.get('contractId'),
                side=pos_data.get('side'),
                quantity=pos_data.get('quantity', pos_data.get('size')),  # Test uses 'quantity'
                avg_price=pos_data.get('avgPrice', pos_data.get('averagePrice')),  # Test uses 'avgPrice'
                unrealized_pnl=pos_data.get('unrealizedPnl', 0.0)
            )
            positions.append(position)

        logger.debug(f"Retrieved {len(positions)} open positions for account {account_id}")
        return positions

    def search_contract_by_id(self, contract_id: str) -> Contract:
        """Get contract metadata by ID"""
        payload = {
            'contractId': contract_id
        }

        data = self._make_authenticated_request('POST', '/api/Contract/searchById', payload)

        if not data.get('success', False):
            error_msg = data.get('errorMessage', 'Unknown error')
            logger.error(f"Failed to search contract: {error_msg}")
            raise APIError(f"Failed to search contract: {error_msg}")

        contract_data = data.get('contract')
        if not contract_data:
            raise APIError(f"No contract data returned for {contract_id}")

        contract = Contract(
            id=contract_data.get('id'),
            name=contract_data.get('name', ''),
            symbol=contract_data.get('symbol', contract_data.get('symbolId', '')),  # Test uses 'symbol'
            exchange=contract_data.get('exchange', ''),
            tick_size=contract_data.get('tickSize', 0.0),
            tick_value=contract_data.get('tickValue', 0.0),
            contract_size=contract_data.get('contractSize', 1)
        )

        logger.debug(f"Retrieved contract metadata for {contract_id}")
        return contract
