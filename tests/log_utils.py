"""Test logging utilities

Provides helper functions for consistent logging across all tests.
"""
import logging
import functools
from datetime import datetime
from typing import Callable, Any


def log_test_start(test_name: str) -> None:
    """Log when a test starts

    Args:
        test_name: Name of the test being executed
    """
    logger = logging.getLogger("pytest")
    logger.info(f"STARTING: {test_name}")


def log_test_pass(test_name: str, duration: float = None) -> None:
    """Log test success

    Args:
        test_name: Name of the test that passed
        duration: Optional test duration in seconds
    """
    logger = logging.getLogger("pytest")
    duration_str = f" ({duration:.3f}s)" if duration else ""
    logger.info(f"✓ PASSED: {test_name}{duration_str}")


def log_test_fail(test_name: str, error: Exception) -> None:
    """Log test failure

    Args:
        test_name: Name of the test that failed
        error: Exception that caused the failure
    """
    logger = logging.getLogger("pytest")
    logger.error(f"✗ FAILED: {test_name}")
    logger.error(f"  Error Type: {type(error).__name__}")
    logger.error(f"  Error Message: {str(error)}")


def log_test_skip(test_name: str, reason: str) -> None:
    """Log test skip

    Args:
        test_name: Name of the test that was skipped
        reason: Reason for skipping
    """
    logger = logging.getLogger("pytest")
    logger.warning(f"⊘ SKIPPED: {test_name} - {reason}")


def log_test_info(test_name: str, message: str) -> None:
    """Log informational message during test

    Args:
        test_name: Name of the test
        message: Information message
    """
    logger = logging.getLogger("pytest")
    logger.info(f"  [{test_name}] {message}")


def log_test_debug(test_name: str, message: str) -> None:
    """Log debug message during test

    Args:
        test_name: Name of the test
        message: Debug message
    """
    logger = logging.getLogger("test_runner")
    logger.debug(f"  [{test_name}] {message}")


def log_coverage_report(coverage_percent: float, lines_covered: int, lines_total: int) -> None:
    """Log coverage statistics

    Args:
        coverage_percent: Coverage percentage
        lines_covered: Number of lines covered
        lines_total: Total number of lines
    """
    logger = logging.getLogger("coverage")
    logger.info(f"Coverage: {coverage_percent:.1f}% ({lines_covered}/{lines_total} lines)")


def logged_test(func: Callable) -> Callable:
    """Decorator to automatically log test execution

    Usage:
        @logged_test
        def test_something():
            assert True
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        test_name = func.__name__
        log_test_start(test_name)

        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            log_test_pass(test_name, duration)
            return result
        except Exception as e:
            log_test_fail(test_name, e)
            raise

    return wrapper


def log_section(section_name: str) -> None:
    """Log a section header for organizing test output

    Args:
        section_name: Name of the test section
    """
    logger = logging.getLogger("pytest")
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"  {section_name}")
    logger.info("=" * 80)


def log_subsection(subsection_name: str) -> None:
    """Log a subsection header

    Args:
        subsection_name: Name of the test subsection
    """
    logger = logging.getLogger("pytest")
    logger.info(f"\n--- {subsection_name} ---")


def log_api_call(endpoint: str, method: str, status_code: int = None) -> None:
    """Log API call information

    Args:
        endpoint: API endpoint being called
        method: HTTP method (GET, POST, etc.)
        status_code: Optional response status code
    """
    logger = logging.getLogger("test_runner")
    status = f" -> {status_code}" if status_code else ""
    logger.debug(f"API: {method} {endpoint}{status}")


def log_database_query(query_type: str, table: str, duration_ms: float = None) -> None:
    """Log database query information

    Args:
        query_type: Type of query (SELECT, INSERT, etc.)
        table: Table being queried
        duration_ms: Optional query duration in milliseconds
    """
    logger = logging.getLogger("test_runner")
    duration = f" ({duration_ms:.2f}ms)" if duration_ms else ""
    logger.debug(f"DB: {query_type} from {table}{duration}")
