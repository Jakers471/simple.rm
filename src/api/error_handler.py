"""
Error Handler for API Resilience

Implements:
- Error classification (transient vs permanent)
- Retry decision logic with exponential backoff
- Error context enrichment
- Comprehensive error taxonomy
- HTTP status code categorization

Error Categories:
- TransientError: Retryable errors (408, 429, 500, 502, 503, 504)
- PermanentError: Non-retryable errors (400, 401, 403, 404)
- APIError: Base error class

Test coverage:
- tests/unit/api/test_error_handler.py
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from src.api.exceptions import APIError, AuthenticationError, RateLimitError, NetworkError

# Configure logging
logger = logging.getLogger(__name__)


class TransientError(APIError):
    """
    Transient errors that may succeed on retry.

    Examples:
    - 408 Request Timeout
    - 429 Too Many Requests
    - 500 Internal Server Error
    - 502 Bad Gateway
    - 503 Service Unavailable
    - 504 Gateway Timeout
    """
    def __init__(self, message: str, status_code: int = None,
                 retry_after: int = None, context: Dict[str, Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after
        self.context = context or {}
        self.timestamp = datetime.now()


class PermanentError(APIError):
    """
    Permanent errors that will not succeed on retry.

    Examples:
    - 400 Bad Request
    - 401 Unauthorized
    - 403 Forbidden
    - 404 Not Found
    - 405 Method Not Allowed
    - 409 Conflict
    - 422 Unprocessable Entity
    """
    def __init__(self, message: str, status_code: int = None,
                 context: Dict[str, Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.context = context or {}
        self.timestamp = datetime.now()


class ErrorHandler:
    """
    Centralized error handling with retry logic and error classification.

    Features:
    - Automatic error classification
    - Exponential backoff calculation
    - Retry decision logic
    - Context enrichment
    - Detailed logging
    """

    # Retry configuration
    MAX_RETRIES = 5
    INITIAL_BACKOFF = 1  # seconds
    MAX_BACKOFF = 60  # seconds
    BACKOFF_MULTIPLIER = 2
    JITTER_FACTOR = 0.1  # 10% jitter

    # HTTP status code categories
    TRANSIENT_STATUS_CODES = {
        408,  # Request Timeout
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
    }

    PERMANENT_STATUS_CODES = {
        400,  # Bad Request
        401,  # Unauthorized
        403,  # Forbidden
        404,  # Not Found
        405,  # Method Not Allowed
        406,  # Not Acceptable
        409,  # Conflict
        410,  # Gone
        422,  # Unprocessable Entity
    }

    # Error message patterns for classification
    TRANSIENT_PATTERNS = [
        'timeout',
        'connection',
        'network',
        'temporary',
        'unavailable',
        'overloaded',
        'retry',
    ]

    PERMANENT_PATTERNS = [
        'invalid',
        'not found',
        'forbidden',
        'unauthorized',
        'bad request',
        'conflict',
    ]

    def __init__(self):
        """Initialize error handler with default configuration"""
        self.retry_counts: Dict[str, int] = {}
        self.error_history: list = []

    def handle_error(self, response: Any, context: Dict[str, Any]) -> Tuple[Exception, bool]:
        """
        Process API error response and classify error type.

        Args:
            response: HTTP response object with status_code and content
            context: Request context (method, endpoint, payload, etc.)

        Returns:
            Tuple of (error_object, should_retry)

        Example:
            error, should_retry = handler.handle_error(response, {
                'method': 'POST',
                'endpoint': '/api/Order/place',
                'attempt': 1
            })
        """
        status_code = getattr(response, 'status_code', None)

        # Extract error message from response
        error_message = self._extract_error_message(response)

        # Classify error
        error_type, retry_after = self.classify_error(status_code, error_message)

        # Enrich context
        enriched_context = self._enrich_context(context, response)

        # Create appropriate error object
        if error_type == 'transient':
            error = TransientError(
                message=error_message,
                status_code=status_code,
                retry_after=retry_after,
                context=enriched_context
            )
            should_retry = True

        elif error_type == 'permanent':
            error = PermanentError(
                message=error_message,
                status_code=status_code,
                context=enriched_context
            )
            should_retry = False

        elif error_type == 'authentication':
            error = AuthenticationError(error_message)
            should_retry = False

        elif error_type == 'rate_limit':
            error = RateLimitError(
                f"Rate limit exceeded. Retry after: {retry_after}s"
            )
            should_retry = True

        else:
            # Unknown error type - default to permanent
            error = APIError(error_message)
            should_retry = False

        # Log error
        self._log_error(error, enriched_context, should_retry)

        # Record in history
        self._record_error(error, enriched_context)

        return error, should_retry

    def classify_error(self, status_code: Optional[int],
                      error_body: str) -> Tuple[str, Optional[int]]:
        """
        Classify error based on HTTP status code and error message.

        Args:
            status_code: HTTP status code
            error_body: Error message or response body

        Returns:
            Tuple of (error_type, retry_after_seconds)

        Error types:
            - 'transient': Temporary error, retry recommended
            - 'permanent': Permanent error, do not retry
            - 'authentication': Authentication failure
            - 'rate_limit': Rate limit exceeded
            - 'unknown': Cannot determine error type
        """
        retry_after = None

        # Check for specific status codes first
        if status_code == 401:
            return ('authentication', None)

        if status_code == 429:
            # Rate limit - extract retry-after if available
            retry_after = self._extract_retry_after(error_body)
            return ('rate_limit', retry_after)

        if status_code in self.TRANSIENT_STATUS_CODES:
            return ('transient', None)

        if status_code in self.PERMANENT_STATUS_CODES:
            return ('permanent', None)

        # Check error message patterns if status code is ambiguous
        if error_body:
            error_body_lower = error_body.lower()

            # Check for transient patterns
            for pattern in self.TRANSIENT_PATTERNS:
                if pattern in error_body_lower:
                    return ('transient', None)

            # Check for permanent patterns
            for pattern in self.PERMANENT_PATTERNS:
                if pattern in error_body_lower:
                    return ('permanent', None)

        # Default to unknown if we can't classify
        return ('unknown', None)

    def should_retry(self, error: Exception, attempt: int = 0) -> bool:
        """
        Determine if request should be retried based on error type and attempt count.

        Args:
            error: Exception object
            attempt: Current retry attempt (0-indexed)

        Returns:
            True if retry is recommended, False otherwise
        """
        # Never retry beyond max attempts
        if attempt >= self.MAX_RETRIES:
            logger.warning(
                f"Max retries ({self.MAX_RETRIES}) exceeded for {type(error).__name__}"
            )
            return False

        # Retry transient errors
        if isinstance(error, TransientError):
            return True

        # Retry rate limit errors
        if isinstance(error, RateLimitError):
            return True

        # Don't retry permanent errors
        if isinstance(error, PermanentError):
            return False

        # Don't retry authentication errors
        if isinstance(error, AuthenticationError):
            return False

        # For unknown errors, be conservative and don't retry
        return False

    def get_retry_delay(self, attempt: int, error: Exception = None) -> float:
        """
        Calculate retry delay with exponential backoff and jitter.

        Args:
            attempt: Current retry attempt (0-indexed)
            error: Optional error object that may contain retry-after hint

        Returns:
            Delay in seconds before next retry

        Formula:
            delay = min(initial_backoff * (multiplier ^ attempt), max_backoff)
            delay += random_jitter (-10% to +10%)
        """
        # Check if error specifies retry-after
        if isinstance(error, TransientError) and error.retry_after:
            return float(error.retry_after)

        # Calculate exponential backoff
        backoff = min(
            self.INITIAL_BACKOFF * (self.BACKOFF_MULTIPLIER ** attempt),
            self.MAX_BACKOFF
        )

        # Add jitter to avoid thundering herd
        import random
        jitter = backoff * self.JITTER_FACTOR * (2 * random.random() - 1)

        delay = backoff + jitter

        logger.debug(
            f"Retry delay calculated: attempt={attempt}, "
            f"backoff={backoff:.2f}s, jitter={jitter:.2f}s, total={delay:.2f}s"
        )

        return max(0, delay)  # Ensure non-negative

    def _extract_error_message(self, response: Any) -> str:
        """
        Extract error message from response object.

        Args:
            response: HTTP response object

        Returns:
            Error message string
        """
        # Try to get JSON error message
        try:
            data = response.json()
            if isinstance(data, dict):
                # Check common error message fields
                for field in ['errorMessage', 'error', 'message', 'detail']:
                    if field in data:
                        return str(data[field])
        except:
            pass

        # Fall back to response text
        try:
            return response.text if response.text else f"HTTP {response.status_code}"
        except:
            return f"HTTP {getattr(response, 'status_code', 'Unknown')}"

    def _extract_retry_after(self, error_body: str) -> Optional[int]:
        """
        Extract Retry-After value from error response.

        Args:
            error_body: Error response body

        Returns:
            Retry-after seconds, or None if not found
        """
        import re

        # Try to find "retry after X seconds" patterns
        patterns = [
            r'retry[- ]?after[:\s]+(\d+)',
            r'wait[:\s]+(\d+)',
            r'(\d+)[:\s]+seconds?',
        ]

        for pattern in patterns:
            match = re.search(pattern, error_body.lower())
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue

        return None

    def _enrich_context(self, context: Dict[str, Any], response: Any) -> Dict[str, Any]:
        """
        Add additional context to error for debugging.

        Args:
            context: Original request context
            response: HTTP response object

        Returns:
            Enriched context dictionary
        """
        enriched = context.copy()

        enriched.update({
            'timestamp': datetime.now().isoformat(),
            'status_code': getattr(response, 'status_code', None),
            'response_headers': dict(getattr(response, 'headers', {})),
        })

        # Add response body if small enough
        try:
            body = response.text
            if len(body) < 1000:  # Only include small responses
                enriched['response_body'] = body
        except:
            pass

        return enriched

    def _log_error(self, error: Exception, context: Dict[str, Any],
                   should_retry: bool):
        """
        Log error with appropriate level based on type and retry status.

        Args:
            error: Error object
            context: Error context
            should_retry: Whether error will be retried
        """
        error_type = type(error).__name__
        status_code = context.get('status_code', 'N/A')
        endpoint = context.get('endpoint', 'N/A')
        method = context.get('method', 'N/A')

        log_msg = (
            f"{error_type} on {method} {endpoint} "
            f"(HTTP {status_code}): {str(error)}"
        )

        if should_retry:
            logger.warning(f"{log_msg} [WILL RETRY]")
        else:
            logger.error(f"{log_msg} [PERMANENT]")

    def _record_error(self, error: Exception, context: Dict[str, Any]):
        """
        Record error in history for analysis.

        Args:
            error: Error object
            context: Error context
        """
        self.error_history.append({
            'timestamp': datetime.now(),
            'error_type': type(error).__name__,
            'message': str(error),
            'status_code': context.get('status_code'),
            'endpoint': context.get('endpoint'),
            'method': context.get('method'),
        })

        # Keep only last 100 errors
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]

    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about errors encountered.

        Returns:
            Dictionary with error statistics
        """
        if not self.error_history:
            return {
                'total_errors': 0,
                'by_type': {},
                'by_status': {},
                'by_endpoint': {},
            }

        stats = {
            'total_errors': len(self.error_history),
            'by_type': {},
            'by_status': {},
            'by_endpoint': {},
        }

        for entry in self.error_history:
            # Count by error type
            error_type = entry['error_type']
            stats['by_type'][error_type] = stats['by_type'].get(error_type, 0) + 1

            # Count by status code
            status_code = entry.get('status_code', 'Unknown')
            stats['by_status'][str(status_code)] = stats['by_status'].get(str(status_code), 0) + 1

            # Count by endpoint
            endpoint = entry.get('endpoint', 'Unknown')
            stats['by_endpoint'][endpoint] = stats['by_endpoint'].get(endpoint, 0) + 1

        return stats

    def clear_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.retry_counts.clear()
