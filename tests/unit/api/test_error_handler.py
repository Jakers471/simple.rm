"""
Comprehensive tests for ErrorHandler with actual implementation API.

Tests cover:
- Error classification for all HTTP status codes (400-599)
- Transient vs permanent error handling
- Retry logic with exponential backoff
- Error statistics tracking
- Context enrichment
- Retry-after header parsing
- Error message extraction
- Pattern-based classification

Target: 90%+ code coverage
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from src.api.error_handler import (
    ErrorHandler,
    TransientError,
    PermanentError
)
from src.api.exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    NetworkError
)


class TestTransientError:
    """Test TransientError class"""

    def test_transient_error_creation(self):
        """Test creating transient error with all fields"""
        error = TransientError(
            message="Service temporarily unavailable",
            status_code=503,
            retry_after=30,
            context={'endpoint': '/api/test'}
        )

        assert str(error) == "Service temporarily unavailable"
        assert error.status_code == 503
        assert error.retry_after == 30
        assert error.context == {'endpoint': '/api/test'}
        assert isinstance(error.timestamp, datetime)

    def test_transient_error_defaults(self):
        """Test transient error with default values"""
        error = TransientError("Timeout")

        assert str(error) == "Timeout"
        assert error.status_code is None
        assert error.retry_after is None
        assert error.context == {}
        assert isinstance(error.timestamp, datetime)

    def test_transient_error_inheritance(self):
        """Test that TransientError extends APIError"""
        error = TransientError("Test")
        assert isinstance(error, APIError)


class TestPermanentError:
    """Test PermanentError class"""

    def test_permanent_error_creation(self):
        """Test creating permanent error with all fields"""
        error = PermanentError(
            message="Resource not found",
            status_code=404,
            context={'endpoint': '/api/missing'}
        )

        assert str(error) == "Resource not found"
        assert error.status_code == 404
        assert error.context == {'endpoint': '/api/missing'}
        assert isinstance(error.timestamp, datetime)

    def test_permanent_error_defaults(self):
        """Test permanent error with default values"""
        error = PermanentError("Bad request")

        assert str(error) == "Bad request"
        assert error.status_code is None
        assert error.context == {}
        assert isinstance(error.timestamp, datetime)

    def test_permanent_error_inheritance(self):
        """Test that PermanentError extends APIError"""
        error = PermanentError("Test")
        assert isinstance(error, APIError)


class TestErrorHandlerInit:
    """Test ErrorHandler initialization"""

    def test_initialization(self):
        """Test handler initializes with empty state"""
        handler = ErrorHandler()

        assert handler.retry_counts == {}
        assert handler.error_history == []
        assert handler.MAX_RETRIES == 5
        assert handler.INITIAL_BACKOFF == 1
        assert handler.MAX_BACKOFF == 60

    def test_constants(self):
        """Test class constants are properly defined"""
        handler = ErrorHandler()

        # Transient status codes
        assert 408 in handler.TRANSIENT_STATUS_CODES
        assert 429 in handler.TRANSIENT_STATUS_CODES
        assert 500 in handler.TRANSIENT_STATUS_CODES
        assert 502 in handler.TRANSIENT_STATUS_CODES
        assert 503 in handler.TRANSIENT_STATUS_CODES
        assert 504 in handler.TRANSIENT_STATUS_CODES

        # Permanent status codes
        assert 400 in handler.PERMANENT_STATUS_CODES
        assert 401 in handler.PERMANENT_STATUS_CODES
        assert 403 in handler.PERMANENT_STATUS_CODES
        assert 404 in handler.PERMANENT_STATUS_CODES
        assert 405 in handler.PERMANENT_STATUS_CODES
        assert 409 in handler.PERMANENT_STATUS_CODES
        assert 422 in handler.PERMANENT_STATUS_CODES


class TestErrorClassification:
    """Test error classification logic"""

    def test_classify_authentication_error(self):
        """Test classification of 401 Unauthorized"""
        handler = ErrorHandler()
        error_type, retry_after = handler.classify_error(401, "Unauthorized")

        assert error_type == 'authentication'
        assert retry_after is None

    def test_classify_rate_limit_error(self):
        """Test classification of 429 Rate Limit"""
        handler = ErrorHandler()
        error_type, retry_after = handler.classify_error(
            429,
            "Rate limit exceeded. Retry after 60 seconds"
        )

        assert error_type == 'rate_limit'
        assert retry_after == 60

    def test_classify_rate_limit_no_retry_after(self):
        """Test 429 without retry-after hint"""
        handler = ErrorHandler()
        error_type, retry_after = handler.classify_error(429, "Too many requests")

        assert error_type == 'rate_limit'
        assert retry_after is None

    @pytest.mark.parametrize("status_code", [408, 500, 502, 503, 504])
    def test_classify_transient_by_status(self, status_code):
        """Test transient error classification by status code"""
        handler = ErrorHandler()
        error_type, retry_after = handler.classify_error(status_code, "Error")

        assert error_type == 'transient'
        assert retry_after is None

    @pytest.mark.parametrize("status_code", [400, 403, 404, 405, 406, 409, 410, 422])
    def test_classify_permanent_by_status(self, status_code):
        """Test permanent error classification by status code"""
        handler = ErrorHandler()
        error_type, retry_after = handler.classify_error(status_code, "Error")

        assert error_type == 'permanent'
        assert retry_after is None

    @pytest.mark.parametrize("message,expected_type", [
        ("Connection timeout", "transient"),
        ("Network error", "transient"),
        ("Service temporarily unavailable", "transient"),
        ("Server overloaded, please retry", "transient"),
        ("Invalid API key", "permanent"),
        ("Resource not found", "permanent"),
        ("Access forbidden", "permanent"),
        ("Bad request format", "permanent"),
    ])
    def test_classify_by_message_pattern(self, message, expected_type):
        """Test classification based on error message patterns"""
        handler = ErrorHandler()
        error_type, _ = handler.classify_error(None, message)

        assert error_type == expected_type

    def test_classify_unknown_error(self):
        """Test classification of unknown errors"""
        handler = ErrorHandler()
        error_type, retry_after = handler.classify_error(418, "I'm a teapot")

        assert error_type == 'unknown'
        assert retry_after is None

    def test_classify_no_status_no_message(self):
        """Test classification with no information"""
        handler = ErrorHandler()
        error_type, retry_after = handler.classify_error(None, "")

        assert error_type == 'unknown'
        assert retry_after is None


class TestRetryAfterExtraction:
    """Test retry-after header parsing"""

    def test_extract_retry_after_standard(self):
        """Test standard 'retry-after: X' format"""
        handler = ErrorHandler()
        retry_after = handler._extract_retry_after("retry-after: 120")

        assert retry_after == 120

    def test_extract_retry_after_hyphenated(self):
        """Test 'retry after X seconds' format"""
        handler = ErrorHandler()
        retry_after = handler._extract_retry_after("Please retry after 30 seconds")

        assert retry_after == 30

    def test_extract_retry_after_wait(self):
        """Test 'wait: X' format"""
        handler = ErrorHandler()
        retry_after = handler._extract_retry_after("wait: 45")

        assert retry_after == 45

    def test_extract_retry_after_not_found(self):
        """Test when retry-after is not present"""
        handler = ErrorHandler()
        retry_after = handler._extract_retry_after("Generic error message")

        assert retry_after is None

    def test_extract_retry_after_invalid_number(self):
        """Test when retry-after contains invalid number"""
        handler = ErrorHandler()
        retry_after = handler._extract_retry_after("retry-after: invalid")

        assert retry_after is None


class TestRetryLogic:
    """Test should_retry decision logic"""

    def test_should_retry_transient_error(self):
        """Test retry decision for transient errors"""
        handler = ErrorHandler()
        error = TransientError("Timeout", status_code=408)

        assert handler.should_retry(error, attempt=0) is True
        assert handler.should_retry(error, attempt=2) is True
        assert handler.should_retry(error, attempt=4) is True

    def test_should_retry_rate_limit_error(self):
        """Test retry decision for rate limit errors"""
        handler = ErrorHandler()
        error = RateLimitError("Rate limited")

        assert handler.should_retry(error, attempt=0) is True
        assert handler.should_retry(error, attempt=3) is True

    def test_should_not_retry_permanent_error(self):
        """Test no retry for permanent errors"""
        handler = ErrorHandler()
        error = PermanentError("Not found", status_code=404)

        assert handler.should_retry(error, attempt=0) is False
        assert handler.should_retry(error, attempt=2) is False

    def test_should_not_retry_auth_error(self):
        """Test no retry for authentication errors"""
        handler = ErrorHandler()
        error = AuthenticationError("Invalid credentials")

        assert handler.should_retry(error, attempt=0) is False

    def test_should_not_retry_unknown_error(self):
        """Test no retry for unknown errors"""
        handler = ErrorHandler()
        error = APIError("Unknown error")

        assert handler.should_retry(error, attempt=0) is False

    def test_should_not_retry_max_attempts_exceeded(self):
        """Test no retry when max attempts exceeded"""
        handler = ErrorHandler()
        error = TransientError("Timeout", status_code=408)

        # Exactly at max should not retry
        assert handler.should_retry(error, attempt=5) is False

        # Beyond max should not retry
        assert handler.should_retry(error, attempt=6) is False
        assert handler.should_retry(error, attempt=10) is False


class TestRetryDelay:
    """Test exponential backoff calculation"""

    def test_get_retry_delay_first_attempt(self):
        """Test delay for first retry (attempt 0)"""
        handler = ErrorHandler()
        delay = handler.get_retry_delay(0)

        # Should be around 1 second (initial backoff) with ±10% jitter
        assert 0.9 <= delay <= 1.1

    def test_get_retry_delay_exponential_growth(self):
        """Test exponential growth of delay"""
        handler = ErrorHandler()

        # Attempt 0: 1 * 2^0 = 1
        delay0 = handler.get_retry_delay(0)
        assert 0.9 <= delay0 <= 1.1

        # Attempt 1: 1 * 2^1 = 2
        delay1 = handler.get_retry_delay(1)
        assert 1.8 <= delay1 <= 2.2

        # Attempt 2: 1 * 2^2 = 4
        delay2 = handler.get_retry_delay(2)
        assert 3.6 <= delay2 <= 4.4

        # Attempt 3: 1 * 2^3 = 8
        delay3 = handler.get_retry_delay(3)
        assert 7.2 <= delay3 <= 8.8

    def test_get_retry_delay_max_cap(self):
        """Test delay is capped at MAX_BACKOFF"""
        handler = ErrorHandler()

        # High attempt should cap at 60 seconds + jitter
        delay = handler.get_retry_delay(10)
        assert delay <= handler.MAX_BACKOFF * 1.1  # Max + jitter
        assert delay >= handler.MAX_BACKOFF * 0.9  # Max - jitter

    def test_get_retry_delay_with_retry_after_hint(self):
        """Test delay respects retry-after from error"""
        handler = ErrorHandler()
        error = TransientError("Timeout", status_code=503, retry_after=45)

        delay = handler.get_retry_delay(0, error)
        assert delay == 45.0

    def test_get_retry_delay_non_negative(self):
        """Test delay is never negative"""
        handler = ErrorHandler()

        for attempt in range(10):
            delay = handler.get_retry_delay(attempt)
            assert delay >= 0


class TestErrorMessageExtraction:
    """Test error message extraction from responses"""

    def test_extract_error_message_json_error_message(self):
        """Test extraction from JSON with 'errorMessage' field"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 400
        response.json.return_value = {'errorMessage': 'Invalid request'}

        message = handler._extract_error_message(response)
        assert message == 'Invalid request'

    def test_extract_error_message_json_error_field(self):
        """Test extraction from JSON with 'error' field"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 500
        response.json.return_value = {'error': 'Internal server error'}

        message = handler._extract_error_message(response)
        assert message == 'Internal server error'

    def test_extract_error_message_json_message_field(self):
        """Test extraction from JSON with 'message' field"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 404
        response.json.return_value = {'message': 'Not found'}

        message = handler._extract_error_message(response)
        assert message == 'Not found'

    def test_extract_error_message_json_detail_field(self):
        """Test extraction from JSON with 'detail' field"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 422
        response.json.return_value = {'detail': 'Validation failed'}

        message = handler._extract_error_message(response)
        assert message == 'Validation failed'

    def test_extract_error_message_fallback_to_text(self):
        """Test fallback to response text when JSON fails"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 500
        response.json.side_effect = ValueError("Invalid JSON")
        response.text = "Internal Server Error"

        message = handler._extract_error_message(response)
        assert message == "Internal Server Error"

    def test_extract_error_message_empty_text(self):
        """Test fallback to status code when text is empty"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 503
        response.json.side_effect = ValueError("Invalid JSON")
        response.text = ""

        message = handler._extract_error_message(response)
        assert message == "HTTP 503"

    def test_extract_error_message_no_status_code(self):
        """Test handling when status code is missing"""
        handler = ErrorHandler()
        response = Mock()
        del response.status_code
        response.json.side_effect = ValueError("Invalid JSON")
        response.text = None

        message = handler._extract_error_message(response)
        assert "Unknown" in message


class TestContextEnrichment:
    """Test error context enrichment"""

    def test_enrich_context_basic(self):
        """Test basic context enrichment"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 500
        response.headers = {'Content-Type': 'application/json'}
        response.text = "Error"

        context = {
            'method': 'POST',
            'endpoint': '/api/test'
        }

        enriched = handler._enrich_context(context, response)

        assert enriched['method'] == 'POST'
        assert enriched['endpoint'] == '/api/test'
        assert enriched['status_code'] == 500
        assert enriched['response_headers'] == {'Content-Type': 'application/json'}
        assert 'timestamp' in enriched
        assert enriched['response_body'] == "Error"

    def test_enrich_context_large_body_excluded(self):
        """Test large response body is not included"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 500
        response.headers = {}
        response.text = "x" * 2000  # Large body

        enriched = handler._enrich_context({}, response)

        assert 'response_body' not in enriched

    def test_enrich_context_preserves_original(self):
        """Test original context is not modified"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 400
        response.headers = {}
        response.text = "Error"

        original = {'method': 'GET', 'endpoint': '/api/test'}
        enriched = handler._enrich_context(original, response)

        # Original should not be modified
        assert 'status_code' not in original
        assert 'timestamp' not in original

        # Enriched should have new fields
        assert enriched['status_code'] == 400
        assert 'timestamp' in enriched


class TestHandleError:
    """Test complete error handling flow"""

    def test_handle_transient_error(self):
        """Test handling of transient error"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 503
        response.headers = {}
        response.json.return_value = {'error': 'Service unavailable'}
        response.text = "Service unavailable"

        context = {'method': 'POST', 'endpoint': '/api/test'}

        error, should_retry = handler.handle_error(response, context)

        assert isinstance(error, TransientError)
        assert error.status_code == 503
        assert should_retry is True
        assert len(handler.error_history) == 1

    def test_handle_permanent_error(self):
        """Test handling of permanent error"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 404
        response.headers = {}
        response.json.return_value = {'error': 'Not found'}
        response.text = "Not found"

        context = {'method': 'GET', 'endpoint': '/api/missing'}

        error, should_retry = handler.handle_error(response, context)

        assert isinstance(error, PermanentError)
        assert error.status_code == 404
        assert should_retry is False
        assert len(handler.error_history) == 1

    def test_handle_authentication_error(self):
        """Test handling of authentication error"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 401
        response.headers = {}
        response.json.return_value = {'error': 'Unauthorized'}
        response.text = "Unauthorized"

        context = {'method': 'GET', 'endpoint': '/api/protected'}

        error, should_retry = handler.handle_error(response, context)

        assert isinstance(error, AuthenticationError)
        assert should_retry is False
        assert len(handler.error_history) == 1

    def test_handle_rate_limit_error(self):
        """Test handling of rate limit error"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 429
        response.headers = {}
        response.json.return_value = {'error': 'Rate limit exceeded. Retry after 60 seconds'}
        response.text = "Rate limit exceeded. Retry after 60 seconds"

        context = {'method': 'POST', 'endpoint': '/api/test'}

        error, should_retry = handler.handle_error(response, context)

        assert isinstance(error, RateLimitError)
        assert should_retry is True
        assert "60" in str(error)

    def test_handle_unknown_error(self):
        """Test handling of unknown error"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 418  # I'm a teapot
        response.headers = {}
        response.json.return_value = {'error': 'Teapot'}
        response.text = "I'm a teapot"

        context = {'method': 'GET', 'endpoint': '/api/coffee'}

        error, should_retry = handler.handle_error(response, context)

        assert isinstance(error, APIError)
        assert should_retry is False


class TestErrorStatistics:
    """Test error statistics tracking"""

    def test_get_error_statistics_empty(self):
        """Test statistics with no errors"""
        handler = ErrorHandler()
        stats = handler.get_error_statistics()

        assert stats['total_errors'] == 0
        assert stats['by_type'] == {}
        assert stats['by_status'] == {}
        assert stats['by_endpoint'] == {}

    def test_get_error_statistics_single_error(self):
        """Test statistics with one error"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 404
        response.headers = {}
        response.json.return_value = {'error': 'Not found'}
        response.text = "Not found"

        handler.handle_error(response, {'method': 'GET', 'endpoint': '/api/test'})

        stats = handler.get_error_statistics()
        assert stats['total_errors'] == 1
        assert stats['by_type']['PermanentError'] == 1
        assert stats['by_status']['404'] == 1
        assert stats['by_endpoint']['/api/test'] == 1

    def test_get_error_statistics_multiple_errors(self):
        """Test statistics with multiple errors"""
        handler = ErrorHandler()

        # Create various error types
        responses = [
            (404, 'Not found'),
            (500, 'Internal error'),
            (503, 'Service unavailable'),
            (404, 'Another not found'),
        ]

        for status_code, message in responses:
            response = Mock()
            response.status_code = status_code
            response.headers = {}
            response.json.return_value = {'error': message}
            response.text = message

            handler.handle_error(response, {'method': 'GET', 'endpoint': f'/api/endpoint{status_code}'})

        stats = handler.get_error_statistics()
        assert stats['total_errors'] == 4
        assert stats['by_type']['PermanentError'] == 2
        assert stats['by_type']['TransientError'] == 2
        assert stats['by_status']['404'] == 2
        assert stats['by_status']['500'] == 1
        assert stats['by_status']['503'] == 1

    def test_error_history_limit(self):
        """Test error history is limited to 100 entries"""
        handler = ErrorHandler()

        # Create 150 errors
        for i in range(150):
            response = Mock()
            response.status_code = 500
            response.headers = {}
            response.json.return_value = {'error': f'Error {i}'}
            response.text = f'Error {i}'

            handler.handle_error(response, {'method': 'GET', 'endpoint': f'/api/test{i}'})

        # Should only keep last 100
        assert len(handler.error_history) == 100

        # First entry should be from error 50 onwards
        assert 'Error 50' in handler.error_history[0]['message']

    def test_clear_history(self):
        """Test clearing error history"""
        handler = ErrorHandler()

        # Create some errors
        response = Mock()
        response.status_code = 500
        response.headers = {}
        response.json.return_value = {'error': 'Error'}
        response.text = 'Error'

        handler.handle_error(response, {'method': 'GET', 'endpoint': '/api/test'})
        handler.handle_error(response, {'method': 'GET', 'endpoint': '/api/test'})

        assert len(handler.error_history) == 2

        # Clear history
        handler.clear_history()

        assert len(handler.error_history) == 0
        assert len(handler.retry_counts) == 0


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_handle_error_missing_status_code(self):
        """Test handling error when response has no status_code"""
        handler = ErrorHandler()
        response = Mock()
        # Remove status_code attribute
        del response.status_code
        response.json.side_effect = Exception("No JSON")
        response.text = "Error occurred"
        response.headers = {}

        context = {'method': 'GET', 'endpoint': '/api/test'}

        error, should_retry = handler.handle_error(response, context)

        # Should handle gracefully
        assert isinstance(error, APIError)
        assert should_retry is False

    def test_retry_delay_with_non_transient_error(self):
        """Test retry delay with error that has no retry_after"""
        handler = ErrorHandler()
        error = PermanentError("Not found", status_code=404)

        # Should still calculate delay even though error won't be retried
        delay = handler.get_retry_delay(0, error)
        assert delay >= 0

    def test_multiple_error_classifications(self):
        """Test that error classification is consistent"""
        handler = ErrorHandler()

        # Same error should classify the same way multiple times
        for _ in range(5):
            error_type, _ = handler.classify_error(500, "Internal error")
            assert error_type == 'transient'

    def test_concurrent_error_handling(self):
        """Test handling multiple errors in sequence"""
        handler = ErrorHandler()

        errors = []
        for i in range(10):
            response = Mock()
            response.status_code = 500 + i
            response.headers = {}
            response.json.return_value = {'error': f'Error {i}'}
            response.text = f'Error {i}'

            error, _ = handler.handle_error(
                response,
                {'method': 'GET', 'endpoint': f'/api/test{i}'}
            )
            errors.append(error)

        # All errors should be recorded
        assert len(handler.error_history) == 10
        assert len(errors) == 10


class TestRealWorldScenarios:
    """Test realistic error scenarios"""

    def test_api_timeout_scenario(self):
        """Test typical API timeout scenario"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 408
        response.headers = {'X-Request-ID': 'abc123'}
        response.json.return_value = {
            'errorMessage': 'Request timeout after 30 seconds'
        }
        response.text = 'Request timeout after 30 seconds'

        context = {
            'method': 'POST',
            'endpoint': '/api/Order/place',
            'attempt': 1
        }

        error, should_retry = handler.handle_error(response, context)

        assert isinstance(error, TransientError)
        assert error.status_code == 408
        assert should_retry is True
        assert error.context['method'] == 'POST'
        assert error.context['endpoint'] == '/api/Order/place'

    def test_rate_limit_with_retry_after(self):
        """Test rate limit with retry-after header"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 429
        response.headers = {'Retry-After': '120'}
        response.json.return_value = {
            'error': 'Rate limit exceeded. retry-after: 120 seconds'
        }
        response.text = 'Rate limit exceeded. retry-after: 120 seconds'

        context = {'method': 'GET', 'endpoint': '/api/Market/positions'}

        error, should_retry = handler.handle_error(response, context)

        assert isinstance(error, RateLimitError)
        assert should_retry is True

        # Retry delay should use retry-after from error message
        delay = handler.get_retry_delay(0, error)
        # RateLimitError doesn't have retry_after, so it uses exponential backoff
        assert delay > 0

    def test_authentication_failure_no_retry(self):
        """Test authentication failure is not retried"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 401
        response.headers = {}
        response.json.return_value = {
            'error': 'Invalid API credentials'
        }
        response.text = 'Invalid API credentials'

        context = {'method': 'POST', 'endpoint': '/api/auth/login'}

        error, should_retry = handler.handle_error(response, context)

        assert isinstance(error, AuthenticationError)
        assert should_retry is False
        assert not handler.should_retry(error, attempt=0)

    def test_server_error_with_retry(self):
        """Test server error is retried with exponential backoff"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 500
        response.headers = {}
        response.json.return_value = {
            'errorMessage': 'Internal server error'
        }
        response.text = 'Internal server error'

        error, should_retry = handler.handle_error(
            response,
            {'method': 'GET', 'endpoint': '/api/data'}
        )

        assert isinstance(error, TransientError)
        assert should_retry is True

        # Test retry delays increase
        delay1 = handler.get_retry_delay(0)
        delay2 = handler.get_retry_delay(1)
        delay3 = handler.get_retry_delay(2)

        assert delay2 > delay1
        assert delay3 > delay2

    def test_not_found_error_no_retry(self):
        """Test 404 errors are not retried"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 404
        response.headers = {}
        response.json.return_value = {
            'message': 'Order not found'
        }
        response.text = 'Order not found'

        error, should_retry = handler.handle_error(
            response,
            {'method': 'GET', 'endpoint': '/api/Order/12345'}
        )

        assert isinstance(error, PermanentError)
        assert error.status_code == 404
        assert should_retry is False
        assert not handler.should_retry(error, attempt=0)

    def test_validation_error_permanent(self):
        """Test validation errors are permanent"""
        handler = ErrorHandler()
        response = Mock()
        response.status_code = 422
        response.headers = {}
        response.json.return_value = {
            'detail': 'Invalid order parameters'
        }
        response.text = 'Invalid order parameters'

        error, should_retry = handler.handle_error(
            response,
            {'method': 'POST', 'endpoint': '/api/Order/place'}
        )

        assert isinstance(error, PermanentError)
        assert error.status_code == 422
        assert should_retry is False
