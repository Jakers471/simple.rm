"""Example test demonstrating logging features

This file shows various logging patterns and best practices.
Run with: pytest tests/test_logging_example.py -v
"""
import pytest
import time
from log_utils import (
    logged_test,
    log_section,
    log_subsection,
    log_test_info,
    log_test_debug,
    log_api_call,
    log_database_query
)


class TestLoggingExamples:
    """Example test class showing logging patterns"""

    def test_section_organization(self):
        """Demonstrate section organization"""
        log_section("Example Test Suite")
        log_subsection("Basic Tests")

        log_test_info("test_section_organization", "Testing section headers")
        assert True

    @logged_test
    def test_automatic_logging(self):
        """Test with automatic logging via decorator"""
        # This test is automatically logged with timing
        result = 1 + 1
        assert result == 2

    def test_manual_logging(self, logger):
        """Test with manual logging using logger fixture"""
        logger.info("Starting manual logging test")

        # Simulate some work
        logger.debug("Processing step 1")
        time.sleep(0.1)

        logger.debug("Processing step 2")
        time.sleep(0.1)

        logger.info("Manual logging test complete")
        assert True

    def test_api_call_logging(self):
        """Demonstrate API call logging"""
        log_test_info("test_api_call_logging", "Testing API endpoints")

        # Simulate API calls
        log_api_call("/api/positions", "GET", 200)
        log_api_call("/api/orders", "POST", 201)
        log_api_call("/api/risk", "GET", 200)

        assert True

    def test_database_logging(self):
        """Demonstrate database query logging"""
        log_test_info("test_database_logging", "Testing database queries")

        # Simulate database queries
        log_database_query("SELECT", "positions", duration_ms=12.5)
        log_database_query("INSERT", "orders", duration_ms=8.3)
        log_database_query("UPDATE", "risk_metrics", duration_ms=15.7)

        assert True

    @logged_test
    def test_with_debug_info(self):
        """Test with debug-level information"""
        log_test_debug("test_with_debug_info", "Starting calculation")

        result = sum(range(100))

        log_test_debug("test_with_debug_info", f"Calculation result: {result}")
        assert result == 4950

    @pytest.mark.parametrize("value,expected", [
        (1, 2),
        (2, 4),
        (3, 6)
    ])
    @logged_test
    def test_parameterized(self, value, expected):
        """Parameterized test with logging"""
        log_test_info(
            "test_parameterized",
            f"Testing with value={value}, expected={expected}"
        )
        assert value * 2 == expected

    def test_complex_workflow(self, logger):
        """Complex multi-step test with detailed logging"""
        log_section("Complex Workflow Test")

        # Step 1: Setup
        log_subsection("Setup Phase")
        logger.info("Initializing test data")
        test_data = {"user": "test_user", "balance": 1000}
        logger.debug(f"Test data: {test_data}")

        # Step 2: Execution
        log_subsection("Execution Phase")
        logger.info("Executing business logic")
        log_api_call("/api/validate", "POST", 200)
        log_database_query("SELECT", "users", duration_ms=10.2)

        # Step 3: Verification
        log_subsection("Verification Phase")
        logger.info("Verifying results")
        assert test_data["balance"] == 1000

        logger.info("Complex workflow test completed successfully")

    @logged_test
    def test_expected_failure(self):
        """Test that demonstrates error logging"""
        # This test will fail to show error logging
        log_test_info("test_expected_failure", "This test is expected to fail")
        assert False, "Intentional failure for logging demonstration"

    def test_with_warnings(self, logger):
        """Test with warning messages"""
        logger.info("Starting test with warnings")

        logger.warning("This is a warning message")
        logger.warning("Deprecated feature being used")

        logger.info("Test completed despite warnings")
        assert True

    @logged_test
    def test_performance_tracking(self):
        """Test with performance tracking"""
        log_test_info("test_performance_tracking", "Measuring performance")

        start = time.time()
        # Simulate work
        time.sleep(0.05)
        duration_ms = (time.time() - start) * 1000

        log_database_query("COMPLEX_QUERY", "analytics", duration_ms=duration_ms)

        assert duration_ms < 100, "Performance within acceptable range"


class TestLoggingIntegration:
    """Tests showing integration with fixtures and setup/teardown"""

    @pytest.fixture
    def sample_data(self, logger):
        """Fixture with logging"""
        logger.info("Setting up sample data fixture")

        data = {"test": "data"}

        yield data

        logger.info("Tearing down sample data fixture")

    def test_with_fixture(self, sample_data, logger):
        """Test using fixture with logging"""
        logger.info(f"Using sample data: {sample_data}")
        assert sample_data["test"] == "data"

    @pytest.fixture(autouse=True)
    def log_test_boundaries(self, logger, request):
        """Automatically log test start and end"""
        test_name = request.node.name
        logger.info(f"=== Starting: {test_name} ===")

        yield

        logger.info(f"=== Finished: {test_name} ===")

    def test_auto_boundaries(self):
        """Test with automatic boundary logging"""
        # The fixture above logs start/end automatically
        assert True


# Example of module-level logging
def test_module_level():
    """Test at module level (not in a class)"""
    log_section("Module Level Tests")
    log_test_info("test_module_level", "Testing module-level function")
    assert True


# Example with skip
@pytest.mark.skip(reason="Demonstrating skip logging")
def test_skipped():
    """This test is skipped"""
    assert True


# Example with conditional skip
@pytest.mark.skipif(True, reason="Conditional skip example")
def test_conditional_skip():
    """This test is conditionally skipped"""
    assert True
