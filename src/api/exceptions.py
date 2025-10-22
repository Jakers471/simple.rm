"""
API Exceptions

TODO: Implement full exception hierarchy according to:
- project-specs/SPECS/01-API-INTEGRATION/REST_API_SPEC.md
- Error handling requirements in test-specs/
"""


class AuthenticationError(Exception):
    """
    Raised when API authentication fails

    TODO: Implement with:
    - Error code
    - Original response
    - Retry information
    """
    pass


class APIError(Exception):
    """
    Base class for API errors

    TODO: Implement with:
    - Status code
    - Error message
    - Request/response context
    """
    pass


class RateLimitError(APIError):
    """
    Raised when rate limit is exceeded

    TODO: Implement with:
    - Retry-After header
    - Current rate limit status
    """
    pass


class NetworkError(APIError):
    """
    Raised on network/timeout errors

    TODO: Implement with:
    - Timeout information
    - Retry attempt count
    """
    pass
