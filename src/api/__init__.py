"""
API Module - REST Client and Exceptions

TODO: This module contains stubs for TDD - implement according to specs in:
- project-specs/SPECS/01-API-INTEGRATION/REST_API_SPEC.md
- reports/api-integration-analysis.md
"""

from src.api.rest_client import RestClient
from src.api.exceptions import AuthenticationError

__all__ = ['RestClient', 'AuthenticationError']
